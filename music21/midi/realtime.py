# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         midi.realtime.py
# Purpose:      music21 classes for playing midi data in realtime
#
# Authors:      Michael Scott Asato Cuthbert
#               (from an idea by Joe "Codeswell")
#
# Copyright:    Copyright © 2012 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
Objects for realtime playback of Music21 Streams as MIDI.

From an idea of Joe "Codeswell":

https://joecodeswell.wordpress.com/2012/06/13/how-to-produce-python-controlled-audio-output-from-music-made-with-music21

https://stackoverflow.com/questions/10983462/how-can-i-produce-real-time-audio-output-from-music-made-with-music21

Requires pygame: http://www.pygame.org/download.shtml
'''
from __future__ import annotations

from importlib.util import find_spec
from io import BytesIO
import unittest

from music21 import defaults
from music21.exceptions21 import Music21Exception
from music21 import stream

from music21.midi import translate as midiTranslate

class StreamPlayerException(Music21Exception):
    pass


class StreamPlayer:  # pragma: no cover
    '''
    Create a player for a stream that plays its midi version in realtime using pygame.

    Set up a detuned piano (where each key has a random but
    consistent detuning from 30 cents flat to sharp)
    and play a Bach Chorale on it in real time.


    >>> import random
    >>> keyDetune = []
    >>> for i in range(127):
    ...    keyDetune.append(random.randint(-30, 30))

    >>> #_DOCS_SHOW b = corpus.parse('bwv66.6')
    >>> #_DOCS_SHOW for n in b.flatten().notes:
    >>> class PitchMock: midi = 20  #_DOCS_HIDE
    >>> class Mock: pitch = PitchMock()  #_DOCS_HIDE
    >>> #_DOCS_HIDE -- should not play back in doctests, see TestExternal
    >>> n = Mock()  #_DOCS_HIDE
    >>> for i in [1]:  #_DOCS_HIDE
    ...    n.pitch.microtone = keyDetune[n.pitch.midi]
    >>> #_DOCS_SHOW sp = midi.realtime.StreamPlayer(b)
    >>> #_DOCS_SHOW sp.play()

    The stream is stored (unaltered) in `StreamPlayer.streamIn`, and can be changed any time the
    midi file is not playing.

    A number of mixer controls can be passed in with keywords:

    *  mixerFreq (default 44100 -- CD quality)
    *  mixerBitSize (default -16 (=unsigned 16bit) --
         really, are you going to do 24bit audio with Python?? :-)  )
    *  mixerChannels (default 2 = stereo)
    *  mixerBuffer (default 1024 = number of samples)
    '''
    mixerInitialized = False

    def __init__(
        self,
        streamIn: stream.Stream,
        reinitMixer: bool = False,
        mixerFreq: int = 44100,
        mixerBitSize: int = -16,
        mixerChannels: int = 2,
        mixerBuffer: int = 1024,
    ):
        try:
            # noinspection PyPackageRequirements
            import pygame  # type: ignore
            self.pygame = pygame
        except ImportError:
            raise StreamPlayerException('StreamPlayer requires pygame.  Install first')
        if self.mixerInitialized is False or reinitMixer:
            pygame.mixer.init(mixerFreq, mixerBitSize, mixerChannels, mixerBuffer)

        self.streamIn = streamIn

    def play(self,
             busyFunction=None,
             busyArgs=None,
             endFunction=None,
             endArgs=None,
             busyWaitMilliseconds=50,
             *,
             playForMilliseconds=float('inf'),
             blocked=True):
        '''
        busyFunction is a function that is called with busyArgs when the music is busy every
        busyWaitMilliseconds.

        endFunction is a function that is called with endArgs when the music finishes playing.

        playForMilliseconds is the amount of time in milliseconds after which
        the playback will be automatically stopped.

        If blocked is False, the method will finish before ending the stream, allowing
        you to completely control whether to stop it. Ignore every other arguments
        '''
        streamStringIOFile = self.getStringOrBytesIOFile()
        self.playStringIOFile(streamStringIOFile,
                              busyFunction=busyFunction,
                              busyArgs=busyArgs,
                              endFunction=endFunction,
                              endArgs=endArgs,
                              busyWaitMilliseconds=busyWaitMilliseconds,
                              playForMilliseconds=playForMilliseconds,
                              blocked=blocked)

    def getStringOrBytesIOFile(self):
        streamMidiFile = midiTranslate.streamToMidiFile(self.streamIn)
        streamMidiWritten = streamMidiFile.writestr()
        return BytesIO(streamMidiWritten)

    def playStringIOFile(self, stringIOFile, busyFunction=None, busyArgs=None,
                         endFunction=None, endArgs=None, busyWaitMilliseconds=50,
                         *,
                         playForMilliseconds=float('inf'), blocked=True):
        '''
        busyFunction is a function that is called with busyArgs when the music is busy every
        busyWaitMilliseconds.

        endFunction is a function that is called with endArgs when the music finishes playing.

        playForMilliseconds is the amount of time in milliseconds after which the
        playback will be automatically stopped.

        If blocked is False, the method will finish before ending the stream, allowing you to
        completely control whether to stop it. Ignore every other arguments but for stringIOFile
        '''
        pygameClock = self.pygame.time.Clock()
        try:
            self.pygame.mixer.music.load(stringIOFile)
        except self.pygame.error:
            raise StreamPlayerException(
                f'Could not play music file {stringIOFile} because: {self.pygame.get_error()}')
        self.pygame.mixer.music.play()
        if not blocked:
            return
        framerate = int(1000 / busyWaitMilliseconds)  # coerce into int even if given a float.
        start_time = self.pygame.time.get_ticks()
        while self.pygame.mixer.music.get_busy():
            if busyFunction is not None:
                busyFunction(busyArgs)
            if self.pygame.time.get_ticks() - start_time > playForMilliseconds:
                self.pygame.mixer.music.stop()
                break
            pygameClock.tick(framerate)

        if endFunction is not None:
            endFunction(endArgs)

    def stop(self):
        self.pygame.mixer.music.stop()


class Test(unittest.TestCase):
    pass


class TestExternal(unittest.TestCase):  # pragma: no cover
    loader = find_spec('pygame')
    if loader is not None:  # pragma: no cover
        pygame_installed = True
    else:
        pygame_installed = False

    @unittest.skipUnless(pygame_installed, 'pygame is not installed')
    def testBachDetune(self):
        from music21 import corpus
        import random
        b = corpus.parse('bwv66.6')
        keyDetune = []
        for i in range(127):
            keyDetune.append(random.randint(-30, 30))
        for n in b.recurse().notes:
            n.pitch.microtone = keyDetune[n.pitch.midi]
        sp = StreamPlayer(b)
        sp.play()

        # # testing playForMilliseconds
        # sp.play(playForMilliseconds=2000)

        # # testing blocked=False
        # sp.play(blocked=False)
        # import time
        # time.sleep(2)
        # sp.stop()
        # time.sleep(1)

    def x_testBusyCallback(self):
        '''
        tests to see if the busyCallback function is called properly
        '''

        from music21 import corpus
        import random

        def busyCounter(timeList):
            timeCounter_inner = timeList[0]
            timeCounter_inner.times += timeCounter_inner.updateTime
            print(f'hi! waited {timeCounter_inner.times} milliseconds')

        class Mock:
            times = 0

        timeCounter = Mock()
        timeCounter.updateTime = 500  # pylint: disable=attribute-defined-outside-init

        b = corpus.parse('bach/bwv66.6')
        keyDetune = []
        for i in range(127):
            keyDetune.append(random.randint(-30, 30))
        for n in b.recurse().notes:
            n.pitch.microtone = keyDetune[n.pitch.midi]
        sp = StreamPlayer(b)
        sp.play(busyFunction=busyCounter, busyArgs=[timeCounter], busyWaitMilliseconds=500)

    def x_testPlayOneMeasureAtATime(self):
        from music21 import corpus
        defaults.ticksAtStart = 0
        b = corpus.parse('bwv66.6')
        measures = []  # store for later
        maxMeasure = len(b.parts[0].getElementsByClass(stream.Measure))
        for i in range(maxMeasure):
            measures.append(b.measure(i))
        sp = StreamPlayer(b)

        for i in range(len(measures)):
            sp.streamIn = measures[i]
            sp.play()

    def x_testPlayRealTime(self):
        '''
        doesn't work -- no matter what there's always at least a small lag, even with queues
        '''
        # pylint: disable=attribute-defined-outside-init
        from music21 import note
        import random

        def getRandomStream():
            s = stream.Stream()
            for i in range(4):
                n = note.Note()
                n.ps = random.randint(48, 72)
                s.append(n)
            lastN = note.Note()
            # lastN.duration.quarterLength = 0.75
            s.append(lastN)
            return s

        # noinspection PyShadowingNames
        def restoreList(timeList):
            timeCounter = timeList[0]
            streamPlayer = timeList[1]
            currentPos = streamPlayer.pygame.mixer.music.get_pos()
            if currentPos < 500 <= timeCounter.lastPos:
                timeCounter.times -= 1
                if timeCounter.times > 0:
                    streamPlayer.streamIn = getRandomStream()
                    # timeCounter.oldIOFile = timeCounter.storedIOFile
                    timeCounter.storedIOFile = streamPlayer.getStringOrBytesIOFile()
                    streamPlayer.pygame.mixer.music.queue(timeCounter.storedIOFile)
                    timeCounter.lastPos = currentPos
            else:
                timeCounter.lastPos = currentPos

        class TimePlayer:
            ready = False
            times = 3
            lastPos = 1000

        timeCounter = TimePlayer()

        b = getRandomStream()
        sp = StreamPlayer(b)
        timeCounter.storedIOFile = sp.getStringOrBytesIOFile()
        while timeCounter.times > 0:
            timeCounter.ready = False
            sp.playStringIOFile(timeCounter.storedIOFile,
                                busyFunction=restoreList,
                                busyArgs=[timeCounter, sp],
                                busyWaitMilliseconds=30)


if __name__ == '__main__':
    import music21
    music21.mainTest(TestExternal)
