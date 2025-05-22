# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         midi.translate.py
# Purpose:      Translate MIDI and music21 objects
#
# Authors:      Christopher Ariza
#               Michael Scott Asato Cuthbert
#
# Copyright:    Copyright © 2010-2024 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
Module to translate MIDI data to music21 Streams and vice versa.  Note that quantization of
notes takes place in the :meth:`~music21.stream.Stream.quantize` method not here.
'''
from __future__ import annotations

from collections.abc import Sequence
import copy
import math
import typing as t
import warnings

from music21 import chord
from music21 import common
from music21.common.numberTools import opFrac
from music21 import defaults
from music21 import duration
from music21 import dynamics
from music21 import exceptions21
from music21 import environment
from music21 import instrument
from music21.instrument import Conductor, UnpitchedPercussion, deduplicate
from music21 import key
from music21 import meter
from music21 import note
from music21 import percussion
from music21 import pitch
from music21 import stream
from music21 import tempo
from music21 import volume

from music21.midi.base import (
    MidiTrack, DeltaTime, MidiFile, MidiEvent,
    ChannelVoiceMessages, MetaEvents, putNumbersAsList, getNumber, putNumber,
)
from music21.midi.percussion import MIDIPercussionException, PercussionMapper



if t.TYPE_CHECKING:
    from music21 import base
    from music21.common.types import OffsetQLIn


environLocal = environment.Environment('midi.translate')
PERCUSSION_MAPPER = PercussionMapper()

NotRestType = t.TypeVar('NotRestType', bound=note.NotRest)

class TimedNoteEvent(t.NamedTuple):
    onTime: int
    offTime: int
    event: MidiEvent

# ------------------------------------------------------------------------------
class TranslateException(exceptions21.Music21Exception):
    pass


class TranslateWarning(UserWarning):
    pass

# ------------------------------------------------------------------------------
# Durations


def offsetToMidiTicks(o: OffsetQLIn, addStartDelay: bool = False) -> int:
    '''
    Helper function to convert a music21 offset value to MIDI ticks,
    depends on *defaults.ticksPerQuarter* and *defaults.ticksAtStart*.

    Returns an int.

    >>> defaults.ticksPerQuarter
    10080
    >>> defaults.ticksAtStart
    10080


    >>> midi.translate.offsetToMidiTicks(0)
    0
    >>> midi.translate.offsetToMidiTicks(0, addStartDelay=True)
    10080

    >>> midi.translate.offsetToMidiTicks(1)
    10080

    >>> midi.translate.offsetToMidiTicks(20.5)
    206640
    '''
    ticks = int(round(o * defaults.ticksPerQuarter))
    if addStartDelay:
        ticks += defaults.ticksAtStart
    return ticks


def durationToMidiTicks(d: duration.Duration) -> int:
    # noinspection PyShadowingNames
    '''
    Converts a :class:`~music21.duration.Duration` object to midi ticks.

    Depends on *defaults.ticksPerQuarter*, Returns an int.
    Does not use defaults.ticksAtStart


    >>> n = note.Note()
    >>> n.duration.type = 'half'
    >>> midi.translate.durationToMidiTicks(n.duration)
    20160

    >>> d = duration.Duration('quarter')
    >>> dReference = midi.translate.ticksToDuration(10080, inputM21DurationObject=d)
    >>> dReference is d
    True
    >>> d.type
    'quarter'
    >>> d.type = '16th'
    >>> d.quarterLength
    0.25
    >>> midi.translate.durationToMidiTicks(d)
    2520
    '''
    return int(round(d.quarterLength * defaults.ticksPerQuarter))


def ticksToDuration(
    ticks: int,
    ticksPerQuarter: int = defaults.ticksPerQuarter,
    inputM21DurationObject: duration.Duration|None = None
) -> duration.Duration:
    # noinspection PyShadowingNames
    '''
    Converts a number of MIDI Ticks to a music21 duration.Duration() object.

    Optional parameters include ticksPerQuarter -- in case something other
    than the default.ticksPerQuarter (10080) is used in this file.  And
    it can take a :class:`~music21.duration.Duration` object to modify, specified
    as *inputM21DurationObject*

    >>> d = midi.translate.ticksToDuration(10080)
    >>> d
    <music21.duration.Duration 1.0>
    >>> d.type
    'quarter'

    >>> n = note.Note()
    >>> midi.translate.ticksToDuration(30240, inputM21DurationObject=n.duration)
    <music21.duration.Duration 3.0>
    >>> n.duration.type
    'half'
    >>> n.duration.dots
    1

    More complex rhythms can also be set automatically:

    >>> d2 = duration.Duration()
    >>> d2reference = midi.translate.ticksToDuration(23625, inputM21DurationObject=d2)
    >>> d2 is d2reference
    True
    >>> d2.quarterLength
    2.34375
    >>> d2.type
    'complex'
    >>> d2.components
    (DurationTuple(type='half', dots=0, quarterLength=2.0),
     DurationTuple(type='16th', dots=0, quarterLength=0.25),
     DurationTuple(type='64th', dots=1, quarterLength=0.09375))
    >>> d2.components[2].type
    '64th'
    >>> d2.components[2].dots
    1

    '''
    if inputM21DurationObject is None:
        d = duration.Duration()
    else:
        d = inputM21DurationObject

    # given a value in ticks
    d.quarterLength = opFrac(ticks / ticksPerQuarter)
    return d


# ------------------------------------------------------------------------------
# utility functions for getting commonly used event


def getStartEvents(
    midiTrack: MidiTrack|None = None,
    channel: int = 1,
    instrumentObj: instrument.Instrument|None = None,
    *,
    encoding: str = 'utf-8',
) -> list[DeltaTime|MidiEvent]:
    '''
    Returns a list of midi.MidiEvent objects found at the beginning of a track.

    A MidiTrack reference can be provided via the `mt` parameter.

    >>> startEvents = midi.translate.getStartEvents()
    >>> startEvents
    [<music21.midi.DeltaTime (empty) track=None>,
     <music21.midi.MidiEvent SEQUENCE_TRACK_NAME, track=None, data=b''>]

    (Music21 DeltaTime events get assigned to the given channel, but this is not written out)

    >>> startEvents[0].channel
    1

    >>> mt = midi.MidiTrack(3)
    >>> midi.translate.getStartEvents(mt, channel=2, instrumentObj=instrument.Harpsichord())
    [<music21.midi.DeltaTime (empty) track=3>,
     <music21.midi.MidiEvent SEQUENCE_TRACK_NAME, track=3, data=b'Harpsichord'>,
     <music21.midi.DeltaTime (empty) track=3>,
     <music21.midi.MidiEvent PROGRAM_CHANGE, track=3, channel=2, data=6>]

    Bug fixed in v9.6 -- the program change and delta time are written to the given track.
    '''
    events: list[DeltaTime|MidiEvent] = []
    if isinstance(instrumentObj, Conductor):
        return events
    elif instrumentObj is None or instrumentObj.bestName() is None:
        partName = ''
    else:
        partName = instrumentObj.bestName()

    dt = DeltaTime(midiTrack, channel=channel)
    events.append(dt)

    me = MidiEvent(midiTrack, channel=channel)
    me.type = MetaEvents.SEQUENCE_TRACK_NAME
    me.data = partName.encode(encoding, 'ignore')
    events.append(me)

    # additional allocation of instruments may happen elsewhere
    # this may lead to two program changes happening at time zero
    # however, this assures that the program change happens before
    # the clearing of the pitch bend data
    if instrumentObj is not None and instrumentObj.midiProgram is not None:
        sub = instrumentToMidiEvents(instrumentObj,
                                     includeDeltaTime=True,
                                     midiTrack=midiTrack,
                                     channel=channel)
        events += sub

    return events


def getEndEvents(
    midiTrack: MidiTrack|None = None,
    channel: int = 1
) -> list[MidiEvent|DeltaTime]:
    '''
    Returns a list of midi.MidiEvent objects found at the end of a track.

    Note that the channel is basically ignored as no end events are channel
    specific.  (Attribute will be removed in v10)

    >>> midi.translate.getEndEvents()
    [<music21.midi.DeltaTime t=10080, track=None>,
     <music21.midi.MidiEvent END_OF_TRACK, track=None, data=b''>]
    '''
    events: list[MidiEvent|DeltaTime] = []

    dt = DeltaTime(track=midiTrack, channel=channel)
    dt.time = defaults.ticksAtStart
    events.append(dt)

    me = MidiEvent(
        track=midiTrack,
        type=MetaEvents.END_OF_TRACK,
        channel=channel,
    )
    me.data = b''  # must set data to empty bytes
    events.append(me)

    return events

# ------------------------------------------------------------------------------
# Multi-object conversion


def music21ObjectToMidiFile(
    music21Object: base.Music21Object,
    *,
    addStartDelay=False,
    encoding: str = 'utf-8',
) -> MidiFile:
    '''
    Either calls streamToMidiFile on the music21Object or
    puts a copy of that object into a Stream (so as
    not to change activeSites, etc.) and calls streamToMidiFile on
    that object.
    '''
    if isinstance(music21Object, stream.Stream):
        if music21Object.atSoundingPitch is False:
            music21Object = music21Object.toSoundingPitch()

        return streamToMidiFile(t.cast(stream.Stream, music21Object),
                                addStartDelay=addStartDelay,
                                encoding=encoding)
    else:
        m21ObjectCopy = copy.deepcopy(music21Object)
        s: stream.Stream = stream.Stream()
        s.insert(0, m21ObjectCopy)
        return streamToMidiFile(s, addStartDelay=addStartDelay,
                                encoding=encoding)


# ------------------------------------------------------------------------------
# Notes

def _constructOrUpdateNotRestSubclass(
    eOn: MidiEvent,
    tOn: int,
    tOff: int,
    ticksPerQuarter: int,
    *,
    returnClass: type[NotRestType],
) -> NotRestType:
    '''
    Construct (or edit the duration of) a NotRest subclass, usually
    a note.Note (or a chord.Chord if provided to `returnClass`).

    If the MidiEvent is on channel 10, then an Unpitched or PercussionChord
    is constructed instead. Raises TypeError if an incompatible class is provided
    for returnClass.

    * Changed in v8: no inputM21
    '''
    if not issubclass(returnClass, note.NotRest):
        raise TypeError(f'Expected subclass of note.NotRest; got {returnClass}')

    nr: note.NotRest
    if (tOff - tOn) != 0:
        nr = returnClass(duration=ticksToDuration(tOff - tOn,
                                                  ticksPerQuarter=ticksPerQuarter))
    else:
        # here we are handling an issue that might arise with double-stemmed notes
        # environLocal.printDebug(['cannot translate found midi event with zero duration:', eOn, n])
        # for now, substitute grace note
        nr = returnClass()
        nr.getGrace(inPlace=True)
    return nr

def midiEventsToNote(
    timedNoteEvent: TimedNoteEvent,
    ticksPerQuarter: int = defaults.ticksPerQuarter,
) -> note.Note|note.Unpitched:
    # noinspection PyShadowingNames
    '''
    Convert a TimedNoteEvent to a music21.note.Note or a music21.note.Unpitched.
    A timed note event is a tuple of (onTime, offTime, MidiEvent) where the
    MidiEvent is the Note On.  (The Note Off event is not used).

    This method is called as part of the midiToStream() conversion.

    In this example, we start a NOTE_ON event at offset 1.0 (at the standard 10080 to quarter)

    >>> mt = midi.MidiTrack(1)
    >>> dt1 = midi.DeltaTime(mt)
    >>> dt1.time = 10080

    >>> me1 = midi.MidiEvent(mt)
    >>> me1.type = midi.ChannelVoiceMessages.NOTE_ON
    >>> me1.pitch = 45
    >>> me1.velocity = 94


    This lasts until we send a NOTE_OFF event at offset 2.0.

    >>> dt2 = midi.DeltaTime(mt)
    >>> dt2.time = 20160
    >>> me2 = midi.MidiEvent(mt)
    >>> me2.type = midi.ChannelVoiceMessages.NOTE_ON
    >>> me2.pitch = 45
    >>> me2.velocity = 0

    Another system will package dt1, dt2 and me1 into a TimedNoteEvent tuple.
    In this example, me2 is not used.

    >>> tne1 = midi.translate.TimedNoteEvent(dt1.time, dt2.time, me1)
    >>> n = midi.translate.midiEventsToNote(tne1)
    >>> n.pitch
    <music21.pitch.Pitch A2>
    >>> n.duration.quarterLength
    1.0
    >>> n.volume.velocity
    94

    If the channel is 10, an Unpitched element is returned.

    >>> me1.channel = 10
    >>> unp = midi.translate.midiEventsToNote(tne1)
    >>> unp
    <music21.note.Unpitched 'Tom-Tom'>

    Access the `storedInstrument`:

    >>> unp.storedInstrument
    <music21.instrument.TomTom 'Tom-Tom'>

    And with values that cannot be translated, a generic
    :class:`~music21.instrument.UnpitchedPercussion` instance is given:

    >>> me1.pitch = 1
    >>> unp = midi.translate.midiEventsToNote(tne1)
    >>> unp.storedInstrument
    <music21.instrument.UnpitchedPercussion 'Percussion'>

    * Changed in v7.3: Returns None if `inputM21` is provided. Returns a
        :class:`~music21.note.Unpitched` instance if the event is on Channel 10.
    * Changed in v8: `inputM21` is no longer supported.
        The only supported usage now is two tuples.
    * Changed in v9.7: Expects a single TimedNoteEvent
    '''
    tOn, tOff, eOn = timedNoteEvent

    returnClass: type[note.Unpitched]|type[note.Note]
    if eOn.channel == 10:
        returnClass = note.Unpitched
    else:
        returnClass = note.Note

    nr = _constructOrUpdateNotRestSubclass(
        eOn,
        tOn,
        tOff,
        ticksPerQuarter,
        returnClass=returnClass
    )

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
    else:
        raise TranslateException(
            f'Got something other than a Note or Unpitched from conversion: {nr}'
        )

    nr.volume.velocity = eOn.velocity
    nr.volume.velocityIsRelative = False  # not relative coming from MIDI
    # n._midiVelocity = eOn.velocity

    return t.cast(note.Note|note.Unpitched, nr)


def noteToMidiEvents(
    inputM21: note.Note|note.Unpitched,
    *,
    includeDeltaTime: bool = True,
    channel: int = 1,
    encoding: str = 'utf-8',
) -> list[DeltaTime|MidiEvent]:
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
    [<music21.midi.DeltaTime (empty) track=None>,
     <music21.midi.MidiEvent NOTE_ON, track=None, channel=1, pitch=61, velocity=90>,
     <music21.midi.DeltaTime t=10080, track=None>,
     <music21.midi.MidiEvent NOTE_OFF, track=None, channel=1, pitch=61, velocity=0>]

    >>> n1.duration.quarterLength = 2.5
    >>> eventList = midi.translate.noteToMidiEvents(n1)
    >>> eventList
    [<music21.midi.DeltaTime (empty) track=None>,
     <music21.midi.MidiEvent NOTE_ON, track=None, channel=1, pitch=61, velocity=90>,
     <music21.midi.DeltaTime t=25200, track=None>,
     <music21.midi.MidiEvent NOTE_OFF, track=None, channel=1, pitch=61, velocity=0>]

    Omitting DeltaTimes:

    >>> eventList2 = midi.translate.noteToMidiEvents(n1, includeDeltaTime=False, channel=9)
    >>> eventList2
    [<music21.midi.MidiEvent NOTE_ON, track=None, channel=9, pitch=61, velocity=90>,
     <music21.midi.MidiEvent NOTE_OFF, track=None, channel=9, pitch=61, velocity=0>]

    * Changed in v7: made keyword-only.
    * Changed in v8: added support for :class:`~music21.note.Unpitched`
    '''
    n = inputM21

    mt = None  # use a midi track set to None
    eventList: list[DeltaTime|MidiEvent] = []

    if (inputM21.lyric is not None and inputM21.lyric != ''):
        if includeDeltaTime:
            dt = DeltaTime(mt, channel=channel)
            eventList.append(dt)
        me = MidiEvent(track=mt)
        me.type = MetaEvents.LYRIC
        me.data = inputM21.lyric.encode(encoding, 'ignore')
        eventList.append(me)

    if includeDeltaTime:
        dt = DeltaTime(track=mt)
        eventList.append(dt)

    me1 = MidiEvent(track=mt)
    me1.type = ChannelVoiceMessages.NOTE_ON
    me1.channel = channel

    if isinstance(n, note.Unpitched):
        me1.pitch = _get_unpitched_pitch_value(n)
    else:
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
        dt = DeltaTime(mt, channel=channel)
        dt.time = durationToMidiTicks(n.duration)
        # add to track events
        eventList.append(dt)

    me2 = MidiEvent(track=mt)
    me2.type = ChannelVoiceMessages.NOTE_OFF
    me2.channel = channel
    me2.pitch = me1.pitch
    me2.centShift = me1.centShift

    me2.velocity = 0  # must be zero
    eventList.append(me2)

    # set correspondence
    me1.correspondingEvent = me2
    me2.correspondingEvent = me1

    return eventList


# ------------------------------------------------------------------------------
# Chords
def midiEventsToChord(
    timedNoteList: Sequence[TimedNoteEvent],
    ticksPerQuarter: int = defaults.ticksPerQuarter,
) -> chord.ChordBase:
    # noinspection PyShadowingNames
    '''
    Creates a Chord from a list of TimedNoteEvents which
    store the noteOn tick, noteOff tick, and Note-On MidiEvent for each note.

    Timings of all objects except the first (for the first note on)
    and last (for the last note off) are ignored.

    >>> mt = midi.MidiTrack(1)

    >>> dt1 = midi.DeltaTime(mt)
    >>> me1 = midi.MidiEvent(mt)
    >>> me1.type = midi.ChannelVoiceMessages.NOTE_ON
    >>> me1.pitch = 45
    >>> me1.velocity = 94

    Note that only the times of the first NOTE_ON and last NOTE_OFF matter, so
    we don't even bother setting the time of dt3 and dt4.

    >>> dt3 = midi.DeltaTime(mt)
    >>> me3 = midi.MidiEvent(mt)
    >>> me3.type = midi.ChannelVoiceMessages.NOTE_OFF

    The pitches of the NOTE_OFF events are not checked by this function.  They
    are assumed to have been aligned by the previous parser.

    >>> me3.pitch = 45
    >>> me3.velocity = 0

    >>> dt2 = midi.DeltaTime(mt)
    >>> me2 = midi.MidiEvent(mt)
    >>> me2.type = midi.ChannelVoiceMessages.NOTE_ON
    >>> me2.pitch = 46
    >>> me2.velocity = 94

    >>> dt4 = midi.DeltaTime(mt)
    >>> dt4.time = 20160

    >>> me4 = midi.MidiEvent(mt)
    >>> me4.type = midi.ChannelVoiceMessages.NOTE_OFF
    >>> me4.pitch = 46
    >>> me4.velocity = 0

    >>> tne1 = midi.translate.TimedNoteEvent(dt1.time, dt3.time, me1)
    >>> tne2 = midi.translate.TimedNoteEvent(dt2.time, dt4.time, me2)

    >>> c = midi.translate.midiEventsToChord([tne1, tne2])
    >>> c
    <music21.chord.Chord A2 B-2>
    >>> c.duration.quarterLength
    2.0

    If the channel of the last element is set to 10, then a PercussionChord is returned:

    >>> me2.channel = 10
    >>> midi.translate.midiEventsToChord([tne1, tne2])
    <music21.percussion.PercussionChord [Tom-Tom Hi-Hat Cymbal]>

    * Changed in v7: Uses the last DeltaTime in the list to get the end time.
    * Changed in v7.3: Returns a :class:`~music21.percussion.PercussionChord` if
      any event is on channel 10.
    * Changed in v8: inputM21 is no longer supported.  Flat list format is removed.
    * Changed in v9.7: expects a list of TimedNoteEvents
    '''
    tOn: int = 0  # ticks
    tOff: int = 0  # ticks

    pitches: list[pitch.Pitch] = []
    volumes = []

    firstOn: MidiEvent = timedNoteList[0].event
    any_channel_10 = False
    # this is a format provided by the Stream conversion of
    # midi events; it pre-groups events for a chord together in nested pairs
    # of abs start time and the event object
    for tOn, tOff, eOn in timedNoteList:
        if eOn.channel == 10:
            any_channel_10 = True
        p = pitch.Pitch()
        p.midi = eOn.pitch
        pitches.append(p)
        v = volume.Volume(velocity=eOn.velocity)
        v.velocityIsRelative = False  # velocity is absolute coming from MIDI
        volumes.append(v)

    returnClass: type[percussion.PercussionChord]|type[chord.Chord]
    if any_channel_10:
        returnClass = percussion.PercussionChord
    else:
        returnClass = chord.Chord

    c = _constructOrUpdateNotRestSubclass(
        firstOn,
        tOn,
        tOff,
        ticksPerQuarter,
        returnClass=returnClass
    )

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
        c.pitches = tuple(pitches)
    c.setVolumes(volumes)

    return c


def chordToMidiEvents(
    inputM21: chord.ChordBase,
    *,
    includeDeltaTime: bool = True,
    channel: int = 1,
    encoding: str = 'utf-8',
) -> list[DeltaTime|MidiEvent]:
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
    [<music21.midi.DeltaTime (empty) track=None>,
     <music21.midi.MidiEvent NOTE_ON, track=None, channel=1, pitch=48, velocity=90>,
     <music21.midi.DeltaTime (empty) track=None>,
     <music21.midi.MidiEvent NOTE_ON, track=None, channel=1, pitch=68, velocity=90>,
     <music21.midi.DeltaTime (empty) track=None>,
     <music21.midi.MidiEvent NOTE_ON, track=None, channel=1, pitch=83, velocity=90>,
     <music21.midi.DeltaTime t=10080, track=None>,
     <music21.midi.MidiEvent NOTE_OFF, track=None, channel=1, pitch=48, velocity=0>,
     <music21.midi.DeltaTime (empty) track=None>,
     <music21.midi.MidiEvent NOTE_OFF, track=None, channel=1, pitch=68, velocity=0>,
     <music21.midi.DeltaTime (empty) track=None>,
     <music21.midi.MidiEvent NOTE_OFF, track=None, channel=1, pitch=83, velocity=0>]

    * Changed in v7: made keyword-only.
    * Changed in v8: added support for :class:`~music21.percussion.PercussionChord`
    '''
    mt = None  # midi track
    eventList: list[DeltaTime|MidiEvent] = []
    c = inputM21

    # temporary storage for setting correspondence
    noteOn: list[MidiEvent] = []
    noteOff: list[MidiEvent] = []

    chordVolume = c.volume  # use if component volume are not defined
    hasComponentVolumes = c.hasComponentVolumes()

    if (inputM21.lyric is not None and inputM21.lyric != ''):
        if includeDeltaTime:
            dt = DeltaTime(track=mt)
            eventList.append(dt)
        me = MidiEvent(track=mt)
        me.type = MetaEvents.LYRIC
        me.data = inputM21.lyric.encode(encoding, 'ignore')
        eventList.append(me)

    for i, chordComponent in enumerate(c):
        # pitchObj = c.pitches[i]
        # noteObj = chordComponent
        if includeDeltaTime:
            dt = DeltaTime(track=mt)
            # for a chord, only the first delta time should have the offset
            # here, all are zero
            # leave dt.time at zero; will be shifted later as necessary
            # add to track events
            eventList.append(dt)

        me = MidiEvent(track=mt)
        me.type = ChannelVoiceMessages.NOTE_ON
        me.channel = 1
        if isinstance(chordComponent, note.Note):
            me.pitch = chordComponent.pitch.midi
            if not chordComponent.pitch.isTwelveTone():
                me.centShift = chordComponent.pitch.getCentShiftFromMidi()
        elif isinstance(chordComponent, note.Unpitched):
            me.pitch = _get_unpitched_pitch_value(chordComponent)
        else:  # pragma: no cover
            raise TypeError('ChordBase can only contain Note and Unpitched as members')

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
    for i, noteOnEvent in enumerate(noteOn):
        if includeDeltaTime:
            # add note off / velocity zero message
            dt = DeltaTime(track=mt)
            # for a chord, only the first delta time should have the dur
            if i == 0:
                dt.time = durationToMidiTicks(c.duration)
            eventList.append(dt)

        me = MidiEvent(track=mt)
        me.type = ChannelVoiceMessages.NOTE_OFF
        me.channel = channel
        me.pitch = noteOnEvent.pitch
        me.centShift = noteOnEvent.centShift
        me.velocity = 0  # must be zero
        eventList.append(me)
        noteOff.append(me)

    # set correspondence
    for i, meOn in enumerate(noteOn):
        meOff = noteOff[i]
        meOn.correspondingEvent = meOff
        meOff.correspondingEvent = meOn

    return eventList


def _get_unpitched_pitch_value(unp: note.Unpitched) -> int:
    unpitched_instrument: instrument.UnpitchedPercussion|None
    if isinstance(unp.storedInstrument, instrument.UnpitchedPercussion):
        unpitched_instrument = unp.storedInstrument
    else:
        if unp._chordAttached is not None:
            unpitched_instrument = unp._chordAttached.getContextByClass(
                instrument.UnpitchedPercussion)
        else:
            unpitched_instrument = unp.getContextByClass(instrument.UnpitchedPercussion)
    if unpitched_instrument is not None and unpitched_instrument.percMapPitch is not None:
        return unpitched_instrument.percMapPitch
    return 60  # e.g. lossy instrument recognition from musicxml


# ------------------------------------------------------------------------------
def instrumentToMidiEvents(
    inputM21: instrument.Instrument,
    includeDeltaTime: bool = True,
    midiTrack: MidiTrack|None = None,
    channel: int = 1,
):
    '''
    Converts a :class:`~music21.instrument.Instrument` object to a list of MidiEvents

    TODO: DOCS and TESTS
    '''
    inst = inputM21
    mt = midiTrack  # midi track
    events: list[MidiEvent|DeltaTime] = []

    if isinstance(inst, Conductor):
        return events
    if includeDeltaTime:
        dt = DeltaTime(track=mt, channel=channel)
        events.append(dt)
    me = MidiEvent(track=mt)
    me.type = ChannelVoiceMessages.PROGRAM_CHANGE
    me.channel = channel
    instMidiProgram = inst.midiProgram
    if instMidiProgram is None:
        instMidiProgram = 0
    me.data = instMidiProgram  # key step
    events.append(me)
    return events


# ------------------------------------------------------------------------------
# Meta events

def midiEventsToInstrument(
    eventList: MidiEvent|tuple[int, MidiEvent],
    *,
    encoding: str = 'utf-8',
) -> instrument.Instrument:
    '''
    Convert a single MIDI event into a music21 Instrument object.

    >>> me = midi.MidiEvent()
    >>> me.type = midi.ChannelVoiceMessages.PROGRAM_CHANGE
    >>> me.data = 53  # MIDI program 54: Voice Oohs
    >>> midi.translate.midiEventsToInstrument(me)
    <music21.instrument.Vocalist 'Voice'>

    The percussion map will be used if the channel is 10:

    >>> me.channel = 10
    >>> instrumentObj = midi.translate.midiEventsToInstrument(me)
    >>> instrumentObj
    <music21.instrument.UnpitchedPercussion 'Percussion'>
    >>> instrumentObj.midiChannel  # 0-indexed in music21
    9
    >>> instrumentObj.midiProgram  # 0-indexed in music21
    53
    '''
    if not common.isListLike(eventList):
        event = t.cast(MidiEvent, eventList)
    else:  # get the second event; first is delta time
        event = eventList[1]

    decoded: str = ''
    try:
        if isinstance(event.data, bytes):
            # MuseScore writes MIDI files with null-terminated
            # instrument names.  Thus, stop before the byte-0x0
            decoded = event.data.decode(encoding).split('\x00')[0]
            decoded = decoded.strip()
            i = instrument.fromString(decoded)
        elif event.channel == 10 and isinstance(event.data, int):
            # Can only get correct instruments from reading NOTE_ON
            i = instrument.UnpitchedPercussion()
            i.midiProgram = event.data
        elif isinstance(event.data, int):
            i = instrument.instrumentFromMidiProgram(event.data)
            # Instrument.midiProgram and event.data are both 0-indexed
            i.midiProgram = event.data
        else:
            raise instrument.InstrumentException(f'Could not get an instrument from {event}')

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
        elif event.type == MetaEvents.SEQUENCE_TRACK_NAME:
            i.partName = decoded
        elif event.type == MetaEvents.INSTRUMENT_NAME:
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
    if not common.isListLike(eventList):
        event = eventList
    else:  # get the second event; first is delta time
        event = eventList[1]

    # time signature is 4 byte encoding
    post = list(event.data)

    n = post[0]
    d = pow(2, post[1])
    ts = meter.TimeSignature(f'{n}/{d}')
    return ts


def timeSignatureToMidiEvents(ts, includeDeltaTime=True) -> list[DeltaTime|MidiEvent]:
    # noinspection PyShadowingNames
    '''
    Translate a :class:`~music21.meter.TimeSignature` to a pair of events: a DeltaTime and
    a MidiEvent TIME_SIGNATURE.

    Returns a two-element list unless there is an error.

    >>> ts = meter.TimeSignature('5/4')
    >>> eventList = midi.translate.timeSignatureToMidiEvents(ts)
    >>> eventList[0]
    <music21.midi.DeltaTime (empty) track=None>
    >>> eventList[1]
    <music21.midi.MidiEvent TIME_SIGNATURE, track=None, data=b'\\x05\\x02\\x18\\x08'>

    Note that time signatures with numerators above 255 cannot be stored in MIDI.
    (A feature?) They will not be stored and an empty list will be returned.
    A warning will be issued.

    >>> ts = meter.TimeSignature('267/32')  # found on music21 list
    >>> import warnings  #_DOCS_HIDE
    >>> with warnings.catch_warnings(): #_DOCS_HIDE
    ...      warnings.simplefilter('ignore') #_DOCS_HIDE
    ...      out = midi.translate.timeSignatureToMidiEvents(ts) #_DOCS_HIDE
    >>> #_DOCS_SHOW out = midi.translate.timeSignatureToMidiEvents(ts)
    >>> out
    []
    '''
    mt = None  # use a midi track set to None
    eventList: list[MidiEvent|DeltaTime] = []
    if includeDeltaTime:
        dt = DeltaTime(track=mt)
        # dt.time set to zero; will be shifted later as necessary
        # add to track events
        eventList.append(dt)

    n = ts.numerator
    if n > 255:
        warnings.warn(
            f'TimeSignature with numerator > 255 cannot be stored in MIDI. Ignoring {ts}',
            TranslateWarning
        )
        return []

    # need log base 2 to solve for exponent of 2
    # 1 is 0, 2 is 1, 4 is 2, 16 is 4, etc
    d = int(math.log2(ts.denominator))
    metroClick = 24  # clock signals per click, clicks are 24 per quarter
    subCount = 8  # number of 32 notes in a quarter note

    me = MidiEvent(track=mt)
    me.type = MetaEvents.TIME_SIGNATURE
    me.channel = 1
    me.data = putNumbersAsList([n, d, metroClick, subCount])
    eventList.append(me)
    return eventList


def midiEventsToKey(eventList) -> key.Key:
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
    >>> list(me2.data)
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
    if not common.isListLike(eventList):
        event = eventList
    else:  # get the second event; first is delta time
        event = eventList[1]
    post = list(event.data)

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


def keySignatureToMidiEvents(
    ks: key.KeySignature,
    includeDeltaTime=True
) -> list[DeltaTime|MidiEvent]:
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
    [<music21.midi.DeltaTime (empty) track=None>,
     <music21.midi.MidiEvent KEY_SIGNATURE, track=None, data=b'\x02\x00'>]

    Note that MIDI Key Signatures are connected to tracks but not to channels.

    MIDI Key Signatures store sharps or flats as the first number, and mode (0 = major
    1 = minor) as the second number.

    Flats are encoded as offsets at 0xff (=1 flat) or below (0xfe = 2 flats ... etc.,
    through 0xfb = 5 flats, below).

    >>> k = key.Key('b-')
    >>> k
    <music21.key.Key of b- minor>
    >>> eventList = midi.translate.keySignatureToMidiEvents(k, includeDeltaTime=False)
    >>> eventList
    [<music21.midi.MidiEvent KEY_SIGNATURE, track=None, data=b'\xfb\x01'>]
    '''
    mt = None  # use a midi track set to None
    eventList: list[DeltaTime|MidiEvent] = []
    if includeDeltaTime:
        dt = DeltaTime(track=mt)
        # leave dt.time set to zero; will be shifted later as necessary
        # add to track events
        eventList.append(dt)

    # negative = flats.
    sharpCount = ks.sharps

    if isinstance(ks, key.Key) and ks.mode == 'minor':
        mode = 1
    else:  # major or None; must define one
        mode = 0

    me = MidiEvent(
        track=mt,
        type=MetaEvents.KEY_SIGNATURE,
    )

    # this is, as far as I'm aware, the one place where we use the
    # negative number aspect of putNumbersAsList.
    me.data = putNumbersAsList([sharpCount, mode])
    eventList.append(me)
    return eventList


def midiEventsToTempo(eventList):
    '''
    Convert a single MIDI event into a music21 Tempo object.

    TODO: Need Tests
    '''
    if not common.isListLike(eventList):
        event = eventList
    else:  # get the second event; first is delta time
        event = eventList[1]
    # get microseconds per quarter
    mspq = getNumber(event.data, 3)[0]  # first data is number
    bpm = round(60_000_000 / mspq, 2)
    # post = list(event.data)
    # environLocal.printDebug(['midiEventsToTempo, got bpm', bpm])
    mm = tempo.MetronomeMark(number=bpm)
    return mm


def tempoToMidiEvents(
    tempoIndication: tempo.MetronomeMark,
    includeDeltaTime=True,
) -> list[DeltaTime|MidiEvent]|None:
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
    <music21.midi.DeltaTime (empty) track=None>

    >>> evt1 = events[1]
    >>> evt1
    <music21.midi.MidiEvent SET_TEMPO, track=None, data=b'\n,+'>
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
    <music21.tempo.MetronomeMark maestoso Quarter=90>

    `None` is returned if the MetronomeMark lacks a number, which can
    happen with metric modulation marks.

    >>> midi.translate.tempoToMidiEvents(tempo.MetronomeMark(number=None)) is None
    True

    Sounding numbers also translate even if number is None

    >>> mm = tempo.MetronomeMark(numberSounding=80)
    >>> midi.translate.tempoToMidiEvents(mm)
    [<music21.midi.DeltaTime ...>, <music21.midi.MidiEvent SET_TEMPO...>]
    '''
    if tempoIndication.number is None and tempoIndication.numberSounding is None:
        return None
    mt = None  # use a midi track set to None
    eventList: list[DeltaTime|MidiEvent] = []
    if includeDeltaTime:
        dt = DeltaTime(track=mt)
        eventList.append(dt)

    me = MidiEvent(track=mt)
    me.type = MetaEvents.SET_TEMPO
    me.channel = 1

    # from any tempo indication, get the sounding metronome mark
    mm = tempoIndication.getSoundingMetronomeMark()
    bpm = mm.getQuarterBPM()
    mspq = int(round(60_000_000 / bpm))  # microseconds per quarter note

    me.data = putNumber(mspq, 3)
    eventList.append(me)
    return eventList


# ------------------------------------------------------------------------------
# Streams


def getPacketFromMidiEvent(
    trackId: int,
    offset: int,
    midiEvent: MidiEvent,
    obj: base.Music21Object|None = None,
    lastInstrument: instrument.Instrument|None = None
) -> dict[str, t.Any]:
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
     'duration': 10080,
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
    if midiEvent.type != ChannelVoiceMessages.NOTE_OFF and obj is not None:
        # store duration to calculate when the
        # channel/pitch bend can be freed
        post['duration'] = durationToMidiTicks(obj.duration)
    # note offs will have the same object ref, and seem like they have a
    # duration when they do not

    return post


def elementToMidiEventList(
    el: base.Music21Object,
    encoding: str = 'utf-8',
) -> list[MidiEvent|DeltaTime]|None:
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
    # "Code is unreachable" PyCharm bug.
    # https://youtrack.jetbrains.com/issue/PY-79770
    match el:
        case note.Rest():
            return None
        case note.Note():
            # get a list of midi events
            # using this property here is easier than using the above conversion
            # methods, as we do not need to know what the object is
            return noteToMidiEvents(el, includeDeltaTime=False, encoding=encoding)
        case note.Unpitched():
            return noteToMidiEvents(el, includeDeltaTime=False, channel=10, encoding=encoding)
        case chord.Chord():
            # TODO: skip Harmony unless showAsChord
            return chordToMidiEvents(el, includeDeltaTime=False, encoding=encoding)
        case percussion.PercussionChord():
            return chordToMidiEvents(el, includeDeltaTime=False, channel=10, encoding=encoding)
        case dynamics.Dynamic():
            return None  # dynamics have already been applied to notes
        case meter.TimeSignature():
            return timeSignatureToMidiEvents(el, includeDeltaTime=False)
        case key.KeySignature():
            return keySignatureToMidiEvents(el, includeDeltaTime=False)
        case tempo.MetronomeMark():
            # any tempo indication will work
            # note: tempo indications need to be in channel one for most playback
            return tempoToMidiEvents(el, includeDeltaTime=False)
        case instrument.Instrument():
            # the first instrument will have been gathered above with get start elements
            return instrumentToMidiEvents(el, includeDeltaTime=False)
        case _:
            # other objects may have already been added
            return None


def streamToPackets(
    s: stream.Stream,
    trackId: int = 1,
    addStartDelay: bool = False,
    encoding: str = 'utf-8',
) -> list[dict[str, t.Any]]:
    '''
    Convert a flattened, sorted Stream to MIDI Packets.

    This assumes that the Stream has already been flattened,
    ties have been stripped, and instruments,
    if necessary, have been added.

    In converting from a Stream to MIDI, this is called first,
    resulting in a collection of packets by offset.
    Then, getPacketFromMidiEvent is called.
    '''
    # store all events by offset without delta times
    # as (absTime, event)
    packetsByOffset = []
    lastInstrument: instrument.Instrument|None = None

    # s should already be flat and sorted
    for el in s:
        midiEventList = elementToMidiEventList(el, encoding=encoding)
        if isinstance(el, instrument.Instrument):
            lastInstrument = el  # store last instrument

        if midiEventList is None:
            continue

        # we process midiEventList here, which is a list of midi events
        # for each event, we create a packet representation
        # all events: delta/note-on/delta/note-off
        # strip delta times
        elementPackets = []
        firstNotePlayed = False
        for midiEvent in midiEventList:
            # store offset, midi event, object
            # add channel and pitch change also

            if (midiEvent.type == ChannelVoiceMessages.NOTE_ON
                    and firstNotePlayed is False):
                firstNotePlayed = True

            if firstNotePlayed is False:
                o = offsetToMidiTicks(s.elementOffset(el), addStartDelay=False)
            else:
                o = offsetToMidiTicks(s.elementOffset(el), addStartDelay=addStartDelay)

            if midiEvent.type != ChannelVoiceMessages.NOTE_OFF:
                # use offset
                p = getPacketFromMidiEvent(
                    trackId,
                    o,
                    midiEvent,
                    obj=el,
                    lastInstrument=lastInstrument,
                )
                elementPackets.append(p)
            # if it is a note_off, use the duration to shift offset
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
    initTrackIdToChannelMap=None,
):
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
        if p['midiEvent'].type != ChannelVoiceMessages.NOTE_ON:
            # set all not note-off messages to init channel
            if p['midiEvent'].type != ChannelVoiceMessages.NOTE_OFF:
                p['midiEvent'].channel = p['initChannel']
            post.append(p)  # add the non note_on packet first
            # if this is a note off, and has a cent shift, need to
            # rest the pitch bend back to 0 cents
            if p['midiEvent'].type == ChannelVoiceMessages.NOTE_OFF:
                # environLocal.printDebug(['got note-off', p['midiEvent']])
                # cent shift is set for note on and note off
                if p['centShift']:
                    # do not set channel, as already set
                    me = MidiEvent(p['midiEvent'].track,
                                   type=ChannelVoiceMessages.PITCH_BEND,
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
                # or if this event has a shift, then we can exclude
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
            me = MidiEvent(p['midiEvent'].track,
                           type=ChannelVoiceMessages.PITCH_BEND,
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

    # post-processing of entire packet collection
    # for all used channels, create a zero pitch bend at time zero
    # for ch in foundChannels:
    # for each track, places a pitch bend in its initChannel
    for trackId in usedTracks:
        if trackId == 0:
            continue  # Conductor track: do not add pitch bend
        ch = initTrackIdToChannelMap[trackId]
        # use None for track; will get updated later
        me = MidiEvent(track=trackId,
                       type=ChannelVoiceMessages.PITCH_BEND,
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
    packetsSrc: list[dict[str, t.Any]],
    trackIdFilter: int|None = None,
) -> list[dict[str, t.Any]]:
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
    packets: list[dict[str, t.Any]],
    midiTrack: MidiTrack,
) -> list[MidiEvent|DeltaTime]:
    '''
    Given a list of packets (which already contain MidiEvent objects)
    return a list of those Events with proper delta times between them.

    At this stage MIDI event objects have been created.
    The key process here is finding the adjacent time
    between events and adding DeltaTime events before each MIDI event.

    Delta time channel values are derived from the previous midi event.
    '''
    events: list[MidiEvent|DeltaTime] = []
    lastOffset = 0
    for packet in packets:
        midiEvent = packet['midiEvent']
        deltaTimeInt = packet['offset'] - lastOffset
        if deltaTimeInt < 0:
            raise TranslateException('got a negative delta time')
        # set the channel from the midi event
        dt = DeltaTime(midiTrack, time=deltaTimeInt, channel=midiEvent.channel)
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
    # TODO: for a given track id, need to find start/end channel
    mt = MidiTrack(trackId)
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
    mt: MidiTrack
) -> list[tuple[int, MidiEvent]]:
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
    timedEvents: list[tuple[int, MidiEvent]]
) -> list[TimedNoteEvent]:
    '''
    Takes in a list of tuples of (tickTime, MidiEvent) and returns a list of
    TimedNoteEvent objects which contain the note on time, the note off time,
    and the MidiEvent of the note on.  (The note off MidiEvent is not included)

    If timedEvents is sorted in non-decreasing order of tickTime, then the
    output here will also be sorted in non-decreasing order of note on time.

    Example: here are two pitches, represented as note on and note off events:

    >>> CVM = midi.ChannelVoiceMessages
    >>> ev1on = midi.MidiEvent(type=CVM.NOTE_ON)
    >>> ev1on.pitch = 60
    >>> ev2on = midi.MidiEvent(type=CVM.NOTE_ON)
    >>> ev2on.pitch = 62
    >>> ev1off = midi.MidiEvent(type=CVM.NOTE_OFF)
    >>> ev1off.pitch = 60
    >>> ev2off = midi.MidiEvent(type=CVM.NOTE_OFF)
    >>> ev2off.pitch = 62

    >>> events = [(0, ev1on), (1, ev2on), (2, ev2off), (3, ev1off)]

    >>> notes = midi.translate.getNotesFromEvents(events)
    >>> len(notes)
    2
    >>> notes
    [TimedNoteEvent(onTime=0, offTime=3, event=<music21.midi.MidiEvent NOTE_ON...>),
     TimedNoteEvent(onTime=1, offTime=2, event=<music21.midi.MidiEvent NOTE_ON...>)]
    >>> (notes[0].event.pitch, notes[1].event.pitch)
    (60, 62)
    '''
    notes: list[TimedNoteEvent] = []  # store tuples of (onTime, offTime, midiEvent)

    # matching pitch and channel to off time
    # Q: do we need to match channel? These should already be separated by channel, right?
    awaitingNoteOn: dict[tuple[int|None, int], int] = {}
    # pitch will never be None for noteOn or noteOff, but mypy does not know that.

    # Iterate backwards: we see note offs first and then await
    # their corresponding note ons.  We do this so that the note list is
    # sorted by (decreasing) note-on time, not note-off time, which is
    # the order we will expect, but without having to do an O(n log n) sort
    # at the end.
    for time, event in timedEvents[::-1]:
        if event.isNoteOff():
            awaitingNoteOn[event.pitch, event.channel] = time
        elif event.isNoteOn():
            try:
                # we had .pop() instead of dict access which would be quite a bit
                # better to have, but there are a number of cases, including the
                # test09 midi set where there are multiple note ons at the same
                # point with multiple note offs at the same time point for the
                # same pitch and channel.  Better to have the notes turned off
                # from some previous note off event then to lose it.
                offTime = awaitingNoteOn[event.pitch, event.channel]
                tne = TimedNoteEvent(time, offTime, event)
                notes.append(tne)
            except KeyError:  # pragma: no cover
                pass
                # raise TranslateException(
                #     f' cannot find note off for pitch {event.pitch} and channel {event.channel}'
                # )

    # could also raise a warning on note offs without a note on.
    return notes[::-1]  # back to increasing order.


def lyricTimingsFromEvents(
    events: list[tuple[int, MidiEvent]],
    *,
    encoding: str = 'utf-8',
) -> dict[int, str]:
    '''
    From a list of timed events, that is a tuple of a tick time and a MidiEvent
    Return a dictionary mapping a tick time to a string representing a lyric.

    If more than one lyric is found at a given tick time, the last one found is
    stored.
    '''
    lyrics: dict[int, str] = {}
    for time, e in events:
        if e.type == MetaEvents.LYRIC and isinstance(e.data, bytes):
            try:
                lyrics[time] = e.data.decode(encoding)
            except UnicodeDecodeError:
                warnings.warn(
                    f'Unable to decode lyrics from {e} as {encoding}',
                    TranslateWarning)
    return lyrics


def getMetaEvents(
    events: list[tuple[int, MidiEvent]],
    *,
    encoding: str = 'utf-8',
) -> list[tuple[int, base.Music21Object]]:
    '''
    Translate MidiEvents whose type is a MetaEvent into Music21Objects.

    Note: this does not translate MetaEvent.LYRIC, since that becomes a
    bare string.

    New in 9.7: add encoding
    '''
    # store pairs of abs time, m21 object
    metaEvents: list[tuple[int, base.Music21Object]] = []
    last_program: int = -1
    for timeEvent, e in events:
        metaObj: base.Music21Object|None = None
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
            metaObj = midiEventsToInstrument(e, encoding=encoding)
            if last_program != -1:
                # Only update if we have had an initial PROGRAM_CHANGE
                metaObj.midiProgram = last_program
        elif e.type == ChannelVoiceMessages.PROGRAM_CHANGE and isinstance(e.parameter1, int):
            # midiEventsToInstrument() WILL set the program on the instance
            metaObj = midiEventsToInstrument(e)
            last_program = e.parameter1
        # elif e.type == MetaEvents.MIDI_PORT:
        #     pass
        # else:
        #     pass

        if metaObj:
            pair = (timeEvent, metaObj)
            metaEvents.append(pair)

    return metaEvents

def insertConductorEvents(
    conductorPart: stream.Part,
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
        # create a deepcopy of the element so flatten() does not have
        # multiple references of the same object in the same Stream
        eventCopy = copy.deepcopy(e)
        if 'TempoIndication' in eventCopy.classes and not isFirst:
            eventCopy.style.hideObjectOnPrint = True
            eventCopy.numberImplicit = True
        target.insert(conductorPart.elementOffset(e), eventCopy)

def midiTrackToStream(
    mt,
    *,
    ticksPerQuarter: int = defaults.ticksPerQuarter,
    quantizePost=True,
    inputM21=None,
    conductorPart: stream.Part|None = None,
    isFirst: bool = False,
    quarterLengthDivisors: Sequence[int] = (),
    encoding: str = 'utf-8',
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
    >>> p = midi.translate.midiTrackToStream(mt, ticksPerQuarter=mf.ticksPerQuarterNote)
    >>> p
    <music21.stream.Part ...>
    >>> len(p.recurse().notesAndRests)
    14
    >>> p.recurse().notes.first().pitch.midi
    36
    >>> p.recurse().notes.first().volume.velocity
    90

    Note that as of music21 v7, the Part object already has measures made:

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

    * Changed in v7: Now makes measures.
    * Changed in v8: all but the first attribute are keyword only.
    '''
    # environLocal.printDebug(['midiTrackToStream(): got midi track: events',
    # len(mt.events), 'ticksPerQuarter', ticksPerQuarter])

    if inputM21 is None:
        s = stream.Part()
    else:
        s = inputM21

    # get events without DeltaTimes
    timedEvents = getTimeForEvents(mt)

    # need to build chords and notes
    notes: list[TimedNoteEvent] = getNotesFromEvents(timedEvents)
    metaEvents = getMetaEvents(timedEvents, encoding=encoding)
    lyricsDict = lyricTimingsFromEvents(timedEvents, encoding=encoding)

    # first create MetaEvents
    for tick, obj in metaEvents:
        # environLocal.printDebug(['insert midi meta event:', t, obj])
        s.coreInsert(opFrac(tick / ticksPerQuarter), obj)
    s.coreElementsChanged()
    deduplicate(s, inPlace=True)
    # environLocal.printDebug([
    #    'midiTrackToStream(): found notes ready for Stream import', len(notes)])

    # collect notes with similar start times into chords
    chordSub: list[TimedNoteEvent] = []

    # store whether any given note index has already been gathered into a chord.
    # changed in May 2025 -- O(n) space, but O(1) time; previously O(n) time.
    iGathered: list[bool] = [False] * len(notes)
    voicesRequired = False

    if not quarterLengthDivisors:
        quarterLengthDivisors = defaults.quantizationQuarterLengthDivisors

    # let tolerance for chord subbing follow the quantization
    if quantizePost:
        divisor = max(quarterLengthDivisors)
    # fallback: 1/16 of a quarter (64th)
    else:
        divisor = 16
    chunkTolerance = ticksPerQuarter / divisor

    for i, timedNoteEvent in enumerate(notes):
        if iGathered[i]:
            # this index has already been gathered into a chord
            continue
        # look at each note; get on time and event
        tickStart = timedNoteEvent.onTime
        tOff = timedNoteEvent.offTime

        chordSub = [timedNoteEvent]

        # environLocal.printDebug(['on, off', on, off, 'i', i, 'len(notes)', len(notes)])

        # go through all following notes; if there is only 1 note, this will
        # not execute;
        # looking for other events that start within a certain small time
        # window to make into a chord
        # if we find a note with a different end time but the same start
        # time, throw into a different voice
        # this isn't really worth improving the speed on.
        for j in range(i + 1, len(notes)):
            # look at each on time event
            tSub = notes[j].onTime
            tOffSub = notes[j].offTime

            # must be strictly less than the quantization unit
            if abs(tSub - tickStart) >= chunkTolerance:
                break

            # isolate case where end time is not w/n tolerance
            if abs(tOffSub - tOff) > chunkTolerance:
                # need to store this as requiring movement to a different
                # voice
                voicesRequired = True
                continue
            chordSub.append(notes[j])
            iGathered[j] = True
            # keep looping through events to see
            # if we can add more elements to this chord group

        note_or_chord: note.NotRest
        if len(chordSub) > 1:
            # composite.append(chordSub)
            note_or_chord = midiEventsToChord(chordSub, ticksPerQuarter)
        else:
            # just append the note, chordSub has only one element
            # timedNoteEvent is chordSub[0]
            note_or_chord = midiEventsToNote(timedNoteEvent, ticksPerQuarter)

        o = opFrac(tickStart / ticksPerQuarter)
        note_or_chord.editorial.midiTickStart = tickStart
        if lyric := lyricsDict.get(tickStart):
            note_or_chord.lyric = lyric
        s.coreInsert(o, note_or_chord)

    s.sort(force=True)  # will also run coreElementsChanged()
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

    meterStream: stream.Stream|None = None
    if conductorPart is not None:
        ts_iter = conductorPart['TimeSignature']
        if ts_iter:
            meterStream = ts_iter.stream()
            if t.TYPE_CHECKING:
                assert meterStream is not None

            # Supply any missing time signature at the start
            if not meterStream.getElementsByOffset(0):
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
        for p in s.getElementsByClass(stream.Stream):
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
    partsList = list(s.getElementsByClass(stream.Stream).getElementsByOffset(0))
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

    # Defaults
    if not conductorPart.getElementsByClass(tempo.MetronomeMark):
        conductorPart.insert(tempo.MetronomeMark(number=120))
    if not conductorPart.getElementsByClass(meter.TimeSignature):
        conductorPart.insert(meter.TimeSignature('4/4'))

    return conductorPart


def channelInstrumentData(
    s: stream.Stream,
    acceptableChannelList: list[int]|None = None,
) -> tuple[dict[int|None, int], list[int]]:
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
        for obj in s.getElementsByClass(stream.Stream):
            # Conductor track: don't consume a channel
            if (not obj[note.GeneralNote]) and obj[Conductor]:
                continue
            else:
                substreamList.append(obj)
    else:
        # should not ever run if prepareStreamForMidi() was run
        substreamList.append(s)  # pragma: no cover

    # Music tracks
    for subs in substreamList:
        # get a first instrument; iterate over rest
        instrumentStream = subs[instrument.Instrument]
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
    substreamList: list[stream.Part],
    *,
    addStartDelay=False,
    encoding: str = 'utf-8',
) -> dict[int, dict[str, t.Any]]:
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
                         'midiEvent': <music21.midi.MidiEvent SET_TEMPO, ...>,
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
                         'duration': 40320,
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
                         'offset': 40320,
                         'trackId': 1}]}}
    '''
    packetStorage = {}

    for trackId, subs in enumerate(substreamList):  # Conductor track is track 0
        subs = subs.flatten()

        # get a first instrument; iterate over rest
        instObj: instrument.Instrument|None = subs.getElementsByClass(
            instrument.Instrument
        ).first()

        if instObj is None or (instObj.offset != 0 or instObj.midiProgram is None):
            if subs.getElementsByClass((note.Unpitched, percussion.PercussionChord)):
                # This dummy instance will be enough to get a channel 10 default in
                # assignPacketsToChannels(). Later, the proper instrument in the stream will be read
                instObj = UnpitchedPercussion()
            elif trackId == 0 and not subs.notesAndRests:
                # maybe prepareStreamForMidi() wasn't run; create Conductor instance
                instObj = Conductor()

        trackPackets = streamToPackets(subs, trackId=trackId, addStartDelay=addStartDelay,
                                       encoding=encoding)
        # store packets in a dictionary; keys are trackIds
        packetStorage[trackId] = {
            'rawPackets': trackPackets,
            'initInstrument': instObj,
        }
    return packetStorage


def updatePacketStorageWithChannelInfo(
    packetStorage: dict[int, dict[str, t.Any]],
    channelByInstrument: dict[int|None, int|None],
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
        elif isinstance(instObj, instrument.UnpitchedPercussion):
            initCh = 10
        elif isinstance(instObj, instrument.Conductor):
            initCh = None
        else:  # keys are midi program
            if t.TYPE_CHECKING:
                assert isinstance(instObj, instrument.Instrument)
            initCh = channelByInstrument[instObj.midiProgram]
        bundle['initChannel'] = initCh  # set for bundle too

        for rawPacket in bundle['rawPackets']:
            rawPacket['initChannel'] = initCh


def streamHierarchyToMidiTracks(
    inputM21,
    *,
    acceptableChannelList=None,
    addStartDelay=False,
    encoding='utf-8',
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

    * Changed in v6: acceptableChannelList is keyword only.  addStartDelay is new.
    * Changed in v6.5: Track 0 (tempo/conductor track) always exported.
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
    for obj in s.getElementsByClass(stream.Stream):
        # prepareStreamForMidi() supplies defaults for these
        if obj.getElementsByClass(('MetronomeMark', 'TimeSignature')):
            # Ensure conductor track is first
            substreamList.insert(0, obj)
        else:
            substreamList.append(obj)

    # strip all ties inPlace
    for subs in substreamList:
        subs.stripTies(inPlace=True, matchByPitch=True)

    packetStorage = packetStorageFromSubstreamList(substreamList, addStartDelay=addStartDelay,
                                                   encoding=encoding)
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
    midiTracks: list[MidiTrack],
    ticksPerQuarter: int = defaults.ticksPerQuarter,
    quantizePost=True,
    inputM21: stream.Score|None = None,
    *,
    encoding: str = 'utf-8',
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
                          ticksPerQuarter=ticksPerQuarter,
                          quantizePost=quantizePost,
                          inputM21=streamPart,
                          conductorPart=conductorPart,
                          isFirst=(mt is firstTrackWithNotes),
                          encoding=encoding,
                          **keywords)

    return s


def streamToMidiFile(
    inputM21: stream.Stream,
    *,
    addStartDelay: bool = False,
    acceptableChannelList: list[int]|None = None,
    encoding: str = 'utf-8',
) -> MidiFile:
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
    s = inputM21
    midiTracks = streamHierarchyToMidiTracks(s,
                                             addStartDelay=addStartDelay,
                                             acceptableChannelList=acceptableChannelList,
                                             encoding=encoding,
                                             )

    # may need to update channel information

    mf = MidiFile()
    mf.tracks = midiTracks
    mf.ticksPerQuarterNote = defaults.ticksPerQuarter
    return mf


def midiFilePathToStream(
    filePath,
    *,
    inputM21=None,
    encoding: str = 'utf-8',
    **keywords,
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

    * Changed in v8: inputM21 is keyword only.
    '''
    mf = MidiFile()
    mf.open(filePath)
    mf.read()
    mf.close()
    return midiFileToStream(mf, inputM21=inputM21, encoding=encoding, **keywords)


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
    mf = MidiFile()

    numTracks = len(tracksEventsList)

    if numTracks == 1:
        mf.format = 1
    else:
        mf.format = midiFormat

    mf.ticksPerQuarterNote = ticksPerQuarterNote

    if tracksEventsList is not None:
        for i in range(numTracks):
            trk = MidiTrack(i)   # sets the MidiTrack index parameters
            for j in tracksEventsList[i]:
                me = MidiEvent(trk)
                dt = DeltaTime(trk)

                chunk_event_param = str(j).split(' ')

                dt.channel = i + 1
                dt.time = int(chunk_event_param[0])

                me.channel = i + 1
                me.pitch = int(chunk_event_param[2], 16)
                me.velocity = int(chunk_event_param[3])

                valid = False
                if chunk_event_param[1] != 'FF':
                    if list(chunk_event_param[1])[0] == '8':
                        me.type = ChannelVoiceMessages.NOTE_OFF
                        valid = True
                    elif list(chunk_event_param[1])[0] == '9':
                        valid = True
                        me.type = ChannelVoiceMessages.NOTE_ON
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
    mf = MidiFile()
    # do not need to call open or close on MidiFile instance
    mf.readstr(strData)
    return midiFileToStream(mf, **keywords)


def midiFileToStream(
    mf: MidiFile,
    *,
    inputM21=None,
    quantizePost=True,
    encoding: str = 'utf-8',
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

    * Changed in v8: inputM21 and quantizePost are keyword only.
    '''
    # environLocal.printDebug(['got midi file: tracks:', len(mf.tracks)])
    if inputM21 is None:
        s = stream.Score()
    else:
        s = inputM21

    if not mf.tracks:
        raise exceptions21.StreamException('no tracks are defined in this MIDI file.')

    # create a stream for each track
    # may need to check if tracks actually have event data
    midiTracksToStreams(mf.tracks,
                        ticksPerQuarter=mf.ticksPerQuarterNote,
                        quantizePost=quantizePost,
                        inputM21=s,
                        encoding=encoding,
                        **keywords)
    # s._setMidiTracks(mf.tracks, mf.ticksPerQuarterNote)

    return s


# ------------------------------------------------------------------------------
_DOC_ORDER = [streamToMidiFile, midiFileToStream]


if __name__ == '__main__':
    import music21
    music21.mainTest()  # , runTest='testConductorStream')

