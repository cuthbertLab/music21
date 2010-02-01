#-------------------------------------------------------------------------------
# Name:         twoStreams.py
# Purpose:      music21 classes for dealing with combining two streams
#
# Authors:      Michael Scott Cuthbert
#               Jackie Rogoff
#               Amy Hailes
#
# Copyright:    (c) 2009 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

'''
Much of this module might be better moved into Stream.  Nonetheless, it
will be useful for now to have this module while counterpoint and trecento
are being completely converted to the new system
'''

import copy
import math
import unittest, doctest

import music21
from music21 import interval
from music21 import note
from music21.duration import Duration, Tuplet
from music21.stream import Stream
from music21.note import Rest

def attackedTogether(stream1, stream2):
    '''
    returns an ordered list of offsets where elements are started (attacked) in both
    stream1 and stream2.

    >>> st1 = Stream()
    >>> st2 = Stream()
    >>> n11 = note.Note()
    >>> n12 = note.Note()
    >>> n21 = note.Note()
    >>> n22 = note.Note()
    
    >>> st1.insert(10, n11)
    >>> st2.insert(10, n21)
    
    >>> st1.insert(20, n12)
    >>> st2.insert(20.5, n22)
    
    >>> simultaneous = attackedTogether(st1, st2)
    >>> simultaneous
    [10.0]
    '''
    stream1Offsets = stream1.groupElementsByOffset()
    stream2Offsets = stream2.groupElementsByOffset()
    
    returnKey = {}
    
    for thisList in stream1Offsets:
        thisOffset = thisList[0].getOffsetBySite(stream1)
        returnKey[thisOffset] = 1
    
    for thatList in stream2Offsets:
        thatOffset = thatList[0].getOffsetBySite(stream2)
        if thatOffset in returnKey:
            returnKey[thatOffset] += 1
    
    returnList = []
    for foundOffset in sorted(returnKey):
        if returnKey[foundOffset] >= 2:
            returnList.append(foundOffset)
    
    return returnList

def attachIntervals(srcStream, cmpStream):
    '''For each element in srcStream, creates an interval object in the element's
    editorial that is the interval between it and the element in cmpStream that
    is sounding at the moment the element in srcStream is attacked.'''

    srcNotes = srcStream.notes
    for thisNote in srcNotes:
        simultEls = cmpStream.getElementsByOffset(thisNote.offset, mustBeginInSpan = False, includeEndBoundary = False)
        simultNote = None
        if len(simultEls) > 0:
            simultNote = (simultEls.notes)[0]

        if simultNote is not None and thisNote.isRest == False:
            interval1 = interval.generateInterval(thisNote, simultNote)
            thisNote.editorial.harmonicInterval = interval1

def mutualAttachIntervals(stream1, stream2):
    '''
    runs attachIntervals(stream1, stream2) then attachIntervals(stream2, stream1)
    '''
    attachIntervals(stream1, stream2)
    attachIntervals(stream2, stream1)


def playingWhenSounded(el, otherStream, elStream = None):
    '''
        given an element in one stream, returns a single element in the other stream
        that is sounding while the given element starts. Will return a note
        that starts at the same time as the given note, if applicable.
        
        if there are multiple elements sounding at the moment it is attacked, it 
        returns the first element of the same class as this element, if any, otherwise
        just the first element.  Use allPlayingWhenSounded for other usages

        returns None if no elements fit the bill.

        The optional elStream is the stream in which el is found. If provided, el's offset
        in that stream is used.  Otherwise, the current offset in el is used.
        '''

    if elStream is not None: # bit of safety
        elOffset = el.getOffsetBySite(elStream)
    else:
        elOffset = el.offset
    
    otherElements = otherStream.getElementsByOffset(elOffset)
    if len(otherElements) == 0:
        return None
    elif len(otherElements) == 1:
        return otherElements[0]
    else:
        for thisEl in otherElements:
            if isinstance(thisEl, el.__class__):
                return thisEl
        return otherElements[0]


def allPlayingWhenSounded(self, el, otherStream, requireClass = False, elStream = None):
    '''
    returns a Stream of elements in otherStream that sound at the same time as el.
    The offset of this Stream is set to el, while the offset of elements within the Stream are
    relative to their position with respect to the start of el.  Thus, a note that is sounding
    already when el begins would have a negative offset.  The duration of otherStream is forced
    to be the length of el -- thus a note sustained after el ends may have a release time beyond
    that of the duration of the Stream.
    
    takes a parameter requireClass.  If True then only elements of the same class as el are added 
    to the Stream.  If a list, it is used like classList in Stream to provide a list of classes 
    that the el must be a part of.
    
    TODO: code requireClass
    
    as above, elStream is an optional Stream to look up el's offset in.

    always returns a Stream, but might be an empty Stream
    '''
    if requireClass is not False:
        raise Exception("requireClass is not implemented")

    if elStream is not None: # bit of safety
        elOffset = el.getOffsetBySite(elStream)
    else:
        elOffset = el.offset
    
    otherElements = otherStream.getElementsByOffset(elOffset, elOffset + el.quarterLength, mustBeginInSpan = False)

    otherElements.offset = elOffset
    otherElements.quarterLength = el.quarterLength
    for thisEl in otherElements:
        thisEl.offset = thisEl.offset - elOffset
    
    return otherElements


class TwoStreamComparer(object):

    def allPlayingWhileSounded(self, note, includeRests = True):
        '''given a note in one stream, returns an ordered list of notes that
        sound while the given note is sounding; includes beginning and end notes
        that may overlap.'''
        sounding = []
        # add the first note to the final list to be returned
        sounding.append(self.playingWhenSounded(note, includeRests))
        
        if note in self.stream1:
            startTime = note.getOffsetBySite(self.stream1)
            endTime = startTime + note.duration.quarterLength
            for i in range(len(self.stream2.notes)):
                otherNote = self.stream2.notes[i]
                otherStart = self.stream2.noteTimeInfo[i]['start']
                if (otherStart>startTime and otherStart<endTime):
                    if isinstance(otherNote, Rest):
                        if includeRests: sounding.append(otherNote)
                    else: sounding.append(otherNote)

        elif note in self.stream2:
            startTime = note.getOffsetBySite(self.stream2)
            endTime = startTime + note.duration.quarterLength
            for i in range(len(self.stream1.notes)):
                otherNote = self.stream1.notes[i]
                otherStart = self.stream1.noteTimeInfo[i]['start']
                if (otherStart>startTime and otherStart<endTime):
                    if isinstance(otherNote, Rest):
                        if includeRests: sounding.append(otherNote)
                    else: sounding.append(otherNote)
        
        else: raise('note object is not found in either stream')

        return sounding

    def exclusivePlayingWhileSounded(self, note, includeRests = True):
        '''given a note in one stream, returns an ordered list of notes that
        sound while the given note is sounding; excludes last note if it
        continues beyond the duration of the given note.'''
        sounding = []
        # add the first note to the final list to be returned
        sounding.append(self.playingWhenSounded(note, includeRests))
        
        if note in self.stream1:
            startTime = note.getOffsetBySite(self.stream1)
            endTime = startTime + note.duration.quarterLength
            for i in range(len(self.stream2.notes)):
                otherNote = self.stream2.notes[i]
                otherStart = otherNote.getOffsetBySite(self.stream2)
                otherEnd = otherStart + otherNote.duration.quarterLength
                if (otherStart > startTime and otherStart < endTime and otherEnd <= endTime):
                    if isinstance(otherNote, Rest):
                        if includeRests: sounding.append(otherNote)
                    else: sounding.append(otherNote)

        elif note in self.stream2:
            startTime = note.getOffsetBySite(self.stream2)
            endTime = startTime + note.duration.quarterLength
            for i in range(len(self.stream1.notes)):
                otherNote = self.stream1.notes[i]
                otherStart = otherNote.getOffsetBySite(self.stream1)
                otherEnd = otherStart + otherNote.duration.quarterLength
                if (otherStart > startTime and otherStart < endTime and otherEnd <= endTime):
                    if isinstance(otherNote, Rest):
                        if includeRests: sounding.append(otherNote)
                    else: sounding.append(otherNote)
        
        else: raise('note object is not found in either stream')

        return sounding
    
    def trimPlayingWhileSounded(self, note, includeRests = True):
        '''given a note in one stream, returns an ordered list of notes that
        sound while the given note is sounding; clips last note to end at same
        time as given note.'''
        sounding = []
        # add the first note to the final list to be returned
        sounding.append(self.playingWhenSounded(note, includeRests))
        
        if note in self.stream1:
            startTime = note.getOffsetBySite(self.stream1)
            endTime = startTime + note.duration.quarterLength
            for i in range(len(self.stream2.notes)):
                otherNote = self.stream2.notes[i]
                otherStart = otherNote.getOffsetBySite(self.stream2)
                otherEnd = otherStart + otherNote.duration.quarterLength
                if (otherStart > startTime and otherStart < endTime and otherEnd <= endTime):
                    if isinstance(otherNote, Rest):
                        if includeRests: sounding.append(otherNote)
                    else: sounding.append(otherNote)

                elif (otherStart > startTime and otherStart < endTime and otherEnd > endTime):
                    newDuration = endTime - otherStart
                    if isinstance(otherNote, Rest):
                        if includeRests:
                            newNote = otherNote.copy()
                            newNote.duration = Duration(newDuration)
                            sounding.append(newNote)
                    else:
                        newNote = otherNote.copy()
                        newNote.duration = Duration(newDuration)
                        sounding.append(newNote)

        elif note in self.stream2:
            startTime = note.getOffsetBySite(self.stream2)
            endTime = startTime + note.duration.quarterLength
            for i in range(len(self.stream1.notes)):
                otherNote = self.stream1.notes[i]
                otherStart = otherNote.getOffsetBySite(self.stream1)
                otherEnd = otherStart + otherNote.duration.quarterLength
                if (otherStart > startTime and otherStart < endTime and otherEnd <= endTime):
                    if isinstance(otherNote, Rest):
                        if includeRests: sounding.append(otherNote)
                    else: sounding.append(otherNote)

                elif (otherStart > startTime and otherStart < endTime and otherEnd > endTime):
                    newDuration = endTime - otherStart
                    if isinstance(otherNote, Rest):
                        if includeRests:
                            newNote = copy.deepcopy(otherNote)
                            newNote.duration = Duration()
                            newNote.duration.setDurationFromQtrLength(newNote, newDuration)
                            sounding.append(newNote)
                    else:
                        newNote = copy.deepcopy(otherNote)
                        newNote.duration = Duration()
                        newNote.duration.setDurationFromQtrLength(newNote, newDuration)
                        sounding.append(newNote)
        
        else: raise('note object is not found in either stream')

        return sounding

    def intervalToOtherStreamWhenAttacked(self):
        '''For each note in stream1, creates an interval object in the note's
        editorial that is the interval between it and the note in stream2 that
        is playing while it sounds.'''
        for note1 in self.stream1:
            simultNote = self.playingWhenSounded(note1, False)
            if simultNote is not None and note1.isRest == False:
                interval1 = interval.generateInterval(note1, simultNote)
                note1.editorial.harmonicInterval = interval1
        for note2 in self.stream2:
            simultNote = self.playingWhenSounded(note2, False)
            if simultNote is not None and note2.isRest == False:
                interval2 = interval.generateInterval(note2, simultNote)
                note2.editorial.harmonicInterval = interval2

class Test(unittest.TestCase):

    def testMany(self):
        from music21.note import Note
    
        (n11,n12,n13,n14) = (Note(), Note(), Note(), Note())
        (n21,n22,n23,n24) = (Note(), Note(), Note(), Note())
        n11.step = "C"
        n12.step = "D"
        n13.step = "E"
        n14.step = "F"
        n21.step = "G"
        n22.step = "A"
        n23.step = "B"
        n24.step = "C"
        n24.octave = 5
        
        n11.duration.type = "half"
        n12.duration.type = "whole"
        n13.duration.type = "eighth"
        n14.duration.type = "half"
        
        n21.duration.type = "half"
        n22.duration.type = "eighth"
        n23.duration.type = "whole"
        n24.duration.type = "eighth"
        
        stream1 = Stream()
        stream1.append([n11,n12,n13,n14])
        stream2 = Stream()
        stream2.append([n21,n22,n23,n24])
    
        attackedT = attackedTogether(stream1, stream2) 
        self.assertEqual(len(attackedT), 3)  # nx1, nx2, nx4
        thisNote = stream2.getElementsByOffset(attackedT[1])[0]
        self.assertTrue(thisNote is n22)
        
    #    playingWhenSounded = twoStream1.playingWhenSounded(n23)
    #    assert playingWhenSounded == n12
    #    
    #    allPlayingWhileSounded = twoStream1.allPlayingWhileSounded(n14)
    #    assert allPlayingWhileSounded == [n24]
    #    
    #    exclusivePlayingWhileSounded = \
    #         twoStream1.exclusivePlayingWhileSounded(n12)
    #    assert exclusivePlayingWhileSounded == [n22]
    #    
    #    trimPlayingWhileSounded = \
    #         twoStream1.trimPlayingWhileSounded(n12)
    #    assert trimPlayingWhileSounded[0] == n22
    #    assert trimPlayingWhileSounded[1].duration.quarterLength == 3.5
        
        #ballataObj = BallataSheet()
        #randomPiece = ballataObj.makeWork(random.randint(231, 312) # landini a-l
        #trecentoStreams =  randomPiece.incipitStreams()
    
    ### test your objects on these two streams
    
if __name__ == "__main__":
    music21.mainTest(Test)