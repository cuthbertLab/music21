# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         midi.translate.py
# Purpose:      Translate MIDI and music21 objects
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2010-2015 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------

'''
Module to translate MIDI data to music21 Streams and voice versa.  Note that quantization of
notes takes place in the :meth:`~music21.stream.Stream.quantize` method not here.
'''


import unittest
import math
import copy

from music21 import defaults
from music21 import common

# modules that import this include stream.py, chord.py, note.py
# thus, cannot import these here

from music21 import exceptions21
from music21 import environment
from music21.ext import six

_MOD = "midi.translate.py"  
environLocal = environment.Environment(_MOD)


#-------------------------------------------------------------------------------
class TranslateException(exceptions21.Music21Exception):
    pass

#-------------------------------------------------------------------------------
# Durations

def offsetToMidi(o):
    '''
    Helper function to convert a music21 offset value to MIDI ticks, depends on *defaults.ticksPerQuarter*
    
    Returns an int.
    
    >>> defaults.ticksPerQuarter
    1024
    >>> midi.translate.offsetToMidi(20.5)
    20992
    '''
    return int(round(o * defaults.ticksPerQuarter))

def durationToMidi(d):
    '''
    Converts a :class:`~music21.duration.Duration` object to midi ticks.
    
    Depends on *defaults.ticksPerQuarter*, Returns an int.
    
    >>> n = note.Note()
    >>> n.duration.type = 'half'
    >>> midi.translate.durationToMidi(n.duration)
    2048
    
    >>> d = duration.Duration()
    >>> dReference = midi.translate.midiToDuration(1024, inputM21DurationObject = d)
    >>> dReference is d
    True
    >>> d.type
    'quarter'
    >>> d.type = '16th'
    >>> d.quarterLength
    0.25
    >>> midi.translate.durationToMidi(d)
    256
    '''
    if d._quarterLengthNeedsUpdating:
        d.updateQuarterLength()
    return int(round(d.quarterLength * defaults.ticksPerQuarter))

def midiToDuration(ticks, ticksPerQuarter=None, inputM21DurationObject=None):
    '''    
    Converts a number of MIDI Ticks to a music21 duration.Duration() object.
    
    Optional parameters include ticksPerQuarter -- in case something other
    than the default.ticksPerQuarter (1024) is used in this file.  And
    it can take a :class:`~music21.duration.Duration` object to modify, specified
    as *inputM21DurationObject*
    
    
    >>> d = midi.translate.midiToDuration(1024)
    >>> d
    <music21.duration.Duration 1.0>
    >>> d.type
    'quarter'
    
    >>> n = note.Note()
    >>> midi.translate.midiToDuration(3072, inputM21DurationObject=n.duration)
    <music21.duration.Duration 3.0>
    >>> n.duration.type
    'half'
    >>> n.duration.dots
    1
    
    More complex rhythms can also be set automatically:
    
    >>> d2 = duration.Duration()
    >>> d2reference = midi.translate.midiToDuration(1200, inputM21DurationObject=d2)
    >>> d2 is d2reference
    True
    >>> d2.quarterLength
    1.171875
    >>> d2.type
    'complex'
    >>> d2.components
    (DurationTuple(type='quarter', dots=0, quarterLength=1.0), 
     DurationTuple(type='32nd', dots=0, quarterLength=0.125), 
     DurationTuple(type='128th', dots=1, quarterLength=0.046875))
    >>> d2.components[2].type
    '128th'
    >>> d2.components[2].dots
    1

    '''
    if inputM21DurationObject is None:
        from music21 import duration
        d = duration.Duration()
    else:
        d = inputM21DurationObject

    if ticksPerQuarter == None:
        ticksPerQuarter = defaults.ticksPerQuarter
    # given a value in ticks
    d._qtrLength = float(ticks) / ticksPerQuarter
    d._componentsNeedUpdating = True
    d._quarterLengthNeedsUpdating = False
    return d


#-------------------------------------------------------------------------------
# utility functions for getting commonly used event


def _getStartEvents(mt=None, channel=1, instrumentObj=None):
    '''
    Returns a list of midi.MidiEvent objects found at the beginning of a track.

    A MidiTrack reference can be provided via the `mt` parameter.
    '''
    from music21 import midi as midiModule
    events = []
    if instrumentObj is None or instrumentObj.bestName() is None:
        partName = ''
    else:
        partName = instrumentObj.bestName()

    dt = midiModule.DeltaTime(mt, channel=channel)
    dt.time = 0
    events.append(dt)

    me = midiModule.MidiEvent(mt, channel=channel)
    me.type = "SEQUENCE_TRACK_NAME"
    me.time = 0 # always at zero?
    me.data = partName
    events.append(me)

    # additional allocation of instruments may happen elsewhere
    # this may lead to two program changes happening at time zero
    # however, this assures that the program change happens before the 
    # the clearing of the pitch bend data
    if instrumentObj is not None and instrumentObj.midiProgram is not None:
        sub = instrumentToMidiEvents(instrumentObj, includeDeltaTime=True, 
                                    channel=channel)
        events += sub

    return events


def getEndEvents(mt=None, channel=1):
    '''
    Returns a list of midi.MidiEvent objects found at the end of a track.
    '''
    from music21 import midi as midiModule

    events = []

    dt = midiModule.DeltaTime(mt, channel=channel)
    dt.time = 0
    events.append(dt)

    me = midiModule.MidiEvent(mt)
    me.type = "END_OF_TRACK"
    me.channel = channel
    me.data = '' # must set data to empty string
    events.append(me)

    return events

#-------------------------------------------------------------------------------
# Multiobject conversion

def music21ObjectToMidiFile(music21Object):
    classes = music21Object.classes
    if 'Stream' in classes:
        return streamToMidiFile(music21Object)
    elif 'Note' in classes:
        return noteToMidiFile(music21Object)
    elif 'Chord' in classes:
        return chordToMidiFile(music21Object)
    else:
        raise TranslateException("Cannot translate this object to MIDI: %s" % music21Object)


#-------------------------------------------------------------------------------
# Notes

def midiEventsToNote(eventList, ticksPerQuarter=None, inputM21=None):
    '''
    Convert from a list of midi.DeltaTime and midi.MidiEvent objects to a music21 Note.
    
    The list can be presented in one of two forms:
    
        [deltaTime1, midiEvent1, deltaTime2, midiEvent2]
    
    or
    
        [(deltaTime1, midiEvent1), (deltaTime2, midiEvent2)]

    It is assumed, but not checked, that midiEvent2 is an appropriate Note_Off command.  Thus, only
    three elements are really needed.

    The `inputM21` parameter can be a Note or None; in the case of None, a Note object is created.
    In either case it returns a Note (N.B.: this will change soon so that None will be returned
    if `inputM21` is given.  This will match the behavior of other translate objects).

    N.B. this takes in a list of music21 MidiEvent objects so see [...] on how to
    convert raw MIDI data to MidiEvent objects

    In this example, we start a NOTE_ON event at offset 1.0 that lasts for 2.0 quarter notes until we
    send a zero-velocity NOTE_ON (=NOTE_OFF) event for the same pitch.

    >>> mt = midi.MidiTrack(1)
    >>> dt1 = midi.DeltaTime(mt)
    >>> dt1.time = 1024

    >>> me1 = midi.MidiEvent(mt)
    >>> me1.type = "NOTE_ON"
    >>> me1.pitch = 45
    >>> me1.velocity = 94

    >>> dt2 = midi.DeltaTime(mt)
    >>> dt2.time = 2048

    >>> me2 = midi.MidiEvent(mt)
    >>> me2.type = "NOTE_ON"
    >>> me2.pitch = 45
    >>> me2.velocity = 0

    >>> n = midi.translate.midiEventsToNote([dt1, me1, dt2, me2])
    >>> n.pitch
    <music21.pitch.Pitch A2>
    >>> n.duration.quarterLength
    1.0
    >>> n.volume.velocity
    94
    
    An `inputM21` object can be given in which case it's set.
    
    >>> m = note.Note()
    >>> dummy = midi.translate.midiEventsToNote([dt1, me1, dt2, me2], inputM21=m)
    >>> m.pitch
    <music21.pitch.Pitch A2>
    >>> m.duration.quarterLength
    1.0
    >>> m.volume.velocity
    94

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
        tOff, unused_eOff = eventList[1]

    # a representation closer to stream
    elif len(eventList) == 4:
        # delta times are first and third
        dur = eventList[2].time - eventList[0].time
        # shift to start at zero; only care about duration here
        tOn, eOn = 0, eventList[1]
        tOff, unused_eOff = dur, eventList[3]
    else:
        raise TranslateException('cannot handle MIDI event list in the form: %r', eventList)

    n.pitch.midi = eOn.pitch
    n.volume.velocity = eOn.velocity
    n.volume.velocityIsRelative = False # not relative coming from MIDI
    #n._midiVelocity = eOn.velocity
    # here we are handling an occasional error that probably should not happen
    if (tOff - tOn) != 0:
        midiToDuration(tOff - tOn, ticksPerQuarter, n.duration)
    else:
        #environLocal.printDebug(['cannot translate found midi event with zero duration:', eOn, n])
        # for now, substitute 1
        n.quarterLength = 1.0

    return n


def noteToMidiEvents(inputM21, includeDeltaTime=True, channel=1):
    '''
    Translate a music21 Note to a list of four MIDI events -- 
    the DeltaTime for the start of the note (0), the NOTE_ON event, the
    DeltaTime to the end of the note, and the NOTE_OFF event.

    If `includeDeltaTime` is not True then the DeltaTime events 
    aren't returned, thus only two events are returned.
    
    The initial deltaTime object is always 0.  It will be changed when
    processing Notes from a Stream. 
    
    The `channel` can be specified, otherwise channel 1 is assumed.

    >>> n1 = note.Note('C#4')
    >>> eventList = midi.translate.noteToMidiEvents(n1)
    >>> eventList
    [<MidiEvent DeltaTime, t=0, track=None, channel=1>, <MidiEvent NOTE_ON, t=None, track=None, channel=1, pitch=61, velocity=90>, <MidiEvent DeltaTime, t=1024, track=None, channel=1>, <MidiEvent NOTE_OFF, t=None, track=None, channel=1, pitch=61, velocity=0>]

    >>> n1.duration.quarterLength = 2.5
    >>> eventList = midi.translate.noteToMidiEvents(n1)
    >>> eventList
    [<MidiEvent DeltaTime, t=0, track=None, channel=1>, <MidiEvent NOTE_ON, t=None, track=None, channel=1, pitch=61, velocity=90>, <MidiEvent DeltaTime, t=2560, track=None, channel=1>, <MidiEvent NOTE_OFF, t=None, track=None, channel=1, pitch=61, velocity=0>]

    Omitting DeltaTimes:

    >>> eventList2 = midi.translate.noteToMidiEvents(n1, includeDeltaTime=False, channel=9)
    >>> eventList2
    [<MidiEvent NOTE_ON, t=None, track=None, channel=9, pitch=61, velocity=90>, <MidiEvent NOTE_OFF, t=None, track=None, channel=9, pitch=61, velocity=0>]
    '''
    from music21 import midi as midiModule

    n = inputM21

    mt = None # use a midi track set to None
    eventList = []

    if includeDeltaTime:
        dt = midiModule.DeltaTime(mt, channel=channel)
        dt.time = 0 # set to zero; will be shifted later as necessary
        # add to track events
        eventList.append(dt)

    me1 = midiModule.MidiEvent(mt)
    me1.type = "NOTE_ON"
    me1.channel = channel
    me1.time = None # not required
    #me1.pitch = n.midi
    me1.pitch = n.pitch.getMidiPreCentShift() # will shift later, do not round
    if not n.pitch.isTwelveTone():
        me1.centShift = n.pitch.getCentShiftFromMidi()

    # TODO: not yet using dynamics or velocity
#     volScalar = n.volume.getRealized(useDynamicContext=False, 
#             useVelocity=True, useArticulations=False)

    # use cached realized, as realized values should have already been set
    me1.velocity = int(round(n.volume.cachedRealized * 127))

    eventList.append(me1)

    if includeDeltaTime:
        # add note off / velocity zero message
        dt = midiModule.DeltaTime(mt, channel=channel)
        dt.time = durationToMidi(n.duration)
        # add to track events
        eventList.append(dt)

    me2 = midiModule.MidiEvent(mt)
    me2.type = "NOTE_OFF"
    me2.channel = channel
    me2.time = None #d
    #me2.pitch = n.midi
    me2.pitch = n.pitch.getMidiPreCentShift() # will shift later, do not round
    me2.pitchSpace = n.pitch.ps
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
    Converts a single Music21 Note to an entire :class:`~music21.midi.base.MidiFile` object
    with one track, on channel 1.

    >>> n1 = note.Note('C4')
    >>> n1.quarterLength = 6
    >>> mf = midi.translate.noteToMidiFile(n1)
    >>> mf
    <MidiFile 1 tracks
      <MidiTrack 1 -- 8 events
        <MidiEvent DeltaTime, t=0, track=1, channel=1>
        <MidiEvent SEQUENCE_TRACK_NAME, t=0, track=1, channel=1, data=''>
        <MidiEvent DeltaTime, t=0, track=1, channel=1>
        <MidiEvent NOTE_ON, t=None, track=1, channel=1, pitch=60, velocity=90>
        <MidiEvent DeltaTime, t=6144, track=1, channel=1>
        <MidiEvent NOTE_OFF, t=None, track=1, channel=1, pitch=60, velocity=0>
        <MidiEvent DeltaTime, t=0, track=1, channel=1>
        <MidiEvent END_OF_TRACK, t=None, track=1, channel=1, data=''>
      >
    >
    
    >>> mf.tracks[0].events
    [<MidiEvent DeltaTime, t=0, track=1, channel=1>, 
     <MidiEvent SEQUENCE_TRACK_NAME, t=0, track=1, channel=1, data=''>, 
     <MidiEvent DeltaTime, t=0, track=1, channel=1>, 
     <MidiEvent NOTE_ON, t=None, track=1, channel=1, pitch=60, velocity=90>, 
     <MidiEvent DeltaTime, t=6144, track=1, channel=1>, 
     <MidiEvent NOTE_OFF, t=None, track=1, channel=1, pitch=60, velocity=0>, 
     <MidiEvent DeltaTime, t=0, track=1, channel=1>, 
     <MidiEvent END_OF_TRACK, t=None, track=1, channel=1, data=''>]
    '''
    from music21 import midi as midiModule
    
    n = inputM21
    mt = midiModule.MidiTrack(1)
    mt.events += _getStartEvents(mt)
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
# TODO: add velocity reading and writing

def midiEventsToChord(eventList, ticksPerQuarter=None, inputM21=None):
    '''
    Creates a Chord from a list of :class:`~music21.midi.base.DeltaTime` 
    and :class:`~music21.midi.base.MidiEvent` objects.  See midiEventsToNote
    for details.
    
    All DeltaTime objects except the first are ignored.
    
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

    >>> c = midi.translate.midiEventsToChord([dt1, me1, dt2, me2, dt3, me3, dt4, me4])
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
    from music21 import volume
    pitches = []
    volumes = []

    # this is a format provided by the Stream conversion of 
    # midi events; it pre groups events for a chord together in nested pairs
    # of abs start time and the event object
    if isinstance(eventList, list) and isinstance(eventList[0], list):
        # pairs of pairs
        tOff = eventList[0][1][0]
        for onPair, unused_offPair in eventList:
            tOn, eOn = onPair
            p = pitch.Pitch()
            p.midi = eOn.pitch
            pitches.append(p)
            v = volume.Volume(velocity=eOn.velocity)
            v.velocityIsRelative = False # velocity is absolute coming from 
            volumes.append(v)
    # assume it is  a flat list        
    else:
        onEvents = eventList[:(len(eventList) // 2)]
        offEvents = eventList[(len(eventList) // 2):]
        # first is always delta time
        tOn = onEvents[0].time
        tOff = offEvents[0].time
        # create pitches for the odd on Events:
        for i in range(1, len(onEvents), 2):
            p = pitch.Pitch()
            p.midi = onEvents[i].pitch
            pitches.append(p)
            v = volume.Volume(velocity=onEvents[i].velocity)
            v.velocityIsRelative = False # velocity is absolute coming from 
            volumes.append(v)

    c.pitches = pitches
    c.volume = volumes # can set a list to volume property
    # can simply use last-assigned pair of tOff, tOn
    if (tOff - tOn) != 0:
        midiToDuration(tOff - tOn, ticksPerQuarter, c.duration)
    else:
        #environLocal.printDebug(['cannot translate found midi event with zero duration:', eventList, c])
        # for now, substitute 1
        c.quarterLength = 1    
    return c


def chordToMidiEvents(inputM21, includeDeltaTime=True):
    '''
    Translates a :class:`~music21.chord.Chord` object to a 
    list of base.DeltaTime and base.MidiEvents objects.
    
    See noteToMidiEvents above for more details.

    >>> c = chord.Chord(['c3','g#4', 'b5'])
    >>> c.volume = volume.Volume(velocity=90)
    >>> c.volume.velocityIsRelative = False
    >>> eventList = midi.translate.chordToMidiEvents(c)
    >>> eventList
    [<MidiEvent DeltaTime, t=0, track=None, channel=None>, <MidiEvent NOTE_ON, t=None, track=None, channel=1, pitch=48, velocity=90>, <MidiEvent DeltaTime, t=0, track=None, channel=None>, <MidiEvent NOTE_ON, t=None, track=None, channel=1, pitch=68, velocity=90>, <MidiEvent DeltaTime, t=0, track=None, channel=None>, <MidiEvent NOTE_ON, t=None, track=None, channel=1, pitch=83, velocity=90>, <MidiEvent DeltaTime, t=1024, track=None, channel=None>, <MidiEvent NOTE_OFF, t=None, track=None, channel=1, pitch=48, velocity=0>, <MidiEvent DeltaTime, t=0, track=None, channel=None>, <MidiEvent NOTE_OFF, t=None, track=None, channel=1, pitch=68, velocity=0>, <MidiEvent DeltaTime, t=0, track=None, channel=None>, <MidiEvent NOTE_OFF, t=None, track=None, channel=1, pitch=83, velocity=0>]
    '''
    from music21 import midi as midiModule
    mt = None # midi track 
    eventList = []
    c = inputM21

    # temporary storage for setting correspondence
    noteOn = []
    noteOff = [] 

    chordVolume = c.volume # use if component volume are not defined
    hasComponentVolumes = c.hasComponentVolumes()

    for i in range(len(c)):
    #for i in range(len(c.pitches)):
        chordComponent = c[i]
        #pitchObj = c.pitches[i]
        #noteObj = chordComponent
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
        me.pitch = chordComponent.pitch.midi
        if not chordComponent.pitch.isTwelveTone():
            me.centShift = chordComponent.pitch.getCentShiftFromMidi()
        #if 'volume' in chordComponent:
        
        if hasComponentVolumes:
#             volScalar = chordComponent.volume.getRealized(
#                 useDynamicContext=False, 
#                 useVelocity=True, useArticulations=False)
            volScalar = chordComponent.volume.cachedRealized
        else:
#             volScalar = chordVolume.getRealized(
#                 useDynamicContext=False, 
#                 useVelocity=True, useArticulations=False)
            volScalar = chordVolume.cachedRealized

        me.velocity = int(round(volScalar * 127))
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
                dt.time = durationToMidi(c.duration)
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
    '''
    Similar to `noteToMidiFile`, translates a Chord to a 
    fully-formed MidiFile object.
    '''
    from music21 import midi as midiModule
    
    # this can be consolidated with noteToMidiFile
    c = inputM21

    mt = midiModule.MidiTrack(1)
    mt.events += _getStartEvents(mt)
    mt.events += chordToMidiEvents(c)
    mt.events += getEndEvents(mt)

    # set all events to have this track
    mt.updateEvents()

    mf = midiModule.MidiFile()
    mf.tracks = [mt]
    mf.ticksPerQuarterNote = defaults.ticksPerQuarter
    return mf


#-------------------------------------------------------------------------------
def instrumentToMidiEvents(inputM21, includeDeltaTime=True, 
                            midiTrack=None, channel=1):
    '''
    Converts a :class:`~music21.instrument.Instrument` object to a list of MidiEvents
    
    TODO: DOCS and TESTS
    '''
    from music21 import midi as midiModule

    inst = inputM21
    mt = midiTrack # midi track 
    events = []
    if includeDeltaTime:
        dt = midiModule.DeltaTime(mt, channel=channel)
        dt.time = 0
        events.append(dt)
    me = midiModule.MidiEvent(mt)
    me.type = "PROGRAM_CHANGE"
    me.time = 0 
    me.channel = channel
    me.data = inst.midiProgram # key step
    events.append(me)
    return events


#-------------------------------------------------------------------------------
# Meta events

def midiEventsToInstrument(eventList):
    '''
    Convert a single MIDI event into a music21 Instrument object.
    '''
    if not common.isListLike(eventList):
        event = eventList
    else: # get the second event; first is delta time
        event = eventList[1]

    from music21 import instrument
    try:
        i = instrument.instrumentFromMidiProgram(event.data)
    except instrument.InstrumentException:
        i = instrument.Instrument()
    return i
    
def midiEventsToTimeSignature(eventList):
    '''
    Convert a single MIDI event into a music21 TimeSignature object.

    >>> mt = midi.MidiTrack(1)
    >>> me1 = midi.MidiEvent(mt)
    >>> me1.type = "TIME_SIGNATURE"
    >>> me1.data = midi.putNumbersAsList([3, 1, 24, 8]) # 3/2 time
    >>> ts = midi.translate.midiEventsToTimeSignature(me1)
    >>> ts
    <music21.meter.TimeSignature 3/2>

    >>> me2 = midi.MidiEvent(mt)
    >>> me2.type = "TIME_SIGNATURE"
    >>> me2.data = midi.putNumbersAsList([3, 4]) # 3/16 time
    >>> ts = midi.translate.midiEventsToTimeSignature(me2)
    >>> ts
    <music21.meter.TimeSignature 3/16>

    '''
    # http://www.sonicspot.com/guide/midifiles.html
    # The time signature defined with 4 bytes, a numerator, a denominator, 
    # a metronome pulse and number of 32nd notes per MIDI quarter-note. 
    # The numerator is specified as a literal value, but the denominator 
    # is specified as (get ready) the value to which the power of 2 must be 
    # raised to equal the number of subdivisions per whole note. For example, 
    # a value of 0 means a whole note because 2 to the power of 0 is 1 
    # (whole note), a value of 1 means a half-note because 2 to the power 
    # of 1 is 2 (half-note), and so on. 

    # The metronome pulse specifies how often the metronome should click in 
    # terms of the number of clock signals per click, which come at a rate 
    # of 24 per quarter-note. For example, a value of 24 would mean to click 
    # once every quarter-note (beat) and a value of 48 would mean to click 
    # once every half-note (2 beats). And finally, the fourth byte specifies 
    # the number of 32nd notes per 24 MIDI clock signals. This value is usually 
    # 8 because there are usually 8 32nd notes in a quarter-note. At least one 
    # Time Signature Event should appear in the first track chunk (or all track 
    # chunks in a Type 2 file) before any non-zero delta time events. If one 
    # is not specified 4/4, 24, 8 should be assumed.
    from music21 import meter
    from music21 import midi as midiModule

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
    '''
    Translate a :class:`~music21.meter.TimeSignature` to a pair of events: a DeltaTime and
    a MidiEvent TIME_SIGNATURE.

    Returns a two-element list

    >>> ts = meter.TimeSignature('5/4')
    >>> eventList = midi.translate.timeSignatureToMidiEvents(ts)
    >>> eventList[0]
    <MidiEvent DeltaTime, t=0, track=None, channel=None>
    >>> eventList[1]
    <MidiEvent TIME_SIGNATURE, t=None, track=None, channel=1, data='\\x05\\x02\\x18\\x08'>
    '''
    from music21 import midi as midiModule

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
    '''
    Convert a single MIDI event into a :class:`~music21.key.KeySignature` object.

    >>> mt = midi.MidiTrack(1)
    >>> me1 = midi.MidiEvent(mt)
    >>> me1.type = "KEY_SIGNATURE"
    >>> me1.data = midi.putNumbersAsList([2, 0]) # d major
    >>> ks = midi.translate.midiEventsToKeySignature(me1)
    >>> ks
    <music21.key.KeySignature of 2 sharps, mode major>
    >>> ks.mode
    'major'

    >>> me2 = midi.MidiEvent(mt)
    >>> me2.type = "KEY_SIGNATURE"
    >>> me2.data = midi.putNumbersAsList([-2, 1]) # g minor
    >>> me2.data
    '\\xfe\\x01'
    >>> midi.getNumbersAsList(me2.data)
    [254, 1]
    >>> ks = midi.translate.midiEventsToKeySignature(me2)
    >>> ks
    <music21.key.KeySignature of 2 flats, mode minor>
    >>> ks.mode
    'minor'
    '''
    # This meta event is used to specify the key (number of sharps or flats) 
    # and scale (major or minor) of a sequence. A positive value for 
    # the key specifies the number of sharps and a negative value specifies 
    # the number of flats. A value of 0 for the scale specifies a major key 
    # and a value of 1 specifies a minor key.
    from music21 import key
    from music21 import midi as midiModule

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

    #environLocal.printDebug(['midiEventsToKeySignature', post, sharpCount])

    # first value is number of sharp, or neg for number of flat
    ks = key.KeySignature(sharpCount)

    if post[1] == 0:
        ks.mode = 'major'
    if post[1] == 1:
        ks.mode = 'minor'
    return ks

def keySignatureToMidiEvents(ks, includeDeltaTime=True):
    '''
    Convert a single :class:`~music21.key.KeySignature` object to 
    a two-element list of midi events,
    where the first is an empty DeltaTime (unless includeDeltaTime is False) and the second
    is a KEY_SIGNATURE :class:`~music21.midi.base.MidiEvent`

    >>> ks = key.KeySignature(2)
    >>> ks
    <music21.key.KeySignature of 2 sharps>
    >>> eventList = midi.translate.keySignatureToMidiEvents(ks)
    >>> eventList[1]
    <MidiEvent KEY_SIGNATURE, t=None, track=None, channel=1, data='\\x02\\x00'>

    >>> ks = key.KeySignature(-5)
    >>> ks.mode = 'minor'
    >>> ks
    <music21.key.KeySignature of 5 flats, mode minor>
    >>> eventList = midi.translate.keySignatureToMidiEvents(ks, includeDeltaTime = False)
    >>> eventList[0]
    <MidiEvent KEY_SIGNATURE, t=None, track=None, channel=1, data='\\xfb\\x01'>
    '''
    from music21 import midi as midiModule
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


def midiEventsToTempo(eventList):
    '''
    Convert a single MIDI event into a music21 Tempo object.

    TODO: Need Tests
    '''
    from music21 import midi as midiModule
    from music21 import tempo

    if not common.isListLike(eventList):
        event = eventList
    else: # get the second event; first is delta time
        event = eventList[1]
    # get microseconds per quarter
    mspq = midiModule.getNumber(event.data, 3)[0] # first data is number
    bpm = round(60000000.0 / mspq, 2)
    #post = midiModule.getNumbersAsList(event.data)
    #environLocal.printDebug(['midiEventsToTempo, got bpm', bpm])
    mm = tempo.MetronomeMark(number=bpm)
    return mm

def tempoToMidiEvents(tempoIndication, includeDeltaTime=True):
    r'''
    Given any TempoIndication, convert it to a MIDI tempo indication. 

    >>> mm = tempo.MetronomeMark(number=90)
    >>> events = midi.translate.tempoToMidiEvents(mm)
    >>> events[0]
    <MidiEvent DeltaTime, t=0, track=None, channel=None>
    
    Data is not displayed directly below since it's a bytes object in PY3 and str in PY2
    
    >>> events[1]
    <MidiEvent SET_TEMPO, t=None, track=None, channel=1, data=...>
    >>> events[1].data    
    b'\n,+'
    >>> microSecondsPerQuarterNote = midi.getNumber(events[1].data, len(events[1].data))[0]
    >>> microSecondsPerQuarterNote
    666667
    
    >>> round(60 * 1000000.0 / microSecondsPerQuarterNote, 1)
    90.0
    
    Test roundtrip.  Note that for pure tempo numbers, by default
    we create a text name if there's an appropriate one:
    
    >>> midi.translate.midiEventsToTempo(events)
    <music21.tempo.MetronomeMark maestoso Quarter=90.0>
    '''
    from music21 import midi as midiModule
    mt = None # use a midi track set to None
    eventList = []
    if includeDeltaTime:
        dt = midiModule.DeltaTime(mt)
        dt.time = 0 # set to zero; will be shifted later as necessary
        # add to track events
        eventList.append(dt)

    me = midiModule.MidiEvent(mt)
    me.type = "SET_TEMPO"
    me.channel = 1
    me.time = None # not required

    # from any tempo indication, get the sounding metronome mark
    mm = tempoIndication.getSoundingMetronomeMark()
    bpm = mm.getQuarterBPM()
    mspq = int(round(60000000.0 / bpm)) # microseconds per quarter note

    me.data = midiModule.putNumber(mspq, 3)
    eventList.append(me)
    return eventList 



#-------------------------------------------------------------------------------
# Streams


def _getPacket(trackId, offset, midiEvent, obj, lastInstrument=None):
    '''
    Pack a dictionary of parameters for each event. 
    Packets are used for sorting and configuring all note events. 
    Includes offset, any cent shift, the midi event, and the source object.

    Offset and duration values stored here are MIDI ticks, not quarter lengths.

    TODO: Test
    '''
    post = {}
    post['trackId'] = trackId
    post['offset'] = offset # offset values are in midi ticks

    # update sort order here, as type may have been set after creation
    midiEvent.updateSortOrder()
    post['midiEvent'] = midiEvent
    post['obj'] = obj # keep a reference to the source object
    post['centShift'] = midiEvent.centShift
    # allocate channel later
    #post['channel'] = None
    if midiEvent.type != 'NOTE_OFF' and obj is not None:
        # store duration so as to calculate when the 
        # channel/pitch bend can be freed
        post['duration'] = durationToMidi(obj.duration)
    # note offs will have the same object ref, and seem like the have a 
    # duration when they do not
    else: 
        post['duration'] = 0

    # store last m21 instrument object, as needed to reset program changes
    post['lastInstrument'] = lastInstrument
    return post

def _streamToPackets(s, trackId=1):
    '''
    Convert a Stream to packets. 

    This assumes that the Stream has already been flattened, 
    ties have been stripped, and instruments, 
    if necessary, have been added. 

    In converting from a Stream to MIDI, this is called first, 
    resulting in a collection of packets by offset. 
    Then, packets to events is called.
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
            continue # dynamics have already been applied to notes 
        elif 'TimeSignature' in classes:
            # return a pair of events
            sub = timeSignatureToMidiEvents(obj, includeDeltaTime=False)
        elif 'KeySignature' in classes:
            sub = keySignatureToMidiEvents(obj, includeDeltaTime=False)
        elif 'TempoIndication' in classes: # any tempo indication will work
            # note: tempo indications need to be in channel one for most playback
            sub = tempoToMidiEvents(obj, includeDeltaTime=False)
        # first instrument will have been gathered above with get start elements
        elif 'Instrument' in classes:
            lastInstrument = obj # store last instrument
            sub = instrumentToMidiEvents(obj, includeDeltaTime=False)
        else: # other objects may have already been added
            continue

        # we process sub here, which is a list of midi events
        # for each event, we create a packet representation
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
                            offsetToMidi(s.elementOffset(obj)), 
                            midiEvent, obj=obj, lastInstrument=lastInstrument)
                packets.append(p)
            # if its a note_off, use the duration to shift offset
            # midi events have already been created; 
            else: 
                p = _getPacket(trackId, 
                               offsetToMidi(s.elementOffset(obj)) + durationToMidi(obj.duration), 
                               midiEvent, obj=obj, lastInstrument=lastInstrument)
                packets.append(p)
        packetsByOffset += packets

    # sorting is useful here, as we need these to be in order to assign last
    # instrument
    packetsByOffset.sort(
        key=lambda x: (x['offset'], x['midiEvent'].sortOrder)
        )
    # return packets and stream, as this flat stream should be retained
    return packetsByOffset


def _processPackets(packets, channelForInstrument=None, channelsDynamic=None, 
        initChannelForTrack=None):
    '''
    Given a list of packets, assign each to a channel. 

    Do each track one at time, based on the track id. 

    Shift to different channels if a pitch bend is necessary. 

    Keep track of which channels are available. 
    Need to insert a program change in the empty channel 
    too, based on last instrument. 
    
    Insert pitch bend messages as well, 
    one for start of event, one for end of event.

    `packets` is a list of packets.
    `channelForInstrument` should be a dictionary.
    `channelsDynamic` should be a list.
    `initChannelForTrack` should be a dictionary.
    '''
    from music21 import midi as midiModule

    if channelForInstrument is None:
        channelForInstrument = {}
    if channelsDynamic is None:
        channelsDynamic = []
    if initChannelForTrack is None:
        initChannelForTrack = {}
    
    #allChannels = list(range(1, 10)) + list(range(11, 17)) # all but 10
    uniqueChannelEvents = {} # dict of (start, stop, usedChannel) : channel
    post = []
    usedTracks = []

    for p in packets:
        #environLocal.printDebug(['_processPackets', p['midiEvent'].track, p['trackId']])
        # must use trackId, as .track on MidiEvent is not yet set
        if p['trackId'] not in usedTracks:
            usedTracks.append(p['trackId'])

        # only need note_ons, as stored correspondingEvent attr can be used
        # to get noteOff
        if p['midiEvent'].type not in ['NOTE_ON']:
            # set all not note-off messages to init channel
            if p['midiEvent'].type not in ['NOTE_OFF']:
                p['midiEvent'].channel = p['initChannel']
            post.append(p) # add the non note_on packet first
            # if this is a note off, and has a cent shift, need to 
            # rest the pitch bend back to 0 cents
            if p['midiEvent'].type in ['NOTE_OFF']:
                #environLocal.printDebug(['got note-off', p['midiEvent']])
                # cent shift is set for note on and note off
                if p['centShift'] is not None:
                    # do not set channel, as already set
                    me = midiModule.MidiEvent(p['midiEvent'].track, 
                        type="PITCH_BEND", channel=p['midiEvent'].channel)
                    # note off stores note on's pitch; do not invert, simply
                    # set to zero
                    me.setPitchBend(0) 
                    pBendEnd = _getPacket(trackId=p['trackId'], 
                        offset=p['offset'], midiEvent=me, 
                        obj=None, lastInstrument=None)
                    post.append(pBendEnd)
                    #environLocal.printDebug(['adding pitch bend', pBendEnd])
            continue # store and continue

        # set default channel for all packets
        p['midiEvent'].channel = p['initChannel']

        # find a free channel       
        # if necessary, add pitch change at start of Note, 
        # cancel pitch change at end
        o = p['offset']
        oEnd = p['offset']+p['duration']

        channelExclude = [] # channels that cannot be used
        centShift = p['centShift'] # may be None

        #environLocal.printDebug(['\n\noffset', o, 'oEnd', oEnd, 'centShift', centShift])

        # iterate through all past events/channels, and find all
        # that are active and have a pitch bend
        for key in uniqueChannelEvents:
            start, stop, usedChannel = key
            # if offset (start time) is in this range of a found event
            # or if any start or stop is within this span
            #if o >= start and o < stop: # found an offset that is used

            if ( (start >= o and start < oEnd) or
                 (stop > o and stop < oEnd) or
                 (start <= o and stop > o) or
                 (start < oEnd and stop > oEnd)
                ) : 
                # if there is a cent shift active in the already used channel
                #environLocal.printDebug(['matchedOffset overlap'])
                centShiftList = uniqueChannelEvents[key]
                if centShiftList:
                    # only add if unique
                    if usedChannel not in channelExclude:
                        channelExclude.append(usedChannel)
                # or if this event has shift, then we can exclude
                # the channel already used without a shift
                elif centShift is not None:
                    if usedChannel not in channelExclude:
                        channelExclude.append(usedChannel)
                            # cannot break early w/o sorting

        # if no channels are excluded, get a new channel
        #environLocal.printDebug(['post process channelExclude', channelExclude])
        if channelExclude: # only change if necessary
            ch = None       
            # iterate in order over all channels: lower will be added first
            for x in channelsDynamic:
                if x not in channelExclude:
                    ch = x
                    break
            if ch is None:
                raise TranslateException('no unused channels available for microtone/instrument assignment')
            p['midiEvent'].channel = ch
            # change channel of note off; this is used above to turn off pbend
            p['midiEvent'].correspondingEvent.channel = ch
            #environLocal.printDebug(['set channel of correspondingEvent:', 
                                #p['midiEvent'].correspondingEvent])

            # TODO: must add program change, as we are now in a new 
            # channel; regardless of if we have a pitch bend (we may
            # move channels for a different reason  
            if p['lastInstrument'] is not None:
                meList = instrumentToMidiEvents(inputM21=p['lastInstrument'], 
                    includeDeltaTime=False, 
                    midiTrack=p['midiEvent'].track, channel=ch)
                pgmChangePacket = _getPacket(trackId=p['trackId'], 
                    offset=o, midiEvent=meList[0], # keep offset here
                    obj=None, lastInstrument=None)
                post.append(pgmChangePacket)

        else: # use the existing channel
            ch = p['midiEvent'].channel
            # always set corresponding event to the same channel
            p['midiEvent'].correspondingEvent.channel = ch

        #environLocal.printDebug(['assigning channel', ch, 'channelsDynamic', channelsDynamic, "p['initChannel']", p['initChannel']])

        if centShift is not None:
            # add pitch bend
            me = midiModule.MidiEvent(p['midiEvent'].track, 
                                    type="PITCH_BEND", channel=ch)
            me.setPitchBend(centShift)
            pBendStart = _getPacket(trackId=p['trackId'], 
                offset=o, midiEvent=me, # keep offset here
                obj=None, lastInstrument=None)
            post.append(pBendStart)
            #environLocal.printDebug(['adding pitch bend', me])
            # removal of pitch bend will happen above with note off

        # key includes channel, so that durations can span once in each channel
        key = (p['offset'], p['offset']+p['duration'], ch)
        if key not in uniqueChannelEvents:
            # need to count multiple instances of events on the same
            # span and in the same channel (fine if all have the same pitchbend
            uniqueChannelEvents[key] = [] 
        # always add the cent shift if it is not None
        if centShift is not None:
            uniqueChannelEvents[key].append(centShift)
        post.append(p) # add packet/ done after ch change or bend addition
        #environLocal.printDebug(['uniqueChannelEvents', uniqueChannelEvents])

    # this is called once at completion
    #environLocal.printDebug(['uniqueChannelEvents', uniqueChannelEvents])

    # after processing, collect all channels used
    foundChannels = []
    for start, stop, usedChannel in uniqueChannelEvents.keys(): # a list
        if usedChannel not in foundChannels:
            foundChannels.append(usedChannel)
#         for ch in chList:
#             if ch not in foundChannels:
#                 foundChannels.append(ch)
    #environLocal.printDebug(['foundChannels', foundChannels])
    #environLocal.printDebug(['usedTracks', usedTracks])

    # post processing of entire packet collection
    # for all used channels, create a zero pitch bend at time zero
    #for ch in foundChannels:
    # for each track, places a pitch bend in its initChannel
    for trackId in usedTracks:
        ch = initChannelForTrack[trackId]
        # use None for track; will get updated later
        me = midiModule.MidiEvent(track=trackId, type="PITCH_BEND", channel=ch)
        me.setPitchBend(0) 
        pBendEnd = _getPacket(trackId=trackId, 
            offset=0, midiEvent=me, obj=None, lastInstrument=None)
        post.append(pBendEnd)
        #environLocal.printDebug(['adding pitch bend for found channels', me])
    # this sort is necessary
    post.sort(
        key=lambda x: (x['offset'], x['midiEvent'].sortOrder)
        )

    # TODO: for each track, add an additional silent event to make sure
    # entire duration gets played

    # diagnostic display
    #for p in post: environLocal.printDebug(['proceessed packet', p])

    #post = packets
    return post


def _packetsToEvents(midiTrack, packetsSrc, trackIdFilter=None):
    '''
    Given a list of packets, sort all packets and add proper 
    delta times. Optionally filters packets by track Id. 

    At this stage MIDI event objects have been created. 
    The key process here is finding the adjacent time 
    between events and adding DeltaTime events before each MIDI event.

    Delta time channel values are derived from the previous midi event. 

    If `trackIdFilter` is not None, process only packets with 
    a matching track id. this can be used to filter out events 
    associated with a track. 
    '''
    from music21 import midi as midiModule

    #environLocal.printDebug(['_packetsToEvents', 'got packets:', len(packetsSrc)])
    # add delta times
    # first, collect only the packets for this track id
    packets = []
    if trackIdFilter is not None:
        for p in packetsSrc:
            if p['trackId'] == trackIdFilter:
                packets.append(p)
    else:
        packets = packetsSrc

    events = []
    lastOffset = 0
    for p in packets:
        me = p['midiEvent']
        if me.time is None:
            me.time = 0
        t = p['offset'] - lastOffset
        if t < 0:
            raise TranslateException('got a negative delta time')
        # set the channel from the midi event
        dt = midiModule.DeltaTime(midiTrack, time=t, channel=me.channel)
        #environLocal.printDebug(['packetsByOffset', p])
        events.append(dt)
        events.append(me)
        lastOffset = p['offset']
    #environLocal.printDebug(['_packetsToEvents', 'total events:', len(events)])
    return events


def packetsToMidiTrack(packets, trackId=1, channels=None):
    '''
    Given packets already allocated with channel 
    and/or instrument assignments, place these in a MidiTrack.

    Note that all packets can be sent; only those with 
    matching trackIds will be collected into the resulting track

    The `channels` defines a collection of channels available for this Track

    Use _streamToPackets to convert the Stream to the packets
    '''
    from music21 import midi as midiModule

    primaryChannel = 1
    mt = midiModule.MidiTrack(trackId)
    # update based on primary ch   
    mt.events += _getStartEvents(mt, channel=primaryChannel) 
    # track id here filters 
    mt.events += _packetsToEvents(mt, packets, trackIdFilter=trackId)
    # must update all events with a ref to this MidiTrack
    mt.updateEvents() # sets this track as .track for all events
    mt.events += getEndEvents(mt, channel=primaryChannel)
    return mt


def midiTrackToStream(mt, ticksPerQuarter=None, quantizePost=True,
    inputM21=None):
    '''
    Note that quantization takes place in stream.py since it's useful not just for MIDI.

    >>> import os
    >>> fp = os.path.join(common.getSourceFilePath(), 'midi', 'testPrimitive',  'test05.mid')
    >>> mf = midi.MidiFile()
    >>> mf.open(fp)
    >>> mf.read()
    >>> mf.close()
    >>> len(mf.tracks)
    1
    >>> mt = mf.tracks[0] 
    >>> s = midi.translate.midiTrackToStream(mt)
    >>> s
    <music21.stream.Stream ...>
    >>> len(s.notesAndRests)
    11
    '''
    #environLocal.printDebug(['midiTrackToStream(): got midi track: events', len(mt.events), 'ticksPerQuarter', ticksPerQuarter])

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
            #environLocal.printDebug(['midiTrackToStream(): got two non delta times in a row'])
            i += 1
            continue
        elif mt.events[i].isDeltaTime() and mt.events[i+1].isDeltaTime():
            #environLocal.printDebug(['midiTrackToStream(): got two delta times in a row'])
            i += 1
            continue
        else:
            # cannot pair delta time to the next event; skip by 1
            #environLocal.printDebug(['cannot pair to delta time', mt.events[i]])
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
            #environLocal.printDebug(['midiTrackToStream(): isNoteOn', e])
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
                pass
                #environLocal.printDebug(['midiTrackToStream(): cannot find a note off for a note on', e])
        else:
            if e.type == 'TIME_SIGNATURE':
                # time signature should be 4 bytes
                metaEvents.append([t, midiEventsToTimeSignature(e)])
            elif e.type == 'KEY_SIGNATURE':
                metaEvents.append([t, midiEventsToKeySignature(e)])
            elif e.type == 'SET_TEMPO':
                metaEvents.append([t, midiEventsToTempo(e)])
            elif e.type == 'INSTRUMENT_NAME':
                # TODO import instrument object
                pass
            elif e.type == 'PROGRAM_CHANGE':
                metaEvents.append([t, midiEventsToInstrument(e)])
            elif e.type == 'MIDI_PORT':
                pass
            else:
                pass
                #environLocal.printDebug(['unhandled event:', e.type, e.data])

    # first create meta events
    for t, obj in metaEvents:
        #environLocal.printDebug(['insert midi meta event:', t, obj])
        s.insert(t / float(ticksPerQuarter), obj)

    #environLocal.printDebug(['midiTrackToStream(): found notes ready for Stream import', len(notes)])

    # collect notes with similar start times into chords
    # create a composite list of both notes and chords
    #composite = []
    chordSub = None
    i = 0
    iGathered = [] # store a lost of indexes of gathered values put into chords
    voicesRequired = False
    if len(notes) > 1:
        #environLocal.printDebug(['\nmidiTrackToStream(): notes', notes])
        while i < len(notes):
            if i in iGathered:
                i += 1
                continue
            # look at each note; get on time and event
            on, off = notes[i]
            t, e = on
            tOff, unused_eOff = off
            #environLocal.printDebug(['on, off', on, off, 'i', i, 'len(notes)', len(notes)])

            # go through all following notes; if there is only 1 note, this will 
            # not execute;
            # looking for other events that start within a certain small time 
            # window to make into a chord
            # if we find a note with a different end time but same start
            # time, through into a different voice
            for j in range(i+1, len(notes)):
                # look at each on time event
                onSub, offSub = notes[j]
                tSub, unused_eSub = onSub
                tOffSub, unused_eOffSub = offSub
 
                # can set a tolerance for chordSubing; here at 1/16th
                # of a quarter
                chunkTolerance = ticksPerQuarter / 16
                if abs(tSub - t) <= chunkTolerance:
                    # isolate case where end time is not w/n tolerance
                    if abs(tOffSub - tOff) > chunkTolerance:
                        # need to store this as requiring movement to a diff
                        # voice
                        voicesRequired = True
                        continue
                    if chordSub is None: # start a new one
                        chordSub = [notes[i]]
                        iGathered.append(i)
                    chordSub.append(notes[j])
                    iGathered.append(j)
                    continue # keep looping through events to see 
                    # if we can add more elements to this chord group
                else: # no more matches; assuming chordSub tones are contiguous
                    break
            # this comparison must be outside of j loop, as the case where we
            # have the last note in a list of notes and the j loop does not 
            # execute; chordSub will be None
            if chordSub is not None:
                #composite.append(chordSub)
                # create a chord here
                c = chord.Chord()
                midiEventsToChord(chordSub, ticksPerQuarter, c)
                o = notes[i][0][0] / float(ticksPerQuarter)
                c.midiTickStart = notes[i][0][0]
                
                s._insertCore(o, c)
                #iSkip = len(chordSub) # amount of accumulated chords
                chordSub = None
            else: # just append the note, chordSub is None
                #composite.append(notes[i])
                # create a note here
                n = note.Note()
                midiEventsToNote(notes[i], ticksPerQuarter, n)
                # the time is the first value in the first pair
                # need to round, as floating point error is likely
                o = notes[i][0][0] / float(ticksPerQuarter)
                n.midiTickStart = notes[i][0][0]

                s._insertCore(o, n)
                #iSkip = 1
            #break # exit secondary loop
            i += 1
    elif len(notes) == 1: # rare case of just one note
        n = note.Note()
        midiEventsToNote(notes[0], ticksPerQuarter, n)
        # the time is the first value in the first pair
        # need to round, as floating point error is likely
        o = notes[0][0][0] / float(ticksPerQuarter)
        n.midiTickStart = notes[i][0][0]
        s._insertCore(o, n)
                    
    s.elementsChanged()
    # quantize to nearest 16th
    if quantizePost:    
        s.quantize([8, 3], processOffsets=True, processDurations=True, inPlace=True)

    if voicesRequired:
        pass
        # this procedure will make the appropriate rests
        s.makeVoices(inPlace=True, fillGaps=True)
    else:
        # always need to fill gaps, as rests are not found in any other way
        s.makeRests(inPlace=True, fillGaps=True)
    return s

    
def _prepareStreamForMidi(s):
    '''
    Given a score, prepare it for midding processing. 
    In particular, place MetronomeMark objects at 
    Score level, or elsewhere, place it in the first part.
    
    Note: will make a deepcopy() of the stream. (QUESTION: Could this
    be done with a shallow copy?)
    '''
    from music21 import volume

    s = copy.deepcopy(s)
    if s.hasPartLikeStreams():
        # check for tempo indications in the score
        mmTopLevel = s.iter.getElementsByClass('MetronomeMark').stream()
        if mmTopLevel: # place in top part
            target = s.iter.getElementsByClass('Stream')[0]
            for mm in mmTopLevel:
                target.insert(mmTopLevel.elementOffset(mm), mm)
                s.remove(mm) # remove from Score level
        # TODO: move any MetronomeMarks not in the top Part to the top Part
        
        # process Volumes one part at a time
        # this assumes that dynamics in a part/stream apply to all components
        # of that part stream
        # this sets the cachedRealized value for each Volume
        for p in s.iter.getElementsByClass('Stream'):
            volume.realizeVolume(p)

    else: # just a single Stream
        volume.realizeVolume(s)

    return s

def streamHierarchyToMidiTracks(inputM21, acceptableChannelList = None):
    '''
    Given a Stream, Score, Part, etc., that may have substreams (i.e.,
    a hierarchy), return a list of :class:`~music21.midi.base.MidiTrack` objects. 

    acceptableChannelList is a list of MIDI Channel numbers that can be used.
    If None, then 1-9, 11-16 are used (10 being reserved for percussion).

    Called by streamToMidiFile()

    The process:
    
    1. makes a deepcopy of the Stream (Developer TODO: could this 
       be done with a shallow copy?)
       
    2. we make a list of all instruments that are being used in the piece.

    '''
    from music21 import midi as midiModule

    # makes a deepcopy
    s = _prepareStreamForMidi(inputM21)

    # return a list of MidiTrack objects
    midiTracks = []

    # TODO: may need to shift all time values to accomodate 
    # Streams that do not start at same time

    # temporary channel allocation
    if acceptableChannelList is not None:
        allChannels = acceptableChannelList
    else:
        allChannels = list(range(1, 10)) + list(range(11, 17)) # all but 10
    # store streams in uniform list
    substreamList = []
    if s.hasPartLikeStreams():
        for obj in s.getElementsByClass('Stream'):
            substreamList.append(obj)
    else:
        substreamList.append(s) # add single

    # first, create all packets by track
    packetStorage = {}
    allUniqueInstruments = [] # store program numbers
    trackCount = 1
    for s in substreamList:
        s = s.stripTies(inPlace=True, matchByPitch=False, 
                        retainContainers=True)
        s = s.flat.sorted

        # get a first instrument; iterate over rest
        instrumentStream = s.iter.getElementsByClass('Instrument')
        
        # if there is an Instrument object at the start, make instObj that instrument.
        if instrumentStream and s.elementOffset(instrumentStream[0]) == 0:
            instObj = instrumentStream[0]
        else:
            instObj = None
            
        # get all unique instrument ids
        if instrumentStream:
            for i in instrumentStream:
                if i.midiProgram not in allUniqueInstruments:
                    allUniqueInstruments.append(i.midiProgram)
        else: # get None as a placeholder for detaul
            if None not in allUniqueInstruments:
                allUniqueInstruments.append(None)

        # store packets in dictionary; keys are trackids
        packetStorage[trackCount] = {}
        packetStorage[trackCount]['rawPackets'] = _streamToPackets(s, 
                                               trackId=trackCount)
        packetStorage[trackCount]['initInstrument'] = instObj
        trackCount += 1

    channelForInstrument = {} # the instrument is the key
    channelsDynamic = [] # remaining channels
    # create an entry for all unique instruments, assign channels
    # for each instrument, assign a channel; if we go above 16, that is fine
    # we just cannot use it and will take modulus later
    channelsAssigned = []
    for i, iPgm in enumerate(allUniqueInstruments): # values are program numbers
        # the key is the program number; the values is the start channel
        if i < len(allChannels) - 1: # save at least on dynamic channel
            channelForInstrument[iPgm] = allChannels[i]
            channelsAssigned.append(allChannels[i])
        else: # just use 1, and deal with the mess: cannot allocate
            channelForInstrument[iPgm] = allChannels[0]
            channelsAssigned.append(allChannels[0])
            
    # get the dynamic channels, or those not assigned
    for ch in allChannels:
        if ch not in channelsAssigned:
            channelsDynamic.append(ch)

    #environLocal.printDebug(['channelForInstrument', channelForInstrument, 'channelsDynamic', channelsDynamic, 'allChannels', allChannels, 'allUniqueInstruments', allUniqueInstruments])

    initChannelForTrack = {}
    # update packets with first channel
    for key, bundle in packetStorage.items():
        initChannelForTrack[key] = None # key is channel id
        bundle['initChannel'] = None # set for bundle too
        for p in bundle['rawPackets']:
            # get instrument
            instObj = bundle['initInstrument']
            if instObj is None:
                try:
                    initCh = channelForInstrument[None]
                except KeyError:
                    initCh = 0  # CUTHBERT ADD -- Not sure if this works...
            else: # use midi program
                initCh = channelForInstrument[instObj.midiProgram]
            p['initChannel'] = initCh
            # only set for bundle once
            if bundle['initChannel'] is None:
                bundle['initChannel'] = initCh
                initChannelForTrack[key] = initCh

    # combine all packets for processing of channel allocation 
    netPackets = []
    for bundle in packetStorage.values():
        netPackets += bundle['rawPackets']

    # process all channel assignments for all packets together
    netPackets = _processPackets(netPackets, 
        channelForInstrument=channelForInstrument, 
        channelsDynamic=channelsDynamic, 
        initChannelForTrack=initChannelForTrack)

    #environLocal.printDebug(['got netPackets:', len(netPackets), 'packetStorage keys (tracks)', packetStorage.keys()])
    # build each track, sorting out the appropriate packets based on track
    # ids
    for trackId in packetStorage:   
        initChannel = packetStorage[trackId]['initChannel']
        instObj = packetStorage[trackId]['initInstrument']
        # TODO: for a given track id, need to find start/end channel
        mt = midiModule.MidiTrack(trackId) 
        # need to pass preferred channel here
        mt.events += _getStartEvents(mt, channel=initChannel, 
                                    instrumentObj=instObj) 
        # note that netPackets is must be passed here, and then be filtered
        # packets have been added to net packets
        mt.events += _packetsToEvents(mt, netPackets, trackIdFilter=trackId)
        mt.events += getEndEvents(mt, channel=initChannel)
        mt.updateEvents()
    # need to filter out packets only for the desired tracks
        midiTracks.append(mt)

    return midiTracks


def midiTracksToStreams(midiTracks, ticksPerQuarter=None, quantizePost=True,
    inputM21=None):
    '''
    Given a list of midiTracks, populate this Stream with a Part for each track. 
    '''
    from music21 import stream
    if inputM21 == None:
        s = stream.Score()
    else:
        s = inputM21
    # store common elements such as time sig, key sig from conductor
    conductorTrack = stream.Stream()
    #environLocal.printDebug(['midi track count', len(midiTracks)])
    for mt in midiTracks:
        # not all tracks have notes defined; only creates parts for those
        # that do
        #environLocal.printDebug(['raw midi trakcs', mt])
        if mt.hasNotes(): 
            streamPart = stream.Part() # create a part instance for each part
            midiTrackToStream(mt, ticksPerQuarter, quantizePost, 
                              inputM21=streamPart)
#             streamPart._setMidiTracksPart(mt,
#                 ticksPerQuarter=ticksPerQuarter, quantizePost=quantizePost)
            s.insert(0, streamPart)
        else:
            # note: in some cases a track such as this might have metadata
            # such as the time sig, tempo, or other parameters
            #environLocal.printDebug(['found midi track without notes:'])
            midiTrackToStream(mt, ticksPerQuarter, quantizePost, 
                              inputM21=conductorTrack)
    #environLocal.printDebug(['show() conductorTrack elements'])
    # if we have time sig/key sig elements, add to each part
    
    # TODO: this would be faster if we iterated in the other order.
    for p in s.getElementsByClass('Stream'):
        for e in conductorTrack.getElementsByClass(
                            ('TimeSignature', 'KeySignature')):
            # create a deepcopy of the element so a flat does not cause
            # multiple references of the same
            eventCopy = copy.deepcopy(e)
            p.insert(conductorTrack.elementOffset(e), eventCopy)

    # if there is a conductor track, add tempo only to the top-most part
    # MSC: WHY?
    
    p = s.getElementsByClass('Stream')[0]
    for e in conductorTrack.getElementsByClass('MetronomeMark'):
        # create a deepcopy of the element so a flat does not cause
        # multiple references of the same
        eventCopy = copy.deepcopy(e)
        p.insert(conductorTrack.elementOffset(e), eventCopy)
    return s


def streamToMidiFile(inputM21):
    '''
    Converts a Stream hierarchy into a :class:`~music21.midi.base.MidiFile` object.
    
    >>> s = stream.Stream()
    >>> n = note.Note('g#')
    >>> n.quarterLength = .5
    >>> s.repeatAppend(n, 4)
    >>> mf = midi.translate.streamToMidiFile(s)
    >>> len(mf.tracks)
    1
    >>> len(mf.tracks[0].events)
    22
    
    From here, you can call mf.writestr() to get the actual file info. 
    
    >>> sc = scale.PhrygianScale('g')
    >>> s = stream.Stream()
    >>> x=[s.append(note.Note(sc.pitchFromDegree(i % 11), quarterLength=.25)) for i in range(60)]
    >>> mf = midi.translate.streamToMidiFile(s)
    >>> #_DOCS_SHOW mf.open('/Volumes/xdisc/_scratch/midi.mid', 'wb')
    >>> #_DOCS_SHOW mf.write()
    >>> #_DOCS_SHOW mf.close()  
    '''
    from music21 import midi as midiModule

    s = inputM21
    midiTracks = streamHierarchyToMidiTracks(s)

    # update track indices
    # may need to update channel information
    for i in range(len(midiTracks)):
        midiTracks[i].index = i + 1

    mf = midiModule.MidiFile()
    mf.tracks = midiTracks
    mf.ticksPerQuarterNote = defaults.ticksPerQuarter
    return mf


def midiFilePathToStream(filePath, inputM21=None):
    '''
    Used by music21.converter:
    
    Take in a file path (name of a file on disk) and using `midiFileToStream`, 
    
    return a :class:`~music21.stream.Score` object (or if inputM21 is passed in,
    use that object instead).
    
    >>> import os #_DOCS_HIDE
    >>> fp = os.path.join(common.getSourceFilePath(), 'midi', 'testPrimitive',  'test05.mid') #_DOCS_HIDE
    >>> #_DOCS_SHOW fp = '/Users/test/music21/midi/testPrimitive/test05.mid'
    >>> streamScore = midi.translate.midiFilePathToStream(fp)
    >>> streamScore
    <music21.stream.Score ...>
    '''
    from music21 import midi as midiModule
    mf = midiModule.MidiFile()
    mf.open(filePath)
    mf.read()
    mf.close()
    return midiFileToStream(mf, inputM21)


def midiAsciiStringToBinaryString(midiFormat = 1, ticksPerQuarterNote = 960, tracksEventsList = None):
    r'''
    Convert Ascii midi data to a binary midi string.
    
    tracksEventsList contains a list of tracks which contain also a list of events.
    
        asciiMidiEventList = ['0 90 27 66', '0 90 3e 60', '3840 80 27 00', '0 80 3e 00']
    
    The format of one event is : 'aa bb cc dd'::
    
        aa = delta time to last event (integer)
        bb = Midi event type
        cc = Note number (hex)
        dd = Velocity (integer)

    Example:
    
    >>> asciiMidiEventList = []
    >>> asciiMidiEventList.append('0 90 31 15')
    >>> midiTrack = []
    >>> midiTrack.append(asciiMidiEventList)
    >>> midiBinStr = midi.translate.midiAsciiStringToBinaryString(tracksEventsList = midiTrack)
    >>> midiBinStr
    b'MThd\x00\x00\x00\x06\x00\x01\x00\x01\x03\xc0MTrk\x00\x00\x00\x04\x00\x901\x0f'
    '''
    from music21 import midi as midiModule
    mf = midiModule.MidiFile()
    
    numTracks = len(tracksEventsList)

    if (numTracks == 1):
        mf.format = 1
    else:
        mf.format = midiFormat
        
    mf.ticksPerQuarterNote = ticksPerQuarterNote

    if (tracksEventsList != None):
        for i in range(numTracks):
            trk = midiModule.MidiTrack(i)   # sets the MidiTrack index parameters
            for j in tracksEventsList[i]:
                me = midiModule.MidiEvent(trk)
                dt = midiModule.DeltaTime(trk)
                
                chunk_event_param = str(j).split(" ")

                dt.channel = i + 1
                dt.time = int(chunk_event_param[0])

                me.channel = i + 1
                me.pitch = int(chunk_event_param[2], 16)
                me.velocity = int(chunk_event_param[3])

                valid = False
                if (chunk_event_param[1] != "FF") :
                    if (list(chunk_event_param[1])[0] == '8'):
                        me.type = "NOTE_OFF"
                        valid = True
                    elif (list(chunk_event_param[1])[0] == '9'):
                        valid = True
                        me.type = "NOTE_ON"
                    else:
                        environLocal.warn("Unsupported midi event: 0x%s" % (chunk_event_param[1]))     
                else:
                    environLocal.warn("Unsupported meta event: 0x%s" % (chunk_event_param[1])) 
                                        
                if valid == True:
                    trk.events.append(dt)
                    trk.events.append(me)
                                
            mf.tracks.append(trk) 

    midiBinStr = b""
    midiBinStr = midiBinStr + mf.writestr()
    
    return midiBinStr

## not working 
def midiStringToStream(strData):
    r'''
    Convert a string of binary midi data to a Music21 stream.Score object.

    TODO: NOT WORKING AS IT SHOULD 
         
#     >>> midiBinStr = 'MThd\x00\x00\x00\x06\x00\x01\x00\x01\x03\xc0MTrk\x00\x00\x00\x04\x00\x901\x0f'
# 
#     >>> s = midi.translate.midiStringToStream(midiBinStr)
#     >>> s.show('text')
#     {0.0} <music21.stream.Part ...>
#         {0.0} <music21.note.Note G>                
# 
    '''
    from music21 import midi as midiModule
     
    mf = midiModule.MidiFile()
    # do not need to call open or close on MidiFile instance
    mf.readstr(strData)
    return midiFileToStream(mf)


def midiFileToStream(mf, inputM21=None, quantizePost=True):
    '''
    Convert a :class:`~music21.midi.base.MidiFile` object to a 
    :class:`~music21.stream.Stream` object.
    
    The `inputM21` object can specify an existing Stream (or Stream subclass) to fill.

    >>> import os
    >>> fp = os.path.join(common.getSourceFilePath(), 'midi', 'testPrimitive',  'test05.mid')
    >>> mf = midi.MidiFile()
    >>> mf.open(fp)
    >>> mf.read()
    >>> mf.close()
    >>> len(mf.tracks)
    1
    >>> s = midi.translate.midiFileToStream(mf)
    >>> s
    <music21.stream.Score ...>
    >>> len(s.flat.notesAndRests)
    11
    '''
    #environLocal.printDebug(['got midi file: tracks:', len(mf.tracks)])

    from music21 import stream
    if inputM21 == None:
        s = stream.Score()
    else:
        s = inputM21

    if len(mf.tracks) == 0:
        raise exceptions21.StreamException('no tracks are defined in this MIDI file.')
    else:
        # create a stream for each tracks   
        # may need to check if tracks actually have event data
        midiTracksToStreams(mf.tracks, 
            ticksPerQuarter=mf.ticksPerQuarterNote, quantizePost=quantizePost, inputM21=s)
        #s._setMidiTracks(mf.tracks, mf.ticksPerQuarterNote)

    return s


#-------------------------------------------------------------------------------
class Test(unittest.TestCase):
    
    def runTest(self):
        pass
    
    def testMidiAsciiStringToBinaryString(self):
        from binascii import a2b_hex
        
        asciiMidiEventList = []
        asciiMidiEventList.append('0 90 1f 15')
        #asciiMidiEventList.append('3840 80 1f 15')
        #asciiMidiEventList.append('0 b0 7b 00')
        
        #asciiMidiEventList = ['0 90 27 66', '3840 80 27 00']
        #asciiMidiEventList = ['0 90 27 66', '0 90 3e 60', '3840 80 27 00', '0 80 3e 00', '0 90 3b 60', '960 80 3b 00', '0 90 41 60', '960 80 41 00', '0 90 3e 60', '1920 80 3e 00', '0 b0 7b 00', '0 90 24 60', '3840 80 24 00', '0 b0 7b 00']
        #asciiMidiEventList = ['0 90 27 66', '0 90 3e 60', '3840 80 27 00', '0 80 3e 00', '0 90 3b 60', '960 80 3b 00', '0 90 41 60', '960 80 41 00', '0 90 3e 60', '1920 80 3e 00', '0 90 24 60', '3840 80 24 00']
        
        midiTrack = []
        midiTrack.append(asciiMidiEventList)
        #midiTrack.append(asciiMidiEventList)
        #midiTrack.append(asciiMidiEventList)
        
        midiBinStr = midiAsciiStringToBinaryString(tracksEventsList = midiTrack)
        
        self.assertEqual(midiBinStr, b"MThd"+ a2b_hex("000000060001000103c0") + b"MTrk" + a2b_hex("0000000400901f0f")) 

    def testNote(self):
        from music21 import midi as midiModule

        from music21 import note
        n1 = note.Note('A4')
        n1.quarterLength = 2.0
        eventList = noteToMidiEvents(n1)
        self.assertEqual(len(eventList), 4)

        self.assertEqual(isinstance(eventList[0], midiModule.DeltaTime), True)
        self.assertEqual(isinstance(eventList[2], midiModule.DeltaTime), True)

        # translate eventList back to a note
        n2 = midiEventsToNote(eventList)
        self.assertEqual(n2.pitch.nameWithOctave, 'A4')
        self.assertEqual(n2.quarterLength, 2.0)

    def testTimeSignature(self):
        from music21 import note, stream, meter
        n = note.Note()
        n.quarterLength = .5
        s = stream.Stream()
        for i in range(20):
            s.append(copy.deepcopy(n))

        s.insert(0, meter.TimeSignature('3/4'))
        s.insert(3, meter.TimeSignature('5/4'))
        s.insert(8, meter.TimeSignature('2/4'))

        
        mt = streamHierarchyToMidiTracks(s)[0]
        #self.assertEqual(str(mt.events), match)
        self.assertEqual(len(mt.events), 92)

        #s.show('midi')
        
        # get and compare just the time signatures
        mtAlt = streamHierarchyToMidiTracks(s.getElementsByClass('TimeSignature'))[0]

        match = """[<MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent SEQUENCE_TRACK_NAME, t=0, track=1, channel=1, data=''>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent PITCH_BEND, t=0, track=1, channel=1, _parameter1=0, _parameter2=64>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent TIME_SIGNATURE, t=0, track=1, channel=1, data='\\x03\\x02\\x18\\x08'>, <MidiEvent DeltaTime, t=3072, track=1, channel=1>, <MidiEvent TIME_SIGNATURE, t=0, track=1, channel=1, data='\\x05\\x02\\x18\\x08'>, <MidiEvent DeltaTime, t=5120, track=1, channel=1>, <MidiEvent TIME_SIGNATURE, t=0, track=1, channel=1, data='\\x02\\x02\\x18\\x08'>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent END_OF_TRACK, t=None, track=1, channel=1, data=''>]"""
        self.assertEqual(str(mtAlt.events), match)

    def testKeySignature(self):
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

        mt = streamHierarchyToMidiTracks(s)[0]
        self.assertEqual(len(mt.events), 98)

        #s.show('midi')
        unused_mtAlt = streamHierarchyToMidiTracks(s.getElementsByClass('TimeSignature'))[0]

    def testAnacrusisTiming(self):

        from music21 import corpus

        s = corpus.parse('bach/bwv103.6')

        # get just the soprano part
        soprano = s.parts['soprano']
        mts = streamHierarchyToMidiTracks(soprano)[0] # get one

        # first note-on is not delayed, even w anacrusis
        match = """[<MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent SEQUENCE_TRACK_NAME, t=0, track=1, channel=1, data='Soprano'>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent PROGRAM_CHANGE, t=0, track=1, channel=1, data=0>, <MidiEvent DeltaTime, t=0, track=1, channel=1>]"""
       
        self.maxDiff = None
        if six.PY2:
            mts.events[1].data = mts.events[1].data.encode('ascii') # unicode fix
        self.assertEqual(str(mts.events[:5]), match)

        # first note-on is not delayed, even w anacrusis
        match = """[<MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent SEQUENCE_TRACK_NAME, t=0, track=1, channel=1, data='Alto'>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent PROGRAM_CHANGE, t=0, track=1, channel=1, data=0>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent PITCH_BEND, t=0, track=1, channel=1, _parameter1=0, _parameter2=64>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent PROGRAM_CHANGE, t=0, track=1, channel=1, data=0>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent KEY_SIGNATURE, t=0, track=1, channel=1, data='\\x02\\x01'>]"""

        alto = s.parts['alto']
        mta = streamHierarchyToMidiTracks(alto)[0]

        if six.PY2:
            mta.events[1].data = mta.events[1].data.encode('ascii') # unicode fix

        self.assertEqual(str(mta.events[:10]), match)

        # try streams to midi tracks
        # get just the soprano part
        soprano = s.parts['soprano']
        mtList = streamHierarchyToMidiTracks(soprano)
        self.assertEqual(len(mtList), 1)

        # its the same as before
        match = """[<MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent SEQUENCE_TRACK_NAME, t=0, track=1, channel=1, data='Soprano'>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent PROGRAM_CHANGE, t=0, track=1, channel=1, data=0>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent PITCH_BEND, t=0, track=1, channel=1, _parameter1=0, _parameter2=64>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent PROGRAM_CHANGE, t=0, track=1, channel=1, data=0>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent KEY_SIGNATURE, t=0, track=1, channel=1, data='\\x02\\x01'>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent TIME_SIGNATURE, t=0, track=1, channel=1, data='\\x04\\x02\\x18\\x08'>]"""
        if six.PY2:
            mtList[0].events[1].data = mtList[0].events[1].data.encode('ascii') # unicode fix

        self.assertEqual(str(mtList[0].events[:12]), match)

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

        unused_mts = streamHierarchyToMidiTracks(s)
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

        unused_mts = streamHierarchyToMidiTracks(s)

        #s.show('midi')

    def testOverlappedEventsA(self):
        from music21 import corpus
        s = corpus.parse('bwv66.6')
        sFlat = s.flat
        mtList = streamHierarchyToMidiTracks(sFlat)
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

        unused_mt = streamHierarchyToMidiTracks(s)[0]

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
        c.pitches[1].microtone = -50
        s.append(c)

        pos = s.highestTime
        s.insert(pos, note.Note('e'))
        s.insert(pos, note.Note('b'))

        unused_mt = streamHierarchyToMidiTracks(s)[0]

        #s.show('midi')

    def testExternalMidiProgramChangeB(self):

        from music21 import stream, instrument, note, scale

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

 
        unused_mts = streamHierarchyToMidiTracks(s)
        #s.show('midi')

        

    def testMicrotonalOutputA(self):
        from music21 import stream, note

        s = stream.Stream()
        s.append(note.Note('c4', type='whole')) 
        s.append(note.Note('c~4', type='whole')) 
        s.append(note.Note('c#4', type='whole')) 
        s.append(note.Note('c#~4', type='whole')) 
        s.append(note.Note('d4', type='whole')) 

        #mts = streamHierarchyToMidiTracks(s)

        s.insert(0, note.Note('g3', quarterLength=10)) 
        unused_mts = streamHierarchyToMidiTracks(s)

#         match = """[<MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent NOTE_ON, t=0, track=1, channel=1, pitch=61, velocity=90>, <MidiEvent DeltaTime, t=2048, track=1, channel=1>, <MidiEvent NOTE_OFF, t=0, track=1, channel=1, pitch=61, velocity=0>, <MidiEvent DeltaTime, t=0, track=1, channel=2>, <MidiEvent PITCH_BEND, t=0, track=1, channel=2, _parameter1=0, _parameter2=80>, <MidiEvent DeltaTime, t=0, track=1, channel=2>, <MidiEvent NOTE_ON, t=0, track=1, channel=2, pitch=61, velocity=90>, <MidiEvent DeltaTime, t=2048, track=1, channel=2>, <MidiEvent NOTE_OFF, t=0, track=1, channel=2, pitch=61, velocity=0>, <MidiEvent DeltaTime, t=0, track=1, channel=2>, <MidiEvent PITCH_BEND, t=0, track=1, channel=2, _parameter1=0, _parameter2=64>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent NOTE_ON, t=0, track=1, channel=1, pitch=62, velocity=90>, <MidiEvent DeltaTime, t=2048, track=1, channel=1>, <MidiEvent NOTE_OFF, t=0, track=1, channel=1, pitch=55, velocity=0>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent NOTE_OFF, t=0, track=1, channel=1, pitch=62, velocity=0>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent END_OF_TRACK, t=None, track=1, channel=1, data=''>]"""
#         self.assertEqual(str(mts[0].events[-20:]), match)
# 
# 
#         #s.show('midi', app='Logic Express')
#         s.show('midi')

        #print(s.write('midi'))
    def testMicrotonalOutputB(self):
        # a two-part stream
        from music21 import stream, note

        p1 = stream.Part()
        p1.append(note.Note('c4', type='whole')) 
        p1.append(note.Note('c~4', type='whole')) 
        p1.append(note.Note('c#4', type='whole')) 
        p1.append(note.Note('c#~4', type='whole')) 
        p1.append(note.Note('d4', type='whole')) 

        #mts = streamHierarchyToMidiTracks(s)
        p2 = stream.Part()
        p2.insert(0, note.Note('g2', quarterLength=20)) 

        # order here matters: this needs to be fixed
        s = stream.Score()
        s.insert(0, p1)
        s.insert(0, p2)

        mts = streamHierarchyToMidiTracks(s)
        self.assertEqual(mts[0].getChannels(),  [1])
        self.assertEqual(mts[1].getChannels(),  [1, 2])
        #print(mts)
        #s.show('midi', app='Logic Express')
        #s.show('midi')

        # recreate with different order
        s = stream.Score()
        s.insert(0, p2)
        s.insert(0, p1)

        mts = streamHierarchyToMidiTracks(s)
        self.assertEqual(mts[0].getChannels(),  [1])
        self.assertEqual(mts[1].getChannels(),  [1, 2])

    def testMicrotonalOutputC(self):
        # test instrument assignments
        from music21 import instrument, stream, note

        iList = [instrument.Harpsichord,  instrument.Viola, 
                    instrument.ElectricGuitar, instrument.Flute]

        # number of notes, ql, pitch
        pmtr = [(8, 1, 'C6'), (4, 2, 'G3'), (2, 4, 'E4'), (6, 1.25, 'C5')]

        s = stream.Score()
        for i, inst in enumerate(iList):
            p = stream.Part()
            p.insert(0, inst()) # must call instrument to create instance

            number, ql, pitchName = pmtr[i]
            for j in range(number):
                p.append(note.Note(pitchName, quarterLength=ql))
            s.insert(0, p)

        #s.show('midi')
        mts = streamHierarchyToMidiTracks(s)
        #print(mts[0])
        self.assertEqual(mts[0].getChannels(),  [1])
        self.assertEqual(mts[1].getChannels(),  [2])
        self.assertEqual(mts[2].getChannels(),  [3])
        self.assertEqual(mts[3].getChannels(),  [4])

    def testMicrotonalOutputD(self):
        # test instrument assignments with microtones
        from music21 import instrument, stream, note

        iList = [instrument.Harpsichord,  instrument.Viola, 
                    instrument.ElectricGuitar, instrument.Flute]

        # number of notes, ql, pitch
        pmtr = [(8, 1, ['C6']), (4, 2, ['G3', 'G~3']), (2, 4, ['E4', 'E5']), (6, 1.25, ['C5'])]

        s = stream.Score()
        for i, inst in enumerate(iList):
            p = stream.Part()
            p.insert(0, inst()) # must call instrument to create instance

            number, ql, pitchNameList = pmtr[i]
            for j in range(number):
                p.append(note.Note(pitchNameList[j%len(pitchNameList)], quarterLength=ql))
            s.insert(0, p)

        #s.show('midi')
        mts = streamHierarchyToMidiTracks(s)
        #print(mts[0])
        self.assertEqual(mts[0].getChannels(),  [1])
        self.assertEqual(mts[0].getProgramChanges(),  [6])

        self.assertEqual(mts[1].getChannels(),  [2, 5])
        self.assertEqual(mts[1].getProgramChanges(),  [41])

        self.assertEqual(mts[2].getChannels(),  [3, 6])
        self.assertEqual(mts[2].getProgramChanges(),  [26])
        #print(mts[2])

        self.assertEqual(mts[3].getChannels(),  [4, 6])
        self.assertEqual(mts[3].getProgramChanges(),  [73])

        #s.show('midi')

    def testMicrotonalOutputE(self):

        from music21 import corpus, stream, interval
        s = corpus.parse('bwv66.6')
        p1 = s.parts[0]
        p2 = copy.deepcopy(p1)
        t = interval.Interval(0.5) # a sharp p4
        p2.transpose(t, inPlace=True)
        post = stream.Score()
        post.insert(0, p1)
        post.insert(0, p2)

        #post.show('midi')

        mts = streamHierarchyToMidiTracks(post)
        self.assertEqual(mts[0].getChannels(),  [1])
        self.assertEqual(mts[0].getProgramChanges(),  [0])
        self.assertEqual(mts[1].getChannels(),  [1, 2])
        self.assertEqual(mts[1].getProgramChanges(),  [0])

        #post.show('midi', app='Logic Express')

    def testMicrotonalOutputF(self):

        from music21 import corpus, stream, interval
        s = corpus.parse('bwv66.6')
        p1 = s.parts[0]
        p2 = copy.deepcopy(p1)
        p3 = copy.deepcopy(p1)

        t1 = interval.Interval(12.5) # a sharp p4
        t2 = interval.Interval(-12.25) # a sharp p4
        p2.transpose(t1, inPlace=True)
        p3.transpose(t2, inPlace=True)
        post = stream.Score()
        post.insert(0, p1)
        post.insert(0, p2)
        post.insert(0, p3)

        #post.show('midi')

        mts = streamHierarchyToMidiTracks(post)
        self.assertEqual(mts[0].getChannels(),  [1])
        self.assertEqual(mts[0].getProgramChanges(),  [0])
        self.assertEqual(mts[1].getChannels(),  [1, 2])
        self.assertEqual(mts[1].getProgramChanges(),  [0])
        self.assertEqual(mts[2].getChannels(),  [1, 2, 3])
        self.assertEqual(mts[2].getProgramChanges(),  [0])

        #post.show('midi', app='Logic Express')

    def testMicrotonalOutputG(self):

        from music21 import corpus, stream, interval, instrument
        s = corpus.parse('bwv66.6')
        p1 = s.parts[0]
        p1.remove(p1.getElementsByClass('Instrument')[0])
        p2 = copy.deepcopy(p1)
        p3 = copy.deepcopy(p1)
        
        t1 = interval.Interval(12.5) # a sharp p4
        t2 = interval.Interval(-7.25) # a sharp p4
        p2.transpose(t1, inPlace=True)
        p3.transpose(t2, inPlace=True)
        post = stream.Score()
        p1.insert(0, instrument.Dulcimer())
        post.insert(0, p1)
        p2.insert(0, instrument.Trumpet())
        post.insert(0.125, p2)
        p3.insert(0, instrument.ElectricGuitar())
        post.insert(0.25, p3)
        
        #post.show('midi')
        
        mts = streamHierarchyToMidiTracks(post)
        self.assertEqual(mts[0].getChannels(),  [1])
        self.assertEqual(mts[0].getProgramChanges(),  [15])
        
        self.assertEqual(mts[1].getChannels(),  [2, 4])
        self.assertEqual(mts[1].getProgramChanges(),  [56])
        
        #print(mts[2])
        self.assertEqual(mts[2].getChannels(),  [3, 4, 5])
        self.assertEqual(mts[2].getProgramChanges(),  [26])

        #post.show('midi', app='Logic Express')

    def testMidiTempoImportA(self):
        import os
        from music21 import converter

        directory = common.getPackageDir(relative=False, remapSep=os.sep)
        for fp in directory:
            if fp.endswith('midi'):
                break
        else:
            fp = None
        dirLib = os.path.join(fp, 'testPrimitive')
        # a simple file created in athenacl
        fp = os.path.join(dirLib, 'test10.mid')        
        s = converter.parse(fp)
        mmStream = s.flat.getElementsByClass('MetronomeMark')
        self.assertEqual(len(mmStream), 4)
        self.assertEqual(mmStream[0].number, 120.0)        
        self.assertEqual(mmStream[1].number, 110.0)        
        self.assertEqual(mmStream[2].number, 90.0)        
        self.assertEqual(mmStream[3].number, 60.0)        
    

        fp = os.path.join(dirLib, 'test06.mid')        
        s = converter.parse(fp)
        mmStream = s.flat.getElementsByClass('MetronomeMark')
        self.assertEqual(len(mmStream), 1)
        self.assertEqual(mmStream[0].number, 120.0)        

        fp = os.path.join(dirLib, 'test07.mid')        
        s = converter.parse(fp)
        mmStream = s.flat.getElementsByClass('MetronomeMark')
        self.assertEqual(len(mmStream), 1)
        self.assertEqual(mmStream[0].number, 180.0)        

    def testMidiTempoImportB(self):
        import os
        from music21 import converter

        directory = common.getPackageDir(relative=False, remapSep=os.sep)
        for fp in directory:
            if fp.endswith('midi'):
                break
        else:
            fp = None
        dirLib = os.path.join(fp, 'testPrimitive')
        # a file with three tracks and one conductor track
        fp = os.path.join(dirLib, 'test11.mid')        
        s = converter.parse(fp)
        self.assertEqual(len(s.parts), 3)
        # metronome marks end up only on the top-most staff
        self.assertEqual(len(s.parts[0].getElementsByClass('MetronomeMark')), 4)
        self.assertEqual(len(s.parts[1].getElementsByClass('MetronomeMark')), 0)
        self.assertEqual(len(s.parts[2].getElementsByClass('MetronomeMark')), 0)

    def testMidiExportConductorA(self):
        '''Testing exporting conductor data to midi
        '''
        from music21 import stream, note, meter, tempo

        p1 = stream.Part()
        p1.repeatAppend(note.Note('c4'), 12)
        p1.insert(0, meter.TimeSignature('3/4'))
        p1.insert(0, tempo.MetronomeMark(number=90))
        p1.insert(6, tempo.MetronomeMark(number=30))

        p2 = stream.Part()
        p2.repeatAppend(note.Note('g4'), 12)    
        p2.insert(6, meter.TimeSignature('6/4'))

        s = stream.Score()
        s.insert([0, p1, 0, p2])     

        mts = streamHierarchyToMidiTracks(s)
        mtsRepr = repr(mts)
        self.assertEqual(mtsRepr.find('SET_TEMPO') > 0, True)
        self.assertEqual(mtsRepr.find('TIME_SIGNATURE') > 0, True)

        #s.show('midi')
        #s.show('midi', app='Logic Express')

    def testMidiExportConductorB(self):
        from music21 import tempo, corpus
        s = corpus.parse('bwv66.6')
        s.insert(0, tempo.MetronomeMark(number=240))
        s.insert(4, tempo.MetronomeMark(number=30))
        s.insert(6, tempo.MetronomeMark(number=120))
        s.insert(8, tempo.MetronomeMark(number=90))
        s.insert(12, tempo.MetronomeMark(number=360))
        #s.show('midi')
        
        mts = streamHierarchyToMidiTracks(s)
        mtsRepr = repr(mts)
        self.assertEqual(mtsRepr.count('SET_TEMPO'), 5)

    def testMidiExportConductorC(self):
        from music21 import tempo, note, stream
        minTempo = 60
        maxTempo = 600
        period = 50
        s = stream.Stream()
        for i in range(100):
            scalar = (math.sin(i * (math.pi*2) / period) + 1) * .5
            n = ((maxTempo - minTempo) * scalar) + minTempo
            s.append(tempo.MetronomeMark(number=n))
            s.append(note.Note('g3'))
        mts = streamHierarchyToMidiTracks(s)
        mtsRepr = repr(mts)
        self.assertEqual(mtsRepr.count('SET_TEMPO'), 100)

    def testMidiExportVelocityA(self):
        from music21 import note, stream

        s = stream.Stream()
        for i in range(10):
            #print(i)
            n = note.Note('c3')
            n.volume.velocityScalar = i/10.
            n.volume.velocityIsRelative = False
            s.append(n)

        #s.show('midi')        
        mts = streamHierarchyToMidiTracks(s)
        mtsRepr = repr(mts)
        #print(mtsRepr)
        self.assertEqual(mtsRepr.count('velocity=114'), 1)
        self.assertEqual(mtsRepr.count('velocity=13'), 1)
        
    def testMidiExportVelocityB(self):
        import random
        from music21 import stream, chord, note, volume
        
        s1 = stream.Stream()
        shift = [0, 6, 12]
        amps = [(x/10. + .4) for x in range(6)]
        amps = amps + list(reversed(amps))
        
        qlList = [1.5] * 6 + [1] * 8 + [2] * 6 + [1.5] * 8 + [1] * 4 
        for j, ql in enumerate(qlList):
            if random.random() > .6:
                c = note.Rest()
            else:
                c = chord.Chord(['c3', 'd-4', 'g5'])
                vChord = []
                for i, unused_cSub in enumerate(c):
                    v = volume.Volume()
                    v.velocityScalar = amps[(j+shift[i]) % len(amps)]
                    v.velocityIsRelative = False
                    vChord.append(v)
                c.volume = vChord # can set to list
            c.duration.quarterLength = ql
            s1.append(c)
        
        s2 = stream.Stream()
        random.shuffle(qlList)
        random.shuffle(amps)
        for j, ql in enumerate(qlList):
            n = note.Note(random.choice(['f#2', 'f#2', 'e-2']))
            n.duration.quarterLength = ql
            n.volume.velocityScalar = amps[j%len(amps)]
            s2.append(n)
        
        s = stream.Score()
        s.insert(0, s1)
        s.insert(0, s2)

        mts = streamHierarchyToMidiTracks(s)
        mtsRepr = repr(mts)
        self.assertEqual(mtsRepr.count('velocity=51') > 2, True)
        self.assertEqual(mtsRepr.count('velocity=102') > 2, True)
        #s.show('midi')

    def testImportTruncationProblemA(self):
        import os
        from music21 import converter

        # specialized problem of not importing last notes
        directory = common.getPackageDir(relative=False, remapSep=os.sep)
        for fp in directory:
            if fp.endswith('midi'):
                break
        else:
            fp = None
        dirLib = os.path.join(fp, 'testPrimitive')
        # a simple file created in athenacl
        fp = os.path.join(dirLib, 'test12.mid')
        s = converter.parse(fp)
        
        self.assertEqual(len(s.parts[0].flat.notes), 3)
        self.assertEqual(len(s.parts[1].flat.notes), 3)
        self.assertEqual(len(s.parts[2].flat.notes), 3)        
        self.assertEqual(len(s.parts[3].flat.notes), 3)

        #s.show('t')
        #s.show('midi')

    def testImportChordVoiceA(self):
        # looking at cases where notes appear to be chord but 
        # are better seen as voices

        import os
        from music21 import converter
        # specialized problem of not importing last notes
        directory = common.getPackageDir(relative=False, remapSep=os.sep)
        for fp in directory:
            if fp.endswith('midi'):
                break
        else:
            fp = None
        fpMidi = fp
        fp = os.path.join(fpMidi, 'testPrimitive', 'test13.mid')
        s = converter.parse(fp)
        #s.show('t')
        self.assertEqual(len(s.flat.notes), 7)
        #s.show('midi')

        fp = os.path.join(fpMidi, 'testPrimitive', 'test14.mid')
        s = converter.parse(fp)
        # three chords will be created, as well as two voices
        self.assertEqual(len(s.flat.getElementsByClass('Chord')), 3)
        self.assertEqual(len(s.parts[0].voices), 2)

    def testImportChordsA(self):
        import os
        from music21 import converter

        directory = common.getPackageDir(relative=False, remapSep=os.sep)
        for fp in directory:
            if fp.endswith('midi'):
                break
        else:
            fp = None
        dirLib = os.path.join(fp, 'testPrimitive')
        # a simple file created in athenacl
        fp = os.path.join(dirLib, 'test05.mid')        
        s = converter.parse(fp)
        #s.show('t')
        self.assertEqual(len(s.flat.getElementsByClass('Chord')), 4)
        

#-------------------------------------------------------------------------------
_DOC_ORDER = [streamToMidiFile, midiFileToStream]

if __name__ == "__main__":
    import music21
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof

