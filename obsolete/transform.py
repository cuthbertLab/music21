#-------------------------------------------------------------------------------
# Name:         transform.py
# Purpose:      utility functions for processing and transforming streams
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    (c) 2009 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------





import unittest, doctest, random
import sys, types

import music21
from music21 import stream
from music21 import note
from music21 import dynamics
from music21 import duration
from music21 import defaults
from music21 import meter


_MOD = 'transform.py'




#-------------------------------------------------------------------------------

class TransformException(Exception):
    pass

#-------------------------------------------------------------------------------

def extendDuration(streamObj, objName):
    '''Given a stream and an object name, go through stream and find each 
    object. The time between adjacent objects is then assigned to the 
    duration of each object. The last duration of the last object is assigned
    to the end of the stream.

    >>> a = stream.Stream()
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
            raise TransformException('can only process objects with duration attributes')
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



def split(streamObj, objName, fx):
    '''Given a stream, get all objects specified by objName and then form
    two new streams, where fx returns 1/True for the first stream and other values for the second stream.

    Probably better named SplitByClass or similar.

    >>> a = stream.Stream()
    >>> for x in range(30,81):
    ...     n = note.Note()
    ...     n.midi = x
    ...     a.append(n)
    >>> fx = lambda n: n.midi > 60
    >>> b, c = split(a, note.Note, fx)
    >>> len(b)
    20
    >>> len(c)
    31
    '''
    a = stream.Stream()
    b = stream.Stream()
    for element in streamObj.getElementsByClass(objName):
        if fx(element):
            a.append(element)
        else:
            b.append(element)
    return a, b
        


#-------------------------------------------------------------------------------


# def makeMeasure(streamObj, meterStream=None):
#     '''Take a stream of one or more meters and use to partition all elements
#     found in another stream.
# 
#     meterStream can be a stream of Meters, or single TimeSignature
# 
#     >>> a = stream.Stream()
#     >>> a.fillNone(3)
#     >>> b = makeMeasure(a)
#     >>> c = meter.TimeSignature('3/4')
#     >>> x = makeMeasure(a, c)
# 
#     >>> d = stream.Stream()
#     >>> n = note.Note()
#     >>> d.repeatCopy(n, range(10))
#     >>> d.repeatCopy(n, [x+.5 for x in range(10)])
#     >>> x = makeMeasure(d)
# 
#     '''
# 
#     if len(streamObj) == 0:
#         raise TransformException('cannot process an empty stream')        
# 
#     if meterStream == None:
#         ts = meter.TimeSignature()
#         ts.numerator = defaults.meterNumerator
#         # provide numerical reprsentation, 4 of 3/4
#         ts.denominator = defaults.meterDenominatorBeatType
#         meterStream = stream.Stream()
#         meterStream.insertAtOffset(ts,0)
# 
#     elif isinstance(meterStream, meter.TimeSignature):
#         # pack it in a stream
#         ms = stream.Stream()
#         ms.insertAtOffset(meterStream,0)
#         meterStream = ms
#     elif not isinstance(meterStream, streamStream):
#         raise TransformException('cannot process stream with a %s' % meterStream)    
#     
#     # handle each element of stream;
#     # assume that flat/sorted options will be set before procesing
#     offsetMap = [] # list of start, start+dur, element
#     for e in streamObj:
#         if hasattr(e, 'duration') and e.duration != None:
#             dur = e.duration.quarterLength
#         else:
#             dur = 0 
#         offsetMap.append([e.offset, e.offset+dur, e])
# 
#     #offsetMap.sort() may not need to sort!
# 
#     oMin = min([start for start, end, e in offsetMap])
#     oMax = max([end for start, end, e in offsetMap])
# 
#     # create a stream of measures to contain the results
#     post = stream.Stream()
#     o = 0 # initial position could be elsewhere
#     meterCount = 0
#     while True:    
#         m = stream.Measure()
#         # get active time signature
#         ts = meterStream[meterCount % len(meterStream)]
#         m.timeSignature = ts
#         m.number = meterCount + 1
# 
#         if ts.barDuration.quarterLength == 0: # will cause an infinite loop
#             raise TransformException('time signature has no duration')    
# 
#         post.insertAtOffset(m, o)
#         o += ts.barDuration.quarterLength # incrment by meter length
# 
#         if o >= oMax: # may be zero
#             break # if length of this measure exceedes last offset
#         else:
#             meterCount += 1
#     
#     #print post.recurseRepr()
# 
#     # populate measures with elements
#     for start, end, e in offsetMap:
#         for i in range(len(post)):
#             m = post[i]
#             # seems like should be able to use m.duration.quarterLengths
#             mStart, mEnd = m.offset, m.offset + m.timeSignature.barDuration.quarterLength
#             # offset cannot start on end
#             if start >= mStart and start < mEnd:
#                 break
#         # i is the index of the measure that this element starts at
#         # mStart, mEnd are correct
# 
#         oNew = start - mStart # remove measure offset from element offset
#         # not copying elements here!
#         # here, we have the correct measure from above
#         m.insertAtOffset(e, oNew)
# 
#     #print post.recurseRepr()
# 
#     return post
# 
# 
# def makeTies(streamObj, meterStream=None):
#     '''Given a stream containing measures, examine each element in the sream
#     if the elements duration extends beyond the measures bound, create a tied 
#     entity.
# 
#     Edits the current stream in-place. 
# 
#     >>> d = stream.Stream()
#     >>> n = note.Note()
#     >>> n.quarterLength = 12
#     >>> d.repeatCopy(n, range(10))
#     >>> d.repeatCopy(n, [x+.5 for x in range(10)])
#     >>> x = makeMeasure(d)
# 
#     >>> x = makeTies(x)
#     '''
#     if len(streamObj) == 0:
#         raise TransformException('cannot process an empty stream')        
# 
#     # get measures from this stream
#     measureStream = streamObj.getElementsByClass(stream.Measure)
#     if len(measureStream) == 0:
#         raise TransformException('cannot process a stream without measures')        
# 
#     mCount = 0
#     while True:
#         # update on each iteration, as new measure may have been added
#         # to the stream 
#         measureStream = streamObj.getElementsByClass(stream.Measure)
#         if mCount >= len(measureStream):
#             break
#         m = measureStream[mCount]
#         if mCount + 1 < len(measureStream):
#             mNext = measureStream[mCount+1]
#             mNextAdd = False
#         else: # create a new measure
#             mNext = stream.Measure()
#             # set offset to last offset plus total length
#             mNext.offset = m.offset + m.timeSignature.barDuration.quarterLength
#             # create default time signature
#             # if no meterStream provided
#             if meterStream == None:
#                 ts = meter.TimeSignature()
#                 ts.numerator = defaults.meterNumerator
#                 ts.denominator = defaults.meterDenominatorBeatType
#             else: # get the appropriately positioned meter
#                 ts = meterStream[mCount % len(meterStream)]
#             mNext.timeSignature = ts
#             mNext.number = m.number + 1
#             mNextAdd = True
# 
#         # seems like should be able to use m.duration.quarterLengths
#         mStart, mEnd = 0, m.timeSignature.barDuration.quarterLength
#         for e in m:
#             if hasattr(e, 'duration') and e.duration != None:
#                 # check to see if duration is within Measure
#                 eEnd = e.offset + e.duration.quarterLength
#                 # assume end can be at boundary of end of measure
#                 if eEnd > mEnd:
#                     if e.offset >= mEnd:
#                         raise TransformException('element has offset %s within a measure that ends at offset %s' % (e.offset, mEnd))  
#                     qLenBegin = mEnd - e.offset
#                     #print 'e.offset, mEnd, qLenBegin', e.offset, mEnd, qLenBegin
#                     qLenRemain = e.duration.quarterLength - qLenBegin
#                     # modify existing duration
#                     e.duration.quarterLength = qLenBegin
#                     # create and palce new element
#                     eRemain = e.deepcopy()
#                     eRemain.duration.quarterLength = qLenRemain
#                     # TODO: need to set ties
# 
#                     # we are not sure that this element fits 
#                     # completely in the next measure
#                     mNext.insertAtOffset(eRemain, 0)
#                     if mNextAdd:
#                         streamObj.insertAtOffset(mNext, mNext.offset)
#         mCount += 1
# 
#     #print streamObj.recurseRepr()
# 
#     return streamObj


