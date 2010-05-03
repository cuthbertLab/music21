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

import copy, types, random
import doctest, unittest
import sys
from copy import deepcopy


import music21 ## needed to properly do isinstance checking
#from music21 import ElementWrapper
from music21 import common
from music21 import clef
from music21 import chord
from music21 import defaults
from music21 import duration
from music21 import dynamics
from music21 import instrument
from music21 import interval
from music21 import key
from music21 import lily as lilyModule
from music21 import measure
from music21 import meter
from music21 import musicxml as musicxmlMod
from music21 import note

from music21 import environment
_MOD = "stream.py"
environLocal = environment.Environment(_MOD)

CLASS_SORT_ORDER = ["Clef", "TempoMark", "KeySignature", "TimeSignature", "Dynamic", "GeneralNote"]
#-------------------------------------------------------------------------------

class StreamException(Exception):
    pass

#-------------------------------------------------------------------------------



#-------------------------------------------------------------------------------
class StreamIterator():
    '''A simple Iterator object used to handle iteration of Streams and other 
    list-like objects. 
    '''
    def __init__(self, srcStream):
        self.srcStream = srcStream
        self.index = 0

    def __iter__(self):
        return self

    def next(self):
        if self.index >= len(self.srcStream.elements):
            del self.srcStream
            raise StopIteration
        post = self.srcStream.elements[self.index]
        # here, the parent of extracted element is being set to Stream
        # that is the source of the iteration
        post.parent = self.srcStream
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

    # define order to present names in documentation; use strings
    _DOC_ORDER = ['append', 'insert', 'measures', 'notes', 'pitches']
    # documentation for all attributes (not properties or methods)
    _DOC_ATTR = {
    'isSorted': 'Boolean describing whether the Stream is sorted or not.',
    'isFlat': 'Boolean describing whether the Stream is flat.',
    'flattenedRepresentationOf': 'When this flat Stream is derived from another non-flat stream, a reference to the source Stream is stored here.',
    }

    def __init__(self, givenElements = None):
        '''
        
        '''
        music21.Music21Object.__init__(self)

        # self._elements stores ElementWrapper objects. These are not ordered.
        # this should have a public attribute/property self.elements
        self._elements = [] # givenElements
        self._unlinkedDuration = None

        # the .obj attributes was held over from old ElementWrapper model
        # no longer needed
        #self.obj = None

        self.isSorted = True
        self.isFlat = True  ## does it have no embedded elements

        # seems that this should be named with a leading lower case?
        # when derivin a flat stream, store a reference to the non-flat Stream          
        # from which this was taken
        self.flattenedRepresentationOf = None 
        
        self._cache = common.defHash()

        if givenElements is not None:
            for thisEl in givenElements:
                self.insert(thisEl)


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

        >>> a = Stream()
        >>> for x in range(4):
        ...     n = note.Note('G#')
        ...     n.offset = x * 3
        ...     a.insert(n)
        >>> len(a)
        4

        >>> b = Stream()
        >>> for x in range(4):
        ...     b.insert(deepcopy(a) ) # append streams
        >>> len(b)
        4
        >>> len(b.flat)
        16
        '''
        return len(self._elements)

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

        >>> a = Stream()
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

        if common.isNum(key):
            returnEl = self.elements[key]
            returnEl.parent = self
            return returnEl
    
        elif isinstance(key, slice): # get a slice of index values
            # NOTE: this copy may return locations references that are 
            # not desirable
            #found = copy.copy(self) # return a stream of elements
            found = self.__class__()
            found.elements = self.elements[key]
            found._elementsChanged()

            # NOTE: this used to iterate over the Stream: probably not needed
            # all tests pass without
            #for element in found:
            #    pass ## sufficient to set parent properly
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


    #---------------------------------------------------------------------------
    # adding and editing Elements and Streams -- all need to call _elementsChanged
    # most will set isSorted to False

    def _elementsChanged(self):
        '''
        Call any time _elements is changed. Called by methods that add or change
        elements.

        >>> a = Stream()
        >>> a.isFlat
        True
        >>> a._elements.append(Stream())
        >>> a._elementsChanged()
        >>> a.isFlat
        False
        '''
        self.isSorted = False
        self.isFlat = True

        for thisElement in self._elements:
            if isinstance(thisElement, Stream): 
                self.isFlat = False
                break
        self._cache = common.defHash()

    def _getElements(self):
        return self._elements
   
    def _setElements(self, value):
        '''
        >>> a = Stream()
        >>> a.repeatInsert(note.Note("C"), range(10))
        >>> b = Stream()
        >>> b.repeatInsert(note.Note("C"), range(10))
        >>> b.offset = 6
        >>> c = Stream()
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

        >>> a = Stream()
        >>> a.repeatInsert(note.Note("C"), range(10))
        >>> b = Stream()
        >>> b.repeatInsert(note.Note("C"), range(10))
        >>> b.offset = 6
        >>> c = Stream()
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

        >>> a = Stream()
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

        >>> a = Stream()
        >>> a.repeatInsert(note.Note("C"), range(10))
        >>> b = Stream()
        >>> b.repeatInsert(note.Note("G"), range(10))
        >>> c = a + b   
        >>> c.pitches
        [C, C, C, C, C, C, C, C, C, C, G, G, G, G, G, G, G, G, G, G]
        '''
        s = Stream()
        s.elements = self._elements + other._elements
        s._elementsChanged()
        return s


    def indexList(self, obj, firstMatchOnly=False):
        '''Return a list of one or more index values where the supplied object is found on this Stream's `elements` list. 

        To just return the first matched index, set `firstMatchOnly` to True.

        No matches are found, an empty list is returned.

        >>> s = Stream()
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
        iMatch = []
        for i in range(len(self._elements)):
            if self._elements[i] == obj:
                iMatch.append(i)
            elif (hasattr(self._elements[i], "obj") and \
                     obj == self._elements[i].obj):
                iMatch.append(i)
            if firstMatchOnly and len(iMatch) > 0:
                break
        return iMatch

    def index(self, obj):
        '''Return the first matched index for the specified object.

        >>> a = Stream()
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

        >>> s = Stream()
        >>> n1 = note.Note('g')
        >>> n2 = note.Note('g#')
        >>> s.insert(10, n1)
        >>> s.insert(5, n2)
        >>> s.remove(n1)
        >>> len(s)
        1
        '''
        iMatch = self.indexList(target, firstMatchOnly=firstMatchOnly)
        match = []
        for i in iMatch:
            # remove from stream with pop with index
            match.append(self._elements.pop(i))
        # after removing, need to remove self from locations reference 
        # and from parent reference, if set; this is taken care of with the 
        # Music21Object method
        for obj in match:
            obj.removeLocation(self)


    def pop(self, index):
        '''Return and remove the object found at the user-specified index value. Index values are those found in `elements` and are not necessary offset order. 

        >>> a = Stream()
        >>> a.repeatInsert(note.Note("C"), range(10))
        >>> junk = a.pop(0)
        >>> len(a)
        9
        '''
        post = self._elements.pop(index)
        self._elementsChanged()

        # remove self from locations here only if
        # there are no further locations
        post.removeLocation(self)

        return post




    def __deepcopy__(self, memo=None):
        '''This produces a new, independent object.
        '''
        #environLocal.printDebug(['Stream calling __deepcopy__', self])

        new = self.__class__()
        old = self
        for name in self.__dict__.keys():

            if name.startswith('__'):
                continue
           
            part = getattr(self, name)
                    
            # all subclasses of Music21Object that define their own
            # __deepcopy__ methods must be sure to not try to copy parent
            if name == '_currentParent':
                newValue = self.parent # keep a reference, not a deepcopy
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
                    # this will work for all with __deepcopy___
                    newElement = copy.deepcopy(e, memo)
                    # get the old offset from the parent Stream     
                    # user here to provide new offset
                    new.insert(e.getOffsetBySite(old), newElement, 
                               ignoreSort = True)
                # the elements, formerly had their stream as parent     
                # they will still have that site in locations
                # need to set new stream as parent 
                
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
                
        return new


    def _addElementPreProcess(self, element):
        '''Before adding an element, this method provides important checks to the element.

        Used by both insert() and append()
        '''
        # using id() here b/c we do not want to get __eq__ comparisons
        if id(element) == id(self): # cannot add this Stream into itself
            raise StreamException("this Stream cannot be contained within itself")

        # temporarily removed

        # if we do not purge locations here, we may have ids() for 
        # Stream that no longer exist stored in the locations entry
        #element.purgeLocations()

