# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         freezeThaw.py
# Purpose:      Methods for storing any music21 object on disk.
#               Uses pickle and json
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2011-2012 Michael Scott Cuthbert and the music21
#               Project
# License:      LGPL or BSD, see license.txt
#------------------------------------------------------------------------------

r'''
This module contains objects for storing complete `Music21Objects`, especially
`Stream` and `Score` objects on disk.  Freezing (or "pickling") refers to
writing the object to a file on disk (or to a string).  Thawing (or
"unpickling") refers to reading in a string or file and returning a Music21
object.

This module offers alternatives to writing a `Score` to `MusicXML` with
`s.write('musicxml')`.  `FreezeThaw` has some advantages over using `.write()`:
virtually every aspect of a music21 object is retained when Freezing.  So
objects like `medRen.Ligature`, which aren't supported by most formats, can be
stored with `FreezeThaw` and then read back again.  Freezing is also much
faster than most conversion methods.  But there's a big downside: only
`music21` and `Python` can use the `Thaw` side to get back `Music21Objects`
(though more information can be brought out of the JSONFreeze format through
any .json reader).  In fact, there's not even a guarantee that future versions
of music21 will be able to read a frozen version of a `Stream`.  So the
advantages and disadvantages of this model definitely need to be kept in mind.

There are two formats that `freezeThaw` can produce: "Pickle" or JSON (for
JavaScript Object Notation -- essentially a string representation of the
JavaScript equivalent of a Python dictionary).  

Pickle is a Python-specific
idea for storing objects.  The `pickle` module stores objects as a text file
that can't be easily read by non-Python applications; it also isn't guaranteed
to work across Python versions or even computers.  However, it works well, is
fast, and is a standard part of python.  

JSON was originally created to pass
JavaScript objects from a web server to a web browser, but its utility
(combining the power of XML with the ease of use of objects) has made it a
growing standard for other languages.  (see
http://docs.python.org/library/json.html).  Music21 has two implementations of JSON (confusing, no?)
because we weren't sure and are still not sure which will be best in the long-run: the first approach
uses explicit lists of attributes that need to be stored and just saves those. This uses a
homemade set of methods that are specifically tailored for music21; but it misses some things that
may be important to you.  The second approach uses the the freely distributable
`jsonpickle` module found in `music21.ext.jsonpickle` (See that folder's
"license.txt" for copyright information). This approach probably stores more data than
someone not using music21 or python is likely to want, but can be used to get back an entire
music21 Stream with no conversion.

Both JSON and Pickle files can be huge, but `freezeThaw` can compress them with
`gzip` or `ZipFile` and thus they're not that large at all.

Streams need to be run through .setupSerializationScaffold and .teardownSerializationScaffold
before and after either Pickle or jsonpickle in order to restore all the weakrefs that we use.

The name freezeThaw comes from Perl's implementation of similar methods -- I
like the idea of thawing something that's frozen; "unpickling" just doesn't
seem possible.  In any event, I needed a name that wouldn't already
exist in the Python namespace.
'''

import copy
import fractions
import inspect
import io
import json
import os
import time
import unittest
import zlib

from music21 import base
from music21 import common
from music21 import defaults
from music21 import derivation
from music21 import exceptions21
from music21 import pitch
#from music21.timespans.trees import ElementTree

from music21.ext import jsonpickle
from music21.ext import six

from music21 import environment
_MOD = "freezeThaw.py"
environLocal = environment.Environment(_MOD)

from music21.common import pickleMod
#------------------------------------------------------------------------------


class FreezeThawException(exceptions21.Music21Exception):
    pass

#------------------------------------------------------------------------------


class StreamFreezeThawBase(object):
    '''
    Contains a few methods that are used for both
    StreamFreezer and StreamThawer
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
        return self.getPickleFp(directory) + '.json'

    def findAllM21Objects(self, streamObj):
        '''
        find all M21 Objects in _elements and _endElements and in nested streams.
        '''
        allObjs = []
        for x in streamObj._elements:
            allObjs.append(x)
            if x.isStream:
                allObjs.extend(self.findAllM21Objects(x))
        for x in streamObj._endElements:
            allObjs.append(x)
            if x.isStream:
                allObjs.extend(self.findAllM21Objects(x))
        return allObjs


#------------------------------------------------------------------------------
class StreamFreezer(StreamFreezeThawBase):
    '''
    This class is used to freeze a Stream, preparing it for serialization
    and providing conversion routines.

    In general, use :func:`~music21.converter.freeze`
    for serializing to a file.

    Use the :func:`~music21.converter.unfreeze` to read from a
    serialized file

    >>> from music21 import freezeThaw

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

    >>> sf2 = freezeThaw.StreamFreezer(s) # do not reuse StreamFreezers
    >>> data2 = sf2.writeStr(fmt='jsonpickle')

    >>> st2 = freezeThaw.StreamThawer()
    >>> st2.openStr(data2)
    >>> s2 = st2.stream
    >>> s2.show('t')
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
    >>> s2 = st.stream
    >>> len(s2.parts[0].measure(7).notes) == 6
    True

    >>> sf2 = freezeThaw.StreamFreezer(c) # do not reuse StreamFreezers
    >>> data2 = sf2.writeStr(fmt='jsonpickle')
    >>> st2 = freezeThaw.StreamThawer()
    >>> st2.openStr(data2)
    >>> s3 = st.stream
    >>> len(s3.parts[0].measure(7).notes) == 6
    True

    '''
    def __init__(self, streamObj=None, fastButUnsafe=False, topLevel = True, streamIds = None):
        StreamFreezeThawBase.__init__(self)
        # must make a deepcopy, as we will be altering .sites
        self.stream = None
        # clear all sites only if the top level.
        self.topLevel = topLevel
        self.streamIds = streamIds

        self.subStreamFreezers = {} # this will keep track of sub freezers for spanners and
        #


        if streamObj is not None and fastButUnsafe is False:
            # deepcopy necessary because we mangle sites in the objects
            # before serialization
            self.stream = copy.deepcopy(streamObj)
            #self.stream = streamObj
        elif streamObj is not None:
            self.stream = streamObj

    def packStream(self, streamObj = None):
        '''
        Prepare the passed in Stream in place, return storage
        dictionary format.

        >>> s = stream.Stream()
        >>> n = note.Note('D#4')
        >>> s.append(n)
        >>> sf = freezeThaw.StreamFreezer(s)
        >>> #_DOCS_SHOW sf.packStream()
        >>> print("{'m21Version': (2, 0, 5), 'stream': <music21.stream.Stream 0x1289212>}") #_DOCS_HIDE
        {'m21Version': (2, 0, 5), 'stream': <music21.stream.Stream 0x1289212>}
        
        '''
        # do all things necessary to setup the stream
        if streamObj is None:
            streamObj = self.stream
        self.setupSerializationScaffold(streamObj)
        storage = {'stream': streamObj, 'm21Version': base.VERSION}
        return storage

    def setupSerializationScaffold(self, streamObj = None):
        '''
        Prepare this stream and all of its contents for pickle/pickling, that
        is, serializing and storing an object representation on file or as a string.

        The `topLevel` and `streamIdsFound` arguments are used to keep track of recursive calls.

        Note that this is a destructive process: elements contained within this Stream
        will have their sites cleared of all contents not in the hierarchy
        of the Streams. Thus, when doing a normal .write('pickle')
        the Stream is deepcopied before this method is called. The
        attribute `fastButUnsafe = True` setting of StreamFreezer ignores the destructive
        effects of these processes and skips the deepcopy.

        >>> from music21 import freezeThaw

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
        allEls = list(streamObj.recurse(restoreActiveSites=False)) # might not work when recurse yields...
        if self.topLevel is True:
            self.findActiveStreamIdsInHierarchy(streamObj)

        for el in allEls:
            if el.isVariant:
                # works like a whole new hierarchy... # no need for deepcopy
                subSF = StreamFreezer(
                    el._stream,
                    fastButUnsafe=True,
                    streamIds=self.streamIds,
                    topLevel=False,
                    )
                subSF.setupSerializationScaffold()
            elif el.isSpanner:
                # works like a whole new hierarchy... # no need for deepcopy
                subSF = StreamFreezer(
                    el.spannerStorage,
                    fastButUnsafe=True,
                    streamIds=self.streamIds,
                    topLevel=False,
                    )
                subSF.setupSerializationScaffold()
            elif el.isStream:
                self.removeStreamStatusClient(el)  # removing seems to create problems for jsonPickle with Spanners

        self.removeStreamStatusClient(streamObj) # removing seems to create problems for jsonPickle with Spanners
        self.setupStoredElementOffsetTuples(streamObj)

        if self.topLevel is True:
            self.recursiveClearSites(streamObj)

    def removeStreamStatusClient(self, streamObj):
        '''
        if s is a stream then 
        
        s.streamStatus._client is s
        
        this can be hard to pickle, so this method removes the streamStatus._client from the
        streamObj (not recursive).  Called by setupSerializationScaffold.
        '''
        if hasattr(streamObj, 'streamStatus'):
            streamObj.streamStatus._client = None


    def recursiveClearSites(self, startObj):
        '''
        recursively clear all sites, including activeSites, taking into account
        that spanners and variants behave differently.
        
        Called by setupSerializationScaffold.

        To be run after setupStoredElementOffsetTuples() has been run
        
        >>> n = note.Note('D#4')
        >>> len(n.sites)
        1
        >>> s = stream.Stream()
        >>> s.id = 'stream s'
        >>> s.insert(10, n)
        >>> len(n.sites)
        2
        >>> t = stream.Stream()
        >>> t.insert(20, n)
        >>> t.id = 'stream t'
        >>> len(n.sites)
        3

        >>> n.getOffsetBySite(s)
        10.0
        >>> n.getOffsetBySite(t)
        20.0
        
        >>> sf = freezeThaw.StreamFreezer()
        
        This will remove n from s but leave the rest of the sites intact...
        
        >>> sf.setupStoredElementOffsetTuples(s)
        >>> len(n.sites)
        2
        >>> n.getOffsetBySite(s)
        Traceback (most recent call last):
        SitesException: an entry for this object <music21.note.Note D#> is not stored in stream <music21.stream.Stream stream s>
        >>> n.getOffsetBySite(t)
        20.0
        
        
        After recursiveClearSites n will be not know its location anywhere...
        
        >>> sf.recursiveClearSites(s)
        >>> len(n.sites)
        0

        This leaves n and t in strange positions, because n is in t.elements still....
        
        >>> n in t.elements
        True
        
        This predicament is why when the standard freezeThaw call is made, what is frozen is a 
        deepcopy of the Stream so that nothing is left in an unusable position
        
        
        '''
        if hasattr(startObj, '_storedElementOffsetTuples'):
            seot = startObj._storedElementOffsetTuples
            for el, unused_offset in seot:
                if el.isStream:
                    self.recursiveClearSites(el)
                if el.isSpanner:
                    self.recursiveClearSites(el.spannerStorage)
                if el.isVariant:
                    self.recursiveClearSites(el._stream)
                if hasattr(el, '_derivation'):
                    el._derivation = derivation.Derivation() #reset

                if (hasattr(el, '_offsetDict')):
                    el._offsetDict = {}
                el.sites.clear()
                el.activeSite = None
            startObj._derivation = derivation.Derivation() #reset
            startObj.sites.clear()
            startObj.activeSite = None

    def setupStoredElementOffsetTuples(self, streamObj):
        '''
        move all elements from ._elements and ._endElements
        to a new attribute ._storedElementOffsetTuples
        which contains a list of tuples of the form
        (el, offset or 'end').
        
        Called by setupSerializationScaffold.

        >>> s = stream.Measure()
        >>> n1 = note.Note("C#")
        >>> n2 = note.Note("E-")
        >>> bl1 = bar.Barline()
        >>> s.insert(0.0, n1)
        >>> s.insert(1.0, n2)
        >>> s.storeAtEnd(bl1)

        >>> sfreeze = freezeThaw.StreamFreezer()
        >>> sfreeze.setupStoredElementOffsetTuples(s)
        >>> s._elements, s._endElements
        ([], [])
        >>> s._storedElementOffsetTuples
        [(<music21.note.Note C#>, 0.0), (<music21.note.Note E->, 1.0), (<music21.bar.Barline style=regular>, 'end')]
        >>> n1.getOffsetBySite(s)
        Traceback (most recent call last):
        SitesException: an entry for this object <music21.note.Note C#> is not stored in stream <music21.stream.Measure 0 offset=0.0>

        Trying it again, but now with substreams:

        >>> s2 = stream.Measure()
        >>> n1 = note.Note("C#")
        >>> n2 = note.Note("E-")
        >>> bl1 = bar.Barline()
        >>> v1 = stream.Voice()
        >>> n3 = note.Note("F#")
        >>> v1.insert(2.0, n3)
        >>> s2.insert(0.0, n1)
        >>> s2.insert(1.0, n2)
        >>> s2.storeAtEnd(bl1)
        >>> s2.insert(2.0, v1)
        >>> sfreeze.setupStoredElementOffsetTuples(s2)

        >>> v1._storedElementOffsetTuples
        [(<music21.note.Note F#>, 2.0)]
        >>> s2._storedElementOffsetTuples
        [(<music21.note.Note C#>, 0.0), (<music21.note.Note E->, 1.0), (<music21.stream.Voice ...>, 2.0), (<music21.bar.Barline style=regular>, 'end')]
        >>> s2._storedElementOffsetTuples[2][0] is v1
        True

        '''
        if hasattr(streamObj, '_storedElementOffsetTuples'):
            # in the case of a spanner storing a Stream, like a StaffGroup
            # spanner, it is possible that the elements have already been
            # transferred.  Thus, we should NOT do this again!
            return

        storedElementOffsetTuples = []
        for e in streamObj._elements:
            elementTuple = (e, streamObj.elementOffset(e))
            storedElementOffsetTuples.append(elementTuple)
            if e.isStream:
                self.setupStoredElementOffsetTuples(e)
            e.sites.remove(streamObj)
            e.activeSite = None
#                e._preFreezeId = id(e)
#                elementDict[id(e)] = s.elementOffset(e)
        for e in streamObj._endElements:
            elementTuple = (e, 'end')
            storedElementOffsetTuples.append(elementTuple)
            if e.isStream:
                self.setupStoredElementOffsetTuples(e)
            e.sites.remove(streamObj)
            e.activeSite = None

        streamObj._storedElementOffsetTuples = storedElementOffsetTuples
        #streamObj._elementTree = None
        streamObj._offsetDict = {}
        streamObj._elements = []
        streamObj._endElements = []
        streamObj.elementsChanged()
            

    def findActiveStreamIdsInHierarchy(self, hierarchyObject = None, getSpanners=True, getVariants=True):
        '''
        Return a list of all Stream ids anywhere in the hierarchy.

        Stores them in .streamIds.

        if hierarchyObject is None, uses self.stream.


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

        Variants are treated similarly:

        >>> s = stream.Stream()
        >>> m = stream.Measure()
        >>> m.append(note.Note(type="whole"))
        >>> s.append(m)

        >>> s2 = stream.Stream()
        >>> m2 = stream.Measure()
        >>> n2 = note.Note("D#4")
        >>> n2.duration.type = "whole"
        >>> m2.append(n2)
        >>> s2.append(m2)
        >>> v = variant.Variant(s2)
        >>> s.insert(0, v)
        >>> sf = freezeThaw.StreamFreezer(s, fastButUnsafe=True)
        >>> allIds = sf.findActiveStreamIdsInHierarchy()
        >>> len(allIds)
        4
        >>> for streamElement in [s, m, m2, v._stream]:
        ...    if id(streamElement) not in allIds:
        ...        print("this should not happen...", allIds, id(streamElement))

        N.B. with variants:

        >>> id(s2) == id(v._stream)
        False

        The method also sets self.streamIds to the returned list:

        >>> sf.streamIds is allIds
        True
        '''
        if hierarchyObject is None:
            streamObj = self.stream
        else:
            streamObj = hierarchyObject
        streamsFoundGenerator = streamObj.recurse(streamsOnly=True,
                       restoreActiveSites=False)
        streamIds = [id(s) for s in streamsFoundGenerator]

        if getSpanners is True:
            spannerBundle = streamObj.spannerBundle
            streamIds += spannerBundle.getSpannerStorageIds()

        if getVariants is True:
            for el in streamObj.recurse():
                if el.isVariant is True:
                    streamIds += self.findActiveStreamIdsInHierarchy(el._stream)

        # should not happen that there are duplicates, but possible with spanners...
        # Python's uniq value...
        streamIds = list(set(streamIds))

        self.streamIds = streamIds
        return streamIds


    #---------------------------------------------------------------------------
    def parseWriteFmt(self, fmt):
        '''Parse a passed-in write format

        >>> from music21 import freezeThaw

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

    def write(self, fmt='pickle', fp=None, zipType=None, **keywords):
        '''
        For a supplied Stream, write a serialized version to
        disk in either 'pickle' or 'jsonpickle' format and
        return the filepath to the file.

        jsonpickle is the better format for transporting from
        one computer to another, but slower and may have some bugs.
        
        If zipType == 'zlib' then zlib compression is done after serializing.
        No other compression types are currently supported. 
        '''
        if zipType not in (None, 'zlib'):
            raise FreezeThawException("Cannot zip files except zlib...")

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
            # a negative protocol value will get the highest protocol;
            # this is generally desirable
            # packStream() returns a storage dictionary
            pickleString = pickleMod.dumps(storage, protocol=pickleMod.HIGHEST_PROTOCOL)
            if zipType == 'zlib':
                pickleString = zlib.compress(pickleString)
            with open(fp, 'wb') as f: # binary
                f.write(pickleString)
        elif fmt == 'jsonpickle':
            data = jsonpickle.encode(storage, **keywords)
            if zipType == 'zlib':
                data = zlib.compress(data)
            with open(fp, 'w') as f:
                f.write(data)

        else:
            raise FreezeThawException('bad StreamFreezer format: %s' % fmt)

        ## must restore the passed-in Stream
        #self.teardownStream(self.stream)
        return fp

    def writeStr(self, fmt=None, **keywords):
        '''
        Convert the object to a pickled/jsonpickled string
        and return the string
        '''
        fmt = self.parseWriteFmt(fmt)
        storage = self.packStream(self.stream)


        if fmt == 'pickle':
            out = pickleMod.dumps(storage, protocol=-1)
        elif fmt == 'jsonpickle':
            out = jsonpickle.encode(storage, **keywords)
        else:
            raise FreezeThawException('bad StreamFreezer format: %s' % fmt)

        #self.teardownStream(self.stream)
        return out


class StreamThawer(StreamFreezeThawBase):
    '''
    This class is used to thaw a data string into a Stream

    In general user :func:`~music21.converter.parse` to read from a
    serialized file.

    >>> from music21 import freezeThaw

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
        StreamFreezeThawBase.__init__(self)
        self.stream = None

    # TODO: Test that the _NoneSite singleton is restored properly after freezeThaw.

    def teardownSerializationScaffold(self, streamObj = None):
        '''
        After rebuilding this Stream from pickled storage, prepare this as a normal `Stream`.

        If streamObj is None, runs it on the embedded stream

        >>> from music21 import freezeThaw


        >>> a = stream.Stream()
        >>> n = note.Note()
        >>> n.duration.type = "whole"
        >>> a.repeatAppend(n, 10)
        >>> sf = freezeThaw.StreamFreezer(a)
        >>> sf.setupSerializationScaffold()

        >>> st = freezeThaw.StreamThawer()
        >>> st.teardownSerializationScaffold(a)
        '''
        def _fixId(e):
            if (e.id is not None and 
                    common.isNum(e.id) and 
                    e.id > defaults.minIdNumberToConsiderMemoryLocation):
                e.id = id(e)

        if streamObj is None:
            streamObj = self.stream
            if streamObj is None:
                raise FreezeThawException("You need to pass in a stream when creating to work")

        storedAutoSort = streamObj.autoSort
        streamObj.autoSort = False

        self.restoreElementsFromTuples(streamObj)

        self.restoreStreamStatusClient(streamObj) # removing seems to create problems for jsonPickle with Spanners
        allEls = self.findAllM21Objects(streamObj)

        for e in allEls:
            if e.isVariant:
#                # works like a whole new hierarchy... # no need for deepcopy
                subSF = StreamThawer()
                subSF.teardownSerializationScaffold(e._stream)
                e._stream.elementsChanged()
                e._cache = {}
                #for el in e._stream.flat:
                #    print el, el.offset, el.sites.siteDict
            elif e.isSpanner:
                subSF = StreamThawer()
                subSF.teardownSerializationScaffold(e.spannerStorage)
                e.spannerStorage.elementsChanged()
                e._cache = {}
            elif e.isStream: 
                self.restoreStreamStatusClient(e) # removing seems to create problems for jsonPickle with Spanners

            _fixId(e)
            #e.wrapWeakref()

        # restore to whatever it was
        streamObj.autoSort = storedAutoSort
        streamObj.elementsChanged()
        _fixId(streamObj)

    def restoreElementsFromTuples(self, streamObj):
        '''
        Take a Stream with elements and offsets stored in
        a list of tuples (element, offset or 'end') at
        _storedElementOffsetTuples
        and restore it to the ._elements and ._endElements lists
        in the proper locations:


        >>> s = stream.Measure()
        >>> s._elements, s._endElements
        ([], [])

        >>> n1 = note.Note("C#")
        >>> n2 = note.Note("E-")
        >>> bl1 = bar.Barline()
        >>> tupleList = [(n1, 0.0), (n2, 1.0), (bl1, 'end')]
        >>> s._storedElementOffsetTuples = tupleList

        >>> sthaw = freezeThaw.StreamThawer()
        >>> sthaw.restoreElementsFromTuples(s)
        >>> s.show('text')
        {0.0} <music21.note.Note C#>
        {1.0} <music21.note.Note E->
        {2.0} <music21.bar.Barline style=regular>
        >>> s._endElements
        [<music21.bar.Barline style=regular>]
        >>> s[1].getOffsetBySite(s)
        1.0

        Trying it again, but now with substreams:

        >>> s2 = stream.Measure()
        >>> v1 = stream.Voice()
        >>> n3 = note.Note("F#")
        >>> v1._storedElementOffsetTuples = [(n3, 2.0)]
        >>> tupleList = [(n1, 0.0), (n2, 1.0), (bl1, 'end'), (v1, 2.0)]
        >>> s2._storedElementOffsetTuples = tupleList
        >>> sthaw.restoreElementsFromTuples(s2)
        >>> s2.show('text')
        {0.0} <music21.note.Note C#>
        {1.0} <music21.note.Note E->
        {2.0} <music21.stream.Voice ...>
            {2.0} <music21.note.Note F#>
        {5.0} <music21.bar.Barline style=regular>
        '''
        if hasattr(streamObj, '_storedElementOffsetTuples'):
            #streamObj._elementTree = ElementTree(source=streamObj)
            for e, offset in streamObj._storedElementOffsetTuples:
                if offset != 'end':
                    streamObj._insertCore(offset, e)
                else:
                    streamObj._storeAtEndCore(e)
            del(streamObj._storedElementOffsetTuples)
            streamObj.elementsChanged()

        for subElement in streamObj:
            if subElement.isStream is True:
                # note that the elements may have already been restored
                # if the spanner stores a part or something in the Stream
                # for instance in a StaffGroup object
                self.restoreElementsFromTuples(subElement)

    def restoreStreamStatusClient(self, streamObj):
        if hasattr(streamObj, 'streamStatus'):
            streamObj.streamStatus._client = streamObj


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

    def parseOpenFmt(self, storage):
        '''
        Look at the file and determine the format
        '''
        if (six.PY3 and isinstance(storage, bytes)):
            if storage.startswith(b'{"'): # was m21Version": {"py/tuple" but order of dict may change
                return 'jsonpickle'
            else:
                return 'pickle'
        else:            
            if storage.startswith('{"'): # was m21Version": {"py/tuple" but order of dict may change
                return 'jsonpickle'
            else:
                return 'pickle'

    def open(self, fp, zipType=None):
        '''
        For a supplied file path to a pickled stream, unpickle
        '''
        if os.sep in fp: # assume it's a complete path
            fp = fp
        else:
            directory = environLocal.getRootTempDir()
            fp = os.path.join(directory, fp)

        f = open(fp, 'rb')
        fileData = f.read() # TODO: do not read entire file
        f.close()

        fmt = self.parseOpenFmt(fileData)
        if fmt == 'pickle':
            #environLocal.printDebug(['opening fp', fp])
            f = open(fp, 'rb')
            if zipType is None:
                storage = pickleMod.load(f)
            elif zipType == 'zlib':
                compressedString = f.read()
                uncompressed = zlib.decompress(compressedString)
                try:
                    storage = pickleMod.loads(uncompressed)
                except AttributeError as e:
                    raise FreezeThawException('Problem in decoding: {}'.format(e))
            else:
                raise FreezeThawException("Unknown zipType %s" % zipType)
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

#--------------------------------------------------------------------------------

class JSONFreezerException(FreezeThawException):
    pass
class JSONThawerException(FreezeThawException):
    pass

class JSONFreezeThawBase(object):
    '''
    Shared functionality for JSONFreeze and JSONThaw
    '''
    # a list of attributes to store.  Also takes the following special attributes
    # __AUTO_GATHER__ : place all autoGatherAttributes here
    # __INHERIT__ : place all attributes from the inherited class here # NOT YET!
    storedClassAttributes = {
        'music21.base.Music21Object' : [
            '_duration', '_priority', 'offset',                
            ],
        'music21.beam.Beam': [
            'type', 'direction', 'independentAngle', 'number',
            ],
        'music21.beam.Beams': [
            'beamsList', 'feathered',
            ],
        'music21.duration.DurationTuple': [
            '__AUTO_GATHER__',
            ],
        'music21.duration.Duration': [
            '_linked',
            '_components',
            '_qtrLength',
            '_tuplets',
            '_componentsNeedUpdating',
            '_quarterLengthNeedsUpdating',
            '_typeNeedsUpdating',
            '_unlinkedType',
            '_dotGroups',
            ],
        'music21.editorial.NoteEditorial': [
            'color', 'misc', 'comment',
            ],
        'music21.editorial.Comment': [
            '__AUTO_GATHER__',
            ],
        'music21.key.KeySignature': [
            'sharps', 'mode', '_alteredPitches',
            ],
        'music21.metadata.primitives.Contributor': [
            '_role', 'relevance', '_names', '_dateRange',
            ],
        'music21.metadata.primitives.Date': [
            'year', 'month', 'day', 'hour', 'minute', 'second',
            'yearError', 'monthError', 'dayError', 'hourError', 'minuteError',
            'secondError',
            ],
        'music21.metadata.primitives.DateSingle': [
            '_relevance',  '_dataError', '_data',
            ],
        'music21.metadata.Metadata': [
            '_date', '_imprint', '_copyright', '_workIds', '_urls',
            '_contributors',
            ],
        'music21.metadata.bundles.MetadataBundle': [
            '_metadataEntries', 'name',
            ],
        'music21.metadata.bundles.MetadataEntry': [
            '_sourcePath', '_number', '_metadataPayload',
            ],
        'music21.metadata.RichMetadata': [
            '__INHERIT__',
            'ambitus',
            'keySignatures',
            'keySignatureFirst',
            'noteCount',
            'pitchHighest',
            'pitchLowest',
            'quarterLength',
            'tempos',
            'tempoFirst',
            'timeSignatureFirst',
            'timeSignatures',
            ],
        'music21.metadata.primitives.Text': [
            '_data', '_language',
            ],
        'music21.meter.TimeSignature': [
            'ratioString',
            ],
        'music21.note.Lyric': [
            'text', 'syllabic', 'number', 'identifier',
            ],
        'music21.note.GeneralNote': [
            '__INHERIT__', '_editorial', 'lyrics', 'expressions', 'articulations',
            'tie',
            ],
        'music21.note.NotRest': [
            '__INHERIT__', '_notehead', '_noteheadFill',
            '_noteheadParenthesis', '_stemDirection', '_volume',
            ],
        'music21.note.Note': [
            '__INHERIT__', 'pitch', 'beams',
            ],
        'music21.pitch.Accidental': [
            '__AUTO_GATHER__',              
            ],
        
        'music21.pitch.Pitch': [
            '_accidental', '_microtone', '_octave', '_step', 
            ],
        'music21.stream.Stream': ['__INHERIT__',
                                  '_atSoundingPitch',
                                  '_elements',
                                  '_endElements',
                                  ],
        'music21.tie.Tie': [
                            'type', 'style'
                            ],
        'music21.volume.Volume': [
                                  '_velocity'
                                  ],
        }

    postClassCreateCall = {
        #'music21.meter.TimeSignature': ('ratioChanged',),
        }

    def __init__(self, storedObject=None):
        self.storedObject = storedObject
        if storedObject is not None:
            self.className = '.'.join((
                storedObject.__class__.__module__,
                storedObject.__class__.__name__,
                ))
        else:
            self.className = None

    def music21ObjectFromString(self, idStr):
        '''
        Given a stored string during JSON serialization, return an object.
        This method effectively converts a string class specification into
        a vanilla instance ready for specialization via stored data attributes.

        A subclass that overrides this method will have access to all
        modules necessary to create whatever objects necessary.


        >>> jss = freezeThaw.JSONFreezer()
        >>> n = jss.music21ObjectFromString('note.Note')
        >>> n
        <music21.note.Note C>

        One can begin with "music21." if you'd like:

        >>> d = jss.music21ObjectFromString('music21.duration.Duration')
        >>> d
        <music21.duration.Duration 0.0>

        Undefined classes give a JSONFreezerException

        >>> jss.music21ObjectFromString('blah.NotAClass')
        Traceback (most recent call last):
        JSONFreezerException: Cannot generate a new object from blah.NotAClass
        '''
        import music21 # pylint: disable=redefined-outer-name
        idStrOrig = idStr
        if idStr.startswith('music21.'):
            idStr = idStr[8:]
        elif idStr.startswith("<class 'music21.") and idStr.endswith("'>"):
            # old style JSON not used anymore:
            # changes <class 'music21.metadata.RichMetadata'> to
            # metadata.RichMetadata
            idStr = idStr[16:]
            idStr = idStr[0:len(idStr)-2]

        idStrSplits = idStr.split('.')
        lastInspect = music21
        for thisMod in idStrSplits:
            try:
                nextMod = getattr(lastInspect, thisMod)
            except AttributeError:
                raise JSONFreezerException("Cannot generate a new object from %s" % idStrOrig)
            if inspect.isclass(nextMod) is True:
                lastInspect = nextMod()
            elif inspect.ismodule(nextMod) is True:
                lastInspect = nextMod
            else:
                raise JSONFreezerException("All the parts of %s must refer to modules or classes" % idStrOrig)

        return lastInspect

    def fullyQualifiedClassFromObject(self, obj):
        '''
        return a fullyQualified class name from an object.

        >>> d = duration.Duration()
        >>> jsbase = freezeThaw.JSONFreezeThawBase()
        >>> jsbase.fullyQualifiedClassFromObject(d)
        'music21.duration.Duration'

        Works on class objects as well:

        >>> dclass = duration.Duration
        >>> jsbase.fullyQualifiedClassFromObject(dclass)
        'music21.duration.Duration'
        '''
        if inspect.isclass(obj):
            return obj.__module__ + '.' + obj.__name__
        else:
            c = obj.__class__
            return c.__module__ + '.' + c.__name__

class JSONFreezer(JSONFreezeThawBase):
    '''
    Class that provides JSON output from an object (whether
    Music21Object or other).


    >>> n = note.Note("C#4")
    >>> jsonF = freezeThaw.JSONFreezer(n)
    >>> jsonF.storedObject
    <music21.note.Note C#>
    >>> jsonF.className
    'music21.note.Note'
    '''
    def __init__(self, storedObject=None):
        JSONFreezeThawBase.__init__(self, storedObject)
    #---------------------------------------------------------------------------
    # override these methods for json functionality

    def autoGatherAttributes(self):
        '''
        Gather just the instance data members that are proceeded by an underscore.

        Returns a list of those data members

        >>> n = note.Note()
        >>> jss = freezeThaw.JSONFreezer(n)
        >>> for attr in jss.autoGatherAttributes():
        ...     attr
        ...
        '_activeSite'
        '_activeSiteStoredOffset'
        '_duration'
        '_editorial'
        '_naiveOffset'
        '_notehead'
        '_noteheadFill'
        '_noteheadParenthesis'
        '_priority'
        '_stemDirection'
        '_volume'
        '''
        result = set()
        if self.storedObject is None:
            return []
        # names that we always do not need
        excludedNames = [
            '_derivation',
            '_DOC_ATTR',
            '_DOC_ORDER',
            ]

        for attr in inspect.classify_class_attrs(type(self.storedObject)):
            if attr.kind == 'data' and inspect.ismemberdescriptor(attr.object):
                if attr.name not in excludedNames and \
                    attr.name.startswith('_') and \
                    not attr.name.startswith('__'):
                    result.add(attr.name)
            else:
                excludedNames.append(attr.name)
        for name in dir(self.storedObject):
            if not name.startswith('_') or name.startswith('__'):
                continue
            elif name in excludedNames:
                continue
            attr = getattr(self.storedObject, name)
            if inspect.ismethod(attr) or \
                inspect.isfunction(attr) or  \
                inspect.isroutine(attr):
                continue
            result.add(name)

#        # get class names that exclude instance names
#        # these names will be rejected in final accumulation
#        classNames = []
#        for bundle in inspect.classify_class_attrs(obj.__class__):
#            if (bundle.name.startswith('_') and not
#                bundle.name.startswith('__')):
#                classNames.append(bundle.name)
#        #environLocal.printDebug(['classNames', classNames])
#        for name in dir(obj):
#            if name.startswith('_') and not name.startswith('__'):
#                attr = getattr(obj, name)
#                #environLocal.printDebug(['inspect.isroutine()', attr, inspect.isroutine(attr)])
#                if (not inspect.ismethod(attr) and not
#                    inspect.isfunction(attr) and not inspect.isroutine(attr)):
#                    # class names stored are class attrs, not needed for
#                    # reinstantiation
#                    if name not in classNames and name not in exclude:
#                        # store the name, not the attr
#                        post.append(name)

        result = sorted(result)
        return result

    def jsonAttributes(self, autoGather=True):
        '''
        Define all attributes of this object that should be JSON serialized for storage and re-instantiation. Attributes that name basic
        Python objects or :class:`~music21.freezeThaw.JSONFreezer` subclasses,
        or dictionaries or lists that contain Python objects or :class:`~music21.freezeThaw.JSONFreezer` subclasses, can be provided.

        Should be overridden in subclasses.

        For an object which does not define this, just returns all the _underscore attributes:

        >>> ed = editorial.NoteEditorial()
        >>> jsf = freezeThaw.JSONFreezer(ed)
        >>> jsf.jsonAttributes()
        ['color', 'misc', 'comment']

        >>> l = note.Lyric()
        >>> jsf = freezeThaw.JSONFreezer(l)
        >>> jsf.jsonAttributes()
        ['text', 'syllabic', 'number', 'identifier']

        Has autoGatherAttributes and others:

        >>> gn = note.GeneralNote()
        >>> jsf = freezeThaw.JSONFreezer(gn)
        >>> jsf.jsonAttributes()
        ['_duration', '_priority', 'offset', '_editorial', 'lyrics', 'expressions', 'articulations', 'tie']
        '''
        if self.storedObject is None:
            return []

        attributeList = []
        fqClassList = [self.fullyQualifiedClassFromObject(x) for x in self.storedObject.__class__.mro()]

        for i, thisClass in enumerate(fqClassList):
            inheritFrom = i + 1
            if thisClass in self.storedClassAttributes:
                attributeList = self.storedClassAttributes[thisClass]
                while "__INHERIT__" in attributeList:
                    inheritMarkerIndex = attributeList.index("__INHERIT__")
                    attributeList2 = attributeList[0:inheritMarkerIndex]
                    inheritClass = fqClassList[inheritFrom]
                    inheritFrom += 1
                    inheritAttributes = self.storedClassAttributes[inheritClass]
                    attributeList2.extend(inheritAttributes)
                    if inheritMarkerIndex != len(attributeList) - 1:
                        attributeList2.extend(attributeList[inheritMarkerIndex+1:])
                    attributeList = attributeList2

                if "__AUTO_GATHER__" in attributeList:
                    autoGathered = self.autoGatherAttributes()
                    # slow way of doing this.
                    autoGatherMarkerIndex = attributeList.index("__AUTO_GATHER__")
                    attributeList2 = attributeList[0:autoGatherMarkerIndex]
                    attributeList2.extend(autoGathered)
                    if autoGatherMarkerIndex != len(attributeList) - 1:
                        attributeList2.extend(attributeList[autoGatherMarkerIndex+1:])
                    attributeList = attributeList2
                return attributeList
        if attributeList == [] and autoGather is True:
            return self.autoGatherAttributes()


    def canBeFrozen(self, possiblyFreezeable):
        '''
        Returns True or False if this attribute can
        be frozen in a way that
        is stronger than just storing the repr of it.


        >>> jsf = freezeThaw.JSONFreezer()
        >>> jsf.canBeFrozen(note.Note())
        True
        >>> jsf.canBeFrozen(345)
        False
        >>> jsf.canBeFrozen(None)
        False

        Lists and Tuples and Dicts return False, but they
        are not just stored as __repr__, don't worry...

        >>> jsf.canBeFrozen([7,8])
        False
        
        >>> jsf.canBeFrozen(pitch.Microtone())
        True
        '''
        if possiblyFreezeable is None:
            return False
        if isinstance(possiblyFreezeable, (base.Music21Object, pitch.Microtone)):
            return True
        if isinstance(possiblyFreezeable, (list, tuple, dict)):
            return False
        if six.PY2 and isinstance(possiblyFreezeable, (int, str, unicode, float)): # @UndefinedVariable pylint: disable=undefined-variable
            return False
        elif six.PY3 and isinstance(possiblyFreezeable, (int, str, bytes, float)):
            return False 

        fqClassList = [self.fullyQualifiedClassFromObject(x) 
                                for x in possiblyFreezeable.__class__.mro()]

        for fqName in fqClassList:
            if fqName in self.storedClassAttributes:
                return True
        return False

    #---------------------------------------------------------------------------
    # core methods for getting and setting

    def getJSONDict(self, includeVersion=False):
        '''
        Return a dictionary representation for JSON processing.
        All component objects are similarly encoded as dictionaries.
        This method is recursively called as needed to store dictionaries
        of component objects that are :class:`~music21.freezeThaw.JSONFreezer` subclasses.


        >>> t = metadata.Text('my text')
        >>> t.language = 'en'
        >>> jsf = freezeThaw.JSONFreezer(t)
        >>> jsdict = jsf.getJSONDict()
        >>> jsdict['__class__']
        'music21.metadata.primitives.Text'
        >>> jsdict['__attr__']['_language']
        'en'
        '''
        obj = self.storedObject
        if obj is not None:
            src = {'__class__': self.className}
        else:
            src = {}
        # always store the version used to create this data
        if includeVersion is True:
            src['__version__'] = base.VERSION

        if obj is None:
            return src

        # flat data attributes
        flatData = {}
        if self.storedObject is None:
            return src

        for attr in self.jsonAttributes():
            attrValue = getattr(self.storedObject, attr)
            if isinstance(attrValue, fractions.Fraction):
                attrValue = float(attrValue)
            #environLocal.printDebug(['_getJSON', attr, "hasattr(attrValue, 'json')", hasattr(attrValue, 'json')])

            # do not store None values; assume initial/unset state
            if attrValue is None:
                continue

            # if, stored on this object, is an object w/ a json method
            if self.canBeFrozen(attrValue):
                #environLocal.printDebug(['attrValue', attrValue])
                internalJSONFreezer = JSONFreezer(attrValue)
                flatData[attr] = internalJSONFreezer.getJSONDict()

            # handle lists; look for objects that have json attributes
            elif isinstance(attrValue, (list, tuple)):
                flatData[attr] = []
                for attrValueSub in attrValue:
                    if self.canBeFrozen(attrValueSub):
                        internalJSONFreezer = JSONFreezer(attrValueSub)
                        flatData[attr].append(internalJSONFreezer.getJSONDict())
                    else: # just store normal data
                        flatData[attr].append(attrValueSub)

            # handle dictionaries; look for objects that have json attributes
            elif isinstance(attrValue, dict):
                flatData[attr] = {}
                for key in attrValue:
                    attrValueSub = attrValue[key]
                    # skip None values for efficiency
                    if attrValueSub is None:
                        continue
                    # see if this object stores a json object or otherwise
                    if self.canBeFrozen(attrValueSub):
                        internalJSONFreezer = JSONFreezer(attrValueSub)
                        flatData[attr][key] = internalJSONFreezer.getJSONDict()
                    else: # just store normal data
                        flatData[attr][key] = attrValueSub
            else:
                flatData[attr] = attrValue
        src['__attr__'] = flatData
        return src

    @property
    def json(self):
        '''
        Get string JSON data for this object.

        This method is only available if a JSONFreezer subclass object has been
        customized and configured by overriding the following methods:
        :meth:`~music21.freezeThaw.JSONFreezer.jsonAttributes`,
        :meth:`~music21.freezeThaw.JSONFreezer.music21ObjectFromString`.

        Return the dictionary returned by self.getJSONDict() as a JSON string.
        '''
        # when called from json property, include version number;
        # this should mean that only the outermost object has a version number
        return json.dumps(
            self.getJSONDict(includeVersion=True),
            sort_keys=True,
            )

    @property
    def prettyJson(self):
        lines = json.dumps(
            self.getJSONDict(includeVersion=True),
            sort_keys=True,
            indent=4,
            ).splitlines()
        return '\n'.join(line.rstrip() for line in lines)


    def jsonPrint(self):
        r'''
        Prints out the json output for a given object:


        >>> n = note.Note('D#5')
        >>> jsf = freezeThaw.JSONFreezer(n)
        >>> jsf.jsonPrint()
        {
          "__attr__": {
            "_duration": {
              "__attr__": {
                "_components": [],
                "_componentsNeedUpdating": true, 
                "_dotGroups": [
                  0
                ],
                "_linked": true,
                "_qtrLength": 1.0, 
                "_quarterLengthNeedsUpdating": false, 
                "_tuplets": [],
                "_typeNeedsUpdating": false
              }, 
              "__class__": "music21.duration.Duration"
            }, 
            "_notehead": "normal", 
            "_noteheadParenthesis": false, 
            "_priority": 0, 
            "_stemDirection": "unspecified", 
            "articulations": [], 
            "beams": {
              "__attr__": {
                "beamsList": [], 
                "feathered": false
              }, 
              "__class__": "music21.beam.Beams"
            }, 
            "expressions": [], 
            "lyrics": [], 
            "offset": 0.0, 
            "pitch": {
              "__attr__": {
                "_accidental": {
                  "__attr__": {
                    "_alter": 1.0, 
                    "_displayType": "normal", 
                    "_modifier": "#", 
                    "_name": "sharp" 
                  }, 
                  "__class__": "music21.pitch.Accidental"
                }, 
                "_microtone": {
                  "__attr__": {
                    "_centShift": 0, 
                    "_harmonicShift": 1
                  }, 
                  "__class__": "music21.pitch.Microtone"
                }, 
                "_octave": 5, 
                "_step": "D"
              }, 
              "__class__": "music21.pitch.Pitch"
            }
          }, 
          "__class__": "music21.note.Note", 
          "__version__": [
            2, 
            ..., 
            ...
          ]
        }
        '''
        print(json.dumps(
            self.getJSONDict(includeVersion=True),
            sort_keys=True,
            indent=2,
            ))

    def jsonWrite(self, fp, formatOutput=True):
        '''
        Given a file path, write JSON to a file
        for this object.

        File extension should be .json. File is opened
        and closed within this method call.
        '''
        with io.open(fp, mode='w', encoding='utf-8') as f:
            jsonDict = self.getJSONDict(includeVersion=True)
            if formatOutput is False:
                jsonString = json.dumps(
                    jsonDict,
                    sort_keys=False,
                    )
            else:
                jsonString = json.dumps(
                    jsonDict,
                    sort_keys=True,
                    indent=2,
                    )
            f.write(jsonString)

class JSONThawer(JSONFreezeThawBase):
    '''
    Class that takes JSON input and makes a Music21Object.
    '''
    def __init__(self, storedObject=None):
        JSONFreezeThawBase.__init__(self, storedObject)

    def _isComponent(self, target):
        '''
        Return a boolean if the provided object is a
        dictionary that defines a __class__ key, the necessary
        conditions to try to instantiate a component object
        with the music21ObjectFromString method.
        '''
        # on export, check for attribute
        if isinstance(target, dict) and '__class__' in target:
            return True
        return False

    def _buildComponent(self, src):
        # get instance from subclass overridden method
        obj = self.music21ObjectFromString(src['__class__'])
        # assign dictionary (property takes dictionary or string)
        self._setJSON(src, obj)
        objFQClass = self.fullyQualifiedClassFromObject(obj)
        if objFQClass in self.postClassCreateCall:
            callMethodStr = self.postClassCreateCall[objFQClass][0]
            # TODO: add args
            callMethod = getattr(obj, callMethodStr)
            callMethod(obj)

        return obj

    def _setJSON(self, jsonStr, inputObject = None):
        '''
        Set this object based on a JSON string
        or instantiated dictionary representation.


        >>> t = metadata.Text('my text')
        >>> t.language = 'en'
        >>> jsf = freezeThaw.JSONFreezer(t)
        >>> jsfJSON = jsf.json

        >>> tNew = metadata.Text()
        >>> jsf2 = freezeThaw.JSONThawer(tNew)
        >>> jsf2.json = jsfJSON
        >>> str(tNew)
        'my text'

        Notice that some normal strings come back as unicode:

        >>> tNew.language
        'en'


        Notes are more complex. Let's not even give an
        input object this time:

        >>> n = note.Note("D#5")
        >>> n.duration.quarterLength = 3.0
        >>> jsf = freezeThaw.JSONFreezer(n)
        >>> jsfJSON = jsf.json


        >>> jsf2 = freezeThaw.JSONThawer()
        >>> jsf2.json = jsfJSON
        >>> n2 = jsf2.storedObject
        >>> n2
        <music21.note.Note D#>
        >>> n2.octave
        5

        Test that other attributes get updated automatically

        >>> n2.duration.dots
        1
        '''
        #environLocal.printDebug(['_setJSON: srcStr', jsonStr])
        if isinstance(jsonStr, dict):
            d = jsonStr # do not loads
        else:
            d = json.loads(jsonStr)

        if inputObject is not None:
            obj = inputObject
        elif self.storedObject is not None:
            obj = self.storedObject
        elif d['__class__'] is not None:
            obj = self.music21ObjectFromString(d['__class__'])
            self.storedObject = obj
        else:
            raise JSONThawerException("Cannot find an object class definition in the jsonStr; you must provide an input object")

        for attr in d:
            #environLocal.printDebug(['_setJSON: attr', attr, d[attr]])
            if attr == '__class__':
                pass
            elif attr == '__version__':
                pass
            elif attr == '__attr__':
                for key in d[attr]:
                    attrValue = d[attr][key]
                    if attrValue == None or isinstance(attrValue,
                        (int, float)):
                        try:
                            setattr(obj, key, attrValue)
                        except AttributeError:
                            raise JSONThawerException("Cannot set attribute '%s' to %s for obj %r" % (key, attrValue, obj))
                    # handle a list or tuple, looking for dicts that define objs
                    elif isinstance(attrValue, (list, tuple)):
                        subList = []
                        for attrValueSub in attrValue:
                            if self._isComponent(attrValueSub):
                                subList.append(
                                    self._buildComponent(attrValueSub))
                            else:
                                subList.append(attrValueSub)
                        setattr(obj, key, subList)
                    # handle a dictionary, looking for dicts that define objs
                    elif isinstance(attrValue, dict):
                        # could be a data dict or a dict of objects;
                        # if an object, will have a __class__ key
                        if self._isComponent(attrValue):
                            setattr(obj, key, self._buildComponent(attrValue))
                        # its a data dictionary; could contain objects as
                        # dictionaries, or flat data
                        else:
                            subDict = {}
                            for subKey in attrValue:
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
                            try:
                                dst = getattr(obj, key)
                            except AttributeError as ae:
                                if key == "_storage": # changed name; help older .json files...
                                    dst = getattr(obj, "storage")
                                else:
                                    raise JSONFreezerException("Problem with key: %s for object %s: %s" % (key, obj, ae))

                            # updating the dictionary preserves default
                            # values created at init
                            dst.update(subDict)
                    else: # assume a string
                        try:
                            setattr(obj, key, attrValue)
                        except AttributeError:
                            pass
            else:
                raise JSONFreezerException('cannot handle json attr: %s'% attr)

    json = property(fset=_setJSON,
        doc = '''
        Take string JSON data from :meth:`~music21.freezeThaw.JSONFreezer.json` and
        produce an object and store it in
        self.storedObject.`.
        ''')

    def jsonRead(self, fp):
        '''
        Given a file path, read JSON from a file to this object.
        Default file extension should be .json. File is opened
        and closed within this method call.

        returns the stored object
        '''
        f = open(fp)
        self.json = f.read()
        f.close()
        return self.storedObject

#------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testSimpleFreezeThaw(self):
        from music21 import stream, note
        s = stream.Stream()
        sDummy = stream.Stream()
        n = note.Note()
        s.insert(2.0, n)
        sDummy.insert(3.0, n)

        sf = StreamFreezer(s)
        out = sf.writeStr()

        del(s)
        del(sDummy)
        del(n)

        st = StreamThawer()
        st.openStr(out)
        outStream = st.stream
        self.assertEqual(len(outStream), 1)
        self.assertEqual(outStream[0].offset, 2.0)

    def testFreezeThawWithSpanner(self):
        from music21 import stream, note, spanner
        s = stream.Stream()
        sDummy = stream.Stream()
        n = note.Note()
        sl1 = spanner.Slur([n])
        s.insert(0.0, sl1)
        s.insert(2.0, n)
        sDummy.insert(3.0, n)

        self.assertIs(s.spanners[0].getFirst(), s.notes[0])

        sf = StreamFreezer(s)
        out = sf.writeStr(fmt='jsonpickle') # easier to read...

        del(s)
        del(sDummy)
        del(n)

        st = StreamThawer()
        st.openStr(out)
        outStream = st.stream
        self.assertEqual(len(outStream), 2)
        self.assertEqual(outStream.notes[0].offset, 2.0)
        self.assertIs(outStream.spanners[0].getFirst(), outStream.notes[0])

    def testFreezeThawCorpusFileWithSpanners(self):
        from music21 import corpus
        c = corpus.parse('luca/gloria')
        sf = StreamFreezer(c)
        data = sf.writeStr(fmt='pickle')

        st = StreamThawer()
        st.openStr(data)
        s = st.stream
        self.assertEqual(len(s.parts[0].measure(7).notes), 6)


    def xtestSimplePickle(self):
        from music21 import freezeThaw
        from music21 import corpus

        c = corpus.parse('bwv66.6').parts[0].measure(0).notes
        #c.show('t')

#        for el in c:
#            storedIds.append(el.id)
#            storedSitesIds.append(id(el.sites))
#
#        return

        n1 = c[0]
        n2 = c[1]
        sf = freezeThaw.StreamFreezer(c, fastButUnsafe=True)
        sf.setupSerializationScaffold()
        for dummy in n1.sites.siteDict:
            pass
            #print idKey
            #print n1.sites.siteDict[idKey]['obj']
        for dummy in n2.sites.siteDict:
            pass
            #print idKey
            #print n2.sites.siteDict[idKey]['obj']

        dummy = pickleMod.dumps(c, protocol=-1)


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

    def testFreezeThawSimpleVariant(self):
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

        sf = freezeThaw.StreamFreezer(s)
        d = sf.writeStr()

        st = freezeThaw.StreamThawer()
        st.openStr(d)
        s = st.stream


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

        #test Variant is in stream
        unused_v1 = c.parts[0].getElementsByClass('Variant')[0]

        sf = freezeThaw.StreamFreezer(c, fastButUnsafe=True)
        #sf.v = v
        d = sf.writeStr()
        #print d

        #print "thawing."

        st = freezeThaw.StreamThawer()
        st.openStr(d)
        s = st.stream
        #s.show('lily.pdf')
        p0 = s.parts[0]
        variants = p0.getElementsByClass('Variant')
        v2 = variants[0]
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

        sf = freezeThaw.StreamFreezer(s2, fastButUnsafe = False)
        sf.setupSerializationScaffold()

        # test safety
        self.assertEqual(s2.hasElement(n1), True)
        self.assertEqual(s1.hasElement(n1), True)

#----------JSON Serialization------------------------------


#    def testJSONSerializationPitchA(self):
#        from music21 import pitch
#
#        m = pitch.Microtone(40)
#        self.assertEqual(str(m), '(+40c)')
#
#        mAlt = pitch.Microtone()
#        mAlt.json = m.json
#        self.assertEqual(str(mAlt), '(+40c)')
#
#        a = pitch.Accidental('##')
#        self.assertEqual(str(a), '<accidental double-sharp>')
#        aAlt = pitch.Accidental()
#        aAlt.json = a.json
#        self.assertEqual(str(aAlt), '<accidental double-sharp>')
#
#        p = pitch.Pitch(ps=61.2)
#        self.assertEqual(str(p), 'C#4(+20c)')
#        pAlt = pitch.Pitch()
#        pAlt.json = p.json
#        self.assertEqual(str(pAlt), 'C#4(+20c)')

#    def testDerivationSerializationA(self):
#        from music21 import derivation
#
#        d = derivation.Derivation()
#        self.assertEqual(d.jsonAttributes(), ['_ancestor', '_ancestorId', '_container', '_containerId', '_method'])
#
#        self.assertEqual(hasattr(d, 'json'), True)

    def testJSONPickleSpanner(self):
        from music21 import converter, note, stream, spanner
        n1 = note.Note('C')
        n2 = note.Note('D')
        s1 = stream.Stream()
        sp = spanner.Line([n1, n2])
        s1.insert(0, sp)
        s1.append(n1)
        s1.append(n2)
        frozen = converter.freezeStr(s1, 'jsonPickle')
        #print frozen
        unused_thawed = converter.thawStr(frozen)
        

    def testPickleMidi(self):
        from music21 import converter
        a = os.path.join(common.getSourceFilePath(),
                         'midi',
                         'testPrimitive',
                         'test03.mid')

        #a = 'https://github.com/ELVIS-Project/vis/raw/master/test_corpus/prolationum-sanctus.midi'
        c = converter.parse(a)
        f = converter.freezeStr(c)
        d = converter.thawStr(f)
        self.assertEqual(d[1][20].volume._client.__class__.__name__, 'weakref')

#------------------------------------------------------------------------------
if __name__ == "__main__":
    import music21
    #import sys
    #sys.argv.append('testFreezeThawWithSpanner')
    music21.mainTest(Test)
    


#------------------------------------------------------------------------------
# eof


