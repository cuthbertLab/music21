# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         freezeThaw.py
# Purpose:      Methods for storing any music21 object on disk.  
#               Uses pickle and jsonpickle
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2011-2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL, see license.txt
#-------------------------------------------------------------------------------
r'''
This module contains objects for storing complete `Music21Objects`, especially
`Stream` and `Score` objects on disk.  Freezing (or "pickling") refers to writing
the object to a file on disk (or to a string).  Thawing (or "unpickling") refers to reading
in a string or file and returning a Music21 object.

This module offers alternatives to writing a `Score` to `MusicXML` with 
`s.write('musicxml')`.  `FreezeThaw` has some advantages over using `.write()`:
virtually every aspect of a music21 object is retained when Freezing.  So
objects like `medRen.Ligature`, which aren't supported by most formats,
can be stored with `FreezeThaw` and then read back again.  Freezing is also
much faster than most conversion methods.  But there's a big downside:
only `music21` and `Python` can use the `Thaw` side to get back `Music21Objects` 
(though
some information can be brought out of the JSONFreeze format through
any .json reader).  In fact, there's not even a guarantee that future versions of music21
will be able to read a frozen version of a `Stream`.  So the advantages and
disadvantages of this model definitely need to be kept in mind.

There are two formats that `freezeThaw` can produce: "Pickle" or JSON (for JavaScript Object
Notation -- essentially a string representation of the JavaScript equivalent
of a Python dictionary).  Pickle is a Python-specific idea for storing objects.
The `pickle` module stores objects as a text file that can't be easily read by
non-Python applications; it also isn't guaranteed to work across Python versions or
even computers.  However, it works well, is fast, and is a standard part of python.
JSON was originally created to pass JavaScript
objects from a web server to a web browser, but its utility (combining the power
of XML with the ease of use of objects) has made it a growing standard for
other languages.  (see http://docs.python.org/library/json.html). 

Both JSON and Pickle files can
be huge, but `freezeThaw` can compress them with `gzip` or `ZipFile` and thus they're
not that large at all. Our implementation of JSON serialization uses the freely distributable `jsonpickle`
module found in `music21.ext.jsonpickle`.  See that folder's "license.txt" for
copyright information.

.. warning: 
    Current versions of jsonpickle do not recreate the same
    object structures when decoded, so it can't really be used
    with complex nesting structures like music21 creates.  For instance:

    >>> from music21.ext import jsonpickle as jsp
    >>> blah = {'hello': 'there'}
    >>> l = [blah, blah]
    >>> l[0] is l[1]
    True
    >>> d = jsp.encode(l)
    >>> print d
    [{"hello": "there"}, {"hello": "there"}]
    >>> e = jsp.decode(d)
    >>> e
    [{u'hello': u'there'}, {u'hello': u'there'}]
    >>> e[0] is e[1]
    False
    
    However, pickle works fine, so we use that by default:
    
    >>> import pickle
    >>> f = pickle.dumps(l)
    >>> f
    "(lp0\n(dp1\nS'hello'\np2\nS'there'\np3\nsag1\na."
    
    Pretty ugly, eh? but it works!
    
    >>> g = pickle.loads(f)
    >>> g
    [{'hello': 'there'}, {'hello': 'there'}]
    >>> g[0] is g[1]
    True

The name freezeThaw comes from Perl's implementation of similar methods -- I
like the idea of thawing something that's frozen; "unpickling" just doesn't
seem possible.  In any event, I needed a name that wouldn't already
exist in the Python namespace.
'''
import copy
import unittest
import os
import time

from music21 import base
from music21 import common
from music21 import derivation
from music21 import exceptions21
from music21.ext import jsonpickle

from music21 import environment
_MOD = "freezeThaw.py"
environLocal = environment.Environment(_MOD)


try:
    import cPickle as pickleMod
except ImportError:
    import pickle as pickleMod
#import pickle as pickleMod

#-------------------------------------------------------------------------------
class FreezeThawException(exceptions21.Music21Exception):
    pass

#-------------------------------------------------------------------------------
class StreamFreezeThawBase(object):
    '''
    Contains a few methods that are used for both
    StreamFreezer and StreamThawer
    '''
    def __init__(self):
        self.stream = None
    
    def teardownSerializationScaffold(self, streamObj = None):
        '''
        After rebuilding this Stream from pickled storage, prepare this as a normal `Stream`.

        Calls `wrapWeakRef` and `unFreezeIds` for the `Stream` and each sub-`Stream`.

        If streamObj is None, runs it on the embedded stream

        >>> from music21 import freezeThaw
        >>> from music21 import *
        
        >>> a = stream.Stream()
        >>> n = note.Note()
        >>> n.duration.type = "whole"
        >>> a.repeatAppend(n, 10)
        >>> sf = freezeThaw.StreamFreezer(a)
        >>> sf.setupSerializationScaffold()

        >>> st = freezeThaw.StreamThawer()
        >>> st.teardownSerializationScaffold(a)
        '''

        if streamObj is None:
            streamObj = self.stream
            if streamObj is None:
                raise FreezeThawException("You need to pass in a stream when creating to work")
        #environLocal.printDebug(['calling teardownSerializationScaffold', self])

        # turn off sorting before teardown
        # should save for all. but we don't...
        storedAutoSort = streamObj.autoSort
        streamObj.autoSort = False

        allEls = self.findAllM21Objects(streamObj)

        for e in allEls:
            if e.isVariant:
#                # works like a whole new hierarchy... # no need for deepcopy
#                print "TESST"
#                for el in e._stream.flat:
#                    print el.offset
#                for el in e._stream._elements[0]._storedElementOffsets:
#                    print el, e._stream._elements[0]._storedElementOffsets[el]
                subSF = StreamThawer()
                subSF.teardownSerializationScaffold(e._stream)
                e._stream._elementsChanged()
                e._cache = {}
                #for el in e._stream.flat:
                #    print el, el.offset, el._definedContexts._definedContexts
                    

            self.thawIds(e)
            e.wrapWeakref()

        # restore to whatever it was
        streamObj.autoSort = storedAutoSort
        streamObj._elementsChanged()
        containedStreams = streamObj.recurse(streamsOnly = True)
        for s in containedStreams:
            if hasattr(s, '_storedElementOffsets'):
                for e in s._elements:
                    if hasattr(e, "_preFreezeId"):
                        if e._preFreezeId in s._storedElementOffsets:
                            storedOffset = s._storedElementOffsets[e._preFreezeId]
                            e.setOffsetBySite(s, storedOffset)
                        del(e._preFreezeId)
                del(s._storedElementOffsets)
            s._elementsChanged()

    def thawIds(self, e):
        '''
        Restore keys to be the id() of the object they contain

        Does not do much, but calls thawContextIds on e.definedContexts
        which does a lot!

        TODO: Test Spanner

        >>> from music21 import freezeThaw
        >>> import music21

        >>> aM21Obj = music21.Music21Object()
        >>> bM21Obj = music21.Music21Object()
        >>> aM21Obj.offset = 30
        >>> aM21Obj.getOffsetBySite(None)
        30.0
        >>> bM21Obj.addLocationAndActiveSite(50, aM21Obj)   
        >>> bM21Obj.activeSite != None
        True
        
        >>> oldActiveSiteId = bM21Obj._activeSiteId
        
        >>> sf = freezeThaw.StreamFreezer()
        >>> sf.freezeIds(bM21Obj)

        >>> newActiveSiteId = bM21Obj._activeSiteId
        >>> oldActiveSiteId == newActiveSiteId
        False

        >>> st = freezeThaw.StreamThawer()
        >>> st.thawIds(bM21Obj)
        >>> postActiveSiteId = bM21Obj._activeSiteId
        >>> oldActiveSiteId == postActiveSiteId
        True
        '''
        #environLocal.printDebug(['unfreezing ids', self])
        self.thawContextIds(e._definedContexts)

        # restore containedById
        e._definedContexts.containedById = id(e)

        # assuming should be called before wrapping weakrefs
        if e._activeSite is not None:
            # this should not be necessary
            obj = common.unwrapWeakref(e._activeSite)
            e._activeSiteId = id(obj)

        try:
            if e.isSpanner:
                self.thawIds(e._components)
            #elif e.isVariant:
            #    self.thawIds(e._stream)
        except AttributeError:
            pass # not having isSpanner or isVariant defined
                    # isn't enough to throw an exception for.

    def findAllM21Objects(self, streamObj):
        allEls = streamObj.recurse()
        for el in allEls:
            if hasattr(el, 'rightBarline') and el.rightBarline is not None:
                allEls.append(el.rightBarline)
            if hasattr(el, 'leftBarline') and el.leftBarline is not None:
                allEls.append(el.leftBarline)
            #if hasattr(el, '_stream') and el._stream is not None and el._stream.isStream is True:
            #    # maybe don't? Variant
            #    newEls = self.findAllM21Objects(el._stream)
            #    allEls.extend(newEls)
#            if hasattr(el, '_components') and el._components is not None and el._components.isStream is True:
#                allEls.append(self.findAllM21Objects(el._components))
        return allEls


    def thawContextIds(self, contexts):
        '''
        Restore keys to be the id() of the object they contain.

        >>> from music21 import freezeThaw
        >>> from music21 import *
        
        >>> class Mock(base.Music21Object): 
        ...     pass
        >>> aObj = Mock()
        >>> bObj = Mock()
        >>> cObj = Mock()
        >>> aContexts = base.DefinedContexts()
        >>> aContexts.add(aObj)
        >>> aContexts.add(bObj)
        >>> aContexts.add(cObj, 200) # a location

        >>> oldKeys = aContexts._definedContexts.keys()
        >>> oldLocations = aContexts._locationKeys[:]

        >>> sf = freezeThaw.StreamFreezer()
        >>> sf.freezeContextIds(aContexts)

        >>> newKeys = aContexts._definedContexts.keys()
        >>> oldKeys == newKeys
        False

        >>> st = freezeThaw.StreamThawer()
        >>> st.thawContextIds(aContexts)
        >>> postKeys = aContexts._definedContexts.keys()

        Notice that order is not retained!

        >>> postKeys == newKeys
        False

        But sorting returns the original 
        
        >>> sorted(postKeys) == sorted(oldKeys) 
        True
        >>> oldLocations == aContexts._locationKeys
        True
        '''
        #environLocal.printDebug(['defined context entering unfreeze ids', self._definedContexts])

        # for encoding to serial, this should be done after weakref unwrapping     
        # for decoding to serial, this should be done before weakref wrapping

        post = {}
        postLocationKeys = []
        for idKey in contexts._definedContexts.keys():
            # check if unwrapped, unwrap
            obj = common.unwrapWeakref(contexts._definedContexts[idKey]['obj'])
            if obj is not None:
                newKey = id(obj)
            else:
                newKey = None
            #environLocal.printDebug(['unfreezing key:', idKey, newKey])
            if idKey in contexts._locationKeys:
                postLocationKeys.append(newKey)
            post[newKey] = contexts._definedContexts[idKey]
        contexts._definedContexts = post
        contexts._locationKeys = postLocationKeys



