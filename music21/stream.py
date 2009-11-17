#-------------------------------------------------------------------------------
# Name:         stream.py
# Purpose:      base clases for dealing with groups of positioned objects
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    (c) 2009 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import copy, types, random
import doctest, unittest

# try:
#     import cPickle as pickleMod
# except ImportError:
#     import pickle as pickleMod


import music21 ## needed to properly do isinstance checking
from music21 import Element

from music21 import common
from music21 import clef
from music21 import chord
from music21 import defaults
from music21 import duration
from music21 import dynamics
from music21 import instrument
from music21 import lily as lilyModule
from music21 import measure
from music21 import meter
from music21 import musicxml as musicxmlMod
from music21 import note

from music21 import environment
_MOD = "stream.py"
environLocal = environment.Environment(_MOD)

CLASS_SORT_ORDER = ["Clef", "TempoMark", "KeySignature", "TimeSignature", "Dynamic", "GeneralNote"]


#-------------------------------------------------------------------------------

class StreamException(Exception):
    pass

#-------------------------------------------------------------------------------
# Stream processing functions


def extendDuration(streamObj, objName):
    '''Given a stream and an object name, go through stream and find each 
    object. The time between adjacent objects is then assigned to the 
    duration of each object. The last duration of the last object is assigned
    to the end of the stream.

    >>> a = Stream()
    >>> n = note.Note()
    >>> n.duration.quarterLength
    1.0
    >>> a.repeatCopy(n, range(0,50,10))
    >>> import music21.dynamics
    >>> d = music21.dynamics.Dynamic('ff')
    >>> d.offset = 15.0
    >>> a.append(d)
    >>> a = a.sorted
    >>> a.duration.quarterLength
    41.0
    >>> len(a)
    6
    >>> a[-1].offset
    40.0

    >>> b = extendDuration(a.flat, note.Note)
    >>> len(b)
    6
    >>> b[0].duration.quarterLength
    10.0
    >>> b[-1].duration.quarterLength
    1.0
    >>> b.duration.quarterLength
    41.0
    >>> b[-1].offset
    40.0

    #>>> a[1].duration.quarterLength
    #1.0  ## TODO: FIX Error: gets 10.0

    '''
# temporarily removed for musicxml testing
#     >>> from music21.musicxml import testFiles
#     >>> from music21 import converter
#     >>> mxString = testFiles.ALL[2] # has dynamics
#     >>> a = converter.parse(mxString)
#     >>> b = extendDuration(a.flat, dynamics.Dynamic)
# 

    # assuming user provides the desired versioin
    #streamObj = streamSrc.flat.sorted

    qLenTotal = streamObj.duration.quarterLength
    elements = []

    for element in streamObj.getElementsByClass(objName):
        if not hasattr(element, 'duration'):
            raise StreamException('can only process objects with duration attributes')
        if element.duration == None:
            element.duration = duration.Duration()
        elements.append(element)

    #print elements[-1], qLenTotal, elements[-1].duration
    # print _MOD, elements
    for i in range(len(elements)-1):
        #print i, len(elements)
        span = elements[i+1].offset - elements[i].offset
        elements[i].duration.quarterLength = span

    # handle last element
    #print elements[-1], qLenTotal, elements[-1].duration
    elements[-1].duration.quarterLength = (qLenTotal -
                                             elements[-1].offset)
    #print elements[-1], elements[-1].duration

    # might want to return a new stream with the altered elements
    return streamObj



def splitByClass(streamObj, objName, fx):
    '''Given a stream, get all objects specified by objName and then form
    two new streams, where fx returns 1/True for the first stream and other values for the second stream.

    Probably better named SplitByClass or similar.

    >>> a = Stream()
    >>> for x in range(30,81):
    ...     n = note.Note()
    ...     n.midi = x
    ...     a.append(n)
    >>> fx = lambda n: n.midi > 60
    >>> b, c = splitByClass(a, note.Note, fx)
    >>> len(b)
    20
    >>> len(c)
    31
    '''
    a = Stream()
    b = Stream()
    for element in streamObj.getElementsByClass(objName):
        if fx(element):
            a.append(element)
        else:
            b.append(element)
    return a, b
        


#-------------------------------------------------------------------------------

def makeRests(streamObj, refStream=None):
    '''Given a streamObj with an Element with an offset not equal to zero, 
    fill with one Rest preeceding this offset. 

    If refStream is provided, use this to get min and max offsets.


    TODO: rename fillRests() or something else

    >>> a = Stream()
    >>> a.insertAtOffset(None, 20)
    >>> len(a)
    1
    >>> a.lowestOffset
    20.0
    >>> b = makeRests(a)
    >>> len(b)
    2
    >>> b.lowestOffset
    0.0
    '''
    #environLocal.printDebug(['calling makeRests'])

    oLow = streamObj.lowestOffset
    oHigh = streamObj.highestTime
    if refStream != None:
        oLowTarget = refStream.lowestOffset
        oHighTarget = refStream.highestTime
        environLocal.printDebug(['refStream usded in makeRests', oLowTarget, oHighTarget])
    else:
        oLowTarget = 0
        oHighTarget = streamObj.highestTime

    post = streamObj.copy()
    
    qLen = oLow - oLowTarget
    if qLen > 0:
        r = note.Rest()
        r.duration.quarterLength = qLen
        post.insertAtOffset(r, oLowTarget)

    qLen = oHighTarget - oHigh
    if qLen > 0:
        r = note.Rest()
        r.duration.quarterLength = qLen
        post.insertAtOffset(r, oHigh)

#     streamLead = Stream() # store rests leading this event
# 
#     o = 0 # starting offset
#     while True:
#         oRemain = oLow - o
#         if oRemain <= 0:
#             break
#         if oRemain >= maxRestQLen:
#             qLen = maxRestQLen
#         else: # oRemain is less tn maxRestQLen but greater than zero
#             qLen = oRemain
# 
#         r = note.Rest()
#         r.duration.quarterLength = qLen
#         streamLead.insertAtOffset(r, o)
# 
#         o = o + qLen

    # do not need to sort, can concatenate without sorting
    # post = streamLead + streamObj 
    return post.sorted



def makeMeasures(streamObj, meterStream=None, refStream=None):
    '''Take a stream of and partition all elements into measures based on 
    one or more TimeSignautre defined within the stream. If no TimeSignatures
    are defined, a default is used.

    If a meterStream is provided, this is used instead of the meterStream
    found in the Stream.

    If a refStream is provided, this is used to provide max offset values, necessary to fill empty rests and similar.

    TODO: this can simply be a method of Stream?

    >>> a = Stream()
    >>> a.fillNone(3)
    >>> b = makeMeasures(a)
    >>> c = meter.TimeSignature('3/4')
    >>> a.insertAtOffset(c, 0)
    >>> x = makeMeasures(a)

    >>> d = Stream()
    >>> n = note.Note()
    >>> d.repeatAdd(n, 10)
    >>> d.repeatCopy(n, [x+.5 for x in range(10)])
    >>> x = makeMeasures(d)
    '''
    #environLocal.printDebug(['calling makeMeasures'])

    # may need to look in parent if no time signatures are found
    if meterStream == None:
        meterStream = streamObj.getTimeSignatures()
    # get a clef and for the entire stream
    clefObj = streamObj.bestClef()

    # for each element in stream, need to find max and min offset
    # assume that flat/sorted options will be set before procesing
    offsetMap = [] # list of start, start+dur, element
    for e in streamObj:
        if hasattr(e, 'duration') and e.duration != None:
            dur = e.duration.quarterLength
        else:
            dur = 0 
        # may just need to copy element offset component
        offsetMap.append([e.offset, e.offset+dur, e.deepcopy()])

    #offsetMap.sort() not necessary; just get min and max
    oMin = min([start for start, end, e in offsetMap])
    oMax = max([end for start, end, e in offsetMap])

    # this should not happend, but just in case
    if oMax != streamObj.highestTime:
        raise StreamException('mismatch between oMax and highestTime (%s, %s)' % (oMax, streamObj.highestTime))
    #environLocal.printDebug(['oMin, oMax', oMin, oMax])

    # if a ref stream is provided, get highst time from there
    # only if it is greater thant the highest time yet encountered
    if refStream != None:
        if refStream.highestTime > oMax:
            oMax = refStream.highestTime

    # create a stream of measures to contain the offsets range defined
    # create as many measures as needed to fit in oMax
    post = Stream()
    o = 0 # initial position of first measure is assumed to be zero
    measureCount = 0
    while True:    
        m = Measure()
        # get active time signature at this offset
        m.timeSignature = meterStream.getElementAtOrBefore(o)
        m.clef = clefObj

        #environLocal.printDebug([measureCount, o, oMax, m.timeSignature,
        #                        m.timeSignature.barDuration.quarterLength])
        m.measureNumber = measureCount + 1
        # avoid an infinite loop
        if m.timeSignature.barDuration.quarterLength == 0:
            raise StreamException('time signature has no duration')    
        post.insertAtOffset(m, o) # insert measure
        o += m.timeSignature.barDuration.quarterLength # increment by meter length
        if o >= oMax: # may be zero
            break # if length of this measure exceedes last offset
        else:
            measureCount += 1

        if measureCount > 99999: # check for infinite loop
            raise StreamException('max measure count exceeded')    

    # populate measures with elements
    for start, end, e in offsetMap:
        # iterate through all measures 
        match = False
        for i in range(len(post)):
            m = post[i]
            # get start and end offsets for each measure
            # seems like should be able to use m.duration.quarterLengths
            mStart, mEnd = m.offset, m.offset + m.timeSignature.barDuration.quarterLength
            # if elements start fits within this measure, break and use 
            # offset cannot start on end
            if start >= mStart and start < mEnd:
                match = True
                #environLocal.printDebug(['found measure match', i, mStart, mEnd, start, end, e])
                break
        if not match:
            raise StreamException('cannot place element with start/end %s/%s within any measures' % (start, end))
        # find offset in the temporal context of this measure
        # i is the index of the measure that this element starts at
        # mStart, mEnd are correct
        oNew = start - mStart # remove measure offset from element offset
        # insert element at this offset in the measure
        # not copying elements here!
        # here, we have the correct measure from above
        #environLocal.printDebug(['measure placement', mStart, oNew, e])
        m.insertAtOffset(e, oNew)
    return post


def makeTies(streamObj, meterStream=None):
    '''Given a stream containing measures, examine each element in the stream
    if the elements duration extends beyond the measures bound, create a tied 
    entity.

    Edits the current stream in-place. 

    TODO: this can simply be a method of Stream

    TODO: take a list of clases to act as filter on what elements are tied.

    configure ".previous" and ".next" attributes

    >>> d = Stream()
    >>> n = note.Note()
    >>> n.quarterLength = 12
    >>> d.repeatAdd(n, 10)
    >>> d.repeatCopy(n, [x+.5 for x in range(10)])
    >>> x = makeMeasures(d)

    >>> x = makeTies(x)

    '''
    if len(streamObj) == 0:
        raise StreamException('cannot process an empty stream')        

    # get measures from this stream
    measureStream = streamObj.getElementsByClass(Measure)
    if len(measureStream) == 0:
        raise StreamException('cannot process a stream without measures')        

    # may need to look in parent if no time signatures are found
    if meterStream == None:
        meterStream = streamObj.getTimeSignatures()

    mCount = 0
    while True:
        # update measureStream on each iteration, 
        # as new measure may have been added
        # to the stream 
        measureStream = streamObj.getElementsByClass(Measure)
        if mCount >= len(measureStream):
            break
        m = measureStream[mCount]
        if mCount + 1 < len(measureStream):
            mNext = measureStream[mCount+1]
            mNextAdd = False
        else: # create a new measure
            mNext = Measure()
            # set offset to last offset plus total length
            mNext.offset = m.offset + m.timeSignature.barDuration.quarterLength
            if len(meterStream) == 0: # in case no meters are defined
                ts = meter.TimeSignature()
                ts.load('%s/%s' % (defaults.meterNumerator, 
                                   defaults.meterDenominatorBeatType))
#                 ts.numerator = defaults.meterNumerator
#                 ts.denominator = defaults.meterDenominatorBeatType
            else: # get the last encountered meter
                ts = meterStream.getElementAtOrBefore(mNext.offset)
            mNext.timeSignature = ts
            mNext.measureNumber = m.measureNumber + 1
            mNextAdd = True

        # seems like should be able to use m.duration.quarterLengths
        mStart, mEnd = 0, m.timeSignature.barDuration.quarterLength
        for e in m:
            if hasattr(e, 'duration') and e.duration != None:
                # check to see if duration is within Measure
                eEnd = e.offset + e.duration.quarterLength
                # assume end can be at boundary of end of measure
                if eEnd > mEnd:
                    if e.offset >= mEnd:
                        raise StreamException('element has offset %s within a measure that ends at offset %s' % (e.offset, mEnd))  

                    # note: cannot use GeneralNote.splitNoteAtPoint b/c
                    # we are not assuming that these are notes, only elements

                    qLenBegin = mEnd - e.offset
                    #print 'e.offset, mEnd, qLenBegin', e.offset, mEnd, qLenBegin
                    qLenRemain = e.duration.quarterLength - qLenBegin
                    # modify existing duration
                    e.duration.quarterLength = qLenBegin
                    # create and palce new element
                    eRemain = e.deepcopy()
                    eRemain.duration.quarterLength = qLenRemain

                    # set ties
                    if (isinstance(e, note.Note) or 
                        isinstance(e, note.Unpitched)):
                        #environLocal.printDebug(['tieing in makeTies', e])
                        e.tie = note.Tie('start')
                        # TODO: not sure if we can assume to stop remainder
                        #e.Remain.tie = note.Tie('stop')

                    # TODO: this does not seem the best way to do this!
                    # need to find a better way to insert this first in elements
                    eRemain.offset = 0
                    mNext.elements = [eRemain] + mNext.elements

                    # we are not sure that this element fits 
                    # completely in the next measure, thus, need to continue
                    # processing each measure
                    if mNextAdd:
                        streamObj.insertAtOffset(mNext, mNext.offset)
        mCount += 1

    #print streamObj.recurseRepr()

    return streamObj



def makeBeams(streamObj, meterStream=None):
    '''Given a stream containing measures, create beams based on 
    TimeSignature objects.

    Edits the current stream in-place. 

    >>> d = Stream()
    >>> n = note.Note()
    >>> n.quarterLength = .25
    >>> d.repeatAdd(n, 16)
    >>> x = makeMeasures(d)
    >>> y = makeBeams(x)

    '''
    if len(streamObj) == 0:
        raise StreamException('cannot process an empty stream')        

    # get measures from this stream
    measureStream = streamObj.getElementsByClass(Measure)
    if len(measureStream) == 0:
        raise StreamException('cannot process a stream without measures')        

    
    for m in streamObj.getElementsByClass(Measure): 
        ts = m.timeSignature
        noteStream = m.getNotes()
        durList = []

        for n in noteStream:
            durList.append(n.duration)
        if len(durList) <= 1: 
            continue

        beamsList = ts.getBeams(durList)
        for i in range(len(noteStream)):
            noteStream[i].beams = beamsList[i]

    return streamObj








def recurseRepr(thisStream, prefixSpaces = 0):
    returnString = ""
    for element in thisStream:    
        if isinstance(element, Stream):
            returnString += (" " * prefixSpaces) + element.__repr__() + "\n"
            returnString += recurseRepr(element, prefixSpaces + 2)
        else:
            if hasattr(element, "obj"):
                obj = element
            else:
                obj = element
            off = str(element.offset)
            returnString += (" " * prefixSpaces) + "{" + off + "} " + obj.__repr__() + "\n"
    return returnString

saveRR = recurseRepr



#-------------------------------------------------------------------------------
class Stream(Element):
    '''
    This is basic unit for timed Elements. In many cases these timed
    Elements will be of the same class of things; notes, clefs, etc. This is
    not required. 
    
    Like the base class, Element, Streams have offsets, priority, id, and groups
    they also have an elements attribute which returns a list of elements; the
    obj attribute returns the same list (Stream-aware applications should ask
    for ElementOrStream.elements first and then look for .obj if the
    ElementOrStream does not have an element attribute).

    The Stream has a duration that can either be explicitly set or it is the
    release time of the chronologically last element in the Stream (that is,
    the highest onset plus duration of any element in the Stream).

    Streams may be embedded within other Streams.
    
    TODO: Get Stream Duration working -- should be the total length of the Stream. -- see the ._getDuration() and ._setDuration() methods
    '''

    def __init__(self):
        '''
        
        '''
        Element.__init__(self)

        # self._elements stores Element objects. These are not ordered.
        # this should have a public attribute/property self.elements
        self._elements = []
        self.obj = None

        self.isSorted = True
        self.isFlat = True  ## does it have no embedded elements
        self.isFlattenedRepresentation = False  ## is this a stream returned by Stream().flat ?
        
        self._cache = common.defHash()
        self._index = 0

#    def clone(self):
#        '''Element.clone should work fine...
#        '''


    #---------------------------------------------------------------------------
    # sequence like operations

    # if we want to have all the features of a mutable sequence, 
    # we should impliment
    # append(), count(), index(), extend(), insert(), 
    # pop(), remove(), reverse() and sort(), like Python standard list objects.
    # But we're not there yet.


    def __len__(self):
        '''Get the total number of elements
        Does not recurse into objects

        >>> a = Stream()
        >>> for x in range(4):
        ...     e = Element(note.Note('G#'))
        ...     e.offset = x * 3
        ...     a.append(e)
        >>> len(a)
        4

        >>> b = Stream()
        >>> for x in range(4):
        ...     b.append(a) # append streams
        >>> len(b)
        4
        '''
        return len(self._elements)

    def __iter__(self):
        '''A Stream can return an iterator.  Same as running x in a.elements
        '''
        # need to reset index each time an iterator is obtained
        # if a previous iteration calls break, _index will not be reset to zero
        self._index = 0 
        return self

    def next(self):
        '''Method for treating this object as an iterator
        Returns each element in order.  For sort order run x.sorted

        >>> a = Stream()
        >>> a.repeatCopy(None, range(6))
        >>> b = []
        >>> for x in a:
        ...     b.append(x.offset) # get just offset
        >>> b
        [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
        '''
        # this will return the self._elementsSorted list
        # unless it needs to be sorted
        if abs(self._index) >= self.__len__():
            self._index = 0 # reset for next run
            raise StopIteration

        out = self.elements[self._index]
        self._index += 1
        return out



    def __getitem__(self, key):
        '''Get an Element from the stream in current order; sorted if isSorted is True,
        but not necessarily.
        
        if an int is given, returns that index
        if a class is given, it runs getElementsByClass and returns that list
        if a string is given it first runs getElementById on the stream then if that
             fails, getElementsByGroup on the stream returning that list.

        ## maybe it should, but does not yet:    if a float is given, returns the element at that offset

        >>> a = Stream()
        >>> a.fillNone(6)
        >>> b = a[2:5]
        >>> len(b)
        3
        >>> a[1].offset
        1.0
        >>> b = note.Note()
        >>> b.id = 'green'
        >>> b.groups.append('violin')
        >>> a.append(b)
        >>> a[0].obj == None
        True
        >>> a[note.Note][0] == b
        True
        >>> a['violin'][0] == b
        True
        >>> a['green'] == b
        True
        '''

        if common.isNum(key):
# let the list do its own IndexError trapping.  this was too buggy 
#            if abs(key) > self.__len__():
#                raise IndexError(str(key) + " is out of range " + str(self.__len__()))
#            else:
                return self.elements[key]

        elif isinstance(key, slice): # get a slice of index values
            found = self.deepcopy() # return a stream of elements
            found.elements = self.elements[key]
            return found

        elif common.isStr(key):
            # first search id, then search groups
            idMatch = self.getElementById(key)
            if idMatch != None:
                return idMatch
            else: # search groups, return first element match
                groupStream = self.getElementsByGroup(key)
                if len(groupStream) > 0:
                    return groupStream
                else:
                    raise KeyError('provided key (%s) does not match any id or group' % key)
        elif isinstance(key, type(type)):
            # assume it is a class name
            classStream = self.getElementsByClass(key)
            if len(classStream) > 0:
                return classStream
            else:
                raise KeyError('provided class (%s) does not match any contained Elements' % key)


    #---------------------------------------------------------------------------
    # adding and editing Elements and Streams -- all need to call _elementsChanged
    # most will set isSorted to False

    def _elementsChanged(self):
        '''
        Call anytime _elements is changed. Called by methods that add or change
        elemens.

        >>> a = Stream()
        >>> a.isFlat
        True
        >>> a._elements.append(Stream())
        >>> a._elementsChanged()
        >>> a.isFlat
        False
        '''
        self.isSorted = False
        self.isFlat = True

        for thisElement in self._elements:
            if isinstance(thisElement, Stream): 
                self.isFlat = False
                break
            # this may not be necessary
#             elif hasattr(thisElement, "elements"):
#                 self.isFlat = False
#                 break
        self._cache = common.defHash()

    def _getElements(self):
        return self._elements
   
    def _setElements(self, value):
        '''
        >>> a = Stream()
        >>> a.repeatCopy(None, range(10))
        >>> b = Stream()
        >>> b.repeatCopy(None, range(10))
        >>> b.offset = 6
        >>> c = Stream()
        >>> c.repeatCopy(None, range(10))
        >>> c.offset = 12
        >>> b.append(c)
        >>> b.isFlat
        False
        >>> a.isFlat
        True
        >>> a.elements = b.elements
        >>> a.isFlat
        False
        '''
        self._elements = value
        self._elementsChanged()
        return value
        
    elements = property(_getElements, _setElements)

    def __setitem__(self, key, value):
        '''Insert items at index positions. Index positions are based
        on position in self.elements. 

        >>> a = Stream()
        >>> a.repeatCopy(None, range(10))
        >>> b = Stream()
        >>> b.repeatCopy(None, range(10))
        >>> b.offset = 6
        >>> c = Stream()
        >>> c.repeatCopy(None, range(10))
        >>> c.offset = 12
        >>> b.append(c)
        >>> a.isFlat
        True
        >>> a[3] = b
        >>> a.isFlat
        False
        '''
        self._elements[key] = value
        storedIsFlat = self.isFlat
        self._elementsChanged()

        # alternative way:
        #if not isinstance(thisElement, Stream): 
        if not hasattr(value, "elements"):
            self.isFlat = storedIsFlat


    def __add__(self, other):
        '''
        Returns a new stream that is the second added to the first.
        this will not shift any offsets; it will simply
        combine the elements.

        >>> a = Stream()
        >>> for x in range(5):
        ...     e = Element(note.Rest())
        ...     e.offset = x * 3
        ...     a.append(e)
        >>> a.isSorted
        True
        >>> a.elements[4].offset
        12.0
        >>> b = Stream()
        >>> for x in range(3):
        ...     e = Element(note.Note('D#'))
        ...     e.offset = (x * 3) + 1
        ...     b.append(e)
        >>> b.isSorted
        True
        >>> c = a + b
        >>> c.__class__.__name__
        'Stream'
        >>> len(c)
        8
        >>> c.isSorted
        False
        >>> c.isFlat
        True
        '''        
        # if an element or a stream
        if not isinstance(other, music21.Music21Object): 
            other = Element(other)
        new = self.copy()
        if isinstance(other, Stream):
            new.elements = self.elements + other.elements
            if self.isSorted is True and other.isSorted is True and \
                self.highestTime <= other.offset:
                    new.isSorted = True
        else: # if other is not a Stream, object os appended 
            new.append(other)
        return new

    def append(self, item):
        '''Add a (sub)Stream, Element, or object (wrapped into a default element)
         to the element Stream.

        >>> a = Stream()
        >>> a.append(None)
        >>> a.append(music21.note.Note('G#'))
        >>> len(a)
        2
        
        QUESTION: should this also add an entry to the parent and context
        attributes (if any) in the object?
        '''
        # if not an element, embed
        if not isinstance(item, music21.Music21Object): 
            element = Element(item)
        else:
            element = item

        # set parent of this element to this object
        element.parent = self

        if self.isSorted is True and \
            self.highestTime <= element.offset:
                storeSorted = True
        else:
                storeSorted = False
        self._elements.append(element)  # could also do self.elements = self.elements + [element]
        self._elementsChanged()         # maybe much slower?
        self.isSorted = storeSorted



    def insert(self, pos, item):
        '''Insert in elements by index position.

        >>> a = Stream()
        >>> a.repeatAdd(note.Note('A-'), 30)
        >>> a[0].name == 'A-'
        True
        >>> a.insert(0, note.Note('B'))
        >>> a[0].name == 'B'
        True
        '''
        self._elements.insert(pos, item)
        self._elementsChanged()


    def insertAtOffset(self, item, offset):
        '''Append an object with a given offset. Wrap in an Element and 
        set offset time. 

        >>> a = Stream()
        >>> a.insertAtOffset(None, 32)
        >>> a._getHighestOffset()
        32.0
        '''
        if not isinstance(item, music21.Music21Object): # if not an element, embed
            element = Element(item)
        else:
            element = item
        element.offset = offset
        self.append(element)


# not needed
#     def merge(self, other):
#         '''Given another stream, merge that stream's elements into this stream.
# 
#         Not sure if other.offset should be taken into account in assigning
#         element offsets.
# 
#         >>> a = Stream()
#         >>> a.fillNone(10)
#         >>> b = Stream()
#         >>> b.fillNone(10)
#         >>> a.merge(b)
#         >>> len(a)
#         20
#         '''
#         for e in other:
#             self.insertAtOffset(e, e.offset)
#         self._elementsChanged() 


    def addNext(self, others):
        '''Add an objects or Elements (including other Streams) to the Stream 
        (or multiple if passed a list)
        with offset equal to the highestTime (that is the latest "release" of an object) plus
        any offset in the Element or Stream to be added.  If that offset is zero (or a bare
        object is added) then this object will directly after the last Element ends. 

        runs fast for multiple addition and will preserve isSorted if True

        >>> a = Stream()
        >>> notes = []
        >>> for x in range(0,3):
        ...     n = note.Note('G#')
        ...     n.duration.quarterLength = 3
        ...     notes.append(n)
        >>> a.addNext(notes[0])
        >>> a.highestOffset, a.highestTime
        (0.0, 3.0)
        >>> a.addNext(notes[1])
        >>> a.highestOffset, a.highestTime
        (3.0, 6.0)
        >>> a.addNext(notes[2])
        >>> a.highestOffset, a.highestTime
        (6.0, 9.0)
        >>> notes2 = []
        >>> # since notes are not embedded in Elements here, their offset
        >>> # changes when added to a stream!
        >>> for x in range(0,3):
        ...     n = notes[x].deepcopy()
        ...     n.offset = 0  
        ...     notes2.append(n)                
        >>> a.addNext(notes2) # add em all again
        >>> a.highestOffset, a.highestTime
        (15.0, 18.0)
        >>> a.isSequence()
        True
        '''
# TODO: this does not return the right result
#         >>> b.highestOffset, b.highestTime
#         (0, 0) 


        highestTimeTemp = self.highestTime
#         if isinstance(others, list):
        # treat all like lists

        # want to include lists and tuples
        if not common.isListLike(others):
            # back into a list for list processing if single
            others = [others]

        for other in others:
            if isinstance(other, music21.Music21Object): # if an element or a stream
                element = other
            else: # create an element for this stream
                element = Element(other)
            element.offset = highestTimeTemp + element.offset
            
            # this should look to the contained object duration
            if (hasattr(element, "duration") and 
                hasattr(element.duration, "quarterLength")):
                highestTimeTemp = element.offset + element.duration.quarterLength
            else:
                highestTimeTemp = element.offset

            # TODO: this should use append() not direclty affect the 
            # _elements list
            self._elements.append(element)  

#         else:
#             if isinstance(others, Element): # if an element or a stream
#                 element = others
#             else: # create an element for this stream
#                 element = Element(others)
#             element.offset = highestTimeTemp + element.offset
#             if hasattr(element, "duration") and hasattr(element.duration, "quarterLength"):
#                 highestTimeTemp = element.offset + element.duration.quarterLength
#             else:
#                 highestTimeTemp = element.offset
#             self._elements.append(element)  


        
        storeSorted = self.isSorted    
        self._elementsChanged()         
        self.isSorted = storeSorted


    def isClass(self, className):
        '''
        Returns true if the Stream or Stream Subclass is a particular class or subclasses that class.

        Used by getElementsByClass in Stream

        >>> a = Stream()
        >>> a.isClass(note.Note)
        False
        >>> a.isClass(Stream)
        True
        >>> b = Measure()
        >>> b.isClass(Measure)
        True
        >>> b.isClass(Stream)
        True
        '''
        ## same as Music21Object.isClass, not Element.isClass
        if isinstance(self, className):
            return True
        else:
            return False


    #---------------------------------------------------------------------------
    # display method
    def recurseRepr(self):
        return saveRR(self)


    #---------------------------------------------------------------------------
    # temporary storage: does not work yet!

#     def writePickle(self, fp):
#         f = open(fp, 'wb') # binary
#         # a negative protocal value will get the highest protocal; 
#         # this is generally desirable 
#         pickleMod.dump(self, f, protocol=-1)
#         f.close()
# 
# 
#     def openPickle(self, fp):
#         # not sure this will work
#         f = open(fp, 'rb')
#         self = pickleMod.load(f)
#         f.close()


    #---------------------------------------------------------------------------
    # methods that act on individual elements without requiring 
    # @ _elementsChanged to fire

    def addGroupForElements(self, group, classFilter=None):
        '''
        Add the group to the groups attribute of all elements.
        if classFilter is set then only those elements whose objects
        belong to a certain class (or for Streams which are themselves of
        a certain class) are set.
         
        >>> a = Stream()
        >>> a.repeatAdd(note.Note('A-'), 30)
        >>> a.repeatAdd(note.Rest(), 30)
        >>> a.addGroupForElements('flute')
        >>> a[0].groups 
        ['flute']
        >>> a.addGroupForElements('quietTime', note.Rest)
        >>> a[0].groups 
        ['flute']
        >>> a[50].groups
        ['flute', 'quietTime']
        >>> a[1].groups.append('quietTime') # set one note to it
        >>> a[1].step = "B"
        >>> b = a.getElementsByGroup('quietTime')
        >>> len(b)
        31
        >>> c = b.getElementsByClass(note.Note)
        >>> len(c)
        1
        >>> c[0].name
        'B-'

        '''
        for myElement in self.elements:
            if classFilter is None:
                myElement.groups.append(group)
            else:
                if hasattr(myElement, "elements"): # stream type
                    if isinstance(myElement, classFilter):
                        myElement.groups.append(group)
                elif hasattr(myElement, "obj"): # element type
                    if isinstance(myElement.obj, classFilter):
                        myElement.groups.append(group)
                else: # music21 type
                    if isinstance(myElement, classFilter):
                        myElement.groups.append(group)

    def setIdForElements(self, id, classFilter=None):
        '''Set all componenent Elements to the given id. Do not change the id
        of the Stream
        
        >>> a = Stream()
        >>> a.repeatAdd(note.Note('A-'), 30)
        >>> a.repeatAdd(note.Note('E-'), 30)
        >>> a.setIdForElements('flute')
        >>> a[0].id 
        'flute'
        >>> ref = a.countId()
        >>> len(ref)
        1
        >>> ref['flute']
        60

        >>> b = Stream()
        >>> b.repeatCopy(None, range(30))
        >>> b.repeatCopy(note.Note('E-'), range(30, 60))
        >>> b.setIdForElements('flute', note.Note)
        >>> a[0].id 
        'flute'
        >>> ref = b.countId()
        >>> ref['flute']
        30

        '''
        # elements do not have to be sorted
        for element in self.elements:
            if classFilter != None:
                if element.isClass(classFilter):
                    element.id = id
            else:
                element.id = id
        # seperate handling for streams?



    #---------------------------------------------------------------------------
    # getElementsByX(self): anything that returns a collection of Elements should return a Stream

    def getElementsByClass(self, classFilterList, unpackElement=False):
        '''
        return a list of all Elements that match the className
        
        >>> a = Stream()
        >>> a.fillNone(10) # adds Elements with obj == None
        >>> for x in range(4):
        ...     n = note.Note('G#')
        ...     n.offset = x * 3
        ...     a.append(n)
        >>> found = a.getElementsByClass(note.Note)
        >>> len(found)
        4
        >>> found[0].pitch.accidental.name
        'sharp'
        >>> b = Stream()
        >>> b.repeatCopy(None, range(10))
        >>> a.append(b)
        >>> # here, it gets elements from within a stream
        >>> # this probably should not do this, as it is one layer lower
        >>> found = a.getElementsByClass(types.NoneType)
        >>> len(found)
        10
        >>> c = Stream()
        >>> c.append(note.Note('A-'))
        >>> d = Stream()
        >>> d.repeatCopy(None, range(10))
        >>> c.append(d)
        >>> a.append(c)
        >>> found = a.getElementsByClass(types.NoneType)
        >>> len(found) # if recursive, should get 20
        10
        >>> found = a.flat.getElementsByClass(types.NoneType)
        >>> len(found)  # this is not the right answer
        30
        '''
        if unpackElement: # a list of objects
            found = []
        else: # return a Stream     
            found = Stream()

        if not common.isListLike(classFilterList):
            classFilterList = [classFilterList]

        ### BUG: if Element fits two classes (GeneralNote & Rest, for instance) it will be appended twice.
        for myEl in self:
            for myCl in classFilterList:
                if myEl.isClass(myCl):
                    if unpackElement and hasattr(myEl, "obj"): # N.B. Streams have .obj too -- bug?
                        found.append(myEl.obj)
                    else:
                        found.append(myEl)
                
        return found






    def getElementsByGroup(self, groupFilterList):
        '''
        # TODO: group comparisons are not YET case insensitive.  
        '''
        
        if not hasattr(groupFilterList, "__iter__"):
            groupFilterList = [groupFilterList]

        returnStream = Stream()
        for myEl in self:
            for myGrp in groupFilterList:
                if myGrp in myEl.groups:
                    returnStream.append(myEl)

        return returnStream


    def getGroups(self):
        '''Get a dictionary for each groupId and the count of instances.

        >>> a = Stream()
        >>> n = note.Note()
        >>> a.repeatAdd(n, 30)
        >>> a.addGroupForElements('P1')
        >>> a.getGroups()
        {'P1': 30}
        >>> a[12].groups.append('green')
        >>> a.getGroups()
        {'P1': 30, 'green': 1}
        '''

        # TODO: and related:

        #getStreamGroups which does the same but makes the value of the hash key be a stream with all the elements that match the group?
        # this is similar to what getElementsByGroup does

        post = {}
        for element in self:
            for groupName in element.groups:
                if groupName not in post.keys():
                    post[groupName] = 0
                post[groupName] += 1
        return post


    def getElementById(self, id, classFilter=None):
        '''Returns the first encountered Element for a given id. Return None
        if no match

        >>> e = 'test'
        >>> a = Stream()
        >>> a.append(e)
        >>> a[0].id = 'green'
        >>> None == a.getElementById(3)
        True
        >>> a.getElementById('green').id
        'green'
        '''
        for element in self.elements:
            if element.id == id:
                if classFilter != None:
                    if element.isClass(classFilter):
                        return element
                    else:
                        continue # id may match but not proper class
                else:
                    return element
        return None


    def countId(self, classFilter=None):
        ## TODO: see if necessary
        # presently, this just creates a dictionary of id and counts
        
        '''Get all componenent Elements id as dictionary of id:count entries.

        Alternative name: getElementIdByClass()
        '''
        post = {}
        for element in self.elements:
            count = False
            if classFilter != None:
                if element.isClass(classFilter):
                    count = True
            else:
                count = True
            if count:
                if element.id not in post.keys():
                    post[element.id] = 0
                post[element.id] += 1
        return post


    def getElementsByOffset(self, offsetStart, offsetEnd,
                    includeCoincidentBoundaries=True, onsetOnly=True,
                    unpackElement=False):
        '''Return a Stream/list of all Elements that are found within a certain offset time range, specified as start and stop values, and including boundaries

        If onsetOnly is true, only the onset of an event is taken into consideration; the offset is not.

        The time range is taken as the context for the flat representation.

        The includeCoincidentBoundaries option determines if an end boundary
        match is included.
        
        >>> a = Stream()
        >>> a.repeatCopy(None, range(10)) # adds Elements with obj == None
        >>> b = a.getElementsByOffset(4,6)
        >>> len(b)
        3
        >>> b = a.getElementsByOffset(4,5.5)
        >>> len(b)
        2

        >>> a = Stream()
        >>> n = note.Note('G')
        >>> n.quarterLength = .5
        >>> a.repeatCopy(n, range(8))
        >>> b = Stream()
        >>> b.repeatCopy(a, [0, 3, 6])
        >>> c = b.getElementsByOffset(2,6.9)
        >>> len(c)
        2
        >>> c = b.flat.getElementsByOffset(2,6.9)
        >>> len(c)
        10
        '''
        if unpackElement: # a list of objects
            found = []
        else: # return a Stream     
            found = Stream()

        #(offset, priority, dur, element). 
        for element in self:
            match = False
            offset = element.offset
            dur = element.duration

            if dur == None or onsetOnly:          
                elementEnd = offset
            else:
                elementEnd = offset + dur

            if includeCoincidentBoundaries:
                if offset >= offsetStart and elementEnd <= offsetEnd:
                    match = True
            else: # 
                if offset >= offsetStart and elementEnd < offsetEnd:
                    match = True

            if match:
                if unpackElement and hasattr(element, "obj"):   
                    found.append(element.obj)
                else:
                    found.append(element)
        return found


    def getElementAtOrBefore(self, offset, unpackElement=False):
        '''Given an offset, find the element at this offset, or with the offset
        less than and nearest to.

        Return one element or None if no elements are at or preceded by this 
        offset. 

        TODO: inlcude sort order for concurrent matches?

        >>> a = Stream()

        >>> x = Element()
        >>> x.id = 'x'
        >>> y = Element()
        >>> y.id = 'y'
        >>> z = Element()
        >>> z.id = 'z'

        >>> a.insertAtOffset(x, 20)
        >>> a.insertAtOffset(y, 10)
        >>> a.insertAtOffset(z, 0)

        >>> b = a.getElementAtOrBefore(21)
        >>> b.offset, b.id
        (20.0, 'x')

        >>> b = a.getElementAtOrBefore(19)
        >>> b.offset, b.id
        (10.0, 'y')

        >>> b = a.getElementAtOrBefore(0)
        >>> b.offset, b.id
        (0.0, 'z')
        >>> b = a.getElementAtOrBefore(0.1)
        >>> b.offset, b.id
        (0.0, 'z')

        '''
        candidates = []
        nearestTrailSpan = offset # start with max time
        for element in self:
            span = offset - element.offset
            if span < 0: # the element is after this offset
                continue
            elif span == 0: 
                candidates.append((span, element))
                nearestTrailSpan = span
            else:
                if span <= nearestTrailSpan: # this may be better than the best
                    candidates.append((span, element))
                    nearestTrailSpan = span
                else:
                    continue
        if len(candidates) > 0:
            candidates.sort()
            return candidates[0][1]
        else:
            return None


    def getElementAtOrAfter(self, offset, unpackElement=False):
        '''Given an offset, find the element at this offset, or with the offset
        greater than and nearest to.
        TODO: write this
        '''
        raise Exception("not yet implemented")




    def getElementBeforeOffset(self, offset, unpackElement=False):
        '''Get element before a provided offset
        TODO: write this
        '''
        raise Exception("not yet implemented")

    def getElementAfterOffset(self, offset, unpackElement=False):
        '''Get element after a provided offset
        TODO: write this
        '''
        raise Exception("not yet implemented")




    def getElementBeforeElement(self, element, unpackElement=False):
        '''given an element, get the element before
        TODO: write this
        '''
        raise Exception("not yet implemented")

    def getElementAfterElement(self, element, unpackElement=False):
        '''given an element, get the element next
        TODO: write this
        '''
        raise Exception("not yet implemented")







    def groupElementsByOffset(self, returnDict = False, unpackElement = False):
        '''
        returns a List of lists in which each entry in the
        main list is a list of elements occuring at the same time.
        list is ordered by offset (since we need to sort the list
        anyhow in order to group the elements), so there is
        no need to call stream.sorted before running this,
        but it can't hurt.
        
        it is DEFINITELY a feature that this method does not
        find elements within substreams that have the same
        absolute offset.  See Score.lily for how this is
        useful.  For the other behavior, call Stream.flat first.
        '''
        offsetsRepresented = common.defHash()
        for el in self.elements:
            if not offsetsRepresented[el.offset]:
                offsetsRepresented[el.offset] = []
            if unpackElement is False:
                offsetsRepresented[el.offset].append(el)
            else:
                offsetsRepresented[el.offset].append(el.obj)
        if returnDict is True:
            return offsetsRepresented
        else:
            offsetList = []
            for thisOffset in sorted(offsetsRepresented.keys()):
                offsetList.append(offsetsRepresented[thisOffset])
            return offsetList



    #--------------------------------------------------------------------------
    # convenieunce routines for obtaining elements form a Stream

    def getNotes(self):
        '''Return all Note objects in a Stream()
        '''
        return self.getElementsByClass(note.GeneralNote)

    notes = property(getNotes)

    def getMeasures(self):
        '''Return all Measure objects in a Stream()
        '''
        return self.getElementsByClass(Measure)

    measures = property(getMeasures)


    def getTimeSignatures(self):
        '''Create a stream of measures, given a stream with one or more        
        TimeSignature ojbects. 
        If not TimeSignature objects are defined, get a default
    
        Note: this could be a method of Stream.
    
        >>> a = Stream()
        >>> b = meter.TimeSignature('3/4')
        >>> a.append(b)
        >>> a.fillNone(10)
        >>> c = a.getTimeSignatures()
        >>> len(c) == 1
        True
        '''
        post = self.getElementsByClass(meter.TimeSignature)
    
        # get a default and/or place default at zero if nothing at zero
        if len(post) == 0 or post[0].offset > 0: 
            ts = meter.TimeSignature()
            ts.load('%s/%s' % (defaults.meterNumerator, 
                               defaults.meterDenominatorBeatType))
            #ts.numerator = defaults.meterNumerator
            #ts.denominator = defaults.meterDenominatorBeatType
            post.insertAtOffset(ts,0)
    
        return post
    


    def getInstrument(self, searchDepth=0):
        '''Search this stream or parent streams for instruments, otherwise 
        return a default

        Rename: getInstruments, and return a Stream of instruments

        >>> a = Stream()
        >>> b = a.getInstrument()
        '''
        environLocal.printDebug(['searching for instrument', searchDepth])
        searchDepth += 1

        instObj = None
        post = self.getElementsByClass(instrument.Instrument)
        if len(post) > 0:
            instObj = post[0] # get first
        else:
            #environLocal.printDebug(['parent', self.parent])

            pass # temporarily removed; causing an infinite loop

#             if isinstance(self.parent, Stream):
#                 environLocal.printDebug(['searching parent Stream'])
#                 instObj = self.parent.getInstrument(searchDepth)         

        # if still not defined, get default
        if instObj == None:
            instObj = instrument.Instrument()
            instObj.partId = defaults.partId # give a default id
            instObj.partName = defaults.partName # give a default id
        return instObj



    def bestClef(self, allowTreble8vb = False):
        '''
        Cheat method: returns the clef that is the best fit for the sequence

        Perhaps rename 'getClef'; providing best clef if not clef is defined in this stream; otherwise, return a stream of clefs with offsets


        >>> a = Stream()
        >>> for x in range(30):
        ...    n = note.Note()
        ...    n.midi = random.choice(range(60,72))
        ...    a.append(n)
        >>> b = a.bestClef()
        >>> b.line
        2
        >>> b.sign
        'G'

        >>> c = Stream()
        >>> for x in range(30):
        ...    n = note.Note()
        ...    n.midi = random.choice(range(35,55))
        ...    c.append(n)
        >>> d = c.bestClef()
        >>> d.line
        4
        >>> d.sign
        'F'
        '''

        totalNotes = 0
        totalHeight = 0

        notes = self.getElementsByClass(note.GeneralNote, unpackElement=True)

        def findHeight(thisPitch):
            height = thisPitch.diatonicNoteNum
            if thisPitch.diatonicNoteNum > 33: # a4
                height += 3 # bonus
            elif thisPitch.diatonicNoteNum < 24: # Bass F or lower
                height += -3 # bonus
            return height
        
        for thisNote in notes:
            if thisNote.isRest:
                pass
            elif thisNote.isNote:
                totalNotes  += 1
                totalHeight += findHeight(thisNote.pitch)
            elif thisNote.isChord:
                for thisPitch in thisNote.pitches:
                    totalNotes += 1
                    totalHeight += findHeight(thisPitch)
        if totalNotes == 0:
            averageHeight = 29
        else:
            averageHeight = (totalHeight + 0.0) / totalNotes

        if (allowTreble8vb == False):
            if averageHeight > 28:    # c4
                return clef.TrebleClef()
            else:
                return clef.BassClef()
        else:
            if averageHeight > 32:    # g4
                return clef.TrebleClef()
            elif averageHeight > 26:  # a3
                return clef.Treble8vbClef()
            else:
                return clef.BassClef()


    #--------------------------------------------------------------------------
    # offset manipulation

    def shiftElements(self, offset):
        '''Add offset value to every offset of contained Elements.

        TODO: add a class filter to set what is shifted

        >>> a = Stream()
        >>> a.repeatCopy(None, range(0,10))
        >>> a.shiftElements(30)
        >>> a.lowestOffset
        30.0
        >>> a.shiftElements(-10)
        >>> a.lowestOffset
        20.0
        '''
        for e in self:
            e.offset = e.offset + offset
        self._elementsChanged() 
        
    def applyOffset(self):
        '''Apply the offset of this stream to all internal elements; then set
        the offset of this stream to zero.

        TODO: rename transferOffset, if retained

        >>> a = Stream()
        >>> a.repeatCopy(None, range(0,10))
        >>> a.offset = 30
        >>> a.applyOffset()
        >>> a.lowestOffset
        30.0
        >>> a.offset
        0.0
        >>> a.offset = 20
        >>> a.applyOffset()        
        >>> a.lowestOffset
        50.0
        '''
        self.shiftElements(self.offset)
        self.offset = 0.0
        self._elementsChanged()


    #--------------------------------------------------------------------------
    # utilities for creating large numbers of elements

    def repeatAdd(self, item, numberOfTimes):
        '''
        Given an object and a number, run addNext that many times on the object.
        numberOfTimes should of course be a positive integer.
        
        >>> a = Stream()
        >>> n = note.Note()
        >>> n.duration.type = "whole"
        >>> a.repeatAdd(n, 10)
        >>> a.duration.quarterLength
        40.0
        >>> a[9].offset
        36.0
        '''
        if not isinstance(item, music21.Music21Object): # if not an element, embed
            element = Element(item)
        else:
            element = item # TODO: remove for new-old-style
            
        for i in range(0, numberOfTimes):
            self.addNext(element.deepcopy())
    
    def repeatCopy(self, item, offsets):
        '''Given an object, create many copies at the possitioins specified by 
        the offset list

        >>> a = Stream()
        >>> n = note.Note('G-')
        >>> n.quarterLength = 1
        >>> a.repeatCopy(n, range(30))
        >>> len(a)
        30
        >>> a[10].offset
        10.0
        '''
        if not isinstance(item, music21.Music21Object): # if not an element, embed
            element = Element(item)
        else:
            element = item

        for offset in offsets:
            #elementCopy = element.clone()

            # this needs to be deep clone in cases, for example, of copying 
            # many notes. w/o using deep clone, all durations objects   
            # are linked
            elementCopy = element.deepcopy()
            elementCopy.offset = offset
            self.append(elementCopy)


    def fillNone(self, number):
        '''For use in testing. fills a None object at every int offset between 0 and number
        '''
        self.repeatCopy(None, range(number))

    def extractContext(self, element, before = 4.0, after = 4.0, 
                       maxBefore = None, maxAfter = None):
        r'''
        extracts elements around the given element within (before) quarter notes and (after) quarter notes
        (default 4)
        
        TODO: maxBefore -- maximum number of elements to return before; etc.
        
        >>> from music21 import note
        >>> qn = note.QuarterNote()
        >>> qtrStream = Stream()
        >>> qtrStream.repeatCopy(qn, [0, 1, 2, 3, 4, 5])
        >>> hn = note.HalfNote()
        >>> hn.name = "B-"
        >>> qtrStream.addNext(hn)
        >>> qtrStream.repeatCopy(qn, [8, 9, 10, 11])
        >>> hnStream = qtrStream.extractContext(hn, 1.0, 1.0)
        >>> recurseRepr(hnStream)
        '{5.0} <music21.note.Note C>\n{6.0} <music21.note.Note B->\n{8.0} <music21.note.Note C>\n'
        '''
        
        display = Stream()
        found = None
        foundOffset = 0
        foundEnd = 0 
        for i in range(0, len(self.elements)):
            b = self.elements[i]
            if b.id is not None or element.id is not None:
                print b.id
                if b.id == element.id:
                    found = i
                    foundOffset = self.elements[i].offset
                    foundEnd    = foundOffset + self.elements[i].duration.quarterLength                        
            else:
                if b is element:
                    found = i
                    foundOffset = self.elements[i].offset
                    foundEnd    = foundOffset + self.elements[i].duration.quarterLength
        if found is None:
            raise StreamException("Could not find the element in the stream")

        for thisElement in self.elements:
            if (thisElement.offset >= foundOffset - before and
                   thisElement.offset < foundEnd + after):
                display.append(thisElement)

        return display


    #---------------------------------------------------------------------------
    def _getSorted(self):
        '''
        returns a new Stream where all the elements are sorted according to offset time
        
        if this stream is not flat, then only the highest elements are sorted.  To sort all,
        run myStream.flat.sorted
        
        ## TODO: CLEF ORDER RULES, etc.
        
        >>> s = Stream()
        >>> s.repeatCopy(note.Note("C#"), [0, 2, 4])
        >>> s.repeatCopy(note.Note("D-"), [1, 3, 5])
        >>> s.isSorted
        False
        >>> g = ""
        >>> for myElement in s:
        ...    g += "%s: %s; " % (myElement.offset, myElement.name)
        >>> g
        '0.0: C#; 2.0: C#; 4.0: C#; 1.0: D-; 3.0: D-; 5.0: D-; '
        >>> y = s.sorted
        >>> y.isSorted
        True
        >>> g = ""
        >>> for myElement in y:
        ...    g += "%s: %s; " % (myElement.offset, myElement.name)
        >>> g
        '0.0: C#; 1.0: D-; 2.0: C#; 3.0: D-; 4.0: C#; 5.0: D-; '
        >>> farRight = note.Note("E")
        >>> farRight.priority = 5
        >>> farRight.offset = 2.0
        >>> y.append(farRight)
        >>> g = ""
        >>> for myElement in y:
        ...    g += "%s: %s; " % (myElement.offset, myElement.name)
        >>> g
        '0.0: C#; 1.0: D-; 2.0: C#; 3.0: D-; 4.0: C#; 5.0: D-; 2.0: E; '
        >>> z = y.sorted
        >>> g = ""
        >>> for myElement in z:
        ...    g += "%s: %s; " % (myElement.offset, myElement.name)
        >>> g
        '0.0: C#; 1.0: D-; 2.0: C#; 2.0: E; 3.0: D-; 4.0: C#; 5.0: D-; '
        >>> z[2].name, z[3].name
        ('C#', 'E')
        '''
        post = self.elements ## already a copy
        post.sort(cmp=lambda x,y: cmp(x.offset, y.offset) or cmp(x.priority, y.priority))
        newStream = self.copy()
        newStream.elements = post
        newStream.isSorted = True
        return newStream
    
    sorted = property(_getSorted)

    def _getFlat(self):
        '''
        returns a new Stream where all no elements nest within other elements
        
        >>> s = Stream()
        >>> s.repeatCopy(note.Note("C#"), [0, 2, 4])
        >>> s.repeatCopy(note.Note("D-"), [1, 3, 5])
        >>> s.isSorted
        False
        >>> g = ""
        >>> for myElement in s:
        ...    g += "%s: %s; " % (myElement.offset, myElement.name)
        >>> g
        '0.0: C#; 2.0: C#; 4.0: C#; 1.0: D-; 3.0: D-; 5.0: D-; '
        >>> y = s.sorted
        >>> y.isSorted
        True
        >>> g = ""
        >>> for myElement in y:
        ...    g += "%s: %s; " % (myElement.offset, myElement.name)
        >>> g
        '0.0: C#; 1.0: D-; 2.0: C#; 3.0: D-; 4.0: C#; 5.0: D-; '

        >>> p = Stream()
        >>> p.repeatCopy(None, range(5))
        >>> q = Stream()
        >>> q.repeatCopy(p, range(0,50,10))
        >>> len(q)
        5
        >>> len(q.flat)        
        25
        >>> q.flat[24].offset
        44.0
        >>> r = Stream()
        >>> r.repeatCopy(q, range(0, 500, 100))
        >>> len(r)
        5
        >>> len(r.flat)
        125
        >>> r.flat[124].offset
        444.0
        '''
        return self._getFlatOrSemiFlat(retainContainers = False)

    flat = property(_getFlat)

    def _getSemiFlat(self):
## does not yet work (nor same for flat above in part because .copy() does not eliminate the cache...
#        if not self._cache['semiflat']:
#            self._cache['semiflat'] = self._getFlatOrSemiFlat(retainContainers = True)
#        return self._cache['semiflat']

        return self._getFlatOrSemiFlat(retainContainers = True)

    semiFlat = property(_getSemiFlat)
        
    def _getFlatOrSemiFlat(self, retainContainers):
        newStream = self.copy()
        newStream._elements = []
        newStream._elementsChanged()

        for myEl in self.elements:
            # check for stream instance instead
            if hasattr(myEl, "elements"): # recurse time:
                if retainContainers == True:
                    myElClone = myEl.copy()
                    newStream.append(myElClone)
                    recurseStream = myEl.semiFlat
                else:
                    recurseStream = myEl.flat
                    
                for subEl in recurseStream:
                    subElClone = subEl.copy()
                    subElClone.offset = recurseStream.offset + subEl.offset
                    newStream.append(subElClone)
            
            else:
                myElClone = myEl.copy()
                newStream.append(myElClone)

        newStream.isFlat = True
        newStream.isFlattenedRepresentation = True
        return newStream
    

    #---------------------------------------------------------------------------
    # duration and offset methods and properties
    
    def _getHighestOffset(self):
        '''
        >>> p = Stream()
        >>> p.repeatCopy(None, range(5))
        >>> q = Stream()
        >>> q.repeatCopy(p, range(0,50,10))
        >>> len(q.flat)        
        25
        >>> q.highestOffset
        40.0
        >>> q.flat.highestOffset
        44.0
        >>> r = Stream()
        >>> r.repeatCopy(q, range(0, 500, 100))
        >>> len(r.flat)
        125
        >>> r.highestOffset
        400.0
        >>> r.flat.highestOffset
        444.0
        '''
        if self._cache["HighestOffset"] is not None:
            pass # return cache unaltered
        elif len(self.elements) == 0:
            self._cache["HighestOffset"] = 0.0
        elif self.isSorted is True:
            lastEl = self.elements[-1]
            self._cache["HighestOffset"] = lastEl.offset 
        else: # iterate through all elements
            max = None
            for thisElement in self.elements:
                elEndTime = None
                elEndTime = thisElement.offset
                if max is None or elEndTime > max :
                    max = elEndTime
            self._cache["HighestOffset"] = max
        return self._cache["HighestOffset"]

    highestOffset = property(_getHighestOffset, doc='''
        Get start time of element with the highest offset in the Stream

        >>> a = Stream()
        >>> for x in range(3,5):
        ...     e = Element(note.Note('G#'))
        ...     e.offset = x * 3
        ...     a.append(e)
        ...
        >>> a.highestOffset
        12.0

        ''')

    def _getHighestTime(self):
        '''The largest offset plus duration.

        >>> n = note.Note('A-')
        >>> n.quarterLength = 3
        >>> p = Stream()
        >>> p.repeatCopy(n, range(5))
        >>> p.highestTime # 4 + 3
        7.0
        >>> q = Stream()
        >>> q.repeatCopy(p, [20, 0, 10, 30, 40]) # insert out of order
        >>> len(q.flat)        
        25
        >>> q.highestTime # this works b/c the component Stream has an dur
        47.0
        >>> q.flat.highestTime # 44 + 3
        47.0
        >>> r = Stream()
        >>> r.repeatCopy(q, range(0, 500, 100))
        >>> len(r.flat)
        125
        >>> r.highestOffset
        400.0
        >>> r.highestTime
        447.0
        >>> r.flat.highestTime
        447.0
        >>> q.flat.highestOffset
        44.0
        >>> r = Stream()
        >>> r.repeatCopy(q, range(0, 500, 100))
        >>> len(r.flat)
        125
        >>> r.highestOffset
        400.0
        >>> r.flat.highestOffset
        444.0
        '''

        if self._cache["HighestTime"] is not None:
            pass # retrun cache unaltered
        elif len(self.elements) == 0:
            self._cache["HighestTime"] = 0.0
        elif self.isSorted is True:
            lastEl = self.elements[-1]
            if hasattr(lastEl, "duration") and hasattr(lastEl.duration, "quarterLength"):
                #environLocal.printDebug([lastEl.offset,
                #         lastEl.offsetlastEl.duration.quarterLength])
                self._cache["HighestTime"] = lastEl.offset + lastEl.duration.quarterLength
            else:
                self._cache["HighestTime"]  = lastEl.offset 
        else:
            max = None
            for thisElement in self.elements:
                elEndTime = None
                if hasattr(thisElement, "duration") and hasattr(thisElement.duration, "quarterLength"):
                    elEndTime = thisElement.offset + thisElement.duration.quarterLength
                else:
                    elEndTime = thisElement.offset
                if max is None or elEndTime > max :
                    max = elEndTime
            self._cache["HighestTime"] = max

        return self._cache["HighestTime"]

    
    highestTime = property(_getHighestTime, doc='''
        returns the max(el.offset + el.duration.quarterLength) over all elements,
        usually representing the last "release" in the Stream.

        The duration of a Stream is usually equal to the highestTime expressed as a Duration object, 
        but can be set separately.  See below.
        ''')




    
    def _getLowestOffset(self):
        '''
        >>> p = Stream()
        >>> p.repeatCopy(None, range(5))
        >>> q = Stream()
        >>> q.repeatCopy(p, range(0,50,10))
        >>> len(q.flat)        
        25
        >>> q.lowestOffset
        0.0
        >>> r = Stream()
        >>> r.repeatCopy(q, range(97, 500, 100))
        >>> len(r.flat)
        125
        >>> r.lowestOffset
        97.0
        '''
        if self._cache["LowestOffset"] is not None:
            pass # return cache unaltered
        elif len(self.elements) == 0:
            self._cache["LowestOffset"] = 0.0
        elif self.isSorted is True:
            firstEl = self.elements[0]
            self._cache["LowestOffset"] = firstEl.offset 
        else: # iterate through all elements
            min = None
            for thisElement in self.elements:
                elStartTime = None
                elStartTime = thisElement.offset
                if min is None or elStartTime < min :
                    min = elStartTime
            self._cache["LowestOffset"] = min
        return self._cache["LowestOffset"]

    lowestOffset = property(_getLowestOffset, doc='''
        Get start time of element with the lowest offset in the Stream

        >>> a = Stream()
        >>> a.lowestOffset
        0.0
        >>> for x in range(3,5):
        ...     e = Element(note.Note('G#'))
        ...     e.offset = x * 3
        ...     a.append(e)
        ...
        >>> a.lowestOffset
        9.0

        ''')




    def _getDuration(self):
        '''
        Gets the duration of the Element (if separately set), but
        normal returns the duration of the component object if available, otherwise
        returns None.

        '''

        if self._unlinkedDuration is not None:
            return self._unlinkedDuration
        elif self._cache["Duration"] is not None:
            return self._cache["Duration"]
        else:
            self._cache["Duration"] = duration.Duration()
            self._cache["Duration"].quarterLength = self.highestTime
            return self._cache["Duration"]



    def _setDuration(self, durationObj):
        '''
        Set the total duration of the Stream independently of the highestTime  
        of the stream.  Useful to define the scope of the stream as independent
        of its constituted elements.
        
        If set to None, then the default behavior of computing automatically from highestTime is reestablished.
        '''
        if (isinstance(durationObj, music21.duration.DurationCommon)):
            self._unlinkedDuration = durationObj
        elif (durationObj is None):
            self._unlinkedDuration = None
        else:
            # need to permit Duration object assignment here
            raise Exception, 'this must be a Duration object, not %s' % durationObj

    duration = property(_getDuration, _setDuration, doc='''
    Returns the total duration of the Stream, from the beginning of the stream until the end of the final element.
    May be set independently by supplying a Duration object.

    >>> a = Stream()
    >>> q = note.QuarterNote()
    >>> a.repeatCopy(q, [0,1,2,3])
    >>> a.highestOffset
    3.0
    >>> a.highestTime
    4.0
    >>> a.duration.quarterLength
    4.0
    
    >>> # Advanced usage: overriding the duration
    >>> newDuration = duration.Duration("half")
    >>> newDuration.quarterLength
    2.0

    >>> a.duration = newDuration
    >>> a.duration.quarterLength
    2.0
    >>> a.highestTime # unchanged
    4.0
    ''')

    #---------------------------------------------------------------------------
    def _getLily(self):
        '''Returns the stream translated into Lilypond format.'''
        if self._overriddenLily is not None:
            return self._overriddenLily
        elif self._cache["lily"] is not None:
            return self._cache["lily"]
        
        lilyout = u" { "
#        if self.showTimeSignature is not False and self.timeSignature is not None:
#            lilyout += self.timeSignature.lily
    
        for thisObject in self.elements:
            if hasattr(thisObject, "startTransparency") and thisObject.startTransparency is True:
                lilyout += lilyModule.TRANSPARENCY_START

            if hasattr(thisObject.duration, "tuplets") and thisObject.duration.tuplets:
                if thisObject.duration.tuplets[0].type == "start":
                    numerator = str(int(thisObject.duration.tuplets[0].tupletNormal[0]))
                    denominator = str(int(thisObject.duration.tuplets[0].tupletActual[0]))
                    lilyout += "\\times " + numerator + "/" + denominator + " {"
                    ### TODO-- should get the actual ratio not assume that the
                    ### type of top and bottom are the same
            if hasattr(thisObject, "lily"):
                lilyout += unicode(thisObject.lily)
                lilyout += " "
            else:
                pass
            
            if hasattr(thisObject.duration, "tuplets") and thisObject.duration.tuplets:
                if thisObject.duration.tuplets[0].type == "stop":
                    lilyout = lilyout.rstrip()
                    lilyout += "} "

            if hasattr(thisObject, "stopTransparency") and thisObject.stopTransparency == True:
                lilyout += lilyModule.TRANSPARENCY_STOP
        
        lilyout += " } "
        lilyObj = lilyModule.LilyString(lilyout)
        self._cache["lily"] = lilyObj
        return lilyObj

    def _setLily(self, value):
        '''Sets the Lilypond output for the stream. Overrides what is obtained
        from get_lily.'''
        self._overriddenLily = value
        self._cache["lily"] = None

    lily = property(_getLily, _setLily)



    def _getMXPart(self, instObj=None, meterStream=None, refStream=None):
        '''If there are Measures within this stream, use them to create and
        return an MX Part and ScorePart. 

        meterStream can be provided to provide a template within which
        these events are positioned; this is necessary for handling
        cases where one part is shorter than another. 
        '''
        #environLocal.printDebug(['calling _getMXPart'])

        if instObj == None:
            # see if an instrument is defined in this or a parent stream
            instObj = self.getInstrument()

        # instruments are defined here
        mxScorePart = musicxmlMod.ScorePart()
        mxScorePart.set('partName', instObj.partName)
        mxScorePart.set('id', instObj.partId)

        mxPart = musicxmlMod.Part()
        mxPart.setDefaults()
        mxPart.set('id', instObj.partId) # need to set id

        # get a stream of measures
        # if flat is used here, the Measure is not obtained
        # may need to be semi flat?
        measureStream = self.getElementsByClass(Measure)
        if len(measureStream) == 0:
            # try to add measures if none defined
            measureStream = makeMeasures(self, meterStream, refStream)
            measureStream = makeTies(measureStream, meterStream)
            measureStream = makeBeams(measureStream)

            if len(measureStream) == 0:            
                raise StreamException('no measures found in stream with %s elements' % (self.__len__()))
            environLocal.printDebug(['created measures:', len(measureStream)])
        # for each measure, call .mx to get the musicxml representation
        for obj in measureStream:
            mxPart.append(obj.mx)

        # mxScorePart contains mxInstrument
        return mxScorePart, mxPart


    def _getMX(self):
        '''Create and return a musicxml score.

        >>> a = note.Note()
        >>> b = Measure()
        >>> b.append(a)
        >>> c = Stream()
        >>> c.append(b)
        >>> mxScore = c.mx
        '''
        environLocal.printDebug('calling _getMX')

        mxComponents = []
        instList = []
        multiPart = False
        meterStream = self.getTimeSignatures() # get from containter first

        # we need independent sub-stream elements to shfitin presentatioin
        highestTime = 0

        for obj in self:
            # if obj is a Part, we have mutli-parts
            if isinstance(obj, Part):
                multiPart = True
                break # only need one
            # if components are Measures, self is a part
            elif isinstance(obj, Measure):
                multiPart = False
                break # only need one
            # if components are streams of Notes or Measures, 
            # than assume this is like a part
            elif isinstance(obj, Stream) and (len(obj.measures) > 0 
                or len(obj.notes) > 0):
                multiPart = True
                break # only need one

        if multiPart:
            # need to edit streams contained within streams
            # must repack into a new stream at each step
            midStream = Stream()
            finalStream = Stream()
            partStream = self.deepcopy()

            for obj in partStream.getElementsByClass(Stream):
                # need to copy element here
                obj.applyOffset() # apply this streams offset to elements

                ts = obj.getTimeSignatures()
                # the longest meterStream is used as the meterStream for all parts
                if len(ts) > meterStream:
                    meterStream = ts
                ht = obj.highestTime
                if ht > highestTime:
                    highestTime = ht
                midStream.append(obj)

            refStream = Stream()
            refStream.insertAtOffset(None, 0) # placeholder at 0
            refStream.insertAtOffset(None, highestTime) 

            # would like to do something like this but cannot
            # replace object inside of the stream
            for obj in midStream.getElementsByClass(Stream):
                obj = makeRests(obj, refStream)
                finalStream.append(makeRests(obj, refStream))

            environLocal.printDebug('handling multi-part Stream')
            for obj in finalStream:
                # only things that can be treated as parts ar ehere
                inst = obj.getInstrument()
                instIdList = [x.partId for x in instList]
                #environLocal.printDebug(['instIdList', instIdList])
                if inst.partId in instIdList: # must have unique ids 
                    inst.partIdRandomize() # set new random id
                instList.append(inst)
                mxComponents.append(obj._getMXPart(inst, meterStream,
                                refStream))

        else: # assume this is the only part
            environLocal.printDebug('handling single-part Stream')
            mxComponents.append(self._getMXPart())


        # create score and part list
        mxPartList = musicxmlMod.PartList()
        mxIdentification = musicxmlMod.Identification()
        mxIdentification.setDefaults() # will create a composer
        mxScore = musicxmlMod.Score()
        mxScore.setDefaults()
        mxScore.set('partList', mxPartList)
        mxScore.set('identification', mxIdentification)

        for mxScorePart, mxPart in mxComponents:
            mxPartList.append(mxScorePart)
            mxScore.append(mxPart)

        return mxScore


    def _setMXPart(self, mxScore, partId):
        '''Load a part given an mxScore and a part name.
        '''
        mxPart = mxScore.getPart(partId)
        mxInstrument = mxScore.getInstrument(partId)

        # create a new music21 instrument
        instrumentObj = instrument.Instrument()
        if mxInstrument != None:
            instrumentObj.mx = mxInstrument

        # add part id as group
        instrumentObj.groups.append(partId)

        streamPart = Part() # create a part instance for each part
        streamPart.append(instrumentObj) # add instrument at zero offset

        # offset is in quarter note length
        oMeasure = 0
        for mxMeasure in mxPart:
            # create a music21 measure and then assign to mx attribute
            m = Measure()
            m.mx = mxMeasure  # assign data into music21 measure 
            # add measure to stream at current offset for this measure
            streamPart.insertAtOffset(m, oMeasure)
            # increment measure offset for next time around
            oMeasure += m.timeSignature.barDuration.quarterLength 

        streamPart.addGroupForElements(partId) # set group for components 
        streamPart.groups.append(partId) # set group for stream itself

        # add to this stream
        # this assumes all start at the same place
        self.insertAtOffset(streamPart, 0)


    def _setMX(self, mxScore):
        '''Given an mxScore, build into this stream
        '''
        partNames = mxScore.getPartNames().keys()
        partNames.sort()
        for partName in partNames: # part names are part ids
            self._setMXPart(mxScore, partName)

    mx = property(_getMX, _setMX)
        


    def _getMusicXML(self):
        '''Provide a complete MusicXM: representation. 
        '''
        mxScore = self._getMX()
        return mxScore.xmlStr()

    def _setMusicXML(self, mxNote):
        '''
        '''
        pass

    musicxml = property(_getMusicXML, _setMusicXML)






    #---------------------------------------------------------------------------
    def _getDurSpan(self, flatStream):
        '''Given elementsSorted, create a lost of parallel
        values that represent dur spans, or start and end times.
        Assume durations of None imply 0

        >>> a = Stream()
        >>> a.repeatCopy(None, range(5))
        >>> a._getDurSpan(a.flat)
        [(0.0, 0.0), (1.0, 1.0), (2.0, 2.0), (3.0, 3.0), (4.0, 4.0)]
        '''
        post = []        
        for i in range(len(flatStream)):
            element = flatStream[i]
            if element.duration == None:
                durSpan = (element.offset, element.offset)
            else:
                dur = element.duration.quarterLength
                durSpan = (element.offset, element.offset+dur)
            post.append(durSpan)
        # assume this is already sorted 
        # index found here will be the same as elementsSorted
        return post


    def _durSpanOverlap(self, a, b, includeCoincidentBoundaries=False):
        '''
        Compare two durSpans and find overlaps; optionally, 
        includ coincident boundaries. a and b are sorted to permit any ordering.

        If an element ends at 3.0 and another starts at 3.0, this may or may not
        be considered an overlap. The includeCoincidentEnds parameter determines
        this behaviour, where ending and starting 3.0 being a type of overlap
        is set by the includeCoincidentBoundaries being True. 

        >>> a = Stream()
        >>> a._durSpanOverlap([0, 10], [11, 12], False)
        False
        >>> a._durSpanOverlap([11, 12], [0, 10], False)
        False
        >>> a._durSpanOverlap([0, 3], [3, 6], False)
        False
        >>> a._durSpanOverlap([0, 3], [3, 6], True)
        True
        '''

        durSpans = [a, b]
        # sorting will ensure that leading numbers are ordered from low to high
        durSpans.sort() 
        found = False

        if includeCoincidentBoundaries:
            # if the start of b is before the end of a
            if durSpans[1][0] <= durSpans[0][1]:   
                found = True
        else: # do not include coincident boundaries
            if durSpans[1][0] < durSpans[0][1]:   
                found = True
        return found



    def _findLayering(self, flatStream, includeNoneDur=True,
                   includeCoincidentBoundaries=False):
        '''Find any elements in an elementsSorted list that have simultaneities 
        or durations that cause overlaps.
        
        Returns two lists. Each list contains a list for each element in 
        elementsSorted. If that elements has overalps or simultaneities, 
        all index values that match are included in that list. 
        
        See testOverlaps, in unit tests, for examples. 
        
        
        '''
        flatStream = flatStream.sorted
        # these may not be sorted
        durSpanSorted = self._getDurSpan(flatStream)

        # create a list with an entry for each element
        # in each entry, provide indices of all other elements that overalap
        overlapMap = [[] for i in range(len(durSpanSorted))]
        # create a list of keys for events that start at the same time
        simultaneityMap = [[] for i in range(len(durSpanSorted))]
        
        for i in range(len(durSpanSorted)):
            src = durSpanSorted[i]
            # second entry is duration
            if not includeNoneDur and flatStream[i].duration == None: 
                continue
            # compare to all past and following durations
            for j in range(len(durSpanSorted)):
                if j == i: continue # do not compare to self
                dst = durSpanSorted[j]
                # print src, dst, self._durSpanOverlap(src, dst, includeCoincidentBoundaries)
        
                if src[0] == dst[0]: # if start times are the same
                    simultaneityMap[i].append(j)
        
                if self._durSpanOverlap(src, dst, includeCoincidentBoundaries):
                    overlapMap[i].append(j)
        
        return simultaneityMap, overlapMap



    def _consolidateLayering(self, flatStream, map):
        '''
        Given elementsSorted and a map of equal lenght with lists of 
        index values that meet a given condition (overlap or simultaneities),
        organize into a dictionary by the relevant or first offset
        '''
        flatStream = flatStream.sorted

        if len(map) != len(flatStream):
            raise StreamException('map must be the same length as flatStream')

        post = {}
        for i in range(len(map)):
            # print 'examining i:', i
            indices = map[i]
            if len(indices) > 0: 
                srcOffset = flatStream[i].offset
                srcElementObj = flatStream[i]
                dstOffset = None
                # print 'found indices', indices
                # check indices
                for j in indices: # indices of other elements tt overlap
                    elementObj = flatStream[j]

                    # check if this object has been stored anywhere yet
                    # if so, use the offset of where it was stored to 
                    # to store the src element below
                    store = True
                    for key in post.keys():
                        if elementObj in post[key]:
                            store = False
                            dstOffset = key
                            break
                    if dstOffset == None:
                        dstOffset = srcOffset
                    if store:
                        # print 'storing offset', dstOffset
                        if dstOffset not in post.keys():
                            post[dstOffset] = [] # create dictionary entry
                        post[dstOffset].append(elementObj)

                # check if this object has been stored anywhere yet
                store = True
                for key in post.keys():
                    if srcElementObj in post[key]:
                        store = False
                        break
                # dst offset may have been set when looking at indices
                if store:
                    if dstOffset == None:
                        dstOffset = srcOffset
                    if dstOffset not in post.keys():
                        post[dstOffset] = [] # create dictionary entry
                    # print 'storing offset', dstOffset
                    post[dstOffset].append(srcElementObj)
                    # print post
        return post



    def findGaps(self):
        '''
        returns either (1) a Stream containing Elements (that wrap the None object)
        whose offsets and durations are the length of gaps in the Stream
        or (2) None if there are no gaps.
        
        N.B. there may be gaps in the flattened representation of the stream
        but not in the unflattened.  Hence why "isSequence" calls self.flat.isGapless
        '''
        if self.cache["GapStream"]:
            return self.cache["GapStream"]
        
        sortedElements = self.sorted.elements
        gapStream = Stream()
        highestCurrentEndTime = 0
        for thisElement in sortedElements:
            if thisElement.offset > highestCurrentEndTime:
                gapElement = Element(obj = None, offset = highestCurrentEndTime)
                gapElement.duration = duration.Duration()
                gapElement.duration.quarterLength = thisElement.offset - highestCurrentEndTime
                gapStream.append(gapElement)
            highestCurrentEndTime = max(highestCurrentEndTime, thisElement.offset + thisElement.duration.quarterLength)

        if len(gapStream) == 0:
            return None
        else:
            self.cache["GapStream"] = gapStream
            return gapStream

    def _getIsGapless(self):
        if self._cache["isGapless"] is not None:
            return self._cache["isGapless"]
        else:
            if self.findGaps() is None:
                self._cache["Gapless"] = True
                return True
            else:
                self._cache["Gapless"] = False
                return False
            
    isGapless = property(_getIsGapless)
            
    def getSimultaneous(self, includeNoneDur=True):
        '''Find and return any elements that start at the same time. 
        >>> a = Stream()
        >>> for x in range(4):
        ...     n = note.Note('G#')
        ...     n.offset = x * 0
        ...     a.append(n)
        ...
        >>> b = a.getSimultaneous()
        >>> len(b[0]) == 4
        True
        >>> c = Stream()
        >>> for x in range(4):
        ...     n = note.Note('G#')
        ...     n.offset = x * 3
        ...     c.append(n)
        ...
        >>> d = c.getSimultaneous()
        >>> len(d) == 0
        True
        '''
        checkOverlap = False
        elementsSorted = self.flat.sorted
        simultaneityMap, overlapMap = self._findLayering(elementsSorted, 
                                                    includeNoneDur)
        
        return self._consolidateLayering(elementsSorted, simultaneityMap)


    def getOverlaps(self, includeNoneDur=True,
                     includeCoincidentBoundaries=False):
        '''Find any elements that overlap. Overlaping might include elements
        that have no duration but that are simultaneous. 
        Whether elements with None durations are included is determined by includeNoneDur.
        This example demosntrates end-joing overlaps: there are four quarter notes spaced by quarter notes. Whether or not these count as overalps
        is determined by the includeCoincidentBoundaries parameter. 

        >>> a = Stream()
        >>> for x in range(4):
        ...     n = note.Note('G#')
        ...     n.duration = duration.Duration('quarter')
        ...     n.offset = x * 1
        ...     a.append(n)
        ...
        >>> d = a.getOverlaps(True, False) 
        >>> len(d)
        0
        >>> d = a.getOverlaps(True, True) # including coincident boundaries
        >>> len(d)
        1
        >>> len(d[0])
        4
        >>> a = Stream()
        >>> for x in [0,0,0,0,13,13,13]:
        ...     n = note.Note('G#')
        ...     n.duration = duration.Duration('half')
        ...     n.offset = x * 1
        ...     a.append(n)
        ...
        >>> d = a.getOverlaps() 
        >>> len(d[0])
        4
        >>> len(d[13])
        3
        >>> a = Stream()
        >>> for x in [0,0,0,0,3,3,3]:
        ...     n = note.Note('G#')
        ...     n.duration = duration.Duration('whole')
        ...     e = Element(n)
        ...     e.offset = x * 1
        ...     a.append(e)
        ...
        >>> # default is to not include coincident boundaries
        >>> d = a.getOverlaps() 
        >>> len(d[0])
        7
        '''
        checkSimultaneity = False
        checkOverlap = True
        elementsSorted = self.flat.sorted
        simultaneityMap, overlapMap = self._findLayering(elementsSorted, 
                                includeNoneDur, includeCoincidentBoundaries)
        return self._consolidateLayering(elementsSorted, overlapMap)



    def isSequence(self, includeNoneDur=True, 
                        includeCoincidentBoundaries=False):
        '''A stream is a sequence if it has no overlaps.

        TODO: check that co-incident boundaries are properly handled
        >>> a = Stream()
        >>> for x in [0,0,0,0,3,3,3]:
        ...     n = note.Note('G#')
        ...     n.duration = duration.Duration('whole')
        ...     e = Element(n)
        ...     e.offset = x * 1
        ...     a.append(e)
        ...
        >>> a.isSequence()
        False
        '''
        elementsSorted = self.flat.sorted
        simultaneityMap, overlapMap = self._findLayering(elementsSorted, 
                                includeNoneDur, includeCoincidentBoundaries)
        post = True
        for indexList in overlapMap:
            if len(indexList) > 0:
                post = False
                break       
        return post





#-------------------------------------------------------------------------------
class Measure(Stream):
    # the music21 object need not know anything about musicxml;
    # all that data is contained within the musicxml objects
    # musicXmlTag = "measure"

    def __init__(self, *args, **keywords):
        Stream.__init__(self, *args, **keywords)
        self.timeSignature = None
        self.timeSignatureIsNew = False
        self.clef = None
        self.clefIsNew = False

        self.filled = False
        self.measureNumber = 0   # 0 means undefined or pickup
        self.measureNumberSuffix = None # for measure 14a would be "a"
        # inherits from prev measure or is default for group
        self.leftbarline = None  
        # inherits from next measure or is default for group
        self.rightbarline = None 
        # for display is overridden by next measure\'s leftbarline if that is not None and
        # the two measures are on the same system


        # TODO: it does not seem that Stream objects should be stored
        # as attributes in another stream: these elements will not be obtained
        # when this stream is flattend or other stream operations
        # are performed. it seems that all Streams, base music21 objects, and
        # Elements should be stored on the Stream's _elements list. 

        #self.internalbarlines = Stream()
        # "measure expressions" that are attached to nowhere in particular
        #self.timeIndependentDirections = Stream() 
        # list of times at which Directions take place.
        #self.timeDependentDirectionsTime = Stream() 
        # should be sorted always.
        # list of Directions that happen at a certain time, 
        # keep indices together
        #self.timeDependentDirections = Stream() 


    def addRepeat(self):
        # TODO: write
        pass

    def addTimeDependentDirection(self, time, direction):
        # TODO: write
        pass

    def addRightBarline(self, blStyle = None):
        self.rightbarline = measure.Barline(blStyle)
        return self.rightbarline
    
    def addLeftBarline(self, blStyle = None):
        self.leftbarline = measure.Barline(blStyle)
        return self.leftbarline
    
    def measureNumberWithSuffix(self):
        if self.measureNumberSuffix:
            return str(self.measureNumber) + self.measureNumberSuffix
        else:
            return str(self.measureNumber)
    
    def __repr__(self):
        return "<MEASURE %s %s offset=%s>" % \
            (self.__class__.__name__, self.measureNumberWithSuffix(), self.offset)
        

    #---------------------------------------------------------------------------
    # clef is stored in the Stream's elements list, however a property
    # is provided to store and access the clef as an attribute

    def _getClef(self):
        clefList = self.getElementsByClass(clef.Clef)
        # only return cleff that has a zero offset
        clefList = clefList.getElementsByOffset(0,0)
        if len(clefList) == 0:
            return None
        else:
            return clefList[0]    
    
    def _setClef(self, clefObj):
        self.insertAtOffset(clefObj, 0)


    clef = property(_getClef, _setClef)    


    #---------------------------------------------------------------------------
    def _getMxDynamics(self, mxDirection):
        '''Given an mxDirection, return a dynamics if present, otherwise, None

        This should be moved into musicxml.py, as a method of mxDirection
        '''
        mxDynamicsFound = []
        mxWedgeFound = []
        for mxObj in mxDirection:
            if isinstance(mxObj, musicxmlMod.DirectionType):
                for mxObjSub in mxObj:
                    if isinstance(mxObjSub, musicxmlMod.Dynamics):
                        for mxObjSubSub in mxObjSub:
                            if isinstance(mxObjSubSub, musicxmlMod.DynamicMark):
                                mxDynamicsFound.append(mxObjSubSub)
                    elif isinstance(mxObjSub, musicxmlMod.Wedge):
                        mxWedgeFound.append(mxObjSub)
        return mxDynamicsFound, mxWedgeFound

    def _getMX(self):
        '''Return a musicxml Measure, populated with notes, chords, rests
        and a musixcml Attributes, populated with time, meter, key, etc

        >>> a = note.Note()
        >>> a.quarterLength = 4
        >>> b = Measure()
        >>> b.insertAtOffset(a, 0)
        >>> len(b) # has a clef object in the stream
        2
        >>> mxMeasure = b.mx
        >>> len(mxMeasure) 
        1
        '''

        mxMeasure = musicxmlMod.Measure()
        mxMeasure.set('number', self.measureNumber)

        mxAttributes = musicxmlMod.Attributes()
        mxAttributes.setDefaults() # get basic defaults, divisions, etc

        if self.timeSignature != None:
            mxAttributes.timeList = self.timeSignature.mx 


        # need to look here at the parent, and try to find
        # the clef in the clef last defined in the parent
        if self.clef == None:
            # this will set a new clef for each measure
            mxAttributes.clefList = [self.bestClef().mx]
        else:
            mxAttributes.clefList = [self.clef.mx]

        #mxAttributes.keyList = []
        mxMeasure.set('attributes', mxAttributes)

        #need to handle objects in order when creating musicxml 
        for obj in self.flat:
            if isinstance(obj, note.GeneralNote):
                # .mx here returns a lost of notes
                mxMeasure.componentList += obj.mx
            elif isinstance(obj, dynamics.Dynamic):
                mxDynamicMark = obj.mx
                mxDynamics = musicxmlMod.Dynamics()
                mxDynamics.append(mxDynamicMark)
                mxDirectionType = musicxmlMod.DirectionType()
                mxDirectionType.append(mxDynamics)
                mxDirection = musicxmlMod.Direction()
                mxDirection.append(mxDirectionType)
                mxMeasure.append(mxDirection)
        return mxMeasure


    def _setMX(self, mxMeasure):
        '''Given an mxMeasure, create a music21 measure
        '''
        # measure number may be a string and not a number (always?)
        self.measureNumber = mxMeasure.get('number')
        junk = mxMeasure.get('implicit')
        # may not be available; may need to be obtained from 

        mxAttributes = mxMeasure.get('attributes')
        if mxAttributes == None:
            # not all measures have attributes definitions; this
            # gets the last-encountered measure attributes
            mxAttributes = mxMeasure.external['attributes']

            if mxAttributes == None:
                raise StreamException(
                    'no mxAttribues available for this measure')

        # if no time is defined, get the last defined value from external
        if len(mxAttributes.timeList) == 0:
            if mxMeasure.external['time'] != None:
                mxTimeList = [mxMeasure.external['time']]
            else:
                environLocal.printDebug('loading with default mxTime')
                mxTime = musicxmlMod.Time()
                mxTime.setDefaults()
                mxTimeList = [mxTime]
                #raise StreamException('no external mxTime object found within mxMeasure: %s' % mxMeasure)
        else:
            mxTimeList = mxAttributes.timeList
        self.timeSignature = meter.TimeSignature()
        self.timeSignature.mx = mxTimeList

        # only set clef if it is defined
        if len(mxAttributes.clefList) != 0:
            self.clef = clef.Clef()
            self.clef.mx = mxAttributes.clefList

        # set to zero for each measure
        offsetMeasureNote = 0 # offset of note w/n measure

        # bar Duration object
        barDuration = self.timeSignature.barDuration
        
        mxNoteList = [] # for chords

        for i in range(len(mxMeasure)):
            mxObj = mxMeasure[i]
            if i < len(mxMeasure)-1:
                mxObjNext = mxMeasure[i+1]
            else:
                mxObjNext = None

            if isinstance(mxObj, musicxmlMod.Note):
                mxNote = mxObj
                if isinstance(mxObjNext, musicxmlMod.Note):
                    mxNoteNext = mxObjNext
                else:
                    mxNoteNext = None
                # the first note of a chord is not identified; only
                # by looking at the next note can we tell if we have a 
                # chord
                if mxNoteNext != None and mxNoteNext.get('chord') == True:
                    if mxNote.get('chord') != True:
                        mxNote.set('chord', True) # set the first as a chord

                if mxNote.get('rest') in [None, False]: # its a note

                    if mxNote.get('chord') == True:
                        mxNoteList.append(mxNote)
                        offsetIncrement = 0
                    else:
                        n = note.Note()
                        n.mx = mxNote
                        self.insertAtOffset(n, offsetMeasureNote)
                        offsetIncrement = n.quarterLength

                    for mxLyric in mxNote.lyricList:
                        lyricObj = note.Lyric()
                        lyricObj.mx = mxLyric
                        n.lyrics.append(lyricObj)
                    if mxNote.get('notations') != None:
                        for mxObjSub in mxNote.get('notations'):
                            # deal with ornaments, strill, etc
                            pass
                else: # its a rest
                    n = note.Rest()
                    n.mx = mxNote # assign mxNote to rest obj
                    self.insertAtOffset(n, offsetMeasureNote)            
                    offsetIncrement = n.quarterLength

                # if we we have notes in the note list and the next
                # not either does not exist or is not a chord, we 
                # have a complete chord
                if len(mxNoteList) > 0 and (mxNoteNext == None 
                    or mxNoteNext.get('chord') == False):
                    c = chord.Chord()
                    c.mx = mxNoteList
                    mxNoteList = [] # clear for next chord
                    self.insertAtOffset(c, offsetMeasureNote)
                    offsetIncrement = c.quarterLength

                # do not need to increment for musicxml chords
                offsetMeasureNote += offsetIncrement

            # load dynamics into measure
            elif isinstance(mxObj, musicxmlMod.Direction):
                mxDynamicsFound, mxWedgeFound = self._getMxDynamics(mxObj)
                for mxDynamicMark in mxDynamicsFound:
                    d = dynamics.Dynamic()
                    d.mx = mxDynamicMark
                    self.insertAtOffset(d, offsetMeasureNote)  
                for mxWedge in mxWedgeFound:
                    w = dynamics.Wedge()
                    w.mx = mxWedge     
                    self.insertAtOffset(w, offsetMeasureNote)  

    mx = property(_getMX, _setMX)    




    def _getMusicXML(self):
        '''Provide a complete MusicXML: representation. 
        '''

        mxMeasure = self._getMX()

        mxPart = musicxmlMod.Part()
        mxPart.setDefaults()
        mxPart.append(mxMeasure) # append measure here


        # see if an instrument is defined in this or a prent stream
        instObj = self.getInstrument()
        mxScorePart = musicxmlMod.ScorePart()
        mxScorePart.set('partName', instObj.partName)
        mxScorePart.set('id', instObj.partId)
        # must set this part to the same id
        mxPart.set('id', instObj.partId)

        mxPartList = musicxmlMod.PartList()
        mxPartList.append(mxScorePart)

        mxIdentification = musicxmlMod.Identification()
        mxIdentification.setDefaults() # will create a composer
        mxScore = musicxmlMod.Score()
        mxScore.setDefaults()
        mxScore.set('partList', mxPartList)
        mxScore.set('identification', mxIdentification)
        mxScore.append(mxPart)

        return mxScore.xmlStr()

    def _setMusicXML(self, mxScore):
        '''
        '''
        pass

    musicxml = property(_getMusicXML, _setMusicXML)










#-------------------------------------------------------------------------------
class Part(Stream):
    '''A stream subclass for containing parts.
    '''

    def _getLily(self):
        lv = Stream._getLily(self)
        lv2 = lilyModule.LilyString(" \\new Staff " + lv.value)
        return lv2
    
    lily = property(_getLily)



class Score(Stream):
    """A Stream subclass for handling multi-part music."""

    def __init__(self, *args, **keywords):
        Stream.__init__(self, *args, **keywords)


    def _getLily(self):
        '''
        returns the lily code for a score.
        '''
        ret = lilyModule.LilyString()
        for thisOffsetPosition in self.groupElementsByOffset():
            if len(thisOffsetPosition) > 1:
                ret += " << "
                for thisSubElement in thisOffsetPosition:
                    if hasattr(thisSubElement, "lily"):
                        ret += thisSubElement.lily
                    else:
                        # TODO: write out debug code here
                        pass
                ret += " >> "
            else:
                if hasattr(thisOffsetPosition[0], "lily"):
                    ret += thisOffsetPosition[0].lily
                else:
                    # TODO: write out debug code here
                    pass
        return ret
        
    lily = property(_getLily)











#-------------------------------------------------------------------------------
class TestExternal(unittest.TestCase):
    def runTest(self):
        pass
    
    def testLilySimple(self):
        a = Stream()
        ts = meter.TimeSignature("3/4")
        
        b = Stream()
        q = note.QuarterNote()
        q.octave = 5
        b.repeatCopy(q, [0,1,2,3])
        
        bestC = b.bestClef(allowTreble8vb = True)
        a.append(bestC)
        a.append(ts)
        a.append(b)
        a.lily.showPNG()

    def testLilySemiComplex(self):
        a = Stream()
        ts = meter.TimeSignature("3/8")
        
        b = Stream()
        q = note.EighthNote()

        dur1 = duration.Duration()
        dur1.type = "eighth"
        
        tup1 = duration.Tuplet()
        tup1.tupletActual = [5, dur1]
        tup1.tupletNormal = [3, dur1]

        q.octave = 2
        q.duration.tuplets.append(tup1)
        
        
        for i in range(0,5):
            b.addNext(q.deepcopy())
            b.elements[i].accidental = note.Accidental(i - 2)
        
        b.elements[0].duration.tuplets[0].type = "start"
        b.elements[-1].duration.tuplets[0].type = "stop"
        b.elements[2].editorial.comment.text = "a real C"
         
        bestC = b.bestClef(allowTreble8vb = True)
        a.append(bestC)
        a.append(ts)
        a.append(b)
        a.lily.showPNG()


    def testMXOutput(self):

        c = Stream()
        for m in range(4):
            b = Measure()
            for pitch in ['a', 'g', 'c#', 'a#']:
                a = note.Note(pitch)
                b.append(a)
            c.append(b)
        c.show()

        
    def testScoreLily(self):
        import meter
        c = note.Note("C4")
        d = note.Note("D4")
        ts = meter.TimeSignature("2/4")
        s1 = Part()
        s1.addNext(c.copy())
        s1.addNext(d.copy())
        s2 = Part()
        s2.addNext(d.copy())
        s2.addNext(c.copy())
        score1 = Score()
        score1.append(ts)
        score1.append(s1)
        score1.append(s2)
        score1.lily.showPNG()
        

    def testMxMeasures(self):

        n = note.Note()        
        n.quarterLength = 3
        a = Stream()
        a.repeatCopy(n, range(0,120,3))
        #a.show() # default time signature used
        
        a.insertAtOffset(meter.TimeSignature("5/4"), 0)
        a.insertAtOffset(meter.TimeSignature("2/4"), 10)
        a.insertAtOffset(meter.TimeSignature("3/16"), 3)
        a.insertAtOffset(meter.TimeSignature("9/8"), 20)
        a.insertAtOffset(meter.TimeSignature("10/4"), 40)
        a.show()


    def testMultipartStreams(self):
        '''Test the creation of multi-part streams w/o Measures or Parts

        Note: this does not work correctly yet, as all measures are note represented b/c each part is a different length 
        '''
        q = Stream()
        r = Stream()
        for x in ['c3','a3','g#4','d2'] * 10:
            n = note.Note(x)
            n.quarterLength = .25
            q.addNext(n)

            m = note.Note(x)
            m.quarterLength = 1.125
            r.addNext(m)

        s = Stream() # container
        s.append(q)
        s.append(r)
        s.insertAtOffset(meter.TimeSignature("3/4"), 0)
        s.insertAtOffset(meter.TimeSignature("5/4"), 3)
        s.insertAtOffset(meter.TimeSignature("3/4"), 8)

        s.show()
            


    def testMultipartMeasures(self):
        from music21 import corpus, converter
        a = converter.parse(corpus.paths[36])
        b = a[3][10:20]
        c = a[3][20:30]
        d = a[3][30:40]

        s = Stream()
        s.append(b)
        s.append(c)
        s.append(d)
        s.show()


    def testCanons(self):
        a = ['c', 'g#', 'd-', 'f#', 'e', 'f' ] * 4

        s = Stream()
        partOffsetShift = 1.25
        partOffset = 0
        for part in range(6):
            p = Stream()
            for pitchName in a:
                n = note.Note(pitchName)
                n.quarterLength = 1.5
                p.addNext(n)
            p.offset = partOffset
            s.append(p)
            partOffset += partOffsetShift

        s.show()



    def testBeamsPartial(self):
        q = Stream()
        for x in [.125, .25, .25, .125, .125, .125] * 30:
            n = note.Note('c')
            n.quarterLength = x
            q.addNext(n)

        s = Stream() # container
        s.append(q)

        s.insertAtOffset(meter.TimeSignature("3/4"), 0)
        s.insertAtOffset(meter.TimeSignature("5/4"), 3)
        s.insertAtOffset(meter.TimeSignature("4/4"), 8)

        s.show()


    def testBeamsStream(self):
        q = Stream()
        r = Stream()
        p = Stream()

        for x in ['c3','a3','c#4','d3'] * 30:
            n = note.Note(x)
            #n.quarterLength = random.choice([.25, .125, .5])
            n.quarterLength = random.choice([.25])
            q.addNext(n)

            m = note.Note(x)
            m.quarterLength = .5
            r.addNext(m)

            o = note.Note(x)
            o.quarterLength = .125
            p.addNext(o)


        s = Stream() # container
        s.append(q)
        s.append(r)
        s.append(p)

        s.insertAtOffset(meter.TimeSignature("3/4"), 0)
        s.insertAtOffset(meter.TimeSignature("5/4"), 3)
        s.insertAtOffset(meter.TimeSignature("4/4"), 8)
        self.assertEqual(len(s.flat.notes), 360)

        s.show()


#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testEquality(self):
        a = Element()
        a.offset = 3.0
        c = Element()
        c.offset = 3.0
        assert (a == c)
        assert (a is not c)        

    def testAdd(self):
        a = Stream()
        a.fillNone(6)
        self.assertTrue(a.isFlat)
        a[2] = Element(note.Note("C#"))
        self.assertTrue(a.isFlat)
        a[3] = Stream()
        self.assertFalse(a.isFlat)

    def testSort(self):
        s = Stream()
        s.repeatCopy(note.Note("C#"), [0, 2, 4])
        s.repeatCopy(note.Note("D-"), [1, 3, 5])
        self.assertFalse(s.isSorted)
        y = s.sorted
        self.assertTrue(y.isSorted)
        g = ""
        for myElement in y:
            g += "%s: %s; " % (myElement.offset, myElement.name)
        self.assertEqual(g, '0.0: C#; 1.0: D-; 2.0: C#; 3.0: D-; 4.0: C#; 5.0: D-; ')

    def testStreamRecursion(self):
        srcStream = Stream()
        for x in range(6):
            n = note.Note('G#')
            n.duration = duration.Duration('quarter')
            e = Element(n)
            e.offset = x * 1
            srcStream.append(e)

        self.assertEqual(len(srcStream), 6)
        self.assertEqual(len(srcStream.flat), 6)

#        self.assertEqual(len(srcStream.getOverlaps()), 0)

        midStream = Stream()
        for x in range(4):
            srcNew = srcStream.copy()
            srcNew.offset = x * 10 
            midStream.append(srcNew)

        self.assertEqual(len(midStream), 4)
        self.assertEqual(len(midStream.flat), 24)
#        self.assertEqual(len(midStream.getOverlaps()), 0)

        farStream = Stream()
        for x in range(7):
            midNew = midStream.copy()
            midNew.offset = x * 100 
            farStream.append(midNew)

        self.assertEqual(len(farStream), 7)
        self.assertEqual(len(farStream.flat), 168)
#        self.assertEqual(len(farStream.getOverlaps()), 0)
#
        # get just offset times
        # elementsSorted returns offset, dur, element
        offsets = [a.offset for a in farStream.flat]

        # create what we epxect to be the offsets
        offsetsMatch = range(0, 6)
        offsetsMatch += [x + 10 for x in range(0, 6)]
        offsetsMatch += [x + 20 for x in range(0, 6)]
        offsetsMatch += [x + 30 for x in range(0, 6)]
        offsetsMatch += [x + 100 for x in range(0, 6)]
        offsetsMatch += [x + 110 for x in range(0, 6)]

        self.assertEqual(offsets[:len(offsetsMatch)], offsetsMatch)

    def testStreamSortRecursion(self):
        srcStream = Stream()
        for x in range(4):
            n = note.Note('G#')
            n.duration = duration.Duration('quarter')
            e = Element(n)
            e.offset = x * 2
            srcStream.append(e)  # 0, 2, 4, 6

        midStream = Stream()
        for x in range(4):
            srcNew = srcStream.copy()
            srcNew.offset = x * 5 
            midStream.append(srcNew) # 0, 5, 10, 15

        farStream = Stream()
        for x in range(4):
            midNew = midStream.copy()
            midNew.offset = x * 13
            farStream.append(midNew)  # 0, 13, 26, 39 

        # get just offset times
        # elementsSorted returns offset, dur, element
        offsets = [a.offset for a in farStream.flat.sorted]
        offsetsBrief = offsets[:20]
        self.assertEquals(offsetsBrief, [0, 2, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 15, 16, 17, 17, 18, 19, 19])





    def testOverlaps(self):
        a = Stream()
        # here, the thir item overlaps with the first
        for offset, dur in [(0,12), (3,2), (11,3)]:
            n = note.Note('G#')
            n.duration = duration.Duration()
            n.duration.quarterLength = dur
            e = Element(n)
            e.offset = offset
            a.append(e)

        includeNoneDur = True
        includeCoincidentBoundaries = False

        simultaneityMap, overlapMap = a._findLayering(a.flat, 
                                  includeNoneDur, includeCoincidentBoundaries)
        self.assertEqual(simultaneityMap, [[], [], []])
        self.assertEqual(overlapMap, [[1,2], [0], [0]])


        post = a._consolidateLayering(a.flat, overlapMap)
        # print post

        #found = a.getOverlaps(includeNoneDur, includeCoincidentBoundaries)
        # there should be one overlap group
        #self.assertEqual(len(found.keys()), 1)
        # there should be three items in this overlap group
        #self.assertEqual(len(found[0]), 3)

        a = Stream()
        # here, the thir item overlaps with the first
        for offset, dur in [(0,1), (1,2), (2,3)]:
            n = note.Note('G#')
            n.duration = duration.Duration()
            n.duration.quarterLength = dur
            e = Element(n)
            e.offset = offset
            a.append(e)

        includeNoneDur = True
        includeCoincidentBoundaries = True

        simultaneityMap, overlapMap = a._findLayering(a.flat, 
                                  includeNoneDur, includeCoincidentBoundaries)
        self.assertEqual(simultaneityMap, [[], [], []])
        self.assertEqual(overlapMap, [[1], [0,2], [1]])

        post = a._consolidateLayering(a.flat, overlapMap)



    def testStreamDuration(self):
        a = Stream()
        q = note.QuarterNote()
        a.repeatCopy(q, [0,1,2,3])
        self.assertEqual(a.highestOffset, 3)
        self.assertEqual(a.highestTime, 4)
        self.assertEqual(a.duration.quarterLength, 4.0)
         
        newDuration = duration.Duration("half")
        self.assertEqual(newDuration.quarterLength, 2.0)

        a.duration = newDuration
        self.assertEqual(a.duration.quarterLength, 2.0)
        self.assertEqual(a.highestTime, 4)

    def testLilySimple(self):
        a = Stream()
        ts = meter.TimeSignature("3/4")
        
        b = Stream()
        q = note.QuarterNote()
        q.octave = 5
        b.repeatCopy(q, [0,1,2,3])
        
        bestC = b.bestClef(allowTreble8vb = True)
        a.append(bestC)
        a.append(ts)
        a.append(b)
        self.assertEqual(a.lily.value, u' { \\clef "treble"  \\time 3/4   { c\'\'4 c\'\'4 c\'\'4 c\'\'4  }   } ')

    def testLilySemiComplex(self):
        a = Stream()
        ts = meter.TimeSignature("3/8")
        
        b = Stream()
        q = note.EighthNote()

        dur1 = duration.Duration()
        dur1.type = "eighth"
        
        tup1 = duration.Tuplet()
        tup1.tupletActual = [5, dur1]
        tup1.tupletNormal = [3, dur1]

        q.octave = 2
        q.duration.tuplets.append(tup1)
        
        
        for i in range(0,5):
            b.addNext(q.deepcopy())
            b.elements[i].accidental = note.Accidental(i - 2)
        
        b.elements[0].duration.tuplets[0].type = "start"
        b.elements[-1].duration.tuplets[0].type = "stop"
        b.elements[2].editorial.comment.text = "a real C"
        
        bestC = b.bestClef(allowTreble8vb = True)
        a.append(bestC)
        a.append(ts)
        a.append(b)
        self.assertEqual(a.lily.value,  u' { \\clef "bass"  \\time 3/8   { \\times 3/5 {ceses,8 ces,8 c,8_"a real C" cis,8 cisis,8}  }   } ')

    def testScoreLily(self):
        c = note.Note("C4")
        d = note.Note("D4")
        ts = meter.TimeSignature("2/4")
        s1 = Part()
        s1.addNext(c.copy())
        s1.addNext(d.copy())
        s2 = Part()
        s2.addNext(d.copy())
        s2.addNext(c.copy())
        score1 = Score()
        score1.append(ts)
        score1.append(s1)
        score1.append(s2)
        self.assertEqual(u" << \\time 2/4  \\new Staff  { c'4 d'4  }  \\new Staff  { d'4 c'4  }  >> ", score1.lily.value)



    def testMeasureStream(self):
        '''An approach to setting TimeSignature measures in offsets and durations
        '''
        a = meter.TimeSignature('3/4')
        b = meter.TimeSignature('5/4')
        c = meter.TimeSignature('2/4')


        a.duration = duration.Duration()
        b.duration = duration.Duration()
        c.duration = duration.Duration()

        # 20 measures of 3/4
        a.duration.quarterLength = 20 * a.barDuration.quarterLength
        # 10 measures of 5/4
        b.duration.quarterLength = 10 * b.barDuration.quarterLength
        # 5 measures of 2/4
        c.duration.quarterLength = 5 * c.barDuration.quarterLength


        m = Stream()
        m.addNext(a)
        m.addNext(b)
        m.addNext(c)
    
        self.assertEqual(m[1].offset, (20 * a.barDuration.quarterLength))    
        self.assertEqual(m[2].offset, ((20 * a.barDuration.quarterLength) + 
                                      (10 * b.barDuration.quarterLength)))    



    def testMultipartStream(self):
        '''Test the creation of streams with multiple parts. See versions
        of this tests in TestExternal for more details
        '''
        q = Stream()
        r = Stream()
        for x in ['c3','a3','g#4','d2'] * 10:
            n = note.Note(x)
            n.quarterLength = .25
            q.addNext(n)

            m = note.Note(x)
            m.quarterLength = 1
            r.addNext(m)

        s = Stream() # container
        s.append(q)
        s.append(r)
        s.insertAtOffset(meter.TimeSignature("3/4"), 0)
        s.insertAtOffset(meter.TimeSignature("5/4"), 3)
        s.insertAtOffset(meter.TimeSignature("3/4"), 8)
        self.assertEqual(len(s.flat.notes), 80)

        from music21 import corpus, converter
        a = converter.parse(corpus.paths[36])
        b = a[3][10:20]
        c = a[3][20:30]
        d = a[3][30:40]

        s = Stream()
        s.append(b)
        s.append(c)
        s.append(d)





if __name__ == "__main__":
    music21.mainTest(Test, TestExternal)