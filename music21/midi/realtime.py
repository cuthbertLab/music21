# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         midi.realtime.py
# Purpose:      music21 classes for playing midi data in realtime
#
# Authors:      Michael Scott Cuthbert
#               (from an idea by Joe "Codeswell")
#
# Copyright:    Copyright © 2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
Objects for realtime playback of Music21 Streams as MIDI. 

From an idea of Joe "Codeswell":

  http://joecodeswell.wordpress.com/2012/06/13/how-to-produce-python-controlled-audio-output-from-music-made-with-music21
  http://stackoverflow.com/questions/10983462/how-can-i-produce-real-time-audio-output-from-music-made-with-music21

Requires pygame: http://www.pygame.org/download.shtml
'''
from music21.exceptions21 import Music21Exception
from music21.midi import translate as midiTranslate

import unittest

try:
    import cStringIO as stringIOModule
except ImportError:
    try:
        import StringIO as stringIOModule
    except ImportError:
        import io as stringIOModule

class StreamPlayerException(Music21Exception):
    pass

class StreamPlayer(object):
    '''
    Create a player for a stream that plays its midi version in realtime using pygame.

    Set up a detuned piano (where each key has a random but consistent detuning from 30 cents flat to sharp)
    and play a Bach Chorale on it in real time.
    
    
    >>> import random
    >>> keyDetune = []
    >>> for i in range(0, 127):
    ...    keyDetune.append(random.randint(-30, 30))
    
    >>> #_DOCS_SHOW b = corpus.parse('bwv66.6')
    >>> #_DOCS_SHOW for n in b.flat.notes:
    >>> class Mock(): midi = 20 #_DOCS_HIDE -- should not playback in doctests, see TestExternal
    >>> n = Mock() #_DOCS_HIDE
    >>> for i in [1]: #_DOCS_HIDE
    ...    n.microtone = keyDetune[n.midi]
    >>> #_DOCS_SHOW sp = midi.realtime.StreamPlayer(b)
    >>> #_DOCS_SHOW sp.play()
     
    The stream is stored (unaltered) in `StreamPlayer.streamIn`, and can be changed any time the
    midi file is not playing.
     
    A number of mixer controls can be passed in with keywords:
    
      mixerFreq (default 44100 -- CD quality)
      mixerBitSize (default -16 (=unsigned 16bit) -- really, are you going to do 24bit audio with Python?? :-)  )
      mixerChannels (default 2 = stereo)
      mixerBuffer (default 1024 = number of samples)
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
    
    def play(self, busyFunction = None, busyArgs = None, endFunction = None, endArgs = None, busyWaitMilliseconds = 50):
        streamStringIOFile = self.getStringIOFile()
        self.playStringIOFile(streamStringIOFile, busyFunction, busyArgs, endFunction, endArgs, busyWaitMilliseconds)

    def getStringIOFile(self):
        streamMidiFile = midiTranslate.streamToMidiFile(self.streamIn)
        streamMidiWritten = streamMidiFile.writestr()
        return stringIOModule.StringIO(streamMidiWritten)
    
    def playStringIOFile(self, stringIOFile, busyFunction = None, busyArgs = None, endFunction = None, endArgs = None, busyWaitMilliseconds = 50):
        pygameClock = self.pygame.time.Clock()
        try:
            self.pygame.mixer.music.load(stringIOFile)
        except self.pygame.error:
            raise StreamPlayerException("Could not play music file %s because: %s" % (stringIOFile, self.pygame.get_error()))
        self.pygame.mixer.music.play()
        framerate = int(1000/busyWaitMilliseconds) # coerce into int even if given a float.
        
        while self.pygame.mixer.music.get_busy():
            if busyFunction is not None:
                busyFunction.__call__(busyArgs)
            pygameClock.tick(framerate)
        
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

    def xtestBusyCallback(self):
        '''
        tests to see if the busyCallback function is called properly
        '''
        
        from music21 import corpus
        import random
        
        def busyCounter(timeList):
            timeCounter = timeList[0]
            timeCounter.times += timeCounter.updateTime
            print("hi! waited %d milliseconds" % (timeCounter.times))
        
        class Mock():
            times = 0
        
        timeCounter = Mock()
        timeCounter.updateTime = 500 # pylint: disable=attribute-defined-outside-init
        
        b = corpus.parse('bach/bwv66.6')
        keyDetune = []
        for i in range(0, 127):
            keyDetune.append(random.randint(-30, 30))
        for n in b.flat.notes:
            n.microtone = keyDetune[n.midi]
        sp = StreamPlayer(b)
        sp.play(busyFunction=busyCounter, busyArgs=[timeCounter], busyWaitMilliseconds = 500)
            
    def xtestPlayOneMeasureAtATime(self):
        from music21 import corpus
        b = corpus.parse('bwv66.6')
        measures = [] # store for later
        maxMeasure = len(b.parts[0].getElementsByClass('Measure'))
        for i in range(maxMeasure):
            measures.append(b.measure(i))
        sp = StreamPlayer(b)
                
        for i in range(len(measures)):
            sp.streamIn = measures[i]
            sp.play()

    def xtestPlayRealTime(self):
        '''
        doesn't work -- no matter what there's always at least a small lag, even with queues
        '''
        # pylint: disable=attribute-defined-outside-init
        from music21 import stream, note
        import random
        
        def getRandomStream():
            s = stream.Stream()
            for i in range(4):
                n = note.Note()
                n.ps = random.randint(48, 72)
                s.append(n)
            lastN = note.Note()
            #lastN.duration.quarterLength = .75
            s.append(lastN)
            return s
        
        def restoreList(timeList):
            timeCounter = timeList[0]
            streamPlayer = timeList[1]
            currentPos = streamPlayer.pygame.mixer.music.get_pos() 
            if currentPos < 500 and timeCounter.lastPos >= 500: 
                timeCounter.times -= 1
                if timeCounter.times > 0:
                    streamPlayer.streamIn = getRandomStream()
                    #timeCounter.oldIOFile = timeCounter.storedIOFile
                    timeCounter.storedIOFile = streamPlayer.getStringIOFile()
                    streamPlayer.pygame.mixer.music.queue(timeCounter.storedIOFile)
                    timeCounter.lastPos = currentPos
            else:
                timeCounter.lastPos = currentPos
        
        class TimePlayer():
            ready = False
            times = 3
            lastPos = 1000

        timeCounter = TimePlayer()

        b = getRandomStream()
        sp = StreamPlayer(b)
        timeCounter.storedIOFile = sp.getStringIOFile()  
        while timeCounter.times > 0:
            timeCounter.ready = False
            sp.playStringIOFile(timeCounter.storedIOFile, 
                                busyFunction=restoreList, 
                                busyArgs=[timeCounter, sp], 
                                busyWaitMilliseconds = 30)

if __name__ == '__main__':
    import music21
    music21.mainTest(TestExternal)

