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
from music21.duration import Duration, Tuplet
from music21.stream import Stream
from music21.note import Rest

class TwoStreamComparer(object):
    def __init__(self, stream1 = Stream(), stream2 = Stream()):
        self.stream1 = stream1
        self.stream2 = stream2

    def attackedTogether(self):
        '''returns an ordered list of pairs of notes that are attacked
        at the same time'''
        sameAttack = []
        for i in range(len(self.stream1.noteTimeInfo)):
            for j in range(len(self.stream2.noteTimeInfo)):
                if (self.stream1.noteTimeInfo[i]['start'] == self.stream2.noteTimeInfo[j]['start']):
                    entry = [self.stream1.notes[i],self.stream2.notes[j]]
                    sameAttack.append(entry)
        return sameAttack
    
    def playingWhenSounded(self, note1, includeRests = True):
        '''given a note in one stream, returns the note in the other stream
        that is sounding while the given note starts. Will return a note
        that starts at the same time as the given note, if applicable.'''

        if note1 in self.stream1:
            startTime = self.stream1.getNoteStartEndTime(note1)[0]
            otherNote = self.stream2.getNoteAtTime(startTime)
            if (otherNote is None):
                print self.stream2 + " hi "
                print self.stream2.duration.quarterLength
                print self.stream2.lily
                raise Exception("Could not find a note at that time %f, note was %s" % (startTime, str(note1.name)))
        elif note1 in self.stream2:
            startTime = self.stream2.getNoteStartEndTime(note1)[0]
            otherNote = self.stream1.getNoteAtTime(startTime)
            if (otherNote is None):
                raise Exception("Could not find a note at that time")
            
        else: 
            raise Exception('note object is not found in either stream')
        
        # Check if note found is a rest; act according to includeRests variable
        if isinstance(otherNote, Rest):
            if includeRests: soundingNote = otherNote
            else: soundingNote = None

        else: soundingNote = otherNote
                
        return soundingNote 

    def allPlayingWhileSounded(self, note, includeRests = True):
        '''given a note in one stream, returns an ordered list of notes that
        sound while the given note is sounding; includes beginning and end notes
        that may overlap.'''
        sounding = []
        # add the first note to the final list to be returned
        sounding.append(self.playingWhenSounded(note, includeRests))
        
        if note in self.stream1:
            noteTimes = self.stream1.getNoteStartEndTime(note)
            startTime = noteTimes[0]
            endTime = noteTimes[1]
            for i in range(len(self.stream2.notes)):
                otherNote = self.stream2.notes[i]
                otherStart = self.stream2.noteTimeInfo[i]['start']
                if (otherStart>startTime and otherStart<endTime):
                    if isinstance(otherNote, Rest):
                        if includeRests: sounding.append(otherNote)
                    else: sounding.append(otherNote)

        elif note in self.stream2:
            noteTimes = self.stream2.getNoteStartEndTime(note)
            startTime = noteTimes[0]
            endTime = noteTimes[1]
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
            noteTimes = self.stream1.getNoteStartEndTime(note)
            startTime = noteTimes[0]
            endTime = noteTimes[1]
            for i in range(len(self.stream2.notes)):
                otherNote = self.stream2.notes[i]
                otherTimes = self.stream2.getNoteStartEndTime(otherNote)
                otherStart = otherTimes[0]
                otherEnd = otherTimes[1]
                if (otherStart > startTime and otherStart < endTime and otherEnd <= endTime):
                    if isinstance(otherNote, Rest):
                        if includeRests: sounding.append(otherNote)
                    else: sounding.append(otherNote)

        elif note in self.stream2:
            noteTimes = self.stream2.getNoteStartEndTime(note)
            startTime = noteTimes[0]
            endTime = noteTimes[1]
            for i in range(len(self.stream1.notes)):
                otherNote = self.stream1.notes[i]
                otherTimes = self.stream2.getNoteStartEndTime(otherNote)
                otherStart = otherTimes[0]
                otherEnd = otherTimes[1]
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
            noteTimes = self.stream1.getNoteStartEndTime(note)
            startTime = noteTimes[0]
            endTime = noteTimes[1]
            for i in range(len(self.stream2.notes)):
                otherNote = self.stream2.notes[i]
                otherTimes = self.stream2.getNoteStartEndTime(otherNote)
                otherStart = otherTimes[0]
                otherEnd = otherTimes[1]
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
            noteTimes = self.stream2.getNoteStartEndTime(note)
            startTime = noteTimes[0]
            endTime = noteTimes[1]
            for i in range(len(self.stream1.notes)):
                otherNote = self.stream1.notes[i]
                otherTimes = self.stream2.getNoteStartEndTime(otherNote)
                otherStart = otherTimes[0]
                otherEnd = otherTimes[1]
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
    stream1.addNext([n11,n12,n13,n14])
    stream2 = Stream()
    stream2.addNext([n21,n22,n23,n24])

    twoStream1 = TwoStreamComparer(stream1, stream2)
    attackedTogether = twoStream1.attackedTogether()
    assert len(attackedTogether) == 3  # nx1, nx2, nx4
    assert attackedTogether[1][1] == n22
    
    playingWhenSounded = twoStream1.playingWhenSounded(n23)
    assert playingWhenSounded == n12
    
    allPlayingWhileSounded = twoStream1.allPlayingWhileSounded(n14)
    assert allPlayingWhileSounded == [n24]
    
    exclusivePlayingWhileSounded = \
         twoStream1.exclusivePlayingWhileSounded(n12)
    assert exclusivePlayingWhileSounded == [n22]
    
    trimPlayingWhileSounded = \
         twoStream1.trimPlayingWhileSounded(n12)
    assert trimPlayingWhileSounded[0] == n22
    assert trimPlayingWhileSounded[1].duration.quarterLength == 3.5
    
    #ballataObj = BallataSheet()
    #randomPiece = ballataObj.makeWork(random.randint(231, 312) # landini a-l
    #trecentoStreams =  randomPiece.incipitStreams()
    
    ### test your objects on these two streams
    
if __name__ == "__main__":
    music21.mainTest(Test)
