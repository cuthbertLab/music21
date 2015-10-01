# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         humdrum.spineParser.py
# Purpose:      Conversion and Utility functions for Humdrum and kern in particular
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2009-2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
music21.humdrum.spineParser is a collection of utilities for changing
native humdrum code into music21 streams.  Most music21 users will
simply want to call:



>>> #_DOCS_SHOW myFile = converter.parse('myfile.krn')
>>> #_DOCS_SHOW myFile.show()


The methods in here are documented for developers wishing to expand
music21's ability to parse humdrum.

SpineParsing consists of several steps.

* The data file is read in and all events are sliced horizontally (EventCollections) and vertically (Protospines)
* Protospines are parsed into HumdrumSpines by following Spine Path Indicators (:samp:`*^` and :samp:`*v` especially)
    Protospines that separate become new Protospines with their parentSpine indicated.  Protospines
    that merge again then followed by the same Protospine as before.  This will cause problems if
    a voice remerges with another staff, but in practice I have not seen a .krn file that does this and
    should be avoided in any case.
* HumdrumSpines are reclassed according to their exclusive definition.  :samp:`**kern` becomes KernSpines, etc.
* All reclassed HumdrumSpines are filled with music21 objects in their .stream property.
    Measures are put into the spine but are empty containers.  The resulting
    HumdrumSpine.stream objects
    look like Stream.semiFlat versions in many ways.
* For HumdrumSpines with parent spines their .stream contents are then inserted into their parent spines with
    voice tagged as a music21 Group property.
* Lyrics and Dynamics are placed into their corresponding HumdrumSpine.stream objects
* Stream elements are moved into their measures within a Stream
* Measures are searched for elements with voice groups and Voice objects are created

'''
#python3
try:
    basestring # @UndefinedVariable
except NameError:
    basestring = str # @ReservedAssignment

import unittest
import math
import re

from music21.ext import six

from music21 import articulations
from music21 import chord
from music21 import dynamics
from music21 import base
from music21 import duration
from music21 import bar
from music21 import key
from music21 import note
from music21 import expressions
from music21 import tempo
from music21 import tie
from music21 import meter
from music21 import clef
from music21 import stream
from music21 import common
from music21 import exceptions21
from music21.humdrum import testFiles
from music21.humdrum import instruments

from music21 import environment
_MOD = "humdrum.spineParser"
environLocal = environment.Environment(_MOD)

flavors = {'JRP': False}

import os

spinePathIndicators = ["*+", "*-", "*^", "*v", "*x", "*"]


class HumdrumDataCollection(object):
    r'''
    A HumdrumDataCollection takes in a mandatory list where each element
    is a line of humdrum data.  Together this list represents a collection
    of spines.  Essentially it's the contents of a humdrum file.


    Usually you will probably want to use HumdrumFile which can read
    in a file directly.  This class exists in case you have your Humdrum
    data in another format (database, from the web, etc.) and already
    have it as a string.


    You are probably better off running humdrum.parseFile("filename")
    which returns a humdrum.SpineCollection directly, or even better,
    converter.parse("file.krn") which will just give you a stream.Score
    instead.



    LIMITATIONS:
    (1) Spines cannot change definition (\*\*exclusive interpretations) mid-spine.

        So if you start off with \*\*kern, the rest of the spine needs to be
        \*\*kern (actually, the first exclusive interpretation for a spine is
        used throughout)

        Note that, even though changing exclusive interpretations mid-spine
        seems to be legal by the humdrum definition, it looks like none of the
        conventional humdrum parsing tools allow for changing
        definitions mid-spine, so I don't think this limitation is a problem.
        (Craig Stuart Sapp confirmed this to me)

        The Aarden/Miller Palestrina dataset uses `\*-` followed by `\*\*kern`
        at the changes of sections thus some parsing of multiple exclusive
        interpretations in a protospine may be necessary.

    (2) Split spines are assumed to be voices in a single spine staff.


    '''
    parsedLines = False

    def __init__(self, dataStream=None, parseLines=True):
        if dataStream is None:
            dataStream = []
        # attributes
        self.eventList = None
        self.maxSpines = None
        self.parsePositionInStream = None
        self.fileLength = None
        self.protoSpines = None
        self.eventCollections = None
        
        
        self.globalEventsInserted = None
        if dataStream is []:
            raise HumdrumException("dataStream is not optional, specify some lines")
        elif isinstance(dataStream, basestring):
            dataStream = dataStream.splitlines()
        self.dataStream = dataStream
        self._storedStream = None
        if parseLines is True:
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

        hasOpus, dataCollections = self.determineIfDataStreamIsOpus(dataStream)
        if hasOpus is True: # Palestrina data collection, maybe others
            self.parseOpusDataCollections(dataCollections)
            return



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
        self.spineCollection.createMusic21Streams()
        self.parsedLines = True
        self.insertGlobalEvents()

    def determineIfDataStreamIsOpus(self, dataStream = None):
        r'''
        Some Humdrum files contain multiple pieces in one file
        which are better represented as :class:`~music21.stream.Opus`
        file containing multiple scores.

        This method examines that dataStream (or self.dataStream) and
        if it only has a single piece then it returns (False, None).

        If it has multiple pieces, it returns True and a list of dataStreams.

        >>> from pprint import pprint as pp

        >>> mps = humdrum.testFiles.multipartSanctus
        >>> hdc = humdrum.spineParser.HumdrumDataCollection(mps, parseLines = False)
        >>> (hasOpus, dataCollections) = hdc.determineIfDataStreamIsOpus()
        >>> hasOpus
        True
        >>> pp(dataCollections)
        [['!!!COM: Palestrina, Giovanni Perluigi da',
          '**kern\t**kern\t**kern\t**kern',
          '*Ibass\t*Itenor\t*Icalto\t*Icant',
          '!Bassus\t!Tenor\t!Altus\t!Cantus',
          '*clefF4\t*clefGv2\t*clefG2\t*clefG2',
          '*M4/2\t*M4/2\t*M4/2\t*M4/2',
          '=1\t=1\t=1\t=1',
          '0r\t0r\t1g\t1r',
          '.\t.\t1a\t1cc',
          '=2\t=2\t=2\t=2',
          '0r\t0r\t1g\t1dd',
          '.\t.\t1r\t1cc',
          '*-\t*-\t*-\t*-'],
         ['!! Pleni',
          '**kern\t**kern\t**kern',
          '*Ibass\t*Itenor\t*Icalto',
          '*clefF4\t*clefGv2\t*clefG2',
          '*M4/2\t*M4/2\t*M4/2',
          '=3\t=3\t=3',
          '1G\t1r\t0r',
          '1A\t1c\t.',
          '=4\t=4\t=4',
          '1B\t1d\t1r',
          '1c\t1e\t1g',
          '*-\t*-\t*-'],
         ['!! Hosanna',
          '**kern\t**kern\t**kern\t**kern',
          '*Ibass\t*Itenor\t*Icalto\t*Icant',
          '*clefF4\t*clefGv2\t*clefG2\t*clefG2',
          '*M3/2\t*M3/2\t*M3/2\t*M3/2',
          '=5\t=5\t=5\t=5',
          '1r\t1r\t1g\t1r',
          '2r\t2r\t[2a\t[2cc',
          '=5\t=5\t=5\t=5',
          '1r\t1r\t2a]\t2cc]',
          '.\t.\t2f\t1dd',
          '2r\t2r\t2g\t.',
          '*-\t*-\t*-\t*-']]
        '''
        if dataStream is None:
            dataStream = self.dataStream

        startPositions = []
        endPositions = []
        for i, line in enumerate(dataStream):
            l = line.rstrip()
            if re.search(r'^(\*\-\t)*\*\-$', l):
                endPositions.append(i)
            elif re.search(r'^(\*\*\w+\t)*\*\*\w+$', l):
                startPositions.append(i)
        if len(startPositions) < 2:
            return (False, None)
        if endPositions[-1] > startPositions[-1]:
            # properly formed .krn with *- at end
            pass
        else:
            # improperly formed .krn without *- at end
            endPositions.append(len(dataStream))

        dataCollections = []
        for i in range(len(endPositions)):
            if i == 0:
                endPos = endPositions[i]
                dataCollections.append(dataStream[:endPos+1])
            elif i == len(endPositions) -1:
                # ignore endPosition and grab to end of file
                startPos = endPositions[i-1] + 1
                dataCollections.append(dataStream[startPos:])
            else:
                # ignore startPositions, grab comments etc. between scores
                startPos = endPositions[i-1] + 1
                endPos = endPositions[i] + 1
                dataCollections.append(dataStream[startPos:endPos])
        return (True, dataCollections)

    def parseOpusDataCollections(self, dataCollections):
        '''
        take a dataCollection from `determineIfDataStreamIsOpus`
        and set self.stream to be an Opus instead.


        >>> mps = humdrum.testFiles.multipartSanctus
        >>> hdc = humdrum.spineParser.HumdrumDataCollection(mps, parseLines = False)
        >>> (hasOpus, dataCollections) = hdc.determineIfDataStreamIsOpus()
        >>> if hasOpus is True:
        ...     op = hdc.parseOpusDataCollections(dataCollections)
        ...     print(len(op.scores))
        ...     for sc in op.scores:
        ...        print(sc)
        3
        <music21.stream.Score section_1>
        <music21.stream.Score section_2>
        <music21.stream.Score section_3>
        '''
        opus = stream.Opus()
        for i, dc in enumerate(dataCollections):
            hdc = HumdrumDataCollection(dc)
            sc = hdc.stream
            sc.id = 'section_' + str(i + 1)
            opus.append(sc)

        self._storedStream = opus
        return opus

    def parseEventListFromDataStream(self, dataStream = None):
        r'''
        Sets self.eventList from a dataStream (that is, a
        list of lines).  It sets self.maxSpines to the
        largest number of spine events found on any line
        in the file.

        It sets self.fileLength to the number of lines (excluding
        totally blank lines) in the file.

        The difference between the dataStream and self.eventList
        are the following:

            * Blank lines are skipped.
            * !!! lines become :class:`~music21.humdrum.spineParser.GlobalReferenceLine` objects
            * !! lines become :class:`~music21.humdrum.spineParser.GlobalCommentLine` objects
            * all other lines become :class:`~music21.humdrum.spineParser.SpineLine` objects

        Returns eventList in addition to setting it as self.eventList.


        >>> eventString = "!!! COM: Beethoven, Ludwig van\n" + \
        ...               "!! Not really a piece by Beethoven\n" + \
        ...               "**kern\t**dynam\n" + \
        ...               "C4\tpp\n" + \
        ...               "D8\t.\n"
        >>> hdc = humdrum.spineParser.HumdrumDataCollection(eventString)
        >>> eList = hdc.parseEventListFromDataStream()
        >>> eList is hdc.eventList
        True
        >>> for e in eList:
        ...     print(e)
        <music21.humdrum.spineParser.GlobalReferenceLine object at 0x...>
        <music21.humdrum.spineParser.GlobalCommentLine object at 0x...>
        <music21.humdrum.spineParser.SpineLine object at 0x...>
        <music21.humdrum.spineParser.SpineLine object at 0x...>
        <music21.humdrum.spineParser.SpineLine object at 0x...>
        >>> print(eList[0].value)
        Beethoven, Ludwig van
        >>> print(eList[3].spineData)
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
            elif re.match(r'\!\!\!', line):
                self.eventList.append(GlobalReferenceLine(self.parsePositionInStream, line))
            elif re.match(r'\!\!', line): ## find global comments at the top of the line
                self.eventList.append(GlobalCommentLine(self.parsePositionInStream, line))
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
        horizontal position in the dataStream.  The contents of
        each cell is a SpineEvent object or None (if there's no
        data at that point).  Even '.' (continuation events) get
        translated into SpineEvent objects.

        Calls :meth:`~music21.humdrum.spineParser.parseEventListFromDataStream`
        if it hasn't already been called.

        returns a tuple of protoSpines and eventCollections in addition to
        setting it in the calling object.


        >>> eventString = "!!!COM: Beethoven, Ludwig van\n" + \
        ...               "!! Not really a piece by Beethoven\n" + \
        ...               "**kern\t**dynam\n" + \
        ...               "C4\tpp\n" + \
        ...               "D8\t.\n"
        >>> hdc = humdrum.spineParser.HumdrumDataCollection(eventString)
        >>> protoSpines, eventCollections = hdc.parseProtoSpinesAndEventCollections()
        >>> protoSpines is hdc.protoSpines
        True
        >>> eventCollections is hdc.eventCollections
        True

        Looking at individual slices is unlikely to tell you much.

        >>> for thisSlice in eventCollections:
        ...    print(thisSlice)
        <music21.humdrum.spineParser.EventCollection object at 0x...>
        <music21.humdrum.spineParser.EventCollection object at 0x...>
        <music21.humdrum.spineParser.EventCollection object at 0x...>
        <music21.humdrum.spineParser.EventCollection object at 0x...>
        <music21.humdrum.spineParser.EventCollection object at 0x...>

        >>> for thisSlice in protoSpines:
        ...    print(thisSlice)
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
                else:  ## Global event -- either GlobalCommentLine or GlobalReferenceLine
                    if j == 0: ## adds to all spines but just runs the first time.
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
        currentSpineList = common.defaultlist(lambda:None)
        spineCollection = SpineCollection()

        # go through the event collections line by line
        for i in range(0, self.fileLength):
            thisEventCollection = eventCollections[i]
            for j in range(0, maxSpines):
                thisEvent = protoSpines[j].eventList[i]

                if thisEvent is not None:  # something there                
                    currentSpine = currentSpineList[j]
                    if currentSpine is None:
                        ## first event after a None = new spine because
                        ## Humdrum does not require *+ at the beginning
                        currentSpine = spineCollection.addSpine()
                        currentSpine.insertPoint = i
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
                newSpineList = common.defaultlist(lambda:None)
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
                        newSpine1 = spineCollection.addSpine(streamClass = stream.Voice)
                        newSpine1.insertPoint = i+1
                        newSpine1.parentSpine = currentSpine
                        newSpine1.isFirstVoice = True
                        newSpine2 = spineCollection.addSpine(streamClass = stream.Voice)
                        newSpine2.insertPoint = i+1
                        newSpine2.parentSpine = currentSpine
                        currentSpine.endingPosition = i # will be overridden if merged
                        currentSpine.childSpines.append(newSpine1)
                        currentSpine.childSpines.append(newSpine2)

                        currentSpine.childSpineInsertPoints[i] = (newSpine1, newSpine2)
                        newSpineList.append(newSpine1)
                        newSpineList.append(newSpine2)
                    elif thisEvent.contents == "*v":  #merge spine -- n.b. we allow non-adjacent lines to be merged. this is incorrect
                        if mergerActive is False:     #               per humdrum syntax, but is easily done.
                            # assume that previous spine continues
                            if currentSpine.parentSpine is not None:
                                mergerActive = currentSpine.parentSpine
                            else:
                                mergerActive = True
                            currentSpine.endingPosition = i
                        else:  ## if second merger code is not found then a one-to-one spine "merge" occurs
                            currentSpine.endingPosition = i
                            # merge back to parent if possible:
                            if currentSpine.parentSpine is not None:
                                newSpineList.append(currentSpine.parentSpine)
                            # or merge back to other spine's parent:
                            elif mergerActive is not True: # other spine parent set
                                newSpineList.append(mergerActive)
                            # or make a new spine...
                            else:
                                s = spineCollection.addSpine(streamClass = stream.Part)
                                s.insertPoint = i
                                newSpineList.append(s)

                            mergerActive = False

                    elif thisEvent.contents == "*x":  # exchange spine
                        if exchangeActive is False:
                            exchangeActive = currentSpine
                        else:  ## if second exchange is not found, then both lines disappear and exception is raised
                                ## n.b. we allow more than one PAIR of exchanges in a line so long as the first
                                ## is totally finished by the time the second happens
                            newSpineList.append(currentSpine)
                            newSpineList.append(exchangeActive)
                            exchangeActive = False
                    else:  ## null processing code "*"
                        newSpineList.append(currentSpine)

                if exchangeActive is not False:
                    raise HumdrumException("ProtoSpine found with unpaired exchange instruction at line %d [%s]" % (i, thisEventCollection.events))
                currentSpineList = newSpineList

        return spineCollection

    def insertGlobalEvents(self):
        '''
        Insert the Global Events (GlobalReferenceLines and GlobalCommentLines) into an appropriate
        place in the outer Stream.


        Run after self.spineCollection.createMusic21Streams().  Is run automatically by self.parseLines().
        uses self.spineCollection.getOffsetsAndPrioritiesByPosition()
        '''
        if hasattr(self, 'globalEventsInserted') and self.globalEventsInserted is True:
            return
        self.globalEventsInserted = True
        positionDict = self.spineCollection.getOffsetsAndPrioritiesByPosition()
        eventList = self.eventList
        maxEventList = len(eventList)
        numberOfGlobalEventsInARow = 0
        insertList = []
        appendList = []

        for i, event in enumerate(eventList):
            if event.isSpineLine is False:
                numberOfGlobalEventsInARow += 1
                insertOffset = None
                insertPriority = 0
                for j in range(i+1, maxEventList):
                    if j in positionDict:
                        insertOffset = positionDict[j][0]
                        # hopefully not more than 20 events in a row...
                        insertPriority = positionDict[j][1][0].priority - 40 + numberOfGlobalEventsInARow
                        break
                if event.isReference is True:
                    # TODO: Fix GlobalReference
                    el = GlobalReference(event.code, event.value)
                else:
                    el = GlobalComment(event.value)
                el.priority = insertPriority
                if insertOffset is None:
                    appendList.append(el)
                else:
                    insertTuple = (insertOffset, el)
                    insertList.append(insertTuple)
                #self.stream.insert(insertOffset, el)
            else:
                numberOfGlobalEventsInARow = 0

        for offset, el in insertList:
            self.stream._insertCore(offset, el)
        if insertList:
            self.stream.elementsChanged()
        for el in appendList:
            self.stream._appendCore(el)
        if appendList:
            self.stream.elementsChanged()

    def _getStream(self):
        if self._storedStream is not None:
            return self._storedStream
        if self.parsedLines is False:
            self.parseLines()

        if self.spineCollection is None:
            raise HumdrumException("parsing got no spine collections!")
        elif self.spineCollection.spines is None:
            raise HumdrumException("really? not a single spine in your data? um, not my problem! (well, maybe it is...file a bug report if you have doubled checked your data)")
        elif self.spineCollection.spines[0].stream is None:
            raise HumdrumException("okay, you got at least one spine, but it aint got a stream in it; have you thought of taking up kindergarten teaching? (just kidding, check your data or file a bug report)")
        else:
            masterStream = stream.Score()
            for thisSpine in self.spineCollection:
                thisSpine.stream.id = "spine_" + str(thisSpine.id)
            for thisSpine in self.spineCollection:
                if thisSpine.parentSpine is None and thisSpine.spineType == 'kern':
                    masterStream.insert(thisSpine.stream)
            self._storedStream = masterStream
            return masterStream

    stream = property(_getStream)

class HumdrumFile(HumdrumDataCollection):
    '''
    A HumdrumFile is a HumdrumDataCollection which takes
    as a mandatory argument a filename to be opened and read.
    '''
    def __init__(self, filename = None):
        super(HumdrumFile, self).__init__()
        self.dataStream = None
        self._storedStream = None
        if (filename is not None):
            try:
                if six.PY3:
                    with open(filename, encoding="latin-1") as humFH:
                        self.eventList = self.parseFH(humFH)
                else:
                    with open(filename) as humFH:
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
    :class:`~music21.humdrum.spineParser.GlobalCommentLine`, and
    :class:`~music21.humdrum.spineParser.GlobalReferenceLine` classes
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


    >>> hsl = humdrum.spineParser.SpineLine(
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

class GlobalReferenceLine(HumdrumLine):
    r'''
    A GlobalReferenceLine is a type of HumdrumLine that contains
    information about the humdrum document.

    In humdrum it is represented by three exclamation points
    followed by non-whitespace followed by a colon.  Examples::

        !!!COM: Stravinsky, Igor Fyodorovich
        !!!CDT: 1882/6/17/-1971/4/6
        !!!ODT: 1911//-1913//; 1947//
        !!!OPT@@RUS: Vesna svyashchennaya
        !!!OPT@FRE: Le sacre du printemps

    The GlobalReferenceLine object takes two inputs::

        position   line number in the humdrum file
        contents   string of contents

    And stores them as three attributes::

        position: as above
        code:     non-whitespace code (usually three letters)
        value:    its value


    >>> gr = humdrum.spineParser.GlobalReferenceLine(
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
        noExclaim = re.sub(r'^\!\!\!+','',contents)
        try:
            (code, value) = noExclaim.split(":", 1)
            value = value.strip()
            if (code is None):
                raise HumdrumException("GlobalReferenceLine (!!!) found without a code listed; this is probably a problem! %s " % contents)
        except IndexError:
            raise HumdrumException("GlobalReferenceLine (!!!) found without a code listed; this is probably a problem! %s " % contents)

        self.contents = contents
        self.code = code
        self.value = value

class GlobalCommentLine(HumdrumLine):
    '''
    A GlobalCommentLine is a humdrum comment that pertains to all spines
    In humdrum it is represented by two exclamation points (and usually one space)

    The GlobalComment object takes two inputs and stores them as attributes::

        position (line number in the humdrum file)
        contents (string of contents)
        value    (contents minus !!)

    The constructor can be passed (position, contents)
    if contents begins with bangs, they are removed along with up to one space directly afterwards


    >>> com1 = humdrum.spineParser.GlobalCommentLine(
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
    isReference = False
    isComment = True
    isSpineLine = False
    numSpines = 0

    def __init__(self, position = 0, contents = ""):
        self.position = position
        value = re.sub(r'^\!\!+\s?','',contents)
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

############ HUMDRUMSPINES #########################
# Ready to be parsed...

class HumdrumSpine(object):
    r'''
    A HumdrumSpine is a representation of a generic HumdrumSpine
    regardless of \*\*definition after spine path indicators have
    been simplified.

    A HumdrumSpine is a collection of events arranged vertically that have a
    connection to each other.
    Each HumdrumSpine MUST have an id (numeric or string) attached to it.


    >>> SE = humdrum.spineParser.SpineEvent
    >>> spineEvents = [SE('**kern'),SE('c,4'), SE('d#8')]
    >>> spine1Id = 5
    >>> spine1 = humdrum.spineParser.HumdrumSpine(spine1Id, spineEvents)
    >>> spine1.insertPoint = 5
    >>> spine1.endingPosition = 6
    >>> spine1.parentSpine = 3  # spine 3 is the previous spine leading to this one
    >>> spine1.childSpines = [7,8] # the spine ends by being split into spines 7 and 8

    we keep weak references to the spineCollection so that we
    don't have circular references

    >>> spineCollection1 = humdrum.spineParser.SpineCollection()
    >>> spine1.spineCollection = spineCollection1

    The spineType property searches the EventList or parentSpine to
    figure out the spineType

    >>> spine1.spineType
    'kern'

    Spines can be iterated through:

    >>> for e in spine1:
    ...    print(e)
    **kern
    c,4
    d#8

    If you'd eventually like this spine to be converted to a class
    other than :class:`~music21.stream.Stream`, pass its classname in
    as the streamClass argument:

    >>> spine2 = humdrum.spineParser.HumdrumSpine(
    ...              streamClass = stream.Part)
    >>> spine2.stream
    <music21.stream.Part ...>
    '''
    def __init__(self, id=0, eventList=None, streamClass=stream.Stream): #@ReservedAssignment
        self.id = id
        if eventList is None:
            eventList = []
        for event in eventList:
            event.spineId = id

        self.eventList = eventList
        self.stream = streamClass()
        self.insertPoint = 0
        self.endingPosition = 0
        self.parentSpine = None
        self.newSpine = None
        self.isLastSpine = False
        self.childSpines = []
        self.childSpineInsertPoints = {}

        self.parsed = False
        self.measuresMoved = False
        self.insertionsDone = False

        self._spineCollection = None
        self._spineType = None
        
        self.isFirstVoice = None
        self.iterIndex = None
        

    def __repr__(self):
        representation = "Spine: " + str(self.id)
        if self.parentSpine:
            representation += " [child of: " + str(self.parentSpine.id) + "]"
        if self.childSpines:
            representation += " [parent of: "
            for s in self.childSpines:
                representation += str(s.id) + " "
            representation += " ]"
        return representation

    def append(self, event):
        '''
        add an item to this Spine
        '''
        self.eventList.append(event)

    def __iter__(self):
        '''
        Resets the counter to 0 so that iteration is correct
        '''
        self.iterIndex = 0
        return self

    def next(self):
        '''
        Returns the current event and increments the iteration index.
        '''
        if self.iterIndex == len(self.eventList):
            raise StopIteration
        thisEvent = self.eventList[self.iterIndex]
        self.iterIndex += 1
        return thisEvent

    def __next__(self):
        return self.next()

    def _getSpineCollection(self):
        return common.unwrapWeakref(self._spineCollection)

    def _setSpineCollection(self, sc = None):
        self._spineCollection = common.wrapWeakref(sc)

    spineCollection = property(_getSpineCollection, _setSpineCollection)

    def _getLocalSpineType(self):
        if self._spineType is not None:
            return self._spineType
        else:
            for thisEvent in self.eventList:
                m1 = re.match(r"\*\*(.*)", thisEvent.contents)
                if m1:
                    self._spineType = m1.group(1)
                    return self._spineType
            return None

    def _getParentSpineType(self):
        parentSpine = self.parentSpine
        if parentSpine is not None:
            psSpineType = parentSpine.spineType
            if psSpineType is not None:
                return psSpineType
            return None
        else:
            return None

    def _getSpineType(self):
        '''
        searches the current and parent spineType for a search
        '''
        if self._spineType is not None:
            return self._spineType
        else:
            st = self._getLocalSpineType()
            if st is not None:
                self._spineType = st
                return st
            else:
                st = self._getParentSpineType()
                if st is not None:
                    self._spineType = st
                    return st
                else:
                    raise HumdrumException("Could not determine spineType " +
                                           "for spine with id " + str(self.id))

    def _setSpineType(self, newSpineType = None):
        self._spineType = newSpineType

    spineType = property(_getSpineType, _setSpineType)

    def moveElementsIntoMeasures(self, streamIn):
        '''
        takes a parsed stream and moves the elements inside the
        measures.  Works with pickup measures, etc. Does not
        automatically create ties, etc...

        Why not just use Stream.makeMeasures()? because
        humdrum measures contain extra information about barlines
        etc. and pickups are explicitly defined.


        >>> s1 = stream.Stream()
        >>> s1.append(meter.TimeSignature('2/4'))
        >>> m1 = stream.Measure()
        >>> m1.number = 1
        >>> s1.append(m1)
        >>> s1.append(note.Note('C4', type='quarter'))
        >>> m2 = stream.Measure()
        >>> m2.number = 2
        >>> s1.append(m2)
        >>> s1.append(note.Note('D4', type='half'))
        >>> s1.show('text')
        {0.0} <music21.meter.TimeSignature 2/4>
        {0.0} <music21.stream.Measure 1 offset=0.0>
        <BLANKLINE>
        {0.0} <music21.note.Note C>
        {1.0} <music21.stream.Measure 2 offset=1.0>
        <BLANKLINE>
        {1.0} <music21.note.Note D>

        >>> hds = humdrum.spineParser.HumdrumSpine()
        >>> s2 = hds.moveElementsIntoMeasures(s1)
        >>> s2.show('text')
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.meter.TimeSignature 2/4>
            {0.0} <music21.note.Note C>
        {1.0} <music21.stream.Measure 2 offset=1.0>
            {0.0} <music21.note.Note D>

        The first measure is correctly identified as a pickup!

        >>> s2.measure(1).paddingLeft
        1.0
        '''
        streamOut = streamIn.__class__()
        currentMeasure = stream.Measure()
        currentMeasure.number = 0
        currentMeasureNumber = 0
        currentMeasureOffset = 0
        hasMeasureOne = False
        for el in streamIn:
            if 'Stream' in el.classes:
                if currentMeasureNumber != 0 or currentMeasure:
                    currentMeasure.elementsChanged()
                    #streamOut.append(currentMeasure)
                    streamOut._appendCore(currentMeasure)
                currentMeasure = el
                currentMeasureNumber = el.number
                currentMeasureOffset = el.offset
                if currentMeasureNumber == 1:
                    hasMeasureOne = True
            else:
                if currentMeasureNumber != 0 or el.duration.quarterLength != 0:
                    #currentMeasure.insert(el.offset - currentMeasureOffset, el)
                    currentMeasure._insertCore(el.offset - currentMeasureOffset, el)
                else:
                    #streamOut.append(el)
                    streamOut._appendCore(el)
        # update the most recent measure and the surrounding stream, then append the last
        currentMeasure.elementsChanged()
        streamOut.elementsChanged()
        if currentMeasure:
            streamOut.append(currentMeasure)

        # move beginning stuff (Clefs, KeySig, etc.) to first measure...
        measureElements = streamOut.getElementsByClass('Measure')
        if measureElements:
            m1 = measureElements[0]
            if hasMeasureOne == False: # pickup measure is not measure1
                m1.number = 1
            beginningStuff = streamOut.getElementsByOffset(0)
            for el in beginningStuff:
                if 'Stream' in el.classes:
                    pass
                elif 'MiscTandem' in el.classes:
                    pass
                else:
                    m1.insert(0, el)
                    streamOut.remove(el)
            m1TimeSignature = m1.timeSignature
            if m1TimeSignature is not None:
                if m1.duration.quarterLength < m1TimeSignature.barDuration.quarterLength:
                    m1.paddingLeft = m1TimeSignature.barDuration.quarterLength - m1.duration.quarterLength

        return streamOut

    def parse(self):
        '''
        Dummy method that pushes all these objects to HumdrumSpine.stream
        as ElementWrappers.  Should be overridden in
        specific Spine subclasses.
        '''
        lastContainer = hdStringToMeasure('=0')

        for event in self.eventList:
            eventC = str(event.contents)
            thisObject = None
            if eventC == ".":
                pass
            elif eventC.startswith('*'):
                ## control processing
                if eventC not in spinePathIndicators:
                    thisObject = MiscTandem(eventC)
            elif eventC.startswith('='):
                lastContainer  = hdStringToMeasure(eventC, lastContainer)
                thisObject = lastContainer
            elif eventC.startswith('!'):
                thisObject = SpineComment(eventC)
            else:
                thisObject = base.ElementWrapper(event)
                thisObject.humdrumPosition = event.position # pylint: disable=attribute-defined-outside-init

            if thisObject is not None:
                self.stream._appendCore(thisObject)
        self.stream.elementsChanged()

class KernSpine(HumdrumSpine):
    r'''
    A KernSpine is a type of humdrum spine with the \*\*kern
    attribute set and thus events are processed as if they
    are kern notes
    '''
    def parse(self):
        lastContainer = hdStringToMeasure('=0')
        inTuplet = False
        lastNote = None
        currentBeamNumbers = 0

        for event in self.eventList:
            # event is a SpineEvent object
            try:
                eventC = event.contents
                thisObject = None
                if eventC == ".":
                    pass
                elif eventC.startswith('*'):
                    ## control processing
                    tempObject = kernTandemToObject(eventC)
                    if tempObject is not None:
                        thisObject = tempObject
                elif eventC.startswith('='):
                    lastContainer  = hdStringToMeasure(eventC, lastContainer)
                    thisObject = lastContainer
                elif eventC.startswith('!'):
                    thisObject = SpineComment(eventC)
                    if thisObject.comment == "":
                        thisObject = None
                elif eventC.count(' '):
                    ### multipleNotes
                    notesToProcess = eventC.split()
                    chordNotes = []
                    for noteToProcess in notesToProcess:
                        thisNote = hdStringToNote(noteToProcess)
                        chordNotes.append(thisNote)
                    thisObject = chord.Chord(chordNotes, beams=chordNotes[-1].beams)
                    thisObject.duration = chordNotes[0].duration

                    if currentBeamNumbers != 0 and len(thisObject.beams.beamsList) == 0:
                        for i in range(currentBeamNumbers):
                            thisObject.beams.append('continue')
                    elif thisObject.beams.beamsList:
                        if thisObject.beams.beamsList[0].type == 'stop':
                            currentBeamNumbers = 0
                        else:
                            for i in range(len(thisObject.beams.beamsList)):
                                if thisObject.beams.beamsList[i].type != 'stop':
                                    currentBeamNumbers += 1

                    # nested tuplets not supported by humdrum...
                    if inTuplet is False and thisObject.duration.tuplets:
                        inTuplet = True
                        desiredTupletDuration = thisObject.duration.tuplets[0].totalTupletLength()
                        currentTupletDuration = thisObject.duration.quarterLength
                        thisObject.duration.tuplets[0].type = 'start'
                    elif inTuplet is True and len(thisObject.duration.tuplets) == 0:
                        inTuplet = False
                        desiredTupletDuration = 0.0
                        currentTupletDuration = 0.0
                        lastNote.duration.tuplets[0].type = 'stop'
                    elif inTuplet is True:
                        currentTupletDuration += thisObject.duration.quarterLength
                        if (currentTupletDuration == desiredTupletDuration or
                            # check for things like 6 6 3 6 6; redundant with previous, but written out for clarity
                            currentTupletDuration/desiredTupletDuration == int(currentTupletDuration/desiredTupletDuration)
                            ):
                            thisObject.duration.tuplets[0].type = 'stop'
                            inTuplet = False
                            currentTupletDuration = 0.0
                            desiredTupletDuration = 0.0
                    lastNote = thisObject

                else: # Note or Rest
                    thisObject = hdStringToNote(eventC)
                    if hasattr(thisObject, 'beams'):
                        if currentBeamNumbers != 0 and len(thisObject.beams.beamsList) == 0:
                            for i in range(currentBeamNumbers):
                                thisObject.beams.append('continue')
                        elif thisObject.beams.beamsList:
                            if thisObject.beams.beamsList[0].type == 'stop':
                                currentBeamNumbers = 0
                            else:
                                for i in range(len(thisObject.beams.beamsList)):
                                    if thisObject.beams.beamsList[i].type != 'stop':
                                        currentBeamNumbers += 1
                    # nested tuplets not supported by humdrum...
                    if inTuplet is False and thisObject.duration.tuplets:
                        inTuplet = True
                        desiredTupletDuration = thisObject.duration.tuplets[0].totalTupletLength()
                        currentTupletDuration = thisObject.duration.quarterLength
                        thisObject.duration.tuplets[0].type = 'start'
                    elif inTuplet is True and not thisObject.duration.tuplets:
                        inTuplet = False
                        desiredTupletDuration = 0.0
                        currentTupletDuration = 0.0
                        lastNote.duration.tuplets[0].type = 'stop'
                    elif inTuplet is True:
                        currentTupletDuration += thisObject.duration.quarterLength
                        if (currentTupletDuration == desiredTupletDuration or
                            # check for things like 6 6 3 6 6; redundant with previous, but written out for clarity
                            currentTupletDuration/desiredTupletDuration == int(currentTupletDuration/desiredTupletDuration)
                            ):
                            thisObject.duration.tuplets[0].type = 'stop'
                            inTuplet = False
                            currentTupletDuration = 0.0
                            desiredTupletDuration = 0.0

                    lastNote = thisObject

                if thisObject is not None:
                    thisObject.humdrumPosition = event.position # pylint: disable=attribute-defined-outside-init
                    thisObject.priority = event.position
                    self.stream._appendCore(thisObject)
            except Exception as e: # pylint: disable=broad-except
                import traceback
                environLocal.warn("Error in parsing event ('%s') at position %r for spine %r: %s" % (event.contents, event.position, event.spineId, str(e)))
                tb = traceback.format_exc()
                environLocal.printDebug("Traceback for the exception: \n%s" % (tb))
                # traceback... environLocal.printDebug()

        self.stream.elementsChanged()
        ## still to be done later... move things before first measure to first measure!

class DynamSpine(HumdrumSpine):
    r'''
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
                    thisObject = MiscTandem(eventC)
            elif eventC.startswith('='):
                if thisContainer is not None:
                    thisContainer.elementsChanged()
                    self.stream._appendCore(thisContainer)
                thisContainer = hdStringToMeasure(eventC)
            elif eventC.startswith('!'):
                thisObject = SpineComment(eventC)
                if thisObject.comment == "":
                    thisObject = None

            elif eventC.startswith('<'):
                thisObject = dynamics.Diminuendo()
            elif eventC.startswith('>'):
                thisObject = dynamics.Crescendo()
            else:
                thisObject = dynamics.Dynamic(eventC)

            if thisObject is not None:
                thisObject.humdrumPosition = event.position # pylint: disable=attribute-defined-outside-init
                if thisContainer is None:
                    self.stream._appendCore(thisObject)
                else:
                    thisContainer._appendCore(thisObject)

        self.stream.elementsChanged()

####### END HUMDRUM SPINES


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


    >>> se1 = humdrum.spineParser.SpineEvent('EEE-8')
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

    def toNote(self, convertString = None):
        r'''
        parse the object as a \*\*kern note and return the a
        :class:`~music21.note.Note` object (or Rest, or Chord)


        >>> se = humdrum.spineParser.SpineEvent('DD#4')
        >>> n = se.toNote()
        >>> n
        <music21.note.Note D#>
        >>> n.octave
        2
        >>> n.duration.type
        'quarter'
        '''
        if convertString is None:
            return hdStringToNote(self.contents)
        else:
            return hdStringToNote(convertString)

#------SPINE COLLECTION------------

class SpineCollection(object):
    '''
    A SpineCollection is a set of HumdrumSpines with relationships to each
    other and where their position attributes indicate
    simultaneous onsets.

    When you iterate over a SpineCollection, it goes from right to
    left, since that's the order that humdrum expects.
    '''

    def __init__(self):
        self.spines = []
        self.nextFreeId  = 0
        self.spineReclassDone = False
        self.iterIndex = None
        self.newSpine = None

    def __iter__(self):
        '''Resets the counter to len(self.spines) so that iteration is correct'''
        self.iterIndex = len(self.spines) - 1
        return self

    def __next__(self):
        '''Returns the current spine and decrements the iteration index.'''
        if self.iterIndex < 0:
            raise StopIteration
        thisSpine = self.spines[self.iterIndex]
        self.iterIndex -= 1
        return thisSpine

    next = __next__ # py2

    def addSpine(self, streamClass = stream.Part):
        '''
        creates a new spine in the collection and returns it.

        By default, the underlying music21 class of the spine is
        :class:`~music21.stream.Part`.  This can be overridden
        by passing in a different streamClass.

        Automatically sets the id of the Spine.


        >>> hsc = humdrum.spineParser.SpineCollection()
        >>> newSpine = hsc.addSpine()
        >>> newSpine.id
        0
        >>> newSpine.stream
        <music21.stream.Part ...>
        >>> newSpine2 = hsc.addSpine(streamClass = stream.Stream)
        >>> newSpine2.id
        1
        >>> newSpine2
        Spine: 1
        >>> newSpine2.stream
        <music21.stream.Stream ...>
        '''
        self.newSpine = HumdrumSpine(self.nextFreeId, streamClass = streamClass)
        self.newSpine.spineCollection = self
        self.spines.append(self.newSpine)
        self.nextFreeId += 1
        self.newSpine.isFirstVoice = False # if this is a subspine (Voice) then does it need to close off measures, etc.
        return self.newSpine

    def appendSpine(self, spine):
        '''
        appendSpine(spine) -- appends an already existing HumdrumSpine
        to the SpineCollection.  Returns void
        '''
        self.spines.append(spine)

    def getSpineById(self, spineId):
        '''
        returns the HumdrumSpine with the given id.

        raises a HumdrumException if the spine with a given id is not found
        '''
        for thisSpine in self.spines:
            if thisSpine.id == spineId:
                return thisSpine
        raise HumdrumException("Could not find a Spine with that ID")

    def removeSpineById(self, spineId):
        '''
        deletes a spine from the SpineCollection (after inserting, integrating, etc.)


        >>> hsc = humdrum.spineParser.SpineCollection()
        >>> newSpine = hsc.addSpine()
        >>> newSpine.id
        0
        >>> newSpine2 = hsc.addSpine()
        >>> newSpine2.id
        1
        >>> hsc.spines
        [Spine: 0, Spine: 1]
        >>> hsc.removeSpineById(newSpine.id)
        >>> hsc.spines
        [Spine: 1]

        raises a HumdrumException if the spine with a given id is not found
        '''
        for s in self.spines:
            if s.id == spineId:
                self.spines.remove(s)
                return None
        raise HumdrumException("Could not find a Spine with that ID %d" % id)


    def createMusic21Streams(self):
        '''
        Create Music21 Stream objects from spineCollections by running:

            self.reclassSpines()
            self.parseMusic21()
            self.performInsertions()
            self.moveObjectsToMeasures()
            self.moveDynamicsAndLyricsToStreams()
            self.makeVoices()
            self.assignIds()
        '''
        self.reclassSpines()
        self.parseMusic21()
        self.performInsertions()
        self.moveObjectsToMeasures()
        self.moveDynamicsAndLyricsToStreams()
        self.makeVoices()
        self.assignIds()

    def assignIds(self):
        '''
        assign an ID based on the instrument or just a string of a number if none


        >>> hsc = humdrum.spineParser.SpineCollection()
        >>> newSpineDefault = hsc.addSpine()
        >>> newSpineDefault2 = hsc.addSpine()
        >>> newSpineOboe1 = hsc.addSpine()
        >>> newSpineOboe2 = hsc.addSpine()
        >>> newSpineTrumpet = hsc.addSpine()
        >>> newSpineOboe1.stream.append(instrument.Oboe())
        >>> newSpineOboe2.stream.append(instrument.Oboe())
        >>> newSpineTrumpet.stream.append(instrument.Trumpet())
        >>> hsc.assignIds()
        >>> for sp in hsc.spines:
        ...     print(sp.stream.id)
        1
        2
        Oboe-1
        Oboe-2
        Trumpet
        '''
        usedIds = {None: 0}
        firstStreamForEachInstrument = {}
        for thisSpine in self.spines:
            spineStream = thisSpine.stream
            instrumentsStream = spineStream.getElementsByClass('Instrument')
            if len(instrumentsStream) == 0:
                spineInstrument = None
            else:
                spineInstrument = instrumentsStream[0].instrumentName
            if spineInstrument not in usedIds:
                firstStreamForEachInstrument[spineInstrument] = spineStream
                usedIds[spineInstrument] = 1
                spineStream.id = spineInstrument
            elif spineInstrument is None:
                usedIds[None] += 1
                spineStream.id = str(usedIds[None])
            else:
                if usedIds[spineInstrument] == 1:
                    firstStreamForEachInstrument[spineInstrument].id = firstStreamForEachInstrument[spineInstrument].id + '-1'
                usedIds[spineInstrument] += 1
                spineStream.id = spineInstrument + '-' + str(usedIds[spineInstrument])

    def performInsertions(self):
        '''
        take a parsed spineCollection as music21 objects and take
        subspines and put them in their proper location
        '''
        for thisSpine in self.spines:
            #removeSpines = []
            if thisSpine.parentSpine is not None:
                continue
            if len(thisSpine.childSpines) == 0:
                continue

            # only spines with children spines and parent spines continue
            newStream = thisSpine.stream.__class__()
            insertPoints = sorted(thisSpine.childSpineInsertPoints)
            lastHumdrumPosition = -1
            # use _elements for being faster.
            for el in thisSpine.stream._elements:
                try:
                    humdrumPosition = el.humdrumPosition
                    for i in insertPoints:
                        if lastHumdrumPosition > i or humdrumPosition < i:
                            continue
                        ## insert a subspine into this Stream at the current location
                        self.performSpineInsertion(thisSpine, newStream, i)
                        insertPoints.remove(i)
                    lastHumdrumPosition = humdrumPosition
                    del el.humdrumPosition
                except AttributeError: # no el.humdrumPosition
                    pass
                newStream._appendCore(el)
                #newStream.append(el)
            newStream.elementsChanged()
            thisSpine.stream = newStream

            # some spines were not inserted because the insertion point was at the end of the parent spine
            # happens in some musedata conversions, such as beethoven 5, movement 1.
            for i in insertPoints:
                self.performSpineInsertion(thisSpine, newStream, i)
            #for removeMe in removeSpines:
            #    #needed for some tests
            #    self.removeSpineById(removeMe)

    def performSpineInsertion(self, thisSpine, newStream, insertionPoint):
        '''
        Insert all the spines into newStream that should be inserted into thisSpine at insertionPoint.
        '''
        newStream.elementsChanged() # update highestTime
        startPoint = newStream.highestTime
        childrenToInsert = thisSpine.childSpineInsertPoints[insertionPoint]
        voiceNumber = 0
        for insertSpine in childrenToInsert:
            #removeSpines.append(insertSpine.id)
            voiceNumber += 1
            voiceStr = 'voice' + str(voiceNumber)
            for insertEl in insertSpine.stream._elements:
                if insertSpine.isFirstVoice is False and 'Measure' in insertEl.classes:
                    pass # only insert one measure object per spine
                else:
                    insertEl.groups.append(voiceStr)
                    #newStream.insert(startPoint + insertEl.offset, insertEl)
                    newStream._insertCore(startPoint + insertEl.offset, insertEl)
        newStream.elementsChanged() # call between _insertCore and _appendCore


    def reclassSpines(self):
        r'''
        changes the classes of HumdrumSpines to more specific types
        (KernSpine, DynamicSpine)
        according to their spineType (e.g., \*\*kern, \*\*dynam)
        '''
        for thisSpine in self.spines:
            if thisSpine.spineType == "kern":
                thisSpine.__class__ = KernSpine
            elif thisSpine.spineType == "dynam":
                thisSpine.__class__ = DynamSpine
        self.spineReclassDone = True

    def getOffsetsAndPrioritiesByPosition(self):
        '''
        iterates through the spines by location
        and records the offset and priority for each

        Returns a dictionary where each index is humdrumPosition and the value is a
        two-element tuple where the first element is the music21 offset and the
        second element is a list of Music21Objects at that position
        '''
        positionDict = {}
        for thisSpine in self.spines:
            if thisSpine.parentSpine == None:
                sf = thisSpine.stream.flat
                for el in sf:
                    if hasattr(el, 'humdrumPosition'):
                        if el.humdrumPosition not in positionDict:
                            elementList = [el]
                            valueTuple = (el.offset, elementList)
                            positionDict[el.humdrumPosition] = valueTuple
                        else:
                            elementList = positionDict[el.humdrumPosition][1]
                            elementList.append(el)
        #print positionDict
        return positionDict

    def moveObjectsToMeasures(self):
        '''
        run moveElementsIntoMeasures for each HumdrumSpine
        that is not a subspine.

        Also fixes up the tuplets using duration.TupletFixer
        '''
        tf = duration.TupletFixer()

        for thisSpine in self.spines:
            if thisSpine.parentSpine == None:
                thisSpine.stream = thisSpine.moveElementsIntoMeasures(thisSpine.stream)

                # fix tuplet groups
                for m in thisSpine.stream.getElementsByClass('Measure'):
                    tf.setStream(m)
                    tupletGroups = tf.findTupletGroups(incorporateGroupings = True)
                    for tg in tupletGroups:
                        tf.fixBrokenTupletDuration(tg)

                thisSpine.measuresMoved = True

    def moveDynamicsAndLyricsToStreams(self):
        '''
        move :samp:`**dynam` and :samp:`**lyrics/**text` information to the appropriate staff.

        Assumes that :samp:`*staff` is consistent through the spine.
        '''
        kernStreams = {}
        for thisSpine in self.spines:
            if thisSpine.parentSpine == None:
                if thisSpine.spineType == 'kern':
                    for tandem in thisSpine.stream.getElementsByClass('MiscTandem'):
                        if tandem.tandem.startswith('*staff'):
                            staffInfo = int(tandem.tandem[6:]) # single staff
                            kernStreams[staffInfo] = thisSpine.stream
                            break
        for thisSpine in self.spines:
            if thisSpine.parentSpine == None:
                if thisSpine.spineType != 'kern':
                    stavesAppliedTo = []
                    prioritiesToSearch = {}
                    for tandem in thisSpine.stream.flat.getElementsByClass('MiscTandem'):
                        if tandem.tandem.startswith('*staff'):
                            staffInfo = tandem.tandem[6:] # could be multiple staves
                            stavesAppliedTo = [int(x) for x in staffInfo.split('/')]
                            break
                    if thisSpine.spineType == 'dynam':
                        for dynamic in thisSpine.stream.flat:
                            if 'Dynamic' in dynamic.classes:
                                prioritiesToSearch[dynamic.humdrumPosition] = dynamic
                        for applyStaff in stavesAppliedTo:
                            applyStream = kernStreams[applyStaff]
                            for el in applyStream.recurse():
                                if el.priority in prioritiesToSearch:
                                    try:
                                        el.activeSite.insert(el.offset, prioritiesToSearch[el.priority])
                                    except exceptions21.StreamException: # may appear twice because of voices...
                                        pass
                                        #el.activeSite.insert(el.offset, copy.deepcopy(prioritiesToSearch[el.priority]))
                    elif thisSpine.spineType == 'lyrics' or thisSpine.spineType == 'text':
                        for text in thisSpine.stream.flat:
                            if 'ElementWrapper' in text.classes:
                                prioritiesToSearch[text.humdrumPosition] = text.obj
                        for applyStaff in stavesAppliedTo:
                            applyStream = kernStreams[applyStaff]
                            for el in applyStream.recurse():
                                if el.priority in prioritiesToSearch:
                                    lyric = prioritiesToSearch[el.priority].contents
                                    el.lyric = lyric


    def makeVoices(self):
        '''
        make voices for each kernSpine -- why not just run
        stream.makeVoices() ? because we have more information
        here that lets us make voices more intelligently

        Should be done after measures have been made.
        '''
        for thisSpine in self.spines:
            if thisSpine.spineType == 'kern' and thisSpine.parentSpine == None:
                thisStream = thisSpine.stream
                for el in thisStream:
                    if 'Measure' in el.classes:
                        hasVoices = False
                        lowestVoiceOffset = 0
                        for mEl in el:
                            if 'voice1' in mEl.groups:
                                hasVoices = True
                                lowestVoiceOffset = mEl.offset
                                break
                        if hasVoices is True:
                            voices = [None for i in range(10)]
                            measureElements = el.elements
                            for mEl in measureElements:
                                mElGroups = mEl.groups
                                #print mEl, mElGroups
                                if len(mElGroups) > 0 and mElGroups[0].startswith('voice'):
                                    voiceName = mElGroups[0]
                                    voiceNumber = int(voiceName[5])
                                    voicePart = voices[voiceNumber]
                                    if voicePart is None:
                                        voices[voiceNumber] = stream.Voice()
                                        voicePart = voices[voiceNumber]
                                        voicePart.groups.append(voiceName)
                                    mElOffset = mEl.offset
                                    el.remove(mEl)
                                    voicePart._insertCore(mElOffset - lowestVoiceOffset, mEl)
                            #print voices
                            for voicePart in voices:
                                if voicePart is not None:
                                    #voicePart.show('text')
                                    voicePart.elementsChanged()
                                    el._insertCore(lowestVoiceOffset, voicePart)
                            el.elementsChanged()
                            #print el.number, "has voices at", lowestVoiceOffset


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
        self.events = common.defaultlist(lambda:None)
        self.lastEvents = common.defaultlist(lambda:None)
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

class HumdrumException(exceptions21.Music21Exception):
    '''
    General Exception class for problems relating to Humdrum
    '''
    pass

def hdStringToNote(contents):
    '''
    returns a :class:`~music21.note.Note` (or Rest or Unpitched, etc.)
    matching the current SpineEvent.
    Does not check to see that it is sane or part of a :samp:`**kern` spine, etc.


    New rhythmic extensions defined in
    http://wiki.humdrum.org/index.php/Rational_rhythms
    are fully implemented:


    >>> n = humdrum.spineParser.hdStringToNote("CC3%2")
    >>> n.duration.quarterLength
    Fraction(8, 3)
    >>> n.duration.fullName
    'Whole Triplet (2 2/3 QL)'

    >>> n = humdrum.spineParser.hdStringToNote("e-00.")
    >>> n.pitch
    <music21.pitch.Pitch E-4>
    >>> n.duration.quarterLength
    24.0
    >>> n.duration.fullName
    'Perfect Longa'

    >>> n = humdrum.spineParser.hdStringToNote("F#000")
    >>> n.duration.quarterLength
    32.0
    >>> n.duration.fullName
    'Imperfect Maxima'


    Note that this is one note in the time of a double-dotted quarter,
    not a double-dotted quarter-note triplet (incorrectly used in
    http://kern.ccarh.org/cgi-bin/ksdata?l=musedata/mozart/quartet&file=k421-01.krn&f=kern
    and the Josquin Research Project [JRP]
    but contradicts the specification in
    http://www.lib.virginia.edu/artsandmedia/dmmc/Music/Humdrum/kern_hlp.html#tuplets )

    >>> storedFlavors = humdrum.spineParser.flavors['JRP'] # DOCS_HIDE

    This is the default:
    >>> humdrum.spineParser.flavors['JRP'] = False

    >>> n = humdrum.spineParser.hdStringToNote("6..fff")
    >>> n.duration.quarterLength
    Fraction(7, 6)
    >>> n.duration.dots
    0
    >>> n.duration.tuplets[0].durationNormal.dots
    2

    If you want the incorrect definition, set humdrum.spineParser.flavors['JRP'] = True
    before calling converter.parse() or anything like that:

    >>> humdrum.spineParser.flavors['JRP'] = True
    >>> n = humdrum.spineParser.hdStringToNote("6..fff")
    >>> n.duration.quarterLength
    Fraction(7, 6)
    >>> n.duration.dots
    2
    >>> n.duration.tuplets[0].durationNormal.dots
    0

    >>> n = humdrum.spineParser.hdStringToNote("gg#q/LL")
    >>> n.duration
    <music21.duration.GraceDuration unlinked type:eighth quarterLength:0.0>
    >>> n.isGrace
    True

    >>> humdrum.spineParser.flavors['JRP'] = storedFlavors # DOCS_HIDE

    '''

    # http://www.lib.virginia.edu/artsandmedia/dmmc/Music/Humdrum/kern_hlp.html#kern

    # 3.2.1 -- pitch

    matchedNote = re.search("([a-gA-G]+)", contents)

    thisObject = None
    if matchedNote:
        kernNoteName = matchedNote.group(1)
        step = kernNoteName[0].lower()
        if (step == kernNoteName[0]): ## middle C or higher
            octave = 3 + len(kernNoteName)
        else: # below middle C
            octave = 4 - len(kernNoteName)
        thisObject = note.Note(octave = octave)
        thisObject.step = step

    # 3.3 -- Rests
    elif contents.count("r"):
        thisObject = note.Rest()
    else:
        raise HumdrumException("Could not parse %s for note information" % contents)

    matchedSharp = re.search(r"(\#+)", contents)
    matchedFlat  = re.search(r"(\-+)", contents)

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
        thisObject.tie = tie.Tie("start")
    elif contents.count(']'):
        thisObject.tie = tie.Tie("stop")
    elif contents.count('_'):
        thisObject.tie = tie.Tie("continue")

    ## 3.2.3 Ornaments
    if contents.count('t'):
        thisObject.expressions.append(expressions.HalfStepTrill())
    elif contents.count('T'):
        thisObject.expressions.append(expressions.WholeStepTrill())

    if contents.count('w'):
        thisObject.expressions.append(expressions.HalfStepInvertedMordent())
    elif contents.count('W'):
        thisObject.expressions.append(expressions.WholeStepInvertedMordent())
    elif contents.count('m'):
        thisObject.expressions.append(expressions.HalfStepMordent())
    elif contents.count('M'):
        thisObject.expressions.append(expressions.WholeStepMordent())

    if contents.count('S'):
        thisObject.expressions.append(expressions.Turn())
    elif contents.count('$'):
        thisObject.expressions.append(expressions.InvertedTurn())
    elif contents.count('R'):
        t1 = expressions.Turn()
        t1.connectedToPrevious = True  ## true by default, but explicitly
        thisObject.expressions.append(t1)

    if contents.count(':'):
        ## TODO: deal with arpeggiation -- should have been in a
        ##  chord structure
        pass

    if contents.count("O"):
        thisObject.expressions.append(expressions.Ornament())
        # generic ornament

    # 3.2.4 Articulation Marks
    if contents.count('\''):
        thisObject.articulations.append(articulations.Staccato())
    if contents.count('"'):
        thisObject.articulations.append(articulations.Pizzicato())
    if contents.count('`'):
        # called 'attacca' mark but means staccatissimo:
        # http://www.music-cog.ohio-state.edu/Humdrum/representations/kern.rep.html
        thisObject.articulations.append(articulations.Staccatissimo())
    if contents.count('~'):
        thisObject.articulations.append(articulations.Tenuto())
    if contents.count('^'):
        thisObject.articulations.append(articulations.Accent())
    if contents.count(';'):
        thisObject.expressions.append(expressions.Fermata())


    # 3.2.5 Up & Down Bows
    if contents.count('v'):
        thisObject.articulations.append(articulations.UpBow())
    elif contents.count('u'):
        thisObject.articulations.append(articulations.DownBow())

    # 3.2.6 Stem Directions
    if contents.count('/'):
        thisObject.stemDirection = "up"
    elif contents.count('\\'):
        thisObject.stemDirection = "down"

    # 3.2.7 Duration +
    # 3.2.8 N-Tuplets

    ## TODO: SPEEDUP -- only search for rational after foundNumber...
    foundRational = re.search(r"(\d+)\%(\d+)", contents)
    foundNumber = re.search(r"(\d+)", contents)
    if foundRational:
        durationFirst = int(foundRational.group(1))
        durationSecond = float(foundRational.group(2))
        thisObject.duration.quarterLength = 4*durationSecond/durationFirst
        if contents.count('.'):
            thisObject.duration.dots = contents.count('.')

    elif foundNumber:
        durationType = int(foundNumber.group(1))
        if durationType == 0:
            durationString = foundNumber.group(1)
            if durationString == '000': # for larger values, see http://wiki.humdrum.org/index.php/Rational_rhythms
                thisObject.duration.type = 'maxima'
                if contents.count('.'):
                    thisObject.duration.dots = contents.count('.')
            elif durationString == '00': # for larger values, see http://wiki.humdrum.org/index.php/Rational_rhythms
                thisObject.duration.type = 'longa'
                if contents.count('.'):
                    thisObject.duration.dots = contents.count('.')
            else:
                thisObject.duration.type = 'breve'
                if contents.count('.'):
                    thisObject.duration.dots = contents.count('.')
        elif durationType in duration.typeFromNumDict:
            thisObject.duration.type = duration.typeFromNumDict[durationType]
            if contents.count('.'):
                thisObject.duration.dots = contents.count('.')
        else:
            dT = int(durationType) + 0.0
            (unused_remainder, exponents) = math.modf(math.log(dT, 2))
            basevalue = 2**exponents
            thisObject.duration.type = duration.typeFromNumDict[int(basevalue)]
            newTup = duration.Tuplet()
            newTup.durationActual = duration.durationTupleFromTypeDots(thisObject.duration.type, 0)
            newTup.durationNormal = duration.durationTupleFromTypeDots(thisObject.duration.type, 0)

            gcd = common.euclidGCD(int(dT), basevalue)
            newTup.numberNotesActual = int(dT/gcd)
            newTup.numberNotesNormal = int(float(basevalue)/gcd)

            # The Josquin Research Project uses an incorrect definition of
            # humdrum tuplets that breaks normal usage.  TODO: Refactor adding a Flavor = "JRP"
            # code that uses this other method...
            JRP = flavors['JRP']
            if JRP is False and contents.count('.'):
                newTup.durationNormal = duration.durationTupleFromTypeDots(newTup.durationNormal.type, contents.count('.'))

            thisObject.duration.appendTuplet(newTup)
            if JRP is True and contents.count('.'):
                thisObject.duration.dots = contents.count('.')
            # call Duration.TupletFixer after to correct this.

    # 3.2.9 Grace Notes and Groupettos
    if contents.count('q'):
        thisObject = thisObject.getGrace()
        thisObject.duration.type = 'eighth'
    elif contents.count('Q'):
        thisObject = thisObject.getGrace()
        thisObject.duration.slash = False
        thisObject.duration.type = 'eighth'
    elif contents.count('P'):
        thisObject = thisObject.getGrace(appogiatura=True)
    elif contents.count('p'):
        pass # end appogiatura duration -- not needed in music21...

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

def hdStringToMeasure(contents, previousMeasure = None):
    '''
    kern uses an equals sign followed by processing instructions to
    create new measures.  Here is how...
    '''
    m1 = stream.Measure()
    rematchMN = re.search(r"(\d+)([a-z]?)", contents)


    if rematchMN:
        m1.number = int(rematchMN.group(1))
        if rematchMN.group(2):
            m1.numberSuffix = rematchMN.group(2)

    #m1.setrightBarline()
    barline = bar.Barline()

    if contents.count('-'):
        barline.style = "none"
    elif contents.count('\''):
        barline.style = "short"
    elif contents.count('`'):
        barline.style = "tick"
    elif contents.count('||'):
        barline.style = "double"
        if contents.count(':') > 1:
            barline.repeat_dots = "both"
        elif contents.count(':|'):
            barline.repeat_dots = "left"
        elif contents.count('|:'):
            barline.repeat_dots = "right"
    elif contents.count('!!'):
        barline.style = "heavy-heavy"
        if contents.count(':') > 1:
            barline.repeat_dots = "both"
        elif contents.count(':!'):
            barline.repeat_dots = "left"
        elif contents.count('!:'):
            barline.repeat_dots = "right"
    elif contents.count('|!'):
        barline.style = "final"
        if contents.count(':') > 1:
            barline.repeat_dots = "both"
        elif contents.count(':|'):
            barline.repeat_dots = "left"
        elif contents.count('!:'):
            barline.repeat_dots = "right"
    elif contents.count('!|'):
        barline.style = "heavy-light"
        if contents.count(':') > 1:
            barline.repeat_dots = "both"
        elif contents.count(':!'):
            barline.repeat_dots = "left"
        elif contents.count('|:'):
            barline.repeat_dots = "right"
    elif contents.count('|'):
        barline.style = "regular"
        if contents.count(':') > 1:
            barline.repeat_dots = "both"
        elif contents.count(':|'):
            barline.repeat_dots = "left"
        elif contents.count('|:'):
            barline.repeat_dots = "right"
    elif contents.count('=='):
        barline.style = "double"
        if contents.count(':') > 1:
            barline.repeat_dots = "both"
            ## cannot specify single repeat dots without styles
        if contents == "==|":
            raise HumdrumException \
                ("Cannot import a double bar visually rendered as a single bar -- not sure exactly what that would mean anyhow.")

    if contents.count(';'):
        barline.pause = expressions.Fermata()


    if previousMeasure is not None:
        previousMeasure.rightBarline = barline
    else:
        m1.leftBarline = barline


    return m1


def kernTandemToObject(tandem):
    '''
    Kern uses symbols such as :samp:`*M5/4` and :samp:`*clefG2`, etc., to control processing

    This method converts them to music21 objects.


    >>> m = humdrum.spineParser.kernTandemToObject('*M3/1')
    >>> m
    <music21.meter.TimeSignature 3/1>


    Unknown objects are converted to MiscTandem objects:

    >>> m2 = humdrum.spineParser.kernTandemToObject('*TandyUnk')
    >>> m2
    <music21.humdrum.spineParser.MiscTandem *TandyUnk humdrum control>
    '''
    # TODO: Cover more tandem controls as they're found
    if tandem in spinePathIndicators:
        return None
    elif tandem.startswith("*clef"):
        clefType = tandem[5:]
        if clefType == "-":
            return clef.NoClef()
        elif clefType == "X":
            return clef.PercussionClef()
        elif clefType == "Gv2": # undocumented in Humdrum, but appears in Huron's Chorales
            return clef.Treble8vbClef()
        elif clefType == "Gv": # unknown if ever used but better safe...
            return clef.Treble8vbClef()
        elif clefType == "G^2": # unknown if ever used but better safe...
            return clef.Treble8vaClef()
        elif clefType == "G^": # unknown if ever used but better safe...
            return clef.Treble8vaClef()
        elif clefType == "Fv4": # unknown if ever used but better safe...
            return clef.Bass8vbClef()
        elif clefType == "Fv": # unknown if ever used but better safe...
            return clef.Bass8vbClef()
        else:
            try:
                clefifier = clef.clefFromString(clefType)
                return clefifier
            except clef.ClefException:
                raise HumdrumException("Unknown clef type %s found", tandem)
    elif tandem.startswith("*MM"):
        metronomeMark = tandem[3:]
        try:
            metronomeMark = float(metronomeMark)
            MM = tempo.MetronomeMark(number=metronomeMark)
            return MM
        except ValueError:
            # assuming that metronomeMark here is text now
            metronomeMark = re.sub(r'^\[','', metronomeMark)
            metronomeMark = re.sub(r']\s*$','', metronomeMark)
            MS = tempo.MetronomeMark(text=metronomeMark)
            return MS
    elif tandem.startswith("*M"):
        meterType = tandem[2:]
        tsTemp = re.match(r'(\d+)/(\d+)', meterType)
        if (tsTemp):
            numerator = int(tsTemp.group(1))
            denominator = tsTemp.group(2)
            if (denominator not in ('0', '00', '000')):
                return meter.TimeSignature(meterType)
            else:
                if (denominator == '0'):
                    numerator *= 2
                    denominator = 1
                elif (denominator == '00'):
                    numerator *= 4
                    denominator = 1
                elif (denominator == '000'):
                    numerator *= 8
                    denominator = 1
                return meter.TimeSignature('%d/%d' % (numerator, denominator))
        else:
            raise HumdrumException('Incorrect meter: %s found', tandem)
        
    elif tandem.startswith("*IC"):
        instrumentClass = tandem[3:]
        try:
            iObj = instruments.fromHumdrumClass(instrumentClass)
            return iObj
        except instruments.HumdrumInstrumentException:
            return MiscTandem(instrumentClass)
    elif tandem.startswith("*IG"):
        #instrumentGroup = tandem[3:]
        return MiscTandem(tandem)
        # TODO: DO SOMETHING WITH INSTRUMENT GROUP; not in hum2xml
    elif tandem.startswith("*ITr"):
        #instrumentTransposing = True
        return MiscTandem(tandem)
        # TODO: DO SOMETHING WITH TRANSPOSING INSTRUMENTS; not in hum2xml
    elif tandem.startswith("*I"): # order has to be last
        instrument = tandem[2:]
        try:
            iObj = instruments.fromHumdrumInstrument(instrument)
            return iObj
        except instruments.HumdrumInstrumentException:
            return MiscTandem(instrument)
    elif tandem.startswith("*k"):
        numSharps = tandem.count('#')
        if numSharps == 0:
            numSharps = -1 * (tandem.count('-'))
        return key.KeySignature(numSharps)
    elif tandem.endswith(":"):
        thisKey = tandem[1:-1]
        return key.Key(thisKey)
    else:
        return MiscTandem(tandem)

#    elif tandem.startswith("*>"):
#        # TODO: Something with 4.2 Repetitions; not in hum2xml
#        pass
#    elif tandem.startswith("*tb"):
#        timeBase = tandem[4:]
#        # TODO: Findout what timeBase means; not in hum2xml
#        pass
#    elif tandem.startswith("*staff"):
#        staffNumbers = tandem[6:]
#        # TODO: make staff numbers relevant; not in hum2xml

# TODO: Parse editorial signifiers


class MiscTandem(base.Music21Object):
    def __init__(self, tandem = ""):
        base.Music21Object.__init__(self)
        self.tandem = tandem
    def __repr__(self):
        return "<music21.humdrum.spineParser.MiscTandem %s humdrum control>" % self.tandem

class SpineComment(base.Music21Object):
    '''
    A Music21Object that represents a comment in a single spine.


    >>> sc = humdrum.spineParser.SpineComment('! this is a spine comment')
    >>> sc
    <music21.humdrum.spineParser.SpineComment "this is a spine comment">
    >>> sc.comment
    'this is a spine comment'
    '''

    def __init__(self, comment = ""):
        base.Music21Object.__init__(self)
        commentPart = re.sub(r'^\!+\s?','', comment)
        self.comment = commentPart

    def __repr__(self):
        return '<music21.humdrum.spineParser.SpineComment "%s">' % self.comment

class GlobalComment(base.Music21Object):
    '''
    A Music21Object that represents a comment for the whole score


    >>> sc = humdrum.spineParser.GlobalComment('!! this is a global comment')
    >>> sc
    <music21.humdrum.spineParser.GlobalComment "this is a global comment">
    >>> sc.comment
    'this is a global comment'
    '''

    def __init__(self, comment = ""):
        base.Music21Object.__init__(self)
        commentPart = re.sub(r'^\!\!+\s?','', comment)
        commentPart = commentPart.strip()
        self.comment = commentPart

    def __repr__(self):
        return '<music21.humdrum.spineParser.GlobalComment "%s">' % self.comment

class GlobalReference(base.Music21Object):
    '''
    A Music21Object that represents a reference in the score


    >>> sc = humdrum.spineParser.GlobalReference('!!!REF:this is a global reference')
    >>> sc
    <music21.humdrum.spineParser.GlobalReference REF "this is a global reference">
    >>> sc.code
    'REF'
    >>> sc.value
    'this is a global reference'

    Alternate form

    >>> sc = humdrum.spineParser.GlobalReference('REF', 'this is a global reference')
    >>> sc
    <music21.humdrum.spineParser.GlobalReference REF "this is a global reference">
    >>> sc.code
    'REF'
    >>> sc.value
    'this is a global reference'

    '''

    def __init__(self, codeOrAll = "", valueOrNone = None):
        base.Music21Object.__init__(self)
        codeOrAll = re.sub(r'^\!\!\!+','', codeOrAll)
        codeOrAll = codeOrAll.strip()
        if valueOrNone is None and ':' in codeOrAll:
            valueOrNone = re.sub(r'^.*?\:','', codeOrAll)
            codeOrAll = re.sub(r'\:.*$', '', codeOrAll)
        self.code = codeOrAll
        self.value = valueOrNone

    def __repr__(self):
        return '<music21.humdrum.spineParser.GlobalReference %s "%s">' % (self.code, self.value)


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
    #        print "\n\n***NEW SPINE: No. " + str(mySpine.id) + " parentSpine: " \
    #            + str(mySpine.parentSpine) + " childSpines: " + str(mySpine.childSpines)
    #        print mySpine.spineType
    #        for childSpinesSpine in mySpine.childSpinesSpines():
    #            print str(childSpinesSpine.id) + " *** testing spineCollection code ***"
    #        for thisEvent in mySpine:
    #            print thisEvent.contents
        spine5 = hf1.spineCollection.getSpineById(5)
        self.assertEqual(spine5.id, 5)
        self.assertEqual(spine5.parentSpine.id, 1)

        spine1 = hf1.spineCollection.getSpineById(1)
        spine1Children = [cs.id for cs in spine1.childSpines]
        self.assertEqual(spine1Children, [5, 6, 9, 10, 13, 14, 23, 24, 27, 28, 31, 32, 35, 36, 39, 40])

        self.assertEqual(spine5.spineType, "kern")
        self.assertTrue(isinstance(spine5, KernSpine))

    def testSingleNote(self):
        a = SpineEvent("40..ccccc##_wtLLK~v/")
        b = a.toNote()
        self.assertEqual(b.pitch.accidental.name, "double-sharp")
        self.assertEqual(b.duration.dots, 0)
        self.assertEqual(b.duration.tuplets[0].durationNormal.dots, 2)

    def testMeasureBoundaries(self):
        m0 = stream.Measure()
        m1 = hdStringToMeasure("=29a;:|:", m0)
        self.assertEqual(m1.number, 29)
        self.assertEqual(m1.numberSuffix, "a")
        self.assertEqual(m0.rightBarline.style, "regular")
        self.assertEqual(m0.rightBarline.repeat_dots, "both")
        assert m0.rightBarline.pause is not None
        assert isinstance(m0.rightBarline.pause, expressions.Fermata)

    def testMeterBreve(self):
        m = kernTandemToObject("*M3/1")
        self.assertEqual(str(m), '<music21.meter.TimeSignature 3/1>')
        m = kernTandemToObject("*M3/0")
        self.assertEqual(str(m), '<music21.meter.TimeSignature 6/1>')
        m = kernTandemToObject("*M3/00")
        self.assertEqual(str(m), '<music21.meter.TimeSignature 12/1>')
        m = kernTandemToObject("*M3/000")
        self.assertEqual(str(m), '<music21.meter.TimeSignature 24/1>')
        

    def xtestFakePiece(self):
        '''
        test loading a fake piece with spine paths, lyrics, dynamics, etc.
        '''
        ms = HumdrumDataCollection(testFiles.fakeTest).stream
        ms.show()

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
#        self.assertTrue(common.basicallyEqual
#                          (common.stripAddresses(expectedOutput),
#                           common.stripAddresses(masterStream._reprText())))
#        print common.stripAddresses(expectedOutput)
#       print common.stripAddresses(masterStream.recurseRepr())

        # humdrum type problem: how many G#s start on beat 2 of a measure?
        GsharpCount = 0
        #masterStream.show('text')
        for n in masterStream.recurse():
            if hasattr(n, "pitch") and n.pitch.name == "G#":
                if n.beat == 2: # beat doesn't work... :-(
                    GsharpCount += 1
            elif hasattr(n, "pitches"):
                for p in n.pitches:
                    if p.name == 'G#' and n.beat == 2:
                        GsharpCount += 1
        #masterStream.show()
        self.assertEqual(GsharpCount, 86)
#        masterStream.show()

#       masterStream.show('text')

    def testParseSineNomine(self):
        from music21 import converter
        parserPath = common.getSourceFilePath() + os.path.sep + 'humdrum'
        sineNominePath = parserPath + os.path.sep + 'Missa_Sine_nomine-Kyrie.krn'
        unused_myScore = converter.parse(sineNominePath)
        #unused_myScore.show('text')

    def testSplitSpines(self):
        hf1 = HumdrumDataCollection(testFiles.splitSpines2)
        unused_masterStream = hf1.stream
        #masterStream.show('text')

    def testMoveDynamics(self):
        hf1 = HumdrumDataCollection(testFiles.fakeTest)
        #hf1.parseLines()
        #hf1.spineCollection.moveDynamicsAndLyricsToStreams()
        unused_s = hf1.stream #.show()

    def testSpineComments(self):
        hf1 = HumdrumDataCollection(testFiles.fakeTest)
        hf1.parseLines()
        s = hf1.stream #.show()
        p = s.parts[2] # last part has a comment
        comments = []
        for c in p.flat.getElementsByClass('SpineComment'):
            comments.append(c.comment)
        self.assertTrue('spine comment' in comments)
        #s.show('text')

    def testFlavors(self):
        prevFlavor = flavors['JRP']
        flavors['JRP'] = False
        c = HumdrumDataCollection(testFiles.dottedTuplet).stream
        flavors['JRP'] = True
        d = HumdrumDataCollection(testFiles.dottedTuplet).stream
        flavors['JRP'] = prevFlavor
        cn = c.parts[0].measure(1).notes[1]
        dn = d.parts[0].measure(1).notes[1]
        self.assertEqual(cn.duration.fullName, 'Eighth Triplet (1/2 QL)')
        self.assertEqual(cn.duration.dots, 0)
        self.assertEqual(repr(cn.duration.tuplets[0].durationNormal), 
                         "DurationTuple(type='eighth', dots=1, quarterLength=0.75)")
        self.assertEqual(cn.duration.tuplets[0].durationNormal.dots, 1)
        self.assertEqual(dn.duration.fullName, 'Dotted Eighth Triplet (1/2 QL)')
        self.assertEqual(dn.duration.dots, 1)
        self.assertEqual(repr(dn.duration.tuplets[0].durationNormal), 
                         "DurationTuple(type='eighth', dots=0, quarterLength=0.5)")
        self.assertEqual(dn.duration.tuplets[0].durationNormal.dots, 0)
        
class TestExternal(unittest.TestCase):

    def runTest(self):
        pass

    def testShowSousa(self):
        hf1 = HumdrumDataCollection(testFiles.sousaStars)
        hf1.stream.show()


if __name__ == "__main__":
    #Test().testMoveDynamics()
    import music21
    #c = music21.converter.parse(r'd:\desktop\b5-new.krn')
    #c.show()
    music21.mainTest(Test) #, TestExternal)

#------------------------------------------------------------------------------
# eof

