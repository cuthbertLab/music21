# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         midi/__init__.py
# Purpose:      Access to MIDI library / music21 classes for dealing with midi data
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#               (Will Ware -- see docs)
#
# Copyright:    Copyright © 2011-2013, 2019 Michael Scott Cuthbert and the music21 Project
#               Some parts of this module are in the Public Domain, see details.
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
Objects and tools for processing MIDI data.  Converts from MIDI files to
:class:`~music21.midi.MidiEvent`, :class:`~music21.midi.MidiTrack`, and
:class:`~music21.midi.MidiFile` objects, and vice-versa.

Further conversion to-and-from MidiEvent/MidiTrack/MidiFile and music21 Stream,
Note, etc., objects takes place in :ref:`moduleMidiTranslate`.

This module originally used routines from Will Ware's public domain midi.py
library from 2001 see
http://groups.google.com/group/alt.sources/msg/0c5fc523e050c35e
'''
__all__ = [
    'realtime', 'percussion',
    'MidiEvent', 'MidiFile', 'MidiTrack', 'MidiException',
    'DeltaTime',
    'MetaEvents', 'ChannelVoiceMessages', 'ChannelModeMessages',
    'SysExEvents',
    'EnumerationException',
]

import io
import re
import os
import string
import struct
import sys
import unicodedata  # @UnresolvedImport
import unittest
from typing import Optional, Union, Tuple

from enum import IntEnum

from music21 import common
from music21 import environment
from music21 import exceptions21
from music21 import prebase

from music21.midi import realtime
from music21.midi import percussion

_MOD = 'midi'
environLocal = environment.Environment(_MOD)


# good midi reference:
# http://www.sonicspot.com/guide/midifiles.html
# ------------------------------------------------------------------------------
class EnumerationException(exceptions21.Music21Exception):
    pass


class MidiException(exceptions21.Music21Exception):
    pass


# ------------------------------------------------------------------------------
def charToBinary(char):
    '''
    Convert a char into its binary representation. Useful for debugging.

    >>> midi.charToBinary('a')
    '01100001'
    '''
    asciiValue = ord(char)
    binaryDigits = []
    while asciiValue:
        if (asciiValue & 1) == 1:
            binaryDigits.append('1')
        else:
            binaryDigits.append('0')
        asciiValue = asciiValue >> 1

    binaryDigits.reverse()
    binary = ''.join(binaryDigits)
    zeroFix = (8 - len(binary)) * '0'
    return zeroFix + binary


def intsToHexBytes(intList):
    r'''
    Convert a list of integers into hex bytes, suitable for testing MIDI encoding.

    Here we take NOTE_ON message, Middle C, 120 velocity and translate it to bytes

    >>> midi.intsToHexBytes([0x90, 60, 120])
    b'\x90<x'
    '''
    # note off are 128 (0x80) to 143 (0x8F)
    # note on messages are decimal 144 (0x90) to 159 (0x9F)
    post = b''
    for i in intList:
        # B is an unsigned char
        # this forces values between 0 and 255
        # the same as chr(int)
        post += struct.pack('>B', i)
    return post


def getNumber(midiStr, length):
    '''
    Return the value of a string byte or bytes if length > 1
    from an 8-bit string or bytes object

    Then, return the remaining string or bytes object

    The `length` is the number of chars to read.
    This will sum a length greater than 1 if desired.

    Note that MIDI uses big-endian for everything.
    This is the inverse of Python's chr() function.

    >>> midi.getNumber('test', 0)
    (0, 'test')

    Given bytes, return bytes:

    >>> midi.getNumber(b'test', 0)
    (0, b'test')

    >>> midi.getNumber('test', 2)
    (29797, 'st')
    >>> midi.getNumber(b'test', 4)
    (1952805748, b'')
    '''
    summation = 0
    if not common.isNum(midiStr):
        for i in range(length):
            midiStrOrNum = midiStr[i]
            if common.isNum(midiStrOrNum):
                summation = (summation << 8) + midiStrOrNum
            else:
                summation = (summation << 8) + ord(midiStrOrNum)
        return summation, midiStr[length:]
    else:  # midiStr is a number...
        midNum = midiStr
        summation = midNum - ((midNum >> (8 * length)) << (8 * length))
        bigBytes = midNum - summation
        return summation, bigBytes


def getVariableLengthNumber(midiBytes):
    r'''
    Given a string or bytes of data, strip off the first character, or all high-byte characters
    terminating with one whose ord() function is < 0x80.  Thus a variable number of bytes
    might be read.

    After finding the appropriate termination,
    return the remaining string.

    This is necessary as DeltaTime times are given with variable size,
    and thus may be of different numbers if characters are used.

    >>> midi.getVariableLengthNumber(b'A-u')
    (65, b'-u')
    >>> midi.getVariableLengthNumber(b'-u')
    (45, b'u')
    >>> midi.getVariableLengthNumber('u')
    (117, b'')

    >>> midi.getVariableLengthNumber(b'test')
    (116, b'est')
    >>> midi.getVariableLengthNumber(b'E@-E')
    (69, b'@-E')
    >>> midi.getVariableLengthNumber(b'@-E')
    (64, b'-E')
    >>> midi.getVariableLengthNumber(b'-E')
    (45, b'E')
    >>> midi.getVariableLengthNumber('E')
    (69, b'')

    Test that variable length characters work:

    >>> midi.getVariableLengthNumber(b'\xff\x7f')
    (16383, b'')
    >>> midi.getVariableLengthNumber('中xy')
    (210638584, b'y')

    If no low-byte character is encoded, raises an IndexError

    >>> midi.getVariableLengthNumber('中国')
    Traceback (most recent call last):
    IndexError: index out of range
    '''
    # from http://faydoc.tripod.com/formats/mid.htm
    # This allows the number to be read one byte at a time, and when you see
    # a msb of 0, you know that it was the last (least significant) byte of the number.
    summation = 0
    i = 0
    if isinstance(midiBytes, str):
        midiBytes = midiBytes.encode('utf-8')

    while i < 999:  # should return eventually... was while True
        x = midiBytes[i]
        # environLocal.printDebug(['getVariableLengthNumber: examined char:',
        # charToBinary(midiBytes[i])])
        summation = (summation << 7) + (x & 0x7F)
        i += 1
        if not (x & 0x80):
            # environLocal.printDebug(['getVariableLengthNumber: depth read into string: %s' % i])
            return summation, midiBytes[i:]
    raise MidiException('did not find the end of the number!')


def getNumbersAsList(midiBytes):
    r'''
    Translate each char into a number, return in a list.
    Used for reading data messages where each byte encodes
    a different discrete value.

    >>> midi.getNumbersAsList(b'\x00\x00\x00\x03')
    [0, 0, 0, 3]
    '''
    post = []
    for i in range(len(midiBytes)):
        if common.isNum(midiBytes[i]):
            post.append(midiBytes[i])
        else:
            post.append(ord(midiBytes[i]))
    return post


def putNumber(num, length):
    r'''
    Put a single number as a hex number at the end of a string `length` bytes long.

    >>> midi.putNumber(3, 4)
    b'\x00\x00\x00\x03'
    >>> midi.putNumber(0, 1)
    b'\x00'
    '''
    lst = bytearray()

    for i in range(length):
        n = 8 * (length - 1 - i)
        thisNum = (num >> n) & 0xFF
        lst.append(thisNum)

    return bytes(lst)


def putVariableLengthNumber(x):
    r'''
    Turn a number into the smallest bytes object that can hold it for MIDI

    >>> midi.putVariableLengthNumber(4)
    b'\x04'
    >>> midi.putVariableLengthNumber(127)
    b'\x7f'
    >>> midi.putVariableLengthNumber(0)
    b'\x00'

    Numbers > 7bit but < 255 need two characters, with the first character to 0x80
    + n // 128

    >>> midi.putVariableLengthNumber(128)
    b'\x81\x00'
    >>> midi.putVariableLengthNumber(129)
    b'\x81\x01'
    >>> midi.putVariableLengthNumber(255)
    b'\x81\x7f'
    >>> midi.putVariableLengthNumber(256)
    b'\x82\x00'
    >>> midi.putVariableLengthNumber(1024)
    b'\x88\x00'
    >>> midi.putVariableLengthNumber(8193)
    b'\xc0\x01'
    >>> midi.putVariableLengthNumber(16383)
    b'\xff\x7f'

    Numbers > 16383 are not really MIDI numbers, but this is how they work:

    >>> midi.putVariableLengthNumber(16384)
    b'\x81\x80\x00'
    >>> midi.putVariableLengthNumber(16384 + 128)
    b'\x81\x81\x00'
    >>> midi.putVariableLengthNumber(16384 * 2)
    b'\x82\x80\x00'
    >>> midi.putVariableLengthNumber(16384 ** 2)
    b'\x81\x80\x80\x80\x00'

    >>> midi.putVariableLengthNumber(-1)
    Traceback (most recent call last):
    music21.midi.MidiException: cannot putVariableLengthNumber() when number is negative: -1
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


def putNumbersAsList(numList):
    r'''
    Translate a list of numbers (0-255) into bytes.
    Used for encoding data messages where each byte encodes a different discrete value.

    >>> midi.putNumbersAsList([0, 0, 0, 3])
    b'\x00\x00\x00\x03'

    If a number is < 0 then it wraps around from the top.

    >>> midi.putNumbersAsList([0, 0, 0, -3])
    b'\x00\x00\x00\xfd'
    >>> midi.putNumbersAsList([0, 0, 0, -1])
    b'\x00\x00\x00\xff'

    list can be of any length

    >>> midi.putNumbersAsList([1, 16, 255])
    b'\x01\x10\xff'

    Any number > 255 raises an exception:

    >>> midi.putNumbersAsList([256])
    Traceback (most recent call last):
    music21.midi.MidiException: Cannot place a number > 255 in a list: 256
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


class _ContainsEnum(IntEnum):
    def __repr__(self):
        val = super().__repr__()
        return re.sub(r'(\d+)', lambda m: f'0x{int(m.group(1)):X}', val)

    @classmethod
    def hasValue(cls, val):
        return val in cls.__members__.values()


class ChannelVoiceMessages(_ContainsEnum):
    NOTE_OFF = 0x80
    NOTE_ON = 0x90
    POLYPHONIC_KEY_PRESSURE = 0xA0
    CONTROLLER_CHANGE = 0xB0
    PROGRAM_CHANGE = 0xC0
    CHANNEL_KEY_PRESSURE = 0xD0
    PITCH_BEND = 0xE0


class ChannelModeMessages(_ContainsEnum):
    ALL_SOUND_OFF = 0x78
    RESET_ALL_CONTROLLERS = 0x79
    LOCAL_CONTROL = 0x7A
    ALL_NOTES_OFF = 0x7B
    OMNI_MODE_OFF = 0x7C
    OMNI_MODE_ON = 0x7D
    MONO_MODE_ON = 0x7E
    POLY_MODE_ON = 0x7F


class MetaEvents(_ContainsEnum):
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


class SysExEvents(_ContainsEnum):
    F0_SYSEX_EVENT = 0xF0
    F7_SYSEX_EVENT = 0xF7


METAEVENT_MARKER = 0xFF

# ------------------------------------------------------------------------------


class MidiEvent:
    '''
    A model of a MIDI event, including note-on, note-off, program change,
    controller change, any many others.

    MidiEvent objects are paired (preceded) by :class:`~music21.midi.DeltaTime`
    objects in the list of events in a MidiTrack object.

    The `track` argument must be a :class:`~music21.midi.MidiTrack` object.

    The `type` attribute is an enumeration of a Midi event from the ChannelVoiceMessages
    or metaEvents enums.

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


    >>> mt = midi.MidiTrack(1)
    >>> me1 = midi.MidiEvent(mt)
    >>> me1.type = midi.ChannelVoiceMessages.NOTE_ON
    >>> me1.channel = 3
    >>> me1.time = 200
    >>> me1.pitch = 60
    >>> me1.velocity = 120
    >>> me1
    <MidiEvent NOTE_ON, t=200, track=1, channel=3, pitch=60, velocity=120>

    >>> me2 = midi.MidiEvent(mt)
    >>> me2.type = midi.MetaEvents.SEQUENCE_TRACK_NAME
    >>> me2.data = 'guitar'
    >>> me2
    <MidiEvent SEQUENCE_TRACK_NAME, t=0, track=1, channel=None, data=b'guitar'>
    '''
    # pylint: disable=redefined-builtin

    def __init__(self,
                 track: Optional['music21.midi.MidiTrack'] = None,
                 type=None,  # @ReservedAssignment
                 time: int = 0,
                 channel=None):
        self.track: Optional['music21.midi.MidiTrack'] = track  # a MidiTrack object
        self.type = type
        self.time: int = time
        self.channel: Optional[int] = channel

        self.parameter1: Union[int, bytes, None] = None  # pitch or first data value
        self.parameter2: Union[int, bytes, None] = None  # velocity or second data value

        # data is a property...

        # if this is a Note on/off, need to store original
        # pitch space value in order to determine if this is has a microtone
        self.centShift: Optional[int] = None

        # store a reference to a corresponding event
        # if a noteOn, store the note off, and vice versa
        # circular ref -- but modern Python will garbage collect it.
        self.correspondingEvent = None

        # store and pass on a running status if found
        self.lastStatusByte: Optional[int] = None

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
        [<MidiEvent NOTE_OFF, t=0, track=None, channel=None>,
         <MidiEvent PITCH_BEND, t=0, track=None, channel=None>,
         <MidiEvent NOTE_ON, t=0, track=None, channel=None>]
        '''
        # update based on type; type may be set after init
        if self.type == ChannelVoiceMessages.NOTE_OFF:  # should come before pitch bend
            return -20
        elif self.type == ChannelVoiceMessages.PITCH_BEND:  # go before note events
            return -10
        else:
            return 0

    def __repr__(self):
        if self.track is None:
            trackIndex = None
        elif isinstance(self.track, int):
            trackIndex = self.track
        else:
            trackIndex = self.track.index

        if isinstance(self.type, _ContainsEnum):
            printType = self.type.name
        elif self.type == 'DeltaTime':
            printType = self.type
        else:
            printType = repr(self.type)

        r = ('<MidiEvent %s, t=%s, track=%s, channel=%s' %
             (printType, repr(self.time), trackIndex,
              repr(self.channel)))
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
        return r + '>'

    # provide parameter access to pitch and velocity
    def _setPitch(self, value):
        self.parameter1 = value

    def _getPitch(self):
        # only return pitch if this is note on /off
        if self.type in (ChannelVoiceMessages.NOTE_ON, ChannelVoiceMessages.NOTE_OFF):
            return self.parameter1
        else:
            return None

    pitch = property(_getPitch, _setPitch)

    def _setVelocity(self, value):
        self.parameter2 = value

    def _getVelocity(self):
        return self.parameter2

    velocity = property(_getVelocity, _setVelocity)

    # store generic data in parameter 1

    def _setData(self, value):
        if value is not None and not isinstance(value, bytes):
            if isinstance(value, str):
                value = value.encode('utf-8')
            elif isinstance(value, bool):
                value = bytes([int(value)])

        self.parameter1 = value

    def _getData(self):
        return self.parameter1

    data = property(_getData, _setData, doc=r'''
        Read or set the data (`.parameter1`) for the object

        Does some automatic conversions:

        >>> me = midi.MidiEvent(type=midi.ChannelModeMessages.LOCAL_CONTROL)
        >>> me.data = True
        >>> me.data
        b'\x01'
    ''')

    def setPitchBend(self, cents, bendRange=2):
        '''
        Treat this event as a pitch bend value, and set the .parameter1 and
         .parameter2 fields appropriately given a specified bend value in cents.

        Also called Pitch Wheel

        The `bendRange` parameter gives the number of half steps in the bend range.


        >>> mt = midi.MidiTrack(1)
        >>> me1 = midi.MidiEvent(mt)
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


        Parameter 2 is most significant digit, not
        parameter 1.

        >>> me1.setPitchBend(101)
        >>> me1.parameter1, me1.parameter2
        (40, 96)

        Exceeding maximum sets max

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

        Pitch bends very close to 0 had problems

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

        # produce a two-char value
        charValue = putVariableLengthNumber(target)
        d1, junk = getNumber(charValue[0], 1)  # d1 = parameter2
        # need to convert from 8 bit to 7, so using & 0x7F
        d1 = d1 & 0x7F
        if len(charValue) > 1:
            d2, junk = getNumber(charValue[1], 1)
            d2 = d2 & 0x7F
        else:
            d2 = d1
            d1 = 0



        # environLocal.printDebug(['got target char value', charValue,
        # 'getVariableLengthNumber(charValue)', getVariableLengthNumber(charValue)[0],
        # 'd1', d1, 'd2', d2,])

        self.parameter1 = d2
        self.parameter2 = d1  # d1 is most significant byte here

    def parseChannelVoiceMessage(self, midiBytes: bytes) -> bytes:
        r'''
        Take a set of bytes that represent a ChannelVoiceMessage and set the
        appropriate enumeration value and data, returning the remaining bytes.

        These are started with messages from 0x80 to 0xEF


        Demonstration.  First let's create a helper function and a MidiEvent:

        >>> to_bytes = midi.intsToHexBytes
        >>> midBytes = to_bytes([0x90, 60, 120])
        >>> midBytes
        b'\x90<x'
        >>> midBytes += b'hello'
        >>> mt = midi.MidiTrack(1)
        >>> me1 = midi.MidiEvent(mt)
        >>> me1
        <MidiEvent None, t=0, track=1, channel=None>


        Now show how the midiBytes changes the event:

        >>> remainder = me1.parseChannelVoiceMessage(midBytes)
        >>> me1
        <MidiEvent NOTE_ON, t=0, track=1, channel=1, pitch=60, velocity=120>

        The remainder would probably contain a delta time and following
        events, but here we'll just show that it passes through.

        >>> remainder
        b'hello'

        We will ignore remainders from now on.

        All attributes are set properly:

        >>> me1.type
        <ChannelVoiceMessages.NOTE_ON: 0x90>
        >>> me1.pitch  # 60 = middle C
        60
        >>> me1.velocity
        120
        >>> me1.channel
        1


        Here we send the message for a note on on another channel (0x91 = channel 2):

        >>> rem = me1.parseChannelVoiceMessage(to_bytes([0x91, 60, 120]))
        >>> me1
        <MidiEvent NOTE_ON, t=0, track=1, channel=2, pitch=60, velocity=120>
        >>> me1.channel
        2

        Now let's make a program change

        >>> me2 = midi.MidiEvent(mt)
        >>> rem = me2.parseChannelVoiceMessage(to_bytes([0xC0, 71]))
        >>> me2
        <MidiEvent PROGRAM_CHANGE, t=0, track=1, channel=1, data=71>
        >>> me2.data  # 71 = clarinet (0-127 indexed)
        71

        Program change and channel pressure only go to 127.  More than that is an error:

        >>> me2.parseChannelVoiceMessage(to_bytes([0xC0, 200]))
        Traceback (most recent call last):
        music21.midi.MidiException: Cannot have a
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

    def read(self, midiBytes):
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

        # detect running status: if the status byte is less than 0x80, its
        # not a status byte, but a data byte
        if byte0 < 0x80:
            # environLocal.printDebug(['MidiEvent.read(): found running status even data',
            # 'self.lastStatusByte:', self.lastStatusByte])

            if self.lastStatusByte is not None:
                rsb = bytes([self.lastStatusByte])
            else:  # provide a default
                rsb = b'\x90'
            # add the running status byte to the front of the string
            # and process as before
            midiBytes = rsb + midiBytes
            byte0 = midiBytes[0]
        else:
            # store last status byte
            self.lastStatusByte = midiBytes[0]

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
            if not MetaEvents.hasValue(byte1):
                environLocal.printDebug([f'unknown meta event: FF {byte1:02X}'])
                sys.stdout.flush()
                raise MidiException(f'Unknown midi event type: FF {byte1:02X}')
            self.type = MetaEvents(byte1)
            length, midiBytesAfterLength = getVariableLengthNumber(midiBytes[2:])
            self.data = midiBytesAfterLength[:length]
            # return remainder
            return midiBytesAfterLength[length:]
        else:
            # an uncaught message
            environLocal.printDebug(['got unknown midi event type', hex(byte0),
                                     'hex(midiBytes[1])', hex(midiBytes[1])])
            raise MidiException(f'Unknown midi event type {hex(byte0)}')

    def getBytes(self):
        r'''
        Return a set of bytes for this MIDI event.

        >>> noteOn = midi.MidiEvent(type=midi.ChannelVoiceMessages.NOTE_ON, channel=10)
        >>> noteOn.pitch = 60
        >>> noteOn.velocity = 127
        >>> noteOn.getBytes()
        b'\x99<\x7f'
        >>> noteOn.pitch = 62
        >>> noteOn.getBytes()
        b'\x99>\x7f'
        '''
        if self.type in ChannelVoiceMessages:
            # environLocal.printDebug(['writing channelVoiceMessages', self.type])
            bytes0 = bytes([self.channel - 1 + self.type.value])
            # for writing note-on/note-off
            if self.type not in (ChannelVoiceMessages.PROGRAM_CHANGE,
                                 ChannelVoiceMessages.CHANNEL_KEY_PRESSURE):
                # this results in a two-part string, like '\x00\x00'
                param1data = b''
                if isinstance(self.parameter1, int):
                    param1data = bytes([self.parameter1])
                else:
                    param1data = self.parameter1

                param2data = b''
                if isinstance(self.parameter2, int):
                    param2data = bytes([self.parameter2])
                else:
                    param2data = self.parameter2

                data = param1data + param2data
            elif self.type == ChannelVoiceMessages.PROGRAM_CHANGE:
                data = bytes([self.data])
            else:  # all other messages
                try:
                    if isinstance(self.data, int):
                        data = bytes([self.data])
                    else:
                        data = self.data
                except (TypeError, ValueError):
                    raise MidiException(
                        f'Got incorrect data for {self} in .data: {self.data}, '
                        + 'cannot parse Miscellaneous Message')
            return bytes0 + data

        elif self.type in ChannelModeMessages:
            channelMode = bytes([0xB0 + self.channel - 1])
            msgValue = bytes([self.type.value])
            if isinstance(self.data, int):
                data = bytes([self.data])
            else:
                data = self.data
            return channelMode + msgValue + data

        elif self.type in SysExEvents:
            s = bytes([self.type.value])
            s = s + putVariableLengthNumber(len(self.data))
            return s + self.data

        elif self.type in MetaEvents:
            s = bytes([METAEVENT_MARKER])
            s += bytes([self.type.value])
            s += putVariableLengthNumber(len(self.data))

            try:
                return s + self.data
            except (UnicodeDecodeError, TypeError):
                # environLocal.printDebug(['cannot decode data', self.data])
                return s + unicodedata.normalize('NFKD',
                                                 self.data).encode('ascii', 'ignore')
        else:
            raise MidiException(f'unknown midi event type: {self.type!r}')

    # --------------------------------------------------------------------------
    def isNoteOn(self):
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
        '''
        if self.type == ChannelVoiceMessages.NOTE_ON and self.velocity != 0:
            return True
        return False

    def isNoteOff(self):
        '''
        Return a boolean if this is should be interpreted as a note-off message,
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
        '''
        if self.type == ChannelVoiceMessages.NOTE_OFF:
            return True
        elif self.type == ChannelVoiceMessages.NOTE_ON and self.velocity == 0:
            return True
        return False

    def isDeltaTime(self):
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

    def matchedNoteOff(self, other):
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
        '''
        if other.isNoteOff():
            # might check velocity here too?
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
    unless overridden (don't!).

    >>> mt = midi.MidiTrack(1)
    >>> dt = midi.DeltaTime(mt)
    >>> dt.time = 1
    >>> dt
    <MidiEvent DeltaTime, t=1, track=1, channel=None>
    '''

    def __init__(self, track, time=0, channel=None):
        super().__init__(track, time=time, channel=channel)
        self.type = 'DeltaTime'

    def read(self, oldBytes: bytes) -> Tuple[int, bytes]:
        r'''
        Read a byte-string until hitting a character below 0x80
        and return the converted number and the rest of the bytes

        >>> mt = midi.MidiTrack(1)
        >>> dt = midi.DeltaTime(mt)
        >>> dt.read(b'\x20')
        (32, b'')
        >>> dt.read(b'\x20hello')
        (32, b'hello')

        here the '\x82' is above 0x80 so the 'h' is read
        as part of the continuation.

        >>> dt.read(b'\x82hello')
        (360, b'ello')
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
    >>> mt.data[:8]
    b'\x00\xff\x03\x00\x00\xe0\x00@'

    Note that the '\x16' got translated to ascii '@'.

    >>> mt.events
    [<MidiEvent DeltaTime, t=0, track=3, channel=None>,
     <MidiEvent SEQUENCE_TRACK_NAME, t=0, track=3, channel=None, data=b''>,
     <MidiEvent DeltaTime, t=0, track=3, channel=None>,
     <MidiEvent PITCH_BEND, t=0, track=3, channel=1, parameter1=0, parameter2=64>,
     <MidiEvent DeltaTime, t=0, track=3, channel=None>,
     <MidiEvent NOTE_ON, t=0, track=3, channel=1, pitch=67, velocity=90>,
     <MidiEvent DeltaTime, t=1024, track=3, channel=None>,
     <MidiEvent NOTE_OFF, t=0, track=3, channel=1, pitch=67, velocity=0>,
     <MidiEvent DeltaTime, t=1024, track=3, channel=None>,
     <MidiEvent END_OF_TRACK, t=0, track=3, channel=None, data=b''>]

    >>> mt
    <music21.midi.MidiTrack 3 -- 10 events>

    There is a class attribute of the headerId which is the same for
    all MidiTrack objects

    >>> midi.MidiTrack.headerId
    b'MTrk'
    '''
    headerId = b'MTrk'

    def __init__(self, index=0):
        self.index = index
        self.events = []
        self.data = b''

    @property
    def length(self):
        return len(self.data)

    def read(self, midiBytes):
        '''
        Read as much of the string (representing midi data) as necessary;
        return the remaining string for reassignment and further processing.

        The string should begin with `MTrk`, specifying a Midi Track

        Calls `processDataToEvents` which creates and stores
        :class:`~music21.midi.DeltaTime`
        and :class:`~music21.midi.MidiEvent` objects.
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

    def processDataToEvents(self, trackData: bytes = b''):
        '''
        Populate .events with trackData.  Called by .read()
        '''
        time = 0  # a running counter of ticks
        previousMidiEvent = None
        while trackData:
            # shave off the time stamp from the event
            delta_t = DeltaTime(track=self)
            # return extracted time, as well as remaining bytes
            dt, trackDataCandidate = delta_t.read(trackData)
            # this is the offset that this event happens at, in ticks
            timeCandidate = time + dt

            # pass self to event, set this MidiTrack as the track for this event
            midiEvent = MidiEvent(track=self)
            if previousMidiEvent is not None:  # set the last status byte
                midiEvent.lastStatusByte = previousMidiEvent.lastStatusByte
            # some midi events may raise errors; simply skip for now
            try:
                trackDataCandidate = midiEvent.read(trackDataCandidate)
            except MidiException:
                # assume that trackData, after delta extraction, is still correct
                # environLocal.printDebug(['forced to skip event; delta_t:', delta_t])
                # set to result after taking delta time
                trackData = trackDataCandidate
                continue
            # only set after trying to read, which may raise exception
            time = timeCandidate
            trackData = trackDataCandidate  # remainder bytes
            # only append if we get this far
            self.events.append(delta_t)
            self.events.append(midiEvent)
            previousMidiEvent = midiEvent

    def getBytes(self):
        r'''
        returns bytes of midi-data from the `.events` in the object.

        >>> mt = midi.MidiTrack(index=2)
        >>> noteOn = midi.MidiEvent(mt, type=midi.ChannelVoiceMessages.NOTE_ON, channel=1)
        >>> noteOn.pitch = 60
        >>> noteOn.velocity = 20
        >>> dt = midi.DeltaTime(mt, time=1024)
        >>> noteOff = midi.MidiEvent(mt, type=midi.ChannelVoiceMessages.NOTE_OFF, channel=1)
        >>> noteOff.pitch = 60
        >>> noteOff.velocity = 0

        >>> mt.events = [noteOn, dt, noteOff]
        >>> mt.getBytes()
        b'MTrk\x00\x00\x00\x08\x90<\x14\x88\x00\x80<\x00'

        The b'\x08' indicates that there are 8 bytes to follow.
        '''
        # set time to the first event
        # time = self.events[0].time
        # build str using MidiEvents
        midiBytes = b''
        for midiEvent in self.events:
            # this writes both delta time and message events
            try:
                eventBytes = midiEvent.getBytes()
                intArray = []
                for x in eventBytes:
                    if common.isNum(x):
                        intArray.append(x)
                    else:
                        intArray.append(ord(x))
                eventBytes = bytes(bytearray(intArray))
                midiBytes = midiBytes + eventBytes
            except MidiException as ex:
                environLocal.warn(f'Conversion error for {midiEvent}: {ex}; ignored.')
        return self.headerId + putNumber(len(midiBytes), 4) + midiBytes

    def _reprInternal(self):
        r = f'{self.index} -- {len(self.events)} events'
        return r

    # --------------------------------------------------------------------------
    def updateEvents(self):
        '''
        We may attach events to this track before setting their `track` parameter.
        This method will move through all events and set their track to this track.

        >>> mt = midi.MidiTrack(index=2)
        >>> noteOn = midi.MidiEvent(type=midi.ChannelVoiceMessages.NOTE_ON, channel=1)
        >>> noteOn.pitch = 60
        >>> noteOn.velocity = 20
        >>> noteOn
        <MidiEvent NOTE_ON, t=0, track=None, channel=1, pitch=60, velocity=20>

        >>> mt.events = [noteOn]
        >>> mt.updateEvents()
        >>> noteOn
        <MidiEvent NOTE_ON, t=0, track=2, channel=1, pitch=60, velocity=20>
        >>> noteOn.track is mt
        True
        '''
        for e in self.events:
            e.track = self

    def hasNotes(self):
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

    def setChannel(self, value):
        '''
        Set the channel of all events in this Track.

        >>> mt = midi.MidiTrack(index=2)
        >>> noteOn = midi.MidiEvent(type=midi.ChannelVoiceMessages.NOTE_ON, channel=1)
        >>> mt.events = [noteOn]
        >>> mt.setChannel(11)
        >>> noteOn.channel
        11

        Channel must be a value from 1-16

        >>> mt.setChannel(22)
        Traceback (most recent call last):
        music21.midi.MidiException: bad channel value: 22
        '''
        if value not in range(1, 17):  # count from 1
            raise MidiException(f'bad channel value: {value}')
        for e in self.events:
            e.channel = value

    def getChannels(self):
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
        post = []
        for e in self.events:
            if e.channel not in post and e.channel is not None:
                post.append(e.channel)
        return sorted(post)

    def getProgramChanges(self):
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
        post = []
        for e in self.events:
            if e.type == ChannelVoiceMessages.PROGRAM_CHANGE:
                if e.data not in post:
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
    1024
    >>> mf.ticksPerSecond is None
    True

    All MidiFiles have the same `headerId`

    >>> midi.MidiFile.headerId
    b'MThd'
    '''
    headerId = b'MThd'

    def __init__(self):
        self.file = None
        self.format = 1
        self.tracks = []
        self.ticksPerQuarterNote = 1024
        self.ticksPerSecond = None

    def open(self, filename, attrib='rb'):
        '''
        Open a MIDI file path for reading or writing.

        For writing to a MIDI file, `attrib` should be "wb".
        '''
        if attrib not in ['rb', 'wb']:
            raise MidiException('cannot read or write unless in binary mode, not:', attrib)
        self.file = open(filename, attrib)

    def openFileLike(self, fileLike):
        '''Assign a file-like object, such as those provided by BytesIO, as an open file object.

        >>> from io import BytesIO
        >>> fileLikeOpen = BytesIO()
        >>> mf = midi.MidiFile()
        >>> mf.openFileLike(fileLikeOpen)
        >>> mf.close()
        '''
        self.file = fileLike

    def _reprInternal(self):
        lenTracks = len(self.tracks)
        plural = 's' if lenTracks != 1 else ''
        return f'{lenTracks} track{plural}'

    def close(self):
        '''
        Close the file.
        '''
        self.file.close()

    def read(self):
        '''
        Read and parse MIDI data stored in a file.
        '''
        self.readstr(self.file.read())

    def readstr(self, midiBytes):
        '''
        Read and parse MIDI data as a bytes, putting the
        data in `.ticksPerQuarterNote` and a list of
        `MidiTrack` objects in the attribute `.tracks`.

        The name readstr is a carryover from Python 2.  It works on bytes objects, not strings
        '''
        if not midiBytes[:4] == b'MThd':
            raise MidiException(f'badly formatted midi bytes, got: {midiBytes[:20]}')

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

    def write(self):
        '''
        Write MIDI data as a file to the file opened with `.open()`.
        '''
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
class TestExternal(unittest.TestCase):  # pragma: no cover
    '''
    These are tests that open windows and rely on external software
    '''

    def testBasic(self):
        pass


# ------------------------------------------------------------------------------


class Test(unittest.TestCase):

    def testWriteMThdStr(self):
        '''
        Convert bytes of Ascii midi data to binary midi bytes.
        '''
        from binascii import a2b_hex
        mf = MidiFile()
        trk = MidiTrack(0)
        mf.format = 1
        mf.tracks.append(trk)
        mf.ticksPerQuarterNote = 960

        midiBinStr = b''
        midiBinStr = midiBinStr + mf.writeMThdStr()

        self.assertEqual(midiBinStr, b'MThd' + a2b_hex(b'000000060001000103c0'))

    def testBasicImport(self):
        dirLib = common.getSourceFilePath() / 'midi' / 'testPrimitive'
        fp = dirLib / 'test01.mid'
        environLocal.printDebug([fp])
        mf = MidiFile()
        mf.open(fp)
        mf.read()
        mf.close()

        self.assertEqual(len(mf.tracks), 2)
        self.assertEqual(mf.ticksPerQuarterNote, 960)
        self.assertEqual(mf.ticksPerSecond, None)
        # self.assertEqual(mf.writestr(), None)

        # try to write contents
        fileLikeOpen = io.BytesIO()
        mf.openFileLike(fileLikeOpen)
        mf.write()
        mf.close()

        # a simple file created in athenacl
        fp = dirLib / 'test02.mid'
        environLocal.printDebug([fp])
        mf = MidiFile()
        mf.open(fp)
        mf.read()
        mf.close()

        self.assertEqual(len(mf.tracks), 5)
        self.assertEqual(mf.ticksPerQuarterNote, 1024)
        self.assertEqual(mf.ticksPerSecond, None)

        # try to write contents
        fileLikeOpen = io.BytesIO()
        mf.openFileLike(fileLikeOpen)
        mf.write()
        mf.close()

        # random files from the internet
        fp = dirLib / 'test03.mid'

        environLocal.printDebug([fp])
        mf = MidiFile()
        mf.open(fp)
        mf.read()
        mf.close()

        self.assertEqual(len(mf.tracks), 4)
        self.assertEqual(mf.ticksPerQuarterNote, 1024)
        self.assertEqual(mf.ticksPerSecond, None)

        # try to write contents
        fileLikeOpen = io.BytesIO()
        mf.openFileLike(fileLikeOpen)
        mf.write()
        mf.close()

        # random files from the internet
        fp = dirLib / 'test04.mid'
        environLocal.printDebug([fp])
        mf = MidiFile()
        mf.open(fp)
        mf.read()
        mf.close()

        self.assertEqual(len(mf.tracks), 18)
        self.assertEqual(mf.ticksPerQuarterNote, 480)
        self.assertEqual(mf.ticksPerSecond, None)

        # try to write contents
        fileLikeOpen = io.BytesIO()
        mf.openFileLike(fileLikeOpen)
        mf.write()
        mf.close()

#         mf = MidiFile()
#         mf.open(fp)
#         mf.read()
#         mf.close()

    def testInternalDataModel(self):
        dirLib = common.getSourceFilePath() / 'midi' / 'testPrimitive'
        fp = dirLib / 'test01.mid'
        # a simple file created in athenacl
        environLocal.printDebug([fp])
        mf = MidiFile()
        mf.open(fp)
        mf.read()
        mf.close()

        track2 = mf.tracks[1]
        # defines a channel object for each of 16 channels
        # self.assertEqual(len(track2.channels), 16)
        # length seems to be the size of midi data in this track
        self.assertEqual(track2.length, 255)

        # a list of events
        self.assertEqual(len(track2.events), 116)

        i = 0
        while i < len(track2.events) - 1:
            self.assertIsInstance(track2.events[i], DeltaTime)
            self.assertIsInstance(track2.events[i + 1], MidiEvent)

            # environLocal.printDebug(['sample events: ', track2.events[i]])
            # environLocal.printDebug(['sample events: ', track2.events[i + 1]])
            i += 2

        # first object is delta time
        # all objects are pairs of delta time, event

    def testBasicExport(self):
        from music21 import midi
        mt = midi.MidiTrack(1)
        # duration, pitch, velocity
        data = [[1024, 60, 90],
                [1024, 50, 70],
                [1024, 51, 120],
                [1024, 62, 80]]
        t = 0
        tLast = 0
        for d, p, v in data:
            dt = midi.DeltaTime(mt)
            dt.time = t - tLast
            # add to track events
            mt.events.append(dt)

            me = midi.MidiEvent(mt)
            me.type = midi.ChannelVoiceMessages.NOTE_ON
            me.channel = 1
            me.pitch = p
            me.velocity = v
            mt.events.append(me)

            # add note off / velocity zero message
            dt = midi.DeltaTime(mt)
            dt.time = d
            # add to track events
            mt.events.append(dt)

            me = midi.MidiEvent(mt)
            me.type = midi.ChannelVoiceMessages.NOTE_ON
            me.channel = 1
            me.pitch = p
            me.velocity = 0
            mt.events.append(me)

            tLast = t + d  # have delta to note off
            t += d  # next time

        # add end of track
        dt = midi.DeltaTime(mt)
        mt.events.append(dt)

        me = midi.MidiEvent(mt)
        me.type = midi.MetaEvents.END_OF_TRACK
        me.channel = 1
        me.data = b''  # must set data to empty bytes
        mt.events.append(me)

        # for e in mt.events:
        #     print(e)

        mf = midi.MidiFile()
        mf.ticksPerQuarterNote = 1024  # cannot use: 10080
        mf.tracks.append(mt)

        fileLikeOpen = io.BytesIO()
        # mf.open('/src/music21/music21/midi/out.mid', 'wb')
        mf.openFileLike(fileLikeOpen)
        mf.write()
        mf.close()

    def testSetPitchBend(self):
        mt = MidiTrack(1)
        me = MidiEvent(mt)
        me.setPitchBend(0)
        me.setPitchBend(200)  # 200 cents should be max range
        me.setPitchBend(-200)  # 200 cents should be max range

    def testWritePitchBendA(self):
        from music21 import midi
        mt = midi.MidiTrack(1)

        # (0 - 16383). The pitch value affects all playing notes on the current channel.
        # Values below 8192 decrease the pitch, while values above 8192 increase the pitch.
        # The pitch range may vary from instrument to instrument, but is usually +/-2 semi-tones.
        # pbValues = [0, 5, 10, 15, 20, 25, 30, 35, 40, 50]
        pbValues = [0, 25, 0, 50, 0, 100, 0, 150, 0, 200]
        pbValues += [-x for x in pbValues]

        # duration, pitch, velocity
        data = [[1024, 60, 90]] * 20
        t = 0
        tLast = 0
        for i, e in enumerate(data):
            d, p, v = e

            dt = midi.DeltaTime(mt)
            dt.time = t - tLast
            # add to track events
            mt.events.append(dt)

            me = midi.MidiEvent(mt, type=midi.ChannelVoiceMessages.PITCH_BEND, channel=1)
            # environLocal.printDebug(['creating event:', me, 'pbValues[i]', pbValues[i]])
            me.setPitchBend(pbValues[i])  # set values in cents
            mt.events.append(me)

            dt = midi.DeltaTime(mt)
            dt.time = t - tLast
            # add to track events
            mt.events.append(dt)

            me = midi.MidiEvent(mt, type=midi.ChannelVoiceMessages.NOTE_ON, channel=1)
            me.pitch = p
            me.velocity = v
            mt.events.append(me)

            # add note off / velocity zero message
            dt = midi.DeltaTime(mt)
            dt.time = d
            # add to track events
            mt.events.append(dt)

            me = midi.MidiEvent(mt, type=midi.ChannelVoiceMessages.NOTE_ON, channel=1)
            me.pitch = p
            me.velocity = 0
            mt.events.append(me)

            tLast = t + d  # have delta to note off
            t += d  # next time

        # add end of track
        dt = midi.DeltaTime(mt)
        mt.events.append(dt)

        me = midi.MidiEvent(mt)
        me.type = midi.MetaEvents.END_OF_TRACK
        me.channel = 1
        me.data = b''  # must set data to empty bytes
        mt.events.append(me)

        # try setting different channels
        mt.setChannel(3)

        mf = midi.MidiFile()
        mf.ticksPerQuarterNote = 1024  # cannot use: 10080
        mf.tracks.append(mt)

        fileLikeOpen = io.BytesIO()
        # mf.open('/_scratch/test.mid', 'wb')
        mf.openFileLike(fileLikeOpen)
        mf.write()
        mf.close()

    def testImportWithRunningStatus(self):
        from music21 import converter

        dirLib = common.getSourceFilePath() / 'midi' / 'testPrimitive'
        fp = dirLib / 'test09.mid'
        # a simple file created in athenacl
        # dealing with midi files that use running status compression
        s = converter.parse(fp)
        self.assertEqual(len(s.parts), 2)
        self.assertEqual(len(s.parts[0].flat.notes), 748)
        self.assertEqual(len(s.parts[1].flat.notes), 856)

        # for n in s.parts[0].notes:
        #    print(n, n.quarterLength)
        # s.show()

    def testReadPolyphonicKeyPressure(self):
        from music21 import midi

        mt = midi.MidiTrack()
        # Example string from MidiTrack doctest
        mt.read(b'MTrk\x00\x00\x00\x16\x00\xff\x03\x00\x00'
                + b'\xe0\x00@\x00\x90CZ\x88\x00\x80C\x00\x88\x00\xff/\x00')

        pressure = MidiEvent()
        pressure.type = ChannelVoiceMessages.POLYPHONIC_KEY_PRESSURE
        pressure.channel = 1
        pressure.parameter1 = 60
        pressure.parameter2 = 90
        mt.events.insert(len(mt.events) - 2, mt.events[-2])  # copy DeltaTime event
        mt.events.insert(len(mt.events) - 2, pressure)

        writingFile = midi.MidiFile()
        writingFile.tracks = [mt]
        byteStr = writingFile.writestr()
        readingFile = midi.MidiFile()
        readingFile.readstr(byteStr)

        pressureEventRead = [e for e in readingFile.tracks[0].events
                            if e.type == ChannelVoiceMessages.POLYPHONIC_KEY_PRESSURE][0]
        self.assertEqual(pressureEventRead.parameter1, 60)
        self.assertEqual(pressureEventRead.parameter2, 90)


# ------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = []

if __name__ == '__main__':
    import music21
    music21.mainTest(Test)


