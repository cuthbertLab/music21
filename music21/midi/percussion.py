# ------------------------------------------------------------------------------
# Name:         midi/percussion.py
# Purpose:      music21 classes for representing pitches
#
# Authors:      Michael Scott Asato Cuthbert
#               Ben Houge
#
# Copyright:    Copyright © 2012-2026 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
from __future__ import annotations

import unittest

from music21 import pitch
from music21 import exceptions21
from music21 import instrument


class MIDIPercussionException(exceptions21.Music21Exception):
    pass


class PercussionMapper:
    '''
    PercussionMapper provides tools to convert between 0-indexed MIDI pitches
    and music21 instruments, based on the official General MIDI Level 1 Percussion Key Map.
    This mapping is conventionally applied to MIDI channel 10;
    see https://midi.org/general-midi-level-1 for more info.

    Give me the instrument that corresponds to MIDI note 58!

    >>> pm = midi.percussion.PercussionMapper()
    >>> pm.reverseInstrumentMapping[58]
    <class 'music21.instrument.Vibraslap'>

    That's right, vibraslap.

    But you're better off using the midiPitchToInstrument() method below!
    '''

    i = instrument
    reverseInstrumentMapping = {35: i.BassDrum,  # Acoustic Bass Drum
                                36: i.BassDrum,  # Bass Drum 1
                                37: i.SnareDrum,  # Side Stick
                                38: i.SnareDrum,  # Acoustic Snare
                                40: i.SnareDrum,  # Electric Snare
                                41: i.TomTom,  # Low Floor Tom
                                42: i.HiHatCymbal,  # Closed Hi Hat
                                43: i.TomTom,  # High Floor Tom
                                44: i.HiHatCymbal,  # Pedal Hi-Hat
                                45: i.TomTom,  # Low Tom
                                46: i.HiHatCymbal,  # Open Hi-Hat
                                47: i.TomTom,  # Low-Mid Tom
                                48: i.TomTom,  # Hi-Mid Tom
                                49: i.CrashCymbals,  # Crash Cymbal 1
                                50: i.TomTom,  # High Tom
                                51: i.RideCymbal,  # Ride Cymbal 1
                                52: i.ChineseCymbal,
                                53: i.RideCymbal,  # Ride Bell
                                54: i.Tambourine,
                                55: i.SplashCymbal,
                                56: i.Cowbell,
                                57: i.CrashCymbals,  # Crash Cymbal 2
                                58: i.Vibraslap,
                                59: i.RideCymbal,  # Ride Cymbal 2
                                60: i.BongoDrums,  # Hi Bongo
                                61: i.BongoDrums,  # Low Bongo
                                62: i.CongaDrum,  # Mute Hi Conga
                                63: i.CongaDrum,  # Open Hi Conga
                                64: i.CongaDrum,  # Low Conga
                                65: i.Timbales,  # High Timbale
                                66: i.Timbales,  # Low Timbale
                                67: i.Agogo,  # High Agogo
                                68: i.Agogo,  # Low Agogo
                                69: i.Cabasa,
                                70: i.Maracas,
                                71: i.Whistle,  # Short Whistle
                                72: i.Whistle,  # Long Whistle
                                73: i.Guiro,  # Short Guiro
                                74: i.Guiro,  # Long Guiro
                                75: i.Claves,
                                76: i.Woodblock,  # Hi Wood Block
                                77: i.Woodblock,  # Low Wood Block
                                78: i.Cuica,  # Mute Cuica
                                79: i.Cuica,  # Open Cuica
                                80: i.Triangle,  # Mute Triangle
                                81: i.Triangle,  # Open Triangle
                                # GM Level 2
                                83: i.SleighBells,  # Jingle Bell
                                85: i.Castanets,
                                86: i.Surdo,  # Mute Surdo
                                87: i.Surdo,  # Open Surdo
                                }

    # sounds in GM Level 1 or GM Level 2 that are not instruments
    namedSoundMapping = {27: 'High Q',
                         28: 'Slap',
                         29: 'Scratch Push',
                         30: 'Scratch Pull',
                         31: 'Sticks',
                         32: 'Square Click',
                         33: 'Metronome Click',
                         34: 'Metronome Bell',
                         39: 'Hand Clap',
                         82: 'Shaker',
                         84: 'Bell Tree',
                         }

    # MIDI percussion mappings from https://midi.org/general-midi-level-1 download at
    # https://drive.google.com/file/d/1TTM2HI2JAp_XiTJYEJ8gPNvuJpIjJiTP/view?pli=1
    # formerly at:
    # https://www.midi.org/specifications/item/gm-level-1-sound-set

    def midiPitchToInstrument(
        self,
        midiPitch: int|pitch.Pitch,
        *,
        raiseIfUnmapped: bool = True,
    ) -> instrument.MidiPercussionMapMixin:
        '''
        Takes a pitch.Pitch object or int ranging from 0-127 and returns
        the corresponding instrument in the GM Percussion Map.

        >>> pm = midi.percussion.PercussionMapper()
        >>> cowPitch = pitch.Pitch(56)
        >>> cowbell = pm.midiPitchToInstrument(cowPitch)
        >>> cowbell
        <music21.instrument.Cowbell 'Cowbell'>

        Or it can just take an integer (representing MIDI note) for the pitch instead:

        >>> moreCowbell = pm.midiPitchToInstrument(56)
        >>> moreCowbell
        <music21.instrument.Cowbell 'Cowbell'>

        The GM Percussion lists go from 27 to 87;
        pitches outside this range raise an exception.

        >>> lowPitch = pitch.Pitch('B-0')
        >>> pm.midiPitchToInstrument(lowPitch)
        Traceback (most recent call last):
        music21.midi.percussion.MIDIPercussionException: 22 does not map to a valid instrument!

        Some music21 Instruments have more than one MidiPitch.  In this case you'll
        get the same Instrument object but with a different modifier

        >>> acousticBassDrumPitch = pitch.Pitch(35)
        >>> acousticBDInstrument = pm.midiPitchToInstrument(acousticBassDrumPitch)
        >>> acousticBDInstrument
        <music21.instrument.BassDrum 'Bass Drum' acoustic>
        >>> acousticBDInstrument.modifier
        'acoustic'

        >>> oneBassDrumPitch = pitch.Pitch(36)
        >>> oneBDInstrument = pm.midiPitchToInstrument(oneBassDrumPitch)
        >>> oneBDInstrument
        <music21.instrument.BassDrum 'Bass Drum' midi-1>
        >>> oneBDInstrument.modifier
        'midi-1'

        Sounds in the map that are not instruments give an UnpitchedPercussion
        object with a name:

        >>> clap = pm.midiPitchToInstrument(39)
        >>> clap
        <music21.instrument.UnpitchedPercussion 'Hand Clap'>
        >>> clap.percMapPitch
        39

        With `raiseIfUnmapped=False`, any other number gives an UnpitchedPercussion
        object that keeps the number:

        >>> other = pm.midiPitchToInstrument(22, raiseIfUnmapped=False)
        >>> other
        <music21.instrument.UnpitchedPercussion 'Percussion'>
        >>> other.percMapPitch
        22

        * Changed in v11: named sounds that are not instruments; `raiseIfUnmapped`.
        '''

        if isinstance(midiPitch, int):
            midiNumber = midiPitch
        else:
            midiNumber = midiPitch.midi
        if midiNumber not in self.reverseInstrumentMapping:
            if midiNumber in self.namedSoundMapping or not raiseIfUnmapped:
                generic = instrument.UnpitchedPercussion()
                generic.percMapPitch = midiNumber
                if midiNumber in self.namedSoundMapping:
                    generic.instrumentName = self.namedSoundMapping[midiNumber]
                return generic
            raise MIDIPercussionException(f'{midiNumber!r} does not map to a valid instrument!')
        midiInstrument = self.reverseInstrumentMapping[midiNumber]

        midiInstrumentObject = midiInstrument()
        if midiNumber in midiInstrumentObject._percMapPitchToModifier:
            midiInstrumentObject.modifier = midiInstrumentObject._percMapPitchToModifier[
                midiNumber]
        midiInstrumentObject.percMapPitch = midiNumber

        return midiInstrumentObject

    def midiInstrumentToPitch(self, midiInstrument: instrument.Instrument) -> pitch.Pitch:
        '''
        Takes an instrument.Instrument object and returns a pitch object
        with the corresponding 1-indexed MIDI note, according to the GM Percussion Map.

        >>> pm = midi.percussion.PercussionMapper()
        >>> myCow = instrument.Cowbell()
        >>> cowPitch = pm.midiInstrumentToPitch(myCow)
        >>> cowPitch.midi
        56

        Note that cowPitch is an actual pitch.Pitch object
        even though it's meaningless!

        >>> cowPitch
        <music21.pitch.Pitch G#3>

        If the instrument does not have an equivalent in the GM Percussion Map,
        return an Exception:

        >>> myBagpipes = instrument.Bagpipes()
        >>> pipePitch = pm.midiInstrumentToPitch(myBagpipes)
        Traceback (most recent call last):
        music21.midi.percussion.MIDIPercussionException: <music21.instrument.Bagpipes 'Bagpipes'>
            is not in the GM Percussion Map!
        '''
        if (not isinstance(midiInstrument, instrument.MidiPercussionMapMixin)
                or midiInstrument.percMapPitch is None):
            raise MIDIPercussionException(f'{midiInstrument!r} is not in the GM Percussion Map!')
        midiPitch = midiInstrument.percMapPitch
        pitchObject = pitch.Pitch()
        pitchObject.midi = midiPitch
        return pitchObject

    _DOC_ORDER = [midiInstrumentToPitch, midiPitchToInstrument]


class Test(unittest.TestCase):

    def testCopyAndDeepcopy(self) -> None:
        from music21.test.commonTest import testCopyAll
        testCopyAll(self, globals())

    def testRoundTrip(self) -> None:
        pm = PercussionMapper()
        for midiNumber in range(27, 88):
            inst = pm.midiPitchToInstrument(midiNumber, raiseIfUnmapped=False)
            self.assertEqual(pm.midiInstrumentToPitch(inst).midi, midiNumber, inst)
            self.assertNotEqual(inst.instrumentName, 'Percussion', midiNumber)

    def testModifiers(self) -> None:
        pm = PercussionMapper()
        for midiNumber, cls, modifier in [
            (51, instrument.RideCymbal, 'midi-1'),
            (53, instrument.RideCymbal, 'bell'),
            (55, instrument.SplashCymbal, None),
            (57, instrument.CrashCymbals, 'midi-2'),
            (68, instrument.Agogo, 'low'),
            (72, instrument.Whistle, 'long'),
            (83, instrument.SleighBells, None),
            (85, instrument.Castanets, None),
        ]:
            inst = pm.midiPitchToInstrument(midiNumber)
            self.assertIsInstance(inst, cls)
            self.assertEqual(inst.modifier, modifier)

        for midiNumber, cls in [
            (52, instrument.ChineseCymbal),
            (69, instrument.Cabasa),
            (73, instrument.Guiro),
            (75, instrument.Claves),
            (78, instrument.Cuica),
            (86, instrument.Surdo),
        ]:
            self.assertIsInstance(pm.midiPitchToInstrument(midiNumber), cls)
        self.assertEqual(pm.midiPitchToInstrument(74).modifier, 'long')
        cuica = pm.midiPitchToInstrument(78)
        assert isinstance(cuica, instrument.Cuica)
        self.assertTrue(cuica.muted)
        surdo = pm.midiPitchToInstrument(87)
        assert isinstance(surdo, instrument.Surdo)
        self.assertFalse(surdo.muted)

        bd = instrument.BassDrum()
        bd.modifier = '1'
        self.assertEqual(bd.modifier, 'midi-1')
        self.assertEqual(bd.percMapPitch, 36)


# ------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [PercussionMapper]


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)

