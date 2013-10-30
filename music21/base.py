# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         base.py
# Purpose:      Music21 base classes and important utilities
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2008-2013 Michael Scott Cuthbert and the music21 Project
# License:      LGPL, see license.txt
#-------------------------------------------------------------------------------

# base -- the convention within music21 is that __init__ files contain:
#    from base import *
'''
`music21.base` is what you get in `music21` if you type ``import music21``. It 
contains all the most low-level objects that also appear in
the music21 module (i.e., music21.base.Music21Object is the same as
music21.Music21Object).

Music21 base classes for :class:`~music21.stream.Stream` objects and all elements 
contained within them including Notes, etc.. Additional objects for defining and manipulating 
elements are included.

The namespace of this file, as all base.py files, is loaded into the package 
that contains this file via __init__.py. Everything in this file is thus 
available after importing music21.

>>> import music21
>>> music21.Music21Object
<class 'music21.base.Music21Object'>

>>> music21.VERSION_STR
'1.7.1'

Alternatively, after doing a complete import, these classes are available
under the module "base":


>>> base.Music21Object
<class 'music21.base.Music21Object'>
'''

#-------------------------------------------------------------------------------
# string and tuple must be the same
from _version import __version__, __version_info__
VERSION = __version_info__
VERSION_STR = __version__
#VERSION_STR = "%s.%s.%s" % (VERSION[0], VERSION[1], VERSION[2])
#-------------------------------------------------------------------------------

import codecs
import copy
import doctest
import sys
import types
import unittest
#import uuid

#-----all exceptions are in the exceptions21 package.
from music21 import exceptions21
Music21Exception = exceptions21.Music21Exception

from music21 import common
from music21 import environment
_MOD = 'music21.base.py'
environLocal = environment.Environment(_MOD)


# check external dependencies and display 
_missingImport = []
import imp
try:
    imp.find_module('matplotlib')
except ImportError:
    _missingImport.append('matplotlib')

try:
    imp.find_module('numpy')
except ImportError:
    _missingImport.append('numpy')

try:
    imp.find_module('scipy')
except ImportError:
    _missingImport.append('scipy')

# used for better PNG processing in lily -- not very important
#try:
#    import PIL
#except ImportError:
#    _missingImport.append('PIL')

# as this is only needed for one module, and error messages print
# to standard io, this has been removed
# try:
#     import pyaudio
# except (ImportError, SystemExit):
#     _missingImport.append('pyaudio')
    #sys.stderr.write('pyaudio is installed but PortAudio is not -- re-download pyaudio at http://people.csail.mit.edu/hubert/pyaudio/')

if len(_missingImport) > 0:
    if environLocal['warnings'] in [1, '1', True]:
        environLocal.warn(common.getMissingImportStr(_missingImport),
        header='music21:')


# define whether weakrefs are used for storage of object locations
WEAKREF_ACTIVE = True

#DEBUG_CONTEXT = False

class SitesException(exceptions21.Music21Exception):
    pass

class Music21ObjectException(exceptions21.Music21Exception):
    pass

class ElementException(exceptions21.Music21Exception):
    pass

#-------------------------------------------------------------------------------
# make subclass of set once that is defined properly
class Groups(list):   
    '''
    Groups is a list of strings used to identify associations that an element might 
    have. 
    
    The Groups object enforces that all elements must be strings, and that 
    the same element cannot be provided more than once.
    
    >>> g = Groups()
    >>> g.append("hello")
    >>> g[0]
    'hello'
    >>> g.append("hello") # not added as already present
    >>> len(g)
    1
    >>> g
    ['hello']
        
    >>> g.append(5)
    Traceback (most recent call last):
    GroupException: Only strings can be used as list names
    '''
    # TODO: presently groups can be cased-differentiated; this may 
    # need to be made case independent
    
    # could be made into a set instance, but actually
    # timing: a subclassed list and a set are almost the same speed...
    
    def append(self, value):
        if isinstance(value, basestring):
            # do not permit the same entry more than once
            if not list.__contains__(self, value): 
                list.append(self, value)
        else:
            raise exceptions21.GroupException("Only strings can be used as list names")
            
    def __setitem__(self, i, y):
        if isinstance(y, basestring):
            list.__setitem__(self, i, y)
        else:
            raise exceptions21.GroupException("Only strings can be used as list names")
        
    def __eq__(self, other):
        '''Test Group equality. In normal lists, order matters; here it does not. 

        >>> a = Groups()
        >>> a.append('red')
        >>> a.append('green')
        >>> a
        ['red', 'green']
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
        TODO: Test! 
        '''
        if other is None or not isinstance(other, Groups):
            return True
        if (list.sort(self) == other.sort()):
            return False
        else:
            return True


#-------------------------------------------------------------------------------
class Sites(object):
    '''
    An object, stored within a Music21Object, that 
    stores (weak) references to a collection of objects 
    that may be contextually relevant to this object.

    Some of these objects are locations (also called sites), 
    or Streams that contain this object. In this case the Sites
    object stores an offset value, used for determining position 
    within a Stream. 

    All defined contexts are stored as dictionaries in a 
    dictionary. The outermost dictionary stores objects.
    '''
#    __slots__ = ('_definedContexts',
#                 '_locationKeys',
#                 '_timeIndex',
#                 'containedById',
#                 '_lastID',
#                 '_lastOffset',
#                 )
    def __init__(self, containedById=None):
        # a dictionary of dictionaries
        self._definedContexts = {} 
        # store idKeys in lists for easy access
        # the same key may be both in locationKeys and contextKeys
        self._locationKeys = []
        # store an index of numbers for tagging the time of defined contexts; 
        # this is used to be able to discern the order of context as added
        self._timeIndex = 0
        # pass a reference to the object that contains this
        self.containedById = containedById
        # cache for performance
        self._lastID = -1 # cannot be None
        self._lastOffset = None

    def __len__(self):
        '''Return the total number of references.

        
        >>> class Mock(base.Music21Object): 
        ...     pass
        >>> aObj = Mock()
        >>> aContexts = base.Sites()
        >>> aContexts.add(aObj)
        >>> len(aContexts) 
        1
        '''
        return len(self._definedContexts)

    def __deepcopy__(self, memo=None):
        '''
        Helper function for copy.deepcopy that in addition to
        copying produces a new, independent Sites object.
        This does not, however, deepcopy site references stored therein.

        All sites, however, are passed on to the new deepcopy, which 
        means that in a deepcopy of a Stream that contains Notes, 
        the copied Note will have the former site as a location, even 
        though the new Note instance is not actually found in the old Stream.

        >>> import copy
        
        >>> class Mock(base.Music21Object): 
        ...     pass
        >>> aObj = Mock()
        >>> aContexts = base.Sites()
        >>> aContexts.add(aObj)
        >>> bContexts = copy.deepcopy(aContexts)
        >>> len(aContexts.get()) == 1
        True
        >>> len(bContexts.get()) == 1
        True
        >>> aContexts.get() == bContexts.get()
        True

        '''
        #TODO: it may be a problem that sites are being transferred to deep
        #copies; this functionality is used at times in context searches, but
        # may be a performance hog.

        new = self.__class__()
        locations = [] #self._locationKeys[:]
        #environLocal.printDebug(['Sites.__deepcopy__', 'self._definedContexts.keys()', self._definedContexts.keys()])
        for idKey in self._definedContexts:
            singleContextDict = self._definedContexts[idKey]
            if singleContextDict['isDead']:
                continue # do not copy dead references
            post = {}
            post['obj'] = singleContextDict['obj'] # already a weak ref

            # not copying the offset in deepcopying means that 
            # the old site becomes a context, not a site
            # this is still experimental
            # post['offset'] = None

            post['offset'] = singleContextDict['offset']
            if post['offset'] is not None:
                locations.append(idKey) # if offset not None, a location

            post['time'] = singleContextDict['time'] # assume still valid
            post['class'] = singleContextDict['class']
            post['isDead'] = False
            new._definedContexts[idKey] = post

        new._locationKeys = locations
        new._timeIndex = self._timeIndex # keep for coherency
        return new

    #---------------------------------------------------------------------------
    # utility conversions

    def unwrapWeakref(self, purgeLocations = True):
        '''
        Unwrap any and all weakrefs stored.

        
        >>> class Mock(base.Music21Object): 
        ...     pass
        >>> aObj = Mock()
        >>> bObj = Mock()
        >>> aSites = base.Sites()
        >>> aSites.add(aObj)
        >>> aSites.add(bObj)
        >>> common.isWeakref(aSites.get()[0]) # unwrapping happens 
        False
        >>> common.isWeakref(aSites._definedContexts[id(aObj)]['obj'])
        True
        >>> aSites.unwrapWeakref()
        >>> common.isWeakref(aSites._definedContexts[id(aObj)]['obj'])
        False
        >>> common.isWeakref(aSites._definedContexts[id(bObj)]['obj'])
        False
        '''
        if purgeLocations is True:
            # might not be needed if you know they are all alive.
            self.purgeLocations(rescanIsDead=True)

        #environLocal.printDebug(['self', self, 'self._definedContexts.keys()', self._definedContexts.keys()])
        for idKey in self._definedContexts:
            if WEAKREF_ACTIVE:
            #if common.isWeakref(self._definedContexts[idKey]['obj']):
                target = self._definedContexts[idKey]['obj']
                if target is None:
                    continue
                if common.isWeakref(target):
                    #environLocal.printDebug(['unwrapping:', self._definedContexts[idKey]['obj']])
                    target = common.unwrapWeakref(target)
                    self._definedContexts[idKey]['obj'] = target
                    # we may need to unwrap the weakrefs in this Stream
                    # if it is not stored elsewhere
#                     if target is not None:
#                         self._definedContexts[idKey]['obj'].unwrapWeakref()

    def wrapWeakref(self):
        '''
        Wrap all stored objects with weakrefs.

        
        >>> class Mock(base.Music21Object): 
        ...     pass
        >>> aObj = Mock()
        >>> bObj = Mock()
        >>> aSites = base.Sites()
        >>> aSites.add(aObj)
        >>> aSites.add(bObj)
        >>> aSites.unwrapWeakref()
        >>> aSites.wrapWeakref()
        >>> common.isWeakref(aSites._definedContexts[id(aObj)]['obj'])
        True
        >>> common.isWeakref(aSites._definedContexts[id(bObj)]['obj'])
        True
        '''
        for idKey in self._definedContexts:
            if self._definedContexts[idKey]['obj'] is None:
                continue # always skip None
            if not common.isWeakref(self._definedContexts[idKey]['obj']):
                #environLocal.printDebug(['wrapping:', self._definedContexts[idKey]['obj']])
                post = common.wrapWeakref(self._definedContexts[idKey]['obj'])
                self._definedContexts[idKey]['obj'] = post

    #---------------------------------------------------------------------------
    # general

    def clear(self):
        '''
        Clear all stored data.
        '''
        self._definedContexts = {} 
        self._locationKeys = []
        self._lastID = -1 # cannot be None
        self._lastOffset = None

    def _prepareObject(self, obj):
        '''
        Prepare an object for storage. 
        May be stored as a standard reference or as a weak reference.
        '''
        # can have this perform differently based on domain
        if obj is None: # leave None alone
            return obj
        elif WEAKREF_ACTIVE:
            return common.wrapWeakref(obj)
        # a normal reference, return unaltered
        else:
            return obj

    def add(self, obj, offset=None, 
            timeValue=None, idKey=None, classString=None):
        '''
        Add a reference to the `Sites` collection for this
        object. 

        N.B. -- like all .sites operations, this is
        an advanced tool not for standard music21 usage.  Instead of:
        
            elObj.add(streamObj, 20.0)
           
        use this command, which will take care of `.sites.add` as well
        as putting `elObj` in `streamObj.elements`:
        
            streamObj.insert(20.0, elObj)

        If `offset` is `None`, then `obj` is interpreted as a Context
        (such as a temperament, a time period, etc.)
        
        If `offset` is not `None`, then `obj` is interpreted as location, 
        i.e., a :class:`~music21.stream.Stream`.  

        `offset` can also be the term `highestTime` which
        is the highest available time in the obj (used for
        ``streamObj.append(el)``)

        The `timeValue` argument is used to store the time
        (in seconds after Jan 1, 1970) when this object was 
        added to locations. If set to `None`, then the current
        time is used.
        
        `idKey` stores the id() of the obj.  If `None`, then
        id(obj) is used.
        
        `classString` stores the class of obj.  If `None` then
        `obj.classes[0]` is used.
        
        TODO: Tests.  Including updates.
        
        '''
        # NOTE: this is a performance critical method

        # a None object will have a key of None
        # do not need to set this as is default
        if idKey is None and obj is not None:
            idKey = id(obj)

        updateNotAdd = False
        if idKey in self._definedContexts:
            updateNotAdd = True 

        if offset is not None: # a location, not a context
            if idKey not in self._locationKeys:                 
                self._locationKeys.append(idKey)
        #environLocal.printDebug(['adding obj', obj, idKey])
        # weak refs were being passed in __deepcopy__ calling this method
        # __deepcopy__ no longer call this method, so we can assume that
        # we will not get weakrefs

        objRef = None

        if obj is not None:
            if classString is None:
                classString = obj.classes[0] # get most current class
            objRef = self._prepareObject(obj)

        if updateNotAdd is True:
            singleContextDict = self._definedContexts[idKey]
        else:
            singleContextDict = {}

        singleContextDict['obj'] = objRef # a weak ref
        singleContextDict['offset'] = offset # offset can be None for contexts
        singleContextDict['class'] = classString 
        singleContextDict['isDead'] = False # store to access w/o unwrapping
        # time is a numeric count, not a real time measure
        if timeValue is None:
            singleContextDict['time'] = self._timeIndex
            self._timeIndex += 1 # increment for next usage
        else:
            singleContextDict['time'] = timeValue
        if not updateNotAdd: # add new/missing information to dictionary
            self._definedContexts[idKey] = singleContextDict


    def remove(self, site):
        '''
        Remove the object (a context or location site) specified 
        from Sites. Object provided can be a location 
        site (i.e., a Stream) or a pure context (like a Temperament). 

        N.B. -- like all .sites operations, this is
        an advanced tool not for standard music21 usage.  Instead of:
        
            elObj.remove(streamObj)
           
        use this command, which will take care of `.sites.remove` as well
        as removing `elObj` from `streamObj.elements`:
        
            streamObj.remove(elObj)

        >>> class Mock(base.Music21Object): 
        ...     pass
        >>> aSite = Mock()
        >>> bSite = Mock()
        >>> cSite = Mock()
        >>> aSites = base.Sites()
        >>> aSites.add(aSite, 23)
        >>> len(aSites)
        1
        >>> aSites.add(bSite, 233)
        >>> len(aSites)
        2
        >>> aSites.add(cSite, 232223)
        >>> len(aSites)
        3
        >>> aSites.remove(aSite)
        >>> len(aSites)
        2

        OMIT_FROM_DOCS
        >>> len(aSites._locationKeys)
        2

        '''
        # must clear
        self._lastID = -1 # cannot be None
        self._lastOffset = None

        siteId = None
        if site is not None: 
            siteId = id(site)
        try:
            del self._definedContexts[siteId]
            #environLocal.printDebug(['removed site w/o exception:', siteId, 'self._definedContexts.keys()', self._definedContexts.keys()])
        except:    
            raise SitesException('an entry for this object (%s) is not stored in this Sites object' % site)
        # also delete from location keys
        if siteId in self._locationKeys:
            self._locationKeys.pop(self._locationKeys.index(siteId))

        #environLocal.printDebug(['removed site:', 'self._definedContexts.getSites()', self.getSites()])
        
    def removeById(self, idKey):
        '''
        Remove a site entry by id key, 
        which is id() of the object. 
        '''
        # must clear if removing
        if idKey == self._lastID:
            self._lastID = -1 # cannot be None
            self._lastOffset = None
        if idKey is None:
            raise SitesException('trying to remove None idKey is not allowed')

        #environLocal.printDebug(['removeById', idKey, 'self._definedContexts.keys()', self._definedContexts.keys()])
        del self._definedContexts[idKey]
        if idKey in self._locationKeys:
            self._locationKeys.pop(self._locationKeys.index(idKey))

    def getById(self, id): # id is okay here @ReservedAssignment
        '''
        Return the object specified by an id.
        Used for testing and debugging. 
        '''
        singleContextDict = self._definedContexts[id]
        # need to check if these is weakref
        #if common.isWeakref(dict['obj']):
        if WEAKREF_ACTIVE:
            return common.unwrapWeakref(singleContextDict['obj'])
        else:
            return singleContextDict['obj']


    def _keysByTime(self, newFirst=True):
        '''
        Get keys sorted by creation time, where most 
        recent are first if `newFirst` is True. else, most recent are last.

        >>> import music21
        >>> class Mock(music21.Music21Object): 
        ...     pass
        >>> aObj = Mock()
        >>> bObj = Mock()
        >>> cObj = Mock()
        >>> aSites = music21.Sites()
        >>> aSites.add(cObj, 345)
        >>> aSites.add(aObj)
        >>> aSites.add(bObj)
        >>> k = aSites._keysByTime()
        >>> aSites._definedContexts[k[0]]['time'] > aSites._definedContexts[k[1]]['time'] > aSites._definedContexts[k[2]]['time']
        True
        '''
        post = []
        for key in self._definedContexts:
            post.append((self._definedContexts[key]['time'], key))
        post.sort()
        if newFirst:
            post.reverse()
        return [k for unused_time, k in post]


    def get(self, locationsTrail=False, sortByCreationTime=False,
            priorityTarget=None, excludeNone=False):
        '''
        Get references; unwrap from weakrefs; order, based 
        on dictionary keys, is from most recently added to least recently added.

        The `locationsTrail` option forces locations to come after all other defined contexts.

        The `sortByCreationTime` option will sort objects by creation time, 
        where most-recently assigned objects are returned first. 

        If `priorityTarget` is defined, this object will be placed first in the list of objects.

        >>> import music21
        >>> class Mock(music21.Music21Object): 
        ...     pass
        >>> aObj = Mock()
        >>> bObj = Mock()
        >>> cObj = Mock()
        >>> aSites = music21.Sites()
        >>> aSites.add(cObj, 345) # a locations
        >>> aSites.add(aObj)
        >>> aSites.add(bObj)
        >>> aSites.get() == [cObj, aObj, bObj]
        True
        >>> aSites.get(locationsTrail=True) == [aObj, bObj, cObj]
        True
        >>> aSites.get(sortByCreationTime=True) == [bObj, aObj, cObj]
        True
        '''
        if sortByCreationTime in [True, 1]:
            keyRepository = self._keysByTime(newFirst=True)
        # reverse creation time puts oldest elements first
        elif sortByCreationTime in [-1, 'reverse']:
            keyRepository = self._keysByTime(newFirst=False)
        else: # None, or False
            keyRepository = self._definedContexts

        post = [] 
        #purgeKeys = []
        
        # get partitioned list of all, w/ locations last if necessary
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
            singleContextDict = self._definedContexts[key]
            # check for None object; default location, not a weakref, keep
            if singleContextDict['obj'] is None:
                if not excludeNone:
                    post.append(singleContextDict['obj'])
            elif WEAKREF_ACTIVE:
                obj = common.unwrapWeakref(singleContextDict['obj'])
                if obj is None: # dead ref
                    singleContextDict['isDead'] = True
                else:
                    post.append(obj)
            else:
                post.append(singleContextDict['obj'])

        # remove dead references
#         if autoPurge:
#             for key in purgeKeys:
#                 self.removeById(key)

        if priorityTarget is not None:
            if priorityTarget in post:
                #environLocal.printDebug(['priorityTarget found in post:', priorityTarget])
                # extract object and make first
                post.insert(0, post.pop(post.index(priorityTarget)))
        return post

    #---------------------------------------------------------------------------
    # for dealing with locations
    def getSites(self, idExclude=None, excludeNone=False):
        '''
        Get all defined contexts that are locations. Note that this unwraps 
        all sites from weakrefs and is thus an expensive operation. 

        >>> import music21
        >>> class Mock(music21.Music21Object): 
        ...     pass
        >>> aObj = Mock()
        >>> bObj = Mock()
        >>> aSites = music21.Sites()
        >>> aSites.add(aObj, 234)
        >>> aSites.add(bObj, 3000)
        >>> len(aSites._locationKeys) == 2
        True
        >>> len(aSites.getSites()) == 2
        True
        '''
#         if idExclude is None:
#             idExclude = [] # else, assume a list
        # use pre-collected keys
        post = []
        for idKey in self._locationKeys:
            if idExclude is not None:
                if idKey in idExclude:
                    continue
            try:
                objRef = self._definedContexts[idKey]['obj']
            except KeyError:
                raise SitesException('no such site: %s' % idKey)
            # skip dead references
            if self._definedContexts[idKey]['isDead']:
                continue
            if idKey is None:
                if not excludeNone: 
                    post.append(None) # keep None as site
            elif not WEAKREF_ACTIVE: # leave None alone
                post.append(objRef)
            else:
                obj = common.unwrapWeakref(objRef)
                if obj is None:
                    self._definedContexts[idKey]['isDead'] = True
                    continue
                post.append(obj)
        return post
    

    def getSitesByClass(self, className):
        '''
        Return sites that match the provided class.
        
        Input can be either a Class object or a string

        >>> import music21
        >>> from music21 import stream
        >>> class Mock(music21.Music21Object): 
        ...     pass
        >>> aObj = Mock()
        >>> bObj = Mock()
        >>> cObj = stream.Stream()
        >>> aSites = music21.Sites()
        >>> aSites.add(aObj, 234)
        >>> aSites.add(bObj, 3000)
        >>> aSites.add(cObj, 200)
        >>> aSites.getSitesByClass(Mock) == [aObj, bObj]
        True
        >>> aSites.getSitesByClass('Stream') == [cObj]
        True
        '''
        found = []
        if not isinstance(className, str):
            className = common.classToClassStr(className)

        for idKey in self._locationKeys:
            if self._definedContexts[idKey]['isDead']:
                continue 
            classStr = self._definedContexts[idKey]['class']
            if classStr == className:
                objRef = self._definedContexts[idKey]['obj']
                if not WEAKREF_ACTIVE: # leave None alone
                    obj = objRef
                else:
                    obj = common.unwrapWeakref(objRef)
                found.append(obj)
        return found
#             
#        found = []
#        for idKey in self._locationKeys:
#            objRef = self._definedContexts[idKey]['obj']
#            if objRef is None:
#                continue
#            if not WEAKREF_ACTIVE: # leave None alone
#                obj = objRef
#            else:
#                obj = common.unwrapWeakref(objRef)
#            match = False
#            if common.isStr(className):
#                if hasattr(obj, 'classes'):
#                    if className in obj.classes:
#                        match = True
#                elif type(obj).__name__.lower() == className.lower():
#                    match = True
#            elif isinstance(obj, className):
#                match = True
#            if match:
#                found.append(obj)
#        return found


    def hasSpannerSite(self):
        '''
        Return True if this object is found in 
        any Spanner. This is determined by looking for 
        a SpannerStorage Stream class as a Site.
        '''
        for idKey in self._locationKeys:
            if self._definedContexts[idKey]['isDead']:
                continue 
            if self._definedContexts[idKey]['class'] == 'SpannerStorage':
                return True
        return False

    def hasVariantSite(self):
        '''
        Return True if this object is found in 
        any Variant. This is determined by looking for 
        a VariantStorage Stream class as a Site.
        '''
        for idKey in self._locationKeys:
            if self._definedContexts[idKey]['isDead']:
                continue 
            if self._definedContexts[idKey]['class'] == 'VariantStorage':
                return True
        return False

    def getSiteCount(self):
        '''
        Return the number of non-dead sites, including None. 
        This does not unwrap weakrefs for performance. 
        '''
        count = 0
        for idKey in self._locationKeys:
            if self._definedContexts[idKey]['isDead']:
                continue 
            count += 1
        return count

    def isSite(self, obj):
        '''
        Given an object, determine if it is a site stored 
        in this Sites. This will return False 
        if the object is simply a context and not a location.
        
        >>> import music21
        >>> class Mock(music21.Music21Object): 
        ...     pass
        >>> aSite = Mock()
        >>> bSite = Mock()
        >>> aLocations = music21.Sites()
        >>> aLocations.add(aSite, 0)
        >>> aLocations.add(bSite) # a context
        >>> aLocations.isSite(aSite)
        True
        >>> aLocations.isSite(bSite)
        False
        '''
        if id(obj) in self._locationKeys:
            return True
        return False

    def hasSiteId(self, siteId):
        '''
        Return True or False if this 
        Sites object already has 
        this site id defined as a location

        >>> import music21
        >>> class Mock(music21.Music21Object): 
        ...     pass
        >>> aSite = Mock()
        >>> bSite = Mock()
        >>> dc = music21.Sites()
        >>> dc.add(aSite, 0)
        >>> dc.add(bSite) # a context
        >>> dc.hasSiteId(id(aSite))
        True
        >>> dc.hasSiteId(id(bSite))
        False
        '''
        if siteId in self._locationKeys:
            return True
        return False

    def getSiteIds(self):
        '''
        Return a list of all site Ids.

        >>> import music21
        >>> class Mock(music21.Music21Object): 
        ...     pass
        >>> aSite = Mock()
        >>> bSite = Mock()
        >>> dc = music21.Sites()
        >>> dc.add(aSite, 0)
        >>> dc.add(bSite) # a context
        >>> dc.getSiteIds() == [id(aSite)]
        True
        '''
        # may want to convert to tuple to avoid user editing?
        return self._locationKeys

    def purgeLocations(self, rescanIsDead=False):
        '''
        Clean all locations that refer to objects that no longer exist.

        The `removeOrphanedSites` option removes sites that 
        may have been the result of deepcopy: the element 
        has the site, but the site does not have
        the element. This results b/c Sites are 
        shallow-copied, and then elements are re-added. 

        >>> import music21
        >>> class Mock(music21.Music21Object): 
        ...     pass
        >>> aSite = Mock()
        >>> bSite = Mock()
        >>> cSite = Mock()
        >>> dSite = Mock()
        >>> aLocations = music21.Sites()
        >>> aLocations.add(aSite, 0)
        >>> aLocations.add(cSite) # a context
        >>> del aSite
        >>> len(aLocations)
        2
        >>> aLocations.purgeLocations(rescanIsDead=True)
        >>> len(aLocations)
        1
        '''
        # first, check if any sites are dead, and cache the results
        if rescanIsDead:
            for idKey in self._locationKeys:
                if idKey is None: 
                    continue
                if self._definedContexts[idKey]['isDead']:
                    continue # already marked
                if WEAKREF_ACTIVE:
                    obj = common.unwrapWeakref(
                        self._definedContexts[idKey]['obj'])
                else:
                    obj = self._definedContexts[idKey]['obj']
                if obj is None: # if None, it no longer exists
                    self._definedContexts[idKey]['isDead'] = True
        # use previously set isDead entry, so as not to
        # unwrap all references
        remove = []
        for idKey in self._locationKeys:
            if idKey is None: 
                continue
            if self._definedContexts[idKey]['isDead']:
                remove.append(idKey)
        for idKey in remove:
            # this call changes the ._locationKeys list, and thus must be 
            # out side _locationKeys loop
            self.removeById(idKey)
        

    def getOffsetBySiteId(self, idKey, strictDeadCheck = False):
        '''
        Main method for getting an offset from a location key.

        >>> import music21
        >>> class Mock(music21.Music21Object): 
        ...     pass
        >>> aSite = Mock()
        >>> bSite = Mock()
        >>> cSite = Mock()
        >>> dSite = Mock()
        >>> eSite = Mock()
        >>> aLocations = music21.Sites()
        >>> aLocations.add(aSite, 0)
        >>> aLocations.add(cSite) # a context
        >>> aLocations.add(bSite, 234) # can add at same offset or a different one
        >>> aLocations.add(dSite) # a context
        >>> aLocations.getOffsetBySiteId(id(bSite))
        234
        
        If strictDeadCheck is False (default) we can still retrieve the context from a dead weakref.  This is necessary to
        get the offset from an iterated Stream often.  Eventually, this should become True -- but too many errors for now.
        
        >>> idBSite = id(bSite)
        >>> del(bSite)
        >>> aLocations._definedContexts[idBSite]['obj']
        <weakref at 0x...; dead>
        >>> aLocations._definedContexts[idBSite]['obj'] is None
        False     
        >>> common.unwrapWeakref(aLocations._definedContexts[idBSite]['obj']) is None
        True
        
        >>> aLocations.getOffsetBySiteId(idBSite, strictDeadCheck = False) # default
        234
        
        With this, you'll get an exception:
        
        >>> aLocations.getOffsetBySiteId(idBSite, strictDeadCheck = True)
        Traceback (most recent call last):
        SitesException: Could not find the object with id ... in the Site marked with idKey ... (was there, now site is dead). 
           object <music21.base.Sites object at 0x...>, definedContexts: {...}
           containedById = ...
        
        
        '''
        # NOTE: this is a core method called very frequently
#        if idKey == self._lastID:
#            return self._lastOffset
        try:
            value = self._definedContexts[idKey]['offset']
            if WEAKREF_ACTIVE and strictDeadCheck is True and self._definedContexts[idKey]['obj'] is not None:
                obj = common.unwrapWeakref(self._definedContexts[idKey]['obj'])
                if obj is None:
                    #if self._definedContexts[idKey]['isDead'] is True: # not good enough
                    errorMsg = "Could not find the object with id %s in the Site marked with idKey %s (was there, now site is dead). " % (id(self), idKey)
                    errorMsg += "\n   object %r, definedContexts: %r" % (self, self._definedContexts)
                    errorMsg += "\n   containedById = %r" % (self.containedById)
                    raise SitesException(errorMsg)
                
        except KeyError:
            errorMsg = "Could not find the object with id %s in the Site marked with idKey %s. " % (id(self), idKey)
            errorMsg += "\n   object %r, definedContexts: %r" % (self, self._definedContexts)
            errorMsg += "\n   containedById = %d" % (self.containedById)
            raise SitesException(errorMsg)
        # stored string are assummed to be attributes of the stored object
        if isinstance(value, str):
            if value not in ['highestTime', 'lowestOffset', 'highestOffset']:
                raise SitesException('attempted to set a bound offset with a string attribute that is not supported: %s' % value)
            if WEAKREF_ACTIVE:
                obj = common.unwrapWeakref(self._definedContexts[idKey]['obj'])
            else:
                obj = self._definedContexts[idKey]['obj']
            # offset value is an attribute string
            # canot cache these values as may change outside of definedcontexts
            return getattr(obj, value)
        # if value is not a string, it is a numerical offset
        self._lastID = idKey
        self._lastOffset = value
        return value


    def getOffsets(self):
        '''
        Return a list of all offsets.

        >>> import music21
        >>> class Mock(music21.Music21Object): 
        ...     pass
        >>> aSite = Mock()
        >>> bSite = Mock()
        >>> cSite = Mock()
        >>> dSite = Mock()
        
        >>> aLocations = music21.Sites()
        >>> aLocations.add(aSite, 0)
        >>> aLocations.add(cSite) # a context
        >>> aLocations.add(bSite, 234) # can add at same offset or another
        >>> aLocations.add(dSite) # a context
        >>> aLocations.getOffsets()
        [0, 234]
        '''
        # here, already having location keys may be an advantage
        return [self.getOffsetBySiteId(x) for x in self._locationKeys] 


    def getOffsetByObjectMatch(self, obj):
        '''
        For a given object, return the 
        offset using a direct object match. 
        The stored id value is not used; 
        instead, the id() of both the stored 
        object reference and the supplied 
        object is used. 

        this should be replaced by getOffsetBySite(strictDeadCheck = True)...
        

        >>> import music21
        >>> class Mock(music21.Music21Object): 
        ...     pass
        >>> aSite = Mock()
        >>> bSite = Mock()
        >>> aLocations = music21.Sites()
        >>> aLocations.add(aSite, 23)
        >>> aLocations.add(bSite, 121.5)
        >>> aLocations.getOffsetByObjectMatch(aSite)
        23
        >>> aLocations.getOffsetByObjectMatch(bSite)
        121.5
        '''
        for idKey in self._definedContexts:
            singleContextDict = self._definedContexts[idKey]
            if singleContextDict['isDead']: # cal alway skip
                continue
            # must unwrap references before comparison
            #if common.isWeakref(dict['obj']):
            if WEAKREF_ACTIVE:
                compareObj = common.unwrapWeakref(singleContextDict['obj'])
            else:
                compareObj = singleContextDict['obj']
            if compareObj is None: # mark isDead for later removal
                singleContextDict['isDead'] = True
                continue
            if id(compareObj) == id(obj):
                #environLocal.printDebug(['found object as site', obj, id(obj), 'idKey', idKey])
                return self.getOffsetBySiteId(idKey) #dict['offset']
        raise SitesException('an entry for this object (%s) is not stored in Sites' % obj)

    def getOffsetBySite(self, site):
        '''
        For a given site return this
        Sites's offset in it. The None site is 
        permitted. The id() of the site is used to find the offset. 


        >>> import music21
        >>> class Mock(music21.Music21Object): 
        ...     pass
        >>> aSite = Mock()
        >>> bSite = Mock()
        >>> aLocations = music21.Sites()
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
            return self.getOffsetBySiteId(siteId) 
            #post = self._definedContexts[siteId]['offset']
        except SitesException: # the site id is not valid
            #environLocal.printDebug(['getOffsetBySite: trying to get an offset by a site failed; self:', self, 'site:', site, 'defined contexts:', self._definedContexts])
            raise # re-raise Exception


    def setOffsetBySite(self, site, value):
        '''Changes the offset of the site specified.  Note that this can also be
        done with add, but the difference is that if the site is not in 
        Sites, it will raise an exception.
        
        >>> import music21
        >>> class Mock(music21.Music21Object): 
        ...     pass
        
        >>> aSite = Mock()
        >>> bSite = Mock()
        >>> cSite = Mock()
        
        >>> aLocations = music21.Sites()
        >>> aLocations.add(aSite, 23)
        >>> aLocations.add(bSite, 121.5)
        >>> aLocations.setOffsetBySite(aSite, 20)
        >>> aLocations.getOffsetBySite(aSite)
        20
        
        >>> aLocations.setOffsetBySite(cSite, 30)        
        Traceback (most recent call last):
        SitesException: an entry for this object (<...Mock object at 0x...>) is not stored in Sites
        '''
        siteId = None
        if site is not None:
            siteId = id(site)
        # will raise an index error if the siteId does not exist
        try:
            self._definedContexts[siteId]['offset'] = value
            self._lastID = siteId
            self._lastOffset = value
        except KeyError:
            raise SitesException('an entry for this object (%s) is not stored in Sites' % site)
            

    def setOffsetBySiteId(self, siteId, value):
        '''Set an offset by siteId. This assumes that 
        the site is valid, is best used for advanced, 
        performance critical usage only.

        The `siteId` parameter can be None.
        '''
        try:
            self._definedContexts[siteId]['offset'] = value
            self._lastID = siteId
            self._lastOffset = value
        except KeyError:
            raise SitesException('an entry for this object (%s) is not stored in Sites' % siteId)


    def getSiteByOffset(self, offset):
        '''For a given offset return the site that fits it

        More than one Site may have the same offset; 
        this at one point returned the last site added by sorting time,
        but now we use a dict, so there's no guarantee that the 
        one you want will be there -- need orderedDicts!

        >>> import music21
        >>> class Mock(music21.Music21Object): 
        ...     pass
        >>> aSite = Mock()
        >>> bSite = Mock()
        >>> cSite = Mock()
        >>> aLocations = music21.Sites()
        >>> aLocations.add(aSite, 23)
        >>> aLocations.add(bSite, 23121.5)
        >>> aSite == aLocations.getSiteByOffset(23)
        True
        '''

        match = None
        for siteId in self._definedContexts:
            # might need to use almost equals here
            if self._definedContexts[siteId]['offset'] == offset:
                if self._definedContexts[siteId]['isDead']:
                    return None
                match = self._definedContexts[siteId]['obj']
                break
        if WEAKREF_ACTIVE:
            if match is None: # this is a dead erfs
                return match
            elif not common.isWeakref(match):
                raise SitesException('site on coordinates is not a weak ref: %s' % match)
            return common.unwrapWeakref(match)
        else:
            return match


    #---------------------------------------------------------------------------
    # for dealing with contexts or getting other information

    def getByClass(self, className, serialReverseSearch=True, callerFirst=None,
             sortByCreationTime=False, prioritizeActiveSite=False, 
             priorityTarget=None, getElementMethod='getElementAtOrBefore', 
             memo=None):
        '''
        Return the most recently added reference based on className. 
        Class name can be a string or the class name.

        This will recursively search the defined contexts of existing defined contexts.

        The `callerFirst` parameters is simply used to pass a reference of the first caller; this
        is necessary if we are looking within a Stream for a flat offset position.

        If `priorityTarget` is specified, this location will 
        be searched first. The `prioritizeActiveSite` is pased to 
        to any recursively called getContextByClass() calls. 

        The `getElementMethod` is a string that selects which Stream method 
        is used to get elements for searching with getElementsByClass() calls. 

        >>> import music21
        >>> class Mock(music21.Music21Object): 
        ...     pass
        >>> import time
        >>> aObj = Mock()
        >>> bObj = Mock()
        >>> aSites = music21.Sites()
        >>> aSites.add(aObj)
        >>> #time.sleep(.05)
        >>> aSites.add(bObj)
        >>> # we get the most recently added object first
        >>> aSites.getByClass('Mock', sortByCreationTime=True) == bObj
        True
        >>> aSites.getByClass(Mock, sortByCreationTime=True) == bObj
        True

        OMIT_FROM_DOCS
        TODO: not sure if memo is properly working: need a test case
        '''
        #if DEBUG_CONTEXT: print 'Y: first call'
        # in general, this should not be the first caller, as this method
        # is called from a Music21Object, not directly on the Sites
        # isntance. Nontheless, if this is the first caller, it is the first
        # caller. 
        if callerFirst is None: # this is the first caller
            callerFirst = self # set Sites as caller first
        if memo is None:
            memo = {} # intialize
        post = None
        #count = 0

        # search any defined contexts first
        # need to sort: look at most-recently added objs are first
        objs = self.get(locationsTrail=False,  
                        sortByCreationTime=sortByCreationTime,
                        priorityTarget=priorityTarget, 
                        excludeNone=True)
        #printMemo(memo, 'getByClass() called: looking at %s sites' % len(objs))
        classNameIsStr = common.isStr(className)
        for obj in objs:
            #environLocal.printDebug(['memo', memo])
            if classNameIsStr:
                if className in obj.classes:
                    post = obj       
                    break
            elif isinstance(obj, className):
                    post = obj
                    break
        if post is not None:
            return post

        # all objs here are containers, as they are all locations
        # if we could be sure that these objs do not have their own locations
        # and do not have the target class, we can skip
        for obj in objs:
            #if DEBUG_CONTEXT: print '\tY: getByClass: iterating objs:', id(obj), obj
            if (classNameIsStr and obj.isFlat and 
                obj.sites.getSiteCount() == 1):
                #if DEBUG_CONTEXT: print '\tY: skipping flat stream that does not contain object:', id(obj), obj
                #environLocal.printDebug(['\tY: skipping flat stream that does not contain object:'])
                if not obj.hasElementOfClass(className, forceFlat=True):
                    continue # skip, not in this stream

            # if after trying to match name, look in the defined contexts' 
            # defined contexts [sic!]
            #if post is None: # no match yet
            # access public method to recurse
            if id(obj) not in memo:
                # if the object is a Musci21Object
                #if hasattr(obj, 'getContextByClass'):
                # store this object as having been searched
                memo[id(obj)] = obj
                post = obj.getContextByClass(className,
                       serialReverseSearch=serialReverseSearch,
                       callerFirst=callerFirst, 
                       sortByCreationTime=sortByCreationTime, 
                       prioritizeActiveSite=prioritizeActiveSite,
                       getElementMethod=getElementMethod,
                       memo=memo)
                if post is not None:
                    break
#                 else: # this is not a music21 object
#                     pass
                    #environLocal.printDebug['cannot call getContextByClass on obj stored in DefinedContext:', obj]
#             else: # objec has already been searched
#                 pass
                #environLocal.printDebug['skipping searching of object already searched:', obj]
#             else: # post is not None
#                 break
        return post



    def getAllByClass(self, className, found=None, idFound=None, memo=None):
        '''
        Return all known references of a given class found 
        in any association with this Sites object.

        This will recursively search the defined contexts 
        of existing defined contexts, and return a list of all 
        objects that match the given class.


        >>> import music21
        >>> class Mock(music21.Music21Object): 
        ...    pass
        >>> class Mocker(music21.Music21Object): 
        ...    pass
        >>> aObj = Mock()
        >>> bObj = Mock()
        >>> cObj = Mocker()
        >>> dc = music21.Sites()
        >>> dc.add(aObj)
        >>> dc.add(bObj)
        >>> dc.add(cObj)
        >>> dc.getAllByClass(Mock) == [aObj, bObj]
        True
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
            if id(obj) not in memo:
                # if the object is a Musci21Object
                #if hasattr(obj, 'getContextByClass'):
                # store this object as having been searched
                memo[id(obj)] = obj
                # will add values to found
                #environLocal.printDebug(['getAllByClass()', 'about to call getAllContextsByClass', 'found', found, 'obj', obj])
                obj.getAllContextsByClass(className, found=found,
                    idFound=idFound, memo=memo)
        # returning found, but not necessary
        return found

    def getAttrByName(self, attrName):
        '''
        Given an attribute name, search all objects and find the first
        that matches this attribute name; then return a reference to this attribute.

        >>> import music21
        >>> class Mock(music21.Music21Object): 
        ...     attr1 = 234
        >>> aObj = Mock()
        >>> aObj.attr1 = 234
        >>> bObj = Mock()
        >>> bObj.attr1 = 98
        >>> aSites = music21.Sites()
        >>> aSites.add(aObj)
        >>> len(aSites)
        1
        >>> aSites.getAttrByName('attr1') == 234
        True
        >>> aSites.remove(aObj)
        >>> aSites.add(bObj)
        >>> aSites.getAttrByName('attr1') == 98
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

        >>> import music21
        >>> class Mock(music21.Music21Object): 
        ...     attr1 = 234
        >>> aObj = Mock()
        >>> bObj = Mock()
        >>> bObj.attr1 = 98
        >>> aSites = music21.Sites()
        >>> aSites.add(aObj)
        >>> aSites.add(bObj)
        >>> aSites.setAttrByName('attr1', 'test')
        >>> aSites.getAttrByName('attr1') == 'test'
        True
        '''
        #post = None
        for obj in self.get():
            if obj is None: continue # in case the reference is dead
            try:
                junk = getattr(obj, attrName) # if attr already exists
                setattr(obj, attrName, value) # if attr already exists
            except AttributeError:
                pass


#-------------------------------------------------------------------------------
class Music21Object(object):
    '''
    Base class for all music21 objects.
    
    All music21 objects have seven pieces of information:    
    
    1. id: identification string unique to the objects container (optional)
    2. groups: a Groups object: which is a list of strings identifying 
       internal subcollections (voices, parts, selections) to which this element belongs
    3. duration: Duration object representing the length of the object
    4. activeSite: a weakreference to the currently active Location
    5. offset: a floating point value, generally in quarter lengths, specifying the position of the object in a site. 
    6. priority: int representing the position of an object among all
       objects at the same offset.
    7. sites: a Sites object that stores all the Streams and Contexts that an object is in.

    Contexts, locations, and offsets are stored in a :class:`~music21.base.Sites` object. 
    Locations specify connections of this object to one location in a Stream subclass. 
    Contexts are weakrefs for current objects that are associated with this object 
    (similar to locations but without an offset)

    Each of these may be passed in as a named keyword to any music21 object.
    
    Some of these may be intercepted by the subclassing object (e.g., duration within Note)
    '''

    classSortOrder = 20  # default classSortOrder
    # these values permit fast class comparisons for performance crtical cases
    isStream = False
    isSpanner = False
    isVariant = False

    # indicates that it can be frozen using _autoGatherAttributes if nothing has been defined for it
    _jsonFreezer = True

    # define order to present names in documentation; use strings
    _DOC_ORDER = ['classes', 'fullyQualifiedClasses', 'findAttributeInHierarchy', 'getContextAttr', 'setContextAttr']
    # documentation for all attributes (not properties or methods)
    _DOC_ATTR = {
    'id': 'A unique identification string (not to be confused with the default `.id()` method.',
    'groups': 'An instance of a :class:`~music21.base.Group` object which describes arbitrary `Groups` that this object belongs to.',
    'isStream': 'Boolean value for quickly identifying :class:`~music21.stream.Stream` objects (False by default).',
    'isSpanner': 'Boolean value for quickly identifying :class:`~music21.spanner.Spanner` objects (False by default).',
    'isVariant': 'Boolean value for quickly identifying :class:`~music21.variant.Variant` objects (False by default).',
    'classSortOrder' : '''Property which returns an number (int or otherwise)
        depending on the class of the Music21Object that
        represents a priority for an object based on its class alone --
        used as a tie for stream sorting in case two objects have the
        same offset and priority.  Lower numbers are sorted to the left
        of higher numbers.  For instance, Clef, KeySignature, TimeSignature
        all come (in that order) before Note.
        
        All undefined classes have classSortOrder of 20 -- same as note.Note
        
        
        >>> m21o = base.Music21Object()
        >>> m21o.classSortOrder
        20
        
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
    'hideObjectOnPrint': 'if set to `True` will not print upon output (only used in MusicXML output at this point and Lilypond for notes, chords, and rests).',
    'xPosition': 'if set, defines the display x-position from the start of the container (in musicxml "tenths" by default)',
    }

    def __init__(self, *arguments, **keywords):
        # None is stored as the internal location of an obj w/o any sites
        self._activeSite = None
        # cached id in case the weakref has gone away...
        self._activeSiteId = None 
        # if this element has been copied, store the id() of the last source
        self._idLastDeepCopyOf = None

        # store classes once when called
        self._classes = None 
        self._fullyQualifiedClasses = None
        # private duration storage; managed by property
        self._duration = None
        self._priority = 0 # default is zero

        self.hideObjectOnPrint = False
        self.xPosition = None
        
        if "id" in keywords:
            self.id = keywords["id"]            
        else:
            self.id = id(self)

        # a duration object is not created until the .duration property is
        # accessed with _getDuration(); this is a performance optimization
        if "duration" in keywords:
            self.duration = keywords["duration"]
        if "groups" in keywords and keywords["groups"] is not None:
            self.groups = keywords["groups"]
        else:
            self.groups = Groups()
        if "sites" in keywords:
            self.sites = keywords["sites"]
        else:
            self.sites = Sites(containedById=id(self))
            # set up a default location for self at zero
            # use None as the name of the site
            self.sites.add(None, 0.0)

        if "activeSite" in keywords:
            self.activeSite = keywords["activeSite"]

        # only for an output format
        self._overriddenLily = None

    def mergeAttributes(self, other):
        '''
        Merge all elementary, static attributes. Namely, 
        `id` and `groups` attributes from another music21 object. 
        Can be useful for copy-like operations.

        
        >>> m1 = base.Music21Object()
        >>> m2 = base.Music21Object()
        >>> m1.id = 'music21Object1'
        >>> m1.groups.append("group1")
        >>> m2.mergeAttributes(m1)
        >>> m2.id
        'music21Object1'
        >>> "group1" in m2.groups
        True

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
        #environLocal.printDebug(['calling Music21Object.__deepcopy__', self])

        # call class to get a new, empty instance
        new = self.__class__()
        #environLocal.printDebug(['Music21Object.__deepcopy__', self, id(self)])
        #for name in dir(self):
        for name in self.__dict__:
            if name.startswith('__'):
                continue

            part = getattr(self, name)
            # attributes that require special handling
            if name == '_activeSite':
                #environLocal.printDebug([self, 'copying activeSite weakref', self._activeSite])
                # keep a reference, not a deepcopy
                # do not use activeSite property; simply use same weak ref obj
                setattr(new, name, self._activeSite)
                #pass
            elif name == 'id':
                # if the id of this source is set to its obj ide, do not copy
                if part != id(self):
                    newValue = copy.deepcopy(part, memo)
                    setattr(new, name, newValue)
            # use sites own __deepcopy__, but set contained by id
            elif name == 'sites':
                newValue = copy.deepcopy(part, memo)
                #environLocal.printDebug(['copied definedContexts:', newValue._locationKeys])
                newValue.containedById = id(new)
                setattr(new, name, newValue)
            else: # use copy.deepcopy, will call __deepcopy__ if available
                newValue = copy.deepcopy(part, memo)
                #setattr() will call the set method of a named property.
                setattr(new, name, newValue)

        # must do this after copying
        new._idLastDeepCopyOf = id(self)
        new.purgeOrphans()

        #environLocal.printDebug([self, 'end deepcopy', 'self._activeSite', self._activeSite])
        return new


    def isClassOrSubclass(self, classFilterList):
        '''
        Given a class filter list (a list or tuple must be submitted), 
        which may have strings or class objects, determine 
        if this class is of the provided classes or a subclasses. 
        '''
        # NOTE: this is a performance critical operation
        # for performance, only accept lists or tuples

        # in case classFilterList is a tuple of classes, can try right away
        # do not change, as performance critical
#         try:
#             if isinstance(self, classFilterList):
#                 return True
#         except TypeError:
#             pass
        eClasses = self.classes # get cached from property
        for className in classFilterList:
            # new method uses string matching of .classes attribute
            # temporarily check to see if this is a string
            #if className in eClasses or (not isinstance(className, str) and isinstance(e, className)):
            if className in eClasses:
                return True
            try: # className may be a string or a Class
                if isinstance(self, className):
                    return True
            # catch TypeError: isinstance() arg 2 must be a class, type, or tuple of classes and types
            except TypeError:
                continue        
        return False


    def _getClasses(self):
        #environLocal.printDebug(['calling _getClasses'])
        if self._classes is None:
            #environLocal.printDebug(['setting self._classes', id(self), self])
            self._classes = [x.__name__ for x in self.__class__.mro()] 
        return self._classes    

    classes = property(_getClasses, 
        doc='''Returns a list containing the names (strings, not objects) of classes that this 
        object belongs to -- starting with the object's class name and going up the mro()
        for the object.  Very similar to Perl's @ISA array:
    
        
        >>> q = note.QuarterNote()
        >>> q.classes
        ['QuarterNote', 'Note', 'NotRest', 'GeneralNote', 'Music21Object', 'object']
        
        Having quick access to these things as strings makes it easier to do comparisons:
        
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
        {10.0} <music21.clef.GClef>
        {30.0} <music21.clef.FrenchViolinClef>    
        ''')

    def _getFullyQualifiedClasses(self):
        #environLocal.printDebug(['calling _getClasses'])
        if self._fullyQualifiedClasses is None:
            #environLocal.printDebug(['setting self._fullyQualifiedClasses', id(self), self])
            self._fullyQualifiedClasses = [x.__module__ + '.' + x.__name__ for x in self.__class__.mro()] 
        return self._fullyQualifiedClasses

    fullyQualifiedClasses = property(_getFullyQualifiedClasses, 
        doc='''
        Similar to `.classes`, returns a list containing the names (strings, not objects) of 
        classes with the full package name that this 
        object belongs to -- starting with the object's class name and going up the mro()
        for the object.  Very similar to Perl's @ISA array:
    
        
        >>> q = note.QuarterNote()
        >>> q.fullyQualifiedClasses
        ['music21.note.QuarterNote', 'music21.note.Note', 'music21.note.NotRest', 'music21.note.GeneralNote', 'music21.base.Music21Object', '__builtin__.object']
        ''')
    
    #---------------------------------------------------------------------------
    # look at this object for an atttribute; if not here
    # look up to activeSite

    def findAttributeInHierarchy(self, attrName):
        '''
        If this element is contained within a Stream (or other Music21 element), 
        findAttributeInHierarchy() searches the attributes of the activeSite for
        this attribute and returns its value. 
        
        If the activeSite does not have this attribute then 
        we search its activeSite and up through the hierarchy until we find a value for
        this attribute.  Or it Returns None if there is no match. 

        
        >>> m = stream.Measure()
        >>> m.number = 12
        >>> n = note.Note()
        >>> m.append(n)
        >>> n.activeSite is m
        True
        >>> n.findAttributeInHierarchy('number')
        12
        >>> print(n.findAttributeInHierarchy('elephant'))
        None
        
        Recursive searches also work.  Here, the Score object is the only one with a 'parts' attribute.
        
        >>> p1 = stream.Part()
        >>> p1.insert(0, m)
        >>> p2 = stream.Part()
        >>> s = stream.Score()
        >>> s.insert(0, p1)
        >>> s.insert(0, p2)
        >>> n.activeSite.activeSite is p1
        True
        >>> n.activeSite.activeSite.activeSite is s
        True

        >>> parts = n.findAttributeInHierarchy('parts')
        >>> (parts[0] is p1, parts[1] is p2)
        (True, True)
        
        OMIT_FROM_DOCS
        this was formerly called SeachParent, then searchActiveSiteByAttr, but we might do other types 
        of searches
        '''
        found = None
        if self.activeSite is not None:
            #print "got activeSite for %r, %r" % (self, self.activeSite)
            try:
                found = getattr(self.activeSite, attrName)
            except AttributeError:
                # not sure of passing here is the best action
                environLocal.printDebug(['findAttributeInHierarchy call raised attribute error for attribute:', attrName])
                pass
            if found is None:
                found = self.activeSite.findAttributeInHierarchy(attrName)
        return found
        

#     def searchActiveSiteByClass(self, classFilterList)
#         '''
#         The first encountered result is returned. 
#         '''
#         if not isinstance(classFilterList, list):
#             if not isinstance(classFilterList, tuple):
#                 classFilterList = [classFilterList]


    def getOffsetBySite(self, site):
        '''
        If this class has been registered in a container such as a Stream, 
        that container can be provided here, and the offset in that object
        can be returned. 

        Note that this is different than the getOffsetByElement() method on 
        Stream in that this can never access the flat representation of a Stream.

        
        >>> n = note.Note('A-4')  # a Music21Objecct
        >>> n.offset = 30
        >>> n.getOffsetBySite(None)
        30.0
        
        >>> s1 = stream.Stream()
        >>> s1.id = 'containingStream'
        >>> s1.insert(20.5, n)
        >>> n.getOffsetBySite(s1)
        20.5
        >>> s2 = stream.Stream()
        >>> s2.id = 'notContainingStream'
        >>> n.getOffsetBySite(s2)
        Traceback (most recent call last):
        SitesException: The object <music21.note.Note A-> is not in site <music21.stream.Stream notContainingStream>.
        '''
        try:
            return self.sites.getOffsetBySite(site)
        except SitesException:
            raise SitesException('The object %r is not in site %r.' % (self, site))

    def setOffsetBySite(self, site, value):
        '''
        Direct access to the Sites setOffsetBySite() method. 
        This should only be used for advanced processing of known site 
        that already has been added.

        >>> import music21
        >>> class Mock(music21.Music21Object): 
        ...     pass
        >>> aSite = Mock()
        >>> a = music21.Music21Object()
        >>> a.sites.add(aSite, 20)
        >>> a.setOffsetBySite(aSite, 30)
        >>> a.getOffsetBySite(aSite)
        30
        '''
        return self.sites.setOffsetBySite(site, value)


    def getContextAttr(self, attr):
        '''
        Given the name of an attribute, search the Sites object for
        contexts having this attribute and return 
        the best match.

        >>> import music21
        >>> class Mock(music21.Music21Object): 
        ...     attr1 = 234
        >>> aObj = Mock()
        >>> aObj.attr1 = 'test'
        >>> a = music21.Music21Object()
        >>> a.sites.add(aObj)
        >>> a.getContextAttr('attr1')
        'test'
        '''
        return self.sites.getAttrByName(attr)

    def setContextAttr(self, attrName, value):
        '''
        Given the name of an attribute, search Contexts and return 
        the best match.

        >>> import music21
        >>> class Mock(music21.Music21Object): 
        ...     attr1 = 234
        >>> aObj = Mock()
        >>> aObj.attr1 = 'test'
        >>> a = music21.Music21Object()
        >>> a.sites.add(aObj)
        >>> a.getContextAttr('attr1')
        'test'
        >>> a.setContextAttr('attr1', 3000)
        >>> a.getContextAttr('attr1')
        3000
        '''
        return self.sites.setAttrByName(attrName, value)

    def addContext(self, obj):
        '''
        Add an object to the :class:`~music21.base.Sites` object. 
        For adding a location, use :meth:`~music21.base.Music21Object.addLocation`.

        DEPRECATED -- use self.sites.add()
        

        >>> import music21
        >>> class Mock(music21.Music21Object): 
        ...     attr1 = 234
        >>> aObj = Mock()
        >>> aObj.attr1 = 'test'
        >>> a = music21.Music21Object()
        >>> a.sites.add(aObj)
        >>> a.getContextAttr('attr1')
        'test'
        '''
        return self.sites.add(obj)

    def hasContext(self, obj):
        '''
        Return a Boolean if an object reference is stored 
        in the object's Sites object.

        This checks both all locations as well as all sites. 

        >>> import music21
        >>> class Mock(music21.Music21Object): 
        ...     attr1 = 234
        >>> aObj = Mock()
        >>> aObj.attr1 = 'test'
        >>> a = music21.Music21Object()
        >>> a.sites.add(aObj)
        >>> a.hasContext(aObj)
        True
        >>> a.hasContext(None)
        True
        >>> a.hasContext(45)
        False
        '''
        for dc in self.sites.get(): # get all
            if obj == dc:
                return True
        return False

    def addLocation(self, site, offset):
        '''
        
        DEPRECATED: use self.sites.add(site, offset)
        
        Add a location to the :class:`~music21.base.Sites` object. 
        The supplied object is a reference to the object (the site) that 
        contains an offset of this object.  For example, if this 
        Music21Object was Note, the site would be a Stream (or Stream 
        subclass) and the offset would be a number for the offset. 

        This is only for advanced location method and is not a complete 
        or sufficient way to add an object to a Stream. 

        >>> from music21 import note, stream
        >>> s = stream.Stream()
        >>> n = note.Note('E-5')
        >>> n.sites.add(s, 10)
        '''
        self.sites.add(site, offset)

    def getSites(self, idExclude=None):
        '''
        DEPRECATED: use self.sites.getSites() instead...
        
        Return a list of all objects that store 
        a location for this object. Will include None, 
        the default empty site placeholder. 

        If `idExclude` is provided, matching site ids will not be returned.

        >>> from music21 import note, stream
        >>> s1 = stream.Stream()
        >>> s2 = stream.Stream()
        >>> n = note.Note()
        >>> s1.append(n)
        >>> s2.append(n)
        >>> n.getSites() == [None, s1, s2]
        True
        '''
        return self.sites.getSites(idExclude=idExclude)

    def getSiteIds(self):
        '''
        DEPRECATED: use self.sites.getSiteIds() instead.

        Return a list of all site Ids, or the 
        id() value of the sites of this object. 
        '''
        return self.sites.getSiteIds()

    def hasSite(self, other):
        '''
        Return True if other is a site in this Music21Object

        
        >>> s = stream.Stream()
        >>> n = note.Note()
        >>> s.append(n)
        >>> n.hasSite(s)
        True
        >>> n.hasSite(stream.Stream())
        False
        '''
        return id(other) in self.sites.getSiteIds()

#    def getCommonSiteIds(self, other):
#        '''
#        Given another music21 object, return a 
#        list of all common site ids. Do not include 
#        the default empty site, None. 
#
#        >>> from music21 import note, stream
#        >>> s1 = stream.Stream()
#        >>> s2 = stream.Stream()
#        >>> n1 = note.Note()
#        >>> n2 = note.Note()
#        >>> s1.append(n1)
#        >>> s1.append(n2)
#        >>> s2.append(n2)
#        >>> n1.getCommonSiteIds(n2) == [id(s1)]
#        True
#        >>> s2.append(n1)
#        >>> n1.getCommonSiteIds(n2) == [id(s1), id(s2)]
#        True
#        '''
#        src = self.getSiteIds()
#        dst = other.getSiteIds()
#        post = []
#        for i in src:
#            if i is None:
#                continue
#            if i in dst:
#                post.append(i)
#        return post

#    def getCommonSites(self, other):
#        '''
#        Given another object, return a list of all sites
#        in common between the two objects. 
#
#        >>> from music21 import note, stream
#        >>> s1 = stream.Stream()
#        >>> s2 = stream.Stream()
#        >>> n1 = note.Note()
#        >>> n2 = note.Note()
#        >>> s1.append(n1)
#        >>> s1.append(n2)
#        >>> s2.append(n2)
#        >>> n1.getCommonSites(n2) == [s1]
#        True
#        >>> s2.append(n1)
#        >>> n1.getCommonSites(n2) == [s1, s2]
#        True
#
#        '''
#        src = self.getSites()
#        dstIds = other.getSiteIds()
#        post = []
#        for obj in src:
#            if obj is None:
#                continue
#            if id(obj) in dstIds:
#                post.append(obj)
#        return post

    def hasSpannerSite(self):
        '''
        DEPRECATED: use self.sites.hasSpannerSite()
        
        Return True if this object is found in 
        any Spanner (i.e. has any spanners attached). 
        This is determined by looking 
        for a SpannerStorage Stream class as a Site.

        
        >>> n1 = note.Note()
        >>> n2 = note.Note()
        >>> n3 = note.Note()
        >>> sp1 = spanner.Slur(n1, n2)
        >>> n1.getSpannerSites() == [sp1]
        True
        >>> sp2 = spanner.Slur(n2, n1)
        >>> n1.hasSpannerSite()
        True
        >>> n2.hasSpannerSite()
        True
        >>> n3.hasSpannerSite()
        False
        '''
        return self.sites.hasSpannerSite()


    def getSpannerSites(self, spannerClassList = None):
        '''
        
        Return a list of all :class:`~music21.spanner.Spanner` objects 
        (or Spanner subclasses) that contain 
        this element. This method provides a way for 
        objects to be aware of what Spanners they 
        reside in. Note that Spanners are not Streams 
        but specialized Music21Objects that use a  
        Stream subclass, SpannerStorage, internally to keep track
        of the elements that are spanned.

        
        >>> n1 = note.Note('C4')
        >>> n2 = note.Note('D4')
        >>> sp1 = spanner.Slur(n1, n2)
        >>> n1.getSpannerSites() == [sp1]
        True
        
        Note that not all Spanners are in the spanner module. They
        tend to reside in modules closer to their musical function:
        
        >>> sp2 = dynamics.Crescendo(n2, n1)
        >>> n2.getSpannerSites() == [sp1, sp2]
        True
        
        Optionally a class name or list of class names can be
        specified and only Spanners of that class will be returned
        
        >>> sp3 = dynamics.Diminuendo(n1, n2)
        >>> n2.getSpannerSites('Diminuendo') == [sp3]
        True
        
        A larger class name can be used to get all subclasses:
        
        >>> n2.getSpannerSites('DynamicWedge') == [sp2, sp3]
        True
        >>> n2.getSpannerSites(['Slur','Diminuendo']) == [sp1, sp3]
        True
        
        The order spanners are returned is generally the order that they were
        added, but that is not guaranteed, so for safety sake, use set comparisons:
        
        >>> set(n2.getSpannerSites(['Slur','Diminuendo'])) == set([sp3, sp1])
        True
        
        
        Example: see which pairs of notes are in the same slur.
        
        >>> n3 = note.Note('E4')
        >>> sp4 = spanner.Slur(n1, n3)
        
        >>> for n in [n1, n2, n3]:
        ...    for nOther in [n1, n2, n3]:
        ...        if n is nOther:
        ...            continue
        ...        nSlurs = n.getSpannerSites('Slur')
        ...        nOtherSlurs = nOther.getSpannerSites('Slur')
        ...        for thisSlur in nSlurs:
        ...            if thisSlur in nOtherSlurs:
        ...               print("%s shares a slur with %s" % (n.name, nOther.name))
        C shares a slur with D
        C shares a slur with E
        D shares a slur with C
        E shares a slur with C
        '''
        found = self.sites.getSitesByClass('SpannerStorage')
        post = []
        if spannerClassList is not None:
            if not common.isListLike(spannerClassList):
                spannerClassList = [spannerClassList]
                
        for obj in found:
            if spannerClassList is None:
                post.append(obj.spannerParent)
            else:
                for spannerClass in spannerClassList:
                    if spannerClass in obj.spannerParent.classes:
                        post.append(obj.spannerParent)
                        break
                     
        return post


    def hasVariantSite(self):
        '''
        Return True if this object is found in 
        any Variant
        This is determined by looking 
        for a VariantStorage Stream class as a Site.

        
        >>> n1 = note.Note()
        >>> n2 = note.Note()
        >>> n3 = note.Note()
        >>> v1 = variant.Variant([n1, n2])
        >>> n1.hasSpannerSite()
        False
        >>> n1.hasVariantSite()
        True
        >>> n2.hasVariantSite()
        True
        >>> n3.hasVariantSite()
        False
        '''
        return self.sites.hasVariantSite()

    def removeLocationBySite(self, site):
        '''
        TO-BE DEPRECATED: use self.sites.remove() instead and set activeSite
        manually.
        
        Remove a location in the :class:`~music21.base.Sites` object.

        This is only for advanced location method and
        is not a complete or sufficient way to remove an object from a Stream. 

        >>> from music21 import note, stream
        >>> s = stream.Stream()
        >>> n = note.Note()
        >>> n.sites.add(s, 10)
        >>> n.activeSite = s
        >>> n.removeLocationBySite(s)
        >>> n.activeSite == None
        True
        '''
        if not self.sites.isSite(site):
            raise Music21ObjectException('supplied site (%s) is not a site in this object: %s' % (site, self))
        #environLocal.printDebug(['removed location by site:', 'self', self, 'site', site])
        self.sites.remove(site)

        # if activeSite is set to that site, reassign to None
        if self._getActiveSite() == site:
            self._setActiveSite(None)


    def removeLocationBySiteId(self, siteId):
        '''
        DEPRECATED -- use sites.removeById and set activeSite manually.
        
        Remove a location in the 
        :class:`~music21.base.Sites` object by id.

        >>> from music21 import note, stream
        >>> s = stream.Stream()
        >>> n = note.Note()
        >>> n.sites.add(s, 10)
        >>> n.activeSite = s
        >>> n.removeLocationBySiteId(id(s))
        >>> n.activeSite == None
        True
        '''
        self.sites.removeById(siteId)
        p = self._getActiveSite()
        if p != None and id(p) == siteId:
            self._setActiveSite(None)


    def purgeOrphans(self, excludeStorageStreams=True):
        '''
        A Music21Object may, due to deep copying or other reasons, 
        have contain a site (with an offset); yet, that site may 
        no longer contain the Music21Object. These lingering sites 
        are called orphans. This methods gets rid of them. 

        The `excludeStorageStreams` are SpannerStorage and VariantStorage.
        '''
        #environLocal.printDebug(['purging orphans'])
        orphans = []
        # TODO: how can this be optimized to not use getSites, so as to 
        # not unwrap weakrefs?
        for s in self.sites.getSites():
            # of the site does not actually have this Music21Object in 
            # its elements list, it is an orphan and should be removed
            # note: this permits non-site context Streams to continue
            if s is None: 
                continue
            if s.isStream and not s.hasElement(self):
                if excludeStorageStreams:
                    # only get those that are not Storage Streams
                    if ('SpannerStorage' not in s.classes 
                        and 'VariantStorage' not in s.classes):
                        #environLocal.printDebug(['removing orphan:', s])
                        orphans.append(id(s))
                else: # get all 
                    orphans.append(id(s))
        for i in orphans:        
            self.removeLocationBySiteId(i)


#    def purgeUndeclaredIds(self, declaredIds, excludeStorageStreams=True):
#        '''
#        TODO- remove...
#        
#        Remove all sites except those that are declared with 
#        the `declaredIds` list. 
#
#        The `excludeStorageStreams` are SpannerStorage and VariantStorage.
#
#        This method is used in Stream serialization to remove 
#        lingering sites that are the result of temporary Streams. 
#        
#        TODO: Test!
#        '''
#        orphans = []
#        # TODO: this can be optimized to get actually get sites
#        for s in self.sites.getSites():
#            if s is None: 
#                continue
#            idTarget = id(s)
#            if idTarget in declaredIds: # skip all declared ids
#                continue # do nothing
#            if s.isStream:
#                if excludeStorageStreams:
#                    # only get those that are not Storage Streams
#                    if ('SpannerStorage' not in s.classes 
#                        and 'VariantStorage' not in s.classes):
#                        #environLocal.printDebug(['removing orphan:', s])
#                        orphans.append(idTarget)
#                else: # get all 
#                    orphans.append(idTarget)
#
#        for i in orphans:   
#            #environLocal.printDebug(['purgeingUndeclaredIds', i])     
#            self.removeLocationBySiteId(i)        


    def purgeLocations(self, rescanIsDead=False):
        '''
        Remove references to all locations in objects that no longer exist.
        '''
        # NOTE: this method is overridden on Spanner and and Variant
        self.sites.purgeLocations(rescanIsDead=rescanIsDead)


#     def removeNonContainedLocations(self):
#         '''Remove all locations in which this object does not 
#         actually reside as an element.
#         '''
#         self.sites.removeNonContainedLocations()


    def getContextByClass(self, className, serialReverseSearch=True,
            callerFirst=None, sortByCreationTime=False, prioritizeActiveSite=True, getElementMethod='getElementAtOrBefore', 
            memo=None):
        '''
        A very powerful method in music21 of fundamental importance:
        Returns the element matching the className that is closest to this
        element in its current hierarchy.  For instance, take this stream of
        changing time signatures:
        
        
        >>> s1 = converter.parse('tinynotation: 3/4 C4 D E 2/4 F G A B 1/4 c')
        >>> s2 = s1.makeMeasures()
        >>> s2.show('t')
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.clef.BassClef>
            {0.0} <music21.meter.TimeSignature 3/4>
            {0.0} <music21.note.Note C>
            {1.0} <music21.note.Note D>
            {2.0} <music21.note.Note E>
        {3.0} <music21.stream.Measure 2 offset=3.0>
            {0.0} <music21.meter.TimeSignature 2/4>
            {0.0} <music21.note.Note F>
            {1.0} <music21.note.Note G>
        {5.0} <music21.stream.Measure 3 offset=5.0>
            {0.0} <music21.note.Note A>
            {1.0} <music21.note.Note B>
        {7.0} <music21.stream.Measure 4 offset=7.0>
            {0.0} <music21.meter.TimeSignature 1/4>
            {0.0} <music21.note.Note C>
            {1.0} <music21.bar.Barline style=final>
        
        
        Let's get the last two notes of the piece, the B and high c:
        
        >>> c = s2.measure(4).notes[0]
        >>> c
        <music21.note.Note C>
        
        >>> b = s2.measure(3).notes[-1]
        >>> b
        <music21.note.Note B>
        
        Now when we run `getContextByClass('TimeSignature')` on c, we get a
        time signature of 1/4.  
        
        >>> c.getContextByClass('TimeSignature')
        <music21.meter.TimeSignature 1/4>
        
        Doing what we just did wouldn't be hard to do with other methods,
        though `getContextByClass` makes it easier.  But the time signature 
        context for b would be much harder to get without this method, since
        in order to do it, it searches backwards within the measure, finds that
        there's nothing there.  It goes to the previous measure and searches that
        one backwards until it gets the proper TimeSignature of 2/4:
        
        >>> b.getContextByClass('TimeSignature')
        <music21.meter.TimeSignature 2/4>
        
        The method is smart enough to stop when it gets to the beginning of the
        part.  This is all you need to know for most uses.  The rest of the docs
        are for advanced uses:        
        
        The methods searches both Sites as well as associated objects 
        to find a matching class. Returns None if not match is found. 

        The a reference to the caller is required to find the offset of the 
        object of the caller. This is needed for serialReverseSearch.

        The caller may be a Sites reference from a lower-level object.
        If so, we can access the location of that lower-level object. However, 
        if we need a flat representation, the caller needs to be the source 
        Stream, not its Sites reference.

        The `callerFirst` is the first object from which this method 
        was called. This is needed in order to determine the final offset from which to search. 

        The `prioritizeActiveSite` parameter searches the object's activeSite 
        before any other object. By default this is True

        The `getElementMethod` is a string that selects which Stream method is used to 
        get elements for searching. The strings 'getElementAtOrBefore' and 'getElementBeforeOffset' are currently accepted. 
        '''
        #if DEBUG_CONTEXT: print 'X: first call; looking for:', className, id(self), self

        #environLocal.printDebug(['call getContextByClass from:', self, 'activeSite:', self.activeSite, 'callerFirst:', callerFirst, 'prioritizeActiveSite', prioritizeActiveSite])
    
        # this method will be called recursively on all object levels, ascending
        # thus, to do serial reverse search we need to 
        # look at activeSite.flat and track back to first encountered class match
        if prioritizeActiveSite:
            priorityTarget = self.activeSite
        else:
            priorityTarget = None

        if callerFirst is None: # this is the first caller
            callerFirst = self
        elif isinstance(callerFirst, Sites):
            # if caller first is Sites, nothing to do here
            return None

        if memo is None:
            memo = {} # intialize
            #if DEBUG_CONTEXT: print 'X: creating new memo'        
        #printMemo(memo, 'getContextByClass called by: %s %s' % (id(self), self))
        #if DEBUG_CONTEXT: print 'X: memo:', [(key, memo[key]) for key in memo]

        post = None
        # first, if this obj is a Stream, we see if the class exists at or
        # before where the offsetOfCaller

        #if DEBUG_CONTEXT: print '\tX: entering if serialReverseSearch'
        if serialReverseSearch:
            # if this is a Stream and we have a caller, see if we 
            # can get the offset from within this Stream of the caller 
            # first, see if this element is even in this Stream     
            getOffsetOfCaller = False
            skipGetOffsetOfCaller = False
            #if (hasattr(self, "elements") and callerFirst is not None): 
            #if self.isStream and callerFirst is not None: 

#             if (self.isStream and callerFirst is not None and not 
#                 isinstance(callerFirst, Sites)): 
            if (self.isStream and callerFirst is not None): 

                # memo check above is needed for string operational contexts
                # where cached semiFlat generation raises an error

                # find the offset of the callerFirst
                # if this is a Stream, we need to find the offset relative
                # to this Stream; it may only be available within a semiFlat
                # representaiton

                # this semiFlat name will be used in the getOffsetOfCaller 
                # branch below

                #environLocal.printDebug(['getContextByClass, serialReverseSearch', 'requesting semi flat from self:', self, id(self)])

                #if DEBUG_CONTEXT: print '\tX: getting semiFlat because self is Stream'

                # using the cached semiFlat here can lead to an ever-
                # increasing number of sites in the outermost semiflat
                # lower level containers each gain a new site (self here)  
                # for example, each Measure in a Part that caches a semiflat
                # each Measure will have a new site for every call; thus
                # we delete the semiflat here used after every call
                #semiFlat = self.semiFlat
                semiFlat = self._getFlatOrSemiFlat(retainContainers=True)

                # see if this element is in this Stream; 
                if not skipGetOffsetOfCaller:
                    if semiFlat.hasElement(callerFirst): 
                        getOffsetOfCaller = True
                    else:
                        #if (hasattr(callerFirst, 'flattenedRepresentationOf') and callerFirst.flattenedRepresentationOf is not None):
                        if (callerFirst.isStream and 
                            callerFirst.flattenedRepresentationOf is not None):
                            if semiFlat.hasElement(
                                callerFirst.flattenedRepresentationOf):
                                getOffsetOfCaller = True

            if getOffsetOfCaller:
                # in some cases we may need to try to get the offset of a semiFlat representation. this is necessary when a Measure
                # is the caller. 
                #if DEBUG_CONTEXT: print '\tX: getting offset of caller'

                #environLocal.printDebug(['getContextByClass(): trying to get offset of caller from a semi-flat representation', 'self', self, self.id, 'callerFirst', callerFirst, callerFirst.id])

                #offsetOfCaller = semiFlat.getOffsetByElement(callerFirst)
                # TODO: use this, as should be faster
                try:
                    offsetOfCaller = callerFirst.getOffsetBySite(semiFlat)
                except SitesException:
                    offsetOfCaller = None

                # our caller might have been flattened after contexts were set
                # thus, this object may be in the caller's defined contexts, 
                # but this object knows nothing about a flat version of the 
                # caller (it cannot get an offset of the caller, which we need
                # to do the serial reverse search)
                #if offsetOfCaller is None and hasattr(
                #    callerFirst, 'flattenedRepresentationOf'):
                if offsetOfCaller is None and callerFirst.isStream:
                    #environLocal.printDebug(['getContextByClass(): trying to get offset of caller from the callers flattenedRepresentationOf attribute', 'self', self, 'callerFirst', callerFirst])

                    # Thanks Johannes Emerich [public@johannes.emerich.de] !
                    if callerFirst.flattenedRepresentationOf is not None:
                        unFlat = callerFirst.flattenedRepresentationOf
                        offsetOfCaller = semiFlat.getOffsetByElement(unFlat)

                # if the offset has been found, get element at or before
                # this offset
                if offsetOfCaller is not None:
                    # NOTE: if there are two elements of the same class here
                    # we are getting based only sort order, which may not be 
                    # what we want
                    if getElementMethod == 'getElementAtOrBefore':
                        post = semiFlat.getElementAtOrBefore(offsetOfCaller, 
                               [className])
                    elif getElementMethod == 'getElementBeforeOffset':
                        #environLocal.printDebug(['getContextByClass(): using getElementsBeforeOffset'])
                        post = semiFlat.getElementBeforeOffset(offsetOfCaller, 
                               [className])
                    else:
                        raise Music21ObjectException('cannot get element with requested method: %s' % getElementMethod)
                #environLocal.printDebug([self, 'results of serialReverseSearch:', post, '; searching for:', className, '; starting from offset', offsetOfCaller])

                # NOTE: deleting this semiFlat is critical, is it prohibits 
                # lower level components retaining this stream as a new site
                # on successive calls
                del semiFlat

        #if DEBUG_CONTEXT: print '\tX: about to call getByClass'
        if post is None: # still no match
            # this will call this method on all defined contexts, including
            # locations (one of which must be the activeSite)
            # if this is a stream, this will be the next level up, recursing
            # a reference to the callerFirst is continuall passed
            post = self.sites.getByClass(className,
                   serialReverseSearch=serialReverseSearch,
                   callerFirst=callerFirst, sortByCreationTime=sortByCreationTime, 
                   # make the priorityTarget the activeSite, meaning we search
                   # this object first
                   prioritizeActiveSite=prioritizeActiveSite, 
                   priorityTarget=priorityTarget,  getElementMethod=getElementMethod, memo=memo)
    
        # if we have a Stream, store the results
#         if self.isStream and isinstance(className, str):
#             if self._cache['contextCache'] is None:
#                 self._cache['contextCache'] = contextCache.ContextCache()
#             self._cache['contextCache'].add(className, callerFirst, 
#                                             getElementMethod, post)

        return post



    def getAllContextsByClass(self, className, found=None, idFound=None,
                             memo=None):
        '''
        Search both Sites as well as associated 
        objects to find all matchinging classes. 
        Returns [] if not match is found. 
        '''
        if memo is None:
            memo = {} # intialize
        if found == None:
            found = []
        if idFound == None:
            idFound = []

        #post = None
        # if this obj is a Stream
        if self.isStream:
        #if hasattr(self, "elements"): 
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
        self.sites.getAllByClass(className, found=found,
                                         idFound=idFound, memo=memo)
        return found


    #---------------------------------------------------------------------------
    def _adjacentObject(self, site, classFilterList=None, ascend=True, 
                        beginNearest=True):
        '''
        Core method for finding adjacent objects given a single site. 
            
        The `site` argument is a Stream that contains this 
        element. The index of this element if sound in this site, 
        and either the next or previous element, if found, is returned.

        If `ascend` is True index values are 
        incremented; if False, index values are decremented.
    
        If `beginNearest` is True, index values are searched based 
        on those closest to the caller; if False, the search is 
        done in reverse, from the most remote index toward the caller. 
        This may be useful as an optimization when looking for elements that are far from the caller. 

        The `classFilterList` may specify one or more classes as targets.
        '''
        siteLength = len(site)
        # get another list to avoid function calls
        siteElements = site.elements
        # special optimization for class selection when a single str class
        # is given
        if (classFilterList is not None and len(classFilterList) == 1 and 
            isinstance(classFilterList[0], str)):
            if not site.hasElementOfClass(classFilterList[0]):
                return None
        # go to right, start at nearest
        if ascend and beginNearest:
            currentIndex = site.index(self) + 1 # start with next
            while (currentIndex < siteLength):
                nextObj = siteElements[currentIndex]
                if classFilterList is not None: 
                    if nextObj.isClassOrSubclass(classFilterList):
                        return nextObj
                else:
                    return nextObj
                currentIndex += 1
        # go to right, start at righmost
        elif ascend and not beginNearest:
            lastIndex = site.index(self) + 1 # end with next
            currentIndex = siteLength
            while (currentIndex >= lastIndex):
                nextObj = siteElements[currentIndex]
                if classFilterList is not None:
                    if nextObj.isClassOrSubclass(classFilterList):
                        return nextObj
                else:
                    return nextObj
                currentIndex -= 1
        # go to left, start at nearest
        elif not ascend and beginNearest:
            currentIndex = site.index(self) - 1 # start with next
            while (currentIndex >= 0):
                nextObj = siteElements[currentIndex]
                if classFilterList is not None: 
                    if nextObj.isClassOrSubclass(classFilterList):
                        return nextObj
                else:
                    return nextObj
                currentIndex -= 1
        # go to left, start at leftmost
        elif not ascend and not beginNearest:
            lastIndex = site.index(self) - 1 # start with next
            currentIndex = 0
            while (currentIndex <= lastIndex):
                nextObj = siteElements[currentIndex]
                if classFilterList is not None:
                    if nextObj.isClassOrSubclass(classFilterList):
                        return nextObj
                else:
                    return nextObj
                currentIndex += 1
        else:
            raise Music21ObjectException('bad organization of ascend and beginNearest parameters')
        # if nothing found, return None
        return None

    def _adjacencySearch(self, classFilterList=None, ascend=True, 
        beginNearest=True, flattenLocalSites=False):
        '''Get the next or previous element if this element is in a Stream. 

        If this element is in multiple Streams, the first next element found in any site will be returned. If not found no next element is found in any site, the flat representation of all sites of each immediate site are searched. 

        If `beginNearest` is True, sites will be searched from the element nearest to the caller and then outward. 
        '''
        if classFilterList is not None:
            if not common.isListLike(classFilterList):
                classFilterList = [classFilterList]
        sites = self.sites.getSites(excludeNone=True)
        match = None

        # store ids of of first sites; might need to take flattened version
        firstSites = []
        for s in sites:
            firstSites.append(id(s))
        # this might use get(sortByCreationTime)
        #environLocal.printDebug(['sites:', sites])
        #siteSites = []

        # first, look in sites that are do not req flat presentation
        # these do not need to be flattened b/c we know the self is in these
        # streams
        memo = {}
        while len(sites) > 0:
            #environLocal.printDebug(['looking at siteSites:', s])
            # check for duplicated sites; may be possible
            s = sites.pop(0) # take the first off of sites
            try:
                memo[id(s)]
                continue # if in dict, do not continue
            except KeyError: # if not in dict
                memo[id(s)] = None # add to dict, value does not matter

            if id(s) in firstSites:
                if flattenLocalSites:
                    if s.isFlat:
                        target = s
                    else:
                        target = s.semiFlat
                else: # do not flatten first sites
                    target = s
                    # add semi flat to sites, as we have not searched it yet
                    sites.append(s.semiFlat)
                firstSites.pop(firstSites.index(id(s))) # remove for efficiency
            # if flat, do not get semiFlat
            # note that semiFlat streams are marked as isFlat=True
            elif s.isFlat:
                target = s
            else: # normal site
                target = s.semiFlat
            # use semiflat of site
            match = self._adjacentObject(target, 
                    classFilterList=classFilterList, ascend=ascend, 
                    beginNearest=beginNearest)
            if match is not None:
                return match
            # append new sites to end of queue
            # these are the sites of s, not target
            sites += s.sites.getSites(excludeNone=True)
        # if cannot be found, return None
        return None            
        

    def next(self, classFilterList=None, flattenLocalSites=False, 
        beginNearest=True):
        '''
        Get the next element found in a the activeSite (or other Sites)
        of this Music21Object. 

        The `classFilterList` can be used to specify one or more classes to match.

        The `flattenLocalSites` parameter determines if the sites of this element (e.g., a Measure's Part) are flattened on first search. When True, elements contained in adjacent containers may be selected first. 

        
        >>> s = corpus.parse('bwv66.6')
        >>> s.parts[0].measure(3).next() == s.parts[0].measure(4)
        True
        >>> s.parts[0].measure(3).next('Note', flattenLocalSites=True) == s.parts[0].measure(3).notes[0]
        True
        '''
        return self._adjacencySearch(classFilterList=classFilterList, 
                                    ascend=True, beginNearest=beginNearest, flattenLocalSites=flattenLocalSites)
                        
    def previous(self, classFilterList=None, flattenLocalSites=False,
        beginNearest=True):
        '''
        Get the previous element found in the activeSite or other .sites of this 
        Music21Object. 

        The `classFilterList` can be used to specify one or more classes to match.

        The `flattenLocalSites` parameter determines if the sites of this element (e.g., a Measure's Part) are flattened on first search. When True, elements contained in adjacent containers may be selected first. 

        
        >>> s = corpus.parse('bwv66.6')
        >>> s.parts[0].measure(3).previous() == s.parts[0].measure(2)
        True
        >>> s.parts[0].measure(3).previous('Note', flattenLocalSites=True) == s.parts[0].measure(2).notes[-1]
        True
        '''
        return self._adjacencySearch(classFilterList=classFilterList, 
                                    ascend=False, beginNearest=beginNearest, flattenLocalSites=flattenLocalSites)


    #---------------------------------------------------------------------------
    # properties

    def _getActiveSite(self):
        # can be None
        if WEAKREF_ACTIVE:
            if self._activeSite is None: #leave None
                return self._activeSite
            else: # even if current activeSite is not a weakref, this will work
                #environLocal.printDebug(['_getActiveSite() called:', 'self._activeSite', self._activeSite])
                return common.unwrapWeakref(self._activeSite)
        else:
            return self._activeSite
    
    def _setActiveSite(self, site):
        #environLocal.printDebug(['_setActiveSite() called:', 'self', self, 'site', site])

        # NOTE: this is a performance intensive call
        if site is not None: 
            siteId = id(site)
            # check that the activeSite is not already set to this object
            # this avoids making another weakref
            if self._activeSiteId == siteId:
                return
            if not self.sites.hasSiteId(siteId):
                self.sites.add(site, self.offset, idKey=siteId) 
        else:
            siteId = None

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
        doc='''       
        A reference to the most-recent object used to 
        contain this object. In most cases, this will be a 
        Stream or Stream sub-class. In most cases, an object's 
        activeSite attribute is automatically set when an the 
        object is attached to a Stream.
        
        
        >>> n = note.Note("C#4")
        >>> p = stream.Part()
        >>> p.insert(20.0, n)
        >>> n.activeSite is p
        True
        >>> n.offset
        20.0
        
        >>> m = stream.Measure()
        >>> m.insert(10.0, n)
        >>> n.activeSite is m
        True
        >>> n.offset
        10.0
        >>> n.activeSite = p
        >>> n.offset
        20.0
        
        DEVELOPER N.B. -- the guts of this call will
        be moved to .sites soon.
        ''')

    def _getOffset(self):
        '''Get the offset for the activeSite.
        
        
        >>> n = note.Note()
        >>> m = stream.Measure()
        >>> m.id = 'm1'
        >>> m.insert(3.0, n)
        >>> n.activeSite is m
        True
        >>> n.offset
        3.0

        Still works...
        
        >>> n._activeSiteId = 3234234
        >>> n.offset
        3.0
        
        There is a branch that does slow searches.  
        See test/testSerialization to have it active.
        '''
        #there is a problem if a new activeSite is being set and no offsets have 
        # been provided for that activeSite; when self.offset is called, 
        # the first case here would match
        #environLocal.printDebug(['Music21Object._getOffset', 'self.id', self.id, 'id(self)', id(self), self.__class__])

        activeSiteId = None
        if self.activeSite is not None:
            activeSiteId = id(self.activeSite)
            self._activeSiteId = id(self.activeSite)
        elif self._activeSiteId is not None:
            activeSiteId = self._activeSiteId
        
        if (activeSiteId is not None and 
            self.sites.hasSiteId(activeSiteId)):
            return self.sites.getOffsetBySiteId(activeSiteId)
            #return self.sites.coordinates[activeSiteId]['offset']
        elif self.activeSite is None: # assume we want self
            return self.sites.getOffsetBySite(None)
        else:
            # try to look for it in all objects
            environLocal.printDebug(['doing a manual activeSite search: probably means that id(self.activeSite) (%s) is not equal to self._activeSiteId (%r)' % (id(self.activeSite), self._activeSiteId)])
            #environLocal.printDebug(['activeSite', self.activeSite, 'self.sites.hasSiteId(activeSiteId)', self.sites.hasSiteId(activeSiteId)])
            #environLocal.printDebug(['self.hasSite(self.activeSite)', self.hasSite(self.activeSite)])

            offset = self.sites.getOffsetByObjectMatch(
                    self.activeSite)
            return offset

            #environLocal.printDebug(['self.sites', self.sites._definedContexts])
        raise Exception('request within %s for offset cannot be made with activeSite of %s (id: %s)' % (self.__class__, self.activeSite, activeSiteId))            

    def _setOffset(self, value):
        '''
        Set the offset for the activeSite. 
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
        # of activeSite
        self.sites.setOffsetBySiteId(self._activeSiteId, offset) 

    
    offset = property(_getOffset, _setOffset, 
        doc = '''
        The offset property sets or returns the position of this object 
        (generally in `quarterLengths`) from the start of its `activeSite`,
        that is, the most recently referenced `Stream` or `Stream` subclass such
        as `Part`, `Measure`, or `Voice`.  It is a simpler
        way of calling `o.getOffsetBySite(o.activeSite)`.

        If we put a `Note` into a `Stream`, we will see the activeSite changes.

        
        >>> n1 = note.Note("D#3")
        >>> n1.activeSite is None
        True
        
        >>> m1 = stream.Measure()
        >>> m1.number = 4
        >>> m1.insert(10.0, n1)
        >>> n1.offset
        10.0
        >>> n1.activeSite
        <music21.stream.Measure 4 offset=0.0>

        >>> n1.activeSite is m1
        True
        
        The most recently referenced `Stream` becomes an object's `activeSite` and 
        thus the place where `.offset` looks to find its number.  
        
        >>> m2 = stream.Measure()
        >>> m2.insert(20.0, n1)
        >>> m2.number = 5
        >>> n1.offset
        20.0
        >>> n1.activeSite is m2
        True

        Notice though that `.offset` depends on the `.activeSite` which is the most 
        recently accessed/referenced Stream.
        
        Here we will iterate over the `elements` in `m1` and we
        will see that the `.offset` of `n1` now is its offset in
        `m1` even though we haven't done anything directly to `n1`.
        Simply iterating over a site is enough to change the `.activeSite`
        of its elements:
        
        >>> for element in m1:
        ...     pass
        >>> n1.offset
        10.0 

        
        The property can also set the offset for the object if no 
        container has been set:

        
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

        After calling `getElementById` on `s1`, the
        returned element's `offset` will be its offset in `s1`.

        >>> n2 = s1.getElementById('hi')
        >>> n2 is n1
        True
        >>> n2.offset
        0.0

        Iterating over the elements in a Stream will
        make its `offset` be the offset in iterated
        Stream.

        >>> for thisElement in s2:
        ...     print thisElement.offset
        30.5
        
        When in doubt, use `.getOffsetBySite(streamObj)`
        which is safer.
        ''')


    def _getDuration(self):
        '''
        Gets the DurationObject of the object or None
        '''
        from music21 import duration
        # lazy duration creation
        if self._duration is None:
            self._duration = duration.Duration(0)
        return self._duration

    def _setDuration(self, durationObj):
        '''
        Set the duration as a quarterNote length
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
        doc = '''
        Get and set the duration of this object as a Duration object.
        ''')


    def _getIsGrace(self):
        return self.duration.isGrace

    isGrace = property(_getIsGrace, doc = '''
        Return True or False if this music21 object has a GraceDuration.

        
        >>> n = note.Note()
        >>> n.isGrace
        False
        >>> ng = n.getGrace()
        >>> ng.isGrace
        True
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
        doc = '''
        Get and set the priority integer value. 

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
        `music21.base.CLASS_SORT_ORDER`.  For instance, a key signature 
        change appears before a time signature change before a 
        note at the same offset.  This produces the familiar order of 
        materials at the start of a musical score.
        
        >>> import music21
        >>> a = music21.Music21Object()
        >>> a.priority = 3
        >>> a.priority = 'high'
        Traceback (most recent call last):
        ElementException: priority values must be integers.
        ''')

    

    #---------------------------------------------------------------------------
    # temporary storage setup routines; public interface

    def unwrapWeakref(self):
        '''
        Public interface to operation on Sites.

        NOTE: Any Music21Object subclass that 
        contains private Streams (like Spanner and Variant) must 
        override these methods.

        >>> import music21
        >>> aM21Obj = music21.Music21Object()
        >>> bM21Obj = music21.Music21Object()
        >>> aM21Obj.offset = 30
        >>> aM21Obj.getOffsetBySite(None)
        30.0
        >>> aM21Obj.sites.add(bM21Obj, 50)
        >>> aM21Obj.activeSite = bM21Obj
        >>> aM21Obj.unwrapWeakref()

        '''
        #environLocal.printDebug(['Music21Object: unwrapWeakref on:', self])

        self.purgeOrphans()

        # this purgesLocations too
        self.sites.unwrapWeakref()
        # doing direct access; not using property activeSite, as filters
        # through global WEAKREF_ACTIVE setting
        if self._activeSite is not None:
            self._activeSite = common.unwrapWeakref(self._activeSite)

        #environLocal.printDebug(['   self._activeSite:', self._activeSite])

    def wrapWeakref(self):
        '''
        Public interface to operation on Sites.

        >>> import music21
        >>> aM21Obj = music21.Music21Object()
        >>> bM21Obj = music21.Music21Object()
        >>> aM21Obj.offset = 30
        >>> aM21Obj.getOffsetBySite(None)
        30.0
        >>> aM21Obj.sites.add(bM21Obj, 50)
        >>> aM21Obj.activeSite = bM21Obj
        >>> aM21Obj.unwrapWeakref()
        >>> aM21Obj.wrapWeakref()
        '''
        self.sites.wrapWeakref()

        # doing direct access; not using property activeSite, as filters
        # through global WEAKREF_ACTIVE setting
        self._activeSite = common.wrapWeakref(self._activeSite)
        # this is done both here and in unfreezeIds()

    #---------------------------------------------------------------------------
    # display and writing

    def write(self, fmt=None, fp=None, **keywords): #pragma: no cover
        '''
        Write out a file of music notation (or an image, etc.) in a given format.  If
        fp is specified as a file path then the file will be placed there.  If it is not
        given then a temporary file will be created.
        
        If fmt is not given then the default of your Environment's 'writeFormat' will
        be used.  For most people that is musicxml.
        
        Returns the full path to the file.
        '''
        if fmt == None: # get setting in environment
            fmt = environLocal['writeFormat']
        elif fmt.startswith('.'):
            fmt = fmt[1:]
 
        fileFormat, ext = common.findFormat(fmt)
        if fileFormat not in common.VALID_WRITE_FORMATS:
            if fileFormat is None:
                raise Music21ObjectException('cannot support showing in this format yet: %s' % fmt)
            else:
                raise Music21ObjectException('cannot support showing in this format yet: %s' % fileFormat)


        if fileFormat is None:
            raise Music21ObjectException('bad format (%s) provided to write()' % fmt)

        if fileFormat == 'musicxml.png':
            ext = '.xml' # temporary change

        if fp is None:
            fp = environLocal.getTempFile(ext)

        if fileFormat in ['text', 'textline', 'musicxml', 'musicxml.png', 'vexflow', 'vexflow.html']:        
            if fileFormat == 'text':
                dataStr = self._reprText()
            elif fileFormat == 'textline':
                dataStr = self._reprTextLine()
                
            # musicxml, musicxml.png, etc.
            elif fileFormat.startswith('musicxml'):
                from music21.musicxml import m21ToString
                dataStr = m21ToString.fromMusic21Object(self)
            elif fileFormat.startswith('vexflow'):
                import music21.vexflow
                dataStr = music21.vexflow.fromObject(self, mode='html')

            f = open(fp, 'w')
            f.write(dataStr)
            f.close()
            
            if fileFormat == 'musicxml.png':
                # HACK
                import os
                musescoreFile = environLocal['musescoreDirectPNGPath']
                if musescoreFile == "":
                    raise Music21Exception("To create PNG files directly from MusicXML you need to download MuseScore")
                elif not os.path.exists(musescoreFile):
                    raise Music21Exception("Cannot find a path to the 'mscore' file at %s -- download MuseScore" % musescoreFile)
                
                fpOut = fp[0:len(fp) - 3]
                fpOut += "png"
                musescoreRun = musescoreFile + " " + fp + " -o " + fpOut
                if 'dpi' in keywords:
                    musescoreRun += " -r " + str(keywords['dpi'])
                if common.runningUnderIPython():
                    musescoreRun += " -r 72"

                storedStrErr = sys.stderr
                import StringIO
                fileLikeOpen = StringIO.StringIO()
                sys.stderr = fileLikeOpen
                os.system(musescoreRun)
                fileLikeOpen.close()
                sys.stderr = storedStrErr
                
                fp = fpOut[0:len(fpOut) - 4] + "-1.png"
                
            return fp

        elif fileFormat in ['braille', 'lily', 'lilypond']:
            if fileFormat in ['lilypond', 'lily']:
                import music21.lily.translate
                conv = music21.lily.translate.LilypondConverter()
                if 'coloredVariants' in keywords and keywords['coloredVariants'] is True:
                    conv.coloredVariants = True
                dataStr = conv.textFromMusic21Object(self).encode('utf-8')
            
            elif fileFormat == 'braille':
                import music21.braille
                dataStr = music21.braille.translate.objectToBraille(self)
            
            f = codecs.open(fp, mode='w', encoding='utf-8')
            f.write(dataStr)
            f.close()
            return fp

        elif fileFormat == 'midi':
            # returns a midi.MidiFile object
            from music21.midi import translate as midiTranslate
            mf = midiTranslate.music21ObjectToMidiFile(self)
            mf.open(fp, 'wb') # write binary
            mf.write()
            mf.close()
            return fp

        elif fileFormat in ['pdf', 'lily.pdf',]:
            if fp.endswith('.pdf'):
                fp = fp[:-4]
            from music21.lily import translate as lilyTranslate
            conv = lilyTranslate.LilypondConverter()
            if 'coloredVariants' in keywords and keywords['coloredVariants'] is True:
                conv.coloredVariants = True
            conv.loadFromMusic21Object(self)
            return conv.createPDF(fp)
        elif fileFormat in ['png', 'lily.png','ipython','ipython.png']:
            if fp.endswith('.png'):
                fp = fp[:-4]
            from music21.lily import translate as lilyTranslate # @Reimport
            conv = lilyTranslate.LilypondConverter()
            if 'coloredVariants' in keywords and keywords['coloredVariants'] is True:
                conv.coloredVariants = True
            conv.loadFromMusic21Object(self)
            convertedFilePath = conv.createPNG(fp)
            if fileFormat in ['ipython','ipython.png']:
                from music21.ipython21 import objects as ipythonObjects
                ipo = ipythonObjects.IPythonPNGObject(convertedFilePath)
                return ipo
            else:
                return convertedFilePath
        elif fileFormat in ['svg', 'lily.svg']:
            if fp.endswith('.svg'):
                fp = fp[:-4]
            from music21.lily import translate as lilyTranslate # @Reimport
            conv = lilyTranslate.LilypondConverter()
            if 'coloredVariants' in keywords and keywords['coloredVariants'] is True:
                conv.coloredVariants = True
            conv.loadFromMusic21Object(self)
            return conv.createSVG(fp)
        else:
            raise Music21ObjectException('cannot yet support writing in the %s format' % fileFormat)



    def _reprText(self):
        '''
        Return a text representation possible with line 
        breaks. This methods can be overridden by subclasses 
        to provide alternative text representations.
        '''
        return self.__repr__()

    def _reprTextLine(self):
        '''
        Return a text representation without line breaks. This 
        methods can be overridden by subclasses to provide 
        alternative text representations.
        '''
        return self.__repr__()

    def show(self, fmt=None, app=None, **keywords): #pragma: no cover
        '''
        Displays an object in a format provided by the 
        fmt argument or, if not provided, the format set in the user's Environment 

        Valid formats include (but are not limited to)::
            musicxml
            text
            midi
            lily (or lilypond)
            lily.png
            lily.pdf
            lily.svg
            braille
            vexflow
            musicxml.png

        N.B. score.write('lily') returns a bare lilypond file,
        score.show('lily') runs it through lilypond and displays it as a png.
        '''
        # note that all formats here must be defined in 
        # common.VALID_SHOW_FORMATS

        if fmt == None: # get setting in environment
            if common.runningUnderIPython():
                fmt = 'ipython'
            else:
                fmt = environLocal['showFormat']
        if common.isStr(fmt) != True:
            raise Music21ObjectException('format must be a string, not whatever this is: %s' % fmt)

        fileFormat, unused_ext = common.findFormat(fmt)
        if fileFormat not in common.VALID_SHOW_FORMATS:
            raise Music21ObjectException('cannot support showing in this format yet: %s' % fileFormat)

        # standard text presentation has line breaks, is printed
        if fileFormat == 'text':
            print(self._reprText())
        # a text line compacts the complete recursive representation into a 
        # single line of text; most for debugging. returned, not printed
        elif fileFormat == 'textline': 
            return self._reprTextLine()

        # TODO: these need to be updated to write files
        # TODO: the lilypondFormat is not yet consulted
        elif fmt in ['lily.pdf', 'pdf']:
            #return self.lily.showPDF()
            import music21.lily.translate
            conv = music21.lily.translate.LilypondConverter()
            if 'coloredVariants' in keywords and keywords['coloredVariants'] is True:
                conv.coloredVariants = True
            conv.loadFromMusic21Object(self)
            environLocal.launch('pdf', conv.createPDF(), app=app)
        elif fmt in ['lily.png', 'png', 'lily', 'lilypond']:
            # TODO check that these use environLocal 
            from music21.lily import translate as lilyTranslate
            conv = lilyTranslate.LilypondConverter()
            if 'coloredVariants' in keywords and keywords['coloredVariants'] is True:
                conv.coloredVariants = True
            conv.loadFromMusic21Object(self)
            return conv.showPNG()
        elif fmt in ['lily.svg', 'svg']:
            # TODO check that these use environLocal 
            from music21.lily import translate as lilyTranslate # @Reimport
            conv = lilyTranslate.LilypondConverter()
            if 'coloredVariants' in keywords and keywords['coloredVariants'] is True:
                conv.coloredVariants = True
            conv.loadFromMusic21Object(self)
            return conv.showSVG()
        elif fmt in ['ipython','ipython.png']:
            # same as write... ipython %load_ext ipython21/ipExtension.py takes care of this.
            return self.write(fileFormat)
            
        elif fmt in ['musicxml', 'midi']: # a format that writes a file
            returnedFilePath = self.write(fileFormat)
            environLocal.launch(fileFormat, returnedFilePath, app=app)
        elif fmt in ['musicxml.png']:
            returnedFilePath = self.write(fileFormat)
            if common.runningUnderIPython():
                from music21.ipython21 import objects as ipythonObjects
                ipo = ipythonObjects.IPythonPNGObject(returnedFilePath)
                return ipo
            else:
                environLocal.launch(fileFormat, returnedFilePath, app=app)
                

        elif fmt == 'braille':
            returnedFilePath = self.write(fileFormat)
            environLocal.launch(fileFormat, returnedFilePath, app=app)

        elif fmt.startswith('vexflow'):
            returnedFilePath = self.write(fileFormat)
            environLocal.launch(fileFormat, returnedFilePath, app=app)

        else:
            raise Music21ObjectException('no such show format is supported:', fmt)



    #---------------------------------------------------------------------------
    # duration manipulation, processing, and splitting

    def _getDerivationHierarchy(self):
        post = []
        focus = self
        endMe = 200
        while endMe > 0:
            endMe = endMe - 1 # do not go forever
            # collect activeSite unless activeSite is None;
            # if so, try to get rootDerivation
            candidate = focus.activeSite
            #environLocal.printDebug(['_getDerivationHierarchy(): activeSite found:', candidate])
            if candidate is None: # nothing more to derive
                # if this is a Stream, we might find a root derivation
                if hasattr(focus, 'rootDerivation'):
                    #environLocal.printDebug(['_getDerivationHierarchy(): found rootDerivation:', focus.rootDerivation])
                    alt = focus.rootDerivation
                    if alt is None:
                        return post
                    else:
                        candidate = alt
                else:
                    return post
            post.append(candidate)
            focus = candidate
        return post

    derivationHierarchy = property(_getDerivationHierarchy, 
        doc = '''
        Return a list of Stream subclasses that this Stream 
        is contained within. This provides a way of seeing 
        Streams contained within Streams.

        
        >>> s = corpus.parse('bach/bwv66.6')
        >>> [str(e.__class__) for e in s[1][2][3].derivationHierarchy]
        ["<class 'music21.stream.Measure'>", "<class 'music21.stream.Part'>", "<class 'music21.stream.Score'>"]
        ''')


    def splitAtQuarterLength(self, quarterLength, retainOrigin=True, 
        addTies=True, displayTiedAccidentals=False, delta=1e-06):
        '''
        Split an Element into two Elements at a provided 
        `quarterLength` (offset) into the Element.

        
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

        Make sure that ties remain as they should be:
        
        >>> d = note.Note('D#4')
        >>> d.duration.quarterLength = 3.0
        >>> d.tie = tie.Tie('start')
        >>> e, f = d.splitAtQuarterLength(2.0)
        >>> e.tie, f.tie
        (<music21.tie.Tie start>, <music21.tie.Tie continue>) 

        Should be the same for chords...
        
        >>> g = chord.Chord(['C4', 'E4', 'G4'])
        >>> g.duration.quarterLength = 3.0
        >>> g._notes[1].tie = tie.Tie('start')
        >>> h, i = g.splitAtQuarterLength(2.0)
        >>> for j in range(0,3):
        ...   print (h._notes[j].tie, i._notes[j].tie)
        (<music21.tie.Tie start>, <music21.tie.Tie stop>)
        (<music21.tie.Tie start>, <music21.tie.Tie continue>)
        (<music21.tie.Tie start>, <music21.tie.Tie stop>)
        '''
        from music21 import duration
        # needed for temporal manipulations; not music21 objects
        from music21 import tie

        if self.duration == None:
            raise Exception('cannot split an element that has a Duration of None')

        if quarterLength - delta > self.duration.quarterLength:
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

        if quarterLength < delta:
            quarterLength = 0
        elif abs(quarterLength - self.duration.quarterLength) < delta:
            quarterLength = self.duration.quarterLength

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
                e.tie = tie.Tie('start') # need a tie object

            eRemain.tie = tie.Tie(forceEndTieType)

        elif addTies and 'Chord' in e.classes:
            for i in range(len(e._notes)):
                component = e._notes[i]
                remainComponent = eRemain._notes[i]
                forceEndTieType = 'stop'
                if component.tie != None:
                    # the last tie of what was formally a start should
                    # continue
                    if component.tie.type == 'start':
                        # keep start  if already set
                        forceEndTieType = 'continue'
                    # a stop was ending a previous tie; we know that
                    # the first is now a continue
                    elif component.tie.type == 'stop':
                        forceEndTieType = 'stop'
                        component.tie.type = 'continue' 
                    elif component.tie.type == 'continue':
                        forceEndTieType = 'continue'
                        # keep continue if already set
                else:
                    component.tie = tie.Tie('start') # need a tie object
                remainComponent.tie = tie.Tie(forceEndTieType)
            
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
        '''
        Given a list of quarter lengths, return a list of 
        Music21Object objects, copied from this Music21Object, 
        that are partitioned and tied with the specified quarter 
        length list durations.

        
        >>> n = note.Note()
        >>> n.quarterLength = 3
        >>> post = n.splitByQuarterLengths([1,1,1])
        >>> [n.quarterLength for n in post]
        [1.0, 1.0, 1.0]
        '''
        # needed for temporal manipulations; not music21 objects
        from music21 import tie

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
        Takes a Music21Object (e.g., a note.Note) and returns a list of similar
        objects with only a single duration.DurationUnit in each. 
        Ties are added if the object supports ties. 

        Articulations only appear on the first note.  Same with lyrics.
        
        Fermatas should be on last note, but not done yet.

        
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
        
        >>> c = note.Note()
        >>> c.quarterLength = 2.5
        >>> d, e = c.splitAtDurations()
        >>> d.duration.type
        'half'
        >>> e.duration.type
        'eighth'
        >>> d.tie.type
        'start'
        >>> print e.tie
        <music21.tie.Tie stop>
        
        Assume c is tied to the next note.  Then the last split note should also be tied
        
        >>> c.tie = tie.Tie()
        >>> d, e = c.splitAtDurations()
        >>> e.tie.type
        'start'
        
        Rests have no ties:
        
        >>> f = note.Rest()
        >>> f.quarterLength = 2.5
        >>> g, h = f.splitAtDurations()
        >>> (g.duration.type, h.duration.type)
        ('half', 'eighth')
        >>> g.tie is None
        True
        '''
        # needed for temporal manipulations; not music21 objects
        from music21 import tie

        if self.duration == None:
            raise Exception('cannot split an element that has a Duration of None')

        returnNotes = []
        linkageType = self.duration.linkage
        for i in range(len(self.duration.components)):
            tempNote = copy.deepcopy(self)
            if i != 0:
                # clear articulations from remaining parts
                if hasattr(tempNote, 'articulations'):
                    tempNote.articulations = []
                if hasattr(tempNote, 'lyrics'):
                    tempNote.lyrics = []

            tempNote.duration = self.duration.components[i]
            if i != (len(self.duration.components) - 1): # if not last note, use linkage
                if linkageType is None:
                    pass
                elif linkageType == 'tie':
                    tempNote.tie = tie.Tie()
            else:
                # last note just gets the tie of the original Note
                if hasattr(self, 'tie') and self.tie is None:
                    tempNote.tie = tie.Tie("stop")
                elif hasattr(self, 'tie') and self.tie is not None and self.tie.type == 'stop':
                    tempNote.tie = tie.Tie("stop")
                elif hasattr(self, 'tie'):
                    tempNote.tie = copy.deepcopy(self.tie)
            returnNotes.append(tempNote)                
        return returnNotes




    #---------------------------------------------------------------------------
    # temporal and beat based positioning

    def _getMeasureNumber(self):
        '''
        If this object is contained in a Measure, return the measure number
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

    measureNumber = property(_getMeasureNumber, 
        doc = '''
        Return the measure number of a :class:`~music21.stream.Measure`  that contains this 
        object if the object is in a measure. 
        
        Returns None if the object is not in a measure.  Also note that by default Measure objects
        have measure number 0.
        
        If an object belongs to multiple measures (not in the same hierarchy...) then it returns the
        measure number of the :meth:`~music21.base.Music21Object.activeSite` if that is a 
        :class:`~music21.stream.Measure` object.  Otherwise it will use :meth:`~music21.base.Music21Object.getContextByClass`
        to find the number of the measure it was most recently added to. 
        
        
        >>> m = stream.Measure()
        >>> m.number = 12
        >>> n = note.Note()
        >>> m.append(n)
        >>> n.measureNumber
        12
        
        >>> n2 = note.Note()
        >>> n2.measureNumber is None
        True
        >>> m2 = stream.Measure()
        >>> m2.append(n2)
        >>> n2.measureNumber
        0
        
        This updates live if the measure number changes:
        
        >>> m2.number = 11
        >>> n2.measureNumber
        11
        
        
        The most recent measure added to is used unless activeSite is a measure:
        
        >>> m.append(n2)
        >>> n2.measureNumber
        12
        >>> n2.activeSite = m2
        >>> n2.measureNumber
        11
        ''')  


    def _getMeasureOffset(self, includeMeasurePadding=True):
        '''
        Try to obtain the nearest Measure that contains this object, 
        and return the offset of this object within that Measure.

        If a Measure is found, and that Measure has padding 
        defined as `paddingLeft` (for pickup measures, etc.), padding will be added to the 
        native offset gathered from the object. 

        
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
            #environLocal.printDebug(['found activeSite as Measure, using for offset'])
            offsetLocal = self.getOffsetBySite(self.activeSite)
        else:
            #environLocal.printDebug(['did not find activeSite as Measure, doing context search', 'self.activeSite', self.activeSite])
            # testing sortByCreationTime == true; this may be necessary
            # as we often want the most recent measure
            m = self.getContextByClass('Measure', sortByCreationTime=True, prioritizeActiveSite=False)
            if m is not None:
                #environLocal.printDebug(['using found Measure for offset access'])     
                try:
                    if includeMeasurePadding:       
                        offsetLocal = self.getOffsetBySite(m) + m.paddingLeft
                    else:
                        offsetLocal = self.getOffsetBySite(m)
                except SitesException:
                    try:
                        offsetLocal = self.offset
                    except:
                        offsetLocal = 0.0

            else: # hope that we get the right one
                #environLocal.printDebug(['_getMeasureOffset(): cannot find a Measure; using standard offset access'])
                offsetLocal = self.offset

        #environLocal.printDebug(['_getMeasureOffset(): found local offset as:', offsetLocal, self])
        return offsetLocal

    def _getMeasureOffsetOrMeterModulusOffset(self, ts):
        '''
        Return the measure offset based on a Measure, if it exists, 
        otherwise based on meter modulus of the TimeSignature. 
        This assumes that a TimeSignature has already been found.

        
        >>> m = stream.Measure()
        >>> ts1 = meter.TimeSignature('3/4')
        >>> m.insert(0, ts1)
        >>> n1 = note.Note()
        >>> m.insert(2, n1)
        >>> n1._getMeasureOffsetOrMeterModulusOffset(ts1) 
        2.0
        >>> n2 = note.Note()
        >>> m.insert(4, n2) # exceeding the range of the Measure gets a modulus
        >>> n1._getMeasureOffsetOrMeterModulusOffset(ts1) 
        2.0

        Can be applied to Notes in a Stream with a TimeSignature.

        >>> ts2 = meter.TimeSignature('5/4')
        >>> s2 = stream.Stream()
        >>> s2.insert(0, ts2)
        >>> n3 = note.Note()
        >>> s2.insert(3, n3)
        >>> n3._getMeasureOffsetOrMeterModulusOffset(ts2) 
        3.0
        >>> n4 = note.Note()
        >>> s2.insert(5, n4)
        >>> n4._getMeasureOffsetOrMeterModulusOffset(ts2) 
        0.0
        '''
        #environLocal.printDebug(['_getMeasureOffsetOrMeterModulusOffset', self, ts, 'ts._getMeasureOffset()', ts._getMeasureOffset(), 'self._getMeasureOffset()', self._getMeasureOffset()])
        mOffset = self._getMeasureOffset()
        tsMeasureOffset = ts._getMeasureOffset(includeMeasurePadding=False)
        if (mOffset + tsMeasureOffset) < ts.barDuration.quarterLength:
            return mOffset
        else:
            # must get offset relative to not just start of Stream, but the last
            # time signature
            post = ((mOffset - tsMeasureOffset) % ts.barDuration.quarterLength)
            #environLocal.printDebug(['result', post])
            return post

    def _getBeat(self):
        '''
        Return a beat designation based on local 
        Measure and TimeSignature

        
        >>> n = note.Note()
        >>> n.quarterLength = 2
        >>> m = stream.Measure()
        >>> m.isMeasure
        True
        >>> m.timeSignature = meter.TimeSignature('4/4')
        >>> m.repeatAppend(n, 2)
        >>> m[1].activeSite # here we get the activeSite, but not in m.notes
        <music21.stream.Measure 0 offset=0.0>

        >>> m.notes[0]._getBeat()
        1.0
        >>> m.notes[1]._getBeat()
        3.0
        '''
        ts = self.getContextByClass('TimeSignature')
        if ts is None:
            raise Music21ObjectException('this object does not have a TimeSignature in Sites')                    
        return ts.getBeatProportion(
            self._getMeasureOffsetOrMeterModulusOffset(ts))


    beat = property(_getBeat,  
        doc = '''
        Return the beat of this object as found in the most 
        recently positioned Measure. Beat values count from 1 and 
        contain a floating-point designation between 0 and 1 to 
        show proportional progress through the beat.

        
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

        >>> s = stream.Stream()
        >>> s.insert(0, meter.TimeSignature('3/4'))
        >>> s.repeatAppend(note.Note(), 8)
        >>> [n.beat for n in s.notes]
        [1.0, 2.0, 3.0, 1.0, 2.0, 3.0, 1.0, 2.0]
        ''')


    def _getBeatStr(self):
        ts = self.getContextByClass('TimeSignature')
        #environLocal.printDebug(['_getBeatStr(): found ts:', ts])
        if ts is None:
            raise Music21ObjectException('this object does not have a TimeSignature in Sites')                    
        return ts.getBeatProportionStr(
            self._getMeasureOffsetOrMeterModulusOffset(ts))


    beatStr = property(_getBeatStr,  
        doc = '''Return a string representation of the beat of 
        this object as found in the most recently positioned 
        Measure. Beat values count from 1 and contain a 
        fractional designation to show progress through the beat.

        
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

        >>> s = stream.Stream()
        >>> s.insert(0, meter.TimeSignature('3/4'))
        >>> s.repeatAppend(note.Note(), 8)
        >>> [n.beatStr for n in s.notes]
        ['1', '2', '3', '1', '2', '3', '1', '2']
        ''')


    def _getBeatDuration(self):
        '''Return a :class:`~music21.duration.Duration` of the beat 
        active for this object as found in the most recently 
        positioned Measure.

        
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
        if ts is None:
            raise Music21ObjectException('this object does not have a TimeSignature in Sites')
        return ts.getBeatDuration(
            self._getMeasureOffsetOrMeterModulusOffset(ts))

    beatDuration = property(_getBeatDuration,  
        doc = '''Return a :class:`~music21.duration.Duration` of the beat active for this object as found in the most recently positioned Measure.

        If extending beyond the Measure, or in a Stream with a TimeSignature, the meter modulus value will be returned. 

        
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

        >>> s = stream.Stream()
        >>> s.insert(0, meter.TimeSignature('2/4+3/4'))
        >>> s.repeatAppend(note.Note(), 8)
        >>> [n.beatDuration.quarterLength for n in s.notes]
        [2.0, 2.0, 3.0, 3.0, 3.0, 2.0, 2.0, 3.0]
        ''')


    def _getBeatStrength(self):
        '''Return an accent weight based on local Measure and TimeSignature. If the offset of this object does not match a defined accent weight, a minimum accent weight will be returned.

        
        >>> n = note.Note("D#7")
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
        
        
        Test not using measures
        

        >>> n = note.Note("E--3")
        >>> n.quarterLength = 2
        >>> s = stream.Stream()
        >>> s.isMeasure
        False
        >>> s.insert(0, meter.TimeSignature('2/2'))
        >>> s.repeatAppend(n, 16)
        >>> s.notes[0]._getBeatStrength()
        1.0
        >>> s.notes[1]._getBeatStrength()
        0.5
        >>> s.notes[4]._getBeatStrength()
        1.0
        >>> s.notes[5]._getBeatStrength()
        0.5
        
        
        '''
        #from music21.meter import MeterException
        ts = self.getContextByClass('TimeSignature')
        if ts is None:
            raise Music21ObjectException('this object does not have a TimeSignature in Sites')                    

#         environLocal.printDebug(['_getBeatStrength(): calling getAccentWeight()', 'self._getMeasureOffset()', self._getMeasureOffset(), 'ts', ts, 'ts.getAccentWeight', accentWeight])
        #mOffset = self._getMeasureOffset()

        return ts.getAccentWeight(
            self._getMeasureOffsetOrMeterModulusOffset(ts), 
                forcePositionMatch=True, permitMeterModulus=False)


    beatStrength = property(_getBeatStrength,  
        doc = '''Return the metrical accent of this object
        in the most recently positioned Measure. Accent values 
        are between zero and one, and are derived from the local 
        TimeSignature's accent MeterSequence weights. If the offset 
        of this object does not match a defined accent weight, a 
        minimum accent weight will be returned.

        
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


        We can also get the beatStrength for elements not in 
        a measure, if the enclosing stream has a :class:`~music21.meter.TimeSignature`.
        We just assume that the time signature carries through to
        hypothetical following measures:
        

        >>> n = note.QuarterNote("E--3")
        >>> s = stream.Stream()
        >>> s.insert(0.0, meter.TimeSignature('2/2'))
        >>> s.repeatAppend(n, 12)
        >>> [s.notes[i].beatStrength for i in range(12)]        
        [1.0, 0.25, 0.5, 0.25, 1.0, 0.25, 0.5, 0.25, 1.0, 0.25, 0.5, 0.25]
        
        
        Changing the meter changes the output, of course:
        
        >>> s.insert(4.0, meter.TimeSignature('3/4'))
        >>> [s.notes[i].beatStrength for i in range(12)]        
        [1.0, 0.25, 0.5, 0.25, 1.0, 0.5, 0.5, 1.0, 0.5, 0.5, 1.0, 0.5]
        
        ''')



    def _setSeconds(self, value):
        ti = self.getContextByClass('TempoIndication')
        if ti is None:
            raise Music21ObjectException('this object does not have a TempoIndication in Sites')
        mm = ti.getSoundingMetronomeMark()
        self.duration = mm.secondsToDuration(value)

    def _getSeconds(self):
        # do not search of duration is zero
        if self.duration is None or self.duration.quarterLength == 0.0:
            return 0.0

        ti = self.getContextByClass('TempoIndication')
        if ti is None:
            raise Music21ObjectException('this object does not have a TempoIndication in Sites')
        mm = ti.getSoundingMetronomeMark()
        # once we have mm, simply pass in this duration
        return mm.durationToSeconds(self.duration)

    seconds = property(_getSeconds, _setSeconds, doc = '''
        Get or set the the duration of this object in seconds, assuming 
        that this object has a :class:`~music21.tempo.MetronomeMark` or :class:`~music21.tempo.MetricModulation` in its past context.

        
        >>> s = stream.Stream()
        >>> s.repeatAppend(note.Note(), 12)
        >>> s.insert(0, tempo.MetronomeMark(number=120))
        >>> s.insert(6, tempo.MetronomeMark(number=240))
        >>> [n.seconds for n in s.notes]
        [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25]
        ''')

#-------------------------------------------------------------------------------
class ElementWrapper(Music21Object):
    '''
    An ElementWrapper is a way of containing any object that is not a 
    :class:`~music21.base.Music21Object`, so that that object can
    be positioned within a :class:`~music21.stream.Stream`.
    
    The object stored within ElementWrapper is available from 
    the the :attr:`~music21.base.ElementWrapper.obj` attribute.
    All the attributes of the stored object (except .id and
    anything else that conflicts with a Music21Object attribute)
    are gettable and settable by querying the ElementWrapper.
    This feature makes it possible easily to mix Music21Objects
    and non-Music21Objects with similarly named attributes in the
    same Stream.
    
    
    This example inserts 10 random wave files into a music21
    Stream and then reports their filename and number of 
    audio channels (in this example, it's always 2) if they
    fall on a strong beat in fast 6/8


    >>> import music21
    >>> from music21 import stream, meter
    >>> #_DOCS_SHOW import wave
    >>> import random
    >>> class Wave_read(object): #_DOCS_HIDE
    ...    def getnchannels(self): return 2 #_DOCS_HIDE
    
    >>> s = stream.Stream()
    >>> s.append(meter.TimeSignature('fast 6/8'))
    >>> for i in range(10):
    ...    fileName = 'thisSound_' + str(random.randint(1,20)) + '.wav'
    ...    fileName = 'thisSound_' + str(1+((i * 100) % 19)) + '.wav' #_DOCS_HIDE #make a more predictable "random" set.
    ...    soundFile = Wave_read() #_DOCS_HIDE
    ...    #_DOCS_SHOW soundFile = wave.open(fileName)
    ...    soundFile.fileName = fileName
    ...    el = music21.ElementWrapper(soundFile)
    ...    s.insert(i, el)

    >>> for j in s.getElementsByClass('ElementWrapper'):
    ...    if j.beatStrength > 0.4:
    ...        print j.offset, j.beatStrength, j.getnchannels(), j.fileName
    0.0 1.0 2 thisSound_1.wav
    3.0 1.0 2 thisSound_16.wav
    6.0 1.0 2 thisSound_12.wav
    9.0 1.0 2 thisSound_8.wav    
    
    
    Test representation of an ElementWrapper
    
    >>> for i, j in enumerate(s.getElementsByClass('ElementWrapper')):
    ...     if i == 2:
    ...         j.id = None
    ...     else:
    ...         j.id = str(i) + "_wrapper"
    ...     if i <=2:
    ...         print j
    <ElementWrapper id=0_wrapper offset=0.0 obj="<...Wave_read object...">
    <ElementWrapper id=1_wrapper offset=1.0 obj="<...Wave_read object...">
    <ElementWrapper offset=2.0 obj="<...Wave_read object...">
    '''
    obj = None
    _id = None

    _DOC_ORDER = ['obj']
    _DOC_ATTR = {
    'obj': 'The object this wrapper wraps. It should not be a Music21Object.',
    }

    def __init__(self, obj = None):
        Music21Object.__init__(self)
        self.obj = obj # object stored here        
        # the unlinkedDuration is the duration that is inherited from 
        # Music21Object
        #self._unlinkedDuration = None




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

        >>> import music21
        >>> from music21 import note
        >>> n = note.Note("C#")
        >>> a = music21.ElementWrapper(n)
        >>> a.offset = 3.0
        >>> b = music21.ElementWrapper(n)
        >>> b.offset = 3.0
        >>> a == b
        True
        >>> a is not b
        True
        >>> c = music21.ElementWrapper(n)
        >>> c.offset = 2.0
        >>> c.offset
        2.0
        >>> a == c
        False
        '''
        if not hasattr(other, "obj") or \
           not hasattr(other, "offset") or \
           not hasattr(other, "priority") or \
           not hasattr(other, "groups") or \
           not hasattr(other, "activeSite") or \
           not hasattr(other, "duration"):
            return False


        if (self.obj == other.obj and \
            self.offset == other.offset and \
            self.priority == other.priority and \
            self.groups == other.groups and \
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
        '''
        A weaker form of equality.  a.isTwin(b) is true if
        a and b store either the same object OR objects that are equal.
        In other words, it is essentially the same object in a different context
             
        >>> import music21
        >>> from music21 import note

        >>> aE = music21.ElementWrapper(obj = "hello")
        
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
        if not hasattr(other, "obj"):
            return False

        if (self.obj is other.obj or self.obj == other.obj):
            return True
        else:
            return False




#-------------------------------------------------------------------------------
class TestMock(Music21Object):
    def __init__(self):
        Music21Object.__init__(self)

class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testCopyAndDeepcopy(self):
        '''Test copying all objects defined in this module
        '''
        for part in sys.modules[self.__module__].__dict__:
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
                i = copy.copy(obj)
                j = copy.deepcopy(obj)


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
        from music21 import note
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
        unused_subStream = stream1.notes

    def testLocationsRefs(self):
        aMock = TestMock()
        bMock = TestMock()

        loc = Sites()
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
        loc = Sites()
        loc.add(None, 0)



    def testM21BaseDeepcopy(self):
        '''
        Test copying
        '''
        a = Music21Object()
        a.id = 'test'
        b = copy.deepcopy(a)
        self.assertNotEqual(a, b)
        self.assertEqual(b.id, 'test')

    def testM21BaseSites(self):
        '''
        Basic testing of M21 base object sites
        '''
        a = Music21Object()
        b = Music21Object()

        # storing a single offset does not add a Sites entry  
        a.offset = 30
        # all offsets are store in locations
        self.assertEqual(len(a.sites), 1)
        self.assertEqual(a.getOffsetBySite(None), 30.0)
        self.assertEqual(a.offset, 30.0)

        # assigning a activeSite directly
        a.activeSite = b
        # now we have two offsets in locations
        self.assertEqual(len(a.sites), 2)

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
        self.assertEqual(len(a.sites), 2)
        self.assertEqual(a.getOffsetBySite(b), 40.0)


    def testM21BaseLocationsCopy(self):
        '''
        Basic testing of M21 base object
        '''
        a = Music21Object()
        a.id = "a obj"
        b = Music21Object()
        b.id = "b obj"

        post = []
        b.id = 'test'
        b.activeSite = a
        c = copy.deepcopy(b)
        c.id = "c obj"
        post.append(c)

        # have two locations: None, and that set by assigning activeSite
        self.assertEqual(len(b.sites), 2)
        dummy = post[-1].sites
        self.assertEqual(len(post[-1].sites), 2)

        # the active site of a deepcopy should not be the same?
        #self.assertEqual(post[-1].activeSite, a)

        a = Music21Object()

        post = []
        b = Music21Object()
        b.id = 'test'
        b.activeSite = a
        b.offset = 30
        c = copy.deepcopy(b)
        c.activeSite = b
        post.append(c)

        self.assertEqual(len(post[-1].sites), 3)

        # this works because the activeSite is being set on the object
        self.assertEqual(post[-1].activeSite, b)
        # the copied activeSite has been deepcopied, and cannot now be accessed
        # this fails! post[-1].getOffsetBySite(a)

    def testSites(self):
        from music21 import note, stream, corpus, clef

        m = stream.Measure()
        m.number = 34
        n = note.Note()
        m.append(n)
        
        n.pitch.sites.add(m)
        n.pitch.sites.add(n) 
        self.assertEqual(n.pitch.getContextAttr('number'), 34)
        n.pitch.setContextAttr('lyric',  
                               n.pitch.getContextAttr('number'))
        # converted to a string now
        self.assertEqual(n.lyric, '34')


        violin1 = corpus.parse(
            "beethoven/opus18no1", 
            3,
            fileExtensions='xml',
            ).getElementById("Violin I")
        lastNote = violin1.flat.notes[-1]
        lastNoteClef = lastNote.getContextByClass(clef.Clef)
        self.assertEqual(isinstance(lastNoteClef, clef.TrebleClef), True)

    def testSitesSearch(self):
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

    def testSitesMeasures(self):
        '''Can a measure determine the last Clef used?
        '''
        from music21 import corpus, clef, stream
        a = corpus.parse('bach/bwv324.xml')
        measures = a.parts[0].getElementsByClass('Measure') # measures of first part

        # the activeSite of measures[1] is set to the new output stream
        self.assertEqual(measures[1].activeSite, measures)
        # the source Part should still be a context of this measure
        self.assertEqual(measures[1].hasContext(a.parts[0]), True)

        # from the first measure, we can get the clef by using 
        # getElementsByClass
        post = measures[0].getElementsByClass(clef.Clef)
        self.assertEqual(isinstance(post[0], clef.TrebleClef), True)

        # make sure we can find offset in a flat representation
        self.assertEqual(a.parts[0].flat.getOffsetByElement(a.parts[0][3]), None)

        # for the second measure
        post = a.parts[0][3].getContextByClass(clef.Clef)
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
        self.assertEqual(measures[3].hasContext(a.parts[0]), True)
        # we can still access the clef through this measure on this
        # new stream
        post = newStream[0].getContextByClass(clef.Clef)
        self.assertEqual(isinstance(post, clef.TrebleClef), True)

    def testSitesClef(self):
        from music21 import note, stream, clef
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

    def testSitesPitch(self):
        # TODO: this form does not yet work
        from music21 import note, stream
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
        s = corpus.parse('bach/bwv66.6.xml')
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
        for n in p1.flat.notesAndRests:
            post.append(n._getMeasureOffset())
        self.assertEqual(post, [3.0, 3.5, 0.0, 1.0, 2.0, 3.0, 0.0, 1.0, 2.0, 3.0, 0.0, 0.5, 1.0, 2.0, 3.0, 0.0, 1.0, 2.0, 3.0, 0.0, 1.0, 2.0, 3.0, 0.0, 1.0, 2.0, 3.0, 0.0, 1.0, 2.0, 0.0, 2.0, 3.0, 0.0, 1.0, 1.5, 2.0])

        # compare derived beat string
        post = []
        for n in p1.flat.notesAndRests:
            post.append(n.beatStr)
        self.assertEqual(post, ['4', '4 1/2', '1', '2', '3', '4', '1', '2', '3', '4', '1', '1 1/2', '2', '3', '4', '1', '2', '3', '4', '1', '2', '3', '4', '1', '2', '3', '4', '1', '2', '3', '1', '3', '4', '1', '2', '2 1/2', '3'])

        # for stream and Stream subclass, overridden methods not yet
        # specialzied
        # _getMeasureOffset gets the offset within the activeSite
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

    def testGetBeatStrengthA(self):
        from music21 import stream, note, meter

        n = note.Note('g')
        n.quarterLength = 1
        s = stream.Stream()
        s.insert(0, meter.TimeSignature('4/4'))
        s.repeatAppend(n, 8)
        #match = []
        self.assertEqual([e.beatStrength for e in s.notes], [1.0, 0.25, 0.5, 0.25, 1.0, 0.25, 0.5, 0.25])

        n = note.QuarterNote("E--3")
        s = stream.Stream()
        s.insert(0.0, meter.TimeSignature('2/2'))
        s.repeatAppend(n, 12)
        match = [s.notes[i].beatStrength for i in range(12)]        
        self.assertEqual([1.0, 0.25, 0.5, 0.25, 1.0, 0.25, 0.5, 0.25, 1.0, 0.25, 0.5, 0.25], match)

    def testMeaureNumberAccess(self):
        '''Test getting measure numebr data from various Music21Objects.
        '''
        from music21 import corpus, stream, note
        
        s = corpus.parse('bach/bwv66.6.xml')
        p1 = s.parts['Soprano']
        for classStr in ['Clef', 'KeySignature', 'TimeSignature']:
            self.assertEqual(p1.flat.getElementsByClass(
                classStr)[0].measureNumber, 0)
        
        match = []
        for n in p1.flat.notesAndRests:
            match.append(n.measureNumber)
        self.assertEqual(match, [0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 6, 6, 6, 6, 7, 7, 7, 8, 8, 8, 9, 9, 9, 9] )
        
        # create a note and put it in different measures
        m1 = stream.Measure()
        m1.number = 3
        m2 = stream.Measure()
        m2.number = 74
        n = note.Note()
        self.assertEqual(n.measureNumber, None) # not in a Meaure
        m1.append(n)
        self.assertEqual(n.measureNumber, 3) 
        m2.append(n)
        self.assertEqual(n.measureNumber, 74)

    def testPickupMeauresBuilt(self):
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
        # m2 can now find a time signature by looking to activeSite stream
        self.assertEqual(m2.duration.quarterLength, 4.0)
        # highest time of score takes into account new measure
        self.assertEqual(s.highestTime, 5.0)
        # offset are contiguous when accessed in a flat form
        self.assertEqual([n.offset for n in s.flat.notesAndRests], [0.0, 1.0])        
    
    
        m3 = stream.Measure()        
        n3 = note.Note('f#2')
        n3.quarterLength = 3.0
        m3.append(n3)
    
        # add to stream
        s.append(m3)
        # m3 can now find a time signature by looking to activeSite stream
        self.assertEqual(m2.duration.quarterLength, 4.0)
        # highest time of score takes into account new measure
        self.assertEqual(s.highestTime, 8.0)
        # offset are contiguous when accessed in a flat form
        self.assertEqual([n.offset for n in s.flat.notesAndRests], [0.0, 1.0, 5.0])        
    
    
    def testPickupMeauresImported(self):
        from music21 import corpus
        s = corpus.parse('bach/bwv103.6')
    
        p = s.parts['soprano']
        m1 = p.getElementsByClass('Measure')[0]
    
    
        self.assertEqual([n.offset for n in m1.notesAndRests], [0.0, 0.5])
        self.assertEqual(m1.paddingLeft, 3.0)
        
        #offsets for flat representation have proper spacing
        self.assertEqual([n.offset for n in p.flat.notesAndRests], [0.0, 0.5, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 12.5, 13.0, 15.0, 16.0, 16.5, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0, 27.0, 28.0, 28.5, 29.0, 31.0, 32.0, 33.0, 34.0, 34.5, 34.75, 35.0, 35.5, 36.0, 37.0, 38.0, 39.0, 40.0, 41.0, 42.0, 43.0, 44.0, 45.0, 47.0, 48.0, 48.5, 49.0, 50.0, 51.0, 52.0, 53.0, 54.0, 55.0, 56.0, 57.0, 58.0, 59.0, 60.0, 60.5, 61.0, 63.0] )
    

    def testBoundLocations(self):
        '''Bound or relative locations; locations that are not based on a number but an attribute of the site.
        '''
        from music21 import stream, note, bar

        s = stream.Stream()
        n1 = note.Note()
        n1.quarterLength = 20
        s.append(n1)
        self.assertEqual(s.highestTime, 20)

        #offset = None

        # this would be in a note
        dc = Sites()
        # we would add, for that note, a location in object s
        # if offset is None, it is a context, and has no offset
        dc.add(s, None)
        self.assertEqual(len(dc), 1)
        self.assertEqual(len(dc._locationKeys), 0)
        self.assertEqual(dc.getSites(), [])

        dc = Sites()
        # if we have an offset, we get a location
        dc.add(s, 30)
        self.assertEqual(len(dc), 1)
        self.assertEqual(len(dc._locationKeys), 1)
        self.assertEqual(dc.getSites(), [s])
        self.assertEqual(dc.getOffsets(), [30])
        self.assertEqual(dc.getOffsetBySite(s), 30)
        self.assertEqual(dc.getOffsetByObjectMatch(s), 30)


        dc = Sites()
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
        
        dc = Sites()
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
        b1.sites.add(s, 'highestTime')
        self.assertEqual(b1.getOffsetBySite(s), 30.0)
        
        s.append(n2)
        self.assertEqual(s.highestTime, 50.0)
        self.assertEqual(b1.getOffsetBySite(s), 50.0)



    def testGetAllContextsByClass(self):
        from music21 import note, stream, clef
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


    def testContainedById(self):
        from music21 import note, stream
        n = note.Note()
        self.assertEqual(id(n), n.sites.containedById)

        n1 = note.Note()
        s1 = stream.Stream()
        s1.append(n1)
        s2 = copy.deepcopy(s1)
        n2 = s2[0] # this is a new instance; not the same as n1
        self.assertEqual(s2.hasElement(n1), False)
        self.assertEqual(s2.hasElement(n2), True)

        # s1 is still a context of n2, but not a site
        #self.assertEqual(n2.hasContext(s1), True)
        self.assertEqual(n2.hasSite(s1), False)
        self.assertEqual(n2.hasContext(s2), True)
        self.assertEqual(n2.hasSite(s2), True)

        self.assertEqual(n2.sites.containedById, id(n2))



    def testGetContextByClassA(self):
        from music21 import stream, note, tempo

        p = stream.Part()
        m1 = stream.Measure()
        m1.repeatAppend(note.Note(quarterLength=1), 4)
        m2 = copy.deepcopy(m1)
        mm1 = tempo.MetronomeMark(number=50, referent=.25)
        m1.insert(0, mm1)
        mm2 = tempo.MetronomeMark(number=150, referent=.5)
        m2.insert(0, mm2)
        p.append([m1, m2])
        
        # if done with default args, we get the same object, as we are using
        # getElementAtOrBefore
        self.assertEqual(str(mm2.getContextByClass('MetronomeMark')),     
            '<music21.tempo.MetronomeMark Eighth=150>')
        # if we provide the getElementMethod parameter, we can use 
        # getElementBeforeOffset
        self.assertEqual(str(mm2.getContextByClass('MetronomeMark',                     
            getElementMethod='getElementBeforeOffset')),
            '<music21.tempo.MetronomeMark lento 16th=50>')


    def testElementWrapperOffsetAccess(self):
        import music21
        from music21 import stream, meter

        class Mock(object): pass

        s = stream.Stream()
        s.append(meter.TimeSignature('fast 6/8'))
        storage = []
        for i in range(0,2):
            mock = Mock() 
            el = music21.ElementWrapper(mock)
            storage.append(el)
            s.insert(i, el)

        for ew in storage:
            self.assertEqual(s.hasElement(ew), True)

        match = [e.getOffsetBySite(s) for e in storage]
        self.assertEqual(match, [0.0, 1.0])

        self.assertEqual(s.getOffsetByElement(storage[0]), 0.0)
        self.assertEqual(s.getOffsetByElement(storage[1]), 1.0)


    def testGetActiveSiteTimeSignature(self):
        import music21
        from music21 import stream, meter
        class Wave_read(object): #_DOCS_HIDE
            def getnchannels(self): return 2 #_DOCS_HIDE
    
        s = stream.Stream()
        s.append(meter.TimeSignature('fast 6/8'))
        #s.show('t')
        storage = []
        for i in range(0,6):
            soundFile = Wave_read() #_DOCS_HIDE
            #el = music21.Music21Object() # 
            el = music21.ElementWrapper(soundFile)
            storage.append(el)
            #print el
            self.assertEqual(el.obj, soundFile)
            s.insert(i, el)

        for ew in storage:
            self.assertEqual(s.hasElement(ew), True)

        matchOffset = []
        matchBeatStrength = []
        matchAudioChannels = []

        for j in s.getElementsByClass('ElementWrapper'):
            matchOffset.append(j.offset)
            matchBeatStrength.append(j.beatStrength)
            matchAudioChannels.append(j.getnchannels())
        self.assertEqual(matchOffset, [0.0, 1.0, 2.0, 3.0, 4.0, 5.0])
        self.assertEqual(matchBeatStrength, [1.0, 0.25, 0.25, 1.0, 0.25, 0.25])
        self.assertEqual(matchAudioChannels, [2, 2, 2, 2, 2, 2])

    
    def testGetMeasureOffsetOrMeterModulusOffsetA(self):
        # test getting metric position in a Stream with a TS
        from music21 import stream, note, meter

        s = stream.Stream()
        s.repeatAppend(note.Note(), 12)
        s.insert(0, meter.TimeSignature('3/4'))
        
        match = [n.beat for n in s.notes]
        self.assertEqual(match, [1.0, 2.0, 3.0, 1.0, 2.0, 3.0, 1.0, 2.0, 3.0, 1.0, 2.0, 3.0])
        
        match = [n.beatStr for n in s.notes]
        self.assertEqual(match, ['1', '2', '3', '1', '2', '3', '1', '2', '3', '1', '2', '3'])
        
        match = [n.beatDuration.quarterLength for n in s.notes]
        self.assertEqual(match, [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0] )
        
        match = [n.beatStrength for n in s.notes]
        self.assertEqual(match, [1.0, 0.5, 0.5, 1.0, 0.5, 0.5, 1.0, 0.5, 0.5, 1.0, 0.5, 0.5] )

    def testGetMeasureOffsetOrMeterModulusOffsetB(self):
        from music21 import stream, note, meter

        s = stream.Stream()
        s.repeatAppend(note.Note(), 12)
        s.insert(0.0, meter.TimeSignature('3/4'))
        s.insert(3.0, meter.TimeSignature('4/4'))
        s.insert(7.0, meter.TimeSignature('2/4'))
        
        match = [n.beat for n in s.notes]
        self.assertEqual(match, [1.0, 2.0, 3.0, 1.0, 2.0, 3.0, 4.0, 1.0, 2.0, 1.0, 2.0, 1.0])
        
        match = [n.beatStr for n in s.notes]
        self.assertEqual(match, ['1', '2', '3', '1', '2', '3', '4', '1', '2', '1', '2', '1'])
        
        match = [n.beatStrength for n in s.notes]
        self.assertEqual(match, [1.0, 0.5, 0.5, 1.0, 0.25, 0.5, 0.25, 1.0, 0.5, 1.0, 0.5, 1.0])



    def testSecondsPropertyA(self):
        from music21 import stream, note, tempo
        s = stream.Stream()
        s.repeatAppend(note.Note(), 12)
        s.insert(0, tempo.MetronomeMark(number=120))
        
        self.assertEqual([n.seconds for n in s.notes], [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5])
        
        # changing tempo mid-stream
        s.insert(6, tempo.MetronomeMark(number=240))
        self.assertEqual([n.seconds for n in s.notes], [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25])
        
        # adding notes based on seconds
        s = stream.Stream()
        s.insert(0, tempo.MetronomeMark(number=120))
        s.append(note.Note())
        s.notes[0].seconds = 2.0
        self.assertEqual(s.notes[0].quarterLength, 4.0)
        
        s.append(note.Note())
        s.notes[1].seconds = 0.5
        self.assertEqual(s.notes[1].quarterLength, 1.0)
        self.assertEqual(s.duration.quarterLength, 5.0)
        
        s.append(tempo.MetronomeMark(number=30))
        s.append(note.Note())
        s.notes[2].seconds = 0.5
        self.assertEqual(s.notes[2].quarterLength, 0.25)
        self.assertEqual(s.duration.quarterLength, 5.25)


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


    def testGetContextByClassB(self):
        from music21 import stream, note, meter

        s = stream.Score()

        p1 = stream.Part()
        m1 = stream.Measure()
        m1.repeatAppend(note.Note(), 3)
        m1.timeSignature = meter.TimeSignature('3/4')
        m2 = stream.Measure()
        m2.repeatAppend(note.Note(), 3)
        p1.append(m1)
        p1.append(m2)

        p2 = stream.Part()
        m3 = stream.Measure()
        m3.timeSignature = meter.TimeSignature('3/4')
        m3.repeatAppend(note.Note(), 3)
        m4 = stream.Measure()
        m4.repeatAppend(note.Note(), 3)
        p2.append(m3)
        p2.append(m4)

        s.insert(0, p1)
        s.insert(0, p2)

        p3 = stream.Part()
        m5 = stream.Measure()
        m5.timeSignature = meter.TimeSignature('3/4')
        m5.repeatAppend(note.Note(), 3)
        m6 = stream.Measure()
        m6.repeatAppend(note.Note(), 3)
        p3.append(m5)
        p3.append(m6)

        p4 = stream.Part()
        m7 = stream.Measure()
        m7.timeSignature = meter.TimeSignature('3/4')
        m7.repeatAppend(note.Note(), 3)
        m8 = stream.Measure()
        m8.repeatAppend(note.Note(), 3)
        p4.append(m7)
        p4.append(m8)

        s.insert(0, p3)
        s.insert(0, p4)

        #self.targetMeasures = m4
        #n1 = m2[-1] # last element is a note
        n2 = m4[-1] # last element is a note

        #environLocal.printDebug(['getContextByClass()'])
        #self.assertEqual(str(n1.getContextByClass('TimeSignature')), '<music21.meter.TimeSignature 3/4>') 
        environLocal.printDebug(['getContextByClass()'])
        self.assertEqual(str(n2.getContextByClass('TimeSignature')), '<music21.meter.TimeSignature 3/4>') 


    def testNextA(self):
        from music21 import stream, scale, note
        s = stream.Stream()
        sc = scale.MajorScale()
        notes = []
        for i in sc.pitches:
            n = note.Note()
            s.append(n)
            notes.append(n) # keep for reference and testing
        
        self.assertEqual(notes[0], s[0])
        self.assertEqual(notes[1], s[0].next())
        self.assertEqual(notes[0], s[1].previous())

        self.assertEqual(id(notes[5]), id(s[4].next()))
        self.assertEqual(id(notes[3]), id(s[4].previous()))

        # if a note has more than one site, what happens
        self.assertEqual(notes[6], s.notes[5].next())
        self.assertEqual(notes[7], s.notes[6].next())
        

    def testNextB(self):
        from music21 import stream, note

        m1 = stream.Measure()
        m1.number = 1
        n1 = note.Note()
        m1.append(n1)

        m2 = stream.Measure()
        m2.number = 2
        n2 = note.Note()    
        m2.append(n2)

        # n1 cannot be connected to n2 as no common site
        self.assertEqual(n1.next(), None)

        p1 = stream.Part()
        p1.append(m1)
        p1.append(m2)
        self.assertEqual(n1.next(), m2)
        self.assertEqual(n1.next('Note'), n2)


    def testNextC(self):
        from music21 import corpus
        s = corpus.parse('bwv66.6')
        
        # getting time signature and key sig
        p1 = s.parts[0]
        nLast = p1.flat.notes[-1]
        self.assertEqual(str(nLast.previous('TimeSignature')), '<music21.meter.TimeSignature 4/4>')
        self.assertEqual(str(nLast.previous('KeySignature')), 
            '<music21.key.KeySignature of 3 sharps, mode minor>')
        
        # iterating at the Measure level, showing usage of flattenLocalSites
        measures = s.parts[0].getElementsByClass('Measure')
        self.assertEqual(measures[3].previous(), measures[2])
        
        self.assertEqual(measures[3].previous(), measures[2])
        self.assertEqual(measures[3].previous(flattenLocalSites=True), measures[2].notes[-1])
        
        self.assertEqual(measures[3].next(), measures[4])
        self.assertEqual(measures[3].next('Note', flattenLocalSites=True), measures[3].notes[0])
        
        self.assertEqual(measures[3].previous().previous(), measures[1])
        self.assertEqual(measures[3].previous().previous().previous(), measures[0])
        self.assertEqual(
            str(measures[3].previous().previous().previous().previous()), 
            'P1: Soprano: Instrument 1')

        self.assertEqual(str(measures[0].previous()), 'P1: Soprano: Instrument 1') 


    def testActiveSiteCopyingA(self):
        from music21 import note, stream

        n1 = note.Note()
        s1 = stream.Stream()
        s1.append(n1)
        self.assertEqual(n1.activeSite, s1)

        unused_n2 = copy.deepcopy(n1)
        #self.assertEqual(n2._activeSite, s1)
        

#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [Music21Object, ElementWrapper, Sites]


def mainTest(*testClasses):
    '''
    Takes as its arguments modules (or a string 'noDocTest' or 'verbose')
    and runs all of these modules through a unittest suite
    
    Unless 'noDocTest' is passed as a module, a docTest
    is also performed on `__main__`, hence the name "mainTest".
    
    If 'moduleRelative' (a string) is passed as a module, then
    global variables are preserved.
    
    Run example (put at end of your modules):
    
    ::

        import unittest
        class Test(unittest.TestCase):
            def testHello(self):
                hello = "Hello"
                self.assertEqual("Hello", hello)
    
        import music21
        if __name__ == '__main__':
            music21.mainTest(Test)

    '''
    #environLocal.printDebug(['mainTest()', testClasses])

    runAllTests = True    

    # start with doc tests, then add unit tests
    if ('noDocTest' in testClasses or 'noDocTest' in sys.argv 
        or 'nodoctest' in sys.argv):
        # create a test suite for storage
        s1 = unittest.TestSuite()
    else: 
        # create test suite derived from doc tests
        # here we use '__main__' instead of a module
        optionflags = (
            doctest.ELLIPSIS|
            doctest.NORMALIZE_WHITESPACE|
            doctest.REPORT_ONLY_FIRST_FAILURE)
        if 'moduleRelative' in testClasses or 'moduleRelative' in sys.argv:
            s1 = doctest.DocTestSuite(
                '__main__',
                optionflags=optionflags,
                )
        else:
            globs = __import__('music21').__dict__.copy()
            s1 = doctest.DocTestSuite(
                '__main__',
                globs=globs,
                optionflags=optionflags,
                )

    verbosity = 1
    if 'verbose' in testClasses or 'verbose' in sys.argv:
        verbosity = 2 # this seems to hide most display

    displayNames = False
    if 'list' in sys.argv or 'display' in sys.argv:
        displayNames = True
        runAllTests = False

    runThisTest = None
    if len(sys.argv) == 2:
        arg = sys.argv[1].lower()
        if arg not in ['list', 'display', 'verbose', 'nodoctest']:
            # run a test directly named in this module
            runThisTest = sys.argv[1]    

    # -f, --failfast
    if 'onlyDocTest' in sys.argv or 'onlyDocTest' in testClasses:
        testClasses = [] # remove cases
    for t in testClasses:
        if not isinstance(t, basestring):
            if displayNames:
                for tName in unittest.defaultTestLoader.getTestCaseNames(t):
                    print('Unit Test Method: %s' % tName)
            if runThisTest is not None:
                tObj = t() # call class
                # search all names for case-insensitive match
                for name in dir(tObj):
                    if name.lower() == runThisTest.lower() or \
                         name.lower() == ('test' + runThisTest.lower()) or \
                         name.lower() == ('xtest' + runThisTest.lower()):
                        runThisTest = name
                        break
                if hasattr(tObj, runThisTest): 
                    print('Running Named Test Method: %s' % runThisTest)
                    getattr(tObj, runThisTest)()
                    runAllTests = False
                    break

            # normally operation collects all tests
            s2 = unittest.defaultTestLoader.loadTestsFromTestCase(t)
            s1.addTests(s2) 


    if runAllTests:
        runner = unittest.TextTestRunner()
        runner.verbosity = verbosity
        unused_testResult = runner.run(s1) 


#------------------------------------------------------------------------------
if __name__ == "__main__":
    mainTest(Test)


#------------------------------------------------------------------------------
# eof

