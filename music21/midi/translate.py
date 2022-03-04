# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         midi.translate.py
# Purpose:      Translate MIDI and music21 objects
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2010-2015, 2019 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
Module to translate MIDI data to music21 Streams and vice versa.  Note that quantization of
notes takes place in the :meth:`~music21.stream.Stream.quantize` method not here.
'''
import unittest
import math
import copy
from typing import Optional, List, Tuple, Dict, Union, Any
import warnings

from music21 import chord
from music21 import common
from music21 import defaults
from music21 import duration
from music21 import exceptions21
from music21 import environment
from music21 import instrument
from music21 import key
from music21 import note
from music21 import percussion
from music21 import pitch
from music21 import stream

from music21.instrument import Conductor, deduplicate
from music21.midi.percussion import MIDIPercussionException, PercussionMapper

_MOD = 'midi.translate'
environLocal = environment.Environment(_MOD)
PERCUSSION_MAPPER = PercussionMapper()


# ------------------------------------------------------------------------------
class TranslateException(exceptions21.Music21Exception):
    pass


class TranslateWarning(UserWarning):
    pass

# ------------------------------------------------------------------------------
# Durations


def offsetToMidiTicks(o, addStartDelay=False):
    '''
    Helper function to convert a music21 offset value to MIDI ticks,
    depends on *defaults.ticksPerQuarter* and *defaults.ticksAtStart*.

    Returns an int.

    >>> defaults.ticksPerQuarter
    1024
    >>> defaults.ticksAtStart
    1024


    >>> midi.translate.offsetToMidiTicks(0)
    0
    >>> midi.translate.offsetToMidiTicks(0, addStartDelay=True)
    1024

    >>> midi.translate.offsetToMidiTicks(1)
    1024

    >>> midi.translate.offsetToMidiTicks(20.5)
    20992
    '''
    ticks = int(round(o * defaults.ticksPerQuarter))
    if addStartDelay:
        ticks += defaults.ticksAtStart
    return ticks


def durationToMidiTicks(d):
    # noinspection PyShadowingNames
    '''
    Converts a :class:`~music21.duration.Duration` object to midi ticks.

    Depends on *defaults.ticksPerQuarter*, Returns an int.
    Does not use defaults.ticksAtStart


    >>> n = note.Note()
    >>> n.duration.type = 'half'
    >>> midi.translate.durationToMidiTicks(n.duration)
    2048

    >>> d = duration.Duration('quarter')
    >>> dReference = midi.translate.ticksToDuration(1024, inputM21DurationObject=d)
    >>> dReference is d
    True
    >>> d.type
    'quarter'
    >>> d.type = '16th'
    >>> d.quarterLength
    0.25
    >>> midi.translate.durationToMidiTicks(d)
    256
    '''
    return int(round(d.quarterLength * defaults.ticksPerQuarter))


def ticksToDuration(ticks, ticksPerQuarter=None, inputM21DurationObject=None):
    # noinspection PyShadowingNames
    '''
    Converts a number of MIDI Ticks to a music21 duration.Duration() object.

    Optional parameters include ticksPerQuarter -- in case something other
    than the default.ticksPerQuarter (1024) is used in this file.  And
    it can take a :class:`~music21.duration.Duration` object to modify, specified
    as *inputM21DurationObject*

    >>> d = midi.translate.ticksToDuration(1024)
    >>> d
    <music21.duration.Duration 1.0>
    >>> d.type
    'quarter'

    >>> n = note.Note()
    >>> midi.translate.ticksToDuration(3072, inputM21DurationObject=n.duration)
    <music21.duration.Duration 3.0>
    >>> n.duration.type
    'half'
    >>> n.duration.dots
    1

    More complex rhythms can also be set automatically:

    >>> d2 = duration.Duration()
    >>> d2reference = midi.translate.ticksToDuration(1200, inputM21DurationObject=d2)
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
        d = duration.Duration()
    else:
        d = inputM21DurationObject

    if ticksPerQuarter is None:
        ticksPerQuarter = defaults.ticksPerQuarter

    # given a value in ticks
    d.quarterLength = float(ticks) / ticksPerQuarter
    return d


# ------------------------------------------------------------------------------
# utility functions for getting commonly used event


def getStartEvents(mt=None, channel=1, instrumentObj=None):
    '''
    Returns a list of midi.MidiEvent objects found at the beginning of a track.

    A MidiTrack reference can be provided via the `mt` parameter.

    >>> midi.translate.getStartEvents()
    [<music21.midi.DeltaTime (empty) track=None, channel=1>,
     <music21.midi.MidiEvent SEQUENCE_TRACK_NAME, track=None, channel=1, data=b''>]

    >>> midi.translate.getStartEvents(channel=2, instrumentObj=instrument.Harpsichord())
    [<music21.midi.DeltaTime (empty) track=None, channel=2>,
     <music21.midi.MidiEvent SEQUENCE_TRACK_NAME, track=None, channel=2, data=b'Harpsichord'>,
     <music21.midi.DeltaTime (empty) track=None, channel=2>,
     <music21.midi.MidiEvent PROGRAM_CHANGE, track=None, channel=2, data=6>]

    '''
    from music21 import midi as midiModule
    events = []
    if isinstance(instrumentObj, Conductor):
        return events
    elif instrumentObj is None or instrumentObj.bestName() is None:
        partName = ''
    else:
        partName = instrumentObj.bestName()

    dt = midiModule.DeltaTime(mt, channel=channel)
    events.append(dt)

    me = midiModule.MidiEvent(mt, channel=channel)
    me.type = midiModule.MetaEvents.SEQUENCE_TRACK_NAME
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

    >>> midi.translate.getEndEvents(channel=2)
    [<music21.midi.DeltaTime t=1024, track=None, channel=2>,
     <music21.midi.MidiEvent END_OF_TRACK, track=None, channel=2, data=b''>]
    '''
    from music21 import midi as midiModule

    events = []

    dt = midiModule.DeltaTime(track=mt, channel=channel)
    dt.time = defaults.ticksAtStart
    events.append(dt)

    me = midiModule.MidiEvent(track=mt)
    me.type = midiModule.MetaEvents.END_OF_TRACK
    me.channel = channel
    me.data = ''  # must set data to empty string
    events.append(me)

    return events

# ------------------------------------------------------------------------------
# Multi-object conversion


def music21ObjectToMidiFile(
    music21Object,
    *,
    addStartDelay=False,
) -> 'music21.midi.MidiFile':
    '''
    Either calls streamToMidiFile on the music21Object or
    puts a copy of that object into a Stream (so as
    not to change activeSites, etc.) and calls streamToMidiFile on
    that object.
    '''
    classes = music21Object.classes
    if 'Stream' in classes:
        if music21Object.atSoundingPitch is False:
            music21Object = music21Object.toSoundingPitch()

        return streamToMidiFile(music21Object, addStartDelay=addStartDelay)
    else:
        m21ObjectCopy = copy.deepcopy(music21Object)
        s = stream.Stream()
        s.insert(0, m21ObjectCopy)
        return streamToMidiFile(s, addStartDelay=addStartDelay)


# ------------------------------------------------------------------------------
# Notes

def _constructOrUpdateNotRest(
    eOn: 'music21.midi.MidiEvent',
    tOn: int,
    tOff: int,
    ticksPerQuarter: int,
    *,
    inputM21: Optional[note.NotRest] = None,
    preferredClass: type = note.Note,
) -> note.NotRest:
    '''
    Construct (or edit the duration of) a NotRest subclass, usually
    a note.Note (or a chord.Chord if provided to `preferredClass`).

    If the MidiEvent is on channel 10, then an Unpitched or PercussionChord
    is constructed instead. Raises TypeError if an incompatible object is provided
    for `inputM21`, e.g. a `chord.Chord` when a `percussion.PercussionChord` is needed.
    '''
    if not issubclass(preferredClass, note.NotRest):
        raise TypeError(f'Expected subclass of note.NotRest; got {preferredClass}')

    if eOn.channel == 10:
        if preferredClass in (chord.Chord, percussion.PercussionChord):
            preferredClass = percussion.PercussionChord
        else:
            preferredClass = note.Unpitched

    if (tOff - tOn) != 0:
        if inputM21 is None:
            nr = preferredClass(duration=ticksToDuration(tOff - tOn, ticksPerQuarter))
        else:
            nr = inputM21
            nr.duration = ticksToDuration(tOff - tOn, ticksPerQuarter, nr.duration)
    else:
        # here we are handling an issue that might arise with double-stemmed notes
        # environLocal.printDebug(['cannot translate found midi event with zero duration:', eOn, n])
        # for now, substitute grace note
        if inputM21 is None:
            nr = preferredClass()
        else:
            nr = inputM21
        nr.getGrace(inPlace=True)

    return nr


def midiEventsToNote(
    eventList,
    ticksPerQuarter=None,
    inputM21: Optional[note.NotRest] = None,
) -> Optional[note.NotRest]:
    # noinspection PyShadowingNames
    '''
    Convert from a list of midi.DeltaTime and midi.MidiEvent objects to a music21 Note.

    The list can be presented in one of two forms:

        [deltaTime1, midiEvent1, deltaTime2, midiEvent2]

    or

        [(deltaTime1, midiEvent1), (deltaTime2, midiEvent2)]

    It is assumed, but not checked, that midiEvent2 is an appropriate Note_Off command.  Thus, only
    three elements are really needed.

    The `inputM21` parameter can be a NotRest or None; in the case of None,
    a Note or Unpitched object is created.

    Changed in v.7.3: Returns None if `inputM21` is provided.

    N.B. this takes in a list of music21 MidiEvent objects so see [...] on how to
    convert raw MIDI data to MidiEvent objects

    In this example, we start a NOTE_ON event at offset 1.0 that lasts
    for 2.0 quarter notes until we
    send a zero-velocity NOTE_ON (=NOTE_OFF) event for the same pitch.

    >>> mt = midi.MidiTrack(1)
    >>> dt1 = midi.DeltaTime(mt)
    >>> dt1.time = 1024

    >>> me1 = midi.MidiEvent(mt)
    >>> me1.type = midi.ChannelVoiceMessages.NOTE_ON
    >>> me1.pitch = 45
    >>> me1.velocity = 94

    >>> dt2 = midi.DeltaTime(mt)
    >>> dt2.time = 2048

    >>> me2 = midi.MidiEvent(mt)
    >>> me2.type = midi.ChannelVoiceMessages.NOTE_ON
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

    Changed in v.7.3 -- Returns a :class:`~music21.note.Unpitched` instance if the event
    is on Channel 10.

    >>> me1.channel = 10
    >>> unp = midi.translate.midiEventsToNote([dt1, me1, dt2, me2])
    >>> unp
    <music21.note.Unpitched object at 0x...>

    Access the `storedInstrument`:

    >>> unp.storedInstrument
    <music21.instrument.TomTom 'Tom-Tom'>

    And with values that cannot be translated, a generic
    :class:`~music21.instrument.UnpitchedPercussion` instance is given:

    >>> me1.pitch = 1
    >>> unp = midi.translate.midiEventsToNote([dt1, me1, dt2, me2])
    >>> unp.storedInstrument
    <music21.instrument.UnpitchedPercussion 'Percussion'>
    '''
    if ticksPerQuarter is None:
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
        raise TranslateException(f'cannot handle MIDI event list in the form: {eventList!r}')

    nr = _constructOrUpdateNotRest(
        eOn, tOn, tOff, ticksPerQuarter, inputM21=inputM21, preferredClass=note.Note)

    if isinstance(nr, note.Note):
        nr.pitch.midi = eOn.pitch
    elif isinstance(nr, note.Unpitched):
        try:
            i = PERCUSSION_MAPPER.midiPitchToInstrument(eOn.pitch)
        except MIDIPercussionException:
            # warnings.warn(str(mpe), TranslateWarning)
            i = instrument.UnpitchedPercussion()
        nr.storedInstrument = i
        # TODO: set reasonable displayPitch?

    nr.volume.velocity = eOn.velocity
    nr.volume.velocityIsRelative = False  # not relative coming from MIDI
    # n._midiVelocity = eOn.velocity

    if inputM21 is None:
        return nr
    else:
        return None


def noteToMidiEvents(inputM21, *, includeDeltaTime=True, channel=1):
    # noinspection PyShadowingNames
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
    [<music21.midi.DeltaTime (empty) track=None, channel=1>,
     <music21.midi.MidiEvent NOTE_ON, track=None, channel=1, pitch=61, velocity=90>,
     <music21.midi.DeltaTime t=1024, track=None, channel=1>,
     <music21.midi.MidiEvent NOTE_OFF, track=None, channel=1, pitch=61, velocity=0>]

    >>> n1.duration.quarterLength = 2.5
    >>> eventList = midi.translate.noteToMidiEvents(n1)
    >>> eventList
    [<music21.midi.DeltaTime (empty) track=None, channel=1>,
     <music21.midi.MidiEvent NOTE_ON, track=None, channel=1, pitch=61, velocity=90>,
     <music21.midi.DeltaTime t=2560, track=None, channel=1>,
     <music21.midi.MidiEvent NOTE_OFF, track=None, channel=1, pitch=61, velocity=0>]

    Omitting DeltaTimes:

    >>> eventList2 = midi.translate.noteToMidiEvents(n1, includeDeltaTime=False, channel=9)
    >>> eventList2
    [<music21.midi.MidiEvent NOTE_ON, track=None, channel=9, pitch=61, velocity=90>,
     <music21.midi.MidiEvent NOTE_OFF, track=None, channel=9, pitch=61, velocity=0>]

    Changed in v7 -- made keyword-only.
    '''
    from music21 import midi as midiModule

    n = inputM21

    mt = None  # use a midi track set to None
    eventList = []

    if includeDeltaTime:
        dt = midiModule.DeltaTime(mt, channel=channel)
        # add to track events
        eventList.append(dt)

    me1 = midiModule.MidiEvent(track=mt)
    me1.type = midiModule.ChannelVoiceMessages.NOTE_ON
    me1.channel = channel
    me1.pitch = n.pitch.midi
    if not n.pitch.isTwelveTone():
        me1.centShift = n.pitch.getCentShiftFromMidi()

    # TODO: not yet using dynamics or velocity
    # volScalar = n.volume.getRealized(useDynamicContext=False,
    #         useVelocity=True, useArticulations=False)

    # use cached realized, as realized values should have already been set
    me1.velocity = int(round(n.volume.cachedRealized * 127))

    eventList.append(me1)

    if includeDeltaTime:
        # add note off / velocity zero message
        dt = midiModule.DeltaTime(mt, channel=channel)
        dt.time = durationToMidiTicks(n.duration)
        # add to track events
        eventList.append(dt)

    me2 = midiModule.MidiEvent(track=mt)
    me2.type = midiModule.ChannelVoiceMessages.NOTE_OFF
    me2.channel = channel
    me2.pitch = n.pitch.midi
    if not n.pitch.isTwelveTone():
        me2.centShift = n.pitch.getCentShiftFromMidi()

    me2.velocity = 0  # must be zero
    eventList.append(me2)

    # set correspondence
    me1.correspondingEvent = me2
    me2.correspondingEvent = me1

    return eventList


# ------------------------------------------------------------------------------
# Chords

def midiEventsToChord(
    eventList: List['music21.midi.MidiEvent'],
    ticksPerQuarter: Optional[int] = None,
    inputM21: Optional[chord.ChordBase] = None
) -> Optional[chord.ChordBase]:
    # noinspection PyShadowingNames
    '''
    Creates a Chord from a list of :class:`~music21.midi.DeltaTime`
    and :class:`~music21.midi.MidiEvent` objects.  See midiEventsToNote
    for details.

    All DeltaTime objects except the first (for the first note on)
    and last (for the last note off) are ignored.

    >>> mt = midi.MidiTrack(1)

    >>> dt1 = midi.DeltaTime(mt)
    >>> me1 = midi.MidiEvent(mt)
    >>> me1.type = midi.ChannelVoiceMessages.NOTE_ON
    >>> me1.pitch = 45
    >>> me1.velocity = 94

    >>> dt2 = midi.DeltaTime(mt)
    >>> me2 = midi.MidiEvent(mt)
    >>> me2.type = midi.ChannelVoiceMessages.NOTE_ON
    >>> me2.pitch = 46
    >>> me2.velocity = 94

    >>> dt3 = midi.DeltaTime(mt)
    >>> me3 = midi.MidiEvent(mt)
    >>> me3.type = midi.ChannelVoiceMessages.NOTE_OFF
    >>> me3.pitch = 45
    >>> me3.velocity = 0

    >>> dt4 = midi.DeltaTime(mt)
    >>> dt4.time = 2048

    >>> me4 = midi.MidiEvent(mt)
    >>> me4.type = midi.ChannelVoiceMessages.NOTE_OFF
    >>> me4.pitch = 46
    >>> me4.velocity = 0

    >>> c = midi.translate.midiEventsToChord([dt1, me1, dt2, me2, dt3, me3, dt4, me4])
    >>> c
    <music21.chord.Chord A2 B-2>
    >>> c.duration.quarterLength
    2.0

    Providing fewer than four events won't work.

    >>> c = midi.translate.midiEventsToChord([dt1, me1, me2])
    Traceback (most recent call last):
    music21.midi.translate.TranslateException: fewer than 4 events provided to midiEventsToChord:
    [<music21.midi.DeltaTime (empty) track=1, channel=None>,
        <music21.midi.MidiEvent NOTE_ON, track=1, channel=None, pitch=45, velocity=94>,
        <music21.midi.MidiEvent NOTE_ON, track=1, channel=None, pitch=46, velocity=94>]

    Changed in v.7 -- Uses the last DeltaTime in the list to get the end time.
    Changed in v.7.3 -- Returns a :class:`~music21.percussion.PercussionChord` if
    any event is on channel 10. Returns None if `inputM21` provided.

    >>> me2.channel = 10
    >>> midi.translate.midiEventsToChord([dt1, me1, dt2, me2, dt3, me3, dt4, me4])
    <music21.percussion.PercussionChord [Tom-Tom Hi-Hat Cymbal]>
    '''
    tOn: int = 0  # ticks
    tOff: int = 0  # ticks

    if ticksPerQuarter is None:
        ticksPerQuarter = defaults.ticksPerQuarter

    from music21 import volume
    pitches: List[pitch.Pitch] = []
    volumes = []

    firstOn: Optional['music21.midi.MidiEvent'] = None
    any_channel_10 = False
    # this is a format provided by the Stream conversion of
    # midi events; it pre groups events for a chord together in nested pairs
    # of abs start time and the event object
    if isinstance(eventList, list) and eventList and isinstance(eventList[0], tuple):
        # pairs of pairs
        for onPair, offPair in eventList:
            tOn, eOn = onPair
            if firstOn is None:
                firstOn = eOn
            if eOn.channel == 10:
                any_channel_10 = True
            tOff, unused_eOff = offPair
            p = pitch.Pitch()
            p.midi = eOn.pitch
            pitches.append(p)
            v = volume.Volume(velocity=eOn.velocity)
            v.velocityIsRelative = False  # velocity is absolute coming from
            volumes.append(v)
    # assume it is a flat list
    elif len(eventList) > 3:
        onEvents = eventList[:(len(eventList) // 2)]
        offEvents = eventList[(len(eventList) // 2):]
        # first is always delta time
        tOn = onEvents[0].time
        # second is the MidiEvent NOTE_ON
        firstOn = onEvents[1]
        # use the off time of the last chord member
        # -1 is the event, -2 is the delta time for the event
        tOff = offEvents[-2].time
        # create pitches for the odd on Events:
        for i in range(1, len(onEvents), 2):
            p = pitch.Pitch()
            on_event = onEvents[i]
            if on_event.channel == 10:
                any_channel_10 = True
            p.midi = on_event.pitch
            pitches.append(p)
            v = volume.Volume(velocity=onEvents[i].velocity)
            v.velocityIsRelative = False  # velocity is absolute coming from
            volumes.append(v)
    else:
        raise TranslateException(f'fewer than 4 events provided to midiEventsToChord: {eventList}')

    if any_channel_10:
        preferredClass = percussion.PercussionChord
    else:
        preferredClass = chord.Chord
    c: chord.ChordBase = _constructOrUpdateNotRest(
        firstOn, tOn, tOff, ticksPerQuarter, inputM21=inputM21, preferredClass=preferredClass)

    if isinstance(c, percussion.PercussionChord):
        # Construct note.Unpitched objects
        for midi_pitch in pitches:
            unp = note.Unpitched()
            try:
                i = PERCUSSION_MAPPER.midiPitchToInstrument(midi_pitch)
            except MIDIPercussionException:
                # warnings.warn(str(mpe), TranslateWarning)
                i = instrument.UnpitchedPercussion()
            unp.storedInstrument = i
            c.add(unp)
    else:
        c.pitches = pitches
    c.volume = volumes  # can set a list to volume property

    if inputM21 is None:
        return c
    else:
        return None


def chordToMidiEvents(inputM21, *, includeDeltaTime=True, channel=1):
    # noinspection PyShadowingNames
    '''
    Translates a :class:`~music21.chord.Chord` object to a
    list of base.DeltaTime and base.MidiEvents objects.

    The `channel` can be specified, otherwise channel 1 is assumed.

    See noteToMidiEvents above for more details.

    >>> c = chord.Chord(['c3', 'g#4', 'b5'])
    >>> c.volume = volume.Volume(velocity=90)
    >>> c.volume.velocityIsRelative = False
    >>> eventList = midi.translate.chordToMidiEvents(c)
    >>> eventList
    [<music21.midi.DeltaTime (empty) track=None, channel=None>,
     <music21.midi.MidiEvent NOTE_ON, track=None, channel=1, pitch=48, velocity=90>,
     <music21.midi.DeltaTime (empty) track=None, channel=None>,
     <music21.midi.MidiEvent NOTE_ON, track=None, channel=1, pitch=68, velocity=90>,
     <music21.midi.DeltaTime (empty) track=None, channel=None>,
     <music21.midi.MidiEvent NOTE_ON, track=None, channel=1, pitch=83, velocity=90>,
     <music21.midi.DeltaTime t=1024, track=None, channel=None>,
     <music21.midi.MidiEvent NOTE_OFF, track=None, channel=1, pitch=48, velocity=0>,
     <music21.midi.DeltaTime (empty) track=None, channel=None>,
     <music21.midi.MidiEvent NOTE_OFF, track=None, channel=1, pitch=68, velocity=0>,
     <music21.midi.DeltaTime (empty) track=None, channel=None>,
     <music21.midi.MidiEvent NOTE_OFF, track=None, channel=1, pitch=83, velocity=0>]

    Changed in v7 -- made keyword-only.
    '''
    from music21 import midi as midiModule
    mt = None  # midi track
    eventList = []
    c = inputM21

    # temporary storage for setting correspondence
    noteOn = []
    noteOff = []

    chordVolume = c.volume  # use if component volume are not defined
    hasComponentVolumes = c.hasComponentVolumes()

    for i in range(len(c)):
        chordComponent = c[i]
        # pitchObj = c.pitches[i]
        # noteObj = chordComponent
        if includeDeltaTime:
            dt = midiModule.DeltaTime(track=mt)
            # for a chord, only the first delta time should have the offset
            # here, all are zero
            # leave dt.time at zero; will be shifted later as necessary
            # add to track events
            eventList.append(dt)

        me = midiModule.MidiEvent(track=mt)
        me.type = midiModule.ChannelVoiceMessages.NOTE_ON
        me.channel = 1
        me.pitch = chordComponent.pitch.midi
        if not chordComponent.pitch.isTwelveTone():
            me.centShift = chordComponent.pitch.getCentShiftFromMidi()
        # if 'volume' in chordComponent:

        if hasComponentVolumes:
            # volScalar = chordComponent.volume.getRealized(
            #     useDynamicContext=False,
            #     useVelocity=True, useArticulations=False)
            volScalar = chordComponent.volume.cachedRealized
        else:
            # volScalar = chordVolume.getRealized(
            #     useDynamicContext=False,
            #     useVelocity=True, useArticulations=False)
            volScalar = chordVolume.cachedRealized

        me.velocity = int(round(volScalar * 127))
        eventList.append(me)
        noteOn.append(me)

    # must create each note on in chord before each note on
    for i in range(len(c.pitches)):
        pitchObj = c.pitches[i]

        if includeDeltaTime:
            # add note off / velocity zero message
            dt = midiModule.DeltaTime(track=mt)
            # for a chord, only the first delta time should have the dur
            if i == 0:
                dt.time = durationToMidiTicks(c.duration)
            eventList.append(dt)

        me = midiModule.MidiEvent(track=mt)
        me.type = midiModule.ChannelVoiceMessages.NOTE_OFF
        me.channel = channel
        me.pitch = pitchObj.midi
        if not pitchObj.isTwelveTone():
            me.centShift = pitchObj.getCentShiftFromMidi()
        me.velocity = 0  # must be zero
        eventList.append(me)
        noteOff.append(me)

    # set correspondence
    for i, meOn in enumerate(noteOn):
        meOff = noteOff[i]
        meOn.correspondingEvent = meOff
        meOff.correspondingEvent = meOn

    return eventList


# ------------------------------------------------------------------------------
def instrumentToMidiEvents(inputM21,
                           includeDeltaTime=True,
                           midiTrack=None,
                           channel=1):
    '''
    Converts a :class:`~music21.instrument.Instrument` object to a list of MidiEvents

    TODO: DOCS and TESTS
    '''
    from music21 import midi as midiModule

    inst = inputM21
    mt = midiTrack  # midi track
    events = []

    if isinstance(inst, Conductor):
        return events
    if includeDeltaTime:
        dt = midiModule.DeltaTime(track=mt, channel=channel)
        events.append(dt)
    me = midiModule.MidiEvent(track=mt)
    me.type = midiModule.ChannelVoiceMessages.PROGRAM_CHANGE
    me.channel = channel
    instMidiProgram = inst.midiProgram
    if instMidiProgram is None:
        instMidiProgram = 0
    me.data = instMidiProgram  # key step
    events.append(me)
    return events


# ------------------------------------------------------------------------------
# Meta events

def midiEventsToInstrument(eventList):
    '''
    Convert a single MIDI event into a music21 Instrument object.

    >>> me = midi.MidiEvent()
    >>> me.type = midi.ChannelVoiceMessages.PROGRAM_CHANGE
    >>> me.data = 53  # MIDI program 54: Voice Oohs
    >>> midi.translate.midiEventsToInstrument(me)
    <music21.instrument.Vocalist 'Voice'>

    The percussion map will be used if the channel is 10:

    >>> me.channel = 10
    >>> i = midi.translate.midiEventsToInstrument(me)
    >>> i
    <music21.instrument.UnpitchedPercussion 'Percussion'>
    >>> i.midiChannel  # 0-indexed in music21
    9
    >>> i.midiProgram  # 0-indexed in music21
    53
    '''
    from music21 import midi as midiModule

    if not common.isListLike(eventList):
        event = eventList
    else:  # get the second event; first is delta time
        event = eventList[1]

    decoded: str = ''
    try:
        if isinstance(event.data, bytes):
            # MuseScore writes MIDI files with null-terminated
            # instrument names.  Thus stop before the byte-0x0
            decoded = event.data.decode('utf-8').split('\x00')[0]
            decoded = decoded.strip()
            i = instrument.fromString(decoded)
        elif event.channel == 10:
            # Can only get correct instruments from reading NOTE_ON
            i = instrument.UnpitchedPercussion()
            i.midiProgram = event.data
        else:
            i = instrument.instrumentFromMidiProgram(event.data)
            # Instrument.midiProgram and event.data are both 0-indexed
            i.midiProgram = event.data
    except UnicodeDecodeError:
        warnings.warn(
            f'Unable to determine instrument from {event}; getting generic Instrument',
            TranslateWarning)
        i = instrument.Instrument()
    except instrument.InstrumentException:
        # Debug logging would be better than warning here
        i = instrument.Instrument()

    # Set MIDI channel
    # Instrument.midiChannel is 0-indexed
    if event.channel is not None:
        i.midiChannel = event.channel - 1

    # Set partName or instrumentName with literal value from parsing
    if decoded:
        # Except for lousy instrument names
        if (
            decoded.lower() in ('instrument', 'inst')
            or decoded.lower().replace('instrument ', '').isdigit()
            or decoded.lower().replace('inst ', '').isdigit()
        ):
            return i
        elif event.type == midiModule.MetaEvents.SEQUENCE_TRACK_NAME:
            i.partName = decoded
        elif event.type == midiModule.MetaEvents.INSTRUMENT_NAME:
            i.instrumentName = decoded
    return i


def midiEventsToTimeSignature(eventList):
    # noinspection PyShadowingNames
    '''
    Convert a single MIDI event into a music21 TimeSignature object.

    >>> mt = midi.MidiTrack(1)
    >>> me1 = midi.MidiEvent(mt)
    >>> me1.type = midi.MetaEvents.TIME_SIGNATURE
    >>> me1.data = midi.putNumbersAsList([3, 1, 24, 8])  # 3/2 time
    >>> ts = midi.translate.midiEventsToTimeSignature(me1)
    >>> ts
    <music21.meter.TimeSignature 3/2>

    >>> me2 = midi.MidiEvent(mt)
    >>> me2.type = midi.MetaEvents.TIME_SIGNATURE
    >>> me2.data = midi.putNumbersAsList([3, 4])  # 3/16 time
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
    else:  # get the second event; first is delta time
        event = eventList[1]

    # time signature is 4 byte encoding
    post = midiModule.getNumbersAsList(event.data)

    n = post[0]
    d = pow(2, post[1])
    ts = meter.TimeSignature(f'{n}/{d}')
    return ts


def timeSignatureToMidiEvents(ts, includeDeltaTime=True):
    # noinspection PyShadowingNames
    '''
    Translate a :class:`~music21.meter.TimeSignature` to a pair of events: a DeltaTime and
    a MidiEvent TIME_SIGNATURE.

    Returns a two-element list

    >>> ts = meter.TimeSignature('5/4')
    >>> eventList = midi.translate.timeSignatureToMidiEvents(ts)
    >>> eventList[0]
    <music21.midi.DeltaTime (empty) track=None, channel=None>
    >>> eventList[1]
    <music21.midi.MidiEvent TIME_SIGNATURE, track=None, channel=1, data=b'\\x05\\x02\\x18\\x08'>
    '''
    from music21 import midi as midiModule

    mt = None  # use a midi track set to None
    eventList = []
    if includeDeltaTime:
        dt = midiModule.DeltaTime(track=mt)
        # dt.time set to zero; will be shifted later as necessary
        # add to track events
        eventList.append(dt)

    n = ts.numerator
    # need log base 2 to solve for exponent of 2
    # 1 is 0, 2 is 1, 4 is 2, 16 is 4, etc
    d = int(math.log2(ts.denominator))
    metroClick = 24  # clock signals per click, clicks are 24 per quarter
    subCount = 8  # number of 32 notes in a quarter note

    me = midiModule.MidiEvent(track=mt)
    me.type = midiModule.MetaEvents.TIME_SIGNATURE
    me.channel = 1
    me.data = midiModule.putNumbersAsList([n, d, metroClick, subCount])
    eventList.append(me)
    return eventList


def midiEventsToKey(eventList) -> 'music21.key.Key':
    # noinspection PyShadowingNames
    r'''
    Convert a single MIDI event into a :class:`~music21.key.KeySignature` object.

    >>> mt = midi.MidiTrack(1)
    >>> me1 = midi.MidiEvent(mt)
    >>> me1.type = midi.MetaEvents.KEY_SIGNATURE
    >>> me1.data = midi.putNumbersAsList([2, 0])  # d major
    >>> ks = midi.translate.midiEventsToKey(me1)
    >>> ks
    <music21.key.Key of D major>
    >>> ks.mode
    'major'

    >>> me2 = midi.MidiEvent(mt)
    >>> me2.type = midi.MetaEvents.KEY_SIGNATURE
    >>> me2.data = midi.putNumbersAsList([-2, 1])  # g minor
    >>> me2.data
    b'\xfe\x01'
    >>> midi.getNumbersAsList(me2.data)
    [254, 1]
    >>> ks = midi.translate.midiEventsToKey(me2)
    >>> ks
    <music21.key.Key of g minor>
    >>> ks.sharps
    -2
    >>> ks.mode
    'minor'
    '''
    # This meta event is used to specify the key (number of sharps or flats)
    # and scale (major or minor) of a sequence. A positive value for
    # the key specifies the number of sharps and a negative value specifies
    # the number of flats. A value of 0 for the scale specifies a major key
    # and a value of 1 specifies a minor key.
    from music21 import midi as midiModule

    if not common.isListLike(eventList):
        event = eventList
    else:  # get the second event; first is delta time
        event = eventList[1]
    post = midiModule.getNumbersAsList(event.data)

    # first value is number of sharp, or neg for number of flat
    if post[0] > 12:
        # flip around 256
        sharpCount = post[0] - 256  # need negative values
    else:
        sharpCount = post[0]

    mode = 'major'
    if post[1] == 1:
        mode = 'minor'

    # environLocal.printDebug(['midiEventsToKey', post, sharpCount])
    ks = key.KeySignature(sharpCount)
    k = ks.asKey(mode)

    return k


def keySignatureToMidiEvents(ks: 'music21.key.KeySignature', includeDeltaTime=True):
    # noinspection PyShadowingNames
    r'''
    Convert a single :class:`~music21.key.Key` or
    :class:`~music21.key.KeySignature` object to
    a two-element list of midi events,
    where the first is an empty DeltaTime (unless includeDeltaTime is False) and the second
    is a KEY_SIGNATURE :class:`~music21.midi.MidiEvent`

    >>> ks = key.KeySignature(2)
    >>> ks
    <music21.key.KeySignature of 2 sharps>
    >>> eventList = midi.translate.keySignatureToMidiEvents(ks)
    >>> eventList
    [<music21.midi.DeltaTime (empty) track=None, channel=None>,
     <music21.midi.MidiEvent KEY_SIGNATURE, track=None, channel=1, data=b'\x02\x00'>]

    >>> k = key.Key('b-')
    >>> k
    <music21.key.Key of b- minor>
    >>> eventList = midi.translate.keySignatureToMidiEvents(k, includeDeltaTime=False)
    >>> eventList
    [<music21.midi.MidiEvent KEY_SIGNATURE, track=None, channel=1, data=b'\xfb\x01'>]
    '''
    from music21 import midi as midiModule
    mt = None  # use a midi track set to None
    eventList = []
    if includeDeltaTime:
        dt = midiModule.DeltaTime(track=mt)
        # leave dt.time set to zero; will be shifted later as necessary
        # add to track events
        eventList.append(dt)
    sharpCount = ks.sharps
    if isinstance(ks, key.Key) and ks.mode == 'minor':
        mode = 1
    else:  # major or None; must define one
        mode = 0
    me = midiModule.MidiEvent(track=mt)
    me.type = midiModule.MetaEvents.KEY_SIGNATURE
    me.channel = 1
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
    else:  # get the second event; first is delta time
        event = eventList[1]
    # get microseconds per quarter
    mspq = midiModule.getNumber(event.data, 3)[0]  # first data is number
    bpm = round(60_000_000 / mspq, 2)
    # post = midiModule.getNumbersAsList(event.data)
    # environLocal.printDebug(['midiEventsToTempo, got bpm', bpm])
    mm = tempo.MetronomeMark(number=bpm)
    return mm


def tempoToMidiEvents(tempoIndication, includeDeltaTime=True):
    # noinspection PyShadowingNames
    r'''
    Given any TempoIndication, convert it to list of :class:`~music21.midi.MidiEvent`
    objects that signifies a MIDI tempo indication.

    >>> mm = tempo.MetronomeMark(number=90)
    >>> events = midi.translate.tempoToMidiEvents(mm)
    >>> events
    [<music21.midi.DeltaTime ...>, <music21.midi.MidiEvent SET_TEMPO...>]
    >>> len(events)
    2

    >>> events[0]
    <music21.midi.DeltaTime (empty) track=None, channel=None>

    >>> evt1 = events[1]
    >>> evt1
    <music21.midi.MidiEvent SET_TEMPO, track=None, channel=1, data=b'\n,+'>
    >>> evt1.data
    b'\n,+'
    >>> microSecondsPerQuarterNote = midi.getNumber(evt1.data, len(evt1.data))[0]
    >>> microSecondsPerQuarterNote
    666667

    >>> round(60_000_000 / microSecondsPerQuarterNote, 1)
    90.0

    If includeDeltaTime is False then the DeltaTime object is omitted:

    >>> midi.translate.tempoToMidiEvents(mm, includeDeltaTime=False)
    [<music21.midi.MidiEvent SET_TEMPO...>]


    Test round-trip.  Note that for pure tempo numbers, by default
    we create a text name if there's an appropriate one:

    >>> midi.translate.midiEventsToTempo(events)
    <music21.tempo.MetronomeMark maestoso Quarter=90.0>

    `None` is returned if the MetronomeMark lacks a number, which can
    happen with metric modulation marks.

    >>> midi.translate.tempoToMidiEvents(tempo.MetronomeMark(number=None)) is None
    True
    '''
    from music21 import midi as midiModule
    if tempoIndication.number is None:
        return
    mt = None  # use a midi track set to None
    eventList = []
    if includeDeltaTime:
        dt = midiModule.DeltaTime(track=mt)
        eventList.append(dt)

    me = midiModule.MidiEvent(track=mt)
    me.type = midiModule.MetaEvents.SET_TEMPO
    me.channel = 1

    # from any tempo indication, get the sounding metronome mark
    mm = tempoIndication.getSoundingMetronomeMark()
    bpm = mm.getQuarterBPM()
    mspq = int(round(60_000_000 / bpm))  # microseconds per quarter note

    me.data = midiModule.putNumber(mspq, 3)
    eventList.append(me)
    return eventList


# ------------------------------------------------------------------------------
# Streams


def getPacketFromMidiEvent(
        trackId: int,
        offset: int,
        midiEvent: 'music21.midi.MidiEvent',
        obj: Optional['music21.base.Music21Object'] = None,
        lastInstrument: Optional['music21.instrument.Instrument'] = None
) -> Dict[str, Any]:
    '''
    Pack a dictionary of parameters for each event.
    Packets are used for sorting and configuring all note events.
    Includes offset, any cent shift, the midi event, and the source object.

    Offset and duration values stored here are MIDI ticks, not quarter lengths.

    >>> n = note.Note('C4')
    >>> midiEvents = midi.translate.elementToMidiEventList(n)
    >>> getPacket = midi.translate.getPacketFromMidiEvent
    >>> getPacket(trackId=1, offset=0, midiEvent=midiEvents[0], obj=n)
    {'trackId': 1,
     'offset': 0,
     'midiEvent': <music21.midi.MidiEvent NOTE_ON, track=None, channel=1, pitch=60, velocity=90>,
     'obj': <music21.note.Note C>,
     'centShift': None,
     'duration': 1024,
     'lastInstrument': None}
    >>> inst = instrument.Harpsichord()
    >>> getPacket(trackId=1, offset=0, midiEvent=midiEvents[1], obj=n, lastInstrument=inst)
    {'trackId': 1,
     'offset': 0,
     'midiEvent': <music21.midi.MidiEvent NOTE_OFF, track=None, channel=1, pitch=60, velocity=0>,
     'obj': <music21.note.Note C>,
     'centShift': None,
     'duration': 0,
     'lastInstrument': <music21.instrument.Harpsichord 'Harpsichord'>}
    '''
    from music21 import midi as midiModule
    post = {
        'trackId': trackId,
        'offset': offset,  # offset values are in midi ticks
        'midiEvent': midiEvent,
        'obj': obj,   # keep a reference to the source object
        'centShift': midiEvent.centShift,
        'duration': 0,
        # store last m21 instrument object, as needed to reset program changes
        'lastInstrument': lastInstrument,
    }

    # allocate channel later
    # post['channel'] = None
    if midiEvent.type != midiModule.ChannelVoiceMessages.NOTE_OFF and obj is not None:
        # store duration so as to calculate when the
        # channel/pitch bend can be freed
        post['duration'] = durationToMidiTicks(obj.duration)
    # note offs will have the same object ref, and seem like the have a
    # duration when they do not

    return post


def elementToMidiEventList(
    el: 'music21.base.Music21Object'
) -> Optional[List['music21.midi.MidiEvent']]:
    '''
    Return a list of MidiEvents (or None) from a Music21Object,
    assuming that dynamics have already been applied, etc.
    Does not include DeltaTime objects.

    Channel (1-indexed) is set to the default, 1.
    Track is not set.

    >>> n = note.Note('C4')
    >>> midiEvents = midi.translate.elementToMidiEventList(n)
    >>> midiEvents
    [<music21.midi.MidiEvent NOTE_ON, track=None, channel=1, pitch=60, velocity=90>,
     <music21.midi.MidiEvent NOTE_OFF, track=None, channel=1, pitch=60, velocity=0>]
    '''
    classes = el.classes
    if 'Rest' in classes:
        return None
    elif 'Note' in classes:
        # get a list of midi events
        # using this property here is easier than using the above conversion
        # methods, as we do not need to know what the object is
        sub = noteToMidiEvents(el, includeDeltaTime=False)
    # TODO: unpitched
    elif 'Chord' in classes:
        # TODO: skip Harmony unless showAsChord
        sub = chordToMidiEvents(el, includeDeltaTime=False)
    elif 'Dynamic' in classes:
        return None  # dynamics have already been applied to notes
    elif 'TimeSignature' in classes:
        # return a pair of events
        el: 'music21.meter.TimeSignature'
        sub = timeSignatureToMidiEvents(el, includeDeltaTime=False)
    elif 'KeySignature' in classes:
        el: 'music21.key.KeySignature'
        sub = keySignatureToMidiEvents(el, includeDeltaTime=False)
    elif 'TempoIndication' in classes:
        # any tempo indication will work
        # note: tempo indications need to be in channel one for most playback
        el: 'music21.tempo.TempoIndication'
        sub = tempoToMidiEvents(el, includeDeltaTime=False)
    elif 'Instrument' in classes:
        # first instrument will have been gathered above with get start elements
        sub = instrumentToMidiEvents(el, includeDeltaTime=False)
    else:
        # other objects may have already been added
        return None

    return sub


def streamToPackets(
    s: stream.Stream,
    trackId: int = 1,
    addStartDelay: bool = False,
) -> List[Dict[str, Any]]:
    '''
    Convert a (flattened, sorted) Stream to packets.

    This assumes that the Stream has already been flattened,
    ties have been stripped, and instruments,
    if necessary, have been added.

    In converting from a Stream to MIDI, this is called first,
    resulting in a collection of packets by offset.
    Then, packets to events is called.
    '''
    from music21 import midi as midiModule
    # store all events by offset by offset without delta times
    # as (absTime, event)
    packetsByOffset = []
    lastInstrument = None

    # s should already be flat and sorted
    for el in s:
        midiEventList = elementToMidiEventList(el)
        if 'Instrument' in el.classes:
            lastInstrument = el  # store last instrument

        if midiEventList is None:
            continue

        # we process midiEventList here, which is a list of midi events
        # for each event, we create a packet representation
        # all events: delta/note-on/delta/note-off
        # strip delta times
        elementPackets = []
        firstNotePlayed = False
        for i in range(len(midiEventList)):
            # store offset, midi event, object
            # add channel and pitch change also
            midiEvent = midiEventList[i]
            if (midiEvent.type == midiModule.ChannelVoiceMessages.NOTE_ON
                    and firstNotePlayed is False):
                firstNotePlayed = True

            if firstNotePlayed is False:
                o = offsetToMidiTicks(s.elementOffset(el), addStartDelay=False)
            else:
                o = offsetToMidiTicks(s.elementOffset(el), addStartDelay=addStartDelay)

            if midiEvent.type != midiModule.ChannelVoiceMessages.NOTE_OFF:
                # use offset
                p = getPacketFromMidiEvent(
                    trackId,
                    o,
                    midiEvent,
                    obj=el,
                    lastInstrument=lastInstrument,
                )
                elementPackets.append(p)
            # if its a note_off, use the duration to shift offset
            # midi events have already been created;
            else:
                p = getPacketFromMidiEvent(
                    trackId,
                    o + durationToMidiTicks(el.duration),
                    midiEvent,
                    obj=el,
                    lastInstrument=lastInstrument)
                elementPackets.append(p)
        packetsByOffset += elementPackets

    # sorting is useful here, as we need these to be in order to assign last
    # instrument
    packetsByOffset.sort(
        key=lambda x: (x['offset'], x['midiEvent'].sortOrder)
    )
    # return packets and stream, as this flat stream should be retained
    return packetsByOffset


def assignPacketsToChannels(
        packets,
        channelByInstrument=None,
        channelsDynamic=None,
        initTrackIdToChannelMap=None):
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
    `channelByInstrument` should be a dictionary.
    `channelsDynamic` should be a list.
    `initTrackIdToChannelMap` should be a dictionary.
    '''
    from music21 import midi as midiModule

    if channelByInstrument is None:
        channelByInstrument = {}
    if channelsDynamic is None:
        channelsDynamic = []
    if initTrackIdToChannelMap is None:
        initTrackIdToChannelMap = {}

    uniqueChannelEvents = {}  # dict of (start, stop, usedChannel) : channel
    post = []
    usedTracks = []

    for p in packets:
        # environLocal.printDebug(['assignPacketsToChannels', p['midiEvent'].track, p['trackId']])
        # must use trackId, as .track on MidiEvent is not yet set
        if p['trackId'] not in usedTracks:
            usedTracks.append(p['trackId'])

        # only need note_ons, as stored correspondingEvent attr can be used
        # to get noteOff
        if p['midiEvent'].type != midiModule.ChannelVoiceMessages.NOTE_ON:
            # set all not note-off messages to init channel
            if p['midiEvent'].type != midiModule.ChannelVoiceMessages.NOTE_OFF:
                p['midiEvent'].channel = p['initChannel']
            post.append(p)  # add the non note_on packet first
            # if this is a note off, and has a cent shift, need to
            # rest the pitch bend back to 0 cents
            if p['midiEvent'].type == midiModule.ChannelVoiceMessages.NOTE_OFF:
                # environLocal.printDebug(['got note-off', p['midiEvent']])
                # cent shift is set for note on and note off
                if p['centShift']:
                    # do not set channel, as already set
                    me = midiModule.MidiEvent(p['midiEvent'].track,
                                              type=midiModule.ChannelVoiceMessages.PITCH_BEND,
                                              channel=p['midiEvent'].channel)
                    # note off stores a note on for each pitch; do not invert, simply
                    # set to zero
                    me.setPitchBend(0)
                    pBendEnd = getPacketFromMidiEvent(
                        trackId=p['trackId'],
                        offset=p['offset'],
                        midiEvent=me,
                    )
                    post.append(pBendEnd)
                    # environLocal.printDebug(['adding pitch bend', pBendEnd])
            continue  # store and continue

        # set default channel for all packets
        p['midiEvent'].channel = p['initChannel']

        # find a free channel
        # if necessary, add pitch change at start of Note,
        # cancel pitch change at end
        o = p['offset']
        oEnd = p['offset'] + p['duration']

        channelExclude = []  # channels that cannot be used
        centShift = p['centShift']  # may be None

        # environLocal.printDebug(['\n\n', 'offset', o, 'oEnd', oEnd, 'centShift', centShift])

        # iterate through all past events/channels, and find all
        # that are active and have a pitch bend
        for key_tuple in uniqueChannelEvents:
            start, stop, usedChannel = key_tuple
            # if offset (start time) is in this range of a found event
            # or if any start or stop is within this span
            # if o >= start and o < stop:  # found an offset that is used

            if ((o <= start < oEnd)
                    or (o < stop < oEnd)
                    or (start <= o < stop)
                    or (start < oEnd < stop)):
                # if there is a cent shift active in the already used channel
                # environLocal.printDebug(['matchedOffset overlap'])
                centShiftList = uniqueChannelEvents[key_tuple]
                if centShiftList:
                    # only add if unique
                    if usedChannel not in channelExclude:
                        channelExclude.append(usedChannel)
                # or if this event has shift, then we can exclude
                # the channel already used without a shift
                elif centShift:
                    if usedChannel not in channelExclude:
                        channelExclude.append(usedChannel)
                        # cannot break early w/o sorting

        # if no channels are excluded, get a new channel
        # environLocal.printDebug(['post process channelExclude', channelExclude])
        if channelExclude:  # only change if necessary
            ch = None
            # iterate in order over all channels: lower will be added first
            for x in channelsDynamic:
                if x not in channelExclude:
                    ch = x
                    break
            if ch is None:
                raise TranslateException(
                    'no unused channels available for microtone/instrument assignment')
            p['midiEvent'].channel = ch
            # change channel of note off; this is used above to turn off bend
            p['midiEvent'].correspondingEvent.channel = ch
            # environLocal.printDebug(['set channel of correspondingEvent:',
            # p['midiEvent'].correspondingEvent])

            # TODO: must add program change, as we are now in a new
            # channel; regardless of if we have a pitch bend (we may
            # move channels for a different reason
            if p['lastInstrument'] is not None:
                meList = instrumentToMidiEvents(inputM21=p['lastInstrument'],
                                                includeDeltaTime=False,
                                                midiTrack=p['midiEvent'].track,
                                                channel=ch)
                pgmChangePacket = getPacketFromMidiEvent(
                    trackId=p['trackId'],
                    offset=o,  # keep offset here
                    midiEvent=meList[0],
                )
                post.append(pgmChangePacket)

        else:  # use the existing channel
            ch = p['midiEvent'].channel
            # always set corresponding event to the same channel
            p['midiEvent'].correspondingEvent.channel = ch

        # environLocal.printDebug(['assigning channel', ch, 'channelsDynamic', channelsDynamic,
        # 'p['initChannel']', p['initChannel']])

        if centShift:
            # add pitch bend
            me = midiModule.MidiEvent(p['midiEvent'].track,
                                      type=midiModule.ChannelVoiceMessages.PITCH_BEND,
                                      channel=ch)
            me.setPitchBend(centShift)
            pBendStart = getPacketFromMidiEvent(
                trackId=p['trackId'],
                offset=o,
                midiEvent=me,  # keep offset here
            )
            post.append(pBendStart)
            # environLocal.printDebug(['adding pitch bend', me])
            # removal of pitch bend will happen above with note off

        # key includes channel, so that durations can span once in each channel
        key_tuple = (p['offset'], p['offset'] + p['duration'], ch)
        if key_tuple not in uniqueChannelEvents:
            # need to count multiple instances of events on the same
            # span and in the same channel (fine if all have the same pitch bend
            uniqueChannelEvents[key_tuple] = []
        # always add the cent shift if it is not None
        if centShift:
            uniqueChannelEvents[key_tuple].append(centShift)
        post.append(p)  # add packet/ done after ch change or bend addition
        # environLocal.printDebug(['uniqueChannelEvents', uniqueChannelEvents])

    # this is called once at completion
    # environLocal.printDebug(['uniqueChannelEvents', uniqueChannelEvents])

    # after processing, collect all channels used
    foundChannels = []
    for start, stop, usedChannel in list(uniqueChannelEvents):  # a list
        if usedChannel not in foundChannels:
            foundChannels.append(usedChannel)
    # for ch in chList:
    #     if ch not in foundChannels:
    #         foundChannels.append(ch)
    # environLocal.printDebug(['foundChannels', foundChannels])
    # environLocal.printDebug(['usedTracks', usedTracks])

    # post processing of entire packet collection
    # for all used channels, create a zero pitch bend at time zero
    # for ch in foundChannels:
    # for each track, places a pitch bend in its initChannel
    for trackId in usedTracks:
        if trackId == 0:
            continue  # Conductor track: do not add pitch bend
        ch = initTrackIdToChannelMap[trackId]
        # use None for track; will get updated later
        me = midiModule.MidiEvent(track=trackId,
                                  type=midiModule.ChannelVoiceMessages.PITCH_BEND,
                                  channel=ch)
        me.setPitchBend(0)
        pBendEnd = getPacketFromMidiEvent(
            trackId=trackId,
            offset=0,
            midiEvent=me,
        )
        post.append(pBendEnd)
        # environLocal.printDebug(['adding pitch bend for found channels', me])
    # this sort is necessary
    post.sort(
        key=lambda x_event: (x_event['offset'], x_event['midiEvent'].sortOrder)
    )

    # TODO: for each track, add an additional silent event to make sure
    # entire duration gets played

    # diagnostic display
    # for p in post: environLocal.printDebug(['processed packet', p])

    # post = packets
    return post


def filterPacketsByTrackId(
    packetsSrc: List[Dict[str, Any]],
    trackIdFilter: Optional[int] = None,
) -> List[Dict[str, Any]]:
    '''
    Given a list of Packet dictionaries, return a list of
    only those whose trackId matches the filter.

    >>> packets = [
    ...     {'trackId': 1, 'name': 'hello'},
    ...     {'trackId': 2, 'name': 'bye'},
    ...     {'trackId': 1, 'name': 'hi'},
    ... ]
    >>> midi.translate.filterPacketsByTrackId(packets, 1)
    [{'trackId': 1, 'name': 'hello'},
     {'trackId': 1, 'name': 'hi'}]
    >>> midi.translate.filterPacketsByTrackId(packets, 2)
    [{'trackId': 2, 'name': 'bye'}]

    If no trackIdFilter is passed, the original list is returned:

    >>> midi.translate.filterPacketsByTrackId(packets) is packets
    True
    '''
    if trackIdFilter is None:
        return packetsSrc

    outPackets = []
    for packet in packetsSrc:
        if packet['trackId'] == trackIdFilter:
            outPackets.append(packet)
    return outPackets


def packetsToDeltaSeparatedEvents(
        packets: List[Dict[str, Any]],
        midiTrack: 'music21.midi.MidiTrack'
) -> List['music21.midi.MidiEvent']:
    '''
    Given a list of packets (which already contain MidiEvent objects)
    return a list of those Events with proper delta times between them.

    At this stage MIDI event objects have been created.
    The key process here is finding the adjacent time
    between events and adding DeltaTime events before each MIDI event.

    Delta time channel values are derived from the previous midi event.
    '''
    from music21.midi import DeltaTime

    events = []
    lastOffset = 0
    for packet in packets:
        midiEvent = packet['midiEvent']
        t = packet['offset'] - lastOffset
        if t < 0:
            raise TranslateException('got a negative delta time')
        # set the channel from the midi event
        dt = DeltaTime(midiTrack, time=t, channel=midiEvent.channel)
        # environLocal.printDebug(['packetsByOffset', packet])
        events.append(dt)
        events.append(midiEvent)
        lastOffset = packet['offset']
    # environLocal.printDebug(['packetsToDeltaSeparatedEvents', 'total events:', len(events)])
    return events


def packetsToMidiTrack(packets, trackId=1, channel=1, instrumentObj=None):
    '''
    Given packets already allocated with channel
    and/or instrument assignments, place these in a MidiTrack.

    Note that all packets can be sent; only those with
    matching trackIds will be collected into the resulting track

    The `channel` defines the channel that startEvents and endEvents
    will be assigned to

    Use streamToPackets to convert the Stream to the packets
    '''
    from music21 import midi as midiModule

    # TODO: for a given track id, need to find start/end channel
    mt = midiModule.MidiTrack(trackId)
    # set startEvents to preferred channel
    mt.events += getStartEvents(mt,
                                channel=channel,
                                instrumentObj=instrumentObj)

    # filter only those packets for this track
    trackPackets = filterPacketsByTrackId(packets, trackId)
    mt.events += packetsToDeltaSeparatedEvents(trackPackets, mt)

    # must update all events with a ref to this MidiTrack
    mt.events += getEndEvents(mt, channel=channel)
    mt.updateEvents()  # sets this track as .track for all events
    return mt


def getTimeForEvents(
    mt: 'music21.midi.MidiTrack'
) -> List[Tuple[int, 'music21.midi.MidiEvent']]:
    '''
    Get a list of tuples of (tickTime, MidiEvent) from the events with time deltas.
    '''
    # get an abs start time for each event, discard deltas
    events = []
    currentTime = 0

    # pair deltas with events, convert abs time
    # get even numbers
    # in some cases, the first event may not be a delta time, but
    # a SEQUENCE_TRACK_NAME or something else. thus, need to get
    # first delta time
    i = 0
    while i < len(mt.events):
        currentEvent = mt.events[i]
        try:
            nextEvent = mt.events[i + 1]
        except IndexError:  # pragma: no cover
            break

        currentDt = currentEvent.isDeltaTime()
        nextDt = nextEvent.isDeltaTime()

        # in pairs, first should be delta time, second should be event
        # environLocal.printDebug(['midiTrackToStream(): index', 'i', i, mt.events[i]])
        # environLocal.printDebug(['midiTrackToStream(): index', 'i + 1', i + 1, mt.events[i + 1]])

        # need to find pairs of delta time and events
        # in some cases, there are delta times that are out of order, or
        # packed in the beginning
        if currentDt and not nextDt:
            currentTime += currentEvent.time  # increment time
            tupleAppend = (currentTime, nextEvent)
            events.append(tupleAppend)
            i += 2
        elif (not currentDt
              and not nextDt):
            # environLocal.printDebug(['midiTrackToStream(): got two non delta times in a row'])
            i += 1
        elif currentDt and nextDt:
            # environLocal.printDebug(['midiTrackToStream(): got two delta times in a row'])
            i += 1
        else:
            # cannot pair delta time to the next event; skip by 1
            # environLocal.printDebug(['cannot pair to delta time', mt.events[i]])
            i += 1

    return events


def getNotesFromEvents(
    events: List[Tuple[int, 'music21.midi.MidiEvent']]
) -> List[Tuple[Tuple[int, 'music21.midi.MidiEvent'],
                Tuple[int, 'music21.midi.MidiEvent']]]:
    '''
    Returns a list of Tuples of MIDI events that are pairs of note-on and
    note-off events.

    '''
    notes = []  # store pairs of pairs
    memo = set()   # store already matched note off
    for i, eventTuple in enumerate(events):
        if i in memo:
            continue
        unused_t, e = eventTuple
        # for each note on event, we need to search for a match in all future
        # events
        if not e.isNoteOn():
            continue
        match = None
        # environLocal.printDebug(['midiTrackToStream(): isNoteOn', e])
        for j in range(i + 1, len(events)):
            if j in memo:
                continue
            unused_tSub, eSub = events[j]
            if e.matchedNoteOff(eSub):
                memo.add(j)
                match = i, j
                break
        if match is not None:
            i, j = match
            pairs = (events[i], events[j])
            notes.append(pairs)
        else:
            pass
            # environLocal.printDebug([
            #    'midiTrackToStream(): cannot find a note off for a note on', e])
    return notes


def getMetaEvents(events):
    from music21.midi import MetaEvents, ChannelVoiceMessages

    metaEvents = []  # store pairs of abs time, m21 object
    last_program: int = -1
    for eventTuple in events:
        t, e = eventTuple
        metaObj = None
        if e.type == MetaEvents.TIME_SIGNATURE:
            # time signature should be 4 bytes
            metaObj = midiEventsToTimeSignature(e)
        elif e.type == MetaEvents.KEY_SIGNATURE:
            metaObj = midiEventsToKey(e)
        elif e.type == MetaEvents.SET_TEMPO:
            metaObj = midiEventsToTempo(e)
        elif e.type in (MetaEvents.INSTRUMENT_NAME, MetaEvents.SEQUENCE_TRACK_NAME):
            # midiEventsToInstrument() WILL NOT have knowledge of the current
            # program, so set it here
            metaObj = midiEventsToInstrument(e)
            if last_program != -1:
                # Only update if we have had an initial PROGRAM_CHANGE
                metaObj.midiProgram = last_program
        elif e.type == ChannelVoiceMessages.PROGRAM_CHANGE:
            # midiEventsToInstrument() WILL set the program on the instance
            metaObj = midiEventsToInstrument(e)
            last_program = e.data
        elif e.type == MetaEvents.MIDI_PORT:
            pass
        else:
            pass
        if metaObj:
            pair = (t, metaObj)
            metaEvents.append(pair)

    return metaEvents

def insertConductorEvents(conductorPart: stream.Part,
                          target: stream.Part,
                          *,
                          isFirst: bool = False,
                          ):
    '''
    Insert a deepcopy of any TimeSignature, KeySignature, or MetronomeMark
    found in the `conductorPart` into the `target` Part at the same offset.

    Obligatory to do this before making measures. New in v7.
    '''
    for e in conductorPart.getElementsByClass(
            ('TimeSignature', 'KeySignature', 'MetronomeMark')):
        # create a deepcopy of the element so a flat does not cause
        # multiple references of the same
        eventCopy = copy.deepcopy(e)
        if 'TempoIndication' in eventCopy.classes and not isFirst:
            eventCopy.style.hideObjectOnPrint = True
            eventCopy.numberImplicit = True
        target.insert(conductorPart.elementOffset(e), eventCopy)

def midiTrackToStream(
    mt,
    ticksPerQuarter=None,
    quantizePost=True,
    inputM21=None,
    conductorPart: Optional[stream.Part] = None,
    isFirst: bool = False,
    **keywords
) -> stream.Part:
    # noinspection PyShadowingNames
    '''
    Note that quantization takes place in stream.py since it's useful not just for MIDI.

    >>> fp = common.getSourceFilePath() / 'midi' / 'testPrimitive' / 'test05.mid'
    >>> mf = midi.MidiFile()
    >>> mf.open(fp)
    >>> mf.read()
    >>> mf.close()
    >>> mf
    <music21.midi.MidiFile 1 track>
    >>> len(mf.tracks)
    1
    >>> mt = mf.tracks[0]
    >>> mt
    <music21.midi.MidiTrack 0 -- 56 events>
    >>> mt.events
    [<music21.midi.DeltaTime ...>,
     <music21.midi.MidiEvent SEQUENCE_TRACK_NAME...>,
     <music21.midi.DeltaTime ...>,
     <music21.midi.MidiEvent NOTE_ON, track=0, channel=1, pitch=36, velocity=90>,
     ...]
    >>> p = midi.translate.midiTrackToStream(mt)
    >>> p
    <music21.stream.Part ...>
    >>> len(p.recurse().notesAndRests)
    14
    >>> p.recurse().notes.first().pitch.midi
    36
    >>> p.recurse().notes.first().volume.velocity
    90

    Changed in v.7 -- Now makes measures

    >>> p.show('text')
    {0.0} <music21.stream.Measure 1 offset=0.0>
        {0.0} <music21.instrument.Instrument ''>
        {0.0} <music21.clef.TrebleClef>
        {0.0} <music21.meter.TimeSignature 4/4>
        {0.0} <music21.note.Note C>
        {1.0} <music21.note.Rest quarter>
        {2.0} <music21.chord.Chord F3 G#4 C5>
        {3.0} <music21.note.Rest quarter>
    {4.0} <music21.stream.Measure 2 offset=4.0>
        {0.0} <music21.note.Rest eighth>
        {0.5} <music21.note.Note B->
        {1.5} <music21.note.Rest half>
        {3.5} <music21.chord.Chord D2 A4>
    {8.0} <music21.stream.Measure 3 offset=8.0>
        {0.0} <music21.note.Rest eighth>
        {0.5} <music21.chord.Chord C#2 B-3 G#6>
        {1.0} <music21.note.Rest dotted-quarter>
        {2.5} <music21.chord.Chord F#3 A4 C#5>
    {12.0} <music21.stream.Measure 4 offset=12.0>
        {0.0} <music21.chord.Chord F#3 A4 C#5>
        {2.5} <music21.note.Rest dotted-quarter>
        {4.0} <music21.bar.Barline type=final>
    '''
    # environLocal.printDebug(['midiTrackToStream(): got midi track: events',
    # len(mt.events), 'ticksPerQuarter', ticksPerQuarter])

    if inputM21 is None:
        s = stream.Part()
    else:
        s = inputM21

    if ticksPerQuarter is None:
        ticksPerQuarter = defaults.ticksPerQuarter

    # get events without DeltaTimes
    events = getTimeForEvents(mt)

    # need to build chords and notes
    notes = getNotesFromEvents(events)
    metaEvents = getMetaEvents(events)

    # first create meta events
    for t, obj in metaEvents:
        # environLocal.printDebug(['insert midi meta event:', t, obj])
        s.coreInsert(t / ticksPerQuarter, obj)
    s.coreElementsChanged()
    deduplicate(s, inPlace=True)
    # environLocal.printDebug([
    #    'midiTrackToStream(): found notes ready for Stream import', len(notes)])

    # collect notes with similar start times into chords
    # create a composite list of both notes and chords
    # composite = []
    chordSub = None
    i = 0
    iGathered = []  # store a list of indexes of gathered values put into chords
    voicesRequired = False

    if 'quarterLengthDivisors' in keywords:
        quarterLengthDivisors = keywords['quarterLengthDivisors']
    else:
        quarterLengthDivisors = defaults.quantizationQuarterLengthDivisors

    if len(notes) > 1:
        # environLocal.printDebug(['\n', 'midiTrackToStream(): notes', notes])
        while i < len(notes):
            if i in iGathered:
                i += 1
                continue
            # look at each note; get on time and event
            on, off = notes[i]
            t, unused_e = on
            tOff, unused_eOff = off
            # environLocal.printDebug(['on, off', on, off, 'i', i, 'len(notes)', len(notes)])

            # go through all following notes; if there is only 1 note, this will
            # not execute;
            # looking for other events that start within a certain small time
            # window to make into a chord
            # if we find a note with a different end time but same start
            # time, throw into a different voice
            for j in range(i + 1, len(notes)):
                # look at each on time event
                onSub, offSub = notes[j]
                tSub, unused_eSub = onSub
                tOffSub, unused_eOffSub = offSub

                # let tolerance for chord subbing follow the quantization
                if quantizePost:
                    divisor = max(quarterLengthDivisors)
                # fallback: 1/16 of a quarter (64th)
                else:
                    divisor = 16
                chunkTolerance = ticksPerQuarter / divisor
                # must be strictly less than the quantization unit
                if abs(tSub - t) < chunkTolerance:
                    # isolate case where end time is not w/n tolerance
                    if abs(tOffSub - tOff) > chunkTolerance:
                        # need to store this as requiring movement to a diff
                        # voice
                        voicesRequired = True
                        continue
                    if chordSub is None:  # start a new one
                        chordSub = [notes[i]]
                        iGathered.append(i)
                    chordSub.append(notes[j])
                    iGathered.append(j)
                    continue  # keep looping through events to see
                    # if we can add more elements to this chord group
                else:  # no more matches; assuming chordSub tones are contiguous
                    break
            # this comparison must be outside of j loop, as the case where we
            # have the last note in a list of notes and the j loop does not
            # execute; chordSub will be None
            if chordSub is not None:
                # composite.append(chordSub)
                c = midiEventsToChord(chordSub, ticksPerQuarter)
                o = notes[i][0][0] / ticksPerQuarter
                c.midiTickStart = notes[i][0][0]

                s.coreInsert(o, c)
                # iSkip = len(chordSub)  # amount of accumulated chords
                chordSub = None
            else:  # just append the note, chordSub is None
                # composite.append(notes[i])
                n = midiEventsToNote(notes[i], ticksPerQuarter)
                # the time is the first value in the first pair
                # need to round, as floating point error is likely
                o = notes[i][0][0] / ticksPerQuarter
                n.midiTickStart = notes[i][0][0]

                s.coreInsert(o, n)
                # iSkip = 1
            # break  # exit secondary loop
            i += 1

    elif len(notes) == 1:  # rare case of just one note
        n = midiEventsToNote(notes[0], ticksPerQuarter)
        # the time is the first value in the first pair
        # need to round, as floating point error is likely
        o = notes[0][0][0] / ticksPerQuarter
        n.midiTickStart = notes[0][0][0]
        s.coreInsert(o, n)

    s.coreElementsChanged()
    # quantize to nearest 16th
    if quantizePost:
        s.quantize(quarterLengthDivisors=quarterLengthDivisors,
                   processOffsets=True,
                   processDurations=True,
                   inPlace=True,
                   recurse=False)  # shouldn't be any substreams yet

    if not notes:
        # Conductor track doesn't need measures made
        # It's an intermediate result only -- not provided to user
        return s

    if conductorPart is not None:
        insertConductorEvents(conductorPart, s, isFirst=isFirst)

    meterStream: Optional[stream.Stream] = None
    if conductorPart is not None:
        ts_iter = conductorPart['TimeSignature']
        if ts_iter:
            meterStream = ts_iter.stream()
            # Supply any missing time signature at the start
            if not meterStream.getElementsByOffset(0):
                from music21 import meter
                meterStream.insert(0, meter.TimeSignature())

    # Only make measures once time signatures have been inserted
    s.makeMeasures(meterStream=meterStream, inPlace=True)
    if voicesRequired:
        for m in s.getElementsByClass(stream.Measure):
            # Gaps will be filled by makeRests, below, which now recurses
            m.makeVoices(inPlace=True, fillGaps=False)
    s.makeTies(inPlace=True)
    # always need to fill gaps, as rests are not found in any other way
    s.makeRests(inPlace=True, fillGaps=True, timeRangeFromBarDuration=True)
    return s


def prepareStreamForMidi(s) -> stream.Stream:
    # noinspection PyShadowingNames
    '''
    Given a score, prepare it for MIDI processing, and return a new Stream:

    1. Expand repeats.

    2. Make changes that will let us later create a conductor (tempo) track
    by placing `MetronomeMark`, `TimeSignature`, and `KeySignature`
    objects into a new Part, and remove them from other parts.

    3.  Ensure that the resulting Stream always has part-like substreams.

    Note: will make a deepcopy() of the stream.

    >>> s = stream.Score()
    >>> p = stream.Part()
    >>> m = stream.Measure(number=1)
    >>> m.append(tempo.MetronomeMark(100))
    >>> m.append(note.Note('C4', type='whole'))  # MIDI 60
    >>> p.append(m)
    >>> s.append(p)
    >>> sOut = midi.translate.prepareStreamForMidi(s)
    >>> sOut.show('text')
    {0.0} <music21.stream.Part 0x10b0439a0>
        {0.0} <music21.tempo.MetronomeMark Quarter=100>
        {0.0} <music21.meter.TimeSignature 4/4>
    {0.0} <music21.stream.Part 0x10b043c10>
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.note.Note C>
    '''
    from music21 import volume

    if s[stream.Measure]:
        s = s.expandRepeats()  # makes a deep copy
    else:
        s = s.coreCopyAsDerivation('prepareStreamForMidi')

    conductor = conductorStream(s)

    if s.hasPartLikeStreams():
        # process Volumes one part at a time
        # this assumes that dynamics in a part/stream apply to all components
        # of that part stream
        # this sets the cachedRealized value for each Volume
        for p in s.getElementsByClass('Stream'):
            volume.realizeVolume(p)

        s.insert(0, conductor)
        out = s

    else:  # just a single Stream
        volume.realizeVolume(s)
        out = stream.Score()
        out.insert(0, conductor)
        out.insert(0, s)

    return out


def conductorStream(s: stream.Stream) -> stream.Part:
    # noinspection PyShadowingNames
    '''
    Strip the given stream of any events that belong in a conductor track
    rather than in a music track, and returns a :class:`~music21.stream.Part`
    containing just those events, without duplicates, suitable for being a
    Part to turn into a conductor track.

    Sets a default MetronomeMark of 120 if no MetronomeMarks are present
    and a TimeSignature of 4/4 if not present.

    Ensures that the conductor track always sorts before other parts.

    Here we purposely use nested generic streams instead of Scores, Parts, etc.
    to show that this still works.  But you should use Score, Part, Measure instead.

    >>> s = stream.Stream(id='scoreLike')
    >>> p = stream.Stream(id='partLike')
    >>> p.priority = -2
    >>> m = stream.Stream(id='measureLike')
    >>> m.append(tempo.MetronomeMark(100))
    >>> m.append(note.Note('C4'))
    >>> p.append(m)
    >>> s.insert(0, p)
    >>> conductor = midi.translate.conductorStream(s)
    >>> conductor.priority
    -3

    The MetronomeMark is moved and a default TimeSignature is added:

    >>> conductor.show('text')
    {0.0} <music21.instrument.Conductor 'Conductor'>
    {0.0} <music21.tempo.MetronomeMark Quarter=100>
    {0.0} <music21.meter.TimeSignature 4/4>

    The original stream still has the note:

    >>> s.show('text')
    {0.0} <music21.stream.Stream partLike>
        {0.0} <music21.stream.Stream measureLike>
            {0.0} <music21.note.Note C>
    '''
    from music21 import tempo
    from music21 import meter
    partsList = list(s.getElementsByClass('Stream').getElementsByOffset(0))
    minPriority = min(p.priority for p in partsList) if partsList else 0
    conductorPriority = minPriority - 1

    conductorPart = stream.Part()
    conductorPart.priority = conductorPriority
    conductorPart.insert(0, Conductor())

    for klass in ('MetronomeMark', 'TimeSignature', 'KeySignature'):
        lastOffset = -1
        for el in s[klass]:
            offset_in_s = el.getOffsetInHierarchy(s)
            # Don't overwrite an event of the same class at this offset
            if offset_in_s > lastOffset:
                conductorPart.insert(offset_in_s, el)
            lastOffset = offset_in_s
        for s_or_inner_stream in s.recurse(streamsOnly=True, includeSelf=True):
            s_or_inner_stream.removeByClass(klass)

    conductorPart.coreElementsChanged()

    # Defaults
    if not conductorPart.getElementsByClass('MetronomeMark'):
        conductorPart.insert(tempo.MetronomeMark(number=120))
    if not conductorPart.getElementsByClass('TimeSignature'):
        conductorPart.insert(meter.TimeSignature('4/4'))

    return conductorPart


def channelInstrumentData(
    s: stream.Stream,
    acceptableChannelList: Optional[List[int]] = None,
) -> Tuple[Dict[Union[int, None], int], List[int]]:
    '''
    Read through Stream `s` and finding instruments in it, return a 2-tuple,
    the first a dictionary mapping MIDI program numbers to channel numbers,
    and the second, a list of unassigned channels that can be used for dynamic
    allocation. One channel is always left unassigned for dynamic allocation.
    If the number of needed channels exceeds the number of available ones,
    any further MIDI program numbers are assigned to channel 1.

    Substreams without notes or rests (e.g. representing a conductor track)
    will not consume a channel.

    Only necessarily works if :func:`~music21.midi.translate.prepareStreamForMidi`
    has been run before calling this routine.

    An instrument's `.midiChannel` attribute is observed.
    `None` is the default `.midiChannel` for all instruments except
    :class:`~music21.instrument.UnpitchedPercussion`
    subclasses. Put another way, the priority is:

    - Instrument instance `.midiChannel` (set by user or imported from MIDI)
    - `UnpitchedPercussion` subclasses receive MIDI Channel 10 (9 in music21)
    - The channel mappings produced by reading from `acceptableChannelList`,
      or the default range 1-16. (More precisely, 1-15, since one dynamic channel
      is always reserved.)

    .. warning::

        The attribute `.midiChannel` on :class:`~music21.instrument.Instrument`
        is 0-indexed, but `.channel` on :class:`~music21.midi.MidiEvent` is 1-indexed,
        as are all references to channels in this function.
    '''
    # temporary channel allocation
    if acceptableChannelList is not None:
        # copy user input, because we will manipulate it
        acceptableChannels = acceptableChannelList[:]
    else:
        acceptableChannels = list(range(1, 10)) + list(range(11, 17))  # all but 10

    # store program numbers
    # tried using set() but does not guarantee proper order.
    allUniqueInstruments = []

    channelByInstrument = {}  # the midiProgram is the key
    channelsDynamic = []  # remaining channels
    # create an entry for all unique instruments, assign channels
    # for each instrument, assign a channel; if we go above 16, that is fine
    # we just cannot use it and will take modulus later
    channelsAssigned = set()

    # store streams in uniform list
    substreamList = []
    if s.hasPartLikeStreams():
        for obj in s.getElementsByClass('Stream'):
            # Conductor track: don't consume a channel
            if (not obj[note.GeneralNote]) and obj[Conductor]:
                continue
            else:
                substreamList.append(obj)
    else:
        # should not ever run if prepareStreamForMidi() was run...
        substreamList.append(s)  # pragma: no cover

    # Music tracks
    for subs in substreamList:
        # get a first instrument; iterate over rest
        instrumentStream = subs.recurse().getElementsByClass('Instrument')
        setAnInstrument = False
        for inst in instrumentStream:
            if inst.midiChannel is not None and inst.midiProgram not in channelByInstrument:
                # Assignment Case 1: read from instrument.midiChannel
                # .midiChannel is 0-indexed, but MIDI channels are 1-indexed, so convert.
                thisChannel = inst.midiChannel + 1
                try:
                    acceptableChannels.remove(thisChannel)
                except ValueError:
                    # Don't warn if 10 is missing, since
                    # we deliberately made it unavailable above.
                    if thisChannel != 10:
                        # If the user wants multiple non-drum programs mapped
                        # to the same MIDI channel for some reason, solution is to provide an
                        # acceptableChannelList containing duplicate entries.
                        warnings.warn(
                            f'{inst} specified 1-indexed MIDI channel {thisChannel} '
                            f'but acceptable channels were {acceptableChannels}. '
                            'Defaulting to channel 1.',
                            TranslateWarning)
                        thisChannel = 1
                channelsAssigned.add(thisChannel)
                channelByInstrument[inst.midiProgram] = thisChannel
            if inst.midiProgram not in allUniqueInstruments:
                allUniqueInstruments.append(inst.midiProgram)
            setAnInstrument = True

        if not setAnInstrument:
            if None not in allUniqueInstruments:
                allUniqueInstruments.append(None)

    programsStillNeeded = [x for x in allUniqueInstruments if x not in channelByInstrument]

    for i, iPgm in enumerate(programsStillNeeded):
        # the key is the program number; the value is the start channel
        if i < len(acceptableChannels) - 1:  # save at least one dynamic channel
            # Assignment Case 2: dynamically assign available channels
            # if Instrument.midiChannel was None
            channelByInstrument[iPgm] = acceptableChannels[i]
            channelsAssigned.add(acceptableChannels[i])
        else:  # just use 1, and deal with the mess: cannot allocate
            channelByInstrument[iPgm] = acceptableChannels[0]
            channelsAssigned.add(acceptableChannels[0])

    # get the dynamic channels, or those not assigned
    for ch in acceptableChannels:
        if ch not in channelsAssigned:
            channelsDynamic.append(ch)

    return channelByInstrument, channelsDynamic


def packetStorageFromSubstreamList(
    substreamList: List[stream.Part],
    *,
    addStartDelay=False,
) -> Dict[int, Dict[str, Any]]:
    # noinspection PyShadowingNames
    r'''
    Make a dictionary of raw packets and the initial instrument for each
    subStream.

    If the first Part in the list of parts is empty then a new
    :class:`~music21.instrument.Conductor` object will be given as the instrument.

    >>> s = stream.Score()
    >>> p = stream.Part()
    >>> m = stream.Measure(number=1)
    >>> m.append(tempo.MetronomeMark(100))
    >>> m.append(instrument.Oboe())
    >>> m.append(note.Note('C4', type='whole'))  # MIDI 60
    >>> p.append(m)
    >>> s.append(p)
    >>> sOut = midi.translate.prepareStreamForMidi(s)
    >>> partList = list(sOut.parts)
    >>> packetStorage = midi.translate.packetStorageFromSubstreamList(partList)
    >>> list(sorted(packetStorage.keys()))
    [0, 1]
    >>> list(sorted(packetStorage[0].keys()))
    ['initInstrument', 'rawPackets']

    >>> from pprint import pprint
    >>> pprint(packetStorage)
    {0: {'initInstrument': <music21.instrument.Conductor 'Conductor'>,
         'rawPackets': [{'centShift': None,
                         'duration': 0,
                         'lastInstrument': <music21.instrument.Conductor 'Conductor'>,
                         'midiEvent': <music21.midi.MidiEvent SET_TEMPO, ... channel=1, ...>,
                         'obj': <music21.tempo.MetronomeMark Quarter=100>,
                         'offset': 0,
                         'trackId': 0},
                        {'centShift': None,
                         'duration': 0,
                         'lastInstrument': <music21.instrument.Conductor 'Conductor'>,
                         'midiEvent': <music21.midi.MidiEvent TIME_SIGNATURE, ...>,
                         'obj': <music21.meter.TimeSignature 4/4>,
                         'offset': 0,
                         'trackId': 0}]},
     1: {'initInstrument': <music21.instrument.Oboe 'Oboe'>,
         'rawPackets': [{'centShift': None,
                         'duration': 0,
                         'lastInstrument': <music21.instrument.Oboe 'Oboe'>,
                         'midiEvent': <music21.midi.MidiEvent PROGRAM_CHANGE,
                                          track=None, channel=1, data=68>,
                         'obj': <music21.instrument.Oboe 'Oboe'>,
                         'offset': 0,
                         'trackId': 1},
                        {'centShift': None,
                         'duration': 4096,
                         'lastInstrument': <music21.instrument.Oboe 'Oboe'>,
                         'midiEvent': <music21.midi.MidiEvent NOTE_ON,
                                          track=None, channel=1, pitch=60, velocity=90>,
                         'obj': <music21.note.Note C>,
                         'offset': 0,
                         'trackId': 1},
                        {'centShift': None,
                         'duration': 0,
                         'lastInstrument': <music21.instrument.Oboe 'Oboe'>,
                         'midiEvent': <music21.midi.MidiEvent NOTE_OFF,
                                           track=None, channel=1, pitch=60, velocity=0>,
                         'obj': <music21.note.Note C>,
                         'offset': 4096,
                         'trackId': 1}]}}
    '''
    packetStorage = {}

    for trackId, subs in enumerate(substreamList):  # Conductor track is track 0
        subs = subs.flatten()

        # get a first instrument; iterate over rest
        instrumentStream = subs.getElementsByClass('Instrument')

        # if there is an Instrument object at the start, make instObj that instrument
        # this may be a Conductor object if prepareStreamForMidi() was run
        if instrumentStream and subs.elementOffset(instrumentStream[0]) == 0:
            instObj = instrumentStream[0]
        elif trackId == 0 and not subs.notesAndRests:
            # maybe prepareStreamForMidi() wasn't run; create Conductor instance
            instObj = Conductor()
        else:
            instObj = None

        trackPackets = streamToPackets(subs, trackId=trackId, addStartDelay=addStartDelay)
        # store packets in dictionary; keys are trackIds
        packetStorage[trackId] = {
            'rawPackets': trackPackets,
            'initInstrument': instObj,
        }
    return packetStorage


def updatePacketStorageWithChannelInfo(
        packetStorage: Dict[int, Dict[str, Any]],
        channelByInstrument: Dict[Union[int, None], Union[int, None]],
) -> None:
    '''
    Take the packetStorage dictionary and using information
    from 'initInstrument' and channelByInstrument, add an 'initChannel' key to each
    packetStorage bundle and to each rawPacket in the bundle['rawPackets']
    '''
    # update packets with first channel
    for unused_trackId, bundle in packetStorage.items():
        # get instrument
        instObj = bundle['initInstrument']
        if instObj is None:
            try:
                initCh = channelByInstrument[None]
            except KeyError:  # pragma: no cover
                initCh = 1  # fallback, should not happen.
        elif 'Conductor' in instObj.classes:
            initCh = None
        else:  # keys are midi program
            initCh = channelByInstrument[instObj.midiProgram]
        bundle['initChannel'] = initCh  # set for bundle too

        for rawPacket in bundle['rawPackets']:
            rawPacket['initChannel'] = initCh


def streamHierarchyToMidiTracks(
    inputM21,
    *,
    acceptableChannelList=None,
    addStartDelay=False,
):
    '''
    Given a Stream, Score, Part, etc., that may have substreams (i.e.,
    a hierarchy), return a list of :class:`~music21.midi.MidiTrack` objects.

    acceptableChannelList is a list of MIDI Channel numbers that can be used or None.
    If None, then 1-9, 11-16 are used (10 being reserved for percussion).

    In addition, if an :class:`~music21.instrument.Instrument` object in the stream
    has a `.midiChannel` that is not None, that channel is observed, and
    also treated as reserved. Only subclasses of :class:`~music21.instrument.UnpitchedPercussion`
    have a default `.midiChannel`, but users may manipulate this.
    See :func:`channelInstrumentData` for more, and for documentation on `acceptableChannelList`.

    Called by streamToMidiFile()

    The process:

    1. makes a deepcopy of the Stream (Developer TODO: could this
       be done with a shallow copy? Not if ties are stripped and volume realized.)

    2. we make a list of all instruments that are being used in the piece.

    Changed in v.6 -- acceptableChannelList is keyword only.  addStartDelay is new.
    Changed in v.6.5 -- Track 0 (tempo/conductor track) always exported.
    '''
    # makes a deepcopy
    s = prepareStreamForMidi(inputM21)
    channelByInstrument, channelsDynamic = channelInstrumentData(s, acceptableChannelList)

    # return a list of MidiTrack objects
    midiTracks = []

    # TODO: may need to shift all time values to accommodate
    #    Streams that do not start at same time

    # store streams in uniform list: prepareStreamForMidi() ensures there are substreams
    substreamList = []
    for obj in s.getElementsByClass('Stream'):
        # prepareStreamForMidi() supplies defaults for these
        if obj.getElementsByClass(('MetronomeMark', 'TimeSignature')):
            # Ensure conductor track is first
            substreamList.insert(0, obj)
        else:
            substreamList.append(obj)

    # strip all ties inPlace
    for subs in substreamList:
        subs.stripTies(inPlace=True, matchByPitch=True)

    packetStorage = packetStorageFromSubstreamList(substreamList, addStartDelay=addStartDelay)
    updatePacketStorageWithChannelInfo(packetStorage, channelByInstrument)

    initTrackIdToChannelMap = {}
    for trackId, bundle in packetStorage.items():
        initTrackIdToChannelMap[trackId] = bundle['initChannel']  # map trackId to channelId

    # combine all packets for processing of channel allocation
    netPackets = []
    for bundle in packetStorage.values():
        netPackets += bundle['rawPackets']

    # process all channel assignments for all packets together
    netPackets = assignPacketsToChannels(
        netPackets,
        channelByInstrument=channelByInstrument,
        channelsDynamic=channelsDynamic,
        initTrackIdToChannelMap=initTrackIdToChannelMap)

    # environLocal.printDebug(['got netPackets:', len(netPackets),
    #    'packetStorage keys (tracks)', packetStorage.keys()])
    # build each track, sorting out the appropriate packets based on track
    # ids
    for trackId in packetStorage:
        initChannel = packetStorage[trackId]['initChannel']
        instrumentObj = packetStorage[trackId]['initInstrument']
        mt = packetsToMidiTrack(netPackets,
                                trackId=trackId,
                                channel=initChannel,
                                instrumentObj=instrumentObj)
        midiTracks.append(mt)

    return midiTracks


def midiTracksToStreams(
    midiTracks: List['music21.midi.MidiTrack'],
    ticksPerQuarter=None,
    quantizePost=True,
    inputM21: Optional[stream.Score] = None,
    **keywords
) -> stream.Score:
    '''
    Given a list of midiTracks, populate either a new stream.Score or inputM21
    with a Part for each track.
    '''
    # environLocal.printDebug(['midi track count', len(midiTracks)])
    s: stream.Score
    if inputM21 is None:
        s = stream.Score()
    else:
        s = inputM21

    # conductorPart will store common elements such as time sig, key sig
    # from the conductor track (or any track without notes).
    conductorPart = stream.Part()
    firstTrackWithNotes = None
    for mt in midiTracks:
        # not all tracks have notes defined; only creates parts for those
        # that do
        # environLocal.printDebug(['raw midi tracks', mt])
        if mt.hasNotes():
            if firstTrackWithNotes is None:
                firstTrackWithNotes = mt
            streamPart = stream.Part()  # create a part instance for each part
            s.insert(0, streamPart)
        else:
            streamPart = conductorPart

        midiTrackToStream(mt,
                          ticksPerQuarter,
                          quantizePost,
                          inputM21=streamPart,
                          conductorPart=conductorPart,
                          isFirst=(mt is firstTrackWithNotes),
                          **keywords)

    return s


def streamToMidiFile(
    inputM21: stream.Stream,
    *,
    addStartDelay: bool = False,
    acceptableChannelList: Optional[List[int]] = None,
) -> 'music21.midi.MidiFile':
    # noinspection PyShadowingNames
    '''
    Converts a Stream hierarchy into a :class:`~music21.midi.MidiFile` object.

    >>> s = stream.Stream()
    >>> n = note.Note('g#')
    >>> n.quarterLength = 0.5
    >>> s.repeatAppend(n, 4)
    >>> mf = midi.translate.streamToMidiFile(s)
    >>> mf.tracks[0].index  # Track 0: conductor track
    0
    >>> len(mf.tracks[1].events)  # Track 1: music track
    22

    From here, you can call mf.writestr() to get the actual file info.

    >>> sc = scale.PhrygianScale('g')
    >>> s = stream.Stream()
    >>> x=[s.append(note.Note(sc.pitchFromDegree(i % 11), quarterLength=0.25)) for i in range(60)]
    >>> mf = midi.translate.streamToMidiFile(s)
    >>> #_DOCS_SHOW mf.open('/Volumes/disc/_scratch/midi.mid', 'wb')
    >>> #_DOCS_SHOW mf.write()
    >>> #_DOCS_SHOW mf.close()

    See :func:`channelInstrumentData` for documentation on `acceptableChannelList`.
    '''
    from music21 import midi as midiModule

    s = inputM21
    midiTracks = streamHierarchyToMidiTracks(s,
                                             addStartDelay=addStartDelay,
                                             acceptableChannelList=acceptableChannelList,
                                             )

    # may need to update channel information

    mf = midiModule.MidiFile()
    mf.tracks = midiTracks
    mf.ticksPerQuarterNote = defaults.ticksPerQuarter
    return mf


def midiFilePathToStream(
    filePath,
    inputM21=None,
    **keywords
):
    '''
    Used by music21.converter:

    Take in a file path (name of a file on disk) and using `midiFileToStream`,

    return a :class:`~music21.stream.Score` object (or if inputM21 is passed in,
    use that object instead).

    Keywords to control quantization:
    `quantizePost` controls whether to quantize the output. (Default: True)
    `quarterLengthDivisors` allows for overriding the default quantization units
    in defaults.quantizationQuarterLengthDivisors. (Default: (4, 3)).

    >>> sfp = common.getSourceFilePath() #_DOCS_HIDE
    >>> fp = str(sfp / 'midi' / 'testPrimitive' / 'test05.mid') #_DOCS_HIDE
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
    return midiFileToStream(mf, inputM21, **keywords)


def midiAsciiStringToBinaryString(
    midiFormat=1,
    ticksPerQuarterNote=960,
    tracksEventsList=None
) -> bytes:
    r'''
    Convert Ascii midi data to a bytes object (formerly binary midi string).

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
    >>> midiBinaryBytes = midi.translate.midiAsciiStringToBinaryString(tracksEventsList=midiTrack)
    >>> midiBinaryBytes
    b'MThd\x00\x00\x00\x06\x00\x01\x00\x01\x03\xc0MTrk\x00\x00\x00\x04\x00\x901\x0f'

    Note that the name is from pre-Python 3.  There is now in fact nothing called a "binary string"
    it is in fact a bytes object.
    '''
    from music21 import midi as midiModule
    mf = midiModule.MidiFile()

    numTracks = len(tracksEventsList)

    if numTracks == 1:
        mf.format = 1
    else:
        mf.format = midiFormat

    mf.ticksPerQuarterNote = ticksPerQuarterNote

    if tracksEventsList is not None:
        for i in range(numTracks):
            trk = midiModule.MidiTrack(i)   # sets the MidiTrack index parameters
            for j in tracksEventsList[i]:
                me = midiModule.MidiEvent(trk)
                dt = midiModule.DeltaTime(trk)

                chunk_event_param = str(j).split(' ')

                dt.channel = i + 1
                dt.time = int(chunk_event_param[0])

                me.channel = i + 1
                me.pitch = int(chunk_event_param[2], 16)
                me.velocity = int(chunk_event_param[3])

                valid = False
                if chunk_event_param[1] != 'FF':
                    if list(chunk_event_param[1])[0] == '8':
                        me.type = midiModule.ChannelVoiceMessages.NOTE_OFF
                        valid = True
                    elif list(chunk_event_param[1])[0] == '9':
                        valid = True
                        me.type = midiModule.ChannelVoiceMessages.NOTE_ON
                    else:
                        environLocal.warn(f'Unsupported midi event: 0x{chunk_event_param[1]}')
                else:
                    environLocal.warn(f'Unsupported meta event: 0x{chunk_event_param[1]}')

                if valid:
                    trk.events.append(dt)
                    trk.events.append(me)

            mf.tracks.append(trk)

    midiBinStr = b''
    midiBinStr = midiBinStr + mf.writestr()

    return midiBinStr


def midiStringToStream(strData, **keywords):
    r'''
    Convert a string of binary midi data to a Music21 stream.Score object.

    Keywords to control quantization:
    `quantizePost` controls whether to quantize the output. (Default: True)
    `quarterLengthDivisors` allows for overriding the default quantization units
    in defaults.quantizationQuarterLengthDivisors. (Default: (4, 3)).

    N.B. -- this has been somewhat problematic, so use at your own risk.

    >>> midiBinStr = (b'MThd\x00\x00\x00\x06\x00\x01\x00\x01\x04\x00'
    ...               + b'MTrk\x00\x00\x00\x16\x00\xff\x03\x00\x00\xe0\x00@\x00'
    ...               + b'\x90CZ\x88\x00\x80C\x00\x88\x00\xff/\x00')
    >>> s = midi.translate.midiStringToStream(midiBinStr)
    >>> s.show('text')
    {0.0} <music21.stream.Part 0x108aa94f0>
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.instrument.Instrument ''>
            {0.0} <music21.clef.TrebleClef>
            {0.0} <music21.meter.TimeSignature 4/4>
            {0.0} <music21.note.Note G>
            {1.0} <music21.note.Rest dotted-half>
            {4.0} <music21.bar.Barline type=final>
    '''
    from music21 import midi as midiModule

    mf = midiModule.MidiFile()
    # do not need to call open or close on MidiFile instance
    mf.readstr(strData)
    return midiFileToStream(mf, **keywords)


def midiFileToStream(
    mf: 'music21.midi.MidiFile',
    inputM21=None,
    quantizePost=True,
    **keywords
):
    # noinspection PyShadowingNames
    '''
    Note: this is NOT the normal way to read a MIDI file.  The best way is generally:

        score = converter.parse('path/to/file.mid')

    Convert a :class:`~music21.midi.MidiFile` object to a
    :class:`~music21.stream.Stream` object.

    The `inputM21` object can specify an existing Stream (or Stream subclass) to fill.

    Keywords to control quantization:
    `quantizePost` controls whether to quantize the output. (Default: True)
    `quarterLengthDivisors` allows for overriding the default quantization units
    in defaults.quantizationQuarterLengthDivisors. (Default: (4, 3)).

    >>> import os
    >>> fp = common.getSourceFilePath() / 'midi' / 'testPrimitive' / 'test05.mid'
    >>> mf = midi.MidiFile()
    >>> mf.open(fp)
    >>> mf.read()
    >>> mf.close()
    >>> len(mf.tracks)
    1
    >>> s = midi.translate.midiFileToStream(mf)
    >>> s
    <music21.stream.Score ...>
    >>> len(s.flatten().notesAndRests)
    14
    '''
    # environLocal.printDebug(['got midi file: tracks:', len(mf.tracks)])
    if inputM21 is None:
        s = stream.Score()
    else:
        s = inputM21

    if not mf.tracks:
        raise exceptions21.StreamException('no tracks are defined in this MIDI file.')

    if 'quantizePost' in keywords:
        quantizePost = keywords.pop('quantizePost')

    # create a stream for each tracks
    # may need to check if tracks actually have event data
    midiTracksToStreams(mf.tracks,
                        ticksPerQuarter=mf.ticksPerQuarterNote,
                        quantizePost=quantizePost,
                        inputM21=s,
                        **keywords)
    # s._setMidiTracks(mf.tracks, mf.ticksPerQuarterNote)

    return s


# ------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def testMidiAsciiStringToBinaryString(self):
        from binascii import a2b_hex

        asciiMidiEventList = []
        asciiMidiEventList.append('0 90 1f 15')
        # asciiMidiEventList.append('3840 80 1f 15')
        # asciiMidiEventList.append('0 b0 7b 00')

        # asciiMidiEventList = ['0 90 27 66', '3840 80 27 00']
        # asciiMidiEventList = ['0 90 27 66', '0 90 3e 60', '3840 80 27 00', '0 80 3e 00',
        #    '0 90 3b 60', '960 80 3b 00', '0 90 41 60', '960 80 41 00', '0 90 3e 60',
        #    '1920 80 3e 00', '0 b0 7b 00', '0 90 24 60', '3840 80 24 00', '0 b0 7b 00']
        # asciiMidiEventList = ['0 90 27 66', '0 90 3e 60', '3840 80 27 00', '0 80 3e 00',
        #    '0 90 3b 60', '960 80 3b 00', '0 90 41 60', '960 80 41 00',
        #    '0 90 3e 60', '1920 80 3e 00', '0 90 24 60', '3840 80 24 00']

        midiTrack = []
        midiTrack.append(asciiMidiEventList)
        # midiTrack.append(asciiMidiEventList)
        # midiTrack.append(asciiMidiEventList)

        midiBinStr = midiAsciiStringToBinaryString(tracksEventsList=midiTrack)

        self.assertEqual(midiBinStr,
                         b'MThd' + a2b_hex('000000060001000103c0')
                         + b'MTrk' + a2b_hex('0000000400901f0f'))

    def testNote(self):
        from music21 import midi as midiModule

        n1 = note.Note('A4')
        n1.quarterLength = 2.0
        eventList = noteToMidiEvents(n1)
        self.assertEqual(len(eventList), 4)

        self.assertIsInstance(eventList[0], midiModule.DeltaTime)
        self.assertIsInstance(eventList[2], midiModule.DeltaTime)

        # translate eventList back to a note
        n2 = midiEventsToNote(eventList)
        self.assertEqual(n2.pitch.nameWithOctave, 'A4')
        self.assertEqual(n2.quarterLength, 2.0)

    def testStripTies(self):
        from music21.midi import ChannelVoiceMessages
        from music21 import tie

        # Stream without measures
        s = stream.Stream()
        n = note.Note('C4', quarterLength=1.0)
        n.tie = tie.Tie('start')
        n2 = note.Note('C4', quarterLength=1.0)
        n2.tie = tie.Tie('stop')
        n3 = note.Note('C4', quarterLength=1.0)
        n4 = note.Note('C4', quarterLength=1.0)
        s.append([n, n2, n3, n4])

        trk = streamHierarchyToMidiTracks(s)[1]
        mt1noteOnOffEventTypes = [event.type for event in trk.events if event.type in (
            ChannelVoiceMessages.NOTE_ON, ChannelVoiceMessages.NOTE_OFF)]

        # Expected result: three pairs of NOTE_ON, NOTE_OFF messages
        # https://github.com/cuthbertLab/music21/issues/266
        self.assertListEqual(mt1noteOnOffEventTypes,
            [ChannelVoiceMessages.NOTE_ON, ChannelVoiceMessages.NOTE_OFF] * 3)

        # Stream with measures
        s.makeMeasures(inPlace=True)
        trk = streamHierarchyToMidiTracks(s)[1]
        mt2noteOnOffEventTypes = [event.type for event in trk.events if event.type in (
            ChannelVoiceMessages.NOTE_ON, ChannelVoiceMessages.NOTE_OFF)]

        self.assertListEqual(mt2noteOnOffEventTypes,
            [ChannelVoiceMessages.NOTE_ON, ChannelVoiceMessages.NOTE_OFF] * 3)

    def testTimeSignature(self):
        from music21 import meter
        n = note.Note()
        n.quarterLength = 0.5
        s = stream.Stream()
        for i in range(20):
            s.append(copy.deepcopy(n))

        s.insert(0, meter.TimeSignature('3/4'))
        s.insert(3, meter.TimeSignature('5/4'))
        s.insert(8, meter.TimeSignature('2/4'))

        mt = streamHierarchyToMidiTracks(s)[0]
        # self.assertEqual(str(mt.events), match)
        self.assertEqual(len(mt.events), 10)

        # s.show('midi')

        # get and compare just the conductor tracks
        # mtAlt = streamHierarchyToMidiTracks(s.getElementsByClass('TimeSignature').stream())[0]
        conductorEvents = repr(mt.events)

        match = '''[<music21.midi.DeltaTime (empty) track=0, channel=None>,
        <music21.midi.MidiEvent SET_TEMPO, track=0, channel=None, data=b'\\x07\\xa1 '>,
        <music21.midi.DeltaTime (empty) track=0, channel=None>,
        <music21.midi.MidiEvent TIME_SIGNATURE, track=0, channel=None,
            data=b'\\x03\\x02\\x18\\x08'>,
        <music21.midi.DeltaTime t=3072, track=0, channel=None>,
        <music21.midi.MidiEvent TIME_SIGNATURE, track=0, channel=None,
            data=b'\\x05\\x02\\x18\\x08'>,
        <music21.midi.DeltaTime t=5120, track=0, channel=None>,
        <music21.midi.MidiEvent TIME_SIGNATURE, track=0, channel=None,
            data=b'\\x02\\x02\\x18\\x08'>,
        <music21.midi.DeltaTime t=1024, track=0, channel=None>,
        <music21.midi.MidiEvent END_OF_TRACK, track=0, channel=None, data=b''>]'''

        self.assertTrue(common.whitespaceEqual(conductorEvents, match), conductorEvents)

    def testKeySignature(self):
        from music21 import meter

        n = note.Note()
        n.quarterLength = 0.5
        s = stream.Stream()
        for i in range(20):
            s.append(copy.deepcopy(n))

        s.insert(0, meter.TimeSignature('3/4'))
        s.insert(3, meter.TimeSignature('5/4'))
        s.insert(8, meter.TimeSignature('2/4'))

        s.insert(0, key.KeySignature(4))
        s.insert(3, key.KeySignature(-5))
        s.insert(8, key.KeySignature(6))

        conductor = streamHierarchyToMidiTracks(s)[0]
        self.assertEqual(len(conductor.events), 16)

        # s.show('midi')

    def testChannelAllocation(self):
        # test instrument assignments
        iList = [instrument.Harpsichord,
                 instrument.Viola,
                 instrument.ElectricGuitar,
                 instrument.Flute,
                 instrument.Vibraphone,  # not 10
                 instrument.BassDrum,  # 10
                 instrument.HiHatCymbal,  # 10
                 ]
        iObjs = []

        s = stream.Score()
        for i, instClass in enumerate(iList):
            p = stream.Part()
            inst = instClass()
            iObjs.append(inst)
            p.insert(0, inst)  # must call instrument to create instance
            p.append(note.Note('C#'))
            s.insert(0, p)

        channelByInstrument, channelsDynamic = channelInstrumentData(s)

        # Default allocations
        self.assertEqual(channelByInstrument.keys(), set(inst.midiProgram for inst in iObjs))
        self.assertSetEqual(set(channelByInstrument.values()), {1, 2, 3, 4, 5, 10})
        self.assertListEqual(channelsDynamic, [6, 7, 8, 9, 11, 12, 13, 14, 15, 16])

        # Limit to given acceptable channels
        acl = list(range(11, 17))
        channelByInstrument, channelsDynamic = channelInstrumentData(s, acceptableChannelList=acl)
        self.assertEqual(channelByInstrument.keys(), set(inst.midiProgram for inst in iObjs))
        self.assertSetEqual(set(channelByInstrument.values()), {10, 11, 12, 13, 14, 15})
        self.assertListEqual(channelsDynamic, [16])

        # User specification
        for i, iObj in enumerate(iObjs):
            iObj.midiChannel = 15 - i

        channelByInstrument, channelsDynamic = channelInstrumentData(s)

        self.assertEqual(channelByInstrument.keys(), set(inst.midiProgram for inst in iObjs))
        self.assertSetEqual(set(channelByInstrument.values()), {11, 12, 13, 14, 15, 16})
        self.assertListEqual(channelsDynamic, [1, 2, 3, 4, 5, 6, 7, 8, 9])

        # User error
        iObjs[0].midiChannel = 100
        want = 'Harpsichord specified 1-indexed MIDI channel 101 but '
        want += r'acceptable channels were \[1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13, 14, 15, 16\]. '
        want += 'Defaulting to channel 1.'
        with self.assertWarnsRegex(TranslateWarning, want):
            channelByInstrument, channelsDynamic = channelInstrumentData(s)
        self.assertEqual(channelByInstrument.keys(), set(inst.midiProgram for inst in iObjs))
        self.assertSetEqual(set(channelByInstrument.values()), {1, 11, 12, 13, 14, 15})
        self.assertListEqual(channelsDynamic, [2, 3, 4, 5, 6, 7, 8, 9, 16])

    def testPacketStorage(self):
        # test instrument assignments
        iList = [None,  # conductor track
                 instrument.Harpsichord,
                 instrument.Viola,
                 instrument.ElectricGuitar,
                 instrument.Flute,
                 None]
        iObjs = []

        substreamList = []
        for i, instClass in enumerate(iList):
            p = stream.Part()
            if instClass is not None:
                inst = instClass()
                iObjs.append(inst)
                p.insert(0, inst)  # must call instrument to create instance
            if i != 0:
                p.append(note.Note('C#'))
            substreamList.append(p)

        packetStorage = packetStorageFromSubstreamList(substreamList, addStartDelay=False)
        self.assertIsInstance(packetStorage, dict)
        self.assertEqual(list(packetStorage.keys()), [0, 1, 2, 3, 4, 5])

        harpsPacket = packetStorage[1]
        self.assertIsInstance(harpsPacket, dict)
        self.assertSetEqual(set(harpsPacket.keys()),
                            {'rawPackets', 'initInstrument'})
        self.assertIs(harpsPacket['initInstrument'], iObjs[0])
        self.assertIsInstance(harpsPacket['rawPackets'], list)
        self.assertTrue(harpsPacket['rawPackets'])
        self.assertIsInstance(harpsPacket['rawPackets'][0], dict)

        channelInfo = {
            iObjs[0].midiProgram: 1,
            iObjs[1].midiProgram: 2,
            iObjs[2].midiProgram: 3,
            iObjs[3].midiProgram: 4,
            None: 5,
        }

        updatePacketStorageWithChannelInfo(packetStorage, channelInfo)
        self.assertSetEqual(set(harpsPacket.keys()),
                            {'rawPackets', 'initInstrument', 'initChannel'})
        self.assertEqual(harpsPacket['initChannel'], 1)
        self.assertEqual(harpsPacket['rawPackets'][-1]['initChannel'], 1)

    def testAnacrusisTiming(self):
        from music21 import corpus

        s = corpus.parse('bach/bwv103.6')

        # get just the soprano part
        soprano = s.parts['soprano']
        mts = streamHierarchyToMidiTracks(soprano)[1]  # get one

        # first note-on is not delayed, even w anacrusis
        match = '''
        [<music21.midi.DeltaTime (empty) track=1, channel=1>,
         <music21.midi.MidiEvent SEQUENCE_TRACK_NAME, track=1, channel=1, data=b'Soprano'>,
         <music21.midi.DeltaTime (empty) track=1, channel=1>,
         <music21.midi.MidiEvent PITCH_BEND, track=1, channel=1, parameter1=0, parameter2=64>,
         <music21.midi.DeltaTime (empty) track=1, channel=1>]'''

        self.maxDiff = None
        found = str(mts.events[:5])
        self.assertTrue(common.whitespaceEqual(found, match), found)

        # first note-on is not delayed, even w anacrusis
        match = '''
        [<music21.midi.DeltaTime (empty) track=1, channel=1>,
        <music21.midi.MidiEvent SEQUENCE_TRACK_NAME, track=1, channel=1, data=b'Alto'>,
        <music21.midi.DeltaTime (empty) track=1, channel=1>,
        <music21.midi.MidiEvent PITCH_BEND, track=1, channel=1, parameter1=0, parameter2=64>,
        <music21.midi.DeltaTime (empty) track=1, channel=1>,
        <music21.midi.MidiEvent PROGRAM_CHANGE, track=1, channel=1, data=0>,
        <music21.midi.DeltaTime (empty) track=1, channel=1>,
        <music21.midi.MidiEvent NOTE_ON, track=1, channel=1, pitch=62, velocity=90>]'''

        alto = s.parts['alto']
        mta = streamHierarchyToMidiTracks(alto)[1]

        found = str(mta.events[:8])
        self.assertTrue(common.whitespaceEqual(found, match), found)

        # try streams to midi tracks
        # get just the soprano part
        soprano = s.parts['soprano']
        mtList = streamHierarchyToMidiTracks(soprano)
        self.assertEqual(len(mtList), 2)

        # it's the same as before
        match = '''[<music21.midi.DeltaTime (empty) track=1, channel=1>,
        <music21.midi.MidiEvent SEQUENCE_TRACK_NAME, track=1, channel=1, data=b'Soprano'>,
        <music21.midi.DeltaTime (empty) track=1, channel=1>,
        <music21.midi.MidiEvent PITCH_BEND, track=1, channel=1, parameter1=0, parameter2=64>,
        <music21.midi.DeltaTime (empty) track=1, channel=1>,
        <music21.midi.MidiEvent PROGRAM_CHANGE, track=1, channel=1, data=0>,
        <music21.midi.DeltaTime (empty) track=1, channel=1>,
        <music21.midi.MidiEvent NOTE_ON, track=1, channel=1, pitch=66, velocity=90>,
        <music21.midi.DeltaTime t=512, track=1, channel=1>,
        <music21.midi.MidiEvent NOTE_OFF, track=1, channel=1, pitch=66, velocity=0>]'''
        found = str(mtList[1].events[:10])
        self.assertTrue(common.whitespaceEqual(found, match), found)

    def testMidiProgramChangeA(self):
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
        # p1.show()
        # s.show('midi')

    def testMidiProgramChangeB(self):
        from music21 import scale
        import random

        iList = [instrument.Harpsichord,
                 instrument.Clavichord, instrument.Accordion,
                 instrument.Celesta, instrument.Contrabass, instrument.Viola,
                 instrument.Harp, instrument.ElectricGuitar, instrument.Ukulele,
                 instrument.Banjo, instrument.Piccolo, instrument.AltoSaxophone,
                 instrument.Trumpet]

        sc = scale.MinorScale()
        pitches = sc.getPitches('c2', 'c5')
        random.shuffle(pitches)

        s = stream.Stream()
        for i in range(30):
            n = note.Note(pitches[i % len(pitches)])
            n.quarterLength = 0.5
            inst = iList[i % len(iList)]()  # call to create instance
            s.append(inst)
            s.append(n)

        unused_mts = streamHierarchyToMidiTracks(s)

        # s.show('midi')

    def testOverlappedEventsA(self):
        from music21 import corpus
        s = corpus.parse('bwv66.6')
        sFlat = s.flatten()
        mtList = streamHierarchyToMidiTracks(sFlat)
        self.assertEqual(len(mtList), 2)

        # it's the same as before
        match = '''[<music21.midi.MidiEvent NOTE_ON, track=1, channel=1, pitch=66, velocity=90>,
        <music21.midi.DeltaTime (empty) track=1, channel=1>,
        <music21.midi.MidiEvent NOTE_ON, track=1, channel=1, pitch=61, velocity=90>,
        <music21.midi.DeltaTime (empty) track=1, channel=1>,
        <music21.midi.MidiEvent NOTE_ON, track=1, channel=1, pitch=58, velocity=90>,
        <music21.midi.DeltaTime (empty) track=1, channel=1>,
        <music21.midi.MidiEvent NOTE_ON, track=1, channel=1, pitch=54, velocity=90>,
        <music21.midi.DeltaTime t=1024, track=1, channel=1>,
        <music21.midi.MidiEvent NOTE_OFF, track=1, channel=1, pitch=66, velocity=0>,
        <music21.midi.DeltaTime (empty) track=1, channel=1>,
        <music21.midi.MidiEvent NOTE_OFF, track=1, channel=1, pitch=61, velocity=0>,
        <music21.midi.DeltaTime (empty) track=1, channel=1>,
        <music21.midi.MidiEvent NOTE_OFF, track=1, channel=1, pitch=58, velocity=0>,
        <music21.midi.DeltaTime (empty) track=1, channel=1>,
        <music21.midi.MidiEvent NOTE_OFF, track=1, channel=1, pitch=54, velocity=0>,
        <music21.midi.DeltaTime t=1024, track=1, channel=1>,
        <music21.midi.MidiEvent END_OF_TRACK, track=1, channel=1, data=b''>]'''

        results = str(mtList[1].events[-17:])
        self.assertTrue(common.whitespaceEqual(results, match), results)

    def testOverlappedEventsB(self):
        from music21 import scale
        import random

        sc = scale.MajorScale()
        pitches = sc.getPitches('c2', 'c5')
        random.shuffle(pitches)

        dur = 16
        step = 0.5
        o = 0
        s = stream.Stream()
        for p in pitches:
            n = note.Note(p)
            n.quarterLength = dur - o
            s.insert(o, n)
            o = o + step

        unused_mt = streamHierarchyToMidiTracks(s)[0]

        # s.plot('pianoroll')
        # s.show('midi')

    def testOverlappedEventsC(self):
        from music21 import meter

        s = stream.Stream()
        s.insert(key.KeySignature(3))
        s.insert(meter.TimeSignature('2/4'))
        s.insert(0, note.Note('c'))
        n = note.Note('g')
        n.pitch.microtone = 25
        s.insert(0, n)

        c = chord.Chord(['d', 'f', 'a'], type='half')
        c.pitches[1].microtone = -50
        s.append(c)

        pos = s.highestTime
        s.insert(pos, note.Note('e'))
        s.insert(pos, note.Note('b'))

        unused_mt = streamHierarchyToMidiTracks(s)[0]

        # s.show('midi')

    def testExternalMidiProgramChangeB(self):
        from music21 import scale

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
        # random.shuffle(pitches)

        s = stream.Stream()
        for i, p in enumerate(pitches):
            n = note.Note(p)
            n.quarterLength = 1.5
            inst = iList[i]()  # call to create instance
            s.append(inst)
            s.append(n)

        unused_mts = streamHierarchyToMidiTracks(s)
        # s.show('midi')

    def testMicrotonalOutputA(self):
        s = stream.Stream()
        s.append(note.Note('c4', type='whole'))
        s.append(note.Note('c~4', type='whole'))
        s.append(note.Note('c#4', type='whole'))
        s.append(note.Note('c#~4', type='whole'))
        s.append(note.Note('d4', type='whole'))

        # mts = streamHierarchyToMidiTracks(s)

        s.insert(0, note.Note('g3', quarterLength=10))
        unused_mts = streamHierarchyToMidiTracks(s)

    def testMicrotonalOutputB(self):
        # a two-part stream
        from music21.midi import translate

        p1 = stream.Part()
        p1.append(note.Note('c4', type='whole'))
        p1.append(note.Note('c~4', type='whole'))
        p1.append(note.Note('c#4', type='whole'))
        p1.append(note.Note('c#~4', type='whole'))
        p1.append(note.Note('d4', type='whole'))

        # mts = translate.streamHierarchyToMidiTracks(s)
        p2 = stream.Part()
        p2.insert(0, note.Note('g2', quarterLength=20))

        # order here matters: this needs to be fixed
        s = stream.Score()
        s.insert(0, p1)
        s.insert(0, p2)

        mts = translate.streamHierarchyToMidiTracks(s)
        self.assertEqual(mts[1].getChannels(), [1])
        self.assertEqual(mts[2].getChannels(), [1, 2])
        # print(mts)
        # s.show('midi')

        # recreate with different order
        s = stream.Score()
        s.insert(0, p2)
        s.insert(0, p1)

        mts = translate.streamHierarchyToMidiTracks(s)
        self.assertEqual(mts[1].getChannels(), [1])
        self.assertEqual(mts[2].getChannels(), [1, 2])

    def testInstrumentAssignments(self):
        # test instrument assignments
        iList = [instrument.Harpsichord,
                 instrument.Viola,
                 instrument.ElectricGuitar,
                 instrument.Flute]

        # number of notes, ql, pitch
        params = [(8, 1, 'C6'),
                  (4, 2, 'G3'),
                  (2, 4, 'E4'),
                  (6, 1.25, 'C5')]

        s = stream.Score()
        for i, inst in enumerate(iList):
            p = stream.Part()
            p.insert(0, inst())  # must call instrument to create instance

            number, ql, pitchName = params[i]
            for j in range(number):
                p.append(note.Note(pitchName, quarterLength=ql))
            s.insert(0, p)

        # s.show('midi')
        mts = streamHierarchyToMidiTracks(s)
        # print(mts[0])
        self.assertEqual(mts[0].getChannels(), [])  # Conductor track
        self.assertEqual(mts[1].getChannels(), [1])
        self.assertEqual(mts[2].getChannels(), [2])
        self.assertEqual(mts[3].getChannels(), [3])
        self.assertEqual(mts[4].getChannels(), [4])

    def testMicrotonalOutputD(self):
        # test instrument assignments with microtones
        from music21.midi import translate

        iList = [instrument.Harpsichord,
                 instrument.Viola,
                 instrument.ElectricGuitar,
                 instrument.Flute
                 ]

        # number of notes, ql, pitch
        params = [(8, 1, ['C6']),
                  (4, 2, ['G3', 'G~3']),
                  (2, 4, ['E4', 'E5']),
                  (6, 1.25, ['C5'])]

        s = stream.Score()
        for i, inst in enumerate(iList):
            p = stream.Part()
            p.insert(0, inst())  # must call instrument to create instance

            number, ql, pitchNameList = params[i]
            for j in range(number):
                p.append(note.Note(pitchNameList[j % len(pitchNameList)], quarterLength=ql))
            s.insert(0, p)

        # s.show('midi')
        mts = translate.streamHierarchyToMidiTracks(s)
        # print(mts[1])
        self.assertEqual(mts[1].getChannels(), [1])
        self.assertEqual(mts[1].getProgramChanges(), [6])  # 6 = GM Harpsichord

        self.assertEqual(mts[2].getChannels(), [2, 5])
        self.assertEqual(mts[2].getProgramChanges(), [41])  # 41 = GM Viola

        self.assertEqual(mts[3].getChannels(), [3, 6])
        self.assertEqual(mts[3].getProgramChanges(), [26])  # 26 = GM ElectricGuitar
        # print(mts[3])

        self.assertEqual(mts[4].getChannels(), [4, 6])
        self.assertEqual(mts[4].getProgramChanges(), [73])  # 73 = GM Flute

        # s.show('midi')

    def testMicrotonalOutputE(self):
        from music21 import corpus
        from music21 import interval
        s = corpus.parse('bwv66.6')
        p1 = s.parts[0]
        p2 = copy.deepcopy(p1)
        t = interval.Interval(0.5)  # half sharp
        p2.transpose(t, inPlace=True, classFilterList=('Note', 'Chord'))
        post = stream.Score()
        post.insert(0, p1)
        post.insert(0, p2)

        # post.show('midi')

        mts = streamHierarchyToMidiTracks(post)
        self.assertEqual(mts[1].getChannels(), [1])
        self.assertEqual(mts[1].getProgramChanges(), [0])
        self.assertEqual(mts[2].getChannels(), [1, 2])
        self.assertEqual(mts[2].getProgramChanges(), [0])

        # post.show('midi', app='Logic Express')

    def testMicrotonalOutputF(self):
        from music21 import corpus
        from music21 import interval
        s = corpus.parse('bwv66.6')
        p1 = s.parts[0]
        p2 = copy.deepcopy(p1)
        p3 = copy.deepcopy(p1)

        t1 = interval.Interval(12.5)  # octave + half sharp
        t2 = interval.Interval(-12.25)  # octave down minus 1/8th tone
        p2.transpose(t1, inPlace=True, classFilterList=('Note', 'Chord'))
        p3.transpose(t2, inPlace=True, classFilterList=('Note', 'Chord'))
        post = stream.Score()
        post.insert(0, p1)
        post.insert(0, p2)
        post.insert(0, p3)

        # post.show('midi')

        mts = streamHierarchyToMidiTracks(post)
        self.assertEqual(mts[1].getChannels(), [1])
        self.assertEqual(mts[1].getProgramChanges(), [0])
        self.assertEqual(mts[2].getChannels(), [1, 2])
        self.assertEqual(mts[2].getProgramChanges(), [0])
        self.assertEqual(mts[3].getChannels(), [1, 3])
        self.assertEqual(mts[3].getProgramChanges(), [0])

        # post.show('midi', app='Logic Express')

    def testMicrotonalOutputG(self):
        from music21 import corpus
        from music21 import interval
        s = corpus.parse('bwv66.6')
        p1 = s.parts[0]
        p1.remove(p1.getElementsByClass('Instrument').first())
        p2 = copy.deepcopy(p1)
        p3 = copy.deepcopy(p1)

        t1 = interval.Interval(12.5)  # a sharp p4
        t2 = interval.Interval(-7.25)  # a sharp p4
        p2.transpose(t1, inPlace=True, classFilterList=('Note', 'Chord'))
        p3.transpose(t2, inPlace=True, classFilterList=('Note', 'Chord'))
        post = stream.Score()
        p1.insert(0, instrument.Dulcimer())
        post.insert(0, p1)
        p2.insert(0, instrument.Trumpet())
        post.insert(0.125, p2)
        p3.insert(0, instrument.ElectricGuitar())
        post.insert(0.25, p3)

        # post.show('midi')

        mts = streamHierarchyToMidiTracks(post)
        self.assertEqual(mts[1].getChannels(), [1])
        self.assertEqual(mts[1].getProgramChanges(), [15])

        self.assertEqual(mts[2].getChannels(), [2, 4])
        self.assertEqual(mts[2].getProgramChanges(), [56])

        # print(mts[3])
        self.assertEqual(mts[3].getChannels(), [3, 5])
        self.assertEqual(mts[3].getProgramChanges(), [26])

        # post.show('midi')#, app='Logic Express')

    def testMidiTempoImportA(self):
        from music21 import converter

        dirLib = common.getSourceFilePath() / 'midi' / 'testPrimitive'
        # a simple file created in athenacl
        fp = dirLib / 'test10.mid'
        s = converter.parse(fp)
        mmStream = s.flatten().getElementsByClass('MetronomeMark')
        self.assertEqual(len(mmStream), 4)
        self.assertEqual(mmStream[0].number, 120.0)
        self.assertEqual(mmStream[1].number, 110.0)
        self.assertEqual(mmStream[2].number, 90.0)
        self.assertEqual(mmStream[3].number, 60.0)

        fp = dirLib / 'test06.mid'
        s = converter.parse(fp)
        mmStream = s.flatten().getElementsByClass('MetronomeMark')
        self.assertEqual(len(mmStream), 1)
        self.assertEqual(mmStream[0].number, 120.0)

        fp = dirLib / 'test07.mid'
        s = converter.parse(fp)
        mmStream = s.flatten().getElementsByClass('MetronomeMark')
        self.assertEqual(len(mmStream), 1)
        self.assertEqual(mmStream[0].number, 180.0)

    def testMidiTempoImportB(self):
        from music21 import converter

        dirLib = common.getSourceFilePath() / 'midi' / 'testPrimitive'
        # a file with three tracks and one conductor track with four tempo marks
        fp = dirLib / 'test11.mid'
        s = converter.parse(fp)
        self.assertEqual(len(s.parts), 3)
        # metronome marks propagate to every staff, but are hidden on subsequent staffs
        self.assertEqual(
            [mm.numberImplicit for mm in s.parts[0].recurse().getElementsByClass('MetronomeMark')],
            [False, False, False, False]
        )
        self.assertEqual(
            [mm.numberImplicit for mm in s.parts[1].recurse().getElementsByClass('MetronomeMark')],
            [True, True, True, True]
        )
        self.assertEqual(
            [mm.numberImplicit for mm in s.parts[2].recurse().getElementsByClass('MetronomeMark')],
            [True, True, True, True]
        )

    def testMidiImportMeter(self):
        from music21 import converter
        fp = common.getSourceFilePath() / 'midi' / 'testPrimitive' / 'test17.mid'
        s = converter.parse(fp)
        for p in s.parts:
            m = p.getElementsByClass('Measure').first()
            ts = m.timeSignature
            self.assertEqual(ts.ratioString, '3/4')
            self.assertIn(ts, m)

    def testMidiImportImplicitMeter(self):
        from music21 import midi as midiModule
        fp = common.getSourceFilePath() / 'midi' / 'testPrimitive' / 'test10.mid'

        # Not the normal way to read a midi file, but we're altering it
        mf = midiModule.MidiFile()
        mf.open(fp)
        mf.read()
        mf.close()

        # Simulate a file with a conductor track
        new_track = midiModule.MidiTrack()
        # Include some events, like part name, but NOT meter
        new_track.events = mf.tracks[0].events[:4]
        mf.tracks.insert(0, new_track)

        s = midiFileToStream(mf)
        for p in s.parts:
            m = p.getElementsByClass('Measure').first()
            ts = m.timeSignature
            self.assertEqual(ts.ratioString, '4/4')
            self.assertIn(ts, m)

    def testMidiExportConductorA(self):
        '''Export conductor data to MIDI conductor track.'''
        from music21 import meter
        from music21 import tempo

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
        self.assertEqual(len(mts), 3)

        # Tempo and time signature should be in conductor track only
        condTrkRepr = repr(mts[0].events)
        self.assertEqual(condTrkRepr.count('SET_TEMPO'), 2)
        self.assertEqual(condTrkRepr.count('TIME_SIGNATURE'), 2)

        musicTrkRepr = repr(mts[1].events)
        self.assertEqual(musicTrkRepr.find('SET_TEMPO'), -1)
        self.assertEqual(musicTrkRepr.find('TIME_SIGNATURE'), -1)

        # s.show('midi')
        # s.show('midi', app='Logic Express')

    def testMidiExportConductorB(self):
        from music21 import tempo
        from music21 import corpus
        s = corpus.parse('bwv66.6')
        s.insert(0, tempo.MetronomeMark(number=240))
        s.insert(4, tempo.MetronomeMark(number=30))
        s.insert(6, tempo.MetronomeMark(number=120))
        s.insert(8, tempo.MetronomeMark(number=90))
        s.insert(12, tempo.MetronomeMark(number=360))
        # s.show('midi')

        mts = streamHierarchyToMidiTracks(s)
        condTrkRepr = repr(mts[0].events)
        self.assertEqual(condTrkRepr.count('SET_TEMPO'), 5)
        musicTrkRepr = repr(mts[1].events)
        self.assertEqual(musicTrkRepr.count('SET_TEMPO'), 0)

    def testMidiExportConductorC(self):
        from music21 import tempo
        minTempo = 60
        maxTempo = 600
        period = 50
        s = stream.Stream()
        for i in range(100):
            scalar = (math.sin(i * (math.pi * 2) / period) + 1) * 0.5
            n = ((maxTempo - minTempo) * scalar) + minTempo
            s.append(tempo.MetronomeMark(number=n))
            s.append(note.Note('g3'))
        mts = streamHierarchyToMidiTracks(s)
        self.assertEqual(len(mts), 2)
        mtsRepr = repr(mts[0].events)
        self.assertEqual(mtsRepr.count('SET_TEMPO'), 100)

    def testMidiExportConductorD(self):
        '''120 bpm and 4/4 are supplied by default.'''
        s = stream.Stream()
        s.insert(note.Note())
        mts = streamHierarchyToMidiTracks(s)
        self.assertEqual(len(mts), 2)
        condTrkRepr = repr(mts[0].events)
        self.assertEqual(condTrkRepr.count('SET_TEMPO'), 1)
        self.assertEqual(condTrkRepr.count('TIME_SIGNATURE'), 1)
        # No pitch bend events in conductor track
        self.assertEqual(condTrkRepr.count('PITCH_BEND'), 0)

    def testMidiExportConductorE(self):
        '''The conductor only gets the first element at an offset.'''
        from music21 import converter
        from music21 import tempo

        s = stream.Stream()
        p1 = converter.parse('tinynotation: c1')
        p2 = converter.parse('tinynotation: d2 d2')
        p1.insert(0, tempo.MetronomeMark(number=44))
        p2.insert(0, tempo.MetronomeMark(number=144))
        p2.insert(2, key.KeySignature(-5))
        s.insert(0, p1)
        s.insert(0, p2)

        conductor = conductorStream(s)
        tempos = conductor.getElementsByClass('MetronomeMark')
        keySignatures = conductor.getElementsByClass('KeySignature')
        self.assertEqual(len(tempos), 1)
        self.assertEqual(tempos[0].number, 44)
        self.assertEqual(len(keySignatures), 1)

    def testMidiExportConductorF(self):
        '''Multiple meter changes'''
        from music21 import converter
        from music21 import midi as midiModule

        source_dir = common.getSourceFilePath() / 'musicxml' / 'lilypondTestSuite'
        s = converter.parse(source_dir / '11a-TimeSignatures.xml')
        self.assertEqual(len(s['TimeSignature']), 11)

        mf = streamToMidiFile(s)
        conductor = mf.tracks[0]
        meter_events = [
            e for e in conductor.events if e.type is midiModule.MetaEvents.TIME_SIGNATURE]
        self.assertEqual(len(meter_events), 11)

    def testMidiExportVelocityA(self):
        s = stream.Stream()
        for i in range(10):
            # print(i)
            n = note.Note('c3')
            n.volume.velocityScalar = i / 10
            n.volume.velocityIsRelative = False
            s.append(n)

        # s.show('midi')
        mts = streamHierarchyToMidiTracks(s)
        mtsRepr = repr(mts[1].events)
        self.assertEqual(mtsRepr.count('velocity=114'), 1)
        self.assertEqual(mtsRepr.count('velocity=13'), 1)

    def testMidiExportVelocityB(self):
        import random
        from music21 import volume

        s1 = stream.Stream()
        shift = [0, 6, 12]
        amps = [(x / 10. + 0.4) for x in range(6)]
        amps = amps + list(reversed(amps))

        qlList = [1.5] * 6 + [1] * 8 + [2] * 6 + [1.5] * 8 + [1] * 4
        for j, ql in enumerate(qlList):
            if random.random() > 0.6:
                c = note.Rest()
            else:
                c = chord.Chord(['c3', 'd-4', 'g5'])
                vChord = []
                for i, unused_cSub in enumerate(c):
                    v = volume.Volume()
                    v.velocityScalar = amps[(j + shift[i]) % len(amps)]
                    v.velocityIsRelative = False
                    vChord.append(v)
                c.volume = vChord  # can set to list
            c.duration.quarterLength = ql
            s1.append(c)

        s2 = stream.Stream()
        random.shuffle(qlList)
        random.shuffle(amps)
        for j, ql in enumerate(qlList):
            n = note.Note(random.choice(['f#2', 'f#2', 'e-2']))
            n.duration.quarterLength = ql
            n.volume.velocityScalar = amps[j % len(amps)]
            s2.append(n)

        s = stream.Score()
        s.insert(0, s1)
        s.insert(0, s2)

        mts = streamHierarchyToMidiTracks(s)
        # mts[0] is the conductor track
        self.assertIn("SET_TEMPO", repr(mts[0].events))
        mtsRepr = repr(mts[1].events) + repr(mts[2].events)
        self.assertGreater(mtsRepr.count('velocity=51'), 2)
        self.assertGreater(mtsRepr.count('velocity=102'), 2)
        # s.show('midi')

    def testImportTruncationProblemA(self):
        from music21 import converter

        # specialized problem of not importing last notes
        dirLib = common.getSourceFilePath() / 'midi' / 'testPrimitive'
        fp = dirLib / 'test12.mid'
        s = converter.parse(fp)

        self.assertEqual(len(s.parts[0].flatten().notes), 3)
        self.assertEqual(len(s.parts[1].flatten().notes), 3)
        self.assertEqual(len(s.parts[2].flatten().notes), 3)
        self.assertEqual(len(s.parts[3].flatten().notes), 3)

        # s.show('t')
        # s.show('midi')

    def testImportChordVoiceA(self):
        # looking at cases where notes appear to be chord but
        # are better seen as voices
        from music21 import converter
        # specialized problem of not importing last notes
        dirLib = common.getSourceFilePath() / 'midi' / 'testPrimitive'
        fp = dirLib / 'test13.mid'
        s = converter.parse(fp)
        # s.show('t')
        self.assertEqual(len(s.flatten().notes), 7)
        # s.show('midi')

        fp = dirLib / 'test14.mid'
        s = converter.parse(fp)
        # three chords will be created, as well as two voices
        self.assertEqual(len(s.flatten().getElementsByClass('Chord')), 3)
        self.assertEqual(len(s.parts.first().measure(3).voices), 2)

    def testImportChordsA(self):
        from music21 import converter

        dirLib = common.getSourceFilePath() / 'midi' / 'testPrimitive'
        fp = dirLib / 'test05.mid'

        # a simple file created in athenacl
        s = converter.parse(fp)
        # s.show('t')
        self.assertEqual(len(s.flatten().getElementsByClass('Chord')), 5)

    def testMidiEventsImported(self):
        self.maxDiff = None
        from music21 import corpus

        def procCompare(mf_inner, match_inner):
            triples = []
            for i in range(2):
                for j in range(0, len(mf_inner.tracks[i].events), 2):
                    d = mf_inner.tracks[i].events[j]  # delta
                    e = mf_inner.tracks[i].events[j + 1]  # events
                    triples.append((d.time, e.type.name, e.pitch))
            self.assertEqual(triples, match_inner)

        s = corpus.parse('bach/bwv66.6')
        part = s.parts[0].measures(6, 9)  # last measures
        # part.show('musicxml')
        # part.show('midi')

        mf = streamToMidiFile(part)
        match = [(0, 'KEY_SIGNATURE', None),  # Conductor track
                 (0, 'TIME_SIGNATURE', None),
                 (0, 'SET_TEMPO', None),
                 (1024, 'END_OF_TRACK', None),
                 (0, 'SEQUENCE_TRACK_NAME', None),  # Music track
                 (0, 'PITCH_BEND', None),
                 (0, 'PROGRAM_CHANGE', None),
                 (0, 'NOTE_ON', 69),
                 (1024, 'NOTE_OFF', 69),
                 (0, 'NOTE_ON', 71),
                 (1024, 'NOTE_OFF', 71),
                 (0, 'NOTE_ON', 73),
                 (1024, 'NOTE_OFF', 73),
                 (0, 'NOTE_ON', 69),
                 (1024, 'NOTE_OFF', 69),
                 (0, 'NOTE_ON', 68),
                 (1024, 'NOTE_OFF', 68),
                 (0, 'NOTE_ON', 66),
                 (1024, 'NOTE_OFF', 66),
                 (0, 'NOTE_ON', 68),
                 (2048, 'NOTE_OFF', 68),
                 (0, 'NOTE_ON', 66),
                 (2048, 'NOTE_OFF', 66),
                 (0, 'NOTE_ON', 66),
                 (1024, 'NOTE_OFF', 66),
                 (0, 'NOTE_ON', 66),
                 (2048, 'NOTE_OFF', 66),
                 (0, 'NOTE_ON', 66),
                 (512, 'NOTE_OFF', 66),
                 (0, 'NOTE_ON', 65),
                 (512, 'NOTE_OFF', 65),
                 (0, 'NOTE_ON', 66),
                 (1024, 'NOTE_OFF', 66),
                 (1024, 'END_OF_TRACK', None)]
        procCompare(mf, match)

    def testMidiInstrumentToStream(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.transposing01)
        mf = streamToMidiFile(s)
        out = midiFileToStream(mf)
        first_instrument = out.parts.first().measure(1).getElementsByClass('Instrument').first()
        self.assertIsInstance(first_instrument, instrument.Oboe)
        self.assertEqual(first_instrument.quarterLength, 0)

        # Unrecognized instrument 'a'
        dirLib = common.getSourceFilePath() / 'midi' / 'testPrimitive'
        fp = dirLib / 'test15.mid'
        s2 = converter.parse(fp)
        self.assertEqual(s2.parts[0].partName, 'a')

    def testImportZeroDurationNote(self):
        '''
        Musescore places zero duration notes in multiple voice scenarios
        to represent double stemmed notes. Avoid false positives for extra voices.
        https://github.com/cuthbertLab/music21/issues/600
        '''
        from music21 import converter

        dirLib = common.getSourceFilePath() / 'midi' / 'testPrimitive'
        fp = dirLib / 'test16.mid'
        s = converter.parse(fp)
        self.assertEqual(len(s.parts.first().measure(1).voices), 2)
        els = s.parts.first().flatten().getElementsByOffset(0.5)
        self.assertSequenceEqual([e.duration.quarterLength for e in els], [0, 1])

    def testRepeatsExpanded(self):
        from music21 import converter
        from music21.musicxml import testPrimitive

        s = converter.parse(testPrimitive.repeatBracketsA)
        num_notes_before = len(s.flatten().notes)
        prepared = prepareStreamForMidi(s)
        num_notes_after = len(prepared.flatten().notes)
        self.assertGreater(num_notes_after, num_notes_before)

    def testNullTerminatedInstrumentName(self):
        '''
        MuseScore currently writes null bytes at the end of instrument names.
        https://musescore.org/en/node/310158
        '''
        from music21 import midi as midiModule

        event = midiModule.MidiEvent()
        event.data = bytes('Piccolo\x00', 'utf-8')
        i = midiEventsToInstrument(event)
        self.assertIsInstance(i, instrument.Piccolo)

        # test that nothing was broken.
        event.data = bytes('Flute', 'utf-8')
        i = midiEventsToInstrument(event)
        self.assertIsInstance(i, instrument.Flute)

    def testLousyInstrumentData(self):
        from music21 import midi as midiModule

        lousyNames = ('    ', 'Instrument 20', 'Instrument', 'Inst 2', 'instrument')
        for name in lousyNames:
            with self.subTest(name=name):
                event = midiModule.MidiEvent()
                event.data = bytes(name, 'utf-8')
                event.type = midiModule.MetaEvents.INSTRUMENT_NAME
                i = midiEventsToInstrument(event)
                self.assertIsNone(i.instrumentName)

        # lousy program change
        # https://github.com/cuthbertLab/music21/issues/988
        event = midiModule.MidiEvent()
        event.data = 0
        event.channel = 10
        event.type = midiModule.ChannelVoiceMessages.PROGRAM_CHANGE

        i = midiEventsToInstrument(event)
        self.assertIsInstance(i, instrument.UnpitchedPercussion)

    def testConductorStream(self):
        s = stream.Stream()
        p = stream.Stream()
        p.priority = -2
        m = stream.Stream()
        m.append(note.Note('C4'))
        p.append(m)
        s.insert(0, p)
        conductor = conductorStream(s)
        self.assertEqual(conductor.priority, -3)

    def testRestsMadeInVoice(self):
        from music21 import converter

        fp = common.getSourceFilePath() / 'midi' / 'testPrimitive' / 'test17.mid'
        inn = converter.parse(fp)

        self.assertEqual(
            len(inn.parts[1].measure(3).voices.last().getElementsByClass('Rest')), 1)

    def testRestsMadeInMeasures(self):
        from music21 import converter

        fp = common.getSourceFilePath() / 'midi' / 'testPrimitive' / 'test17.mid'
        inn = converter.parse(fp)
        pianoLH = inn.parts.last()
        m1 = pianoLH.measure(1)  # quarter note, quarter note, quarter rest
        m2 = pianoLH.measure(2)
        self.assertEqual(len(m1.notesAndRests), 3)
        self.assertEqual(len(m1.notes), 2)
        self.assertEqual(m1.duration.quarterLength, 3.0)
        self.assertEqual(pianoLH.elementOffset(m2), 3.0)

        for part in inn.parts:
            with self.subTest(part=part):
                self.assertEqual(
                    sum(m.barDuration.quarterLength for m in part.getElementsByClass(
                        stream.Measure)
                        ),
                    part.duration.quarterLength
                )

    def testEmptyExport(self):
        p = stream.Part()
        p.insert(instrument.Instrument())
        # Previously, this errored when we assumed streams lacking notes
        # to be conductor tracks
        # https://github.com/cuthbertLab/music21/issues/1013
        streamToMidiFile(p)

    def testImportInstrumentsWithoutProgramChanges(self):
        '''
        Instrument instances are created from both program changes and
        track or sequence names. Since we have a MIDI file, we should not
        rely on default MIDI programs defined in the instrument module; we
        should just keep track of the active program number.
        https://github.com/cuthbertLab/music21/issues/1085
        '''
        from music21 import midi as midiModule

        event1 = midiModule.MidiEvent()
        event1.data = 0
        event1.channel = 1
        event1.type = midiModule.ChannelVoiceMessages.PROGRAM_CHANGE

        event2 = midiModule.MidiEvent()
        # This will normalize to an instrument.Soprano, but we don't want
        # the default midiProgram, we want 0.
        event2.data = b'Soprano'
        event2.channel = 2
        event2.type = midiModule.MetaEvents.SEQUENCE_TRACK_NAME

        DUMMY_DELTA_TIME = None
        meta_event_pairs = getMetaEvents([(DUMMY_DELTA_TIME, event1), (DUMMY_DELTA_TIME, event2)])
        # Second element of the tuple is the instrument instance
        self.assertEqual(meta_event_pairs[0][1].midiProgram, 0)
        self.assertEqual(meta_event_pairs[1][1].midiProgram, 0)

        # Remove the initial PROGRAM_CHANGE and get a default midiProgram
        meta_event_pairs = getMetaEvents([(DUMMY_DELTA_TIME, event2)])
        self.assertEqual(meta_event_pairs[0][1].midiProgram, 53)


# ------------------------------------------------------------------------------
_DOC_ORDER = [streamToMidiFile, midiFileToStream]

if __name__ == '__main__':
    import music21
    music21.mainTest(Test)  # , runTest='testConductorStream')

