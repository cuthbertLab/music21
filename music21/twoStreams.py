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

import interval
from duration import Duration, Tuplet
from stream import Stream
from note import Rest
import math
import copy

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


