# ------------------------------------------------------------------------------
# Name:         humdrum.spineParser.py
# Purpose:      Conversion and Utility functions for Humdrum and kern in particular
#
# Authors:      Michael Scott Asato Cuthbert
#
# Copyright:    Copyright © 2009-2026 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
music21.humdrum.spineParser is a collection of utilities for changing
native Humdrum code into music21 streams.  Most music21 users will
simply want to call:

>>> #_DOCS_SHOW myFile = converter.parse('myFile.krn')
>>> #_DOCS_SHOW myFile.show()

The methods in here are documented for developers wishing to expand
music21's ability to parse humdrum.

SpineParsing consists of several steps.

* The data file is read in and all events are sliced horizontally (EventCollections)
    and vertically (Protospines)
* Protospines are parsed into HumdrumSpines by following Spine Path Indicators
    (:samp:`*^` and :samp:`*v` especially)
    Protospines that separate become new Protospines with their parentSpine indicated.  Protospines
    that merge again are then followed by the same Protospine as before.  This will cause problems
    if a voice re-merges with another staff, but in practice I have not
    seen a .krn file that does this and
    should be avoided in any case.
* HumdrumSpines are reclassed according to their exclusive definition.
    :samp:`**kern` becomes KernSpines, etc.
* All reclassed HumdrumSpines are filled with music21 objects in their .stream property.
    Measures are put into the spine but are empty containers.  The resulting
    HumdrumSpine.stream objects
    look like `Stream.flatten(retainContainers=True)` versions in many ways.
* For HumdrumSpines with parent spines their .stream contents are then
    inserted into their parent spines with
    voice tagged as a music21 Group property.
* Lyrics and Dynamics are placed into their corresponding HumdrumSpine.stream objects.
* Stream elements are moved into their measures within a Stream.
* Measures are searched for elements with voice groups and Voice objects are created.

* Changed in v10: flag attributes `isSpineLine, isComment, isGlobal, isReference` have been
    removed from HumdrumLine and all subclasses. `isinstance(...)` is a bit slower than
    checking these, but adds correct typing.  Nothing is stored with weakrefs.  `.iterIndex`
    and hand rolled iterator/generators are gone now (could've gone when Python 2.4 became
    the minimum version).  `HumdrumDataCollection.parsePositionInStream` is gone (was
    duplicating `numLines`); `HumdrumDataCollection.fileLength` is now the read-only
    property `numLines` (= `len(self.dataStream)`); `HumdrumLine.position` and
    `SpineEvent.position` were both renamed to `lineNumber` and now hold the 1-based
    source line number (was eventList index for SpineEvent),
    advancing on blank lines too.  Blank lines now produce `BlankLine` HumdrumLine
    entries rather than being skipped, so `eventList[lineNumber - 1]` always
    resolves to the line at that source position.
'''
from __future__ import annotations

import copy
import math
import re
import typing as t
import unittest
import weakref

from music21.common.numberTools import opFrac
from music21.common.types import OffsetQL

from music21 import articulations
from music21 import bar
from music21 import base
from music21 import chord
from music21 import clef
from music21 import common
from music21 import dynamics
from music21 import duration
from music21 import environment
from music21 import exceptions21
from music21 import expressions
from music21 import instrument
from music21 import key
from music21 import note
from music21 import meter
from music21 import metadata
from music21 import roman
from music21 import pitch
from music21 import prebase
from music21 import stream
from music21 import tempo
from music21 import tie
from music21.duration import GraceDuration

from music21.humdrum import harmParser
from music21.humdrum import instruments

if t.TYPE_CHECKING:
    import pathlib

environLocal = environment.Environment('humdrum.spineParser')

flavors = {'JRP': False}

spinePathIndicators = ['*+', '*-', '*^', '*v', '*x', '*']


class HumdrumException(exceptions21.Music21Exception):
    '''
    General Exception class for problems relating to Humdrum
    '''
    pass


class HumdrumDataCollection(prebase.ProtoM21Object):
    r'''
    .. note:: Most users should not need to be here.  Just run `converter.parse('file.krn')`
        and it will give you a stream.Score instead.
        Intermediate users who want to get into the guts of Humdrum are still
        probably better off running humdrum.parseFile("filename")
        which returns a humdrum.SpineCollection directly.

    A HumdrumDataCollection takes in a mandatory list where each element
    is a line of Humdrum data.  Together this list represents a collection
    of spines.  Essentially it's the contents of a Humdrum file.

    Usually you will probably want to use HumdrumFile which can read
    in a file directly.  This class exists in case you have your Humdrum
    data in another format (database, from the web, etc.) and already
    have it as a string.

    LIMITATIONS:
    (1) Spines cannot change definition (\*\*exclusive interpretations) mid-spine.

        So if you start off with \*\*kern, the rest of the spine needs to be
        \*\*kern (actually, the first exclusive interpretation for a spine is
        used throughout).

        Note that, even though changing exclusive interpretations mid-spine
        seems to be legal by the Humdrum definition, it looks like none of the
        conventional Humdrum parsing tools allow for changing
        definitions mid-spine, so I don't think this limitation is a problem.
        (Craig Stuart Sapp confirmed this to me.)

        The Aarden/Miller Palestrina dataset uses `\*-` followed by `\*\*kern`
        at the changes of sections thus some parsing of multiple exclusive
        interpretations in a protospine may be necessary.  But none change definition.

    (2) Split spines are assumed to be voices in a single spine staff.
    '''

    def __init__(self, dataStream: str|list[str]) -> None:
        # attributes
        self.eventList: list[HumdrumLine] = []
        self.maxSpines: int = 0
        self.protoSpines: list[ProtoSpine] = []
        self.eventCollections: list[EventCollection] = []
        self.spineCollection: SpineCollection|None = None

        if isinstance(dataStream, str):
            dataStream = dataStream.splitlines()

        self.dataStream: list[str] = dataStream
        # Defaults to a Score; parseOpusDataCollections will replace it with
        # an Opus if the input turns out to be a multipart file.
        self.stream: stream.Score|stream.Opus = stream.Score()

    @property
    def numLines(self) -> int:
        '''
        The number of lines in `self.dataStream`, including blank lines.
        '''
        return len(self.dataStream)

    def parse(self) -> stream.Score|stream.Opus:
        '''
        Parse `self.dataStream` into music21 objects, returning the resulting
        :class:`~music21.stream.Score` (or :class:`~music21.stream.Opus`
        for multipart files like the Palestrina dataset).

        The parsed stream is also stored on `self.stream`.
        '''
        if not self.dataStream:
            raise HumdrumException('Need a list of lines (dataStream) to parse!')

        hasOpus, dataCollections = self.determineIfDataStreamIsOpus(self.dataStream)
        if hasOpus and dataCollections is not None:
            # True for the Palestrina data collection, maybe others
            return self.parseOpusDataCollections(dataCollections)
        else:
            return self.parseNonOpus(self.dataStream)

    def parseNonOpus(self, dataStream: list[str]) -> stream.Score:
        '''
        The main parse function for non-opus data collections.

        Populates `self.stream` (a :class:`~music21.stream.Score`) and returns it.
        '''
        # Reset to a fresh Score in case parse() is called more than once.
        score = stream.Score()
        self.stream = score
        self.maxSpines = 0

        # parse global comments and figure out the maximum number of spines we will have
        self.parseEventListFromDataStream(dataStream)  # sets self.eventList
        self.parseProtoSpinesAndEventCollections()
        self.spineCollection = self.createHumdrumSpines()
        self.spineCollection.createMusic21Streams()
        self.insertGlobalEvents()
        for thisSpine in self.spineCollection:
            thisSpine.stream.id = 'spine_' + str(thisSpine.id)
        for thisSpine in self.spineCollection:
            if thisSpine.parentSpine is None and thisSpine.spineType == 'kern':
                score.insert(thisSpine.stream)

        self.parseMetadata()
        return score

    # noinspection SpellCheckingInspection
    def determineIfDataStreamIsOpus(
        self,
        dataStream: list[str]|None = None,
    ) -> tuple[bool, list[list[str]]|None]:
        # noinspection PyShadowingNames
        r'''
        Some Humdrum files contain multiple pieces in one file
        which are better represented as an :class:`~music21.stream.Opus`
        file containing multiple scores.

        This method examines the dataStream (or `self.dataStream`) and
        if it only has a single piece then it returns (False, None).

        If it has multiple pieces, it returns True and a list of dataStreams.

        >>> from pprint import pprint as pp

        >>> mps = humdrum.testFiles.multipartSanctus
        >>> hdc = humdrum.spineParser.HumdrumDataCollection(mps)
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

        if dataStream is None:  # pragma: no cover
            raise TypeError('dataStream cannot be None')

        startIndices = []
        endIndices = []
        for i, line in enumerate(dataStream):
            line = line.rstrip()
            if re.search(r'^(\*-\t)*\*-$', line):
                endIndices.append(i)
            elif re.search(r'^(\*\*\w+\t)*\*\*\w+$', line):
                startIndices.append(i)
        if len(startIndices) < 2:
            return (False, None)
        if endIndices[-1] > startIndices[-1]:
            # properly formed .krn with *- at end
            pass
        else:
            # improperly formed .krn without *- at end
            endIndices.append(len(dataStream))

        dataCollections = []
        for i in range(len(endIndices)):
            if i == 0:
                endPos = endIndices[i]
                dataCollections.append(dataStream[:endPos + 1])
            elif i == len(endIndices) - 1:
                # ignore endPosition and grab to end of file
                startIndex = endIndices[i - 1] + 1
                dataCollections.append(dataStream[startIndex:])
            else:
                # ignore startIndices, grab comments etc. between scores
                startIndex = endIndices[i - 1] + 1
                endIndex = endIndices[i] + 1
                dataCollections.append(dataStream[startIndex:endIndex])

        if len(dataCollections) > 1:
            return (True, dataCollections)
        else:
            raise HumdrumException(
                'Malformed Humdrum data: '
                + 'possibly multiple **tags without closing information. Or a *tandem tag '
                + 'accidentally encoded as a **spine tag.')

    def parseOpusDataCollections(self, dataCollections: list[list[str]]) -> stream.Opus:
        # noinspection PyShadowingNames
        '''
        Take a dataCollection from `determineIfDataStreamIsOpus`
        and set `self.stream` to be an Opus instead.

        >>> mps = humdrum.testFiles.multipartSanctus
        >>> hdc = humdrum.spineParser.HumdrumDataCollection(mps)
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
            sc = hdc.parse()
            sc.id = 'section_' + str(i + 1)
            sc.metadata.number = i + 1
            opus.append(sc)

        if dataCollections:
            opus.metadata = copy.deepcopy(opus.scores[0].metadata)
            opus.metadata.number = 0

        self.stream = opus
        return opus

    def parseEventListFromDataStream(
        self,
        dataStream: list[str]|None = None,
    ) -> list[HumdrumLine]:
        r'''
        Sets `self.eventList` from a dataStream (that is, a
        list of lines).  It sets `self.maxSpines` to the
        largest number of spine events found on any line
        in the file.

        The differences between the dataStream and `self.eventList`
        are the following:

            * Blank lines become :class:`~music21.humdrum.spineParser.BlankLine` objects
            * !!! lines become :class:`~music21.humdrum.spineParser.GlobalReferenceLine` objects
            * !! lines become :class:`~music21.humdrum.spineParser.GlobalCommentLine` objects
            * all other lines become :class:`~music21.humdrum.spineParser.SpineLine` objects

        Returns eventList in addition to setting it as `self.eventList`.

        >>> eventString = ('!!! COM: Beethoven, Ludwig van\n'
        ...                '!! Not really a piece by Beethoven\n'
        ...                '**kern\t**dynam\n'
        ...                'C4\tpp\n'
        ...                'D8\t.\n')
        >>> hdc = humdrum.spineParser.HumdrumDataCollection(eventString)
        >>> hdc.maxSpines = 2
        >>> eList = hdc.parseEventListFromDataStream()
        >>> eList is hdc.eventList
        True
        >>> for e in eList:
        ...     print(e)
        <music21.humdrum.spineParser.GlobalReferenceLine COM: 'Beethoven, Ludwig van'>
        <music21.humdrum.spineParser.GlobalCommentLine 'Not really a piece by Beethoven'>
        <music21.humdrum.spineParser.SpineLine line 3 (2 spines)>
        <music21.humdrum.spineParser.SpineLine line 4 (2 spines)>
        <music21.humdrum.spineParser.SpineLine line 5 (2 spines)>
        >>> print(eList[0].value)
        Beethoven, Ludwig van

        Print line number 4 (which is eList[3] in zero indexed)

        >>> print(eList[3].spineData)
        ['C4', 'pp']
        '''
        if dataStream is None:
            dataStream = self.dataStream
            if dataStream is None:
                raise HumdrumException('Need a list of lines (dataStream) to parse!')

        self.eventList = []
        lineNumber = 0  # 1-based file line number; advances on blanks too

        for line in dataStream:
            lineNumber += 1
            line = line.rstrip()
            if line == '':
                # Humdrum forbids blanks, but they appear in real files; keep
                # eventList aligned with the source so eventList[n-1] is line n.
                self.eventList.append(BlankLine(lineNumber))
            elif re.match(r'!!!', line):
                self.eventList.append(GlobalReferenceLine(lineNumber, line))
            elif re.match(r'!!', line):  # find global comments at the top of the line
                self.eventList.append(GlobalCommentLine(lineNumber, line))
            else:
                thisLine = SpineLine(lineNumber, line)
                self.maxSpines = max(self.maxSpines, thisLine.numSpines)
                self.eventList.append(thisLine)
        return self.eventList

    def parseProtoSpinesAndEventCollections(
        self,
    ) -> tuple[list[ProtoSpine], list[EventCollection]]:
        r'''
        Run after
        :meth:`~music21.humdrum.spineParser.HumdrumDataCollection.parseEventListFromDataStream()`
        to take `self.eventList` and slice it horizontally
        to get `self.eventCollections`, which is a list of
        EventCollection objects, or things that happen simultaneously.

        And, more importantly, this method slices `self.eventList`
        vertically to get `self.protoSpines` which is a list
        of ProtoSpines, that is a vertical slice of everything that
        happens in a column, regardless of spine-path indicators.

        EventCollection objects store global events. ProtoSpines do not.

        So `self.eventCollections` and `self.protoSpines` can each be
        thought of as a two-dimensional sheet of cells, but where
        the first index of the former is the vertical index in
        the dataStream and the first index of the latter is the
        horizontal index in the dataStream.  The contents of
        each cell is a SpineEvent object or None (if there's no
        data at that point).  Even '.' (continuation events) get
        translated into SpineEvent objects.

        Calls :meth:`~music21.humdrum.spineParser.parseEventListFromDataStream`
        if it hasn't already been called.

        Returns a tuple of protoSpines and eventCollections in addition to
        setting it in the calling object.

        >>> eventString = ('!!!COM: Beethoven, Ludwig van\n'
        ...                '!! Not really a piece by Beethoven\n'
        ...                '**kern\t**dynam\n'
        ...                'C4\tpp\n'
        ...                'D8\t.\n')
        >>> hdc = humdrum.spineParser.HumdrumDataCollection(eventString)
        >>> hdc.maxSpines = 2
        >>> protoSpines, eventCollections = hdc.parseProtoSpinesAndEventCollections()
        >>> protoSpines is hdc.protoSpines
        True
        >>> eventCollections is hdc.eventCollections
        True

        Looking at individual slices is unlikely to tell you much:

        >>> for thisSlice in eventCollections:
        ...    print(thisSlice)
        <music21.humdrum.spineParser.EventCollection line 1, 2 events, 2 spines>
        <music21.humdrum.spineParser.EventCollection line 2, 2 events, 2 spines>
        <music21.humdrum.spineParser.EventCollection line 3, 2 events, 2 spines>
        <music21.humdrum.spineParser.EventCollection line 4, 2 events, 2 spines>
        <music21.humdrum.spineParser.EventCollection line 5, 2 events, 2 spines>

        >>> for thisSlice in protoSpines:
        ...    print(thisSlice)
        <music21.humdrum.spineParser.ProtoSpine 5 events>
        <music21.humdrum.spineParser.ProtoSpine 5 events>

        But looking at the individual slices is revealing:

        >>> eventCollections[4].getAllOccurring()
        [<music21.humdrum.spineParser.SpineEvent D8>, <music21.humdrum.spineParser.SpineEvent pp>]

        >>> for protoEvent in protoSpines[0]:
        ...    print(repr(protoEvent))
        None
        None
        <music21.humdrum.spineParser.SpineEvent **kern>
        <music21.humdrum.spineParser.SpineEvent C4>
        <music21.humdrum.spineParser.SpineEvent D8>
        '''
        if not self.eventList:
            self.parseEventListFromDataStream()

        # we make two lists: one of ProtoSpines (vertical slices) and
        # one of Events(horizontal slices)
        returnProtoSpines: list[ProtoSpine] = []
        returnEventCollections: list[EventCollection] = []

        # noinspection PyShadowingNames
        def processEventForOneCell(i: int, j: int) -> SpineEvent|None:
            '''
            Process the (i, j) cell.  Mutates `returnEventCollections[i]`
            and returns the SpineEvent to record in the protoSpine, or
            None if there's no event at this cell.
            '''
            thisEventCollection = returnEventCollections[i]
            currentLine = self.eventList[i]

            if isinstance(currentLine, SpineLine) and len(currentLine.spineData) > j:
                # actual event at this cell
                thisEvent = SpineEvent(currentLine.spineData[j], currentLine.lineNumber)
                thisEvent.protoSpineId = j
                if thisEvent.contents in spinePathIndicators:
                    thisEventCollection.spinePathData = True
                thisEventCollection.addSpineEvent(j, thisEvent)
                if thisEvent.contents == '.' and i > 0:
                    lastEvent = returnEventCollections[i - 1].events[j]
                    if lastEvent is not None:
                        occurringEvent = returnEventCollections[i - 1].getSpineOccurring(j)
                        if occurringEvent is not None:
                            thisEventCollection.addLastSpineEvent(j, occurringEvent)
                return thisEvent

            # placeholder cell: either a SpineLine with no data this far over,
            # or a global line (GlobalComment, GlobalReference, or BlankLine).
            if not isinstance(currentLine, SpineLine) and j == 0:
                # not SpineLine = GlobalComment, GlobalReference, or BlankLine.
                # global events register once, against the first column
                thisEventCollection.addGlobalEvent(currentLine)
            placeholder = SpineEvent('', currentLine.lineNumber)
            placeholder.protoSpineId = j
            thisEventCollection.addSpineEvent(j, placeholder)
            return None

        numEvents = len(self.eventList)
        for j in range(self.maxSpines):
            protoSpineEventList: list[SpineEvent|None] = []
            for i in range(numEvents):
                if j == 0:
                    returnEventCollections.append(
                        EventCollection(self.maxSpines,
                                        lineNumber=self.eventList[i].lineNumber))
                protoSpineEventList.append(processEventForOneCell(i, j))
            returnProtoSpines.append(ProtoSpine(protoSpineEventList))

        self.protoSpines = returnProtoSpines
        self.eventCollections = returnEventCollections

        return (returnProtoSpines, returnEventCollections)

    def createHumdrumSpines(
        self,
        protoSpines: list[ProtoSpine]|None = None,
        eventCollections: list[EventCollection]|None = None,
    ) -> SpineCollection:
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
        if protoSpines is None or eventCollections is None:
            protoSpines = self.protoSpines
            eventCollections = self.eventCollections
        maxSpines = len(protoSpines)

        # currentSpineList is a list of currently active
        # spines ordered from left to right.
        currentSpineList = common.defaultlist(lambda: None)
        spineCollection = SpineCollection()

        # go through the event collections line by line
        for i in range(len(eventCollections)):
            thisEventCollection = eventCollections[i]
            lineNumber = thisEventCollection.lineNumber
            for j in range(maxSpines):
                thisEvent = protoSpines[j].eventList[i]

                if thisEvent is None:  # nothing there
                    continue

                currentSpine = currentSpineList[j]
                if currentSpine is None:
                    # first event after a None = new spine because
                    # Humdrum does not require *+ at the beginning
                    currentSpine = spineCollection.addSpine()
                    currentSpine.insertPoint = lineNumber
                    currentSpineList[j] = currentSpine

                currentSpine.append(thisEvent)
                # currentSpine.id is always unique in a spineCollection
                thisEvent.protoSpineId = currentSpine.id

            # check for spinePathData
            if not thisEventCollection.spinePathData:
                continue

            # note that nothing else can happen in an eventCollection
            # except spine path data if any spine has spine path data.
            # thus, this is illegal.  The C#4 will be ignored:
            # *x     *x     C#4

            newSpineList = common.defaultlist(lambda: None)

            # These are either False OR the spine being merged/exchanged.
            # TODO: separate the two concepts.
            mergerActive = False
            exchangeActive = False
            for j in range(maxSpines):
                thisEvent = protoSpines[j].eventList[i]
                currentSpine = currentSpineList[j]

                if thisEvent is None and currentSpine is not None:
                    # should this happen?
                    newSpineList.append(currentSpine)
                    continue
                elif thisEvent is None:
                    continue
                if thisEvent.contents == '*-':  # terminate spine
                    currentSpine.endingPoint = lineNumber
                elif thisEvent.contents == '*^':  # split spine assume they are voices
                    newSpine1 = spineCollection.addSpine(streamClass=stream.Voice)
                    newSpine1.insertPoint = lineNumber + 1
                    newSpine1.parentSpine = currentSpine
                    newSpine1.isFirstVoice = True
                    newSpine2 = spineCollection.addSpine(streamClass=stream.Voice)
                    newSpine2.insertPoint = lineNumber + 1
                    newSpine2.parentSpine = currentSpine
                    currentSpine.endingPoint = lineNumber  # overridden if merged
                    currentSpine.childSpines.append(newSpine1)
                    currentSpine.childSpines.append(newSpine2)

                    currentSpine.childSpineInsertPoints[lineNumber] = (newSpine1, newSpine2)
                    newSpineList.append(newSpine1)
                    newSpineList.append(newSpine2)
                elif thisEvent.contents == '*v':
                    # merge spine -- n.b. we allow non-adjacent
                    # lines to be merged. this is incorrect
                    # per Humdrum syntax, but is easily done.
                    if mergerActive is False:
                        # assume that previous spine continues
                        if currentSpine.parentSpine is not None:
                            mergerActive = currentSpine.parentSpine
                        else:
                            mergerActive = True
                        currentSpine.endingPoint = lineNumber
                    else:
                        # if second merger code is not found then
                        # a one-to-one spine 'merge' occurs
                        currentSpine.endingPoint = lineNumber
                        # merge back to parent if possible:
                        if currentSpine.parentSpine is not None:
                            newSpineList.append(currentSpine.parentSpine)
                        # or merge back to other spine's parent:
                        elif mergerActive is not True:  # other spine parent set
                            newSpineList.append(mergerActive)
                        # or make a new spine:
                        else:
                            s = spineCollection.addSpine(streamClass=stream.Part)
                            s.insertPoint = lineNumber
                            newSpineList.append(s)

                        mergerActive = False

                elif thisEvent.contents == '*x':  # exchange spine
                    if exchangeActive is False:
                        exchangeActive = currentSpine
                    else:
                        # if second exchange is not found, then both
                        # lines disappear and exception is raised
                        # n.b. we allow more than one PAIR of exchanges
                        # in a line so long as the first
                        # is totally finished by the time the second happens
                        newSpineList.append(currentSpine)
                        newSpineList.append(exchangeActive)
                        exchangeActive = False
                else:  # null processing code '*'
                    newSpineList.append(currentSpine)

            if exchangeActive is not False:
                raise HumdrumException('ProtoSpine found with unpaired exchange instruction '
                                       f'at line {lineNumber} [{thisEventCollection.events}]')
            currentSpineList = newSpineList

        return spineCollection

    def insertGlobalEvents(self) -> None:
        '''
        Insert the Global Events (GlobalReferenceLines and GlobalCommentLines) into an appropriate
        place in the outer Stream.

        Run after `self.spineCollection.createMusic21Streams()`.
        Is run automatically by `self.parse()`.
        uses `self.spineCollection.getOffsetsAndPrioritiesByLineNumber()`
        '''
        spineCollection = self.spineCollection
        if spineCollection is None:
            raise HumdrumException(
                'cannot insert global events: no spineCollection. '
                'Call parse() (or createHumdrumSpines() and parseMusic21()) first.')
        lineNumberDict = spineCollection.getOffsetsAndPrioritiesByLineNumber()
        eventList = self.eventList
        maxEventList = len(eventList)
        numberOfGlobalEventsInARow = 0
        insertList: list[tuple[OffsetQL, GlobalReference|GlobalComment]] = []
        appendList: list[GlobalReference|GlobalComment] = []

        for i, event in enumerate(eventList):
            if isinstance(event, (GlobalReferenceLine, GlobalCommentLine)):
                numberOfGlobalEventsInARow += 1
                insertOffset: OffsetQL|None = None
                insertPriority = 0
                for j in range(i + 1, maxEventList):
                    if j in lineNumberDict:
                        insertOffset = lineNumberDict[j][0]
                        # hopefully not more than 20 events in a row!
                        insertPriority = (lineNumberDict[j][1][0].priority
                                          - 40
                                          + numberOfGlobalEventsInARow)
                        break
                el: GlobalReference|GlobalComment
                if isinstance(event, GlobalReferenceLine):
                    # TODO: Fix GlobalReference (added in 2012; as of 2016 not sure what to fix)
                    #    might add language?
                    el = GlobalReference(event.code, event.value)
                else:
                    el = GlobalComment(event.value)
                el.priority = insertPriority
                if insertOffset is None:
                    appendList.append(el)
                else:
                    insertTuple = (insertOffset, el)
                    insertList.append(insertTuple)
                # self.stream.insert(insertOffset, el)
            else:
                numberOfGlobalEventsInARow = 0

        for offset, el in insertList:
            self.stream.coreInsert(offset, el)

        if insertList:
            self.stream.coreElementsChanged()

        for el in appendList:
            self.stream.coreAppend(el)

        if appendList:
            self.stream.coreElementsChanged()

    # @property
    # def stream(self):
    #     if self._storedStream is not None:
    #         return self._storedStream
    #     if self.parsedLines is False:
    #         self.parse()
    #
    #     if self.spineCollection is None:
    #         raise HumdrumException('parsing got no spine collections!')
    #     elif self.spineCollection.spines is None:
    #         raise HumdrumException('not a single spine in your data. Is this your problem? '
    #                                '(File a bug report if you '
    #                                'have doubled checked your data)')
    #     elif self.spineCollection.spines[0].stream is None:
    #         raise HumdrumException('okay, you got at least one spine, but it does not have '
    #                                'a stream in it; (check your data or file a bug report)')
    #     else:
    #         masterStream = stream.Score()
    #         for thisSpine in self.spineCollection:
    #             thisSpine.stream.id = 'spine_' + str(thisSpine.id)
    #         for thisSpine in self.spineCollection:
    #             if thisSpine.parentSpine is None and thisSpine.spineType == 'kern':
    #                 masterStream.insert(thisSpine.stream)
    #         self._storedStream = masterStream
    #         return masterStream

    def parseMetadata(self, s: stream.Stream|None = None) -> None:
        '''
        Create a metadata object for the file.
        '''
        if s is None:
            s = self.stream
        md = metadata.Metadata()
        s.metadata = md
        grToRemove: list[GlobalReference] = []

        for gr in s[GlobalReference]:
            gr.updateMetadata(md)
            grToRemove.append(gr)

        if grToRemove:
            s.remove(grToRemove, recurse=True)


class HumdrumFile(HumdrumDataCollection):
    '''
    A HumdrumFile is a HumdrumDataCollection which takes
    as a mandatory argument a filename to be opened and read.
    '''

    def __init__(self, filename: str|pathlib.Path) -> None:
        super().__init__([])
        self.filename: str|pathlib.Path = filename

    def parseFilename(self, filename: str|pathlib.Path|None = None) -> None:
        if filename is None:
            filename = self.filename

        with open(filename, encoding='latin-1') as humFH:
            self.parseFileHandle(humFH)
        # might raise IOError

    def parseFileHandle(self, fileHandle: t.Iterable[str]) -> stream.Score|stream.Opus:
        '''
        Read all lines from `fileHandle` into ``self.dataStream``, then call
        :meth:`parse` and return its result (a :class:`~music21.stream.Score`
        or :class:`~music21.stream.Opus`).
        '''
        spineDataCollection: list[str] = []
        for line in fileHandle:
            spineDataCollection.append(line)
        self.dataStream = spineDataCollection
        return self.parse()


class HumdrumLine(prebase.ProtoM21Object):
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
    lineNumber: int = 0
    contents: str = ''
    numSpines: int = 0


class SpineLine(HumdrumLine):
    r'''
    A SpineLine is any horizontal line of a Humdrum file that
    contains one or more spine elements (separated by tabs)
    and not Global elements.

    Takes in a 1-based line number in the file and a string of contents.

    >>> hsl = humdrum.spineParser.SpineLine(
    ...         lineNumber=7, contents='C4\t!local comment\t*M[4/4]\t.\n')
    >>> hsl
    <music21.humdrum.spineParser.SpineLine line 7 (4 spines)>
    >>> hsl.lineNumber
    7
    >>> hsl.numSpines
    4
    >>> hsl.spineData
    ['C4', '!local comment', '*M[4/4]', '.']
    '''
    def __init__(self, lineNumber: int = 0, contents: str = '') -> None:
        self.lineNumber = lineNumber
        contents = contents.rstrip()
        returnList = re.split('\t+', contents)
        self.numSpines = len(returnList)
        self.contents = contents
        self.spineData: list[str] = returnList

    def _reprInternal(self) -> str:
        return f'line {self.lineNumber} ({self.numSpines} spines)'


class GlobalReferenceLine(HumdrumLine):
    # noinspection SpellCheckingInspection
    r'''
    A GlobalReferenceLine is a type of HumdrumLine that contains
    information/metadata about the Humdrum document.

    In Humdrum it is represented by three exclamation points
    followed by non-whitespace followed by a colon.  Examples::

        !!!COM: Stravinsky, Igor Fyodorovich
        !!!CDT: 1882/6/17/-1971/4/6
        !!!ODT: 1911//-1913//; 1947//
        !!!OPT@@RUS: Vesna svyashchennaya
        !!!OPT@FRE: Le sacre du printemps

    The GlobalReferenceLine object takes two inputs::

        lineNumber   1-based line number in the Humdrum file
        contents     string of contents

    And stores them as three attributes::

        lineNumber: as above
        code:       non-whitespace code (usually three letters)
        value:      its value

    >>> gr = humdrum.spineParser.GlobalReferenceLine(
    ...        lineNumber=20, contents='!!!COM: Stravinsky, Igor Fyodorovich\n')
    >>> gr
    <music21.humdrum.spineParser.GlobalReferenceLine COM: 'Stravinsky, Igor Fyodorovich'>
    >>> gr.lineNumber
    20
    >>> gr.code
    'COM'
    >>> gr.value
    'Stravinsky, Igor Fyodorovich'

    TODO: add parsing of three-digit Kern comment codes into fuller metadata
    TODO: parse ``@``/``@@`` language tags here (e.g. ``!!!OPT@@RUS:``, ``!!!OPT@FRE:``)
    and propagate language/isPrimary so that GlobalReference.updateMetadata
    can attach ``metadata.Text(value, language=...)`` instead of bare strings.
    '''
    def __init__(self, lineNumber: int = 0, contents: str = '!!! NUL: None') -> None:
        self.lineNumber = lineNumber
        noExclaim = re.sub(r'^!!!+', '', contents)
        try:
            (code, value) = noExclaim.split(':', 1)
            value = value.strip()
            if code is None:
                raise HumdrumException('GlobalReferenceLine (!!!) found without a code '
                                       f'listed; this is probably a problem! {contents} ')
        except IndexError:  # pragma: no cover
            raise HumdrumException('GlobalReferenceLine (!!!) found without a code listed; '
                                   f'this is probably a problem! {contents} ')

        self.contents = contents
        self.code: str = code
        self.value: str = value

    def _reprInternal(self) -> str:
        return f'{self.code}: {self.value!r}'


class GlobalCommentLine(HumdrumLine):
    '''
    A GlobalCommentLine is a Humdrum comment that pertains to all spines.
    In Humdrum it is represented by two exclamation points (and usually one space).

    The GlobalComment object takes two inputs and stores them as attributes::

        lineNumber (1-based line number in the Humdrum file)
        contents   (string of contents)
        value      (contents minus !!)

    The constructor can be passed (lineNumber, contents); if contents begins with
    bangs, they are removed along with up to one space directly afterwards.

    >>> com1 = humdrum.spineParser.GlobalCommentLine(
    ...          lineNumber=4, contents='!! this comment is global')
    >>> com1
    <music21.humdrum.spineParser.GlobalCommentLine 'this comment is global'>
    >>> com1.lineNumber
    4
    >>> com1.contents
    '!! this comment is global'
    >>> com1.value
    'this comment is global'
    '''
    value: str = ''

    def __init__(self, lineNumber: int = 0, contents: str = '') -> None:
        self.lineNumber = lineNumber
        value = re.sub(r'^!!+\s?', '', contents)
        self.contents = contents
        self.value = value

    def _reprInternal(self) -> str:
        return repr(self.value)


class BlankLine(HumdrumLine):
    '''
    A blank line in a Humdrum source.  Humdrum forbids blank lines, but
    they appear in the wild.  Storing them as BlankLine objects keeps
    `eventList` aligned with the source: `eventList[lineNumber - 1]` is
    always the HumdrumLine at that 1-based source line.

    Treated as a global event by `parseProtoSpinesAndEventCollections`
    (no SpineEvent is created at this line for any spine).

    >>> b = humdrum.spineParser.BlankLine(lineNumber=12)
    >>> b
    <music21.humdrum.spineParser.BlankLine line 12>
    >>> b.lineNumber
    12
    '''
    def __init__(self, lineNumber: int = 0) -> None:
        self.lineNumber = lineNumber
        self.contents = ''

    def _reprInternal(self) -> str:
        return f'line {self.lineNumber}'


class ProtoSpine(prebase.ProtoM21Object):
    '''
    A ProtoSpine is a collection of events arranged vertically.
    It differs from a HumdrumSpine in that spine paths are not followed.
    So ProtoSpine(1) would be everything in the 2nd column
    of a Humdrum file regardless of whether the 2nd column
    was at some point an independent Spine
    or if it later became a split from the first spine.

    See :meth:`~music21.humdrum.spineParser.parseProtoSpinesAndEventCollections`
    for more details on how ProtoSpine objects are created.

    * Changed in v10: ProtoSpines now iterate over their eventLists and are ProtoM21Objects.
    '''

    def __init__(self, eventList: list[SpineEvent|None]|None = None) -> None:
        if eventList is None:
            eventList = []
        self.eventList: list[SpineEvent|None] = eventList

    def __iter__(self) -> t.Iterator[SpineEvent|None]:
        return iter(self.eventList)

    def _reprInternal(self) -> str:
        return f'{len(self.eventList)} events'


# HUMDRUM SPINES #
# Ready to be parsed.
class HumdrumSpine(prebase.ProtoM21Object):
    r'''
    A HumdrumSpine is a representation of a generic HumdrumSpine
    regardless of \*\*definition after spine path indicators have
    been simplified.

    A subclass of HumdrumSpine should be defined for each \*\*type. Those
    subclasses cannot redefine `__init__()`

    A HumdrumSpine is a collection of events arranged vertically that have a
    connection to each other.
    Each HumdrumSpine MUST have an id (numeric or string) attached to it.

    >>> SE = humdrum.spineParser.SpineEvent
    >>> spineEvents = [SE('**kern'), SE('c,4'), SE('d#8')]
    >>> spine1Id = 5
    >>> spine1 = humdrum.spineParser.HumdrumSpine(spine1Id, spineEvents)
    >>> spine1.insertPoint = 5
    >>> spine1.endingPoint = 6
    >>> spine1.parentSpine = 3  # spine 3 is the previous spine leading to this one
    >>> spine1.childSpines = [7, 8]  # the spine ends by being split into spines 7 and 8

    A spine knows the SpineCollection it belongs to:

    >>> spineCollection1 = humdrum.spineParser.SpineCollection()
    >>> spine1.parentSpineCollection = spineCollection1

    The spineType property searches the EventList or parentSpine to
    figure out the spineType.

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

    >>> spine2 = humdrum.spineParser.HumdrumSpine(streamClass=stream.Part)
    >>> spine2.stream
    <music21.stream.Part ...>
    '''
    @t.final
    def __init__(
        self,
        spineId: int = 0,
        eventList: list[SpineEvent]|None = None,
        streamClass: type[stream.Stream] = stream.Stream,
        parentSpineCollection: SpineCollection|None = None,
    ) -> None:
        self.id: int = spineId
        if eventList is None:
            eventList = []
        for event in eventList:
            event.spineId = spineId

        self.eventList: list[SpineEvent] = eventList
        self.stream: stream.Stream = streamClass()
        self.insertPoint: int = 0
        self.endingPoint: int = 0
        self.parentSpine: HumdrumSpine|None = None
        self.newSpine: HumdrumSpine|None = None
        self.isLastSpine: bool = False
        self.childSpines: list[HumdrumSpine] = []
        self.childSpineInsertPoints: dict[int, tuple[HumdrumSpine, ...]] = {}

        self.parsed: bool = False
        self.measuresMoved: bool = False
        self.insertionsDone: bool = False

        if parentSpineCollection is None:
            # Mostly for unit tests / direct construction.  Real spines come
            # from SpineCollection.addSpine() which always passes the parent.
            parentSpineCollection = SpineCollection()
        self.parentSpineCollection: SpineCollection = parentSpineCollection
        self._spineType: str = ''

        self.isFirstVoice: bool = False

    def _reprInternal(self) -> str:
        representation = ': ' + str(self.id)
        if self.parentSpine:
            representation += ' [child of: ' + str(self.parentSpine.id) + ']'
        if self.childSpines:
            representation += ' [parent of: '
            for s in self.childSpines:
                representation += str(s.id) + ' '
            representation += ' ]'
        return representation

    def append(self, event: SpineEvent) -> None:
        '''
        add an item to this Spine
        '''
        self.eventList.append(event)

    def __iter__(self) -> t.Iterator[SpineEvent]:
        return iter(self.eventList)

    def _getLocalSpineType(self) -> str:
        if self._spineType:
            return self._spineType
        for thisEvent in self.eventList:
            m1 = re.match(r'\*\*(.*)', thisEvent.contents)
            if m1:
                self._spineType = m1.group(1)
                return self._spineType
        return ''

    def _getParentSpineType(self) -> str:
        parentSpine = self.parentSpine
        if parentSpine is None:
            return ''
        return parentSpine.spineType

    def _getSpineType(self) -> str:
        '''
        searches the current and parent spineType for a search
        '''
        if self._spineType:
            return self._spineType
        st = self._getLocalSpineType()
        if st:
            self._spineType = st
            return st
        st = self._getParentSpineType()
        if st:
            self._spineType = st
            return st
        raise HumdrumException('Could not determine spineType '
                               + 'for spine with id ' + str(self.id))

    def _setSpineType(self, newSpineType: str = '') -> None:
        self._spineType = newSpineType

    spineType = property(_getSpineType, _setSpineType)

    def moveElementsIntoMeasures(self, streamIn: stream.Stream) -> stream.Stream:
        # noinspection PyShadowingNames
        '''
        Takes a parsed stream and moves the elements inside the
        measures.  Works with pickup measures, etc. Does not
        automatically create ties, etc.

        Why not just use Stream.makeMeasures()? because
        Humdrum measures contain extra information about barlines
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
        {0.0} <music21.stream.Measure 1 offset=0.0>
        <BLANKLINE>
        {0.0} <music21.meter.TimeSignature 2/4>
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
        currentMeasureOffset: OffsetQL = 0.0
        hasMeasureOne = False
        for el in streamIn:
            if isinstance(el, stream.Measure):
                if currentMeasureNumber != 0 or currentMeasure:
                    currentMeasure.coreElementsChanged()
                    # streamOut.append(currentMeasure)
                    streamOut.coreAppend(currentMeasure)
                currentMeasure = el
                currentMeasureNumber = el.number
                currentMeasureOffset = el.offset
                if currentMeasureNumber == 1:
                    hasMeasureOne = True
            else:
                if currentMeasureNumber != 0 or el.duration.quarterLength != 0:
                    # currentMeasure.insert(el.offset - currentMeasureOffset, el)
                    currentMeasure.coreInsert(el.offset - currentMeasureOffset, el)
                else:
                    # streamOut.append(el)
                    streamOut.coreAppend(el)
        # update the most recent measure and the surrounding stream, then append the last
        currentMeasure.coreElementsChanged()
        streamOut.coreElementsChanged()
        if currentMeasure:
            streamOut.append(currentMeasure)

        # move beginning stuff (Clefs, KeySig, etc.) to first measure.
        measureElements = streamOut.getElementsByClass(stream.Measure)
        if measureElements:
            m1 = measureElements[0]
            if not hasMeasureOne:  # pickup measure is not measure1
                m1.number = 1
            beginningStuff = streamOut.getElementsByOffset(0)
            for el in beginningStuff:
                if isinstance(el, stream.Stream):
                    pass
                elif 'MiscTandem' in el.classes:
                    pass
                else:
                    m1.insert(0, el)
                    streamOut.remove(el)
            m1TimeSignature = m1.timeSignature
            if m1TimeSignature is not None:
                if m1.duration.quarterLength < m1TimeSignature.barDuration.quarterLength:
                    m1.paddingLeft = opFrac(m1TimeSignature.barDuration.quarterLength
                                            - m1.duration.quarterLength)

        return streamOut

    def parse(self) -> None:
        '''
        Dummy method that pushes all these objects to HumdrumSpine.stream
        as ElementWrappers.  Should be overridden in
        specific Spine subclasses.
        '''
        humdrumLineNumbers = self.parentSpineCollection.humdrumLineNumbers
        lastContainer = hdStringToMeasure('=0')

        for event in self.eventList:
            eventC = str(event.contents)
            thisObject: base.Music21Object|None = None
            if eventC == '.':
                pass
            elif eventC.startswith('*'):
                # control processing
                if eventC not in spinePathIndicators:
                    thisObject = MiscTandem(eventC)
            elif eventC.startswith('='):
                lastContainer = hdStringToMeasure(eventC, lastContainer)
                thisObject = lastContainer
            elif eventC.startswith('!'):
                thisObject = SpineComment(eventC)
            else:
                thisObject = base.ElementWrapper(event)

            if thisObject is not None:
                humdrumLineNumbers[thisObject] = event.lineNumber
                self.stream.coreAppend(thisObject)
        self.stream.coreElementsChanged()


class KernSpine(HumdrumSpine):
    r'''
    A KernSpine is a type of Humdrum spine with the \*\*kern
    attribute set and thus events are processed as if they
    are kern notes.

    Instances are not constructed directly; `reclassSpines` reassigns
    `__class__` from `HumdrumSpine` to `KernSpine` once the spine's
    exclusive interpretation is known.  All KernSpine-specific state
    is initialized at the top of `parse()`.

    * Changed in v10: `currentTupletDuration` / `desiredTupletDuration`
        renamed to `currentTupletQL` / `desiredTupletQL`.
    '''
    # Set in parse(); declared here so type-checkers see them.
    lastContainer: stream.Measure|None
    inTuplet: bool
    lastNote: note.GeneralNote|None
    currentBeamNumbers: int
    currentTupletQL: OffsetQL
    desiredTupletQL: OffsetQL

    def parse(self) -> None:
        humdrumLineNumbers = self.parentSpineCollection.humdrumLineNumbers
        self.lastContainer = hdStringToMeasure('=0')
        self.inTuplet = False
        self.lastNote = None
        self.currentBeamNumbers = 0
        self.currentTupletQL = 0.0
        self.desiredTupletQL = 0.0

        for event in self.eventList:
            # event is a SpineEvent object
            try:
                eventC = event.contents
                thisObject: base.Music21Object|None = None
                if eventC == '.':
                    pass
                elif eventC.startswith('*'):
                    # control processing
                    tempObject = kernTandemToObject(eventC)
                    if tempObject is not None:
                        thisObject = tempObject
                elif eventC.startswith('='):
                    self.lastContainer = hdStringToMeasure(eventC, self.lastContainer)
                    thisObject = self.lastContainer
                elif eventC.startswith('!'):
                    spineCommentObj = SpineComment(eventC)
                    if spineCommentObj.comment != '':
                        thisObject = spineCommentObj
                elif ' ' in eventC:
                    thisObject = self.processChordEvent(eventC)
                else:  # Note or Rest
                    thisObject = self.processNoteEvent(eventC)

                if thisObject is not None:
                    humdrumLineNumbers[thisObject] = event.lineNumber
                    # priority is doing double duty: real Stream sort priority
                    # (used by insertGlobalEvents) AND a proxy for Humdrum line
                    # number (used by attachNonKernEvents to align spines).
                    thisObject.priority = event.lineNumber
                    self.stream.coreAppend(thisObject)
            except Exception as e:  # pylint: disable=broad-exception-caught  # pragma: no cover
                import traceback
                environLocal.warn(
                    f'Error in parsing event ({event.contents!r}) '
                    f'at line {event.lineNumber} '
                    f'for spine {event.spineId}: {e}'
                )
                tb = traceback.format_exc()
                environLocal.printDebug(f'Traceback for the exception: \n{tb}')
                # traceback: environLocal.printDebug()

        self.stream.coreElementsChanged()
        # still to be done later. Move things before first measure to first measure!

    def processNoteEvent(self, eventC: str) -> note.GeneralNote:
        '''
        similar to hdStringToNote, this method processes a string representing a single
        note, but stores information about current beam and tuplet state.
        '''
        eventNote = hdStringToNote(eventC)

        self.setBeamsForNote(eventNote)
        self.setTupletTypeForNote(eventNote)

        self.lastNote = eventNote
        return eventNote

    def processChordEvent(self, eventC: str) -> chord.Chord:
        '''
        Process a single chord event

        Like processNoteEvent, stores information about current beam and tuplet state.
        '''
        # multipleNotes
        notesToProcess = eventC.split()
        chordNotes: list[note.Note] = []
        defaultDuration: duration.Duration|None = None  # for non-first notes without a duration
        for i, noteToProcess in enumerate(notesToProcess):
            thisNote = hdStringToNote(noteToProcess, defaultDuration)
            if isinstance(thisNote, note.Note):
                chordNotes.append(thisNote)
            if i == 0:
                defaultDuration = thisNote.duration
        eventChord = chord.Chord(chordNotes, beams=chordNotes[-1].beams,  # type: ignore
                                 duration=defaultDuration)
        self.setBeamsForNote(eventChord)
        self.setTupletTypeForNote(eventChord)
        self.lastNote = eventChord

        return eventChord

    def setBeamsForNote(self, n: note.GeneralNote) -> None:
        '''
        sets the beams for a Note (or Chord) given self.currentBeamNumbers
        and updates self.currentBeamNumbers based on stop beams.

        Safe enough to use on elements such as rests that don't have beam info.
        '''
        if not hasattr(n, 'beams'):
            return None

        if self.currentBeamNumbers != 0 and not n.beams.beamsList:
            for unused_counter in range(self.currentBeamNumbers):
                n.beams.append('continue')
        elif n.beams.beamsList:
            if n.beams.beamsList[0].type == 'stop':
                self.currentBeamNumbers = 0
            else:
                for thisBeam in n.beams.beamsList:
                    if thisBeam.type != 'stop':
                        self.currentBeamNumbers += 1

    def setTupletTypeForNote(self, n: note.GeneralNote) -> None:
        # nested tuplets not supported by humdrum.
        nDur = n.duration
        nTuplets = n.duration.tuplets

        if not self.inTuplet and nTuplets:
            self.inTuplet = True
            self.desiredTupletQL = nTuplets[0].totalTupletLength()
            self.currentTupletQL = nDur.quarterLength
            n.duration.tuplets[0].type = 'start'
        elif self.inTuplet and not nTuplets:
            self.inTuplet = False
            self.desiredTupletQL = 0.0
            self.currentTupletQL = 0.0
            if self.lastNote is not None:
                self.lastNote.duration.tuplets[0].type = 'stop'
        elif self.inTuplet:
            self.currentTupletQL = opFrac(self.currentTupletQL + nDur.quarterLength)
            # Stop on the first integer multiple of desiredTupletQL --
            # handles both exact fits and overshoots like trying to get 3 1/6ths to
            # add to 0.5, but getting instead 1/6+1/6+1/3+1/6+1/6 = 2*0.5.
            if (self.currentTupletQL >= self.desiredTupletQL
                    and self.currentTupletQL % self.desiredTupletQL == 0):
                nTuplets[0].type = 'stop'
                self.inTuplet = False
                self.currentTupletQL = 0.0
                self.desiredTupletQL = 0.0


class DynamSpine(HumdrumSpine):
    r'''
    A DynamSpine is a type of Humdrum spine with the \*\*dynam
    attribute set and thus events are processed as if they
    are dynamics.
    '''
    def parse(self) -> None:
        humdrumLineNumbers = self.parentSpineCollection.humdrumLineNumbers
        thisContainer: stream.Measure|None = None
        for event in self.eventList:
            eventC = event.contents
            thisObject: base.Music21Object|None = None
            if eventC == '.':
                pass
            elif eventC.startswith('*'):
                # control processing
                if eventC not in spinePathIndicators:
                    thisObject = MiscTandem(eventC)
            elif eventC.startswith('='):
                if thisContainer is not None:
                    thisContainer.coreElementsChanged()
                    self.stream.coreAppend(thisContainer)
                thisContainer = hdStringToMeasure(eventC)
            elif eventC.startswith('!'):
                spineCommentObj = SpineComment(eventC)
                if spineCommentObj.comment != '':
                    thisObject = spineCommentObj

            elif eventC.startswith('<'):
                thisObject = dynamics.Diminuendo()
            elif eventC.startswith('>'):
                thisObject = dynamics.Crescendo()
            else:
                thisObject = dynamics.Dynamic(eventC)

            if thisObject is not None:
                humdrumLineNumbers[thisObject] = event.lineNumber
                if thisContainer is None:
                    self.stream.coreAppend(thisObject)
                else:
                    thisContainer.coreAppend(thisObject)

        # flush the final Measure (events after the last barline)
        if thisContainer is not None:
            thisContainer.coreElementsChanged()
            self.stream.coreAppend(thisContainer)
        self.stream.coreElementsChanged()


class HarmSpine(HumdrumSpine):
    r'''
    A HarmSpine is a type of Humdrum spine with the \*\*harm
    attribute set and thus events are processed as if they
    are harmonic analysis annotations in the "harm" syntax.

    The harm roman numeral annotations are parsed using
    a superset of the original \*\*harm Humdrum representation, written
    for python and extending the syntax based on other projects like the
    RomanText and the MuseScore roman numeral notations.
    '''
    def parse(self) -> None:
        humdrumLineNumbers = self.parentSpineCollection.humdrumLineNumbers
        lastContainer = hdStringToMeasure('=0')
        currentKey = key.Key('C')
        for event in self.eventList:
            eventC = event.contents
            thisObject: base.Music21Object|None = None
            if eventC == '.':
                pass
            elif eventC.startswith('*'):
                if eventC in spinePathIndicators:
                    continue
                # TODO: is the ":" ending enough to identify a key tandem?
                if eventC.endswith(':'):
                    keyString = eventC[1:-1]
                    currentKey = key.Key(keyString)
                    thisObject = currentKey
                else:
                    # treat everything else generically
                    thisObject = MiscTandem(eventC)
            elif eventC.startswith('='):
                lastContainer = hdStringToMeasure(eventC, lastContainer)
                thisObject = lastContainer
            elif eventC.startswith('!'):
                thisObject = SpineComment(eventC)
            else:
                harmStr = event.contents
                romanStr = harmParser.convertHarmToRoman(harmStr)
                if romanStr is None:
                    # Token did not parse as **harm.  Like KernSpine with an
                    # unparseable note, warn and skip rather than emit a
                    # spurious empty RomanNumeral at this position.
                    environLocal.warn(
                        f'Could not parse **harm token ({harmStr!r}) '
                        f'at line {event.lineNumber} '
                        f'for spine {event.spineId}; skipping.'
                    )
                else:
                    thisObject = roman.RomanNumeral(
                        romanStr,
                        currentKey,
                        sixthMinor=roman.Minor67Default.FLAT,
                        seventhMinor=roman.Minor67Default.SHARP
                    )

            if thisObject is not None:
                humdrumLineNumbers[thisObject] = event.lineNumber
                thisObject.priority = event.lineNumber
                self.stream.coreAppend(thisObject)
        self.stream.coreElementsChanged()

# END HUMDRUM SPINES


class SpineEvent(prebase.ProtoM21Object):
    '''
    A SpineEvent is an event in a HumdrumSpine or ProtoSpine.

    Its .contents property contains the contents of the spine, or
    it could be '.', in which case it means that a
    particular event appears after the last event in a different spine.
    It could also be "None" indicating that there is no event at all
    at this moment in the Humdrum file.  Happens if no ProtoSpine exists
    at this point in the file in this tab position.

    Should be initialized with its contents and 1-based source line number.

    These attributes are optional but likely to be very helpful::

        lineNumber -- 1-based source line number in the Humdrum file
        protoSpineId -- ProtoSpine id (0 to N)
        spineId -- id of HumdrumSpine actually attached to (after SpinePaths are parsed)

    The `toNote()` method converts the contents into a music21 note as
    if it's kern -- useful to have in all spine types.

    >>> se1 = humdrum.spineParser.SpineEvent('EEE-8')
    >>> se1.lineNumber = 40
    >>> se1.contents
    'EEE-8'
    >>> se1
    <music21.humdrum.spineParser.SpineEvent EEE-8>
    >>> n = se1.toNote()
    >>> n
    <music21.note.Note E->
    '''
    def __init__(self, contents: str = '', lineNumber: int = 0) -> None:
        self.contents: str = contents
        self.lineNumber: int = lineNumber
        self.protoSpineId: int = 0
        self.spineId: int|None = None

    def _reprInternal(self) -> str:
        return self.contents

    def __str__(self) -> str:
        return self.contents

    def toNote(self, convertString: str|None = None) -> note.GeneralNote:
        r'''
        parse the object as a \*\*kern note and return a
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

# -----SPINE COLLECTION------------


class SpineCollection(prebase.ProtoM21Object):
    '''
    A SpineCollection is a set of HumdrumSpines with relationships to each
    other and where their position attributes indicate
    simultaneous onsets.

    When you iterate over a SpineCollection, it goes from right to
    left, since that's the order that Humdrum expects.
    '''
    def __init__(self) -> None:
        self.spines: list[HumdrumSpine] = []
        self.nextFreeId: int = 0
        self.spineReclassDone: bool = False
        self.newSpine: HumdrumSpine|None = None
        # Maps each parsed Music21Object to its Humdrum file line position.
        self.humdrumLineNumbers: weakref.WeakKeyDictionary[base.Music21Object, int] = (
            weakref.WeakKeyDictionary()
        )

    def __iter__(self) -> t.Iterator[HumdrumSpine]:
        '''
        Iterates spines right-to-left, the order Humdrum expects.
        '''
        return reversed(self.spines)

    def addSpine(self, streamClass: type[stream.Stream] = stream.Part) -> HumdrumSpine:
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
        >>> newSpine2 = hsc.addSpine(streamClass=stream.Stream)
        >>> newSpine2.id
        1
        >>> newSpine2
        <music21.humdrum.spineParser.HumdrumSpine: 1>
        >>> newSpine2.stream
        <music21.stream.Stream ...>
        '''
        self.newSpine = HumdrumSpine(
            self.nextFreeId,
            streamClass=streamClass,
            parentSpineCollection=self
        )
        self.spines.append(self.newSpine)
        self.nextFreeId += 1
        return self.newSpine

    def appendSpine(self, spine: HumdrumSpine) -> None:
        '''
        appendSpine(spine) -- appends an already existing HumdrumSpine
        to the SpineCollection.  Returns void
        '''
        self.spines.append(spine)

    def getSpineById(self, spineId: int) -> HumdrumSpine:
        '''
        returns the HumdrumSpine with the given id.

        raises a HumdrumException if the spine with a given id is not found
        '''
        for thisSpine in self.spines:
            if thisSpine.id == spineId:
                return thisSpine
        raise HumdrumException('Could not find a Spine with that ID')

    def removeSpineById(self, spineId: int) -> None:
        '''
        Deletes a spine from the SpineCollection (after inserting, integrating, etc.)

        >>> hsc = humdrum.spineParser.SpineCollection()
        >>> newSpine = hsc.addSpine()
        >>> newSpine.id
        0
        >>> newSpine2 = hsc.addSpine()
        >>> newSpine2.id
        1
        >>> hsc.spines
        [<music21.humdrum.spineParser.HumdrumSpine: 0>,
         <music21.humdrum.spineParser.HumdrumSpine: 1>]
        >>> hsc.removeSpineById(newSpine.id)
        >>> hsc.spines
        [<music21.humdrum.spineParser.HumdrumSpine: 1>]

        raises a HumdrumException if the spine with a given id is not found
        '''
        for s in self.spines:
            if s.id == spineId:
                self.spines.remove(s)
                return None
        raise HumdrumException(f'Could not find a Spine with that ID {id}')

    def createMusic21Streams(self) -> None:
        '''
        Create Music21 Stream objects from spineCollections by running:

            self.reclassSpines()
            self.parseMusic21()
            self.performInsertions()
            self.moveObjectsToMeasures()
            self.attachNonKernEvents()
            self.makeVoices()
            self.assignIds()
        '''
        self.reclassSpines()
        self.parseMusic21()
        self.performInsertions()
        self.moveObjectsToMeasures()
        self.attachNonKernEvents()
        self.makeVoices()
        self.assignIds()

    def assignIds(self) -> None:
        '''
        Assign an ID based on the instrument, or just a string of a number
        if there is no instrument.

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
        usedIds: dict[str|None, int] = {None: 0}
        firstStreamForEachInstrument: dict[str|None, stream.Stream] = {}
        for thisSpine in self.spines:
            spineStream = thisSpine.stream
            instrumentsStream = spineStream.getElementsByClass(instrument.Instrument)
            if not instrumentsStream:
                spineInstrument = None
            else:
                spineInstrument = instrumentsStream[0].instrumentName

            if spineInstrument not in usedIds:
                firstStreamForEachInstrument[spineInstrument] = spineStream
                usedIds[spineInstrument] = 1
                if spineInstrument is not None:
                    spineStream.id = spineInstrument
            elif spineInstrument is None:
                usedIds[None] += 1
                spineStream.id = str(usedIds[None])
            else:
                if usedIds[spineInstrument] == 1:
                    myFirstStream = firstStreamForEachInstrument[spineInstrument]
                    myFirstStream.id = str(myFirstStream.id) + '-1'
                usedIds[spineInstrument] += 1
                spineStream.id = spineInstrument + '-' + str(usedIds[spineInstrument])

    def performInsertions(self) -> None:
        '''
        Take a parsed spineCollection as Music21Objects and take
        sub-spines and put them in their proper location.
        '''
        for thisSpine in self.spines:
            # removeSpines = []
            if thisSpine.parentSpine is not None:
                continue
            if not thisSpine.childSpines:
                continue

            # only spines with children spines and parent spines continue
            newStream = thisSpine.stream.__class__()
            insertPoints = sorted(thisSpine.childSpineInsertPoints)
            lastLineNumber = -1
            for el in thisSpine.stream:
                lineNumber = self.humdrumLineNumbers.get(el)
                if lineNumber is not None:
                    for i in insertPoints:
                        if lastLineNumber > i or lineNumber < i:
                            continue
                        # insert a sub-spine into this Stream at the current location
                        self.performSpineInsertion(thisSpine, newStream, i)
                        insertPoints.remove(i)
                    lastLineNumber = lineNumber
                    del self.humdrumLineNumbers[el]
                newStream.coreAppend(el)
                # newStream.append(el)
            newStream.coreElementsChanged()
            thisSpine.stream = newStream

            # some spines were not inserted because the
            # insertion point was at the end of the parent spine
            # happens in some musedata conversions, such as beethoven 5, movement 1.
            for i in insertPoints:
                self.performSpineInsertion(thisSpine, newStream, i)
            # for removeMe in removeSpines:
            #    # needed for some tests
            #    self.removeSpineById(removeMe)

    def performSpineInsertion(
        self,
        thisSpine: HumdrumSpine,
        newStream: stream.Stream,
        insertionPoint: int,
    ) -> None:
        '''
        Insert all the spines into newStream that should be
        inserted into thisSpine at insertionPoint.
        '''
        newStream.coreElementsChanged()  # update highestTime
        startPoint = newStream.highestTime
        childrenToInsert = thisSpine.childSpineInsertPoints[insertionPoint]
        voiceNumber = 0
        for insertSpine in childrenToInsert:
            # removeSpines.append(insertSpine.id)
            voiceNumber += 1
            voiceStr = 'voice' + str(voiceNumber)
            for insertEl in insertSpine.stream:
                if not insertSpine.isFirstVoice and isinstance(insertEl, stream.Measure):
                    pass  # only insert one measure object per spine
                else:
                    insertEl.groups.append(voiceStr)
                    # newStream.insert(startPoint + insertEl.offset, insertEl)
                    newStream.coreInsert(startPoint + insertEl.offset, insertEl)
        newStream.coreElementsChanged()  # call between coreInsert and coreAppend

    def reclassSpines(self) -> None:
        r'''
        Changes the classes of HumdrumSpines to more specific types
        (KernSpine, DynamicSpine)
        according to their spineType (e.g., \*\*kern, \*\*dynam)
        '''
        for thisSpine in self.spines:
            if thisSpine.spineType == 'kern':
                thisSpine.__class__ = KernSpine
            elif thisSpine.spineType == 'dynam':
                thisSpine.__class__ = DynamSpine
            elif thisSpine.spineType == 'harm':
                thisSpine.__class__ = HarmSpine
        self.spineReclassDone = True

    def getOffsetsAndPrioritiesByLineNumber(
        self,
    ) -> dict[int, tuple[OffsetQL, list[base.Music21Object]]]:
        '''
        Iterates through the spines by location
        and records the offset and priority for each element in the spines.

        Returns a dictionary keyed by Humdrum line number whose values are
        two-element tuples: (music21 offset, list of Music21Objects at that line).
        '''
        lineNumberDict: dict[int, tuple[OffsetQL, list[base.Music21Object]]] = {}
        for thisSpine in self.spines:
            if thisSpine.parentSpine is None:
                for el in thisSpine.stream.flatten():
                    pos = self.humdrumLineNumbers.get(el)
                    if pos is None:
                        continue
                    if pos not in lineNumberDict:
                        lineNumberDict[pos] = (el.offset, [el])
                    else:
                        lineNumberDict[pos][1].append(el)
        return lineNumberDict

    def moveObjectsToMeasures(self) -> None:
        '''
        run moveElementsIntoMeasures for each HumdrumSpine
        that is not a sub-spine.

        Also fixes up the tuplets using duration.TupletFixer
        '''
        tf = duration.TupletFixer()

        for thisSpine in self.spines:
            if thisSpine.parentSpine is None:
                thisSpine.stream = thisSpine.moveElementsIntoMeasures(thisSpine.stream)

                # fix tuplet groups
                for m in thisSpine.stream.getElementsByClass(stream.Measure):
                    tf.setStream(m)
                    tupletGroups = tf.findTupletGroups(incorporateGroupings=True)
                    for tg in tupletGroups:
                        tf.fixBrokenTupletDuration(tg)

                thisSpine.measuresMoved = True

    def attachNonKernEvents(self) -> None:
        '''
        move :samp:`**dynam` and :samp:`**lyrics/**text` information to the appropriate staff.

        Assumes that :samp:`*staff` is consistent through the spine.

        TODO: misaligned events (a `**dynam` or `**harm` whose source line has '.'
        in the kern column) are silently dropped because the matcher only accepts
        exact :samp:`el.priority == event.lineNumber`.  Desired: when no kern note
        sits on the same line, attach to the stream at the offset of the most
        recently-sounding kern note (ideal: between current and next note's
        offsets).  Lyrics/text continue to attach to notes only.
        See `humdrum.tests.Test.testDynamAttachedMisaligned` /
        `testHarmAttachedMisaligned`.
        '''
        kernStreams: dict[int, stream.Stream] = {}
        for thisSpine in self.spines:
            if thisSpine.parentSpine is not None:
                continue
            if thisSpine.spineType != 'kern':
                continue
            for tandem in thisSpine.stream.getElementsByClass(MiscTandem):
                if not tandem.tandem.startswith('*staff'):
                    continue
                staffInfo = int(tandem.tandem[6:])  # single staff
                kernStreams[staffInfo] = thisSpine.stream
                break

        for thisSpine in self.spines:
            if thisSpine.parentSpine is not None:
                continue
            if thisSpine.spineType == 'kern':
                continue

            stavesAppliedTo: list[int] = []
            prioritiesToSearch: dict[int, base.Music21Object] = {}
            for tandem in thisSpine.stream[MiscTandem]:
                if tandem.tandem.startswith('*staff'):
                    staffInfoStr = tandem.tandem[6:]  # could be multiple staves
                    stavesAppliedTo = [int(x) for x in staffInfoStr.split('/')]
                    break
            if thisSpine.spineType == 'dynam':
                for dynamic in thisSpine.stream[dynamics.Dynamic]:
                    dynamicPos = self.humdrumLineNumbers.get(dynamic)
                    if dynamicPos is not None:
                        prioritiesToSearch[dynamicPos] = dynamic
                for applyStaff in stavesAppliedTo:
                    applyStream = kernStreams[applyStaff]
                    for el in applyStream.recurse():
                        if el.priority not in prioritiesToSearch:
                            continue
                        try:
                            el.activeSite.insert(el.offset,
                                                 prioritiesToSearch[el.priority])
                        except exceptions21.StreamException:
                            # may appear twice because of voices
                            pass
                            # el.activeSite.insert(el.offset,
                            #    copy.deepcopy(prioritiesToSearch[el.priority]))
            elif thisSpine.spineType == 'harm':
                for harm in thisSpine.stream[roman.RomanNumeral]:
                    harmPos = self.humdrumLineNumbers.get(harm)
                    if harmPos is not None:
                        prioritiesToSearch[harmPos] = harm
                for applyStaff in stavesAppliedTo:
                    applyStream = kernStreams[applyStaff]
                    for el in applyStream.recurse():
                        if el.priority not in prioritiesToSearch:
                            continue
                        try:
                            el.activeSite.insert(el.offset,
                                                 prioritiesToSearch[el.priority])
                        except exceptions21.StreamException:
                            # may appear twice because of voices
                            pass
                            # el.activeSite.insert(el.offset,
                            #    copy.deepcopy(prioritiesToSearch[el.priority]))
            elif thisSpine.spineType in ('lyrics', 'text'):
                for wrapper in thisSpine.stream[base.ElementWrapper]:
                    wrapperPos = self.humdrumLineNumbers.get(wrapper)
                    if wrapperPos is not None:
                        prioritiesToSearch[wrapperPos] = wrapper.obj
                for applyStaff in stavesAppliedTo:
                    applyStream = kernStreams[applyStaff]
                    matched = 0
                    for el in applyStream.recurse().getElementsByClass(note.GeneralNote):
                        if el.priority in prioritiesToSearch:
                            wrappedEvent = prioritiesToSearch[el.priority]
                            el.lyric = wrappedEvent.contents  # type: ignore[attr-defined]
                            matched += 1
                    if not matched and prioritiesToSearch:
                        environLocal.warn(
                            f'No notes/rests on staff {applyStaff} matched any '
                            f'lyric/text events from spine {thisSpine.id}.')

    def makeVoices(self) -> None:
        '''
        make voices for each kernSpine -- why not just run
        stream.makeVoices() ? because we have more information
        here that lets us make voices more intelligently

        Should be done after measures have been made.
        '''
        for thisSpine in self.spines:
            if thisSpine.spineType != 'kern' or thisSpine.parentSpine is not None:
                continue
            thisStream = thisSpine.stream
            for el in thisStream.getElementsByClass(stream.Measure):
                hasVoices = False
                lowestVoiceOffset = 0
                for mEl in el:
                    if 'voice1' in mEl.groups:
                        hasVoices = True
                        lowestVoiceOffset = mEl.offset
                        break
                if not hasVoices:
                    continue

                voices: list[stream.Voice|None] = [None for i in range(10)]
                measureElements = el.elements
                for mEl in measureElements:
                    mElGroups = mEl.groups
                    # print(mEl, mElGroups)
                    if not mElGroups or not mElGroups[0].startswith('voice'):
                        continue

                    voiceName = mElGroups[0]
                    voiceNumber = int(voiceName[5])
                    voicePart = voices[voiceNumber]
                    if voicePart is None:
                        voicePart = stream.Voice()
                        voices[voiceNumber] = voicePart
                        voicePart.groups.append(voiceName)
                    if t.TYPE_CHECKING:
                        assert voicePart is not None

                    mElOffset = mEl.offset
                    el.remove(mEl)
                    voicePart.coreInsert(mElOffset - lowestVoiceOffset, mEl)
                # print(voices)
                for voicePart in voices:
                    if voicePart is not None:
                        # voicePart.show('text')
                        voicePart.coreElementsChanged()
                        el.coreInsert(lowestVoiceOffset, voicePart)
                el.coreElementsChanged()
                # print(el.number, 'has voices at', lowestVoiceOffset)

    def parseMusic21(self) -> None:
        '''
        runs spine.parse() for each Spine,
        thus populating the spine.stream for each Spine.
        '''
        for thisSpine in self.spines:
            thisSpine.parse()

    # TODO: append global comments and have a way of recalling them


class EventCollection(prebase.ProtoM21Object):
    '''
    An EventCollection holds every event that appears on a single source line
    of a Humdrum file -- one cell per spine, in their `events` array.

    If a spine's cell on this line is '.' or a comment (no new event), use
    `lastEvents[spineNum]` to retrieve the previous event still sounding.
    `getSpineOccurring` returns either the current event or the last event
    that's still active.

    These events should happen at the same time (offset)
    but they are not necessarily the only events to happen at that same time.
    E.g. a clef change and the note that follows it on the next line take place at
    the same musical time but live in different EventCollections.

    These objects normally get created by
    :meth:`~music21.humdrum.spineParser.HumdrumDataCollection.parseProtoSpinesAndEventCollections`
    so you won't need to do all the setup.

    Assume that ec1 is

        C4     pp

    on source line 4, and ec2 is

        D4     .

    on source line 5:

    >>> SE = humdrum.spineParser.SpineEvent
    >>> eventList1 = [SE('C4', lineNumber=4), SE('pp', lineNumber=4)]
    >>> eventList2 = [SE('D4', lineNumber=5), SE('.', lineNumber=5)]
    >>> ec1 = humdrum.spineParser.EventCollection(maxSpines=2, lineNumber=4)
    >>> ec1.events = eventList1
    >>> ec2 = humdrum.spineParser.EventCollection(maxSpines=2, lineNumber=5)
    >>> ec2.events = eventList2
    >>> ec2.lastEvents[1] = eventList1[1]
    >>> ec2.maxSpines
    2
    >>> ec2.lineNumber
    5
    >>> ec2.getAllOccurring()
    [<music21.humdrum.spineParser.SpineEvent D4>, <music21.humdrum.spineParser.SpineEvent pp>]

    If there were spine path markers this next boolean would be true:

    >>> ec2.spinePathData
    False

    In the future, EventCollection may enforce that all events have the same lineNumber

    * New in v10: lineNumber.
    '''
    def __init__(self, maxSpines: int = 0, lineNumber: int = 0) -> None:
        self.events: common.defaultlist = common.defaultlist(lambda: None)
        self.lastEvents: common.defaultlist = common.defaultlist(lambda: None)
        self.maxSpines: int = maxSpines
        self.lineNumber: int = lineNumber
        self.spinePathData: bool = False
        # true if the line contains data about changing spinePaths

    def _reprInternal(self) -> str:
        return f'line {self.lineNumber}, {len(self.events)} events, {self.maxSpines} spines'

    def addSpineEvent(self, spineNum: int, spineEvent: SpineEvent) -> None:
        self.events[spineNum] = spineEvent

    def addLastSpineEvent(self, spineNum: int, spineEvent: SpineEvent) -> None:
        # should only add if current 'event' is '.' or a comment
        self.lastEvents[spineNum] = spineEvent

    def addGlobalEvent(self, globalEvent: HumdrumLine) -> None:
        for i in range(self.maxSpines):
            self.events[i] = globalEvent

    def getSpineEvent(self, spineNum: int) -> SpineEvent|None:
        return self.events[spineNum]

    def getSpineOccurring(self, spineNum: int) -> SpineEvent|None:
        # returns the lastEvent if set (
        # should only happen if currentEvent is '.')
        # or the current event
        if self.lastEvents[spineNum] is not None:
            return self.lastEvents[spineNum]
        else:
            return self.events[spineNum]

    def getAllOccurring(self) -> list[SpineEvent|None]:
        retEvents: list[SpineEvent|None] = []
        for i in range(self.maxSpines):
            retEvents.append(self.getSpineOccurring(i))
        return retEvents


def _hdStringToDuration(contents: str,
        defaultDuration: duration.Duration|None = None) -> duration.Duration:
    '''
    returns a :class:`~music21.duration.Duration` matching the current
        SpineEvent.

    This is used internally by hdStringToNote to figure out the duration part
    of a humdrum note or rest in a kern spine.
    '''
    # 3.2.7 Duration +
    # 3.2.8 N-Tuplets
    dotCount = contents.count('.')
    durationRegex = re.search(r'(\d+)%?(\d+)?', contents)
    if durationRegex:
        foundNumber, foundRational = durationRegex.groups()

        if foundRational:
            durationFirst = int(foundNumber)
            durationSecond = float(foundRational)
            quarterLength = 4 * durationSecond / durationFirst
            thisDuration = duration.Duration(quarterLength, dots=dotCount)

        elif foundNumber:
            durationType = int(foundNumber)
            if durationType == 0:
                if foundNumber == '000':
                    # for larger values, see https://extras.humdrum.org/man/rscale/
                    _type = 'maxima'
                elif foundNumber == '00':
                    # for larger values, see https://extras.humdrum.org/man/rscale/
                    _type = 'longa'
                else:
                    _type = 'breve'
                thisDuration = duration.Duration(type=_type, dots=dotCount)
            elif durationType in duration.typeFromNumDict:
                _type = duration.typeFromNumDict[durationType]
                thisDuration = duration.Duration(type=_type, dots=dotCount)
            else:
                dT = durationType + 0.0
                (unused_remainder, exponents) = math.modf(math.log2(dT))
                baseValue = 2 ** exponents
                baseValueInt = int(baseValue)
                _type = duration.typeFromNumDict[baseValueInt]
                thisDuration = duration.Duration(type=_type)
                newTup = duration.Tuplet()
                newTup.durationActual = duration.durationTupleFromTypeDots(_type, 0)
                newTup.durationNormal = duration.durationTupleFromTypeDots(_type, 0)

                gcd = math.gcd(durationType, baseValueInt)
                newTup.numberNotesActual = int(dT / gcd)
                newTup.numberNotesNormal = int(baseValue / gcd)

                # The Josquin Research Project uses an incorrect definition of
                # humdrum tuplets that breaks normal usage.  TODO: Refactor adding a Flavor = 'JRP'
                # code that uses this other method...
                JRP = flavors['JRP']
                if JRP is False and dotCount:
                    newTup.durationNormal = duration.durationTupleFromTypeDots(
                        newTup.durationNormal.type, dotCount)  # type: ignore

                thisDuration.appendTuplet(newTup)
                if JRP is True and dotCount:
                    thisDuration.dots = dotCount
                # call Duration.TupletFixer after to correct this.

    elif defaultDuration is not None:
        thisDuration = defaultDuration

    else:  # no duration string or default duration given
        if 'q' in contents:
            thisDuration = duration.Duration(0.5, dots=dotCount)
        else:
            thisDuration = duration.Duration(1, dots=dotCount)

    return thisDuration


def hdStringToNote(contents: str,
        defaultDuration: duration.Duration|None = None) -> note.GeneralNote:
    '''
    returns a :class:`~music21.note.Note` (or Rest or Unpitched, etc.)
    matching the current SpineEvent.
    Does not check to see that it is sane or part of a :samp:`**kern` spine, etc.

    New rhythmic extensions formerly defined in
    `wiki.humdrum.org/index.php/Rational_rhythms`
    and now at https://extras.humdrum.org/man/rscale/
    are fully implemented:

    >>> n = humdrum.spineParser.hdStringToNote('CC3%2')
    >>> n.duration.quarterLength
    Fraction(8, 3)
    >>> n.duration.fullName
    'Whole Triplet (2 2/3 QL)'

    >>> n = humdrum.spineParser.hdStringToNote('e-00.')
    >>> n.pitch
    <music21.pitch.Pitch E-4>
    >>> n.duration.quarterLength
    24.0
    >>> n.duration.fullName
    'Perfect Longa'

    >>> n = humdrum.spineParser.hdStringToNote('F#000')
    >>> n.duration.quarterLength
    32.0
    >>> n.duration.fullName
    'Imperfect Maxima'

    Note that the following example is interpreted as one note in the time of a
    double-dotted quarter not a double-dotted quarter-note triplet.

    I believe that the latter definition, though used in
    https://kern.humdrum.org/cgi-bin/ksdata?l=musedata/mozart/quartet&file=k421-01.krn&f=kern
    and the Josquin Research Project [JRP] is incorrect, seeing as it
    contradicts the specification in
    https://web.archive.org/web/20100203144730/http://www.music-cog.ohio-state.edu/Humdrum/representations/kern.html#N-Tuplets

    >>> storedFlavors = humdrum.spineParser.flavors['JRP']  #_DOCS_HIDE

    This is the default:

    >>> humdrum.spineParser.flavors['JRP'] = False

    >>> n = humdrum.spineParser.hdStringToNote('6..fff')
    >>> n.duration.quarterLength
    Fraction(7, 6)

    >>> n.duration.dots
    0

    >>> n.duration.tuplets[0].durationNormal.dots
    2

    If you want the JRP definition, set humdrum.spineParser.flavors['JRP'] = True
    before calling converter.parse() or anything like that:

    >>> humdrum.spineParser.flavors['JRP'] = True
    >>> n = humdrum.spineParser.hdStringToNote('6..fff')
    >>> n.duration.quarterLength
    Fraction(7, 6)
    >>> n.duration.dots
    2
    >>> n.duration.tuplets[0].durationNormal.dots
    0

    >>> n = humdrum.spineParser.hdStringToNote('gg#q/LL')
    >>> n.duration
    <music21.duration.GraceDuration unlinked type:quarter quarterLength:0.0>
    >>> n.duration.isGrace
    True

    >>> humdrum.spineParser.flavors['JRP'] = storedFlavors  #_DOCS_HIDE

    '''

    # http://www.lib.virginia.edu/artsandmedia/dmmc/Music/Humdrum/kern_hlp.html#kern

    # Determine duration part first to avoid making an unused duration
    thisDuration = _hdStringToDuration(contents, defaultDuration)

    # 3.2.1 Pitches and 3.3 Rests
    thisObject: t.Union[note.Note|note.Rest]
    # Detect rests first, because rests can contain manual positioning information,
    # which is also detected by the `matchedNote` variable above.
    thisObject: note.GeneralNote
    if 'r' in contents:
        thisObject = note.Rest(duration=thisDuration)

    elif matchedNote := re.search('([a-gA-G]+)([n#-]*)', contents):
        kernNoteName = matchedNote.group(1)
        step = kernNoteName[0].lower()
        if step == kernNoteName[0]:  # middle C or higher
            octave = 3 + len(kernNoteName)
        else:  # below middle C
            octave = 4 - len(kernNoteName)

        accid = matchedNote.group(2)
        if accid:
            _pitch = pitch.Pitch(step, octave=octave, accidental=accid)
        else:
            _pitch = pitch.Pitch(step, octave=octave)

        thisObject = note.Note(_pitch, duration=thisDuration)

    else:
        raise HumdrumException(f'Could not parse {contents} for note information')

    # 3.2.2 -- Slurs, Ties, Phrases
    # TODO: add music21 phrase information
    # for i in range(contents.count('{')):
    #     pass  # phraseMark start
    # for i in range(contents.count('}')):
    #     pass  # phraseMark end
    # for i in range(contents.count('(')):
    #     pass  # slur start
    # for i in range(contents.count(')')):
    #     pass  # slur end
    if '[' in contents:
        thisObject.tie = tie.Tie('start')
    elif ']' in contents:
        thisObject.tie = tie.Tie('stop')
    elif '_' in contents:
        thisObject.tie = tie.Tie('continue')

    # 3.2.3 Ornaments
    if 't' in contents:
        thisObject.expressions.append(expressions.HalfStepTrill())
    elif 'T' in contents:
        thisObject.expressions.append(expressions.WholeStepTrill())

    if 'w' in contents:
        thisObject.expressions.append(expressions.HalfStepInvertedMordent())
    elif 'W' in contents:
        thisObject.expressions.append(expressions.WholeStepInvertedMordent())
    elif 'm' in contents:
        thisObject.expressions.append(expressions.HalfStepMordent())
    elif 'M' in contents:
        thisObject.expressions.append(expressions.WholeStepMordent())

    if 'S' in contents:
        thisObject.expressions.append(expressions.Turn())
    elif '$' in contents:
        thisObject.expressions.append(expressions.InvertedTurn())
    elif 'R' in contents:
        t1 = expressions.Turn()
        t1.connectedToPrevious = True  # true by default, but explicitly
        thisObject.expressions.append(t1)

    # if ':' in contents:
    #     # TODO: deal with arpeggiation -- should have been in a
    #     #  chord structure
    #     pass

    if 'O' in contents:
        thisObject.expressions.append(expressions.Ornament())
        # generic ornament

    # 3.2.4 Articulation Marks
    if "'" in contents:
        thisObject.articulations.append(articulations.Staccato())
    if '"' in contents:
        thisObject.articulations.append(articulations.Pizzicato())
    if '`' in contents:
        # called 'attacca' mark but means staccatissimo:
        # http://www.music-cog.ohio-state.edu/Humdrum/representations/kern.rep.html
        thisObject.articulations.append(articulations.Staccatissimo())
    if '~' in contents:
        thisObject.articulations.append(articulations.Tenuto())
    if '^' in contents:
        thisObject.articulations.append(articulations.Accent())
    if ';' in contents:
        thisObject.expressions.append(expressions.Fermata())

    # 3.2.5 Up & Down Bows
    if 'v' in contents:
        thisObject.articulations.append(articulations.UpBow())
    elif 'u' in contents:
        thisObject.articulations.append(articulations.DownBow())

    # 3.2.9 Grace Notes and Groupettos
    if (qCount := contents.count('q')):
        thisObject.getGrace(inPlace=True)
        if qCount == 2:
            thisObject.duration.slash = False  # type: ignore
    elif 'Q' in contents:
        thisObject.getGrace(inPlace=True)
        thisObject.duration.slash = False  # type: ignore
    elif 'P' in contents:
        thisObject.getGrace(appoggiatura=True, inPlace=True)
    # elif 'p' in contents:
    #     pass  # end appoggiatura duration -- not needed in music21...

    if thisObject.isNote:  # handle note-specific attributes
        # 3.2.6 Stem Directions
        if '/' in contents:
            thisObject.stemDirection = 'up'
        elif '\\' in contents:
            thisObject.stemDirection = 'down'

        # 3.2.10 Beaming
        # TODO: Support really complex beams
        for i in range(contents.count('L')):
            thisObject.beams.append('start')
        for i in range(contents.count('J')):
            thisObject.beams.append('stop')
        for i in range(contents.count('k')):
            thisObject.beams.append('partial', 'right')
        for i in range(contents.count('K')):
            thisObject.beams.append('partial', 'right')

    return thisObject

def hdStringToMeasure(
    contents: str,
    previousMeasure: stream.Measure|None = None,
) -> stream.Measure:
    '''
    kern uses an equals sign followed by processing instructions to
    create new measures.

    * Changed in v10: repeat dots are encoded as :class:`~music21.bar.Repeat`
        objects instead of being stuffed into a non-existent ``Barline.repeatDots``
        attribute.  ``:|:`` now produces an end-Repeat on the previous measure's
        right barline AND a start-Repeat on the new measure's left barline.
    '''
    if contents == '==|':
        environLocal.warn(
            '"Double bar visually rendered as a single bar" is not supported '
            'in music21; storing as a double bar.')

    m = stream.Measure()
    match_measure_number = re.search(r'(\d+)([a-z]?)', contents)
    if match_measure_number:
        m.number = int(match_measure_number.group(1))
        if match_measure_number.group(2):
            m.numberSuffix = match_measure_number.group(2)

    # Bar type from the bar character(s).
    barType = ''
    if '-' in contents:
        barType = 'none'
    elif "'" in contents:
        barType = 'short'
    elif '`' in contents:
        barType = 'tick'
    elif '||' in contents or '==' in contents:
        barType = 'double'
    elif '!!' in contents:
        barType = 'heavy-heavy'
    elif '|!' in contents:
        barType = 'final'
    elif '!|' in contents:
        barType = 'heavy-light'
    elif '|' in contents:
        barType = 'regular'

    # Repeat dots:
    #   ':' before a bar character → end-repeat (dots on the left of the bar)
    #   ':' after a bar character  → start-repeat (dots on the right of the bar)
    #   two or more ':' anywhere   → both
    bothRepeats = contents.count(':') > 1
    endRepeat = bothRepeats or bool(re.search(r':[|!=]', contents))
    startRepeat = bothRepeats or bool(re.search(r'[|!=]:', contents))

    def makeBar(direction: str|None) -> bar.Barline:
        if direction is not None:
            b: bar.Barline = bar.Repeat(direction=direction)
        else:
            b = bar.Barline()
        if barType:
            b.type = barType
        return b

    rightBar = makeBar('end' if endRepeat else None)
    if ';' in contents:
        rightBar.pause = expressions.Fermata()

    if previousMeasure is not None:
        previousMeasure.rightBarline = rightBar
        if startRepeat:
            m.leftBarline = makeBar('start')
    else:
        # No previous measure to attach to: put whatever we have on m's left.
        m.leftBarline = makeBar('start') if startRepeat else rightBar

    return m

def kernTandemToObject(tandem: str) -> base.Music21Object|None:
    '''
    Kern uses symbols such as :samp:`*M5/4` and :samp:`*clefG2`, etc., to control processing

    This method converts them to music21 objects.

    >>> m = humdrum.spineParser.kernTandemToObject('*M3/1')
    >>> m
    <music21.meter.TimeSignature 3/1>

    Unknown objects are converted to MiscTandem objects:

    >>> m2 = humdrum.spineParser.kernTandemToObject('*TandyUnk')
    >>> m2
    <music21.humdrum.spineParser.MiscTandem *TandyUnk>
    '''
    # TODO: Cover more tandem controls as they're found
    if tandem in spinePathIndicators:
        return None
    elif tandem.startswith('*clef'):
        clefType = tandem[5:]
        if clefType == '-':
            return clef.NoClef()
        elif clefType == 'X':
            return clef.PercussionClef()
        elif clefType == 'Gv2':  # undocumented in Humdrum, but appears in Huron's Chorales
            return clef.Treble8vbClef()
        elif clefType == 'Gv':  # unknown if ever used but better safe.
            return clef.Treble8vbClef()
        elif clefType == 'G^2':  # unknown if ever used but better safe.
            return clef.Treble8vaClef()
        elif clefType == 'G^':  # unknown if ever used but better safe.
            return clef.Treble8vaClef()
        elif clefType == 'Fv4':  # unknown if ever used but better safe.
            return clef.Bass8vbClef()
        elif clefType == 'Fv':  # unknown if ever used but better safe.
            return clef.Bass8vbClef()
        else:
            try:
                clefFromString = clef.clefFromString(clefType)
                return clefFromString
            except clef.ClefException:
                raise HumdrumException(f'Unknown clef type {tandem} found')
    elif tandem.startswith('*MM'):
        metronomeMarkText = tandem[3:]
        try:
            metronomeMarkNumber = float(metronomeMarkText)
            MM = tempo.MetronomeMark(number=metronomeMarkNumber)
            return MM
        except ValueError:
            # assuming that metronomeMarkText is text now
            metronomeMarkText = re.sub(r'^\[', '', metronomeMarkText)
            metronomeMarkText = re.sub(r']\s*$', '', metronomeMarkText)
            MS = tempo.MetronomeMark(text=metronomeMarkText)
            return MS
    elif tandem.startswith('*M'):
        meterType = tandem[2:]
        tsTemp = re.match(r'(\d+)/(\d+)', meterType)
        if tsTemp:
            numerator = int(tsTemp.group(1))
            denominatorStr = tsTemp.group(2)
            if denominatorStr not in ('0', '00', '000'):
                return meter.TimeSignature(meterType)
            else:
                denominator = 1
                if denominatorStr == '0':
                    numerator *= 2
                elif denominatorStr == '00':
                    numerator *= 4
                elif denominatorStr == '000':
                    numerator *= 8
                return meter.TimeSignature(f'{numerator}/{denominator}')
        else:
            raise HumdrumException(f'Incorrect meter: {tandem} found')

    elif tandem.startswith('*IC'):
        instrumentClass = tandem[3:]
        try:
            iObj = instruments.fromHumdrumClass(instrumentClass)
            return iObj
        except instruments.HumdrumInstrumentException:
            return MiscTandem(instrumentClass)
    elif tandem.startswith('*IG'):
        # instrumentGroup = tandem[3:]
        return MiscTandem(tandem)
        # TODO: DO SOMETHING WITH INSTRUMENT GROUP; not in hum2xml
    elif tandem.startswith('*ITr'):
        # instrumentTransposing = True
        return MiscTandem(tandem)
        # TODO: DO SOMETHING WITH TRANSPOSING INSTRUMENTS; not in hum2xml
    elif tandem.startswith('*I'):  # order has to be last
        instrumentStr = tandem[2:]
        try:
            iObj = instruments.fromHumdrumInstrument(instrumentStr)
            return iObj
        except instruments.HumdrumInstrumentException:
            return MiscTandem(instrumentStr)
    elif tandem.startswith('*k'):
        numSharps = tandem.count('#')
        if numSharps == 0:
            numSharps = -1 * (tandem.count('-'))
        return key.KeySignature(numSharps)
    elif tandem.endswith(':'):
        thisKey = tandem[1:-1]
        return key.Key(thisKey)
    else:
        return MiscTandem(tandem)

    # elif tandem.startswith('*>'):
    #     # TODO: Something with 4.2 Repetitions; not in hum2xml
    #     pass
    # elif tandem.startswith('*tb'):
    #     timeBase = tandem[4:]
    #     # TODO: Find out what timeBase means; not in hum2xml
    #     pass
    # elif tandem.startswith('*staff'):
    #     staffNumbers = tandem[6:]
    #     # TODO: make staff numbers relevant; not in hum2xml
    # TODO: Parse editorial signifiers


class MiscTandem(base.Music21Object):
    def __init__(self, tandem: str = '', **keywords) -> None:
        super().__init__(**keywords)
        self.tandem: str = tandem

    def _reprInternal(self) -> str:
        return f'{self.tandem}'


class SpineComment(base.Music21Object):
    '''
    A Music21Object that represents a comment in a single spine.

    >>> sc = humdrum.spineParser.SpineComment('! this is a spine comment')
    >>> sc
    <music21.humdrum.spineParser.SpineComment 'this is a spine comment'>
    >>> sc.comment
    'this is a spine comment'
    '''
    def __init__(self, comment: str = '', **keywords) -> None:
        super().__init__(**keywords)
        commentPart = re.sub(r'^!+\s?', '', comment)
        self.comment: str = commentPart

    def _reprInternal(self) -> str:
        return repr(self.comment)


class GlobalComment(base.Music21Object):
    '''
    A Music21Object that represents a comment for the whole score.

    >>> sc = humdrum.spineParser.GlobalComment('!! this is a global comment')
    >>> sc
    <music21.humdrum.spineParser.GlobalComment 'this is a global comment'>
    >>> sc.comment
    'this is a global comment'
    '''
    def __init__(self, comment: str = '', **keywords) -> None:
        super().__init__(**keywords)
        commentPart = re.sub(r'^!!+\s?', '', comment)
        commentPart = commentPart.strip()
        self.comment: str = commentPart

    def _reprInternal(self) -> str:
        return repr(self.comment)


class GlobalReference(base.Music21Object):
    # noinspection SpellCheckingInspection
    '''
    A Music21Object that represents a reference in the score, called a "reference record"
    in Humdrum.  See Humdrum User's Guide Chapter 2.

    >>> sc = humdrum.spineParser.GlobalReference('!!!REF:this is a global reference')
    >>> sc
    <music21.humdrum.spineParser.GlobalReference REF 'this is a global reference'>
    >>> sc.code
    'REF'
    >>> sc.value
    'this is a global reference'

    Alternate form:

    >>> sc = humdrum.spineParser.GlobalReference('REF', 'this is a global reference')
    >>> sc
    <music21.humdrum.spineParser.GlobalReference REF 'this is a global reference'>
    >>> sc.code
    'REF'
    >>> sc.value
    'this is a global reference'

    Language codes are parsed:

    >>> sc = humdrum.spineParser.GlobalReference('!!!OPT@@RUS: Vesna svyashchennaya')
    >>> sc.code
    'OPT'
    >>> sc.language
    'RUS'
    >>> sc.isPrimary
    True

    >>> sc = humdrum.spineParser.GlobalReference('!!!OPT@FRE: Le sacre du printemps')
    >>> sc.code
    'OPT'
    >>> sc.language
    'FRE'
    >>> sc.isPrimary
    False
    '''
    def __init__(
        self,
        codeOrAll: str = '',
        valueOrNone: str|None = None,
        **keywords,
    ) -> None:
        super().__init__(**keywords)
        codeOrAll = re.sub(r'^!!!+', '', codeOrAll)
        codeOrAll = codeOrAll.strip()
        if valueOrNone is None and ':' in codeOrAll:
            valueOrNone = re.sub(r'^.*?:', '', codeOrAll)
            codeOrAll = re.sub(r':.*$', '', codeOrAll)
        self.code: str = codeOrAll
        self.value: str|None = valueOrNone
        self.language: str|None = None  # does it have a language code?
        self.isPrimary: bool = False  # is this language marked as primary?
        if '@@' in self.code:
            self.isPrimary = True
            self.code = self.code.replace('@@', '@')
        if '@' in self.code:
            self.code, self.language = self.code.split('@')

    humdrumKeyToUniqueName: dict[str, str] = {
        # dict value is music21's unique name or '' (if there is no supported equivalent)
        # Authorship information:
        'COM': 'composer',              # composer's name
        'COA': 'attributedComposer',    # attributed composer
        'COS': 'suspectedComposer',     # suspected composer
        'COL': 'composerAlias',         # composer's abbreviated, alias, or stage name
        'COC': 'composerCorporate',     # composer's corporate name
        'CDT': '',  # composer's birth and death dates (**zeit format)
        'CBL': '',  # composer's birth location
        'CDL': '',  # composer's death location
        'CNT': '',  # composer's nationality
        'LYR': 'lyricist',  # lyricist's name
        'LIB': 'librettist',    # librettist's name
        'LAR': 'arranger',  # music arranger's name
        'LOR': 'orchestrator',  # orchestrator's name
        'TXO': 'textOriginalLanguage',  # original language of vocal/choral text
        'TXL': 'textLanguage',  # language of the encoded vocal/choral text
        # Recording information (if the Humdrum encodes information pertaining
        # to an audio recording)
        'TRN': 'translator',  # translator of the text
        'RTL': '',  # album title
        'RMM': 'manufacturer',  # manufacturer or sponsoring company
        'RC#': '',  # recording company's catalog number of album
        'RRD': 'dateIssued',  # release date (**date format)
        'RLC': '',  # place of recording
        'RNP': 'producer',  # producer's name
        'RDT': '',  # date of recording (**date format)
        'RT#': '',  # track number
        # Performance information (if the Humdrum encodes, say, a MIDI performance)
        'MGN': '',  # ensemble's name
        'MPN': '',  # performer's name
        'MPS': '',  # suspected performer
        'MRD': '',  # date of performance (**date format)
        'MLC': '',  # place of performance
        'MCN': 'conductor',  # conductor's name
        'MPD': '',  # date of first performance (**date format)
        'MDT': '',  # unknown, but I've seen 'em (another way to say date of performance?)
        # Work identification information
        'OTL': 'title',  # title
        'OTP': 'popularTitle',  # popular title
        'OTA': 'alternativeTitle',  # alternative title
        'OPR': 'parentTitle',  # title of parent work
        'OAC': 'actNumber',  # act number (e.g. '2' or 'Act 2')
        'OSC': 'sceneNumber',  # scene number (e.g. '3' or 'Scene 3')
        'OMV': 'movementNumber',  # movement number (e.g. '4', or 'mov. 4')
        'OMD': 'movementName',  # movement name
        'OPS': 'opusNumber',  # opus number (e.g. '23', or 'Opus 23')
        'ONM': 'number',  # number (e.g. number of song within ABC multi-song file)
        'OVM': 'volumeNumber',  # volume number (e.g. '6' or 'Vol. 6')
        'ODE': 'dedicatedTo',  # dedicated to
        'OCO': 'commission',  # commissioned by
        'OCL': 'transcriber',  # collected/transcribed by
        'ONB': '',  # free form note (nota bene) related to title or identity of work
        'ODT': 'dateCreated',  # date or period of composition (**date or **zeit format)
        'OCY': 'countryOfComposition',  # country of composition
        'OPC': 'localeOfComposition',  # city, town, or village of composition
        # Group information
        'GTL': 'groupTitle',  # group title (e.g. 'The Seasons')
        'GAW': 'associatedWork',  # associated work, such as a play or film
        'GCO': 'collectionDesignation',  # collection designation (e.g. 'Norton Scores')
        # Imprint information
        'PUB': '',  # publication status 'published'/'unpublished'
        'PED': '',  # publication editor
        'PPR': 'firstPublisher',  # first publisher
        'PDT': 'dateFirstPublished',  # date first published (**date format)
        'PTL': 'publicationTitle',  # publication (volume) title
        'PPP': 'placeFirstPublished',  # place first published
        'PC#': 'publishersCatalogNumber',  # publisher's catalog number (NOT scholarly catalog)
        'SCT': 'scholarlyCatalogAbbreviation',  # scholarly catalog abbrev/number (e.g. 'BWV 551')
        'SCA': 'scholarlyCatalogName',  # scholarly catalog (unabbreviated) (e.g. 'Koechel 117')
        'SMS': 'manuscriptSourceName',  # unpublished manuscript source name
        'SML': 'manuscriptLocation',  # unpublished manuscript location
        'SMA': 'manuscriptAccessAcknowledgement',  # acknowledgment of manuscript access
        'YEP': 'electronicPublisher',  # publisher of electronic edition
        'YEC': 'copyright',  # date and owner of electronic copyright
        'YER': 'electronicReleaseDate',  # date electronic edition released
        'YEM': '',  # copyright message (e.g. 'All rights reserved')
        'YEN': '',  # country of copyright
        'YOR': '',  # original document from which encoded document was prepared
        'YOO': 'originalDocumentOwner',  # original document owner
        'YOY': '',  # original copyright year
        'YOE': 'originalEditor',  # original editor
        'EED': 'electronicEditor',  # electronic editor
        'ENC': 'electronicEncoder',  # electronic encoder (person)
        'END': '',  # encoding date
        'EMD': '',  # electronic document modification description (one per modification)
        'EEV': '',  # electronic edition version
        'EFL': '',  # file number e.g. '1/4' for one of four
        'EST': '',  # encoding status (free form, normally eliminated prior to distribution)
        'VTS': '',  # checksum (excluding the VTS line itself)
        # Analytic information
        'ACO': '',  # collection designation
        'AFR': '',  # form designation
        'AGN': '',  # genre designation
        'AST': '',  # style, period, or type of work designation
        'AMD': '',  # mode classification e.g. '5; Lydian'
        'AMT': '',  # metric classification, must be one of eight specific names
        'AIN': '',  # instrumentation; alphabetically ordered list of *I abbrevs, space-delimited
        'ARE': '',  # geographical region of origin (list of 'narrowing down' names of regions)
        'ARL': '',  # geographical location of origin (lat/long)
        # Historical and background information
        'HAO': '',  # aural history (lots of text, stories about the work)
        'HTX': '',  # freeform translation of vocal text
        # Representation information
        'RLN': '',  # Extended ASCII language code
        'RNB': '',  # a note about the representation
        'RWB': ''  # a warning about the representation
    }

    def updateMetadata(self, md: metadata.Metadata) -> None:
        '''
        update a metadata object according to information in this GlobalReference

        See Humdrum guide Appendix I for information
        '''
        c = self.code
        v = self.value

        uniqueName: str = self.humdrumKeyToUniqueName.get(c, '')
        if uniqueName:
            md.add(uniqueName, v)
        elif c in self.humdrumKeyToUniqueName:
            # it's a Humdrum key, but unsupported
            md.addCustom('humdrum:' + c, v)
        else:
            # it's a free-form key
            md.addCustom(c, v)

    def _reprInternal(self) -> str:
        return f'{self.code} {self.value!r}'


class Test(unittest.TestCase):
    '''
    Note: most spineParser tests are in :mod:`music21.humdrum.tests`.
    Only `testCopyAndDeepcopy` lives here so that `globals()` resolves.
    '''
    def testCopyAndDeepcopy(self) -> None:
        from music21.test.commonTest import testCopyAll
        testCopyAll(self, globals())


        hf1 = HumdrumDataCollection(testFiles.mazurka6)
        hf1.parse()

        # hf1 = HumdrumFile('d:/web/eclipse/music21misc/ojibway.krn')
        # for thisEventCollection in hf1.eventCollections:
        #     ev = thisEventCollection.getSpineEvent(0).contents
        #     if ev is not None:
        #         print(ev)
        #     else:
        #         print('NONE')
        #
        # for mySpine in hf1.spineCollection:
        #     print('\n\n***NEW SPINE: No. ' + str(mySpine.id) + ' parentSpine: '
        #         + str(mySpine.parentSpine) + ' childSpines: ' + str(mySpine.childSpines))
        #     print(mySpine.spineType)
        #     for childSpinesSpine in mySpine.childSpinesSpines():
        #         print(str(childSpinesSpine.id) + ' *** testing spineCollection code ***')
        #     for thisEvent in mySpine:
        #         print(thisEvent.contents)
        spine5 = hf1.spineCollection.getSpineById(5)
        self.assertEqual(spine5.id, 5)
        self.assertEqual(spine5.parentSpine.id, 1)

        spine1 = hf1.spineCollection.getSpineById(1)
        spine1Children = [cs.id for cs in spine1.childSpines]
        self.assertEqual(spine1Children,
                         [5, 6, 9, 10, 13, 14, 23, 24, 27, 28, 31, 32, 35, 36, 39, 40])

        self.assertEqual(spine5.spineType, 'kern')
        self.assertIsInstance(spine5, KernSpine)

    def testSingleNote(self):
        # noinspection SpellCheckingInspection
        a = SpineEvent('40..ccccc##_wtLLK~v/')
        b = a.toNote()
        self.assertEqual(b.pitch.accidental.name, 'double-sharp')
        self.assertEqual(b.duration.dots, 0)
        self.assertEqual(b.duration.tuplets[0].durationNormal.dots, 2)

    def testGraceNote(self):
        ks = KernSpine()
        # noinspection SpellCheckingInspection
        a = ks.processNoteEvent('4Cq')
        self.assertEqual(a.duration.type, 'quarter')
        self.assertEqual(a.duration.slash, True)

    def testGraceNote2(self):
        ks = KernSpine()
        # noinspection SpellCheckingInspection
        a = ks.processNoteEvent('16Cqq')
        self.assertEqual(a.duration.type, '16th')
        self.assertEqual(a.duration.slash, False)

    def testChord(self):
        ks = KernSpine()
        # noinspection SpellCheckingInspection
        c = ks.processChordEvent('8C 8E')
        self.assertEqual(len(c.notes), 2)
        self.assertEqual(c.notes[0].duration, c.duration)

    def testChord2(self):
        # noinspection SpellCheckingInspection
        ks = KernSpine()
        c = ks.processChordEvent('8C E')
        self.assertEqual(c.notes[0].duration, c.notes[1].duration)

    def testMeasureBoundaries(self):
        m0 = stream.Measure()
        m1 = hdStringToMeasure('=29a;:|:', m0)
        self.assertEqual(m1.number, 29)
        self.assertEqual(m1.numberSuffix, 'a')
        self.assertEqual(m0.rightBarline.type, 'regular')
        self.assertEqual(m0.rightBarline.repeatDots, 'both')
        self.assertIsNotNone(m0.rightBarline.pause)
        self.assertIsInstance(m0.rightBarline.pause, expressions.Fermata)

    def testMeterBreve(self):
        m = kernTandemToObject('*M3/1')
        self.assertEqual(str(m), '<music21.meter.TimeSignature 3/1>')
        m = kernTandemToObject('*M3/0')
        self.assertEqual(str(m), '<music21.meter.TimeSignature 6/1>')
        m = kernTandemToObject('*M3/00')
        self.assertEqual(str(m), '<music21.meter.TimeSignature 12/1>')
        m = kernTandemToObject('*M3/000')
        self.assertEqual(str(m), '<music21.meter.TimeSignature 24/1>')

    def x_testFakePiece(self):
        '''
        test loading a fake piece with spine paths, lyrics, dynamics, etc.
        '''
        hdc = HumdrumDataCollection(testFiles.fakeTest)
        hdc.parse()
        ms = hdc.stream
        ms.show()

    def testSpineMazurka(self):
        # hf1 = HumdrumFile('d:/web/eclipse/music21misc/mazurka06-2.krn')
        hf1 = HumdrumDataCollection(testFiles.mazurka6)
        # hf1 = HumdrumDataCollection(testFiles.ojibway)
        # hf1 = HumdrumDataCollection(testFiles.schubert)
        # hf1 = HumdrumDataCollection(testFiles.ivesSpring)
        # hf1 = HumdrumDataCollection(testFiles.sousaStars)  # parse errors b/c of graces
        hf1.parse()
        masterStream = hf1.stream
        # for spineX in hf1.spineCollection:
        #     spineX.stream.id = 'spine %s' % str(spineX.id)
        #     masterStream.append(spineX.stream)
        # self.assertTrue(common.whitespaceEqual
        #                  (common.stripAddresses(expectedOutput),
        #                   common.stripAddresses(masterStream._reprText())))
        # print(common.stripAddresses(expectedOutput))
        # print(common.stripAddresses(masterStream.recurseRepr()))

        # humdrum type problem: how many G#s start on beat 2 of a measure?
        gSharpCount = 0
        # masterStream.show('text')
        for n in masterStream.recurse():
            if hasattr(n, 'pitch') and n.pitch.name == 'G#':
                if n.beat == 2:  # beat doesn't work... :-(
                    gSharpCount += 1
            elif hasattr(n, 'pitches'):
                for p in n.pitches:
                    if p.name == 'G#' and n.beat == 2:
                        gSharpCount += 1
        # masterStream.show()
        self.assertEqual(gSharpCount, 86)
        # masterStream.show()
        # masterStream.show('text')

    def testParseSineNomine(self):
        from music21 import converter
        parserPath = common.getSourceFilePath() / 'humdrum'
        sineNominePath = parserPath / 'Missa_Sine_nomine-Kyrie.krn'
        unused_myScore = converter.parse(sineNominePath)
        # unused_myScore.show('text')

    def testSplitSpines(self):
        hf1 = HumdrumDataCollection(testFiles.splitSpines2)
        hf1.parse()
        masterStream = hf1.stream
        self.assertTrue(masterStream.parts[0].measure(4).hasVoices())
        self.assertFalse(masterStream.parts[0].measure(5).hasVoices())

    def x_testMoveDynamics(self):
        hf1 = HumdrumDataCollection(testFiles.fakeTest)
        hf1.parse()
        # hf1.spineCollection.moveDynamicsAndLyricsToStreams()
        unused_s = hf1.stream
        # unused_s.show('text')

    def testLyricsInSpine(self):
        from music21 import text
        hf1 = HumdrumDataCollection(testFiles.fakeTest)
        hf1.parse()
        # hf1.spineCollection.moveDynamicsAndLyricsToStreams()
        s = hf1.stream
        lyrics = text.assembleLyrics(s)
        # noinspection SpellCheckingInspection
        self.assertEqual(lyrics, 'Magijago ickewyan')

    def testSplitSpines2(self):
        '''
        Currently this does not work since a second split on a stream that
        already resulted from a split does not parse properly.  Shows up also
        in strangeWTCOpening, below.
        '''
        hf1 = HumdrumDataCollection(testFiles.splitLots)
        hf1.parse()
        unused_masterStream = hf1.stream

    def testParseStrangeSplit(self):
        hf1 = HumdrumDataCollection(testFiles.strangeWTCOpening)
        unused_masterStream = hf1.stream

    def testSpineComments(self):
        hf1 = HumdrumDataCollection(testFiles.fakeTest)
        hf1.parse()
        s = hf1.stream  # .show()
        p = s.parts[2]  # last part has a comment
        comments = []
        for c in p[SpineComment]:
            comments.append(c.comment)
        self.assertTrue('spine comment' in comments)
        # s.show('text')

    def testHarmSpineDegrees(self):
        hf1 = HumdrumDataCollection(testFiles.harmScaleDegrees)
        hf1.parse()
        s = hf1.stream
        groundTruth = {
            0.0: ('I in C major', [0, 4, 7], 'C', 'C', 53, False),
            1.0: ('ii in C major', [2, 5, 9], 'D', 'D', 53, False),
            2.0: ('iii in C major', [4, 7, 11], 'E', 'E', 53, False),
            3.0: ('IV in C major', [5, 9, 0], 'F', 'F', 53, False),
            4.0: ('I64 in C major', [7, 0, 4], 'C', 'G', 64, False),
            5.0: ('V in C major', [7, 11, 2], 'G', 'G', 53, False),
            6.0: ('vi in C major', [9, 0, 4], 'A', 'A', 53, False),
            7.0: ('V6 in C major', [11, 2, 7], 'G', 'B', 6, False),
            8.0: ('viio65/i in C major', [2, 5, 8, 11], 'B', 'D', 65, True),
            9.0: ('I in C major', [0, 4, 7], 'C', 'C', 53, False),
            11.0: ('I in C major', [0, 4, 7], 'C', 'C', 53, False),
            12.0: ('i in c minor', [0, 3, 7], 'C', 'C', 53, False),
            13.0: ('iio in c minor', [2, 5, 8], 'D', 'D', 53, False),
            14.0: ('III in c minor', [3, 7, 10], 'E-', 'E-', 53, False),
            15.0: ('N6 in c minor', [5, 8, 1], 'D-', 'F', 6, False),
            16.0: ('i64 in c minor', [7, 0, 3], 'C', 'G', 64, False),
            17.0: ('V in c minor', [7, 11, 2], 'G', 'G', 53, False),
            18.0: ('It6 in c minor', [8, 0, 6], 'F#', 'A-', 6, False),
            20.0: ('V in c minor', [7, 11, 2], 'G', 'G', 53, False),
            21.0: ('Fr43 in c minor', [8, 0, 2, 6], 'D', 'A-', 43, True),
            23.0: ('V in c minor', [7, 11, 2], 'G', 'G', 53, False),
            24.0: ('Ger65 in c minor', [8, 0, 3, 6], 'F#', 'A-', 65, True),
            27.0: ('iv in c minor', [5, 8, 0], 'F', 'F', 53, False),
            30.0: ('V in c minor', [7, 11, 2], 'G', 'G', 53, False),
            32.0: ('V in c minor', [7, 11, 2], 'G', 'G', 53, False),
            33.0: ('I in c minor', [0, 4, 7], 'C', 'C', 53, False)
        }
        for harm in s.flatten().getElementsByClass(roman.RomanNumeral):
            figureAndKey = harm.figureAndKey
            pitchClasses = harm.pitchClasses
            root = harm.root().name
            bass = harm.bass().name
            inversionName = harm.inversionName()
            isSeventh = harm.isSeventh()
            assertTuple = (
                figureAndKey,
                pitchClasses,
                root,
                bass,
                inversionName,
                isSeventh
            )
            self.assertEqual(assertTuple, groundTruth[harm.offset])

    def testHarmSpineSevenths(self):
        hf1 = HumdrumDataCollection(testFiles.harmSevenths)
        hf1.parse()
        s = hf1.stream
        groundTruth = {
            0.0: ('I7 in C major', [0, 4, 7, 11], 'C', 'C', 7, True),
            1.0: ('IV7 in C major', [5, 9, 0, 4], 'F', 'F', 7, True),
            2.0: ('viio7 in C major', [11, 2, 5, 8], 'B', 'B', 7, True),
            3.0: ('iii7 in C major', [4, 7, 11, 2], 'E', 'E', 7, True),
            4.0: ('vi7 in C major', [9, 0, 4, 7], 'A', 'A', 7, True),
            5.0: ('ii7 in C major', [2, 5, 9, 0], 'D', 'D', 7, True),
            6.0: ('V7 in C major', [7, 11, 2, 5], 'G', 'G', 7, True),
            7.0: ('I in C major', [0, 4, 7], 'C', 'C', 53, False),
            12.0: ('i7 in a minor', [9, 0, 4, 7], 'A', 'A', 7, True),
            13.0: ('iv7 in a minor', [2, 5, 9, 0], 'D', 'D', 7, True),
            14.0: ('-VII7 in a minor', [7, 11, 2, 5], 'G', 'G', 7, True),
            15.0: ('III7 in a minor', [0, 4, 7, 11], 'C', 'C', 7, True),
            16.0: ('VI7 in a minor', [5, 9, 0, 4], 'F', 'F', 7, True),
            17.0: ('iio7 in a minor', [11, 2, 5, 8], 'B', 'B', 7, True),
            18.0: ('V7 in a minor', [4, 8, 11, 2], 'E', 'E', 7, True),
            19.0: ('i in a minor', [9, 0, 4], 'A', 'A', 53, False),
            24.0: ('I65 in C major', [4, 7, 11, 0], 'C', 'E', 65, True),
            25.0: ('IV2 in C major', [4, 5, 9, 0], 'F', 'E', 42, True),
            26.0: ('viio65 in C major', [2, 5, 8, 11], 'B', 'D', 65, True),
            27.0: ('iii2 in C major', [2, 4, 7, 11], 'E', 'D', 42, True),
            28.0: ('vi43 in C major', [4, 7, 9, 0], 'A', 'E', 43, True),
            29.0: ('ii7 in C major', [2, 5, 9, 0], 'D', 'D', 7, True),
            30.0: ('V43 in C major', [2, 5, 7, 11], 'G', 'D', 43, True),
            31.0: ('I in C major', [0, 4, 7], 'C', 'C', 53, False),
            36.0: ('i65 in a minor', [0, 4, 7, 9], 'A', 'C', 65, True),
            37.0: ('iv2 in a minor', [0, 2, 5, 9], 'D', 'C', 42, True),
            38.0: ('-VII65 in a minor', [11, 2, 5, 7], 'G', 'B', 65, True),
            39.0: ('III2 in a minor', [11, 0, 4, 7], 'C', 'B', 42, True),
            40.0: ('VI43 in a minor', [0, 4, 5, 9], 'F', 'C', 43, True),
            41.0: ('iio7 in a minor', [11, 2, 5, 8], 'B', 'B', 7, True),
            42.0: ('V43 in a minor', [11, 2, 4, 8], 'E', 'B', 43, True),
            43.0: ('i in a minor', [9, 0, 4], 'A', 'A', 53, False)
        }
        for harm in s.flatten().getElementsByClass(roman.RomanNumeral):
            figureAndKey = harm.figureAndKey
            pitchClasses = harm.pitchClasses
            root = harm.root().name
            bass = harm.bass().name
            inversionName = harm.inversionName()
            isSeventh = harm.isSeventh()
            assertTuple = (
                figureAndKey,
                pitchClasses,
                root,
                bass,
                inversionName,
                isSeventh
            )
            self.assertEqual(assertTuple, groundTruth[harm.offset])

    def testHarmSpineAugmentedSixths(self):
        hf1 = HumdrumDataCollection(testFiles.harmScaleDegrees)
        hf1.parse()
        s = hf1.stream
        groundTruth = {
            # Aug6, Italian, French, German
            0.0: (False, False, False, False),
            1.0: (False, False, False, False),
            2.0: (False, False, False, False),
            3.0: (False, False, False, False),
            4.0: (False, False, False, False),
            5.0: (False, False, False, False),
            6.0: (False, False, False, False),
            7.0: (False, False, False, False),
            8.0: (False, False, False, False),
            9.0: (False, False, False, False),
            11.0: (False, False, False, False),
            12.0: (False, False, False, False),
            13.0: (False, False, False, False),
            14.0: (False, False, False, False),
            15.0: (False, False, False, False),
            16.0: (False, False, False, False),
            17.0: (False, False, False, False),
            18.0: (True, True, False, False),
            20.0: (False, False, False, False),
            21.0: (True, False, True, False),
            23.0: (False, False, False, False),
            24.0: (True, False, False, True),
            27.0: (False, False, False, False),
            30.0: (False, False, False, False),
            32.0: (False, False, False, False),
            33.0: (False, False, False, False)
        }
        for harm in s.flatten().getElementsByClass(roman.RomanNumeral):
            isAugmentedSixth = harm.isAugmentedSixth()
            isItalianAugmentedSixth = harm.isItalianAugmentedSixth()
            isFrenchAugmentedSixth = harm.isFrenchAugmentedSixth()
            isGermanAugmentedSixth = harm.isGermanAugmentedSixth()
            assertTuple = (
                isAugmentedSixth,
                isItalianAugmentedSixth,
                isFrenchAugmentedSixth,
                isGermanAugmentedSixth
            )
            self.assertEqual(assertTuple, groundTruth[harm.offset])

    def testMetadataRetrieved(self):
        from music21 import corpus
        c = corpus.parse('palestrina/agnus_0')
        md = c.metadata
        self.assertIsNotNone(md.composer)
        self.assertIn('Palestrina', md.composer)

    def testFlavors(self):
        prevFlavor = flavors['JRP']
        flavors['JRP'] = False
        hdc = HumdrumDataCollection(testFiles.dottedTuplet)
        hdc.parse()
        c = hdc.stream
        flavors['JRP'] = True
        hdc2 = HumdrumDataCollection(testFiles.dottedTuplet)
        hdc2.parse()
        d = hdc2.stream
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
    show = True

    def testShowSousa(self):
        hf1 = HumdrumDataCollection(testFiles.sousaStars)
        hf1.parse()
        if self.show:
            hf1.stream.show()
# -----------------------------------------------------------------------------

if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
