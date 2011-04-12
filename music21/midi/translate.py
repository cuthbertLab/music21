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
import math

import music21
from music21 import midi as midiModule
from music21 import defaults
from music21 import common

# modules that import this include stream.py, chord.py, note.py
# thus, cannot import these here

from music21 import environment
_MOD = "midi.translate.py"  
environLocal = environment.Environment(_MOD)




#-------------------------------------------------------------------------------
class TranslateException(Exception):
    pass


#-------------------------------------------------------------------------------
# Durations

def offsetToMidi(o):
    '''Convert an offset value to MIDI ticks.
    '''
    return int(round(o * defaults.ticksPerQuarter))


def durationToMidi(d):
    if d._quarterLengthNeedsUpdating:
        d.updateQuarterLength()
    return int(round(d.quarterLength * defaults.ticksPerQuarter))

def midiToDuration(ticks, ticksPerQuarter=None, inputM21=None):
    if inputM21 == None:
        from music21 import duration
        d = duration.Duration
    else:
        d = inputM21

    if ticksPerQuarter == None:
        ticksPerQuarter = defaults.ticksPerQuarter
    # given a value in ticks
    d._qtrLength = float(ticks) / ticksPerQuarter
    d._componentsNeedUpdating = True
    d._quarterLengthNeedsUpdating = False
    return d




#-------------------------------------------------------------------------------
# utility functions for getting commonly used event


def getStartEvents(mt=None, instrumentObj=None):
    '''Provide a list of events found at the beginning of a track.

    A MidiTrack reference can be provided via the `mt` parameter.
    '''

    # TODO: may need to provide channel as argument

    events = []
    if instrumentObj is None or instrumentObj.bestName() is None:
        partName = ''
    else:
        partName = instrumentObj.bestName()

    dt = midiModule.DeltaTime(mt)
    dt.time = 0
    events.append(dt)

    me = midiModule.MidiEvent(mt)
    me.type = "SEQUENCE_TRACK_NAME"
    me.time = 0 # always at zero?
    me.data = partName
    events.append(me)

    # must have channel information
#     if instrumentObj is not None and instrumentObj.midiProgram is not None:
#         sub = instrumentToMidiEvents(instrumentObj, includeDeltaTime=True)
#         for e in sub:
#             e.time = 0
#         events += sub

#         dt = DeltaTime(mt)
#         dt.time = 0
#         events.append(dt)
#     
#         environLocal.printDebug(['adding program change: %s' % partProgram])
#         me = MidiEvent(mt)
#         me.type = "PROGRAM_CHANGE"
#         me.time = 0 
#         me.channel = 1
#         me.data = partProgram
#         events.append(me)

    #environLocal.printDebug(['got start events', events])

    return events


def getEndEvents(mt=None, channelNumber=1):
    '''Provide a list of events found at the end of a track.
    '''
    events = []

    dt = midiModule.DeltaTime(mt)
    dt.time = 0
    events.append(dt)

    me = midiModule.MidiEvent(mt)
    me.type = "END_OF_TRACK"
    me.channel = channelNumber
    me.data = '' # must set data to empty string
    events.append(me)

    return events





#-------------------------------------------------------------------------------
# Notes

def midiEventsToNote(eventList, ticksPerQuarter=None, inputM21=None):
    '''Convert from a list of MIDI message to a music21 note

    The `inputM21` parameter can be a Note or None; in the case of None, a Note object is created. 

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
    if inputM21 == None:
        from music21 import note
        n = note.Note()
    else:
        n = inputM21

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


def noteToMidiEvents(inputM21, includeDeltaTime=True):
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
    n = inputM21

    mt = None # use a midi track set to None
    eventList = []

    if includeDeltaTime:
        dt = midiModule.DeltaTime(mt)
        dt.time = 0 # set to zero; will be shifted later as necessary
        # add to track events
        eventList.append(dt)

    me1 = midiModule.MidiEvent(mt)
    me1.type = "NOTE_ON"
    me1.channel = 1
    me1.time = None # not required
    me1.pitch = n.midi
    if not n.pitch.isTwelveTone():
        me1.centShift = n.pitch.getCentShiftFromMidi()
    me1.velocity = 90 # default, can change later
    eventList.append(me1)

    if includeDeltaTime:
        # add note off / velocity zero message
        dt = midiModule.DeltaTime(mt)
        dt.time = n.duration.midi
        # add to track events
        eventList.append(dt)

    me2 = midiModule.MidiEvent(mt)
    me2.type = "NOTE_OFF"
    me2.channel = 1
    me2.time = None #d
    me2.pitch = n.midi
    me2.pitchSpace = n.ps
    if not n.pitch.isTwelveTone():
        me2.centShift = n.pitch.getCentShiftFromMidi()

    me2.velocity = 0 # must be zero
    eventList.append(me2)

    # set correspondence
    me1.correspondingEvent = me2
    me2.correspondingEvent = me1

    return eventList 



def noteToMidiFile(inputM21): 
    '''
    >>> from music21 import note
    >>> n1 = note.Note()
    >>> n1.quarterLength = 6
    >>> mf = noteToMidiFile(n1)
    >>> mf.tracks[0].events
    [<MidiEvent DeltaTime, t=0, track=1, channel=None>, <MidiEvent SEQUENCE_TRACK_NAME, t=0, track=1, channel=None, data=''>, <MidiEvent DeltaTime, t=0, track=1, channel=None>, <MidiEvent NOTE_ON, t=None, track=1, channel=1, pitch=60, velocity=90>, <MidiEvent DeltaTime, t=6144, track=1, channel=None>, <MidiEvent NOTE_OFF, t=None, track=1, channel=1, pitch=60, velocity=0>, <MidiEvent DeltaTime, t=0, track=1, channel=None>, <MidiEvent END_OF_TRACK, t=None, track=1, channel=1, data=''>]
    '''
    n = inputM21
    mt = midiModule.MidiTrack(1)
    mt.events += getStartEvents(mt)
    mt.events += noteToMidiEvents(n)
    mt.events += getEndEvents(mt)

    # set all events to have this track
    mt.updateEvents()

    mf = midiModule.MidiFile()
    mf.tracks = [mt]
    mf.ticksPerQuarterNote = defaults.ticksPerQuarter
    return mf




#-------------------------------------------------------------------------------
# Chords

def midiEventsToChord(eventList, ticksPerQuarter=None, inputM21=None):
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
    <music21.chord.Chord A2 B-2>
    >>> c.duration.quarterLength
    2.0
    '''
    if inputM21 == None:
        from music21 import chord
        c = chord.Chord()
    else:
        c = inputM21

    if ticksPerQuarter == None:
        ticksPerQuarter = defaults.ticksPerQuarter

    from music21 import pitch
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


