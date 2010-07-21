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

def midiEventsToNote(eventList, ticksPerQuarter=None, input=None):
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
    >>> me1.velocity = 0

    >>> n = midiEventsToNote([dt1, me1, dt2, me1])
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


def noteToMidiEvents(input):
    '''Translate Note to four MIDI events.

    >>> from music21 import *
    >>> n1 = note.Note()
    >>> eventList = noteToMidiEvents(n1)
    >>> eventList
    [<MidiEvent DeltaTime, t=0, track=None, channel=None>, <MidiEvent NOTE_ON, t=None, track=None, channel=1, pitch=60, velocity=90>, <MidiEvent DeltaTime, t=1024, track=None, channel=None>, <MidiEvent NOTE_OFF, t=None, track=None, channel=1, pitch=60, velocity=0>]
    >>> n1.duration.quarterLength = 2.5
    >>> eventList = noteToMidiEvents(n1)
    >>> eventList
    [<MidiEvent DeltaTime, t=0, track=None, channel=None>, <MidiEvent NOTE_ON, t=None, track=None, channel=1, pitch=60, velocity=90>, <MidiEvent DeltaTime, t=2560, track=None, channel=None>, <MidiEvent NOTE_OFF, t=None, track=None, channel=1, pitch=60, velocity=0>]
    '''

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



def noteToMidiFile(input): 
    '''
    >>> from music21 import note
    >>> n1 = note.Note()
    >>> n1.quarterLength = 6
    >>> mf = noteToMidiFile(n1)
    >>> mf.tracks[0].events
    [<MidiEvent DeltaTime, t=0, track=1, channel=None>, <MidiEvent SEQUENCE_TRACK_NAME, t=0, track=1, channel=None, data=''>, <MidiEvent DeltaTime, t=0, track=1, channel=None>, <MidiEvent NOTE_ON, t=None, track=1, channel=1, pitch=60, velocity=90>, <MidiEvent DeltaTime, t=6144, track=1, channel=None>, <MidiEvent NOTE_OFF, t=None, track=1, channel=1, pitch=60, velocity=0>, <MidiEvent DeltaTime, t=0, track=1, channel=None>, <MidiEvent END_OF_TRACK, t=None, track=1, channel=1, data=''>]
    '''
    n = input
    mt = midiModule.MidiTrack(1)
    mt.events += midiModule.getStartEvents(mt)
    mt.events += noteToMidiEvents(n)
    mt.events += midiModule.getEndEvents(mt)

    # set all events to have this track
    mt.updateEvents()

    mf = midiModule.MidiFile()
    mf.tracks = [mt]
    mf.ticksPerQuarterNote = defaults.ticksPerQuarter
    return mf




#-------------------------------------------------------------------------------
# Chords

def midiEventsToChord(eventList, ticksPerQuarter=None, input=None):
    '''

    >>> from music21 import *
    >>> mt = midi.MidiTrack(1)

    >>> dt1 = midi.DeltaTime(mt)
    >>> dt1.time = 0

    >>> me1 = midi.MidiEvent(mt)
    >>> me1.type = "NOTE_ON"
    >>> me1.pitch = 45
    >>> me1.velocity = 94

    >>> dt2 = midi.DeltaTime(mt)
    >>> dt2.time = 0

    >>> me2 = midi.MidiEvent(mt)
    >>> me2.type = "NOTE_ON"
    >>> me2.pitch = 46
    >>> me2.velocity = 94


    >>> dt3 = midi.DeltaTime(mt)
    >>> dt3.time = 2048

    >>> me3 = midi.MidiEvent(mt)
    >>> me3.type = "NOTE_OFF"
    >>> me3.pitch = 45
    >>> me3.velocity = 0

    >>> dt4 = midi.DeltaTime(mt)
    >>> dt4.time = 0

    >>> me4 = midi.MidiEvent(mt)
    >>> me4.type = "NOTE_OFF"
    >>> me4.pitch = 46
    >>> me4.velocity = 0

    >>> c = midiEventsToChord([dt1, me1, dt2, me2, dt3, me3, dt4, me4])
    >>> c
    <music21.chord.Chord A2 A#2>
    >>> c.duration.quarterLength
    2.0
    '''
    if input == None:
        from music21 import chord
        c = chord.Chord()
    else:
        c = input

    if ticksPerQuarter == None:
        ticksPerQuarter = defaults.ticksPerQuarter

    pitches = []

    # this is a format provided by the Stream conversion of 
    # midi events; it pre groups events for a chord together in nested pairs
    # of abs start time and the event object
    if isinstance(eventList, list) and isinstance(eventList[0], list):
        # pairs of pairs
        for onPair, offPair in eventList:
            tOn, eOn = onPair
            tOff, eOff = offPair

            p = pitch.Pitch()
            p.midi = eOn.pitch
            pitches.append(p)
    # assume it is  a flat list        
    else:
        onEvents = eventList[:(len(eventList) / 2)]
        offEvents = eventList[(len(eventList) / 2):]
        # first is always delta time
        tOn = onEvents[0].time
        tOff = offEvents[0].time

        # create pitches for the odd on Events:
        for i in range(1, len(onEvents), 2):
            p = pitch.Pitch()
            p.midi = onEvents[i].pitch
            pitches.append(p)

    c.pitches = pitches
    # can simply use last-assigned pair of tOff, tOn
    c.duration.midi = (tOff - tOn), ticksPerQuarter
    return c



def chordToMidiEvents(input):
    '''
    >>> from music21 import *
    >>> c = chord.Chord(['c3','g#4', 'b5'])
    >>> eventList = chordToMidiEvents(c)
    >>> eventList
    [<MidiEvent DeltaTime, t=0, track=None, channel=None>, <MidiEvent NOTE_ON, t=None, track=None, channel=1, pitch=48, velocity=90>, <MidiEvent DeltaTime, t=0, track=None, channel=None>, <MidiEvent NOTE_ON, t=None, track=None, channel=1, pitch=68, velocity=90>, <MidiEvent DeltaTime, t=0, track=None, channel=None>, <MidiEvent NOTE_ON, t=None, track=None, channel=1, pitch=83, velocity=90>, <MidiEvent DeltaTime, t=1024, track=None, channel=None>, <MidiEvent NOTE_OFF, t=None, track=None, channel=1, pitch=48, velocity=0>, <MidiEvent DeltaTime, t=0, track=None, channel=None>, <MidiEvent NOTE_OFF, t=None, track=None, channel=1, pitch=68, velocity=0>, <MidiEvent DeltaTime, t=0, track=None, channel=None>, <MidiEvent NOTE_OFF, t=None, track=None, channel=1, pitch=83, velocity=0>]

    '''
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



def chordToMidiFile(input): 
    # this can be consolidated with noteToMidiFile
    c = input

    mt = midiModule.MidiTrack(1)
    mt.events += midiModule.getStartEvents(mt)
    mt.events += chordToMidiEvents(c)
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

