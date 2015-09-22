# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         midi/__init__.py
# Purpose:      Access to MIDI library / music21 classes for dealing with midi data
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#               (Will Ware -- see docs)
#
# Copyright:    Copyright © 2011-2013 Michael Scott Cuthbert and the music21 Project
#               Some parts of this module are in the Public Domain, see details.
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
Objects and tools for processing MIDI data.  Converts from MIDI files to
:class:`~music21.midi.MidiEvent`, :class:`~music21.midi.MidiTrack`, and
:class:`~music21.midi.MidiFile` objects, and vice-versa.

Further conversion to-and-from MidiEvent/MidiTrack/MidiFile and music21 Stream,
Note, etc., objects takes place in :ref:`moduleMidiTranslate`.

This module uses routines from Will Ware's public domain midi.py library from 2001
see http://groups.google.com/group/alt.sources/msg/0c5fc523e050c35e
'''
__all__ = ['translate', 'realtime', 'percussion']

import sys
from music21.midi import realtime
from music21.midi import percussion
from music21.ext import six

import unittest
import unicodedata
import os, string
import struct

from music21 import common
from music21 import exceptions21

from music21 import environment
_MOD = "midi.base.py"  
environLocal = environment.Environment(_MOD)


# good midi reference:
# http://www.sonicspot.com/guide/midifiles.html



#-------------------------------------------------------------------------------
class EnumerationException(exceptions21.Music21Exception): 
    pass 

class MidiException(exceptions21.Music21Exception): 
    pass 




#-------------------------------------------------------------------------------
# def showstr(str, n=16): 
#     for x in str[:n]: 
#         print (('%02x' % ord(x)),) 
#     print("")

def charToBinary(char):
    '''
    Convert a char into its binary representation. Useful for debugging. 
    
    >>> midi.charToBinary('a')
    '01100001'
    '''
    asciiValue = ord(char)
    binaryDigits = []
    while (asciiValue > 0):
        if (asciiValue & 1) == 1:
            binaryDigits.append("1")
        else:
            binaryDigits.append("0")
        asciiValue = asciiValue >> 1
    
    binaryDigits.reverse()
    binary = ''.join(binaryDigits)
    zerofix = (8 - len(binary)) * '0'
    return zerofix + binary


def intsToHexString(intList):
    '''
    Convert a list of integers into a hex string, suitable for testing MIDI encoding.
    
    
    >>> # note on, middle c, 120 velocity
    >>> midi.intsToHexString([144, 60, 120])
    b'\\x90<x'
    '''
    # note off are 128 to 143
    # note on messages are decimal 144 to 159
    post = b''
    for i in intList:
        # B is an unsigned char
        # this forces values between 0 and 255
        # the same as chr(int)
        post += struct.pack(">B", i)
    return post
    

def getNumber(midiStr, length): 
    '''
    Return the value of a string byte or bytes if length > 1
    from an 8-bit string or (PY3) bytes object
    
    Then, return the remaining string or bytes object

    The `length` is the number of chars to read. 
    This will sum a length greater than 1 if desired.

    Note that MIDI uses big-endian for everything.
    This is the inverse of Python's chr() function.
    
    >>> midi.getNumber('test', 0)
    (0, 'test')
    >>> midi.getNumber('test', 2)
    (29797, 'st')
    >>> midi.getNumber('test', 4)
    (1952805748, '')
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
        summation = midNum - (( midNum >> (8*length)) << (8*length))
        bigBytes = midNum - summation
        return summation, bigBytes

def getVariableLengthNumber(midiStr): 
    r'''
    Given a string of data, strip off a the first character, or all high-byte characters 
    terminating with one whose ord() function is < 0x80.  Thus a variable number of bytes
    might be read.
    
    After finding the appropriate termination, 
    return the remaining string.

    This is necessary as DeltaTime times are given with variable size, 
    and thus may be if different numbers of characters are used.

    (The ellipses below are just to make the doctests work on both Python 2 and
    Python 3 (where the output is in bytes).)
    
    >>> midi.getVariableLengthNumber('A-u')
    (65, ...'-u')
    >>> midi.getVariableLengthNumber('-u')
    (45, ...'u')
    >>> midi.getVariableLengthNumber('u')
    (117, ...'')

    >>> midi.getVariableLengthNumber('test')
    (116, ...'est')
    >>> midi.getVariableLengthNumber('E@-E')
    (69, ...'@-E')
    >>> midi.getVariableLengthNumber('@-E')
    (64, ...'-E')
    >>> midi.getVariableLengthNumber('-E')
    (45, ...'E')
    >>> midi.getVariableLengthNumber('E')
    (69, ...'')

    Test that variable length characters work:

    >>> midi.getVariableLengthNumber(b'\xff\x7f')
    (16383, ...'')
    >>> midi.getVariableLengthNumber('中xy')
    (210638584, ...'y')

    If no low-byte character is encoded, raises an IndexError

    >>> midi.getVariableLengthNumber('中国')
    Traceback (most recent call last):
    IndexError: ...index out of range
    '''
    # from http://faydoc.tripod.com/formats/mid.htm
    # This allows the number to be read one byte at a time, and when you see a msb of 0, you know that it was the last (least significant) byte of the number.
    summation = 0 
    i = 0 
    if six.PY3 and isinstance(midiStr, str):
        midiStr = midiStr.encode('utf-8')
    
    while i < 999: # should return eventually... was while True
        if common.isNum(midiStr[i]):
            x = midiStr[i]
        else:
            x = ord(midiStr[i]) 
        #environLocal.printDebug(['getVariableLengthNumber: examined char:', charToBinary(midiStr[i])])
        summation = (summation << 7) + (x & 0x7F) 
        i += 1 
        if not (x & 0x80): 
            #environLocal.printDebug(['getVariableLengthNumber: depth read into string: %s' % i])
            return summation, midiStr[i:] 
    raise MidiException('did not find the end of the number!')

def getNumbersAsList(midiStr):
    '''
    Translate each char into a number, return in a list. 
    Used for reading data messages where each byte encodes 
    a different discrete value. 

    
    >>> midi.getNumbersAsList('\\x00\\x00\\x00\\x03')
    [0, 0, 0, 3]
    '''
    post = []
    for i in range(len(midiStr)):
        if common.isNum(midiStr[i]):
            post.append(midiStr[i])
        else:
            post.append(ord(midiStr[i]))
    return post

def putNumber(num, length): 
    '''
    Put a single number as a hex number at the end of a string `length` bytes long.
    
    >>> midi.putNumber(3, 4)
    b'\\x00\\x00\\x00\\x03'
    >>> midi.putNumber(0, 1)
    b'\\x00'
    '''
    if six.PY2:
        lst = [] 
    else:
        lst = bytearray()
    
    for i in range(length): 
        n = 8 * (length - 1 - i) 
        thisNum = (num >> n) & 0xFF
        if six.PY2:
            lst.append(chr(thisNum)) 
        else:
            lst.append(thisNum)
    
    if six.PY2:
        return string.join(lst, "") # @UndefinedVariable
    else:
        return bytes(lst)

def putVariableLengthNumber(x): 
    '''
    >>> midi.putVariableLengthNumber(4)
    b'\\x04'
    >>> midi.putVariableLengthNumber(127)
    b'\\x7f'
    >>> midi.putVariableLengthNumber(0)
    b'\\x00'
    >>> midi.putVariableLengthNumber(1024)
    b'\\x88\\x00'
    >>> midi.putVariableLengthNumber(8192)
    b'\\xc0\\x00'
    >>> midi.putVariableLengthNumber(16383)
    b'\\xff\\x7f'

    >>> midi.putVariableLengthNumber(-1)
    Traceback (most recent call last):
    MidiException: cannot putVariableLengthNumber() when number is negative: -1
    '''
    #environLocal.printDebug(['calling putVariableLengthNumber(x) with', x])
    # note: negative numbers will cause an infinite loop here
    if x < 0:
        raise MidiException('cannot putVariableLengthNumber() when number is negative: %s' % x)
    if six.PY2:
        lst = [] 
    else:
        lst = bytearray()
    while True: 
        y, x = x & 0x7F, x >> 7 
        if six.PY2:
            lst.append(chr(y + 0x80)) 
        else:
            lst.append(y + 0x80)
        if x == 0: 
            break 
    lst.reverse() 
    if six.PY2:
        lst[-1] = chr(ord(lst[-1]) & 0x7f) 
        return string.join(lst, "")  # @UndefinedVariable
    else:
        lst[-1] = lst[-1] & 0x7f 
        return bytes(lst)

def putNumbersAsList(numList):
    '''
    Translate a list of numbers (0-255) into a character byte strings. 
    Used for encoding data messages where each byte encodes a different discrete value. 

    
    >>> midi.putNumbersAsList([0, 0, 0, 3])
    '\\x00\\x00\\x00\\x03'

    If a number is < 0 but >= -256 then it wraps around from the top.

    >>> midi.putNumbersAsList([0, 0, 0, -3])
    '\\x00\\x00\\x00\\xfd'
    >>> midi.putNumbersAsList([0, 0, 0, -1])
    '\\x00\\x00\\x00\\xff'
    '''
    post = []
    for n in numList:
        # assume if a number exceeds range count down from top?
        if n < 0:
            n = 256 + n # -1 will be 255
        post.append(chr(n))
    return ''.join(post)

#-------------------------------------------------------------------------------
class Enumeration(object): 
    '''
    Utility object for defining binary MIDI message constants. 
    '''
    def __init__(self, enumList = None): 
        if enumList is None:
            enumList = []
        lookup = { } 
        reverseLookup = {} 
        i = 0 
        uniqueNames = [ ] 
        uniqueValues = [ ] 
        for x in enumList: 
            if isinstance(x, tuple): 
                x, i = x 
            if not isinstance(x, str): 
                raise EnumerationException("enum name is not a string: " + x)
            if not isinstance(i, int): 
                raise EnumerationException("enum value is not an integer: " + i)
            if x in uniqueNames: 
                raise EnumerationException("enum name is not unique: " + x)
            if i in uniqueValues: 
                raise EnumerationException("enum value is not unique for " + x)
            uniqueNames.append(x) 
            uniqueValues.append(i) 
            lookup[x] = i 
            reverseLookup[i] = x 
            i = i + 1 
        self.lookup = lookup 
        self.reverseLookup = reverseLookup 

    def __add__(self, other): 
        lst = [ ] 
        for k in self.lookup: 
            lst.append((k, self.lookup[k])) 
        for k in other.lookup: 
            lst.append((k, other.lookup[k])) 
        return Enumeration(lst) 

    def hasattr(self, attr): 
        if attr in self.lookup:
            return True
        return False
        #return attr in self.lookup

    def hasValue(self, attr): 
        if attr in self.reverseLookup:
            return True
        return False
        #return attr in self.reverseLookup

    def __getattr__(self, attr): 
        if attr not in self.lookup: 
            raise AttributeError 
        return self.lookup[attr] 

    def whatis(self, value): 
        post = self.reverseLookup[value] 
        #environLocal.printDebug(['whatis() call: post', post])
        return post

channelVoiceMessages = Enumeration([("NOTE_OFF", 0x80), 
                                    ("NOTE_ON", 0x90), 
                                    ("POLYPHONIC_KEY_PRESSURE", 0xA0), 
                                    ("CONTROLLER_CHANGE", 0xB0), 
                                    ("PROGRAM_CHANGE", 0xC0), 
                                    ("CHANNEL_KEY_PRESSURE", 0xD0), 
                                    ("PITCH_BEND", 0xE0)]) 

channelModeMessages = Enumeration([("ALL_SOUND_OFF", 0x78), 
                                   ("RESET_ALL_CONTROLLERS", 0x79), 
                                   ("LOCAL_CONTROL", 0x7A), 
                                   ("ALL_NOTES_OFF", 0x7B), 
                                   ("OMNI_MODE_OFF", 0x7C), 
                                   ("OMNI_MODE_ON", 0x7D), 
                                   ("MONO_MODE_ON", 0x7E), 
                                   ("POLY_MODE_ON", 0x7F)]) 

metaEvents = Enumeration([("SEQUENCE_NUMBER", 0x00), 
                          ("TEXT_EVENT", 0x01), 
                          ("COPYRIGHT_NOTICE", 0x02), 
                          ("SEQUENCE_TRACK_NAME", 0x03), 
                          ("INSTRUMENT_NAME", 0x04), 
                          ("LYRIC", 0x05), 
                          ("MARKER", 0x06), 
                          ("CUE_POINT", 0x07), 
                          ("PROGRAM_NAME", 0x08), #optional event is used to embed the patch/program name that is called up by the immediately subsequent Bank Select and Program Change messages. It serves to aid the end user in making an intelligent program choice when using different hardware.
                          ("SOUND_SET_UNSUPPORTED", 0x09),
                          ("MIDI_CHANNEL_PREFIX", 0x20), 
                          ("MIDI_PORT", 0x21), 
                          ("END_OF_TRACK", 0x2F), 
                          ("SET_TEMPO", 0x51), 
                          ("SMTPE_OFFSET", 0x54), 
                          ("TIME_SIGNATURE", 0x58), 
                          ("KEY_SIGNATURE", 0x59), 
                          ("SEQUENCER_SPECIFIC_META_EVENT", 0x7F)]) 

#-------------------------------------------------------------------------------
class MidiEvent(object): 
    '''
    A model of a MIDI event, including note-on, note-off, program change, 
    controller change, any many others.

    MidiEvent objects are paired (preceded) by :class:`~music21.midi.base.DeltaTime` 
    objects in the list of events in a MidiTrack object.

    The `track` argument must be a :class:`~music21.midi.base.MidiTrack` object.

    The `type` attribute is a string representation of a Midi event from the channelVoiceMessages 
    or metaEvents definitions. 

    The `channel` attribute is an integer channel id, from 1 to 16. 

    The `time` attribute is an integer duration of the event in ticks. This value 
    can be zero. This value is not essential, as ultimate time positioning is 
    determined by :class:`~music21.midi.base.DeltaTime` objects. 

    The `pitch` attribute is only defined for note-on and note-off messages. 
    The attribute stores an integer representation (0-127, with 60 = middle C).

    The `velocity` attribute is only defined for note-on and note-off messages. 
    The attribute stores an integer representation (0-127).  A note-on message with
    velocity 0 is generally assumed to be the same as a note-off message.

    The `data` attribute is used for storing other messages, 
    such as SEQUENCE_TRACK_NAME string values. 

    
    >>> mt = midi.MidiTrack(1)
    >>> me1 = midi.MidiEvent(mt)
    >>> me1.type = "NOTE_ON"
    >>> me1.channel = 3
    >>> me1.time = 200
    >>> me1.pitch = 60
    >>> me1.velocity = 120
    >>> me1
    <MidiEvent NOTE_ON, t=200, track=1, channel=3, pitch=60, velocity=120>

    >>> me2 = midi.MidiEvent(mt)
    >>> me2.type = "SEQUENCE_TRACK_NAME"
    >>> me2.time = 0
    >>> me2.data = 'guitar'
    >>> me2
    <MidiEvent SEQUENCE_TRACK_NAME, t=0, track=1, channel=None, data='guitar'>
    '''
    
    def __init__(self, track, type=None, time=None, channel=None): #@ReservedAssignment
        self.track = track  # a MidiTrack object
        self.type = type
        self.time = time
        self.channel = channel

        self._parameter1 = None # pitch or first data value
        self._parameter2 = None # velocity or second data value

        # data is a property...

        # if this is a Note on/off, need to store original
        # pitch space value in order to determine if this is has a microtone
        self.centShift = None
    
        # store a reference to a corresponding event
        # if a noteOn, store the note off, and vice versa
        self.correspondingEvent = None

        # store and pass on a running status if found
        self.lastStatusByte = None

        # need to store a sort order based on type
        self.sortOrder = 0
        self.updateSortOrder()
    

    def updateSortOrder(self):
        # update based on type; type may be set after init
        if self.type == 'PITCH_BEND': #go before note events
            self.sortOrder = -10
        if self.type == 'NOTE_OFF': # should come before pitch bend
            self.sortOrder = -20
    
    def __repr__(self): 
        if self.track == None:
            trackIndex = None
        else:
            trackIndex = self.track.index

        r = ("<MidiEvent %s, t=%s, track=%s, channel=%s" % 
             (self.type, repr(self.time), trackIndex, 
              repr(self.channel))) 
        if self.type in ['NOTE_ON', 'NOTE_OFF']:
            attrList = ["pitch", "velocity"]
        else:
            if self._parameter2 is None:
                attrList = ['data']
            else:
                attrList = ['_parameter1', '_parameter2']

        for attrib in attrList: 
            if getattr(self, attrib) is not None: 
                r = r + ", " + attrib + "=" + repr(getattr(self, attrib)) 
        return r + ">" 
    
    # provide parameter access to pitch and velocity
    def _setPitch(self, value):
        self._parameter1 = value

    def _getPitch(self):
        # only return pitch if this is note on /off
        if self.type in ['NOTE_ON', 'NOTE_OFF']:
            return self._parameter1
        else:
            return None

    pitch = property(_getPitch, _setPitch)

    def _setVelocity(self, value):
        self._parameter2 = value

    def _getVelocity(self):
        return self._parameter2

    velocity = property(_getVelocity, _setVelocity)


    # store generic data in parameter 1
    def _setData(self, value):
        self._parameter1 = value

    def _getData(self):
        return self._parameter1

    data = property(_getData, _setData)


    def setPitchBend(self, cents, bendRange=2):
        '''Treat this event as a pitch bend value, and set the ._parameter1 and ._parameter2 fields appropriately given a specified bend value in cents.
    
        The `bendRange` parameter gives the number of half steps in the bend range.

        
        >>> mt = midi.MidiTrack(1)
        >>> me1 = midi.MidiEvent(mt)
        >>> me1.setPitchBend(50)
        >>> me1._parameter1, me1._parameter2
        (0, 80)
        >>> me1.setPitchBend(100)
        >>> me1._parameter1, me1._parameter2
        (0, 96)
        >>> me1.setPitchBend(200)
        >>> me1._parameter1, me1._parameter2
        (127, 127)
        >>> me1.setPitchBend(-50)
        >>> me1._parameter1, me1._parameter2
        (0, 48)
        >>> me1.setPitchBend(-100)
        >>> me1._parameter1, me1._parameter2
        (0, 32)
        '''
        # value range is 0, 16383
        # center should be 8192
        centRange = bendRange * 100
        center = 8192
        topSpan = 16383 - center
        bottomSpan = center

        if cents > 0:
            shiftScalar = cents / float(centRange)
            shift = int(round(shiftScalar * topSpan))
        elif cents < 0:
            shiftScalar = cents / float(centRange) # will be negative
            shift = int(round(shiftScalar * bottomSpan)) # will be negative
        else: # cents is zero
            shift = 0
        target = center + shift

        # produce a two-char value
        charValue = putVariableLengthNumber(target)
        d1, junk = getNumber(charValue[0], 1)
        # need to convert from 8 bit to 7, so using & 0x7F
        d1 = d1 & 0x7F
        if len(charValue) > 1:
            d2, junk = getNumber(charValue[1], 1)
            d2 = d2 & 0x7F
        else:
            d2 = 0

        #environLocal.printDebug(['got target char value', charValue, 'getVariableLengthNumber(charValue)', getVariableLengthNumber(charValue)[0], 'd1', d1, 'd2', d2,])

        self._parameter1 = d2
        self._parameter2 = d1 # d1 is msb here
        
    def _parseChannelVoiceMessage(self, midiStr):
        '''
        
        >>> mt = midi.MidiTrack(1)
        >>> me1 = midi.MidiEvent(mt)
        >>> remainder = me1._parseChannelVoiceMessage(midi.intsToHexString([144, 60, 120]))
        >>> me1.channel
        1
        >>> remainder = me1._parseChannelVoiceMessage(midi.intsToHexString([145, 60, 120]))
        >>> me1.channel
        2
        >>> me1.type
        'NOTE_ON'
        >>> me1.pitch
        60
        >>> me1.velocity
        120
        '''
        # x, y, and z define characteristics of the first two chars
        # for x: The left nybble (4 bits) contains the actual command, and the right nibble contains the midi channel number on which the command will be executed.
        if common.isNum(midiStr[0]):
            x = midiStr[0]
        else:
            x = ord(midiStr[0])  # given a string representation, get decimal number
        y = x & 0xF0  # bitwise and to derive channel number
        if common.isNum(midiStr[1]):
            z = midiStr[1]
        else:
            z = ord(midiStr[1])  # given a string representation, get decimal number
        if common.isNum(midiStr[2]):
            thirdByte = midiStr[2]
        else:
            thirdByte = ord(midiStr[2])  # given a string representation, get decimal number

        self.channel = (x & 0x0F) + 1  # this is same as y + 1
        self.type = channelVoiceMessages.whatis(y) 
        #environLocal.printDebug(['MidiEvent.read()', self.type])
        if (self.type == "PROGRAM_CHANGE" or 
            self.type == "CHANNEL_KEY_PRESSURE"): 
            self.data = z 
            return midiStr[2:] 
        elif (self.type == "CONTROLLER_CHANGE"):
            # for now, do nothing with this data
            # for a note, str[2] is velocity; here, it is the control value
            self.pitch = z # this is the controller id
            self.velocity = thirdByte # this is the controller value
            return midiStr[3:] 
        else: 
            self.pitch = z # the second byte
            # read the third chart toi get velocity 
            self.velocity = thirdByte
            # each MidiChannel object is accessed here
            # using that channel, data for each event is added or 
            # removed 
            return midiStr[3:] 

    def read(self, time, midiStr): 
        '''
        Parse the string that is given and take the beginning
        section and convert it into data for this event and return the
        now truncated string.

        The `time` value is the number of ticks into the Track 
        at which this event happens. This is derived from reading 
        data the level of the track.

        TODO: These instructions are inadequate.

        >>> # all note-on messages (144-159) can be found
        >>> 145 & 0xF0 # testing message type extraction
        144
        >>> 146 & 0xF0 # testing message type extraction
        144
        >>> (144 & 0x0F) + 1 # getting the channel
        1
        >>> (159 & 0x0F) + 1 # getting the channel
        16
        '''
        if len(midiStr) < 2:
            # often what we have here are null events:
            # the string is simply: 0x00
            environLocal.printDebug(['MidiEvent.read(): got bad data string', 'time', time, 'str', repr(midiStr)])
            return ''

        # x, y, and z define characteristics of the first two chars
        # for x: The left nybble (4 bits) contains the actual command, and the right nibble contains the midi channel number on which the command will be executed.
        if common.isNum(midiStr[0]):
            x = midiStr[0]
        else:
            x = ord(midiStr[0])  # given a string representation, get decimal number

        # detect running status: if the status byte is less than 128, its 
        # not a status byte, but a data byte
        if x < 128:
            # environLocal.printDebug(['MidiEvent.read(): found running status even data', 'self.lastStatusByte:', self.lastStatusByte])

            if self.lastStatusByte is not None:
                rsb = self.lastStatusByte
                if common.isNum(rsb):
                    rsb = bytes([rsb])
            else: # provide a default
                if six.PY3:
                    rsb = bytes([0x90])
                else:
                    rsb = chr(0x90)
            #post = self._parseChannelVoiceMessage(str, runningStatusByte=rsb)
            #return post
            # add the running status byte to the front of the string 
            # and process as before
            midiStr = rsb + midiStr
            if common.isNum(midiStr[0]):
                x = midiStr[0]
            else:
                x = ord(midiStr[0]) # given a string representation, get decimal number
        else:
            # store last status byte
            self.lastStatusByte = midiStr[0]

        y = x & 0xF0  # bitwise and to derive message type

        if common.isNum(midiStr[1]):
            z = midiStr[1]
        else:
            z = ord(midiStr[1])  # given a string representation, get decimal number

        #environLocal.printDebug(['MidiEvent.read(): trying to parse a MIDI event, looking at first two chars:', 'repr(x)', repr(x), 'charToBinary(str[0])', charToBinary(str[0]), 'charToBinary(str[1])', charToBinary(str[1])])

        if channelVoiceMessages.hasValue(y): 
            return self._parseChannelVoiceMessage(midiStr)

        elif y == 0xB0 and channelModeMessages.hasValue(z): 
            self.channel = (x & 0x0F) + 1 
            self.type = channelModeMessages.whatis(z) 
            if self.type == "LOCAL_CONTROL": 
                self.data = (ord(midiStr[2]) == 0x7F) 
            elif self.type == "MONO_MODE_ON": 
                self.data = ord(midiStr[2]) 
            else:
                environLocal.printDebug(['unhandled message:', midiStr[2]])
            return midiStr[3:]

        elif x == 0xF0 or x == 0xF7: 
            self.type = {0xF0: "F0_SYSEX_EVENT", 
                         0xF7: "F7_SYSEX_EVENT"}[x] 
            length, midiStr = getVariableLengthNumber(midiStr[1:]) 
            self.data = midiStr[:length] 
            return midiStr[length:]

        # SEQUENCE_TRACK_NAME and other MetaEvents are here
        elif x == 0xFF: 
            #environLocal.printDebug(['MidiEvent.read(): got a variable length meta event', charToBinary(str[0])])
            if not metaEvents.hasValue(z): 
                environLocal.printDebug(["unknown meta event: FF %02X" % z])
                sys.stdout.flush() 
                raise MidiException("Unknown midi event type: %r, %r" % (x, z))
            self.type = metaEvents.whatis(z) 
            length, midiStr = getVariableLengthNumber(midiStr[2:]) 
            self.data = midiStr[:length] 
            # return remainder
            return midiStr[length:] 
        else:
            # an uncaught message
            environLocal.printDebug(['got unknown midi event type', repr(x), 'charToBinary(midiStr[0])', charToBinary(midiStr[0]), 'charToBinary(midiStr[1])', charToBinary(midiStr[1])])
            raise MidiException("Unknown midi event type")


    def getBytes(self): 
        '''
        Return a set of bytes for this MIDI event.
        '''
        sysex_event_dict = {"F0_SYSEX_EVENT": 0xF0, 
                            "F7_SYSEX_EVENT": 0xF7} 
        if channelVoiceMessages.hasattr(self.type): 
            #environLocal.printDebug(['writing channelVoiceMessages', self.type])
            x = chr((self.channel - 1) + 
                    getattr(channelVoiceMessages, self.type)) 
            # for writing note-on/note-off
            if self.type not in ['PROGRAM_CHANGE', 
                'CHANNEL_KEY_PRESSURE']:
                # this results in a two-part string, like '\x00\x00'
                try:
                    data = chr(self._parameter1) + chr(self._parameter2) 
                except ValueError:
                    raise MidiException("Problem with representing either %d or %d" % (self._parameter1, self._parameter2))
            elif self.type in ['PROGRAM_CHANGE']:
                #environLocal.printDebug(['trying to add program change data: %s' % self.data])
                try:
                    data = chr(self.data) 
                except TypeError:
                    raise MidiException("Got incorrect data for %s in .data: %s, cannot parse Program Change" % (self, self.data))
            else:  # all other messages
                try:
                    data = chr(self.data) 
                except TypeError:
                    raise MidiException("Got incorrect data for %s in .data: %s, cannot parse Miscellaneous Message" % (self, self.data))
            return x + data 

        elif channelModeMessages.hasattr(self.type): 
            x = getattr(channelModeMessages, self.type) 
            x = (chr(0xB0 + (self.channel - 1)) + 
                 chr(x) + 
                 chr(self.data)) 
            return x 

        elif self.type in sysex_event_dict: 
            if six.PY2:
                s = chr(sysex_event_dict[self.type]) 
            else:
                s = bytes([sysex_event_dict[self.type]])
            s = s + putVariableLengthNumber(len(self.data)) 
            return s + self.data 

        elif metaEvents.hasattr(self.type):                 
            if six.PY2:
                s = chr(0xFF) + chr(getattr(metaEvents, self.type))
            else:
                s = bytes([0xFF]) + bytes([getattr(metaEvents, self.type)])
            s = s + putVariableLengthNumber(len(self.data)) 

            try: # TODO: need to handle unicode
                return s + self.data 
            except (UnicodeDecodeError, TypeError):
                #environLocal.printDebug(['cannot decode data', self.data])
                return s + unicodedata.normalize('NFKD', 
                           self.data).encode('ascii','ignore')
        else: 
            raise MidiException("unknown midi event type: %s" % self.type)

    #---------------------------------------------------------------------------
    def isNoteOn(self):
        '''
        Return a boolean if this is a note-on message and velocity is not zero.
        
        >>> mt = midi.MidiTrack(1)
        >>> me1 = midi.MidiEvent(mt)
        >>> me1.type = "NOTE_ON"
        >>> me1.velocity = 120
        >>> me1.isNoteOn()
        True
        >>> me1.isNoteOff()
        False
        '''
        if self.type == "NOTE_ON" and self.velocity != 0:
            return True
        return False

    def isNoteOff(self):
        '''
        Return a boolean if this is should be interpreted as a note-off message, 
        either as a real note-off or as a note-on with zero velocity.

        
        >>> mt = midi.MidiTrack(1)
        >>> me1 = midi.MidiEvent(mt)
        >>> me1.type = "NOTE_OFF"
        >>> me1.isNoteOn()
        False
        >>> me1.isNoteOff()
        True

        >>> me2 = midi.MidiEvent(mt)
        >>> me2.type = "NOTE_ON"
        >>> me2.velocity = 0
        >>> me2.isNoteOn()
        False
        >>> me2.isNoteOff()
        True
        '''
        if self.type == "NOTE_OFF":
            return True
        elif self.type == "NOTE_ON" and self.velocity == 0:
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
        if self.type == "DeltaTime":
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
        >>> me1.type = "NOTE_ON"
        >>> me1.velocity = 120
        >>> me1.pitch = 60

        >>> me2 = midi.MidiEvent(mt)
        >>> me2.type = "NOTE_ON"
        >>> me2.velocity = 0
        >>> me2.pitch = 60

        >>> me1.matchedNoteOff(me2)
        True

        >>> me2.pitch = 61
        >>> me1.matchedNoteOff(me2)
        False

        >>> me2.type = "NOTE_OFF"
        >>> me1.matchedNoteOff(me2)
        False

        >>> me2.pitch = 60
        >>> me1.matchedNoteOff(me2)
        True
        
        >>> me2.channel = 12
        >>> me1.matchedNoteOff(me2)
        False

        '''
        if other.isNoteOff:
            # might check velocity here too?
            if self.pitch == other.pitch and self.channel == other.channel:
                return True
        return False



class DeltaTime(MidiEvent): 
    '''
    A :class:`~music21.midi.base.MidiEvent` subclass that stores the 
    time change (in ticks) since the start or since the last MidiEvent.

    Pairs of DeltaTime and MidiEvent objects are the basic presentation of temporal data.

    The `track` argument must be a :class:`~music21.midi.base.MidiTrack` object.

    Time values are in integers, representing ticks. 

    The `channel` attribute, inherited from MidiEvent is not used and set to None
    unless overridden (don't!).

    
    >>> mt = midi.MidiTrack(1)
    >>> dt = midi.DeltaTime(mt)
    >>> dt.time = 380
    >>> dt
    <MidiEvent DeltaTime, t=380, track=1, channel=None>

    '''
    def __init__(self, track, time=None, channel=None):
        MidiEvent.__init__(self, track, time=time, channel=channel)
        self.type = "DeltaTime" 

    def read(self, oldstr): 
        self.time, newstr = getVariableLengthNumber(oldstr) 
        return self.time, newstr 

    def getBytes(self): 
        midiStr = putVariableLengthNumber(self.time) 
        return midiStr



class MidiTrack(object): 
    '''
    A MIDI Track. Each track contains a list of 
    :class:`~music21.midi.base.MidiChannel` objects, one for each channel.

    All events are stored in the `events` list, in order.

    An `index` is an integer identifier for this object.


    TODO: Better Docs

    
    >>> mt = midi.MidiTrack(0)
    
    '''
    def __init__(self, index): 
        self.index = index 
        self.events = [] 
        self.length = 0 #the data length; only used on read()

        # no longer need channel objects
        # an object for each of 16 channels is created
#         self.channels = [] 
#         for i in range(16): 
#             self.channels.append(MidiChannel(self, i+1)) 

    def read(self, midiStr): 
        '''
        Read as much of the string (representing midi data) as necessary; 
        return the remaining string for reassignment and further processing.

        The string should begin with `MTrk`, specifying a Midi Track

        Creates and stores :class:`~music21.midi.base.DeltaTime` 
        and :class:`~music21.midi.base.MidiEvent` objects. 
        '''
        time = 0 # a running counter of ticks

        if not midiStr[:4] == b"MTrk":
            raise MidiException('badly formed midi string: missing leading MTrk')
        # get the 4 chars after the MTrk encoding
        length, midiStr = getNumber(midiStr[4:], 4)      
        #environLocal.printDebug(['MidiTrack.read(): got chunk size', length])   
        self.length = length 

        # all event data is in the track str
        trackStr = midiStr[:length] 
        remainder = midiStr[length:] 

        ePrevious = None
        while trackStr: 
            # shave off the time stamp from the event
            delta_t = DeltaTime(self) 
            # return extracted time, as well as remaining string
            dt, trackStrCandidate = delta_t.read(trackStr) 
            # this is the offset that this event happens at, in ticks
            timeCandidate = time + dt 
    
            # pass self to event, set this MidiTrack as the track for this event
            e = MidiEvent(self) 
            if ePrevious is not None: # set the last status byte
                e.lastStatusByte = ePrevious.lastStatusByte
            # some midi events may raise errors; simply skip for now
            try:
                trackStrCandidate = e.read(timeCandidate, trackStrCandidate) 
            except MidiException:
                # assume that trackStr, after delta extraction, is still correct
                #environLocal.printDebug(['forced to skip event; delta_t:', delta_t])
                # set to result after taking delta time
                trackStr = trackStrCandidate
                continue
            # only set after trying to read, which may raise exception
            time = timeCandidate
            trackStr = trackStrCandidate # remainder string
            # only append if we get this far
            self.events.append(delta_t) 
            self.events.append(e) 
            ePrevious = e

        return remainder # remainder string after extracting track data
    
    def getBytes(self): 
        '''
        returns a string of midi-data from the `.events` in the object.
        '''
        
        # set time to the first event
        # time = self.events[0].time 
        # build str using MidiEvents 
        midiStr = b""
        for e in self.events: 
            # this writes both delta time and message events
            try:
                ew = e.getBytes()
                if six.PY3:
                    intArray = []
                    for x in ew:
                        if common.isNum(x):
                            intArray.append(x)
                        else:
                            intArray.append(ord(x))
                    ew = bytes(bytearray(intArray)) 
                midiStr = midiStr + ew
            except MidiException as me:
                environLocal.warn("Conversion error for %s: %s; ignored." % (e, me))
        return b"MTrk" + putNumber(len(midiStr), 4) + midiStr
    
    def __repr__(self): 
        r = "<MidiTrack %d -- %d events\n" % (self.index, len(self.events)) 
        for e in self.events: 
            r = r + "    " + e.__repr__() + "\n" 
        return r + "  >" 

    #---------------------------------------------------------------------------
    def updateEvents(self):
        '''
        We may attach events to this track before setting their `track` parameter. 
        This method will move through all events and set their track to this track. 
        '''
        for e in self.events:
            e.track = self

    def hasNotes(self):
        '''Return True/False if this track has any note-on/note-off pairs defined. 
        '''
        for e in self.events:
            if e.isNoteOn(): 
                return True
        return False

    def setChannel(self, value):
        '''Set the channel of all events in this Track.
        '''
        if value not in range(1,17): # count from 1
            raise MidiException('bad channel value: %s' % value)
        for e in self.events:
            e.channel = value

    def getChannels(self):
        '''Get all channels used in this Track.
        '''
        post = []
        for e in self.events:
            if e.channel not in post:
                post.append(e.channel)
        return post            

    def getProgramChanges(self):
        '''Get all unique program changes used in this Track, sorted.
        '''
        post = []
        for e in self.events:
            if e.type == 'PROGRAM_CHANGE':
                if e.data not in post:
                    post.append(e.data)
        return post            


class MidiFile(object):
    '''
    Low-level MIDI file writing, emulating methods from normal Python files. 

    The `ticksPerQuarterNote` attribute must be set before writing. 1024 is a common value.

    This object is returned by some properties for directly writing files of midi representations.
    '''
    
    def __init__(self): 
        self.file = None 
        self.format = 1 
        self.tracks = [] 
        self.ticksPerQuarterNote = 1024 
        self.ticksPerSecond = None 
    
    def open(self, filename, attrib="rb"): 
        '''
        Open a MIDI file path for reading or writing.
    
        For writing to a MIDI file, `attrib` should be "wb".
        '''
        if attrib not in ['rb', 'wb']:
            raise MidiException('cannot read or write unless in binary mode, not:', attrib)
        self.file = open(filename, attrib) 

    def openFileLike(self, fileLike):
        '''Assign a file-like object, such as those provided by StringIO, as an open file object.

        >>> from music21.ext.six import StringIO        
        >>> fileLikeOpen = StringIO()
        >>> mf = midi.MidiFile()
        >>> mf.openFileLike(fileLikeOpen)
        >>> mf.close()
        '''
        self.file = fileLike
    
    def __repr__(self): 
        r = "<MidiFile %d tracks\n" % len(self.tracks) 
        for t in self.tracks: 
            r = r + "  " + t.__repr__() + "\n" 
        return r + ">" 
    
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
    
    def readstr(self, midiStr): 
        '''
        Read and parse MIDI data as a string, putting the
        data in `.ticksPerQuarterNote` and a list of
        `MidiTrack` objects in the attribute `.tracks`. 
        '''
        if not midiStr[:4] == b"MThd":
            raise MidiException('badly formated midi string, got: %s' % midiStr[:20])

        # we step through the str src, chopping off characters as we go
        # and reassigning to str
        length, midiStr = getNumber(midiStr[4:], 4) 
        if not length == 6:
            raise MidiException('badly formated midi string')

        midiFormatType, midiStr = getNumber(midiStr, 2) 
        self.format = midiFormatType
        if not midiFormatType in [0, 1]:
            raise MidiException('cannot handle midi file format: %s' % format)

        numTracks, midiStr = getNumber(midiStr, 2) 
        division, midiStr = getNumber(midiStr, 2) 

        # very few midi files seem to define ticksPerSecond
        if division & 0x8000: 
            framesPerSecond = -((division >> 8) | -128) 
            ticksPerFrame = division & 0xFF 
            if not ticksPerFrame in [24, 25, 29, 30]:
                raise MidiException('cannot handle ticks per frame: %s' % ticksPerFrame)
            if ticksPerFrame == 29: 
                ticksPerFrame = 30  # drop frame 
            self.ticksPerSecond = ticksPerFrame * framesPerSecond 
        else: 
            self.ticksPerQuarterNote = division & 0x7FFF 

        #environLocal.printDebug(['MidiFile.readstr(): got midi file format:', self.format, 'with specified number of tracks:', numTracks, 'ticksPerSecond:', self.ticksPerSecond, 'ticksPerQuarterNote:', self.ticksPerQuarterNote])

        for i in range(numTracks): 
            trk = MidiTrack(i) # sets the MidiTrack index parameters
            midiStr = trk.read(midiStr) # pass all the remaining string, reassing
            self.tracks.append(trk) 
    
    def write(self): 
        '''
        Write MIDI data as a file to the file opened with `.open()`.
        '''
        ws = self.writestr()
        self.file.write(ws) 
    
    def writestr(self): 
        '''
        Generate the MIDI data header and convert the list of
        MidiTrack objects in self.tracks into MIDI data and return it as a string.
        '''
        midiStr = self.writeMThdStr()
        for trk in self.tracks: 
            midiStr = midiStr + trk.getBytes() 
        return midiStr 


    def writeMThdStr(self): 
        '''
        Convert the information in self.ticksPerQuarterNote
        into MIDI data header and return it as a string.
        '''
        division = self.ticksPerQuarterNote 
        # Don't handle ticksPerSecond yet, too confusing 
        if (division & 0x8000) != 0:
            raise MidiException('Cannot write midi string unless self.ticksPerQuarterNote is a multiple of 1024')
        midiStr = b"MThd" + putNumber(6, 4) + putNumber(self.format, 2) 
        midiStr = midiStr + putNumber(len(self.tracks), 2) 
        midiStr = midiStr + putNumber(division, 2) 
        return midiStr



#-------------------------------------------------------------------------------
class TestExternal(unittest.TestCase):
    '''
    These are tests that open windows and rely on external software
    '''

    def runTest(self):
        pass

    def testBasic(self):
        pass

#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testWriteMThdStr(self):
        '''
        Convert a string of Ascii midi data to a binary midi string.
        '''
        from binascii import a2b_hex
        mf = MidiFile()
        trk = MidiTrack(0)
        mf.format = 1
        mf.tracks.append(trk)
        mf.ticksPerQuarterNote = 960
    
        midiBinStr = b""
        midiBinStr = midiBinStr + mf.writeMThdStr()
        
        self.assertEqual(midiBinStr, b"MThd"+ a2b_hex(b"000000060001000103c0") )

    def testBasicImport(self):

        directory = common.getPackageDir(relative=False, remapSep=os.sep)
        fp = None
        for fp in directory:
            if fp.endswith('midi'):
                break
        if fp is None:
            raise MidiException("No MIDI directory found!")

        dirLib = os.path.join(fp, 'testPrimitive')
        # a simple file created in athenacl
        fp = os.path.join(dirLib, 'test01.mid')
        environLocal.printDebug([fp])
        mf = MidiFile()
        mf.open(fp)
        mf.read()
        mf.close()

        self.assertEqual(len(mf.tracks), 2)
        self.assertEqual(mf.ticksPerQuarterNote, 960)
        self.assertEqual(mf.ticksPerSecond, None)
        #self.assertEqual(mf.writestr(), None)

        # try to write contents
        fileLikeOpen = six.BytesIO()
        mf.openFileLike(fileLikeOpen)
        mf.write()
        mf.close()


        # a simple file created in athenacl
        fp = os.path.join(dirLib, 'test02.mid')
        environLocal.printDebug([fp])
        mf = MidiFile()
        mf.open(fp)
        mf.read()
        mf.close()

        self.assertEqual(len(mf.tracks), 5)
        self.assertEqual(mf.ticksPerQuarterNote, 1024)
        self.assertEqual(mf.ticksPerSecond, None)

        # try to write contents
        fileLikeOpen = six.BytesIO()
        mf.openFileLike(fileLikeOpen)
        mf.write()
        mf.close()


        # random files from the internet
        fp = os.path.join(dirLib, 'test03.mid')
        environLocal.printDebug([fp])
        mf = MidiFile()
        mf.open(fp)
        mf.read()
        mf.close()

        self.assertEqual(len(mf.tracks), 4)
        self.assertEqual(mf.ticksPerQuarterNote, 1024)
        self.assertEqual(mf.ticksPerSecond, None)

        # try to write contents
        fileLikeOpen = six.BytesIO()
        mf.openFileLike(fileLikeOpen)
        mf.write()
        mf.close()

        # random files from the internet
        fp = os.path.join(dirLib, 'test04.mid')
        environLocal.printDebug([fp])
        mf = MidiFile()
        mf.open(fp)
        mf.read()
        mf.close()

        self.assertEqual(len(mf.tracks), 18)
        self.assertEqual(mf.ticksPerQuarterNote,480)
        self.assertEqual(mf.ticksPerSecond, None)

        # try to write contents
        fileLikeOpen = six.BytesIO()
        mf.openFileLike(fileLikeOpen)
        mf.write()
        mf.close()

#         mf = MidiFile()
#         mf.open(fp)
#         mf.read()
#         mf.close()


    def testInternalDataModel(self):

        directory = common.getPackageDir(relative=False, remapSep=os.sep)
        fp = None
        for fp in directory:
            if fp.endswith('midi'):
                break
        if fp is None:
            raise MidiException("No MIDI directory found!")

        dirLib = os.path.join(fp, 'testPrimitive')
        # a simple file created in athenacl
        fp = os.path.join(dirLib, 'test01.mid')
        environLocal.printDebug([fp])
        mf = MidiFile()
        mf.open(fp)
        mf.read()
        mf.close()

        track2 = mf.tracks[1]
        # defines a channel object for each of 16 channels
        #self.assertEqual(len(track2.channels), 16)
        # length seems to be the size of midi data in this track
        self.assertEqual(track2.length, 255)

        # a list of events
        self.assertEqual(len(track2.events), 116)

        i = 0
        while i < len(track2.events)-1:
            self.assertTrue(isinstance(track2.events[i], DeltaTime))
            self.assertTrue(isinstance(track2.events[i+1], MidiEvent))

            #environLocal.printDebug(['sample events: ', track2.events[i]])
            #environLocal.printDebug(['sample events: ', track2.events[i+1]])
            i += 2

        # first object is delta time
        # all objects are pairs of delta time, event


    def testBasicExport(self):

        mt = MidiTrack(1)
        # duration, pitch, velocity
        data = [[1024, 60, 90], [1024, 50, 70], [1024, 51, 120],[1024, 62, 80],
                ]
        t = 0
        tLast = 0
        for d, p, v in data:
            dt = DeltaTime(mt)
            dt.time = t - tLast
            # add to track events
            mt.events.append(dt)

            me = MidiEvent(mt)
            me.type = "NOTE_ON"
            me.channel = 1
            me.time = None #d
            me.pitch = p
            me.velocity = v
            mt.events.append(me)

            # add note off / velocity zero message
            dt = DeltaTime(mt)
            dt.time = d
            # add to track events
            mt.events.append(dt)

            me = MidiEvent(mt)
            me.type = "NOTE_ON"
            me.channel = 1
            me.time = None #d
            me.pitch = p
            me.velocity = 0
            mt.events.append(me)

            tLast = t + d # have delta to note off
            t += d # next time

        # add end of track
        dt = DeltaTime(mt)
        dt.time = 0
        mt.events.append(dt)

        me = MidiEvent(mt)
        me.type = "END_OF_TRACK"
        me.channel = 1
        me.data = '' # must set data to empty string
        mt.events.append(me)

#        for e in mt.events:
#            print e

        mf = MidiFile()
        mf.ticksPerQuarterNote = 1024 # cannot use: 10080
        mf.tracks.append(mt)

        
        fileLikeOpen = six.BytesIO()
        #mf.open('/src/music21/music21/midi/out.mid', 'wb')
        mf.openFileLike(fileLikeOpen)
        mf.write()
        mf.close()


    def testSetPitchBend(self):
        mt = MidiTrack(1)
        me = MidiEvent(mt)
        me.setPitchBend(0)
        me.setPitchBend(200) # 200 cents should be max range
        me.setPitchBend(-200) # 200 cents should be max range


    def testWritePitchBendA(self):

        mt = MidiTrack(1)

#(0 - 16383). The pitch value affects all playing notes on the current channel. Values below 8192 decrease the pitch, while values above 8192 increase the pitch. The pitch range may vary from instrument to instrument, but is usually +/-2 semi-tones.
        #pbValues = [0, 5, 10, 15, 20, 25, 30, 35, 40, 50] 
        pbValues = [0, 25, 0, 50, 0, 100, 0, 150, 0, 200] 
        pbValues += [-x for x in pbValues]

        # duration, pitch, velocity
        data = [[1024, 60, 90]] * 20
        t = 0
        tLast = 0
        for i, e in enumerate(data):
            d, p, v = e
            
            dt = DeltaTime(mt)
            dt.time = t - tLast
            # add to track events
            mt.events.append(dt)

            me = MidiEvent(mt, type="PITCH_BEND", channel=1)
            #environLocal.printDebug(['creating event:', me, 'pbValues[i]', pbValues[i]])
            me.time = None #d
            me.setPitchBend(pbValues[i]) # set values in cents
            mt.events.append(me)

            dt = DeltaTime(mt)
            dt.time = t - tLast
            # add to track events
            mt.events.append(dt)

            me = MidiEvent(mt, type="NOTE_ON", channel=1)
            me.time = None #d
            me.pitch = p
            me.velocity = v
            mt.events.append(me)

            # add note off / velocity zero message
            dt = DeltaTime(mt)
            dt.time = d
            # add to track events
            mt.events.append(dt)

            me = MidiEvent(mt, type='NOTE_ON', channel=1)
            me.time = None #d
            me.pitch = p
            me.velocity = 0
            mt.events.append(me)

            tLast = t + d # have delta to note off
            t += d # next time

        # add end of track
        dt = DeltaTime(mt)
        dt.time = 0
        mt.events.append(dt)

        me = MidiEvent(mt)
        me.type = "END_OF_TRACK"
        me.channel = 1
        me.data = '' # must set data to empty string
        mt.events.append(me)

        # try setting different channels
        mt.setChannel(3)

        mf = MidiFile()
        mf.ticksPerQuarterNote = 1024 # cannot use: 10080
        mf.tracks.append(mt)

        
        fileLikeOpen = six.BytesIO()
        #mf.open('/_scratch/test.mid', 'wb')
        mf.openFileLike(fileLikeOpen)
        mf.write()
        mf.close()

    def testImportWithRunningStatus(self):
        from music21 import converter

        directory = common.getPackageDir(relative=False, remapSep=os.sep)
        fp = None
        for fp in directory:
            if fp.endswith('midi'):
                break   
        if fp is None:
            raise MidiException("No MIDI directory found!")
        dirLib = os.path.join(fp, 'testPrimitive')
        # a simple file created in athenacl
        fp = os.path.join(dirLib, 'test09.mid')
        # dealing with midi files that use running status compression
        s = converter.parse(fp)
        self.assertEqual(len(s.parts), 2)
        self.assertEqual(len(s.parts[0].flat.notes), 746)
        self.assertEqual(len(s.parts[1].flat.notes), 857)

        #for n in s.parts[0].notes:
        #    print n, n.quarterLength
        #s.show()

#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = []

if __name__ == "__main__":
    import music21
    music21.mainTest(Test)


#------------------------------------------------------------------------------
# eof