def chordToMidiEvents(inputM21, includeDeltaTime=True):
    '''
    >>> from music21 import *
    >>> c = chord.Chord(['c3','g#4', 'b5'])
    >>> eventList = chordToMidiEvents(c)
    >>> eventList
    [<MidiEvent DeltaTime, t=0, track=None, channel=None>, <MidiEvent NOTE_ON, t=None, track=None, channel=1, pitch=48, velocity=90>, <MidiEvent DeltaTime, t=0, track=None, channel=None>, <MidiEvent NOTE_ON, t=None, track=None, channel=1, pitch=68, velocity=90>, <MidiEvent DeltaTime, t=0, track=None, channel=None>, <MidiEvent NOTE_ON, t=None, track=None, channel=1, pitch=83, velocity=90>, <MidiEvent DeltaTime, t=1024, track=None, channel=None>, <MidiEvent NOTE_OFF, t=None, track=None, channel=1, pitch=48, velocity=0>, <MidiEvent DeltaTime, t=0, track=None, channel=None>, <MidiEvent NOTE_OFF, t=None, track=None, channel=1, pitch=68, velocity=0>, <MidiEvent DeltaTime, t=0, track=None, channel=None>, <MidiEvent NOTE_OFF, t=None, track=None, channel=1, pitch=83, velocity=0>]

    '''
    mt = None # midi track 
    eventList = []
    c = inputM21

    # temporary storage for setting correspondance
    noteOn = []
    noteOff = [] 

    for i in range(len(c.pitches)):
        pitchObj = c.pitches[i]

        if includeDeltaTime:
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
        if not pitchObj.isTwelveTone():
            me.centShift =  pitchObj.getCentShiftFromMidi()
        me.velocity = 90 # default, can change later
        eventList.append(me)
        noteOn.append(me)

    # must create each note on in chord before each note on
    for i in range(len(c.pitches)):
        pitchObj = c.pitches[i]

        if includeDeltaTime:
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
        if not pitchObj.isTwelveTone():
            me.centShift =  pitchObj.getCentShiftFromMidi()
        me.velocity = 0 # must be zero
        eventList.append(me)
        noteOff.append(me)

    # set correspondence
    for i, meOn in enumerate(noteOn):
        meOff = noteOff[i]
        meOn.correspondingEvent = meOff
        meOff.correspondingEvent = meOn

    return eventList 



def chordToMidiFile(inputM21): 
    # this can be consolidated with noteToMidiFile
    c = inputM21

    mt = midiModule.MidiTrack(1)
    mt.events += getStartEvents(mt)
    mt.events += chordToMidiEvents(c)
    mt.events += getEndEvents(mt)

    # set all events to have this track
    mt.updateEvents()

    mf = midiModule.MidiFile()
    mf.tracks = [mt]
    mf.ticksPerQuarterNote = defaults.ticksPerQuarter
    return mf



#-------------------------------------------------------------------------------
def instrumentToMidiEvents(inputM21, includeDeltaTime=True):

    inst = inputM21
    mt = None # midi track 

    events = []
    if includeDeltaTime:
        dt = midiModule.DeltaTime(mt)
        dt.time = 0
        events.append(dt)

    me = midiModule.MidiEvent(mt)
    me.type = "PROGRAM_CHANGE"
    me.time = None 
    me.channel = 1
    me.data = inst.midiProgram
    events.append(me)
    return events




#-------------------------------------------------------------------------------
# Meta events

def midiEventsToTimeSignature(eventList):
    '''Convert a single MIDI event into a music21 TimeSignature object.

    >>> from music21 import *
    >>> mt = midi.MidiTrack(1)
    >>> me1 = midi.MidiEvent(mt)
    >>> me1.type = "TIME_SIGNATURE"
    >>> me1.data = midi.putNumbersAsList([3, 1, 24, 8]) # 3/2 time
    >>> ts = midiEventsToTimeSignature(me1)
    >>> ts
    <music21.meter.TimeSignature 3/2>

    >>> me2 = midi.MidiEvent(mt)
    >>> me2.type = "TIME_SIGNATURE"
    >>> me2.data = midi.putNumbersAsList([3, 4]) # 3/16 time
    >>> ts = midiEventsToTimeSignature(me2)
    >>> ts
    <music21.meter.TimeSignature 3/16>

    '''
    # http://www.sonicspot.com/guide/midifiles.html
    # The time signature defined with 4 bytes, a numerator, a denominator, a metronome pulse and number of 32nd notes per MIDI quarter-note. The numerator is specified as a literal value, but the denominator is specified as (get ready) the value to which the power of 2 must be raised to equal the number of subdivisions per whole note. For example, a value of 0 means a whole note because 2 to the power of 0 is 1 (whole note), a value of 1 means a half-note because 2 to the power of 1 is 2 (half-note), and so on. 

    #The metronome pulse specifies how often the metronome should click in terms of the number of clock signals per click, which come at a rate of 24 per quarter-note. For example, a value of 24 would mean to click once every quarter-note (beat) and a value of 48 would mean to click once every half-note (2 beats). And finally, the fourth byte specifies the number of 32nd notes per 24 MIDI clock signals. This value is usually 8 because there are usually 8 32nd notes in a quarter-note. At least one Time Signature Event should appear in the first track chunk (or all track chunks in a Type 2 file) before any non-zero delta time events. If one is not specified 4/4, 24, 8 should be assumed.
    from music21 import meter

    if not common.isListLike(eventList):
        event = eventList
    else: # get the second event; first is delta time
        event = eventList[1]

    # time signature is 4 byte encoding
    post = midiModule.getNumbersAsList(event.data)

    n = post[0]
    d = pow(2, post[1])
    ts = meter.TimeSignature('%s/%s' % (n, d))
    return ts

def timeSignatureToMidiEvents(ts, includeDeltaTime=True):
    '''Translate a m21 TiemSignature to a pair of events, including a DeltaTime.

    >>> from music21 import *
    >>> ts = meter.TimeSignature('5/4')
    >>> eventList = timeSignatureToMidiEvents(ts)
    >>> eventList[0]
    <MidiEvent DeltaTime, t=0, track=None, channel=None>
    >>> eventList[1]
    <MidiEvent TIME_SIGNATURE, t=None, track=None, channel=1, data='\\x05\\x02\\x18\\x08'>
    '''
    mt = None # use a midi track set to None

    eventList = []

    if includeDeltaTime:
        dt = midiModule.DeltaTime(mt)
        dt.time = 0 # set to zero; will be shifted later as necessary
        # add to track events
        eventList.append(dt)

    n = ts.numerator
    # need log base 2 to solve for exponent of 2
    # 1 is 0, 2 is 1, 4 is 2, 16 is 4, etc
    d = int(math.log(ts.denominator, 2))
    metroClick = 24 # clock signals per click, clicks are 24 per quarter
    subCount = 8 # number of 32 notes in a quarternote

    me = midiModule.MidiEvent(mt)
    me.type = "TIME_SIGNATURE"
    me.channel = 1
    me.time = None # not required
    me.data = midiModule.putNumbersAsList([n, d, metroClick, subCount])
    eventList.append(me)

    return eventList 



def midiEventsToKeySignature(eventList):
    '''Convert a single MIDI event into a music21 TimeSignature object.

    >>> from music21 import *
    >>> mt = midi.MidiTrack(1)
    >>> me1 = midi.MidiEvent(mt)
    >>> me1.type = "KEY_SIGNATURE"
    >>> me1.data = midi.putNumbersAsList([2, 0]) # d major
    >>> ks = midiEventsToKeySignature(me1)
    >>> ks
    <music21.key.KeySignature of 2 sharps>

    >>> me2 = midi.MidiEvent(mt)
    >>> me2.type = "KEY_SIGNATURE"
    >>> me2.data = midi.putNumbersAsList([-2, 0]) # b- major
    >>> me2.data
    '\\xfe\\x00'
    >>> midi.getNumbersAsList(me2.data)
    [254, 0]
    >>> ks = midiEventsToKeySignature(me2)
    >>> ks
    <music21.key.KeySignature of 2 flats>

    '''
    # This meta event is used to specify the key (number of sharps or flats) and scale (major or minor) of a sequence. A positive value for the key specifies the number of sharps and a negative value specifies the number of flats. A value of 0 for the scale specifies a major key and a value of 1 specifies a minor key.
    from music21 import key

    if not common.isListLike(eventList):
        event = eventList
    else: # get the second event; first is delta time
        event = eventList[1]
    post = midiModule.getNumbersAsList(event.data)

    if post[0] > 12:
        # flip around 256
        sharpCount = post[0] - 256 # need negative values
    else:
        sharpCount = post[0]

    environLocal.printDebug(['midiEventsToKeySignature', post, sharpCount])

    # first value is number of sharp, or neg for number of flat
    ks = key.KeySignature(sharpCount)

    if post[1] == 0:
        ks.mode = 'major'
    if post[1] == 1:
        ks.mode = 'minor'
    return ks

def keySignatureToMidiEvents(ks, includeDeltaTime=True):
    '''Convert a single MIDI event into a music21 TimeSignature object.

    >>> from music21 import key
    >>> ks = key.KeySignature(2)
    >>> ks
    <music21.key.KeySignature of 2 sharps>
    >>> eventList = keySignatureToMidiEvents(ks)
    >>> eventList[1]
    <MidiEvent KEY_SIGNATURE, t=None, track=None, channel=1, data='\\x02\\x00'>

    >>> ks = key.KeySignature(-5)
    >>> ks
    <music21.key.KeySignature of 5 flats>
    >>> eventList = keySignatureToMidiEvents(ks)
    >>> eventList[1]
    <MidiEvent KEY_SIGNATURE, t=None, track=None, channel=1, data='\\xfb\\x00'>
    '''

    mt = None # use a midi track set to None

    eventList = []

    if includeDeltaTime:
        dt = midiModule.DeltaTime(mt)
        dt.time = 0 # set to zero; will be shifted later as necessary
        # add to track events
        eventList.append(dt)

    sharpCount = ks.sharps
    if ks.mode == 'minor':        
        mode = 1
    else: # major or None; must define one
        mode = 0

    me = midiModule.MidiEvent(mt)
    me.type = "KEY_SIGNATURE"
    me.channel = 1
    me.time = None # not required
    me.data = midiModule.putNumbersAsList([sharpCount, mode])
    eventList.append(me)

    return eventList 




#-------------------------------------------------------------------------------
# Streams

def _prepareStream(streamObj, instObj=None):
    '''Prepare a Stream for MIDI processing. This includes removing ties, flattening, and finding a first instrument of necessary. An optional `instObj` parameter can be provided 
    '''
    if instObj is None:
        # see if an instrument is defined in this or a parent stream
        # used for the first instrument definition
        instObj = streamObj.getInstrument(returnDefault=False)

    # have to be sorted, have to strip ties
    # retain containers to get all elements: time signatures, dynamics, etc
    s = streamObj.stripTies(inPlace=False, matchByPitch=False, 
        retainContainers=True)
    s = s.flat.sorted

    # see if there is an instrument in the first position of this Stream, if not
    # insert found instrument
    if instObj is not None:
        iStream = s.getElementsByClass('Instrument')
        if len(iStream) > 0 and iStream[0].getOffsetBySite(s) == 0:
            # already have an instrument in the first position
            pass
        else:
            s.insert(0, instObj)
    return s, instObj


def _getPacket(trackId, offset, midiEvent, obj, lastInstrument=None):
    '''Pack a dictionary of parameters for each event. Packets are used for sorting and configuring all note events.
    '''
    post = {}
    post['trackId'] = trackId
    post['offset'] = offset
    post['midiEvent'] = midiEvent
    post['obj'] = obj # keep a reference to the source object
    post['centShift'] = midiEvent.centShift
    # allocate channel later
    post['channel'] = None
    # store last m21 instrument object
    post['lastInstrument'] = lastInstrument
    return post

def _streamToPackets(s, trackId=1):
    '''Convert a Stream to packets. This assumes that the Stream has already been flattened, ties have been stripped, and instruments, if necessary, have been added. 
    '''
    # store all events by offset by offset without delta times
    # as (absTime, event)
    packetsByOffset = []
    lastInstrument = None

    # probably already flat and sorted
    for obj in s:
        classes = obj.classes
        # test: match to 'GeneralNote'
        if 'Note' in classes or 'Rest' in classes:
            if 'Rest' in classes:
                continue
            # get a list of midi events
            # using this property here is easier than using the above conversion
            # methods, as we do not need to know what the object is
            sub = noteToMidiEvents(obj, includeDeltaTime=False)
        elif 'Chord' in classes:
            sub = chordToMidiEvents(obj, includeDeltaTime=False)
        elif 'Dynamic' in classes:
            pass # configure dynamics
        elif 'TimeSignature' in classes:
            # return a pair of events
            sub = timeSignatureToMidiEvents(obj, includeDeltaTime=False)
        elif 'KeySignature' in classes:
            sub = keySignatureToMidiEvents(obj, includeDeltaTime=False)
        # first instrument will have been gathered above with get start elements
        elif 'Instrument' in classes:
            lastInstrument = obj
            sub = instrumentToMidiEvents(obj, includeDeltaTime=False)
        else: # other objects may have already been added
            environLocal.printDebug(['streamToMidiTrack: skipping', obj])
            continue

        # all events: delta/note-on/delta/note-off
        # strip delta times
        packets = []
        for i in range(len(sub)):
            # store offset, midi event, object
            # add channel and pitch change also
            midiEvent = sub[i]
            if midiEvent.type != 'NOTE_OFF':
                # use offset
                p = _getPacket(trackId, 
                            offsetToMidi(obj.getOffsetBySite(s)), 
                            midiEvent, obj=obj, lastInstrument=lastInstrument)
                packets.append(p)
            else: # if its a note_off, use the duration to shift offset
                p = _getPacket(trackId, 
                    offsetToMidi(obj.getOffsetBySite(s)) + durationToMidi(obj.duration), 
                    midiEvent, obj=obj, lastInstrument=lastInstrument)
                packets.append(p)
        packetsByOffset += packets

    # add events to the list
    # need to convert add delta times for all events

    packetsByOffset.sort(
        cmp=lambda x,y: cmp(x['offset'], y['offset'])
        )

    # return packets and stream, as this flat stream should be retained
    return packetsByOffset


# what  we can do is keep a tuple for each moment in the offset map:
# 
# (channel, midi-patch, fractional-part-of-alter, free-after-offset)
# 
# when we encounter a pitch object, we see what its midi-patch and
# fractional-part-of-alter is,
# then we see if there is already a channel that matches that.  If so, we assign
# that channel to this note and if this note's endTime is > free-after-offset, we
# set free-after-offset to be endTime.  If there isn't a channel for this
# midi-patch/fpoa and there are channels free, then we add an entry for that
# channel, send the midi patch change and pitch bend info to that channel and
# update the free-after-offset time to be endTime.  If there are no channels
# free, we find the first one whose free-after-offset < currentNote.offset and we
# put a midi-patch change and/or pitchbend change there and assign the note to
# that channel, and set free-after-offset.  Only if there are no free channels
# after that would we raise an exception.
# 
# It seems like conceptually in this model, MidiChannel should be a Stream
# subclass that represents notes in a particular MidiChannel but also contains
# MidiPatchChange objects and MidiPitchBend objects.  All in midi.py -- what do
# you think?


def _processPackets(packets):
    '''Given a list of packets, assign each to a channel. Do each track one at time, based on the track id. Shift to different channels if a pitch bend is necessary. Keep track of which channels are available. Need to insert a program change in the empty channel to based on last instrument. Insert pitch bend messages as well, one for start of event, one for end of event.
    '''
    pass



def _packetsToEvents(midiTrack, packetsSrc, trackIdFilter=None):
    '''Given a list of packets, sort all packets and add proper delta times. Optionally filters packets by track Id. 
    '''
    environLocal.printDebug(['_packetsToEvents', 'got packets:', len(packetsSrc)])
    # add delta times
    # first, collect only the packets for this track id
    packets = []
    if trackIdFilter is not None:
        for p in packetsSrc:
            if p['trackId'] == trackIdFilter:
                packets.append(p)
    else:
        packets = packetsSrc

    packets.sort(
        cmp=lambda x,y: cmp(x['offset'], y['offset'])
        )

    events = []
    lastOffset = 0
    for p in packets:
        me = p['midiEvent']
        if me.time is None:
            me.time = 0

        t = p['offset'] - lastOffset
        if t < 0:
            raise TranslateException('got a negative delta time')
        dt = midiModule.DeltaTime(midiTrack, time=t, channel=me.channel)
        environLocal.printDebug(['packetsByOffset', p])
        events.append(dt)
        events.append(me)
        lastOffset = p['offset']

    environLocal.printDebug(['_packetsToEvents', 'total events:', len(events)])

    return events


def streamToMidiTrack(inputM21, instObj=None, trackId=1):
    '''Returns a :class:`music21.midi.base.MidiTrack` object based on the content of this Stream.

    This assumes that this Stream has only one Part. For Streams that contain sub-streams, use streamToMidiTracks.

    >>> from music21 import *
    >>> s = stream.Stream()
    >>> n = note.Note('g#')
    >>> n.quarterLength = .5
    >>> s.repeatAppend(n, 4)
    >>> mt = streamToMidiTrack(s)
    >>> len(mt.events)
    20
    '''
    environLocal.printDebug(['streamToMidiTrack()'])

    s, instObj = _prepareStream(inputM21, instObj)
    mt = midiModule.MidiTrack(trackId)

    mt.events += getStartEvents(mt, instObj) # gets track name
    packetsByOffset = _streamToPackets(s, trackId)
   
    mt.events += _packetsToEvents(mt, packetsByOffset, trackIdFilter=trackId)
    # must update all events with a ref to this MidiTrack

    mt.updateEvents()
    mt.events += getEndEvents(mt)
    return mt





# def streamToMidiTrack(inputM21, instObj=None, translateTimeSignature=True):
#     '''Returns a :class:`music21.midi.base.MidiTrack` object based on the content of this Stream.
# 
#     This assumes that this Stream has only one Part. For Streams that contain sub-streams, use streamToMidiTracks.
# 
#     >>> from music21 import *
#     >>> s = stream.Stream()
#     >>> n = note.Note('g#')
#     >>> n.quarterLength = .5
#     >>> s.repeatAppend(n, 4)
#     >>> mt = streamToMidiTrack(s)
#     >>> len(mt.events)
#     20
#     '''
# 
#     # NOTE: this procedure requires that there are no overlaps between
#     # adjacent events. 
# 
#     environLocal.printDebug(['streamToMidiTrack()'])
# 
#     if instObj is None:
#         # see if an instrument is defined in this or a parent stream
#         instObj = inputM21.getInstrument()
# 
#     # each part will become midi track
#     # the 1 here becomes the midi track index
#     mt = midiModule.MidiTrack(1)
#     mt.events += midiModule.getStartEvents(mt, instObj.partName)
# 
#     # initial time is start of this Stream
#     #t = self.offset * defaults.ticksPerQuarter
#     # should shift at tracks level
#     t = 0 * defaults.ticksPerQuarter
# 
#     # have to be sorted, have to strip ties
#     # retain containers to get all elements: time signatures, dynamics, etc
#     s = inputM21.stripTies(inPlace=False, matchByPitch=False, 
#         retainContainers=True)
#     s = s.flat
#     # probably already flat and sorted
#     for obj in s.sorted:
#         tDurEvent = 0 # the found delta ticks in each event
# 
#         classes = obj.classes
#         # test: match to 'GeneralNote'
#         if 'Note' in classes or 'Rest' in classes or 'Chord' in classes:
#         #if obj.isNote or obj.isRest or obj.isChord:
# 
#             # find difference since last event to this event
#             # cannot use getOffsetBySite(self), as need flat offset
#             # all values are in tpq; t stores abs time in tpq
#             tDif = (obj.offset * defaults.ticksPerQuarter) - t
# 
#             #environLocal.printDebug([str(obj).ljust(26), 't', str(t).ljust(10), 'tdif', tDif])
# 
#             # include 'Unpitched'
#             if 'Rest' in classes:
#                 # for a rest, do not do anything: difference in offset will 
#                 # account for the gap
#                 continue
# 
#             # get a list of midi events
#             # using this property here is easier than using the above conversion
#             # methods, as we do not need to know what the object is
#             sub = obj.midiEvents
#             # need to tag these events with their local time for sorting
# 
#             # a note has 4 events: delta/note-on/delta/note-off
#             if 'Note' in classes:
#                 sub[0].time = int(round(tDif)) # set first delta 
#                 # get the duration in ticks; this is the delta to 
#                 # to the note off message; already set when midi events are 
#                 # obtained
#                 tDurEvent = int(round(sub[2].time))
# 
#             # a chord has delta/note-on/delta/note-off for each memeber
#             # of the chord. on the first delta is the offset, and only
#             # the first delta preceding the first note-off is the duration
#             if 'Chord' in classes:
#                 # divide events between note-on and note-off
#                 sub[0].time = int(round(tDif)) # set first delta 
#                 # only the delta before the first note-off has the event dur
#                 # could also sum all durations before setting first
#                 # this is the second half of events
#                 tDurEvent = int(round(len(sub) / 2))
# 
#             # to get new current time, need both the duration of the event
#             # as well as any difference found between the last event
#             t += tDif + tDurEvent
#             # add events to the list
#             mt.events += sub
# 
#         elif 'Dynamic' in classes:
#             pass # configure dynamics
# 
#         elif 'TimeSignature' in classes:
#             # find difference since last event to this event
#             # cannot use getOffsetBySite(self), as need flat offset
#             # all values are in tpq; t stores abs time in tpq
#             tDif = (obj.offset * defaults.ticksPerQuarter) - t
#             # return a pair of events
#             sub = timeSignatureToMidiEvents(obj)
#             # for a ts, this will usually be zero, but not always
#             sub[0].time = int(round(tDif)) # set first delta 
#             t += tDif
#             mt.events += sub
# 
#         elif 'KeySignature' in classes:
#             tDif = (obj.offset * defaults.ticksPerQuarter) - t
# 
#             environLocal.printDebug([str(obj).ljust(26), 't', str(t).ljust(10), 'tdif', tDif])
# 
#             sub = keySignatureToMidiEvents(obj)
#             # for a ts, this will usually be zero, but not always
#             sub[0].time = int(round(tDif)) # set first delta 
#             t += tDif
#             mt.events += sub
# 
#         else: # other objects may have already been added
#             pass
# 
#     # must update all events with a ref to this MidiTrack
#     mt.updateEvents()
#     mt.events += midiModule.getEndEvents(mt)
#     return mt
#     