#     def applyTimeSignature(self, timeSignature = None,
#                            startingQtrPosition = 0, startingMeasure = 1):
#         '''applyTimeSignature(self, timeSignature = self.timeSignature, startingBeat,
#         startingMeasure)
# 
#         applies the timeSignature to the notes so they are aware of their
#         position in the measure.  alters stream object
# 
#         Does not yet handle ComplexNotes
# 
#         '''
# 
#         if (timeSignature is None):
#             timeSignature = self.timeSignature
#         if (timeSignature is None):
#             raise StreamException("Can't applyTimeSignature without a TimeSignature object")
# 
#         measureLength = timeSignature.barDuration.quarterLength
#         currentQtrPosition = startingQtrPosition
#         currentMeasure = startingMeasure
#         for i in range(len(self.notesAndRests)):
#             thisNote = self.notesAndRests[i]

# we probably do not need to continue to support a noteTimeInfo intermediary 
# data structure

#             self.noteTimeInfo[i]['quarterPosition'] = currentQtrPosition
#             self.noteTimeInfo[i]['measure'] = currentMeasure
#             self.noteTimeInfo[i]['beat'] = timeSignature.quarterPositionToBeat(currentQtrPosition)
#             if self.debug is True:
#                 print "Note %d: measure %3d, beat %3.3f, quarter %3.3f" % \
#                       (i, currentMeasure, timeSignature.quarterPositionToBeat(currentQtrPosition), currentQtrPosition)
#             
#             currentQtrPosition += thisNote.duration.quarterLength
#             (percentOff, additionalMeasures) = modf(currentQtrPosition/measureLength)
#             currentMeasure += additionalMeasures
#             currentQtrPosition = percentOff * measureLength






#     def sliceDurationsForMeasures(self, timeSignature = None):
#         '''run this AFTER applyTimeSignature: looks at each note's timeInfo
#         and splits its duration into different durations in order to make each duration
#         fit in one measure only.  Needed for proper LilyPond output.
#         '''
#         if (timeSignature is None):
#             timeSignature = self.timeSignature
#         if (timeSignature is None):
#             raise StreamException("Can't sliceDurationsForMeasures without a TimeSignature object")
# 
#         measureLength = timeSignature.barDuration.quarterLength
#         for i in range(len(self.notesAndRests)):
#             thisNote = self.notesAndRests[i]
#             qtrPosition = self.noteTimeInfo[i]['quarterPosition']
#             noteLength = thisNote.duration.quarterLength
#             if (noteLength + qtrPosition > measureLength):
#                 #measure length has been exceeded
#                 exceededLength = noteLength + qtrPosition - measureLength
#                 if not hasattr(thisNote.duration, "components"):
#                     raise StreamException("Cannot slice a simple Duration")
#                 if (len(thisNote.duration.components) == 0):
#                     thisNote.duration.transferDurationToComponent0()
#                 
#                 firstCut = measureLength - qtrPosition
#                 thisNote.duration.sliceComponentAtPosition(firstCut)
#                 exceededLength = exceededLength - firstCut
#                 cutPosition = firstCut
#                 
#                 while greaterThan(exceededLength, measureLength):
#                     cutPosition += measureLength
#                     if thisNote.duration.quarterLength > cutPosition:
#                         thisNote.duration.sliceComponentAtPosition(cutPosition)
#                     exceededLength = exceededLength - measureLength





#     def makeMeasures(self, timeSignature = None, startingQtrPosition = 0, startingMeasure = 1, fillMeasure = None):
#         '''run this AFTER applyTimeSignature
# 
#         timeSignature: TimeSignature object.  Otherwise uses self.timeSignature or raises StreamException
#         startingQtrPosition: place in the measure to begin (default zero)
#         startingMeasure: First measure number to begin on (default 1)
#         fillMeasure: if beginning midway through a measure, requires a music21.Measure object filled
#                      up to that point.  Does nothing unless startingQtrPosition is not zero
# 
#         Does not yet handle ComplexNotes
#         '''
#         
#         if (timeSignature is None):
#             timeSignature = self.timeSignature
#         if (timeSignature is None):
#             raise StreamException("Can't applyTimeSignature without a TimeSignature object")
#         
#         currentMeasure = startingMeasure
#         currentQtrPosition = startingQtrPosition
#         isFirstMeasure = True  # not measure 1 but the
#         if startingQtrPosition > 0:
#             if fillMeasure is None:
#                 raise StreamException("Need a Measure object for fillMeasure if startingQtrPosition is > 0")
#             else:
#                 currentMeasureObject = fillMeasure
#         else:
#             currentMeasureObject = measure.Measure()
#             currentMeasureObject.timeSignature = timeSignature
#             currentMeasureObject.number = currentMeasure
# 
#         returnMeasures = []
#         returnMeasures.append(currentMeasureObject)
#         lastNote = None
# 
#         for i in range(len(self.notesAndRests)):
#             thisNote = self.notesAndRests[i]
#             thisNoteMeasure = self.noteTimeInfo[i]['measure']
#             while thisNoteMeasure > currentMeasure:
#                 currentMeasureObject.filled = True
#                 currentMeasure += 1
#                 currentMeasure = thisNoteMeasure
#                 currentMeasureObject = measure.Measure()
#                 currentMeasureObject.timeSignature = timeSignature
#                 currentMeasureObject.number = int(currentMeasure)
#                 returnMeasures.append(currentMeasureObject)
#             currentMeasureObject.notesAndRests.append(thisNote)
#             currentQtrPosition += thisNote.duration.quarterLength
#             currentQtrPosition = currentQtrPosition % timeSignature.barDuration.quarterLength 
#             lastNote = thisNote
#         
#         if almostEquals(currentQtrPosition, 0):
#             currentMeasureObject.filled = True
# 
#         return returnMeasures
# 
# 


#-------------------------------------------------------------------------------


class Test(unittest.TestCase):

    def runTest(self):
        pass


    def testBasic(self):
        a = stream.Stream()
        n = note.Note()
        a.repeatCopy(n, range(0,50,10))


#-------------------------------------------------------------------------------
if __name__ == "__main__":

    if len(sys.argv) == 1:
        music21.mainTest(Test)

# no TestExternal defined...
#    elif len(sys.argv) == 3:
#        t = TestExternal()
#        # provide file path, output
#        t.processHistogram(sys.argv[1], sys.argv[2])