#-------------------------------------------------------------------------------
class StreamFreezer(StreamFreezeThawBase):
    '''
    This class is used to freeze a Stream, preparing it for serialization 
    and providing conversion routines.

    In general, use :func:`~music21.converter.freeze`
    for serializing to a file. 
    
    Use the :func:`~music21.converter.unfreeze` to read from a 
    serialized file

    >>> from music21 import freezeThaw
    >>> from music21 import *
    >>> s = stream.Stream()
    >>> s.repeatAppend(note.Note('C4'), 8) 
    >>> temp = [s[n].transpose(n, inPlace=True) for n in range(len(s))]

    >>> sf = freezeThaw.StreamFreezer(s) # provide a Stream at init
    >>> data = sf.writeStr(fmt='pickle') # pickle is default format

    >>> st = freezeThaw.StreamThawer() 
    >>> st.openStr(data)
    >>> s = st.stream
    >>> s.show('t')
    {0.0} <music21.note.Note C>
    {1.0} <music21.note.Note D->
    {2.0} <music21.note.Note D>
    {3.0} <music21.note.Note E->
    {4.0} <music21.note.Note E>
    {5.0} <music21.note.Note F>
    {6.0} <music21.note.Note G->
    {7.0} <music21.note.Note G>
    
    
    >>> c = corpus.parse('luca/gloria')
    >>> sf = freezeThaw.StreamFreezer(c)
    >>> data = sf.writeStr(fmt='pickle')
    
    >>> st = freezeThaw.StreamThawer()
    >>> st.openStr(data)
    >>> s = st.stream
    >>> len(s.parts[0].measure(7).notes) == 6
    True
    '''
    def __init__(self, streamObj=None, fastButUnsafe=False):
        # must make a deepcopy, as we will be altering DefinedContexts
        self.stream = None
        if streamObj is not None and fastButUnsafe is False:
            # deepcopy necessary because we mangle sites in the objects
            # before serialization
            self.stream = copy.deepcopy(streamObj)
            #self.stream = streamObj
        elif streamObj is not None:
            self.stream = streamObj

    def getPickleFp(self, directory):
        if directory == None:
            raise ValueError
        # cannot get data from stream, as offsets are broken
        streamStr = str(time.time())
        return os.path.join(directory, 'm21-' + common.getMd5(streamStr) + '.p')

    def getJsonFp(self, directory):
        if directory == None:
            raise ValueError
        # cannot get data from stream, as offsets are broken
        streamStr = str(time.time())
        return os.path.join(directory, 'm21-' + common.getMd5(streamStr) + '.json')


    def packStream(self, streamObj = None):
        '''
        Prepare the passed in Stream in place, return storage 
        dictionary format.
        
        Needed?
        '''        
        # do all things necessary to setup the stream
        if streamObj is None:
            streamObj = self.stream
        self.setupSerializationScaffold(streamObj)
        storage = {'stream': streamObj, 'm21Version': base.VERSION}
        return storage

    def teardownStream(self, streamObj = None):
        '''
        Call this after setting packing and writing

        Redundant with teardownSerializationScaffold?
        '''
        if streamObj is None:
            streamObj = self.stream
        self.teardownSerializationScaffold(streamObj)
    
    def findActiveStreamIdsInHierarchy(self, hierarchyObject = None, getSpanners=True):
        '''
        Return a list of all Stream ids anywhere in the hierarchy.
        
        Stores them in .streamIds.
        
        if hierarchyObject is None, uses self.stream.

        >>> from music21 import *
        >>> sc = stream.Score()
        >>> p1 = stream.Part()
        >>> p2 = stream.Part()
        >>> m1 = stream.Measure()
        >>> v1 = stream.Voice()
        >>> m1.insert(0, v1)
        >>> p2.insert(0, m1)
        >>> sc.insert(0, p1)
        >>> sc.insert(0, p2)
        >>> shouldFindIds = [id(sc), id(p1), id(p2), id(m1), id(v1)]
        
        fastButUnsafe is needed because it does not make a deepcopy
        and thus lets you compare ids before and after.
        
        >>> sf = freezeThaw.StreamFreezer(sc, fastButUnsafe=True)
        >>> foundIds = sf.findActiveStreamIdsInHierarchy()
        >>> for thisId in shouldFindIds:
        ...     if thisId not in foundIds:
        ...         raise Exception("Missing Id")
        >>> for thisId in foundIds:
        ...     if thisId not in shouldFindIds:
        ...         raise Exception("Additional Id Found")
        
        Spanners are included unless getSpanners is False
        
        
        >>> staffGroup = layout.StaffGroup([p1, p2])
        >>> sc.insert(0, staffGroup)
        
        :class:`~music21.layout.StaffGroup` is a spanner, so
        it should be found
        
        >>> sf2 = freezeThaw.StreamFreezer(sc, fastButUnsafe=True)
        >>> foundIds = sf2.findActiveStreamIdsInHierarchy()
        
        But you won't find the id of the spanner itself in
        the foundIds:
        
        >>> id(staffGroup) in foundIds
        False
        
        instead it's the id of the storage object:
        
        >>> staffGroup.getSpannerStorageId() in foundIds
        True
                
        TODO: Get Variants as well...
        '''
        if hierarchyObject is None:
            streamObj = self.stream
        else:
            streamObj = hierarchyObject
        streamsFound = streamObj._yieldElementsDownward(streamsOnly=True, 
                       restoreActiveSites=True)
        streamIds = [id(s) for s in streamsFound]
        
        if getSpanners is True:
            spannerBundle = streamObj.spannerBundle
            streamIds += spannerBundle.getSpannerStorageIds()
        ## should also get Variants
        
        self.streamIds = streamIds
        return streamIds

    
    def setupSerializationScaffold(self, streamObj = None):
        '''
        Prepare this stream and all of its contents for pickle/pickling, that
        is, serializing and storing an object representation on file or as a string.

        The `topLevel` and `streamIdsFound` arguments are used to keep track of recursive calls. 

        Note that this is a destructive process: elements contained within this Stream 
        will have their sites cleared of all contents not in the hierarchy 
        of the Streams. Thus, when doing a normal .write('pickle')
        the Stream is deepcopied.  `fastButUnsafe = True` ignores the destructive
        parts of this.
        
        Calls `purgeUndeclaredIds`, `unwrapWeakref`, and `freezeIds` the stream
        and each substream.

        >>> from music21 import freezeThaw
        >>> from music21 import *

        >>> a = stream.Stream()
        >>> n = note.Note()
        >>> n.duration.type = "whole"
        >>> a.repeatAppend(n, 10)
        >>> sf = freezeThaw.StreamFreezer(a)
        >>> sf.setupSerializationScaffold()
        '''
        if streamObj is None:
            streamObj = self.stream
            if streamObj is None:
                raise FreezeThawException("You need to pass in a stream when creating to work")
        # get all Streams that are in this hierarchy
        
        streamIdsFound = self.findActiveStreamIdsInHierarchy(streamObj)
        environLocal.printDebug(['setupSerializationScaffold: streamIdsFound: ', streamIdsFound])

        self.removeSitesNotInHierarchy(streamObj, streamIdsFound)

#        try:
#            v = streamObj.parts[0].getElementsByClass('Variant')[0]
#            print "got one"
#            v.show('t')
#        except:
#            pass

        containedStreams = streamObj.recurse(streamsOnly = True)
        for s in containedStreams:
            elementDict = {}
            for e in s._elements:
                e._preFreezeId = id(e)
                elementDict[id(e)] = e.getOffsetBySite(s)
            s._storedElementOffsets = elementDict

        # remove all caches again; the spanner bundle will be here
        allEls = streamObj.recurse()
        streamObj._elementsChanged()

        #allEls.append(streamObj)
        
        for el in allEls:
            if el.isVariant:
                # works like a whole new hierarchy... # no need for deepcopy
                subSF = StreamFreezer(el._stream, fastButUnsafe=True)
                subSF.setupSerializationScaffold()
            self.removeWeakrefsForFreezing(el)

    def removeWeakrefsForFreezing(self, el):
        '''
        remove all the places weakrefs tend to hide...
        '''
        el.unwrapWeakref()
        el._activeSite = None
        el._activeSiteId = None
        if hasattr(el, '_derivation'): # derives from none
            el._derivation = derivation.Derivation()
        self.freezeIds(el)
        
        
    def removeSitesNotInHierarchy(self, hierarchyObj = None, idsInHierarchy = None, excludeStorageStreams=False):
        '''
        Removes all sites from all objects in the hierarchy
        unless its id is listed in idsInHierarchy.
        
        >>> from music21 import *
        >>> sc = stream.Score()
        >>> p1 = stream.Part()
        >>> p2 = stream.Part()
        >>> n1 = note.Note()
        >>> p1.insert(2.0, n1)
        >>> sc.insert(0.0, p1)
        >>> sc.insert(0.0, p2)
        
        This part is not part of the hierarchy...
        
        >>> p3 = stream.Part()
        >>> p3.insert(3.0, n1)
        >>> n1.getOffsetBySite(p1)
        2.0
        >>> n1.getOffsetBySite(p3)
        3.0
        
        >>> sf = freezeThaw.StreamFreezer(sc, fastButUnsafe=True)
        >>> foundIds = sf.findActiveStreamIdsInHierarchy()
        >>> sf.removeSitesNotInHierarchy(idsInHierarchy = foundIds)
        
              # the idsInHierarchy part is optional above, because
              # findActiveStreamIdsInHierarchy has already been run
 
        >>> n1.getOffsetBySite(p1)
        2.0
        >>> n1.getOffsetBySite(p3)
        Traceback (most recent call last):
        DefinedContextsException: The object <music21.note.Note C> is not in site <music21.stream.Part ...>.
        '''
        if hierarchyObj is None:
            streamObj = self.stream
        else:
            streamObj = hierarchyObj
        
        if idsInHierarchy is None:
            streamIds = self.streamIds
        else:
            streamIds = idsInHierarchy

        # cannot use recurse() because of hidden m21 objects
        # such as rightBarline, variants, etc...
#        try:
#            v = streamObj.parts[0].getElementsByClass('Variant')[0]
#            print "got two"
#            v.show('t')
#        except:
#            pass

        allEls = self.findAllM21Objects(streamObj)        
        
        for el in allEls:
            orphans = []
            if el.isVariant is True:
                continue
            for site in el._definedContexts.getSites():
                # TODO: this can be optimized to get actually get sites

                if site is None: 
                    continue
                idTarget = id(site)
                if idTarget in streamIds: # skip all declared ids
                    continue # do nothing
                if site.isStream:
                    if excludeStorageStreams:
                        # only get those that are not Storage Streams
                        if ('SpannerStorage' not in site.classes 
                            and 'VariantStorage' not in site.classes):
                            #environLocal.printDebug(['removing orphan:', s])
                            orphans.append(idTarget)
                    else: # get all 
                        orphans.append(idTarget)

            for i in orphans:   
                #environLocal.printDebug(['purgeingUndeclaredIds', i])     
                el.removeLocationBySiteId(i)        

#        try:
#            v = streamObj.parts[0].getElementsByClass('Variant')[0]
#            print "got three"
#            v.show('t')
#        except:
#            pass

    def wrapSpannerWeakRef(self, s):
        '''
        Overridden method for wrapping the weakref of a spanner's
        components.
        '''
        # call base method: this gets defined contexts and active site
        base.Music21Object.wrapWeakref(s)
        s._components.wrapWeakref()

    def freezeIds(self, e):
        '''
        Temporarily replace are stored keys with a different value.

        Does not do much, but calls freezeContextIds on e.definedContexts
        which does a lot!

        >>> from music21 import freezeThaw
        >>> import music21
        
        >>> aM21Obj = music21.Music21Object()
        >>> bM21Obj = music21.Music21Object()
        >>> aM21Obj.offset = 30
        >>> aM21Obj.getOffsetBySite(None)
        30.0
        >>> bM21Obj.addLocationAndActiveSite(50, aM21Obj)   
        >>> bM21Obj.activeSite != None
        True
        >>> oldActiveSiteId = bM21Obj._activeSiteId

        >>> sf = freezeThaw.StreamFreezer()
        >>> sf.freezeIds(bM21Obj)

        >>> newActiveSiteId = bM21Obj._activeSiteId
        >>> oldActiveSiteId == newActiveSiteId
        False
        '''
        dummy_counter = common.SingletonCounter()

        self.freezeContextIds(e._definedContexts)
        try:
            if e.isSpanner:
                self.freezeIds(e._components)
            ##don't; instead make a whole new scaffold
            #elif e.isVariant:
            #    self.freezeIds(e._stream)
        except AttributeError:
            pass # not having isSpanner or isVariant defined
                    # isn't enough to throw an exception for.
        
        # _activeSite could be a weak ref; may need to manage
        e._activeSiteId = None # uuid.uuid4() # a place holder
        e._idLastDeepCopyOf = None # clear

    def freezeContextIds(self, contexts):
        '''
        Temporarily replace all stored keys (object ids) 
        with a temporary values suitable for usage in pickling.

        >>> from music21 import freezeThaw
        >>> from music21 import *
        
        >>> class Mock(base.Music21Object): 
        ...     pass
        >>> aObj = Mock()
        >>> bObj = Mock()
        
        >>> aContexts = base.DefinedContexts()
        >>> aContexts.add(aObj)
        >>> aContexts.add(bObj)
        >>> oldKeys = aContexts._definedContexts.keys()
        
        >>> sf = freezeThaw.StreamFreezer()
        >>> sf.freezeContextIds(aContexts)

        >>> newKeys = aContexts._definedContexts.keys()
        >>> oldKeys == newKeys
        False
        '''
        # need to store self._locationKeys as well
        post = {}
        postLocationKeys = []
        counter = common.SingletonCounter()

        for idKey in contexts._definedContexts.keys():
            if idKey is not None:
                newKey = counter() # uuid.uuid4()
            else:
                newKey = idKey # keep None
            # might want to store old id?
            #environLocal.printDebug(['freezing key:', idKey, newKey])
            if idKey in contexts._locationKeys:
                postLocationKeys.append(newKey)
            post[newKey] = contexts._definedContexts[idKey]
        contexts._definedContexts = post
        contexts._locationKeys = postLocationKeys
        #environLocal.printDebug(['post freezeids', self._definedContexts])

        # clear this for setting later
        contexts.containedById = counter()
        contexts._lastID = -1 # set to inactive


#    def unwrapWeakref(self, streamObj):
#        '''Overridden method for unwrapping all Weakrefs.
#        '''
#        self.unwrapWeakref(streamObj._derivation)
#        # call base method: this gets defined contexts and active site
#        base.Music21Object.unwrapWeakref(streamObj)
#        # for contained objects that have weak refs
#        # this presently is not a weakref but in case of future changes
##         if common.isWeakref(self.flattenedRepresentationOf):
##             post = common.unwrapWeakref(objRef)
##             self.flattenedRepresentationOf = post
#
#
#    def wrapWeakref(self, streamObj):
#        '''Overridden method for unwrapping all Weakrefs.
#        '''
#        # call base method: this gets defined contexts and active site
#        base.Music21Object.wrapWeakref(streamObj)
#        self.wrapWeakref(streamObj._derivation)
##         if not common.isWeakref(self.flattenedRepresentationOf):
##             post = common.wrapWeakref(objRef)
##             self.flattenedRepresentationOf = post

    #---------------------------------------------------------------------------
    def parseWriteFmt(self, fmt):
        '''Parse a passed-in write format

        >>> from music21 import freezeThaw
        >>> from music21 import *
        >>> sf = freezeThaw.StreamFreezer()
        >>> sf.parseWriteFmt(None)
        'pickle'
        >>> sf.parseWriteFmt('JSON')
        'jsonpickle'
        '''
        if fmt is None: # this is the default
            return 'pickle'
        fmt = fmt.strip().lower()
        if fmt in ['p', 'pickle']:
            return 'pickle'
        elif fmt in ['jsonpickle', 'json']:
            return 'jsonpickle'            
        #elif fmt in ['jsonnative']:
        #    return 'jsonnative'
        else:
            return 'pickle'

    def write(self, fmt='pickle', fp=None, zipType=None):
        '''
        For a supplied Stream, write a serialized version to
        disk in either 'pickle' or 'jsonpickle' format and
        return the filepath to the file.
        
        N.B. jsonpickle is the better format for transporting from
        one computer to another, but still has some bugs.
        '''
        if zipType is not None:
            raise FreezeThawException("Cannot zip files yet...")
        
        fmt = self.parseWriteFmt(fmt)

        if fp is None:
            directory = environLocal.getRootTempDir()
            if fmt.startswith('json'):
                fp = self.getJsonFp(directory)
            else:
                fp = self.getPickleFp(directory)
        elif os.sep in fp: # assume its a complete path
            fp = fp
        else:
            directory = environLocal.getRootTempDir()
            fp = os.path.join(directory, fp)

    
        storage = self.packStream(self.stream)

        environLocal.printDebug(['writing fp', fp])

        if fmt == 'pickle':
            f = open(fp, 'wb') # binary
            # a negative protocal value will get the highest protocal; 
            # this is generally desirable 
            # packStream() returns a storage dictionary
            pickleMod.dump(storage, f, protocol=-1)
            f.close()
        elif fmt == 'jsonpickle':
            data = jsonpickle.encode(storage)
            f = open(fp, 'w') 
            f.write(data)
            f.close()
        else:
            raise FreezeThawException('bad StreamFreezer format: %s' % fmt)


        # must restore the passed-in Stream
        self.teardownStream(self.stream)
        return fp

    def writeStr(self, fmt=None):
        '''
        Convert the object to a pickled/jsonpickled string
        and return the string
        '''
        fmt = self.parseWriteFmt(fmt)

        storage = self.packStream(self.stream)

        if fmt == 'pickle':
            out = pickleMod.dumps(storage, protocol=-1)
        elif fmt == 'jsonpickle':
            out = jsonpickle.encode(storage)
        else:
            raise FreezeThawException('bad StreamFreezer format: %s' % fmt)

        self.teardownStream(self.stream)
        return out

class StreamThawer(StreamFreezeThawBase):
    '''
    This class is used to thaw a data string into a Stream
    
    In general user :func:`~music21.converter.parse` to read from a 
    serialized file.

    >>> from music21 import freezeThaw
    >>> from music21 import *
    >>> s = stream.Stream()
    >>> s.repeatAppend(note.Note('C4'), 8) 
    >>> temp = [s[n].transpose(n, inPlace=True) for n in range(len(s))]

    >>> sf = freezeThaw.StreamFreezer(s) # provide a Stream at init
    >>> data = sf.writeStr(fmt='pickle') # pickle is default format

    >>> sfOut = freezeThaw.StreamThawer() 
    >>> sfOut.openStr(data)
    >>> s = sfOut.stream
    >>> s.show('t')
    {0.0} <music21.note.Note C>
    {1.0} <music21.note.Note D->
    {2.0} <music21.note.Note D>
    {3.0} <music21.note.Note E->
    {4.0} <music21.note.Note E>
    {5.0} <music21.note.Note F>
    {6.0} <music21.note.Note G->
    {7.0} <music21.note.Note G>
    
    
#    >>> c = corpus.parse('luca/gloria')
#    >>> sf = freezeThaw.StreamFreezer(c)
#    >>> data = sf.writeStr(fmt='jsonpickle')
#    
#    >>> sfOut = freezeThaw.StreamThawer()
#    >>> sfOut.openStr(data)
#    >>> s = sfOut.stream
#    >>> #s.show('t')
    '''
    def __init__(self):
        self.stream = None
    
    def getPickleFp(self, directory):
        if directory == None:
            raise ValueError
        # cannot get data from stream, as offsets are broken
        streamStr = str(time.time())
        return os.path.join(directory, 'm21-' + common.getMd5(streamStr) + '.p')

    def getJsonFp(self, directory):
        if directory == None:
            raise ValueError
        # cannot get data from stream, as offsets are broken
        streamStr = str(time.time())
        return os.path.join(directory, 'm21-' + common.getMd5(streamStr) + '.json')

    def unpackStream(self, storage):
        '''
        Convert from storage dictionary to Stream.
        '''
        version = storage['m21Version']
        if version != base.VERSION:
            environLocal.warn('this pickled file is out of date and may not function properly.')
        streamObj = storage['stream']

        self.teardownSerializationScaffold(streamObj)
        return streamObj

    def unwrapSpannerWeakRef(self, s):
        '''
        Overridden method for unwrapping the weakref of a spanner's
        components.
        '''
        # call base method: this gets defined contexts and active site
        base.Music21Object.unwrapWeakref(self)
        # for contained objects that have weak refs
        #environLocal.printDebug(['spanner unwrapping contained stream'])
        self._components.unwrapWeakref()
        # this presently is not a weakref but in case of future changes
        
#    def unwrapWeakref(self, streamObj):
#        '''Overridden method for unwrapping all Weakrefs.
#        '''
#        self.unwrapWeakref(streamObj._derivation)
#        # call base method: this gets defined contexts and active site
#        base.Music21Object.unwrapWeakref(streamObj)
#        # for contained objects that have weak refs
#        # this presently is not a weakref but in case of future changes
##         if common.isWeakref(self.flattenedRepresentationOf):
##             post = common.unwrapWeakref(objRef)
##             self.flattenedRepresentationOf = post
#
#
#    def wrapWeakref(self, streamObj):
#        '''Overridden method for unwrapping all Weakrefs.
#        '''
#        # call base method: this gets defined contexts and active site
#        base.Music21Object.wrapWeakref(streamObj)
#        self.wrapWeakref(streamObj._derivation)
##         if not common.isWeakref(self.flattenedRepresentationOf):
##             post = common.wrapWeakref(objRef)
##             self.flattenedRepresentationOf = post

    def parseOpenFmt(self, storage):
        '''Look at the file and determine the format
        '''
        if storage.startswith('{"m21Version": {"py/tuple"'):
            return 'jsonpickle'
        else:
            return 'pickle'

    def open(self, fp):
        '''
        For a supplied file path to a pickled stream, unpickle
        '''
        if os.sep in fp: # assume it's a complete path
            fp = fp
        else:
            directory = environLocal.getRootTempDir()
            fp = os.path.join(directory, fp)

        f = open(fp, 'r')
        fileData = f.read() # TODO: do not read entire file
        f.close()

        fmt = self.parseOpenFmt(fileData)
        if fmt == 'pickle':
            #environLocal.printDebug(['opening fp', fp])
            f = open(fp, 'rb')
            storage = pickleMod.load(f)
            f.close()
        elif fmt == 'jsonpickle':
            f = open(fp, 'r')
            data = f.read()
            f.close()
            storage = jsonpickle.decode(data)
        else:
            raise FreezeThawException('bad StreamFreezer format: %s' % fmt)

        self.stream = self.unpackStream(storage)

    def openStr(self, fileData, pickleFormat = None):
        '''
        Take a string representing a Frozen(pickled/jsonpickled) 
        Stream and convert it to a normal Stream.
        
        if format is None then the format is automatically
        determined from the string contents.
        '''
        if pickleFormat is not None:
            fmt = pickleFormat
        else:
            fmt = self.parseOpenFmt(fileData)

        if fmt == 'pickle':
            storage = pickleMod.loads(fileData)
        elif fmt == 'jsonpickle':
            storage = jsonpickle.decode(fileData)
        else:
            raise FreezeThawException('bad StreamFreezer format: %s' % fmt)
        environLocal.printDebug("StreamThawer:openStr: storage is: %s" % storage)
        self.stream = self.unpackStream(storage)

#---------------------------------------------------------------------------------

class JSONSerializerException(FreezeThawException):
    pass

#------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def xtestDirectCorpusPickle(self):
        '''
        does not work!
        '''
        from music21 import corpus
        from music21.ext import jsonpickle as jsp
        import json
        
        c = corpus.parse('bwv66.6').parts[0].measure(0).notes
        d = jsp.encode(c)
        ddecode = json.loads(d)
        print json.dumps(ddecode, sort_keys=True, indent=2)
        dummy = jsp.decode(d)
        
    def xtestSimplePickle(self):
        from music21 import freezeThaw
        from music21 import corpus
        
        c = corpus.parse('bwv66.6').parts[0].measure(0).notes
        #c.show('t')
        
#        for el in c:
#            storedIds.append(el.id)
#            storedDefinedContextsIds.append(id(el._definedContexts))
#            
#        return
        
        n1 = c[0]
        n2 = c[1]
        sf = freezeThaw.StreamFreezer(c, fastButUnsafe=True)
        sf.setupSerializationScaffold()
        for dummy in n1._definedContexts._definedContexts.keys():
            pass
            #print idKey
            #print n1._definedContexts._definedContexts[idKey]['obj']
        for dummy in n2._definedContexts._definedContexts.keys():
            pass
            #print idKey
            #print n2._definedContexts._definedContexts[idKey]['obj']

        dummy_data = pickleMod.dumps(c, protocol=-1)
        
        
        #data = sf.writeStr(fmt='pickle')
    
        #st = freezeThaw.StreamThawer()
        #st.openStr(data)
        #s = st.stream
#        for el in s._elements:
#            idEl = el.id
#            if idEl not in storedIds:
#                print("Could not find ID %d for element %r at offset %f" % 
#                      (idEl, el, el.offset))
#        print storedIds
        #s.show('t')

    def xtestFreezeThawPickle(self):
        from music21 import freezeThaw
        from music21 import corpus
        
        c = corpus.parse('luca/gloria')
        #c.show('t')
        
        sf = freezeThaw.StreamFreezer(c, fastButUnsafe=True)
        d = sf.writeStr()
        #print d
        
        st = freezeThaw.StreamThawer()
        st.openStr(d)
        s = st.stream
        
        # test to see if we can find everything
        for dummy in s.recurse():
            pass
        
        #s.show()
        #s.show('t')
        
    def xtestFreezeThawSimpleVariant(self):
        from music21 import freezeThaw
        from music21 import variant
        from music21 import stream
        from music21 import note
        
        s = stream.Stream()
        m = stream.Measure()
        m.append(note.Note(type="whole"))
        s.append(m)
        
        s2 = stream.Stream()
        m2 = stream.Measure()
        n2 = note.Note("D#4")
        n2.duration.type = "whole"
        m2.append(n2)
        s2.append(m2)
        v = variant.Variant(s2)
        
        s.insert(0, v)
        #s.show('t')
        #print v.rightBarline

        sf = freezeThaw.StreamFreezer(s, fastButUnsafe=True)
        d = sf.writeStr()
        
        st = freezeThaw.StreamThawer()
        st.openStr(d)
        s = st.stream
        s.show('lily.pdf')
        #s.show('t')

    def testFreezeThawVariant(self):
        from music21 import freezeThaw
        from music21 import corpus
        from music21 import variant
        from music21 import stream
        from music21 import note
        
        c = corpus.parse('luca/gloria')

        data2M2 = [('f', 'eighth'), ('c', 'quarter'), ('a', 'eighth'), ('a', 'quarter')]
        stream2 = stream.Stream()
        m = stream.Measure()
        for pitchName,durType in data2M2:
            n = note.Note(pitchName)
            n.duration.type = durType
            m.append(n)
#            stream2.append(n)
        stream2.append(m)
        #c.show('t')
        variant.addVariant(c.parts[0], 6.0, stream2, variantName = 'rhythmic switch', replacementDuration = 3.0)
#        for i in range(20):
#            try:
#                print i
#                x = c._elements[i]
#                for j in range(200):
#                    print j
#                    print x._elements[j]
#            except:
#                pass
#        v = c._elements[8]._elements[139]
#        v.show('t')
#
#        v1 = c.parts[0].getElementsByClass('Variant')[0]
#        v1.show('t')

        #c.parts[0].show('t')
        #c.show('t')
        #c.show('lily.pdf')
        #exit()
        
        sf = freezeThaw.StreamFreezer(c, fastButUnsafe=True)
        #sf.v = v
        d = sf.writeStr()
        #print d

        #print "thawing."
        
        st = freezeThaw.StreamThawer()
        st.openStr(d)
        s = st.stream
        #s.show('lily.pdf')
        v2 = s.parts[0].getElementsByClass('Variant')[0]
        self.assertEqual(v2._stream[0][1].offset, 0.5)
        #v2.show('t')

    def testSerializationScaffoldA(self):
        from music21 import note, stream
        from music21 import freezeThaw
        
        n1 = note.Note()

        s1 = stream.Stream()
        s2 = stream.Stream()

        s1.append(n1)
        s2.append(n1)
        
        sf = freezeThaw.StreamFreezer(s2, fastButUnsafe = True)
        sf.setupSerializationScaffold()
        sf.teardownSerializationScaffold()

        self.assertEqual(s2.hasElement(n1), True)
        # the scaffold has removes all non-contained sites, so n1
        # no longer has s1 as a site
        self.assertEqual(s1 in n1.getSites(), False)
        self.assertEqual(s2 in n1.getSites(), True)


#------------------------------------------------------------------------------
if __name__ == "__main__":
    base.mainTest(Test)


#------------------------------------------------------------------------------
# eof


