#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         midi.py
# Purpose:      music21 classes for dealing with midi data
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    (c) 2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
'''

This module incorporates Will Ware's public domain midi.py from 2001
see http://groups.google.com/group/alt.sources/msg/0c5fc523e050c35e
'''

import unittest, doctest
import sys, string, types

debugflag = 0 

def showstr(str, n=16): 
    for x in str[:n]: 
        print (('%02x' % ord(x)),) 
    print("")

def getNumber(str, length): 
    # MIDI uses big-endian for everything 
    sum = 0 
    for i in range(length): 
        sum = (sum << 8) + ord(str[i]) 
    return sum, str[length:] 

def getVariableLengthNumber(str): 
    sum = 0 
    i = 0 
    while 1: 
        x = ord(str[i]) 
        i = i + 1 
        sum = (sum << 7) + (x & 0x7F) 
        if not (x & 0x80): 
            return sum, str[i:] 

def putNumber(num, length): 
    # MIDI uses big-endian for everything 
    lst = [ ] 
    for i in range(length): 
        n = 8 * (length - 1 - i) 
        lst.append(chr((num >> n) & 0xFF)) 
    return string.join(lst, "") 

def putVariableLengthNumber(x): 
    lst = [ ] 
    while 1: 
        y, x = x & 0x7F, x >> 7 
        lst.append(chr(y + 0x80)) 
        if x == 0: 
            break 
    lst.reverse() 
    lst[-1] = chr(ord(lst[-1]) & 0x7f) 
    return string.join(lst, "") 

class EnumException(Exception): 
    pass 

class Enumeration(object): 
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
                raise EnumException("enum name is not a string: " + x)
            if type(i) != types.IntType: 
                raise EnumException("enum value is not an integer: " + i)
            if x in uniqueNames: 
                raise EnumException("enum name is not unique: " + x)
            if i in uniqueValues: 
                raise EnumException("enum value is not unique for " + x)
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

# runningStatus appears to want to be an attribute of a MidiTrack. But 
# it doesn't seem to do any harm to implement it as a global. 

runningStatus = None 

class MidiEvent(object): 
    
    def __init__(self, track): 
        self.track = track 
        self.time = None 
        self.channel = self.pitch = self.velocity = self.data = None 
    
    def __cmp__(self, other): 
        # assert self.time != None and other.time != None 
        return cmp(self.time, other.time) 
    
    def __repr__(self): 
        r = ("<MidiEvent %s, t=%s, track=%s, channel=%s" % 
             (self.type, 
              repr(self.time), 
              self.track.index, 
              repr(self.channel))) 
        for attrib in ["pitch", "data", "velocity"]: 
            if getattr(self, attrib) != None: 
                r = r + ", " + attrib + "=" + repr(getattr(self, attrib)) 
        return r + ">" 
    
    def read(self, time, str): 
        global runningStatus 
        self.time = time 
        # do we need to use running status? 
        if not (ord(str[0]) & 0x80): 
            str = runningStatus + str 
        runningStatus = x = str[0] 
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
                print("Unknown meta event: FF %02X" % z)
                sys.stdout.flush() 
                raise "Unknown midi event type" 
            self.type = metaEvents.whatis(z) 
            length, str = getVariableLengthNumber(str[2:]) 
            self.data = str[:length] 
            return str[length:] 
        raise "Unknown midi event type" 
    
    def write(self): 
        sysex_event_dict = {"F0_SYSEX_EVENT": 0xF0, 
                            "F7_SYSEX_EVENT": 0xF7} 
        if channelVoiceMessages.hasattr(self.type): 
            x = chr((self.channel - 1) + 
                    getattr(channelVoiceMessages, self.type)) 
            if (self.type != "PROGRAM_CHANGE" and 
                self.type != "CHANNEL_KEY_PRESSURE"): 
                data = chr(self.pitch) + chr(self.velocity) 
            else: 
                data = chr(self.data) 
            return x + data 
        elif channelModeMessages.hasattr(self.type): 
            x = getattr(channelModeMessages, self.type) 
            x = (chr(0xB0 + (self.channel - 1)) + 
                 chr(x) + 
                 chr(self.data)) 
            return x 
        elif sysex_event_dict.has_key(self.type): 
            str = chr(sysex_event_dict[self.type]) 
            str = str + putVariableLengthNumber(len(self.data)) 
            return str + self.data 
        elif metaEvents.hasattr(self.type): 
            str = chr(0xFF) + chr(getattr(metaEvents, self.type)) 
            str = str + putVariableLengthNumber(len(self.data)) 
            return str + self.data 
        else: 
            raise "unknown midi event type: " + self.type 

""" 
register_note() is a hook that can be overloaded from a script that 
imports this module. Here is how you might do that, if you wanted to 
store the notes as tuples in a list. Including the distinction 
between track and channel offers more flexibility in assigning voices. 
import midi 
notelist = [ ] 
def register_note(t, c, p, v, t1, t2): 
    notelist.append((t, c, p, v, t1, t2)) 
midi.register_note = register_note 
""" 

def register_note(track_index, channel_index, pitch, velocity, 
                  keyDownTime, keyUpTime): 
    pass 

class MidiChannel(object): 
    """A channel (together with a track) provides the continuity connecting 
    a NOTE_ON event with its corresponding NOTE_OFF event. Together, those 
    define the beginning and ending times for a Note.""" 
    
    def __init__(self, track, index): 
        self.index = index 
        self.track = track 
        self.pitches = { } 

    def __repr__(self): 
        return "<MIDI channel %d>" % self.index 

    def noteOn(self, pitch, time, velocity): 
        self.pitches[pitch] = (time, velocity) 

    def noteOff(self, pitch, time): 
        if pitch in self.pitches: 
            keyDownTime, velocity = self.pitches[pitch] 
            register_note(self.track.index, self.index, pitch, velocity, 
                          keyDownTime, time) 
            del self.pitches[pitch] 
        # The case where the pitch isn't in the dictionary is illegal, 
        # I think, but we probably better just ignore it. 

class DeltaTime(MidiEvent): 

    type = "DeltaTime" 
    
    def read(self, oldstr): 
        self.time, newstr = getVariableLengthNumber(oldstr) 
        return self.time, newstr 
    def write(self): 
        str = putVariableLengthNumber(self.time) 
        return str 

class MidiTrack(object): 
    
    def __init__(self, index): 
        self.index = index 
        self.events = [] 
        self.channels = [] 
        self.length = 0
        for i in range(16): 
            self.channels.append(MidiChannel(self, i+1)) 

    def read(self, str): 
        time = 0 
        assert str[:4] == "MTrk" 
        length, str = getNumber(str[4:], 4) 
        self.length = length 
        mystr = str[:length] 
        remainder = str[length:] 
        while mystr: 
            delta_t = DeltaTime(self) 
            dt, mystr = delta_t.read(mystr) 
            time = time + dt 
            self.events.append(delta_t) 
            e = MidiEvent(self) 
            mystr = e.read(time, mystr) 
            self.events.append(e) 
        return remainder 
    
    def write(self): 
        time = self.events[0].time 
        # build str using MidiEvents 
        str = "" 
        for e in self.events: 
            str = str + e.write() 
        return "MTrk" + putNumber(len(str), 4) + str 
    
    def __repr__(self): 
        r = "<MidiTrack %d -- %d events\n" % (self.index, len(self.events)) 
        for e in self.events: 
            r = r + "    " + `e` + "\n" 
        return r + "  >" 

class MidiFile(object):
    
    def __init__(self): 
        self.file = None 
        self.format = 1 
        self.tracks = [ ] 
        self.ticksPerQuarterNote = None 
        self.ticksPerSecond = None 
    
    def open(self, filename, attrib="rb"): 
        if filename == None: 
            if attrib in ["r", "rb"]: 
                self.file = sys.stdin 
            else: 
                self.file = sys.stdout 
        else: 
            self.file = open(filename, attrib) 
    
    def __repr__(self): 
        r = "<MidiFile %d tracks\n" % len(self.tracks) 
        for t in self.tracks: 
            r = r + "  " + `t` + "\n" 
        return r + ">" 
    
    def close(self): 
        self.file.close() 
    
    def read(self): 
        self.readstr(self.file.read()) 
    
    def readstr(self, str): 
        assert str[:4] == "MThd" 
        length, str = getNumber(str[4:], 4) 
        assert length == 6 
        format, str = getNumber(str, 2) 
        self.format = format 
        assert format == 0 or format == 1   # dunno how to handle 2 
        numTracks, str = getNumber(str, 2) 
        division, str = getNumber(str, 2) 
        if division & 0x8000: 
            framesPerSecond = -((division >> 8) | -128) 
            ticksPerFrame = division & 0xFF 
            assert ticksPerFrame == 24 or ticksPerFrame == 25 or \
                   ticksPerFrame == 29 or ticksPerFrame == 30 
            if ticksPerFrame == 29: ticksPerFrame = 30  # drop frame 
            self.ticksPerSecond = ticksPerFrame * framesPerSecond 
        else: 
            self.ticksPerQuarterNote = division & 0x7FFF 
        for i in range(numTracks): 
            trk = MidiTrack(i) 
            str = trk.read(str) 
            self.tracks.append(trk) 
    
    def write(self): 
        self.file.write(self.writestr()) 
    
    def writestr(self): 
        division = self.ticksPerQuarterNote 
        # Don't handle ticksPerSecond yet, too confusing 
        assert (division & 0x8000) == 0 
        str = "MThd" + putNumber(6, 4) + putNumber(self.format, 2) 
        str = str + putNumber(len(self.tracks), 2) 
        str = str + putNumber(division, 2) 
        for trk in self.tracks: 
            str = str + trk.write() 
        return str 

def main(argv): 
    global debugflag 
    import getopt 
    infile = None 
    outfile = None 
    printflag = 0 
    optlist, args = getopt.getopt(argv[1:], "i:o:pd") 
    for (option, value) in optlist: 
        if option == '-i': 
            infile = value 
        elif option == '-o': 
            outfile = value 
        elif option == '-p': 
            printflag = 1 
        elif option == '-d': 
            debugflag = 1 
    m = MidiFile() 
    m.open(infile) 
    m.read() 
    m.close() 
    if printflag: 
        print(m) 
    else: 
        m.open(outfile, "wb") 
        m.write() 
        m.close() 

if __name__ == "__main__": 
    main(sys.argv) 