# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         midi/percussion.py
# Purpose:      music21 classes for representing pitches
#
# Authors:      Michael Scott Cuthbert
#               Ben Houge
#
# Copyright:    Copyright © 2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------

from music21 import pitch
from music21 import exceptions21
from music21 import instrument

import unittest
import copy

class MIDIPercussionException(exceptions21.Music21Exception):
    pass

class PercussionMapper(object):
    '''
    PercussionMapper provides tools to convert between MIDI notes and music21 instruments, 
    based on the official General MIDI Level 1 Percussion Key Map.
    This mapping is conventionally applied to MIDI channel 10;
    see http://www.midi.org/techspecs/gm1sound.php for more info.
    
    Give me the instrument that corresponds to MIDI note 58!
    
    
    >>> pm = midi.percussion.PercussionMapper()
    >>> pm.reverseInstrumentMapping[58]
    <class 'music21.instrument.Vibraslap'>
    
    That's right, vibraslap.

    But you're better off using the midiPitchToInstrument() method below!
    
    '''
    
    i = instrument
    reverseInstrumentMapping = {35: i.BassDrum, #Acoustic Bass Drum
                                36: i.BassDrum, #Bass Drum 1
                                37: i.SnareDrum, #Side Stick
                                38: i.SnareDrum, #Acoustic Snare
                                #39: i.Hand Clap,
                                40: i.SnareDrum, #Electric Snare
                                41: i.TomTom, #Low Floor Tom
                                42: i.HiHatCymbal, #Closed Hi Hat
                                43: i.TomTom, #High Floor Tom
                                44: i.HiHatCymbal, #Pedal Hi-Hat
                                45: i.TomTom, #Low Tom
                                46: i.HiHatCymbal, #Open Hi-Hat
                                47: i.TomTom, #Low-Mid Tom
                                48: i.TomTom, #Hi-Mid Tom
                                49: i.CrashCymbals, #Crash Cymbal 1
                                50: i.TomTom, #High Tom
                                #51: i.Ride Cymbal 1,
                                #52: i.Chinese Cymbal,
                                #53: i.Ride Bell,
                                54: i.Tambourine,
                                #55: i.Splash Cymbal,
                                56: i.Cowbell,
                                57: i.CrashCymbals, #Crash Cymbal 2
                                58: i.Vibraslap,
                                #59: i.Ride Cymbal 2,
                                60: i.BongoDrums, #Hi Bongo
                                61: i.BongoDrums, #Low Bongo
                                62: i.CongaDrum, #Mute Hi Conga
                                63: i.CongaDrum, #Open Hi Conga
                                64: i.CongaDrum, #Low Conga
                                65: i.Timbales, #High Timbale
                                66: i.Timbales, #Low Timbale
                                67: i.Agogo, #High Agogo
                                68: i.Agogo, #Low Agogo
                                #69: i.Cabasa,
                                70: i.Maracas,
                                71: i.Whistle, #Short Whistle
                                72: i.Whistle, #Long Whistle
                                #73: i.Short Guiro,
                                #74: i.Long Guiro,
                                #75: i.Claves,
                                76: i.Woodblock, #Hi Wood Block
                                77: i.Woodblock, #Low Wood Block
                                #78: i.Mute Cuica,
                                #79: i.Open Cuica,
                                80: i.Triangle, #Mute Triangle
                                81: i.Triangle} #Open Triangle

    # MIDI percussion mappings from http://www.midi.org/techspecs/gm1sound.php
    
    def midiPitchToInstrument(self, midiPitch):
        '''
        Takes a pitch.Pitch object or int and returns the corresponding instrument in the GM Percussion Map.
        
        
        >>> pm = midi.percussion.PercussionMapper()
        >>> cowPitch = pitch.Pitch(56)
        >>> cowbell = pm.midiPitchToInstrument(cowPitch)
        >>> cowbell
        <music21.instrument.Instrument Cowbell>
        
        Or it can just take an integer (representing MIDI note) for the pitch instead...
        
        >>> moreCowbell = pm.midiPitchToInstrument(56)
        >>> moreCowbell
        <music21.instrument.Instrument Cowbell>
        
        The standard GM Percussion list goes from 35 to 81;
        pitches outside this range raise an exception.
        
        >>> bassDrum1Pitch = pitch.Pitch('B-1')
        >>> pm.midiPitchToInstrument(bassDrum1Pitch)
        Traceback (most recent call last):
        MIDIPercussionException: 34 doesn't map to a valid instrument!
        
        Also, certain GM instruments do not have corresponding music21 instruments, 
        so at present they also raise an exception.
        
        >>> cabasaPitch = 69
        >>> pm.midiPitchToInstrument(cabasaPitch)
        Traceback (most recent call last):
        MIDIPercussionException: 69 doesn't map to a valid instrument!


        Some music21 Instruments have more than one MidiPitch.  In this case you'll
        get the same Instrument object but with a different modifier
        
        >>> acousticBassDrumPitch = pitch.Pitch(35)
        >>> acousticBDInstrument = pm.midiPitchToInstrument(acousticBassDrumPitch)
        >>> acousticBDInstrument
        <music21.instrument.Instrument Bass Drum>
        >>> acousticBDInstrument.modifier
        'acoustic'
        
        >>> oneBassDrumPitch = pitch.Pitch(36)
        >>> oneBDInstrument = pm.midiPitchToInstrument(oneBassDrumPitch)
        >>> oneBDInstrument
        <music21.instrument.Instrument Bass Drum>
        >>> oneBDInstrument.modifier
        '1'
        
        '''
        
        if isinstance(midiPitch, int):
            midiNumber = midiPitch
        else:
            midiNumber = midiPitch.midi
        if midiNumber not in self.reverseInstrumentMapping:
            raise MIDIPercussionException("%r doesn't map to a valid instrument!" % midiNumber)
        midiInstrument = self.reverseInstrumentMapping[midiNumber]
        
        midiInstrumentObject = midiInstrument()
        if midiInstrumentObject.inGMPercMap is True and hasattr(midiInstrumentObject, '_percMapPitchToModifier'):
            if midiNumber in midiInstrumentObject._percMapPitchToModifier:
                modifier = midiInstrumentObject._percMapPitchToModifier[midiNumber]
                midiInstrumentObject.modifier = modifier
        
        return midiInstrumentObject
    
    def midiInstrumentToPitch(self, midiInstrument):
        '''
        Takes an instrument.Instrument object and returns a pitch object
        with the corresponding MIDI note, according to the GM Percussion Map.
        
        
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
        MIDIPercussionException: <music21.instrument.Instrument Bagpipes> is not in the GM Percussion Map!
        '''
        
        if not hasattr(midiInstrument, 'inGMPercMap') or midiInstrument.inGMPercMap is False:
            raise MIDIPercussionException("%r is not in the GM Percussion Map!" % midiInstrument)
        midiPitch = midiInstrument.percMapPitch
        pitchObject = pitch.Pitch()
        pitchObject.midi = midiPitch
        return pitchObject

    _DOC_ORDER = [midiInstrumentToPitch, midiPitchToInstrument]

class Test(unittest.TestCase):
    
    def runTest(self):
        pass

    def testCopyAndDeepcopy(self):
        '''
        Test copying all objects defined in this module
        '''
        import sys, types
        for part in sys.modules[self.__module__].__dict__.keys():
            match = False
            for skip in ['_', '__', 'Test', 'Exception']:
                if part.startswith(skip) or part.endswith(skip):
                    match = True
            if match:
                continue
            name = getattr(sys.modules[self.__module__], part)
            if callable(name) and not isinstance(name, types.FunctionType):
                try: # see if obj can be made w/ args
                    obj = name()
                except TypeError:
                    continue
                junk = copy.copy(obj)
                junk = copy.deepcopy(obj)



#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [PercussionMapper]


if __name__ == "__main__":
    import music21
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof

