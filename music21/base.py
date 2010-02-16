#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         base.py
# Purpose:      Music21 base classes and important utilities
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    (c) 2009 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

'''
Music21 base classes and important utilities

base -- the convention within music21 is that __init__ files contain:

   from base import *
   
so everything in this file can be accessed as music21.XXXX

'''


import copy
import unittest, doctest
import sys
import types
import time
import inspect

from music21 import common
from music21 import environment
_MOD = 'music21.base.py'
environLocal = environment.Environment(_MOD)


#-------------------------------------------------------------------------------
VERSION = (0, 2, 4)  # increment any time picked versions will be obsolete.
VERSION_STR = '.'.join([str(x) for x in VERSION]) + 'a1'
WEAKREF_ACTIVE = True

#-------------------------------------------------------------------------------
class Music21Exception(Exception):
    pass

class ContextsException(Exception):
    pass

class LocationsException(Exception):
    pass

class Music21ObjectException(Exception):
    pass

class ElementException(Exception):
    pass

class GroupException(Exception):
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
class Contexts(object):
    '''An object, stored within a Music21Object, that provides an ordered collection of objects that may be contextually relevant.
    '''
    #TODO: make locations, by default, use weak refs
    # make contexts, by default, not use weak refs

    def __init__(self):
        self._ref = [] # references
        self._loc = [] # locations

    def __len__(self):
        '''Return the total number of references.

        >>> class Mock(Music21Object): pass
        >>> aObj = Mock()
        >>> aContexts = Contexts()
        >>> aContexts.addReference(aObj)
        >>> len(aContexts) 
        1
        '''
        return len(self._ref) + len(self._loc)

    def countLoc(self):
        return len(self._loc)

    def countRef(self):
        return len(self._ref)

    def _selectDomain(self, arg):
        post = []
        if 'ref' in arg:
            post.append(self._ref)
        elif 'loc' in arg:
            post.append(self._loc)
        return post

    def scrub(self, domain=['ref', 'loc']):
        '''Remove all weak ref objects that point to objects that no longer exist.
        '''
        for coll in self._selectDomain(domain):
            delList = []
            for i in range(len(coll)):
                if common.isWeakref(self._ref[i]): # only del weak refs
                    if common.unwrapWeakref(self._ref[i]['obj']) is None:
                        delList.append(i)
            delList.reverse() # go in reverse from largest to maintain positions
            for i in delList:
                del self._ref[i]

    def clear(self):
        '''Clear all data.
        '''
        self._ref = []
        self._loc = []


    def get(self, domain=['ref', 'loc']):
        '''Get references; unwrap from weakrefs; place in order from 
        most recently added to least recently added

        >>> class Mock(Music21Object): pass
        >>> aObj = Mock()
        >>> bObj = Mock()
        >>> aContexts = Contexts()
        >>> aContexts.addReference(aObj)
        >>> aContexts.addReference(bObj)
        >>> aContexts.getReferences() == [bObj, aObj]
        True
        '''
        post = []
        for coll in self._selectDomain(domain):
            for i in range(len(self._ref)-1, -1, -1):
                dict = self._ref[i]
                # need to check if these is weakref
                if common.isWeakref(dict['obj']):
                    post.append(common.unwrapWeakref(dict['obj']))
                else:
                    post.append(dict['obj'])
        return post

    def getReferences(self):
        return self.get('ref')

    def getLocations(self):
        return self.get('loc')

    def addReference(self, obj, weakRef=False):
        '''Add a reference
        '''
        # only add if not already here
        if obj not in self.getReferences(): 
            objRef = common.wrapWeakref(obj)
            self._ref.append({}) # create new
            self._ref[-1]['obj'] = objRef
            self._ref[-1]['name'] = type(obj).__name__
            self._ref[-1]['time'] = time.time()

    def remove(self, obj, domain=['ref', 'loc']):
        '''Remove the entry specified by sites

        '''
        match = False
        for coll in self._selectDomain(domain):
            if obj in coll: 
                del coll[coll.index(obj)]
                match = True
        if not match:
            raise ContextsException('an entry for this object (%s) is not stored in this object' % obj)


    def getById(self, id, domain=['ref', 'loc']):
        pass
    
    def getByGroup(self, id, domain=['ref', 'loc']):
        pass

    def getByClass(self, className, domain=['ref', 'loc']):
        '''Return the most recently added reference based on className. Class name can be a string or the real class name.

        TODO: do this recursively, searching the Contexts of all members

        >>> class Mock(Music21Object): pass
        >>> aObj = Mock()
        >>> bObj = Mock()
        >>> aContexts = Contexts()
        >>> aContexts.addReference(aObj)
        >>> aContexts.addReference(bObj)
        >>> aContexts.getByClass('mock') == bObj
        True
        >>> aContexts.getByClass(Mock) == bObj
        True

        '''
        for obj in self.get(domain=domain):
            if obj is None: continue # in case the reference is dead
            if common.isStr(className):
                if type(obj).__name__.lower() == className.lower():
                    return obj       
            else:
                if isinstance(obj, className):
                    return obj

    def getAttrByName(self, attrName, domain=['rec', 'loc']):
        '''Given an attribute name, search all objects and find the first
        that matches this attribute name; then return a reference to this attribute.

        >>> class Mock(Music21Object): attr1=234
        >>> aObj = Mock()
        >>> bObj = Mock()
        >>> bObj.attr1 = 98
        >>> aContexts = Contexts()
        >>> aContexts.addReference(aObj)
        >>> aContexts.addReference(bObj)
        >>> aContexts.getAttrByName('attr1') == 98
        True
        >>> del bObj
        >>> aContexts.getAttrByName('attr1') == 234
        True
        '''
        post = None
        for obj in self.get(domain=domain):
            if obj is None: continue # in case the reference is dead
            try:
                post = getattr(obj, attrName)
                return post
            except AttributeError:
                pass

    def setAttrByName(self, attrName, value, domain=['rec', 'loc']):
        '''Given an attribute name, search all objects and find the first
        that matches this attribute name; then return a reference to this attribute.

        >>> class Mock(Music21Object): attr1=234
        >>> aObj = Mock()
        >>> bObj = Mock()
        >>> bObj.attr1 = 98
        >>> aContexts = Contexts()
        >>> aContexts.addReference(aObj)
        >>> aContexts.addReference(bObj)
        >>> aContexts.setAttrByName('attr1', 'test')
        >>> aContexts.getAttrByName('attr1') == 'test'
        True
        '''
        post = None
        for obj in self.get(domain=domain):
            if obj is None: continue # in case the reference is dead
            try:
                junk = getattr(obj, attrName) # if attr already exists
                setattr(obj, attrName, value) # if attr already exists
            except AttributeError:
                pass



    def find(self, classList, recursive=True, hasAttr=None):
        pass


