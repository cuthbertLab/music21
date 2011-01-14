import copy, types, random
import functools

import music21 ## needed to properly do isinstance checking
from music21 import note
from music21 import common
from music21 import clef
from music21 import duration
from music21 import measure
from music21 import meter


from music21 import musicxml
musicxmlMod = musicxml # alias as to avoid name conflicts

from music21 import environment
_MOD = 'stream.py'
environLocal = environment.Environment(_MOD)


import doctest, unittest


CLASS_SORT_ORDER = ["Clef", "TempoMark", "KeySignature", "TimeSignature", "Dynamic", "GeneralNote"]

#-------------------------------------------------------------------------------
class GroupException(Exception):
    pass

class ElementException(Exception):
    pass

class StreamException(Exception):
    pass

class StreamBundleException(Exception):
    pass





#-------------------------------------------------------------------------------
class Groups(object):   
    '''A list of strings used to identify associations that an element might 
    have. 

    Presently, this does not subclass list; ultimately, it should.
    '''
    def __init__(self):
        self._ids = []
        self._index = 0

    def __repr__(self):
        return repr(self._ids)

    def append(self, groupId):
        '''Add a group identifier string to an ElementWrapper

        >>> a = Groups()
        >>> a.append('red')
        >>> a
        ['red']
        '''
        if not common.isStr(groupId):
            raise GroupException('group identifiers must be strings')
        if groupId not in self._ids:
            self._ids.append(groupId)

    def remove(self, groupId):
        '''

        >>> a = Groups()
        >>> a.append('red')
        >>> len(a)
        1
        >>> a.remove('red')
        >>> len(a)
        0
        '''
        if groupId in self._ids:
            self._ids.remove(groupId)
        else: # python lists normally raise a value error when trying 
            # to remove an element from a list and it does not exist
            raise GroupException('%s is not in Group' % groupId)

    def __len__(self):
        return len(self._ids)        


    def __iter__(self):
        '''A Group can return an iterator.
        '''
        return self


    def __eq__(self, other):
        '''Test ElementWrapper equality.
        '''
        if not isinstance(other, Groups):
            return False
        if (self._ids.sort() == other._ids.sort()):
            return True
        else:
            return False

    def __ne__(self, other):
        '''
        '''
        if other == None or not isinstance(other, Groups):
            return True
        if (self._ids.sort() == other._ids.sort()):
            return False
        else:
            return True

    def next(self):
        '''Method for treating this object as an iterator

        >>> a = Groups()
        >>> a.append('red')
        >>> a.append('blue')
        >>> for x in a:
        ...     print(x)
        red
        blue
        >>> if 'red' in a: print(True)
        True
        '''
        # this will return the self._elementsSorted list
        # unless it needs to be sorted
        if self._index < -self.__len__() or self._index >= self.__len__():
            self._index = 0 # reset for next run
            raise StopIteration

        out = self._ids[self._index]
        self._index = self._index + 1
        return out




#-------------------------------------------------------------------------------
class ElementWrapper(object):
    '''An individual object within a stream.

    __slots__ might be defined for efficiency?

    groups is an optional list identifying internal subcollections
        to which this element belongs.
    id is an optional string identifying this ElementWrapper
    '''
    def __init__(self, obj=None):
        self._obj = obj # object stored here

        self._offset = duration.DurationUnit()
        self._priority = 0 # numerical representation 
        self.id = None # optional string identifiers; may or not be unique

        # list of string identifiers, assumed to not be unique
        self.groups = Groups()


    def clone(self, copyObj=True):
        '''Try to use clone() methods if available. Otherwise, deep copy.

        Need a parameter to determine if we clone contained object or not.
        
        >>> a = ElementWrapper()
        >>> n = note.Note('A-')
        >>> n.quarterLength = 2
        >>> a.obj = n
        >>> b = a.clone()
        >>> b.duration.quarterLength = 1
        >>> a.obj.quarterLength
        2.0
        >>> b.obj.quarterLength
        1.0


        >>> data = [3,4,5]
        >>> a = ElementWrapper(data)
        >>> a.offset = 3
        >>> b = a.clone(False)
        >>> b.obj
        [3, 4, 5]
        >>> b.offset = 39
        >>> a.offset 
        3
        >>> data.append(6)
        >>> a.obj
        [3, 4, 5, 6]
        >>> b.obj
        [3, 4, 5, 6]
        >>> c = b.clone(True)
        >>> data.append(7)
        >>> c.obj
        [3, 4, 5, 6]
        >>> a.obj
        [3, 4, 5, 6, 7]
        >>> b.obj
        [3, 4, 5, 6, 7]

        >>> data = duration.Duration()
        >>> a = ElementWrapper(data)
        >>> b = a.clone()
        >>> b.obj.quarterLength = 30
        >>> a.obj.quarterLength 
        0.0
        >>> c = a.clone(False)
        >>> a.obj.quarterLength = 56
        >>> c.obj.quarterLength
        56.0

        '''
        new = ElementWrapper()
        if hasattr(self._obj, 'clone'):
            if copyObj:
                new._obj = self._obj.clone()
            else: # store a reference
                new._obj = self._obj
        else:
            if copyObj:
                new._obj = copy.deepcopy(self._obj)
            else: # store a reference
                new._obj = self._obj

        new._offset = self._offset.clone() # a DurationUnit 
        new._priority = self._priority # copy?
        new.id = self.id
        new.groups = copy.deepcopy(self.groups)
        # new.parents = copy.deepcopy(self.parents)

        return new


    def __repr__(self):
        if (self.id is not None):
            return '<%s id=%s offset=%s obj=%s>' % \
                (self.__class__.__name__, self.id, self.offset, self._obj)
        else:
            return '<%s offset=%s obj=%s>' % \
                (self.__class__.__name__, self.offset, self._obj)


    def __eq__(self, other):
        '''Test ElementWrapper equality.

        This does not look at Parents. 

        >>> a = ElementWrapper()
        >>> a.offset = 3
        >>> b = ElementWrapper()
        >>> b.offset = 5
        >>> c = ElementWrapper()
        >>> c.offset = 3
        >>> a == c
        True
        >>> id(a) != id(c)
        True

        >>> a = ElementWrapper()
        >>> a == None
        False
        '''
        if other == None or not isinstance(other, ElementWrapper):
            return False

        if (self._obj == other._obj and self._offset == other._offset and 
            self._priority == other._priority and self.id == other.id and
            self.groups == other.groups):
            return True
        else:
            return False

    def __ne__(self, other):
        '''
        '''
        if other == None or not isinstance(other, ElementWrapper):
            return True
        if (self._obj == other._obj and self._offset == other._offset and 
            self._priority == other._priority and self.id == other.id and
            self.groups == other.groups):
            return False
        else:
            return True


    #---------------------------------------------------------------------------
    # properties

    def _getOffset(self):
        return self._offset.quarterLength

    def _setOffset(self, offset):
        '''Set the offset as a quarterNote length

        >>> a = ElementWrapper(note.Note('A#'))
        >>> a.offset = 23
        >>> a.offset
        23
        '''
        if common.isNum(offset):
            # if a number assume it is a quarter length
            self._offset = duration.DurationUnit()

            # as offset durations will rarely be represented as notation
            # it seems that it is more efficient to leave them unlinked 
            # until a notation representation is needed. at that time,
            # when the duraton is linked, resolving a duration of 31.5 or 
            # otherwise can be dealt with. 
            self._offset.unlink() # always unlink? 
            self._offset.quarterLength = offset
        else:
            # need to permit Duration object assignment here
            raise ElementException('we must only set numbers for now, not %s' % offset)
            #self._offset = offset

    offset = property(_getOffset, _setOffset)


    def _getDuration(self):
        '''Gets the duration of the component object if available, otherwise
        returns None.
        >>> a = ElementWrapper()
        >>> n = note.Note('F#')
        >>> n.quarterLength = 2
        >>> n.duration.quarterLength 
        2.0
        >>> a.obj = n
        >>> a.duration.quarterLength
        2.0
        '''
        if hasattr(self._obj, 'duration'):
            return self._obj.duration
        else:
            return None

    def _setDuration(self, durationObj):
        '''Set the offset as a quarterNote length

        '''
        if (isinstance(durationObj, duration.DurationCommon) and 
            hasattr(self._obj, 'duration')):
            # if a number assume it is a quarter length
            self._obj.duration = durationObj
        else:
            # need to permit Duration object assignment here
            raise ElementException('this must be a Duration object, not %s' % durationObj)

    duration = property(_getDuration, _setDuration)



    def _getObject(self):
        return self._obj

    def _setObject(self, obj):
        self._obj = obj
        if (hasattr(obj, "duration") and obj.duration is not None):
            self.duration = obj.duration
        else:
            self.duration = note.ZeroDuration()

    obj = property(_getObject, _setObject)


    def _getPriority(self):
        return self._priority

    def _setPriority(self, value):
        '''
        Priority specifies the order of processing from 
        left (LOWEST #) to right (HIGHEST #) of objects at the
        same offset.  For instance, if you want a key change and a clef change
        to happen at the same time but the key change to appear
        first, then set: keySigElement.priority = 1; clefElement.priority = 2
        this might be a slightly counterintuitive numbering of priority, but
        it does mean, for instance, if you had two elements at the same 
        offset, an allegro tempo change and an andante tempo change, 
        then the tempo change with the higher priority number would 
        apply to the following notes (by being processed
        second).
        
        Default priority is 0; thus negative priorities are encouraged
        to have Elements that appear non-priority set elements.
        
        In case of tie, there are defined class sort orders defined in
        music21.stream.CLASS_SORT_ORDER.  For instance, a key signature
        change appears before a time signature change before a note at the
        same offset.  This produces the familiar order of materials at the
        start of a musical score.
        
        >>> a = ElementWrapper()
        >>> a.priority = 3
        >>> a.priority = 'high'
        Traceback (most recent call last):
        ElementException: priority values must be numbers.
        '''
        if not common.isNum(value):
            raise ElementException('priority values must be numbers.')
        self._priority = value

    priority = property(_getPriority, _setPriority)


    #---------------------------------------------------------------------------
    # utility methods

    def isClass(self, className):
        '''This might be used to quickly extract a number of elements by classes
        from a Stream

        >>> a = ElementWrapper(None)
        >>> a.isClass(note.Note)
        False
        >>> a.isClass(types.NoneType)
        True
        >>> b = ElementWrapper(note.Note('A4'))
        >>> b.isClass(note.Note)
        True
        >>> b.isClass(types.NoneType)
        False
        '''
        if isinstance(self._obj, className):
            return True
        else:
            return False




#-------------------------------------------------------------------------------
class Stream(ElementWrapper):
    '''This is basic unit for timed Elements. In most cases these timed
    Elements will be of the same class of things; notes, clefs, etc. This is
    not required. If Elements in Streams have a duration attribute, it will
    be assumed that it is a Duration or DurationUnit object. 

    Streams may be embedded within other Streams. For Streams embedded in Streams, 
    like all other Elements, offset is determined by an optional initial 
    offset value. If this value is
    zero offsets are always assumed to be relative to the position of the 
    outermost stream [IS THIS A GOOD IDEA?]. 
    Otherwise, offset values might be set be the same as the 
    parent stream or in some other relative arrangement. 
    
    
    '''

    def __init__(self):
        '''
        
        '''
        ElementWrapper.__init__(self)

        # self._elements stores ElementWrapper objects. These are not ordered.
        # this should have a public attribute/property self.elements
        self._elements = []
        self._obj = self._elements

        # option for representation
        self.views = ['shallow', 'flat']
        self._view = 'shallow' # 
        self._viewSingleCall = None # temporary view for single attribute calls

        # self._offset is defined in subclass
        #self._offset = duration.DurationUnit()
        self._offset.quarterLength = 0

        # store a sorted version of elements that is only updated 
        # when requested and out of date
        self._unsorted = True
        # this stores a flat representation with offset, priority, dur, ElementWrapper
        self._elementsSorted = None 

        self._index = 0


    def clone(self, copyObj=True):
        '''Not sure this works recursively 
        '''
        new = Stream()
        if copyObj:
            for element in self._elements:
                new.append(element.clone(copyObj))
        else:
            new._elements = self._elements
            new._obj = new._elements # need to link

        new._unsorted = True
        # these do not need to be copied
        new._offset = self._offset.clone()
        new.id = self.id
        new.groups = self.groups


        new._view = self._view
        return new

    # for backwards compat
    def flatten(self):
        self.setView('flat')

    def setView(self, value):
        '''Need recurse through all embeded Streams and set them to flat too.
        '''
        if value not in self.views:
            raise StreamException('%s is not a valid view' % value)
        self._view = value
        for element in self._elements:
            if isinstance(element, Stream):  
                element.setView(value)




    #---------------------------------------------------------------------------
    # adding and editing Elements and Streams

    def __add__(self, other):
        '''Mixes two Streams; this will not shift any offsets; it will simply
        combine the elements.

        This method might, alternatively, add at the end of the last duration

        >>> a = Stream()
        >>> for x in range(4):
        ...     e = ElementWrapper(note.Note('G#'))
        ...     e.offset = x * 3
        ...     a.append(e)
        >>> b = Stream()
        >>> for x in range(4):
        ...     e = ElementWrapper(note.Note('G#'))
        ...     e.offset = x * 3
        ...     b.append(e)
        >>> c = a + b
        >>> len(c)
        8
        '''        
        if not isinstance(other, Stream): # if an element or a stream
            raise StreamException('cannot add anything by another Stream')

        new = Stream()
        # use public method at least for other.elements; better both... 
        #  do not have to recurse to here
        new._elements = self._elements + other._elements
        new._obj = new._elements
        new._unsorted = True
        return new


#     def _shallowEndDuration(self):
#         '''Get the max offset for all _elements
#         '''
#         # may need to add self.offset
#         max = 0.0
#         for element in self._elements:
#             if element.duration == None and element.offset > max:
#                 max = element.offset
#             if element.duration != None:
#                 if element.duration.quarterLength + element.offset > max:
#                     max = element.duration.quarterLength + element.offset
#         return max

    def _shallowEndDurationLast(self):
        '''Get the last added Elements offset or offset + duration
        '''
        if len(self._elements) == 0:
            return 0.0 # may need to return self.offset
        element = self._elements[-1]
        if element.duration == None:
            return element.offset
        else:
            return element.offset + element.duration.quarterLength



    def addNext(self, other, offsetShift=0):
        '''Add objects or Elements (including other Streams) to the Stream after 
        the ElementWrapper with the lastly added onset.  The new element will have an offset equal to the last ElementWrapper's offset plus the last ElementWrapper's duration (that is, it will start directly after the last ElementWrapper ends). 
        If last object has no duration, the 
        new object will be added at the same offset as the last.

        Optional offsetShift will put a gap between the previous last ElementWrapper 
        an the new element
        
        QUESTION: if we create a new ElementWrapper should it have the same groups
        as the ElementWrapper it is following?  I vote yes, since that makes easy things
        easier but hard things still possible.

        >>> a = Stream()
        >>> notes = []
        >>> for x in range(0,3):
        ...     n = note.Note('G#')
        ...     n.duration.quarterLength = 3
        ...     notes.append(n)
        >>> a.addNext(notes[0])
        >>> a.getEndOffset(), a.getEndDuration()
        (0.0, 3.0)
        >>> a.addNext(notes[1])
        >>> a.getEndOffset(), a.getEndDuration()
        (3.0, 6.0)
        >>> a.addNext(notes[2])
        >>> a.getEndOffset(), a.getEndDuration()
        (6.0, 9.0)
        >>> a.isSequence()
        True
        >>> a.isCloud()
        False
        '''
        # assume other is an element or stream
        if isinstance(other, ElementWrapper): # if an element or a stream
            element = other
        else: # create an element for this stream
            element = ElementWrapper(other)

        if self._view in ['shallow']:
            # if shallow, simply get the offset + dur of the last-added
            # element
            element.offset = self._shallowEndDurationLast() + offsetShift
        elif self._view in ['flat']:
            # if flat, we need to find the end duration; this can be done 
            # w/o sorting, but Stream offsets have to be taken into account
            element.offset = self.getEndDuration() + offsetShift
        self._elements.append(element)
        self._unsorted = True


    def sort(self):
        '''Sort the _elementsSorted list; this is called internally when    
        needed. 
        '''
        self._elementsSorted.sort()


    def append(self, item):
        '''Append an ElementWrapper to the Stream. 

        >>> a = Stream()
        >>> a.append(None)
        >>> a.append(note.Note('G#'))
        >>> len(a)
        2
        '''
        if not isinstance(item, ElementWrapper): # if not an element, embed
            element = ElementWrapper(item)
        else:
            element = item
        # store light copys to last
        self._elementLast = element.clone(copyObj=False)
        self._elements.append(element)

        if not self._unsorted:
            self._unsorted = True


    def insertAtOffset(self, item, offset):
        '''Append an object with a given offset. Wrap in an ElementWrapper and 
        set offset time. 

        >>> a = Stream()
        '''
        if not isinstance(item, ElementWrapper): # if not an element, embed
            element = ElementWrapper(item)
        else:
            element = item
        element.offset = offset
        self._elements.append(element)

        if not self._unsorted:
            self._unsorted = True



    def insert(self, indexList, item):
        '''Insertion can only happen in the unflattend representation
        A list of one or indices can be given
        '''
        pass





    #---------------------------------------------------------------------------
    # manipulating all ElementWrapper id attributes

    def setIdElements(self, id, classFilter=None):
        '''Set all componenent Elements to the given id. Do not change the id
        of the Stream
        
        Alternative names: setElementIdByClass()

        >>> a = Stream()
        >>> a.repeatCopy(note.Note('A-'), range(30))
        >>> a.repeatCopy(note.Note('E-'), range(30, 60))
        >>> a.setIdElements('flute')
        >>> a[0].id 
        'flute'
        >>> ref = a.getIdElements()
        >>> len(ref)
        1
        >>> ref['flute']
        60

        >>> b = Stream()
        >>> b.repeatCopy(None, range(30))
        >>> b.repeatCopy(note.Note('E-'), range(30, 60))
        >>> b.setIdElements('flute', note.Note)
        >>> a[0].id 
        'flute'
        >>> ref = b.getIdElements()
        >>> ref['flute']
        30

        '''
        # elements do not have to be sorted
        for element in self.getElements():
            if classFilter != None:
                if element.isClass(classFilter):
                    element.id = id
            else:
                element.id = id

    def getIdElements(self, classFilter=None):
        '''Get all componenent Elements id as dictionary of id:count entries.

        Alternative name: getElementIdByClass()
        '''
        post = {}
        for element in self.getElements():
            count = False
            if classFilter != None:
                if element.isClass(classFilter):
                    count = True
            else:
                count = True
            if count:
                if element.id not in post.keys():
                    post[element.id] = 0
                post[element.id] += 1
        return post



    #---------------------------------------------------------------------------
    # stream as iterator and list
    # Mutable sequences should provide methods append(), count(), index(), extend(), insert(), pop(), remove(), reverse() and sort(), like Python standard list objects.


    def __len__(self):
        '''Get the total number of elements. Recursively check internals. 

        >>> a = Stream()
        >>> for x in range(4):
        ...     e = ElementWrapper(note.Note('G#'))
        ...     e.offset = x * 3
        ...     a.append(e)
        >>> len(a)
        4

        >>> a = Stream()
        >>> a.repeatCopy(None, range(10))
        >>> b = Stream()    
        >>> for x in range(4):
        ...     b.append(a) # append streams
        >>> len(b)
        4
        >>> b.flatten()
        >>> len(b)
        40
        '''
        count = 0
        for element in self._elements:
            # recuse when flat
            if self._view in ['flat'] and isinstance(
                element, Stream):  
                count += element.__len__()
            else:
                count += 1
        return count



    def __iter__(self):
        '''A Stream can return an iterator.
        '''
        return self


    def next(self):
        '''Method for treating this object as an iterator
        Returns each element in sort order; could be in tree order. 

        >>> a = Stream()
        >>> a.fillNone(6)
        >>> b = []
        >>> for x in a:
        ...     b.append(x.offset) # get just offset
        >>> b
        [0, 1, 2, 3, 4, 5]
        '''
        # this will return the self._elementsSorted list
        # unless it needs to be sorted
        if self._index < 0 or self._index >= self.__len__():
            self._index = 0 # reset for next run
            raise StopIteration

        out = self.getElements()[self._index] 
        self._index += 1
        return out


    def __getitem__(self, key):
        '''Get an ElementWrapper from the stream in sorted flat order.

        If getting an item in the unsorted, nested order, we can only access 
        Elements on the top-most level of self._elements. 

        >>> a = Stream()
        >>> a.fillNone(6)
        >>> a[1].offset
        1
        >>> a[5].offset
        5
        '''
        # this will return the self._elementsSorted list
        # unless it needs to be sorted
        if key >= self.__len__():
            raise IndexError('got key %s but length %s' % (key, self.__len__()))
        return self.getElements()[key] 





    def _delete(self, indexList, scope=None):
        '''Low level access to self._elements. indexList stores a list
        if indices that are found in one or emore self._elements. 

        >>> a = Stream()
        >>> a.repeatCopy(None, range(30))
        >>> b = Stream()
        >>> b.repeatCopy(None, range(30))
        >>> c = Stream()
        >>> c.repeatCopy(None, range(30))
        >>> candidate = c[23]
        >>> candidate.id = 'tagged'
        >>> c[23].id   
        'tagged'
        >>> b.append(c)
        >>> a.append(b) # a holds all recursively
        >>> a.flatten()
        >>> len(a)
        90
        >>> len(a._elements)
        31
        >>> junk = a._delete([30, 30, 23])
        >>> len(a)
        89
        >>> len(a._elements)
        31
        >>> junk.id
        'tagged'
        >>> print(a._access([30, 30, 23]).id)
        None
        '''
        if scope == None:
            scope = self
        # get ElementWrapper at first index
        post = scope._elements[indexList[0]]
        if len(indexList) == 1:
            # pop out the object at this index
            post = scope._elements.pop(indexList[0])
        else:
            indexList = indexList[1:] # crop indices
            # call with what is left of index and the last found
            # ElementWrapper as scope
            post = self._delete(indexList, post)

        scope._unsorted = True
        return post

    def _access(self, indexList, scope=None):
        '''Low level access to self._elements. indexList stores a list
        if indices that are found in one or emore self._elements. 

        >>> a = Stream()
        >>> a.repeatCopy(None, range(30))
        >>> b = Stream()
        >>> b.repeatCopy(None, range(30))
        >>> c = Stream()
        >>> c.repeatCopy(None, range(30))
        >>> candidate = c[23]
        >>> candidate.id = 'tagged'
        >>> c[23].id   
        'tagged'
        >>> b.append(c)
        >>> a.append(b) # a holds all recursivey
        >>> a._access([3]).offset
        3
        >>> a._access([30, 30, 23]).offset
        23
        >>> a._access([30, 30, 23]).id
        'tagged'
        '''
        if scope == None:
            scope = self
        # get ElementWrapper at first index
        post = scope._elements[indexList[0]]
        if len(indexList) == 1:
            return post # return object if no more indices
        else:
            indexList = indexList[1:] # crop indices
            # call with what is left of index and the last found
            # ElementWrapper as scope
            post = self._access(indexList, post)
        return post

    def _find(self, element, scope=None):
        '''Given an element inside of self._elements[], search through
        nested structure to get that element.
        Address is a list of indices to get to that element

        >>> a = Stream()
        >>> a.repeatCopy(None, range(30))
        >>> b = Stream()
        >>> b.repeatCopy(None, range(30))
        >>> c = Stream()
        >>> c.repeatCopy(None, range(30))
        >>> candidate = c[23]
        >>> candidate.id = 'tagged'
        >>> c[23].id   
        'tagged'
        >>> b.append(c)
        >>> a.append(b) # a holds all recursivey
        >>> a.flatten()
        >>> len(a) # flattened length
        90
        >>> len(a._elements) # unflattened length
        31
        >>> # id(a._elements[30][30][23]) == id(candidate)
        >>> a._find(candidate)
        [30, 30, 23]
        >>> a._access(a._find(candidate)).id
        'tagged'
        '''
        # much match memory id, not object __eq__
        idSeek = id(element) 
        address = [] # a list indices into self._elements
        i = 0
        # the lenght of self._elements is not the same as __len__       
        # as __len__ take recursion into account
        if scope == None:
            scope = self
        for i in range(len(scope._elements)):
            candidate = scope._elements[i]
            if isinstance(candidate, Stream):
                postRecurseAddress = candidate._find(element, candidate)
                if postRecurseAddress != []:
                    address.append(i) # add outer first
                    address += postRecurseAddress
            else:
                if idSeek == id(candidate):
                    address.append(i)
                    return address
        return address # may be empty list if not found


    def _setListRecurse(self, srcList, indices, value):
        '''Given a nested list srcList, and list of indices that should be 
        used to access these lists in order, set the value specified by value
        to the designated index positions.
        
        Needed for __setitem__ below

        >>> a = [3,4,[5,6,[7,8]]]
        >>> indices = [2,2,1]
        >>> b = Stream()
        >>> b._setListRecurse(a, indices, 2345)
        >>> a[2][2][1]
        2345
        '''
        if len(indices) != 1:
            newSrcList = srcList[indices[0]]
            newIndices = indices[1:]
            self._setListRecurse(newSrcList, newIndices, value)
        else:
            srcList[indices[0]] = value

# alternative method for gettting; this does not work
# for setting, it seems. 
# >>> lst = ['a', 'b', ['aa', ['aaa', 'bbb', 'ccc'], 'cc']] 
# >>> from functools import reduce 
# >>> lst = ['a', 'b', ['aa', ['aaa', 'bbb', 'ccc'], 'cc']] 
# >>> reduce(list.__getitem__, (2, 1, 0), lst) 


    def __setitem__(self, index, value):
        '''Insert items at index positions. Index positions are may be for
        flat or nested 

        >>> a = Stream()
        >>> a.repeatCopy(None, range(10))
        >>> b = Stream()
        >>> b.repeatCopy(a, range(0, 100, 10))
        >>> b[6][4].id = 'testing'
        >>> b.flat.index(b[6][4])
        64
        >>> b.flat[64] = ElementWrapper(None)
        >>> b[6][4].id == None
        True
        '''
        if self._view in ['shallow']:
            if not isinstance(value, ElementWrapper): # if not an element, embed
                self._elements[index] = ElementWrapper(value)
            else:
                self._elements[index] = value
        elif self._view in ['flat']:
            dst = self.getElements()[index]
            address = self._find(dst)
            if not isinstance(value, ElementWrapper): # if not an element, embed
                value = ElementWrapper(value)
                # get old offset if not an element
                value.offset = dst.offset

            self._setListRecurse(self._elements, address, value)
            
        self._unsorted = True


    def pop(self, index):
        '''Remove and return element form the sorted list at the specified
        position.

        >>> a = Stream()
        >>> a.repeatCopy(None, range(10))
        >>> b = Stream()
        >>> b.repeatCopy(a, range(0, 100, 10))
        >>> d = a.clone()
        >>> d[7].id = 'tagged'
        >>> d.offset = 110
        >>> b.append(d)
        >>> len(b.shallow)
        11
        >>> len(b.flat)
        110
        >>> b.flat.index(d[7])
        107
        >>> obj = b.flat.pop(107)
        >>> len(b.flat)
        109
        >>> obj.id == 'tagged'
        True

        >>> a = Stream()
        >>> a.repeatCopy(None, [4,3,1,8,5])
        >>> b = Stream()
        >>> b.repeatCopy(a, [30, 0, 20, 80, 75])
        >>> len(b.shallow)
        5
        >>> len(b.flat)
        25
        >>> b.shallow[-1].offset
        75
        >>> b.flat[-1].offset
        8
        >>> b.flat[-1].id = 'last event'
        >>> e = b.flat.pop(b.flat.index(b.flat[-1]))
        >>> len(b.flat)
        24
        >>> e.id
        'last event'
        >>> e.offset = 0
        >>> e.id = 'first event'
        >>> b.append(e)
        >>> len(b) # shallow is default
        6
        >>> len(b.flat) # shallow is default
        25
        >>> b.flat[0].id
        'first event'
        >>> b.index(e)
        5
        '''
        if self._view in ['shallow']:
            obj = self._elements.pop(index)
        elif self._view in ['flat']:
            obj = self.getElements()[index]
            address = self._find(obj)
            obj = self._delete(address)

        self._unsorted = True
        return obj


    def remove(self, element):
        '''
        >>> a = Stream()
        >>> a.repeatCopy(None, range(10))
        >>> b = Stream()
        >>> b.repeatCopy(a, range(0, 100, 10))
        >>> d = a.clone()
        >>> d[7].id = 'tagged'
        >>> d.offset = 110
        >>> b.append(d)
        >>> len(b.flat)
        110
        >>> b.shallow.remove(d[7])
        Traceback (most recent call last):
        ValueError: list.remove(x): x not in list
        >>> b.flat.remove(d[7])
        >>> len(b.flat)
        109
        '''
        if self._view in ['shallow']:
            self._elements.remove(element)
        elif self._view in ['flat']:
            address = self._find(element)
            obj = self._delete(address)
        self._unsorted = True


    def index(self, element):
        '''
        >>> a = Stream()
        >>> a.repeatCopy(None, range(10))
        >>> b = Stream()
        >>> b.repeatCopy(a, range(0, 100, 10))
        >>> d = a.clone()
        >>> d[7].id = 'tagged'
        >>> d.offset = 110
        >>> b.append(d)
        >>> len(b.shallow)
        11
        >>> len(b.flat)
        110
        >>> b.flat.index(d[7])
        107
        >>> b.shallow.index(d[7])
        Traceback (most recent call last):
        ValueError: list.index(x): x not in list
        >>> b.flat[107].id
        'tagged'
        >>> b.flat[107].id = 'tagged again'
        >>> b[10][7].id
        'tagged again'
        '''
#         >>> b.setView('flat')
#         >>> b.index(d[7])
#         [10, 7]

        if self._view in ['shallow']:
            return self.getElements().index(element)
        elif self._view in ['flat']:
            return self.getElements().index(element)





    #---------------------------------------------------------------------------
    # utilities for creating large numbers of elements


    def repeatCopy(self, item, offsets):
        '''Given an object, create many copies at the possitioins specified by 
        the offset list.

        Alternative names: copyRepeatedly(), repeatClone()

        >>> a = Stream()
        >>> n = note.Note('G-')
        >>> n.quarterLength = 1
        >>> a.repeatCopy(n, range(30))
        >>> len(a)
        30
        >>> a[10].offset
        10
        '''
        if not isinstance(item, ElementWrapper): # if not an element, embed
            element = ElementWrapper(item)
        else:
            element = item

        for offset in offsets:
            elementCopy = element.clone(copyObj=True)
            elementCopy.offset = offset
            self.append(elementCopy)


    def fillNone(self, number):
        '''For use in testing.
        '''
        self.repeatCopy(None, range(number))


    #---------------------------------------------------------------------------
    def _offsetList(self, elements):
        '''Presentation of elements with derived offsets. 
        Can format must be use for sorting. 

        Returns a flat list of tuples in the form
        (offset, priority, dur, element). 

        All embedded strams are flattened into a single list.

        Priority comes before duration because elements with the same offset are
        sorted first by priority, then duration

        If duration is not defined, it is given the value None. 
        '''
        post = []
        for element in elements:
            if isinstance(element, Stream): # recurse
                # element is a stream
                # use public method getSortedOffsets() for efficiency  
                # need to add this Streams offset to all offset obtained
                elementSorted = [(a+self._getOffset(), b, c, d) 
                    for a, b, c, d in element.getSortedOffsets()]
                post += elementSorted
            else: 
                if hasattr(element.obj, 'duration'):
                    dur = element.obj.duration.quarterLength
                else:
                    dur = None
                # this orientation asures that simultaneities with shorter
                # durations come first
                post.append((element.offset + self._getOffset(),
                             element.priority, 
                             dur, 
                             element))
        return post


#     def _offsetSort(self, elements):
#         '''Raw sorting routine. May operate on any elements. 
# 
#         Returns a flat list of tuples in the form
#         (offset, priority, dur, element). 
# 
#         All embedded strams are flattened into a single list.
# 
#         Priority comes before duration because elements with the same offset are
#         sorted first by priority, then duration
# 
#         If duration is not defined, it is given the value None. 
#         '''
#         # print _MOD, 'calling sort routine'
#         post = []
#         for element in elements:
#             if isinstance(element, Stream): # recurse
#                 # element is a stream
#                 # use public method getSortedOffsets() for efficiency  
#                 # need to add this Streams offset to all offset obtained
#                 elementSorted = [(a+self._getOffset(), b, c, d) 
#                     for a, b, c, d in element.getSortedOffsets()]
#                 post += elementSorted
#             else: 
#                 if hasattr(element.obj, 'duration'):
#                     dur = element.obj.duration.quarterLength
#                 else:
#                     dur = None
#                 # this orientation asures that simultaneities with shorter
#                 # durations come first
#                 post.append((element.offset + self._getOffset(),
#                              element.priority, 
#                              dur, 
#                              element))
#         post.sort()
#         return post


    def getSortedOffsets(self, elementsOnly=False):
        '''Create a sorted list of elements. Flatten any internal Streams.

        Returns a flat list of tuples in the form
        (offset, priority, dur, element). 

        >>> a = Stream()
        >>> for x in range(4):
        ...     e = ElementWrapper(note.Note('G#'))
        ...     e.offset = x * 3
        ...     a.append(e)
        ...
        >>> a.getSortedOffsets()[0][0]
        0
        >>> a.getSortedOffsets()[1][0]
        3
        >>> a.getSortedOffsets()[2][0]
        6
        >>> a.getSortedOffsets(elementsOnly=True)[2].offset
        6
        >>> a.append(a.clone()) # recursive test
        >>> len(a.getSortedOffsets())
        8
        '''

        if self._unsorted or self._elementsSorted == None: # need to update
            #self._elementsSorted = self._offsetSort(self._elements)
            self._elementsSorted = self._offsetList(self._elements)
            self.sort()
            self._unsorted = False

        if elementsOnly:
            return [d for a, b, c, d in self._elementsSorted]
        else:
            return self._elementsSorted


    def _extract(self, view='flat', elements=None):
        '''Return all elements as a list of Elements. Recurse down
        all Streams to gather all sub Elements.

        >>> a = Stream()
        >>> a.repeatCopy(None, range(10))
        >>> b = Stream()
        >>> for x in range(4):
        ...     b.append(a) # append streams
        >>> c = b._extract()
        >>> len(c)
        40
        '''
        if elements == None:
            elements = self._elements

        if view == 'shallow':
            return elements
        # this is gathered in positional order; the resulsts are not sorted
        elif view in ['flat', 'deep']:
            post = []
            for element in elements:
                if isinstance(element, Stream): # recurse
                    post += element._extract()
                else:
                    post.append(element)
            return post


    def getElements(self):
        '''Get all Elements, either sorted or not, in a list.

        '''
        if self._view in ['shallow']:
            # these might also be sorted at times?
            return self._extract(self._view)
        elif self._view in ['deep']:
            # these returns falt elements un osrted
            return self._extract(self._view)
        elif self._view == 'flat': # this returns elements sorted
            return self.getSortedOffsets(elementsOnly=True)


    def getFlatStream(self):
        '''In order to get the Elements flat, and retain their tempora
        positioning, we need to change each of their offset as determined
        in relation to all nested Streams.

        >>> a = Stream()
        >>> a.repeatCopy(None, range(10))
        >>> a[9].offset
        9
        >>> b = Stream()
        >>> for x in range(4):
        ...     c = a.clone()
        ...     c.offset = x * 10 
        ...     b.append(c) # append shifted streams
        >>> b.setView('flat')
        >>> b.getElements()[10].offset  # gets a list of all elelemtns
        0
        >>> d = b.getFlatStream()
        >>> len(d)
        40
        >>> d[9].offset
        9
        >>> d[10].offset
        10
        '''
        out = Stream()
        #(offset, priority, dur, element). 
        for a, b, c, d in self.getSortedOffsets():
            new = d.clone()
            new.offset = a 
            out.append(new)
        return out


    #---------------------------------------------------------------------------
    # getting numeric offset values

    def getStartOffset(self):
        '''Get start time of first element.

        This value should take into account a Stream offset

        Note that this cannot be determined by looking at Elements alone, as 
        nested Elements alone do not take into account the offset of their
        Stream container.

        This can be done without sorting; by getting all nested Elements, 
        finding offset shifts, and finding the minimium offset.
        

        >>> a = Stream()
        >>> for x in range(3,5):
        ...     e = ElementWrapper(note.Note('G#'))
        ...     e.offset = x * 3
        ...     a.append(e)
        ...
        >>> a.getStartOffset()
        9
        >>> a.offset = 21
        >>> a.getStartOffset()
        30
        >>> a[0].offset
        9
        '''
        elementsSorted = self.getSortedOffsets()
        if len(elementsSorted) == 0:
            return 0.0
        else:
            return elementsSorted[0][0]


    def getEndOffset(self):
        '''Get start time of last element.

        Note that this cannot be determined by looking at Elements alone, as 
        nested Elements alone do not take into account the offset of their
        Stream container.

        This value should take into account a Stream offset:

        This can be done without sorting; by getting all nested Elements, 
        finding offset shifts, and finding the minimium offset.

        >>> a = Stream()
        >>> for x in range(3,5):
        ...     e = ElementWrapper(note.Note('G#'))
        ...     e.offset = x * 3
        ...     a.append(e)
        ...
        >>> a.getEndOffset()
        12
        >>> a.offset = 30
        >>> a.getEndOffset()
        42

        '''
        elementsSorted = self.getSortedOffsets()
        if len(elementsSorted) == 0:
            return 0.0
        else:
            return elementsSorted[-1][0]


    def getEndDuration(self):
        '''Get end time of last element with duration

        Note that this cannot be determined by looking at Elements alone, as 
        nested Elements alone do not take into account the offset of their
        Stream container.

        Possible return a Duration objectt

        This value should take into account a Stream offset:

        >>> a = Stream()
        >>> for x in range(0,4):
        ...     n = note.Note('G#')
        ...     n.duration.quarterLength = 2
        ...     e = ElementWrapper(n)
        ...     e.offset = x
        ...     a.append(e)
        ...
        >>> a.getEndDuration()
        5.0
        >>> a.offset = 30
        >>> a.getEndDuration()
        35.0

        ''' 
        elementsSorted = self.getSortedOffsets()
        if len(elementsSorted) == 0:
            return 0.0
        elif elementsSorted[-1][2] == None: # if no duration
            return elementsSorted[-1][0]
        else:
            return elementsSorted[-1][0] + elementsSorted[-1][2]


    def getOffsetToNext(self, index):
        '''Given an index position, find out how many offset units are necessary
        to get to the next elemnt

        >>> a = Stream()
        >>> b = ElementWrapper()
        >>> b.offset = 3
        >>> c = ElementWrapper()
        >>> c.offset = 9
        >>> a.append(b)
        >>> a.append(c)
        >>> a.getOffsetToNext(0)
        6
        >>> a.getOffsetToNext(1)
        0
        '''
        # this will return the self._elementsSorted list
        # unless it needs to be sorted
        if index >= self.__len__():
            raise StreamException('no ElementWrapper at stream position %s' % index)

        if index == self.__len__() - 1:
            # this is the last index
            this = self.getElements()[index]
            if this.duration == None:
                return 0
            else:
                return 0 + this.duration

        else:
            this = self.getElements()[index] 
            next = self.getElements()[index+1] 
            return next.offset - this.offset


    #---------------------------------------------------------------------------
    # properties

    def _getTotalDuration(self):
        '''Find span between start and last duration.
        This might take into account a sustain time, separate from duratioin.

        Note that this is not the sum of component durations.

        Note that this cannot be determined by looking at Elements alone, as 
        nested Elements alone do not take into account the offset of their
        Stream container.

        >>> c = Stream()
        >>> for x in range(4):
        ...     n = note.Note('G#')
        ...     n.duration = duration.Duration('quarter')
        ...     e = ElementWrapper(n)
        ...     e.offset = x * 2
        ...     c.append(e)
        ...
        >>> d = c.getSortedOffsets()
        >>> d[0][:-1] # get first two elements
        (0, 0, 1.0)
        >>> d[-1][:-1] # get first two elements
        (6, 0, 1.0)
        >>> c._getTotalDuration()
        7.0

        '''
        sorted = self.getSortedOffsets()

        offsetFirst, priorityFirst, durFirst, objFirst = sorted[0]
        if durFirst == None:
            durFirst = 0
        start = offsetFirst
 
        offsetLast, priorityFirst, durLast, objLast = sorted[-1]
        if durLast == None:
            durLast = 0
        end = offsetLast + durLast

        return end-start


    def _setTotalDuration(self, value):
        '''This could do to things. This could override the real duration with an unlinked value.

        This could also scale and transform all offsets (and optioally durations) to meet the new duration. Note that this duration is in the
        time units, which are assumed to be quarter notes. 
        '''
        pass

    totalDuration = property(_getTotalDuration, _setTotalDuration)



    # override methods from ElementWrapper to provide acess to a duration
    # object that represents the duration of this Stream
    def _getDuration(self):
        '''Gets the duration of the component object if available, otherwise
        returns None
        '''
        dur = duration.DurationUnit()
        dur.quarterLength = self._getTotalDuration()
        return dur

    def _setDuration(self, durationObj):
        '''Set the offset as a quarterNote length

        '''
        if isinstance(durationObj, duration.DurationUnit):
            # if a number assume it is a quarter length
            self._setTotalDuration(durationObj.quarterLength)
        else:
            # need to permit Duration object assignment here
            raise StreamException('this must be a Duration object, not %s' % durationObj)

    duration = property(_getDuration, _setDuration)


    def _setOffset(self, offset):
        '''Set the offset as a quarterNote length
        '''
        # call base class
        ElementWrapper._setOffset(self, offset)
        self._unsorted = True

    offset = property(ElementWrapper._getOffset, _setOffset, doc='''
        >>> a = Stream()
        >>> a.fillNone(6)
        >>> a._getOffset()
        0
        >>> a.offset = 30
        >>> a._getOffset()
        30
    ''')


    def _getFlat(self):
        '''
        >>> a = Stream()
        >>> a.repeatCopy(None, range(10))
        >>> b = Stream()
        >>> b.repeatCopy(a, range(0, 100, 10))
        >>> c = Stream()
        >>> c.repeatCopy(b, range(0, 1000, 100))
        >>> len(c.flat)
        1000
        >>> len(c.shallow)
        10
        '''
        ref = self.clone(copyObj=False)
        ref.setView('flat')
        return ref

    flat = property(_getFlat, None)


    def _getShallow(self):
        ref = self.clone(copyObj=False)
        ref.setView('shallow')
        return ref

    shallow = property(_getShallow, None)




    #---------------------------------------------------------------------------
    # methods that return element objects

    def _getDurSpan(self, elementsSorted):
        '''Given elementsSorted, create a lost of parallel
        values that represent dur spans, or start and end times.
        Assume durations of None imply 0
        '''
        post = []        
        for i in range(len(elementsSorted)):
            offset, priority, dur, obj = elementsSorted[i]
            if dur == None:
                durSpan = (offset, offset)
            else:
                durSpan = (offset, offset+dur)
            post.append(durSpan)
        # assume this is already sorted 
        # index found here will be the same as elementsSorted
        return post

    def _durSpanOverlap(self, a, b, includeCoincidentBoundaries=False):
        '''
        Compare two durSpans and find overlaps; optionally, 
        includ coincident boundaries. a and b are sorted to permit any ordering.

        If an element ends at 3.0 and another starts at 3.0, this may or may not
        be considered an overlap. The includeCoincidentEnds parameter determines
        this behaviour, where ending and starting 3.0 being a type of overlap
        is set by the includeCoincidentBoundaries being True. 

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

        if includeCoincidentBoundaries:
            # if the start of b is before the end of a
            if durSpans[1][0] <= durSpans[0][1]:   
                found = True
        else: # do not include coincident boundaries
            if durSpans[1][0] < durSpans[0][1]:   
                found = True
        return found


    def _findLayering(self, elementsSorted, includeNoneDur=True,
                    includeCoincidentBoundaries=False):
        '''Find any elements in an elementsSorted list that have simultaneities 
        or durations that cause overlaps.

        Returns two lists. Each list contains a list for each element in 
        elementsSorted. If that elements has overalps or simultaneities, 
        all index values that match are included in that list. 

        See testOverlaps, in unit tests, for examples. 
        '''
        # index values are the same as in elementsSorted
        durSpanSorted = self._getDurSpan(elementsSorted)

        # create a list with an entry for each element
        # in each entry, provide indices of all other elements that overalap
        overlapMap = [[] for i in range(len(durSpanSorted))]
        # create a list of keys for events that start at the same time
        simultaneityMap = [[] for i in range(len(durSpanSorted))]

        for i in range(len(durSpanSorted)):
            src = durSpanSorted[i]
            # second entry is duration
            if not includeNoneDur and elementsSorted[i][2] == None: 
                continue
            # compare to all past and following durations
            for j in range(len(durSpanSorted)):
                if j == i: continue # do not compare to self
                dst = durSpanSorted[j]
                # print src, dst, self._durSpanOverlap(src, dst, includeCoincidentBoundaries)

                if src[0] == dst[0]: # if start times are the same
                    simultaneityMap[i].append(j)

                if self._durSpanOverlap(src, dst, includeCoincidentBoundaries):
                    overlapMap[i].append(j)

        return simultaneityMap, overlapMap


    def _consolidateLayering(self, elementsSorted, map):
        '''
        Given elementsSorted and a map of equal lenght with lists of 
        index values that meet a given condition (overlap or simultaneities),
        organize into a dictionary by the relevant or first offset
        '''
        if len(map) != len(elementsSorted):
            raise StreamException('map must be the same length as elementsSorted')

        post = {}
        for i in range(len(map)):
            # print 'examining i:', i
            indices = map[i]
            if len(indices) > 0: 
                srcOffset = elementsSorted[i][0]
                srcElementObj = elementsSorted[i][3]
                dstOffset = None
                # print 'found indices', indices
                # check indices
                for j in indices: # indices of other elements tt overlap
                    elementObj = elementsSorted[j][3]

                    # check if this object has been stored anywhere yet
                    # if so, use the offset of where it was stored to 
                    # to store the src element below
                    store = True
                    for key in post.keys():
                        if elementObj in post[key]:
                            store = False
                            dstOffset = key
                            break
                    if dstOffset == None:
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
                    if dstOffset == None:
                        dstOffset = srcOffset
                    if dstOffset not in post.keys():
                        post[dstOffset] = [] # create dictionary entry
                    # print 'storing offset', dstOffset
                    post[dstOffset].append(srcElementObj)
                    # print post
        return post

    def _findGaps(self):
        '''Search all elements with durations and find any gabs, or
        undefined time regions. 

        
        '''
        pass

    def getSimultaneous(self, includeNoneDur=True):
        '''Find and return any elements that start at the same time. 

        >>> a = Stream()
        >>> for x in range(4):
        ...     e = ElementWrapper(note.Note('G#'))
        ...     e.offset = x * 0
        ...     a.append(e)
        ...
        >>> b = a.getSimultaneous()
        >>> len(b[0]) == 4
        True

        >>> c = Stream()
        >>> for x in range(4):
        ...     e = ElementWrapper(note.Note('G#'))
        ...     e.offset = x * 3
        ...     c.append(e)
        ...
        >>> d = c.getSimultaneous()
        >>> len(d) == 0
        True

        '''
        checkOverlap = False
        elementsSorted = self.getSortedOffsets()
        simultaneityMap, overlapMap = self._findLayering(elementsSorted, 
                                                    includeNoneDur)
        
        return self._consolidateLayering(elementsSorted, simultaneityMap)


    def getOverlaps(self, includeNoneDur=True,
                   includeCoincidentBoundaries=False):
        '''Find any elements that overlap. Overlaping might include elements
        taht have no duration but that are simultaneous. 

        Whether elements with None durations are included is determined by includeNoneDur.

        This example demosntrates end-joing overlaps: there are four quarter notes spaced by quarter notes. Whether or not these count as overalps
        is determined by the includeCoincidentBoundaries parameter. 

        >>> a = Stream()
        >>> for x in range(4):
        ...     n = note.Note('G#')
        ...     n.duration = duration.Duration('quarter')
        ...     e = ElementWrapper(n)
        ...     e.offset = x * 1
        ...     a.append(e)
        ...
        >>> # default is to not include coincident boundaries
        >>> d = a.getOverlaps(True, False) 
        >>> len(d)
        0
        >>> d = a.getOverlaps(True, True) # including coincident boundaries
        >>> len(d)
        1
        >>> len(d[0])
        4

        This example demonstrates simultaneities with durations. 

        >>> a = Stream()
        >>> for x in [0,0,0,0,13,13,13]:
        ...     n = note.Note('G#')
        ...     n.duration = duration.Duration('half')
        ...     e = ElementWrapper(n)
        ...     e.offset = x * 1
        ...     a.append(e)
        ...
        >>> # default is to not include coincident boundaries
        >>> d = a.getOverlaps() 
        >>> len(d[0])
        4
        >>> len(d[13])
        3

        >>> a = Stream()
        >>> for x in [0,0,0,0,3,3,3]:
        ...     n = note.Note('G#')
        ...     n.duration = duration.Duration('whole')
        ...     e = ElementWrapper(n)
        ...     e.offset = x * 1
        ...     a.append(e)
        ...
        >>> # default is to not include coincident boundaries
        >>> d = a.getOverlaps() 
        >>> len(d[0])
        7

        '''
        checkSimultaneity = False
        checkOverlap = True
        elementsSorted = self.getSortedOffsets()

        simultaneityMap, overlapMap = self._findLayering(elementsSorted, 
                                 includeNoneDur, includeCoincidentBoundaries)

        return self._consolidateLayering(elementsSorted, overlapMap)



    def isSequence(self, includeNoneDur=True, 
                         includeCoincidentBoundaries=False):
        '''A stream is a sequence if it has no overlaps.

        

        >>> a = Stream()
        >>> for x in [0,0,0,0,3,3,3]:
        ...     n = note.Note('G#')
        ...     n.duration = duration.Duration('whole')
        ...     e = ElementWrapper(n)
        ...     e.offset = x * 1
        ...     a.append(e)
        ...
        >>> a.isSequence()
        False
        '''
        elementsSorted = self.getSortedOffsets()
        simultaneityMap, overlapMap = self._findLayering(elementsSorted, 
                                 includeNoneDur, includeCoincidentBoundaries)

        post = True
        for indexList in overlapMap:
            if len(indexList) > 0:
                post = False
                break       
        return post
      
    def isCloud(self, includeNoneDur=True, 
                      includeCoincidentBoundaries=False):
        '''
        A stream is a cloud if it includes any overlaps
        '''        
        return not self.isSequence(includeNoneDur, includeCoincidentBoundaries)


    #---------------------------------------------------------------------------
    # getting new streams and elements from streams

    # neew method: getObjectsByClass that returns ElementWrapper.obj
    # shold sort; return a list not a Stream    
    # never return a list of Elements, always return a Stream
    # decomposer streams into losts of component objects
    # get


    def getElementsByClass(self, className, unpackElement=False):
        '''
        return a list of all Elements that match the className
        
        >>> a = Stream()
        >>> a.fillNone(10) # adds Elements with obj == None
        >>> for x in range(4):
        ...     e = ElementWrapper(note.Note('G#'))
        ...     e.offset = x * 3
        ...     a.append(e)
        >>> found = a.getElementsByClass(note.Note)
        >>> len(found)
        4
        >>> found[0].obj.pitch.accidental.name
        'sharp'
        '''
        if unpackElement: # a list of objects
            found = []
        else: # return a Stream     
            found = Stream()

        for elementsSorted in self.getSortedOffsets():
            element = elementsSorted[3]

            if element.isClass(className):
                if unpackElement:   
                    found.append(element.obj)
                else:
                    found.append(element)
        return found



    def countId(self, idSeek, unpackElement=False):
        '''
        return a list of all Elements that match the given id
        
        Perhaps a better name is getElementsByClass() ?

        >>> a = Stream()
        >>> a.fillNone(10) # adds Elements with obj == None
        >>> a[3].id = 'green'
        >>> a[6].id = 'green'
        >>> b = a.countId('green', True)
        >>> len(b)
        2
        '''
        if unpackElement: # a list of objects
            found = []
        else: # return a Stream     
            found = Stream()


        for elementsSorted in self.getSortedOffsets():
            element = elementsSorted[3]
            if element.id == idSeek:
                if unpackElement:   
                    found.append(element.obj)
                else:
                    found.append(element)
        return found




    def getElementsByOffset(self, offsetStart, offsetEnd,
                    includeCoincidentBoundaries=True, onsetOnly=True,
                    unpackElement=False):
        '''Return a list of all Elements that are found within a certain offset time range, specified as start and stop values, and including boundaries

        If onsetOnly is true, only the onset of an event is taken into consideration; the offset is not.

        The time range is taken as the context for the flat representation.

        The includeCoincidentBoundaries option determines if an end boundary
        match is included
        
        >>> a = Stream()
        >>> a.repeatCopy(None, range(10)) # adds Elements with obj == None
        >>> b = a.getElementsByOffset(4,6)
        >>> len(b)
        3
        >>> b = a.getElementsByOffset(4,5.5)
        >>> len(b)
        2

        >>> a = Stream()
        >>> n = note.Note('G')
        >>> n.quarterLength = .5
        >>> a.repeatCopy(n, range(8))
        >>> b = Stream()
        >>> b.repeatCopy(a, [0, 3, 6])
        >>> c = b.getElementsByOffset(2,6.9)
        >>> len(c)
        10
        '''
        if unpackElement: # a list of objects
            found = []
        else: # return a Stream     
            found = Stream()


        #(offset, priority, dur, element). 
        for elementsSorted in self.getSortedOffsets():
            match = False
            offset = elementsSorted[0]
            dur = elementsSorted[2]
            element = elementsSorted[3]

            if dur == None or onsetOnly:          
                elementEnd = offset
            else:
                elementEnd = offset + dur

            if includeCoincidentBoundaries:
                if offset >= offsetStart and elementEnd <= offsetEnd:
                    match = True
            else: # 
                if offset >= offsetStart and elementEnd < offsetEnd:
                    match = True

            if match:
                if unpackElement:   
                    found.append(element.obj)
                else:
                    found.append(element)
        return found




    def filterClass(self, classNames):
        '''Get one or more Streams based on one or more classNames. 
        Note that this will flatten any embedded streams, creating a 
        Stream that does not have the same _elements structure as the source

        Returns a list of Streams.

        >>> a = Stream()
        >>> a.repeatCopy(note.Note('A-'), range(30))
        >>> a.repeatCopy(None, range(30, 60))
        >>> b = a.filterClass([note.Note])[0] # values in a list
        >>> len(b)
        30
        >>> b, c = a.filterClass([note.Note, types.NoneType])
        >>> len(b)
        30
        >>> len(c)
        30
        '''
        post = [Stream() for x in range(len(classNames))]

        for elementsSorted in self.getSortedOffsets():
            element = elementsSorted[3]
            for i in range(len(classNames)):
                if element.isClass(classNames[i]):
                    post[i].append(element)
        return post


    def filterId(self, idNames):
        '''Get one or more Streams based on element id

        Rreturns a list of Streams

        >>> a = Stream()
        >>> a.repeatCopy(note.Note('A-'), range(30))
        >>> a.setIdElements('red')
        >>> b = Stream()
        >>> b.repeatCopy(note.Note('D#'), range(30))
        >>> b.setIdElements('green')
        >>> c = Stream()
        >>> c = a + b
        >>> len(c)
        60
        >>> e, f = c.filterId(['red', 'green'])
        >>> len(e)
        30
        >>> len(f)
        30
        '''
        post = [Stream() for x in range(len(idNames))]

        for elementsSorted in self.getSortedOffsets():
            element = elementsSorted[3]
            for i in range(len(idNames)):
                if element.id == idNames[i]:
                    post[i].append(element)
        return post



    def filterNote(self, includeRests=True):
        '''Extract all notes from this stream and return a NoteStream or 
        a NoteCloud. 
    
        Need to look at notes and determine if this is a cloud or a sequence

        Rreturns a NoteStream

        >>> a = Stream()
        >>> a.repeatCopy(note.Note('A-'), range(30))
        >>> a.repeatCopy(None, range(30))
        >>> b = a.filterNote()
        >>> len(b)
        30
        >>> isinstance(b, NoteStream)
        True
        '''
        post = NoteStream()

        for elementsSorted in self.getSortedOffsets():
            element = elementsSorted[3]
            if element.isClass(note.Note):
                post.append(element)
            if includeRests:
                if element.isClass(note.Rest):
                    post.append(element)
        return post








#-------------------------------------------------------------------------------
class StreamBundle(Stream):
    '''A stream bundle is a Stream that knows what streams are in what slots
    of _elements. This is useful to speed up operations that need to freuquently
    access isolated streams.
    '''

    def __init__(self):
        Stream.__init__(self)
        # store a key, _elements index reference pair
        self._reference = {}


    def __getitem__(self, key):
        '''Note: this override the behavior of Streams in that keys here
        are strings, not index values
        '''
        return self.getStream(key)

    def __setitem__(self, key, value):
        '''Note: this override the behavior of Streams in that keys here
        are strings, not index values
        '''
        self.addStream(key, value)



    def addStream(self, name, streamObj):
        '''Can be used to add or set a Stream
        '''
        if name not in self._reference.keys():
            index = len(self._reference.keys())
            self._reference[name] = index
            self.append(streamObj)
        else:
            self._elements[self._reference[name]].append(streamObj)
        self._unsorted = True


    def getStream(self, name):
        '''
        There may be a more efficient way to do this, but here: a single 
        compose Stream is created and then sorted. 
        '''   
        if name in self._reference.keys():
            return self._elements[self._reference[name]]
        else:
            raise KeyError

    def delStream(self, name):
        '''
        Remove a stream by name. Shift all indices.

        >>> b = Stream()
        >>> b.repeatCopy(None, range(10))
        >>> b.setIdElements('green')
        >>> c = Stream()
        >>> c.repeatCopy(None, range(10))
        >>> c.setIdElements('red')
        >>> d = Stream()
        >>> d.repeatCopy(None, range(10))
        >>> d.setIdElements('blue')
        >>> 
        >>> a = StreamBundle()
        >>> a.addStream('green', b)
        >>> a.addStream('red', c)
        >>> a.addStream('blue', d)
        >>>
        >>> a.getStream('blue')[0].id
        'blue'
        >>> a.getStream('red')[0].id
        'red'
        >>> a.delStream('red')
        >>> a.getStream('blue')[0].id
        'blue'
        '''   
        if name in self._reference.keys():
            i = self._reference[name] # get index to remove
            junk = self._elements.pop(i)
            # shift all indices above this one down one
            for key, value in self._reference.items():
                if value > i:
                    self._reference[key] -= 1
            del self._reference[name]
            del junk
        else:
            raise KeyError


    def keys(self):
        '''
        There may be a more efficient way to do this, but here: a single 
        compose Stream is created and then sorted. 
        '''   
        return self._reference.keys()



#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
# subclasses of Stream

class NoteStream(Stream):
    '''A type of stream that provides utilities for processing a collection of
    Notes as elements. 
    '''
    def __init__(self):
        Stream.__init__(self)


    def getAccidentalDistribution(self):
        '''Test method.

        >>> a = NoteStream()
        >>> a.fillNone(10)
        >>> pitches = ['G#', 'A#', 'B-', 'D-']
        >>> for x in range(len(pitches)):
        ...     n = note.Note(pitches[x])
        ...     n.duration = duration.Duration('quarter')
        ...     e = ElementWrapper(n)
        ...     e.offset = x * 3
        ...     a.append(e)
        >>> found = a.getAccidentalDistribution()
        >>> found['sharp']
        2
        >>> found['flat']
        2
        '''
        found = self.getElementsByClass(note.Note)
        count = {}
        for element in found:
            accName = element.obj.pitch.accidental.name
            if accName not in count.keys():
                count[accName] = 0
            count[accName] += 1
        return count

    def bestClef(self, allowTreble8vb = False):
        '''
        Returns the clef that is the best fit for the sequence

        >>> a = NoteStream()
        >>> for x in range(30):
        ...    n = note.Note()
        ...    n.midi = random.choice(range(60,72))
        ...    a.append(n)
        >>> b = a.bestClef()
        >>> b.line
        2
        >>> b.sign
        'G'

        >>> c = NoteStream()
        >>> for x in range(30):
        ...    n = note.Note()
        ...    n.midi = random.choice(range(35,55))
        ...    c.append(n)
        >>> d = c.bestClef()
        >>> d.line
        4
        >>> d.sign
        'F'

        '''

        totalNotes = 0
        totalHeight = 0.0

        notes = self.getElementsByClass(note.Note, unpackElement=True)
        
        for thisNote in notes:
            totalNotes += 1
            totalHeight += thisNote.diatonicNoteNum
            if thisNote.diatonicNoteNum > 33: # a4
                totalHeight += 3 # bonus
            elif thisNote.diatonicNoteNum < 24: # Bass F or lower
                totalHeight += -3 # bonus
        if totalNotes == 0:
            averageHeight = 29
        else:
            averageHeight = totalHeight / totalNotes

        #if self.debug is True:
        #    print "Average Clef Height: " + str(averageHeight) + " "

        # c4 = 32
        if (allowTreble8vb == False):
            if averageHeight > 28:    # c4
                return clef.TrebleClef()
            else:
                return clef.BassClef()
        else:
            if averageHeight > 32:    # g4
                return clef.TrebleClef()
            elif averageHeight > 26:  # a3
                return clef.Treble8vbClef()
            else:
                return clef.BassClef()


    def _getMusicXML(self):
        '''
        Returns an incomplete mxMeasure object

        '''

        notes = self.getElementsByClass(note.Note, unpackElement=True)
        mxMeasure = musicxmlMod.Measure()
        for note in notes:
            mxMeasure.append(note.musicxml)
        return mxMeasure


    def _setMusicXML(self, item):
        '''
        '''
        pass

    musicxml = property(_getMusicXML, _setMusicXML)    





#-------------------------------------------------------------------------------
class NoteSequence(NoteStream):
    '''A type of stream that automatically configures offset values
    based on note duration. NoteStreams assure that there will be no
    duration overalps. 
    '''
    pass


class NoteCloud(NoteStream):
    '''A type of stream that permits any arrangement of notes
    '''
    pass


#-------------------------------------------------------------------------------
# subclasses of StreamBundle



#-------------------------------------------------------------------------------
class NotationStream(StreamBundle):
    '''A type of StreamBundle w

    could be called NotationStream

    This stores the timed information necessary to create one or more measures
    '''

    def __init__(self):
        '''
        >>> a = NotationStream()
        >>> len(a.getStream('measures'))
        0
        >>> a['measures'].repeatCopy(measure.MeasureUnit(), range(2))
        >>> len(a.getStream('measures'))
        2
        '''
        StreamBundle.__init__(self)

        # stream of measure objects
        self.addStream('measures', Stream())
        # stream of clef objects
        self.addStream('clef', Stream())
        self.addStream('key', Stream())
        self.addStream('meter', Stream())
        self.addStream('dynamics', Stream())


    def _getMX(self):
        '''
        Returns an incomplete mxPart object

        >>> a = NotationStream()
        >>> mxPart = a._getMX()

        '''
        mxPart = musicxmlMod.Part()
        i = 0
        for element in self.getStream('measures'):
            measureObj = elment.obj
            if not isinstance(measure, measure.MeasureUnit):
                raise StreamBundleException('not a MeasureUnit')

            mxMeasure = musicxmlMod.Measure()
            if measureObj.number == None:
                mxMeasure.set('number', i)
            else:
                mxMeasure.set('number', measureObj.number)
            mxPart.append(mxMeasure)
        return mxPart

    def _setMX(self, mxNote):
        '''
        Given a lost of one or more MusicXML Note objects, read in and create
        Duration
        '''
        pass

    mx = property(_getMX, _setMX)    





#-------------------------------------------------------------------------------
class PartStream(StreamBundle):
    '''A type of StreamBundle 

    '''

    def __init__(self):
        StreamBundle.__init__(self)


        # stream of part objects
        self.addStream('parts', StreamBundle())
        # stream of instrument object
        self.addStream('instruments', StreamBundle())
        # a stream of notes
        self.addStream('noteStreams', StreamBundle())

        # a stream of measures; temporary location
        self.addStream('notationStreams', StreamBundle())

        # each part is defined by having an entry in each of the 
        # streams here, in parallel. 

#     def getPartData(self, partId):
#         partObj = self.getStream('parts').getStream(partId)
#         instObj = self.getStream('instruments').getStream(partId)
#         noteStream = self.getStream('noteStreams').getStream(partId)    

    def setData(self, id, partObj, instObj, noteStream, notationStream):
        '''
        >>> b = NoteStream()
        >>> b.repeatCopy(note.Note('g'), range(30))
        >>> c = NoteStream()
        >>> c.repeatCopy(note.Note('f#'), range(30))

        >>> q = NotationStream()
        >>> q.getStream('measures').repeatCopy(measure.MeasureUnit(), range(0,30,4))

        >>> a = PartStream()
        >>> a.setData('flute1', measure.Part(), 'instObjB', b, q)
        >>> a.setData('bass3', measure.Part(), 'instObjC', c, q)

        >>> w = a.getNoteStream('bass3')
        >>> len(w)
        30
        '''

        partStreamBundle = self.getStream('parts')
        partStreamBundle[id] = partObj

        instStreamBundle = self.getStream('instruments')
        instStreamBundle[id] = instObj

        noteStreamBundle = self.getStream('noteStreams')
        noteStreamBundle[id] = noteStream

        notationStreamBundle = self.getStream('notationStreams')
        notationStreamBundle[id] = notationStream



    def getNoteStream(self, partId):
        return self.getStream('noteStreams')[partId]
        

    def _getMX(self):
        '''
        Returns an incomplete mxScore object

        '''
        mxScore = musicxmlMod.Score()
        mxPartList = musicxmlMod.PartList()

        partStreamBundle = self.getStream('parts')
        instStreamBundle = self.getStream('instruments')
        noteStreamBundle = self.getStream('noteStreams')
        notationStreamBundle = self.getStream('notationStreams')


        # keys are valid for all components
        keys = partStreamBundle.keys()
        # note that hese need to be in order
        for partId in keys:
            # music21 part object
            partObject = partStreamBundle[partId].obj
            instObject = instStreamBundle[partId].obj
            # need note stream
            noteStream = noteStreamBundle[partId]
            # do not get .obj here, just element (tt is a stream)
            notationStream = notationStreamBundle[partId]

            mxScorePart = partObject.mx # returns an mxScorePart
            mxScorePart.set('id', partId)
            mxPartList.append(mxScorePart)

            mxPart = musicxmlMod.Part()
            mxPart.set('id', partId)

            measureStream = notationStream.getStream('measures')
            meterStream = notationStream.getStream('meter')

            for i in range(len(measureStream)):
                meterObj = meterStream[i].obj
                measureStart = measureStream[i].offset
                measureEnd = measureStart + meterObj.barDuration.quarterLength

                # print _MOD, measureStart, measureEnd
                mxMeasure = measureStream[i].obj.mx
                # assign a lost of meter objects
                mxAttributes = musicxml.Attributes()
                # meter returns a lost of mxTime objects
                mxAttributes.set('time', meterObj.mx)
                mxMeasure.set('attributes', mxAttributes)

                # return a list of note objects for the valid time span
                for noteObj in noteStream.getElementsByOffset(measureStart,
                    measureEnd, includeCoincidentBoundaries=False, 
                    unpackElement=True):
                    # each Note may return 1 or more musicxml notes
                    mxMeasure.componentList += noteObj.mx               
                mxPart.append(mxMeasure)

            # notes go here; not he same as mxPart
            mxScore.append(mxPart)

        #mxScore.set('partList', mxPartList)
        mxScore.partListObj = mxPartList
        return mxScore

    def _setMX(self, item):
        '''
        '''
        pass

    mx = property(_getMX, _setMX)    





    def _getMusicXML(self):
        '''
        '''
        mxIdentification = musicxml.Identification()
        mxIdentification.setDefaults() # will create a composer

        mxScoreDefault = musicxml.Score()
        mxScoreDefault.setDefaults()
        mxScoreDefault.set('identification', mxIdentification)

        # note: this merge is not happing, not sure why
        mxScore = self._getMX()
        mxScore = mxScore.merge(mxScoreDefault)

        return mxScore.xmlStr()


    def _setMusicXML(self, item):
        '''
        '''
        pass

    musicxml = property(_getMusicXML, _setMusicXML)    




    def write(self, format='musicxml', fp=None):
        '''Write a file.
        A None file path will result in temporary file
        '''
        if format == 'musicxml':
            if fp == None:
                fp = environLocal.getTempFile('.xml')
            dataStr = self.musicxml
        f = open(fp, 'w')
        f.write(dataStr)
        f.close()
        return fp

    def show(self, format='musicxml'):
        '''This might need to return the file path.
        '''
        environLocal.launch(format, self.write(format))





#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------

class TestSpeed(object):
     


# time for flat creation        <class 'music21.stream.Stream'>         1.93153500557
# time for flat creation        <class 'music21.stream_msc.Stream'>     54.6658909321
# time for flat note creation   <class 'music21.stream.Stream'>         1.65771198273
# time for flat note creation   <class 'music21.stream_msc.Stream'>     56.7881579399
# time for flat sorting         <class 'music21.stream.Stream'>         2.12981987
# time for flat sorting         <class 'music21.stream_msc.Stream'>     1.66900706291
# time for nested creation      <class 'music21.stream.Stream'>         0.00493693351746
# time for nested creation      <class 'music21.stream_msc.Stream'>     0.00213885307312
# time for nested sorting       <class 'music21.stream.Stream'>         0.64213514328
# time for nested sorting       <class 'music21.stream_msc.Stream'>     0.123522043228
# 

    def __init__(self):
        import stream_msc
        self.classNames = [(Stream, ElementWrapper), 
                           (stream_msc.Stream, stream_msc.ElementWrapper)]
        self.results = {}

    def _timeFlatCreation(self):
        idStr = 'time for flat creation'
        for nameStream, nameElement in self.classNames:
            t = common.Timer()
            t.start()

            a = nameStream()
            for x in range(10000):
                a.append(None)
            self.results[(idStr, str(nameStream))] = t()

    def _timeNestedCreation(self):
        idStr = 'time for nested creation'
        for nameStream, nameElement in self.classNames:
            t = common.Timer()
            t.start()

            a = nameStream()
            a.repeatCopy(None, range(10))
            b = nameStream()
            b.repeatCopy(a, range(0, 100, 10))
            c = nameStream()
            c.repeatCopy(b, range(0, 1000, 100))

            self.results[(idStr, str(nameStream))] = t()


    def _timeFlatSort(self):
        idStr = 'time for flat sorting'
        for nameStream, nameElement in self.classNames:
            t = common.Timer()
            t.start()
            for i in range(100):
                a = nameStream()
                for x in range(100):
                    e = nameElement()
                    e.offset = random.choice(range(100))
                    a.append(e)
                post = a.flat
            self.results[(idStr, str(nameStream))] = t()


    def _timeNestedSort(self):
        idStr = 'time for nested sorting'
        for nameStream, nameElement in self.classNames:
            t = common.Timer()
            t.start()

            for i in range(100):
                a = nameStream()
                for x in range(10):
                    e = nameElement()
                    e.offset = random.choice(range(10))
                    a.append(e)    
                b = nameStream()
                for x in range(10):
                    e = nameElement()
                    e.offset = 10 * random.choice(range(10))
                    b.append(e)    
                c = nameStream()
                for x in range(10):
                    e = nameElement()
                    e.offset = 100 * random.choice(range(10))
                    c.append(e)  
                post = c.flat
            self.results[(idStr, str(nameStream))] = t()


    def _timeFlatAddNextNote(self):
        idStr = 'time for flat note creation'
        for nameStream, nameElement in self.classNames:
            t = common.Timer()
            t.start()

            a = nameStream()
            for x in range(10000):
                n = note.Note(random.choice(['F#', 'G-']))
                n.quarterLength = 2
                a.addNext(n)
            self.results[(idStr, str(nameStream))] = t()

    def _timeNestedAddNextNote(self):
        idStr = 'time for nested note creation'
        for nameStream, nameElement in self.classNames:
            t = common.Timer()
            t.start()

            a = nameStream()
            for x in range(10):
                n = note.Note(random.choice(['F#', 'G-']))
                n.quarterLength = 2
                a.addNext(n)
            b = nameStream()
            for x in range(10):
                b.addNext(a)
            c = nameStream()
            for x in range(10):
                c.addNext(b)
            self.results[(idStr, str(nameStream))] = t()



    def reset(self):
        self.results = {}

    def run(self):
        self._timeFlatCreation()
        self._timeNestedCreation()
        self._timeFlatSort()
        self._timeNestedSort()
        self._timeFlatAddNextNote()
        self._timeNestedAddNextNote()

    def report(self):
        keys = self.results.keys()
        keys.sort()
        for key in keys:
            testName, objName = key
            print(testName.ljust(30) + objName.ljust(40) + 
                  str(self.results[key]))



#-------------------------------------------------------------------------------



class Test(unittest.TestCase):

    def runTest(self):
        pass


    def testStreamRecursion(self):
        srcStream = Stream()
        for x in range(6):
            n = note.Note('G#')
            n.duration = duration.Duration('quarter')
            e = ElementWrapper(n)
            e.offset = x * 1
            srcStream.append(e)

        self.assertEqual(len(srcStream), 6)
        self.assertEqual(len(srcStream.getOverlaps()), 0)

        midStream = Stream()
        for x in range(4):
            srcNew = srcStream.clone()
            srcNew.offset = x * 10 
            midStream.append(srcNew)

        midStream.flatten()
        self.assertEqual(len(midStream), 24)
        self.assertEqual(len(midStream.getOverlaps()), 0)

        farStream = Stream()
        for x in range(7):
            midNew = midStream.clone()
            midNew.offset = x * 100 
            farStream.append(midNew)

        farStream.flatten()
        self.assertEqual(len(farStream), 168)
        self.assertEqual(len(farStream.getOverlaps()), 0)

        elementsSorted = farStream.getSortedOffsets()

        # get just offset times
        # elementsSorted returns offset, dur, element
        offsets = [a for a, b, c, d in elementsSorted]

        # create what we epxect to be the offsets
        offsetsMatch = range(0,6)
        offsetsMatch += [x+10 for x in range(0,6)]
        offsetsMatch += [x+20 for x in range(0,6)]
        offsetsMatch += [x+30 for x in range(0,6)]
        offsetsMatch += [x+100 for x in range(0,6)]
        offsetsMatch += [x+110 for x in range(0,6)]

        self.assertEqual(offsets[:len(offsetsMatch)], offsetsMatch)




    def testStreamBundle(self):
        a = Stream()
        for x in range(6):
            n = note.Note('G#')
            n.duration = duration.Duration('quarter')
            e = ElementWrapper(n)
            e.offset = x * 1
            a.append(e)
        
        b = Stream()
        for x in range(6):
            n = note.Note('G#')
            n.duration = duration.Duration('quarter')
            e = ElementWrapper(n)
            e.offset = x * 10
            b.append(e)


        c = Stream()
        for x in range(6):
            n = note.Note('G#')
            n.duration = duration.Duration('quarter')
            e = ElementWrapper(n)
            e.offset = x * 100
            c.append(e)

        q = StreamBundle()
        q.addStream('a', a)
        q.addStream('b', b)
        q.addStream('c', c)

        elementsSorted = q.getSortedOffsets()
        self.assertEqual(len(elementsSorted), 18)

        # get just offsets
        offsets = [a for a, b, c, d in elementsSorted]

        # create what we epxect to be the offsets
        offsetsMatch = range(0,6)
        offsetsMatch += [x*10 for x in range(0,6)]
        offsetsMatch += [x*100 for x in range(0,6)]
        offsetsMatch.sort()

        self.assertEqual(offsets[:len(offsetsMatch)], offsetsMatch)



    def testOverlaps(self):
        a = Stream()
        # here, the thir item overlaps with the first
        for offset, dur in [(0,12), (3,2), (11,3)]:
            n = note.Note('G#')
            n.duration = duration.Duration()
            n.duration.quarterLength = dur
            e = ElementWrapper(n)
            e.offset = offset
            a.append(e)

        includeNoneDur = True
        includeCoincidentBoundaries = False

        simultaneityMap, overlapMap = a._findLayering(a.getSortedOffsets(), 
                                  includeNoneDur, includeCoincidentBoundaries)
        self.assertEqual(simultaneityMap, [[], [], []])
        self.assertEqual(overlapMap, [[1,2], [0], [0]])


        post = a._consolidateLayering(a.getSortedOffsets(), overlapMap)
        # print post

        #found = a.getOverlaps(includeNoneDur, includeCoincidentBoundaries)
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
            e = ElementWrapper(n)
            e.offset = offset
            a.append(e)

        includeNoneDur = True
        includeCoincidentBoundaries = True

        simultaneityMap, overlapMap = a._findLayering(a.getSortedOffsets(), 
                                  includeNoneDur, includeCoincidentBoundaries)
        self.assertEqual(simultaneityMap, [[], [], []])
        self.assertEqual(overlapMap, [[1], [0,2], [1]])


        post = a._consolidateLayering(a.getSortedOffsets(), overlapMap)



    def testStreamDuration(self):
        pass
#         a = Stream()
#         a.duration.quarterLength = 30
#         print a.offset



    def testMusicXMLBasic(self):
        nStream = NoteStream()
        for o in ['3', '4','5']:
            for p in ['c', 'd', 'e', 'f', 'e', 'f', 'g', 'a']:
                n = note.Note(p+o)
                n.quarterLength = .5
                nStream.addNext(n)

        notationStreamA = NotationStream()
        pos = 0
        for timeStr in ['3/4', '5/8', '2/4', '5/8', '4/4']:
            meterObj = meter.TimeSignature(timeStr)
            measureObj = measure.MeasureUnit()
            notationStreamA['measures'].insertAtOffset(measureObj, pos)
            notationStreamA['meter'].insertAtOffset(meterObj, pos)
            pos += meterObj.barDuration.quarterLength

        notationStreamB = NotationStream()
        pos = 0
        for timeStr in ['3/8', '2/8', '1/8', '5/8', '6/4', '1/8']:
            meterObj = meter.TimeSignature(timeStr)
            measureObj = measure.MeasureUnit()
            notationStreamB['measures'].insertAtOffset(measureObj, pos)
            notationStreamB['meter'].insertAtOffset(meterObj, pos)
            pos += meterObj.barDuration.quarterLength


        for notationStream in [notationStreamA, notationStreamB]:
            pStream = PartStream()
            for partName in ['ocarina', 'tuba']:
                part = measure.Part()
                part.partName = partName 
                pStream.setData(partName, part, None, nStream, notationStream)
        
            #pStream.show()

            post = pStream.mx
            post = pStream.musicxml
    
            
        





if __name__ == "__main__":
    s1 = doctest.DocTestSuite(__name__)
    s2 = unittest.defaultTestLoader.loadTestsFromTestCase(Test)
    s1.addTests(s2)
    runner = unittest.TextTestRunner()
    runner.run(s1)  









#-------------------------------------------------------------------------------
# class StreamBundle(Stream):
#     '''A stream bundle is a Stream that knows what streams are in what slots
#     of _elements. This is useful to speed up operations that need to freuquently
#     access isolated streams.
#     '''
# 
#     def __init__(self):
#         Stream.__init__(self)
#         # store a key, _elements index reference pair
#         self._reference = {}
# 
# 
#     def __getitem__(self, key):
#         '''Note: this override the behavior of Streams in that keys here
#         are strings, not index values
#         '''
#         return self.getStream(key)
# 
#     def __setitem__(self, key, value):
#         '''Note: this override the behavior of Streams in that keys here
#         are strings, not index values
#         '''
#         self.addStream(key, value)
# 
# 
# 
#     def addStream(self, name, streamObj):
#         '''Can be used to add or set a Stream
#         '''
#         if name not in self._reference.keys():
#             index = len(self._reference.keys())
#             self._reference[name] = index
#             self.append(streamObj)
#         else:
#             self._elements[self._reference[name]].append(streamObj)
#         self._unsorted = True
# 
# 
#     def getStream(self, name):
#         '''
#         There may be a more efficient way to do this, but here: a single 
#         compose Stream is created and then sorted. 
#         '''   
#         if name in self._reference.keys():
#             return self._elements[self._reference[name]]
#         else:
#             raise KeyError
# 
#     def delStream(self, name):
#         '''
#         Remove a stream by name. Shift all indices.
# 
#         >>> b = Stream()
#         >>> b.repeatCopy(None, range(10))
#         >>> b.setIdForElements('green')
#         >>> c = Stream()
#         >>> c.repeatCopy(None, range(10))
#         >>> c.setIdForElements('red')
#         >>> d = Stream()
#         >>> d.repeatCopy(None, range(10))
#         >>> d.setIdForElements('blue')
#         >>> 
#         >>> a = StreamBundle()
#         >>> a.addStream('green', b)
#         >>> a.addStream('red', c)
#         >>> a.addStream('blue', d)
#         >>>
#         >>> a.getStream('blue')[0].id
#         'blue'
#         >>> a.getStream('red')[0].id
#         'red'
#         >>> a.delStream('red')
#         >>> a.getStream('blue')[0].id
#         'blue'
#         '''   
#         if name in self._reference.keys():
#             i = self._reference[name] # get index to remove
#             junk = self._elements.pop(i)
#             # shift all indices above this one down one
#             for key, value in self._reference.items():
#                 if value > i:
#                     self._reference[key] -= 1
#             del self._reference[name]
#             del junk
#         else:
#             raise KeyError
# 
# 
#     def keys(self):
#         '''
#         There may be a more efficient way to do this, but here: a single 
#         compose Stream is created and then sorted. 
#         '''   
#         return self._reference.keys()



#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
# subclasses of Stream

# class NoteStream(Stream):
#     '''A type of stream that provides utilities for processing a collection of
#     Notes as elements. 
#     '''
#     def __init__(self):
#         Stream.__init__(self)
# 
# 
#     def getAccidentalDistribution(self):
#         '''Test method.
# 
#         >>> a = NoteStream()
#         >>> a.fillNone(10)
#         >>> pitches = ['G#', 'A#', 'B-', 'D-']
#         >>> for x in range(len(pitches)):
#         ...     n = note.Note(pitches[x])
#         ...     n.duration = duration.Duration('quarter')
#         ...     n.offset = x * 3
#         ...     a.append(n)
#         >>> found = a.getAccidentalDistribution()
#         >>> found['sharp']
#         2
#         >>> found['flat']
#         2
#         '''
#         found = self.getElementsByClass(note.Note)
#         count = {}
#         for element in found:
#             accName = element.pitch.accidental.name
#             if accName not in count.keys():
#                 count[accName] = 0
#             count[accName] += 1
#         return count
# 
# 
#     def _getMusicXML(self):
#         '''
#         Returns an incomplete mxMeasure object
# 
#         '''
# 
#         notes = self.getElementsByClass(note.Note, unpackElement=True)
#         mxMeasure = musicxmlMod.Measure()
#         for note in notes:
#             mxMeasure.append(note.musicxml)
#         return mxMeasure
# 
# 
#     def _setMusicXML(self, item):
#         '''
#         '''
#         pass
# 
#     musicxml = property(_getMusicXML) #, _setMusicXML) COMMENT OUT FOR NOW...
# 
# 
# 
# 
# 
# #-------------------------------------------------------------------------------
# class NoteSequence(NoteStream):
#     '''A type of stream that automatically configures offset values
#     based on note duration. NoteStreams assure that there will be no
#     duration overalps. 
#     '''
#     pass
# 
# 
# class NoteCloud(NoteStream):
#     '''A type of stream that permits any arrangement of notes
#     '''
#     pass


#-------------------------------------------------------------------------------
# subclasses of StreamBundle



#-------------------------------------------------------------------------------
# class NotationStream(StreamBundle):
#     '''A type of StreamBundle w
# 
#     could be called NotationStream
# 
#     This stores the timed information necessary to create one or more measures
#     '''
# 
#     def __init__(self):
#         '''
#         >>> a = NotationStream()
#         >>> len(a.getStream('measures'))
#         0
#         >>> a['measures'].repeatCopy(measure.MeasureUnit(), range(2))
#         >>> len(a.getStream('measures'))
#         2
#         '''
#         StreamBundle.__init__(self)
# 
#         # stream of measure objects
#         self.addStream('measures', Stream())
#         # stream of clef objects
#         self.addStream('clef', Stream())
#         self.addStream('key', Stream())
#         self.addStream('meter', Stream())
#         self.addStream('dynamics', Stream())
# 
# 
#     def _getMX(self):
#         '''
#         Returns an incomplete mxPart object
# 
#         >>> a = NotationStream()
#         >>> mxPart = a._getMX()
# 
#         '''
#         mxPart = musicxmlMod.Part()
#         i = 0
#         for element in self.getStream('measures'):
#             measureObj = elment.obj
#             if not isinstance(measure, measure.MeasureUnit):
#                 raise StreamBundleException('not a MeasureUnit')
# 
#             mxMeasure = musicxmlMod.Measure()
#             if measureObj.number == None:
#                 mxMeasure.set('number', i)
#             else:
#                 mxMeasure.set('number', measureObj.number)
#             mxPart.append(mxMeasure)
#         return mxPart
# 
#     def _setMX(self, mxNote):
#         '''
#         Given a lost of one or more MusicXML Note objects, read in and create
#         Duration
#         '''
#         pass
# 
#     mx = property(_getMX, _setMX)    
# 
# 
# 


#-------------------------------------------------------------------------------
# class PartStream(StreamBundle):
#     '''A type of StreamBundle 
# 
#     '''
# 
#     def __init__(self):
#         StreamBundle.__init__(self)
# 
# 
#         # stream of part objects
#         self.addStream('parts', StreamBundle())
#         # stream of instrument object
#         self.addStream('instruments', StreamBundle())
#         # a stream of notes
#         self.addStream('noteStreams', StreamBundle())
# 
#         # a stream of measures; temporary location
#         self.addStream('notationStreams', StreamBundle())
# 
#         # each part is defined by having an entry in each of the 
#         # streams here, in parallel. 
# 
# #     def getPartData(self, partId):
# #         partObj = self.getStream('parts').getStream(partId)
# #         instObj = self.getStream('instruments').getStream(partId)
# #         noteStream = self.getStream('noteStreams').getStream(partId)    
# 
#     def setData(self, id, partObj, instObj, noteStream, notationStream):
#         '''
#         >>> b = NoteStream()
#         >>> b.repeatCopy(note.Note('g'), range(30))
#         >>> c = NoteStream()
#         >>> c.repeatCopy(note.Note('f#'), range(30))
# 
#         >>> q = NotationStream()
#         >>> q.getStream('measures').repeatCopy(measure.MeasureUnit(), range(0,30,4))
# 
#         >>> a = PartStream()
#         >>> a.setData('flute1', measure.Part(), 'instObjB', b, q)
#         >>> a.setData('bass3', measure.Part(), 'instObjC', c, q)
# 
#         >>> w = a.getNoteStream('bass3')
#         >>> len(w)
#         30
#         '''
# 
#         partStreamBundle = self.getStream('parts')
#         partStreamBundle[id] = partObj
# 
#         instStreamBundle = self.getStream('instruments')
#         instStreamBundle[id] = instObj
# 
#         noteStreamBundle = self.getStream('noteStreams')
#         noteStreamBundle[id] = noteStream
# 
#         notationStreamBundle = self.getStream('notationStreams')
#         notationStreamBundle[id] = notationStream
# 
# 
# 
#     def getNoteStream(self, partId):
#         return self.getStream('noteStreams')[partId]
#         
# 
#     def _getMX(self):
#         '''
#         Returns an incomplete mxScore object
# 
#         '''
#         mxScore = musicxmlMod.Score()
#         mxPartList = musicxmlMod.PartList()
# 
#         partStreamBundle = self.getStream('parts')
#         instStreamBundle = self.getStream('instruments')
#         noteStreamBundle = self.getStream('noteStreams')
#         notationStreamBundle = self.getStream('notationStreams')
# 
# 
#         # keys are valid for all components
#         keys = partStreamBundle.keys()
#         # note that hese need to be in order
#         for partId in keys:
#             # music21 part object
#             partObject = partStreamBundle[partId].obj
#             instObject = instStreamBundle[partId].obj
#             # need note stream
#             noteStream = noteStreamBundle[partId]
#             # do not get .obj here, just element (tt is a stream)
#             notationStream = notationStreamBundle[partId]
# 
#             mxScorePart = partObject.mx # returns an mxScorePart
#             mxScorePart.set('id', partId)
#             mxPartList.append(mxScorePart)
# 
#             mxPart = musicxmlMod.Part()
#             mxPart.set('id', partId)
# 
#             measureStream = notationStream.getStream('measures')
#             meterStream = notationStream.getStream('meter')
# 
#             for i in range(len(measureStream)):
#                 meterObj = meterStream[i].obj
#                 measureStart = measureStream[i].offset
#                 measureEnd = measureStart + meterObj.barDuration.quarterLength
# 
#                 # print _MOD, measureStart, measureEnd
#                 mxMeasure = measureStream[i].obj.mx
#                 # assign a lost of meter objects
#                 mxAttributes = musicxml.Attributes()
#                 # meter returns a lost of mxTime objects
#                 mxAttributes.set('time', meterObj.mx)
#                 mxMeasure.set('attributes', mxAttributes)
# 
#                 # return a list of note objects for the valid time span
#                 for noteObj in noteStream.getElementsByOffset(measureStart,
#                     measureEnd, includeCoincidentBoundaries=False, 
#                     unpackElement=True):
#                     # each Note may return 1 or more musicxml notes
#                     mxMeasure.componentList += noteObj.mx               
#                 mxPart.append(mxMeasure)
# 
#             # notes go here; not he same as mxPart
#             mxScore.append(mxPart)
# 
#         #mxScore.set('partList', mxPartList)
#         mxScore.partListObj = mxPartList
#         return mxScore
# 
#     def _setMX(self, item):
#         '''
#         '''
#         pass
# 
#     mx = property(_getMX, _setMX)    
# 
# 
# 
# 
# 
#     def _getMusicXML(self):
#         '''
#         '''
#         mxIdentification = musicxml.Identification()
#         mxIdentification.setDefaults() # will create a composer
# 
#         mxScoreDefault = musicxml.Score()
#         mxScoreDefault.setDefaults()
#         mxScoreDefault.set('identification', mxIdentification)
# 
#         # note: this merge is not happing, not sure why
#         mxScore = self._getMX()
#         mxScore = mxScore.merge(mxScoreDefault)
# 
#         return mxScore.xmlStr()
# 
# 
#     def _setMusicXML(self, item):
#         '''
#         '''
#         pass
# 
#     musicxml = property(_getMusicXML, _setMusicXML)    
# 
# 
# 
# 
#     def write(self, format='musicxml', fp=None):
#         '''Write a file.
#         A None file path will result in temporary file
#         '''
#         if format == 'musicxml':
#             if fp == None:
#                 fp = environLocal.getTempFile('.xml')
#             dataStr = self.musicxml
#         f = open(fp, 'w')
#         f.write(dataStr)
#         f.close()
#         return fp
# 
#     def show(self, format='musicxml'):
#         '''This might need to return the file path.
#         '''
#         environLocal.launch(format, self.write(format))
# 
# 



#     def testStreamBundle(self):
#         a = Stream()
#         for x in range(6):
#             n = note.Note('G#')
#             n.duration = duration.Duration('quarter')
#             e = ElementWrapper(n)
#             e.offset = x * 1
#             a.append(e)
#         
#         b = Stream()
#         for x in range(6):
#             n = note.Note('G#')
#             n.duration = duration.Duration('quarter')
#             e = ElementWrapper(n)
#             e.offset = x * 10
#             b.append(e)
# 
# 
#         c = Stream()
#         for x in range(6):
#             n = note.Note('G#')
#             n.duration = duration.Duration('quarter')
#             e = ElementWrapper(n)
#             e.offset = x * 100
#             c.append(e)
# 
#         q = StreamBundle()
#         q.addStream('a', a)
#         q.addStream('b', b)
#         q.addStream('c', c)
# 
#         elementsSorted = q.flat.sorted
#         self.assertEqual(len(elementsSorted), 18)
# 
#         # get just offsets
#         offsets = [a.offset for a in elementsSorted]
# 
#         # create what we epxect to be the offsets
#         offsetsMatch = range(0, 6)
#         offsetsMatch += [x * 10 for x in range(0, 6)]
#         offsetsMatch += [x * 100 for x in range(0, 6)]
#         offsetsMatch.sort()
# 
#         self.assertEqual(offsets[:len(offsetsMatch)], offsetsMatch)

#     def testMusicXMLBasic(self):
#         nStream = NoteStream()
#         for o in ['3', '4','5']:
#             for p in ['c', 'd', 'e', 'f', 'e', 'f', 'g', 'a']:
#                 n = note.Note(p+o)
#                 n.quarterLength = .5
#                 nStream.addNext(n)
# 
#         notationStreamA = NotationStream()
#         pos = 0
#         for timeStr in ['3/4', '5/8', '2/4', '5/8', '4/4']:
#             meterObj = meter.TimeSignature(timeStr)
#             measureObj = measure.MeasureUnit()
#             notationStreamA['measures'].insertAtOffset(measureObj, pos)
#             notationStreamA['meter'].insertAtOffset(meterObj, pos)
#             pos += meterObj.barDuration.quarterLength
# 
#         notationStreamB = NotationStream()
#         pos = 0
#         for timeStr in ['3/8', '2/8', '1/8', '5/8', '6/4', '1/8']:
#             meterObj = meter.TimeSignature(timeStr)
#             measureObj = measure.MeasureUnit()
#             notationStreamB['measures'].insertAtOffset(measureObj, pos)
#             notationStreamB['meter'].insertAtOffset(meterObj, pos)
#             pos += meterObj.barDuration.quarterLength
# 
# 
#         for notationStream in [notationStreamA, notationStreamB]:
#             pStream = PartStream()
#             for partName in ['ocarina', 'tuba']:
#                 part = measure.Part()
#                 part.partName = partName 
#                 pStream.setData(partName, part, None, nStream, notationStream)
#         
#             # spStream.show()
# 
#             post = pStream.mx
#             post = pStream.musicxml
    


#    def isCloud(self, includeNoneDur=True, 
#                      includeCoincidentBoundaries=False):
#        '''
#        A stream is a cloud if it includes any overlaps
#        '''        
#        ## DOESN'T WORK b/c of gaps.
#        return not self.isSequence(includeNoneDur, includeCoincidentBoundaries)
#
#
#    def filterNote(self):
#        '''Extract all notes from this stream and return a NoteStream or 
#        a NoteCloud.
#    
#        Need to look at notes and determine if this is a cloud or a sequence
#
#        >>> a = Stream()
#        >>> a.repeatCopy(note.Note('A-'), range(30))
#        >>> a.repeatCopy(None, range(30))
#        >>> b = a.filterNote()
#        >>> len(b)
#        30
#        >>> isinstance(b, NoteStream)
#        True
#        '''
#        post = NoteStream()
#
#        for elementsSorted in self.getSorted():
#            element = elementsSorted[3]
#            if element.isClass(note.Note):
#                post.append(element)
#        return post



#    def delete(self, indexList):
#        '''Seldom used: deletes elements by index in self.elements. indexList stores a list
#        if indices that are found in self.elements.  Returns a list of elements deleted.
#
#        >>> a = Stream()
#        >>> a.repeatCopy(None, range(30))
#        >>> b = Stream()
#        >>> b.repeatCopy(None, range(30))
#        >>> c = Stream()
#        >>> c.repeatCopy(None, range(30))
#        >>> candidate = c[23]
#        >>> candidate.id = 'tagged'
#        >>> c[23].id   
#        'tagged'
#        >>> b.append(c)
#        >>> a.append(b) # a holds all recursively
#        >>> len(a)
#        31
#        >>> len(a.flat)
#        90
#        >>> junk = a[30][30].delete([23])
#        >>> len(a)
#        31
#        >>> len(a.flat)
#        29
#        >>> junk[0].id
#        'tagged'
#        #>>> print(a._access([30, 30, 23]).id)
#        #None
#        '''
##        returnList = []
##        for thisIndex in indexList:
##            returnList 
#        post = self.elements[indexList[0]]
#        if len(indexList) == 1:
#            # pop out the object at this index
#            post = scope._elements.pop(indexList[0])
#        else:
#            indexList = indexList[1:] # crop indices
#            # call with what is left of index and the last found
#            # ElementWrapper as scope
#            post = self._delete(indexList, post)
#
#        scope._unsorted = True
#        return post
#
#    def _access(self, indexList, scope=None):
#        '''Low level access to self._elements. indexList stores a list
#        if indices that are found in one or emore self._elements. 
#
#        >>> a = Stream()
#        >>> a.repeatCopy(None, range(30))
#        >>> b = Stream()
#        >>> b.repeatCopy(None, range(30))
#        >>> c = Stream()
#        >>> c.repeatCopy(None, range(30))
#        >>> candidate = c[23]
#        >>> candidate.id = 'tagged'
#        >>> c[23].id   
#        'tagged'
#        >>> b.append(c)
#        >>> a.append(b) # a holds all recursivey
#        >>> a._access([3]).offset
#        3
#        >>> a._access([30, 30, 23]).offset
#        23
#        >>> a._access([30, 30, 23]).id
#        'tagged'
#        '''
#        if scope == None:
#            scope = self
#        # get ElementWrapper at first index
#        post = scope._elements[indexList[0]]
#        if len(indexList) == 1:
#            return post # return object if no more indices
#        else:
#            indexList = indexList[1:] # crop indices
#            # call with what is left of index and the last found
#            # ElementWrapper as scope
#            post = self._access(indexList, post)
#        return post
#
#    def _find(self, element, scope=None):
#        '''Given an element inside of self._elements[], search through
#        nested structure to get that element.
#        Address is a list of indices to get to that element
#
#        >>> a = Stream()
#        >>> a.repeatCopy(None, range(30))
#        >>> b = Stream()
#        >>> b.repeatCopy(None, range(30))
#        >>> c = Stream()
#        >>> c.repeatCopy(None, range(30))
#        >>> candidate = c[23]
#        >>> candidate.id = 'tagged'
#        >>> c[23].id   
#        'tagged'
#        >>> b.append(c)
#        >>> a.append(b) # a holds all recursivey
#        >>> len(a) # flattened length
#        90
#        >>> len(a._elements) # unflattened length
#        31
#        >>> # id(a._elements[30][30][23]) == id(candidate)
#        >>> a._find(candidate)
#        [30, 30, 23]
#        >>> a._access(a._find(candidate)).id
#        'tagged'
#        '''
#        # much match memory id, not object __eq__
#        idSeek = id(element) 
#        address = [] # a list indices into self._elements
#        i = 0
#        # the lenght of self._elements is not the same as __len__       
#        # as __len__ take recursion into account
#        if scope == None:
#            scope = self
#        for i in range(len(scope._elements)):
#            candidate = scope._elements[i]
#            if isinstance(candidate, Stream):
#                postRecurseAddress = candidate._find(element, candidate)
#                if postRecurseAddress != []:
#                    address.append(i) # add outer first
#                    address += postRecurseAddress
#            else:
#                if idSeek == id(candidate):
#                    address.append(i)
#                    return address
#        return address # may be empty list if not found
#
#
#    def pop(self, index):
#        '''Remove and return element form the sorted list at the specified
#        position.
#
#        
#
#        Note: the challenge is finding where in _elements the element is
#        '''
#        element = self.getSorted()[index][3] # item 3 is ElementWrapper
#        # transverse through _elements to find this element
#        
#        self._elements
#        self._unsorted = True
#
#
#    def index(self, element):
#        '''
#        
#        '''
#        pass
#
##         '''Get the index of an element. This is not presently working
## 
##         >>> a = Stream()
##         >>> a.repeatCopy(note.Note('A'), range(20))
##         >>> a.repeatCopy(None, range(10,20))
##         >>> e = ElementWrapper(None)
##         >>> e.offset = 12
##         >>> a.index(e)
##         10
##         '''
##         i = 0
##         for a, b, c, d in self.getSorted():
##             if d == element: return i
##             i += 1
##         raise ValueError('element %s not in Stream' % element)
#