def midiTrackToStream(mt, ticksPerQuarter=None, quantizePost=True,
    inputM21=None):
    '''
    >>> from music21 import *
    >>> import os
    >>> fp = os.path.join(common.getSourceFilePath(), 'midi', 'testPrimitive',  'test05.mid')
    >>> mf = midi.MidiFile()
    >>> mf.open(fp)
    >>> mf.read()
    >>> mf.close()
    >>> len(mf.tracks)
    1
    >>> mt = mf.tracks[0] 
    >>> s = midiTrackToStream(mt)
    >>> len(s.notesAndRests)
    9
    '''
    environLocal.printDebug(['midiTrackToStream(): got midi track: events', len(mt.events), 'ticksPerQuarter', ticksPerQuarter])

    if inputM21 == None:
        from music21 import stream
        s = stream.Stream()
    else:
        s = inputM21

    if ticksPerQuarter == None:
        ticksPerQuarter = defaults.ticksPerQuarter

    # need to build chords and notes
    from music21 import chord
    from music21 import note

    # get an abs start time for each event, discard deltas
    events = []
    t = 0

    # pair deltas with events, convert abs time
    # get even numbers
    # in some cases, the first event may not be a delta time, but
    # a SEQUENCE_TRACK_NAME or something else. thus, need to get
    # first delta time
    i = 0
    while i < len(mt.events):
        # in pairs, first should be delta time, second should be event
        #environLocal.printDebug(['midiTrackToStream(): index', 'i', i, mt.events[i]])
        #environLocal.printDebug(['midiTrackToStream(): index', 'i+1', i+1, mt.events[i+1]])

        # need to find pairs of delta time and events
        # in some cases, there are delta times that are out of order, or
        # packed in the beginning
        if mt.events[i].isDeltaTime() and not mt.events[i+1].isDeltaTime():
            td = mt.events[i]
            e = mt.events[i+1]
            t += td.time # increment time
            events.append([t, e])
            i += 2
            continue
        elif (not mt.events[i].isDeltaTime() and not 
            mt.events[i+1].isDeltaTime()):
            environLocal.printDebug(['midiTrackToStream(): got two non delta times in a row'])
            i += 1
            continue
        elif mt.events[i].isDeltaTime() and mt.events[i+1].isDeltaTime():
            environLocal.printDebug(['midiTrackToStream(): got two delta times in a row'])
            i += 1
            continue
        else:
            # cannot pair delta time to the next event; skip by 1
            environLocal.printDebug(['cannot pair to delta time', mt.events[i]])
            i += 1
            continue


    #environLocal.printDebug(['raw event pairs', events])

    # need to pair note-on with note-off
    notes = [] # store pairs of pairs
    metaEvents = [] # store pairs of abs time, m21 object
    memo = [] # store already matched note off
    for i in range(len(events)):
        #environLocal.printDebug(['midiTrackToStream(): paired events', events[i][0], events[i][1]])

        if i in memo:
            continue
        t, e = events[i]
        # for each note on event, we need to search for a match in all future
        # events
        if e.isNoteOn():
            match = None
            for j in range(i+1, len(events)):
                if j in memo: 
                    continue
                tSub, eSub = events[j]
                if e.matchedNoteOff(eSub):
                    memo.append(j)
                    match = i, j
                    break
            if match is not None:
                i, j = match
                notes.append([events[i], events[j]])
            else:
                environLocal.printDebug(['midiTrackToStream(): cannot find a note off for a note on', e])
        else:
            if e.type == 'TIME_SIGNATURE':
                # time signature should be 4 bytes
                metaEvents.append([t, midiEventsToTimeSignature(e)])
            elif e.type == 'KEY_SIGNATURE':
                metaEvents.append([t, midiEventsToKeySignature(e)])
            elif e.type == 'SET_TEMPO':
                pass
            elif e.type == 'INSTRUMENT_NAME':
                # TODO import instrument object
                pass
            elif e.type == 'PROGRAM_CHANGE':
                pass
            elif e.type == 'MIDI_PORT':
                pass

    # first create meta events
    for t, obj in metaEvents:
        environLocal.printDebug(['insert midi meta event:', t, obj])
        s.insert(t / float(ticksPerQuarter), obj)


    environLocal.printDebug(['midiTrackToStream(): found notes ready for Stream import', len(notes)])

    # collect notes with similar start times into chords
    # create a composite list of both notes and chords
    #composite = []
    chordSub = None
    i = 0
    while i < len(notes):
        # look at each note; get on time and event
        on, off = notes[i]
        t, e = on
        # go through all following notes
        for j in range(i+1, len(notes)):
            # look at each on time event
            onSub, offSub = notes[j]
            tSub, eSub = onSub
            # can set a tolerance for chordSubing; here at 1/16th
            # of a quarter
            if tSub - t <= ticksPerQuarter / 16:
                if chordSub == None: # start a new one
                    chordSub = [notes[i]]
                chordSub.append(notes[j])
                continue # keep looing
            else: # no more matches; assuming chordSub tones are contiguous
                if chordSub != None:
                    #composite.append(chordSub)
                    # create a chord here
                    c = chord.Chord()
                    c._setMidiEvents(chordSub, ticksPerQuarter)
                    o = notes[i][0][0] / float(ticksPerQuarter)
                    s.insert(o, c)
                    iSkip = len(chordSub)
                    chordSub = None
                else: # just append the note
                    #composite.append(notes[i])
                    # create a note here
                    n = note.Note()
                    n._setMidiEvents(notes[i], ticksPerQuarter)
                    # the time is the first value in the first pair
                    # need to round, as floating point error is likely
                    o = notes[i][0][0] / float(ticksPerQuarter)
                    s.insert(o, n)
                    iSkip = 1
                break # exit secondary loop
        i += iSkip
                    
#     environLocal.printDebug(['got notes:'])
#     for e in notes:
#         print e

    # quantize to nearest 16th
    if quantizePost:    
        s.quantize([8, 3], processOffsets=True, processDurations=True)

    # always need to fill gaps, as rests are not found in any other way
    s.makeRests(inPlace=True, fillGaps=True)
    return s



def streamsToMidiTracks(inputM21):
    '''Given a multipart stream, return a list of MIDI tracks. 
    '''
    from music21 import stream
    s = inputM21

    # return a list of MidiTrack objects
    midiTracks = []

    # TODO: may add a conductor track that contains
    # time signature, tempo, and other meta data

    # TODO: may need to shift all time values to accomodate 
    # Streams that do not start at same time

    # temporary channel allocation
    channels = range(1,10) + range(11,17) # skip 10

    if s.hasPartLikeStreams():
        for obj in s.getElementsByClass('Stream'):
            mt = streamToMidiTrack(obj)
            mt.setChannel(channels.pop(0))
            midiTracks.append(mt)
    else: # just get this single stream
        mt = streamToMidiTrack(s)
        mt.setChannel(channels.pop(0))
        midiTracks.append(mt)
    return midiTracks


def midiTracksToStreams(midiTracks, ticksPerQuarter=None, quantizePost=True,
    inputM21=None):
    '''Given a list of midiTracks, populate this Stream with sub-streams for each part. 
    '''
    from music21 import stream
    if inputM21 == None:
        s = stream.Stream()
    else:
        s = inputM21

    for mt in midiTracks:
        # not all tracks have notes defined; only creates parts for those
        # that do
        #environLocal.printDebug(['raw midi trakcs', mt])

        if mt.hasNotes(): 
            streamPart = stream.Part() # create a part instance for each part
            streamPart._setMidiTracksPart(mt,
                ticksPerQuarter=ticksPerQuarter, quantizePost=quantizePost)
            s.insert(0, streamPart)
        else:
            # note: in some cases a track such as this might have metadata
            # such as the time sig, tempo, or other parameters
            environLocal.printDebug(['skipping midi track with no notes', mt])
    
    return s


