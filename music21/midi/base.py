#-------------------------------------------------------------------------------
# Name:         midi.base.py
# Purpose:      music21 classes for dealing with midi data
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#               (Will Ware -- see docs)
#
# Copyright:    (c) 2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
'''
Objects and tools for processing MIDI data. 

This module uses routines from Will Ware's public domain midi.py from 2001
see http://groups.google.com/group/alt.sources/msg/0c5fc523e050c35e
'''

import unittest, doctest
import unicodedata
import sys, os, string, types

try:
    import StringIO # python 2 
except:
    from io import StringIO # python3 (also in python 2.6+)

import music21
from music21 import common

from music21 import environment
_MOD = "midi.base.py"  
environLocal = environment.Environment(_MOD)






#-------------------------------------------------------------------------------
class EnumerationException(Exception): 
    pass 

class MidiException(Exception): 
    pass 




#-------------------------------------------------------------------------------
# def showstr(str, n=16): 
#     for x in str[:n]: 
#         print (('%02x' % ord(x)),) 
#     print("")

def getNumber(str, length): 
    '''Return the value of a string byte from and 8-bit string.

    This will sum a length greater than 1 if desired.

    >>> getNumber('test', 0)
    (0, 'test')
    >>> getNumber('test', 2)
    (29797, 'st')
    >>> getNumber('test', 4)
    (1952805748, '')
    '''
    # MIDI uses big-endian for everything 
    # in python this is the inverse of chr()

    sum = 0 
    for i in range(length): 
        sum = (sum << 8) + ord(str[i]) 
    return sum, str[length:] 

def getVariableLengthNumber(str): 
    '''
    >>> getVariableLengthNumber('test')
    (116, 'est')
    '''
    sum = 0 
    i = 0 
    while 1: 
        x = ord(str[i]) 
        i = i + 1 
        sum = (sum << 7) + (x & 0x7F) 
        if not (x & 0x80): 
            return sum, str[i:] 

def getNumbersAsList(str):
    '''Translate each char into a number, return in a list. Used for reading data messages where each byte encodes a different discrete value. 

    >>> getNumbersAsList('\\x00\\x00\\x00\\x03')
    [0, 0, 0, 3]
    '''
    post = []
    for i in range(len(str)):
        post.append(ord(str[i]))
    return post

def putNumber(num, length): 
    '''
    >>> putNumber(3, 4)
    '\\x00\\x00\\x00\\x03'
    >>> putNumber(0, 1)
    '\\x00'
    '''
    lst = [] 
    for i in range(length): 
        n = 8 * (length - 1 - i) 
        lst.append(chr((num >> n) & 0xFF)) 
    return string.join(lst, "") 

def putVariableLengthNumber(x): 
    '''
    >>> putVariableLengthNumber(4)
    '\\x04'
    >>> putVariableLengthNumber(127)
    '\\x7f'
    >>> putVariableLengthNumber(0)
    '\\x00'
    >>> putVariableLengthNumber(1024)
    '\\x88\\x00'
    >>> putVariableLengthNumber(-1)
    Traceback (most recent call last):
    MidiException: cannot putVariableLengthNumber() when number is negative: -1
    '''
    #environLocal.printDebug(['calling putVariableLengthNumber(x) with', x])
    # note: negative numbers will cause an infinite loop here
    if x < 0:
        raise MidiException('cannot putVariableLengthNumber() when number is negative: %s' % x)
    lst = [ ] 
    while True: 
        y, x = x & 0x7F, x >> 7 
        lst.append(chr(y + 0x80)) 
        if x == 0: 
            break 
    lst.reverse() 
    lst[-1] = chr(ord(lst[-1]) & 0x7f) 
    return string.join(lst, "") 


def putNumbersAsList(numList):
    '''Translate a list of numbers into a character byte strings. Used for encoding data messages where each byte encodes a different discrete value. 

    >>> putNumbersAsList([0, 0, 0, 3])
    '\\x00\\x00\\x00\\x03'
    >>> putNumbersAsList([0, 0, 0, -3])
    '\\x00\\x00\\x00\\xfd'
    >>> putNumbersAsList([0, 0, 0, -1])
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
    '''Utility object for defining binary MIDI message constants. 
    '''
    def __init__(self, enumList): 
        lookup = { } 
        reverseLookup = { } 
        i = 0 
        uniqueNames = [ ] 
        uniqueValues = [ ] 
        for x in enumList: 
            if type(x) == types.TupleType: 
                x, i = x 
            if type(x) != types.StringType: 
                raise EnumerationException("enum name is not a string: " + x)
            if type(i) != types.IntType: 
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
        for k in self.lookup.keys(): 
            lst.append((k, self.lookup[k])) 
        for k in other.lookup.keys(): 
            lst.append((k, other.lookup[k])) 
        return Enumeration(lst) 

    def hasattr(self, attr): 
        return self.lookup.has_key(attr) 

    def has_value(self, attr): 
        return self.reverseLookup.has_key(attr) 

    def __getattr__(self, attr): 
        if not self.lookup.has_key(attr): 
            raise AttributeError 
        return self.lookup[attr] 

    def whatis(self, value): 
        return self.reverseLookup[value] 

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
                          ("MIDI_CHANNEL_PREFIX", 0x20), 
                          ("MIDI_PORT", 0x21), 
                          ("END_OF_TRACK", 0x2F), 
                          ("SET_TEMPO", 0x51), 
                          ("SMTPE_OFFSET", 0x54), 
                          ("TIME_SIGNATURE", 0x58), 
                          ("KEY_SIGNATURE", 0x59), 
                          ("SEQUENCER_SPECIFIC_META_EVENT", 0x7F)]) 



# def register_note(track_index, channel_index, pitch, velocity, 
#                   keyDownTime, keyUpTime): 
# 
#     """ 
#     register_note() is a hook that can be overloaded from a script that 
#     imports this module. Here is how you might do that, if you wanted to 
#     store the notes as tuples in a list. Including the distinction 
#     between track and channel offers more flexibility in assigning voices. 
#     import midi 
#     notelist = [ ] 
#     def register_note(t, c, p, v, t1, t2): 
#         notelist.append((t, c, p, v, t1, t2)) 
#     midi.register_note = register_note 
#     """ 
#     pass 



class MidiChannel(object): 
    '''A channel (together with a track) provides the continuity connecting 
    a NOTE_ON event with its corresponding NOTE_OFF event. Together, those 
    define the beginning and ending times for a Note.

    >>> mc = MidiChannel(0, 0)
    ''' 
    
    def __init__(self, track, index): 
        self.index = index 
        self.track = track 
        self.pitches = {} 

    def __repr__(self): 
        return "<MIDI channel %d>" % self.index 

    def noteOn(self, pitch, time, velocity): 
        self.pitches[pitch] = (time, velocity) 

    def noteOff(self, pitch, time): 
        if pitch in self.pitches: 
            keyDownTime, velocity = self.pitches[pitch] 
            #register_note(self.track.index, self.index, pitch, velocity, 
            #              keyDownTime, time) 
            del self.pitches[pitch] 



#-------------------------------------------------------------------------------
class MidiEvent(object): 
    '''A model of a MIDI event, including note-on, note-off, program change, controller change, any many others.

    MidiEvent objects are paired (preceded) by DeltaTime objects in the list of events in a MidiTrack object.

    The `track` argument must be a :class:`~music21.midi.base.MidiTrack` object.

    The `type` attribute is a string representation of a Midi event from the channelVoiceMessages or metaEvents definitions. 

    The `channel` attribute is an integer channel id, from 1 to 16. 

    The `time` attribute is an integer duration of the event in ticks. This value can be zero. This value is not essential, as ultimate time positioning is determined by DeltaTime objects. 

    The `pitch` attribute is only defined for note-on and note-off messages. The attribute stores an integer representation (0-127).

    The `velocity` attribute is only defined for note-on and note-off messages. The attribute stores an integer representation (0-127).

    The `data` attribute is used for storing other messages, such as SEQUENCE_TRACK_NAME string values. 

    >>> mt = MidiTrack(1)
    >>> me1 = MidiEvent(mt)
    >>> me1.type = "NOTE_ON"
    >>> me1.channel = 1
    >>> me1.time = 200
    >>> me1.pitch = 60
    >>> me1.velocity = 120
    >>> me1
    <MidiEvent NOTE_ON, t=200, track=1, channel=1, pitch=60, velocity=120>

    >>> me2 = MidiEvent(mt)
    >>> me2.type = "SEQUENCE_TRACK_NAME"
    >>> me2.time = 0
    >>> me2.data = 'guitar'
    >>> me2
    <MidiEvent SEQUENCE_TRACK_NAME, t=0, track=1, channel=None, data='guitar'>
    '''
    
    def __init__(self, track): 
        self.track = track 
        self.type = None 
        self.time = None 
        self.channel = None
        self.pitch = None
        self.velocity = None
        self.data = None 
    
    def __cmp__(self, other): 
        return cmp(self.time, other.time) 
    
    def __repr__(self): 
        if self.track == None:
            trackIndex = None
        else:
            trackIndex = self.track.index

        r = ("<MidiEvent %s, t=%s, track=%s, channel=%s" % 
             (self.type, repr(self.time), trackIndex, 
              repr(self.channel))) 
        for attrib in ["pitch", "data", "velocity"]: 
            if getattr(self, attrib) != None: 
                r = r + ", " + attrib + "=" + repr(getattr(self, attrib)) 
        return r + ">" 
    
    def read(self, time, str): 
        '''Read a MIDI event.
        '''
        x = str[0] 
        x = ord(x) 
        y = x & 0xF0 
        z = ord(str[1]) 
        if channelVoiceMessages.has_value(y): 
            self.channel = (x & 0x0F) + 1 
            self.type = channelVoiceMessages.whatis(y) 
            if (self.type == "PROGRAM_CHANGE" or 
                self.type == "CHANNEL_KEY_PRESSURE"): 
                self.data = z 
                return str[2:] 
            else: 
                self.pitch = z 
                self.velocity = ord(str[2]) 

                # each channel's object is accessed here
                # using that channel, data for each event is sent
                # note-offs are automatically paired
                channel = self.track.channels[self.channel - 1] 
                if (self.type == "NOTE_OFF" or 
                    (self.velocity == 0 and self.type == "NOTE_ON")): 
                    channel.noteOff(self.pitch, self.time) 

                elif self.type == "NOTE_ON": 
                    channel.noteOn(self.pitch, self.time, self.velocity) 
                return str[3:] 

        elif y == 0xB0 and channelModeMessages.has_value(z): 
            self.channel = (x & 0x0F) + 1 
            self.type = channelModeMessages.whatis(z) 
            if self.type == "LOCAL_CONTROL": 
                self.data = (ord(str[2]) == 0x7F) 
            elif self.type == "MONO_MODE_ON": 
                self.data = ord(str[2]) 
            return str[3:] 
        elif x == 0xF0 or x == 0xF7: 
            self.type = {0xF0: "F0_SYSEX_EVENT", 
                         0xF7: "F7_SYSEX_EVENT"}[x] 
            length, str = getVariableLengthNumber(str[1:]) 
            self.data = str[:length] 
            return str[length:] 
        elif x == 0xFF: 
            if not metaEvents.has_value(z): 
                environLocal.printDebug(["unknown meta event: FF %02X" % z])
                sys.stdout.flush() 
                raise MidiException("Unknown midi event type")

            self.type = metaEvents.whatis(z) 
            length, str = getVariableLengthNumber(str[2:]) 
            self.data = str[:length] 
            return str[length:] 

        raise MidiException("Unknown midi event type")
    
    def write(self): 
        sysex_event_dict = {"F0_SYSEX_EVENT": 0xF0, 
                            "F7_SYSEX_EVENT": 0xF7} 

        if channelVoiceMessages.hasattr(self.type): 
            x = chr((self.channel - 1) + 
                    getattr(channelVoiceMessages, self.type)) 

            # for writing note-on/note-off
            if (self.type != "PROGRAM_CHANGE" and 
                self.type != "CHANNEL_KEY_PRESSURE"): 
                data = chr(self.pitch) + chr(self.velocity) 
            else:  # all other messages
                data = chr(self.data) 
            return x + data 

        elif channelModeMessages.hasattr(self.type): 
            x = getattr(channelModeMessages, self.type) 
            x = (chr(0xB0 + (self.channel - 1)) + 
                 chr(x) + 
                 chr(self.data)) 
            return x 

        elif sysex_event_dict.has_key(self.type): 
            s = chr(sysex_event_dict[self.type]) 
            s = s + putVariableLengthNumber(len(self.data)) 
            return s + self.data 

        elif metaEvents.hasattr(self.type): 
            s = chr(0xFF) + chr(getattr(metaEvents, self.type)) 
            s = s + putVariableLengthNumber(len(self.data)) 
            try: # TODO: need to handle unicode
                return s + self.data 
            except UnicodeDecodeError:
                #environLocal.printDebug(['cannot decode data', self.data])
                return s + unicodedata.normalize('NFKD', 
                           self.data).encode('ascii','ignore')
        else: 
            raise MidiException("unknown midi event type: %s" % self.type)

    #---------------------------------------------------------------------------
    def isNoteOn(self):
        '''Return a boolean if this is a note-on message and velocity is not zero.

        >>> mt = MidiTrack(1)
        >>> me1 = MidiEvent(mt)
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
        '''Return a boolean if this is a note-off message, either as a note-off or as a note-on with zero velocity.

        >>> mt = MidiTrack(1)
        >>> me1 = MidiEvent(mt)
        >>> me1.type = "NOTE_OFF"
        >>> me1.isNoteOn()
        False
        >>> me1.isNoteOff()
        True

        >>> me2 = MidiEvent(mt)
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
        '''Return a boolean if this is a note-on message and velocity is not zero.

        >>> mt = MidiTrack(1)
        >>> dt = DeltaTime(mt)
        >>> dt.isDeltaTime()
        True
        '''
        if self.type == "DeltaTime":
            return True
        return False

    def matchedNoteOff(self, other):
        '''If this is a note-on, given another MIDI event, is this a matching note-off for this event, return True. Checks both pitch and channel.

        >>> mt = MidiTrack(1)
        >>> me1 = MidiEvent(mt)
        >>> me1.type = "NOTE_ON"
        >>> me1.velocity = 120
        >>> me1.pitch = 60

        >>> me2 = MidiEvent(mt)
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

        '''
        if other.isNoteOff:
            if self.pitch == other.pitch and self.channel == other.channel:
                return True
        return False


class DeltaTime(MidiEvent): 
    '''Store the time change since the start or the last MidiEvent.

    Pairs of DeltaTime and MidiEvent objects are the basic presentation of temporal data.

    The `track` argument must be a :class:`~music21.midi.base.MidiTrack` object.

    Time values are in integers, representing ticks. 

    The `channel` attribute, inherited from MidiEvent is not used.

    >>> mt = MidiTrack(1)
    >>> dt = DeltaTime(mt)
    >>> dt.time = 380
    >>> dt
    <MidiEvent DeltaTime, t=380, track=1, channel=None>

    '''
    def __init__(self, track):
        MidiEvent.__init__(self, track)
        self.type = "DeltaTime" 

    def read(self, oldstr): 
        self.time, newstr = getVariableLengthNumber(oldstr) 
        return self.time, newstr 

    def write(self): 
        str = putVariableLengthNumber(self.time) 
        return str 





class MidiTrack(object): 
    '''A MIDI track.

    An `index` is an integer identifier for this object.

    >>> mt = MidiTrack(0)
    
    '''
    def __init__(self, index): 
        self.index = index 
        self.events = [] 
        self.length = 0 #the data length; only used on read()

        # an object for each of 16 channels is created
        self.channels = [] 
        for i in range(16): 
            self.channels.append(MidiChannel(self, i+1)) 

    def read(self, str): 
        time = 0 # a running counter of ticks

        if not str[:4] == "MTrk":
            raise MidiException('badly formed midi string')
        length, str = getNumber(str[4:], 4) 

        
        self.length = length 
        mystr = str[:length] 
        remainder = str[length:] 

        while mystr: 
            # shave off the time stamp from the event
            delta_t = DeltaTime(self) 
            dt, mystr = delta_t.read(mystr) 
            time = time + dt 
            self.events.append(delta_t) 
    
            # set this MidiTrack as the track for this event
            e = MidiEvent(self) 
            # some midi events may raise errors; simply skip for now
            try:
                mystr = e.read(time, mystr) 
            except MidiException:
                #environLocal.printDebug(['forced to skip event; delta_t:', delta_t])
                # remove the last delta_t added to events
                junk = self.events.pop(len(self.events)-1)
                continue
            self.events.append(e) 

        return remainder 
    
    def write(self): 
        # set time to the first event
        time = self.events[0].time 
        # build str using MidiEvents 
        str = ""
        for e in self.events: 
            # this writes both delta time and message events
            ew = e.write()
            str = str + ew 
        return "MTrk" + putNumber(len(str), 4) + str 
    
    def __repr__(self): 
        r = "<MidiTrack %d -- %d events\n" % (self.index, len(self.events)) 
        for e in self.events: 
            r = r + "    " + `e` + "\n" 
        return r + "  >" 

    #---------------------------------------------------------------------------
    def updateEvents(self):
        '''We may attach events to this track before setting their `track` parameter. This method will move through all events and set their track to this track. 
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
        '''Open a MIDI file path for reading or writing.

        For writing to a MIDI file, `attrib` should be "wb".
        '''
        if attrib not in ['rb', 'wb']:
            raise MidiException('cannot read or write unless in binary mode, not:', attrib)
        self.file = open(filename, attrib) 

    def openFileLike(self, fileLike):
        '''Assign a file-like object, such as those provided by StringIO, as an open file object.

        >>> fileLikeOpen = StringIO.StringIO()
        >>> mf = MidiFile()
        >>> mf.openFileLike(fileLikeOpen)
        >>> mf.close()
        '''
        self.file = fileLike
    
    def __repr__(self): 
        r = "<MidiFile %d tracks\n" % len(self.tracks) 
        for t in self.tracks: 
            r = r + "  " + `t` + "\n" 
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
    
    def readstr(self, str): 
        '''
        Read and parse MIDI data as a string.
        '''
        if not str[:4] == "MThd":
            raise MidiException('badly formated midi string, got: %s' % str[:20])
        length, str = getNumber(str[4:], 4) 
        if not length == 6:
            raise MidiException('badly formated midi string')

        format, str = getNumber(str, 2) 
        self.format = format 

        if not format in [0, 1]:
            raise MidiException('cannot handle midi file format: %s' % format)

        numTracks, str = getNumber(str, 2) 
        division, str = getNumber(str, 2) 

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

        for i in range(numTracks): 
            trk = MidiTrack(i) 
            str = trk.read(str) 
            self.tracks.append(trk) 
    
    def write(self): 
        '''
        Write MIDI data as a file.
        '''
        ws = self.writestr()
        self.file.write(ws) 
    
    def writestr(self): 
        '''
        Return MIDI data as a string. 
        '''
        division = self.ticksPerQuarterNote 
        # Don't handle ticksPerSecond yet, too confusing 
        if (division & 0x8000) != 0:
            raise MidiException('cannot write midi string')
        str = "MThd" + putNumber(6, 4) + putNumber(self.format, 2) 
        str = str + putNumber(len(self.tracks), 2) 
        str = str + putNumber(division, 2) 
        for trk in self.tracks: 
            str = str + trk.write() 
        return str 


#-------------------------------------------------------------------------------
# utility functions for getting commonly used event


def getStartEvents(mt=None, partName='', partProgram=0):
    '''Provide a list of events found at the beginning of a track.

    A MidiTrack reference can be provided via the `mt` parameter.
    '''
    events = []

    dt = DeltaTime(mt)
    dt.time = 0
    events.append(dt)

    me = MidiEvent(mt)
    me.type = "SEQUENCE_TRACK_NAME"
    me.time = 0 # always at zero?
    me.data = partName
    events.append(me)

    return events


def getEndEvents(mt=None, channelNumber=1):
    '''Provide a list of events found at the end of a track.
    '''
    events = []

    dt = DeltaTime(mt)
    dt.time = 0
    events.append(dt)

    me = MidiEvent(mt)
    me.type = "END_OF_TRACK"
    me.channel = channelNumber
    me.data = '' # must set data to empty string
    events.append(me)

    return events



#-------------------------------------------------------------------------------
class TestExternal(unittest.TestCase):
    '''These are tests that open windows and rely on external software
    '''

    def runTest(self):
        pass

    def testBasic(self):
        pass

#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testBasicImport(self):

        dir = common.getPackageDir(relative=False, remapSep=os.sep)
        for fp in dir:
            if fp.endswith('midi'):
                break

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
        #self.assertEqual(mf.writestr, None)

        # try to write contents
        fileLikeOpen = StringIO.StringIO()
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
        fileLikeOpen = StringIO.StringIO()
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
        fileLikeOpen = StringIO.StringIO()
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
        fileLikeOpen = StringIO.StringIO()
        mf.openFileLike(fileLikeOpen)
        mf.write()
        mf.close()

#         mf = MidiFile()
#         mf.open(fp)
#         mf.read()
#         mf.close()


    def testInternalDataModel(self):

        dir = common.getPackageDir(relative=False, remapSep=os.sep)
        for fp in dir:
            if fp.endswith('midi'):
                break

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
        self.assertEqual(len(track2.channels), 16)
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

        
        fileLikeOpen = StringIO.StringIO()
        #mf.open('/src/music21/music21/midi/out.mid', 'wb')
        mf.openFileLike(fileLikeOpen)
        mf.write()
        mf.close()


#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = []

if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)
    elif len(sys.argv) > 1:
        a = Test()
        b = TestExternal()



        #a.testNoteBeatPropertyCorpus()


#------------------------------------------------------------------------------
# eof

