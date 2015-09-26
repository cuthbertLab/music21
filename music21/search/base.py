# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         search/base.py
# Purpose:      music21 classes for searching within files
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2011-2013 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------



import copy
import difflib
import math
import unittest

from music21 import base as m21Base
from music21 import exceptions21
from music21 import duration

class WildcardDuration(duration.Duration):
    '''
    a wildcard duration (it might define a duration
    in itself, but the methods here will see that it
    is a wildcard of some sort)
    
    TODO: Write
    '''
    pass

class Wildcard(m21Base.Music21Object):
    '''
    An object that may have some properties defined, but others not that
    matches a single object in a music21 stream.  Equivalent to the
    regular expression "."

    
    >>> wc1 = search.Wildcard()
    >>> wc1.pitch = pitch.Pitch("C")
    >>> st1 = stream.Stream()
    >>> st1.append(note.Note("D", type='half'))
    >>> st1.append(wc1)    
    '''
    def __init__(self):
        m21Base.Music21Object.__init__(self)
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
    
    
    >>> thisStream = converter.parse("tinynotation: 3/4 c4. d8 e4 g4. a8 f4. c4.").flat
    >>> thisStream.show('text')
    {0.0} <music21.clef.TrebleClef>
    {0.0} <music21.meter.TimeSignature 3/4>
    {0.0} <music21.note.Note C>
    {1.5} <music21.note.Note D>
    {2.0} <music21.note.Note E>
    {3.0} <music21.note.Note G>
    {4.5} <music21.note.Note A>
    {5.0} <music21.note.Note F>
    {6.5} <music21.note.Note C>    
    {8.0} <music21.bar.Barline style=final>
        
    Now we will search for all dotted-quarter/eighth elements in the Stream:
    
    >>> searchStream1 = stream.Stream()
    >>> searchStream1.append(note.Note(quarterLength = 1.5))
    >>> searchStream1.append(note.Note(quarterLength = .5))
    >>> l = search.rhythmicSearch(thisStream, searchStream1)
    >>> l
    [2, 5]
    >>> stream.Stream(thisStream[5:7]).show('text')
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
    [3, 6]
    >>> for found in l:
    ...     thisStream[found].lyric = "*"
    >>> #_DOCS_SHOW thisStream.show()
    
    
    .. image:: images/searchRhythmic1.*
        :width: 221

    
    Now we can test the search on a real dataset and show the types
    of preparation that are needed to make it most likely a success.
    We will look through the first movement of Corelli Trio Sonata op. 3 no. 1 (F major)
    looking to see how much more common the first search term (dotted-quarter, eighth)
    is than the second (eighth, anything, dotted-quarter).  In fact, my hypothesis
    was wrong, and the second term is actually more common than the first! (n.b. rests
    are being counted here as well as notes)
    
    
    >>> grave = corpus.parse('corelli/opus3no1/1grave')
    >>> term1results = []
    >>> term2results = []
    >>> for p in grave.parts:
    ...    pf = p.flat.stripTies()  # consider tied notes as one long note
    ...    temp1 = search.rhythmicSearch(pf, searchStream1)
    ...    temp2 = search.rhythmicSearch(pf, searchStream2)
    ...    for found in temp1: term1results.append(found)
    ...    for found in temp2: term2results.append(found)
    >>> term1results
    [0, 7, 13, 21, 42, 57, 64, 66, 0, 5, 7, 19, 21, 40, 46, 63, 0, 8, 31, 61, 69, 71, 73, 97]
    >>> term2results
    [5, 29, 95]
    >>> float(len(term1results))/len(term2results)
    8.0
    
    
    OMIT_FROM_DOCS
    
    >>> s = stream.Stream()
    >>> search.rhythmicSearch(pf, s)
    Traceback (most recent call last):
    SearchException: the search Stream cannot be empty
    
    why doesn't this work?  thisStream[found].expressions.append(expressions.TextExpression("*"))
    
    '''
    
    searchLength = len(searchStream)
    if searchLength == 0:
        raise SearchException('the search Stream cannot be empty')
    streamLength = len(thisStream)
    foundEls = []
    for start in range(1 + streamLength - searchLength):
        #miniStream = thisStream[start:start+searchLength]
        foundException = False
        for j in range(searchLength):
            #x = searchStream[j].duration
            if "WildcardDuration" in searchStream[j].duration.classes:
                continue
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


    
    >>> s = converter.parse("tinynotation: 4/4 c4 d8 e16 FF a'4 b-")
    >>> o1 = converter.parse("tinynotation: 4/4 c4 d8 e GG a' b-4")
    >>> o1.id = 'o1'
    >>> o2 = converter.parse("tinynotation: 4/4 d#2 f A a' G b")
    >>> o2.id = 'o2'
    >>> o3 = converter.parse("tinynotation: 4/4 c8 d16 e32 FF32 a'8 b-8")
    >>> o3.id = 'o3'
    >>> l = search.approximateNoteSearch(s, [o1, o2, o3])
    >>> for i in l:
    ...    print("%s %r" % (i.id, i.matchProbability))
    o1 0.666666...
    o3 0.333333...
    o2 0.083333...
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


    
    >>> s = converter.parse("tinynotation: 4/4 c4 d8 e16 FF a'4 b-")
    >>> o1 = converter.parse("tinynotation: 4/4 c4 d8 e GG a' b-4")
    >>> o1.id = 'o1'
    >>> o2 = converter.parse("tinynotation: 4/4 d#2 f A a' G b")
    >>> o2.id = 'o2'
    >>> o3 = converter.parse("tinynotation: 4/4 c4 d e GG CCC r")
    >>> o3.id = 'o3'
    >>> l = search.approximateNoteSearchNoRhythm(s, [o1, o2, o3])
    >>> for i in l:
    ...    print("%s %r" % (i.id, i.matchProbability))
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



def approximateNoteSearchOnlyRhythm(thisStream, otherStreams):
    '''
    searches the list of otherStreams and returns an ordered list of matches
    (each stream will have a new property of matchProbability to show how
    well it matches)


    
    >>> s = converter.parse("tinynotation: 4/4 c4 d8 e16 FF a'4 b-")
    >>> o1 = converter.parse("tinynotation: 4/4 c4 d8 e GG a' b-4")
    >>> o1.id = 'o1'
    >>> o2 = converter.parse("tinynotation: 4/4 d#2 f A a' G b")
    >>> o2.id = 'o2'
    >>> o3 = converter.parse("tinynotation: 4/4 c4 d e GG CCC r")
    >>> o3.id = 'o3'
    >>> l = search.approximateNoteSearchOnlyRhythm(s, [o1, o2, o3])
    >>> for i in l:
    ...    print("%s %r" % (i.id, i.matchProbability))
    o1 0.5
    o3 0.33...
    o2 0.0
    '''
    isJunk = None
    n = thisStream.flat.notesAndRests
    thisStreamStr = translateStreamToStringOnlyRhythm(n)
    sorterList = []
    for s in otherStreams:
        sn = s.flat.notesAndRests
        thatStreamStr = translateStreamToStringOnlyRhythm(sn)
        ratio = difflib.SequenceMatcher(isJunk, thisStreamStr, thatStreamStr).ratio()
        s.matchProbability = ratio
        sorterList.append((ratio, s))
    sortedList = sorted(sorterList, key = lambda x: 1-x[0])
    sortedStreams = [x[1] for x in sortedList]
    return sortedStreams


def approximateNoteSearchWeighted(thisStream, otherStreams):
    '''
    searches the list of otherStreams and returns an ordered list of matches
    (each stream will have a new property of matchProbability to show how
    well it matches)


    
    >>> s = converter.parse("tinynotation: 4/4 c4 d8 e16 FF a'4 b-")
    >>> o1 = converter.parse("tinynotation: 4/4 c4 d8 e GG2 a' b-4")
    >>> o1.id = 'o1'
    >>> o2 = converter.parse("tinynotation: 4/4 AAA4 AAA8 AAA16 AAA16 AAA4 AAA4")
    >>> o2.id = 'o2'
    >>> o3 = converter.parse("tinynotation: 4/4 c8 d16 e32 FF32 a'8 b-8")
    >>> o3.id = 'o3'
    >>> o4 = converter.parse("tinynotation: 4/4 c1 d1 e1 FF1 a'1 b-1")
    >>> o4.id = 'o4'
    >>> l = search.approximateNoteSearchWeighted(s, [o1, o2, o3, o4])
    >>> for i in l:
    ...    print("%s %r" % (i.id, i.matchProbability))
    o3 0.83333...
    o1 0.75
    o4 0.75
    o2 0.25
    '''
    isJunk = None
    n = thisStream.flat.notesAndRests
    thisStreamStrPitches = translateStreamToStringNoRhythm(n)
    thisStreamStrDuration = translateStreamToStringOnlyRhythm(n)   
#    print "notes",thisStreamStrPitches
#    print "rhythm",thisStreamStrDuration 
    sorterList = []
    for s in otherStreams:
        sn = s.flat.notesAndRests
        thatStreamStrPitches = translateStreamToStringNoRhythm(sn)
        thatStreamStrDuration = translateStreamToStringOnlyRhythm(sn)
#        print "notes2",thatStreamStrPitches
#        print "rhythm2",thatStreamStrDuration 
        ratioPitches = difflib.SequenceMatcher(isJunk, thisStreamStrPitches, thatStreamStrPitches).ratio()
        ratioDuration = difflib.SequenceMatcher(isJunk,thisStreamStrDuration,thatStreamStrDuration).ratio()
        ratio = (3*ratioPitches+ratioDuration)/4.0
        s.matchProbability = ratio
        sorterList.append((ratio, s))
    sortedList = sorted(sorterList, key = lambda x: 1-x[0])
    sortedStreams = [x[1] for x in sortedList]
    return sortedStreams



def translateStreamToString(inputStream):
    '''
    takes a stream of notesAndRests only and returns
    a string for searching on.
    
    
    >>> s = converter.parse("tinynotation: 3/4 c4 d8 r16 FF8. a'8 b-2.")
    >>> sn = s.flat.notesAndRests
    >>> streamString = search.translateStreamToString(sn)
    >>> print(streamString)
    <P>F<)KQFF_
    >>> len(streamString)  
    12
    '''
    b = ''
    for n in inputStream:
        b += translateNoteWithDurationToBytes(n)
    return b

def translateDiatonicStreamToString(inputStream, previousRest=False, previousTie=False, previousQL=None, returnLastTuple=False):
    r'''
    translates a stream of Notes and Rests only into a string,
    encoding only the .step (no accidental or octave) and whether
    the note is slower, faster, or the same speed as the previous
    note.
    
    Skips all but the first note of tie. Skips multiple rests in a row 
    
    Each note gets one byte:
    
    A-G = note of same length as previous
    H-N = note of longer length than previous
    O-U = note of shorter length than previous
    Z = rest
    
    
    >>> s = converter.parse("tinynotation: 3/4 c4 d8~ d16 r16 FF8 F#8 a'8 b-2.")
    >>> sn = s.flat.notesAndRests
    >>> streamString = search.translateDiatonicStreamToString(sn)
    >>> print(streamString)
    CRZFFAI
    >>> len(streamString)
    7
    
    If returnLastTuple is True, returns a triplet of whether the last note
    was a rest, whether the last note was tied, and what the last quarterLength was,
    which can be fed back into this algorithm:
    
    >>> streamString2, lastTuple = search.translateDiatonicStreamToString(sn, returnLastTuple = True)
    >>> streamString == streamString2
    True
    >>> lastTuple
    (False, False, 3.0)
    '''
    b = []
#    previousRest = False
#    previousTie = False
#    previousQL = None
    for n in inputStream:
        if n.isRest:
            if previousRest is True:
                continue
            else:
                previousRest = True
                b.append('Z')
                continue
        else:
            previousRest = False
        if previousTie is True:
            if n.tie is None or n.tie.type == 'stop':
                previousTie = False
            continue
        elif n.tie is not None:
            previousTie = True
        ql = n.duration.quarterLength
        if previousQL is None or previousQL == ql:
            ascShift = 0
        elif previousQL > ql:
            ascShift = 14
        else:
            ascShift = 7
        previousQL = ql
        newName = chr(ord(n.pitch.step) + ascShift)
        b.append(newName)
    
    if returnLastTuple is False:
        return ''.join(b)
    else:
        joined = ''.join(b)
        return (joined, (previousRest, previousTie, previousQL))

def translateStreamToStringNoRhythm(inputStream):
    '''
    takes a stream of notesAndRests only and returns
    a string for searching on, using translateNoteToByte.
    
    >>> s = converter.parse("tinynotation: 4/4 c4 d e FF a' b-")
    >>> sn = s.flat.notesAndRests
    >>> search.translateStreamToStringNoRhythm(sn)
    '<>@)QF'
    '''
    b = ''
    for n in inputStream:
        b += translateNoteToByte(n)
    return b
  
  
def translateStreamToStringOnlyRhythm(inputStream):
    '''
    takes a stream of notesAndRests only and returns
    a string for searching on.
    
    
    >>> s = converter.parse("tinynotation: 3/4 c4 d8 e16 FF8. a'8 b-2.")
    >>> sn = s.flat.notesAndRests
    >>> streamString = search.translateStreamToStringOnlyRhythm(sn)
    >>> print(streamString)
    PF<KF_
    >>> len(streamString)  
    6
    '''
    b = ''
    for n in inputStream:
        b += translateDurationToBytes(n)
    return b

  
def translateNoteToByte(n):
    '''
    takes a note.Note object and translates it to a single byte representation.

    currently returns the chr() for the note's midi number. or chr(127) for rests
    
    
    >>> n = note.Note("C4")
    >>> b = search.translateNoteToByte(n)
    >>> b
    '<'
    >>> ord(b) 
    60
    >>> ord(b) == n.pitch.midi
    True

    Chords are currently just searched on the first note (or treated as a rest if none)
    '''
    if n.isRest:
        return chr(127)
    elif n.isChord:
        if len(n.pitches) > 0:
            return chr(n.pitches[0].midi)
        else:
            return chr(127)
    else:
        return chr(n.pitch.midi)

def translateNoteWithDurationToBytes(n, includeTieByte=True):
    '''
    takes a note.Note object and translates it to a three-byte representation.
    
    currently returns the chr() for the note's midi number. or chr(127) for rests
    followed by the log of the quarter length (fitted to 1-127, see formula below)
    followed by 's', 'c', or 'e' if includeTieByte is True and there is a tie

    
    >>> n = note.Note("C4")
    >>> n.duration.quarterLength = 3  # dotted half
    >>> trans = search.translateNoteWithDurationToBytes(n)
    >>> trans
    '<_'
    >>> (2**(ord(trans[1])/10.0))/256  # approximately 3
    2.828...
    
    >>> n.tie = tie.Tie('stop')
    >>> trans = search.translateNoteWithDurationToBytes(n)
    >>> trans
    '<_e'

    >>> trans = search.translateNoteWithDurationToBytes(n, includeTieByte=False)
    >>> trans
    '<_'

    
    '''
    firstByte = translateNoteToByte(n)
    duration1to127 = int(math.log(n.duration.quarterLength * 256, 2)*10)
    if duration1to127 >= 127:
        duration1to127 = 127
    elif duration1to127 == 0:
        duration1to127 = 1
    secondByte = chr(duration1to127)
    
    thirdByte = translateNoteTieToByte(n)
    if includeTieByte is True:
        return firstByte + secondByte + thirdByte
    else:
        return firstByte + secondByte

def translateNoteTieToByte(n):
    '''
    takes a note.Note object and returns a one-byte representation
    of its tie status.
    's' if start tie, 'e' if stop tie, 'c' if continue tie, and '' if no tie
    
    
    >>> n = note.Note("E")
    >>> search.translateNoteTieToByte(n)
    ''
    
    >>> n.tie = tie.Tie("start")
    >>> search.translateNoteTieToByte(n)
    's'
    
    >>> n.tie.type = 'continue'
    >>> search.translateNoteTieToByte(n)
    'c'
    
    >>> n.tie.type = 'stop'
    >>> search.translateNoteTieToByte(n)
    'e'
    '''
    if n.tie is None:
        return ''
    elif n.tie.type == 'start':
        return 's'
    elif n.tie.type == 'continue':
        return 'c'
    elif n.tie.type == 'stop':
        return 'e'
    else:
        return ''

def translateDurationToBytes(n):
    '''
    takes a note.Note object and translates it to a two-byte representation

    currently returns the chr() for the note's midi number. or chr(127) for rests
    followed by the log of the quarter length (fitted to 1-127, see formula below)

    
    >>> n = note.Note("C4")
    >>> n.duration.quarterLength = 3  # dotted half
    >>> trans = search.translateDurationToBytes(n)
    >>> trans
    '_'
    >>> (2**(ord(trans[0])/10.0))/256  # approximately 3
    2.828...
    
    '''
    duration1to127 = int(math.log(n.duration.quarterLength * 256, 2)*10)
    if duration1to127 >= 127:
        duration1to127 = 127
    elif duration1to127 == 0:
        duration1to127 = 1
    secondByte = chr(duration1to127)
    return secondByte
    

#--------------------

def mostCommonMeasureRythms(streamIn, transposeDiatonic = False):
    '''
    returns a sorted list of dictionaries 
    of the most common rhythms in a stream where
    each dictionary contains:
    
    number: the number of times a rhythm appears
    rhythm: the rhythm found (with the pitches of the first instance of the rhythm transposed to C5)
    measures: a list of measures containing the rhythm
    rhythmString: a string representation of the rhythm (see translateStreamToStringOnlyRhythm)

    
    >>> bach = corpus.parse('bwv1.6')
    >>> sortedRhythms = search.mostCommonMeasureRythms(bach)
    >>> for dict in sortedRhythms[0:3]:
    ...     print('no: %d %s %s' % (dict['number'], 'rhythmString:', dict['rhythmString']))
    ...     print('  bars: %r' % ([(m.number, str(m.getContextByClass('Part').id)) for m in dict['measures']]))
    ...     dict['rhythm'].show('text')
    ...     print('-----')
    no: 34 rhythmString: PPPP
      bars: [(1, 'Soprano'), (1, 'Alto'), (1, 'Tenor'), (1, 'Bass'), (2, 'Soprano'), ..., (19, 'Soprano')]
    {0.0} <music21.note.Note C>
    {1.0} <music21.note.Note A>
    {2.0} <music21.note.Note F>
    {3.0} <music21.note.Note C>
    -----
    no: 7 rhythmString: ZZ
      bars: [(13, 'Soprano'), (13, 'Alto'), ..., (14, 'Bass')]
    {0.0} <music21.note.Note C>
    {2.0} <music21.note.Note A>
    -----
    no: 6 rhythmString: ZPP
      bars: [(6, 'Soprano'), (6, 'Bass'), ..., (18, 'Tenor')]
    {0.0} <music21.note.Note C>
    {2.0} <music21.note.Note B->
    {3.0} <music21.note.Note B->
    -----
    '''
    returnDicts = []
    for thisMeasure in streamIn.semiFlat.getElementsByClass('Measure'):
        rhythmString = translateStreamToStringOnlyRhythm(thisMeasure.notesAndRests)
        rhythmFound = False
        for entry in returnDicts:
            if entry['rhythmString'] == rhythmString:
                rhythmFound = True
                entry['number'] += 1
                entry['measures'].append(thisMeasure)
                break
        if rhythmFound == False:
            newDict = {}
            newDict['number'] = 1
            newDict['rhythmString'] = rhythmString
            measureNotes = thisMeasure.notes
            foundNote = False
            for i in range(len(measureNotes)):
                if 'Note' in measureNotes[i].classes:
                    distanceToTranspose = 72 - measureNotes[0].pitch.ps
                    foundNote = True
                    break
            if foundNote == True:
                thisMeasureCopy = copy.deepcopy(thisMeasure)
                for n in thisMeasureCopy.notes:
                    # TODO: Transpose Diatonic
                    n.transpose(distanceToTranspose, inPlace=True)
                newDict['rhythm'] = thisMeasureCopy
            else:
                newDict['rhythm'] = thisMeasure
            newDict['measures'] = [thisMeasure]
            returnDicts.append(newDict)
    
    sortedDicts = sorted(returnDicts, key=lambda k: k['number'], reverse=True)
    return sortedDicts

class SearchException(exceptions21.Music21Exception):
    pass


class Test(unittest.TestCase):

    def testCopyAndDeepcopy(self):
        '''Test copying all objects defined in this module
        '''
        import sys, types
        for part in sys.modules[self.__module__].__dict__:
            match = False
            for skip in ['_', '__', 'Test', 'Exception']:
                if part.startswith(skip) or part.endswith(skip):
                    match = True
            if match:
                continue
            obj = getattr(sys.modules[self.__module__], part)
            if callable(obj) and not isinstance(obj, types.FunctionType):
                i = copy.copy(obj)
                j = copy.deepcopy(obj)

    

#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = []


if __name__ == "__main__":
    import music21
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof
