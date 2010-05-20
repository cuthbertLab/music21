#-------------------------------------------------------------------------------
# Name:         humdrum.spineParser.py
# Purpose:      Conversion and Utility functions for Humdrum and kern in particular
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    (c) 2009 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import doctest
import unittest
import math
import re
import weakref
import music21.articulations
import music21.chord
import music21.dynamics

from music21 import duration
import music21.key
import music21.measure
import music21.note
import music21.expressions
import music21.tempo
import music21.meter
import music21.clef
import music21.stream
from music21.stream import Stream
from music21 import ElementWrapper
from music21 import common
from music21.humdrum import testFiles, canonicalOutput
from music21.dynamics import Dynamic, Wedge

spinePathIndicators = ["*+", "*-", "*^", "*v", "*x", "*"]

class HumdrumDataCollection(object):
    '''
    A HumdrumDataCollection takes in a mandatory list each of which is a line 
    of humdrum data.  Together this list represents a collection of spines.  
    
    Usually you will probably want to use HumdrumFile which can read 
    in a file directly.  This class exists in case you have your Humdrum
    data in another format (database, from the web, etc.) and already
    have it as a string.

    LIMITATION:    
    (1) Spines cannot change definition (**exclusive 
        interpretations) mid-spine.
    
        So if you start off with **kern, the rest of the spine needs to be 
        **kern (actually, the first exclusive interpretation for a spine is 
        used throughout)

        Note that, even though doing seems to be legal by
        the humdrum definition, it looks like none of the
        conventional humdrum parsing tools allow for changing 
        definitions mid-spine, so I don't think this limitation is a problem.
    
    You are probably better off running humdrum.parseFile("filename") 
    which returns a humdrum.SpineCollection directly
    '''
    def __init__(self, dataStream = [] ):
        if dataStream is []:
            raise HumdrumException("dataStream is not optional")
        elif isinstance(dataStream, basestring):
            dataStream = dataStream.splitlines()
        try:
            self.eventList = self.parseLines(dataStream)
        except IOError:          
            raise

    def parseLines(self, dataStream):
        eventList = []
        i = 0
        
        maxspines = 0

        for line in dataStream:
            line = line.rstrip()
            if line == "":
                continue # technically forbidden by Humdrum but the source of so many errors!
            elif re.match('\!\!\!', line):
                eventList.append(GlobalReference(i, line))
            elif re.match('\!\!', line): ## find global comments at the top of the line
                eventList.append(GlobalComment(i, line))
            else:
                thisLine = HumdrumSpineLine(i, line)
                if thisLine.numSpines > maxspines:
                    maxspines = thisLine.numSpines
                eventList.append(thisLine)
            i += 1
        fileLength = i
        self.fileLength = fileLength

        ## we make two lists: one of ProtoSpines (vertical slices) and 
        ##    one of Events(horizontal slices)
        returnProtoSpines = []
        returnEventCollections = []

        for j in range(0,maxspines):
            protoSpineEventList = []
            
            for i in range(0,fileLength):
                if j == 0:
                    thisEventCollection = EventCollection(maxspines)
                    returnEventCollections.append(thisEventCollection)
                else:
                    thisEventCollection = returnEventCollections[i]
                if eventList[i].isSpineLine is True:  ## or isGlobal is False
                    if len(eventList[i].spineData) > j:  
                        ## are there actually this many spines at this point?
                        thisEvent = SpineEvent(eventList[i].spineData[j])
                        thisEvent.position = i
                        thisEvent.protoSpineNum = j
                        if thisEvent.contents in spinePathIndicators:
                            thisEventCollection.spinePathData = True
                        
                        protoSpineEventList.append(thisEvent)
                        thisEventCollection.addSpineEvent(j, thisEvent)
                    else:  ## no data here
                        thisEvent = SpineEvent(None)
                        thisEvent.position = i
                        thisEvent.protoSpineNum = j
                        thisEventCollection.addSpineEvent(j, thisEvent)

                        protoSpineEventList.append(None)
                else:  ## Global event
                    if j == 0:
                        thisEventCollection.addGlobalEvent(eventList[i])
                    thisEvent = SpineEvent(None)
                    thisEvent.position = i
                    thisEvent.protoSpineNum = j
                    thisEventCollection.addSpineEvent(j, thisEvent)
                    protoSpineEventList.append(None)

            returnProtoSpines.append(ProtoSpine(protoSpineEventList))

        self.protoSpines = returnProtoSpines
        self.eventCollections = returnEventCollections
        self.spineCollection = self.parseProtoSpines(returnProtoSpines)
        self.spineCollection.reclass()
        self.spineCollection.parseMusic21()

    def parseProtoSpines(self, protoSpines):
        maxSpines = len(protoSpines)
        currentSpineList = common.defList(default = None)
        spineCollection = SpineCollection()
        
        for i in range(0, self.fileLength):
            thisEventCollection = self.eventCollections[i]                    
            for j in range(0, maxSpines):
                thisEvent = protoSpines[j].eventList[i]                 
               
                if thisEvent is not None:  # something there
                    currentSpine = currentSpineList[j]
                    if currentSpine is None: 
                        ## first event after a None = new spine because 
                        ## Humdrum does not require *+ at the beginning
                        currentSpine = spineCollection.addSpine()
                        currentSpine.beginningPosition = i
                        currentSpineList[j] = currentSpine
                    
                    currentSpine.append(thisEvent)
                    thisEvent.protoSpineNum = currentSpine.id

            '''
            Now we check for spinePathData (from HumdrumDoc):
            *+    add a new spine (to the right of the current spine)
            *-    terminate a current spine 
            *^    split a spine (into two)
            *v    join (two or more) spines into one
            *x    exchange the position of two spines
            *     do nothing
            '''
 
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
                    elif thisEvent.contents == "*^":  ## split spine
                        newSpine1 = spineCollection.addSpine()
                        newSpine1.beginningPosition = i+1
                        newSpine1.upstream = [currentSpine.id]
                        newSpine2 = spineCollection.addSpine()
                        newSpine2.beginningPosition = i+1
                        newSpine2.upstream = [currentSpine.id]
                        currentSpine.endingPosition = i
                        currentSpine.downstream = [newSpine1.id, newSpine2.id]
                        newSpineList.append(newSpine1)
                        newSpineList.append(newSpine2)
                    elif thisEvent.contents == "*v":  #merge spine -- n.b. we allow non-adjacent lines to be merged this is incorrect
                        if mergerActive is False:     #               per humdrum syntax, but is easily done.
                            mergeSpine = spineCollection.addSpine()
                            mergeSpine.beginningPosition = i+1
                            mergeSpine.upstream = [currentSpine.id]
                            mergerActive = mergeSpine
                            currentSpine.endingPosition = i
                            currentSpine.downstream = [mergeSpine.id]
                            newSpineList.append(mergeSpine)
                        else:  ## if second merger code is not found then a 1-1 spine "merge" occurs
                            mergeSpine = mergerActive
                            currentSpine.endingPosition = i
                            currentSpine.downstream = [mergeSpine.id]
                            mergeSpine.upstream.append(currentSpine.id)
                    elif thisEvent.contents == "*x":  # exchange spine    
                        if exchangeActive is False:
                            exchangeActive = currentSpine
                        else:  ## if second exchange is not found, then both lines disappear and exception is raised
                               ## n.b. we allow more than one PAIR of exchanges in a line
                            newSpineList.append(currentSpine)
                            newSpineList.append(exchangeActive)
                            exchangeActive = False;
                    else:  ## null processing code "*" 
                        newSpineList.append(currentSpine)
                        
                if exchangeActive is not False:
                    raise HumdrumException("Protospine found with unpaired exchange instruction")        
                currentSpineList = newSpineList
        return spineCollection

    def _getStream(self):
        if self.spineCollection is None:
            raise HumdrumException("parse lines first!")
        elif self.spineCollection.spines is None:
            raise HumdrumException("really? not a single spine in your data? um, not my problem!")
        elif self.spineCollection.spines[0].music21Objects is None:
            raise HumdrumException("okay, you got at least one spine, but it aint got nothing in it; have you thought of taking up kindergarten teaching?")
        else:
            masterStream = Stream()
            for thisSpine in self.spineCollection:
                thisSpine.music21Objects.id = "spine_" + str(thisSpine.id)
                masterStream.insert(thisSpine.music21Objects)
            return masterStream

    stream = property(_getStream)

class HumdrumFile(HumdrumDataCollection):
    '''
    A HumdrumFile is a HumdrumDataCollection which takes as a mandatory argument a filename to be opened and read.
    '''
    
    
    def __init__(self, filename = None):
        if (filename is None):
            raise HumdrumException("Filename is not optional")
        
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
    HumdrumLine is a dummy class for subclassing HumdrumSpineLine, GlobalComment, etc. classes
    all of which represent one horizontal line of text in a HumdrumFile
    '''
    isReference = False
    isGlobal = False
    isComment = False

class HumdrumSpineLine(HumdrumLine):
    '''
    A HumdrumSpineLine is any horizontal line of a Humdrum file that contains one or more spine elements
    and not Global elements
    '''
    position = 0
    contents = ""
    isSpineLine = True
    numSpines = 0
    
    def __init__(self, position = 0, contents = ""):
        self.position = position
        returnList = re.split("\t+", contents)
        self.numSpines = len(returnList)
        self.contents = contents
        self.spineData = returnList

class GlobalReference(HumdrumLine):
    '''
    A GlobalReference is a type of HumdrumLine that contains information about the humdrum document
    In humdrum it is represented by three exclamation points followed by non-whitespace followed by a colon
    
    !!!COM: Stravinsky, Igor Fyodorovich
    !!!CDT: 1882/6/17/-1971/4/6
    !!!ODT: 1911//-1913//; 1947//
    !!!OPT@@RUS: Vesna svyashchennaya
    !!!OPT@FRE: Le sacre du printemps

    The GlobalReference object takes two inputs:
        position (line number in the humdrum file)
        contents (string of contents)
    And stores them as three attributes:
        position (as above)
        code: non-whitespace code (usually three letters)
        contents (string of contents)
    
    TODO: add parsing of three-digit Kern comment codes
    '''
    position = 0
    contents = ""
    isGlobal = True
    isReference = True
    isComment = True
    isSpineLine = False
    numSpines = 0

    def __init__(self, position = 0, contents = ""):
        self.positon = position
        noExclaim = re.sub('^\!\!\!+','',contents)
        (code, value) = noExclaim.split(":", 1)
        value = value.strip()
        if (code is None):
            raise HumdrumException("!!! GlobalReference found without a code listed; this is probably a problem!")
        self.contents = contents
        self.code = code
        self.value = value
    
class GlobalComment(HumdrumLine):
    '''
    A GlobalComment is a humdrum comment that pertains to all spines
    In humdrum it is represented by two exclamation points (and usually one space)
    
    The GlobalComment object takes two inputs and stores them as attributes:
        position (line number in the humdrum file)
        contents (string of contents)
        value    (contents minus !!)

    The constructor can be passed (position, contents)
    if contents begins with bangs, they are removed along with up to one space directly afterwards
    '''
    position = 0
    contents = ""
    value    = ""
    isGlobal = True
    isComment = True
    isSpineLine = False
    numSpines = 0

    def __init__(self, position = 0, contents = ""):
        self.positon = position
        value = re.sub('^\!\!+/s','',contents)
        self.contents = contents
        self.value    = value

class ProtoSpine(object):
    '''
    A ProtoSpine is a collection of events arranged vertically.  It differs from a HumdrumSpine
    in that spine paths are not followed.  So ProtoSpine(1) would be everything in the 2nd column
    of a Humdrum file regardless of whether the 2nd column was at some point an independent Spine
    or if it later became a split from the first spine.
    '''
    def __init__(self, eventList = None):
        if eventList is None:
            eventList = []
        self.eventList = eventList

class HumdrumSpine(object):
    '''
    A HumdrumSpine is a collection of events arranged vertically that have a connection to each other
    Each HumdrumSpine MUST have an id (numeric or string) attached to it.

    spine1 = HumdrumSpine(5, [SpineEvent1, SpineEvent2])
    spine1.beginningPosition = 5
    spine1.endingPosition = 6
    spine1.upstream = [3]
    spine1.downstream = [7,8]
    spine1.spineCollection = weakref.ref(SpineCollection1)
           ## we keep weak references to the spineCollection so that we don't have circular references

    print(spine1.spineType)  ## searches the EventList or upstreamSpines to figure out the spineType

    '''
    def __init__(self, id, eventList = None):
        self.id = id
        if eventList is None:
            eventList = []
        for event in eventList:
            event.spineId = id
        
        self.eventList = eventList
        self.music21Objects = Stream()
        self.beginningPosition = 0
        self.endingPosition = 0
        self.upstream = []
        self.downstream = []

        self._spineCollection = None
        self._spineType = None

    def __repr__(self):
        return str(self.id) + repr(self.upstream) + repr(self.downstream)

    def append(self, event):
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
        self._spineCollection = sc
    
    spineCollection = property(_getSpineCollection, _setSpineCollection)

    def upstreamSpines(self):
        '''
        Returns the HumdrumSpine(s) that are upstream (if the spineCollection is set)
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
        Returns the HumdrumSpine(s) that are downstream (if the spineCollection is set)
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
        dummmy method that pushes all these objects to music21Objects
        even though they probably are not.
        '''
        for event in self.eventList:
            eventC = str(event.contents)
            if eventC == ".":
                pass
            else:
                self.music21Objects.append(event)

class KernSpine(HumdrumSpine):
    def parse(self):
        thisContainer = None
        inTuplet = False
        lastNote = None
        
        for event in self.eventList:
            eventC = str(event.contents)  # is str already; just for Eclipse
            thisObject = None
            if eventC.count(' '):
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
            
            elif eventC == ".":
                pass
            elif eventC.startswith('*'):
                ## control processing
                tempObject = kernTandamToControl(eventC)
                if tempObject is not None:
                    thisObject = tempObject
            elif eventC.startswith('='):
                ## barline/measure processing
                if thisContainer is not None:
                    self.music21Objects.append(thisContainer)
                thisContainer = hdStringToMeasure(eventC)                
            elif eventC.startswith('!'):
                ## TODO: process comments
                pass
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
                    self.music21Objects.append(thisObject)
                else:
                    thisContainer.append(thisObject)

class DynamSpine(HumdrumSpine):
    def parse(self):
        thisContainer = None
        for event in self.eventList:
            eventC = str(event.contents)  # is str already; just for Eclipse
            thisObject = None
            if eventC == ".":
                pass
            elif eventC.startswith('*'):
                ## control processing
                tempObject = miscTandamToControl(eventC)
                if tempObject is not None:
                    thisObject = tempObject
            elif eventC.startswith('='):
                if thisContainer is not None:
                    self.music21Objects.append(thisContainer)
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
                    self.music21Objects.append(thisObject)
                else:
                    thisContainer.append(thisObject)


        
class SpineEvent(object):
    '''
    A SpineEvent is the next event in a HumdrumSpine.
    It may be empty, in which case it means that a particular event appears after the last event in a different spine.

    Should be initalized with its contents.
    two attributes: 
        position -- event position in the file
        protoSpineNum -- proto spine number (0 to N)
        spineId -- spine actually attached to (after SpinePaths are parsed)
    both are optional but likely to be very helpful
    '''
    position = 0
    protoSpineNum= 0
    contents = ""
    spineId = None
    
    def __init__(self, contents = None, lastContents = None, position = 0):
        self.contents = contents
        self.lastContents = lastContents
        self.position = position

    def __str__(self):
        return self.contents

    def toNote(self):
        return hdStringToNote(self.contents)        

class SpineCollection(object):
    '''
    A SpineCollection is a set of Spines with relationships to each other and where their position attributes indicate
    simultaneous onsets.
    '''

    def __init__(self): 
        self.spines = []
        self.nextFreeId  = 0
        
    def addSpine(self):
        '''
        addSpine() -- creates a new spine in the collection and returns it
        '''
        
        self.newSpine = HumdrumSpine(self.nextFreeId)
        self.newSpine.spineCollection = weakref.ref(self)
        self.spines.append(self.newSpine)
        self.nextFreeId += 1
        return self.newSpine
    
    def appendSpine(self, spine):
        '''
        appendSpine(spine) -- appends an already existing HumdrumSpine to the SpineCollection
        returns void
        '''
        self.spines.append(spine)
        
    def getSpineById(self, id):
        '''
        getSpineById(id) -- returns the HumdrumSpine with the given id
        raises a HumdrumException if the spine with a given id is not found
        '''
        for thisSpine in self.spines:
            if thisSpine.id == id:
                return thisSpine
        raise HumdrumException("Could not find a Spine with that ID")

    def reclass(self):
        '''
        reclass() -- changes the classes of HumdrumSpines to more specific types (KernSpine, DynamicSpine)
                     according to their spineType (**kern, **dynam)
        '''                     
        for thisSpine in self.spines:
            if thisSpine.spineType == "kern":
                thisSpine.__class__ = KernSpine
            elif thisSpine.spineType == "dynam":
                thisSpine.__class__ = DynamSpine
            

    def parseMusic21(self):
        '''
        runs spine.sparse for each Spine.  
        thus populating a stream (music21Objects) for each Spine
        '''
        for thisSpine in self.spines:
            thisSpine.parse()

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
     
    # TODO: append global comments and have a way of recalling them

class EventCollection(object):
    '''
    An Event Collection is a time slice of all events that have an onset of a certain time
    If an event does not occur at a certain time, then you should check EventCollection[n].lastEvent to get the previous event
    (if it is a note, it is the note still sounding, etc.).  The happeningEvent method gets either currentEvent or lastEvent.
    '''
    def __init__(self, maxspines = 0):
        self.events = common.defList()
        self.lastEvents = common.defList()
        self.maxspines = maxspines
        self.spinePathData = False  ## true if the line contains data about changing spinePaths

    def addSpineEvent(self, spineNum, spineEvent):
        self.events[spineNum] = spineEvent
        
    def addLastSpineEvent(self, spineNum, spineEvent): ## should only add if current "event" is "." or a comment
        self.lastEvents[spineNum] = spineEvent
        
    def addGlobalEvent(self, globalEvent):
        for i in range(0, self.maxspines):
            self.events[i] = globalEvent

    def getSpineEvent(self, spineNum):
        return self.events[spineNum]
    
    def getSpineOccuring(self, spineNum):  ## returns the currentEvent or the lastEvent if currentEvent is "."
        if self.lastEvents[spineNum] is not None:
            return self.lastEvents[spineNum]
        else:
            return self.events[spineNum]

    def getAllOccurring(self):
        retEvents = []
        for i in range(0, self.maxspines):
            retEvents.append(self.getSpineOccuring(i))
        return retEvents
        
class HumdrumException(Exception):
    '''
    General Exception class for problems relating to Humdrum
    '''
    pass

def hdStringToNote(contents):
    '''
    returns a music21.note.Note (or Rest or Unpitched, etc.) matching the current SpineEvent.
    Does not check to see that it is sane or part of a **kern spine, etc.

    TODO: Write it!
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
        thisObject.tie = music21.note.Tie("start")
    elif contents.count(']'):
        thisObject.tie = music21.note.Tie("stop")
    elif contents.count('_'):
        thisObject.tie = music21.note.Tie("continue")
    
    ## 3.2.3 Ornaments    
    if contents.count('t'):
        thisObject.notations.append(music21.expressions.HalfStepTrill())
    elif contents.count('T'):
        thisObject.notations.append(music21.expressions.WholeStepTrill())
    
    if contents.count('w'):
        thisObject.notations.append(music21.expressions.HalfStepInvertedMordent())
    elif contents.count('W'):
        thisObject.notations.append(music21.expressions.WholeStepInvertedMordent())
    elif contents.count('m'):
        thisObject.notations.append(music21.expressions.HalfStepMordent())
    elif contents.count('M'):
        thisObject.notations.append(music21.expressions.WholeStepMordent())

    if contents.count('S'):
        thisObject.notations.append(music21.expressions.Turn())
    elif contents.count('$'):
        thisObject.notations.append(music21.expressions.InvertedTurn())
    elif contents.count('R'):
        t1 = music21.expressions.Turn()
        t1.connectedToPrevious = True  ## true by default, but explicitly
        thisObject.notations.append(t1)
    
    if contents.count(':'):
        ## TODO: deal with arpeggiation -- should have been in a chord structure
        pass
    
    if contents.count("O"):
        thisObject.notations.append(music21.expressions.Ornament())  # generic ornament
    
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
    
    # 3.2.7 Duration
    # 3.2.8 N-Tuplets
    foundNumber = re.search("(\d+)", contents)
    if foundNumber:
        durationType = int(foundNumber.group(1))
        if durationType in duration.typeFromNumDict:
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

            gcd = common.EuclidGCD(int(dT), basevalue)
            newTup.numberNotesActual = dT/gcd
            newTup.numberNotesNormal = float(basevalue)/gcd
            
            if contents.count('.'):
                newTup.durationNormal.dots = contents.count('.')
            
            thisObject.duration.appendTuplet(newTup)
                    
    # 3.2.9 Grace Notes and Groupettos
    # TODO: Rewrite after music21 gracenotes are implimented
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
    m1.setRightBarline()
    
    if rematchMN:
        m1.measureNumber = int(rematchMN.group(1))
        if rematchMN.group(2):
            m1.measureNumberSuffix = rematchMN.group(2)

    if contents.count('-'):
        m1.rightbarline.style = "none"
    elif contents.count('\''):
        m1.rightbarline.style = "short"
    elif contents.count('`'):
        m1.rightbarline.style = "tick"
    elif contents.count('||'):
        m1.rightbarline.style = "light-light"
        if contents.count(':') > 1:
            m1.rightbarline.repeat_dots = "both"
        elif contents.count(':|'):
            m1.rightbarline.repeat_dots = "left"
        elif contents.count('|:'):
            m1.rightbarline.repeat_dots = "right"
    elif contents.count('!!'):
        m1.rightbarline.style = "heavy-heavy"
        if contents.count(':') > 1:
            m1.rightbarline.repeat_dots = "both"
        elif contents.count(':!'):
            m1.rightbarline.repeat_dots = "left"
        elif contents.count('!:'):
            m1.rightbarline.repeat_dots = "right"
    elif contents.count('|!'):
        m1.rightbarline.style = "light-heavy"
        if contents.count(':') > 1:
            m1.rightbarline.repeat_dots = "both"
        elif contents.count(':|'):
            m1.rightbarline.repeat_dots = "left"
        elif contents.count('!:'):
            m1.rightbarline.repeat_dots = "right"
    elif contents.count('!|'):
        m1.rightbarline.style = "heavy-light"
        if contents.count(':') > 1:
            m1.rightbarline.repeat_dots = "both"
        elif contents.count(':!'):
            m1.rightbarline.repeat_dots = "left"
        elif contents.count('|:'):
            m1.rightbarline.repeat_dots = "right"
    elif contents.count('|'):
        m1.rightbarline.style = "regular"
        if contents.count(':') > 1:
            m1.rightbarline.repeat_dots = "both"
        elif contents.count(':|'):
            m1.rightbarline.repeat_dots = "left"
        elif contents.count('|:'):
            m1.rightbarline.repeat_dots = "right"
    elif contents.count('=='):
        m1.rightbarline.style = "light-light"
        if contents.count(':') > 1:
            m1.rightbarline.repeat_dots = "both"
            ## cannot specify single repeat does without styles
        if contents == "==|":
            raise HumdrumException \
                ("Cannot import a double bar visually rendered as a single bar")
    
    if contents.count(';'):
        m1.rightbarline.pause = music21.expressions.Fermata()

    return m1


def kernTandamToControl(tandam):
    '''
    kern uses *M5/4  *clefG2 etc, to control processing
    '''
    # TODO: Cover more tandam controls as they're found
    tandam = str(tandam)
    
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
            MM = music21.tempo.MetronomeMark(metronomeMark)    
            return MM
        except ValueError:
            metronomeMark = re.sub('^\[','',metronomeMark)
            metronomeMark = re.sub(']\s*$','',metronomeMark)
            MS = music21.tempo.TempoMark(metronomeMark)
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

def miscTandamToControl(tandam):
    tandam = str(tandam)
    
    if tandam in spinePathIndicators:
        return None
    else:
        return MiscTandam(tandam)

class MiscTandam(object):
    def __init__(self, tandam):
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
        self.assertEqual(m1.measureNumber, 29)
        self.assertEqual(m1.measureNumberSuffix, "a")
        self.assertEqual(m1.rightbarline.style, "regular")
        self.assertEqual(m1.rightbarline.repeat_dots, "both")
        assert m1.rightbarline.pause is not None
        assert isinstance(m1.rightbarline.pause, music21.expressions.Fermata)

    def testSpineMazurka(self):    
#        hf1 = HumdrumFile("d:/web/eclipse/music21misc/mazurka06-2.krn")    
        hf1 = HumdrumDataCollection(testFiles.mazurka6)
#        hf1 = HumdrumDataCollection(testFiles.ojibway)
#        hf1 = HumdrumDataCollection(testFiles.schubert)
#        hf1 = HumdrumDataCollection(testFiles.ivesSpring)
#        hf1 = HumdrumDataCollection(testFiles.sousaStars) # parse errors b/c of graces
        masterStream = hf1.stream
#        for spineX in hf1.spineCollection:
#            spineX.music21Objects.id = "spine %s" % str(spineX.id)
#            masterStream.append(spineX.music21Objects)
        expectedOutput = canonicalOutput.mazurka6repr
#        self.assertTrue(common.basicallyEqual
#                          (common.stripAddresses(expectedOutput),
#                           common.stripAddresses(masterStream._reprText())))
#        print common.stripAddresses(expectedOutput)
#       print common.stripAddresses(masterStream.recurseRepr())
        
        # humdrum type problem: how many G#s start on beat 2 of a measure?
        GsharpCount = 0
        for element in masterStream.flat:  ## recursion this time
            if common.almostEquals(element.offset, 1.0):
                if hasattr(element, "pitch") and element.pitch.name == "G#":
                    GsharpCount += 1
                elif hasattr(element, "pitches"):
                    for thisPitch in element.pitches:
                        if thisPitch.name == "G#":
                            GsharpCount += 1
        # in reality, we should run getElementsByClass("measure") and use Measure attributes
        #   to get the note attacked at beat X.  but we're not there yet.
        # TODO: when measures have beats, do this...
        
        self.assertEqual(GsharpCount, 34)
            
if __name__ == "__main__":
    music21.mainTest(Test)