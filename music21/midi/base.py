# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         midi/__init__.py
# Purpose:      Access to MIDI library / music21 classes for dealing with midi data
#
# Authors:      Christopher Ariza
#               Michael Scott Asato Cuthbert
#               (Will Ware -- see docs)
#
# Copyright:    Copyright © 2011-2013, 2019 Michael Scott Asato Cuthbert
#               Some parts of this module are in the Public Domain, see details.
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
Objects and tools for processing MIDI data.  Converts from MIDI files to
:class:`~music21.midi.MidiEvent`, :class:`~music21.midi.MidiTrack`, and
:class:`~music21.midi.MidiFile` objects, and vice-versa.

This module originally used routines from Will Ware's public domain midi.py
library from 2001 which was once posted at (http link)
groups.google.com/g/alt.sources/msg/0c5fc523e050c35e
'''
from __future__ import annotations

__all__ = [
    'MidiEvent', 'MidiFile', 'MidiTrack', 'MidiException',
    'DeltaTime',
    'MetaEvents', 'ChannelVoiceMessages', 'ChannelModeMessages',
    'SysExEvents',
    'charToBinary',
    'getNumber', 'getVariableLengthNumber', 'putNumber', 'putVariableLengthNumber',
    'getNumbersAsList', 'putNumbersAsList',
    'intsToHexBytes',
    # add enums:
    'ChannelVoiceMessages', 'ChannelModeMessages', 'SysExEvents',
    'METAEVENT_MARKER',
]

from collections.abc import Iterable
import unicodedata
from typing import overload
import typing as t

from music21 import common
from music21.common.enums import ContainsEnum
from music21 import defaults
from music21 import environment
from music21 import exceptions21
from music21 import prebase

environLocal = environment.Environment('midi.base')

# good midi reference:
# http://www.sonicspot.com/guide/midifiles.html
# ------------------------------------------------------------------------------
class MidiException(exceptions21.Music21Exception):
    pass

# ------------------------------------------------------------------------------
@common.deprecated('v9.7', 'v10', 'use bin(ord(char)) instead.')
def charToBinary(char: str):
    '''
    DEPRECATED: just use bin(ord(char)) instead.

    Or for the exact prior output (with left-padding)
    use `f'{int(bin(ord(char))[2:]):08d}'`


    Convert a char into its binary representation. Useful for debugging.

    >>> #_DOCS_SHOW midi.charToBinary('a')
    >>> f'{int(bin(ord("a"))[2:]):08d}'  #_DOCS_HIDE
    '01100001'

    Note: This function is deprecated and will be removed in v10.  Music21 actually
    predates the bin() function in Python (added in Python 2.6).
    '''
    binary = bin(ord(char))[2:]
    zeroFix = (8 - len(binary)) * '0'
    return zeroFix + binary

@common.deprecated('v9.7', 'v10', 'Just use bytes(...) instead')
def intsToHexBytes(intList: Iterable[int]) -> bytes:
    r'''
    (Deprecated: just use bytes(...) instead)

    Convert a list of integers into hex bytes, suitable for testing MIDI encoding.

    Here we take NOTE_ON message, Middle C, 120 velocity and translate it to bytes

    >>> #_DOCS_SHOW midi.intsToHexBytes([0x90, 60, 120])
    >>> bytes([0x90, 60, 120])  #_DOCS_HIDE
    b'\x90<x'

    Note: This function is deprecated and will be removed in v10.  This
    function has not been needed since music21 became Python 3-only in v.5.
    '''
    return bytes(intList)


@overload
def getNumber(midiStr: int, length: int) -> tuple[int, int]:
    ...

@overload
def getNumber(midiStr: str, length: int) -> tuple[int, str]:
    ...

@overload
def getNumber(midiStr: bytes, length: int) -> tuple[int, bytes]:
    ...

def getNumber(midiStr: str|bytes|int, length: int) -> tuple[int, str|bytes|int]:
    '''
    Return the value of a string byte or bytes if length > 1
    from an 8-bit string or bytes object

    Then, return the remaining string or bytes object

    The `length` is the number of chars to read.
    This will sum a length greater than 1 if desired.

    Note that MIDI uses big-endian for everything.
    This is the inverse of Python's chr() function.

    Read first two bytes

    >>> midi.getNumber(b'test', 2)
    (29797, b'st')

    That number comes from:

    >>> ord('t') * 256 + ord('e')
    29797

    Demonstration of reading the whole length in:

    >>> midi.getNumber(b'test', 4)
    (1952805748, b'')

    Reading in zero bytes leaves the midiStr unchanged:

    >>> midi.getNumber(b'test', 0)
    (0, b'test')


    The method can also take in an integer and return an integer and the remainder part.
    This usage might be deprecated in the future and has already been replaced within
    music21 internal code.

    >>> midi.getNumber(516, 1)   # = 2*256 + 4
    (4, 512)

    As of v9.7, this method can also take a string as input and return a string.
    This usage is deprecated and will be removed in v10.

    >>> midi.getNumber('test', 2)
    (29797, 'st')
    '''
    summation = 0
    if not isinstance(midiStr, int):
        for i in range(length):
            midiStrOrNum = midiStr[i]
            if isinstance(midiStrOrNum, int):
                summation = (summation << 8) + midiStrOrNum
            else:  # to remove
                if t.TYPE_CHECKING:
                    assert isinstance(midiStrOrNum, str)
                summation = (summation << 8) + ord(midiStrOrNum)
        return summation, midiStr[length:]
    else:  # midiStr is an int
        midNum = midiStr
        summation = midNum - ((midNum >> (8 * length)) << (8 * length))
        bigBytes = midNum - summation
        return summation, bigBytes


def getVariableLengthNumber(midiBytes: bytes) -> tuple[int, bytes]:
    r'''
    Given a string or bytes of data, strip off the first character, or all high-byte characters
    terminating with one whose ord() function is < 0x80.  Thus, a variable number of bytes
    might be read.

    After finding the appropriate termination,
    return the remaining string.

    This is necessary as DeltaTime times are given with variable size,
    and thus may be of different numbers if characters are used.

    >>> midi.getVariableLengthNumber(b'A-u')
    (65, b'-u')
    >>> midi.getVariableLengthNumber(b'-u')
    (45, b'u')
    >>> midi.getVariableLengthNumber(b'u')
    (117, b'')

    >>> midi.getVariableLengthNumber(b'test')
    (116, b'est')
    >>> midi.getVariableLengthNumber(b'E@-E')
    (69, b'@-E')
    >>> midi.getVariableLengthNumber(b'@-E')
    (64, b'-E')
    >>> midi.getVariableLengthNumber(b'-E')
    (45, b'E')
    >>> midi.getVariableLengthNumber(b'E')
    (69, b'')

    Test that variable length characters work:

    >>> midi.getVariableLengthNumber(b'\xff\x7f')
    (16383, b'')
    >>> midi.getVariableLengthNumber('中xy'.encode('utf-8'))
    (210638584, b'y')

    If no low-byte character is encoded, raises an IndexError

    >>> midi.getVariableLengthNumber('中国'.encode('utf-8'))
    Traceback (most recent call last):
    IndexError: index out of range

    Up to v9.7, this method could also take a string as input and return a string.  This usage is
    now removed.
    '''
    # from http://faydoc.tripod.com/formats/mid.htm
    # This allows the number to be read one byte at a time, and when you see
    # a msb of 0, you know that it was the last (least significant) byte of the number.
    summation = 0
    i = 0
    while i < 999:  # should return eventually (was "while True")
        x = midiBytes[i]
        # environLocal.printDebug(['getVariableLengthNumber: examined char:',
        #     bin(ord(midiBytes[i])))
        summation = (summation << 7) + (x & 0x7F)
        i += 1
        if not (x & 0x80):
            # environLocal.printDebug([f' getVariableLengthNumber: depth read into string: {i}'])
            return summation, midiBytes[i:]
    raise MidiException('did not find the end of the number!')


@common.deprecated('v9.7', 'v10', 'use list(midiBytes) instead')
def getNumbersAsList(midiBytes: bytes|Iterable[int]) -> list[int]:
    r'''
    Deprecated: this method existed in Python 2.6 and for Python 2 (no bytes)
    compatibility.  Now use `list(midiBytes)` instead.

    Ability to pass in a string will be removed in v10.

    ----
    Translate each char into a number, return in a list.
    Used for reading data messages where each byte encodes
    a different discrete value.

    >>> #_DOCS_SHOW midi.getNumbersAsList(b'\x00\x00\x00\x03')
    >>> list(b'\x00\x00\x00\x03') #_DOCS_HIDE
    [0, 0, 0, 3]

    Now just do:

    >>> list(b'\x00\x00\x00\x03')
    [0, 0, 0, 3]
    '''
    post = []
    for midiByte in midiBytes:
        if isinstance(midiByte, str):
            post.append(ord(midiByte))
        else:
            post.append(midiByte)
    return post


def putNumber(num: int, length: int) -> bytes:
    r'''
    Put a single number as a hex number at the end of a bytes object `length` bytes long.

    >>> midi.putNumber(3, 4)
    b'\x00\x00\x00\x03'
    >>> midi.putNumber(0, 1)
    b'\x00'

    >>> midi.putNumber(258, 2)
    b'\x01\x02'

    If the number is larger than the length currently only the least significant
    bytes are returned. This behavior may change in the near future to raise an
    exception instead.

    >>> midi.putNumber(258, 1)
    b'\x02'
    '''
    lst = bytearray()

    for i in range(length):
        n = 8 * (length - 1 - i)
        thisNum = (num >> n) & 0xFF
        lst.append(thisNum)

    return bytes(lst)


def putVariableLengthNumber(x: int) -> bytes:
    r'''
    Turn an integer number into the smallest bytes object that can hold it for MIDI

    Numbers < 128 are encoded as single bytes and are the same as bytes([x])

    >>> midi.putVariableLengthNumber(4)
    b'\x04'
    >>> midi.putVariableLengthNumber(127)
    b'\x7f'
    >>> bytes([127])
    b'\x7f'
    >>> midi.putVariableLengthNumber(0)
    b'\x00'

    Numbers > 7bit but < 16384 need two characters,
    with the first character set as 0x80 + n // 128
    and the second character set as n % 128:

    >>> midi.putVariableLengthNumber(128)
    b'\x81\x00'
    >>> midi.putVariableLengthNumber(129)
    b'\x81\x01'
    >>> midi.putVariableLengthNumber(255)
    b'\x81\x7f'

    This differs from the 8-bit representation of
    `bytes([x])`:

    >>> bytes([128])
    b'\x80'
    >>> bytes([255])
    b'\xff'


    This method can also deal with numbers > 255, which `bytes` cannot.

    >>> midi.putVariableLengthNumber(256)
    b'\x82\x00'
    >>> bytes([256])
    Traceback (most recent call last):
    ValueError: bytes must be in range(0, 256)

    It also differs from the normal way of representing 256 in Python bytes:

    >>> bytes([1, 0])
    b'\x01\x00'

    Here are MIDI representation of other numbers that are too large to fit in 8 bits
    but stored in two bytes in MIDI.

    >>> midi.putVariableLengthNumber(1024)
    b'\x88\x00'

    Notice that the least significant byte is second.

    >>> midi.putVariableLengthNumber(8192)
    b'\xc0\x00'
    >>> midi.putVariableLengthNumber(8193)
    b'\xc0\x01'

    This is the maximum normal MIDI number that can be stored in 2 bytes.

    >>> midi.putVariableLengthNumber(16383)
    b'\xff\x7f'

    Numbers >= 16384 are not used in 2-byte classic MIDI,
    but this routine continues the basic principle from above:

    >>> midi.putVariableLengthNumber(16384)
    b'\x81\x80\x00'
    >>> midi.putVariableLengthNumber(16384 + 128)
    b'\x81\x81\x00'
    >>> midi.putVariableLengthNumber(16384 * 2)
    b'\x82\x80\x00'
    >>> midi.putVariableLengthNumber(16384 ** 2)
    b'\x81\x80\x80\x80\x00'

    Negative numbers raise MidiException

    >>> midi.putVariableLengthNumber(-1)
    Traceback (most recent call last):
    music21.midi.base.MidiException: cannot putVariableLengthNumber() when number is negative: -1
    '''
    # environLocal.printDebug(['calling putVariableLengthNumber(x) with', x])
    # note: negative numbers will cause an infinite loop here
    if x < 0:
        raise MidiException(f'cannot putVariableLengthNumber() when number is negative: {x}')

    lst = bytearray()
    while True:
        y, x = x & 0x7F, x >> 7
        lst.append(y + 0x80)
        if x == 0:
            break
    lst.reverse()

    lst[-1] = lst[-1] & 0x7F
    return bytes(lst)


def putNumbersAsList(numList: Iterable[int]) -> bytes:
    r'''
    Translate a list of numbers (0-255) into bytes.
    Used for encoding data messages where each byte encodes a different discrete value.

    >>> midi.putNumbersAsList([0, 0, 0, 3])
    b'\x00\x00\x00\x03'

    For positive numbers this method behaves the same as `bytes(numList)` and that
    method should be used if you are sure all numbers are positive.

    >>> bytes([0, 0, 0, 3])
    b'\x00\x00\x00\x03'


    If a number is < 0 then it wraps around from the top.  This is used in places
    like MIDI key signatures where flats are represented by `256 - flats`.

    >>> midi.putNumbersAsList([0, 0, 0, -3])
    b'\x00\x00\x00\xfd'
    >>> midi.putNumbersAsList([0, 0, 0, -1])
    b'\x00\x00\x00\xff'

    The behavior with negative numbers is different from `bytes(numList)`

    List can be of any length

    >>> midi.putNumbersAsList([1, 16, 255])
    b'\x01\x10\xff'

    Any number > 255 (or less than -255) raises an exception:

    >>> midi.putNumbersAsList([256])
    Traceback (most recent call last):
    music21.midi.base.MidiException: Cannot place a number > 255 in a list: 256
    '''
    post = bytearray()
    for n in numList:
        # assume if a number exceeds range count down from top?
        if n < 0:
            n = n % 256  # -1 will be 255
        if n >= 256:
            raise MidiException(f'Cannot place a number > 255 in a list: {n}')
        post.append(n)
    return bytes(post)


class ChannelVoiceMessages(ContainsEnum):
    '''
    ChannelVoiceMessages are the main MIDI messages for channel 1-16, such as
    NOTE_ON, NOTE_OFF, etc.
    '''
    NOTE_OFF = 0x80
    NOTE_ON = 0x90
    POLYPHONIC_KEY_PRESSURE = 0xA0
    CONTROLLER_CHANGE = 0xB0
    PROGRAM_CHANGE = 0xC0
    CHANNEL_KEY_PRESSURE = 0xD0
    PITCH_BEND = 0xE0


class ChannelModeMessages(ContainsEnum):
    ALL_SOUND_OFF = 0x78
    RESET_ALL_CONTROLLERS = 0x79
    LOCAL_CONTROL = 0x7A
    ALL_NOTES_OFF = 0x7B
    OMNI_MODE_OFF = 0x7C
    OMNI_MODE_ON = 0x7D
    MONO_MODE_ON = 0x7E
    POLY_MODE_ON = 0x7F


class MetaEvents(ContainsEnum):
    SEQUENCE_NUMBER = 0x00
    TEXT_EVENT = 0x01
    COPYRIGHT_NOTICE = 0x02
    SEQUENCE_TRACK_NAME = 0x03
    INSTRUMENT_NAME = 0x04
    LYRIC = 0x05
    MARKER = 0x06
    CUE_POINT = 0x07
    PROGRAM_NAME = 0x08
    # optional event is used to embed the
    #    patch/program name that is called up by the immediately
    #    subsequent Bank Select and Program Change messages.
    #    It serves to aid the end user in making an intelligent
    #  program choice when using different hardware.
    SOUND_SET_UNSUPPORTED = 0x09
    MIDI_CHANNEL_PREFIX = 0x20
    MIDI_PORT = 0x21
    END_OF_TRACK = 0x2F
    SET_TEMPO = 0x51
    SMPTE_OFFSET = 0x54
    TIME_SIGNATURE = 0x58
    KEY_SIGNATURE = 0x59
    SEQUENCER_SPECIFIC_META_EVENT = 0x7F
    UNKNOWN = 0xFF  # Container for any unknown code


class SysExEvents(ContainsEnum):
    F0_SYSEX_EVENT = 0xF0
    F7_SYSEX_EVENT = 0xF7


METAEVENT_MARKER = 0xFF


MidiEventTypes = (
    ChannelVoiceMessages
    | ChannelModeMessages
    | MetaEvents
    | SysExEvents
    | t.Literal['DeltaTime']
)

# ------------------------------------------------------------------------------


class MidiEvent(prebase.ProtoM21Object):
    '''
    A model of a MIDI event, including note-on, note-off, program change,
    controller change, any many others.

    MidiEvent objects are paired (preceded) by :class:`~music21.midi.DeltaTime`
    objects in the list of events in a MidiTrack object.

    The `track` argument must be a :class:`~music21.midi.MidiTrack` object.

    The `type` attribute is an enumeration of a Midi event from the ChannelVoiceMessages,
    ChannelModeMessages, SysExEvents, or MetaEvents enums; if unspecified,
    defaults to MetaEvents.UNKNOWN.

    The `channel` attribute is an integer channel id, from 1 to 16.

    The `time` attribute is an integer duration of the event in ticks. This value
    can be zero. This value is not essential, as ultimate time positioning is
    determined by :class:`~music21.midi.DeltaTime` objects.

    The `pitch` attribute is only defined for note-on and note-off messages.
    The attribute stores an integer representation (0-127, with 60 = middle C).

    The `velocity` attribute is only defined for note-on and note-off messages.
    The attribute stores an integer representation (0-127).  A note-on message with
    velocity 0 is generally assumed to be the same as a note-off message.

    The `data` attribute is used for storing other messages,
    such as SEQUENCE_TRACK_NAME string values.

    .. warning::

        The attributes `.midiProgram` and `.midiChannel` on :class:`~music21.instrument.Instrument`
        objects are 0-indexed, just as they need to be in the written binary .mid.
        However, as a convenience, :attr:`MidiEvent.channel` is 1-indexed. No
        analogous convenience is provided for program change data.

    >>> mt = midi.MidiTrack(1)
    >>> me1 = midi.MidiEvent(mt)
    >>> me1.type = midi.ChannelVoiceMessages.NOTE_ON
    >>> me1.channel = 3
    >>> me1.time = 200
    >>> me1.pitch = 60
    >>> me1.velocity = 120
    >>> me1
    <music21.midi.MidiEvent NOTE_ON, t=200, track=1, channel=3, pitch=60, velocity=120>

    >>> me2 = midi.MidiEvent(mt)
    >>> me2.type = midi.MetaEvents.SEQUENCE_TRACK_NAME
    >>> me2.data = 'guitar'
    >>> me2
    <music21.midi.MidiEvent SEQUENCE_TRACK_NAME, track=1, data=b'guitar'>

    Changed in v9.7 - None is not a valid type anymore.  Use MetaEvents.UNKNOWN instead.
        Channel defaults to 1.
    '''
    # noinspection PyShadowingBuiltins
    # pylint: disable=redefined-builtin
    def __init__(self,
                 track: MidiTrack|None = None,
                 type: MidiEventTypes = MetaEvents.UNKNOWN,
                 time: int = 0,
                 channel: int = 1):
        self.track: MidiTrack|None = track  # a MidiTrack object
        self.type: MidiEventTypes = type
        self.time: int = time
        self.channel: int = channel

        self.parameter1: int|bytes|None = None  # pitch or first data value
        self.parameter2: int|bytes|None = None  # velocity or second data value

        # data is a property

        # if this is a Note on/off, need to store original
        # pitch space value in order to determine if this has a microtone
        self.centShift: int|None = None

        # store a reference to a corresponding event
        # if a noteOn, store the note off, and vice versa
        # circular ref -- but modern Python will garbage collect it.
        self.correspondingEvent: MidiEvent|None = None

        # store and pass on a running status if found
        self.lastStatusByte: int|None = None

    @property
    def sortOrder(self) -> int:
        '''
        Ensure that for MidiEvents at the same "time", that order is
        NOTE_OFF, PITCH_BEND, all others.

        >>> CVM = midi.ChannelVoiceMessages
        >>> noteOn = midi.MidiEvent(type=CVM.NOTE_ON)
        >>> noteOff = midi.MidiEvent(type=CVM.NOTE_OFF)
        >>> pitchBend = midi.MidiEvent(type=CVM.PITCH_BEND)

        >>> sorted([noteOn, noteOff, pitchBend], key=lambda me: me.sortOrder)
        [<music21.midi.MidiEvent NOTE_OFF, track=None, channel=1>,
         <music21.midi.MidiEvent PITCH_BEND, track=None, channel=1>,
         <music21.midi.MidiEvent NOTE_ON, track=None, channel=1>]
        '''
        # update based on type; type may be set after init
        if self.type == ChannelVoiceMessages.NOTE_OFF:  # should come before pitch bend
            return -20
        elif self.type == ChannelVoiceMessages.PITCH_BEND:  # go before note events
            return -10
        else:
            return 0

    def _reprInternal(self) -> str:
        trackIndex: int|None
        if self.track is None:
            trackIndex = None
        elif isinstance(self.track, int):  # should not happen anymore
            trackIndex = self.track
        else:
            trackIndex = self.track.index

        printType: str
        if isinstance(self.type, ContainsEnum):
            printType = self.type.name
        elif self.type is None:
            printType = 'None'
        else:  # should not happen anymore
            printType = repr(self.type)

        r = f'{printType}, '
        if self.time != 0:
            r += f't={self.time!r}, '
        r += f'track={trackIndex}'
        if self.type in ChannelVoiceMessages or self.type in ChannelModeMessages:
            r += f', channel={self.channel!r}'
        if self.type in (ChannelVoiceMessages.NOTE_ON, ChannelVoiceMessages.NOTE_OFF):
            attrList = ['pitch', 'velocity']
        else:
            if self.parameter2 is None:
                attrList = ['data']
            else:
                attrList = ['parameter1', 'parameter2']

        for attrib in attrList:
            if getattr(self, attrib) is not None:
                r = r + ', ' + attrib + '=' + repr(getattr(self, attrib))
        return r

    # provide parameter access to pitch and velocity
    @property
    def pitch(self) -> int|None:
        # only return pitch if this is note on /off
        if (self.type in (ChannelVoiceMessages.NOTE_ON, ChannelVoiceMessages.NOTE_OFF)
                and self.parameter1 is not None):
            return int(self.parameter1)
        else:
            return None

    @pitch.setter
    def pitch(self, value: int|None):
        self.parameter1 = value

    @property
    def velocity(self) -> int|None:
        if not isinstance(self.parameter2, int):
            return None
        return self.parameter2

    @velocity.setter
    def velocity(self, value: int|None):
        self.parameter2 = value

    # store generic data in parameter 1
    @property
    def data(self) -> int|bytes|None:
        r'''
        Read or set the data (`.parameter1`) for the object

        Does some automatic conversions:

        >>> me = midi.MidiEvent(type=midi.ChannelModeMessages.LOCAL_CONTROL)
        >>> me.data = True
        >>> me.data
        b'\x01'
        '''
        return self.parameter1

    @data.setter
    def data(self, value: int|str|bytes|bool|None):
        if value is not None and not isinstance(value, bytes):
            if isinstance(value, str):
                value = value.encode('utf-8')
            elif isinstance(value, bool):
                value = bytes([int(value)])
        self.parameter1 = value


    def setPitchBend(self, cents: int|float, bendRange=2) -> None:
        '''
        Treat this event as a pitch bend value, and set the .parameter1 and
         .parameter2 fields appropriately given a specified bend value in cents.

        Also called Pitch Wheel

        The `bendRange` parameter gives the number of half steps in the bend range.

        >>> mt = midi.MidiTrack(1)
        >>> me1 = midi.MidiEvent(mt, type=midi.ChannelVoiceMessages.PITCH_BEND)
        >>> me1.setPitchBend(50)
        >>> me1.parameter1, me1.parameter2
        (0, 80)
        >>> me1.setPitchBend(100)
        >>> me1.parameter1, me1.parameter2
        (0, 96)

        Neutral is 0, 64

        >>> me1.setPitchBend(0)
        >>> me1.parameter1, me1.parameter2
        (0, 64)

        Parameter 2 is the most significant digit, not
        parameter 1.

        >>> me1.setPitchBend(101)
        >>> me1.parameter1, me1.parameter2
        (40, 96)

        Exceeding maximum pitch bend sets the max (127, 127)

        >>> me1.setPitchBend(200)
        >>> me1.parameter1, me1.parameter2
        (127, 127)
        >>> me1.setPitchBend(300)
        >>> me1.parameter1, me1.parameter2
        (127, 127)

        >>> me1.setPitchBend(-50)
        >>> me1.parameter1, me1.parameter2
        (0, 48)
        >>> me1.setPitchBend(-100)
        >>> me1.parameter1, me1.parameter2
        (0, 32)
        >>> me1.setPitchBend(-196)
        >>> me1.parameter1, me1.parameter2
        (36, 1)
        >>> me1.setPitchBend(-200)
        >>> me1.parameter1, me1.parameter2
        (0, 0)

        Again, excess trimmed

        >>> me1.setPitchBend(-300)
        >>> me1.parameter1, me1.parameter2
        (0, 0)

        But a larger `bendRange` can be set in semitones for non-GM devices:

        >>> me1.setPitchBend(-300, bendRange=4)
        >>> me1.parameter1, me1.parameter2
        (0, 16)
        >>> me1.setPitchBend(-399, bendRange=4)
        >>> me1.parameter1, me1.parameter2
        (20, 0)

        OMIT_FROM_DOCS

        Pitch bends very close to 0 formerly had problems

        >>> me1.setPitchBend(-196)
        >>> me1.parameter1, me1.parameter2
        (36, 1)
        >>> me1.setPitchBend(-197)
        >>> me1.parameter1, me1.parameter2
        (123, 0)
        '''
        # value range is 0, 16383 (0 to 0x4000 - 1)
        # center should be 8192 (0x2000)
        centRange = bendRange * 100
        if cents > centRange:
            cents = centRange
        elif cents < -1 * centRange:
            cents = -1 * centRange

        center = 0x2000
        topSpan = 0x4000 - 1 - center
        bottomSpan = center

        shiftScalar = cents / centRange

        if cents > 0:
            shift = int(round(shiftScalar * topSpan))
        elif cents < 0:
            shift = int(round(shiftScalar * bottomSpan))  # will be negative
        else:  # cents is zero
            shift = 0
        target = center + shift

        # produce a 1-2-byte value with most significant byte first.
        charValue = putVariableLengthNumber(target)
        d1 = charValue[0]  # d1 = parameter2; bytes[i] returns an int
        # need to convert from 8 bit to 7, so using & 0x7F
        d1 = d1 & 0x7F
        if len(charValue) > 1:
            d2 = charValue[1]
            d2 = d2 & 0x7F
        else:
            d2 = d1
            d1 = 0

        # environLocal.printDebug(['got target char value', charValue,
        # 'getVariableLengthNumber(charValue)', getVariableLengthNumber(charValue)[0],
        # 'd1', d1, 'd2', d2,])

        self.parameter1 = d2
        self.parameter2 = d1  # d1 is the most significant byte here

    def parseChannelVoiceMessage(self, midiBytes: bytes) -> bytes:
        r'''
        Take a set of bytes that represent a ChannelVoiceMessage and set the
        appropriate event type and data, returning the remaining bytes.

        Channel voice messages start with a one-byte message from 0x80 to 0xEF,
        where the first nibble (8-E) is the message type and the second nibble (0-F)
        is the channel represented in hex.

        First let's create a MidiEvent that does not know its type.

        >>> mt = midi.MidiTrack(1)
        >>> me1 = midi.MidiEvent(mt)
        >>> me1
        <music21.midi.MidiEvent UNKNOWN, track=1>

        Now create two messages -- a note on (at pitch = 60 or C4) at velocity 120

        >>> midBytes = bytes([0x92, 60, 120])
        >>> midBytes
        b'\x92<x'

        Add a second hypothetical message (would normally be a delta time)

        >>> midBytes += b'hello'
        >>> midBytes
        b'\x92<xhello'


        Now see how parsing this ChannelVoiceMessage changes the MidiEvent

        >>> remainder = me1.parseChannelVoiceMessage(midBytes)
        >>> me1
        <music21.midi.MidiEvent NOTE_ON, track=1, channel=3, pitch=60, velocity=120>

        The remainder would probably contain a delta time and following
        events, but here we'll just show that it passes whatever is left through.

        >>> remainder
        b'hello'

        We will ignore remainders for the rest of this demo.  Note that all
        attributes are set properly:

        >>> me1.type
        <ChannelVoiceMessages.NOTE_ON: 0x90>
        >>> me1.pitch  # 60 = middle C
        60
        >>> me1.velocity
        120

        The channel is 3 because 0x90 is NOTE_ON for channel 1, 0x91 is 2, and 0x92 is 3, etc.

        >>> me1.channel
        3

        Now let's make a program change on channel 16:

        >>> me2 = midi.MidiEvent(mt)
        >>> rem = me2.parseChannelVoiceMessage(bytes([0xCF, 71]))
        >>> me2
        <music21.midi.MidiEvent PROGRAM_CHANGE, track=1, channel=16, data=71>
        >>> me2.data  # 71 = clarinet (0-127 indexed)
        71

        Program changes and channel pressures only go to 127.  More than that signals an error:

        >>> me2.parseChannelVoiceMessage(bytes([0xCF, 200]))
        Traceback (most recent call last):
        music21.midi.base.MidiException: Cannot have a
            <ChannelVoiceMessages.PROGRAM_CHANGE: 0xC0> followed by a byte > 127: 200
        '''
        # x, y, and z define characteristics of the first two chars
        # for x: The left nybble (4 bits) contains the actual command, and the right nibble
        # contains the midi channel number on which the command will be executed.
        if len(midiBytes) < 2:
            raise ValueError(f'length of {midiBytes!r} must be at least 2')

        byte0 = midiBytes[0]
        byte1 = midiBytes[1]
        byte2 = 0
        if len(midiBytes) > 2:  # very likely, but may be translating in pieces
            byte2 = midiBytes[2]

        msgNybble: int = byte0 & 0xF0  # 0x80, 0x90, 0xA0 ... 0xE0
        channelNybble: int = byte0 & 0x0F  # 0-15

        self.channel = channelNybble + 1
        self.type = ChannelVoiceMessages(msgNybble)

        # environLocal.printDebug(['MidiEvent.read()', self.type])
        if self.type in (ChannelVoiceMessages.PROGRAM_CHANGE,
                         ChannelVoiceMessages.CHANNEL_KEY_PRESSURE):
            if byte1 > 127:
                raise MidiException(
                    f'Cannot have a {self.type!r} followed by a byte > 127: {byte1}')
            self.data = byte1
            return midiBytes[2:]
        elif self.type == ChannelVoiceMessages.CONTROLLER_CHANGE:
            specificDataSet = False
            if ChannelModeMessages.hasValue(byte1):
                self.type = ChannelModeMessages(byte1)
                if self.type == ChannelModeMessages.LOCAL_CONTROL:
                    specificDataSet = True
                    self.data = (midiBytes[2] == 0x7F)
                elif self.type == ChannelModeMessages.MONO_MODE_ON:
                    specificDataSet = True
                    # see http://midi.teragonaudio.com/tech/midispec/mono.htm
                    self.data = midiBytes[2]
            if not specificDataSet:
                self.parameter1 = byte1  # this is the controller id
                self.parameter2 = byte2  # this is the controller value
            return midiBytes[3:]
        elif self.type == ChannelVoiceMessages.PITCH_BEND:
            self.parameter1 = byte1  # least significant byte
            self.parameter2 = byte2  # most significant byte
            return midiBytes[3:]
        elif self.type in (ChannelVoiceMessages.NOTE_ON, ChannelVoiceMessages.NOTE_OFF):
            # next two bytes:  pitch, velocity
            self.pitch = byte1
            self.velocity = byte2
            return midiBytes[3:]
        elif self.type == ChannelVoiceMessages.POLYPHONIC_KEY_PRESSURE:
            self.parameter1 = byte1  # pitch
            self.parameter2 = byte2  # pressure
            return midiBytes[3:]
        raise TypeError(f'expected ChannelVoiceMessage, got {self.type}')  # pragma: no cover

    def read(self, midiBytes: bytes) -> bytes:
        r'''
        Parse the bytes given and take the beginning
        section and convert it into data for this event and return the
        now truncated bytes.

        >>> channel = 0x2
        >>> noteOnMessage = midi.ChannelVoiceMessages.NOTE_ON | channel
        >>> hex(noteOnMessage)
        '0x92'

        This is how the system reads note-on messages (0x90-0x9F) and channels

        >>> hex(0x91 & 0xF0)  # testing message type extraction
        '0x90'
        >>> hex(0x92 & 0xF0)  # testing message type extraction
        '0x90'
        >>> (0x90 & 0x0F) + 1  # getting the channel
        1
        >>> (0x9F & 0x0F) + 1  # getting the channel
        16
        '''
        if len(midiBytes) < 2:
            # often what we have here are null events:
            # the string is simply: 0x00
            environLocal.printDebug(
                ['MidiEvent.read(): got bad data string', repr(midiBytes)])
            return b''

        # x, y, and z define characteristics of the first two chars
        # for x: The left nybble (4 bits) contains the actual command, and the right nibble
        # contains the midi channel number on which the command will be executed.
        byte0: int = midiBytes[0]  # extracting a single val from a byte makes it an int

        # detect running status: if the status byte is less than 0x80, it is
        # not a status byte, but a data byte
        if byte0 < 0x80:
            # environLocal.printDebug(['MidiEvent.read(): found running status even data',
            # 'self.lastStatusByte:', self.lastStatusByte])

            if self.lastStatusByte is not None:
                runningStatusByte = bytes([self.lastStatusByte])
            else:  # provide a default
                runningStatusByte = b'\x90'
            # add the running status byte to the front of the string
            # and process as before
            midiBytes = runningStatusByte + midiBytes
            byte0 = midiBytes[0]
        elif byte0 != 0xff:
            # store last status byte, unless it's a meta message
            self.lastStatusByte = byte0

        msgType: int = byte0 & 0xF0  # bitwise and to derive message type w/o channel

        byte1: int = midiBytes[1]

        # environLocal.printDebug([
        #    'MidiEvent.read(): trying to parse a MIDI event, looking at first two chars:',
        #    'hex(byte0)', hex(byte0), 'hex(byte[1])', hex(byte[1]),])

        if ChannelVoiceMessages.hasValue(msgType):
            # NOTE_ON and NOTE_OFF and PROGRAM_CHANGE, PITCH_BEND, etc.
            return self.parseChannelVoiceMessage(midiBytes)

        elif SysExEvents.hasValue(byte0):
            self.type = SysExEvents(byte0)
            length, midiBytesAfterLength = getVariableLengthNumber(midiBytes[1:])
            self.data = midiBytesAfterLength[:length]
            return midiBytesAfterLength[length:]

        # SEQUENCE_TRACK_NAME and other MetaEvents are here
        elif byte0 == METAEVENT_MARKER:  # 0xFF
            if MetaEvents.hasValue(byte1):
                self.type = MetaEvents(byte1)
            else:
                # environLocal.printDebug([f' unknown meta event: FF {byte1:02X}'])
                # sys.stdout.flush()
                self.type = MetaEvents.UNKNOWN
            length, midiBytesAfterLength = getVariableLengthNumber(midiBytes[2:])
            self.data = midiBytesAfterLength[:length]
            # return remainder
            return midiBytesAfterLength[length:]
        else:
            # an uncaught message
            environLocal.printDebug(['got unknown midi event type', hex(byte0),
                                     'hex(midiBytes[1])', hex(midiBytes[1])])
            raise MidiException(f'Unknown midi event type {hex(byte0)}')

    def getBytes(self) -> bytes:
        r'''
        Return a set of bytes for this MIDI event (used for translating from music21 to MIDI)

        >>> noteOn = midi.MidiEvent(type=midi.ChannelVoiceMessages.NOTE_ON, channel=10)
        >>> noteOn.pitch = 60
        >>> noteOn.velocity = 127
        >>> noteOn.getBytes()
        b'\x99<\x7f'

        Changing the pitch changes the second byte (from less than to greater than):

        >>> noteOn.pitch = 62
        >>> noteOn.getBytes()
        b'\x99>\x7f'
        >>> ord('>')
        62

        Changing the velocity changes the third byte:

        >>> noteOn.velocity = 64
        >>> noteOn.getBytes()
        b'\x99>@'

        The third byte is `\x40` but it is represented by '@'

        >>> ord('@')
        64
        >>> hex(64)
        '0x40'

        And changing the channel changes the first byte:

        >>> noteOn.channel = 11
        >>> noteOn.getBytes()
        b'\x9a>@'
        '''
        if t.TYPE_CHECKING:
            # no DeltaTime here.
            assert isinstance(self.type, ContainsEnum)

        if self.type in ChannelVoiceMessages:
            # environLocal.printDebug(['writing channelVoiceMessages', self.type])
            bytes0 = bytes([self.channel - 1 + self.type.value])
            # for writing note-on/note-off
            if self.type not in (ChannelVoiceMessages.PROGRAM_CHANGE,
                                 ChannelVoiceMessages.CHANNEL_KEY_PRESSURE):
                if self.parameter1 is None or self.parameter2 is None:
                    raise MidiException(
                        'Cannot write MIDI event without parameter1 and parameter2 set.'
                    )

                # this results in a two-part string, like '\x00\x00'
                param1data: bytes
                if isinstance(self.parameter1, int):
                    param1data = bytes([self.parameter1])
                else:
                    param1data = self.parameter1

                param2data: bytes
                if isinstance(self.parameter2, int):
                    param2data = bytes([self.parameter2])
                else:
                    param2data = self.parameter2

                data = param1data + param2data
            elif self.type == ChannelVoiceMessages.PROGRAM_CHANGE and isinstance(self.data, int):
                data = bytes([self.data])
            else:  # all the other messages
                try:
                    if isinstance(self.data, int):
                        data = bytes([self.data])
                    elif isinstance(self.data, bytes):
                        data = self.data
                    else:
                        raise TypeError('data must be bytes or int')
                except (TypeError, ValueError):
                    raise MidiException(
                        f'Got incorrect data for {self} in .data: {self.data!r}, '
                        + 'cannot parse Miscellaneous Message')
            return bytes0 + data

        elif self.type in ChannelModeMessages and self.data is not None:
            channelMode = bytes([0xB0 + self.channel - 1])
            msgValue = bytes([self.type.value])
            if isinstance(self.data, int):
                data = bytes([self.data])
            else:
                data = self.data
            return channelMode + msgValue + data

        elif self.type in SysExEvents and isinstance(self.data, bytes):
            s = bytes([self.type.value])
            s = s + putVariableLengthNumber(len(self.data))
            sys_data = t.cast(bytes, self.data)
            return s + sys_data

        elif self.type in MetaEvents and isinstance(self.data, (bytes, str)):
            s = bytes([METAEVENT_MARKER])
            s += bytes([self.type.value])
            s += putVariableLengthNumber(len(self.data))

            try:
                sys_data = t.cast(bytes, self.data)
                return s + sys_data
            except (UnicodeDecodeError, TypeError):
                # environLocal.printDebug(['cannot decode data', self.data])

                # normalize can take bytes.
                # noinspection PyTypeChecker
                return s + unicodedata.normalize(
                    'NFKD',
                    t.cast(str, self.data)
                ).encode('ascii', 'ignore')
        else:
            raise MidiException(f'unknown midi event type: {self.type!r}')

    # --------------------------------------------------------------------------
    def isNoteOn(self) -> bool:
        '''
        Return a boolean if this is a note-on message and velocity is not zero.

        >>> mt = midi.MidiTrack(1)
        >>> me1 = midi.MidiEvent(mt)
        >>> me1.type = midi.ChannelVoiceMessages.NOTE_ON
        >>> me1.velocity = 120
        >>> me1.isNoteOn()
        True
        >>> me1.isNoteOff()
        False

        A zero velocity note-on is treated as a note-off:

        >>> me1.velocity = 0
        >>> me1.isNoteOn()
        False
        >>> me1.isNoteOff()
        True

        A midi event can be neither a note on or a note off.

        >>> me1.type = midi.ChannelVoiceMessages.PROGRAM_CHANGE
        >>> me1.isNoteOn()
        False
        >>> me1.isNoteOff()
        False
        '''
        if self.type == ChannelVoiceMessages.NOTE_ON and self.velocity != 0:
            return True
        return False

    def isNoteOff(self) -> bool:
        '''
        Return a boolean if this should be interpreted as a note-off message,
        either as a real note-off or as a note-on with zero velocity.

        >>> mt = midi.MidiTrack(1)
        >>> me1 = midi.MidiEvent(mt)
        >>> me1.type = midi.ChannelVoiceMessages.NOTE_OFF
        >>> me1.isNoteOn()
        False
        >>> me1.isNoteOff()
        True

        >>> me2 = midi.MidiEvent(mt)
        >>> me2.type = midi.ChannelVoiceMessages.NOTE_ON
        >>> me2.velocity = 0
        >>> me2.isNoteOn()
        False
        >>> me2.isNoteOff()
        True

        See :meth:`~music21.midi.MidiEvent.isNoteOn` for more examples.
        '''
        if self.type == ChannelVoiceMessages.NOTE_OFF:
            return True
        elif self.type == ChannelVoiceMessages.NOTE_ON and self.velocity == 0:
            return True
        return False

    def isDeltaTime(self) -> bool:
        '''
        Return a boolean if this is a DeltaTime subclass.

        >>> mt = midi.MidiTrack(1)
        >>> dt = midi.DeltaTime(mt)
        >>> dt.isDeltaTime()
        True
        '''
        if self.type == 'DeltaTime':
            return True
        return False

    def matchedNoteOff(self, other: MidiEvent) -> bool:
        '''
        Returns True if `other` is a MIDI event that specifies
        a note-off message for this message.  That is, this event
        is a NOTE_ON message, and the other is a NOTE_OFF message
        for this pitch on this channel.  Otherwise returns False

        >>> mt = midi.MidiTrack(1)
        >>> me1 = midi.MidiEvent(mt)
        >>> me1.type = midi.ChannelVoiceMessages.NOTE_ON
        >>> me1.velocity = 120
        >>> me1.pitch = 60

        >>> me2 = midi.MidiEvent(mt)
        >>> me2.type = midi.ChannelVoiceMessages.NOTE_ON
        >>> me2.velocity = 0
        >>> me2.pitch = 60

        `me2` is a Note off for `me1` because it has velocity 0 and matches
        pitch.

        >>> me1.matchedNoteOff(me2)
        True

        Now the pitch does not match, so it does not work.

        >>> me2.pitch = 61
        >>> me1.matchedNoteOff(me2)
        False

        >>> me2.type = midi.ChannelVoiceMessages.NOTE_OFF
        >>> me1.matchedNoteOff(me2)
        False

        >>> me2.pitch = 60
        >>> me1.matchedNoteOff(me2)
        True

        Channels must match also:

        >>> me2.channel = 12
        >>> me1.matchedNoteOff(me2)
        False

        Note that this method is no longer used in MIDI Parsing
        because it is inefficient.
        '''
        if self.isNoteOn() and other.isNoteOff():
            if self.pitch == other.pitch and self.channel == other.channel:
                return True
        return False


class DeltaTime(MidiEvent):
    r'''
    A :class:`~music21.midi.MidiEvent` subclass that stores the
    time change (in ticks) since the start or since the last MidiEvent.

    Pairs of DeltaTime and MidiEvent objects are the basic presentation of temporal data.

    The `track` argument must be a :class:`~music21.midi.MidiTrack` object.

    Time values are in integers, representing ticks.

    The `channel` attribute, inherited from MidiEvent is not used and set to None
    unless overridden (it does not do anything if set and is not written out to MIDI).

    >>> mt = midi.MidiTrack(1)
    >>> dt = midi.DeltaTime(mt)
    >>> dt.time = 1
    >>> dt
    <music21.midi.DeltaTime t=1, track=1>

    Changed in v9.7 -- DeltaTime repr no longer lists its channel (to de-emphasize it).
        Channel defaults to 1.
    '''
    def __init__(
        self,
        track: MidiTrack|None = None,
        time: int = 0,
        channel: int = 1,
    ):
        super().__init__(track, time=time, channel=channel)
        self.type = 'DeltaTime'

    def _reprInternal(self) -> str:
        rep = super()._reprInternal()
        rep = rep.replace("'DeltaTime', ", '')
        if self.time == 0:
            rep = '(empty) ' + rep
        return rep

    def readUntilLowByte(self, oldBytes: bytes) -> tuple[int, bytes]:
        r'''
        Read a byte-string until hitting a character below 0x80
        and return the converted number and the rest of the bytes.

        The first number is also stored in `self.time`.

        >>> mt = midi.MidiTrack(1)
        >>> dt = midi.DeltaTime(mt)
        >>> dt.time
        0

        >>> dt.readUntilLowByte(b'\x20')
        (32, b'')
        >>> dt.time
        32

        >>> dt.readUntilLowByte(b'\x20hello')
        (32, b'hello')

        here the '\x82' is above 0x80 so the 'h' is read
        as part of the continuation.

        >>> dt.readUntilLowByte(b'\x82hello')
        (360, b'ello')

        Changed in v9: had an incompatible signature with MidiEvent
        '''
        self.time, newBytes = getVariableLengthNumber(oldBytes)
        return self.time, newBytes

    def getBytes(self) -> bytes:
        r'''
        Convert the time integer into a set of bytes.

        >>> mt = midi.MidiTrack(1)
        >>> dt = midi.DeltaTime(mt)
        >>> dt.time = 1
        >>> dt.getBytes()
        b'\x01'

        >>> dt.time = 128
        >>> dt.getBytes()
        b'\x81\x00'

        >>> dt.time = 257
        >>> dt.getBytes()
        b'\x82\x01'

        >>> dt.time = 16385
        >>> dt.getBytes()
        b'\x81\x80\x01'
        '''
        midiBytes = putVariableLengthNumber(self.time)
        return midiBytes


class MidiTrack(prebase.ProtoM21Object):
    r'''
    A MIDI Track. Each track contains an index and a list of events.

    All events are stored in the `events` list, in order.

    An `index` is an integer identifier for this object.  It is often called
    "trackId" though technically the id for a MidiTrack is always b'MTrk'

    >>> mt = midi.MidiTrack(index=3)
    >>> mt.events
    []
    >>> mt.index
    3

    The data consists of all the midi data after b'MTrk'

    >>> mt.data
    b''

    And the .length is the same as the data's length

    >>> mt.length
    0

    After reading a string

    >>> mt.read(b'MTrk\x00\x00\x00\x16\x00\xff\x03\x00\x00'
    ...         + b'\xe0\x00@\x00\x90CZ\x88\x00\x80C\x00\x88\x00\xff/\x00')
    b''

    The returned value is what is left over after the track is read
    (for instance the data for another track)

    >>> mt.length
    22

    New in v9.7: len(mt) returns the same as mt.length, but more Pythonic.

    >>> len(mt)
    22

    >>> mt.data[:8]
    b'\x00\xff\x03\x00\x00\xe0\x00@'

    Note that the '\x16' got translated to ascii '@'.

    >>> mt.events
    [<music21.midi.DeltaTime (empty) track=3>,
     <music21.midi.MidiEvent SEQUENCE_TRACK_NAME, track=3, data=b''>,
     <music21.midi.DeltaTime (empty) track=3>,
     <music21.midi.MidiEvent PITCH_BEND, track=3, channel=1, parameter1=0, parameter2=64>,
     <music21.midi.DeltaTime (empty) track=3>,
     <music21.midi.MidiEvent NOTE_ON, track=3, channel=1, pitch=67, velocity=90>,
     <music21.midi.DeltaTime t=1024, track=3>,
     <music21.midi.MidiEvent NOTE_OFF, track=3, channel=1, pitch=67, velocity=0>,
     <music21.midi.DeltaTime t=1024, track=3>,
     <music21.midi.MidiEvent END_OF_TRACK, track=3, data=b''>]

    >>> mt
    <music21.midi.MidiTrack 3 -- 10 events>

    There is a class attribute of the headerId which is the same for
    all MidiTrack objects

    >>> midi.MidiTrack.headerId
    b'MTrk'
    '''
    headerId = b'MTrk'

    def __init__(self, index: int = 0):
        self.index = index
        self.events: list[MidiEvent] = []  # or DeltaTime subclass
        self.data = b''

    def __len__(self) -> int:
        '''
        New in v9.7
        '''
        return len(self.data)

    @property
    def length(self) -> int:
        return len(self.data)

    def read(self, midiBytes: bytes) -> bytes:
        '''
        Read as much of the bytes object (representing midi data) as necessary;
        return the remaining bytes object for reassignment and further processing.

        The string should begin with `MTrk`, specifying a Midi Track

        Stores the read data (after the header and length information) in self.data

        Calls `processDataToEvents` which creates
        :class:`~music21.midi.DeltaTime`
        and :class:`~music21.midi.MidiEvent` objects and stores them in self.events
        '''
        if not midiBytes[:4] == self.headerId:
            raise MidiException('badly formed midi string: missing leading MTrk')
        # get the 4 chars after the MTrk encoding
        length, midiBytes = getNumber(midiBytes[4:], 4)
        # environLocal.printDebug(['MidiTrack.read(): got chunk size', length])

        # all event data is in the track str
        trackData = midiBytes[:length]
        self.data = trackData

        remainder = midiBytes[length:]
        self.processDataToEvents(trackData)
        return remainder  # remainder string after extracting track data

    def processDataToEvents(self, trackData: bytes = b'') -> None:
        '''
        Populate .events with trackData.  Called by .read()
        '''
        time: int = 0  # a running counter of ticks
        previousMidiEvent: MidiEvent|None = None

        dt: int
        trackDataCandidate: bytes
        timeCandidate: int

        while trackData:
            # shave off the time stamp from the event
            delta_t = DeltaTime(track=self)
            # return extracted time, as well as remaining bytes
            dt, trackDataCandidate = delta_t.readUntilLowByte(trackData)
            # this is the offset that this event happens at, in ticks
            timeCandidate = time + dt

            # pass self to event, set this MidiTrack as the track for this event
            midiEvent = MidiEvent(track=self)
            if previousMidiEvent is not None:  # synchronize the last status byte
                midiEvent.lastStatusByte = previousMidiEvent.lastStatusByte

            # some midi events may raise errors; simply skip for now
            try:
                trackData = midiEvent.read(trackDataCandidate)
                time = timeCandidate
            except MidiException:
                # assume that trackData, after delta extraction, is still correct
                # environLocal.printDebug(['forced to skip event; delta_t:', delta_t])
                # set to result after taking delta time
                trackData = trackDataCandidate
                continue

            # only append if we get this far
            self.events.append(delta_t)
            self.events.append(midiEvent)
            previousMidiEvent = midiEvent

    def getBytes(self) -> bytes:
        r'''
        Returns bytes of midi-data from the `.events` in the object.
        For conversion from music21 to MIDI.

        For example: two events, one note-on and one note-off on C4 which appears as "<"
        in the data.

        >>> mt = midi.MidiTrack(index=2)
        >>> dt1 = midi.DeltaTime(mt, time=0)
        >>> noteOn = midi.MidiEvent(mt, type=midi.ChannelVoiceMessages.NOTE_ON, channel=3)
        >>> noteOn.pitch = 60
        >>> noteOn.velocity = 20
        >>> dt2 = midi.DeltaTime(mt, time=1030)
        >>> noteOff = midi.MidiEvent(mt, type=midi.ChannelVoiceMessages.NOTE_OFF, channel=3)
        >>> noteOff.pitch = 60
        >>> noteOff.velocity = 0

        >>> mt.events = [dt1, noteOn, dt2, noteOff]
        >>> bytes = mt.getBytes()
        >>> bytes
        b'MTrk\x00\x00\x00\t\x00\x92<\x14\x88\x06\x82<\x00'

        Explanation:

        The first four bytes `MTrk` are the header for any MIDI Track

        >>> bytes[:4]
        b'MTrk'

        The next four bytes are the length of the data in bytes, the final `b'\t'`
        indicates there are 9 bytes to follow.

        >>> midi.base.getNumber(bytes[4:8], 4)
        (9, b'')

        The next byte is an empty delta time event.

        >>> bytes[8]
        0

        The next three bytes are the note-on event.

        >>> noteOn2 = midi.MidiEvent()
        >>> _ = noteOn2.parseChannelVoiceMessage(bytes[9:12])
        >>> noteOn2
        <music21.midi.MidiEvent NOTE_ON, track=None, channel=3, pitch=60, velocity=20>

        Followed by two bytes for the DeltaTime of 1030 ticks.

        >>> dt3 = midi.DeltaTime()
        >>> dt3.readUntilLowByte(bytes[12:14])
        (1030, b'')

        The 1030 is stored as b'\x88\x06' where the first byte is 136 and the second 6,
        but MIDI stores each continuing digit as the last 7 bits of a 8-bit number with
        first bit 1, so we remove the first bit by subtracting 128: 136 - 128 = 8.
        Then we multiply 8 by 128 to get 1024 and add 6 to get 1030.

        Finally, the last three bytes are the note-off event.

        >>> noteOff2 = midi.MidiEvent()
        >>> _ = noteOff2.parseChannelVoiceMessage(bytes[14:])
        >>> noteOff2
        <music21.midi.MidiEvent NOTE_OFF, track=None, channel=3, pitch=60, velocity=0>
        '''
        # set time to the first event
        # time = self.events[0].time
        # build str using MidiEvents
        midiBytes: list[bytes] = []
        for midiEvent in self.events:
            # this writes both delta time and message events
            try:
                midiBytes.append(midiEvent.getBytes())
            except MidiException as ex:
                environLocal.warn(f'Conversion error for {midiEvent}: {ex}; ignored.')

        bytes_out = b''.join(midiBytes)
        return self.headerId + putNumber(len(bytes_out), 4) + bytes_out

    def _reprInternal(self):
        r = f'{self.index} -- {len(self.events)} events'
        return r

    # --------------------------------------------------------------------------
    def updateEvents(self) -> None:
        '''
        We may attach events to this track before setting their `track` parameter.
        This method will move through all events and set their track to this track.

        >>> mt = midi.MidiTrack(index=2)
        >>> noteOn = midi.MidiEvent(type=midi.ChannelVoiceMessages.NOTE_ON, channel=1)
        >>> noteOn.pitch = 60
        >>> noteOn.velocity = 20
        >>> noteOn
        <music21.midi.MidiEvent NOTE_ON, track=None, channel=1, pitch=60, velocity=20>

        >>> mt.events = [noteOn]
        >>> mt.updateEvents()
        >>> noteOn
        <music21.midi.MidiEvent NOTE_ON, track=2, channel=1, pitch=60, velocity=20>
        >>> noteOn.track is mt
        True
        '''
        for e in self.events:
            e.track = self

    def hasNotes(self) -> bool:
        '''
        Return True/False if this track has any note-ons defined.

        >>> mt = midi.MidiTrack(index=2)
        >>> mt.hasNotes()
        False

        >>> noteOn = midi.MidiEvent(type=midi.ChannelVoiceMessages.NOTE_ON, channel=1)
        >>> mt.events = [noteOn]

        >>> mt.hasNotes()
        True
        '''
        for e in self.events:
            if e.isNoteOn():
                return True
        return False

    def setChannel(self, value: int) -> None:
        '''
        Set the one-indexed channel of all events in this Track.

        >>> mt = midi.MidiTrack(index=2)
        >>> noteOn = midi.MidiEvent(type=midi.ChannelVoiceMessages.NOTE_ON, channel=1)
        >>> mt.events = [noteOn]
        >>> mt.setChannel(11)
        >>> noteOn.channel
        11

        Channel must be a value from 1-16

        >>> mt.setChannel(22)
        Traceback (most recent call last):
        music21.midi.base.MidiException: bad channel value: 22
        '''
        if value not in range(1, 17):  # count from 1
            raise MidiException(f'bad channel value: {value}')
        for e in self.events:
            e.channel = value

    def getChannels(self) -> list[int]:
        '''
        Get all channels (excluding None) used in this Track (sorted)

        >>> mt = midi.MidiTrack(index=2)
        >>> noteOn = midi.MidiEvent(type=midi.ChannelVoiceMessages.NOTE_ON, channel=14)
        >>> noteOn2 = midi.MidiEvent(type=midi.ChannelVoiceMessages.NOTE_ON, channel=5)
        >>> noteOn3 = midi.MidiEvent(type=midi.ChannelVoiceMessages.NOTE_ON, channel=14)
        >>> noteOn4 = midi.MidiEvent(type=midi.ChannelVoiceMessages.PROGRAM_CHANGE, channel=None)

        >>> mt.events = [noteOn, noteOn2, noteOn3, noteOn4]

        >>> mt.getChannels()
        [5, 14]
        '''
        post: set[int] = set()
        for e in self.events:
            if e.channel is not None:
                post.add(e.channel)
        return sorted(post)

    def getProgramChanges(self) -> list[int]:
        '''
        Get all unique program changes used in this Track, in order they appear.

        >>> mt = midi.MidiTrack(index=2)
        >>> pc1 = midi.MidiEvent(type=midi.ChannelVoiceMessages.PROGRAM_CHANGE)
        >>> pc1.data = 14
        >>> noteOn = midi.MidiEvent(type=midi.ChannelVoiceMessages.NOTE_ON, channel=14)
        >>> pc2 = midi.MidiEvent(type=midi.ChannelVoiceMessages.PROGRAM_CHANGE)
        >>> pc2.data = 1

        >>> mt.events = [pc1, noteOn, pc2]
        >>> mt.getProgramChanges()
        [14, 1]
        '''
        post: list[int] = []
        for e in self.events:
            if (e.type == ChannelVoiceMessages.PROGRAM_CHANGE
                    and isinstance(e.data, int)
                    and e.data not in post):  # O(127) = O(1), faster than a set lookup + append
                post.append(e.data)
        return post


class MidiFile(prebase.ProtoM21Object):
    '''
    Low-level MIDI file writing, emulating methods from normal Python files.

    For most users, do not go here, simply use:

        score = converter.parse('path/to/file/in.mid')
        midi_out = score.write('midi', fp='path/to/file/out.mid')

    The `ticksPerQuarterNote` attribute must be set before writing. 1024 is a common value.

    This object is returned by some properties for directly writing files of midi representations.

    >>> mf = midi.MidiFile()
    >>> mf
    <music21.midi.MidiFile 0 tracks>

    Music21 can read format 0 and format 1, and writes format 1.  Format 2 files
    are not parsable.

    >>> mf.format
    1

    After loading or before writing, tracks are stored in this list.

    >>> mf.tracks
    []

    Most midi files store `ticksPerQuarterNote` and not `ticksPerSecond`

    >>> mf.ticksPerQuarterNote
    10080
    >>> mf.ticksPerSecond is None
    True

    All MidiFiles have the same `headerId`

    >>> midi.MidiFile.headerId
    b'MThd'
    '''
    headerId = b'MThd'

    def __init__(self) -> None:
        self.file: t.BinaryIO|None = None
        self.format: int = 1
        self.tracks: list[MidiTrack] = []
        self.ticksPerQuarterNote: int = defaults.ticksPerQuarter
        self.ticksPerSecond: int|None = None

    def open(self, filename, attrib='rb') -> None:
        '''
        Open a MIDI file path for reading or writing.

        For writing to a MIDI file, `attrib` should be "wb".
        '''
        if attrib not in ['rb', 'wb']:
            raise MidiException('cannot read or write unless in binary mode, not:', attrib)
        # pylint: disable-next=consider-using-with, unspecified-encoding
        self.file = t.cast(t.BinaryIO, open(filename, attrib))

    def openFileLike(self, fileLike: t.BinaryIO) -> None:
        '''
        Assign a file-like object, such as those provided by BytesIO, as an open file object.

        >>> from io import BytesIO
        >>> fileLikeOpen = BytesIO()
        >>> mf = midi.MidiFile()
        >>> mf.openFileLike(fileLikeOpen)
        >>> mf.close()
        '''
        self.file = fileLike

    def _reprInternal(self) -> str:
        lenTracks = len(self.tracks)
        plural = 's' if lenTracks != 1 else ''
        return f'{lenTracks} track{plural}'

    def close(self) -> None:
        '''
        Close the file.
        '''
        if not self.file:
            # nothing to do
            return

        self.file.close()

    def read(self) -> None:
        '''
        Read and parse MIDI data stored in a file.
        '''
        if not self.file:
            raise TypeError('No file is open.')

        self.readstr(self.file.read())

    def readstr(self, midiBytes: bytes) -> None:
        '''
        Read and parse MIDI data as a bytes, putting the
        data in `.ticksPerQuarterNote` and a list of
        `MidiTrack` objects in the attribute `.tracks`.

        The name readstr is a carryover from Python 2.
        It works on bytes objects, not strings
        '''
        if not midiBytes[:4] == b'MThd':
            raise MidiException(f'badly formatted midi bytes, got: {midiBytes[:20]!r}')

        # we step through the str src, chopping off characters as we go
        # and reassigning to str
        length, midiBytes = getNumber(midiBytes[4:], 4)
        if length != 6:
            raise MidiException('badly formatted midi bytes')

        midiFormatType, midiBytes = getNumber(midiBytes, 2)
        self.format = midiFormatType
        if midiFormatType not in (0, 1):
            raise MidiException(f'cannot handle midi file format: {format}')

        numTracks, midiBytes = getNumber(midiBytes, 2)
        division, midiBytes = getNumber(midiBytes, 2)

        # very few midi files seem to define ticksPerSecond
        if division & 0x8000:
            framesPerSecond = -((division >> 8) | -0x80)
            ticksPerFrame = division & 0xFF
            if ticksPerFrame not in [24, 25, 29, 30]:
                raise MidiException(f'cannot handle ticks per frame: {ticksPerFrame}')
            if ticksPerFrame == 29:
                ticksPerFrame = 30  # drop frame
            self.ticksPerSecond = ticksPerFrame * framesPerSecond
        else:
            self.ticksPerQuarterNote = division & 0x7FFF

        # environLocal.printDebug(['MidiFile.readstr(): got midi file format:', self.format,
        # 'with specified number of tracks:', numTracks, 'ticksPerSecond:', self.ticksPerSecond,
        # 'ticksPerQuarterNote:', self.ticksPerQuarterNote])

        for i in range(numTracks):
            trk = MidiTrack(i)  # sets the MidiTrack index parameters
            midiBytes = trk.read(midiBytes)  # pass all the remaining bytes, reassigning
            self.tracks.append(trk)

    def write(self) -> None:
        '''
        Write MIDI data as a file to the file opened with `.open()`.
        '''
        if not self.file:
            raise TypeError('No file is open.')

        ws = self.writestr()
        self.file.write(ws)

    def writestr(self) -> bytes:
        '''
        Generate the MIDI data header and convert the list of
        MidiTrack objects in self.tracks into MIDI data and return it as bytes.

        The name `writestr` is a carry-over from Python 2.  It works on bytes, not strings.
        '''
        midiBytes = self.writeMThdStr()
        for trk in self.tracks:
            midiBytes = midiBytes + trk.getBytes()
        return midiBytes

    def writeMThdStr(self) -> bytes:
        '''
        Convert the information in self.ticksPerQuarterNote
        into MIDI data header and return it as bytes.

        The name `writeMThdStr` is a carry-over from Python 2.  It works on bytes, not strings.
        '''
        division = self.ticksPerQuarterNote
        # Don't handle ticksPerSecond yet, too confusing
        if (division & 0x8000) != 0:
            raise MidiException(
                'Cannot write midi bytes unless self.ticksPerQuarterNote is a multiple of 1024')
        midiBytes = self.headerId + putNumber(6, 4) + putNumber(self.format, 2)
        midiBytes = midiBytes + putNumber(len(self.tracks), 2)
        midiBytes = midiBytes + putNumber(division, 2)
        return midiBytes


# ------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER: list[type] = [MidiEvent, DeltaTime, MidiTrack, MidiFile]

if __name__ == '__main__':
    import music21
    music21.mainTest()


