#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         midi.translate.py
# Purpose:      Translate MIDI and music21 objects
#
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------



import unittest

import music21
from music21 import midi as midiModule
from music21 import defaults
from music21 import pitch



#-------------------------------------------------------------------------------
class TranslateException(Exception):
    pass



#-------------------------------------------------------------------------------
# Notes

def fromMidiEventsToNote(eventList, ticksPerQuarter=None, input=None):
    '''Convert from a list of MIDI message to a music21 note

    The `input` parameter can be a Note or None; in the case of None, a Note object is created. 

    >>> from music21 import *

    >>> mt = midi.MidiTrack(1)
    >>> dt1 = midi.DeltaTime(mt)
    >>> dt1.time = 1024

    >>> me1 = midi.MidiEvent(mt)
    >>> me1.type = "NOTE_ON"
    >>> me1.pitch = 45
    >>> me1.velocity = 94

    >>> dt2 = midi.DeltaTime(mt)
    >>> dt2.time = 2048

    >>> me1 = midi.MidiEvent(mt)
    >>> me1.type = "NOTE_ON"
    >>> me1.pitch = 45
    >>> me1.velocity = 94

    >>> n = fromMidiEventsToNote([dt1, me1, dt2, me1])
    >>> n.pitch
    A2
    >>> n.duration.quarterLength
    1.0
    '''
    if input == None:
        from music21 import note
        n = note.Note()
    else:
        n = input

    if ticksPerQuarter == None:
        ticksPerQuarter = defaults.ticksPerQuarter

    # pre sorted from a stream
    if len(eventList) == 2:
        tOn, eOn = eventList[0]
        tOff, eOff = eventList[1]

    # a representation closer to stream
    elif len(eventList) == 4:
        # delta times are first and third
        dur = eventList[2].time - eventList[0].time
        # shift to start at zero; only care about duration here
        tOn, eOn = 0, eventList[1]
        tOff, eOff = dur, eventList[3]
    else:
        raise TranslateException('cannot handle MIDI event list in the form: %r', eventList)

    n.duration.midi = (tOff - tOn), ticksPerQuarter
    n.pitch.midi = eOn.pitch


    return n


def fromNoteToMidiEvents(input):

    n = input

    mt = None # use a midi track set to None
    eventList = []
    dt = midiModule.DeltaTime(mt)
    dt.time = 0 # set to zero; will be shifted later as necessary
    # add to track events
    eventList.append(dt)

    me = midiModule.MidiEvent(mt)
    me.type = "NOTE_ON"
    me.channel = 1
    me.time = None # not required
    me.pitch = n.midi
    me.velocity = 90 # default, can change later
    eventList.append(me)

    # add note off / velocity zero message
    dt = midiModule.DeltaTime(mt)
    dt.time = n.duration.midi
    # add to track events
    eventList.append(dt)

    me = midiModule.MidiEvent(mt)
    me.type = "NOTE_OFF"
    me.channel = 1
    me.time = None #d
    me.pitch = n.midi
    me.velocity = 0 # must be zero
    eventList.append(me)

    return eventList 



def fromNoteToMidiFile(input): 
    n = input

    mt = midiModule.MidiTrack(1)
    mt.events += midiModule.getStartEvents(mt)
    mt.events += fromNoteToMidiEvents(n)
    mt.events += midiModule.getEndEvents(mt)

    # set all events to have this track
    mt.updateEvents()

    mf = midiModule.MidiFile()
    mf.tracks = [mt]
    mf.ticksPerQuarterNote = defaults.ticksPerQuarter
    return mf




#-------------------------------------------------------------------------------
# Chords

def fromMidiEventsToChord(eventList, ticksPerQuarter=None, input=None):

    if input == None:
        from music21 import chord
        c = chord.Chord()
    else:
        c = input

    if isinstance(eventList, list) and isinstance(eventList[0], list):
        pitches = []
        # pairs of pairs
        for onPair, offPair in eventList:
            tOn, eOn = onPair
            tOff, eOff = offPair

            p = pitch.Pitch()
            p.midi = eOn.pitch
            pitches.append(p)
            
    c.pitches = pitches
    # can simply use last-assigned pair of tOff, tOn
    c.duration.midi = (tOff - tOn), ticksPerQuarter
    return c



def fromChordToMidiEvents(input):
    mt = None # midi track 
    eventList = []
    c = input

    for i in range(len(c.pitches)):
        pitchObj = c.pitches[i]

        dt = midiModule.DeltaTime(mt)
        # for a chord, only the first delta time should have the offset
        # here, all are zero
        dt.time = 0 # set to zero; will be shifted later as necessary
        # add to track events
        eventList.append(dt)

        me = midiModule.MidiEvent(mt)
        me.type = "NOTE_ON"
        me.channel = 1
        me.time = None # not required
        me.pitch = pitchObj.midi
        me.velocity = 90 # default, can change later
        eventList.append(me)

    # must create each note on in chord before each note on
    for i in range(len(c.pitches)):
        pitchObj = c.pitches[i]

        # add note off / velocity zero message
        dt = midiModule.DeltaTime(mt)
        # for a chord, only the first delta time should have the dur
        if i == 0:
            dt.time = c.duration.midi
        else:
            dt.time = 0
        eventList.append(dt)

        me = midiModule.MidiEvent(mt)
        me.type = "NOTE_OFF"
        me.channel = 1
        me.time = None #d
        me.pitch = pitchObj.midi
        me.velocity = 0 # must be zero
        eventList.append(me)
    return eventList 



def fromChordToMidiFile(input): 
    # this can be consolidated with fromNoteToMidiFile
    c = input

    mt = midiModule.MidiTrack(1)
    mt.events += midiModule.getStartEvents(mt)
    mt.events += fromChordToMidiEvents(c)
    mt.events += midiModule.getEndEvents(mt)

    # set all events to have this track
    mt.updateEvents()

    mf = midiModule.MidiFile()
    mf.tracks = [mt]
    mf.ticksPerQuarterNote = defaults.ticksPerQuarter
    return mf










#-------------------------------------------------------------------------------
class Test(unittest.TestCase):
    
    def runTest(self):
        pass

    def testNote(self):

        from music21 import note
        n = note.Note()
        eventList = n.midiEvents
        self.assertEqual(len(eventList), 4)

        self.assertEqual(isinstance(eventList[0], midiModule.DeltaTime), True)
        self.assertEqual(isinstance(eventList[2], midiModule.DeltaTime), True)



if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)
    elif len(sys.argv) > 1:
        a = Test()
        a.testPitchEquality()

