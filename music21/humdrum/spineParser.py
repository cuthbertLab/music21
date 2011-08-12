# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         humdrum.spineParser.py
# Purpose:      Conversion and Utility functions for Humdrum and kern in particular
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    (c) 2009-11 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
'''
music21.humdrum.spineParser is a collection of utilities for changing
native humdrum code into music21 streams.  Most music21 users will
simply want to call:


>>> from music21 import *
>>> #_DOCS_SHOW myFile = converter.parse('myfile.krn')
>>> #_DOCS_SHOW myFile.show()


The methods in here are documented for developers wishing to expand
music21's ability to parse humdrum.
'''


import doctest
import unittest
import math
import re
import music21.articulations
import music21.chord
import music21.dynamics

from music21 import duration
from music21 import bar

import music21.key
#import music21.measure
import music21.note
import music21.expressions
import music21.tempo
import music21.tie
import music21.meter
import music21.clef
import music21.stream
from music21 import common
from music21.base import Music21Exception
from music21.humdrum import testFiles, canonicalOutput
from music21.dynamics import Dynamic, Wedge

import os

spinePathIndicators = ["*+", "*-", "*^", "*v", "*x", "*"]

class HumdrumDataCollection(object):
    '''
    A HumdrumDataCollection takes in a mandatory list where each element
    is a line of humdrum data.  Together this list represents a collection 
    of spines.  
    
    
    Usually you will probably want to use HumdrumFile which can read 
    in a file directly.  This class exists in case you have your Humdrum
    data in another format (database, from the web, etc.) and already
    have it as a string.


    You are probably better off running humdrum.parseFile("filename") 
    which returns a humdrum.SpineCollection directly, or even better,
    converter.parse("file.krn") which will just give you a stream.Score
    instead.



    LIMITATION:    
    Spines cannot change definition (\*\*exclusive interpretations) mid-spine.
    
    
    So if you start off with \*\*kern, the rest of the spine needs to be 
    \*\*kern (actually, the first exclusive interpretation for a spine is 
    used throughout)


    Note that, even though changing exclusive interpretations mid-spine
    seems to be legal by the humdrum definition, it looks like none of the
    conventional humdrum parsing tools allow for changing 
    definitions mid-spine, so I don't think this limitation is a problem.
    (Craig Stuart Sapp confirmed this to me)
        
    '''
    parsedLines = False
    
    def __init__(self, dataStream = [] ):
        if dataStream is []:
            raise HumdrumException("dataStream is not optional, specify some lines")
        elif isinstance(dataStream, basestring):
            dataStream = dataStream.splitlines()
        self.dataStream = dataStream
        try:
            self.parseLines(self.dataStream)
        except IOError:
            raise

    def parseLines(self, dataStream = None):
        '''
        Parse a list (dataStream) of lines into a HumdrumSpineCollection
        (which contains HumdrumSpines)
        and set it in self.spineCollection
        
        
        if dataStream is None, look for it in self.dataStream.  If that's None too,
        return an exception.
        
        '''
        if dataStream is None:
            dataStream = self.dataStream
            if dataStream is None:
                raise HumdrumException('Need a list of lines (dataStream) to parse!')
        self.maxSpines = 0

        # parse global comments and figure out the maximum number of spines we will have

        self.parsePositionInStream = 0
        self.parseEventListFromDataStream(dataStream) # sets self.eventList and fileLength
        try:
            assert(self.parsePositionInStream == self.fileLength)
        except AssertionError:
            raise HumdrumException('getEventListFromDataStream failed: did not parse entire file')

        self.parseProtoSpinesAndEventCollections()
        
        self.spineCollection = self.createHumdrumSpines()
        self.spineCollection.reclassSpines()
        self.spineCollection.parseMusic21()
        self.parsedLines = True

    def parseEventListFromDataStream(self, dataStream = None):
        r'''
        Sets self.eventList from a dataStream (that is, a
        list of lines).  It sets self.maxSpines to the
        largest number of spine events found on any line
        in the file.
        
        
        It sets self.fileLength to the number of lines (excluding
        totally blank lines) in the file.
        
        
        The difference between the dataStream and self.eventList
        are the following::
        
            * Blank lines are skipped.
            * !!! lines become :class:`~music21.humdrum.spineParser.GlobalReference` objects
            * !! lines become :class:`~music21.humdrum.spineParser.GlobalComment` objects
            * all other lines become :class:`~music21.humdrum.spineParser.SpineLine` objects
            
        
        Returns eventList in addition to setting it as self.eventList.
        
        
        >>> from music21 import *
        >>> eventString = "!!! COM: Beethoven, Ludwig van\n" + \
        ...               "!! Not really a piece by Beethoven\n" + \
        ...               "**kern\t**dynam\n" + \
        ...               "C4\tpp\n" + \
        ...               "D8\t.\n"
        >>> hdc = music21.humdrum.spineParser.HumdrumDataCollection(eventString)
        >>> eList = hdc.parseEventListFromDataStream()
        >>> eList is hdc.eventList
        True
        >>> for e in eList:
        ...     print e
        <music21.humdrum.spineParser.GlobalReference object at 0x...>
        <music21.humdrum.spineParser.GlobalComment object at 0x...>
        <music21.humdrum.spineParser.SpineLine object at 0x...>
        <music21.humdrum.spineParser.SpineLine object at 0x...>
        <music21.humdrum.spineParser.SpineLine object at 0x...>
        >>> print eList[0].value
        Beethoven, Ludwig van
        >>> print eList[3].spineData
        ['C4', 'pp']
        '''
        if dataStream is None:
            dataStream = self.dataStream
            if dataStream is None:
                raise HumdrumException('Need a list of lines (dataStream) to parse!')
        
        self.parsePositionInStream = 0
        self.eventList = []
        
        for line in dataStream:
            line = line.rstrip()
            if line == "":
                continue # technically forbidden by Humdrum but the source of so many errors!
            elif re.match('\!\!\!', line):
                self.eventList.append(GlobalReference(self.parsePositionInStream, line))
            elif re.match('\!\!', line): ## find global comments at the top of the line
                self.eventList.append(GlobalComment(self.parsePositionInStream, line))
            else:
                thisLine = SpineLine(self.parsePositionInStream, line)
                if thisLine.numSpines > self.maxSpines:
                    self.maxSpines = thisLine.numSpines
                self.eventList.append(thisLine)
            self.parsePositionInStream += 1
        self.fileLength = self.parsePositionInStream 
        return self.eventList

    def parseProtoSpinesAndEventCollections(self):
        r'''
        Run after :meth:`~music21.humdrum.spineParser.HumdrumDataCollection.parseEventListFromDataStream()`
        to take self.eventList and slice it horizontally
        to get self.eventCollections, which is a list of 
        EventCollection objects, or things that happen simultaneously.
        
        
        And, more importantly, this method slices self.eventList 
        vertically to get self.protoSpines which is a list
        of ProtoSpines, that is a vertical slice of everything that
        happens in a column, regardless of spine-path indicators.
        
        
        EventCollection objects store global events at the position.
        ProtoSpines do not.
        
        
        So self.eventCollections and self.protoSpines can each be
        thought of as a two-dimensional sheet of cells, but where
        the first index of the former is the vertical position in
        the dataStream and the first index of the later is the
        horizonal position in the dataStream.  The contents of
        each cell is a SpineEvent object or None (if there's no
        data at that point).  Even '.' (continuation events) get
        translated into SpineEvent objects.

        
        Calls :meth:`~music21.humdrum.spineParser.parseEventListFromDataStream`
        if it hasn't already been called.
        

        returns a tuple of protoSpines and eventCollections in addition to
        setting it in the calling object.
        
                
        >>> from music21 import *
        >>> eventString = "!!! COM: Beethoven, Ludwig van\n" + \
        ...               "!! Not really a piece by Beethoven\n" + \
        ...               "**kern\t**dynam\n" + \
        ...               "C4\tpp\n" + \
        ...               "D8\t.\n"
        >>> hdc = music21.humdrum.spineParser.HumdrumDataCollection(eventString)
        >>> protoSpines, eventCollections = hdc.parseProtoSpinesAndEventCollections()
        >>> protoSpines is hdc.protoSpines
        True
        >>> eventCollections is hdc.eventCollections
        True


        Looking at individual slices is unlikely to tell you much.


        >>> for thisSlice in eventCollections:
        ...    print thisSlice
        <music21.humdrum.spineParser.EventCollection object at 0x...>
        <music21.humdrum.spineParser.EventCollection object at 0x...>
        <music21.humdrum.spineParser.EventCollection object at 0x...>
        <music21.humdrum.spineParser.EventCollection object at 0x...>
        <music21.humdrum.spineParser.EventCollection object at 0x...>

        >>> for thisSlice in protoSpines:
        ...    print thisSlice
        <music21.humdrum.spineParser.ProtoSpine object at 0x...>
        <music21.humdrum.spineParser.ProtoSpine object at 0x...>
       
        
        But looking at the individual slices is revealing:
        
        
        >>> eventCollections[4].getAllOccurring()
        [<music21.humdrum.spineParser.SpineEvent D8>, <music21.humdrum.spineParser.SpineEvent pp>]
    
       
        
        '''
        if self.eventList == []:
            self.parseEventListFromDataStream()
        
        ## we make two lists: one of ProtoSpines (vertical slices) and 
        ##    one of Events(horizontal slices)
        returnProtoSpines = []
        returnEventCollections = []

        for j in range(0, self.maxSpines):
            protoSpineEventList = []
            
            for i in range(0, self.fileLength):
                # get the currentEventCollection
                if j == 0: 
                    thisEventCollection = EventCollection(self.maxSpines)
                    returnEventCollections.append(thisEventCollection)
                else:
                    thisEventCollection = returnEventCollections[i]
                    
                # parse this cell
                if self.eventList[i].isSpineLine is True:
                    # not a global event
                    if len(self.eventList[i].spineData) > j:  
                        ## are there actually this many spines at this point?
                        ## thus, is there an event here? True
                        thisEvent = SpineEvent(self.eventList[i].spineData[j])
                        thisEvent.position = i
                        thisEvent.protoSpineId = j
                        if thisEvent.contents in spinePathIndicators:
                            thisEventCollection.spinePathData = True
                                                
                        protoSpineEventList.append(thisEvent)
                        thisEventCollection.addSpineEvent(j, thisEvent)
                        if thisEvent.contents == '.' and i > 0:
                            lastEvent = returnEventCollections[i-1].events[j]
                            if lastEvent is not None:
                                thisEventCollection.addLastSpineEvent(j, returnEventCollections[i-1].getSpineOccurring(j))

                        
                    else:  ## no data here
                        thisEvent = SpineEvent(None)
                        thisEvent.position = i
                        thisEvent.protoSpineId = j
                        thisEventCollection.addSpineEvent(j, thisEvent)

                        protoSpineEventList.append(None)
                else:  ## Global event
                    if j == 0:
                        thisEventCollection.addGlobalEvent(self.eventList[i])
                    thisEvent = SpineEvent(None)
                    thisEvent.position = i
                    thisEvent.protoSpineId = j
                    thisEventCollection.addSpineEvent(j, thisEvent)
                    protoSpineEventList.append(None)

            returnProtoSpines.append(ProtoSpine(protoSpineEventList))

        self.protoSpines = returnProtoSpines
        self.eventCollections = returnEventCollections
        
        return (returnProtoSpines, returnEventCollections)

    def createHumdrumSpines(self, protoSpines = None, eventCollections = None):
        '''
        Takes the data from the object's protoSpines and eventCollections
        and returns a :class:`~music21.humdrum.spineParser.SpineCollection` 
        object that contains HumdrumSpine() objects.
        
        
        A HumdrumSpine object differs from a ProtoSpine in that it follows
        spinePathData -- a ProtoSpine records all data in a given tab
        position, and thus might consist of data from several
        spines that move around.  HumdrumSpines are smart enough not to
        have this limitation.
        

        When we check for spinePathData we look for the following spine 
        path indicators (from HumdrumDoc)::
            
            
            *+    add a new spine (to the right of the current spine) 
            
            *-    terminate a current spine                           
            
            *^    split a spine (into two)                            
            
            *v    join (two or more) spines into one                  
            
            *x    exchange the position of two spines                 
            
            *     do nothing                                          
        
        
        '''

        
        if protoSpines == None or eventCollections == None:
            protoSpines = self.protoSpines
            eventCollections = self.eventCollections
        maxSpines = len(protoSpines)
        
        # currentSpineList is a list of currently active
        # spines ordered from left to right.
        currentSpineList = common.defList(default = None)
        spineCollection = SpineCollection()

        # go through the event collections line by line        
        for i in range(0, self.fileLength):
            thisEventCollection = eventCollections[i]                    
            for j in range(0, maxSpines):
                thisEvent = protoSpines[j].eventList[i]                 
               
                if thisEvent is not None:  # something there
                    # defList ensures that something will be returned
                    currentSpine = currentSpineList[j]
                    if currentSpine is None: 
                        ## first event after a None = new spine because 
                        ## Humdrum does not require *+ at the beginning
                        currentSpine = spineCollection.addSpine()
                        currentSpine.beginningPosition = i
                        currentSpineList[j] = currentSpine
                    
                    currentSpine.append(thisEvent)
                    # currentSpine.id is always unique in a spineCollection
                    thisEvent.protoSpineId = currentSpine.id

            # check for spinePathData
            # note that nothing else can happen in an eventCollection
            # except spine path data if any spine has spine path data.
            # thus, this is illegal.  The C#4 will be ignored:
            # *x     *x     C#4
            if thisEventCollection.spinePathData is True:
                newSpineList = common.defList()
                mergerActive = False
                exchangeActive = False
                for j in range(0, maxSpines):
                    thisEvent = protoSpines[j].eventList[i]                 
                    currentSpine = currentSpineList[j]
                    if thisEvent is None and currentSpine is not None:
                        ## should this happen?
                        newSpineList.append(currentSpine)
                    elif thisEvent is None:
                        continue
                    elif thisEvent.contents == "*-":  ## terminate spine
                        currentSpine.endingPosition = i
                    elif thisEvent.contents == "*^":  ## split spine assume they are voices
                        newSpine1 = spineCollection.addSpine(streamClass = music21.stream.Voice)
                        newSpine1.beginningPosition = i+1
                        newSpine1.upstream = [currentSpine.id]
                        newSpine2 = spineCollection.addSpine(streamClass = music21.stream.Voice)
                        newSpine2.beginningPosition = i+1
                        newSpine2.upstream = [currentSpine.id]
                        currentSpine.endingPosition = i
                        currentSpine.downstream = [newSpine1.id, newSpine2.id]
                        newSpineList.append(newSpine1)
                        newSpineList.append(newSpine2)
                    elif thisEvent.contents == "*v":  #merge spine -- n.b. we allow non-adjacent lines to be merged. this is incorrect
                        if mergerActive is False:     #               per humdrum syntax, but is easily done.
                            mergeSpine = spineCollection.addSpine()
                            mergeSpine.beginningPosition = i+1
                            mergeSpine.upstream = [currentSpine.id]
                            mergerActive = mergeSpine
                            currentSpine.endingPosition = i
                            currentSpine.downstream = [mergeSpine.id]
                            newSpineList.append(mergeSpine)
                        else:  ## if second merger code is not found then a one-to-one spine "merge" occurs
                            mergeSpine = mergerActive
                            currentSpine.endingPosition = i
                            currentSpine.downstream = [mergeSpine.id]
                            mergeSpine.upstream.append(currentSpine.id)
                    elif thisEvent.contents == "*x":  # exchange spine    
                        if exchangeActive is False:
                            exchangeActive = currentSpine
                        else:  ## if second exchange is not found, then both lines disappear and exception is raised
                               ## n.b. we allow more than one PAIR of exchanges in a line so long as the first
                               ## is totally finished by the time the second happens
                            newSpineList.append(currentSpine)
                            newSpineList.append(exchangeActive)
                            exchangeActive = False;
                    else:  ## null processing code "*" 
                        newSpineList.append(currentSpine)
                        
                if exchangeActive is not False:
                    raise HumdrumException("ProtoSpine found with unpaired exchange instruction at line %d [%s]" % (i, thisEventCollection.events))
                currentSpineList = newSpineList
        return spineCollection

    def _getStream(self):
        if self.parsedLines is False:
            self.parseLines()

        if self.spineCollection is None:
            raise HumdrumException("parsing got no spine collections!")
        elif self.spineCollection.spines is None:
            raise HumdrumException("really? not a single spine in your data? um, not my problem! (well, maybe it is...file a bug report if you have doubled checked your data)")
        elif self.spineCollection.spines[0].stream is None:
            raise HumdrumException("okay, you got at least one spine, but it aint got a stream in it; have you thought of taking up kindergarten teaching? (just kidding, check your data or file a bug report)")

        else:
            masterStream = music21.stream.Score()
            for thisSpine in self.spineCollection:
                thisSpine.stream.id = "spine_" + str(thisSpine.id)
                masterStream.insert(thisSpine.stream)
            return masterStream

    stream = property(_getStream)

class HumdrumFile(HumdrumDataCollection):
    '''
    A HumdrumFile is a HumdrumDataCollection which takes 
    as a mandatory argument a filename to be opened and read.
    '''
    
    
    def __init__(self, filename = None):
        if (filename is not None):
            try:
                humFH = open(filename)
                self.eventList = self.parseFH(humFH)
            except IOError:          
                raise

    def parseFH(self, fileHandle):
        '''
        parseFH takes a fileHandle and returns a HumdrumCollection
        '''

        spineDataCollection = []
        for line in fileHandle:
            spineDataCollection.append(line)
        return self.parseLines(spineDataCollection)

class HumdrumLine(object):    
    '''
    HumdrumLine is a dummy class for subclassing 
    :class:`~music21.humdrum.spineParser.SpineLine`, 
    :class:`~music21.humdrum.spineParser.GlobalComment`, and 
    :class:`~music21.humdrum.spineParser.GlobalReference` classes
    all of which represent one horizontal line of 
    text in a :class:`~music21.humdrum.spineParser.HumdrumDataCollection` 
    that is aware of its 
    position in the file.
    
    
    See the documentation for the specific classes mentioned above
    for more details.
    '''
    isReference = False
    isGlobal = False
    isComment = False
    position = 0

class SpineLine(HumdrumLine):
    r'''
    A SpineLine is any horizontal line of a Humdrum file that 
    contains one or more spine elements (separated by tabs)
    and not Global elements.
    
    
    Takes in a position (line number in file, excluding blank lines) 
    and a string of contents.
    
    
    >>> from music21 import *
    >>> hsl = music21.humdrum.spineParser.SpineLine(
    ...         position = 7, contents="C4\t!local comment\t*M[4/4]\t.\n")
    >>> hsl.position
    7
    >>> hsl.numSpines
    4
    >>> hsl.spineData
    ['C4', '!local comment', '*M[4/4]', '.']
    
    '''
    position = 0
    contents = ""
    isSpineLine = True
    numSpines = 0
    
    def __init__(self, position = 0, contents = ""):
        self.position = position
        contents = contents.rstrip()
        returnList = re.split("\t+", contents)
        self.numSpines = len(returnList)
        self.contents = contents
        self.spineData = returnList

class GlobalReference(HumdrumLine):
    r'''
    A GlobalReference is a type of HumdrumLine that contains 
    information about the humdrum document.
    
    
    In humdrum it is represented by three exclamation points 
    followed by non-whitespace followed by a colon.  Examples::
    
    
        !!!COM: Stravinsky, Igor Fyodorovich

        !!!CDT: 1882/6/17/-1971/4/6

        !!!ODT: 1911//-1913//; 1947//

        !!!OPT@@RUS: Vesna svyashchennaya

        !!!OPT@FRE: Le sacre du printemps


    The GlobalReference object takes two inputs::


        position (line number in the humdrum file)
        
        contents (string of contents)


    And stores them as three attributes::


        position (as above)
        
        code: non-whitespace code (usually three letters)
        
        contents (string of contents)


    >>> from music21 import *
    >>> gr = music21.humdrum.spineParser.GlobalReference(
    ...        position = 20, contents = "!!!COM: Stravinsky, Igor Fyodorovich\n")
    >>> gr.position
    20
    >>> gr.code
    'COM'
    >>> gr.value
    'Stravinsky, Igor Fyodorovich'
    
    
    TODO: add parsing of three-digit Kern comment codes into fuller metadata
    '''
    position = 0
    contents = ""
    isGlobal = True
    isReference = True
    isComment = True
    isSpineLine = False
    numSpines = 0

    def __init__(self, position = 0, contents = "!!! NUL: None"):
        self.position = position
        noExclaim = re.sub('^\!\!\!+','',contents)
        try:
            (code, value) = noExclaim.split(":", 1)
            value = value.strip()
            if (code is None):
                raise HumdrumException("GlobalReference (!!!) found without a code listed; this is probably a problem! %s " % contents)
        except IndexError:
            raise HumdrumException("GlobalReference (!!!) found without a code listed; this is probably a problem! %s " % contents)

        self.contents = contents
        self.code = code
        self.value = value
    
class GlobalComment(HumdrumLine):
    '''
    A GlobalComment is a humdrum comment that pertains to all spines
    In humdrum it is represented by two exclamation points (and usually one space)
    
    
    The GlobalComment object takes two inputs and stores them as attributes::
    
    
        position (line number in the humdrum file)
        contents (string of contents)
        value    (contents minus !!)


    The constructor can be passed (position, contents)
    if contents begins with bangs, they are removed along with up to one space directly afterwards


    >>> from music21 import *
    >>> com1 = music21.humdrum.spineParser.GlobalComment(
    ...          position = 4, contents='!! this comment is global')
    >>> com1.position
    4
    >>> com1.contents
    '!! this comment is global'
    >>> com1.value
    'this comment is global'

    '''
    position = 0
    contents = ""
    value    = ""
    isGlobal = True
    isComment = True
    isSpineLine = False
    numSpines = 0

    def __init__(self, position = 0, contents = ""):
        self.position = position
        value = re.sub('^\!\!+\s?','',contents)
        self.contents = contents
        self.value    = value

class ProtoSpine(object):
    '''
    A ProtoSpine is a collection of events arranged vertically.  
    It differs from a HumdrumSpine in that spine paths are not followed.  
    So ProtoSpine(1) would be everything in the 2nd column
    of a Humdrum file regardless of whether the 2nd column 
    was at some point an independent Spine
    or if it later became a split from the first spine.
    

    See :meth:`~music21.humdrum.spineParser.parseProtoSpinesAndEventCollections`
    for more details on how ProtoSpine objects are created.
    '''
    def __init__(self, eventList = None):
        if eventList is None:
            eventList = []
        self.eventList = eventList

class HumdrumSpine(object):
    '''
    A HumdrumSpine is a representation of a generic HumdrumSpine
    regardless of \*\*definition after spine path indicators have
    been simplified. 
    
    
    A HumdrumSpine is a collection of events arranged vertically that have a
    connection to each other.
    Each HumdrumSpine MUST have an id (numeric or string) attached to it.


    >>> from music21 import *
    >>> SE = music21.humdrum.spineParser.SpineEvent
    >>> spineEvents = [SE('**kern'),SE('c,4'), SE('d#8')]
    >>> spine1Id = 5
    >>> spine1 = music21.humdrum.spineParser.HumdrumSpine(spine1Id, spineEvents)
    >>> spine1.beginningPosition = 5
    >>> spine1.endingPosition = 6
    >>> spine1.upstream = [3]  # spine 3 is the previous spine leading to this one
    >>> spine1.downstream = [7,8] # the spine ends by being split into spines 7 and 8


    we keep weak references to the spineCollection so that we 
    don't have circular references


    >>> spineCollection1 = music21.humdrum.spineParser.SpineCollection()
    >>> spine1.spineCollection = spineCollection1


    The spineType property searches the EventList or upstreamSpines to 
    figure out the spineType

           
    >>> spine1.spineType
    'kern'
    
    
    Spines can be iterated through:
    
    
    >>> for e in spine1:
    ...    print e
    **kern
    c,4
    d#8
    
    
    If you'd eventually like this spine to be converted to a class
    other than :class:`~music21.stream.Stream`, pass its classname in
    as the streamClass argument:
    
    
    >>> spine2 = music21.humdrum.spineParser.HumdrumSpine(
    ...              streamClass = music21.stream.Part)
    >>> spine2.stream
    <music21.stream.Part ...>
    
    '''
    def __init__(self, id=0, eventList = None, streamClass = music21.stream.Stream):
        self.id = id
        if eventList is None:
            eventList = []
        for event in eventList:
            event.spineId = id
        
        self.eventList = eventList
        self.stream = streamClass()
        self.beginningPosition = 0
        self.endingPosition = 0
        self.upstream = []
        self.downstream = []

        self._spineCollection = None
        self._spineType = None

    def __repr__(self):
        return str(self.id) + repr(self.upstream) + repr(self.downstream)

    def append(self, event):
        '''
        add an item to this Spine
        '''
        self.eventList.append(event)

    def __iter__(self):
        '''Resets the counter to 0 so that iteration is correct'''
        self.iterIndex = 0
        return self

    def next(self):
        '''Returns the current event and increments the iteration index.'''
        if self.iterIndex == len(self.eventList):
            raise StopIteration
        thisEvent = self.eventList[self.iterIndex]
        self.iterIndex += 1
        return thisEvent

    def _getSpineCollection(self):
        return common.unwrapWeakref(self._spineCollection)

    def _setSpineCollection(self, sc = None):
        self._spineCollection = common.wrapWeakref(sc)
    
    spineCollection = property(_getSpineCollection, _setSpineCollection)

    def upstreamSpines(self):
        '''
        Returns a list of HumdrumSpine(s) that are upstream from
        this spine.
        (only works if if the spineCollection is set)
        
        
        Otherwise returns an empty list
        '''
        if self.upstream:
            sc1 = self.spineCollection
            if sc1:
                spineReturn = []
                for upstreamId in self.upstream:
                    spineReturn.append(sc1.getSpineById(upstreamId))
                return spineReturn
            else:
                return []
        else:
            return []

    def downstreamSpines(self):
        '''
        Returns the HumdrumSpine(s) that are downstream (if the 
        spineCollection is set)
        '''
        if self.downstream:
            sc1 = self.spineCollection
            if sc1:
                spineReturn = []
                for downstreamId in self.downstream:
                    spineReturn.append(sc1.getSpineById(downstreamId))
                return spineReturn
            else:
                return []
        else:
            return []

    def _getLocalSpineType(self):
        if self._spineType is not None:
            return self._spineType
        else:
            for thisEvent in self.eventList:
                m1 = re.match("\*\*(.*)", thisEvent.contents)
                if m1:
                    self._spineType = m1.group(1)
                    return self._spineType
            return None
    
    def _getUpstreamSpineType(self):
        pS = self.upstreamSpines()
        if pS:
            ## leftFirst, DepthFirst search
            for thisPS in pS:
                psSpineType = thisPS.spineType
                if psSpineType is not None:
                    return psSpineType
            return None
        else:
            return None
            

    def _getSpineType(self):
        if self._spineType is not None:
            return self._spineType
        else:
            st = self._getLocalSpineType()
            if st is not None:
                self._spineType = st
                return st
            else:
                st = self._getUpstreamSpineType()
                if st is not None:
                    self._spineType = st
                    return st
                else:
                    raise HumdrumException("Could not determine spineType " + 
                                           "for spine with id " + str(self.id))
    
    def _setSpineType(self, newSpineType = None):
        self._spineType = newSpineType
    
    spineType = property(_getSpineType, _setSpineType)

    def parse(self):
        '''
        Dummy method that pushes all these objects to HumdrumSpine.stream
        as ElementWrappers.  Should be overridden in
        specific Spine subclasses.
        '''
        for event in self.eventList:
            eventC = str(event.contents)
            if eventC == ".":
                pass
            else:
                self.stream.append(music21.base.ElementWrapper(event))

class KernSpine(HumdrumSpine):
    '''
    A KernSpine is a type of humdrum spine with the \*\*kern
    attribute set and thus events are processed as if they
    are kern notes
    '''
    def parse(self):
        thisContainer = None # hdStringToMeasure('=0')
        inTuplet = False
        lastNote = None
        
        for event in self.eventList:
            eventC = str(event.contents)  # is str already; just for Eclipse completion
            thisObject = None            
            if eventC == ".":
                pass
            elif eventC.startswith('*'):
                ## control processing
                tempObject = kernTandamToObject(eventC)
                if tempObject is not None:
                    thisObject = tempObject
            elif eventC.startswith('='):
                ## barline/measure processing
                oldContainer = thisContainer
                thisContainer = hdStringToMeasure(eventC)
                if oldContainer is not None:
                    self.stream.append(oldContainer)
                    
                    # deal with pickups
                    if "Measure" in oldContainer.classes and oldContainer.number is None:
                        oldContainer.number = thisContainer.number - 1
            elif eventC.startswith('!'):
                ## TODO: process comments
                pass
            elif eventC.count(' '):
                ### multipleNotes
                notesToProcess = eventC.split()
                chordNotes = []
                for noteToProcess in notesToProcess:
                    chordNotes.append(hdStringToNote(noteToProcess))
                thisObject = music21.chord.Chord(chordNotes)
                thisObject.duration = chordNotes[0].duration

                if inTuplet is False and len(thisObject.duration.tuplets) > 0:
                    inTuplet = True
                    thisObject.duration.tuplets[0].type = 'start'
                elif inTuplet is True and len(thisObject.duration.tuplets) == 0:
                    inTuplet = False
                    lastNote.duration.tuplets[0].type = 'stop'
                lastNote = thisObject

            else:
                thisObject = hdStringToNote(eventC)
                if inTuplet is False and len(thisObject.duration.tuplets) > 0:
                    inTuplet = True
                    thisObject.duration.tuplets[0].type = 'start'
                elif inTuplet is True and len(thisObject.duration.tuplets) == 0:
                    inTuplet = False
                    lastNote.duration.tuplets[0].type = 'stop'
                lastNote = thisObject
            
            if thisObject is not None:
                thisObject.humdrumPosition = event.position
                thisObject.humdrumSpineId  = event.spineId                
                if thisContainer is None:
                    self.stream.append(thisObject)
                else:
                    thisContainer.append(thisObject)

        ## move things before first measure to first measure!

class DynamSpine(HumdrumSpine):
    '''
    A DynamSpine is a type of humdrum spine with the \*\*dynam
    attribute set and thus events are processed as if they
    are dynamics.
    '''
    def parse(self):
        thisContainer = None
        for event in self.eventList:
            eventC = str(event.contents)  # is str already; just so Eclipse gives the right tools
            thisObject = None
            if eventC == ".":
                pass
            elif eventC.startswith('*'):
                ## control processing
                if eventC not in spinePathIndicators:
                    thisObject = MiscTandam(eventC)
            elif eventC.startswith('='):
                if thisContainer is not None:
                    self.stream.append(thisContainer)
                thisContainer = hdStringToMeasure(eventC)                
            elif eventC.startswith('!'):
                ## TODO: process comments
                pass
            elif eventC.startswith('<'):
                thisObject = Wedge()
                thisObject.type = 'diminuendo'
            elif eventC.startswith('>'):
                thisObject = Wedge()
                thisObject.type = 'crescendo'
            else:
                thisObject = Dynamic(eventC)
            
            if thisObject is not None:
                thisObject.humdrumPosition = event.position
                thisObject.humdrumSpineId  = event.spineId                
                if thisContainer is None:
                    self.stream.append(thisObject)
                else:
                    thisContainer.append(thisObject)


        
class SpineEvent(object):
    '''
    A SpineEvent is an event in a HumdrumSpine or ProtoSpine.


    It's .contents property contains the contents of the spine or 
    it could be '.', in which case it means that a 
    particular event appears after the last event in a different spine.
    It could also be "None" indicating that there is no event at all
    at this moment in the humdrum file.  Happens if no ProtoSpine exists
    at this point in the file in this tab position.



    Should be initialized with its contents and position in file.
    
    

    These attributes are optional but likely to be very helpful::
    
        position -- event position in the file
        protoSpineId -- ProtoSpine id (0 to N)
        spineId -- id of HumdrumSpine actually attached to (after SpinePaths are parsed)


    The `toNote()` method converts the contents into a music21 note as
    if it's kern -- useful to have in all spine types.
    
    
    >>> from music21 import *
    >>> se1 = music21.humdrum.spineParser.SpineEvent('EEE-8')
    >>> se1.position = 40
    >>> se1.contents
    'EEE-8'
    >>> se1
    <music21.humdrum.spineParser.SpineEvent EEE-8>
    >>> n = se1.toNote()
    >>> n
    <music21.note.Note E->

    '''
    protoSpineId = 0
    spineId = None
    
    def __init__(self, contents = None, position = 0):
        self.contents = contents
        self.position = position

    def __repr__(self):
        return "<music21.humdrum.spineParser.SpineEvent %s>" % self.contents

    def __str__(self):
        return self.contents

    def toNote(self):
        '''
        parse the object as a \*\*kern note and return the a
        :class:`~music21.note.Note` object (or Rest, or Chord)
        
        
        >>> from music21 import *
        >>> se = music21.humdrum.spineParser.SpineEvent('CC#4')
        >>> n = se.toNote()
        >>> n
        <music21.note.Note C#>
        >>> n.octave
        2
        >>> n.duration.type
        'quarter'
        '''
        
        return hdStringToNote(self.contents)        

class SpineCollection(object):
    '''
    A SpineCollection is a set of Spines with relationships to each 
    other and where their position attributes indicate
    simultaneous onsets.
    '''

    def __init__(self): 
        self.spines = []
        self.nextFreeId  = 0
        self.spineReclassDone = False
        
    def __iter__(self):
        '''Resets the counter to 0 so that iteration is correct'''
        self.iterIndex = 0
        return self

    def next(self):
        '''Returns the current spine and increments the iteration index.'''
        if self.iterIndex == len(self.spines):
            raise StopIteration
        thisSpine = self.spines[self.iterIndex]
        self.iterIndex += 1
        return thisSpine
        
    def addSpine(self, streamClass = music21.stream.Part):
        '''
        creates a new spine in the collection and returns it.
        
        
        By default, the underlying music21 class of the spine is
        :class:`~music21.stream.Part`.  This can be overridden
        by passing in a different streamClass.
        
        
        Automatically sets the id of the Spine.
        
        
        >>> from music21 import *
        >>> hsc = music21.humdrum.spineParser.SpineCollection()
        >>> newSpine = hsc.addSpine()
        >>> newSpine.id
        0
        >>> newSpine.stream
        <music21.stream.Part ...>
        >>> newSpine2 = hsc.addSpine(streamClass = music21.stream.Stream)
        >>> newSpine2.id
        1
        >>> newSpine2
        1[][]
        >>> newSpine2.stream
        <music21.stream.Stream ...>
        
        
        '''
        
        self.newSpine = HumdrumSpine(self.nextFreeId, streamClass = streamClass)
        self.newSpine.spineCollection = self
        self.spines.append(self.newSpine)
        self.nextFreeId += 1
        return self.newSpine
    
    def appendSpine(self, spine):
        '''
        appendSpine(spine) -- appends an already existing HumdrumSpine 
        to the SpineCollection.  Returns void
        '''
        self.spines.append(spine)
        
    def getSpineById(self, id):
        '''
        returns the HumdrumSpine with the given id.
        
        raises a HumdrumException if the spine with a given id is not found
        '''
        for thisSpine in self.spines:
            if thisSpine.id == id:
                return thisSpine
        raise HumdrumException("Could not find a Spine with that ID")


    def reclassSpines(self):
        '''
        changes the classes of HumdrumSpines to more specific types 
        (KernSpine, DynamicSpine)
        according to their spineType (**kern, **dynam)
        '''                     
        for thisSpine in self.spines:
            if thisSpine.spineType == "kern":
                thisSpine.__class__ = KernSpine
            elif thisSpine.spineType == "dynam":
                thisSpine.__class__ = DynamSpine
        self.spineReclassDone = True

    def parseMusic21(self):
        '''
        runs spine.parse() for each Spine.  
        thus populating the spine.stream for each Spine
        '''
        for thisSpine in self.spines:
            thisSpine.parse()

     
    # TODO: append global comments and have a way of recalling them

class EventCollection(object):
    '''
    An EventCollection is a time slice of all events that have 
    an onset of a certain time.  If an event does not occur at 
    a certain time, then you should check EventCollection[n].lastEvents 
    to get the previous event.  (If it is a note, it is the note 
    still sounding, etc.).  The happeningEvent method gets either 
    currentEvent or lastEvent.


    These objects normally get created by 
    :meth:`~music21.humdrum.spineParser.HumdrumDataCollection.parseProtoSpinesAndEventCollections`
    so you won't need to do all the setup.


    Assume that ec1 is
         C4     pp
         
    and ec2 is:
         D4     .
         


    >>> from music21 import *
    >>> SE = humdrum.spineParser.SpineEvent
    >>> eventList1 = [SE('C4'),SE('pp')]
    >>> eventList2 = [SE('D4'),SE('.')]
    >>> ec1 = humdrum.spineParser.EventCollection(maxSpines = 2)
    >>> ec1.events = eventList1
    >>> ec2 = humdrum.spineParser.EventCollection(maxSpines = 2)
    >>> ec2.events = eventList2
    >>> ec2.lastEvents[1] = eventList1[1]
    >>> ec2.maxSpines
    2
    >>> ec2.getAllOccurring()
    [<music21.humdrum.spineParser.SpineEvent D4>, <music21.humdrum.spineParser.SpineEvent pp>]
    

    '''
    def __init__(self, maxSpines = 0):
        self.events = common.defList()
        self.lastEvents = common.defList()
        self.maxSpines = maxSpines
        self.spinePathData = False  
               ## true if the line contains data about changing spinePaths

    def addSpineEvent(self, spineNum, spineEvent):
        self.events[spineNum] = spineEvent
        
    def addLastSpineEvent(self, spineNum, spineEvent): 
        ## should only add if current "event" is "." or a comment
        self.lastEvents[spineNum] = spineEvent
        
    def addGlobalEvent(self, globalEvent):
        for i in range(0, self.maxSpines):
            self.events[i] = globalEvent

    def getSpineEvent(self, spineNum):
        return self.events[spineNum]
    
    def getSpineOccurring(self, spineNum):  
        ## returns the lastEvent if set (
        ## should only happen if currentEvent is ".")
        ## or the current event
        if self.lastEvents[spineNum] is not None:
            return self.lastEvents[spineNum]
        else:
            return self.events[spineNum]

    def getAllOccurring(self):
        retEvents = []
        for i in range(0, self.maxSpines):
            retEvents.append(self.getSpineOccurring(i))
        return retEvents
        
class HumdrumException(Music21Exception):
    '''
    General Exception class for problems relating to Humdrum
    '''
    pass

def hdStringToNote(contents):
    '''
    returns a music21.note.Note (or Rest or Unpitched, etc.) 
    matching the current SpineEvent.
    Does not check to see that it is sane or part of a \*\*kern spine, etc.
    '''
    
    # http://www.lib.virginia.edu/artsandmedia/dmmc/Music/Humdrum/kern_hlp.html#kern
    
    # 3.2.1 -- pitch
    
    matchedNote = re.search("([a-gA-G]+)", contents)

    thisObject = None
    if matchedNote:
        thisObject = music21.note.Note()
        kernNoteName = matchedNote.group(1)
        step = kernNoteName[0].lower()
        thisObject.step = step
        if (step == kernNoteName[0]): ## middle C or higher
            octave = 3 + len(kernNoteName)
        else: # below middle C
            octave = 4 - len(kernNoteName)
        thisObject.octave = octave

    # 3.3 -- Rests
    elif contents.count("r"):
        thisObject = music21.note.Rest()
    else:
        raise HumdrumException("Could not parse %s for note information" % contents)

    matchedSharp = re.search("(\#+)", contents)
    matchedFlat  = re.search("(\-+)", contents)
    
    if matchedSharp:
        thisObject.accidental = matchedSharp.group(0)
    elif matchedFlat:
        thisObject.accidental = matchedFlat.group(0)
    elif contents.count("n"):
        thisObject.accidental = "n"
    
    # 3.2.2 -- Slurs, Ties, Phrases
    # TODO: add music21 phrase information
    if contents.count('{'):
        for i in range(0, contents.count('{')):
            pass # phraseMark start
    if contents.count('}'):
        for i in range(0, contents.count('}')):
            pass # phraseMark end
    if contents.count('('):
        for i in range(0, contents.count('(')):
            pass # slur start
    if contents.count(')'):
        for i in range(0, contents.count(')')):
            pass # slur end
    if contents.count('['):
        thisObject.tie = music21.tie.Tie("start")
    elif contents.count(']'):
        thisObject.tie = music21.tie.Tie("stop")
    elif contents.count('_'):
        thisObject.tie = music21.tie.Tie("continue")
    
    ## 3.2.3 Ornaments    
    if contents.count('t'):
        thisObject.expressions.append(music21.expressions.HalfStepTrill())
    elif contents.count('T'):
        thisObject.expressions.append(music21.expressions.WholeStepTrill())
    
    if contents.count('w'):
        thisObject.expressions.append(music21.expressions.HalfStepInvertedMordent())
    elif contents.count('W'):
        thisObject.expressions.append(music21.expressions.WholeStepInvertedMordent())
    elif contents.count('m'):
        thisObject.expressions.append(music21.expressions.HalfStepMordent())
    elif contents.count('M'):
        thisObject.expressions.append(music21.expressions.WholeStepMordent())

    if contents.count('S'):
        thisObject.expressions.append(music21.expressions.Turn())
    elif contents.count('$'):
        thisObject.expressions.append(music21.expressions.InvertedTurn())
    elif contents.count('R'):
        t1 = music21.expressions.Turn()
        t1.connectedToPrevious = True  ## true by default, but explicitly
        thisObject.expressions.append(t1)
    
    if contents.count(':'):
        ## TODO: deal with arpeggiation -- should have been in a 
        ##  chord structure
        pass
    
    if contents.count("O"):
        thisObject.expressions.append(music21.expressions.Ornament())  
        # generic ornament
    
    # 3.2.4 Articulation Marks
    if contents.count('\''):
        thisObject.articulations.append(music21.articulations.Staccato())
    if contents.count('"'):
        thisObject.articulations.append(music21.articulations.Pizzicato())
    if contents.count('`'):
        ### HMMMMM? WHAT DOES THIS MEAN?  Can't find it anywhere.
        raise HumdrumException("Attacca mark found -- what is that?  I cannot find any references to attacca marks anywhere on the web or reference books!")
    if contents.count('~'):
        thisObject.articulations.append(music21.articulations.Tenuto())
    if contents.count('^'):
        thisObject.articulations.append(music21.articulations.Accent())
    
    # 3.2.5 Up & Down Bows
    if contents.count('v'):
        thisObject.articulations.append(music21.articulations.UpBow())
    elif contents.count('u'):
        thisObject.articulations.append(music21.articulations.DownBow())
    
    # 3.2.6 Stem Directions
    if contents.count('/'):
        thisObject.stemDirection = "up"
    elif contents.count('\\'):
        thisObject.stemDirection = "down"        
    
    # 3.2.7 Duration +
    # 3.2.8 N-Tuplets
    foundNumber = re.search("(\d+)", contents)
    if foundNumber:
        durationType = int(foundNumber.group(1))
        if durationType == 0:
            thisObject.duration.type = 'breve'
            if contents.count('.'):
                thisObject.duration.dots = contents.count('.')
        elif durationType in duration.typeFromNumDict:
            thisObject.duration.type = duration.typeFromNumDict[durationType]
            if contents.count('.'):
                thisObject.duration.dots = contents.count('.')
        else:
            dT = int(durationType) + 0.0
            (remainder, exponents) = math.modf(math.log(dT, 2))
            basevalue = 2**exponents
            thisObject.duration.type = duration.typeFromNumDict[int(basevalue)]
            newTup = duration.Tuplet()
            newTup.durationActual.type = thisObject.duration.type
            newTup.durationNormal.type = thisObject.duration.type

            gcd = common.euclidGCD(int(dT), basevalue)
            newTup.numberNotesActual = dT/gcd
            newTup.numberNotesNormal = float(basevalue)/gcd
            
            if contents.count('.'):
                newTup.durationNormal.dots = contents.count('.')
            
            thisObject.duration.appendTuplet(newTup)
                    
    # 3.2.9 Grace Notes and Groupettos
    # TODO: Rewrite after music21 gracenotes are implemented
    if contents.count('q'):
        thisObject.duration.__class__ = music21.duration.GraceDuration
    elif contents.count('Q'):
        thisObject.duration.__class__ = music21.duration.LongGraceDuration
    elif contents.count('P'):
        thisObject.duration.__class__ = music21.duration.AppogiaturaStartDuration
    elif  contents.count('p'):
        thisObject.duration.__class__ = music21.duration.AppogiaturaStopDuration
    
    # 3.2.10 Beaming
    # TODO: Support really complex beams
    for i in range(0, contents.count('L')):
        thisObject.beams.append('start')
    for i in range(0, contents.count('J')):
        thisObject.beams.append('stop')
    for i in range(0, contents.count('k')):
        thisObject.beams.append('partial', 'right')
    for i in range(0, contents.count('K')):
        thisObject.beams.append('partial', 'right')
    
    return thisObject

def hdStringToMeasure(contents):
    '''
    kern uses an equals sign followed by processing instructions to
    create new measures.  Here is how...
    '''
    m1 = music21.stream.Measure()
    rematchMN = re.search("(\d+)([a-z]?)", contents)

    #m1.setrightBarline()
    barline = bar.Barline()
    m1.rightBarline = barline
        
    
    if rematchMN:
        m1.number = int(rematchMN.group(1))
        if rematchMN.group(2):
            m1.numberSuffix = rematchMN.group(2)

    if contents.count('-'):
        m1.rightBarline.style = "none"
    elif contents.count('\''):
        m1.rightBarline.style = "short"
    elif contents.count('`'):
        m1.rightBarline.style = "tick"
    elif contents.count('||'):
        m1.rightBarline.style = "light-light"
        if contents.count(':') > 1:
            m1.rightBarline.repeat_dots = "both"
        elif contents.count(':|'):
            m1.rightBarline.repeat_dots = "left"
        elif contents.count('|:'):
            m1.rightBarline.repeat_dots = "right"
    elif contents.count('!!'):
        m1.rightBarline.style = "heavy-heavy"
        if contents.count(':') > 1:
            m1.rightBarline.repeat_dots = "both"
        elif contents.count(':!'):
            m1.rightBarline.repeat_dots = "left"
        elif contents.count('!:'):
            m1.rightBarline.repeat_dots = "right"
    elif contents.count('|!'):
        m1.rightBarline.style = "light-heavy"
        if contents.count(':') > 1:
            m1.rightBarline.repeat_dots = "both"
        elif contents.count(':|'):
            m1.rightBarline.repeat_dots = "left"
        elif contents.count('!:'):
            m1.rightBarline.repeat_dots = "right"
    elif contents.count('!|'):
        m1.rightBarline.style = "heavy-light"
        if contents.count(':') > 1:
            m1.rightBarline.repeat_dots = "both"
        elif contents.count(':!'):
            m1.rightBarline.repeat_dots = "left"
        elif contents.count('|:'):
            m1.rightBarline.repeat_dots = "right"
    elif contents.count('|'):
        m1.rightBarline.style = "regular"
        if contents.count(':') > 1:
            m1.rightBarline.repeat_dots = "both"
        elif contents.count(':|'):
            m1.rightBarline.repeat_dots = "left"
        elif contents.count('|:'):
            m1.rightBarline.repeat_dots = "right"
    elif contents.count('=='):
        m1.rightBarline.style = "light-light"
        if contents.count(':') > 1:
            m1.rightBarline.repeat_dots = "both"
            ## cannot specify single repeat dots without styles
        if contents == "==|":
            raise HumdrumException \
                ("Cannot import a double bar visually rendered as a single bar -- not sure exactly what that would mean anyhow.")
    
    if contents.count(';'):
        m1.rightBarline.pause = music21.expressions.Fermata()

    return m1


def kernTandamToObject(tandam):
    '''
    kern uses *M5/4  *clefG2 etc, to control processing
    
    
    >>> from music21 import *
    >>> m = humdrum.spineParser.kernTandamToObject('*M3/1')
    >>> m
    <music21.meter.TimeSignature 3/1>
    '''
    # TODO: Cover more tandam controls as they're found
    if tandam in spinePathIndicators:
        return None
    elif tandam.startswith("*clef"):
        clefType = tandam[5:]
        if clefType == "-":
            return music21.clef.NoClef()
        elif clefType == "X":
            return music21.clef.PercussionClef()
        elif clefType == "Gv2": # undocumented in Humdrum, but appears in Huron's Chorales
            return music21.clef.Treble8vbClef()
        elif clefType == "G^2": # unknown if ever used but better safe...
            return music21.clef.Treble8vaClef()
        elif clefType == "Fv4": # unknown if ever used but better safe...
            return music21.clef.Bass8vbClef()
        else:
            try:
                clefifier = music21.clef.standardClefFromXN(clefType)
                return clefifier
            except music21.clef.ClefException:
                raise HumdrumException("Unknown clef type %s found", tandam)
    elif tandam.startswith("*MM"):
        metronomeMark = tandam[3:]
        try:
            metronomeMark = float(metronomeMark)
            MM = music21.tempo.MetronomeMark(number=metronomeMark)    
            return MM
        except ValueError:
            # assuming that metronomeMark here is text now 
            metronomeMark = re.sub('^\[','', metronomeMark)
            metronomeMark = re.sub(']\s*$','', metronomeMark)
            MS = music21.tempo.MetronomeMark(text=metronomeMark)
            return MS
    elif tandam.startswith("*M"):
        meterType = tandam[2:]
        return music21.meter.TimeSignature(meterType)
    elif tandam.startswith("*IC"):
        instrumentClass = tandam[3:]
        # TODO: DO SOMETHING WITH INSTRUMENT CLASS; not in hum2xml
    elif tandam.startswith("*IG"):
        instrumentGroup = tandam[3:]
        # TODO: DO SOMETHING WITH INSTRUMENT GROUP; not in hum2xml
    elif tandam.startswith("*ITr"):
        instrumentTransposing = True
        # TODO: DO SOMETHING WITH TRANSPOSING INSTRUMENTS; not in hum2xml
    elif tandam.startswith("*I"):
        instrument = tandam[2:]
        # TODO: SOMETHING WITH INSTRUMENTS; not in hum2xml
    elif tandam.startswith("*k"):
        numSharps = tandam.count('#')
        if numSharps == 0:
            numSharps = -1 * (tandam.count('-'))
        return music21.key.KeySignature(numSharps)
    elif tandam.endswith(":"):
        thisKey = tandam[1:-1]
        # does not work yet
        return music21.key.keyFromString(thisKey)
    else:
        return MiscTandam(tandam)

#    elif tandam.startswith("*>"):
#        # TODO: Something with 4.2 Repetitions; not in hum2xml
#        pass
#    elif tandam.startswith("*tb"):
#        timeBase = tandam[4:]
#        # TODO: Findout what timeBase means; not in hum2xml
#        pass
#    elif tandam.startswith("*staff"):
#        staffNumbers = tandam[6:]
#        # TODO: make staff numbers relevant; not in hum2xml

# TODO: Parse editorial signifiers


class MiscTandam(music21.Music21Object):
    def __init__(self, tandam = ""):
        music21.Music21Object.__init__(self)
        self.tandam = tandam
    def __repr__(self):
        return "<music21.humdrum.MiscTandam %s humdrum control>" % self.tandam
           
class Test(unittest.TestCase):

    def runTest(self):
        pass
     
    def testLoadMazurka(self):    
        #hf1 = HumdrumFile("d:/web/eclipse/music21misc/mazurka06-2.krn")    

        hf1 = HumdrumDataCollection(testFiles.mazurka6)
        
    #    hf1 = HumdrumFile("d:/web/eclipse/music21misc/ojibway.krn")    
    #    for thisEventCollection in hf1.eventCollections:
    #        ev = thisEventCollection.getSpineEvent(0).contents
    #        if ev is not None:
    #            print ev
    #        else:
    #            print "NONE"
        
    #    for mySpine in hf1.spineCollection:
    #        print "\n\n***NEW SPINE: No. " + str(mySpine.id) + " upstream: " \
    #            + str(mySpine.upstream) + " downstream: " + str(mySpine.downstream)
    #        print mySpine.spineType
    #        for downstreamSpine in mySpine.downstreamSpines():
    #            print str(downstreamSpine.id) + " *** testing spineCollection code ***"
    #        for thisEvent in mySpine:
    #            print thisEvent.contents
        spine5 = hf1.spineCollection.getSpineById(5)
        self.assertEqual(spine5.id, 5)
        self.assertEqual(spine5.upstream, [3,4])
        self.assertEqual(spine5.downstream, [9,10])
        self.assertEqual(spine5.spineType, "kern")
        self.assertTrue(isinstance(spine5, KernSpine))
    
    def testSingleNote(self):
        a = SpineEvent("40..ccccc##_wtLLK~v/")
        b = a.toNote()
        self.assertEqual(b.accidental.name, "double-sharp")
        self.assertEqual(b.duration.dots, 0)
        self.assertEqual(b.duration.tuplets[0].durationNormal.dots, 2)
        
        m1 = hdStringToMeasure("=29a;:|:")
        self.assertEqual(m1.number, 29)
        self.assertEqual(m1.numberSuffix, "a")
        self.assertEqual(m1.rightBarline.style, "regular")
        self.assertEqual(m1.rightBarline.repeat_dots, "both")
        assert m1.rightBarline.pause is not None
        assert isinstance(m1.rightBarline.pause, music21.expressions.Fermata)

    def xtestFakePiece(self):
        '''
        test loading a fake piece with spine paths, lyrics, dynamics, etc.
        '''
        ms = HumdrumDataCollection(testFiles.fakeTest).stream
        ms.show('text')

    def testSpineMazurka(self):    
#        hf1 = HumdrumFile("d:/web/eclipse/music21misc/mazurka06-2.krn")    
        hf1 = HumdrumDataCollection(testFiles.mazurka6)
#        hf1 = HumdrumDataCollection(testFiles.ojibway)
#        hf1 = HumdrumDataCollection(testFiles.schubert)
#        hf1 = HumdrumDataCollection(testFiles.ivesSpring)
#        hf1 = HumdrumDataCollection(testFiles.sousaStars) # parse errors b/c of graces
        masterStream = hf1.stream
#        for spineX in hf1.spineCollection:
#            spineX.stream.id = "spine %s" % str(spineX.id)
#            masterStream.append(spineX.stream)
        expectedOutput = canonicalOutput.mazurka6repr
#        self.assertTrue(common.basicallyEqual
#                          (common.stripAddresses(expectedOutput),
#                           common.stripAddresses(masterStream._reprText())))
#        print common.stripAddresses(expectedOutput)
#       print common.stripAddresses(masterStream.recurseRepr())
        
        # humdrum type problem: how many G#s start on beat 2 of a measure?
        GsharpCount = 0
        notes = masterStream.flat.notes
        for n in notes:
            if n.offset != 1:
                continue
            if hasattr(n, "pitch") and n.pitch.name == "G#":
 #               if n.beat == 2:
                  GsharpCount += 1
            elif hasattr(n, "pitches"):
                if 'G#' in [p.name for p in n.pitches]:
  #                  if n.beat == 2:
                        GsharpCount += 1
                           
                
        self.assertEqual(GsharpCount, 34)
#       masterStream.show('text')
        
    def testParseSineNomine(self):
        from music21 import converter
        parserPath = os.path.dirname(__file__)
        sineNominePath = parserPath + os.path.sep + 'Missa_Sine_nomine-Kyrie.krn'
        myScore = converter.parse(sineNominePath)

        
if __name__ == "__main__":
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof

