# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         search.py
# Purpose:      music21 classes for searching
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
'''
Methods and Classes useful in searching among repertories.
'''

import difflib
import math
import unittest, doctest
import music21
import music21.note
import music21.duration

class WildcardDuration(music21.duration.Duration):
    '''
    a wildcard duration (it might define a duration
    in itself, but the methods here will see that it
    is a wildcard of some sort)
    '''
    pass

class Wildcard(music21.Music21Object):
    '''
    An object that may have some properties defined, but others not that
    matches a single object in a music21 stream.  Equivalent to the
    regular expression "."

    >>> from music21 import *
    >>> wc1 = search.Wildcard()
    >>> wc1.pitch = pitch.Pitch("C")
    >>> st1 = stream.Stream()
    >>> st1.append(note.HalfNote("D"))
    >>> st1.append(wc1)    
    '''
    def __init__(self):
        music21.Music21Object.__init__(self)
        self.duration = WildcardDuration()

def rhythmicSearch(thisStream, searchStream):
    '''
    Takes two streams -- the first is the stream to be searched and the second
    is a stream of elements whose rhythms must match the first.  Returns a list
    of indices which begin a successful search.

    searches are made based on quarterLength.
    thus an dotted sixteenth-note and a quadruplet (4:3) eighth
    will match each other.    
    
    
    Example 1: First we will set up a simple stream for searching:
    
    
    >>> from music21 import *
    >>> thisStream = tinyNotation.TinyNotationStream("c4. d8 e4 g4. a8 f4. c4.", "3/4")
    >>> thisStream.show('text')
    {0.0} <music21.meter.TimeSignature 3/4>
    {0.0} <music21.note.Note C>
    {1.5} <music21.note.Note D>
    {2.0} <music21.note.Note E>
    {3.0} <music21.note.Note G>
    {4.5} <music21.note.Note A>
    {5.0} <music21.note.Note F>
    {6.5} <music21.note.Note C>    
    
    
    Now we will search for all dotted-quarter/eighth elements in the Stream:
    
    
    >>> searchStream1 = stream.Stream()
    >>> searchStream1.append(note.Note(quarterLength = 1.5))
    >>> searchStream1.append(note.Note(quarterLength = .5))
    >>> l = search.rhythmicSearch(thisStream, searchStream1)
    >>> l
    [1, 4]
    >>> stream.Stream(thisStream[4:6]).show('text')
    {3.0} <music21.note.Note G>
    {4.5} <music21.note.Note A>
    
    
    Slightly more advanced search: we will look for any instances of eighth, 
    followed by a note (or other element) of any length, followed by a dotted quarter 
    note.  Again, we will find two instances; this time we will tag them both with
    a TextExpression of "*" and then show the original stream:
    
    
    >>> searchStream2 = stream.Stream()
    >>> searchStream2.append(note.Note(quarterLength = .5))
    >>> searchStream2.append(search.Wildcard())
    >>> searchStream2.append(note.Note(quarterLength = 1.5))
    >>> l = search.rhythmicSearch(thisStream, searchStream2)
    >>> l
    [2, 5]
    >>> for found in l:
    ...     thisStream[found].lyric = "*"
    >>> #_DOCS_SHOW thisStream.show()
    
    
    .. image:: images/searchRhythmic1.*
        :width: 221

    
    Now we can test the search on a real dataset and show the types
    of preparation that are needed to make it most likely a success.
    We will look through the first movement of Beethoven's string quartet op. 59 no. 2
    looking to see how much more common the first search term (dotted-quarter, eighth)
    is than the second (eighth, anything, dotted-quarter).  In fact, my hypothesis
    was wrong, and the second term is actually more common than the first! (n.b. rests
    are being counted here as well as notes)
    
    
    >>> op59_2_1 = corpus.parse('beethoven/opus59no2', 1)
    >>> term1results = []
    >>> term2results = []
    >>> for p in op59_2_1.parts:
    ...    pf = p.flat.stripTies()  # consider tied notes as one long note
    ...    temp1 = search.rhythmicSearch(pf, searchStream1)
    ...    temp2 = search.rhythmicSearch(pf, searchStream2)
    ...    for found in temp1: term1results.append(found)
    ...    for found in temp2: term2results.append(found)
    >>> term1results
    [86, 283, 330, 430, 688, 1096, 1140, 1266, 21, 25, 952, 1100, 1135, 1236, 64, 252, 467, 688, 852, 1105, 1308, 1312, 1107]
    >>> term2results
    [241, 689, 690, 1054, 6, 13, 23, 114, 118, 280, 287, 288, 702, 709, 719, 983, 984, 1077, 11, 12, 118, 122, 339, 841, 842, 850, 1306, 1310, 26, 72, 78, 197, 223, 707, 992, 993]
    >>> float(len(term1results))/len(term2results)
    0.6388...
    
    
    OMIT_FROM_DOCS
    
    why doesn't this work?  thisStream[found].expressions.append(expressions.TextExpression("*"))
    
    '''
    
    searchLength = len(searchStream)
    if searchLength == 0:
        raise SearchException('the search Stream cannot be empty')
    streamLength = len(thisStream)
    foundEls = []
    for start in range(1 + streamLength - searchLength):
        miniStream = thisStream[start:start+searchLength]
        foundException = False
        for j in range(searchLength):
            x = searchStream[j].duration
            if "WildcardDuration" in searchStream[j].duration.classes:
                next
            elif searchStream[j].duration.quarterLength != thisStream[start + j].duration.quarterLength:
                foundException = True
                break
        if foundException == False:
            foundEls.append(start)
    return foundEls

