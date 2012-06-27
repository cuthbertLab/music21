# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         midi.realtime.py
# Purpose:      music21 classes for playing midi data in realtime
#
# Authors:      Michael Scott Cuthbert
#               (from an idea by Joe "Codeswell")
#
# Copyright:    (c) 2012 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
'''
Objects for realtime playback of Music21 Streams as MIDI. 

From an idea of Joe "Codeswell":

  http://joecodeswell.wordpress.com/2012/06/13/how-to-produce-python-controlled-audio-output-from-music-made-with-music21
  http://stackoverflow.com/questions/10983462/how-can-i-produce-real-time-audio-output-from-music-made-with-music21

Requires pygame: http://www.pygame.org/download.shtml
'''
from music21.base import Music21Exception

import unittest

try:
    import cStringIO as stringIOModule
except ImportError:
    import StringIO as stringIOModule

class StreamPlayerException(Music21Exception):
    pass

class StreamPlayer(object):
    '''
    Create a player for a stream that plays its midi version in realtime using pygame.

    Set up a detuned piano (where each key has a random but consistent detuning from 30 cents flat to sharp)
    and play a Bach Chorale on it in real time.
    
    >>> from music21 import *
    >>> import random
    >>> keyDetune = []
    >>> for i in range(0, 127):
    ...    keyDetune.append(random.randint(-30, 30))
    
    >>> b = corpus.parse('bwv66.6')
    >>> for n in b.flat.notes:
    ...    n.microtone = keyDetune[n.midi]
    >>> sp = midi.realtime.StreamPlayer(b)
    >>> sp.play()
     
    '''
    mixerInitialized = False
    
    def __init__(self, streamIn, **keywords):
        try:
           import pygame
           self.pygame = pygame
        except ImportError:
            raise StreamPlayerException("StreamPlayer requires pygame.  Install first")
        if self.mixerInitialized is False or ("reinitMixer" in keywords and keywords["reinitMixer"] != False):
            if "mixerFreq" in keywords:
                mixerFreq = keywords["mixerFreq"]
            else:
                mixerFreq = 44100
            
            if "mixerBitSize" in keywords:
                mixerBitSize = keywords['mixerBitSize']
            else:
                mixerBitSize = -16
            
            if "mixerChannels" in keywords:
                mixerChannels = keywords['mixerChannels']
            else:
                mixerChannels = 2
            
            if "mixerBuffer" in keywords:
                mixerBuffer = keywords['mixerBuffer']
            else:
                mixerBuffer = 1024
            
            pygame.mixer.init(mixerFreq, mixerBitSize, mixerChannels, mixerBuffer)
        
        self.streamIn = streamIn
    
    def play(self, busyFunction = None, busyArgs = None, endFunction = None, endArgs = None, busyWaitMilliseconds = 30):
        streamMidiFile = self.streamIn.midiFile
        streamMidiWritten = streamMidiFile.writestr()
        streamStringIOFile = stringIOModule.StringIO(streamMidiWritten)
        self.playStringIOFile(streamStringIOFile, busyFunction, busyArgs, endFunction, endArgs, busyWaitMilliseconds)
    
    def playStringIOFile(self, stringIOFile, busyFunction = None, busyArgs = None, endFunction = None, endArgs = None, busyWaitMilliseconds = 30):
        pygameClock = self.pygame.time.Clock()
        try:
            self.pygame.mixer.music.load(stringIOFile)
        except self.pygame.error:
            raise StreamPlayerException("Could not play music file %s because: %s" % (stringIOFile, self.pygame.get_error()))
        self.pygame.mixer.music.play()
        while self.pygame.mixer.music.get_busy():
            if busyFunction is not None:
                busyFunction.__call__(busyArgs)
            pygameClock.tick(busyWaitMilliseconds)
        
        if endFunction is not None:
            endFunction.__call__(endArgs)

class Test(unittest.TestCase):
    pass

class TestExternal(unittest.TestCase):
    
    def testBachDetune(self):
        from music21 import corpus
        import random
        b = corpus.parse('bwv66.6')
        keyDetune = []
        for i in range(0, 127):
            keyDetune.append(random.randint(-30, 30))
        for n in b.flat.notes:
            n.microtone = keyDetune[n.midi]
        sp = StreamPlayer(b)
        sp.play()
            

if __name__ == '__main__':
    import music21
    music21.mainTest(Test)