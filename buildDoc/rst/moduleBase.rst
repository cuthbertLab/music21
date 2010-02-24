.. _moduleBase:

music21.base
============



Music21 base classes and important utilities

base -- the convention within music21 is that __init__ files contain:

   from base import *
   
so everything in this file can be accessed as music21.XXXX

Class ElementWrapper
--------------------

Inherits from: base.Music21Object, object

An element wraps an object so that the same object can be positioned within a stream. The object is always available as element.obj -- however, calls to the ElementWrapper will call Object is now mandatory -- calls to ElementWrapper without an object fail, because in the new (11/29) object model, ElementWrapper should only be used to wrap an object. 



Methods
~~~~~~~


Inherited from base.Music21Object

**write()**

**show()**

**searchParent()**

**isClass()**

**getOffsetBySite()**

**contexts()**

**addLocationAndParent()**


Locally Defined

**setId()**


**obj()**


**isTwin()**

    a weaker form of equality.  a.isTwin(b) is true if a and b store either the same object OR objects that are equal and a.groups == b.groups and a.id == b.id (or both are none) and duration are equal. but does not require position, priority, or parent to be the same In other words, is essentially the same object in a different context 

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

**getId()**


Properties
~~~~~~~~~~


Inherited from base.Music21Object

**priority**

**parent**

**offset**

**id**

**duration**


Class Groups
------------

Inherits from: list, object

A list of strings used to identify associations that an element might have. Enforces that all elements must be strings 

>>> g = Groups()
>>> g.append("hello")
>>> g[0]
'hello' 
>>> g.append(5)
Traceback (most recent call last): 
GroupException: Only strings can be used as list names 

Methods
~~~~~~~


Inherited from list

**sort()**

**reverse()**

**remove()**

**pop()**

**insert()**

**index()**

**extend()**

**count()**

**append()**


Class Locations
---------------

Inherits from: object

An object, stored within a Music21Object, that manages site/offset pairs. Site is an object that contains an object; site may be a parent. Sites are always stored as weak refs. An object may store None as a site -- this becomes the default offset for any newly added sites that do not have any sites 

Attributes
~~~~~~~~~~

**coordinates**

Methods
~~~~~~~


Locally Defined

**setOffsetBySite()**

    Changes the offset of the site specified.  Note that this can also be done with add, but the difference is that if the site is not in Locations, it will raise an exception. 

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

**scrubEmptySites()**

    If a parent has been deleted, we will still have an empty ref in coordinates; when called, this empty ref will return None. This method will remove all parents that deref to None DOES NOT WORK IF A FULLREF, NOT WEAKREF IS STORED 

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

**remove()**

    Remove the entry specified by sites 

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

**getTimes()**


**getSites()**

    Get parents; unwrap from weakrefs 

**getSiteByOffset()**

    For a given offset return the parent # More than one parent may have the same offset; # this can return the last site added by sorting time No - now we use a dict, so there's no guarantee that the one you want will be there -- need orderedDicts! 

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

**getOffsets()**

    Return a list of all offsets. 

    >>> class Mock(Music21Object): pass
    >>> aSite = Mock()
    >>> bSite = Mock()
    >>> aLocations = Locations()
    >>> aLocations.add(0, aSite)
    >>> aLocations.add(234, bSite) # can add at same offset or another
    >>> aLocations.getOffsets()
    [0, 234] 

**getOffsetBySite()**

    For a given site return its offset. 

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

**clear()**

    Clear all data. 

**add()**

    Add a location to the object. If site already exists, this will update that entry. 

    >>> class Mock(Music21Object): pass
    >>> aSite = Mock()
    >>> bSite = Mock()
    >>> aLocations = Locations()
    >>> aLocations.add(23, aSite)
    >>> aLocations.add(23, bSite) # can add at same offset
    >>> aLocations.add(12, aSite) # will change the offset for aSite
    >>> aSite == aLocations.getSiteByOffset(12)
    True 


Class Music21Object
-------------------

Inherits from: object

Base class for all music21 objects All music21 objects encode 7 pieces of information: (1) id        : unique identification string (optional) (2) groups    : a Groups object: which is a list of strings identifying internal subcollections (voices, parts, selections) to which this element belongs (3) duration  : Duration object representing the length of the object (4) locations : a Locations object (see above) that specifies connections of this object to one location in another object (5) parent    : a reference or weakreference to a currently active Location (6) offset    : a float or duration specifying the position of the object in parent (7) contexts  : a list of references or weakrefs for current contexts of the object (similar to locations but without an offset) (8) priority  : int representing the position of an object among all objects at the same offset. 

Each of these may be passed in as a named keyword to any music21 object. Some of these may be intercepted by the subclassing object (e.g., duration within Note) 



Attributes
~~~~~~~~~~

**contexts**

**groups**

**id**

**locations**

Methods
~~~~~~~


Locally Defined

**write()**

    Write a file. A None file path will result in temporary file 

**show()**

    Displays an object in the given format (default: musicxml) using the default display tools. This might need to return the file path. 

**searchParent()**

    If this element is contained within a Stream or other Music21 element, searchParent() permits searching attributes of higher-level objects. The first encountered match is returned, or None if no match. 

**isClass()**

    returns bool depending on if the object is a particular class or not here, it just returns isinstance, but for Elements it will return true if the embedded object is of the given class.  Thus, best to use it throughout music21 and only use isinstance if you really want to see if something is an ElementWrapper or not. 

**id()**


**getOffsetBySite()**

    

    >>> a = Music21Object()
    >>> a.offset = 30
    >>> a.getOffsetBySite(None)
    30.0 

**contexts()**


**addLocationAndParent()**

    ADVANCED: a speedup tool that adds a new location element and a new parent.  Called by Stream.insert -- this saves some dual processing.  Does not do safety checks that the siteId doesn't already exist etc., because that is done earlier. This speeds up things like stream.getElementsById substantially. Testing script (N.B. manipulates Stream._elements directly -- so not to be emulated) 

    >>> from stream import Stream
    >>> st1 = Stream()
    >>> o1 = Music21Object()
    >>> st1_wr = common.wrapWeakref(st1)
    >>> offset = 20.0
    >>> st1._elements = [o1]
    >>> o1.addLocationAndParent(offset, st1, st1_wr)
    >>> o1.parent is st1
    True 
    >>> o1.getOffsetBySite(st1)
    20.0 

Properties
~~~~~~~~~~


Locally Defined

**priority**


**parent**


**offset**

    

    

    

**duration**

    Gets the DurationObject of the object or None 

    


Class Relations
---------------

Inherits from: object

An object, stored within a Music21Object, that provides a collection of objects that may be contextually relevant. 

Methods
~~~~~~~


Locally Defined

**setOffsetBySite()**

    Changes the offset of the site specified.  Note that this can also be done with add, but the difference is that if the site is not in Relations, it will raise an exception. 

    >>> class Mock(Music21Object): pass
    >>> aSite = Mock()
    >>> bSite = Mock()
    >>> cSite = Mock()
    >>> aLocations = Relations()
    >>> aLocations.add(aSite, 23)
    >>> aLocations.add(bSite, 121.5)
    >>> aLocations.setOffsetBySite(aSite, 20)
    >>> aLocations.getOffsetBySite(aSite)
    20 
    >>> aLocations.setOffsetBySite(cSite, 30)
    Traceback (most recent call last): 
    RelationsException: ... 

**setAttrByName()**

    Given an attribute name, search all objects and find the first that matches this attribute name; then return a reference to this attribute. 

    >>> class Mock(Music21Object): attr1=234
    >>> aObj = Mock()
    >>> bObj = Mock()
    >>> bObj.attr1 = 98
    >>> aRelations = Relations()
    >>> aRelations.add(aObj)
    >>> aRelations.add(bObj)
    >>> aRelations.setAttrByName('attr1', 'test')
    >>> aRelations.getAttrByName('attr1') == 'test'
    True 

**scrub()**

    Remove all weak ref objects that point to objects that no longer exist. 

**removeById()**


**getSiteByOffset()**

    For a given offset return the parent # More than one parent may have the same offset; # this can return the last site added by sorting time No - now we use a dict, so there's no guarantee that the one you want will be there -- need orderedDicts! 

    >>> class Mock(Music21Object): pass
    >>> aSite = Mock()
    >>> bSite = Mock()
    >>> cSite = Mock()
    >>> aLocations = Relations()
    >>> aLocations.add(aSite, 23)
    >>> aLocations.add(bSite, 23121.5)
    >>> aSite == aLocations.getSiteByOffset(23)
    True 
    #### no longer works 
    #Adding another site at offset 23 will change getSiteByOffset 
    #>>> aLocations.add(cSite, 23) 
    #>>> aSite == aLocations.getSiteByOffset(23) 
    #False 
    #>>> cSite == aLocations.getSiteByOffset(23) 
    #True 

**getOffsets()**

    Return a list of all offsets. 

    >>> class Mock(Music21Object): pass
    >>> aSite = Mock()
    >>> bSite = Mock()
    >>> cSite = Mock()
    >>> dSite = Mock()
    >>> aLocations = Relations()
    >>> aLocations.add(aSite, 0)
    >>> aLocations.add(cSite) # a context
    >>> aLocations.add(bSite, 234) # can add at same offset or another
    >>> aLocations.add(dSite) # a context
    >>> aLocations.getOffsets()
    [0, 234] 

**getOffsetBySite()**

    For a given site return its offset. 

    >>> class Mock(Music21Object): pass
    >>> aSite = Mock()
    >>> bSite = Mock()
    >>> cParent = Mock()
    >>> aLocations = Relations()
    >>> aLocations.add(aSite, 23)
    >>> aLocations.add(bSite, 121.5)
    >>> aLocations.getOffsetBySite(aSite)
    23 
    >>> aLocations.getOffsetBySite(bSite)
    121.5 
    >>> aLocations.getOffsetBySite(cParent)
    Traceback (most recent call last): 
    RelationsException: ... 

**getByClass()**

    Return the most recently added reference based on className. Class name can be a string or the real class name. TODO: do this recursively, searching the Relations of all members 

    >>> class Mock(Music21Object): pass
    >>> aObj = Mock()
    >>> bObj = Mock()
    >>> aRelations = Relations()
    >>> aRelations.add(aObj)
    >>> aRelations.add(bObj)
    >>> aRelations.getByClass('mock') == aObj
    True 
    >>> aRelations.getByClass(Mock) == aObj
    True 

    

**getAttrByName()**

    Given an attribute name, search all objects and find the first that matches this attribute name; then return a reference to this attribute. 

    >>> class Mock(Music21Object): attr1=234
    >>> aObj = Mock()
    >>> bObj = Mock()
    >>> bObj.attr1 = 98
    >>> aRelations = Relations()
    >>> aRelations.add(aObj)
    >>> aRelations.getAttrByName('attr1') == 234
    True 
    >>> aRelations.removeById(id(aObj))
    >>> aRelations.add(bObj)
    >>> aRelations.getAttrByName('attr1') == 98
    True 

**get()**

    Get references; unwrap from weakrefs; place in order from most recently added to least recently added 

    >>> class Mock(Music21Object): pass
    >>> aObj = Mock()
    >>> bObj = Mock()
    >>> aRelations = Relations()
    >>> aRelations.add(aObj)
    >>> aRelations.add(bObj)
    >>> aRelations.get('contexts') == [aObj, bObj]
    True 

**clear()**

    Clear all data. 

**add()**

    Add a reference if offset is None, it is interpreted as a context if offset is a value, it is intereted as location NOTE: offset follows obj here, unlike with add() in old Locations 