def approximateNoteSearch(thisStream, otherStreams):
    '''
    searches the list of otherStreams and returns an ordered list of matches
    (each stream will have a new property of matchProbability to show how
    well it matches)


    >>> from music21 import *
    >>> s = converter.parse("c4 d8 e16 FF a'4 b-", "4/4")
    >>> o1 = converter.parse("c4 d8 e GG a' b-4", "4/4")
    >>> o1.id = 'o1'
    >>> o2 = converter.parse("d#2 f A a' G b", "4/4")
    >>> o2.id = 'o2'
    >>> o3 = converter.parse("c4 d e GG CCC r", "4/4")
    >>> o3.id = 'o3'
    >>> l = approximateNoteSearch(s, [o1, o2, o3])
    >>> for i in l:
    ...    print i.id, i.matchProbability
    o1 0.6666666...
    o3 0.5
    o2 0.0833333...
    '''
    isJunk = None
    n = thisStream.flat.notesAndRests
    thisStreamStr = translateStreamToString(n)
    sorterList = []
    for s in otherStreams:
        sn = s.flat.notesAndRests
        thatStreamStr = translateStreamToString(sn)
        ratio = difflib.SequenceMatcher(isJunk, thisStreamStr, thatStreamStr).ratio()
        s.matchProbability = ratio
        sorterList.append((ratio, s))
    sortedList = sorted(sorterList, key = lambda x: 1-x[0])
    sortedStreams = [x[1] for x in sortedList]
    return sortedStreams


def approximateNoteSearchNoRhythm(thisStream, otherStreams):
    '''
    searches the list of otherStreams and returns an ordered list of matches
    (each stream will have a new property of matchProbability to show how
    well it matches)


    >>> from music21 import *
    >>> s = converter.parse("c4 d8 e16 FF a'4 b-", "4/4")
    >>> o1 = converter.parse("c4 d8 e GG a' b-4", "4/4")
    >>> o1.id = 'o1'
    >>> o2 = converter.parse("d#2 f A a' G b", "4/4")
    >>> o2.id = 'o2'
    >>> o3 = converter.parse("c4 d e GG CCC r", "4/4")
    >>> o3.id = 'o3'
    >>> l = approximateNoteSearchNoRhythm(s, [o1, o2, o3])
    >>> for i in l:
    ...    print i.id, i.matchProbability
    o1 0.83333333...
    o3 0.5
    o2 0.1666666...
    '''
    isJunk = None
    n = thisStream.flat.notesAndRests
    thisStreamStr = translateStreamToStringNoRhythm(n)
    sorterList = []
    for s in otherStreams:
        sn = s.flat.notesAndRests
        thatStreamStr = translateStreamToStringNoRhythm(sn)
        ratio = difflib.SequenceMatcher(isJunk, thisStreamStr, thatStreamStr).ratio()
        s.matchProbability = ratio
        sorterList.append((ratio, s))
    sortedList = sorted(sorterList, key = lambda x: 1-x[0])
    sortedStreams = [x[1] for x in sortedList]
    return sortedStreams


def translateStreamToString(inputStream):
    '''
    takes a stream of notes only and returns
    a string for searching on.
    
    >>> from music21 import *
    >>> s = converter.parse("c4 d8 e16 FF8. a'8 b-2.", "3/4")
    >>> sn = s.flat.notes
    >>> streamString = translateStreamToString(sn)
    >>> print streamString
    <P>F@<)KQFF_
    >>> len(streamString)  
    12
    '''
    b = ''
    for n in inputStream:
        b += translateNoteWithDurationToBytes(n)
    return b


def translateStreamToStringNoRhythm(inputStream):
    '''
    takes a stream of notes only and returns
    a string for searching on.
    
    >>> from music21 import *
    >>> s = converter.parse("c4 d e FF a' b-", "4/4")
    >>> sn = s.flat.notes
    >>> translateStreamToStringNoRhythm(sn)
    '<>@)QF'
    '''
    b = ''
    for n in inputStream:
        b += translateNoteToByte(n)
    return b
  
def translateNoteToByte(n):
    '''
    takes a note.Note object and translates it to a single byte representation

    currently returns the chr() for the note's midi number. or chr(127) for rests
    

    >>> from music21 import *
    >>> n = note.Note("C4")
    >>> translateNoteToByte(n)
    '<'
    >>> ord(translateNoteToByte(n)) == n.midi
    True


    '''
    if n.isRest:
        return chr(127)
    elif n.isChord:
        if len(n.pitches) > 0:
            return chr(n.pitches[0].midi)
        else:
            return chr(127)
    else:
        return chr(n.midi)

def translateNoteWithDurationToBytes(n):
    '''
    takes a note.Note object and translates it to a two-byte representation

    currently returns the chr() for the note's midi number. or chr(127) for rests
    followed by the log of the quarter length (fitted to 1-127, see formula below)

    >>> from music21 import *
    >>> n = note.Note("C4")
    >>> n.duration.quarterLength = 3  # dotted half
    >>> trans = translateNoteWithDurationToBytes(n)
    >>> trans
    '<_'
    >>> (2**(ord(trans[1])/10.0))/256  # approximately 3
    2.828...
    
    '''
    firstByte = translateNoteToByte(n)
    duration1to127 = int(math.log(n.duration.quarterLength * 256, 2)*10)
    if duration1to127 >= 127:
        duration1to127 = 127
    elif duration1to127 == 0:
        duration1to127 = 1
    secondByte = chr(duration1to127)
    return firstByte + secondByte


class SearchException(music21.Music21Exception):
    pass


class Test(unittest.TestCase):
    def runTest(self):
        pass

    def testCopyAndDeepcopy(self):
        '''Test copying all objects defined in this module
        '''
        import sys, types, copy
        for part in sys.modules[self.__module__].__dict__.keys():
            match = False
            for skip in ['_', '__', 'Test', 'Exception']:
                if part.startswith(skip) or part.endswith(skip):
                    match = True
            if match:
                continue
            obj = getattr(sys.modules[self.__module__], part)
            if callable(obj) and not isinstance(obj, types.FunctionType):
                a = copy.copy(obj)
                b = copy.deepcopy(obj)

    

#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = []


if __name__ == "__main__":
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof

