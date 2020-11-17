# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Name:         freezeThaw.py
# Purpose:      Methods for storing any music21 object on disk.
#               Uses pickle and json
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2011-2012 Michael Scott Cuthbert and the music21
#               Project
# License:      BSD, see license.txt
# -----------------------------------------------------------------------------
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
http://docs.python.org/library/json.html).
Music21 has two implementations of JSON (confusing, no?)
because we weren't sure and are still not sure which will be best in the long-run:
the first approach
uses explicit lists of attributes that need to be stored and just saves those. This uses a
homemade set of methods that are specifically tailored for music21; but it misses some things that
may be important to you.  The second approach uses the the freely distributable
`jsonpickle` module. This approach probably stores more data than
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
import os
import pathlib
import pickle
import time
import unittest
import zlib

from typing import Union, List

from music21 import base
from music21 import common
from music21 import defaults
from music21 import derivation
from music21 import exceptions21
# from music21.tree.trees import ElementTree

from music21 import environment
_MOD = 'freezeThaw'
environLocal = environment.Environment(_MOD)

# -----------------------------------------------------------------------------


class FreezeThawException(exceptions21.Music21Exception):
    pass

# -----------------------------------------------------------------------------


class StreamFreezeThawBase:
    '''
    Contains a few methods that are used for both
    StreamFreezer and StreamThawer
    '''

    def __init__(self):
        self.stream = None

    def getPickleFp(self, directory: Union[str, pathlib.Path]):
        if directory is None:
            raise ValueError('directory must be specified')

        if not isinstance(directory, pathlib.Path):
            directory = pathlib.Path(directory)

        # cannot get data from stream, as offsets are broken
        streamStr = str(time.time())
        return directory / ('m21-' + common.getMd5(streamStr) + '.p')

    def getJsonFp(self, directory):
        return self.getPickleFp(directory) + '.json'

    def findAllM21Objects(self, streamObj):
        '''
        find all M21 Objects in _elements and _endElements and in nested streams.
        '''
        allObjs = []
        for x in streamObj:
            allObjs.append(x)
            if x.isStream:
                allObjs.extend(self.findAllM21Objects(x))
        return allObjs


# -----------------------------------------------------------------------------
class StreamFreezer(StreamFreezeThawBase):
    '''
    This class is used to freeze a Stream, preparing it for serialization
    and providing conversion routines.

    In general, use :func:`~music21.converter.freeze`
    for serializing to a file.

    Use the :func:`~music21.converter.unfreeze` to read from a
    serialized file

    >>> s = stream.Stream()
    >>> s.repeatAppend(note.Note('C4'), 8)
    >>> temp = [s[n].transpose(n, inPlace=True) for n in range(len(s))]

    >>> sf = freezeThaw.StreamFreezer(s)  # provide a Stream at init
    >>> data = sf.writeStr(fmt='pickle')  # pickle is default format

    >>> st = freezeThaw.StreamThawer()
    >>> st.openStr(data)
    >>> s = st.stream
    >>> s.show('t')
    {0.0} <music21.note.Note C>
    {1.0} <music21.note.Note C#>
    {2.0} <music21.note.Note D>
    {3.0} <music21.note.Note E->
    {4.0} <music21.note.Note E>
    {5.0} <music21.note.Note F>
    {6.0} <music21.note.Note F#>
    {7.0} <music21.note.Note G>

    >>> sf2 = freezeThaw.StreamFreezer(s)  # do not reuse StreamFreezers
    >>> data2 = sf2.writeStr(fmt='jsonpickle')

    >>> st2 = freezeThaw.StreamThawer()
    >>> st2.openStr(data2)
    >>> s2 = st2.stream
    >>> s2.show('t')
    {0.0} <music21.note.Note C>
    {1.0} <music21.note.Note C#>
    {2.0} <music21.note.Note D>
    {3.0} <music21.note.Note E->
    {4.0} <music21.note.Note E>
    {5.0} <music21.note.Note F>
    {6.0} <music21.note.Note F#>
    {7.0} <music21.note.Note G>


    >>> c = corpus.parse('luca/gloria')
    >>> sf = freezeThaw.StreamFreezer(c)
    >>> data = sf.writeStr(fmt='pickle')

    >>> st = freezeThaw.StreamThawer()
    >>> st.openStr(data)
    >>> s2 = st.stream
    >>> len(s2.parts[0].measure(7).notes) == 6
    True

    JSONPickle is also an acceptable way of Freezing streams.  Especially
    for going to music21j in Javascript:

    >>> sf2 = freezeThaw.StreamFreezer(c)  # do not reuse StreamFreezers
    >>> data2 = sf2.writeStr(fmt='jsonpickle')
    >>> st2 = freezeThaw.StreamThawer()
    >>> st2.openStr(data2)
    >>> s3 = st2.stream
    >>> len(s3.parts[0].measure(7).notes) == 6
    True

    '''

    def __init__(self, streamObj=None, fastButUnsafe=False, topLevel=True, streamIds=None):
        super().__init__()
        # must make a deepcopy, as we will be altering .sites
        self.stream = None
        # clear all sites only if the top level.
        self.topLevel = topLevel
        self.streamIds = streamIds

        self.subStreamFreezers = {}  # this will keep track of sub freezers for spanners

        if streamObj is not None and fastButUnsafe is False:
            # deepcopy necessary because we mangle sites in the objects
            # before serialization
            self.stream = copy.deepcopy(streamObj)
            # self.stream = streamObj
        elif streamObj is not None:
            self.stream = streamObj

    def packStream(self, streamObj=None):
        '''
        Prepare the passed in Stream in place, return storage
        dictionary format.

        >>> from pprint import pprint
        >>> s = stream.Stream()
        >>> n = note.Note('D#4')
        >>> s.append(n)
        >>> sf = freezeThaw.StreamFreezer(s)
        >>> pprint(sf.packStream())
        {'m21Version': (...), 'stream': <music21.stream.Stream 0x1289212>}

        '''
        # do all things necessary to setup the stream
        if streamObj is None:
            streamObj = self.stream
        self.setupSerializationScaffold(streamObj)
        storage = {'stream': streamObj, 'm21Version': base.VERSION}
        return storage

    def setupSerializationScaffold(self, streamObj=None):
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

        >>> a = stream.Stream()
        >>> n = note.Note()
        >>> n.duration.type = 'whole'
        >>> a.repeatAppend(n, 10)
        >>> sf = freezeThaw.StreamFreezer(a)
        >>> sf.setupSerializationScaffold()
        '''
        if streamObj is None:
            streamObj = self.stream
            if streamObj is None:
                raise FreezeThawException('You need to pass in a stream when creating to work')
        # might not work when recurse yields...
        allEls = list(streamObj.recurse(restoreActiveSites=False))

        if self.topLevel is True:
            self.findActiveStreamIdsInHierarchy(streamObj)

        for el in allEls:
            if 'Variant' in el.classes:
                # works like a whole new hierarchy...  # no need for deepcopy
                subSF = StreamFreezer(
                    el._stream,
                    fastButUnsafe=True,
                    streamIds=self.streamIds,
                    topLevel=False,
                )
                subSF.setupSerializationScaffold()
            elif 'Spanner' in el.classes:
                # works like a whole new hierarchy...  # no need for deepcopy
                subSF = StreamFreezer(
                    el.spannerStorage,
                    fastButUnsafe=True,
                    streamIds=self.streamIds,
                    topLevel=False,
                )
                subSF.setupSerializationScaffold()
            elif el.isStream:
                self.removeStreamStatusClient(el)
                # removing seems to create problems for jsonPickle with Spanners

        self.removeStreamStatusClient(streamObj)
        # removing seems to create problems for jsonPickle with Spanners
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
        music21.sites.SitesException: an entry for this object <music21.note.Note D#>
               is not stored in stream <music21.stream.Stream stream s>
        >>> n.getOffsetBySite(t)
        20.0


        After recursiveClearSites n will be not know its location anywhere...

        >>> sf.recursiveClearSites(s)
        >>> len(n.sites)  # just the None site
        1

        This leaves n and t in strange positions, because n is in t.elements still....

        >>> n in t.elements
        True

        This predicament is why when the standard freezeThaw call is made, what is frozen is a
        deepcopy of the Stream so that nothing is left in an unusable position


        '''
        if hasattr(startObj, '_storedElementOffsetTuples'):
            storedElementOffsetTuples = startObj._storedElementOffsetTuples
            for el, unused_offset in storedElementOffsetTuples:
                if el.isStream:
                    self.recursiveClearSites(el)
                if 'Spanner' in el.classes:
                    self.recursiveClearSites(el.spannerStorage)
                if 'Variant' in el.classes:
                    self.recursiveClearSites(el._stream)
                if hasattr(el, '_derivation'):
                    el._derivation = derivation.Derivation()  # reset

                if hasattr(el, '_offsetDict'):
                    el._offsetDict = {}
                el.sites.clear()
                el.activeSite = None
            startObj._derivation = derivation.Derivation()  # reset
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
        >>> n1 = note.Note('C#')
        >>> n2 = note.Note('E-')
        >>> bl1 = bar.Barline()
        >>> s.insert(0.0, n1)
        >>> s.insert(1.0, n2)
        >>> s.storeAtEnd(bl1)

        >>> sFreeze = freezeThaw.StreamFreezer()
        >>> sFreeze.setupStoredElementOffsetTuples(s)
        >>> s._elements, s._endElements
        ([], [])
        >>> s._storedElementOffsetTuples
        [(<music21.note.Note C#>, 0.0),
         (<music21.note.Note E->, 1.0),
         (<music21.bar.Barline type=regular>, 'end')]
        >>> n1.getOffsetBySite(s)
        Traceback (most recent call last):
        music21.sites.SitesException: an entry for this object <music21.note.Note C#> is
             not stored in stream <music21.stream.Measure 0 offset=0.0>

        Trying it again, but now with substreams:

        >>> s2 = stream.Measure()
        >>> n1 = note.Note('C#')
        >>> n2 = note.Note('E-')
        >>> bl1 = bar.Barline()
        >>> v1 = stream.Voice()
        >>> n3 = note.Note('F#')
        >>> v1.insert(2.0, n3)
        >>> s2.insert(0.0, n1)
        >>> s2.insert(1.0, n2)
        >>> s2.storeAtEnd(bl1)
        >>> s2.insert(2.0, v1)
        >>> sFreeze.setupStoredElementOffsetTuples(s2)

        >>> v1._storedElementOffsetTuples
        [(<music21.note.Note F#>, 2.0)]
        >>> s2._storedElementOffsetTuples
        [(<music21.note.Note C#>, 0.0),
         (<music21.note.Note E->, 1.0),
         (<music21.stream.Voice ...>, 2.0),
         (<music21.bar.Barline type=regular>, 'end')]
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
            # e._preFreezeId = id(e)
            # elementDict[id(e)] = s.elementOffset(e)
        for e in streamObj._endElements:
            elementTuple = (e, 'end')
            storedElementOffsetTuples.append(elementTuple)
            if e.isStream:
                self.setupStoredElementOffsetTuples(e)
            e.sites.remove(streamObj)
            e.activeSite = None

        streamObj._storedElementOffsetTuples = storedElementOffsetTuples
        # streamObj._elementTree = None
        streamObj._offsetDict = {}
        streamObj._elements = []
        streamObj._endElements = []
        streamObj.coreElementsChanged()

    def findActiveStreamIdsInHierarchy(
        self,
        hierarchyObject=None,
        getSpanners=True,
        getVariants=True
    ) -> List[int]:
        '''
        Return a list of all Stream ids anywhere in the hierarchy.  By id,
        we mean `id(s)` not `s.id` -- so they are memory locations and unique.

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
        ...         raise Exception('Missing Id')
        >>> for thisId in foundIds:
        ...     if thisId not in shouldFindIds:
        ...         raise Exception('Additional Id Found')

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

        >>> id(staffGroup.spannerStorage) in foundIds
        True

        Variants are treated similarly:

        >>> s = stream.Stream()
        >>> m = stream.Measure()
        >>> m.append(note.Note(type='whole'))
        >>> s.append(m)

        >>> s2 = stream.Stream()
        >>> m2 = stream.Measure()
        >>> n2 = note.Note('D#4')
        >>> n2.duration.type = 'whole'
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
        ...        print('this should not happen...', allIds, id(streamElement))

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
                                                  restoreActiveSites=False,
                                                  includeSelf=True)
        streamIds = [id(s) for s in streamsFoundGenerator]

        if getSpanners is True:
            spannerBundle = streamObj.spannerBundle
            streamIds += spannerBundle.getSpannerStorageIds()

        if getVariants is True:
            for el in streamObj.recurse(includeSelf=True).getElementsByClass('Variant'):
                streamIds += self.findActiveStreamIdsInHierarchy(el._stream)

        # should not happen that there are duplicates, but possible with spanners...
        # Python's uniq value...
        streamIds = list(set(streamIds))

        self.streamIds = streamIds
        return streamIds

    # --------------------------------------------------------------------------

    def parseWriteFmt(self, fmt):
        '''
        Parse a passed-in write format

        >>> sf = freezeThaw.StreamFreezer()
        >>> sf.parseWriteFmt(None)
        'pickle'
        >>> sf.parseWriteFmt('JSON')
        'jsonpickle'
        '''
        if fmt is None:  # this is the default
            return 'pickle'
        fmt = fmt.strip().lower()
        if fmt in ['p', 'pickle']:
            return 'pickle'
        elif fmt in ['jsonpickle', 'json']:
            return 'jsonpickle'
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
            raise FreezeThawException('Cannot zip files except zlib...')

        fmt = self.parseWriteFmt(fmt)

        if fp is None:
            directory = environLocal.getRootTempDir()
            if fmt.startswith('json'):
                fp = self.getJsonFp(directory)
            else:
                fp = self.getPickleFp(directory)
        else:
            if not isinstance(fp, pathlib.Path):
                fp = pathlib.Path(fp)

            if not fp.is_absolute():  # assume its a complete path
                fp = environLocal.getRootTempDir() / fp

        storage = self.packStream(self.stream)

        environLocal.printDebug(['writing fp', str(fp)])

        if fmt == 'pickle':
            # previously used highest protocol, but now protocols are changing too
            # fast, and might not be compatible for sharing.
            # packStream() returns a storage dictionary
            pickleString = pickle.dumps(storage)
            if zipType == 'zlib':
                pickleString = zlib.compress(pickleString)

            with open(fp, 'wb') as f:  # binary
                f.write(pickleString)
        elif fmt == 'jsonpickle':
            import jsonpickle
            data = jsonpickle.encode(storage, **keywords)
            if zipType == 'zlib':
                data = zlib.compress(data)

            with open(fp, 'w') as f:
                f.write(data)

        else:
            raise FreezeThawException('bad StreamFreezer format: %s' % fmt)

        # must restore the passed-in Stream
        # self.teardownStream(self.stream)
        return fp

    def writeStr(self, fmt=None, **keywords):
        '''
        Convert the object to a pickled/jsonpickled string
        and return the string
        '''
        fmt = self.parseWriteFmt(fmt)
        storage = self.packStream(self.stream)

        if fmt == 'pickle':
            out = pickle.dumps(storage, protocol=-1)
        elif fmt == 'jsonpickle':
            import jsonpickle
            out = jsonpickle.encode(storage, **keywords)
        else:
            raise FreezeThawException('bad StreamFreezer format: %s' % fmt)

        # self.teardownStream(self.stream)
        return out


class StreamThawer(StreamFreezeThawBase):
    '''
    This class is used to thaw a data string into a Stream

    In general user :func:`~music21.converter.parse` to read from a
    serialized file.

    >>> s = stream.Stream()
    >>> s.repeatAppend(note.Note('C4'), 8)
    >>> temp = [s[n].transpose(n, inPlace=True) for n in range(len(s))]

    >>> sf = freezeThaw.StreamFreezer(s)  # provide a Stream at init
    >>> data = sf.writeStr(fmt='pickle')  # pickle is default format

    >>> sfOut = freezeThaw.StreamThawer()
    >>> sfOut.openStr(data)
    >>> s = sfOut.stream
    >>> s.show('t')
    {0.0} <music21.note.Note C>
    {1.0} <music21.note.Note C#>
    {2.0} <music21.note.Note D>
    {3.0} <music21.note.Note E->
    {4.0} <music21.note.Note E>
    {5.0} <music21.note.Note F>
    {6.0} <music21.note.Note F#>
    {7.0} <music21.note.Note G>
    '''

    def __init__(self):
        super().__init__()
        self.stream = None

    # TODO: Test that the _NoneSite singleton is restored properly after freezeThaw.

    def teardownSerializationScaffold(self, streamObj=None):
        '''
        After rebuilding this Stream from pickled storage, prepare this as a normal `Stream`.

        If streamObj is None, runs it on the embedded stream

        >>> a = stream.Stream()
        >>> n = note.Note()
        >>> n.duration.type = 'whole'
        >>> a.repeatAppend(n, 10)
        >>> sf = freezeThaw.StreamFreezer(a)
        >>> sf.setupSerializationScaffold()

        >>> st = freezeThaw.StreamThawer()
        >>> st.teardownSerializationScaffold(a)
        '''
        def _fixId(innerEl):
            if (innerEl.id is not None
                    and common.isNum(innerEl.id)
                    and innerEl.id > defaults.minIdNumberToConsiderMemoryLocation):
                innerEl.id = id(innerEl)

        if streamObj is None:
            streamObj = self.stream
            if streamObj is None:
                raise FreezeThawException('You need to pass in a stream when creating to work')

        storedAutoSort = streamObj.autoSort
        streamObj.autoSort = False

        self.restoreElementsFromTuples(streamObj)

        self.restoreStreamStatusClient(streamObj)
        # removing seems to create problems for jsonPickle with Spanners
        allEls = self.findAllM21Objects(streamObj)

        for e in allEls:
            eClasses = e.classes
            if 'Variant' in eClasses:
                # works like a whole new hierarchy...  # no need for deepcopy
                subSF = StreamThawer()
                subSF.teardownSerializationScaffold(e._stream)
                e._stream.coreElementsChanged()
                e._cache = {}
                # for el in e._stream.flat:
                #    print(el, el.offset, el.sites.siteDict)
            elif 'Spanner' in eClasses:
                subSF = StreamThawer()
                subSF.teardownSerializationScaffold(e.spannerStorage)
                e.spannerStorage.coreElementsChanged()
                e._cache = {}
            elif e.isStream:
                self.restoreStreamStatusClient(e)
                # removing seems to create problems for jsonPickle with Spanners

            _fixId(e)
            # e.wrapWeakref()

        # restore to whatever it was
        streamObj.autoSort = storedAutoSort
        streamObj.coreElementsChanged()
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

        >>> n1 = note.Note('C#')
        >>> n2 = note.Note('E-')
        >>> bl1 = bar.Barline()
        >>> tupleList = [(n1, 0.0), (n2, 1.0), (bl1, 'end')]
        >>> s._storedElementOffsetTuples = tupleList

        >>> sThaw = freezeThaw.StreamThawer()
        >>> sThaw.restoreElementsFromTuples(s)
        >>> s.show('text')
        {0.0} <music21.note.Note C#>
        {1.0} <music21.note.Note E->
        {2.0} <music21.bar.Barline type=regular>
        >>> s._endElements
        [<music21.bar.Barline type=regular>]
        >>> s[1].getOffsetBySite(s)
        1.0

        Trying it again, but now with substreams:

        >>> s2 = stream.Measure()
        >>> v1 = stream.Voice()
        >>> n3 = note.Note('F#')
        >>> v1._storedElementOffsetTuples = [(n3, 2.0)]
        >>> tupleList = [(n1, 0.0), (n2, 1.0), (bl1, 'end'), (v1, 2.0)]
        >>> s2._storedElementOffsetTuples = tupleList
        >>> sThaw.restoreElementsFromTuples(s2)
        >>> s2.show('text')
        {0.0} <music21.note.Note C#>
        {1.0} <music21.note.Note E->
        {2.0} <music21.stream.Voice ...>
            {2.0} <music21.note.Note F#>
        {5.0} <music21.bar.Barline type=regular>
        '''
        if hasattr(streamObj, '_storedElementOffsetTuples'):
            # streamObj._elementTree = ElementTree(source=streamObj)
            for e, offset in streamObj._storedElementOffsetTuples:
                if offset != 'end':
                    try:
                        streamObj.coreInsert(offset, e)
                    except AttributeError:
                        print('Problem in decoding... some debug info...')
                        print(offset, e)
                        print(streamObj)
                        print(streamObj.activeSite)
                        raise
                else:
                    streamObj.coreStoreAtEnd(e)
            del streamObj._storedElementOffsetTuples
            streamObj.coreElementsChanged()

        for subElement in streamObj:
            if subElement.isStream is True:
                # note that the elements may have already been restored
                # if the spanner stores a part or something in the Stream
                # for instance in a StaffGroup object
                self.restoreElementsFromTuples(subElement)

    def restoreStreamStatusClient(self, streamObj):
        '''
        Restore the streamStatus client to point to the Stream
        (do we do this for derivations?  No: there should not be derivations stored.
        Other objects?  Unclear...)
        '''
        if hasattr(streamObj, 'streamStatus'):
            streamObj.streamStatus.client = streamObj

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
        if isinstance(storage, bytes):
            if storage.startswith(b'{"'):
                # was m21Version": {"py/tuple" but order of dict may change
                return 'jsonpickle'
            else:
                return 'pickle'
        else:
            if storage.startswith('{"'):
                # was m21Version": {"py/tuple" but order of dict may change
                return 'jsonpickle'
            else:
                return 'pickle'

    def open(self, fp, zipType=None):
        '''
        For a supplied file path to a pickled stream, unpickle
        '''
        if not os.path.exists(fp):
            directory = environLocal.getRootTempDir()
            fp = directory / fp

        f = open(fp, 'rb')
        fileData = f.read()  # TODO: do not read entire file
        f.close()

        fmt = self.parseOpenFmt(fileData)
        if fmt == 'pickle':
            common.restorePathClassesAfterUnpickling()
            # environLocal.printDebug(['opening fp', fp])
            f = open(fp, 'rb')
            if zipType is None:
                storage = pickle.load(f)
            elif zipType == 'zlib':
                compressedString = f.read()
                uncompressed = zlib.decompress(compressedString)
                try:
                    storage = pickle.loads(uncompressed)
                except AttributeError as e:
                    common.restoreWindowsAfterUnpickling()
                    raise FreezeThawException(
                        f'Problem in decoding: {e}'
                    ) from e
            else:
                common.restorePathClassesAfterUnpickling()
                raise FreezeThawException(f'Unknown zipType {zipType}')
            common.restorePathClassesAfterUnpickling()
            f.close()
        elif fmt == 'jsonpickle':
            import jsonpickle
            f = open(fp, 'r')
            data = f.read()
            f.close()
            storage = jsonpickle.decode(data)
        else:
            raise FreezeThawException(f'bad StreamFreezer format: {fmt!r}')

        self.stream = self.unpackStream(storage)

    def openStr(self, fileData, pickleFormat=None):
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
            storage = pickle.loads(fileData)
        elif fmt == 'jsonpickle':
            import jsonpickle
            storage = jsonpickle.decode(fileData)
        else:
            raise FreezeThawException('bad StreamFreezer format: %s' % fmt)
        environLocal.printDebug('StreamThawer:openStr: storage is: %s' % storage)
        self.stream = self.unpackStream(storage)

# -------------------------------------------------------------------------------

# -----------------------------------------------------------------------------


class Test(unittest.TestCase):

    def testSimpleFreezeThaw(self):
        from music21 import stream, note
        s = stream.Stream()
        sDummy = stream.Stream()
        n = note.Note()
        s.insert(2.0, n)
        sDummy.insert(3.0, n)

        sf = StreamFreezer(s)
        out = sf.writeStr()

        del s
        del sDummy
        del n

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
        out = sf.writeStr(fmt='jsonpickle')  # easier to read...

        del s
        del sDummy
        del n

        st = StreamThawer()
        st.openStr(out)
        outStream = st.stream
        self.assertEqual(len(outStream), 2)
        self.assertEqual(outStream.notes[0].offset, 2.0)
        self.assertIs(outStream.spanners[0].getFirst(), outStream.notes[0])

    def testFreezeThawJsonPickleEnum(self):
        '''
        Versions of jsonpickle prior to  0.9.3 were having problems serializing Enums.

        Works now
        '''
        from music21 import corpus
        c = corpus.parse('luca/gloria').parts[2].measures(1, 2)
        sf2 = StreamFreezer(c)
        data2 = sf2.writeStr(fmt='jsonpickle')
        st2 = StreamThawer()
        st2.openStr(data2)

    def testFreezeThawCorpusFileWithSpanners(self):
        from music21 import corpus
        c = corpus.parse('luca/gloria')
        sf = StreamFreezer(c)
        data = sf.writeStr(fmt='pickle')

        st = StreamThawer()
        st.openStr(data)
        s = st.stream
        self.assertEqual(len(s.parts[0].measure(7).notes), 6)

    def x_testSimplePickle(self):
        from music21 import freezeThaw
        from music21 import corpus

        c = corpus.parse('bwv66.6').parts[0].measure(0).notes
        #  c.show('t')
        #
        # for el in c:
        #     storedIds.append(el.id)
        #     storedSitesIds.append(id(el.sites))
        #
        # return

        n1 = c[0]
        n2 = c[1]
        sf = freezeThaw.StreamFreezer(c, fastButUnsafe=True)
        sf.setupSerializationScaffold()
        for dummy in n1.sites.siteDict:
            pass
            # print(idKey)
            # print(n1.sites.siteDict[idKey]['obj'])
        for dummy in n2.sites.siteDict:
            pass
            # print(idKey)
            # print(n2.sites.siteDict[idKey]['obj'])

        dummy = pickle.dumps(c, protocol=-1)
        # data = sf.writeStr(fmt='pickle')
        # st = freezeThaw.StreamThawer()
        # st.openStr(data)
        # s = st.stream
        # for el in s._elements:
        #    idEl = el.id
        #    if idEl not in storedIds:
        #        print('Could not find ID %d for element %r at offset %f' %
        #              (idEl, el, el.offset))
        # print(storedIds)
        # s.show('t')

    def x_testFreezeThawPickle(self):
        from music21 import freezeThaw
        from music21 import corpus

        c = corpus.parse('luca/gloria')
        # c.show('t')

        sf = freezeThaw.StreamFreezer(c, fastButUnsafe=True)
        d = sf.writeStr()
        # print(d)

        st = freezeThaw.StreamThawer()
        st.openStr(d)
        s = st.stream

        # test to see if we can find everything
        for dummy in s.recurse():
            pass

    def testFreezeThawSimpleVariant(self):
        from music21 import freezeThaw
        from music21 import variant
        from music21 import stream
        from music21 import note

        s = stream.Stream()
        m = stream.Measure()
        m.append(note.Note(type='whole'))
        s.append(m)

        s2 = stream.Stream()
        m2 = stream.Measure()
        n2 = note.Note('D#4')
        n2.duration.type = 'whole'
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
        for pitchName, durType in data2M2:
            n = note.Note(pitchName)
            n.duration.type = durType
            m.append(n)
        stream2.append(m)
        # c.show('t')
        variant.addVariant(c.parts[0], 6.0, stream2,
                           variantName='rhythmic_switch', replacementDuration=3.0)

        # test Variant is in stream
        unused_v1 = c.parts[0].getElementsByClass('Variant')[0]

        sf = freezeThaw.StreamFreezer(c, fastButUnsafe=True)
        # sf.v = v
        d = sf.writeStr()
        # print(d)

        # print('thawing.')

        st = freezeThaw.StreamThawer()
        st.openStr(d)
        s = st.stream
        # s.show('lily.pdf')
        p0 = s.parts[0]
        variants = p0.getElementsByClass('Variant')
        v2 = variants[0]
        self.assertEqual(v2._stream[0][1].offset, 0.5)
        # v2.show('t')

    def testSerializationScaffoldA(self):
        from music21 import note, stream
        from music21 import freezeThaw

        n1 = note.Note()

        s1 = stream.Stream()
        s2 = stream.Stream()

        s1.append(n1)
        s2.append(n1)

        sf = freezeThaw.StreamFreezer(s2, fastButUnsafe=False)
        sf.setupSerializationScaffold()

        # test safety
        self.assertTrue(s2.hasElement(n1))
        self.assertTrue(s1.hasElement(n1))

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
        # print(frozen)
        unused_thawed = converter.thawStr(frozen)

    def testPickleMidi(self):
        from music21 import converter
        a = str(common.getSourceFilePath()
                         / 'midi'
                         / 'testPrimitive'
                         / 'test03.mid')

        # a = 'https://github.com/ELVIS-Project/vis/raw/master/test_corpus/prolationum-sanctus.midi'
        c = converter.parse(a)
        f = converter.freezeStr(c)
        d = converter.thawStr(f)
        self.assertEqual(d[1][20].volume._client.__class__.__name__, 'weakref')


# -----------------------------------------------------------------------------
if __name__ == '__main__':
    import music21
    music21.mainTest(Test)


