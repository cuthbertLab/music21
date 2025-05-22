from binascii import a2b_hex
import copy
import io
import math
import random
import unittest

from music21 import chord
from music21 import converter
from music21 import common
from music21 import corpus
from music21 import environment
from music21 import instrument
from music21 import interval
from music21 import key
from music21 import meter
from music21.midi.base import (
    ChannelVoiceMessages,
    DeltaTime,
    MetaEvents,
    MidiTrack,
    MidiEvent,
    MidiFile,
)
from music21.midi.translate import (
    TimedNoteEvent,
    TranslateWarning,
    channelInstrumentData,
    conductorStream,
    getMetaEvents,
    midiAsciiStringToBinaryString,
    midiEventsToInstrument,
    midiEventsToNote,
    midiFileToStream,
    noteToMidiEvents,
    packetStorageFromSubstreamList,
    prepareStreamForMidi,
    streamHierarchyToMidiTracks,
    streamToMidiFile,
    updatePacketStorageWithChannelInfo,
)
from music21.musicxml import testPrimitive
from music21 import note
from music21 import percussion
from music21 import scale
from music21 import stream
from music21 import tempo
from music21 import tie
from music21 import volume

environLocal = environment.Environment('midi.tests')


class Test(unittest.TestCase):

    # ------------ originally in __init__.py, now base.py --------- #

    def testWriteMThdStr(self):
        '''
        Convert bytes of Ascii midi data to binary midi bytes.
        '''
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

        # mf = MidiFile()
        # mf.open(fp)
        # mf.read()
        # mf.close()

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
        mt = MidiTrack(1)
        # duration, pitch, velocity
        data = [[1024, 60, 90],
                [1024, 50, 70],
                [1024, 51, 120],
                [1024, 62, 80]]
        timeNow = 0
        tLast = 0
        for d, p, v in data:
            dt = DeltaTime(mt)
            dt.time = timeNow - tLast
            # add to track events
            mt.events.append(dt)

            me = MidiEvent(mt)
            me.type = ChannelVoiceMessages.NOTE_ON
            me.channel = 1
            me.pitch = p
            me.velocity = v
            mt.events.append(me)

            # add note off / velocity zero message
            dt = DeltaTime(mt)
            dt.time = d
            # add to track events
            mt.events.append(dt)

            me = MidiEvent(mt)
            me.type = ChannelVoiceMessages.NOTE_ON
            me.channel = 1
            me.pitch = p
            me.velocity = 0
            mt.events.append(me)

            tLast = timeNow + d  # have delta to note off
            timeNow += d  # next time

        # add end of track
        dt = DeltaTime(mt)
        mt.events.append(dt)

        me = MidiEvent(mt)
        me.type = MetaEvents.END_OF_TRACK
        me.channel = 1
        me.data = b''  # must set data to empty bytes
        mt.events.append(me)

        # for e in mt.events:
        #     print(e)

        mf = MidiFile()
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
        mt = MidiTrack(1)

        # (0 - 16383). The pitch value affects all playing notes on the current channel.
        # Values below 8192 decrease the pitch, while values above 8192 increase the pitch.
        # The pitch range may vary from instrument to instrument,
        # but is usually +/-2 semi-tones.
        # pbValues = [0, 5, 10, 15, 20, 25, 30, 35, 40, 50]
        pbValues = [0, 25, 0, 50, 0, 100, 0, 150, 0, 200]
        pbValues += [-x for x in pbValues]

        # duration, pitch, velocity
        data = [[1024, 60, 90]] * 20
        timeNow = 0
        tLast = 0
        for i, e in enumerate(data):
            d, p, v = e

            dt = DeltaTime(mt)
            dt.time = timeNow - tLast
            # add to track events
            mt.events.append(dt)

            me = MidiEvent(mt, type=ChannelVoiceMessages.PITCH_BEND, channel=1)
            # environLocal.printDebug(['creating event:', me, 'pbValues[i]', pbValues[i]])
            me.setPitchBend(pbValues[i])  # set values in cents
            mt.events.append(me)

            dt = DeltaTime(mt)
            dt.time = timeNow - tLast
            # add to track events
            mt.events.append(dt)

            me = MidiEvent(mt, type=ChannelVoiceMessages.NOTE_ON, channel=1)
            me.pitch = p
            me.velocity = v
            mt.events.append(me)

            # add note off / velocity zero message
            dt = DeltaTime(mt)
            dt.time = d
            # add to track events
            mt.events.append(dt)

            me = MidiEvent(mt, type=ChannelVoiceMessages.NOTE_ON, channel=1)
            me.pitch = p
            me.velocity = 0
            mt.events.append(me)

            tLast = timeNow + d  # have delta to note off
            timeNow += d  # next time

        # add end of track
        dt = DeltaTime(mt)
        mt.events.append(dt)

        me = MidiEvent(mt)
        me.type = MetaEvents.END_OF_TRACK
        me.channel = 1
        me.data = b''  # must set data to empty bytes
        mt.events.append(me)

        # try setting different channels
        mt.setChannel(3)

        mf = MidiFile()
        mf.ticksPerQuarterNote = 1024  # cannot use: 10080
        mf.tracks.append(mt)

        fileLikeOpen = io.BytesIO()
        # mf.open('/_scratch/test.mid', 'wb')
        mf.openFileLike(fileLikeOpen)
        mf.write()
        mf.close()

    def testImportWithRunningStatus(self):
        dirLib = common.getSourceFilePath() / 'midi' / 'testPrimitive'
        fp = dirLib / 'test09.mid'
        # a simple file created in athenacl
        # dealing with midi files that use running status compression
        s = converter.parse(fp)
        self.assertEqual(len(s.parts), 2)
        self.assertEqual(len(s.parts[0].recurse().notes), 702)
        self.assertEqual(len(s.parts[1].recurse().notes), 856)

        # for n in s.parts[0].notes:
        #    print(n, n.quarterLength)
        # s.show()

    def testReadPolyphonicKeyPressure(self):
        mt = MidiTrack()
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

        writingFile = MidiFile()
        writingFile.tracks = [mt]
        byteStr = writingFile.writestr()
        readingFile = MidiFile()
        readingFile.readstr(byteStr)

        pressureEventRead = [e for e in readingFile.tracks[0].events
                             if e.type == ChannelVoiceMessages.POLYPHONIC_KEY_PRESSURE][0]
        self.assertEqual(pressureEventRead.parameter1, 60)
        self.assertEqual(pressureEventRead.parameter2, 90)

    def testReadUnknownMetaMessage(self):
        mt = MidiTrack()
        mt.processDataToEvents(b'\x00\xff\x08\x06DUMMY\x00\x00\xff\n\x05Myut\x00'
                               + b'\x00\xffX\x04\x03\x01\x12\x01')
        self.assertEqual(len(mt.events), 6)
        self.assertEqual(mt.events[3].type, MetaEvents.UNKNOWN)

    # ------------ originally in translate.py --------------------- #

    def testMidiAsciiStringToBinaryString(self):
        # noinspection PyListCreation
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

        # noinspection PyListCreation
        midiTrack = []
        midiTrack.append(asciiMidiEventList)
        # midiTrack.append(asciiMidiEventList)
        # midiTrack.append(asciiMidiEventList)

        midiBinStr = midiAsciiStringToBinaryString(tracksEventsList=midiTrack)

        self.assertEqual(midiBinStr,
                         b'MThd' + a2b_hex('000000060001000103c0')
                         + b'MTrk' + a2b_hex('0000000400901f0f'))

    def testNote(self):
        n1 = note.Note('A4')
        n1.quarterLength = 2.0
        eventList = noteToMidiEvents(n1)

        self.assertEqual(len(eventList), 4)
        self.assertIsInstance(eventList[0], DeltaTime)
        self.assertIsInstance(eventList[1], MidiEvent)
        self.assertIsInstance(eventList[2], DeltaTime)
        self.assertIsInstance(eventList[3], MidiEvent)

        # translate eventList back to a note
        n2 = midiEventsToNote(TimedNoteEvent(eventList[0].time, eventList[2].time, eventList[1]))
        self.assertEqual(n2.pitch.nameWithOctave, 'A4')
        self.assertEqual(n2.quarterLength, 2.0)

    def testStripTies(self):
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
                             [ChannelVoiceMessages.NOTE_ON,
                              ChannelVoiceMessages.NOTE_OFF] * 3)

        # Stream with measures
        s.makeMeasures(inPlace=True)
        trk = streamHierarchyToMidiTracks(s)[1]
        mt2noteOnOffEventTypes = [event.type for event in trk.events if event.type in (
            ChannelVoiceMessages.NOTE_ON, ChannelVoiceMessages.NOTE_OFF)]

        self.assertListEqual(mt2noteOnOffEventTypes,
                             [ChannelVoiceMessages.NOTE_ON,
                              ChannelVoiceMessages.NOTE_OFF] * 3)

    def testTimeSignature(self):
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
        # mtAlt = streamHierarchyToMidiTracks(s.getElementsByClass(meter.TimeSignature).stream())[0]
        conductorEvents = repr(mt.events)

        match = r'''[<music21.midi.DeltaTime (empty) track=0>,
        <music21.midi.MidiEvent SET_TEMPO, track=0, data=b'\x07\xa1 '>,
        <music21.midi.DeltaTime (empty) track=0>,
        <music21.midi.MidiEvent TIME_SIGNATURE, track=0, data=b'\x03\x02\x18\x08'>,
        <music21.midi.DeltaTime t=30240, track=0>,
        <music21.midi.MidiEvent TIME_SIGNATURE, track=0, data=b'\x05\x02\x18\x08'>,
        <music21.midi.DeltaTime t=50400, track=0>,
        <music21.midi.MidiEvent TIME_SIGNATURE, track=0, data=b'\x02\x02\x18\x08'>,
        <music21.midi.DeltaTime t=10080, track=0>,
        <music21.midi.MidiEvent END_OF_TRACK, track=0, data=b''>]'''

        self.assertTrue(common.whitespaceEqual(conductorEvents, match), conductorEvents)

    def testKeySignature(self):
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
        s = corpus.parse('bach/bwv103.6')

        # get just the soprano part
        soprano = s.parts['#soprano']
        mts = streamHierarchyToMidiTracks(soprano)[1]  # get one

        # first note-on is not delayed, even w anacrusis
        match = '''
        [<music21.midi.DeltaTime (empty) track=1>,
         <music21.midi.MidiEvent SEQUENCE_TRACK_NAME, track=1, data=b'Soprano'>,
         <music21.midi.DeltaTime (empty) track=1>,
         <music21.midi.MidiEvent PITCH_BEND, track=1, channel=1, parameter1=0, parameter2=64>,
         <music21.midi.DeltaTime (empty) track=1>]'''

        self.maxDiff = None
        found = str(mts.events[:5])
        self.assertTrue(common.whitespaceEqual(found, match), found)

        # first note-on is not delayed, even w anacrusis
        match = '''
        [<music21.midi.DeltaTime (empty) track=1>,
        <music21.midi.MidiEvent SEQUENCE_TRACK_NAME, track=1, data=b'Alto'>,
        <music21.midi.DeltaTime (empty) track=1>,
        <music21.midi.MidiEvent PITCH_BEND, track=1, channel=1, parameter1=0, parameter2=64>,
        <music21.midi.DeltaTime (empty) track=1>,
        <music21.midi.MidiEvent PROGRAM_CHANGE, track=1, channel=1, data=0>,
        <music21.midi.DeltaTime (empty) track=1>,
        <music21.midi.MidiEvent NOTE_ON, track=1, channel=1, pitch=62, velocity=90>]'''

        alto = s.parts['#alto']
        mta = streamHierarchyToMidiTracks(alto)[1]

        found = str(mta.events[:8])
        self.assertTrue(common.whitespaceEqual(found, match), found)

        # try streams to midi tracks
        # get just the soprano part
        soprano = s.parts['#soprano']
        mtList = streamHierarchyToMidiTracks(soprano)
        self.assertEqual(len(mtList), 2)

        # it's the same as before
        match = '''[<music21.midi.DeltaTime (empty) track=1>,
        <music21.midi.MidiEvent SEQUENCE_TRACK_NAME, track=1, data=b'Soprano'>,
        <music21.midi.DeltaTime (empty) track=1>,
        <music21.midi.MidiEvent PITCH_BEND, track=1, channel=1, parameter1=0, parameter2=64>,
        <music21.midi.DeltaTime (empty) track=1>,
        <music21.midi.MidiEvent PROGRAM_CHANGE, track=1, channel=1, data=0>,
        <music21.midi.DeltaTime (empty) track=1>,
        <music21.midi.MidiEvent LYRIC, track=1, data=b'1. Was\\nzu\\n2. Ich\\nwas'>,
        <music21.midi.DeltaTime (empty) track=1>,
        <music21.midi.MidiEvent NOTE_ON, track=1, channel=1, pitch=66, velocity=90>,
        <music21.midi.DeltaTime t=5040, track=1>,
        <music21.midi.MidiEvent NOTE_OFF, track=1, channel=1, pitch=66, velocity=0>]'''
        found = str(mtList[1].events[:12])
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

        streamHierarchyToMidiTracks(s)
        # p1.show()
        # s.show('midi')

    def testMidiProgramChangeB(self):
        iList = [instrument.Harpsichord,
                 instrument.Clavichord, instrument.Accordion,
                 instrument.Celesta, instrument.Contrabass, instrument.Viola,
                 instrument.Harp, instrument.ElectricGuitar, instrument.Ukulele,
                 instrument.Banjo, instrument.Piccolo, instrument.AltoSaxophone,
                 instrument.Trumpet]

        sc = scale.MinorScale()
        # something strange with PyCharm type checker here.  Thinks it is off one argument.
        # noinspection PyTypeChecker
        pitches = sc.getPitches('c2', 'c5')
        random.shuffle(pitches)

        s = stream.Stream()
        for i in range(30):
            n = note.Note(pitches[i % len(pitches)])
            n.quarterLength = 0.5
            inst = iList[i % len(iList)]()  # call to create instance
            s.append(inst)
            s.append(n)

        streamHierarchyToMidiTracks(s)

        # s.show('midi')

    def testOverlappedEventsA(self):
        s = corpus.parse('bwv66.6')
        sFlat = s.flatten()
        mtList = streamHierarchyToMidiTracks(sFlat)
        self.assertEqual(len(mtList), 2)

        # it's the same as before
        match = '''[<music21.midi.MidiEvent NOTE_ON, track=1, channel=1, pitch=66, velocity=90>,
        <music21.midi.DeltaTime (empty) track=1>,
        <music21.midi.MidiEvent NOTE_ON, track=1, channel=1, pitch=61, velocity=90>,
        <music21.midi.DeltaTime (empty) track=1>,
        <music21.midi.MidiEvent NOTE_ON, track=1, channel=1, pitch=58, velocity=90>,
        <music21.midi.DeltaTime (empty) track=1>,
        <music21.midi.MidiEvent NOTE_ON, track=1, channel=1, pitch=54, velocity=90>,
        <music21.midi.DeltaTime t=10080, track=1>,
        <music21.midi.MidiEvent NOTE_OFF, track=1, channel=1, pitch=66, velocity=0>,
        <music21.midi.DeltaTime (empty) track=1>,
        <music21.midi.MidiEvent NOTE_OFF, track=1, channel=1, pitch=61, velocity=0>,
        <music21.midi.DeltaTime (empty) track=1>,
        <music21.midi.MidiEvent NOTE_OFF, track=1, channel=1, pitch=58, velocity=0>,
        <music21.midi.DeltaTime (empty) track=1>,
        <music21.midi.MidiEvent NOTE_OFF, track=1, channel=1, pitch=54, velocity=0>,
        <music21.midi.DeltaTime t=10080, track=1>,
        <music21.midi.MidiEvent END_OF_TRACK, track=1, data=b''>]'''

        results = str(mtList[1].events[-17:])
        self.assertTrue(common.whitespaceEqual(results, match), results)

    def testOverlappedEventsB(self):
        sc = scale.MajorScale()
        # something strange with PyCharm type checker here.  Thinks it is off one argument.
        # noinspection PyTypeChecker
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

        streamHierarchyToMidiTracks(s)

        # s.plot('pianoroll')
        # s.show('midi')

    def testOverlappedEventsC(self):
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

        streamHierarchyToMidiTracks(s)

        # s.show('midi')

    def testExternalMidiProgramChangeB(self):
        iList = [instrument.Harpsichord, instrument.Clavichord, instrument.Accordion,
                 instrument.Celesta, instrument.Contrabass, instrument.Viola,
                 instrument.Harp, instrument.ElectricGuitar, instrument.Ukulele,
                 instrument.Banjo, instrument.Piccolo, instrument.AltoSaxophone,
                 instrument.Trumpet, instrument.Clarinet, instrument.Flute,
                 instrument.Violin, instrument.Soprano, instrument.Oboe,
                 instrument.Tuba, instrument.Sitar, instrument.Ocarina,
                 instrument.Piano]

        sc = scale.MajorScale()
        # something strange with PyCharm type checker here.  Thinks it is off one argument.
        # noinspection PyTypeChecker
        pitches = sc.getPitches('c2', 'c5')
        # random.shuffle(pitches)

        s = stream.Stream()
        for i, p in enumerate(pitches):
            n = note.Note(p)
            n.quarterLength = 1.5
            inst = iList[i]()  # call to create instance
            s.append(inst)
            s.append(n)

        streamHierarchyToMidiTracks(s)
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
        streamHierarchyToMidiTracks(s)

    def testMicrotonalOutputB(self):
        p1 = stream.Part()
        p1.append(note.Note('c4', type='whole'))
        p1.append(note.Note('c~4', type='whole'))
        p1.append(note.Note('c#4', type='whole'))
        p1.append(note.Note('c#~4', type='whole'))
        p1.append(note.Note('d4', type='whole'))

        # mts = streamHierarchyToMidiTracks(s)
        p2 = stream.Part()
        p2.insert(0, note.Note('g2', quarterLength=20))

        # order here matters: this needs to be fixed
        s = stream.Score()
        s.insert(0, p1)
        s.insert(0, p2)

        mts = streamHierarchyToMidiTracks(s)
        self.assertEqual(mts[1].getChannels(), [1])
        self.assertEqual(mts[2].getChannels(), [1, 2])
        # print(mts)
        # s.show('midi')

        # recreate with different order
        s = stream.Score()
        s.insert(0, p2)
        s.insert(0, p1)

        mts = streamHierarchyToMidiTracks(s)
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
        mts = streamHierarchyToMidiTracks(s)
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
        s = corpus.parse('bwv66.6')
        p1 = s.parts[0]
        p2 = copy.deepcopy(p1)
        halfSharp = interval.Interval(0.5)  # half sharp
        p2.transpose(halfSharp, inPlace=True, classFilterList=('Note', 'Chord'))
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
        s = corpus.parse('bwv66.6')
        p1 = s.parts[0]
        p1.remove(p1.getElementsByClass(instrument.Instrument).first())
        p2 = copy.deepcopy(p1)
        p3 = copy.deepcopy(p1)

        t1 = interval.Interval(12.5)  # a sharp p4
        t2 = interval.Interval(-7.25)  # a sharp p4
        p2.transpose(t1, inPlace=True, classFilterList=(note.Note, chord.Chord))
        p3.transpose(t2, inPlace=True, classFilterList=(note.Note, chord.Chord))
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
        dirLib = common.getSourceFilePath() / 'midi' / 'testPrimitive'
        # a simple file created in athenacl
        fp = dirLib / 'test10.mid'
        s = converter.parse(fp)
        mmStream = s.flatten().getElementsByClass(tempo.MetronomeMark)
        self.assertEqual(len(mmStream), 4)
        self.assertEqual(mmStream[0].number, 120.0)
        self.assertEqual(mmStream[1].number, 110.0)
        self.assertEqual(mmStream[2].number, 90.0)
        self.assertEqual(mmStream[3].number, 60.0)

        fp = dirLib / 'test06.mid'
        s = converter.parse(fp)
        mmStream = s.flatten().getElementsByClass(tempo.MetronomeMark)
        self.assertEqual(len(mmStream), 1)
        self.assertEqual(mmStream[0].number, 120.0)

        fp = dirLib / 'test07.mid'
        s = converter.parse(fp)
        mmStream = s.flatten().getElementsByClass(tempo.MetronomeMark)
        self.assertEqual(len(mmStream), 1)
        self.assertEqual(mmStream[0].number, 180.0)

    def testMidiTempoImportB(self):
        dirLib = common.getSourceFilePath() / 'midi' / 'testPrimitive'
        # a file with three tracks and one conductor track with four tempo marks
        fp = dirLib / 'test11.mid'
        s = converter.parse(fp)
        self.assertEqual(len(s.parts), 3)
        # metronome marks propagate to every staff, but are hidden on subsequent staffs
        self.assertEqual(
            [mm.numberImplicit for mm in s.parts[0][tempo.MetronomeMark]],
            [False, False, False, False]
        )
        self.assertEqual(
            [mm.numberImplicit for mm in s.parts[1][tempo.MetronomeMark]],
            [True, True, True, True]
        )
        self.assertEqual(
            [mm.numberImplicit for mm in s.parts[2][tempo.MetronomeMark]],
            [True, True, True, True]
        )

    def testMidiImportMeter(self):
        fp = common.getSourceFilePath() / 'midi' / 'testPrimitive' / 'test17.mid'
        s = converter.parse(fp)
        for p in s.parts:
            m = p.getElementsByClass(stream.Measure).first()
            ts = m.timeSignature
            self.assertEqual(ts.ratioString, '3/4')
            self.assertIn(ts, m)

    def testMidiImportImplicitMeter(self):
        fp = common.getSourceFilePath() / 'midi' / 'testPrimitive' / 'test10.mid'

        # Not the normal way to read a midi file, but we're altering it
        mf = MidiFile()
        mf.open(fp)
        mf.read()
        mf.close()

        # Simulate a file with a conductor track
        new_track = MidiTrack()
        # Include some events, like part name, but NOT meter
        new_track.events = mf.tracks[0].events[:4]
        mf.tracks.insert(0, new_track)

        s = midiFileToStream(mf)
        for p in s.parts:
            m = p.getElementsByClass(stream.Measure).first()
            ts = m.timeSignature
            self.assertEqual(ts.ratioString, '4/4')
            self.assertIn(ts, m)

    def testMidiExportConductorA(self):
        '''
        Export conductor data to MIDI conductor track.
        '''
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
        '''
        120 bpm and 4/4 are supplied by default.
        '''
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
        '''
        The conductor only gets the first element at an offset.
        '''
        s = stream.Stream()
        p1 = converter.parse('tinynotation: c1')
        p2 = converter.parse('tinynotation: d2 d2')
        p1.insert(0, tempo.MetronomeMark(number=44))
        p2.insert(0, tempo.MetronomeMark(number=144))
        p2.insert(2, key.KeySignature(-5))
        s.insert(0, p1)
        s.insert(0, p2)

        conductor = conductorStream(s)
        tempos = conductor.getElementsByClass(tempo.MetronomeMark)
        keySignatures = conductor.getElementsByClass(key.KeySignature)
        self.assertEqual(len(tempos), 1)
        self.assertEqual(tempos[0].number, 44)
        self.assertEqual(len(keySignatures), 1)

    def testMidiExportConductorF(self):
        '''
        Multiple meter changes
        '''
        source_dir = common.getSourceFilePath() / 'musicxml' / 'lilypondTestSuite'
        s = converter.parse(source_dir / '11a-TimeSignatures.xml')
        self.assertEqual(len(s['TimeSignature']), 11)

        mf = streamToMidiFile(s)
        conductor = mf.tracks[0]
        meter_events = [
            e for e in conductor.events if e.type is MetaEvents.TIME_SIGNATURE]
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

    def testMidiExportVelocityB(self) -> None:
        s1: stream.Stream = stream.Stream()
        shift = [0, 6, 12]
        amps = [(x / 10. + 0.4) for x in range(6)]
        amps = amps + list(reversed(amps))

        qlList = [1.5] * 6 + [1] * 8 + [2] * 6 + [1.5] * 8 + [1] * 4

        c: note.Rest|chord.Chord
        for j, ql in enumerate(qlList):
            if random.random() > 0.6:
                c = note.Rest()
            else:
                ch = chord.Chord(['c3', 'd-4', 'g5'])
                vChord: list[volume.Volume] = []
                for i, unused_cSub in enumerate(ch):
                    v = volume.Volume()
                    v.velocityScalar = amps[(j + shift[i]) % len(amps)]
                    v.velocityIsRelative = False
                    vChord.append(v)
                ch.setVolumes(vChord)
                c = ch
            c.duration.quarterLength = ql
            s1.append(c)

        random.shuffle(qlList)
        random.shuffle(amps)

        s2: stream.Stream[note.Note] = stream.Stream()
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
        self.assertIn('SET_TEMPO', repr(mts[0].events))
        mtsRepr = repr(mts[1].events) + repr(mts[2].events)
        self.assertGreater(mtsRepr.count('velocity=51'), 2)
        self.assertGreater(mtsRepr.count('velocity=102'), 2)
        # s.show('midi')

    def testImportTruncationProblemA(self):
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
        self.assertEqual(len(s[chord.Chord]), 3)
        self.assertEqual(len(s.parts.first().measure(3).voices), 2)

    def testImportChordsA(self):
        dirLib = common.getSourceFilePath() / 'midi' / 'testPrimitive'
        fp = dirLib / 'test05.mid'

        # a simple file created in athenacl
        s = converter.parse(fp)
        # s.show('t')
        self.assertEqual(len(s[chord.Chord]), 5)

    def testMidiEventsImported(self):
        self.maxDiff = None

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
                 (10080, 'END_OF_TRACK', None),
                 (0, 'SEQUENCE_TRACK_NAME', None),  # Music track
                 (0, 'PITCH_BEND', None),
                 (0, 'PROGRAM_CHANGE', None),
                 (0, 'NOTE_ON', 69),
                 (10080, 'NOTE_OFF', 69),
                 (0, 'NOTE_ON', 71),
                 (10080, 'NOTE_OFF', 71),
                 (0, 'NOTE_ON', 73),
                 (10080, 'NOTE_OFF', 73),
                 (0, 'NOTE_ON', 69),
                 (10080, 'NOTE_OFF', 69),
                 (0, 'NOTE_ON', 68),
                 (10080, 'NOTE_OFF', 68),
                 (0, 'NOTE_ON', 66),
                 (10080, 'NOTE_OFF', 66),
                 (0, 'NOTE_ON', 68),
                 (20160, 'NOTE_OFF', 68),
                 (0, 'NOTE_ON', 66),
                 (20160, 'NOTE_OFF', 66),
                 (0, 'NOTE_ON', 66),
                 (10080, 'NOTE_OFF', 66),
                 (0, 'NOTE_ON', 66),
                 (20160, 'NOTE_OFF', 66),
                 (0, 'NOTE_ON', 66),
                 (5040, 'NOTE_OFF', 66),
                 (0, 'NOTE_ON', 65),
                 (5040, 'NOTE_OFF', 65),
                 (0, 'NOTE_ON', 66),
                 (10080, 'NOTE_OFF', 66),
                 (10080, 'END_OF_TRACK', None)]
        procCompare(mf, match)

    def testMidiInstrumentToStream(self):
        s = converter.parse(testPrimitive.transposing01)
        mf = streamToMidiFile(s)
        out = midiFileToStream(mf)
        first_instrument = out.parts.first().measure(1).getElementsByClass(
            instrument.Instrument).first()
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
        dirLib = common.getSourceFilePath() / 'midi' / 'testPrimitive'
        fp = dirLib / 'test16.mid'
        s = converter.parse(fp)
        self.assertEqual(len(s.parts.first().measure(1).voices), 2)
        els = s.parts.first().flatten().getElementsByOffset(0.5)
        self.assertSequenceEqual([e.duration.quarterLength for e in els], [0, 1])

    def testRepeatsExpanded(self):
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
        event = MidiEvent()
        event.data = bytes('Piccolo\x00', 'utf-8')
        i = midiEventsToInstrument(event)
        self.assertIsInstance(i, instrument.Piccolo)

        # test that nothing was broken.
        event.data = bytes('Flute', 'utf-8')
        i = midiEventsToInstrument(event)
        self.assertIsInstance(i, instrument.Flute)

    def testLousyInstrumentData(self):
        lousyNames = ('    ', 'Instrument 20', 'Instrument', 'Inst 2', 'instrument')
        for name in lousyNames:
            with self.subTest(name=name):
                event = MidiEvent()
                event.data = bytes(name, 'utf-8')
                event.type = MetaEvents.INSTRUMENT_NAME
                i = midiEventsToInstrument(event)
                self.assertIsNone(i.instrumentName)

        # lousy program change
        # https://github.com/cuthbertLab/music21/issues/988
        event = MidiEvent()
        event.data = 0
        event.channel = 10
        event.type = ChannelVoiceMessages.PROGRAM_CHANGE

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
        fp = common.getSourceFilePath() / 'midi' / 'testPrimitive' / 'test17.mid'
        inn = converter.parse(fp)

        self.assertEqual(
            len(inn.parts[1].measure(3).voices.last().getElementsByClass(note.Rest)), 1)

    def testRestsMadeInMeasures(self):
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
        event1 = MidiEvent()
        event1.data = 0
        event1.channel = 1
        event1.type = ChannelVoiceMessages.PROGRAM_CHANGE

        event2 = MidiEvent()
        # This will normalize to an instrument.Soprano, but we don't want
        # the default midiProgram, we want 0.
        event2.data = b'Soprano'
        event2.channel = 2
        event2.type = MetaEvents.SEQUENCE_TRACK_NAME

        DUMMY_DELTA_TIME = 0
        meta_event_pairs = getMetaEvents([(DUMMY_DELTA_TIME, event1), (DUMMY_DELTA_TIME, event2)])

        # Second element of the tuple is the instrument instance
        me0 = meta_event_pairs[0][1]
        assert isinstance(me0, instrument.Instrument)
        me1 = meta_event_pairs[0][1]
        assert isinstance(me1, instrument.Instrument)

        self.assertEqual(me0.midiProgram, 0)
        self.assertEqual(me1.midiProgram, 0)

        # Remove the initial PROGRAM_CHANGE and get a default midiProgram
        meta_event_pairs = getMetaEvents([(DUMMY_DELTA_TIME, event2)])
        me0 = meta_event_pairs[0][1]
        assert isinstance(me0, instrument.Instrument)
        self.assertEqual(me0.midiProgram, 53)

    def testExportUnpitched(self):
        m = stream.Measure([
            instrument.BassDrum(),
            note.Unpitched(),
            percussion.PercussionChord([note.Unpitched(), note.Unpitched()]),
        ])
        tracks = streamHierarchyToMidiTracks(m)
        bass_drum_track = tracks[1]

        self.assertTrue({ev.channel for ev in bass_drum_track.events}, {10})
        note_ons = [
            ev for ev in bass_drum_track.events
            if ev.type is ChannelVoiceMessages.NOTE_ON
        ]
        self.assertEqual(len(note_ons), 3)
        self.assertEqual({ev.pitch for ev in note_ons}, {35})

        # Replace the BassDrum with a vague instrument (lossy import)
        m.pop(0)
        m.insert(0, instrument.Instrument())

        tracks = streamHierarchyToMidiTracks(m)
        drum_track = tracks[1]

        self.assertTrue({ev.channel for ev in drum_track.events}, {10})
        note_ons = [
            ev for ev in drum_track.events if ev.type is ChannelVoiceMessages.NOTE_ON]
        self.assertEqual(len(note_ons), 3)
        self.assertEqual({ev.pitch for ev in note_ons}, {60})  # fallback

        # Change the stored instrument: affects that note only
        m.notes.first().storedInstrument = instrument.Agogo()

        tracks = streamHierarchyToMidiTracks(m)
        mixed_track = tracks[1]

        self.assertTrue({ev.channel for ev in mixed_track.events}, {10})
        note_ons = [
            ev for ev in mixed_track.events if ev.type is ChannelVoiceMessages.NOTE_ON]
        self.assertEqual(len(note_ons), 3)
        self.assertEqual([ev.pitch for ev in note_ons], [67, 60, 60])

    def testMidiImportLyrics(self):
        lyricFactZh = ['明', '山', '涌', '水', '郁', '郁', '葱', '', '葱',
                       '钟', '灵', '毓', '秀', '海', '天', '', '东',
                       '济', '济', '多', '士', '四', '方', '所', '', '崇',
                       '早', '', '育', '', '文', '明', '', '种']
        lyricFactKo = ['빛', '날', '세', '라', '영', '웅', '열', '', '사',
                       '만', '세', '불', '망', '하', '실', '', '이',
                       '옛', '적', '이', '나', '지', '금', '이', '', '나',
                       '항', '상', '앙', '모', '합', '니', '', '다']
        testCases = [
            ('test18.mid', 'utf-8', lyricFactZh),
            ('test19.mid', 'gbk', lyricFactZh),
            ('test20.mid', 'utf-8', lyricFactKo),
            ('test21.mid', 'euc-kr', lyricFactKo),
        ]

        for filename, encoding, lyricFact in testCases:
            fp = common.getSourceFilePath() / 'midi' / 'testPrimitive' / filename
            s = converter.parse(fp, encoding=encoding)
            for (n, l) in zip(s.flatten().notes, lyricFact):
                self.assertEqual(n.lyric, l)

    def testMidiExportLyrics(self):
        lyricEn = 'cat'  # ascii characters should be supported by every encoding
        lyricZh = '明'
        lyricKo = '빛'

        testCases = [
            ('utf-8', lyricEn),
            ('gbk', lyricEn),
            ('euc-kr', lyricEn),
            ('utf-8', lyricZh),
            ('gbk', lyricZh),
            ('utf-8', lyricKo),
            ('euc-kr', lyricKo),
        ]
        for encoding, lyric in testCases:
            with self.subTest(encoding=encoding, lyric=lyric):
                s = stream.Score()
                p1 = stream.Part()
                p2 = stream.Part()

                n1 = note.Note('c4')
                n1.lyric = lyric
                n2 = note.Note('g4')
                n2.lyric = lyric

                p1.append(n1)
                p2.append(n2)

                s.append(p1)
                s.append(p2)

                b = converter.toData(s, fmt='midi', encoding=encoding)
                self.assertIsInstance(b, bytes)

                m = converter.parseData(b, fmt='midi', encoding=encoding)
                for n in m.flatten().notes:
                    self.assertEqual(n.lyric, lyric)


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    import music21
    music21.mainTest(Test)