def streamToMidiFile(inputM21):
    '''
    >>> from music21 import *
    >>> s = stream.Stream()
    >>> n = note.Note('g#')
    >>> n.quarterLength = .5
    >>> s.repeatAppend(n, 4)
    >>> mf = streamToMidiFile(s)
    >>> len(mf.tracks)
    1
    >>> len(mf.tracks[0].events)
    20
    '''
    s = inputM21

    midiTracks = s._getMidiTracks()

    # update track indices
    # may need to update channel information
    for i in range(len(midiTracks)):
        midiTracks[i].index = i + 1

    mf = midiModule.MidiFile()
    mf.tracks = midiTracks
    mf.ticksPerQuarterNote = defaults.ticksPerQuarter
    return mf



def midiFileToStream(mf, inputM21=None):
    '''
    >>> from music21 import *
    >>> import os
    >>> fp = os.path.join(common.getSourceFilePath(), 'midi', 'testPrimitive',  'test05.mid')
    >>> mf = midi.MidiFile()
    >>> mf.open(fp)
    >>> mf.read()
    >>> mf.close()
    >>> len(mf.tracks)
    1
    >>> s = midiFileToStream(mf)
    >>> len(s.flat.notesAndRests)
    9
    '''

    environLocal.printDebug(['got midi file: tracks:', len(mf.tracks)])

    from music21 import stream
    if inputM21 == None:
        s = stream.Stream()
    else:
        s = inputM21

    if len(mf.tracks) == 0:
        raise StreamException('no tracks are defined in this MIDI file.')
    else:
        # create a stream for each tracks   
        # may need to check if tracks actually have event data
        s._setMidiTracks(mf.tracks, mf.ticksPerQuarterNote)

    return s



#-------------------------------------------------------------------------------
class Test(unittest.TestCase):
    
    def runTest(self):
        pass

    def testNote(self):

        from music21 import note
        n1 = note.Note('A4')
        n1.quarterLength = 2.0
        eventList = n1.midiEvents
        self.assertEqual(len(eventList), 4)

        self.assertEqual(isinstance(eventList[0], midiModule.DeltaTime), True)
        self.assertEqual(isinstance(eventList[2], midiModule.DeltaTime), True)


        # translate eventList back to a note
        n2 = midiEventsToNote(eventList)
        self.assertEqual(n2.pitch.nameWithOctave, 'A4')
        self.assertEqual(n2.quarterLength, 2.0)


    def testTimeSignature(self):
        import copy
        from music21 import note, stream, meter
        n = note.Note()
        n.quarterLength = .5
        s = stream.Stream()
        for i in range(20):
            s.append(copy.deepcopy(n))

        s.insert(0, meter.TimeSignature('3/4'))
        s.insert(3, meter.TimeSignature('5/4'))
        s.insert(8, meter.TimeSignature('2/4'))

        mt = streamToMidiTrack(s)
        self.assertEqual(len(mt.events), 90)

        #s.show('midi')
        
        # get and compare just the time signatures
        mtAlt = streamToMidiTrack(s.getElementsByClass('TimeSignature'))
        match = """[<MidiEvent DeltaTime, t=0, track=1, channel=None>, <MidiEvent SEQUENCE_TRACK_NAME, t=0, track=1, channel=None, data=''>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent TIME_SIGNATURE, t=0, track=1, channel=1, data='\\x03\\x02\\x18\\x08'>, <MidiEvent DeltaTime, t=3072, track=1, channel=1>, <MidiEvent TIME_SIGNATURE, t=0, track=1, channel=1, data='\\x05\\x02\\x18\\x08'>, <MidiEvent DeltaTime, t=5120, track=1, channel=1>, <MidiEvent TIME_SIGNATURE, t=0, track=1, channel=1, data='\\x02\\x02\\x18\\x08'>, <MidiEvent DeltaTime, t=0, track=1, channel=None>, <MidiEvent END_OF_TRACK, t=None, track=1, channel=1, data=''>]"""
        self.assertEqual(str(mtAlt.events), match)





    def testKeySignature(self):
        import copy
        from music21 import note, stream, meter, key
        n = note.Note()
        n.quarterLength = .5
        s = stream.Stream()
        for i in range(20):
            s.append(copy.deepcopy(n))

        s.insert(0, meter.TimeSignature('3/4'))
        s.insert(3, meter.TimeSignature('5/4'))
        s.insert(8, meter.TimeSignature('2/4'))

        s.insert(0, key.KeySignature(4))
        s.insert(3, key.KeySignature(-5))
        s.insert(8, key.KeySignature(6))

        mt = streamToMidiTrack(s)
        self.assertEqual(len(mt.events), 96)

        #s.show('midi')
        mtAlt = streamToMidiTrack(s.getElementsByClass('TimeSignature'))



    def testAnacrusisTiming(self):

        from music21 import corpus

        s = corpus.parse('bach/bwv103.6')

        # get just the soprano part
        soprano = s.parts['soprano']
        mts = streamToMidiTrack(soprano)

        # first note-on is not delayed, even w anacrusis
        match = """[<MidiEvent DeltaTime, t=0, track=1, channel=None>, <MidiEvent SEQUENCE_TRACK_NAME, t=0, track=1, channel=None, data=u'Soprano'>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent PROGRAM_CHANGE, t=0, track=1, channel=1, data=0>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent KEY_SIGNATURE, t=0, track=1, channel=1, data='\\x02\\x01'>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent TIME_SIGNATURE, t=0, track=1, channel=1, data='\\x04\\x02\\x18\\x08'>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent NOTE_ON, t=0, track=1, channel=1, pitch=66, velocity=90>]"""
       

        self.assertEqual(str(mts.events[:10]), match)

        # first note-on is not delayed, even w anacrusis
        match = """[<MidiEvent DeltaTime, t=0, track=1, channel=None>, <MidiEvent SEQUENCE_TRACK_NAME, t=0, track=1, channel=None, data=u'Alto'>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent PROGRAM_CHANGE, t=0, track=1, channel=1, data=0>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent KEY_SIGNATURE, t=0, track=1, channel=1, data='\\x02\\x01'>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent TIME_SIGNATURE, t=0, track=1, channel=1, data='\\x04\\x02\\x18\\x08'>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent NOTE_ON, t=0, track=1, channel=1, pitch=62, velocity=90>]"""

        alto = s.parts['alto']
        mta = streamToMidiTrack(alto)

        self.assertEqual(str(mta.events[:10]), match)


        # try streams to midi tracks
        # get just the soprano part
        soprano = s.parts['soprano']
        mtList = streamsToMidiTracks(soprano)
        self.assertEqual(len(mtList), 1)

        # its the same as before
        match = """[<MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent SEQUENCE_TRACK_NAME, t=0, track=1, channel=1, data=u'Soprano'>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent PROGRAM_CHANGE, t=0, track=1, channel=1, data=0>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent KEY_SIGNATURE, t=0, track=1, channel=1, data='\\x02\\x01'>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent TIME_SIGNATURE, t=0, track=1, channel=1, data='\\x04\\x02\\x18\\x08'>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent NOTE_ON, t=0, track=1, channel=1, pitch=66, velocity=90>]"""

        self.assertEqual(str(mtList[0].events[:10]), match)



    def testMidiProgramChangeA(self):
        from music21 import stream, instrument, note
        p1 = stream.Part()
        p1.append(instrument.Dulcimer())
        p1.repeatAppend(note.Note('g6', quarterLength=1.5), 4)
        
        p2 = stream.Part()
        p2.append(instrument.Tuba())
        p2.repeatAppend(note.Note('c1', quarterLength=2), 2)
        
        p3 = stream.Part()
        p3.append(instrument.TubularBells())
        p3.repeatAppend(note.Note('e4', quarterLength=1), 4)
        
        s = stream.Score()
        s.insert(0, p1)
        s.insert(0, p2)
        s.insert(0, p3)

        mts = streamsToMidiTracks(s)
        #p1.show()
        #s.show('midi')


    def testMidiProgramChangeB(self):

        from music21 import stream, instrument, note, scale
        import random

        iList = [instrument.Harpsichord, instrument.Clavichord, instrument.Accordion, instrument.Celesta, instrument.Contrabass, instrument.Viola, instrument.Harp, instrument.ElectricGuitar, instrument.Ukulele, instrument.Banjo, instrument.Piccolo, instrument.AltoSaxophone, instrument.Trumpet]

        sc = scale.MinorScale()
        pitches = sc.getPitches('c2', 'c5')
        random.shuffle(pitches)

        s = stream.Stream()
        for i in range(30):
            n = note.Note(pitches[i%len(pitches)])
            n.quarterLength = .5
            inst = iList[i%len(iList)]() # call to create instance
            s.append(inst)
            s.append(n)

        mts = streamsToMidiTracks(s)

        #s.show('midi')



    def testOverlappedEventsA(self):
        from music21 import corpus
        s = corpus.parse('bwv66.6')
        sFlat = s.flat
        mtList = streamsToMidiTracks(sFlat)
        self.assertEqual(len(mtList), 1)

        # its the same as before
        match = """[<MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent NOTE_OFF, t=0, track=1, channel=1, pitch=65, velocity=0>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent NOTE_ON, t=0, track=1, channel=1, pitch=66, velocity=90>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent NOTE_ON, t=0, track=1, channel=1, pitch=61, velocity=90>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent NOTE_ON, t=0, track=1, channel=1, pitch=58, velocity=90>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent NOTE_ON, t=0, track=1, channel=1, pitch=54, velocity=90>, <MidiEvent DeltaTime, t=1024, track=1, channel=1>, <MidiEvent NOTE_OFF, t=0, track=1, channel=1, pitch=66, velocity=0>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent NOTE_OFF, t=0, track=1, channel=1, pitch=61, velocity=0>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent NOTE_OFF, t=0, track=1, channel=1, pitch=58, velocity=0>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent NOTE_OFF, t=0, track=1, channel=1, pitch=54, velocity=0>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent END_OF_TRACK, t=None, track=1, channel=1, data=''>]"""

        self.assertEqual(str(mtList[0].events[-20:]), match)


    def testOverlappedEventsB(self):
        from music21 import stream, scale, note
        import random
        
        sc = scale.MajorScale()
        pitches = sc.getPitches('c2', 'c5')
        random.shuffle(pitches)
        
        dur = 16
        step = .5
        o = 0
        s = stream.Stream()
        for p in pitches:
            n = note.Note(p)
            n.quarterLength = dur - o
            s.insert(o, n)
            o = o + step

        mt = streamToMidiTrack(s)

        #s.plot('pianoroll')
        #s.show('midi')

    def testOverlappedEventsC(self):

        from music21 import stream, note, chord, meter, key

        s = stream.Stream()
        s.insert(key.KeySignature(3))
        s.insert(meter.TimeSignature('2/4'))
        s.insert(0, note.Note('c'))
        n = note.Note('g')
        n.pitch.microtone = 25
        s.insert(0, n)

        c = chord.Chord(['d','f','a'], type='half')
        c.pitches[1].microtone = -15
        s.append(c)

        pos = s.highestTime
        s.insert(pos, note.Note('e'))
        s.insert(pos, note.Note('b'))

        mt = streamToMidiTrack(s)

        #s.show('midi')

    def testExternalMidiProgramChangeB(self):

        from music21 import stream, instrument, note, scale
        import random

        iList = [instrument.Harpsichord, instrument.Clavichord, instrument.Accordion, 
                 instrument.Celesta, instrument.Contrabass, instrument.Viola, 
                 instrument.Harp, instrument.ElectricGuitar, instrument.Ukulele, 
                 instrument.Banjo, instrument.Piccolo, instrument.AltoSaxophone, 
                 instrument.Trumpet, instrument.Clarinet, instrument.Flute,
                 instrument.Violin, instrument.Soprano, instrument.Oboe,
                 instrument.Tuba, instrument.Sitar, instrument.Ocarina,
                 instrument.Piano]

        sc = scale.MajorScale()
        pitches = sc.getPitches('c2', 'c5')
        #random.shuffle(pitches)

        s = stream.Stream()
        for i, p in enumerate(pitches):
            n = note.Note(p)
            n.quarterLength = 1.5
            inst = iList[i]() # call to create instance
            s.append(inst)
            s.append(n)

 
        mts = streamsToMidiTracks(s)
        #s.show('midi')

        


if __name__ == "__main__":
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof

