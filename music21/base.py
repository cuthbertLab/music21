#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         base.py
# Purpose:      Music21 base classes and important utilities
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    (c) 2009-2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

'''
Music21 base classes for :class:`~music21.stream.Stream` objects and elements 
contained within them. Additional objects for defining and manipulating 
elements are included.

The namespace of this file, as all base.py files, is loaded into the package 
that contains this file via __init__.py. Everything in this file is thus 
available after importing music21.

>>> import music21
>>> music21.Music21Object
<class 'music21.base.Music21Object'>

Alternatively, after doing a complete import, these classes are available
under the module "base":

>>> from music21 import *
>>> base.Music21Object
<class 'music21.base.Music21Object'>

'''

# base -- the convention within music21 is that __init__ files contain:
#    from base import *


import copy
import unittest, doctest
import sys
import types
import inspect
import uuid
import json
import codecs

from music21 import common
from music21 import environment

# needed for temporal manipulations; not music21 objects
from music21 import tie
from music21 import duration

_MOD = 'music21.base.py'
environLocal = environment.Environment(_MOD)


# check external dependencies and display 
_missingImport = []
try:
    import matplotlib
except ImportError:
    _missingImport.append('matplotlib')

try:
    import numpy
except ImportError:
    _missingImport.append('numpy')

try:
    import PIL
except ImportError:
    _missingImport.append('PIL')

try:
    import abjad
except ImportError:
    _missingImport.append('abjad')


if len(_missingImport) > 0:
    if environLocal['warnings'] in [1, '1', True]:
        environLocal.warn(common.getMissingImportStr(_missingImport),
        header='music21:')





#-------------------------------------------------------------------------------
VERSION = (0, 3, 4)  # increment any time picked versions will be obsolete or other significant changes have been made
VERSION_STR = '.'.join([str(x) for x in VERSION]) + 'a8'

# define whether weakrefs are used for storage of object locations
WEAKREF_ACTIVE = True


#-------------------------------------------------------------------------------
class Music21Exception(Exception):
    pass

# should be renamed:
class DefinedContextsException(Music21Exception):
    pass

class Music21ObjectException(Music21Exception):
    pass

class ElementException(Music21Exception):
    pass

class GroupException(Music21Exception):
    pass

#-------------------------------------------------------------------------------
# make subclass of set once that is defined properly
class Groups(list):   
    '''A list of strings used to identify associations that an element might 
    have. Enforces that all elements must be strings
    
    >>> g = Groups()
    >>> g.append("hello")
    >>> g[0]
    'hello'
    
    >>> g.append(5)
    Traceback (most recent call last):
    GroupException: Only strings can be used as list names
    '''
    def append(self, value):
        if isinstance(value, basestring):
            list.append(self, value)
        else:
            raise GroupException("Only strings can be used as list names")
            

    def __setitem__(self, i, y):
        if isinstance(y, basestring):
            list.__setitem__(self, i, y)
        else:
            raise GroupException("Only strings can be used as list names")
        

    def __eq__(self, other):
        '''Test Group equality. In normal lists, order matters; here it does not. 

        >>> a = Groups()
        >>> a.append('red')
        >>> a.append('green')
        >>> b = Groups()
        >>> b.append('green')
        >>> b.append('red')
        >>> a == b
        True
        '''
        if not isinstance(other, Groups):
            return False
        if (list.sort(self) == other.sort()):
            return True
        else:
            return False

    def __ne__(self, other):
        '''In normal lists, order matters; here it does not. 
        '''

        if other is None or not isinstance(other, Groups):
            return True
        if (list.sort(self) == other.sort()):
            return False
        else:
            return True





#-------------------------------------------------------------------------------
class DefinedContexts(object):
    '''An object, stored within a Music21Object, that stores references to a collection of objects that may be contextually relevant.

    Some of these objects are locations; these DefinedContext additional store an offset value, used for determining position within a Stream. 

    DefinedContexts are one of many ways that context can be found; context can also be found through searching (using objects in DefinedContexts). 

    All defined contexts are stored as dictionaries in a dictionary. The outermost dictionary stores objects 

    '''

    def __init__(self):
        # a dictionary of dictionaries
        self._definedContexts = {} 
        # store idKeys in lists for easy access
        # the same key may be both in locationKeys and contextKeys
        self._locationKeys = []
        # store an index of numbers for tagging the time of defined contexts; 
        # this is used to be able to descern the order of context as added
        self._timeIndex = 0

    def __len__(self):
        '''Return the total number of references.

        >>> class Mock(Music21Object): pass
        >>> aObj = Mock()
        >>> aContexts = DefinedContexts()
        >>> aContexts.add(aObj)
        >>> len(aContexts) 
        1
        '''
        return len(self._definedContexts)

    def __deepcopy__(self, memo=None):
        '''This produces a new, independent DefinedContexts object.
        This does not, however, deepcopy site references stored therein

        >>> import copy
        >>> class Mock(Music21Object): pass
        >>> aObj = Mock()
        >>> aContexts = DefinedContexts()
        >>> aContexts.add(aObj)
        >>> bContexts = copy.deepcopy(aContexts)
        >>> len(aContexts.get()) == 1
        True
        >>> len(bContexts.get()) == 1
        True
        >>> aContexts.get() == bContexts.get()
        True

        OMIT_FROM_DOCS
        the not copying object references here may be a problem
        seems to be a problem in copying Streams before pickling
        '''
        new = self.__class__()
        for idKey in self._definedContexts.keys():
            dict = self._definedContexts[idKey]
            new.add(dict['obj'], offset=dict['offset'], timeValue=dict['time'],
                    idKey=idKey)
        return new

    #---------------------------------------------------------------------------
    # utility conversions

    def unwrapWeakref(self):
        '''Unwrap any and all weakrefs stored.

        >>> class Mock(Music21Object): pass
        >>> aObj = Mock()
        >>> bObj = Mock()
        >>> aContexts = DefinedContexts()
        >>> aContexts.add(aObj)
        >>> aContexts.add(bObj)
        >>> common.isWeakref(aContexts.get()[0]) # unwrapping happens 
        False
        >>> common.isWeakref(aContexts._definedContexts[id(aObj)]['obj'])
        True
        >>> aContexts.unwrapWeakref()
        >>> common.isWeakref(aContexts._definedContexts[id(aObj)]['obj'])
        False
        >>> common.isWeakref(aContexts._definedContexts[id(bObj)]['obj'])
        False
        '''
        for idKey in self._definedContexts.keys():
            if WEAKREF_ACTIVE:
            #if common.isWeakref(self._definedContexts[idKey]['obj']):

                #environLocal.printDebug(['unwrapping:', self._definedContexts[idKey]['obj']])

                post = common.unwrapWeakref(self._definedContexts[idKey]['obj'])
                self._definedContexts[idKey]['obj'] = post


    def wrapWeakref(self):
        '''Wrap any and all weakrefs stored.

        >>> class Mock(Music21Object): pass
        >>> aObj = Mock()
        >>> bObj = Mock()
        >>> aContexts = DefinedContexts()
        >>> aContexts.add(aObj)
        >>> aContexts.add(bObj)
        >>> aContexts.unwrapWeakref()
        >>> aContexts.wrapWeakref()
        >>> common.isWeakref(aContexts._definedContexts[id(aObj)]['obj'])
        True
        >>> common.isWeakref(aContexts._definedContexts[id(bObj)]['obj'])
        True
        '''
        for idKey in self._definedContexts.keys():
            if self._definedContexts[idKey]['obj'] == None:
                continue # always skip None
            if not common.isWeakref(self._definedContexts[idKey]['obj']):
                #environLocal.printDebug(['wrapping:', self._definedContexts[idKey]['obj']])

                post = common.wrapWeakref(self._definedContexts[idKey]['obj'])
                self._definedContexts[idKey]['obj'] = post



    def freezeIds(self):
        '''Temporarily replace are stored keys with a different value.

        >>> class Mock(Music21Object): pass
        >>> aObj = Mock()
        >>> bObj = Mock()
        >>> aContexts = DefinedContexts()
        >>> aContexts.add(aObj)
        >>> aContexts.add(bObj)
        >>> oldKeys = aContexts._definedContexts.keys()
        >>> aContexts.freezeIds()
        >>> newKeys = aContexts._definedContexts.keys()
        >>> oldKeys == newKeys
        False
        '''
        # need to store self._locationKeys as well

        post = {}
        postLocationKeys = []
        for idKey in self._definedContexts.keys():

            # make a random UUID
            if idKey != None:
                newKey = uuid.uuid4()
            else:
                newKey = idKey # keep None

            # might want to store old id?
            #environLocal.printDebug(['freezing key:', idKey, newKey])

            if idKey in self._locationKeys:
                postLocationKeys.append(newKey)
            
            post[newKey] = self._definedContexts[idKey]

        self._definedContexts = post
        self._locationKeys = postLocationKeys

        #environLocal.printDebug(['post freezeids', self._definedContexts])


    def unfreezeIds(self):
        '''Restore keys to be the id() of the object they contain

        >>> class Mock(Music21Object): pass
        >>> aObj = Mock()
        >>> bObj = Mock()
        >>> cObj = Mock()
        >>> aContexts = DefinedContexts()
        >>> aContexts.add(aObj)
        >>> aContexts.add(bObj)
        >>> aContexts.add(cObj, 200) # a location

        >>> oldKeys = aContexts._definedContexts.keys()
        >>> oldLocations = aContexts._locationKeys[:]
        >>> aContexts.freezeIds()
        >>> newKeys = aContexts._definedContexts.keys()
        >>> oldKeys == newKeys
        False
        >>> aContexts.unfreezeIds()
        >>> postKeys = aContexts._definedContexts.keys()
        >>> postKeys == newKeys
        False
        >>> # restored original ids b/c objs are alive
        >>> sorted(postKeys) == sorted(oldKeys) 
        True
        >>> oldLocations == aContexts._locationKeys
        True
        '''
        #environLocal.printDebug(['defined context entering unfreeze ids', self._definedContexts])

        post = {}
        postLocationKeys = []
        for idKey in self._definedContexts.keys():

            # check if unwrapped, unwrap
            obj = common.unwrapWeakref(self._definedContexts[idKey]['obj'])
            if obj != None:
                newKey = id(obj)
            else:
                newKey = None
            #environLocal.printDebug(['unfreezing key:', idKey, newKey])

            if idKey in self._locationKeys:
                postLocationKeys.append(newKey)
            post[newKey] = self._definedContexts[idKey]

        self._definedContexts = post
        self._locationKeys = postLocationKeys


    #---------------------------------------------------------------------------
    # general

    def clear(self):
        '''Clear all stored data.
        '''
        self._definedContexts = {} 
        self._locationKeys = []

    def _prepareObject(self, obj, domain):
        '''Prepare an object for storage. May be stored as a standard refernce or as a weak reference.
        '''
        # can have this perform differently based on domain
        if obj is None: # leave None alone
            return obj
        elif WEAKREF_ACTIVE:
            return common.wrapWeakref(obj)
        # a normal reference, return unaltered
        else:
            return obj
        

    def add(self, obj, offset=None, timeValue=None, idKey=None):
        '''Add a reference to the DefinedContexts collection. 
        if offset is None, it is interpreted as a context
        if offset is a value, it is intereted as location

        The `timeValue` argument is used to store the time at which an object is added to locations. This is not the same as `offset` 

        '''
        # NOTE: this is a performance critical method

        isLocation = False # 'contexts'
        if offset is not None: 
            isLocation = True # 'locations'

        # note: if we want both context and locations to exists
        # for the same object, may need to append character code to id

        if idKey is None and obj != None:
            idKey = id(obj)
        # a None object will have a key of None
        # do not need to set this as is default

        #environLocal.printDebug(['adding obj', obj, idKey])
        objRef = self._prepareObject(obj, isLocation)

        updateNotAdd = False
        if idKey in self._definedContexts.keys():
            updateNotAdd = True

        if isLocation: # the dictionary may already be a context
            if not updateNotAdd: # already know that it is new (not an update)
                self._locationKeys.append(idKey)
            # this may be a context that is now a location
            elif idKey not in self._locationKeys: 
                self._locationKeys.append(idKey)
            # otherwise, this is attempting to define a new offset for 
            # a known location

        dict = {}
        dict['obj'] = objRef
        dict['offset'] = offset # offset can be None for contexts

        # NOTE: this may not give sub-second resolution on some platforms
        if timeValue is None:
            dict['time'] = self._timeIndex
            self._timeIndex += 1 # increment for next usage
        else:
            dict['time'] = timeValue

        # TODO: store id() and class name for matching without unwrapping
        # weakref!

        if updateNotAdd: # add new/missing information to dictionary
            self._definedContexts[idKey].update(dict)
        else: # add:
            self._definedContexts[idKey] = dict

    def remove(self, site):
        '''Remove the object (a context or location site) specified from DefinedContexts. Object provided can be a location site or a defined context. 

        >>> class Mock(Music21Object): pass
        >>> aSite = Mock()
        >>> bSite = Mock()
        >>> cSite = Mock()
        >>> aContexts = DefinedContexts()
        >>> aContexts.add(aSite, 23)
        >>> len(aContexts)
        1
        >>> aContexts.add(bSite, 233)
        >>> len(aContexts)
        2
        >>> aContexts.add(cSite, 232223)
        >>> len(aContexts)
        3
        >>> aContexts.remove(aSite)
        >>> len(aContexts)
        2

        OMIT_FROM_DOCS
        >>> len(aContexts._locationKeys)
        2

        '''
        siteId = None
        if site is not None: 
            siteId = id(site)
        try:
            del self._definedContexts[siteId]
        except:    
            raise DefinedContextsException('an entry for this object (%s) is not stored in DefinedContexts' % site)
        # also delete from location keys
        if siteId in self._locationKeys:
            self._locationKeys.pop(self._locationKeys.index(siteId))


    def removeById(self, idKey):
        '''Remove a defined contexts entry by id key, which is id() of the object. 
        '''
        if idKey == None:
            raise Exception('trying to remove None idKey')
        del self._definedContexts[idKey]
        if idKey in self._locationKeys:
            self._locationKeys.pop(self._locationKeys.index(idKey))

    def getById(self, id):
        '''Return the object specified by an id.
        Used for testing and debugging. 
        '''
        dict = self._definedContexts[id]
        # need to check if these is weakref
        #if common.isWeakref(dict['obj']):
        if WEAKREF_ACTIVE:
            return common.unwrapWeakref(dict['obj'])
        else:
            return dict['obj']


    def _keysByTime(self, newFirst=True):
        '''Get keys sorted by creation time, where most recent are first if `newFirst` is True. else, most recent are last.

        >>> from music21 import *
        >>> import time
        >>> class Mock(Music21Object): pass
        >>> aObj = Mock()
        >>> bObj = Mock()
        >>> cObj = Mock()
        >>> aContexts = DefinedContexts()
        >>> aContexts.add(cObj, 345)
        >>> aContexts.add(aObj)
        >>> aContexts.add(bObj)
        >>> k = aContexts._keysByTime()
        >>> aContexts._definedContexts[k[0]]['time'] > aContexts._definedContexts[k[1]]['time'] > aContexts._definedContexts[k[2]]['time']
        True
        '''
        post = []
        for key in self._definedContexts.keys():
            post.append((self._definedContexts[key]['time'], key))
        post.sort()
        if newFirst:
            post.reverse()
        return [k for t, k in post]


    def get(self, locationsTrail=False, sortByCreationTime=False,
            priorityTarget=None, autoPurge=True):
        '''Get references; unwrap from weakrefs; order, based on dictionary keys, is from most recently added to least recently added.

        The `locationsTrail` option forces locations to come after all other defined contexts.

        The `sortByCreationTime` option will sort objects by creation time, where most-recently assigned objects are returned first. 

        If `priorityTarget` is defined, this object will be placed first in the list of objects.

        If `autoPurge` is True, this method automatically removes dead weak-refs. Thus, every time locations are gotten, any dead weakrefs are removed. This provides a modest performance boost. 

        >>> from music21 import *
        >>> import time
        >>> class Mock(Music21Object): pass
        >>> aObj = Mock()
        >>> bObj = Mock()
        >>> cObj = Mock()
        >>> aContexts = DefinedContexts()
        >>> aContexts.add(cObj, 345) # a locations
        >>> #time.sleep(.05)
        >>> aContexts.add(aObj)
        >>> #time.sleep(.05)
        >>> aContexts.add(bObj)
        >>> aContexts.get() == [cObj, aObj, bObj]
        True
        >>> aContexts.get(locationsTrail=True) == [aObj, bObj, cObj]
        True
        >>> aContexts.get(sortByCreationTime=True) == [bObj, aObj, cObj]
        True
        '''
        if sortByCreationTime in [True, 1]:
            keyRepository = self._keysByTime(newFirst=True)
        # reverse creation time puts oldest elements first
        elif sortByCreationTime in [-1, 'reverse']:
            keyRepository = self._keysByTime(newFirst=False)
        else: # None, or False
            keyRepository = self._definedContexts.keys()

        post = [] 
        purgeKeys = []
        
        # get partitioned lost of all, w/ locations last if necessary
        if locationsTrail:
            keys = []
            keysLocations = [] # but possibly sorted
            for key in keyRepository:
                if key not in self._locationKeys: # skip these
                    keys.append(key) # others first
                else:
                    keysLocations.append(key)
            keys += keysLocations # now locations are at end
        else:
            keys = keyRepository
            
        # get each dict from all defined contexts
        for key in keys:
            dict = self._definedContexts[key]
            # check for None object; default location, not a weakref, keep
            if dict['obj'] == None:
                post.append(dict['obj'])
            elif WEAKREF_ACTIVE:
                obj = common.unwrapWeakref(dict['obj'])
                if obj is None: # dead ref
                    purgeKeys.append(key)
                else:
                    post.append(obj)
            else:
                post.append(dict['obj'])

        # remove dead references
        if autoPurge:
            for key in purgeKeys:
                self.removeById(key)

        if priorityTarget is not None:
            if priorityTarget in post:
                #environLocal.printDebug(['priorityTarget found in post:', priorityTarget])
                # extract object and make first
                post.insert(0, post.pop(post.index(priorityTarget)))
        return post

    #---------------------------------------------------------------------------
    # for dealing with locations
    def getSites(self):
        '''Get all defined contexts that are locations; unwrap from weakrefs

        >>> from music21 import *
        >>> class Mock(Music21Object): pass
        >>> aObj = Mock()
        >>> bObj = Mock()
        >>> aContexts = DefinedContexts()
        >>> aContexts.add(aObj, 234)
        >>> aContexts.add(bObj, 3000)
        >>> len(aContexts._locationKeys) == 2
        True
        >>> len(aContexts.getSites()) == 2
        True
        '''
        # use pre-collected keys
        post = []
        for idKey in self._locationKeys:
            try:
                s1 = self._definedContexts[idKey]['obj']
            except KeyError:
                raise DefinedContextsException('no such site: %s' % idKey)
            if s1 is None or WEAKREF_ACTIVE == False: # leave None alone
                post.append(s1)
            else:
                post.append(common.unwrapWeakref(s1))
        return post
    

    def getSitesByClass(self, className):
        '''Return sites that match the provided class.

        >>> from music21 import *
        >>> class Mock(Music21Object): pass
        >>> aObj = Mock()
        >>> bObj = Mock()
        >>> cObj = stream.Stream()
        >>> aContexts = DefinedContexts()
        >>> aContexts.add(aObj, 234)
        >>> aContexts.add(bObj, 3000)
        >>> aContexts.add(cObj, 200)
        >>> aContexts.getSitesByClass(Mock) == [aObj, bObj]
        True
        >>> aContexts.getSitesByClass('Stream') == [cObj]
        True
        '''
        found = []
        for idKey in self._locationKeys:
            objRef = self._definedContexts[idKey]['obj']
            if objRef is None:
                continue
            if not WEAKREF_ACTIVE: # leave None alone
                obj = objRef
            else:
                obj = common.unwrapWeakref(objRef)
            match = False
            if common.isStr(className):
                if hasattr(obj, 'classes'):
                    if className in obj.classes:
                        match = True
                elif type(obj).__name__.lower() == className.lower():
                    match = True
            elif isinstance(obj, className):
                match = True
            if match:
                found.append(obj)
        return found

    def isSite(self, obj):
        '''Given an object, determine if it is a site stored in this DefinedContexts. This will return False if the object is simply a context and not a location

        >>> class Mock(Music21Object): pass
        >>> aSite = Mock()
        >>> bSite = Mock()
        >>> aLocations = DefinedContexts()
        >>> aLocations.add(aSite, 0)
        >>> aLocations.add(bSite) # a context
        >>> aLocations.isSite(aSite)
        True
        >>> aLocations.isSite(bSite)
        False
        '''
        if id(obj) in self._locationKeys:
            return True
        else:
            return False

    def hasSiteId(self, siteId):
        '''Return True or False if this DefinedContexts object already has this site id defined as a location

        >>> from music21 import *; import music21
        >>> class Mock(Music21Object): pass
        >>> aSite = Mock()
        >>> bSite = Mock()
        >>> dc = music21.DefinedContexts()
        >>> dc.add(aSite, 0)
        >>> dc.add(bSite) # a context
        >>> dc.hasSiteId(id(aSite))
        True
        >>> dc.hasSiteId(id(bSite))
        False
        '''
        if siteId in self._locationKeys:
            return True
        else:
            return False

    def getSiteIds(self):
        '''Return a list of all site Ids.

        >>> from music21 import *; import music21
        >>> class Mock(Music21Object): pass
        >>> aSite = Mock()
        >>> bSite = Mock()
        >>> dc = music21.DefinedContexts()
        >>> dc.add(aSite, 0)
        >>> dc.add(bSite) # a context
        >>> dc.getSiteIds() == [id(aSite)]
        True
        '''
        # may want to convert to tuple to avoid user editing?
        return self._locationKeys


    def purgeLocations(self):
        '''Clean all locations that refer to objects that no longer exist.

        >>> class Mock(Music21Object): pass
        >>> aSite = Mock()
        >>> bSite = Mock()
        >>> cSite = Mock()
        >>> dSite = Mock()
        >>> aLocations = DefinedContexts()
        >>> aLocations.add(aSite, 0)
        >>> aLocations.add(cSite) # a context
        >>> del aSite
        >>> len(aLocations)
        2
        >>> aLocations.purgeLocations()
        >>> len(aLocations)
        1
        '''
        match = []
        for idKey in self._locationKeys:
            if idKey == None: 
                continue
            if WEAKREF_ACTIVE:
                obj = common.unwrapWeakref(self._definedContexts[idKey]['obj'])
            else:
                obj = self._definedContexts[idKey]['obj']
            if obj == None: # if None, it no longer exists
                match.append(idKey)
        for id in match:
            self.removeById(id)

    def _getOffsetBySiteId(self, idKey):
        '''Main method for getting an offset from a location key.

        >>> class Mock(Music21Object): pass
        >>> aSite = Mock()
        >>> bSite = Mock()
        >>> cSite = Mock()
        >>> dSite = Mock()
        >>> eSite = Mock()
        >>> aLocations = DefinedContexts()
        >>> aLocations.add(aSite, 0)
        >>> aLocations.add(cSite) # a context
        >>> aLocations.add(bSite, 234) # can add at same offset or another
        >>> aLocations.add(dSite) # a context
        >>> aLocations._getOffsetBySiteId(id(bSite))
        234
        '''
        try:
            value = self._definedContexts[idKey]['offset']
        except KeyError:
            raise DefinedContextsException("Could not find the object with id %d in the Site marked with idKey %d" % (id(self), idKey))
        # stored string are summed to be attributes of the stored object
        if isinstance(value, str):
            if value not in ['highestTime', 'lowestOffset', 'highestOffset']:
                raise DefinedContextsException('attempted to set a bound offset with a string attribute that is not supported: %s' % value)

            if WEAKREF_ACTIVE:
                obj = common.unwrapWeakref(self._definedContexts[idKey]['obj'])
            else:
                obj = self._definedContexts[idKey]['obj']
            # offset value is an attribute string
            return getattr(obj, value)
        # if value is not a string, it is a proper offset
        else:
            return value

    def getOffsets(self):
        '''Return a list of all offsets.

        >>> class Mock(Music21Object): pass
        >>> aSite = Mock()
        >>> bSite = Mock()
        >>> cSite = Mock()
        >>> dSite = Mock()
        >>> aLocations = DefinedContexts()
        >>> aLocations.add(aSite, 0)
        >>> aLocations.add(cSite) # a context
        >>> aLocations.add(bSite, 234) # can add at same offset or another
        >>> aLocations.add(dSite) # a context
        >>> aLocations.getOffsets()
        [0, 234]
        '''
        # here, already having location keys may be an advantage
        return [self._getOffsetBySiteId(x) for x in self._locationKeys] 


    def getOffsetByObjectMatch(self, obj):
        '''For a given object return the offset using a direct object match. The stored id value is not used; instead, the id() of both the stored object reference and the supplied objet is used. 

        >>> class Mock(Music21Object): pass
        >>> aSite = Mock()
        >>> bSite = Mock()
        >>> cParent = Mock()
        >>> aLocations = DefinedContexts()
        >>> aLocations.add(aSite, 23)
        >>> aLocations.add(bSite, 121.5)
        >>> aLocations.getOffsetBySite(aSite)
        23
        >>> aLocations.getOffsetBySite(bSite)
        121.5
        '''
        for idKey in self._definedContexts.keys():
            dict = self._definedContexts[idKey]
            # must unwrap references before comparison
            #if common.isWeakref(dict['obj']):
            if WEAKREF_ACTIVE:
                compareObj = common.unwrapWeakref(dict['obj'])
            else:
                compareObj = dict['obj']
            if id(compareObj) == id(obj):
                return self._getOffsetBySiteId(idKey) #dict['offset']
        raise DefinedContextsException('an entry for this object (%s) is not stored in DefinedContexts' % obj)

    def getOffsetBySite(self, site):
        '''For a given site return its offset. The None site is permitted. The id() of the site is used to find the offset. 

        >>> class Mock(Music21Object): pass
        >>> aSite = Mock()
        >>> bSite = Mock()
        >>> cParent = Mock()
        >>> aLocations = DefinedContexts()
        >>> aLocations.add(aSite, 23)
        >>> aLocations.add(bSite, 121.5)
        >>> aLocations.getOffsetBySite(aSite)
        23
        >>> aLocations.getOffsetBySite(bSite)
        121.5
        '''
        # NOTE: this is a performance critical operation
        siteId = None
        if site is not None:
            siteId = id(site)
        try:
            # will raise a key error if not found
            post = self._getOffsetBySiteId(siteId) 
            #post = self._definedContexts[siteId]['offset']
        except DefinedContextsException: # the site id is not valid
            environLocal.printDebug(['getOffsetBySite: trying to get an offset by a site failed; self:', self, 'site:', site, 'defined contexts:', self._definedContexts])

#             self.purgeLocations()
#             environLocal.printDebug(['post purge locations', self, 'site:', site, 'defined contexts:', self._definedContexts])

            raise # re-raise Exception

        if post is None: # 
            raise DefinedContextsException('an entry for this object (%s) is not stored in DefinedContexts' % siteId)
        #self._definedContexts[siteId]['offset']
        return post


    def getOffsetBySiteId(self, siteId):
        '''For a given site id, return its offset.

        >>> class Mock(Music21Object): pass
        >>> aSite = Mock()
        >>> bSite = Mock()
        >>> cParent = Mock()
        >>> aLocations = DefinedContexts()
        >>> aLocations.add(aSite, 23)
        >>> aLocations.add(bSite, 121.5)
        >>> aLocations.getOffsetBySiteId(id(aSite))
        23
        >>> aLocations.getOffsetBySiteId(id(bSite))
        121.5
        '''
        post = self._getOffsetBySiteId(siteId) 
        #post = self._definedContexts[siteId]['offset']
        if post == None: # 
            raise DefinedContextsException('an entry for this object (%s) is not stored in DefinedContexts' % siteId)
        return post


    def setOffsetBySite(self, site, value):
        '''Changes the offset of the site specified.  Note that this can also be
        done with add, but the difference is that if the site is not in 
        DefinedContexts, it will raise an exception.
        
        >>> class Mock(Music21Object): pass
        >>> aSite = Mock()
        >>> bSite = Mock()
        >>> cSite = Mock()
        >>> aLocations = DefinedContexts()
        >>> aLocations.add(aSite, 23)
        >>> aLocations.add(bSite, 121.5)
        >>> aLocations.setOffsetBySite(aSite, 20)
        >>> aLocations.getOffsetBySite(aSite)
        20
        >>> aLocations.setOffsetBySite(cSite, 30)        
        Traceback (most recent call last):
        DefinedContextsException: ...
        '''
        siteId = None
        if site != None:
            siteId = id(site)
        # will raise an index error if the siteId does not exist
        try:
            self._definedContexts[siteId]['offset'] = value
        except KeyError:
            raise DefinedContextsException('an entry for this object (%s) is not stored in DefinedContexts' % site)
            

    def setOffsetBySiteId(self, siteId, value):
        '''Set an offset by siteId. This assumes that the site is valid, is best used for advanced, performance critical usage only.

        The `siteId` parameter can be None
        '''
        try:
            self._definedContexts[siteId]['offset'] = value
        except KeyError:
            raise DefinedContextsException('an entry for this object (%s) is not stored in DefinedContexts' % site)


    def getSiteByOffset(self, offset):
        '''For a given offset return the parent

        # More than one parent may have the same offset; 
        # this can return the last site added by sorting time

        No - now we use a dict, so there's no guarantee that the one you want will be there -- need orderedDicts!

        >>> class Mock(Music21Object): pass
        >>> aSite = Mock()
        >>> bSite = Mock()
        >>> cSite = Mock()
        >>> aLocations = DefinedContexts()
        >>> aLocations.add(aSite, 23)
        >>> aLocations.add(bSite, 23121.5)
        >>> aSite == aLocations.getSiteByOffset(23)
        True
        '''
        match = None
        for siteId in self._definedContexts.keys():
            # might need to use almost equals here
            if self._definedContexts[siteId]['offset'] == offset:
                match = self._definedContexts[siteId]['obj']
                break
        if WEAKREF_ACTIVE:
            if match is None:
                return match
            elif not common.isWeakref(match):
                raise DefinedContextsException('site on coordinates is not a weak ref: %s' % match)
            return common.unwrapWeakref(match)
        else:
            return match


    #---------------------------------------------------------------------------
    # for dealing with contexts or getting other information

    def getByClass(self, className, serialReverseSearch=True, callerFirst=None,
             sortByCreationTime=False, prioritizeActiveSite=False, 
             priorityTarget=None, memo=None):
        '''Return the most recently added reference based on className. Class name can be a string or the class name.

        This will recursively search the defined contexts of existing defined contexts.

        The `callerFirst` parameters is simply used to pass a reference of the first caller; this
        is necessary if we are looking within a Stream for a flat offset position.

        If `priorityTarget` is specified, this location will be searched first. The `prioritizeActiveSite` is pased to to any recursively called getContextByClass() calls. 

        >>> class Mock(Music21Object): pass
        >>> import time
        >>> aObj = Mock()
        >>> bObj = Mock()
        >>> aContexts = DefinedContexts()
        >>> aContexts.add(aObj)
        >>> #time.sleep(.05)
        >>> aContexts.add(bObj)
        >>> # we get the most recently added object first
        >>> aContexts.getByClass('mock', sortByCreationTime=True) == bObj
        True
        >>> aContexts.getByClass(Mock, sortByCreationTime=True) == bObj
        True

        OMIT_FROM_DOCS
        TODO: not sure if memo is properly working: need a test case
        '''
        # in general, this should not be the first caller, as this method
        # is called from a Music21Object, not directly on the DefinedContexts
        # isntance. Nontheless, if this is the first caller, it is the first
        # caller. 
        if callerFirst == None: # this is the first caller
            callerFirst = self
        if memo == None:
            memo = {} # intialize

        post = None

        count = 0
        # search any defined contexts first
        # need to sort: look at most-recently added objs are first

        # TODO: can optimize search of defined contexts if we store in advance
        # all class names; then weakrefs will not have to be used
        objs = self.get(locationsTrail=True,  
                        sortByCreationTime=sortByCreationTime,
                        priorityTarget=priorityTarget)
        for obj in objs:
            #environLocal.printDebug(['memo', memo])
            if obj is None: 
                continue # a None context, or a dead reference
            # TODO: look for classes attribute
            if common.isStr(className):
                if type(obj).__name__.lower() == className.lower():
                    post = obj       
                    break
            elif isinstance(obj, className):
                    post = obj       
                    break
        if post != None:
            return post

        # all objs here are containers, as they are all locations
        for obj in objs:
            if obj is None: 
                continue # in case the reference is dead
            # if after trying to match name, look in the defined contexts' 
            # defined contexts [sic!]
            if post is None: # no match yet
                # access public method to recurse
                if id(obj) not in memo.keys():
                    # if the object is a Musci21Object
                    if hasattr(obj, 'getContextByClass'):
                        # store this object as having been searched
                        memo[id(obj)] = obj
                        post = obj.getContextByClass(className,
                               serialReverseSearch=serialReverseSearch,
                               callerFirst=callerFirst, 
                               sortByCreationTime=sortByCreationTime, 
                               prioritizeActiveSite=prioritizeActiveSite,
                               memo=memo)
                        if post != None:
                            break
                    else: # this is not a music21 object
                        pass
                        #environLocal.printDebug['cannot call getContextByClass on obj stored in DefinedContext:', obj]
                else: # objec has already been searched
                    pass
                    #environLocal.printDebug['skipping searching of object already searched:', obj]
            else: # post is not None
                break
        return post



    def getAllByClass(self, className, found=None, idFound=None, memo=None):
        '''Return all known references of a given class found in any association with this DefinedContexts.

        This will recursively search the defined contexts of existing defined contexts, and return a list of all objects that match the given class.

        >>> from music21 import *; import music21
        >>> class Mock(Music21Object): pass
        >>> import time
        >>> aObj = Mock()
        >>> bObj = Mock()
        >>> dc = music21.DefinedContexts()
        >>> dc.add(aObj)
        >>> dc.add(bObj)
        >>> dc.getAllByClass = [aObj, bObj]
        '''
        if memo == None:
            memo = {} # intialize
        if found == None:
            found = []
        if idFound == None:
            idFound = []

        objs = self.get(locationsTrail=False)
        for obj in objs:
            #environLocal.printDebug(['memo', memo])
            if obj is None: 
                continue # in case the reference is dead
            if common.isStr(className):
                if type(obj).__name__.lower() == className.lower():
                    found.append(obj)
                    idFound.append(id(obj))
            elif isinstance(obj, className):
                    found.append(obj)
                    idFound.append(id(obj))
        for obj in objs:
            if obj is None: 
                continue # in case the reference is dead
            # if after trying to match name, look in the defined contexts' 
            # defined contexts [sic!]
            if id(obj) not in memo.keys():
                # if the object is a Musci21Object
                if hasattr(obj, 'getContextByClass'):
                    # store this object as having been searched
                    memo[id(obj)] = obj
                    # will add values to found
                    #environLocal.printDebug(['getAllByClass()', 'about to call getAllContextsByClass', 'found', found, 'obj', obj])
                    obj.getAllContextsByClass(className, found=found,
                        idFound=idFound, memo=memo)
        # returning found, but not necessary
        return found

    def getAttrByName(self, attrName):
        '''Given an attribute name, search all objects and find the first
        that matches this attribute name; then return a reference to this attribute.

        >>> class Mock(Music21Object): attr1=234
        >>> aObj = Mock()
        >>> aObj.attr1 = 234
        >>> bObj = Mock()
        >>> bObj.attr1 = 98
        >>> aContexts = DefinedContexts()
        >>> aContexts.add(aObj)
        >>> len(aContexts)
        1
        >>> aContexts.getAttrByName('attr1') == 234
        True
        >>> aContexts.removeById(id(aObj))
        >>> aContexts.add(bObj)
        >>> aContexts.getAttrByName('attr1') == 98
        True
        '''
        post = None
        for obj in self.get():
            if obj is None: 
                continue # in case the reference is dead
            try:
                post = getattr(obj, attrName)
                return post
            except AttributeError:
                pass

    def setAttrByName(self, attrName, value):
        '''Given an attribute name, search all objects and find the first
        that matches this attribute name; then return a reference to this attribute.

        >>> class Mock(Music21Object): attr1=234
        >>> aObj = Mock()
        >>> bObj = Mock()
        >>> bObj.attr1 = 98
        >>> aContexts = DefinedContexts()
        >>> aContexts.add(aObj)
        >>> aContexts.add(bObj)
        >>> aContexts.setAttrByName('attr1', 'test')
        >>> aContexts.getAttrByName('attr1') == 'test'
        True
        '''
        post = None
        for obj in self.get():
            if obj is None: continue # in case the reference is dead
            try:
                junk = getattr(obj, attrName) # if attr already exists
                setattr(obj, attrName, value) # if attr already exists
            except AttributeError:
                pass

#     def find(self, classList, recursive=True, hasAttr=None):
#         pass




#-------------------------------------------------------------------------------
class JSONSerializerException(Exception):
    pass


class JSONSerializer(object):
    '''Class that provides JSON output and input routines. Objects can inherit this class directly, or gain its functional through inheriting Music21Object. 
    '''
    # note that, since this inherits form object, other classes that inherit
    # this class need to give object last
    # e.g. class Text(music21.JSONSerializer, object):

    def __init__(self):
        pass

    #---------------------------------------------------------------------------
    # override these methods for json functionality

    def jsonAttributes(self):
        '''Define all attributes of this object that should be JSON serialized for storage and re-instantiation. Attributes that name basic Python objects or :class:`~music21.base.JSONSerializer` subclasses, or dictionaries or lists that contain Python objects or :class:`~music21.base.JSONSerializer` subclasses, can be provided.
        '''
        return []

    def jsonComponentFactory(self, idStr):
        '''Given a stored string during JSON serialization, return an object'

        The subclass that overrides this method will have access to all modules necessary to create whatever objects necessary. 
        '''
        return None

    #---------------------------------------------------------------------------
    # core methods for getting and setting

    def _getJSONDict(self, includeVersion=False):
        '''Return a dictionary representation for JSON processing. All component objects are similarly encoded as dictionaries. This method is recursively called as needed to store dictionaries of component objects that are :class:`~music21.base.JSONSerializer` subclasses.

        >>> from music21 import *
        >>> t = metadata.Text('my text')
        >>> t.language = 'en'
        >>> post = t.json # cannot show string as self changes in context
        '''
        src = {'__class__': str(self.__class__)}
        # always store the version used to create this data
        if includeVersion:
            src['__version__'] = VERSION

        # flat data attributes
        flatData = {}
        for attr in self.jsonAttributes():
            #environLocal.printDebug(['_getJSON', attr])
            attrValue = getattr(self, attr)
            # do not store None values; assume initial/unset state
            if attrValue is None:
                continue

            # if, stored on this object, is an object w/ a json method
            if hasattr(attrValue, 'json'):
                flatData[attr] = attrValue._getJSONDict()

            # handle lists; look for objects that have json attributes
            elif isinstance(attrValue, (list, tuple)):
                flatData[attr] = []
                for attrValueSub in attrValue:
                    if hasattr(attrValueSub, 'json'):
                        flatData[attr].append(attrValueSub._getJSONDict())
                    else: # just store normal data
                        flatData[attr].append(attrValueSub)

            # handle dictionaries; look for objects that have json attributes
            elif isinstance(attrValue, dict):
                flatData[attr] = {}
                for key in attrValue.keys():
                    attrValueSub = attrValue[key]
                    # skip None values for efficiency
                    if attrValueSub is None:
                        continue
                    # see if this object stores a json object or otherwise
                    if hasattr(attrValueSub, 'json'):
                        flatData[attr][key] = attrValueSub._getJSONDict()
                    else: # just store normal data
                        flatData[attr][key] = attrValueSub
            else:
                flatData[attr] = attrValue
        src['__attr__'] = flatData
        return src

    def _getJSON(self):
        '''Return the dictionary returned by _getJSONDict() as a JSON string.
        '''
        # when called from json property, include version number;
        # this should mean that only the outermost object has a version number
        return json.dumps(self._getJSONDict(includeVersion=True))


    def _isComponent(self, target):
        '''Return a boolean if the provided object is a dictionary that defines a __class__ key, the necessary conditions to try to instantiate a component object with the jsonComponentFactory method.
        '''
        # on export, check for attribute
        if isinstance(target, dict) and '__class__' in target.keys():
            return True
        return False

    def _buildComponent(self, src):
        # get instance from subclass overridden method
        obj = self.jsonComponentFactory(src['__class__'])
        # assign dictionary (property takes dictionary or string)
        obj.json = src
        return obj

    def _setJSON(self, jsonStr):
        '''Set this object based on a JSON string or instantiated dictionary representation.

        >>> from music21 import *
        >>> t = metadata.Text('my text')
        >>> t.language = 'en'
        >>> tNew = metadata.Text()
        >>> tNew.json = t.json
        >>> str(t)
        'my text'
        >>> t.language
        'en'
        '''
        #environLocal.printDebug(['_setJSON: srcStr', jsonStr])
        if isinstance(jsonStr, dict):
            d = jsonStr # do not loads  
        else:
            d = json.loads(jsonStr)

        for attr in d.keys():
            #environLocal.printDebug(['_setJSON: attr', attr, d[attr]])
            if attr == '__class__':
                pass
            elif attr == '__version__':
                pass
            elif attr == '__attr__':
                for key in d[attr].keys():
                    attrValue = d[attr][key]

                    if attrValue == None or isinstance(attrValue, 
                        (int, float)):
                        setattr(self, key, attrValue)

                    # handle a list or tuple, looking for dicts that define objs
                    elif isinstance(attrValue, (list, tuple)):
                        subList = []
                        for attrValueSub in attrValue:
                            if self._isComponent(attrValueSub):
                                subList.append(
                                    self._buildComponent(attrValueSub))
                            else:
                                subList.append(attrValueSub)
                        setattr(self, key, subList)

                    # handle a dictionary, looking for dicts that define objs
                    elif isinstance(attrValue, dict):
                        # could be a data dict or a dict of objects; 
                        # if an object, will have a __class__ key
                        if self._isComponent(attrValue):
                            setattr(self, key, self._buildComponent(attrValue))
                        # its a data dictionary; could contain objects as
                        # dictionaries, or flat data                           
                        else:
                            subDict = {}
                            for subKey in attrValue.keys():
                                # this could be flat data or a obj definition
                                # in a dictionary
                                attrValueSub = attrValue[subKey]
                                # if a dictionary, and defines a __class__, 
                                # create an object
                                if self._isComponent(attrValueSub):
                                    subDict[subKey] = self._buildComponent(
                                        attrValueSub)
                                else:
                                    subDict[subKey] = attrValueSub
                            #setattr(self, key, subDict)
                            dst = getattr(self, key)
                            # updating the dictionary preserves default 
                            # values created at init
                            dst.update(subDict) 
                    else: # assume a string
                        setattr(self, key, attrValue)

            else:
                raise JSONSerializerException('cannot handle json attr: %s'% attr)

    json = property(_getJSON, _setJSON, 
        doc = '''Get or set string JSON data for this object. This method is only available if a JSONSerializer subclass object has been customized and configured by overriding the following methods: :meth:`~music21.base.JSONSerializer.jsonAttributes`, :meth:`~music21.base.JSONSerializer.jsonComponentFactory`.

        ''')    


    def jsonPrint(self):
        print(json.dumps(self._getJSONDict(includeVersion=True), 
            sort_keys=True, indent=2))


    def jsonWrite(self, fp, format=True):
        '''Given a file path, write JSON to a file for this object. Default file extension should be .json. File is opened and closed within this method call. 
        '''
        f = codecs.open(fp, mode='w', encoding='utf-8')
        if not format:
            f.write(json.dumps(self._getJSONDict(includeVersion=True)))
        else:
            f.write(json.dumps(self._getJSONDict(includeVersion=True), 
            sort_keys=True, indent=2))
        f.close()

    def jsonRead(self, fp):
        '''Given a file path, read JSON from a file to this object. Default file extension should be .json. File is opened and closed within this method call. 
        '''
        f = open(fp)
        self.json = f.read()
        f.close()





#-------------------------------------------------------------------------------
class Music21Object(JSONSerializer):
    '''
    Base class for all music21 objects.
    
    All music21 objects encode 7 pieces of information:
    
    (1) id: identification string unique to the objects container (optional)
    (2) groups: a Groups object: which is a list of strings identifying 
                    internal subcollections
                    (voices, parts, selections) to which this element belongs
    (3) duration: Duration object representing the length of the object
    (4) parent: a reference or weakreference to a currently active Location
    (5) offset: a floating point value, generally in quarter lengths, specifying the position of the object in parent 
    (6) priority: int representing the position of an object among all
                    objects at the same offset.

    Contexts, locations, and offsets are stored in a  :class:`~music21.base.DefinedContexts` object. Locations specify connections of this object to one location in a Stream subclass. Contexts are weakrefs for current objects that are associated with this object (similar to locations but without an offset)


    Each of these may be passed in as a named keyword to any music21 object.
    Some of these may be intercepted by the subclassing object (e.g., duration within Note)
    '''

    _duration = None
    _definedContexts = None
    id = None
    _priority = 0
    classSortOrder = 20  # default classSortOrder

    # define order to present names in documentation; use strings
    _DOC_ORDER = ['searchParentByAttr', 'getContextAttr', 'setContextAttr']
    # documentation for all attributes (not properties or methods)
    _DOC_ATTR = {
    'id': 'Unique identification string.',
    'groups': 'An instance of a Group object.',
    'classSortOrder' : '''Property which returns an number (int or otherwise)
        depending on the class of the Music21Object that
        represents a priority for an object based on its class alone --
        used as a tie for stream sorting in case two objects have the
        same offset and priority.  Lower numbers are sorted to the left
        of higher numbers.  For instance, Clef, KeySignature, TimeSignature
        all come (in that order) before Note.
        
        All undefined classes have classSortOrder of 20 -- same as note.Note
        
        >>> from music21 import *
        >>> tc = clef.TrebleClef()
        >>> tc.classSortOrder
        0
        >>> ks = key.KeySignature(3)
        >>> ks.classSortOrder
        1
        
        
        
        New classes can define their own default classSortOrder
        
        
        
        >>> class ExampleClass(base.Music21Object):
        ...     classSortOrderDefault = 5
        ...
        >>> ec1 = ExampleClass()
        >>> ec1.classSortOrder
        5
        ''',

    }

    def __init__(self, *arguments, **keywords):

        # an offset keyword arg should set the offset in location
        # not in a local parameter
#         if "offset" in keywords and not self.offset:
#             self.offset = keywords["offset"]

        self._overriddenLily = None
        # None is stored as the internal location of an obj w/o a parent
        self._activeSite = None
        # cached id in case the weakref has gone away...
        self._activeSiteId = None 
    
        # if this element has been copied, store the id() of the last source
        self._idLastDeepCopyOf = None

        if "id" in keywords and not self.id:
            self.id = keywords["id"]            
        else:
            self.id = id(self)
        
        if "duration" in keywords and self.duration is None:
            self.duration = keywords["duration"]
        else:
            self.duration = duration.Duration(0)
        
        if "groups" in keywords and keywords["groups"] is not None and \
            (not hasattr(self, "groups") or self.groups is None):
            self.groups = keywords["groups"]
        elif not hasattr(self, "groups"):
            self.groups = Groups()
        elif self.groups is None:
            self.groups = Groups()

        # TODO: key word should be definedContexts
        if "locations" in keywords and self._definedContexts is None:
            self._definedContexts = keywords["locations"]
        else:
            self._definedContexts = DefinedContexts()
            # set up a default location for self at zero
            # use None as the name of the site
            self._definedContexts.add(None, 0.0)

        if "activeSite" in keywords and self.activeSite is None:
            self.activeSite = keywords["activeSite"]
        
#         if ("definedContexts" in keywords and 
#             keywords["definedContexts"] is not None and 
#             self._definedContexts is None):
#             self._definedContexts = keywords["definedContexts"]
#         elif self._definedContexts is None:
#             self._definedContexts = []

    def mergeAttributes(self, other):
        '''
        Merge all elementary, static attributes. Namely, 
        `id` and `groups` attributes from another music21 object. 
        Can be useful for copy-like operations.
        '''
        self.id = other.id
        self.groups = copy.deepcopy(other.groups)



    def __deepcopy__(self, memo=None):
        '''
        Helper method to copy.py's deepcopy function.  Call it from there.

        memo=None is the default as specified in copy.py

        Problem: if an attribute is defined with an understscore (_priority) but
        is also made available through a property (e.g. priority)  using dir(self) 
        results in the copy happening twice. Thus, __dict__.keys() is used.

        >>> from copy import deepcopy
        >>> from music21 import note, duration
        >>> n = note.Note('A')
        >>> n.offset = 1.0 #duration.Duration("quarter")
        >>> n.groups.append("flute")
        >>> n.groups
        ['flute']

        >>> b = deepcopy(n)
        >>> b.offset = 2.0 #duration.Duration("half")
        
        >>> n is b
        False
        >>> n.accidental = "-"
        >>> b.name
        'A'
        >>> n.offset
        1.0
        >>> b.offset
        2.0
        >>> n.groups[0] = "bassoon"
        >>> ("flute" in n.groups, "flute" in b.groups)
        (False, True)
        '''
        # call class to get a new, empty instance
        new = self.__class__()
        #environLocal.printDebug(['Music21Object.__deepcopy__', self, id(self)])
        #for name in dir(self):
        for name in self.__dict__.keys():
            if name.startswith('__'):
                continue
            part = getattr(self, name)
            # attributes that require special handling
            if name == '_activeSite':
                #environLocal.printDebug(['creating parent reference'])
                newValue = self.activeSite # keep a reference, not a deepcopy
                setattr(new, name, newValue)
            # this is an error check, particularly for object that inherit
            # this object and place a Stream as an attribute
            elif hasattr(part, '_elements'):
                environLocal.printDebug(['found stream in dict keys', self,
                    part, name])
                raise Music21Exception('streams as attributes requires special handling when deepcopying')
            else: # use copy.deepcopy, will call __deepcopy__ if available
                newValue = copy.deepcopy(part, memo)
                #setattr() will call the set method of a named property.
                setattr(new, name, newValue)

        # must do this after copying
        new._idLastDeepCopyOf = id(self)
        return new


#     def isClass(self, className):
#         '''
#         DEPRECATED: DO NOT USE!
#         
#         Returns a boolean value depending on if the object is a particular class or not.
#         
#         In Music21Object, it just returns the result of `isinstance`. For Elements it will return True if the embedded object is of the given class.  Thus, best to use it throughout music21 and only use isinstance if you really want to see if something is an ElementWrapper or not.
# 
#         >>> from music21 import *
#         >>> n = note.Note()
#         >>> n.isClass(note.Note)
#         True
#         >>> e = ElementWrapper(3.2)
#         >>> e.isClass(note.Note)
#         False
#         >>> e.isClass(float)
#         True
# 
#         '''
#         if isinstance(self, className):
#             return True
#         else:
#             return False

    def _getClasses(self):
        # TODO: cache this as a stored list?
        return [x.__name__ for x in self.__class__.mro()] 

    classes = property(_getClasses, 
        doc='''Returns a list containing the names (strings, not objects) of classes that this 
        object belongs to -- starting with the object's class name and going up the mro()
        for the object.  Very similar to Perl's @ISA array:
    
        >>> from music21 import *
        >>> q = note.QuarterNote()
        >>> q.classes[:5]
        ['QuarterNote', 'Note', 'NotRest', 'GeneralNote', 'Music21Object']
        
        
        Example: find GClefs that are not Treble clefs (or treble 8vb, etc.):
        
        
        >>> s = stream.Stream()
        >>> s.insert(10, clef.GClef())
        >>> s.insert(20, clef.TrebleClef())
        >>> s.insert(30, clef.FrenchViolinClef())
        >>> s.insert(40, clef.Treble8vbClef())
        >>> s.insert(50, clef.BassClef())
        >>> s2 = stream.Stream()
        >>> for t in s:
        ...    if 'GClef' in t.classes and 'TrebleClef' not in t.classes:
        ...        s2.insert(t)
        >>> s2.show('text')
        {10.0} <music21.clef.GClef object at 0x...>
        {30.0} <music21.clef.FrenchViolinClef object at 0x...>    
        ''')
    
    #---------------------------------------------------------------------------
    # look at this object for an atttribute; if not here
    # look up to activeSite

    def searchParentByAttr(self, attrName):
        '''If this element is contained within a Stream or other Music21 element, 
        searchParentByAttr() permits searching attributes of higher-level
        objects. The first encountered match is returned, or None if no match. All parents are recursively searched upward. 

        OMIT_FROM_DOCS
        this presently only searches upward; it does not search other lower level leafs in a container

        this was formerly called SeachParent, but we might do other types 
        of parent searches
        '''
        found = None
        try:
            found = getattr(self.activeSite, attrName)
        except AttributeError:
            # not sure of passing here is the best action
            environLocal.printDebug(['searchParentByAttr call raised attribute error for attribute:', attrName])
            pass
        if found is None:
            found = self.activeSite.searchParentByAttr(attrName)
        return found
        

#     def searchParentByClass(self, classFilterList)
#         '''
#         The first encountered result is returned. 
#         '''
#         if not isinstance(classFilterList, list):
#             if not isinstance(classFilterList, tuple):
#                 classFilterList = [classFilterList]


    def getOffsetBySite(self, site):
        '''If this class has been registered in a container such as a Stream, 
        that container can be provided here, and the offset in that object
        can be returned. 

        Note that this is different than the getOffsetByElement() method on 
        Stream in that this can never access the flat representation of a Stream.

        >>> from music21 import *
        >>> a = base.Music21Object()
        >>> a.offset = 30
        >>> a.getOffsetBySite(None)
        30.0
        
        >>> s1 = stream.Stream()
        >>> s1.insert(20.5, a)
        >>> a.getOffsetBySite(s1)
        20.5
        >>> s2 = stream.Stream()
        >>> a.getOffsetBySite(s2)
        Traceback (most recent call last):
        ...
        DefinedContextsException: Could not find the object with id ...
        
        '''
        return self._definedContexts.getOffsetBySite(site)


    def setOffsetBySite(self, site, value):
        '''Direct access to the DefinedContexts setOffsetBySite() method. This should only be used for advanced processing of known site that already has been added.

        >>> class Mock(Music21Object): pass
        >>> aSite = Mock()
        >>> a = Music21Object()
        >>> a.addLocation(aSite, 20)
        >>> a.setOffsetBySite(aSite, 30)
        '''
        return self._definedContexts.setOffsetBySite(site, value)


    def getContextAttr(self, attr):
        '''Given the name of an attribute, search Conctexts and return 
        the best match.

        >>> class Mock(Music21Object): attr1=234
        >>> aObj = Mock()
        >>> aObj.attr1 = 'test'
        >>> a = Music21Object()
        >>> a.addContext(aObj)
        >>> a.getContextAttr('attr1')
        'test'
        '''
        return self._definedContexts.getAttrByName(attr)

    def setContextAttr(self, attrName, value):
        '''Given the name of an attribute, search Conctexts and return 
        the best match.

        >>> class Mock(Music21Object): attr1=234
        >>> aObj = Mock()
        >>> aObj.attr1 = 'test'
        >>> a = Music21Object()
        >>> a.addContext(aObj)
        >>> a.getContextAttr('attr1')
        'test'
        >>> a.setContextAttr('attr1', 3000)
        >>> a.getContextAttr('attr1')
        3000
        '''
        return self._definedContexts.setAttrByName(attrName, value)

    def addContext(self, obj):
        '''Add an ojbect to the :class:`~music21.base.DefinedContexts` object. For adding a location, use :meth:`~music21.base.Music21Object.addLocation`.

        >>> class Mock(Music21Object): attr1=234
        >>> aObj = Mock()
        >>> aObj.attr1 = 'test'
        >>> a = Music21Object()
        >>> a.addContext(aObj)
        >>> a.getContextAttr('attr1')
        'test'
        '''
        return self._definedContexts.add(obj)

    def hasContext(self, obj):
        '''Return a Boolean if an object reference is stored in the object's DefinedContexts object.

        This checks both all locations as well as all sites. 

        >>> class Mock(Music21Object): attr1=234
        >>> aObj = Mock()
        >>> aObj.attr1 = 'test'
        >>> a = Music21Object()
        >>> a.addContext(aObj)
        >>> a.hasContext(aObj)
        True
        >>> a.hasContext(None)
        True
        >>> a.hasContext(45)
        False
        '''
        for dc in self._definedContexts.get(): # get all
            if obj == dc:
                return True
        else:
            return False

    def addLocation(self, site, offset):
        '''Add a location to the :class:`~music21.base.DefinedContexts` object. The supplied object is a reference to the object (the site) that contains an offset of this object.  For example, if this Music21Object was Note, the site would be a Stream (or Stream subclass) and the offset would be a number for the offset. 

        This is only for advanced location method and is not a complete or sufficient way to add an object to a Stream. 

        >>> from music21 import note, stream
        >>> s = stream.Stream()
        >>> n = note.Note()
        >>> n.addLocation(s, 10)
        '''
        self._definedContexts.add(site, offset)

    def getSites(self):
        '''Return a list of all objects that store a location for this object. Will remove None, the default empty site placeholder. 

        >>> from music21 import note, stream
        >>> s1 = stream.Stream()
        >>> s2 = stream.Stream()
        >>> n = note.Note()
        >>> s1.append(n)
        >>> s2.append(n)
        >>> n.getSites() == [None, s1, s2]
        True
        '''
        return self._definedContexts.getSites()

    def getSiteIds(self):
        '''Return a list of all site Ids, or the id() value of the sites of this object. 
        '''
        return self._definedContexts.getSiteIds()

    def getSpannerSites(self):
        '''Return a list of all sites that are Spanner or Spanner subclasses. This provides a way for objects to be aware of what Spanners they reside in. Note that Spanners are not Stream subclasses, but Music21Objects that are composed with a specialized Stream subclass.

        >>> from music21 import *
        >>> n1 = note.Note()
        >>> n2 = note.Note()
        >>> sp1 = spanner.Slur(n1, n2)
        >>> n1.getSpannerSites() == [sp1]
        True
        >>> sp2 = spanner.Slur(n2, n1)
        >>> n2.getSpannerSites() == [sp1, sp2]
        True
        '''
        found = self._definedContexts.getSitesByClass('SpannerStorage')
        post = []
        # get reference to actual spanner stored in each SpannerStorage obj
        # these are the Spanners
        for obj in found:
            post.append(obj.spannerParent)
        return post


    def removeLocationBySite(self, site):
        '''Remove a location in the :class:`~music21.base.DefinedContexts` object.

        This is only for advanced location method and is not a complete or sufficient way to remove an object from a Stream. 

        >>> from music21 import note, stream
        >>> s = stream.Stream()
        >>> n = note.Note()
        >>> n.addLocation(s, 10)
        >>> n.activeSite = s
        >>> n.removeLocationBySite(s)
        >>> n.activeSite == None
        True
        '''
        if not self._definedContexts.isSite(site):
            raise Music21ObjectException('supplied object (%s) is not a site in this object.')
        self._definedContexts.remove(site)
        # if parent is set to that site, reassign to None

        if self._getActiveSite() == site:
            self._setActiveSite(None)


    def removeLocationBySiteId(self, siteId):
        '''Remove a location in the :class:`~music21.base.DefinedContexts` object by id.

        >>> from music21 import note, stream
        >>> s = stream.Stream()
        >>> n = note.Note()
        >>> n.addLocation(s, 10)
        >>> n.activeSite = s
        >>> n.removeLocationBySiteId(id(s))
        >>> n.activeSite == None
        True
        '''
        self._definedContexts.removeById(siteId)
        p = self._getActiveSite()
        if p != None and id(p) == siteId:
            self._setActiveSite(None)


    def purgeLocations(self):
        '''Remove references to all locations in objects that no longer exist.
        '''
        self._definedContexts.purgeLocations()

#     def clearLocations(self):
#         '''Clear all locations stored by this object.
#         '''
#         self._definedContexts.clearLocations()


    def getContextByClass(self, className, serialReverseSearch=True,
                          callerFirst=None, sortByCreationTime=False, prioritizeActiveSite=True, memo=None):
        '''Search both DefinedContexts as well as associated objects to find a matching class. Returns None if not match is found. 

        The a reference to the caller is required to find the offset of the 
        object of the caller. This is needed for serialReverseSearch.

        The caller may be a DefinedContexts reference from a lower-level object.
        If so, we can access the location of that lower-level object. However, 
        if we need a flat representation, the caller needs to be the source 
        Stream, not its DefinedContexts reference.

        The `callerFirst` is the first object from which this method was called. This is needed in order to determine the final offset from which to search. 

        The `prioritizeActiveSite` parameter searches the objects parent before any other object. 
        '''
        #environLocal.printDebug(['call getContextByClass from:', self, 'parent:', self.activeSite, 'callerFirst:', callerFirst, 'prioritizeActiveSite', prioritizeActiveSite])
    
        # this method will be called recursively on all object levels, ascending
        # thus, to do serial reverse search we need to 
        # look at parent flat and track back to first encountered class match
        if prioritizeActiveSite:
            priorityTarget = self.activeSite
        else:
            priorityTarget = None

        if callerFirst is None: # this is the first caller
            callerFirst = self
        if memo is None:
            memo = {} # intialize

        post = None
        # first, if this obj is a Stream, we see if the class exists at or
        # before where the offsetOfCaller
        if serialReverseSearch:

            # if this is a Stream and we have a caller, see if we 
            # can get the offset from within this Stream       
            # first, see if this element is even in this Stream     
            getOffsetOfCaller = False
            if hasattr(self, "elements") and callerFirst is not None: 
                # find the offset of the callerFirst
                # if this is a Stream, we need to find the offset relative
                # to this Stream; it may only be available within a semiFlat
                # representaiton

                # this semiFlat name will be used in the getOffsetOfCaller 
                # branch below
                semiFlat = self.semiFlat
                # see if this element is in this Stream; 
                if semiFlat.hasElement(callerFirst): 
                    getOffsetOfCaller = True
                else:
                    if hasattr(callerFirst, 'flattenedRepresentationOf'):
                        if callerFirst.flattenedRepresentationOf is not None:
                            if semiFlat.hasElement(
                            callerFirst.flattenedRepresentationOf):
                                getOffsetOfCaller = True

            if getOffsetOfCaller:
                # in some cases we may need to try to get the offset of a semiFlat representation. this is necessary when a Measure
                # is the caller. 

                #environLocal.printDebug(['getContextByClass(): trying to get offset of caller from a semi-flat representation', 'self', self, self.id, 'callerFirst', callerFirst, callerFirst.id])
                offsetOfCaller = semiFlat.getOffsetByElement(callerFirst)

                # our caller might have been flattened after contexts were set
                # thus, this object may be in the caller's defined contexts, 
                # but this object knows nothing about a flat version of the 
                # caller (it cannot get an offset of the caller, which we need
                # to do the serial reverse search)
                if offsetOfCaller is None and hasattr(
                    callerFirst, 'flattenedRepresentationOf'):
                    #environLocal.printDebug(['getContextByClass(): trying to get offset of caller from the callers flattenedRepresentationOf attribute', 'self', self, 'callerFirst', callerFirst])

                    # Thanks Johannes Emerich [public@johannes.emerich.de] !
                    if callerFirst.flattenedRepresentationOf != None:
                        unFlat = callerFirst.flattenedRepresentationOf
                        offsetOfCaller = semiFlat.getOffsetByElement(unFlat)

                # if the offset has been found, get element at  or before
                # this offset
                if offsetOfCaller != None:
                    post = semiFlat.getElementAtOrBefore(offsetOfCaller, 
                               [className])

                #environLocal.printDebug([self, 'results of serialReverseSearch:', post, '; searching for:', className, '; starting from offset', offsetOfCaller])

        if post is None: # still no match
            # this will call this method on all defined contexts, including
            # locations (one of which must be the parent)
            # if this is a stream, this will be the next level up, recursing
            # a reference to the callerFirst is continuall passed
            post = self._definedContexts.getByClass(className,
                   serialReverseSearch=serialReverseSearch,
                   callerFirst=callerFirst, sortByCreationTime=sortByCreationTime, 
                   # make the priorityTarget the parent, meaning we search
                   # this object first
                   prioritizeActiveSite=prioritizeActiveSite, 
                   priorityTarget=priorityTarget, memo=memo)

        return post



    def getAllContextsByClass(self, className, found=None, idFound=None,
                             memo=None):
        '''Search both DefinedContexts as well as associated objects to find all matchinging classes. Returns [] if not match is found. 

        '''
        if memo is None:
            memo = {} # intialize
        if found == None:
            found = []
        if idFound == None:
            idFound = []

        post = None
        # if this obj is a Stream
        if hasattr(self, "elements"): 
            semiFlat = self.semiFlat
            # this memos updates to not exclude redundancies
            # TODO: check if getContextByClass can be improved
            # by adding these to memo
            memo[id(self)] = self
            memo[id(semiFlat)] = semiFlat

            for e in semiFlat.getElementsByClass([className]):
                # cannot be sure if this element is already found, as we may be 
                # looking at a flattened version of container
                #if e not in found:
                if id(e) not in idFound:
                    found.append(e)
                    idFound.append(id(e))

        # next, search all defined contexts
        self._definedContexts.getAllByClass(className, found=found,
                                         idFound=idFound, memo=memo)

        return found



    #---------------------------------------------------------------------------
    # properties

    def _getActiveSite(self):
        # can be None
        if WEAKREF_ACTIVE:
            if self._activeSite is None: #leave None
                return self._activeSite
            else: # even if current activeSite is not a weakref, this= will work
                return common.unwrapWeakref(self._activeSite)
        else:
            return self._activeSite
    
    def _setActiveSite(self, site):
        siteId = None
        if site != None: 
            siteId = id(site)
            # check that the activeSite is not already set to this object
            # this avoids making another weakref
            if self._activeSiteId == siteId:
                return

        if site is not None and not self._definedContexts.hasSiteId(siteId):
            self._definedContexts.add(site, self.offset, idKey=siteId) 
        
        if WEAKREF_ACTIVE:
            if site is None: # leave None alone
                self._activeSite = None
                self._activeSiteId = None
            else:
                self._activeSite = common.wrapWeakref(site)
                self._activeSiteId = siteId
        else:
            self._activeSite = site
            self._activeSiteId = siteId


    activeSite = property(_getActiveSite, _setActiveSite, 
        doc='''A reference to the most-recent object used to contain this object. In most cases, this will be a Stream or Stream sub-class. In most cases, an object's parent attribute is automatically set when an the object is attached to a Stream. 
        ''')

    def addLocationAndActiveSite(self, offset, activeSite, activeSiteWeakRef = None):
        '''
        This method is for advanced usage, generally as a speedup tool that adds a 
        new location element and a new activeSite.  Formerly called
        by Stream.insert -- this saves some dual processing.  
        Does not do safety checks that
        the siteId doesn't already exist etc., because that is done earlier.
        
        This speeds up things like stream.getElementsById substantially.

        Testing script (N.B. manipulates Stream._elements directly -- so not to be emulated)

        >>> from stream import Stream
        >>> st1 = Stream()
        >>> o1 = Music21Object()
        >>> st1_wr = common.wrapWeakref(st1)
        >>> offset = 20.0
        >>> st1._elements = [o1]
        >>> o1.addLocationAndActiveSite(offset, st1, st1_wr)
        >>> o1.activeSite is st1
        True
        >>> o1.getOffsetBySite(st1)
        20.0
        '''
        activeSiteId = id(activeSite)
        self._definedContexts.add(activeSite, offset, idKey=activeSiteId) 
        
        # if the current parent is already set, nothing to do
        # do not create a new weakref 
        if self._activeSiteId == activeSiteId:
            return 

        if WEAKREF_ACTIVE:
                if activeSiteWeakRef is None:
                    activeSiteWeakRef = common.wrapWeakref(activeSite)
                self._activeSite = activeSiteWeakRef
                self._activeSiteId = activeSiteId
        else:
            self._activeSite = activeSite
            self._activeSiteId = activeSiteId
        

    def _getOffset(self):
        '''Get the offset for the activeSite.

        '''
        #there is a problem if a new activeSite is being set and no offsets have 
        # been provided for that activeSite; when self.offset is called, 
        # the first case here would match

        parentId = None
        if self.activeSite is not None:
            parentId = id(self.activeSite)
        elif self._activeSiteId is not None:
            parentId = self._activeSiteId
        
        if parentId is not None and self._definedContexts.hasSiteId(parentId):
        # if parentId is not None and parentId in self._definedContexts.coordinates:
            return self._definedContexts.getOffsetBySiteId(parentId)
            #return self._definedContexts.coordinates[parentId]['offset']
        elif self.activeSite is None: # assume we want self
            return self._definedContexts.getOffsetBySite(None)
        else:
            # try to look for it in all objects
            environLocal.printDebug(['doing a manual parent search: problably means that id(self.activeSite) (%s) is not equal to self._activeSiteId (%s)' % (id(self.activeSite), self._activeSiteId)])
            offset = self._definedContexts.getOffsetByObjectMatch(self.activeSite)
            return offset

            environLocal.printDebug(['self._definedContexts', self._definedContexts._definedContexts])
            raise Exception('request within %s for offset cannot be made with parent of %s (id: %s)' % (self.__class__, self.activeSite, parentId))            

    def _setOffset(self, value):
        '''Set the offset for the activeSite. 
        '''
        # assume that most times this is a number; in that case, the fastest
        # thing to do is simply try to set the offset w/ float(value)

        #if common.isNum(value):
        try:
            offset = float(value)
        except TypeError:
            pass

        if hasattr(value, "quarterLength"):
            # probably a Duration object, but could be something else -- in any case, we'll take it.
            offset = value.quarterLength

# this no longer seems necessary; an exception will be raised elsewhere
#         else:
#             raise Exception('We cannot set  %s as an offset' % value)

        # using _activeSiteId offers a considerable speed boost, as we
        # do not have to unwrap a weakref of self.activeSite to get the id()
        # of parent
        self._definedContexts.setOffsetBySiteId(self._activeSiteId, offset) 

    
    offset = property(_getOffset, _setOffset, 
        doc = '''The offset property returns the position of this object from 
        the start of its most recently referenced container (a Stream or 
        Stream sub-class found in activeSite) in quarter lengths.

        It can also set the offset for the object if no container has been
        set

        >>> from music21 import *
        >>> n1 = note.Note()
        >>> n1.id = 'hi'
        >>> n1.offset = 20
        >>> n1.offset
        20.0
        >>> s1 = stream.Stream()
        >>> s1.append(n1)
        >>> n1.offset
        0.0
        >>> s2 = stream.Stream()
        >>> s2.insert(30.5, n1)
        >>> n1.offset
        30.5
        >>> n2 = s1.getElementById('hi')
        >>> n2 is n1
        True
        >>> n2.offset
        0.0
        >>> for thisElement in s2:
        ...     print thisElement.offset
        30.5
        
        ''')


    def _getDuration(self):
        '''
        Gets the DurationObject of the object or None

        '''
        return self._duration

    def _setDuration(self, durationObj):
        '''
        Set the offset as a quarterNote length
        '''
        if hasattr(durationObj, "quarterLength"):
            # we cannot directly test to see isInstance(duration.DurationCommon) because of
            # circular imports; so we instead just take any object with a quarterLength as a
            # duration
            self._duration = durationObj
        else:
            # need to permit Duration object assignment here
            raise Exception('this must be a Duration object, not %s' % durationObj)

    duration = property(_getDuration, _setDuration, 
        doc = '''Get and set the duration of this object as a Duration object.
        ''')

    def _getPriority(self):
        return self._priority

    def _setPriority(self, value):
        '''
        value is an int.
        '''
        if not isinstance(value, int):
            raise ElementException('priority values must be integers.')
        self._priority = value

    priority = property(_getPriority, _setPriority,
        doc = '''Get and set the priority integer value. 

        Priority specifies the order of processing from left (lowest number)
        to right (highest number) of objects at the same offset.  For 
        instance, if you want a key change and a clef change to happen at 
        the same time but the key change to appear first, then set: 
        keySigElement.priority = 1; clefElement.priority = 2 this might be 
        a slightly counterintuitive numbering of priority, but it does 
        mean, for instance, if you had two elements at the same offset, 
        an allegro tempo change and an andante tempo change, then the 
        tempo change with the higher priority number would apply to the 
        following notes (by being processed second).

        Default priority is 0; thus negative priorities are encouraged 
        to have Elements that appear non-priority set elements.

        In case of tie, there are defined class sort orders defined in 
        music21.base.CLASS_SORT_ORDER.  For instance, a key signature 
        change appears before a time signature change before a 
        note at the same offset.  This produces the familiar order of 
        materials at the start of a musical score.
        
        >>> from music21 import *
        >>> a = base.Music21Object()
        >>> a.priority = 3
        >>> a.priority = 'high'
        Traceback (most recent call last):
        ElementException: priority values must be integers.
        ''')

    

    #---------------------------------------------------------------------------
    # temporary storage setup routines; public interfdace

    def unwrapWeakref(self):
        '''Public interface to operation on DefinedContexts.

        >>> aM21Obj = Music21Object()
        >>> bM21Obj = Music21Object()
        >>> aM21Obj.offset = 30
        >>> aM21Obj.getOffsetBySite(None)
        30.0
        >>> aM21Obj.addLocationAndActiveSite(50, bM21Obj)
        >>> aM21Obj.unwrapWeakref()

        '''
        self._definedContexts.unwrapWeakref()
        # doing direct access; not using property parent, as filters
        # through global WEAKREF_ACTIVE setting
        self._activeSite = common.unwrapWeakref(self._activeSite)

    def wrapWeakref(self):
        '''Public interface to operation on DefinedContexts.

        >>> aM21Obj = Music21Object()
        >>> bM21Obj = Music21Object()
        >>> aM21Obj.offset = 30
        >>> aM21Obj.getOffsetBySite(None)
        30.0
        >>> aM21Obj.addLocationAndActiveSite(50, bM21Obj)
        >>> aM21Obj.unwrapWeakref()
        >>> aM21Obj.wrapWeakref()
        '''
        self._definedContexts.wrapWeakref()

        # doing direct access; not using property parent, as filters
        # through global WEAKREF_ACTIVE setting
        self._activeSite = common.wrapWeakref(self._activeSite)
        # this is done both here and in unfreezeIds()
        # not sure if both are necesary
        if self._activeSite is not None:
            obj = common.unwrapWeakref(self._activeSite)
            self._activeSiteId = id(obj)


    def freezeIds(self):
        '''Temporarily replace are stored keys with a different value.

        >>> aM21Obj = Music21Object()
        >>> bM21Obj = Music21Object()
        >>> aM21Obj.offset = 30
        >>> aM21Obj.getOffsetBySite(None)
        30.0
        >>> bM21Obj.addLocationAndActiveSite(50, aM21Obj)   
        >>> bM21Obj.activeSite != None
        True
        >>> oldParentId = bM21Obj._activeSiteId
        >>> bM21Obj.freezeIds()
        >>> newParentId = bM21Obj._activeSiteId
        >>> oldParentId == newParentId
        False
        '''
        self._definedContexts.freezeIds()

        # _activeSite could be a weak ref; may need to manage
        if self._activeSite is not None:
            #environLocal.printDebug(['freezeIds: adjusting _activeSiteId', self._activeSite])
            self._activeSiteId = uuid.uuid4() # a place holder


    def unfreezeIds(self):
        '''Restore keys to be the id() of the object they contain

        >>> aM21Obj = Music21Object()
        >>> bM21Obj = Music21Object()
        >>> aM21Obj.offset = 30
        >>> aM21Obj.getOffsetBySite(None)
        30.0
        >>> bM21Obj.addLocationAndActiveSite(50, aM21Obj)   
        >>> bM21Obj.activeSite != None
        True
        >>> oldParentId = bM21Obj._activeSiteId
        >>> bM21Obj.freezeIds()
        >>> newParentId = bM21Obj._activeSiteId
        >>> oldParentId == newParentId
        False
        >>> bM21Obj.unfreezeIds()
        >>> postParentId = bM21Obj._activeSiteId
        >>> oldParentId == postParentId
        True
        '''
        #environLocal.printDebug(['unfreezing ids', self])
        self._definedContexts.unfreezeIds()

        if self._activeSite is not None:
            obj = common.unwrapWeakref(self._activeSite)
            self._activeSiteId = id(obj)






    #---------------------------------------------------------------------------
    # display and writing

    def write(self, fmt=None, fp=None):
        '''Write a file.
        
        A None file path will result in temporary file
        '''
        if fmt == None: # get setting in environment
            fmt = environLocal['writeFormat']
 
        format, ext = common.findFormat(fmt)
        if format not in common.VALID_WRITE_FORMATS:
            raise Music21ObjectException('cannot support showing in this format yet: %s' % format)

        if format is None:
            raise Music21ObjectException('bad format (%s) provided to write()' % fmt)

        if fp is None:
            fp = environLocal.getTempFile(ext)

        if format in ['text', 'textline', 'musicxml', 'lilypond']:        
            if format == 'text':
                dataStr = self._reprText()
            elif format == 'textline':
                dataStr = self._reprTextLine()
            elif format == 'musicxml':
                dataStr = self.musicxml
            elif format == 'lilypond':
                dataStr = self.lily.renderTemplate()

            f = open(fp, 'w')
            f.write(dataStr)
            f.close()
            return fp

        elif format == 'midi':
            # returns a midi file object
            mf = self.midiFile
            mf.open(fp, 'wb') # write binary
            mf.write()
            mf.close()
            return fp

#         elif fmt == 'lily.pdf':
#             return self.lily.showPDF()
#         elif fmt == 'lily.png':
#             return self.lily.showPNG()
#         elif fmt == 'lily':
#             return self.lily.showPNG()

        else:
            raise Music21ObjectException('cannot support writing in this format, %s yet' % format)



    def _reprText(self):
        '''Retrun a text representation possible with line breaks. This methods can be overridden by subclasses to provide alternative text representations.
        '''
        return self.__repr__()

    def _reprTextLine(self):
        '''Retrun a text representation without line breaks. This methods can be overridden by subclasses to provide alternative text representations.
        '''
        return self.__repr__()

    def show(self, fmt=None, app=None):
        '''
        Displays an object in a format provided by the fmt argument or, if not provided, the format set in the user's Environment 

        Valid formats include (but are not limited to):
          xml (musicxml)
          text
          lily.png
          lily.pdf

        OMIT_FROM_DOCS        
        This might need to return the file path.
        '''

        if fmt == None: # get setting in environment
            fmt = environLocal['showFormat']

        format, ext = common.findFormat(fmt)
        if format not in common.VALID_SHOW_FORMATS:
            raise Music21ObjectException('cannot support showing in this format yet: %s' % format)

        # standard text presentation has line breaks, is printed
        if format == 'text':
            print(self._reprText())
        # a text line compacts the complete recursive representation into a 
        # single line of text; most for debugging. returned, not printed
        elif format == 'textline': 
            return self._reprTextLine()

        # TODO: these need to be updated to write files

        elif fmt == 'lily.pdf':
            #return self.lily.showPDF()
            environLocal.launch('pdf', self.lily.createPDF(), app=app)
        elif fmt == 'lily.png':
            # TODO check that these use environLocal 
            return self.lily.showPNG()
        elif fmt == 'lily':
            return self.lily.showPNG()

        elif fmt in ['musicxml', 'midi']: # a format that writes a file
            returnedFilePath = self.write(format)
            environLocal.launch(format, returnedFilePath, app=app)

        else:
            raise Music21ObjectException('no such show format is supported:', fmt)



    #---------------------------------------------------------------------------
    # duration manipulation, processing, and splitting


    def splitAtQuarterLength(self, quarterLength, retainOrigin=True, 
        addTies=True, displayTiedAccidentals=False):
        '''
        Split an Element into two Elements at a provided QuarterLength into the Element.

        >>> from music21 import *
        >>> a = note.Note('C#5')
        >>> a.duration.type = 'whole'
        >>> a.articulations = [articulations.Staccato()]
        >>> a.lyric = 'hi'
        >>> a.expressions = [expressions.Mordent(), expressions.Trill(), expressions.Fermata()]
        >>> b, c = a.splitAtQuarterLength(3)
        >>> b.duration.type
        'half'
        >>> b.duration.dots
        1
        >>> b.duration.quarterLength
        3.0
        >>> b.articulations
        [<music21.articulations.Staccato>]
        >>> b.lyric
        'hi'
        >>> b.expressions
        [<music21.expressions.Mordent>, <music21.expressions.Trill>]
        >>> c.duration.type
        'quarter'
        >>> c.duration.dots
        0
        >>> c.duration.quarterLength
        1.0
        >>> c.articulations
        []
        >>> c.lyric
        >>> c.expressions
        [<music21.expressions.Trill>, <music21.expressions.Fermata>]

        '''
        # was note.splitNoteAtPoint

        if self.duration == None:
            raise Exception('cannot split an element that has a Duration of None')

        if quarterLength > self.duration.quarterLength:
            raise duration.DurationException(
            "cannot split a duration (%s) at this quarterLength (%s)" % (
            self.duration.quarterLength, quarterLength))

        if retainOrigin == True:
            e = self
        else:
            e = copy.deepcopy(self)
        eRemain = copy.deepcopy(self)
        
        # clear articulations from remaining parts
        if hasattr(eRemain, 'articulations'):
            eRemain.articulations = []
        if hasattr(eRemain, 'lyrics'):
            eRemain.lyrics = []

        if hasattr(e, 'expressions'):
            tempExpressions = e.expressions
            e.expressions = []
            eRemain.expressions = []
            for thisExpression in tempExpressions:
                if hasattr(thisExpression, 'tieAttach'):
                    if thisExpression.tieAttach == 'first':
                        e.expressions.append(thisExpression)
                    elif thisExpression.tieAttach == 'last':
                        eRemain.expressions.append(thisExpression)
                    else:  # default = 'all'
                        e.expressions.append(thisExpression)
                        eRemain.expressions.append(thisExpression)
                else: # default = 'all'
                    e.expressions.append(thisExpression)
                    eRemain.expressions.append(thisExpression)


        lenEnd = self.duration.quarterLength - quarterLength
        lenStart = self.duration.quarterLength - lenEnd

        d1 = duration.Duration()
        d1.quarterLength = lenStart

        d2 = duration.Duration()
        d2.quarterLength = lenEnd

        e.duration = d1
        eRemain.duration = d2

        # some higher-level classes need this functionality
        # set ties
        if addTies and ('Note' in e.classes or 
            'Chord' in e.classes or 
            'Unpitched' in e.classes):

            forceEndTieType = 'stop'
            if e.tie != None:
                # the last tie of what was formally a start should
                # continue
                if e.tie.type == 'start':
                    # keep start  if already set
                    forceEndTieType = 'continue'
                # a stop was ending a previous tie; we know that
                # the first is now a continue
                elif e.tie.type == 'stop':
                    forceEndTieType = 'stop'
                    e.tie.type = 'continue' 
                elif e.tie.type == 'continue':
                    forceEndTieType = 'continue'
                    # keep continue if already set
            else:
                e.tie = tie.Tie('start') # need a tie objects

            eRemain.tie = tie.Tie(forceEndTieType)
    
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

        return [e, eRemain]

    def splitByQuarterLengths(self, quarterLengthList, addTies=True, 
        displayTiedAccidentals=False):
        '''Given a list of quarter lengths, return a list of 
        Music21Object objects, copied from this Music21Object, 
        that are partitioned and tied with the specified quarter 
        length list durations.

        >>> from music21 import *
        >>> n = note.Note()
        >>> n.quarterLength = 3
        >>> post = n.splitByQuarterLengths([1,1,1])
        >>> [n.quarterLength for n in post]
        [1, 1, 1]
        '''
        if self.duration == None:
            raise Music21ObjectException('cannot split an element that has a Duration of None')

        if not common.almostEqual(sum(quarterLengthList),
            self.duration.quarterLength, grain=1e-4):
            raise Music21ObjectException('cannot split by quarter length list that is not equal to the duration of the source: %s, %s' % (quarterLengthList, self.duration.quarterLength))
        # if nothing to do
        elif (len(quarterLengthList) == 1 and quarterLengthList[0] ==     
            self.duration.quarterLength):
            # return a copy of self in a list
            return [copy.deepcopy(self)]
        elif len(quarterLengthList) <= 1:
            raise Music21ObjectException('cannot split by this quarter length list: %s.' % quarterLengthList)

        post = []
        forceEndTieType = 'stop'
        for i in range(len(quarterLengthList)):
            ql = quarterLengthList[i]
            e = copy.deepcopy(self)
            e.quarterLength = ql

            if i != 0:
                # clear articulations from remaining parts
                if hasattr(e, 'articulations'):
                    e.articulations = []


            if addTies:
                # if not last
                if i == 0:
                    # if the first elements has a Tie, then the status
                    # of that Tie needs to be continued here and, at the 
                    # end of all durations in this block.
                    if e.tie != None:
                        # the last tie of what was formally a start should
                        # continue
                        if e.tie.type == 'start':
                            # keep start  if already set
                            forceEndTieType = 'continue'
                        # a stop was ending a previous tie; we know that
                        # the first is now a continue
                        elif e.tie.type == 'stop':
                            forceEndTieType = 'stop'
                            e.tie.type = 'continue' 
                        elif e.tie.type == 'continue':
                            forceEndTieType = 'continue'
                            # keep continue if already set
                    else:
                        e.tie = tie.Tie('start') # need a tie objects
                elif i < (len(quarterLengthList) - 1):
                    e.tie = tie.Tie('continue') # need a tie objects
                else: # if last
                    # last note just gets the tie of the original Note
                    e.tie = tie.Tie(forceEndTieType)

            # hide accidentals on tied notes where previous note
            # had an accidental that was shown
            if i != 0:
                # look at self for characteristics of origin
                if hasattr(self, 'accidental') and self.accidental != None:
                    if not displayTiedAccidentals: # if False
                        # do not show accidentals unless display type in 'even-tied'
                        if (self.accidental.displayType not in     
                            ['even-tied']):
                            e.accidental.displayStatus = False
                    else: # display tied accidentals
                        e.accidental.displayType = 'even-tied'
                        e.accidental.displayStatus = True

            post.append(e)

        return post


    def splitAtDurations(self):
        '''
        Takes a Note and returns a list of Notes with only a single
        duration.DurationUnit in each. Ties are added. 

        >>> from music21 import *
        >>> a = note.Note()
        >>> a.duration.clear() # remove defaults
        >>> a.duration.addDurationUnit(duration.Duration('half'))
        >>> a.duration.quarterLength
        2.0
        >>> a.duration.addDurationUnit(duration.Duration('whole'))
        >>> a.duration.quarterLength
        6.0
        >>> b = a.splitAtDurations()
        >>> b[0].pitch == b[1].pitch
        True
        >>> b[0].duration.type
        'half'
        >>> b[1].duration.type
        'whole'
        '''
        # Note: this method is not used used in any critical code and could possible be removed.

        if self.duration == None:
            raise Exception('cannot split an element that has a Duration of None')

        returnNotes = []

        if len(self.duration.components) == (len(self.duration.linkages) - 1):
            for i in range(len(self.duration.components)):
                tempNote = copy.deepcopy(self)
                if i != 0:
                    # clear articulations from remaining parts
                    if hasattr(tempNote, 'articulations'):
                        tempNote.articulations = []

                
                # note that this keeps durations 
                tempNote.duration = self.duration.components[i]
                if i != (len(self.duration.components) - 1):
                    tempNote.tie = self.duration.linkages[i]                
                    # last note just gets the tie of the original Note
                returnNotes.append(tempNote)
        else: 
            for i in range(len(self.duration.components)):
                tempNote = copy.deepcopy(self)
                tempNote.duration = self.duration.components[i]
                if i != (len(self.duration.components) - 1):
                    tempNote.tie = tie.Tie()
                else:
                    # last note just gets the tie of the original Note
                    if self.tie is None:
                        self.tie = tie.Tie("stop")
                returnNotes.append(tempNote)                
        return returnNotes




    #---------------------------------------------------------------------------
    # temporal and beat based positioning


    def _getMeasureNumberLocal(self):
        '''If this object is contained in a Measure, return the measure number
        '''
        mNumber = None # default for not defined
        if self.activeSite != None and self.activeSite.isMeasure:
            mNumber = self.activeSite.number
        else:
            # testing sortByCreationTime == true; this may be necessary
            # as we often want the most recent measure
            m = self.getContextByClass('Measure', sortByCreationTime=True)
            if m != None:
                mNumber = m.number
        return mNumber

    measureNumberLocal = property(_getMeasureNumberLocal, 
        doc = '''Return the measure number of a Measure that contains this object. 
        ''')  


    def _getMeasureOffset(self):
        '''Try to obtain the nearest Measure that contains this object, and return the offset within that Measure.

        If a Measure is found, and that Measure has padding defined as `paddingLeft`, padding will be added to the native offset gathered from the object. 

        >>> from music21 import *
        >>> n = note.Note()
        >>> n.quarterLength = 2
        >>> m = stream.Measure()
        >>> n._getMeasureOffset() # returns zero when not assigned
        0.0 
        >>> n.quarterLength = .5
        >>> m = stream.Measure()
        >>> m.repeatAppend(n, 4)
        >>> [n._getMeasureOffset() for n in m.notes]
        [0.0, 0.5, 1.0, 1.5]
        '''

        if self.activeSite != None and self.activeSite.isMeasure:
            environLocal.printDebug(['found parent as Measure, using for offset'])
            offsetLocal = self.getOffsetBySite(self.activeSite)
        else:
            #environLocal.printDebug(['did not find parent as Measure, doing context search', 'self.activeSite', self.activeSite])
            # testing sortByCreationTime == true; this may be necessary
            # as we often want the most recent measure
            m = self.getContextByClass('Measure', sortByCreationTime=True, prioritizeActiveSite=False)
            if m != None:
                #environLocal.printDebug(['using found Measure for offset access'])            
                offsetLocal = self.getOffsetBySite(m) + m.paddingLeft

            else: # hope that we get the right one
                environLocal.printDebug(['_getMeasureOffset(): cannot find a Measure; using standard offset access'])
                offsetLocal = self.offset

        #environLocal.printDebug(['_getMeasureOffset(): found local offset as:', offsetLocal, self])
        return offsetLocal

    def _getBeat(self):
        '''Return a beat designation based on local Measure and TimeSignature

        >>> from music21 import *
        >>> n = note.Note()
        >>> n.quarterLength = 2
        >>> m = stream.Measure()
        >>> m.isMeasure
        True
        >>> m.timeSignature = meter.TimeSignature('4/4')
        >>> m.repeatAppend(n, 2)
        >>> m[1].activeSite # here we get the parent, but not in m.notes
        <music21.stream.Measure 0 offset=0.0>

        >>> m.notes[0]._getBeat()
        1.0
        >>> m.notes[1]._getBeat()
        3.0
        '''
        ts = self.getContextByClass('TimeSignature')
        if ts == None:
            raise Music21ObjectException('this Note does not have a TimeSignature in DefinedContexts')                    
        return ts.getBeatProportion(self._getMeasureOffset())


    beat = property(_getBeat,  
        doc = '''Return the beat of this Note as found in the most recently positioned Measure. Beat values count from 1 and contain a floating-point designation between 0 and 1 to show proportional progress through the beat.

        >>> from music21 import *
        >>> n = note.Note()
        >>> n.quarterLength = .5
        >>> m = stream.Measure()
        >>> m.timeSignature = meter.TimeSignature('3/4')
        >>> m.repeatAppend(n, 6)
        >>> [m.notes[i].beat for i in range(6)]
        [1.0, 1.5, 2.0, 2.5, 3.0, 3.5]

        >>> m.timeSignature = meter.TimeSignature('6/8')
        >>> [m.notes[i].beat for i in range(6)]
        [1.0, 1.3333333..., 1.666666666..., 2.0, 2.33333333..., 2.66666...]

        ''')


    def _getBeatStr(self):
        ts = self.getContextByClass('TimeSignature')
        #environLocal.printDebug(['_getBeatStr(): found ts:', ts])
        if ts == None:
            raise Music21ObjectException('this Note does not have a TimeSignature in DefinedContexts')                    
        return ts.getBeatProportionStr(self._getMeasureOffset())


    beatStr = property(_getBeatStr,  
        doc = '''Return a string representation of the beat of this Note as found in the most recently positioned Measure. Beat values count from 1 and contain a fractional designation to show progress through the beat.

        >>> from music21 import *
        >>> n = note.Note()
        >>> n.quarterLength = .5
        >>> m = stream.Measure()
        >>> m.timeSignature = meter.TimeSignature('3/4')
        >>> m.repeatAppend(n, 6)
        >>> [m.notes[i].beatStr for i in range(6)]
        ['1', '1 1/2', '2', '2 1/2', '3', '3 1/2']
        >>> m.timeSignature = meter.TimeSignature('6/8')
        >>> [m.notes[i].beatStr for i in range(6)]
        ['1', '1 1/3', '1 2/3', '2', '2 1/3', '2 2/3']
        ''')


    def _getBeatDuration(self):
        '''Return a :class:`~music21.duration.Duration` of the beat active for this Note as found in the most recently positioned Measure.

        >>> from music21 import *
        >>> n = note.Note()
        >>> n.quarterLength = 2
        >>> m = stream.Measure()
        >>> m.timeSignature = meter.TimeSignature('4/4')
        >>> m.repeatAppend(n, 2)
        >>> m.notes[0]._getBeatDuration()
        <music21.duration.Duration 1.0>
        >>> m.notes[1]._getBeatDuration()
        <music21.duration.Duration 1.0>
        '''
        ts = self.getContextByClass('TimeSignature')
        if ts == None:
            raise Music21ObjectException('this Note does not have a TimeSignature in DefinedContexts')
        return ts.getBeatDuration(self._getMeasureOffset())

    beatDuration = property(_getBeatDuration,  
        doc = '''Return a :class:`~music21.duration.Duration` of the beat active for this Note as found in the most recently positioned Measure.

        >>> from music21 import *
        >>> n = note.Note()
        >>> n.quarterLength = .5
        >>> m = stream.Measure()
        >>> m.timeSignature = meter.TimeSignature('3/4')
        >>> m.repeatAppend(n, 6)
        >>> [m.notes[i].beatDuration.quarterLength for i in range(6)]
        [1.0, 1.0, 1.0, 1.0, 1.0, 1.0]

        >>> m.timeSignature = meter.TimeSignature('6/8')
        >>> [m.notes[i].beatDuration.quarterLength for i in range(6)]
        [1.5, 1.5, 1.5, 1.5, 1.5, 1.5]
        ''')


    def _getBeatStrength(self):
        '''Return an accent weight based on local Measure and TimeSignature. If the offset of this Note does not match a defined accent weight, a minimum accent weight will be returned.

        >>> from music21 import *
        >>> n = note.Note()
        >>> n.quarterLength = .25
        >>> m = stream.Measure()
        >>> m.isMeasure
        True
        >>> m.timeSignature = meter.TimeSignature('4/4')
        >>> m.repeatAppend(n, 16)

        >>> m.notes[0]._getBeatStrength()
        1.0
        >>> m.notes[4]._getBeatStrength()
        0.25
        >>> m.notes[8]._getBeatStrength()
        0.5
        '''
        ts = self.getContextByClass('TimeSignature')
        if ts == None:
            raise Music21ObjectException('this Note does not have a TimeSignature in DefinedContexts')                    
        return ts.getAccentWeight(self._getMeasureOffset(),
               forcePositionMatch=True)


    beatStrength = property(_getBeatStrength,  
        doc = '''Return the metrical accent of this Note in the most recently positioned Measure. Accent values are between zero and one, and are derived from the local TimeSignature's accent MeterSequence weights. If the offset of this Note does not match a defined accent weight, a minimum accent weight will be returned.

        >>> from music21 import *
        >>> n = note.Note()
        >>> n.quarterLength = .5
        >>> m = stream.Measure()
        >>> m.timeSignature = meter.TimeSignature('3/4')
        >>> m.repeatAppend(n, 6)
        >>> [m.notes[i].beatStrength for i in range(6)]
        [1.0, 0.25, 0.5, 0.25, 0.5, 0.25]

        >>> m.timeSignature = meter.TimeSignature('6/8')
        >>> [m.notes[i].beatStrength for i in range(6)]
        [1.0, 0.25, 0.25, 0.5, 0.25, 0.25]

        ''')


#-------------------------------------------------------------------------------
class ElementWrapper(Music21Object):
    '''
    An element wraps any object that is not a :class:`~music21.base.Music21Object`, so that that object can
    be positioned within a :class:`~music21.stream.Stream`.
    
    The object stored within ElementWrapper is available from the the :attr:`~music21.base.ElementWrapper.obj` attribute.
    
    Providing an object at initialization is mandatory. 

    OMIT_FROM_DOCS
    because in the new (29/11/2009) object model, ElementWrapper should only be used
    to wrap a non music21-object it should be removed from most docs.
    '''
    obj = None
    _id = None

    _DOC_ORDER = ['obj']
    _DOC_ATTR = {
    'obj': 'The object this wrapper wraps.',
    }

    def __init__(self, obj):
        Music21Object.__init__(self)
        self.obj = obj # object stored here        
        self._unlinkedDuration = None


    def __copy__(self):
        '''
        Makes a copy of this element with a reference
        to the SAME object but with unlinked offset, priority
        and a cloned Groups object

        >>> import note
        >>> import duration
        >>> n = note.Note('A')
        
        >>> a = ElementWrapper(obj = n)
        >>> a.offset = duration.Duration("quarter")
        >>> a.groups.append("flute")

        >>> b = copy.copy(a)
        >>> b.offset = duration.Duration("half")
        
        '''
#         >>> a.obj.accidental = "-"
#         >>> b.name
#         'A-'
#         >>> a.obj is b.obj
#         True

#         >>> a.offset.quarterLength
#         1.0
#         >>> a.groups[0] = "bassoon"
#         >>> ("flute" in a.groups, "flute" in b.groups)
#         (False, True)

        new = self.__class__(self.obj)
        #for name in dir(self):
        for name in self.__dict__.keys():
            if name.startswith('__'):
                continue
            part = getattr(self, name)
            newValue = part # just provide a reference
            setattr(new, name, newValue)

        # it is assumed that we need new objects for groups, contexts
        # and locations in order to position / group this object
        # independently
        new.groups = copy.deepcopy(self.groups)
        new._definedContexts = copy.deepcopy(self._definedContexts)
        return new

    def __deepcopy__(self, memo=None):
        '''
        similar to copy but also does a deepcopy of
        the object as well.
        
        (name is all lowercase to go with copy.deepcopy convention)

        >>> import copy    
        >>> from music21 import note, duration
        >>> n = note.Note('A')
        
        >>> a = ElementWrapper(obj = n)
        >>> a.offset = 1.0 # duration.Duration("quarter")
        >>> a.groups.append("flute")

        >>> b = copy.deepcopy(a)
        >>> b.offset = 2.0 # duration.Duration("half")
        
        >>> a.obj is b.obj
        False
        >>> a.obj.accidental = "-"
        >>> b.obj.name
        'A'
        >>> a.offset
        1.0
        >>> b.offset
        2.0
        >>> a.groups[0] = "bassoon"
        >>> ("flute" in a.groups, "flute" in b.groups)
        (False, True)
        '''
        new = self.__copy__()

        # this object needs a new locations object
        new._definedContexts = copy.deepcopy(self._definedContexts)
        new.obj = copy.deepcopy(self.obj)

        new._idLastDeepCopyOf = id(self)
        return new




    #---------------------------------------------------------------------------
    # properties

    def getId(self):
        if self.obj is not None:
            if hasattr(self.obj, "id"):
                return self.obj.id
            else:
                return self._id
        else:
            return self._id

    def setId(self, newId):
        if self.obj is not None:
            if hasattr(self.obj, "id"):
                self.obj.id = newId
            else:
                self._id = newId
        else:
            self._id = newId

    id = property (getId, setId)


    def _getDuration(self):
        '''
        Gets the duration of the ElementWrapper (if separately set), but
        normal returns the duration of the component object if available, otherwise
        returns None.

        >>> import note
        >>> n = note.Note('F#')
        >>> n.quarterLength = 2.0
        >>> n.duration.quarterLength 
        2.0
        >>> el1 = ElementWrapper(n)
        >>> el1.duration.quarterLength
        2.0

        ADVANCED FEATURE TO SET DURATION OF ELEMENTS AND STREAMS SEPARATELY
        >>> class KindaStupid(object):
        ...     pass
        >>> ks1 = ElementWrapper(KindaStupid())
        >>> ks1.obj.duration
        Traceback (most recent call last):
        AttributeError: 'KindaStupid' object has no attribute 'duration'
        
        >>> import duration
        >>> ks1.duration = duration.Duration("whole")
        >>> ks1.duration.quarterLength
        4.0
        >>> ks1.obj.duration  # still not defined
        Traceback (most recent call last):
        AttributeError: 'KindaStupid' object has no attribute 'duration'
        '''
        if self._unlinkedDuration is not None:
            return self._unlinkedDuration
        elif hasattr(self, "obj") and hasattr(self.obj, 'duration'):
            return self.obj.duration
        else:
            return None

    def _setDuration(self, durationObj):
        '''
        Set the offset as a quarterNote length
        '''
        if not hasattr(durationObj, "quarterLength"):
            raise Exception('this must be a Duration object, not %s' % durationObj)
        
        if hasattr(self.obj, 'duration'):
            # if a number assume it is a quarter length
            self.obj.duration = durationObj
        else:
            self._unlinkedDuration = durationObj
            
    duration = property(_getDuration, _setDuration)

    offset = property(Music21Object._getOffset, Music21Object._setOffset)

    #---------------------------------------------------------------------------
    def __repr__(self):
        shortObj = (str(self.obj))[0:30]
        if len(str(self.obj)) > 30:
            shortObj += "..."
            
        if self.id is not None:
            return '<%s id=%s offset=%s obj="%s">' % \
                (self.__class__.__name__, self.id, self.offset, shortObj)
        else:
            return '<%s offset=%s obj="%s">' % \
                (self.__class__.__name__, self.offset, shortObj)


    def __eq__(self, other):
        '''Test ElementWrapper equality

        >>> import note
        >>> n = note.Note("C#")
        >>> a = ElementWrapper(n)
        >>> a.offset = 3.0
        >>> b = ElementWrapper(n)
        >>> b.offset = 3.0
        >>> a == b
        True
        >>> a is not b
        True
        >>> c = ElementWrapper(n)
        >>> c.offset = 2.0
        >>> c.offset
        2.0
        >>> a == c
        False
        '''
        if not hasattr(other, "obj") or \
           not hasattr(other, "offset") or \
           not hasattr(other, "priority") or \
           not hasattr(other, "id") or \
           not hasattr(other, "groups") or \
           not hasattr(other, "activeSite") or \
           not hasattr(other, "duration"):
            return False


        if (self.obj == other.obj and \
            self.offset == other.offset and \
            self.priority == other.priority and \
            self.id == other.id and \
            self.groups == other.groups and \
            self.activeSite == other.activeSite and \
            self.duration == self.duration):
            return True
        else:
            return False

    def __ne__(self, other):
        '''
        '''
        return not self.__eq__(other)


    def __setattr__(self, name, value):
        #environLocal.printDebug(['calling __setattr__ of ElementWrapper', name, value])

        # if in the ElementWrapper already, set that first
        if name in self.__dict__:  
            object.__setattr__(self, name, value)
        
        # if not, change the attribute in the stored object
        storedobj = object.__getattribute__(self, "obj")
        if name not in ['offset', '_offset', '_activeSite'] and \
            storedobj is not None and hasattr(storedobj, name):
            setattr(storedobj, name, value)
        # unless neither has the attribute, in which case add it to the ElementWrapper
        else:  
            object.__setattr__(self, name, value)

    def __getattr__(self, name):
        '''This method is only called when __getattribute__() fails.
        Using this also avoids the potential recursion problems of subclassing
        __getattribute__()_
        
        see: http://stackoverflow.com/questions/371753/python-using-getattribute-method for examples
         
        '''
        storedobj = Music21Object.__getattribute__(self, "obj")
        if storedobj is None:
            raise AttributeError("Could not get attribute '" + name + "' in an object-less element")
        else:
            return object.__getattribute__(storedobj, name)



    def isTwin(self, other):
        '''A weaker form of equality.  a.isTwin(b) is true if
        a and b store either the same object OR objects that are equal
        and a.groups == b.groups 
        and a.id == b.id (or both are none) and duration are equal.
        but does not require position, priority, or activeSite to be the same
        In other words, is essentially the same object in a different context
             
        >>> import note
        >>> aE = ElementWrapper(obj = note.Note("A-"))
        >>> aE.id = "aflat-Note"
        >>> aE.groups.append("out-of-range")
        >>> aE.offset = 4.0
        >>> aE.priority = 4
        
        >>> bE = copy.copy(aE)
        >>> aE is bE
        False
        >>> aE == bE
        True
        >>> aE.isTwin(bE)
        True

        >>> bE.offset = 14.0
        >>> bE.priority = -4
        >>> aE == bE
        False
        >>> aE.isTwin(bE)
        True
        '''
        if not hasattr(other, "obj") or \
           not hasattr(other, "id") or \
           not hasattr(other, "duration") or \
           not hasattr(other, "groups"):
            return False

        if (self.obj == other.obj and \
            self.id == other.id and \
            self.duration == self.duration and \
            self.groups == other.groups):
            return True
        else:
            return False





#-------------------------------------------------------------------------------
# class WeakElementWrapper(Music21Object):
#     '''An element wraps a :class:`~music21.base.Music21Object` and stores it as a weak reference.
#     
#     The object stored within ElementWrapper is available from the the :attr:`~music21.base.ElementWrapper.obj` property.
#     
#     Providing an object at initialization is mandatory. 
#     '''
# 
#     _DOC_ORDER = ['obj']
#     _DOC_ATTR = {
#     'obj': 'The object this wrapper wraps.',
#     }
# 
#     def __init__(self, obj):
#         self._obj = None # actual storage
#         # store object id() for comparison without unwrapping
#         self._objId = None
#         # must define above first, before calling this
#         Music21Object.__init__(self)
#         self._setObj(obj) # object set with property
#         self._unlinkedDuration = None
# 
#     def _setObj(self, obj):
#         self._objId = id(obj)
#         self._obj = common.wrapWeakref(obj)
#         environLocal.printDebug(['setting object', obj])
# 
#     def _getObj(self):
#         return common.unwrapWeakref(self._obj)
# 
#     obj = property(_getObj, _setObj)
# 
#     # for serialization, need to wrap and unwrap weakrefs
#     def freezeIds(self):
#         pass
# 
#     def unfreezeIds(self):
#         pass
# 
#     def __copy__(self):
#         '''
#         Makes a copy of this element with a reference
#         to the SAME object but with unlinked offset, priority
#         and a cloned Groups object
#         '''
#         # will be None if obj has gone out of scope
#         if self.obj is None:
#             return None
#         # this calls a new class with a dereferenced copy
#         new = self.__class__(self.obj)
#         for name in self.__dict__.keys():
#             if name.startswith('__'):
#                 continue
#             part = getattr(self, name)
#             newValue = part # just provide a reference
#             setattr(new, name, newValue)
# 
#         # it is assumed that we need new objects for groups, contexts
#         # and locations in order to position / group this object
#         # independently
#         new.groups = copy.deepcopy(self.groups)
#         new._definedContexts = copy.deepcopy(self._definedContexts)
#         return new
# 
#     def __deepcopy__(self, memo=None):
#         '''
#         '''
#         new = self.__copy__()
#         new._idLastDeepCopyOf = id(self)
#         return new
# 
# 
#     def _getClasses(self):
#         # if stored object is not None, return its classes
#         objRef = self.obj
#         if objRef is not None:
#             return [x.__name__ for x in objRef.__class__.mro()] 
#         else:
#             return [x.__name__ for x in self.__class__.mro()] 
# 
#     classes = property(_getClasses, 
#         doc='''Returns a list containing the names (strings, not objects) of classes that are found in the object contained in this wrapper
#     
#         >>> from music21 import *
#         >>> n1 = note.QuarterNote()
#         >>> wew = WeakElementWrapper(n1)
#         >>> wew.classes[:5]
#         ['QuarterNote', 'Note', 'NotRest', 'GeneralNote', 'Music21Object']
#         >>> del n1
#         >>> wew.classes
#         ['WeakElementWrapper', 'Music21Object', 'JSONSerializer', 'object']
#         ''')
# 
# 
# 
#     #---------------------------------------------------------------------------
#     # properties
# 
#     def getId(self):
#         objRef = self.obj
#         if objRef is not None:
#             if hasattr(objRef, "id"):
#                 return objRef.id
#         return None
# 
#     def setId(self, newId):
#         objRef = self.obj
#         if objRef is not None:
#             if hasattr(objRef, "id"):
#                 objRef.id = newId
# 
#     id = property(getId, setId)
# 
# 
#     def _getDuration(self):
#         '''
#         Gets the duration of the WeakElementWrapper (if separately set), but
#         normal returns the duration of the component object if available, otherwise returns None.
#         '''
#         objRef = self.obj
#         if self._unlinkedDuration is not None:
#             #environLocal.printDebug(['returning unlinkedDuration'])
#             return self._unlinkedDuration
#         elif objRef is not None and hasattr(objRef, 'duration'):
#             #environLocal.printDebug(['returning objRef.duration'])
#             return objRef.duration
#         else:
#             #environLocal.printDebug(['get get duration; returning None'])
#             return None
# 
#     def _setDuration(self, durationObj):
#         '''
#         Set the offset as a quarterNote length
#         '''
#         #environLocal.printDebug(['calling _setDuration', 'durationObj', durationObj])
#         if not hasattr(durationObj, "quarterLength"):
#             raise Exception('this must be a Duration object, not %s' % durationObj)
#         objRef = self.obj        
#         if objRef is not None and hasattr(objRef, 'duration'):
#             # if a number assume it is a quarter length
#             objRef.duration = durationObj
#         else:
#             self._unlinkedDuration = durationObj
#             
#     duration = property(_getDuration, _setDuration)
# 
#     offset = property(Music21Object._getOffset, Music21Object._setOffset)
# 
#     #---------------------------------------------------------------------------
#     def __repr__(self):
#         shortObj = (str(self.obj))[0:30]
#         if len(str(self.obj)) > 30:
#             shortObj += "..."
#         if self.id is not None:
#             return '<%s id=%s offset=%s obj="%s">' % \
#                 (self.__class__.__name__, self.id, self.offset, shortObj)
#         else:
#             return '<%s offset=%s obj="%s">' % \
#                 (self.__class__.__name__, self.offset, shortObj)
# 
# 
#     def __eq__(self, other):
#         '''Test WeakElementWrapper equality
# 
#         >>> import note
#         >>> n1 = note.Note("C#")
#         >>> a = WeakElementWrapper(n1)
#         >>> a.offset = 3.0
#         >>> b = WeakElementWrapper(n1)
#         >>> b.offset = 1.0
#         >>> a == b # offset does not matter here
#         True
#         '''
#         if hasattr(other, "obj"):
#             if self.obj == other.obj:
#                 return True
#         return False
# 
#     def __ne__(self, other):
#         '''
#         '''
#         return not self.__eq__(other)
# 
#     def __getattr__(self, name):
#         '''This method is only called when __getattribute__() fails.
#         Using this also avoids the potential recursion problems of subclassing
#         __getattribute__()_
#         
#         see: http://stackoverflow.com/questions/371753/python-using-getattribute-method for examples
# 
#         >>> import note
#         >>> n1 = note.Note("C#4")
#         >>> a = WeakElementWrapper(n1)
#         >>> a.pitch.nameWithOctave
#         'C#4'
#         >>> del n1
#         >>> a.pitch.nameWithOctave
#         Traceback (most recent call last):
#         AttributeError: Could not get attribute 'pitch'
#         >>> a.obj == None
#         True
#         '''
#         storedobj = self._getObj()
#         if name == 'obj': # return unwrapped object
#             return storedobj
# 
#         if storedobj is None:
#             raise AttributeError("Could not get attribute '" + name + "'")
#         else:
#             return object.__getattribute__(storedobj, name)






#-------------------------------------------------------------------------------
class TestMock(Music21Object):
    def __init__(self):
        Music21Object.__init__(self)

class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testCopyAndDeepcopy(self):
        '''Test copyinng all objects defined in this module
        '''
        import sys, types, copy
        for part in sys.modules[self.__module__].__dict__.keys():
            match = False
            for skip in ['_', '__', 'Test', 'Exception']:
                if part.startswith(skip) or part.endswith(skip):
                    match = True
            if match:
                continue
            name = getattr(sys.modules[self.__module__], part)
            if callable(name) and not isinstance(name, types.FunctionType):
                try: # see if obj can be made w/ args
                    obj = name()
                except TypeError:
                    continue
                a = copy.copy(obj)
                b = copy.deepcopy(obj)


    def testObjectCreation(self):
        a = TestMock()
        a.groups.append("hello")
        a.id = "hi"
        a.offset = 2.0
        assert(a.offset == 2.0)

    def testElementEquality(self):
        from music21 import note
        n = note.Note("F-")
        a = ElementWrapper(n)
        a.offset = 3.0
        c = ElementWrapper(n)
        c.offset = 3.0
        assert (a == c)
        assert (a is not c)
        b = ElementWrapper(n)
        b.offset = 2.0
        assert (a != b)

    def testNoteCreation(self):
        from music21 import note, duration
        n = note.Note('A')
        n.offset = 1.0 #duration.Duration("quarter")
        n.groups.append("flute")

        b = copy.deepcopy(n)
        b.offset = 2.0 # duration.Duration("half")
        
        self.assertFalse(n is b)
        n.accidental = "-"
        self.assertEqual(b.name, "A")
        self.assertEqual(n.offset, 1.0)
        self.assertEqual(b.offset, 2.0)
        n.groups[0] = "bassoon"
        self.assertFalse("flute" in n.groups)
        self.assertTrue("flute" in b.groups)

    def testOffsets(self):
        from music21 import note
        a = ElementWrapper(note.Note('A#'))
        a.offset = 23.0
        self.assertEqual(a.offset, 23.0)

    def testObjectsAndElements(self):
        from music21 import note, stream
        note1 = note.Note("B-")
        note1.duration.type = "whole"
        stream1 = stream.Stream()
        stream1.append(note1)
        subStream = stream1.notes

    def testLocationsRefs(self):
        aMock = TestMock()
        bMock = TestMock()

        loc = DefinedContexts()
        loc.add(aMock, 234)
        loc.add(bMock, 12)
        
#        self.assertEqual(loc.getOffsetByIndex(-1), 12)
        self.assertEqual(loc.getOffsetBySite(aMock), 234)
        self.assertEqual(loc.getSiteByOffset(234), aMock)
#        self.assertEqual(loc.getSiteByIndex(-1), bMock)

        #del aMock
        # if the activeSite has been deleted, the None will be returned
        # even though there is still an entry
        #self.assertEqual(loc.getSiteByIndex(0), None)


    def testLocationsNone(self):
        '''Test assigning a None to activeSite
        '''
        loc = DefinedContexts()
        loc.add(None, 0)



    def testM21BaseDeepcopy(self):
        '''Test copying
        '''
        a = Music21Object()
        a.id = 'test'
        b = copy.deepcopy(a)
        self.assertNotEqual(a, b)
        self.assertEqual(b.id, 'test')

    def testM21BaseLocations(self):
        '''Basic testing of M21 base object
        '''
        a = Music21Object()
        b = Music21Object()

        # storing a single offset does not add a DefinedContexts entry  
        a.offset = 30
        # all offsets are store in locations
        self.assertEqual(len(a._definedContexts), 1)
        self.assertEqual(a.getOffsetBySite(None), 30.0)
        self.assertEqual(a.offset, 30.0)

        # assigning a activeSite directly
        a.activeSite = b
        # now we have two offsets in locations
        self.assertEqual(len(a._definedContexts), 2)

        a.offset = 40
        # still have activeSite
        self.assertEqual(a.activeSite, b)
        # now the offst returns the value for the current activeSite 
        self.assertEqual(a.offset, 40.0)

        # assigning a activeSite to None
        a.activeSite = None
        # properly returns original offset
        self.assertEqual(a.offset, 30.0)
        # we still have two locations stored
        self.assertEqual(len(a._definedContexts), 2)
        self.assertEqual(a.getOffsetBySite(b), 40.0)


    def testM21BaseLocationsCopy(self):
        '''Basic testing of M21 base object
        '''
        a = Music21Object()
        a.id = "a obj"
        b = Music21Object()
        b.id = "b obj"

        post = []
        for x in range(30):
            b.id = 'test'
            b.activeSite = a
            c = copy.deepcopy(b)
            c.id = "c obj"
            post.append(c)

        # have two locations: None, and that set by assigning activeSite
        self.assertEqual(len(b._definedContexts), 2)
        g = post[-1]._definedContexts
        self.assertEqual(len(post[-1]._definedContexts), 2)

        # this now works
        self.assertEqual(post[-1].activeSite, a)


        a = Music21Object()

        post = []
        for x in range(30):
            b = Music21Object()
            b.id = 'test'
            b.activeSite = a
            b.offset = 30
            c = copy.deepcopy(b)
            c.activeSite = b
            post.append(c)

        self.assertEqual(len(post[-1]._definedContexts), 3)

        # this works because the activeSite is being set on the object
        self.assertEqual(post[-1].activeSite, b)
        # the copied activeSite has been deepcopied, and cannot now be accessed
        # this fails! post[-1].getOffsetBySite(a)



    def testDefinedContexts(self):
        from music21 import base, note, stream, corpus, clef

        m = stream.Measure()
        m.number = 34
        n = note.Note()
        m.append(n)
        
        n.pitch.addContext(m)
        n.pitch.addContext(n) 
        self.assertEqual(n.pitch.getContextAttr('number'), 34)
        n.pitch.setContextAttr('lyric',  
                               n.pitch.getContextAttr('number'))
        # converted to a string now
        self.assertEqual(n.lyric, '34')


        violin1 = corpus.parseWork("beethoven/opus18no1", 
                                3, extList='xml').getElementById("Violin I")
        lastNote = violin1.flat.notes[-1]
        lastNoteClef = lastNote.getContextByClass(clef.Clef)
        self.assertEqual(isinstance(lastNoteClef, clef.TrebleClef), True)



    def testDefinedContextsSearch(self):
        from music21 import note, stream, clef

        n1 = note.Note('A')
        n2 = note.Note('B')
        c1 = clef.TrebleClef()
        c2 = clef.BassClef()
        
        s1 = stream.Stream()
        s1.insert(10, n1)
        s1.insert(100, n2)
        
        s2 = stream.Stream()
        s2.insert(0, c1)
        s2.insert(100, c2)
        s2.insert(10, s1) # placing s1 here should result in c2 being before n2
        
        self.assertEqual(s1.getOffsetBySite(s2), 10)
        # make sure in the context of s1 things are as we expect
        self.assertEqual(s2.flat.getElementAtOrBefore(0), c1)
        self.assertEqual(s2.flat.getElementAtOrBefore(100), c2)
        self.assertEqual(s2.flat.getElementAtOrBefore(20), n1)
        self.assertEqual(s2.flat.getElementAtOrBefore(110), n2)
        
        # note: we cannot do this
        #self.assertEqual(s2.flat.getOffsetBySite(n2), 110)
        # we can do this:
        self.assertEqual(n2.getOffsetBySite(s2.flat), 110)
        
        # this seems more idiomatic
        self.assertEqual(s2.flat.getOffsetByElement(n2), 110)
        
        # both notes can find the treble clef in the activeSite stream
        post = n1.getContextByClass(clef.TrebleClef)
        self.assertEqual(isinstance(post, clef.TrebleClef), True)
        
        post = n2.getContextByClass(clef.TrebleClef)
        self.assertEqual(isinstance(post, clef.TrebleClef), True)
        
        # n1 cannot find a bass clef
        post = n1.getContextByClass(clef.BassClef)
        self.assertEqual(post, None)
        
        # n2 can find a bass clef, due to its shifted position in s2
        post = n2.getContextByClass(clef.BassClef)
        self.assertEqual(isinstance(post, clef.BassClef), True)



    def testDefinedContextsMeasures(self):
        '''Can a measure determine the last Clef used?
        '''
        from music21 import corpus, clef, stream
        a = corpus.parseWork('bach/bwv324.xml')
        measures = a[0].getElementsByClass('Measure') # measures of first part

        # the parent of measures[1] is set to the new output stream
        self.assertEqual(measures[1].activeSite, measures)
        # the source Part should still be a context of this measure
        self.assertEqual(measures[1].hasContext(a[0]), True)

        # from the first measure, we can get the clef by using 
        # getElementsByClass
        post = measures[0].getElementsByClass(clef.Clef)
        self.assertEqual(isinstance(post[0], clef.TrebleClef), True)

        # make sure we can find offset in a flat representation
        self.assertEqual(a[0].flat.getOffsetByElement(a[0][3]), None)

        # for the second measure
        post = a[0][3].getContextByClass(clef.Clef)
        self.assertEqual(isinstance(post, clef.TrebleClef), True)

        # for the second measure accessed from measures
        # we can get the clef, now that getContextByClass uses semiFlat
        post = measures[3].getContextByClass(clef.Clef)
        self.assertEqual(isinstance(post, clef.TrebleClef), True)

        # add the measure to a new stream
        newStream = stream.Stream()
        newStream.insert(0, measures[3])
        # all previous locations are still available as a context
        self.assertEqual(measures[3].hasContext(newStream), True)
        self.assertEqual(measures[3].hasContext(measures), True)
        self.assertEqual(measures[3].hasContext(a[0]), True)
        # we can still access the clef through this measure on this
        # new stream
        post = newStream[0].getContextByClass(clef.Clef)
        self.assertEqual(isinstance(post, clef.TrebleClef), True)

        


    def testDefinedContextsClef(self):
        from music21 import base, note, stream, clef
        s1 = stream.Stream()
        s2 = stream.Stream()
        n = note.Note()
        s2.append(n)
        s1.append(s2)
        # append clef to outer stream
        s1.insert(0, clef.AltoClef()) 
        pre = s1.getElementAtOrBefore(0, [clef.Clef])
        self.assertEqual(isinstance(pre, clef.AltoClef), True)


        # we should be able to find a clef from the lower-level stream
        post = s2.getContextByClass(clef.Clef)
        self.assertEqual(isinstance(post, clef.AltoClef), True)

        post = s2.getClefs(clef.Clef)
        self.assertEqual(isinstance(post[0], clef.AltoClef), True)



    def testDefinedContextsPitch(self):
        # TODO: this form does not yet work
        from music21 import base, note, stream, clef
        m = stream.Measure()
        m.number = 34
        n = note.Note()
        m.append(n)
        
        #pitchMeasure = n.pitch.getContextAttr('number')
        #n.pitch.setContextAttr('lyric', pitchMeasure)
        #self.assertEqual(n.lyric, 34)


    def testBeatAccess(self):
        '''Test getting beat data from various Music21Objects.
        '''
        from music21 import corpus
        s = corpus.parseWork('bach/bwv66.6.xml')
        p1 = s.parts['Soprano']

        # this does not work; cannot get these values from Measures
        #self.assertEqual(p1.getElementsByClass('Measure')[3].beat, 3)

        # clef/ks can get its beat; these objects are in a pickup, 
        # and this give their bar offset relative to the bar
        for classStr in ['Clef', 'KeySignature']:
            self.assertEqual(p1.flat.getElementsByClass(
                classStr)[0].beat, 4.0)
            self.assertEqual(p1.flat.getElementsByClass(
                classStr)[0].beatDuration.quarterLength, 1.0)
            self.assertEqual(
                p1.flat.getElementsByClass(classStr)[0].beatStrength, 0.25)

        # ts can get beatStrength, beatDuration
        self.assertEqual(p1.flat.getElementsByClass(
            'TimeSignature')[0].beatDuration.quarterLength, 1.0)
        self.assertEqual(p1.flat.getElementsByClass(
            'TimeSignature')[0].beatStrength, 0.25)
        
        # compare offsets found with items positioned in Measures
        # as the first bar is a pickup, the the measure offset here is returned
        # with padding (resulting in 3) 
        post = []
        for n in p1.flat.notes:
            post.append(n._getMeasureOffset())
        self.assertEqual(post, [3.0, 3.5, 0.0, 1.0, 2.0, 3.0, 0.0, 1.0, 2.0, 3.0, 0.0, 0.5, 1.0, 2.0, 3.0, 0.0, 1.0, 2.0, 3.0, 0.0, 1.0, 2.0, 3.0, 0.0, 1.0, 2.0, 3.0, 0.0, 1.0, 2.0, 0.0, 2.0, 3.0, 0.0, 1.0, 1.5, 2.0])

        # compare derived beat string
        post = []
        for n in p1.flat.notes:
            post.append(n.beatStr)
        self.assertEqual(post, ['4', '4 1/2', '1', '2', '3', '4', '1', '2', '3', '4', '1', '1 1/2', '2', '3', '4', '1', '2', '3', '4', '1', '2', '3', '4', '1', '2', '3', '4', '1', '2', '3', '1', '3', '4', '1', '2', '2 1/2', '3'])

        # for stream and Stream subclass, overridden methods not yet
        # specialzied
        # _getMeasureOffset gets the offset within the parent
        # this shows that measure offsets are accommodating pickup
        post = []
        for m in p1.getElementsByClass('Measure'):
            post.append(m._getMeasureOffset())
        self.assertEqual(post, [0.0, 1.0, 5.0, 9.0, 13.0, 17.0, 21.0, 25.0, 29.0, 33.0] )

        # all other methods define None
        post = []
        for n in p1.getElementsByClass('Measure'):
            post.append(n.beat)
        self.assertEqual(post, [None, None, None, None, None, None, None, None, None, None] )

        post = []
        for n in p1.getElementsByClass('Measure'):
            post.append(n.beatStr)
        self.assertEqual(post, [None, None, None, None, None, None, None, None, None, None] )

        post = []
        for n in p1.getElementsByClass('Measure'):
            post.append(n.beatDuration)
        self.assertEqual(post, [None, None, None, None, None, None, None, None, None, None] )


    def testMeaureNumberAccess(self):
        '''Test getting measure numebr data from various Music21Objects.
        '''

        from music21 import corpus, stream, note
        
        s = corpus.parseWork('bach/bwv66.6.xml')
        p1 = s.parts['Soprano']
        for classStr in ['Clef', 'KeySignature', 'TimeSignature']:
            self.assertEqual(p1.flat.getElementsByClass(
                classStr)[0].measureNumberLocal, 0)
        
        match = []
        for n in p1.flat.notes:
            match.append(n.measureNumberLocal)
        self.assertEqual(match, [0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 6, 6, 6, 6, 7, 7, 7, 8, 8, 8, 9, 9, 9, 9] )
        
        
        # create a note and put it in different measures
        m1 = stream.Measure()
        m1.number = 3
        m2 = stream.Measure()
        m2.number = 74
        n = note.Note()
        self.assertEqual(n.measureNumberLocal, None) # not in a Meaure
        m1.append(n)
        self.assertEqual(n.measureNumberLocal, 3) 
        m2.append(n)
        self.assertEqual(n.measureNumberLocal, 74)



    def testPickupMeauresBuilt(self):
        import music21
        from music21 import stream, meter, note
    
        s = stream.Score()
    
        m1 = stream.Measure()
        m1.timeSignature = meter.TimeSignature('4/4')
        n1 = note.Note('d2')
        n1.quarterLength = 1.0
        m1.append(n1)
        # barDuration is baed only on TS
        self.assertEqual(m1.barDuration.quarterLength, 4.0)
        # duration shows the highest offset in the bar
        self.assertEqual(m1.duration.quarterLength, 1.0)
        # presently, the offset of the added note is zero
        self.assertEqual(n1.getOffsetBySite(m1), 0.0)
        # the _getMeasureOffset method is called by all methods that evaluate
        # beat position; this takes padding into account
        self.assertEqual(n1._getMeasureOffset(), 0.0)
        self.assertEqual(n1.beat, 1.0)
        
        # the Measure.padAsAnacrusis() method looks at the barDuration and, 
        # if the Measure is incomplete, assumes its an anacrusis and adds
        # the appropriate padding
        m1.padAsAnacrusis()
        # app values are the same except _getMeasureOffset()
        self.assertEqual(m1.barDuration.quarterLength, 4.0)
        self.assertEqual(m1.duration.quarterLength, 1.0)
        self.assertEqual(n1.getOffsetBySite(m1), 0.0)
        # lowest offset inside of Measure still returns 0
        self.assertEqual(m1.lowestOffset, 0.0)
        # these values are now different
        self.assertEqual(n1._getMeasureOffset(), 3.0)
        self.assertEqual(n1.beat, 4.0)
    
        # appending this measure to the Score
        s.append(m1)
        # score duration is correct: 1
        self.assertEqual(s.duration.quarterLength, 1.0)
        # lowest offset is that of the first bar
        self.assertEqual(s.lowestOffset, 0.0)
        self.assertEqual(s.highestTime, 1.0)
    
    
        m2 = stream.Measure()
        n2 = note.Note('e2')
        n2.quarterLength = 4.0
        m2.append(n2)
        # based on contents
        self.assertEqual(m2.duration.quarterLength, 4.0)
        # we cannot get a bar duration b/c we have not associated a ts
        try:
            m2.barDuration.quarterLength
        except stream.StreamException:
            pass
    
        # append to Score
        s.append(m2)
        # m2 can now find a time signature by looking to parent stream
        self.assertEqual(m2.duration.quarterLength, 4.0)
        # highest time of score takes into account new measure
        self.assertEqual(s.highestTime, 5.0)
        # offset are contiguous when accessed in a flat form
        self.assertEqual([n.offset for n in s.flat.notes], [0.0, 1.0])        
    
    
        m3 = stream.Measure()        
        n3 = note.Note('f#2')
        n3.quarterLength = 3.0
        m3.append(n3)
    
        # add to stream
        s.append(m3)
        # m3 can now find a time signature by looking to parent stream
        self.assertEqual(m2.duration.quarterLength, 4.0)
        # highest time of score takes into account new measure
        self.assertEqual(s.highestTime, 8.0)
        # offset are contiguous when accessed in a flat form
        self.assertEqual([n.offset for n in s.flat.notes], [0.0, 1.0, 5.0])        
    
    
    def testPickupMeauresImported(self):
        from music21 import corpus
        s = corpus.parseWork('bach/bwv103.6')
    
        p = s.parts['soprano']
        m1 = p.getElementsByClass('Measure')[0]
    
    
        self.assertEqual([n.offset for n in m1.notes], [0.0, 0.5])
        self.assertEqual(m1.paddingLeft, 3.0)
        
        #offsets for flat representation have proper spacing
        self.assertEqual([n.offset for n in p.flat.notes], [0.0, 0.5, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 12.5, 13.0, 15.0, 16.0, 16.5, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0, 27.0, 28.0, 28.5, 29.0, 31.0, 32.0, 33.0, 34.0, 34.5, 34.75, 35.0, 35.5, 36.0, 37.0, 38.0, 39.0, 40.0, 41.0, 42.0, 43.0, 44.0, 45.0, 47.0, 48.0, 48.5, 49.0, 50.0, 51.0, 52.0, 53.0, 54.0, 55.0, 56.0, 57.0, 58.0, 59.0, 60.0, 60.5, 61.0, 63.0] )
    

    def testBoundLocations(self):
        '''Bound or relative locations; locations that are not based on a number but an attribute of the site.
        '''
        from music21 import stream, note, bar

        s = stream.Stream()
        n1 = note.Note()
        n1.quarterLength = 20
        s.append(n1)
        self.assertEqual(s.highestTime, 20)

        offset = None

        # this would be in a note
        dc = DefinedContexts()
        # we would add, for that note, a location in object s
        # if offset is None, it is a context, and has no offset
        dc.add(s, None)
        self.assertEqual(len(dc), 1)
        self.assertEqual(len(dc._locationKeys), 0)
        self.assertEqual(dc.getSites(), [])

        dc = DefinedContexts()
        # if we have an offset, we get a location
        dc.add(s, 30)
        self.assertEqual(len(dc), 1)
        self.assertEqual(len(dc._locationKeys), 1)
        self.assertEqual(dc.getSites(), [s])
        self.assertEqual(dc.getOffsets(), [30])
        self.assertEqual(dc.getOffsetBySite(s), 30)
        self.assertEqual(dc.getOffsetByObjectMatch(s), 30)


        dc = DefinedContexts()
        # instead of adding the position of this dc in s, we add a lambda
        # expression that take s as an argument
        dc.add(s, 30)
        self.assertEqual(len(dc), 1)
        self.assertEqual(len(dc._locationKeys), 1)
        self.assertEqual(dc.getSites(), [s])
        self.assertEqual(dc.getOffsets(), [30])
        self.assertEqual(dc.getOffsetBySite(s), 30)
        self.assertEqual(dc.getOffsetByObjectMatch(s), 30)


        # need to account for two cases; where a location is linked
        # to another objects location.
        # and where location is linked to a 

        # could use lambda functions, but they may be hard to seralize
        # instead, use a string for the attribute
        
        dc = DefinedContexts()
        # instead of adding the position of this dc in s, we add a lambda
        # expression that take s as an argument
        dc.add(s, 'highestTime')
        self.assertEqual(len(dc), 1)
        self.assertEqual(len(dc._locationKeys), 1)
        self.assertEqual(dc.getSites(), [s])
        self.assertEqual(dc.getOffsetBySite(s), 20.0)
        self.assertEqual(dc.getOffsets(), [20.0])
        self.assertEqual(dc.getOffsetByObjectMatch(s), 20.0)

        # change the stream and see that the location has changed
        n2 = note.Note()
        n2.quarterLength = 30
        s.append(n2)
        self.assertEqual(s.highestTime, 50)
        self.assertEqual(dc.getOffsetBySite(s), 50.0)

        # can add another location for the lowest offset
        dc.add(s, 'lowestOffset')
        # still only have one site
        self.assertEqual(dc.getSites(), [s])
        self.assertEqual(dc.getOffsetBySite(s), 0.0)

        dc.add(s, 'highestOffset')
        # still only have one site
        self.assertEqual(dc.getSites(), [s])
        self.assertEqual(dc.getOffsetBySite(s), 20.0)

        # valid boundLocations are the following:
        # highestOffset, lowestOffset, highestTime

        # this works, but only b/c we are not actually appending
        # the bar object. 

        s = stream.Stream()
        n1 = note.Note()
        n1.quarterLength = 30
        n2 = note.Note()
        n2.quarterLength = 20

        b1 = bar.Barline()
        s.append(n1)
        self.assertEqual(s.highestTime, 30.0)
        b1.addLocation(s, 'highestTime')
        self.assertEqual(b1.getOffsetBySite(s), 30.0)
        
        s.append(n2)
        self.assertEqual(s.highestTime, 50.0)
        self.assertEqual(b1.getOffsetBySite(s), 50.0)



    def testGetAllContextsByClass(self):
        from music21 import base, note, stream, clef
        s1 = stream.Stream()
        s2 = stream.Stream()
        s3 = stream.Stream()

        n1 = note.Note()
        n2 = note.Note()
        n3 = note.Note()
        c1 = clef.Clef()
        c2 = clef.Clef()
        c3 = clef.Clef()

        s1.append(n1)
        s1.append(c1)
        s2.append(n2)
        s2.append(c2)
        s3.append(n3)
        s3.append(c3)

        # only get n1 here, as that is only level available
        self.assertEqual(s1.getAllContextsByClass('Note'), [n1])
        self.assertEqual(s2.getAllContextsByClass('Note'), [n2])
        self.assertEqual(s1.getAllContextsByClass('Clef'), [c1])
        self.assertEqual(s2.getAllContextsByClass('Clef'), [c2])

        # attach s2 to s1
        s2.append(s1)
        # stream 1 gets both notes
        self.assertEqual(s1.getAllContextsByClass('Note'), [n1, n2])
        # clef 1 gets both notes
        self.assertEqual(c1.getAllContextsByClass('Note'), [n1, n2])

        # stream 2 gets all notes, b/c we take a flat version
        self.assertEqual(s2.getAllContextsByClass('Note'), [n1, n2])
        # clef 2 gets both notes
        self.assertEqual(c2.getAllContextsByClass('Note'), [n1, n2])


        # attach s2 to s3
        s3.append(s2)
        # any stream can get all three notes
        self.assertEqual(s1.getAllContextsByClass('Note'), [n1, n2, n3])
        self.assertEqual(s2.getAllContextsByClass('Note'), [n1, n2, n3])
        self.assertEqual(s3.getAllContextsByClass('Note'), [n1, n2, n3])



    def testStoreLastDeepCopyOf(self):
        from music21 import note
        
        n1 = note.Note()
        n2 = copy.deepcopy(n1)
        self.assertEqual(n2._idLastDeepCopyOf, id(n1))

    
#     def testWeakElementWrapper(self):
#         from music21 import note
#         n = note.Note('g2')
#         n.quarterLength = 1.5
#         self.assertEqual(n.quarterLength, 1.5)
# 
#         self.assertEqual(n, n)
#         wew = WeakElementWrapper(n)
#         unwrapped = wew.obj
#         self.assertEqual(str(unwrapped), '<music21.note.Note G>')
# 
#         self.assertEqual(unwrapped.pitch, n.pitch)
#         self.assertEqual(unwrapped.pitch.nameWithOctave, 'G2')
# 
#         self.assertEqual(unwrapped.quarterLength, n.quarterLength)
#         self.assertEqual(unwrapped.quarterLength, 1.5)
#         self.assertEqual(n.quarterLength, 1.5)
# 
#         self.assertEqual(n, unwrapped)


#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [Music21Object, ElementWrapper, DefinedContexts]


def mainTest(*testClasses):
    '''
    Takes as its arguments modules (or a string 'noDocTest' or 'verbose')
    and runs all of these modules through a unittest suite
    
    unless 'noDocTest' is passed as a module, a docTest
    is also performed on __main__.  Hence the name "mainTest"
    
    run example (put at end of your modules)
    
        import unittest
        class Test(unittest.TestCase):
            def testHello(self):
                hello = "Hello"
                self.assertEqual("Hello", hello)
    
        import music21
        if __name__ == '__main__':
            music21.mainTest(Test)
    '''
    

    if ('noDocTest' in testClasses):
        s1 = unittest.TestSuite()
    else: 
        s1 = doctest.DocTestSuite('__main__', 
        optionflags = (doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE))

    if ('verbose') in testClasses:
        verbosity = 2
    else:
        verbosity = 1

    for thisClass in testClasses:
        if isinstance(thisClass, str):
            pass
        else:
            s2 = unittest.defaultTestLoader.loadTestsFromTestCase(thisClass)
            s1.addTests(s2) 
    runner = unittest.TextTestRunner()
    runner.verbosity = verbosity
    runner.run(s1)  


#------------------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) == 1:
        mainTest(Test)
    elif len(sys.argv) > 1:
        t = Test()
        # arg[1] is test to launch
        if hasattr(t, sys.argv[1]): getattr(t, sys.argv[1])()

#------------------------------------------------------------------------------
# eof