#         if id(self) in element.getSiteIds():
#             environLocal.printDebug(['element site ids', element, element.getSiteIds()])
#             environLocal.printDebug(['self id', self, id(self)])
#             #self.show('t')
#             raise StreamException('this element (%s, id %s) already has a location for this container (%s, id %s)' % (element, id(element), self, id(self)))


    def insert(self, offsetOrItemOrList, itemOrNone = None, ignoreSort = False):
        '''
        Inserts an item(s) at the given offset(s).  if ignoreSort is True then the inserting does not
        change whether the stream is sorted or not (much faster if you're going to be inserting dozens
        of items that don't change the sort status)
        
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
        
        In single argument form list a list of alternating offsets and items, inserts the items
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
        
        Raise an error if offset is not a number
        >>> Stream().insert("l","g")
        Traceback (most recent call last):
        StreamException: ...
        
        '''
        if itemOrNone is not None:
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
        else:
            item = offsetOrItemOrList
            offset = item.offset

        if not common.isNum(offset):
            raise StreamException("offset %s must be a number", offset)

        # if not a Music21Object, embed
        if not isinstance(item, music21.Music21Object): 
            element = music21.ElementWrapper(item)
        else:
            element = item

        self._addElementPreProcess(element)

        offset = float(offset)
        element.addLocation(self, offset)
        # need to explicitly set the parent of the element
        element.parent = self 
        # element.addLocationAndParent(offset, self)

        if ignoreSort is False:
            if self.isSorted is True and self.highestTime <= offset:
                storeSorted = True
            else:
                storeSorted = False

        self._elements.append(element)  # could also do self.elements = self.elements + [element]
        self._elementsChanged()         # maybe much slower?

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
        
        '''

        highestTime = self.highestTime
        if not common.isListLike(others):
            # back into a list for list processing if single
            others = [others]

        for item in others:    
    
            # if not an element, embed
            if not isinstance(item, music21.Music21Object): 
                element = music21.ElementWrapper(item)
            else:
                element = item
    
            self._addElementPreProcess(element)
    
            element.addLocation(self, highestTime)
            # need to explicitly set the parent of the element
            element.parent = self 
            self._elements.append(element)  

            # this should look to the contained object duration
            if (hasattr(element, "duration") and 
                hasattr(element.duration, "quarterLength")):
                highestTime += element.duration.quarterLength

        ## does not change sorted state
        storeSorted = self.isSorted    
        self._elementsChanged()         
        self.isSorted = storeSorted


    def insertAtNativeOffset(self, item):
        '''
        inserts the item at the offset that was defined before the item was inserted into a stream
        (that is item.getOffsetBySite(None); in fact, the entire code is self.insert(item.getOffsetBySite(None), item)

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

    def isClass(self, className):
        '''Returns true if the Stream or Stream Subclass is a particular class or subclasses that class.

        Used by getElementsByClass in Stream

        >>> a = Stream()
        >>> a.isClass(note.Note)
        False
        >>> a.isClass(Stream)
        True
        >>> b = Measure()
        >>> b.isClass(Measure)
        True
        >>> b.isClass(Stream)
        True
        '''
        ## same as Music21Object.isClass, not ElementWrapper.isClass
        if isinstance(self, className):
            return True
        else:
            return False


    #---------------------------------------------------------------------------
    # searching and replacing routines

    def replace(self, target, replacement, firstMatchOnly=False,
                 allTargetSites=True):
        '''Given a `target` object, replace all references of that object with references to the supplied `replacement` object.

        If `allTargetSites` is True, all sites that have a reference for the relacement will be similarly changed. This is useful altering both a flat and nested representation.         
        '''
        # get all indices in this Stream that match
        iMatch = self.indexList(target, firstMatchOnly=firstMatchOnly)
        for i in iMatch:
            # replace all index target with the replacement
            self._elements[i] = replacement
            # place the replacement at the old objects offset for this site

            # NOTE: an alternative way to do this would be to look at all the 
            # sites defined by the target and add them to the replacement
            # this would not put them in those locations elements, however

            replacement.addLocation(self, target.getOffsetBySite(self))
            # remove this location from old; this will also adjust the parent
            # assignment if necessary
            target.removeLocation(self)

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

        Note: plots requires matplotib to be installed.
    
        Plot method can be specified as a second argument or by the `method` keyword. Available plots include the following:
    
        pitchSpace (:class:`~music21.graph.PlotHistogramPitchSpace`)
        pitchClass (:class:`~music21.graph.PlotHistogramPitchClass`)
        quarterLength (:class:`~music21.graph.PlotHistogramQuarterLength`)
    
        scatterPitchSpaceQuarterLength (:class:`~music21.graph.PlotScatterPitchSpaceQuarterLength`)
        scatterPitchClassQuarterLength (:class:`~music21.graph.PlotScatterPitchClassQuarterLength`)
        scatterPitchClassOffset (':class:`~graph.PlotScatterPitchClassOffset`)
    
        pitchClassOffset (:class:`~music21.graph.PlotHorizontalBarPitchSpaceOffset`)
        pitchSpaceOffset (:class:`~music21.graph.PlotHorizontalBarPitchClassOffset`)
    
        pitchSpaceQuarterLengthCount (:class:`~music21.graph.PlotScatterWeightedPitchSpaceQuarterLength`)
        pitchClassQuarterLengthCount (:class:`~music21.graph.PlotScatterWeigthedPitchClassQuarterLength`)

        3DPitchSpaceQuarterLengthCount (:class:`~music21.graph.Plot3DBarsPitchSpaceQuarterLength`)

        >>> a = Stream()
        >>> n = note.Note()
        >>> a.append(n)
        >>> a.plot('pitchspaceoffset', doneAction=None)
        '''
        # import is here to avoid import of matplotlib problems
        from music21 import graph
        # first ordered arg can be method type
        graph.plotStream(self, *args, **keywords)


    #---------------------------------------------------------------------------
    # methods that act on individual elements without requiring 
    # @ _elementsChanged to fire

    def addGroupForElements(self, group, classFilter=None):
        '''
        Add the group to the groups attribute of all elements.
        if classFilter is set then only those elements whose objects
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
        for myElement in self.elements:
            if classFilter is None:
                myElement.groups.append(group)
            else:
                if hasattr(myElement, "elements"): # stream type
                    if isinstance(myElement, classFilter):
                        myElement.groups.append(group)
                elif hasattr(myElement, "obj"): # element type
                    if isinstance(myElement.obj, classFilter):
                        myElement.groups.append(group)
                else: # music21 type
                    if isinstance(myElement, classFilter):
                        myElement.groups.append(group)


    #---------------------------------------------------------------------------
    # getElementsByX(self): anything that returns a collection of Elements should return a Stream

    def getElementsByClass(self, classFilterList):
        '''Return a list of all Elements that match the className.
        
        >>> a = Stream()
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
        >>> b = Stream()
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
        '''
        # should probably be whatever class the caller is
        found = Stream()

        # much faster in the most common case than calling common.isListLike
        if not isinstance(classFilterList, list):
            if not isinstance(classFilterList, tuple):
                classFilterList = [classFilterList]

        # appendedAlready fixes bug where if an element matches two 
        # classes it was appendedTwice
        for myEl in self:
            appendedAlready = False
            for myCl in classFilterList:
                if appendedAlready is False and myEl.isClass(myCl):
                    appendedAlready = True
                    found.insert(myEl.getOffsetBySite(self), myEl, ignoreSort = True)
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

        returnStream = Stream()
        for myEl in self:
            for myGrp in groupFilterList:
                if hasattr(myEl, "groups") and myGrp in myEl.groups:
                    returnStream.insert(myEl.getOffsetBySite(self),
                                                myEl, ignoreSort = True)
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
        for element in self:
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
        KeyError: ...

        >>> s2.flat.getOffsetByElement(n1)
        20.0
        >>> s2.flat.getOffsetByElement(n2)
        110.0
        '''
        post = None
        for element in self:
            if element == obj:
                post = obj.getOffsetBySite(self)
                break
        return post

    def getElementById(self, id, classFilter=None):
        '''Returns the first encountered element for a given id. Return None
        if no match

        >>> e = 'test'
        >>> a = Stream()
        >>> a.insert(0, music21.ElementWrapper(e))
        >>> a[0].id = 'green'
        >>> None == a.getElementById(3)
        True
        >>> a.getElementById('green').id
        'green'
        '''
        for element in self.elements:
            if element.id == id:
                if classFilter is not None:
                    if element.isClass(classFilter):
                        return element
                    else:
                        continue # id may match but not proper class
                else:
                    return element
        return None

    def getElementsByOffset(self, offsetStart, offsetEnd = None,
                    includeEndBoundary = True, mustFinishInSpan = False, mustBeginInSpan = True):
        '''Return a Stream of all Elements that are found at a certain offset or within a certain offset time range, specified as start and stop values.

        If mustFinishInSpan is True than an event that begins between offsetStart and offsetEnd but which ends after offsetEnd will not be included.  For instance, a half note at offset 2.0 will be found in.

        The includeEndBoundary option determines if an element begun just at offsetEnd should be included.  Setting includeEndBoundary to False at the same time as mustFinishInSpan is set to True is probably NOT what you ever want to do.
        
        Setting mustBeginInSpan to False is a good way of finding 
        

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
        
        found = Stream()

        #(offset, priority, dur, element). 
        for element in self:
            match = False
            offset = element.offset

            dur = element.duration
            if dur is None or mustFinishInSpan is False:
                elementEnd = offset
            else:
                elementEnd = offset + dur.quarterLength

            if mustBeginInSpan is False and dur is not None:
                elementStart = offset + dur.quarterLength
            else:
                elementStart = offset

            if includeEndBoundary is True and mustBeginInSpan is True and \
                elementStart >= offsetStart and elementEnd <= offsetEnd:
                    match = True
            elif includeEndBoundary is True and mustBeginInSpan is False and \
                elementStart > offsetStart and elementEnd <= offsetEnd:
                    match = True
            elif includeEndBoundary is False and mustBeginInSpan is True and \
                elementStart >= offsetStart and elementEnd < offsetEnd:
                    match = True
            elif includeEndBoundary is False and mustBeginInSpan is False and \
                elementStart > offsetStart and elementEnd < offsetEnd:
                    match = True
            else: # 
                match = False

            if match is True:
                found.insert(element)
        return found


    def getElementAtOrBefore(self, offset, classList=None):
        '''Given an offset, find the element at this offset, or with the offset
        less than and nearest to.

        Return one element or None if no elements are at or preceded by this 
        offset. 

        >>> a = Stream()

        >>> x = music21.Music21Object()
        >>> x.id = 'x'
        >>> y = music21.Music21Object()
        >>> y.id = 'y'
        >>> z = music21.Music21Object()
        >>> z.id = 'z'

        >>> a.insert(20, x)
        >>> a.insert(10, y)
        >>> a.insert( 0, z)

        >>> b = a.getElementAtOrBefore(21)
        >>> b.offset, b.id
        (20.0, 'x')

        >>> b = a.getElementAtOrBefore(19)
        >>> b.offset, b.id
        (10.0, 'y')

        >>> b = a.getElementAtOrBefore(0)
        >>> b.offset, b.id
        (0.0, 'z')
        >>> b = a.getElementAtOrBefore(0.1)
        >>> b.offset, b.id
        (0.0, 'z')
        >>> c = a.getElementAtOrBefore(0.1, [music21.Music21Object])
        >>> c.offset, c.id
        (0.0, 'z')


        OMIT_FROM_DOCS
        TODO: include sort order for concurrent matches?
        '''
        candidates = []
        nearestTrailSpan = offset # start with max time
        for element in self:
            if classList != None:
                match = False
                for cl in classList:
                    if isinstance(element, cl):
                        match = True
                        break
                if not match:
                    continue
            span = offset - element.offset
            #environLocal.printDebug(['element span check', span])
            if span < 0: # the element is after this offset
                continue
            elif span == 0: 
                candidates.append((span, element))
                nearestTrailSpan = span
            else:
                if span <= nearestTrailSpan: # this may be better than the best
                    candidates.append((span, element))
                    nearestTrailSpan = span
                else:
                    continue
        #environLocal.printDebug(['getElementAtOrBefore(), element candidates', candidates])
        if len(candidates) > 0:
            candidates.sort()
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
            elPos = self.index(element)
        except ValueError:
            raise StreamException("Could not find element in index")

       
        if classList is None:
            if elPos == len(self.elements) - 1:
                return None
            else:
                return self.elements[elPos + 1]
        else:
            for i in range(elPos + 1, len(self.elements)):
                for cl in classList:
                    if isinstance(self.elements[i], cl): 
                        return self.elements[i]
            return None
        
        raise Exception("not yet implemented")


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

    def getMeasureRange(self, numberStart, numberEnd, 
        collect=[clef.Clef, meter.TimeSignature, 
        instrument.Instrument, key.KeySignature]):
        '''Get a region of Measures based on a start and end Measure number, were the boundary numbers are both included. That is, a request for measures 4 through 10 will return 7 Measures, numbers 4 through 10.

        Additionally, any number of associated classes can be gathered as well. Associated classes are the last found class relevant to this Stream or Part.  

        >>> from music21 import corpus
        >>> a = corpus.parseWork('bach/bwv324.xml')
        >>> b = a[0].getMeasureRange(4,6)
        >>> len(b)
        3

        OMIT_FROM_DOCS
        TODO: this probably needs to deepcopy the new first measure.
        '''
        
        # create a dictionary of measure number, list of Meaures
        # there may be more than one Measure with the same Measure number
        mapRaw = {}
        mNumbersUnique = [] # store just the numbers
        for m in self.getMeasures():
            # mId is a tuple of measure nmber and any suffix
            mId = (m.measureNumber, m.measureNumberSuffix)
            # store unique measure numbers for reference
            if m.measureNumber not in mNumbersUnique:
                mNumbersUnique.append(m.measureNumber)
            if mId not in mapRaw.keys():
                mapRaw[mId] = [] # use a list
            # these will be in order by measure number
            # there may be multiple None and/or 0 measure numbers
            mapRaw[mId].append(m)

        #environLocal.printDebug(['mapRaw', mapRaw])

        # if measure numbers are not defined, we should just count them 
        # in order, starting from 1
        if len(mNumbersUnique) == 1:
            mapCooked = {}  
            # only one key but we do not know what it is
            i = 1
            for number, suffix in mapRaw.keys():
                for m in mapRaw[(number, suffix)]:
                    # expecting a lost of measures
                    mapCooked[(i, None)] = [m]
                    i += 1
        else:
            mapCooked = mapRaw
        #environLocal.printDebug(['mapCooked', mapCooked])

        post = Stream()
        startOffset = None # set with the first measure
        startMeasure = None # store for adding other objects
        # get requested range
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
                    startOffset = m.getOffsetBySite(self)
                    # not sure if a deepcopy is necessary; this does not yet work
                    #startMeasure = copy.deepcopy(m)
                    startMeasure = m

                    # this works here, but not after appending!
                    #found = startMeasure.getContextByClass(clef.Clef)
                    #environLocal.printDebug(['early clef search', found])

                oldOffset = m.getOffsetBySite(self)
                # subtract the offset of the first measure
                # this will be zero in the first usage
                newOffset = oldOffset - startOffset
                post.insert(newOffset, m)

                #environLocal.printDebug(['old/new offset', oldOffset, newOffset])

        # manipulate startMeasure to add desired context objects
        for className in collect:
            # first, see if it is in this Measure
            found = startMeasure.getElementsByClass(className)
            if len(found) > 0:
                continue # already have one on this measure

            found = startMeasure.getContextByClass(className)
            if found != None:
                startMeasure.insert(0, found)
            else:
                environLocal.printDebug(['cannot find requested class in stream:', className])

        return post


    def getMeasure(self, measureNumber, 
        collect=[clef.Clef, meter.TimeSignature, 
        instrument.Instrument, key.KeySignature]):
        '''Given a measure number, return a single :class:`~music21.stream.Measure` object if the Measure number exists, otherwise return None.

        This method is distinguished from :meth:`~music21.stream.Stream.getMeasureRange` in that this method returns a single Measure object, not a Stream containing one or more Measure objects.

        >>> from music21 import corpus
        >>> a = corpus.parseWork('bach/bwv324.xml')
        >>> a[0].getMeasure(3)
        <music21.stream.Measure 3 offset=0.0>
        '''
        # we must be able to obtain a measure from this (not a flat) 
        # representation (e.g., this is a Stream or Part, not a Score)
        if len(self.getElementsByClass(Measure)) >= 1:
            s = self.getMeasureRange(measureNumber, measureNumber, collect=collect)
            if len(s) == 0:
                return None
            else:
                return s.getElementsByClass(Measure)[0]
        else:   
            return None



    def getMeasures(self):
        '''Return all :class:`~music21.stream.Measure` objects in a Stream()
        '''
        return self.getElementsByClass(Measure)

    measures = property(getMeasures)

    def measureOffsetMap(self, classFilterList=None):
        '''If this Stream contains Measures, provide a dictionary where keys are offsets and values are a list of references to one or more Measures that start at that offset. The offset values is always in the frame of the calling Stream (self).

        The `classFilterList` argument can be a list of classes used to find Measures. A default of None uses Measure. 

        >>> from music21 import corpus
        >>> a = corpus.parseWork('bach/bwv324.xml')
        >>> sorted(a[0].measureOffsetMap().keys())
        [0.0, 4.0, 8.0, 12.0, 16.0, 20.0, 24.0, 28.0, 32.0]

        OMIT_FROM_DOCS
        see important examples in testMeasureOffsetMap() andtestMeasureOffsetMapPostTie()
        '''
        if classFilterList == None:
            classFilterList = [Measure]
        if not common.isListLike(classFilterList):
            classFilterList = [classFilterList]

        #environLocal.printDebug([classFilterList])
        map = {}
        # first, try to get measures
        # this works best of this is a Part or Score
        if Measure in classFilterList:
            for m in self.getMeasures():
                offset = m.getOffsetBySite(self)
                if offset not in map.keys():
                    map[offset] = []
                # there may be more than one measure at the same offset
                map[offset].append(m)

        # try other classes
        for className in classFilterList:
            if className == Measure: # do not redo
                continue
            for e in self.getElementsByClass(className):
                #environLocal.printDebug([e])
                m = e.getContextByClass(Measure)
                if m == None: 
                    continue
                # assuming that the offset returns the proper offset context
                # this is, the current offset may not be the stream that 
                # contains this Measure; its current parent
                offset = m.offset
                if offset not in map.keys():
                    map[offset] = []
                if m not in map[offset]:
                    map[offset].append(m)
        return map

    def getTimeSignatures(self):
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
        post = self.getElementsByClass(meter.TimeSignature)
    
        # get a default and/or place default at zero if nothing at zero
        if len(post) == 0 or post[0].offset > 0: 
            ts = meter.TimeSignature()
            ts.load('%s/%s' % (defaults.meterNumerator, 
                               defaults.meterDenominatorBeatType))
            #ts.numerator = defaults.meterNumerator
            #ts.denominator = defaults.meterDenominatorBeatType
            post.insert(0, ts)
        return post
        

    def getInstrument(self, searchParent=True):
        '''Search this stream or parent streams for :class:`~music21.instrument.Instrument` objects, otherwise 
        return a default

        >>> a = Stream()
        >>> b = a.getInstrument()
        '''
        #environLocal.printDebug(['searching for instrument, called from:', 
        #                        self])
        #TODO: Rename: getInstruments, and return a Stream of instruments
        #for cases when there is more than one instrument

        instObj = None
        post = self.getElementsByClass(instrument.Instrument)
        if len(post) > 0:
            #environLocal.printDebug(['found local instrument:', post[0]])
            instObj = post[0] # get first
        else:
            if searchParent:
                if isinstance(self.parent, Stream) and self.parent != self:
                    #environLocal.printDebug(['searching parent Stream', 
                    #    self, self.parent])
                    instObj = self.parent.getInstrument(
                              searchParent=searchParent) 

        # if still not defined, get default
        if instObj is None:
            instObj = instrument.Instrument()
            instObj.partId = defaults.partId # give a default id
            instObj.partName = defaults.partName # give a default id
        return instObj



    def bestClef(self, allowTreble8vb = False):
        '''Returns the clef that is the best fit for notes and chords found in thisStream.

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

        def findHeight(thisPitch):
            height = thisPitch.diatonicNoteNum
            if thisPitch.diatonicNoteNum > 33: # a4
                height += 3 # bonus
            elif thisPitch.diatonicNoteNum < 24: # Bass F or lower
                height += -3 # bonus
            return height
        
        for thisNote in notes:
            if thisNote.isRest:
                pass
            elif thisNote.isNote:
                totalNotes  += 1
                totalHeight += findHeight(thisNote.pitch)
            elif thisNote.isChord:
                for thisPitch in thisNote.pitches:
                    totalNotes += 1
                    totalHeight += findHeight(thisPitch)
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


    def getClefs(self, searchParent=True, searchContext=True):
        '''Collect all :class:`~music21.clef.Clef` objects in this Stream in a new Stream. Optionally search the parent stream and/or contexts. 

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
        # this may not be useful unless a stream is flat
        post = self.getElementsByClass(clef.Clef)
        #environLocal.printDebug(['getClefs(); count of local', len(post), post])

# do not do this: this returns the default before the context search is complete
#         if len(post) == 0 and searchParent:
#             if isinstance(self.parent, Stream) and self.parent != self:
#                 environLocal.printDebug(['getClefs() searching parent Stream', 
#                     self, self.parent])
#                 post = self.parent.getClefs(searchParent=searchParent)  
       
        if len(post) == 0 and searchContext:
            # returns a single value
            post = Stream()
            obj = self.getContextByClass(clef.Clef)
            #environLocal.printDebug(['getClefs(): searching contexts: results', obj])
            if obj != None:
                post.append(obj)

        # get a default and/or place default at zero if nothing at zero
        if len(post) == 0 or post[0].offset > 0: 
            environLocal.printDebug(['getClefs(): using bestClef()'])
            post.insert(0, self.bestClef())
        return post



    #--------------------------------------------------------------------------
    # offset manipulation

    def shiftElements(self, offset):
        '''Add offset value to every offset of contained Elements.

        >>> a = Stream()
        >>> a.repeatInsert(note.Note("C"), range(0,10))
        >>> a.shiftElements(30)
        >>> a.lowestOffset
        30.0
        >>> a.shiftElements(-10)
        >>> a.lowestOffset
        20.0
        '''
        for e in self:
            e._definedContexts.setOffsetBySite(self, 
                e._definedContexts.getOffsetBySite(self) + offset)
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
        '''Given an object, create many DEEPcopies at the positions specified by 
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
                       maxBefore = None, maxAfter = None):
        r'''
        extracts elements around the given element within (before) quarter notes and (after) quarter notes
        (default 4)
                
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
        '{5.0} <music21.note.Note C>\n{6.0} <music21.note.Note B->\n{8.0} <music21.note.Note C>'


        OMIT_FROM_DOCS
        TODO: maxBefore -- maximum number of elements to return before; etc.

        note: this probably should be renamed, as we use Context in a specail way. Perhaps better is extractNeighbors?
        
        '''
       
        display = Stream()
        found = None
        foundOffset = 0
        foundEnd = 0 
        for i in range(0, len(self.elements)):
            b = self.elements[i]
            if b.id is not None or searchElement.id is not None:
                if b.id == searchElement.id:
                    found = i
                    foundOffset = self.elements[i].getOffsetBySite(self)
                    foundEnd    = foundOffset + self.elements[i].duration.quarterLength                        
            else:
                if b is searchElement or (hasattr(b, "obj") and b.obj is searchElement):
                    found = i
                    foundOffset = self.elements[i].getOffsetBySite(self)
                    foundEnd    = foundOffset + self.elements[i].duration.quarterLength
        if found is None:
            raise StreamException("Could not find the element in the stream")

        for thisElement in self:
            thisElOffset = thisElement.getOffsetBySite(self)
            if (thisElOffset >= foundOffset - before and
                   thisElOffset < foundEnd + after):
                display.insert(thisElOffset, thisElement)

        return display


    #---------------------------------------------------------------------------
    # transformations of self that return a new Stream

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
        a = Stream()
        b = Stream()
        for element in self.getElementsByClass(objName):
            if fx(element):
                a.insert(element)
            else:
                b.insert(element)
        return a, b
            


    def makeMeasures(self, meterStream=None, refStream=None):
        '''Take a stream and partition all elements into measures based on 
        one or more TimeSignature defined within the stream. If no TimeSignatures are defined, a default is used.

        This always creates a new stream with Measures, though objects are not
        copied from self stream. 
    
        If a meterStream is provided, this is used instead of the meterStream
        found in the Stream.
    
        If a refStream is provided, this is used to provide max offset values, necessary to fill empty rests and similar.
        
        >>> sSrc = Stream()
        >>> sSrc.repeatAppend(note.Rest(), 3)
        >>> sMeasures = sSrc.makeMeasures()
        >>> len(sMeasures.measures)
        1
        >>> sMeasures[0].timeSignature
        <music21.meter.TimeSignature 4/4>

        >>> sSrc.insert(0.0, meter.TimeSignature('3/4'))
        >>> sMeasures = sSrc.makeMeasures()
        >>> sMeasures[0].timeSignature
        <music21.meter.TimeSignature 3/4>
            
        >>> sSrc = Stream()
        >>> n = note.Note()
        >>> sSrc.repeatAppend(n, 10)
        >>> sSrc.repeatInsert(n, [x+.5 for x in range(10)])
        >>> sMeasures = sSrc.makeMeasures()
        >>> len(sMeasures.measures)
        3
        >>> sMeasures[0].timeSignature
        <music21.meter.TimeSignature 4/4>
        '''
        #environLocal.printDebug(['calling Stream.makeMeasures()'])

        # the srcObj shold not be modified or chagned
        # removed element copyig below and now making a deepcopy of entire stream
        # must take a flat representation, as we need to be able to 
        # position components, and sub-streams might hide elements that
        # should be contained


        #environLocal.printDebug(['makeMeasures(): first clef found before copying and flattening', self.getClefs()[0]])

        # TODO: make inPlace an option
        srcObj = copy.deepcopy(self.flat)
        # may need to look in parent if no time signatures are found
        if meterStream is None:
            meterStream = srcObj.getTimeSignatures()

        # get a clef for the entire stream; this will use bestClef
        # presently, this only gets the first clef
        # may need to store a clefStream and access changes in clefs
        # as is done with meterStream
        clefStream = srcObj.getClefs()
        clefObj = clefStream[0]

        #environLocal.printDebug(['makeMeasures(): first clef found after copying and flattening', clefObj])
    
        # for each element in stream, need to find max and min offset
        # assume that flat/sorted options will be set before procesing
        offsetMap = [] # list of start, start+dur, element
        for e in srcObj:
            if hasattr(e, 'duration') and e.duration is not None:
                dur = e.duration.quarterLength
            else:
                dur = 0 
            # NOTE: rounding here may cause secondary problems
            offset = round(e.getOffsetBySite(srcObj), 8)
            # NOTE: used to make a copy.copy of elements here; 
            # this is not necssary b/c making deepcopy of entire Stream
            # changed on 4/16/2010
            offsetMap.append([offset, offset + dur, e])
            #offsetMap.append([offset, offset + dur, copy.copy(e)])
    
        #environLocal.printDebug(['makesMeasures()', offsetMap])    
    
        #offsetMap.sort() not necessary; just get min and max
        oMin = min([start for start, end, e in offsetMap])
        oMax = max([end for start, end, e in offsetMap])
    
        # this should not happen, but just in case
        if not common.almostEquals(oMax, srcObj.highestTime):
            raise StreamException('mismatch between oMax and highestTime (%s, %s)' % (oMax, srcObj.highestTime))
        #environLocal.printDebug(['oMin, oMax', oMin, oMax])
    
        # if a ref stream is provided, get highst time from there
        # only if it is greater thant the highest time yet encountered
        if refStream is not None:
            if refStream.highestTime > oMax:
                oMax = refStream.highestTime
    
        # create a stream of measures to contain the offsets range defined
        # create as many measures as needed to fit in oMax
        post = Stream()
        o = 0 # initial position of first measure is assumed to be zero
        measureCount = 0
        lastTimeSignature = None
        while True:    
            m = Measure()
            m.measureNumber = measureCount + 1
            # get active time signature at this offset
            # make a copy and it to the meter
            thisTimeSignature = meterStream.getElementAtOrBefore(o)
            if thisTimeSignature != lastTimeSignature:
                lastTimeSignature = meterStream.getElementAtOrBefore(o)
                m.timeSignature = deepcopy(thisTimeSignature)
                #environLocal.printDebug(['assigned time sig', m.timeSignature])

            # only add a clef for the first measure when automatically 
            # creating Measures; this clef is from getClefs, called above
            if measureCount == 0: 
                m.clef = clefObj
                #environLocal.printDebug(['assigned clef to measure', measureCount, m.clef])    

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
        for start, end, e in offsetMap:
            # iterate through all measures 
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
                raise StreamException('cannot place element with start/end %s/%s within any measures' % (start, end))
            # find offset in the temporal context of this measure
            # i is the index of the measure that this element starts at
            # mStart, mEnd are correct
            oNew = start - mStart # remove measure offset from element offset
            # insert element at this offset in the measure
            # not copying elements here!
            # here, we have the correct measure from above
            #environLocal.printDebug(['measure placement', mStart, oNew, e])

            # in the case of a Clef, and possible other measure attributes, 
            # the element may have already been placed in this measure
            #environLocal.printDebug(['compare e, clef', e, m.clef])
            if m.clef == e:
                continue

            m.insert(oNew, e)

        return post # returns a new stream populated w/ new measure streams


    def makeRests(self, refStream=None, inPlace=True):
        '''Given a streamObj with an  with an offset not equal to zero, 
        fill with one Rest preeceding this offset. 
    
        If refStream is provided, this is used to get min and max offsets. Rests 
        will be added to fill all time defined within refStream.
        
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
        TODO: rename fillRests() or something else.
        TODO: if inPlace == True, this should return None
        '''
        #environLocal.printDebug(['calling makeRests'])
        if not inPlace: # make a copy
            returnObj = deepcopy(self)
        else:
            returnObj = self
    
        oLow = returnObj.lowestOffset
        oHigh = returnObj.highestTime
        if refStream is not None:
            oLowTarget = refStream.lowestOffset
            oHighTarget = refStream.highestTime
            environLocal.printDebug(['refStream used in makeRests', oLowTarget, oHighTarget, len(refStream)])
        else:
            oLowTarget = 0
            oHighTarget = returnObj.highestTime
            
        qLen = oLow - oLowTarget
        if qLen > 0:
            r = note.Rest()
            r.duration.quarterLength = qLen
            returnObj.insert(oLowTarget, r)
    
        qLen = oHighTarget - oHigh
        if qLen > 0:
            r = note.Rest()
            r.duration.quarterLength = qLen
            returnObj.insert(oHigh, r)
    
        # do not need to sort, can concatenate without sorting
        # post = streamLead + returnObj 
        return returnObj.sorted


    def makeTies(self, meterStream=None, inPlace=True, 
        displayTiedAccidentals=False):
        '''Given a stream containing measures, examine each element in the stream 
        if the elements duration extends beyond the measures bound, create a tied  entity.
    
        Edits the current stream in-place by default.  This can be changed by setting the inPlace keyword to false
            
        configure ".previous" and ".next" attributes
    
        >>> d = Stream()
        >>> n = note.Note()
        >>> n.quarterLength = 12
        >>> d.repeatAppend(n, 10)
        >>> d.repeatInsert(n, [x+.5 for x in range(10)])
        >>> x = d.makeMeasures()
        >>> x = x.makeTies()
    
        OMIT_FROM_DOCS
        TODO: take a list of clases to act as filter on what elements are tied.
        '''
        #environLocal.printDebug(['calling Stream.makeTies()'])
        if not inPlace: # make a copy
            returnObj = deepcopy(self)
        else:
            returnObj = self
        if len(returnObj) == 0:
            raise StreamException('cannot process an empty stream')        
    
        # get measures from this stream
        measureStream = returnObj.getMeasures()
        if len(measureStream) == 0:
            raise StreamException('cannot process a stream without measures')        
    
        environLocal.printDebug(['makeTies() processing measureStream, length', measureStream, len(measureStream)])

        # may need to look in parent if no time signatures are found
        if meterStream is None:
            meterStream = returnObj.getTimeSignatures()
    
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

            # get a next measure; we may not need it, but have it ready
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
                mNext.measureNumber = m.measureNumber + 1
                mNextAdd = True # new measure, needs to be appended
    
            #environLocal.printDebug(['makeTies() dealing with measure', m, 'mNextAdd', mNextAdd])
            # for each measure, go through each element and see if its
            # duraton fits in the bar that contains it
            mStart, mEnd = 0, lastTimeSignature.barDuration.quarterLength
            for e in m:
                #environLocal.printDebug(['Stream.makeTies() iterating over elements in measure', m, e])

                if hasattr(e, 'duration') and e.duration is not None:
                    # check to see if duration is within Measure
                    eoffset = e.getOffsetBySite(m)
                    eEnd = eoffset + e.duration.quarterLength
                    # assume end can be at boundary of end of measure
                    if eEnd > mEnd:
                        if eoffset >= mEnd:
                            raise StreamException('element (%s) has offset %s within a measure that ends at offset %s' % (e, eoffset, mEnd))  
    
                        # note: cannot use GeneralNote.splitNoteAtPoint b/c
                        # we are not assuming that these are notes, only elements
    
                        qLenBegin = mEnd - eoffset
                        #print 'e.offset, mEnd, qLenBegin', e.offset, mEnd, qLenBegin
                        qLenRemain = e.duration.quarterLength - qLenBegin
                        # modify existing duration
                        e.duration.quarterLength = qLenBegin
                        # create and place new element
                        eRemain = deepcopy(e)
                        eRemain.duration.quarterLength = qLenRemain

                        # set ties
                        if (e.isClass(note.Note) or e.isClass(note.Unpitched)):
                            #environLocal.printDebug(['tieing in makeTies', e])
                            e.tie = note.Tie('start')
                            # we can set eRamain to be a stop on this iteration
                            # if it needs to be tied to something on next
                            # iteration, the tie object will be re-created
                            eRemain.tie = note.Tie('stop')
    
                        # hide accidentals on tied notes where previous note
                        # had an accidental that was shown
                        if hasattr(e, 'accidental') and e.accidental != None:
                            if not displayTiedAccidentals: # if False
                                if (e.accidental.displayType not in     
                                    ['even-tied']):
                                    eRemain.accidental.displayStatus = False
                            else: # display tied accidentals
                                eRemain.accidental.displayType = 'even-tied'
                                eRemain.accidental.displayStatus = True


                        # TODO: not sure this is the best way to make sure
                        # eRamin comes first 
                        # NOTE: must set parent here b/c otherwise offset
                        # setting is for the wrong location
                        eRemain.parent = mNext # manually set parent
                        eRemain.offset = 0
                        mNext.elements = [eRemain] + mNext.elements

                        # alternative approach (same slowness)
                        #mNext.insert(0, eRemain)
                        #mNext = mNext.sorted
    
                        # we are not sure that this element fits 
                        # completely in the next measure, thus, need to continue
                        # processing each measure
                        if mNextAdd:
                            environLocal.printDebug(['makeTies() inserting mNext into returnObj', mNext])
                            returnObj.insert(mNext.offset, mNext)
            mCount += 1

        return returnObj
    

    def makeBeams(self, inPlace=True):
        '''Return a new measure with beams applied to all notes. 

        if inPlace is false, this creates a new, independent copy of the source.

        In the process of making Beams, this method also updates tuplet types. this is destructive and thus changes an attribute of Durations in Notes.

        >>> aMeasure = Measure()
        >>> aMeasure.timeSignature = meter.TimeSignature('4/4')
        >>> aNote = note.Note()
        >>> aNote.quarterLength = .25
        >>> aMeasure.repeatAppend(aNote,16)
        >>> bMeasure = aMeasure.makeBeams()

        OMIT_FROM_DOCS
        TODO: inPlace=False does not work in many cases

        '''

        #environLocal.printDebug(['calling Stream.makeBeams()'])

        if not inPlace: # make a copy
            returnObj = deepcopy(self)
        else:
            returnObj = self

        if self.isClass(Measure):
            mColl = [] # store a list of measures for processing
            mColl.append(returnObj)
        elif len(self.getMeasures()) > 0:
            mColl = returnObj.getMeasures() # a stream of measures
        else:
            raise StreamException('cannot process a stream that neither is a Measure nor has Measures')        

        lastTimeSignature = None
        for m in mColl:
            if m.timeSignature is not None:
                lastTimeSignature = m.timeSignature
            if lastTimeSignature is None:
                raise StreamException('cannot proces beams in a Measure without a time signature')
    
            # environLocal.printDebug(['beaming with ts', ts])
            noteStream = m.notes
            if len(noteStream) <= 1: 
                continue # nothing to beam
            durList = []
            for n in noteStream:
                durList.append(n.duration)
            # getBeams can take a list of Durations; however, this cannot
            # distinguish a Note from a Rest; thus, we can submit a flat 
            # stream of note or note-like entities; will return
            # the saem lost of beam objects
            beamsList = lastTimeSignature.getBeams(noteStream)
            for i in range(len(noteStream)):
                # this may try to assign a beam to a Rest
                noteStream[i].beams = beamsList[i]
            # apply tuple types in place
            duration.updateTupletType(durList)

        return returnObj



    def makeAccidentals(self, pitchPrevious=[], cautionaryPitchClass=True,     
            cautionaryAll=False, inPlace=True): 
        '''A method to set and provide accidentals given varous conditions and contexts.

        If `cautionaryPitchClass` is True, all pitch classes are used in comparison; if false, only pitch space is used.

        Optional `pcPast` and `psPast` permit passing in pitches from pervious groupings, taken as part of the present context.

        The :meth:`~music21.pitch.Pitch.updateAccidentalDisplay` method is used to determine if an accidental is necessary.

        This will assume that the complete Stream is the context of evaluation. For smaller context ranges, call this on Measure objects. 
        '''
        if not inPlace: # make a copy
            returnObj = deepcopy(self)
        else:
            returnObj = self

        pitchPast = [] # store a list of pc's encountered
        pitchPast += pitchPrevious

        # need to move through notes in order
        # NOTE: this may or may have sub-streams that are not being examined
        noteStream = returnObj.sorted.notes

        # get chords, notes, and rests
        for i in range(len(noteStream)):
            e = noteStream[i]
            if isinstance(e, note.Note):
                e.pitch.updateAccidentalDisplay(pitchPast, 
                    cautionaryPitchClass=cautionaryPitchClass,
                    cautionaryAll=cautionaryAll)
                pitchPast.append(e.pitch)
            elif isinstance(e, chord.Chord):
                pGroup = e.pitches
                # add all chord elements to past first
                # when reading a chord, this will apply an accidental 
                # if pitches in the chord suggest an accidental
                for p in pGroup:
                    p.updateAccidentalDisplay(pitchPast, 
                        cautionaryPitchClass=cautionaryPitchClass, cautionaryAll=cautionaryAll)
                pitchPast += pGroup

        return returnObj




    def extendDuration(self, objName, inPlace=True):
        '''Given a Stream and an object class name, go through the Stream and find each instance of the desired object. The time between adjacent objects is then assigned to the duration of each object. The last duration of the last object is assigned to extend to the end of the Stream.
        
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
    


    def stripTies(self, inPlace=False, matchByPitch=False):
        '''Find all notes that are tied; remove all tied notes, then make the first of the tied notes have a duration equal to that of all tied 
        constituents. Lastly, remove the formerly-tied notes.

        Presently, this only returns Note objects; Measures and other structures are stripped from the Stream. 

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
        if not inPlace: # make a copy
            returnObj = deepcopy(self)
        else:
            returnObj = self

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

            # a start typed tie may not be a true start tie
            if (hasattr(n, 'tie') and n.tie is not None and 
                n.tie.type == 'start'):
                # find a true start
                if iLast is None or iLast not in posConnected:
                    posConnected = [i] # reset list with start
                # find a continuation: the last note was a tie      
                # start and this note is a tie start
                elif iLast in posConnected:
                    posConnected.append(i)
                endMatch = False # a connection has been started

            # establish end condition
            if endMatch is None: # not yet set, not a start
                if hasattr(n, 'tie') and n.tie is not None and n.tie.type == 'stop':
                    endMatch = True
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
                    # should be an error; presently, just skipping
                    #raise StreamException('cannot consolidate ties when only one tie is present', notes[posConnected[0]])
                    environLocal.printDebug(['cannot consolidate ties when only one tie is present', notes[posConnected[0]]])
                    posConnected = [] 
                    continue

                # get sum of duratoins for all parts to add to first
                durSum = 0
                for q in posConnected[1:]: # all but the first
                    durSum += notes[q].quarterLength
                    posDelete.append(q) # store for deleting later
                if durSum == 0:
                    raise StreamException('aggregated ties have a zero duration sum')
                # add duration to lead
                qLen = notes[posConnected[0]].quarterLength
                notes[posConnected[0]].quarterLength = qLen + durSum

                # set tie to None
                notes[posConnected[0]].tie = None

                posConnected = [] # resset to empty
                    
        # presently removing from notes, not resultObj, as index positions
        # in result object may not be the same
        posDelete.reverse() # start from highest and go down
        for i in posDelete:
            #environLocal.printDebug(['removing note', notes[i]])
            junk = notes.pop(i)

        return notes


    #---------------------------------------------------------------------------
    def _getSorted(self):
        '''
        returns a new Stream where all the elements are sorted according to offset time
        
        if this stream is not flat, then only the highest elements are sorted.  To sort all,
        run myStream.flat.sorted
                
        >>> s = Stream()
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


        OMIT_FROM_DOCS
        TODO: CLEF ORDER RULES, etc.
        '''
        post = self.elements ## already a copy
        post.sort(cmp=lambda x,y: cmp(x.getOffsetBySite(self), y.getOffsetBySite(self)) or cmp(x.priority, y.priority))
        newStream = copy.copy(self)
        newStream.elements = post
        for thisElement in post:
            thisElement._definedContexts.add(newStream,
                                     thisElement.getOffsetBySite(self))
            # need to explicitly set parent
            thisElement.parent = newStream 

        newStream.isSorted = True
        return newStream
    
    sorted = property(_getSorted)        

        
    def _getFlatOrSemiFlat(self, retainContainers):

        # if already flat, could just return a shallow copy?
#         if self.isFlat == True:
#             return self

        # this copy will have a shared locations object
        sNew = copy.copy(self)
        #sNew = self.__class__()

        sNew._elements = []
        sNew._elementsChanged()

        #environLocal.printDebug(['_getFlatOrSemiFlat(), sNew id', id(sNew)])
        # Note: for e in self.elements creates a new Stream
        for e in self.elements:
            # check for stream instance instead
            # if this element is a stream
            if hasattr(e, "elements"): # recurse time:
                recurseStreamOffset = e._definedContexts.getOffsetBySite(self)
                if retainContainers is True: # semiFlat
                    sNew.insert(recurseStreamOffset, e)
                    recurseStream = e.semiFlat
                else:
                    recurseStream = e.flat
                
                #environLocal.printDebug("recurseStreamOffset: " + str(e.id) + " " + str(recurseStreamOffset))
                
                for subEl in recurseStream:
                    # TODO: this should not access the private attribute 
                    oldOffset = subEl._definedContexts.getOffsetBySite(
                                recurseStream)
                    newOffset = oldOffset + recurseStreamOffset
                    #environLocal.printDebug(["newOffset: ", subEl.id, newOffset])
                    sNew.insert(newOffset, subEl)
            # if element not a stream
            else:
                # insert into new stream at offset in old stream
                sNew.insert(e._definedContexts.getOffsetBySite(self), e)

        sNew.isFlat = True
        # here, we store the source stream from which thiss stream was derived
        # TODO: this should probably be a weakref
        sNew.flattenedRepresentationOf = self #common.wrapWeakref(self)
        return sNew
    

    def _getFlat(self):
        '''
        returns a new Stream where no elements nest within other elements
        
        >>> s = Stream()
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
        return self._getFlatOrSemiFlat(retainContainers = False)

    flat = property(_getFlat, 
        doc='''Return a new Stream that has all sub-container flattened within.
        ''')


    def _getSemiFlat(self):
    # does not yet work (nor same for flat above in part because .copy() does not eliminate the cache...
    #        if not self._cache['semiflat']:
    #            self._cache['semiflat'] = self._getFlatOrSemiFlat(retainContainers = True)
    #        return self._cache['semiflat']
        return self._getFlatOrSemiFlat(retainContainers = True)

    semiFlat = property(_getSemiFlat, doc='''
        Returns a flat-like Stream representation. Stream sub-classed containers, such as Measure or Part, are retained in the output Stream, but positioned at their relative offset. 
        ''')


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
        elif len(self.elements) == 0:
            self._cache["HighestOffset"] = 0.0
        elif self.isSorted is True:
            lastEl = self.elements[-1]
            self._cache["HighestOffset"] = lastEl.offset 
        else: # iterate through all elements
            max = None
            for thisElement in self.elements:
                elEndTime = None
                elEndTime = thisElement.offset
                if max is None or elEndTime > max :
                    max = elEndTime
            self._cache["HighestOffset"] = max
        return self._cache["HighestOffset"]

    highestOffset = property(_getHighestOffset, doc='''
        Get start time of element with the highest offset in the Stream.
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
        '''The largest offset plus duration.

        >>> n = note.Note('A-')
        >>> n.quarterLength = 3
        >>> p1 = Stream()
        >>> p1.repeatInsert(n, [0, 1, 2, 3, 4])
        >>> p1.highestTime # 4 + 3
        7.0
        
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

        if self._cache["HighestTime"] is not None:
            pass # return cache unaltered
        elif len(self.elements) == 0:
            self._cache["HighestTime"] = 0.0
            return 0.0
        elif self.isSorted is True:
            lastEl = self.elements[-1]
            if hasattr(lastEl, "duration") and hasattr(lastEl.duration, "quarterLength"):
                #environLocal.printDebug([lastEl.offset,
                #         lastEl.offsetlastEl.duration.quarterLength])
                self._cache["HighestTime"] = lastEl.getOffsetBySite(self) + lastEl.duration.quarterLength
            else:
                self._cache["HighestTime"] = lastEl.getOffsetBySite(self)
        else:
            max = None
            for thisElement in self:
                elEndTime = None
                if hasattr(thisElement, "duration") and hasattr(thisElement.duration, "quarterLength"):
                    elEndTime = thisElement.getOffsetBySite(self) + thisElement.duration.quarterLength
                else:
                    elEndTime = thisElement.getOffsetBySite(self)
                if max is None or elEndTime > max :
                    max = elEndTime
            self._cache["HighestTime"] = max

        return self._cache["HighestTime"]

    
    highestTime = property(_getHighestTime, doc='''
        Returns the maximum of all Element offsets plus their Duration in quarter lengths. This value usually represents the last "release" in the Stream.

        The duration of a Stream is usually equal to the highestTime expressed as a Duration object, but can be set separately.
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
        elif len(self.elements) == 0:
            self._cache["LowestOffset"] = 0.0
        elif self.isSorted is True:
            firstEl = self.elements[0]
            self._cache["LowestOffset"] = firstEl.offset 
        else: # iterate through all elements
            min = None
            for thisElement in self.elements:
                elStartTime = None
                elStartTime = thisElement.offset
                if min is None or elStartTime < min :
                    min = elStartTime
            self._cache["LowestOffset"] = min
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
    # transformations

    def transpose(self, value, inPlace=False):
        '''Transpose all Pitches, Notes, and Chords in the 
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
        for p in post.pitches: # includes chords
            # do inplace transpositions on the deepcopy
            p.transpose(value, inPlace=True)            

        if not inPlace:
            return post
        else:       
            return None


    def offsetScale(self, scalar):
        '''Scale all offsets by a provided scalar.
        '''
        pass

    def durationScale(self, scalar):
        '''Scale all durations by a provided scalar.
        '''
        pass

    def augmentOrDiminish(self, scalar):
        '''Scale this Stream by a provided scalar. 
        '''
        pass


    #---------------------------------------------------------------------------
    def _getLily(self):
        '''Returns the stream translated into Lilypond format.'''
        if self._overriddenLily is not None:
            return self._overriddenLily
        elif self._cache["lily"] is not None:
            return self._cache["lily"]
        
        lilyout = u" { "
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
        self._cache["lily"] = lilyObj
        return lilyObj

    def _setLily(self, value):
        '''Sets the Lilypond output for the stream. Overrides what is obtained
        from get_lily.'''
        self._overriddenLily = value
        self._cache["lily"] = None

    lily = property(_getLily, _setLily)



    def _getMXPart(self, instObj=None, meterStream=None, refStream=None):
        '''If there are Measures within this stream, use them to create and
        return an MX Part and ScorePart. 

        meterStream can be provided to provide a template within which
        these events are positioned; this is necessary for handling
        cases where one part is shorter than another. 
        '''
        #environLocal.printDebug(['calling Stream._getMXPart'])

        if instObj is None:
            # see if an instrument is defined in this or a parent stream
            instObj = self.getInstrument()

        # instruments are defined here
        mxScorePart = musicxmlMod.ScorePart()
        mxScorePart.set('partName', instObj.partName)
        mxScorePart.set('id', instObj.partId)

        mxPart = musicxmlMod.Part()
        mxPart.setDefaults()
        mxPart.set('id', instObj.partId) # need to set id

        # get a stream of measures
        # if flat is used here, the Measure is not obtained
        # may need to be semi flat?
        measureStream = self.getElementsByClass(Measure)
        if len(measureStream) == 0:
            # try to add measures if none defined
            # returns a new stream w/ new Measures but the same objects

            #environLocal.printDebug('\nStream._getMXPart: pre makeMeasures')
            #environLocal.printDebug([self.getClefs()[0]])

            measureStream = self.makeMeasures(meterStream, refStream)
            #environLocal.printDebug(['Stream._getMXPart: post makeMeasures, length', len(measureStream)])

            # for now, calling makeAccidentals once per measures       
            # pitches from last measure are passed
            # this needs to be called before makeTies
            for i in range(len(measureStream)):
                m = measureStream[i]
                if i > 0:
                    m.makeAccidentals(measureStream[i-1].pitches)
                else:
                    m.makeAccidentals()

            measureStream = measureStream.makeTies(meterStream)
            measureStream = measureStream.makeBeams()

            if len(measureStream) == 0:            
                raise StreamException('no measures found in stream with %s elements' % (self.__len__()))
            environLocal.printDebug(['created measures:', len(measureStream)])
        else: # there are measures
            # this will override beams already set
            pass
            # measureStream = makeBeams(measureStream)

        # for each measure, call .mx to get the musicxml representation
        for obj in measureStream:
            mxPart.append(obj.mx)

        # mxScorePart contains mxInstrument
        return mxScorePart, mxPart


    def _getMX(self):
        '''Create and return a musicxml score.

        >>> n1 = note.Note()
        >>> measure1 = Measure()
        >>> measure1.insert(n1)
        >>> str1 = Stream()
        >>> str1.insert(measure1)
        >>> mxScore = str1.mx
        '''
        #environLocal.printDebug('calling Stream._getMX')

        mxComponents = []
        instList = []
        multiPart = False
        meterStream = self.getTimeSignatures() # get from containter first

        # we need independent sub-stream elements to shift in presentation
        highestTime = 0

        for obj in self:
            # if obj is a Part, we have multi-parts
            if isinstance(obj, Part):
                multiPart = True
                break # only need one
            # if components are Measures, self is a part
            elif isinstance(obj, Measure):
                multiPart = False
                break # only need one
            # if components are streams of Notes or Measures, 
            # than assume this is like a Part
            elif isinstance(obj, Stream) and (len(obj.measures) > 0 
                or len(obj.notes) > 0):
                multiPart = True
                break # only need one


        if multiPart:
            #environLocal.printDebug('Stream._getMX: interpreting multipart')
            # need to edit streams contained within streams
            # must repack into a new stream at each step
            #midStream = Stream()
            #finalStream = Stream()

            # NOTE: used to make a shallow copy here
            # TODO: check; removed 4/16/2010
            # TODO: now making a deepcopy, as we are going to edit internal objs
            partStream = copy.deepcopy(self)

            for obj in partStream.getElementsByClass(Stream):
                # may need to copy element here
                # apply this streams offset to elements
                obj.transferOffsetToElements() 

                ts = obj.getTimeSignatures()
                # the longest meterStream is the meterStream for all parts
                if len(ts) > meterStream:
                    meterStream = ts
                ht = obj.highestTime
                if ht > highestTime:
                    highestTime = ht
                # used to place in intermediary stram
                #midStream.insert(obj)

            refStream = Stream()
            refStream.insert(0, music21.Music21Object()) # placeholder at 0
            refStream.insert(highestTime, music21.Music21Object()) 

            # would like to do something like this but cannot
            # replace object inside of the stream
            for obj in partStream.getElementsByClass(Stream):
                obj.makeRests(refStream, inPlace=True)
                # used to move into a final Stream: no longer necessary
                #finalStream.insert(obj)

            environLocal.printDebug(['handling multi-part Stream of length:',
                                    len(partStream)])
            count = 0
            for obj in partStream.getElementsByClass(Stream):
                count += 1
                if count > len(partStream):
                    raise StreamException('infinite stream encountered')

                # only things that can be treated as parts are in finalStream
                inst = obj.getInstrument()
                instIdList = [x.partId for x in instList]
                if inst.partId in instIdList: # must have unique ids 
                    inst.partIdRandomize() # set new random id
                instList.append(inst)

                mxComponents.append(obj._getMXPart(inst, meterStream,
                                refStream))

        else: # assume this is the only part
            environLocal.printDebug('handling single-part Stream')
            # if no instrument is provided it will be obtained through self
            # when _getMxPart is called
            mxComponents.append(self._getMXPart(None, meterStream))


        # create score and part list
        mxPartList = musicxmlMod.PartList()
        mxIdentification = musicxmlMod.Identification()
        mxIdentification.setDefaults() # will create a composer
        mxScore = musicxmlMod.Score()
        mxScore.setDefaults()
        mxScore.set('partList', mxPartList)
        mxScore.set('identification', mxIdentification)

        for mxScorePart, mxPart in mxComponents:
            mxPartList.append(mxScorePart)
            mxScore.append(mxPart)

        return mxScore


    def _setMXPart(self, mxScore, partId):
        '''Load a part given an mxScore and a part name.
        '''
        #environLocal.printDebug(['calling Stream._setMXPart'])

        mxPart = mxScore.getPart(partId)
        mxInstrument = mxScore.getInstrument(partId)

        # create a new music21 instrument
        instrumentObj = instrument.Instrument()
        if mxInstrument is not None:
            instrumentObj.mx = mxInstrument

        # add part id as group
        instrumentObj.groups.append(partId)

        streamPart = Part() # create a part instance for each part
        # set part id to stream best name
        if instrumentObj.bestName() is not None:
            streamPart.id = instrumentObj.bestName()
        streamPart.insert(instrumentObj) # add instrument at zero offset

        # offset is in quarter note length
        oMeasure = 0
        lastTimeSignature = None
        for mxMeasure in mxPart:
            # create a music21 measure and then assign to mx attribute
            m = Measure()
            m.mx = mxMeasure  # assign data into music21 measure 
            if m.timeSignature is not None:
                lastTimeSignature = m.timeSignature
            elif lastTimeSignature is None and m.timeSignature is None:
                # if no time sigature is defined, need to get a default
                ts = meter.TimeSignature()
                ts.load('%s/%s' % (defaults.meterNumerator, 
                                   defaults.meterDenominatorBeatType))
                lastTimeSignature = ts
            # add measure to stream at current offset for this measure
            streamPart.insert(oMeasure, m)
            # increment measure offset for next time around
            oMeasure += lastTimeSignature.barDuration.quarterLength 

        streamPart.addGroupForElements(partId) # set group for components 
        streamPart.groups.append(partId) # set group for stream itself

        # add to this stream
        # this assumes all start at the same place
        self.insert(0, streamPart)


    def _setMX(self, mxScore):
        '''Given an mxScore, build into this stream
        '''
        partNames = mxScore.getPartNames().keys()
        partNames.sort()
        for partName in partNames: # part names are part ids
            self._setMXPart(mxScore, partName)

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
        return self.getElementsByClass([note.GeneralNote, chord.Chord])
        # note: class names must be provided in one argument as a list

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
        returnPitches = []
        for thisEl in self.elements:
            if hasattr(thisEl, "pitch"):
                returnPitches.append(thisEl.pitch)
            # both Chords and Stream have a pitches properties            
            elif hasattr(thisEl, "pitches"):
                for thisPitch in thisEl.pitches:
                    returnPitches.append(thisPitch)
            elif isinstance(thisEl, music21.pitch.Pitch):
                returnPitches.append(thisEl)
        return returnPitches
    
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

        OMIT_FROM_DOCS
        Test to make sure that Pitch objects are
        also being retrieved
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

    #------------ interval routines --------------------------------------------
    
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
            
        for el in sortedSelf.elements:
            if lastWasNone is False and skipGaps is False and el.offset > lastEnd:
                if not noNone:
                    returnList.append(None)
                    lastWasNone = True
            if hasattr(el, "pitch"):
                if (skipUnisons is False or isinstance(lastPitch, list) or lastPitch is None or 
                    el.pitch.pitchClass != lastPitch.pitchClass or (skipOctaves is False and el.pitch.ps != lastPitch.ps)):
                    if getOverlaps is True or el.offset >= lastEnd:
                        if el.offset >= lastEnd:  # is not an overlap...
                            lastStart = el.offset
                            if hasattr(el, "duration"):
                                lastEnd = lastStart + el.duration.quarterLength
                            else:
                                lastEnd = lastStart
                            lastWasNone = False
                            lastPitch = el.pitch
                        else:  # do not update anything for overlaps
                            pass 

                        returnList.append(el)

            elif hasattr(el, "pitches"):
                if skipChords is True:
                    if lastWasNone is False:
                        if not noNone:
                            returnList.append(None)
                            lastWasNone = True
                            lastPitch = None
                else:
                    if (skipUnisons is True and isinstance(lastPitch, list) and
                        el.pitches[0].ps == lastPitch[0].ps):
                        pass
                    else:
                        if getOverlaps is True or el.offset >= lastEnd:
                            if el.offset >= lastEnd:  # is not an overlap...
                                lastStart = el.offset
                                if hasattr(el, "duration"):
                                    lastEnd = lastStart + el.duration.quarterLength
                                else:
                                    lastEnd = lastStart
            
                                lastPitch = el.pitches
                                lastWasNone = False 

                            else:  # do not update anything for overlaps
                                pass 
                            returnList.append(el)

            elif skipRests is False and isinstance(el, note.Rest) and lastWasNone is False:
                if noNone is False:
                    returnList.append(None)
                    lastWasNone = True
                    lastPitch = None
            elif skipRests is True and isinstance(el, note.Rest):
                lastEnd = el.offset + el.duration.quarterLength
        
        if lastWasNone is True:
            returnList.pop()
        return returnList
    
    def melodicIntervals(self, *skipArgs, **skipKeywords):
        '''Returns a Stream of :class:`~music21.interval.Interval` objects between Notes (and by default, Chords) that follow each other in a stream.
        the offset of the Interval is the offset of the beginning of the interval (if two notes are adjacent, 
        then it is equal to the offset of the second note)
        
        See Stream.findConsecutiveNotes for a discussion of what consecutive notes mean, and which keywords are allowed.
        
        The interval between a Note and a Chord (or between two chords) is the interval between pitches[0]. For more complex interval calculations, run findConsecutiveNotes and then use notesToInterval.
                
        Returns None of there are not at least two elements found by findConsecutiveNotes.

        See Test.testMelodicIntervals() for usage details.

        OMIT_FROM_DOCS
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
                    returnInterval = interval.notesToInterval(firstPitch, secondPitch)
                    returnInterval.offset = firstNote.offset + firstNote.duration.quarterLength
                    returnInterval.duration = duration.Duration(secondNote.offset - returnInterval.offset)
                    returnStream.insert(returnInterval)

        return returnStream

    #---------------------------------------------------------------------------
    def _getDurSpan(self, flatStream):
        '''Given elementsSorted, create a list of parallel
        values that represent dur spans, or start and end times.

        >>> a = Stream()
        >>> a.repeatInsert(note.HalfNote(), range(5))
        >>> a._getDurSpan(a.flat)
        [(0.0, 2.0), (1.0, 3.0), (2.0, 4.0), (3.0, 5.0), (4.0, 6.0)]
        '''
        post = []        
        for i in range(len(flatStream)):
            element = flatStream[i]
            if element.duration is None:
                durSpan = (element.offset, element.offset)
            else:
                dur = element.duration.quarterLength
                durSpan = (element.offset, element.offset+dur)
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
            if not includeDurationless and flatStream[i].duration is None: 
                continue
            # compare to all past and following durations
            for j in range(len(durSpanSorted)):
                if j == i: continue # do not compare to self
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
                        if elementObj in post[key]:
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
                    if srcElementObj in post[key]:
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



    def findGaps(self):
        '''
        returns either (1) a Stream containing Elements (that wrap the None object)
        whose offsets and durations are the length of gaps in the Stream
        or (2) None if there are no gaps.
        
        N.B. there may be gaps in the flattened representation of the stream
        but not in the unflattened.  Hence why "isSequence" calls self.flat.isGapless
        '''
        if self.cache["GapStream"]:
            return self.cache["GapStream"]
        
        sortedElements = self.sorted.elements
        gapStream = Stream()
        highestCurrentEndTime = 0
        for thisElement in sortedElements:
            if thisElement.offset > highestCurrentEndTime:
                gapElement = music21.ElementWrapper(obj = None, offset = highestCurrentEndTime)
                gapElement.duration = duration.Duration()
                gapElement.duration.quarterLength = thisElement.offset - highestCurrentEndTime
                gapStream.insert(gapElement)
            highestCurrentEndTime = max(highestCurrentEndTime, thisElement.offset + thisElement.duration.quarterLength)

        if len(gapStream) == 0:
            return None
        else:
            self.cache["GapStream"] = gapStream
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
        
        CHRIS: What does this return? and how can someone use this?
        
        This example demonstrates end-joing overlaps: there are four quarter notes each
        following each other. Whether or not these count as overlaps
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
        return self._consolidateLayering(elementsSorted, overlapMap)



    def isSequence(self, includeDurationless=True, 
                        includeEndBoundary=False):
        '''A stream is a sequence if it has no overlaps.

        >>> a = Stream()
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
        '''For each element in self, creates an interval object in the element's
        editorial that is the interval between it and the element in cmpStream that
        is sounding at the moment the element in srcStream is attacked.'''
    
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
        >>> n3.parent = None
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
        '''Returns a new Stream of elements in this stream that sound at the same time as "el", an element presumably in another Stream.
        
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




#-------------------------------------------------------------------------------
class Measure(Stream):
    '''A representation of a Measure organized as a Stream. 

    All properties of a Measure that are Music21 objects are found as part of 
    the Stream's elements. 
    '''

    # define order to present names in documentation; use strings
    _DOC_ORDER = ['']
    # documentation for all attributes (not properties or methods)
    _DOC_ATTR = {
    'timeSignatureIsNew': 'Boolean describing if the TimeSignature is different than the previous Measure.',
    'clefIsNew': 'Boolean describing if the Clef is different than the previous Measure.',
    'keyIsNew': 'Boolean describing if KeySignature is different than the previous Measure.',
    'measureNumber': 'A number representing the displayed or shown Measure number as presented in a written Score.',
    'measureNumberSuffix': 'If a Measure number has a string annotation, such as "a" or similar, this string is stored here.',
   
    }

    def __init__(self, *args, **keywords):
        Stream.__init__(self, *args, **keywords)

        # clef and timeSignature is defined as a property below
        self.timeSignatureIsNew = False
        self.clefIsNew = False
        self.keyIsNew = False

        self.filled = False
        # NOTE: it seems that the default measure number should be zero.
        self.measureNumber = 0 # 0 means undefined or pickup
        self.measureNumberSuffix = None # for measure 14a would be "a"

        # inherits from prev measure or is default for group
        # inherits from next measure or is default for group

        # these need to be put on, and obtained from .elements
        self.leftbarline = None  
        self.rightbarline = None 

        # for display is overridden by next measure\'s leftbarline if that is not None and
        # the two measures are on the same system

        #self.internalbarlines = Stream()
        # "measure expressions" that are attached to nowhere in particular
        #self.timeIndependentDirections = Stream() 
        # list of times at which Directions take place.
        #self.timeDependentDirectionsTime = Stream() 
        # should be sorted always.
        # list of Directions that happen at a certain time, 
        # keep indices together
        #self.timeDependentDirections = Stream() 


    def addRepeat(self):
        # TODO: write
        pass

    def addTimeDependentDirection(self, time, direction):
        # TODO: write
        pass

    def setRightBarline(self, blStyle = None):
        self.rightbarline = measure.Barline(blStyle)
        return self.rightbarline
    
    def setLeftBarline(self, blStyle = None):
        self.leftbarline = measure.Barline(blStyle)
        return self.leftbarline
    
    def measureNumberWithSuffix(self):
        if self.measureNumberSuffix:
            return str(self.measureNumber) + self.measureNumberSuffix
        else:
            return str(self.measureNumber)
    
    def __repr__(self):
        return "<music21.stream.%s %s offset=%s>" % \
            (self.__class__.__name__, self.measureNumberWithSuffix(), self.offset)
        
    #---------------------------------------------------------------------------
    def bestTimeSignature(self):
        '''Given a Measure with elements in it, get a TimeSignature that contains all elements.

        Note: this does not yet accommodate triplets. 
        '''
        minDurQL = 4 # smallest denominator
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


    #---------------------------------------------------------------------------
    # Music21Objects are stored in the Stream's elements list 
    # properties are provided to store and access these attribute

    def _getClef(self):
        '''
        >>> a = Measure()
        >>> a.clef = clef.TrebleClef()
        >>> a.clef.sign    # clef is an element
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
        tsList = self.getElementsByClass(meter.TimeSignature)
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
            environLocal.printDebug(['removing ts', oldTimeSignature])
            junk = self.pop(self.index(oldTimeSignature))
        self.insert(0, tsObj)

    timeSignature = property(_getTimeSignature, _setTimeSignature)   


    def _getKey(self):
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
    
    def _setKey(self, keyObj):
        '''
        >>> a = Measure()
        >>> a.keySignature = key.KeySignature(3)
        >>> a.keySignature.sharps   
        3
        >>> a.keySignature = key.KeySignature(6)
        >>> a.keySignature.sharps
        6
        '''
        oldKey = self._getKey()
        if oldKey is not None:
            environLocal.printDebug(['removing key', oldKey])
            junk = self.pop(self.index(oldKey))
        self.insert(0, keyObj)

    keySignature = property(_getKey, _setKey)   

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

        mxMeasure = musicxmlMod.Measure()
        mxMeasure.set('number', self.measureNumber)

        # get an empty mxAttributes object
        mxAttributes = musicxmlMod.Attributes()
        # best to only set dvisions here, as clef, time sig, meter are not
        # required for each measure
        mxAttributes.setDefaultDivisions() 

        # may need to look here at the parent, and try to find
        # the clef in the clef last defined in the parent
        if self.clef is not None:
            mxAttributes.clefList = [self.clef.mx]

        if self.keySignature is not None: 
            # key.mx returns a Key ojbect, needs to be in a list
            mxAttributes.keyList = [self.keySignature.mx]
        
        if self.timeSignature is not None:
            mxAttributes.timeList = self.timeSignature.mx 

        #mxAttributes.keyList = []
        mxMeasure.set('attributes', mxAttributes)

        #need to handle objects in order when creating musicxml 
        for obj in self.flat:
            if obj.isClass(note.GeneralNote):
                # .mx here returns a list of notes
                mxMeasure.componentList += obj.mx
            elif obj.isClass(dynamics.Dynamic):
                # returns an mxDirection object
                mxMeasure.append(obj.mx)
            else:
                pass
                #environLocal.printDebug(['_getMX of Measure is not processing', obj])
        return mxMeasure


    def _setMX(self, mxMeasure):
        '''Given an mxMeasure, create a music21 measure
        '''
        # measure number may be a string and not a number (always?)
        mNum, mSuffix = common.getNumFromStr(mxMeasure.get('number'))
        # assume that measure numbers are integers
        if mNum not in [None, '']:
            self.measureNumber = int(mNum)
        if mSuffix not in [None, '']:
            self.measureNumberSuffix = mSuffix

        junk = mxMeasure.get('implicit')
#         environLocal.printDebug(['_setMX: working on measure:',
#                                 self.measureNumber])

        mxAttributes = mxMeasure.get('attributes')
        mxAttributesInternal = True
        if mxAttributes is None:    
            # need to keep track of where mxattributessrc is coming from
            mxAttributesInternal = False
            # not all measures have attributes definitions; this
            # gets the last-encountered measure attributes
            mxAttributes = mxMeasure.external['attributes']
            if mxAttributes is None:
                raise StreamException(
                    'no mxAttribues available for this measure')

        #environLocal.printDebug(['mxAttriutes clefList', mxAttributes.clefList, 
        #                        mxAttributesInternal])

        if mxAttributesInternal and len(mxAttributes.timeList) != 0:
            self.timeSignature = meter.TimeSignature()
            self.timeSignature.mx = mxAttributes.timeList

        if mxAttributesInternal is True and len(mxAttributes.clefList) != 0:
            self.clef = clef.Clef()
            self.clef.mx = mxAttributes.clefList

        if mxAttributesInternal is True and len(mxAttributes.keyList) != 0:
            self.keySignature = key.KeySignature()
            self.keySignature.mx = mxAttributes.keyList

        # set to zero for each measure
        offsetMeasureNote = 0 # offset of note w/n measure        
        mxNoteList = [] # for chords
        for i in range(len(mxMeasure)):
            mxObj = mxMeasure[i]
            if i < len(mxMeasure)-1:
                mxObjNext = mxMeasure[i+1]
            else:
                mxObjNext = None

            if isinstance(mxObj, musicxmlMod.Note):
                mxNote = mxObj
                if isinstance(mxObjNext, musicxmlMod.Note):
                    mxNoteNext = mxObjNext
                else:
                    mxNoteNext = None

                if mxNote.get('print-object') == 'no':
                    #environLocal.printDebug(['got mxNote with printObject == no', 'measure number', self.measureNumber])
                    continue

                mxGrace = mxNote.get('grace')
                if mxGrace is not None: # graces have a type but not a duration
                    #TODO: add grace notes with duration equal to ZeroDuration
                    #environLocal.printDebug(['got mxNote with an mxGrace', 'duration', mxNote.get('duration'), 'measure number', 
                    #self.measureNumber])
                    continue

                # the first note of a chord is not identified directly; only
                # by looking at the next note can we tell if we have a chord
                if mxNoteNext is not None and mxNoteNext.get('chord') is True:
                    if mxNote.get('chord') is False:
                        mxNote.set('chord', True) # set the first as a chord

                if mxNote.get('rest') in [None, False]: # it is a note

                    if mxNote.get('chord') is True:
                        mxNoteList.append(mxNote)
                        offsetIncrement = 0
                    else:
                        n = note.Note()
                        n.mx = mxNote
                        self.insert(offsetMeasureNote, n)
                        offsetIncrement = n.quarterLength
                    for mxLyric in mxNote.lyricList:
                        lyricObj = note.Lyric()
                        lyricObj.mx = mxLyric
                        n.lyrics.append(lyricObj)
                    if mxNote.get('notations') is not None:
                        for mxObjSub in mxNote.get('notations'):
                            # deal with ornaments, strill, etc
                            pass
                else: # its a rest
                    n = note.Rest()
                    n.mx = mxNote # assign mxNote to rest obj
                    self.insert(offsetMeasureNote, n)            
                    offsetIncrement = n.quarterLength

                # if we we have notes in the note list and the next
                # not either does not exist or is not a chord, we 
                # have a complete chord
                if len(mxNoteList) > 0 and (mxNoteNext is None 
                    or mxNoteNext.get('chord') is False):
                    c = chord.Chord()
                    c.mx = mxNoteList
                    mxNoteList = [] # clear for next chord
                    self.insert(offsetMeasureNote, c)
                    offsetIncrement = c.quarterLength

                # do not need to increment for musicxml chords
                offsetMeasureNote += offsetIncrement

            # load dynamics into measure
            elif isinstance(mxObj, musicxmlMod.Direction):
#                 mxDynamicsFound, mxWedgeFound = self._getMxDynamics(mxObj)
#                 for mxDirection in mxDynamicsFound:
                if mxObj.getDynamicMark() is not None:
                    d = dynamics.Dynamic()
                    d.mx = mxObj
                    self.insert(offsetMeasureNote, d)  
                if mxObj.getWedge() is not None:
                    w = dynamics.Wedge()
                    w.mx = mxObj     
                    self.insert(offsetMeasureNote, w)  

    mx = property(_getMX, _setMX)    



    def _getMusicXML(self):
        '''Provide a complete MusicXML: representation. 
        '''

        mxMeasure = self._getMX()

        mxPart = musicxmlMod.Part()
        mxPart.setDefaults()
        mxPart.append(mxMeasure) # append measure here


        # see if an instrument is defined in this or a prent stream
        instObj = self.getInstrument()
        mxScorePart = musicxmlMod.ScorePart()
        mxScorePart.set('partName', instObj.partName)
        mxScorePart.set('id', instObj.partId)
        # must set this part to the same id
        mxPart.set('id', instObj.partId)

        mxPartList = musicxmlMod.PartList()
        mxPartList.append(mxScorePart)

        mxIdentification = musicxmlMod.Identification()
        mxIdentification.setDefaults() # will create a composer
        mxScore = musicxmlMod.Score()
        mxScore.setDefaults()
        mxScore.set('partList', mxPartList)
        mxScore.set('identification', mxIdentification)
        mxScore.append(mxPart)

        return mxScore.xmlStr()

    def _setMusicXML(self, mxScore):
        '''
        '''
        pass

    musicxml = property(_getMusicXML, _setMusicXML)

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

class Part(Stream):
    '''A Stream subclass for designating music that is
    considered a single part.
    
    May be enclosed in a staff (for instance, 2nd and 3rd trombone
    on a single staff), may enclose staves (piano treble and piano bass),
    or may not enclose or be enclosed by a staff (in which case, it
    assumes that this part fits on one staff and shares it with no other
    part
    '''

    def _getLily(self):
        lv = Stream._getLily(self)
        lv2 = lilyModule.LilyString(" \\new Staff " + lv.value)
        return lv2
    
    lily = property(_getLily)

class Staff(Stream):
    '''
    A Stream subclass for designating music on a single staff
    '''
    
    staffLines = 5

class Performer(Stream):
    '''
    A Stream subclass for designating music to be performed by a
    single Performer.  Should only be used when a single performer
    performs on multiple parts.  E.g. Bass Drum and Triangle on separate
    staves performed by one player.

    a Part + changes of Instrument is fine for designating most cases
    where a player changes instrument in a piece.  A part plus staves
    with individual instrument changes could also be a way of designating
    music that is performed by a single performer (see, for instance
    the Piano doubling Celesta part in Lukas Foss's Time Cycle).  The
    Performer Stream-subclass could be useful for analyses of, for instance,
    how 5 percussionists chose to play a piece originally designated for 4
    (or 6) percussionists in the score.
    '''
    pass


class System(Stream):
    '''Totally optional: designation that all the music in this Stream
    belongs in a single system.
    '''
    systemNumber = 0
    systemNumbering = "Score" # or Page; when do system numbers reset?

class Page(Stream):
    '''
    Totally optional: designation that all the music in this Stream
    belongs on a single notated page
    '''
    pageNumber = 0
    
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
                ret += " >> "
            else:
                if hasattr(thisOffsetPosition[0], "lily"):
                    ret += thisOffsetPosition[0].lily
                else:
                    # TODO: write out debug code here
                    pass
        return ret
        
    lily = property(_getLily)


    def getMeasureRange(self, numberStart, numberEnd, 
        collect=[clef.Clef, meter.TimeSignature, 
        instrument.Instrument, key.KeySignature]):
        '''This method override the :meth:`~music21.stream.Stream.getMeasureRange` method on Stream. This creates a new Score stream that has the same measure range for all Parts.
        '''
        post = Score()
        # note that this will strip all objects that are not Parts
        for p in self.getElementsByClass(Part):
            # insert all at zero
            post.insert(0, p.getMeasureRange(numberStart, numberEnd,
                        collect))
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
            b.elements[i].accidental = note.Accidental(i - 2)
        
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
        probably b/c when appending to s Stream parent is set to that stream
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
        '''Test copyinng all objects defined in this module
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
        

    def testParentCopiedStreams(self):
        srcStream = Stream()
        srcStream.insert(3, note.Note())
        # the note's parent is srcStream now
        self.assertEqual(srcStream[0].parent, srcStream)

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





    def testOverlaps(self):
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
        self.assertEqual(a.lily.value, u' { \\clef "treble"  \\time 3/4   { c\'\'4 c\'\'4 c\'\'4 c\'\'4  }   } ')

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
            b.elements[i].accidental = note.Accidental(i - 2)
        
        b.elements[0].duration.tuplets[0].type = "start"
        b.elements[-1].duration.tuplets[0].type = "stop"
        b2temp = b.elements[2]
        c = b2temp.editorial
        c.comment.text = "a real C"
        
        bestC = b.bestClef(allowTreble8vb = True)
        a.insert(bestC)
        a.insert(ts)
        a.insert(b)
        self.assertEqual(a.lily.value,  u' { \\clef "bass"  \\time 3/8   { \\times 3/5 {ceses,8 ces,8 c,8_"a real C" cis,8 cisis,8}  }   } ')

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
        self.assertEqual(u" << \\time 2/4  \\new Staff  { c'4 d'4  }  \\new Staff  { d'4 c'4  }  >> ", score1.lily.value)



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




    def testParents(self):
        '''Test parent relationships.

        Note that here we see why sometimes qualified class names are needed.
        This test passes fine with class names Part and Measure when run interactively, 
        creating a Test instance. When run from the command line
        Part and Measure do not match, and instead music21.stream.Part has to be 
        employed instead. 
        '''

        from music21 import corpus, converter
        a = converter.parse(corpus.getWork('haydn/opus74no2/movement4.xml'))

        # test basic parent relationships
        b = a[3]
        self.assertEqual(isinstance(b, music21.stream.Part), True)
        self.assertEqual(b.parent, a)

        # this, if called, actively destroys the parent relationship!
        # on the measures (as new Elements are not created)
        #m = b.getMeasures()[5]
        #self.assertEqual(isinstance(m, Measure), True)

        # this false b/c, when getting the measures, parents are lost
        #self.assertEqual(m.parent, b) #measures parent should be part

        self.assertEqual(isinstance(b[8], music21.stream.Measure), True)
        self.assertEqual(b[8].parent, b) #measures parent should be part


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

        self.assertEqual(q.parent, s)
        self.assertEqual(r.parent, s)

    def testParentsMultiple(self):
        '''Test an object having multiple parents.
        '''
        a = Stream()
        b = Stream()
        n = note.Note("G#")
        n.offset = 10
        a.insert(n)
        b.insert(n)
        # the objects elements has been transfered to each parent
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
        from music21 import corpus, converter

        # manuall set parent to associate 
        a = converter.parse(corpus.getWork(['haydn', 'opus74no2', 
                                            'movement4.xml']))

        b = a[3][10:20]
        # TODO: manually setting the parent is still necessary
        b.parent = a[3] # manually set the parent
        instObj = b.getInstrument()
        self.assertEqual(instObj.partName, 'Cello')

        p = a[3] # get part
        # a mesausre within this part has as its parent the part
        self.assertEqual(p[10].parent, a[3])
        instObj = p.getInstrument()
        self.assertEqual(instObj.partName, 'Cello')

        instObj = p[10].getInstrument()
        self.assertEqual(instObj.partName, 'Cello')




    def testGetInstrumentManual(self):
        from music21 import corpus, converter


        #import pdb; pdb.set_trace()
        # search parent from a measure within

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
        # search parent from a measure within

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
            junk = x.getInstrument(searchParent=True)
            del junk
            counter += 1


    def testGetTimeSignatures(self):
        #getTimeSignatures

        n = note.Note()        
        n.quarterLength = 3
        a = Stream()
        a.insert( 0, meter.TimeSignature("5/4")  )
        a.insert(10, meter.TimeSignature("2/4")  )
        a.insert( 3, meter.TimeSignature("3/16") )
        a.insert(20, meter.TimeSignature("9/8")  )
        a.insert(40, meter.TimeSignature("10/4") )

        offsets = [x.offset for x in a]
        self.assertEqual(offsets, [0.0, 10.0, 3.0, 20.0, 40.0])

        a.repeatInsert(n, range(0,120,3))        

        b = a.getTimeSignatures()
        self.assertEqual(len(b), 5)
        self.assertEqual(b[0].numerator, 5)
        self.assertEqual(b[4].numerator, 10)

        self.assertEqual(b[4].parent, b)

        # none of the offsets are being copied 
        offsets = [x.offset for x in b]
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
        

    def testStripTies(self):
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
        b = a[3].getMeasureRange(4,6)
        self.assertEqual(len(b), 3) 
        # first measure now has keu sig
        self.assertEqual(len(b[0].getElementsByClass(key.KeySignature)), 1) 
        # first measure now has meter
        self.assertEqual(len(b[0].getElementsByClass(meter.TimeSignature)), 1) 
        # first measure now has clef
        self.assertEqual(len(b[0].getElementsByClass(clef.Clef)), 1) 

        #b.show()       

        # test measures with no measure numbesr
        c = Stream()
        for i in range(4):
            m = Measure()
            n = note.Note()
            m.repeatAppend(n, 4)
            c.append(m)
        #c.show()
        d = c.getMeasureRange(2,3)
        self.assertEqual(len(d), 2) 
        #d.show()

        # try the score method
        a = corpus.parseWork('bach/bwv324.xml')
        b = a.getMeasureRange(2,4)
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
            [0.0, 4.0, 8.0, 12.0, 16.0, 20.0, 24.0, 28.0, 32.0] )

        # try on a complete score
        a = corpus.parseWork('bach/bwv324.xml')
        mOffsetMap = a.measureOffsetMap()
        #environLocal.printDebug([mOffsetMap])
        self.assertEqual(sorted(mOffsetMap.keys()), 
            [0.0, 4.0, 8.0, 12.0, 16.0, 20.0, 24.0, 28.0, 32.0] )

        for key, value in mOffsetMap.items():
            # each key contains 4 measures
            self.assertEqual(len(value), 4)

        # we can get this information from Notes too!
        a = corpus.parseWork('bach/bwv324.xml')
        # get notes form one measure
        mOffsetMap = a[0].measures[1].measureOffsetMap(note.Note)
        self.assertEqual(sorted(mOffsetMap.keys()), [4.0] )

        mOffsetMap = a[0].flat.measureOffsetMap(note.Note)
        self.assertEqual(sorted(mOffsetMap.keys()), [0.0, 4.0, 8.0, 12.0, 16.0, 20.0, 24.0, 28.0, 32.0]  )

        # this should work but does not yet
        # it seems that the flat score does not work as the flat part
        #mOffsetMap = a.flat.measureOffsetMap(note.Note)
        #self.assertEqual(sorted(mOffsetMap.keys()), [0.0, 4.0, 8.0, 12.0, 16.0, 20.0, 24.0, 28.0, 32.0]  )



    def testMeasureOffsetMapPostTie(self):
        from music21 import corpus, stream
        
        a = corpus.parseWork('bach/bwv4.8.xml')
        # alto line syncopated/tied notes accross bars
        alto = a[1]
        self.assertEqual(len(alto.flat.notes), 73)
        
        # offset map for measures looking at the part's Measures
        post = alto.measureOffsetMap()
        self.assertEqual(sorted(post.keys()), [0.0, 4.0, 8.0, 12.0, 16.0, 20.0, 24.0, 28.0, 32.0, 36.0, 40.0, 44.0, 48.0, 52.0, 56.0, 60.0, 64.0])
        
        # looking at Measure and Notes: no problem
        post = alto.flat.measureOffsetMap([Measure, note.Note])
        self.assertEqual(sorted(post.keys()), [0.0, 4.0, 8.0, 12.0, 16.0, 20.0, 24.0, 28.0, 32.0, 36.0, 40.0, 44.0, 48.0, 52.0, 56.0, 60.0, 64.0])
        
        
        # after stripping ties, we have a stream with fewer notes
        altoPostTie = a[1].stripTies()
        # we can get the length of this directly b/c we just of a stream of 
        # notes, no Measures
        self.assertEqual(len(altoPostTie.notes), 69)
        
        # we can still get measure numbers:
        mNo = altoPostTie[3].getContextByClass(stream.Measure).measureNumber
        self.assertEqual(mNo, 1)
        mNo = altoPostTie[8].getContextByClass(stream.Measure).measureNumber
        self.assertEqual(mNo, 2)
        mNo = altoPostTie[15].getContextByClass(stream.Measure).measureNumber
        self.assertEqual(mNo, 4)
        
        # can we get an offset Measure map by looking for measures
        post = altoPostTie.measureOffsetMap(stream.Measure)
        # nothing: no Measures:
        self.assertEqual(post.keys(), [])
        
        # but, we can get an offset Measure map by looking at Notes
        post = altoPostTie.measureOffsetMap(note.Note)
        # nothing: no Measures:
        self.assertEqual(sorted(post.keys()), [0.0, 4.0, 8.0, 12.0, 16.0, 20.0, 24.0, 28.0, 32.0, 36.0, 40.0, 44.0, 48.0, 52.0, 56.0, 60.0, 64.0])

        #from music21 import graph
        #graph.plotStream(altoPostTie, 'scatter', values=['pitchclass','offset'])


    def testMusicXMLAttribute(self):
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

        post = s.musicxml


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
        self.assertEqual(len(sMeasures.measures), 1) # one measure
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
        environLocal.printDebug(
            ['s1Flat._definedContexts._definedContexts[id(s1)', s1Flat._definedContexts._definedContexts[id(s2)]])
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
        
        s3.insert(0, clef.AltoClef())
        # both output parts have alto clefs
        #s3.show()

        # get clef form higher level stream; only option
        post = s1.getClefs()[0]
        self.assertEqual(isinstance(post, clef.AltoClef), True)

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


        s1Measures = s1.makeMeasures()
        self.assertEqual(isinstance(s1Measures[0].clef, clef.AltoClef), True)

        s2Measures = s2.makeMeasures()
        self.assertEqual(isinstance(s2Measures[0].clef, clef.TenorClef), True)


        # try making a deep copy of s3

        s3copy = copy.deepcopy(s3)
        s1Measures = s3copy[0].makeMeasures()
        self.assertEqual(isinstance(s1Measures[0].clef, clef.AltoClef), True)
        #s1Measures.show() # these show the proper clefs

        s2Measures = s3copy[1].makeMeasures()
        self.assertEqual(isinstance(s2Measures[0].clef, clef.TenorClef), True)
        #s2Measures.show() # this shows the proper clef

        #TODO: this still retruns tenor cleff for both parts
        # need to examine

        # now we in sert a clef in s2; s2 will get this clef first
        s1.insert(0, clef.BassClef())
        post = s1.getClefs()[0]
        self.assertEqual(isinstance(post, clef.BassClef), True)


        #s3.show()

    def testMakeMeasuresMeterStream(self):
        '''Testing making measures of various sizes with a supplied single element meter stream. This illustrate an approach to partitioning elements by various sized windows. 
        '''
        from music21 import meter, corpus
        sBach = corpus.parseWork('bach/bwv324.xml')
        meterStream = Stream()
        meterStream.insert(0, meter.TimeSignature('2/4'))
        # need to call make ties to allocate notes
        sPartitioned = sBach.flat.makeMeasures(meterStream).makeTies()
        self.assertEqual(len(sPartitioned), 18)


        meterStream = Stream()
        meterStream.insert(0, meter.TimeSignature('1/4'))
        # need to call make ties to allocate notes
        sPartitioned = sBach.flat.makeMeasures(meterStream).makeTies()
        self.assertEqual(len(sPartitioned), 36)


        meterStream = Stream()
        meterStream.insert(0, meter.TimeSignature('3/4'))
        # need to call make ties to allocate notes
        sPartitioned = sBach.flat.makeMeasures(meterStream).makeTies()
        self.assertEqual(len(sPartitioned), 12)


        meterStream = Stream()
        meterStream.insert(0, meter.TimeSignature('12/4'))
        # need to call make ties to allocate notes
        sPartitioned = sBach.flat.makeMeasures(meterStream).makeTies()
        self.assertEqual(len(sPartitioned), 3)


        meterStream = Stream()
        meterStream.insert(0, meter.TimeSignature('36/4'))
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

        self.assertEqual(n1.parent, s)
        s.remove(n1)
        self.assertEqual(len(s), 2)
        # parent is Now sent to Nonte
        self.assertEqual(n1.parent, None)


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

        environLocal.printDebug(['s1', s1, id(s1)])    
        environLocal.printDebug(['s2', s2, id(s2)])    
        environLocal.printDebug(['s2flat', s2Flat, id(s2Flat)])

        environLocal.printDebug(['n1.siteIds', n1, n1.getSites(), n1.getSiteIds()])

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
        self.assertEqual(n3.accidental, None)

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



        
    def xtestMultipleReferencesOneStream(self):
        '''Test having multiple references of the same element in a single Stream.
        '''
        s = Stream()
        n1 = note.Note('g')
        n2 = note.Note('g#')

        # TODO: this is a problem as presently an object can only have one 
        # offset for one site
        s.insert(0, n1)

        self.assertRaises(StreamException,  s.insert, 10, n1)

       


#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [Stream, Measure]



if __name__ == "__main__":

    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)
    elif len(sys.argv) > 1:
        a = Test()
        b = TestExternal()

        # a.testMeasureRange()

        #a.testMultipartStream()

        #a.testBestTimeSignature()

        a.testMakeAccidentals()