#-------------------------------------------------------------------------------
class Locations(object):
    '''An object, stored within a Music21Object, that manages site/offset pairs. 
    Site is an object that contains an object; site may be a parent. 
    Sites are always stored as weak refs.
    
    An object may store None as a site -- this becomes the default offset
    for any newly added sites that do not have any sites
    '''
    def __init__(self):
        self.coordinates = {} # a dictionary of dictionaries

    def __len__(self):
        '''Return the total number of offsets.
        >>> class Mock(Music21Object): pass
        >>> aSite = Mock()
        >>> bSite = Mock()
        >>> aLocations = Locations()
        >>> aLocations.add(843, aSite)
        >>> aLocations.add(12, bSite) # can add at same offset or different
        >>> len(aLocations)
        2
        '''
        return len(self.coordinates)

    def __deepcopy__(self, memo=None):
        '''This produces a new, independent locations object.
        This does not, however, deepcopy site references stored therein

        >>> class Mock(Music21Object): pass
        >>> aSite = Mock()
        >>> bSite = Mock()
        >>> aLocations = Locations()
        >>> aLocations.add(843, aSite)
        >>> aLocations.add(12, bSite) # can add at same offset or different
        >>> bLocations = copy.deepcopy(aLocations)
        >>> aLocations != bLocations
        True
        
        #>>> aLocations.getSiteByIndex(-1) == bLocations.getSiteByIndex(-1)      
        #True
        '''
        new = self.__class__()
        for siteId in self.coordinates:
            dict = self.coordinates[siteId]
            new.add(dict['offset'], dict['site'], dict['time'], siteId)

        return new


    def scrubEmptySites(self):
        '''If a parent has been deleted, we will still have an empty ref in 
        coordinates; when called, this empty ref will return None.
        This method will remove all parents that deref to None

        DOES NOT WORK IF A FULLREF, NOT WEAKREF IS STORED

        >>> class Mock(Music21Object): pass
        >>> aSite = Mock()
        >>> bSite = Mock()
        >>> aLocations = Locations()
        >>> aLocations.add(0, aSite)
        >>> aLocations.add(234, bSite)
        >>> del aSite
        >>> len(aLocations)
        2
        >>> #aLocations.scrubEmptySites()
        >>> #len(aLocations)
        #1
        '''
        delList = []
        for i in self.coordinates:
            s = self.coordinates[i]['site']
            if s is None:
                continue
            if common.unwrapWeakref(s) is None:
                delList.append(i)
        delList.reverse() # go in reverse from largest to maintain positions
        for i in delList:
            del self.coordinates[i]

    def clear(self):
        '''Clear all data.
        '''
        self.coordinates = {}

    def getSites(self):
        '''Get parents; unwrap from weakrefs
        '''
        #environLocal.printDebug([self.coordinates])
        if WEAKREF_ACTIVE:
            post = []
            for cokey in self.coordinates:
                s1 = self.coordinates[cokey]['site']
                if s1 is None: # leave None alone
                    post.append(None)
                else:
                    post.append(common.unwrapWeakref(s1))
            return post
        else:
            return [self.coordinates[x]['site'] for x in self.coordinates]

    def getOffsets(self):
        '''Return a list of all offsets.

        >>> class Mock(Music21Object): pass
        >>> aSite = Mock()
        >>> bSite = Mock()
        >>> aLocations = Locations()
        >>> aLocations.add(0, aSite)
        >>> aLocations.add(234, bSite) # can add at same offset or another
        >>> aLocations.getOffsets()
        [0, 234]
        '''
        return [self.coordinates[x]['offset'] for x in self.coordinates]   

    def getTimes(self):
        return [self.coordinates[x]['time'] for x in self.coordinates]   

    def add(self, offset, site, timeValue=None, siteId=None):
        '''Add a location to the object.

        If site already exists, this will update that entry. 

        >>> class Mock(Music21Object): pass
        >>> aSite = Mock()
        >>> bSite = Mock()
        >>> aLocations = Locations()
        >>> aLocations.add(23, aSite)
        >>> aLocations.add(23, bSite) # can add at same offset
        >>> aLocations.add(12, aSite) # will change the offset for aSite
        >>> aSite == aLocations.getSiteByOffset(12)
        True
        '''
        ## should NOT be a weakref, but never can be too sure...
        site = common.unwrapWeakref(site)

#        if not common.isNum(offset):
#            raise LocationsException("offset must be a number (later, a Duration might be allowed)")

        if siteId is None and site is not None:
            siteId = id(site)
        if siteId not in self.coordinates:
            self.coordinates[siteId] = {}

        if WEAKREF_ACTIVE:
            if site is None: # leave None alone
                siteRef = site
            else:
                siteRef = common.wrapWeakref(site)
        else:
            siteRef = site

        # site here is wrapped in weakref
        self.coordinates[siteId]['site'] = siteRef

        self.coordinates[siteId]['offset'] = offset

        # store creation time in order to sort by time
        if timeValue is None:
            self.coordinates[siteId]['time'] = time.time()
        else: # a time value might be provided
            self.coordinates[siteId]['time'] = timeValue

    def remove(self, site):
        '''Remove the entry specified by sites

        >>> class Mock(Music21Object): pass
        >>> aSite = Mock()
        >>> bSite = Mock()
        >>> aLocations = Locations()
        >>> aLocations.add(23, aSite)
        >>> len(aLocations)
        1
        >>> aLocations.remove(aSite)
        >>> len(aLocations)
        0
        
        '''
        siteId = None
        if site is not None: 
            siteId = id(site)
        
        if not siteId in self.coordinates: 
            raise LocationsException('an entry for this object (%s) is not stored in Locations' % site)
        del self.coordinates[siteId]


    def getOffsetBySite(self, site):
        '''For a given site return its offset.

        >>> class Mock(Music21Object): pass
        >>> aSite = Mock()
        >>> bSite = Mock()
        >>> cParent = Mock()
        >>> aLocations = Locations()
        >>> aLocations.add(23, aSite)
        >>> aLocations.add(121.5, bSite)
        >>> aLocations.getOffsetBySite(aSite)
        23
        >>> aLocations.getOffsetBySite(bSite)
        121.5
        >>> aLocations.getOffsetBySite(cParent)    
        Traceback (most recent call last):
        LocationsException: ...
        '''

        siteId = None
        if site is not None:
            siteId = id(site)
        if not siteId in self.coordinates: 
            raise LocationsException('an entry for this object (%s) is not stored in Locations' % siteId)

        return self.coordinates[siteId]['offset']


    def setOffsetBySite(self, site, value):
        '''
        Changes the offset of the site specified.  Note that this can also be
        done with add, but the difference is that if the site is not in 
        Locations, it will raise an exception.
        
        >>> class Mock(Music21Object): pass
        >>> aSite = Mock()
        >>> bSite = Mock()
        >>> cSite = Mock()
        >>> aLocations = Locations()
        >>> aLocations.add(23, aSite)
        >>> aLocations.add(121.5, bSite)
        >>> aLocations.setOffsetBySite(aSite, 20)
        >>> aLocations.getOffsetBySite(aSite)
        20
        >>> aLocations.setOffsetBySite(cSite, 30)        
        Traceback (most recent call last):
        LocationsException: ...
        '''
        siteId = None
        if site is not None:
            siteId = id(site)
        if siteId in self.coordinates: 
            #environLocal.printDebug(['site already defined in this Locations object', site])
            # order is the same as in coordinates
            self.coordinates[siteId]['offset'] = value
        else:
            raise LocationsException('an entry for this object (%s) is not stored in Locations' % site)


#    def getOffsetByIndex(self, index):
#        '''For a given parent return an offset.
#
#        >>> class Mock(Music21Object): pass
#        >>> aSite = Mock()
#        >>> bSite = Mock()
#        >>> aLocations = Locations()
#        >>> aLocations.add(23, aSite)
#        >>> aLocations.add(121.5, bSite)
#        >>> aLocations.getOffsetByIndex(-1)
#        121.5
#        >>> aLocations.getOffsetByIndex(2)
#        Traceback (most recent call last):
#        IndexError: list index out of range
#        '''
#        return self.coordinates[index]['offset']



    def getSiteByOffset(self, offset):
        '''For a given offset return the parent

        ####More than one parent may have the same offset; 
        ####this will return the last site added.
        No - now we use a dict, so there's no guarantee that the one you want will be there -- need orderedDicts!

        >>> class Mock(Music21Object): pass
        >>> aSite = Mock()
        >>> bSite = Mock()
        >>> cSite = Mock()
        >>> aLocations = Locations()
        >>> aLocations.add(23, aSite)
        >>> aLocations.add(121.5, bSite)
        >>> aSite == aLocations.getSiteByOffset(23)
        True
        
        #### no longer works
        #Adding another site at offset 23 will change getSiteByOffset
        #>>> aLocations.add(23, cSite)
        #>>> aSite == aLocations.getSiteByOffset(23)
        #False
        #>>> cSite == aLocations.getSiteByOffset(23)
        #True
        '''
        match = None
        # assume that last added offset is more likely the first needed
        # access index values in reverse from highest to 0
#        for i in range(len(self.coordinates)-1, -1, -1):
        for siteIndex in self.coordinates:
            # might need to use almost equals here
            if self.coordinates[siteIndex]['offset'] == offset:
                match = self.coordinates[siteIndex]['site']
                break
        if WEAKREF_ACTIVE:
            if match is None:
                return match
            if not common.isWeakref(match):
                raise LocationsException('site on coordinates is not a weak ref: %s' % match)
            return common.unwrapWeakref(match)
        else:
            return match


#    def getSiteByIndex(self, index):
#        '''Get parent by index value, unwrapping the weakref.
#
#        >>> class Mock(Music21Object): pass
#        >>> aSite = Mock()
#        >>> bSite = Mock()
#        >>> aLocations = Locations()
#        >>> aLocations.add(23, aSite)
#        >>> aLocations.add(121.5, bSite)
#        >>> bSite == aLocations.getSiteByIndex(-1)
#        True
#        '''
#        siteRef = self.coordinates[index]['site']
#        if WEAKREF_ACTIVE:
#            if siteRef is None: # let None parents pass
#                return siteRef
#            if not common.isWeakref(siteRef):
#                raise LocationsException('parent on coordinates is not a weakref: %s' % siteRef)
#            return common.unwrapWeakref(siteRef)
#        else:
#            return siteRef





#-------------------------------------------------------------------------------
class Music21Object(object):
    '''
    Base class for all music21 objects
    
    All music21 objects encode 7 pieces of information:
    
    (1) id        : unique identification string (optional)
    (2) groups    : a Groups object: which is a list of strings identifying 
                    internal subcollections
                    (voices, parts, selections) to which this element belongs
    (3) duration  : Duration object representing the length of the object
    (4) locations : a Locations object (see above) that specifies connections of
                    this object to one location in another object
    (5) parent    : a reference or weakreference to a currently active Location
    (6) offset    : a float or duration specifying the position of the object in parent 
    (7) contexts  : a list of references or weakrefs for current contexts 
                    of the object (similar to locations but without an offset)
    (8) priority  : int representing the position of an object among all
                    objects at the same offset.

    
    Each of these may be passed in as a named keyword to any music21 object.
    Some of these may be intercepted by the subclassing object (e.g., duration within Note)

    '''

    _duration = None
    contexts = None
    id = None
    _priority = 0
    _overriddenLily = None
    # None is stored as the internal location of an obj w/o a parent
    _currentParent = None
    _currentParentId = None # cached id in case the weakref has gone away...

    def __init__(self, *arguments, **keywords):
        # an offset keyword arg should set the offset in location
        # not in a local parameter
#         if "offset" in keywords and not self.offset:
#             self.offset = keywords["offset"]

        if "id" in keywords and not self.id:
            self.id = keywords["id"]            
        else:
            self.id = id(self)
        
        if "duration" in keywords and self.duration is None:
            self.duration = keywords["duration"]
        
        if "groups" in keywords and keywords["groups"] is not None and \
            (not hasattr(self, "groups") or self.groups is None):
            self.groups = keywords["groups"]
        elif not hasattr(self, "groups"):
            self.groups = Groups()
        elif self.groups is None:
            self.groups = Groups()

        if "locations" in keywords and self.locations is None:
            self.locations = keywords["locations"]
        else:
            self.locations = Locations()
            # set up a default location for self at zero
            # use None as the name of the site
            self.locations.add(0.0, None)

        if "parent" in keywords and self.parent is None:
            self.parent = keywords["parent"]
        
        if "contexts" in keywords and keywords["contexts"] is not None and self.contexts is None:
            self.contexts = keywords["contexts"]
        elif self.contexts is None:
            self.contexts = []
    

    def __deepcopy__(self, memo=None):
        '''
        Helper method to copy.py's deepcopy function.  Call it from there

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
        #for name in dir(self):
        for name in self.__dict__.keys():

            if name.startswith('__'):
                continue
           
            part = getattr(self, name)
            
            # attributes that require special handling
            if name == '_currentParent':
                #environLocal.printDebug(['creating parent reference'])
                newValue = self.parent # keep a reference, not a deepcopy
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
                
        return new


    def isClass(self, className):
        '''
        returns bool depending on if the object is a particular class or not
        
        here, it just returns isinstance, but for Elements it will return true
        if the embedded object is of the given class.  Thus, best to use it throughout
        music21 and only use isinstance if you really want to see if something is
        an ElementWrapper or not.
        '''
        if isinstance(self, className):
            return True
        else:
            return False

    
    #---------------------------------------------------------------------------
    # look at this object for an atttribute; if not here
    # look up to parents

    def searchParent(self, attrName):
        '''If this element is contained within a Stream or other Music21 element, 
        searchParent() permits searching attributes of higher-level
        objects. The first encountered match is returned, or None if no match.
        '''
        found = None
        try:
            found = getattr(self.parent, attrName)
        except AttributeError:
            # not sure of passing here is the best action
            environLocal.printDebug(['searchParent call raised attribute error for attribute:', attrName])
            pass
        if found is None:
            found = self.parent.searchParent(attrName)
        return found
        

    def getOffsetBySite(self, site):
        '''
        >>> a = Music21Object()
        >>> a.offset = 30
        >>> a.getOffsetBySite(None)
        30.0
        '''
#         if site == self:
#             site = None # shortcut
        return self.locations.getOffsetBySite(site)

    #---------------------------------------------------------------------------
    # properties

    def _getParent(self):
        # can be None
        if WEAKREF_ACTIVE:
            if self._currentParent is None: #leave None
                return self._currentParent
            else:
                return common.unwrapWeakref(self._currentParent)
        else:
            return self._currentParent

#         if self._currentParent is not None:
#             return self._currentParent
#         elif len(self.locations) == 0:
#             return None # return None if no sites set
#         else: 
#             return self.locations.getSiteByIndex(-1) 

    
    def _setParent(self, site):
#         if site == self:
#             site = None # shortcut translation

        siteId = None
        if site is not None: 
            siteId = id(site)
        if site is not None and \
            siteId not in self.locations.coordinates:
            self.locations.add(self.offset, site, siteId = siteId) 
        
        if WEAKREF_ACTIVE:
            if site is None: # leave None alone
                self._currentParent = None
                self._currentParentId = None
            else:
                self._currentParent = common.wrapWeakref(site)
                self._currentParentId = siteId
        else:
            self._currentParent = site
            self._currentParentId = siteId


    parent = property(_getParent, _setParent)



    def _getOffset(self):
        '''

        '''
        #there is a problem if a new parent is being set and no offsets have 
        # been provided for that parent; when self.offset is called, 
        # the first case here would match

        parentId = None
        if self.parent is not None:
            parentId = id(self.parent)
        elif self._currentParentId is not None:
            parentId = self._currentParentId
        
        if parentId is not None and parentId in self.locations.coordinates:
            return self.locations.coordinates[parentId]['offset']
        elif self.parent is None: # assume we want self
            return self.locations.getOffsetBySite(None)
        else:
            raise Exception('request for offset cannot be made with parent of %s (id: %s)' % (self.parent, parentId))            

    def _setOffset(self, value):
        if common.isNum(value):
            # if a number assume it is a quarter length
            # self._offset = duration.DurationUnit()
            # MSC: We can change this when we decide that we want to return
            #      something other than quarterLength

            offset = float(value)
        elif hasattr(value, "quarterLength"):
            ## probably a Duration object, but could be something else -- in any case, 
            ## we'll take it.
            offset = value.quarterLength
        else:
            raise Exception, 'We cannot set  %s as an offset' % value
 
        self.locations.setOffsetBySite(self.parent, offset)
#        if self.parent is None:
            # a None parent gets the offset at self
#            self.locations.setOffsetBySite(None, offset)
            #self.disconnectedOffset = offset
#        else:
#            self.locations.setOffsetBySite(self.parent, offset)
    
    offset = property(_getOffset, _setOffset)


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
            raise Exception, 'this must be a Duration object, not %s' % durationObj

    duration = property(_getDuration, _setDuration)

    def _getPriority(self):
        return self._priority

    def _setPriority(self, value):
        '''
        value is an int.
        
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
        
        >>> a = Music21Object()
        >>> a.priority = 3
        >>> a.priority = 'high'
        Traceback (most recent call last):
        ElementException: priority values must be integers.
        '''
        if not isinstance(value, int):
            raise ElementException('priority values must be integers.')
        self._priority = value

    priority = property(_getPriority, _setPriority)


    #---------------------------------------------------------------------------
    def write(self, fmt='musicxml', fp=None):
        '''Write a file.
        
        A None file path will result in temporary file
        '''
        format, ext = common.findFormat(fmt)
        if format is None:
            raise Music21ObjectException('bad format (%s) provided to write()' % fmt)
        elif format == 'text':
            if fp is None:
                fp = environLocal.getTempFile(ext)
            dataStr = self._reprText()
        elif format == 'musicxml':
            if fp is None:
                fp = environLocal.getTempFile(ext)
            dataStr = self.musicxml
        else:
            raise Music21ObjectException('cannot support writing in this format, %s yet' % format)
        f = open(fp, 'w')
        f.write(dataStr)
        f.close()
        return fp


    def _reprText(self):
        '''Retrun a text representation. This methods can be overridden by
        subclasses to provide alternative text representations.
        '''
        return self.__repr__()


    def show(self, fmt='musicxml'):
        '''
        Displays an object in the given format (default: musicxml) using the default display
        tools.
        
        This might need to return the file path.
        '''
        format, ext = common.findFormat(fmt)
        if format == 'text':
            print(self._reprText())
        else: # a format that writes a file
            environLocal.launch(format, self.write(format))



#-------------------------------------------------------------------------------
class ElementWrapper(Music21Object):
    '''
    An element wraps an object so that the same object can
    be positioned within a stream.
    
    The object is always available as element.obj -- however, calls to
    the ElementWrapper will call 
    
    Object is now mandatory -- calls to ElementWrapper without an object fail,
    because in the new (11/29) object model, ElementWrapper should only be used
    to wrap an object.
    
    '''
    obj = None
    _id = None

    def __init__(self, obj):
        Music21Object.__init__(self)
        self.obj = obj # object stored here        
        self._unlinkedDuration = None

    def isClass(self, className):
        '''
        Returns true if the object embedded is a particular class.

        Used by getElementsByClass in Stream

        >>> import note
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
        if isinstance(self.obj, className):
            return True
        else:
            return False

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
        new.contexts = copy.deepcopy(self.contexts)
        new.locations = copy.deepcopy(self.locations)
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
        new.locations = copy.deepcopy(self.locations)
        new.obj = copy.deepcopy(self.obj)
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
            raise Exception, 'this must be a Duration object, not %s' % durationObj
        
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
           not hasattr(other, "parent") or \
           not hasattr(other, "duration"):
            return False


        if (self.obj == other.obj and \
            self.offset == other.offset and \
            self.priority == other.priority and \
            self.id == other.id and \
            self.groups == other.groups and \
            self.parent == other.parent and \
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

        if name in self.__dict__:  # if in the ElementWrapper already, set that first
            object.__setattr__(self, name, value)
        
        # if not, change the attribute in the stored object
        storedobj = object.__getattribute__(self, "obj")
        if name not in ['offset', '_offset', '_currentParent'] and \
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
        a weaker form of equality.  a.isTwin(b) is true if
        a and b store either the same object OR objects that are equal
        and a.groups == b.groups 
        and a.id == b.id (or both are none) and duration are equal.
        but does not require position, priority, or parent to be the same
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
        note1.type = "whole"
        stream1 = stream.Stream()
        stream1.append(note1)
        subStream = stream1.getNotes()

    def testLocationsRefs(self):
        aMock = TestMock()
        bMock = TestMock()

        loc = Locations()
        loc.add(234, aMock)
        loc.add(12, bMock)
        
#        self.assertEqual(loc.getOffsetByIndex(-1), 12)
        self.assertEqual(loc.getOffsetBySite(aMock), 234)
        self.assertEqual(loc.getSiteByOffset(234), aMock)
#        self.assertEqual(loc.getSiteByIndex(-1), bMock)

        #del aMock
        # if the parent has been deleted, the None will be returned
        # even though there is still an entry
        #self.assertEqual(loc.getSiteByIndex(0), None)


    def testLocationsNone(self):
        '''Test assigning a None to parent
        '''
        loc = Locations()
        loc.add(0, None)



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

        # storing a single offset does not add a Locations entry  
        a.offset = 30
        # all offsets are store in locations
        self.assertEqual(len(a.locations), 1)
        self.assertEqual(a.getOffsetBySite(None), 30.0)
        self.assertEqual(a.offset, 30.0)

        # assigning a parent directly
        a.parent = b
        # now we have two offsets in locations
        self.assertEqual(len(a.locations), 2)

        a.offset = 40
        # still have parent
        self.assertEqual(a.parent, b)
        # now the offst returns the value for the current parent 
        self.assertEqual(a.offset, 40.0)

        # assigning a parent to None
        a.parent = None
        # properly returns original offset
        self.assertEqual(a.offset, 30.0)
        # we still have two locations stored
        self.assertEqual(len(a.locations), 2)
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
            b.parent = a
            c = copy.deepcopy(b)
            c.id = "c obj"
            post.append(c)

        # have two locations: None, and that set by assigning parent
        self.assertEqual(len(b.locations), 2)
        g = post[-1].locations
        self.assertEqual(len(post[-1].locations), 2)

        # this now works
        self.assertEqual(post[-1].parent, a)


        a = Music21Object()

        post = []
        for x in range(30):
            b = Music21Object()
            b.id = 'test'
            b.parent = a
            b.offset = 30
            c = copy.deepcopy(b)
            c.parent = b
            post.append(c)

        self.assertEqual(len(post[-1].locations), 3)

        # this works because the parent is being set on the object
        self.assertEqual(post[-1].parent, b)
        # the copied parent has been deepcopied, and cannot now be accessed
        # this fails! post[-1].getOffsetBySite(a)



def mainTest(*testClasses):
    '''
    Takes as its arguments modules (or a string 'noDocTest')
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
        s1 = doctest.DocTestSuite('__main__', optionflags = (doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE))

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

if __name__ == "__main__":
    mainTest(Test)