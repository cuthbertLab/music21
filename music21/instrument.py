# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         instrument.py
# Purpose:      Class for basic instrument information
#
# Authors:      Neena Parikh
#               Christopher Ariza
#               Michael Scott Cuthbert
#               Jose Cabal-Ugaz
#               Ben Houge
#
# Copyright:    Copyright © 2009-2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------

'''
This module represents instruments through objects that contain general information
such as Metadata for instrument names, classifications, transpositions and default 
MIDI program numbers.  It also contains information specific to each instrument
or instrument family, such as string pitches, etc.  Information about instrumental
ensembles is also included here though it may later be separated out into its own
ensemble.py module. 
'''
import copy
import unittest
import sys
from collections import OrderedDict

from music21 import base
from music21 import common
from music21 import interval
from music21 import pitch

from music21.exceptions21 import InstrumentException

from music21.ext import six

from music21 import environment
_MOD = "instrument.py"
environLocal = environment.Environment(_MOD)




def unbundleInstruments(streamIn, inPlace = False):
    '''
    takes a :class:`~music21.stream.Stream` that has :class:`~music21.note.Unpitched` objects
    and moves their `.storedInstrument` attributes to a new Stream (unless inPlace = True)  

    
    >>> up1 = note.Unpitched()
    >>> up1.storedInstrument = instrument.BassDrum()
    >>> up2 = note.Unpitched()
    >>> up2.storedInstrument = instrument.Cowbell()
    >>> s = stream.Stream()
    >>> s.append(up1)
    >>> s.append(up2)
    >>> s2 = instrument.unbundleInstruments(s)
    >>> s2.show('text')
    {0.0} <music21.instrument.Instrument Bass Drum>
    {0.0} <music21.note.Unpitched object at 0x...>
    {1.0} <music21.instrument.Instrument Cowbell>
    {1.0} <music21.note.Unpitched object at 0x...>
    '''    
    if inPlace is True:
        s = streamIn
    else:
        s = copy.deepcopy(streamIn)
    
    for thisObj in s:
        if 'Unpitched' in thisObj.classes:
            i = thisObj.storedInstrument
            if i is not None:
                off = thisObj.offset
                s.insert(off, i)
    
    if inPlace is False:
        return s

def bundleInstruments(streamIn, inPlace = False):
    '''
    
    >>> up1 = note.Unpitched()
    >>> up1.storedInstrument = instrument.BassDrum()
    >>> upUnknownInstrument = note.Unpitched()
    
    >>> up2 = note.Unpitched()
    >>> up2.storedInstrument = instrument.Cowbell()
    >>> s = stream.Stream()
    >>> s.append(up1)
    >>> s.append(upUnknownInstrument)
    >>> s.append(up2)
    >>> s2 = instrument.unbundleInstruments(s)
    >>> s3 = instrument.bundleInstruments(s2)
    >>> for test in s3:
    ...     print(test.storedInstrument)
    Bass Drum
    Bass Drum
    Cowbell
    
    '''
    if inPlace is True:
        s = streamIn
    else:
        s = copy.deepcopy(streamIn)
    
    for thisObj in s:
        if 'Instrument' in thisObj.classes:
            lastInstrument = thisObj
            s.remove(thisObj)
        elif 'Unpitched' in thisObj.classes:
            thisObj.storedInstrument = lastInstrument
        
    if inPlace is False:
        return s

    

class Instrument(base.Music21Object):
    '''
    Base class for all musical instruments.  Designed
    for subclassing, though usually a more specific
    instrument class (such as StringInstrument) would
    be better to subclass.
    
    Some defined attributes for instruments include:
    
    * partId
    * partName
    * partAbbreviation
    * instrumentId
    * instrumentName
    * instrumentAbbreviation
    * midiProgram
    * midiChannel
    * lowestNote (a note object or a string)
    * highestNote (a note object or a string)
    * transposition (an interval object)
    * inGMPercMap (bool -- if it uses the GM percussion map)
    * soundfontFn (filepath to a sound font, optional)
    '''
    
    classSortOrder = -25

    def __init__(self):
        base.Music21Object.__init__(self)

        self.partId = None
        self.partName = None
        self.partAbbreviation = None

        self.instrumentId = None # apply to midi and instrument
        self.instrumentName = None
        self.instrumentAbbreviation = None
        self.midiProgram = None
        self.midiChannel = None
        
        self.lowestNote = None
        self.highestNote = None

        # define interval to go from written to sounding
        self.transposition = None
        
        self.inGMPercMap = False
        self.soundfontFn = None # if defined...

    def __str__(self):
        msg = []
        if self.partId is not None:
            msg.append('%s: ' % self.partId)
        if self.partName is not None:
            msg.append('%s: ' % self.partName)
        if self.instrumentName is not None:
            msg.append(self.instrumentName)
        return ''.join(msg)

    def __repr__(self):
        return "<music21.instrument.Instrument %s>" % self.__str__()

    def bestName(self):
        '''
        Find a viable name, looking first at instrument, then part, then 
        abbreviations.
        '''
        if self.partName != None:
            return self.partName
        elif self.partAbbreviation != None:
            return self.partAbbreviation
        elif self.instrumentName != None:
            return self.instrumentName
        elif self.instrumentAbbreviation != None:
            return self.instrumentAbbreviation
        else:
            return None


    def partIdRandomize(self):
        '''
        Force a unique id by using an MD5
        '''
        idNew = 'P%s' % common.getMd5()
        #environLocal.printDebug(['incrementing instrument from', 
        #                         self.partId, 'to', idNew])
        self.partId = idNew
         
    def instrumentIdRandomize(self):
        '''
        Force a unique id by using an MD5
        '''
        idNew = 'I%s' % common.getMd5()
        #environLocal.printDebug(['incrementing instrument from', 
        #                         self.partId, 'to', idNew])
        self.instrumentId = idNew
         

    def autoAssignMidiChannel(self, usedChannels=[]): # CORRECT! # pylint: disable=dangerous-default-value
        '''
        Assign an unused midi channel given a list of
        used channels.

        assigns the number to self.midiChannel and returns
        it as an int.

        Note that midi channel 10 is special, and
        thus is skipped.

        Currently only 16 channels are used.

        Note that the reused "usedChannels=[]" in the
        signature is NOT a mistake, but necessary for
        the case where there needs to be a global list.
        
        >>> used = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 11]
        >>> i = instrument.Violin()
        >>> i.autoAssignMidiChannel(used)
        12
        >>> i.midiChannel
        12
        
        
        OMIT_FROM_DOCS
        
        >>> used2 = range(0,16)
        >>> i = instrument.Instrument()
        >>> i.autoAssignMidiChannel(used2)
        Traceback (most recent call last):
        InstrumentException: we are out of midi channels! help!
        '''
        # NOTE: this is used in musicxml output, not in midi output
        maxMidi = 16
        channelFilter = []
        for e in usedChannels:
            if e != None:
                channelFilter.append(e)

        if len(channelFilter) == 0:
            self.midiChannel = 0
            return 0
        elif len(channelFilter) >= maxMidi:
            raise InstrumentException("we are out of midi channels! help!")
        else:
            for ch in range(maxMidi):
                if ch in channelFilter:
                    continue
                elif ch % 16 == 10:
                    continue # skip 10 /perc for now
                else:
                    self.midiChannel = ch
                    return ch
            return 0
            #raise InstrumentException("we are out of midi channels and this was not already detected PROGRAM BUG!")


#-------------------------------------------------------------------------------
class KeyboardInstrument(Instrument):

    def __init__(self):
        Instrument.__init__(self)
        self.instrumentName = 'Keyboard'
        self.instrumentAbbreviation = 'Kb'

class Piano(KeyboardInstrument):   
    '''
    
    >>> p = instrument.Piano()
    >>> p.instrumentName
    'Piano'
    >>> p.midiProgram
    0
    '''
    def __init__(self):
        KeyboardInstrument.__init__(self)

        self.instrumentName = 'Piano'
        self.instrumentAbbreviation = 'Pno'
        self.midiProgram = 0

        self.lowestNote = pitch.Pitch('A0')
        self.highestNote = pitch.Pitch('C8')

        self.names = {'de': ['Klavier', 'Pianoforte'],
                      'en': ["Piano", "Pianoforte"]}

class Harpsichord(KeyboardInstrument):   
    def __init__(self):
        KeyboardInstrument.__init__(self)

        self.instrumentName = 'Harpsichord'
        self.instrumentAbbreviation = 'Hpschd'
        self.midiProgram = 6

        self.lowestNote = pitch.Pitch('F1')
        self.highestNote = pitch.Pitch('F6')

class Clavichord(KeyboardInstrument):   
    def __init__(self):
        KeyboardInstrument.__init__(self)

        self.instrumentName = 'Clavichord'
        self.instrumentAbbreviation = 'Clv'
        self.midiProgram = 7
        
        #TODO: self.lowestNote = pitch.Pitch('')
        #TODO: self.highestNote = pitch.Pitch('')

class Celesta(KeyboardInstrument):   
    def __init__(self):
        KeyboardInstrument.__init__(self)

        self.instrumentName = 'Celesta'
        self.instrumentAbbreviation = 'Clst'
        self.midiProgram = 8


#-------------------------------------------------------------------------------
class Organ(Instrument):
    def __init__(self):
        Instrument.__init__(self)
        
        self.midiProgram = 19
        
class PipeOrgan(Organ):
    def __init__(self):
        Organ.__init__(self)
        
        self.instrumentName = 'Pipe Organ'
        self.instrumentAbbreviation = 'P Org'
        self.midiProgram = 19
        
        self.lowestNote = pitch.Pitch('C2')
        self.highestNote = pitch.Pitch('C6')
        
class ElectricOrgan(Organ):
    def __init__(self):
        Organ.__init__(self)
        
        self.instrumentName = 'Electric Organ'
        self.instrumentAbbreviation = 'Elec Org'
        self.midiProgram = 16
        
        self.lowestNote = pitch.Pitch('C2')
        self.highestNote = pitch.Pitch('C6')

class ReedOrgan(Organ):
    def __init__(self):
        Organ.__init__(self)
        
        self.instrumentName = 'Reed Organ'
        #TODO self.instrumentAbbreviation = ''
        self.midiProgram = 20
        
        self.lowestNote = pitch.Pitch('C2')
        self.highestNote = pitch.Pitch('C6')

class Accordion(Organ):
    def __init__(self):
        Organ.__init__(self)
        
        self.instrumentName = 'Accordion'
        self.instrumentAbbreviation = 'Acc'
        self.midiProgram = 21
        
        self.lowestNote = pitch.Pitch('F3')
        self.highestNote = pitch.Pitch('A6')

class Harmonica(Organ):
    def __init__(self):
        Organ.__init__(self)
        
        self.instrumentName = 'Harmonica'
        self.instrumentAbbreviation = 'Hmca'
        self.midiProgram = 22
        
        self.lowestNote = pitch.Pitch('C3')
        self.highestNote = pitch.Pitch('C6')


#------------------------------------------------------
class StringInstrument(Instrument):

    def __init__(self):
        Instrument.__init__(self)
        self._stringPitches = None
        self._cachedPitches = None
        self.instrumentName = 'StringInstrument'
        self.instrumentAbbreviation = 'Str'

        self.midiProgram = 48
    
    def _getStringPitches(self):    
        if hasattr(self, "_cachedPitches") and self._cachedPitches is not None:
            return self._cachedPitches
        elif not hasattr(self, "_stringPitches"):
            raise InstrumentException("cannot get stringPitches for these instruments")
        else:
            self._cachedPitches = [pitch.Pitch(x) for x in self._stringPitches]
            return self._cachedPitches
    
    def _setStringPitches(self, newPitches):
        if len(newPitches) > 0 and (hasattr(newPitches[0], "step") or newPitches[0] is None):
            # newPitches is pitchObjects or something 
            self._stringPitches = newPitches
            self._cachedPitches = newPitches
        else:
            self._cachedPitches = None
            self._stringPitches = newPitches
    
    stringPitches = property(_getStringPitches, _setStringPitches, doc = '''
            stringPitches is a property that stores a list of Pitches (or pitch names, 
            such as "C4") that represent the pitch of the open strings from lowest to
            highest.[*]

            
            
            >>> vln1 = instrument.Violin()
            >>> [str(p) for p in vln1.stringPitches]
            ['G3', 'D4', 'A4', 'E5']
            
            instrument.stringPitches are full pitch objects, not just names:

            >>> [x.octave for x in vln1.stringPitches]
            [3, 4, 4, 5]
            
            Scordatura for Scelsi's violin concerto *Anahit*.
            (N.B. that string to pitch conversion is happening automatically)
            
            
            >>> vln1.stringPitches = ["G3","G4","B4","D4"]
            
            (`[*]In some tuning methods such as reentrant tuning on the ukulele,
            lute, or five-string banjo the order might not strictly be from lowest to
            highest.  The same would hold true for certain violin scordatura pieces, such
            as some of Biber's *Mystery Sonatas*`)
            ''')
                       
class Violin(StringInstrument):   
    def __init__(self):
        StringInstrument.__init__(self)

        self.instrumentName = 'Violin'
        self.instrumentAbbreviation = 'Vln'
        self.midiProgram = 40

        self.lowestNote = pitch.Pitch('G3')
        self._stringPitches = ['G3','D4','A4','E5']

class Viola(StringInstrument):
    def __init__(self):
        StringInstrument.__init__(self)

        self.instrumentName = 'Viola'
        self.instrumentAbbreviation = 'Vla'
        self.midiProgram = 41

        self.lowestNote = pitch.Pitch('C3')
        self._stringPitches = ['C3','G3','D4','A4']

class Violoncello(StringInstrument):
    def __init__(self):
        StringInstrument.__init__(self)

        self.instrumentName = 'Violoncello'
        self.instrumentAbbreviation = 'Vc'
        self.midiProgram = 42

        self.lowestNote = pitch.Pitch('C2')
        self._stringPitches = ['C2','G2','D3','A3']

class Contrabass(StringInstrument):
    '''
    For the Contrabass (or double bass), the stringPitches attribute refers to the sounding pitches
    of each string; whereas the lowestNote attribute refers to the lowest written 
    note
    
    '''
    def __init__(self):
        StringInstrument.__init__(self)

        self.instrumentName = 'Contrabass'
        self.instrumentAbbreviation = 'Cb'
        self.midiProgram = 43

        self.lowestNote = pitch.Pitch('E2')
        self._stringPitches = ['E1','A1','D2','G2']
        self.transposition = interval.Interval('P-8')

class Harp(StringInstrument):
    def __init__(self):
        StringInstrument.__init__(self)

        self.instrumentName = 'Harp'
        self.instrumentAbbreviation = 'Hp'
        self.midiProgram = 46

        self.lowestNote = pitch.Pitch('C1')
        self.highestNote = pitch.Pitch('G#7')


class Guitar(StringInstrument):
    def __init__(self):
        StringInstrument.__init__(self)

class AcousticGuitar(Guitar):
    def __init__(self):
        Guitar.__init__(self)

        self.instrumentName = 'Acoustic Guitar'
        self.instrumentAbbreviation = 'Ac Gtr'
        self.midiProgram = 24

        self.lowestNote = pitch.Pitch('E2')
        self._stringPitches = ['E2','A2','D3','G3','B3','E4']

class ElectricGuitar(Guitar):
    def __init__(self):
        Guitar.__init__(self)

        self.instrumentName = 'Electric Guitar'
        self.instrumentAbbreviation = 'Elec Gtr'
        self.midiProgram = 26

        self.lowestNote = pitch.Pitch('E2')
        self._stringPitches = ['E2','A2','D3','G3','B3','E4']

class AcousticBass(Guitar):
    def __init__(self):
        Guitar.__init__(self)

        self.instrumentName = 'Acoustic Bass'
        self.instrumentAbbreviation = 'Ac b'
        self.midiProgram = 32

        self.lowestNote = pitch.Pitch('E1')
        self._stringPitches = ['E1','A1','D2','G2']

class ElectricBass(Guitar):
    def __init__(self):
        Guitar.__init__(self)

        self.instrumentName = 'Electric Bass'
        self.instrumentAbbreviation = 'Elec b'
        self.midiProgram = 33

        self.lowestNote = pitch.Pitch('E1')
        self._stringPitches = ['E1','A1','D2','G2']
        
class FretlessBass(Guitar):
    def __init__(self):
        Guitar.__init__(self)

        self.instrumentName = 'Fretless Bass'
        #TODO: self.instrumentAbbreviation = ''
        self.midiProgram = 35

        self.lowestNote = pitch.Pitch('E1')
        self._stringPitches = ['E1','A1','D2','G2']
        
        
class Mandolin(StringInstrument):
    def __init__(self):
        StringInstrument.__init__(self)
        
        self.instrumentName = 'Mandolin'
        self.instrumentAbbreviation = 'Mdln'
        
        self.lowestNote = pitch.Pitch('G3')
        self._stringPitches = ['G3','D4','A4','E5']
        
class Ukulele(StringInstrument):
    def __init__(self):
        StringInstrument.__init__(self)
        
        self.instrumentName = 'Ukulele'
        self.instrumentAbbreviation = 'Uke'
        
        self.lowestNote = pitch.Pitch('C4')
        self._stringPitches = ['G4','C4','E4','A4']

class Banjo(StringInstrument):
    def __init__(self):
        StringInstrument.__init__(self)
        
        self.instrumentName = 'Banjo'
        self.instrumentAbbreviation = 'Bjo'
        self.midiProgram = 105
        
        self.lowestNote = pitch.Pitch('C3')
        self._stringPitches = ['C3','G3','D4','A4']
        self.transposition = interval.Interval('P-8')

class Lute(StringInstrument):
    def __init__(self):
        StringInstrument.__init__(self)
        
        self.instrumentName = 'Lute'
        self.instrumentAbbreviation = 'Lte'
        self.midiProgram = 24        

class Sitar(StringInstrument):
    def __init__(self):
        StringInstrument.__init__(self)
        
        self.instrumentName = 'Sitar'
        self.instrumentAbbreviation = 'Sit'
        self.midiProgram = 104
        
class Shamisen(StringInstrument):
    def __init__(self):
        StringInstrument.__init__(self)
        
        self.instrumentName = 'Shamisen'
        #TODO: self.instrumentAbbreviation = ''
        self.midiProgram = 106
        
class Koto(StringInstrument):
    def __init__(self):
        StringInstrument.__init__(self)
        
        self.instrumentName = 'Koto'
        #TODO: self.instrumentAbbreviation = ''
        self.midiProgram = 107

#-------------------------------------------------------------------------------
class WoodwindInstrument(Instrument):
    def __init__(self):
        Instrument.__init__(self)
        self.instrumentName = 'Woodwind'
        self.instrumentAbbreviation = 'Ww'

class Flute(WoodwindInstrument):
    def __init__(self):
        WoodwindInstrument.__init__(self)

        self.instrumentName = 'Flute'
        self.instrumentAbbreviation = 'Fl'
        self.midiProgram = 73

        self.lowestNote = pitch.Pitch('C4')

class Piccolo(Flute):
    def __init__(self):
        Flute.__init__(self)

        self.instrumentName = 'Piccolo'
        self.instrumentAbbreviation = 'Picc'
        self.midiProgram = 72

        self.lowestNote = pitch.Pitch('C5')
        self.transposition = interval.Interval('P8')

class Recorder(Flute):
    def __init__(self):
        Flute.__init__(self)

        self.instrumentName = 'Recorder'
        self.instrumentAbbreviation = 'Rec'
        self.midiProgram = 74

        self.lowestNote = pitch.Pitch('F4')

class PanFlute(Flute):
    def __init__(self):
        Flute.__init__(self)

        self.instrumentName = 'Pan Flute'
        self.instrumentAbbreviation = 'P Fl'
        self.midiProgram = 75

class Shakuhachi(Flute):
    def __init__(self):
        Flute.__init__(self)

        self.instrumentName = 'Shakuhachi'
        self.instrumentAbbreviation = 'Shk Fl'
        self.midiProgram = 77

class Whistle(Flute):
    def __init__(self):
        Flute.__init__(self)

        self.instrumentName = 'Whistle'
        self.instrumentAbbreviation = 'Whs'
        self.inGMPercMap = True
        self.percMapPitch = 71
        self.midiProgram = 78

class Ocarina(Flute):
    def __init__(self):
        Flute.__init__(self)

        self.instrumentName = 'Ocarina'
        self.instrumentAbbreviation = 'Oc'
        self.midiProgram = 79
        
class Oboe(WoodwindInstrument):
    def __init__(self):
        WoodwindInstrument.__init__(self)

        self.instrumentName = 'Oboe'
        self.instrumentAbbreviation = 'Ob'
        self.midiProgram = 68

        self.lowestNote = pitch.Pitch('B-3')

class EnglishHorn(WoodwindInstrument):
    def __init__(self):
        WoodwindInstrument.__init__(self)

        self.instrumentName = 'English Horn'
        self.instrumentAbbreviation = 'Eng Hn'
        self.midiProgram = 69

        self.lowestNote = pitch.Pitch('E3')
        self.transposition = interval.Interval('P-5')

class Clarinet(WoodwindInstrument):
    def __init__(self):
        WoodwindInstrument.__init__(self)

        self.instrumentName = 'Clarinet'
        self.instrumentAbbreviation = 'Cl'
        self.midiProgram = 71

        self.lowestNote = pitch.Pitch('E3')
        # sounds a M2 lower than written
        self.transposition = interval.Interval('M-2')

class BassClarinet(Clarinet):
    '''
    
    >>> bcl = instrument.BassClarinet()
    >>> bcl.instrumentName
    'Bass clarinet'
    >>> bcl.midiProgram
    71
    >>> 'WoodwindInstrument' in bcl.classes
    True
    '''
    def __init__(self):
        Clarinet.__init__(self)
        
        self.instrumentName = 'Bass clarinet'
        self.instrumentAbbreviation = 'Bs Cl'

        self.lowestNote = pitch.Pitch('E-3')
        self.transposition = interval.Interval('M-9')

class Bassoon(WoodwindInstrument):
    def __init__(self):
        WoodwindInstrument.__init__(self)

        self.instrumentName = 'Bassoon'
        self.instrumentAbbreviation = 'Bs'
        self.midiProgram = 70

        self.lowestNote = pitch.Pitch('B-1')


class Saxophone(WoodwindInstrument):
    def __init__(self):
        WoodwindInstrument.__init__(self)

        self.instrumentName = 'Saxophone'
        self.instrumentAbbreviation = 'Sax'
        self.midiProgram = 65
    
class SopranoSaxophone(Saxophone):
    def __init__(self):
        Saxophone.__init__(self)
        
        self.instrumentName = 'Soprano Saxophone'
        self.instrumentAbbreviation = 'S Sax'
        self.midiProgram = 64
        
        self.lowestNote = pitch.Pitch('B-3')
        self.transposition = interval.Interval('M-2')
        
class AltoSaxophone(Saxophone):
    def __init__(self):
        Saxophone.__init__(self)
        
        self.instrumentName = 'Alto Saxophone'
        self.instrumentAbbreviation = 'A Sax'
        self.midiProgram = 65
        
        self.lowestNote = pitch.Pitch('B-3')
        self.transposition = interval.Interval('M-6')
        
class TenorSaxophone(Saxophone):
    def __init__(self):
        Saxophone.__init__(self)
        
        self.instrumentName = 'Tenor Saxophone'
        self.instrumentAbbreviation = 'T Sax'
        self.midiProgram = 66
        
        self.lowestNote = pitch.Pitch('B-3')
        self.transposition = interval.Interval('M-9')
        
class BaritoneSaxophone(Saxophone):
    def __init__(self):
        Saxophone.__init__(self)
        
        self.instrumentName = 'Baritone Saxophone'
        self.instrumentAbbreviation = 'Bar Sax'
        self.midiProgram = 67
        
        self.lowestNote = pitch.Pitch('B-3')
        self.transposition = interval.Interval('M-13')
        

class Bagpipes(WoodwindInstrument):
    def __init__(self):
        WoodwindInstrument.__init__(self)
        
        self.instrumentName = 'Bagpipes'
        self.instrumentAbbreviation = 'Bag'
        self.midiProgram = 109
        
class Shehnai(WoodwindInstrument):
    def __init__(self):
        WoodwindInstrument.__init__(self)
        
        self.instrumentName = 'Shehnai'
        self.instrumentAbbreviation = 'Shn'
        self.midiProgram = 111

        
        
#-------------------------------------------------------------------------------

class BrassInstrument(Instrument):
    def __init__(self):
        Instrument.__init__(self)
        self.instrumentName = 'Brass'
        self.instrumentAbbreviation = 'Brs'

        self.midiProgram = 61

class Horn(BrassInstrument):
    '''
    
    >>> hn = instrument.Horn()
    >>> hn.instrumentName
    'Horn'
    >>> hn.midiProgram
    60
    >>> 'BrassInstrument' in hn.classes
    True
    '''
    def __init__(self):
        BrassInstrument.__init__(self)

        self.instrumentName = 'Horn'
        self.instrumentAbbreviation = 'Hn'
        self.midiProgram = 60

        self.lowestNote = pitch.Pitch('C2')
        self.transposition = interval.Interval('P-5')
        
class Trumpet(BrassInstrument):
    def __init__(self):
        BrassInstrument.__init__(self)

        self.instrumentName = 'Trumpet'
        self.instrumentAbbreviation = 'Tpt'
        self.midiProgram = 56
        
        self.lowestNote = pitch.Pitch('F#3')
        self.transposition = interval.Interval('M-2')

class Trombone(BrassInstrument):
    def __init__(self):
        BrassInstrument.__init__(self)

        self.instrumentName = 'Trombone'
        self.instrumentAbbreviation = 'Trb'
        self.midiProgram = 57
        
        self.lowestNote = pitch.Pitch('C2')

class BassTrombone(Trombone):
    def __init__(self):
        Trombone.__init__(self)

        self.instrumentName = 'Bass Trombone'
        self.instrumentAbbreviation = 'BTrb'        


class Tuba(BrassInstrument):
    def __init__(self):
        BrassInstrument.__init__(self)

        self.instrumentName = 'Tuba'
        self.instrumentAbbreviation = 'Tba'
        self.midiProgram = 58

        self.lowestNote = pitch.Pitch('E-2')

    
#-------------
class Percussion(Instrument):
    def __init__(self):
        Instrument.__init__(self)
        self.inGMPercMap = False
        self.percMapPitch = None
        self.instrumentName = 'Percussion'
        self.instrumentAbbreviation = 'Perc'


class PitchedPercussion(Percussion):
    pass


class UnpitchedPercussion(Percussion):
    def __init__(self):
        Percussion.__init__(self)
        self._modifier = None
        self._modifierToPercMapPitch = {}        
        
    def _getModifier(self):
        return self._modifier
    
    def _setModifier(self, modifier):
        modifier = modifier.lower().strip()
        # BEN: to-do, pull out hyphens, spaces, etc.
        
        
        if self.inGMPercMap is True and modifier.lower() in self._modifierToPercMapPitch:
            self.percMapPitch = self._modifierToPercMapPitch[modifier.lower()]
            
            # normalize modifiers...
            if self.percMapPitch in self._percMapPitchToModifier:
                modifier = self._percMapPitchToModifier[self.percMapPitch]
        
        self._modifier = modifier
        
    modifier = property(_getModifier, _setModifier, doc='''
    Returns or sets the modifier for this instrument.  A modifier could
    be something like "low-floor" for a TomTom or "rimshot" for a SnareDrum.
    
    If the modifier is in the object's ._modifierToPercMapPitch dictionary
    then changing the modifier also changes the .percMapPitch for the object
    
    
    >>> bd = instrument.BongoDrums()
    >>> bd.modifier
    'high'
    
    >>> bd.percMapPitch
    60
    >>> bd.modifier = 'low'
    >>> bd.percMapPitch
    61
    
    Variations on modifiers can also be used and they get normalized:
    
    >>> wb1 = instrument.Woodblock()
    >>> wb1.percMapPitch
    76
    >>> wb1.modifier = 'LO'
    >>> wb1.percMapPitch
    77
    >>> wb1.modifier  # n.b. -- not LO
    'low'
    ''')


class Vibraphone(PitchedPercussion):
    def __init__(self):
        PitchedPercussion.__init__(self)
        
        self.instrumentName = 'Vibraphone'
        self.instrumentAbbreviation = 'Vbp'
        self.midiProgram = 11

class Marimba(PitchedPercussion):
    def __init__(self):
        PitchedPercussion.__init__(self)
        
        self.instrumentName = 'Marimba'
        self.instrumentAbbreviation = 'Mar'
        self.midiProgram = 12

class Xylophone(PitchedPercussion):
    def __init__(self):
        PitchedPercussion.__init__(self)

        self.instrumentName = 'Xylophone'
        self.instrumentAbbreviation = 'Xyl.'
        self.midiProgram = 13

class Glockenspiel(PitchedPercussion):
    def __init__(self):
        PitchedPercussion.__init__(self)

        self.instrumentName = 'Glockenspiel'
        self.instrumentAbbreviation = 'Gsp'
        self.midiProgram = 9
        
class ChurchBells(PitchedPercussion):
    def __init__(self):
        PitchedPercussion.__init__(self)
        
        self.instrumentName = 'Church Bells'
        self.instrumentAbbreviation = 'Bells'
        self.midiProgram = 14

class TubularBells(PitchedPercussion):
    def __init__(self):
        PitchedPercussion.__init__(self)
        
        self.instrumentName = 'Tubular Bells'
        self.instrumentAbbreviation = 'Tbells'
        self.midiProgram = 14
                
class Gong(PitchedPercussion):
    def __init__(self):
        PitchedPercussion.__init__(self)
        
        self.instrumentName = 'Gong'
        self.instrumentAbbreviation = 'Gng'
        
class Handbells(PitchedPercussion):
    def __init__(self):
        PitchedPercussion.__init__(self)
        
        self.instrumentName = 'Handbells'
        #TODO: self.instrumentAbbreviation = ''

class Dulcimer(PitchedPercussion):
    def __init__(self):
        PitchedPercussion.__init__(self)
        
        self.instrumentName = 'Dulcimer'
        #TODO: self.instrumentAbbreviation = ''
        self.midiProgram = 15
        
class SteelDrum(PitchedPercussion):
    def __init__(self):
        PitchedPercussion.__init__(self)
        
        self.instrumentName = 'Steel Drum'
        self.instrumentAbbreviation = 'St Dr'
        self.midiProgram = 114
        
class Timpani(PitchedPercussion):
    def __init__(self):
        PitchedPercussion.__init__(self)
        
        self.instrumentName = 'Timpani'
        self.instrumentAbbreviation = 'Timp'
        self.midiProgram = 47

class Kalimba(PitchedPercussion):
    def __init__(self):
        PitchedPercussion.__init__(self)
        
        self.instrumentName = 'Kalimba'
        self.instrumentAbbreviation = 'Kal'
        self.midiProgram = 108


class Woodblock(UnpitchedPercussion):
    def __init__(self):
        UnpitchedPercussion.__init__(self)
        
        self.instrumentName = 'Woodblock'
        self.instrumentAbbreviation = 'Wd Bl'
        self.inGMPercMap = True
        self.midiProgram = 115
        
        self._modifier = 'high'
        self._modifierToPercMapPitch = { 'high': 76, 'low': 77, 'hi': 76, 'lo': 77 }
        self._percMapPitchToModifier = { 76: 'high', 77: 'low' }
        self.percMapPitch = self._modifierToPercMapPitch[self._modifier]
                
class TempleBlock(UnpitchedPercussion):
    def __init__(self):
        UnpitchedPercussion.__init__(self)
        
        self.instrumentName = 'Temple Block'
        self.instrumentAbbreviation = 'Temp Bl'
        
class Castanets(UnpitchedPercussion):
    def __init__(self):
        UnpitchedPercussion.__init__(self)
        
        self.instrumentName = 'Castanets'
        self.instrumentAbbreviation = 'Cas'
        
class Maracas(UnpitchedPercussion):
    def __init__(self):
        UnpitchedPercussion.__init__(self)
        
        self.instrumentName = 'Maracas'
        self.inGMPercMap = True
        self.percMapPitch = 70
        #TODO: self.instrumentAbbreviation = ''
        
class Vibraslap(UnpitchedPercussion):
    def __init__(self):
        UnpitchedPercussion.__init__(self)
        
        self.instrumentName = 'Vibraslap'
        self.instrumenAbbreviation = 'Vbslp'
        self.inGMPercMap = True
        self.percMapPitch = 58
        
# BEN: Standardize Cymbals as plural

class Cymbals(UnpitchedPercussion):
    def __init__(self):
        UnpitchedPercussion.__init__(self)
        self.instrumentName = 'Cymbals'
        self.instrumentAbbreviation = 'Cym'
        
class FingerCymbals(Cymbals):
    def __init__(self):
        Cymbals.__init__(self)
        
        self.instrumentName = 'Finger Cymbals'
        self.instrumentAbbreviation = 'Fing Cym'
        
class CrashCymbals(Cymbals):
    def __init__(self):
        Cymbals.__init__(self)
        
        self.instrumentName = 'Crash Cymbals'
        self.instrumentAbbreviation = 'Cym'
        self.inGMPercMap = True
        self._modifier = "1"
        
        self._modifierToPercMapPitch = {'1': 49,
                                        '2': 57,
                                        }
        self._percMapPitchToModifier = {49: '1',
                                        57: '2',
                                        }
        self.percMapPitch = self._modifierToPercMapPitch[self._modifier]
    
        
class SuspendedCymbal(Cymbals):
    def __init__(self):
        Cymbals.__init__(self)
        
        self.instrumentName = 'Suspended Cymbal'
        #TODO: self.instrumentAbbreviation = ''
        
class SizzleCymbal(Cymbals):
    def __init__(self):
        Cymbals.__init__(self)
        
        self.instrumentName = 'Sizzle Cymbal'
        #TODO: self.instrumentAbbreviation = ''

class SplashCymbals(Cymbals):
    def __init__(self):
        Cymbals.__init__(self)
        
        self.instrumentName = 'Splash Cymbals'
        #TODO: self.instrumentAbbreviation = ''

class RideCymbals(Cymbals):
    def __init__(self):
        Cymbals.__init__(self)
        
        self.instrumentName = 'Ride Cymbals'
        #TODO: self.instrumentAbbreviation = ''
        
class HiHatCymbal(Cymbals):
    def __init__(self):
        Cymbals.__init__(self)
        
        self.instrumentName = 'Hi-Hat Cymbal'
        self.inGMPercMap = True
        
        self._modifier = 'pedal'
        
        self._modifierToPercMapPitch = {'pedal': 44,
                                        'open': 46,
                                        'closed': 42,
                                        }
        self._percMapPitchToModifier = {44: 'pedal',
                                        46: 'open',
                                        42: 'closed',
                                        }
        self.percMapPitch = self._modifierToPercMapPitch[self._modifier]
    
        #TODO: self.instrumentAbbreviation = ''
        
class Triangle(UnpitchedPercussion):
    def __init__(self):
        UnpitchedPercussion.__init__(self)
        
        self.instrumentName = 'Triangle'
        self.instrumentAbbreviation = 'Tri'
        self.inGMPercMap = True
        self._modifier = 'open'
        
        self._modifierToPercMapPitch = {'open': 81,
                                        'mute': 80,
                                        }
        self._percMapPitchToModifier = {80: 'mute',
                                        81: 'open',
                                        }
        self.percMapPitch = self._modifierToPercMapPitch[self._modifier]
    
        
class Cowbell(UnpitchedPercussion):
    def __init__(self):
        UnpitchedPercussion.__init__(self)
        
        self.instrumentName = 'Cowbell'
        self.instrumentAbbreviation = 'Cwb'
        self.inGMPercMap = True
        self.percMapPitch = 56
        
class Agogo(UnpitchedPercussion):
    def __init__(self):
        UnpitchedPercussion.__init__(self)
        
        self.instrumentName = 'Agogo'
        #TODO: self.instrumentAbbreviation = ''
        self.inGMPercMap = True
        self.percMapPitch = 67     
        self.midiProgram = 113

class TamTam(UnpitchedPercussion):
    def __init__(self):
        UnpitchedPercussion.__init__(self)
        
        self.instrumentName = 'Tam-Tam'
        #TODO: self.instrumentAbbreviation = ''
        
class SleighBells(UnpitchedPercussion):
    def __init__(self):
        UnpitchedPercussion.__init__(self)
        
        self.instrumentName = 'Sleigh Bells'
        #TODO: self.instrumentAbbreviation = ''
        
class SnareDrum(UnpitchedPercussion):
    def __init__(self):
        UnpitchedPercussion.__init__(self)
        
        self.instrumentName = 'Snare Drum'
        self.instrumentAbbreviation = 'Sn Dr'
        self.inGMPercMap = True
        self._modifier = "acoustic"
        self._modifierToPercMapPitch = {'acoustic': 38,
                                        'side': 37,
                                        'electic': 40,
                                        }
        self._percMapPitchToModifier = {38: 'acoustic',
                                        37: 'side',
                                        40: 'electric',
                                        }
        self.percMapPitch = self._modifierToPercMapPitch[self._modifier]
    
class TenorDrum(UnpitchedPercussion):
    def __init__(self):
        UnpitchedPercussion.__init__(self)
        
        self.instrumentName = 'Tenor Drum'
        self.instrumentAbbreviation = 'Ten Dr'

class BongoDrums(UnpitchedPercussion):
    def __init__(self):
        UnpitchedPercussion.__init__(self)
        
        self.instrumentName = 'Bongo Drums'
        self.instrumentAbbreviation = 'Bgo Dr'
        
        self.inGMPercMap = True
        self._modifier = 'high'
        self._modifierToPercMapPitch = { 'high': 60, 'low': 61 }
        self._percMapPitchToModifier = { 60: 'high', 61: 'low' }
        self.percMapPitch = self._modifierToPercMapPitch[self._modifier]
        
    
class TomTom(UnpitchedPercussion):
    def __init__(self):
        UnpitchedPercussion.__init__(self)
        
        self.instrumentName = 'Tom-Tom'
        #TODO: self.instrumentAbbreviation = ''
        self.inGMPercMap = True
        self._modifier = 'low floor'
        self._modifierToPercMapPitch = { 'low floor': 41, 'high floor': 43, 'low': 45, 
                                         'low-mid': 47, 'high-mid': 48, 'high': 50 }
        self._percMapPitchToModifier = { 41: 'low floor', 43: 'high floor', 45: 'low', 
                                        47: 'low-mid', 48: 'high-mid', 50: 'high' }
        self.percMapPitch = self._modifierToPercMapPitch[self._modifier]
        
    
class Timbales(UnpitchedPercussion):
    def __init__(self):
        UnpitchedPercussion.__init__(self)
        
        self.instrumentName = 'Timbales'
        self.instrumentAbbreviation = 'Tim'
        self.inGMPercMap = True
        self._modifier = 'high'
        self._modifierToPercMapPitch = { 'high': 65, 'low': 66 }
        self._percMapPitchToModifier = { 65: 'high', 66: 'low' }
        self.percMapPitch = self._modifierToPercMapPitch[self._modifier]
        
        
class CongaDrum(UnpitchedPercussion):
    def __init__(self):
        UnpitchedPercussion.__init__(self)
        
        self.instrumentName = 'Conga Drum'
        self.instrumentAbbreviation = 'Cga Dr'
        self.inGMPercMap = True
        self._modifier = 'low'
        self._modifierToPercMapPitch = { 'low': 64, 'mute high': 62, 'open high': 63 }
        self._percMapPitchToModifier = { 64: 'low', 62: 'mute high', 63: 'open high' }
        self.percMapPitch = self._modifierToPercMapPitch[self._modifier]
        
        
class BassDrum(UnpitchedPercussion):
    def __init__(self):
        UnpitchedPercussion.__init__(self)
        
        self.instrumentName = 'Bass Drum'
        self.instrumentAbbreviation = 'B Dr'
        self.inGMPercMap = True
        self._modifier = 'acoustic'
        self._modifierToPercMapPitch = { 'acoustic': 35, '1': 36 }
        self._percMapPitchToModifier = { 35: 'acoustic', 36: '1' }
        self.percMapPitch = self._modifierToPercMapPitch[self._modifier]

        
class Taiko(UnpitchedPercussion):
    def __init__(self):
        UnpitchedPercussion.__init__(self)
        
        self.instrumentName = 'Taiko'
        #TODO: self.instrumentAbbreviation = ''
        self.midiProgram = 116
        
class Tambourine(UnpitchedPercussion):
    def __init__(self):
        UnpitchedPercussion.__init__(self)
        
        self.instrumentName = 'Tambourine'
        self.instrumentAbbreviation = 'Tmbn'
        self.inGMPercMap = True
        self.percMapPitch = 54
        
class Whip(UnpitchedPercussion):
    def __init__(self):
        UnpitchedPercussion.__init__(self)
        
        self.instrumentName = 'Whip'
        #TODO: self.instrumentAbbreviation = ''
        
class Ratchet(UnpitchedPercussion):
    def __init__(self):
        UnpitchedPercussion.__init__(self)
        
        self.instrumentName = 'Ratchet'
        #TODO: self.instrumentAbbreviation = ''
        
class Siren(UnpitchedPercussion):
    def __init__(self):
        UnpitchedPercussion.__init__(self)
        
        self.instrumentName = 'Siren'
        #TODO: self.instrumentAbbreviation = ''
        
class SandpaperBlocks(UnpitchedPercussion):
    def __init__(self):
        UnpitchedPercussion.__init__(self)
        
        self.instrumentName = 'Sandpaper Blocks'
        self.instrumentAbbreviation = 'Sand Bl'
        
class WindMachine(UnpitchedPercussion):
    def __init__(self):
        UnpitchedPercussion.__init__(self)
        
        self.instrumentName = 'Wind Machine'
        #TODO: self.instrumentAbbreviation = ''


#------------------------------------------------------

class Vocalist(Instrument):
    '''
    n.b. called Vocalist to not be confused with stream.Voice
    '''
    def __init__(self):
        Instrument.__init__(self)

        self.instrumentName = 'Voice'
        self.instrumentAbbreviation = 'V'
        self.midiProgram = 52
        
class Soprano(Vocalist):
    def __init__(self):
        Vocalist.__init__(self)
        
        self.instrumentName = 'Soprano'
        self.instrumentAbbreviation = 'S'
        
class MezzoSoprano(Soprano):
    def __init__(self):
        Soprano.__init__(self)
        
        self.instrumentName = 'Mezzo-Soprano'
        self.instrumentAbbreviation = 'Mez'
        
class Alto(Vocalist):
    def __init__(self):
        Vocalist.__init__(self)
        
        self.instrumentName = 'Alto'
        self.instrumentAbbreviation = 'A'

class Tenor(Vocalist):
    def __init__(self):
        Vocalist.__init__(self)
        
        self.instrumentName = 'Tenor'
        self.instrumentAbbreviation = 'T'
        
class Baritone(Vocalist):
    def __init__(self):
        Vocalist.__init__(self)
        
        self.instrumentName = 'Baritone'
        self.instrumentAbbreviation = 'Bar'

class Bass(Vocalist):
    def __init__(self):
        Vocalist.__init__(self)
        
        self.instrumentName = 'Bass'
        self.instrumentAbbreviation = 'B'

 
#------------------------------------------------------------------------------


ensembleNamesBySize = ['no performers', 'solo', 'duet', 'trio', 'quartet', 
                       'quintet', 'sextet', 'septet', 'octet', 'nonet', 'dectet', 
                       'undectet', 'duodectet', 'tredectet', 'quattuordectet', 
                       'quindectet', 'sexdectet', 'septendectet', 'octodectet', 
                       'novemdectet', 'vigetet', 'unvigetet', 'duovigetet', 
                       'trevigetet', 'quattuorvigetet', 'quinvigetet', 'sexvigetet', 
                       'septenvigetet', 'octovigetet', 'novemvigetet', 
                       'trigetet', 'untrigetet', 'duotrigetet', 'tretrigetet', 
                       'quottuortrigetet', 'quintrigetet', 'sextrigetet', 
                       'septentrigetet', 'octotrigetet', 'novemtrigetet', 
                       'quadragetet', 'unquadragetet', 'duoquadragetet', 
                       'trequadragetet', 'quattuorquadragetet', 'quinquadragetet', 
                       'sexquadragetet', 'octoquadragetet', 'octoquadragetet', 
                       'novemquadragetet', 'quinquagetet', 'unquinquagetet', 
                       'duoquinquagetet', 'trequinguagetet', 'quattuorquinquagetet', 
                       'quinquinquagetet', 'sexquinquagetet', 'septenquinquagetet', 
                       'octoquinquagetet', 'novemquinquagetet', 'sexagetet', 
                       'undexagetet', 'duosexagetet', 'tresexagetet', 
                       'quoattuorsexagetet', 'quinsexagetet', 'sexsexagetet', 
                       'septensexagetet', 'octosexagetet', 'novemsexagetet', 
                       'septuagetet', 'unseptuagetet', 'duoseptuagetet', 'treseptuagetet', 
                       'quattuorseptuagetet', 'quinseptuagetet', 'sexseptuagetet', 
                       'septenseptuagetet', 'octoseptuagetet', 'novemseptuagetet', 
                       'octogetet', 'unoctogetet', 'duooctogetet', 
                       'treoctogetet', 'quattuoroctogetet', 'quinoctogetet', 
                       'sexoctogetet', 'septoctogetet', 'octooctogetet', 
                       'novemoctogetet', 'nonagetet', 'unnonagetet', 'duononagetet', 
                       'trenonagetet', 'quattuornonagetet', 'quinnonagetet', 
                       'sexnonagetet', 'septennonagetet', 'octononagetet', 
                       'novemnonagetet', 'centet'] 
        
def ensembleNameBySize(number):
    '''
    return the name of a generic ensemble with "number" players:
    
    
    >>> instrument.ensembleNameBySize(4)
    'quartet'
    >>> instrument.ensembleNameBySize(1)
    'solo'
    >>> instrument.ensembleNameBySize(83)
    'treoctogetet'
    '''
    if number > 100:
        raise InstrumentException('okay, youre on your own for this one buddy')
    elif number < 0:
        raise InstrumentException('okay, youre on your own for this one buddy')
    else:
        return ensembleNamesBySize[int(number)]


def instrumentFromMidiProgram(number):
    '''
    return the instrument with "number" as its assigned midi program:
    
    >>> instrument.instrumentFromMidiProgram(0)
    <music21.instrument.Instrument Piano>
    >>> instrument.instrumentFromMidiProgram(21)
    <music21.instrument.Instrument Accordion>
    >>> instrument.instrumentFromMidiProgram(500)
    Traceback (most recent call last):
        ...
    InstrumentException: No instrument found with given midi program    
    '''    
    foundInstrument = False
    for myThing in sys.modules[__name__].__dict__.values():
        try: 
            i = myThing()
            mp = getattr(i, 'midiProgram')
            if mp == number:
                foundInstrument = True
                return i
        except (AttributeError, TypeError):
            pass
    if not foundInstrument:
        raise InstrumentException('No instrument found with given midi program')

    

def partitionByInstrument(streamObj):
    '''
    Given a single Stream, or a Score or similar multi-part structure, 
    partition into a Part for each unique Instrument, joining events 
    possibly from different parts.
    
    >>> p1 = converter.parse("tinynotation: 4/4 c4  d  e  f  g  a  b  c'  c1")
    >>> p2 = converter.parse("tinynotation: 4/4 C#4 D# E# F# G# A# B# c#  C#1")

    >>> p1.getElementsByClass('Measure')[0].insert(0.0, instrument.Piccolo())
    >>> p1.getElementsByClass('Measure')[0].insert(2.0, instrument.AltoSaxophone())
    >>> p1.getElementsByClass('Measure')[1].insert(3.0, instrument.Piccolo())
    
    >>> p2.getElementsByClass('Measure')[0].insert(0.0, instrument.Trombone())
    >>> p2.getElementsByClass('Measure')[0].insert(3.0, instrument.Piccolo()) # not likely...
    >>> p2.getElementsByClass('Measure')[1].insert(1.0, instrument.Trombone())
    
    >>> s = stream.Score()
    >>> s.insert(0, p1)
    >>> s.insert(0, p2)
    >>> s.show('text')
    {0.0} <music21.stream.Part ...>
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.instrument.Instrument Piccolo>
            {0.0} <music21.clef.TrebleClef>
            {0.0} <music21.meter.TimeSignature 4/4>
            {0.0} <music21.note.Note C>
            {1.0} <music21.note.Note D>
            {2.0} <music21.instrument.Instrument Alto Saxophone>
            {2.0} <music21.note.Note E>
            {3.0} <music21.note.Note F>
        {4.0} <music21.stream.Measure 2 offset=4.0>
            {0.0} <music21.note.Note G>
            {1.0} <music21.note.Note A>
            {2.0} <music21.note.Note B>
            {3.0} <music21.instrument.Instrument Piccolo>
            {3.0} <music21.note.Note C>
        {8.0} <music21.stream.Measure 3 offset=8.0>
            {0.0} <music21.note.Note C>
            {4.0} <music21.bar.Barline style=final>
    {0.0} <music21.stream.Part ...>
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.instrument.Instrument Trombone>
            {0.0} <music21.clef.BassClef>
            {0.0} <music21.meter.TimeSignature 4/4>
            {0.0} <music21.note.Note C#>
            {1.0} <music21.note.Note D#>
            {2.0} <music21.note.Note E#>
            {3.0} <music21.instrument.Instrument Piccolo>
            {3.0} <music21.note.Note F#>
        {4.0} <music21.stream.Measure 2 offset=4.0>
            {0.0} <music21.note.Note G#>
            {1.0} <music21.instrument.Instrument Trombone>
            {1.0} <music21.note.Note A#>
            {2.0} <music21.note.Note B#>
            {3.0} <music21.note.Note C#>
        {8.0} <music21.stream.Measure 3 offset=8.0>
            {0.0} <music21.note.Note C#>
            {4.0} <music21.bar.Barline style=final>

    >>> s2 = instrument.partitionByInstrument(s)
    >>> len(s2.parts)
    3
    
    # TODO: this step might not be necessary...
    
    >>> for p in s2.parts:
    ...     unused = p.makeRests(fillGaps=True, inPlace=True)
    
    # TODO: this step SHOULD not be necessary (measureTemplate)...
    
    >>> for p in s2.parts:
    ...     p.makeMeasures(inPlace = True)
    ...     p.makeTies(inPlace = True)
    
    >>> s2.show('text')
    {0.0} <music21.stream.Part Piccolo>
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.instrument.Instrument Piccolo>
            {0.0} <music21.clef.TrebleClef>
            {0.0} <music21.meter.TimeSignature 4/4>
            {0.0} <music21.note.Note C>
            {1.0} <music21.note.Note D>
            {2.0} <music21.note.Rest rest>
            {3.0} <music21.note.Note F#>
        {4.0} <music21.stream.Measure 2 offset=4.0>
            {0.0} <music21.note.Note G#>
            {1.0} <music21.note.Rest rest>
            {3.0} <music21.note.Note C>
        {8.0} <music21.stream.Measure 3 offset=8.0>
            {0.0} <music21.note.Note C>
            {4.0} <music21.bar.Barline style=final>
    {0.0} <music21.stream.Part Trombone>
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.instrument.Instrument Trombone>
            {0.0} <music21.clef.BassClef>
            {0.0} <music21.meter.TimeSignature 4/4>
            {0.0} <music21.note.Note C#>
            {1.0} <music21.note.Note D#>
            {2.0} <music21.note.Note E#>
            {3.0} <music21.note.Rest rest>
        {4.0} <music21.stream.Measure 2 offset=4.0>
            {0.0} <music21.note.Rest rest>
            {1.0} <music21.note.Note A#>
            {2.0} <music21.note.Note B#>
            {3.0} <music21.note.Note C#>
        {8.0} <music21.stream.Measure 3 offset=8.0>
            {0.0} <music21.note.Note C#>
            {4.0} <music21.bar.Barline style=final>
    {0.0} <music21.stream.Part Alto Saxophone>
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.instrument.Instrument Alto Saxophone>
            {0.0} <music21.clef.TrebleClef>
            {0.0} <music21.meter.TimeSignature 4/4>
            {2.0} <music21.note.Note E>
            {3.0} <music21.note.Note F>
        {4.0} <music21.stream.Measure 2 offset=4.0>
            {0.0} <music21.instrument.Instrument Alto Saxophone>
            {0.0} <music21.note.Note G>
            {1.0} <music21.note.Note A>
            {2.0} <music21.note.Note B>
            {3.0} <music21.bar.Barline style=final>


    Bug in makeRests -- notice the missing rest at the beginning of the alto sax part...

    TODO: parts should be in Score Order. Cooindicence that this works.
    TODO: note redundant Alto Saxophone...
    '''
    from music21 import stream

    if not streamObj.hasPartLikeStreams():
        # place in a score for uniform operations
        s = stream.Score()
        s.insert(0, streamObj.flat)
    else:
        s = stream.Score()
        # append flat parts
        for sub in streamObj.getElementsByClass('Stream'):
            s.insert(0, sub.flat)

    # first, lets extend the duration of each instrument to match stream
    for sub in s.getElementsByClass('Stream'):
        sub.extendDuration('Instrument')

    # first, find all unique instruments
    found = s.flat.getElementsByClass('Instrument')
    if len(found) == 0:
        return None # no partition is available
    
    names = OrderedDict() # store unique names
    for e in found:
        # matching here by instrument name
        if e.instrumentName not in names:
            names[e.instrumentName] = {'Instrument':e} # just store one instance
        
    # create a return object that has a part for each instrument
    post = stream.Score()
    for iName in names:
        p = stream.Part()
        p.id = iName
        # add the instrument instance
        p.insert(0, names[iName]['Instrument'])
        # store a handle to this part
        names[iName]['Part'] = p
        post.insert(0, p)

    # iterate over flat sources; get events within each defined instrument
    # add to corresponding part
    for sub in s:
        for i in sub.getElementsByClass('Instrument'):
            start = i.offset 
            # duration will have been set with sub.extendDuration above
            end = i.offset + i.duration.quarterLength
            # get destination Part
            p = names[i.instrumentName]['Part']
            coll = sub.getElementsByOffset(start, end, 
                    # do not include elements that start at the end
                    includeEndBoundary=False, 
                    mustFinishInSpan=False, mustBeginInSpan=True)
            # add to part at original offset
            # do not gather instrument
            for e in coll.getElementsNotOfClass('Instrument'):
                p.insert(sub.elementOffset(e), e)
    return post



def _combinations(instrumentString):
    sampleList = instrumentString.split()
    allComb = []
    for size in range(1,len(sampleList)+1):
        for i in range(len(sampleList)-size+1):
            allComb.append(u" ".join(sampleList[i:i+size]))
    return allComb

def fromString(instrumentString):
    """
    Given a string with instrument content (from an orchestral score
    for example), attempts to return an appropriate
    :class:`~music21.instrument.Instrument`.
    
    >>> from music21 import instrument
    >>> t1 = instrument.fromString("Clarinet 2 in A")
    >>> t1
    <music21.instrument.Instrument Clarinet>
    >>> t1.transposition
    <music21.interval.Interval m-3>
    
    >>> t2 = instrument.fromString("Clarinetto 3")
    >>> t2
    <music21.instrument.Instrument Clarinet>
    
    >>> t3 = instrument.fromString("Flauto 2")
    >>> t3
    <music21.instrument.Instrument Flute>
    
    
    Excess information is ignored, and the useful information can be extracted
    correctly as long as it's sequential.
    
    
    >>> t4 = instrument.fromString("I <3 music saxofono tenor go beavers")
    >>> t4
    <music21.instrument.Instrument Tenor Saxophone>
    
    
    #_OMIT_FROM_DOCS
    
    
    >>> t5 = instrument.fromString("Bb Clarinet")
    >>> t5
    <music21.instrument.Instrument Clarinet>
    >>> t5.transposition
    <music21.interval.Interval M-2>

    >>> t6 = instrument.fromString("Clarinet in B-flat")
    >>> t5.bestName() == t6.bestName() and t5.transposition == t6.transposition
    True

    >>> t7 = instrument.fromString("B-flat Clarinet")
    >>> t5.bestName() == t7.bestName() and t5.transposition == t7.transposition
    True
    
    >>> t8 = instrument.fromString("Eb Clarinet")
    >>> t5.bestName() == t8.bestName()
    True
    >>> t8.transposition
    <music21.interval.Interval m3>
    """
    from music21.languageExcerpts import instrumentLookup
    allCombinations = _combinations(instrumentString)
    # First task: Find the best instrument.
    bestInstClass = None
    bestInstrument = None
    bestName = None
    for substring in allCombinations:
        try:
            if six.PY2:
                englishName = instrumentLookup.allToBestName[unicode(substring.lower())] # pylint: disable=undefined-variable
            else:
                englishName = instrumentLookup.allToBestName[substring.lower()]
            className = instrumentLookup.bestNameToInstrumentClass[englishName]
            thisInstClass = globals()[className]        
            thisInstClassParentClasses = [parentcls.__name__ for parentcls in thisInstClass.mro()]
            if 'Instrument' not in thisInstClassParentClasses or \
                'Music21Object' not in thisInstClassParentClasses:
                # little bit of security against calling another global...
                raise KeyError

            thisInstrument = thisInstClass()
            thisBestName = thisInstrument.bestName().lower()
            if bestInstClass is None or len(thisBestName.split())\
                    >= len(bestName.split()) and not issubclass(bestInstClass, thisInstClass):
                # priority is also given to same length instruments which fall later
                # on in the string (i.e. Bb Piccolo Trumpet)
                bestInstClass = thisInstClass
                bestInstrument = thisInstrument
                bestName = thisBestName
        except KeyError:
            pass
    if bestInstClass is None:
        raise InstrumentException("Could not match string with instrument: {0}".format(instrumentString))
    if bestName not in instrumentLookup.transposition:
        return bestInstrument

    # A transposition table is defined for the instrument.
    # Second task: Determine appropriate transposition (if any)
    for substring in allCombinations:
        try:
            if six.PY2:
                bestPitch = instrumentLookup.pitchFullNameToName[unicode(substring.lower())] # pylint: disable=undefined-variable
            else:
                bestPitch = instrumentLookup.pitchFullNameToName[substring.lower()]
            bestInterval = instrumentLookup.transposition[bestName][bestPitch]
            bestInstrument.transposition = interval.Interval(bestInterval)
            break
        except KeyError:
            pass
    return bestInstrument






#-------------------------------------------------------------------------------
class TestExternal(unittest.TestCase):
    
    def runTest(self):
        pass
    

class Test(unittest.TestCase):
    
    def runTest(self):
        pass

    def testCopyAndDeepcopy(self):
        '''Test copying all objects defined in this module
        '''
        import types
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
                i = copy.copy(obj)
                j = copy.deepcopy(obj)


    def testMusicXMLExport(self):
        from music21 import stream, note

        s1 = stream.Stream()
        i1 = Violin()
        i1.partName = 'test'
        s1.append(i1)
        s1.repeatAppend(note.Note(), 10)
        #s.show()

        s2 = stream.Stream()
        i2 = Piano()
        i2.partName = 'test2'
        s2.append(i2)
        s2.repeatAppend(note.Note('g4'), 10)

        s3 = stream.Score()
        s3.insert(0, s1)
        s3.insert(0, s2)

        #s3.show()


    def testPartitionByInstrumentA(self):
        from music21 import instrument, stream

        # basic case of instruments in Parts
        s = stream.Score()
        p1 = stream.Part() 
        p1.append(instrument.Piano())
        
        p2 = stream.Part() 
        p2.append(instrument.Piccolo())
        s.insert(0, p1)
        s.insert(0, p2)

        post = instrument.partitionByInstrument(s)
        self.assertEqual(len(post), 2)
        self.assertEqual(len(post.flat.getElementsByClass('Instrument')), 2)

        #post.show('t')


        # one Stream with multiple instruments
        s = stream.Stream()
        s.insert(0, instrument.PanFlute())
        s.insert(20, instrument.ReedOrgan())
        
        post = instrument.partitionByInstrument(s)
        self.assertEqual(len(post), 2)
        self.assertEqual(len(post.flat.getElementsByClass('Instrument')), 2)
        #post.show('t')


    def testPartitionByInstrumentB(self):
        from music21 import instrument, stream, note

        # basic case of instruments in Parts
        s = stream.Score()
        p1 = stream.Part() 
        p1.append(instrument.Piano())
        p1.repeatAppend(note.Note(), 6)
        
        p2 = stream.Part() 
        p2.append(instrument.Piccolo())
        p2.repeatAppend(note.Note(), 12)
        s.insert(0, p1)
        s.insert(0, p2)

        post = instrument.partitionByInstrument(s)
        self.assertEqual(len(post), 2)
        self.assertEqual(len(post.flat.getElementsByClass('Instrument')), 2)
        self.assertEqual(len(post.parts[0].notes), 6)
        self.assertEqual(len(post.parts[1].notes), 12)


    def testPartitionByInstrumentC(self):
        from music21 import instrument, stream, note

        # basic case of instruments in Parts
        s = stream.Score()
        p1 = stream.Part() 
        p1.append(instrument.Piano())
        p1.repeatAppend(note.Note('a'), 6)
        # will go in next available offset
        p1.append(instrument.AcousticGuitar())
        p1.repeatAppend(note.Note('b'), 3)
        
        p2 = stream.Part() 
        p2.append(instrument.Piccolo())
        p2.repeatAppend(note.Note('c'), 2)
        p2.append(instrument.Flute())
        p2.repeatAppend(note.Note('d'), 4)

        s.insert(0, p1)
        s.insert(0, p2)

        post = instrument.partitionByInstrument(s)
        self.assertEqual(len(post), 4) # 4 instruments
        self.assertEqual(len(post.flat.getElementsByClass('Instrument')), 4)
        self.assertEqual(post.parts[0].getInstrument().instrumentName, 'Piano')
        self.assertEqual(len(post.parts[0].notes), 6)
        self.assertEqual(post.parts[1].getInstrument().instrumentName, 'Piccolo')
        self.assertEqual(len(post.parts[1].notes), 2)
        self.assertEqual(post.parts[2].getInstrument().instrumentName, 'Flute')
        self.assertEqual(len(post.parts[2].notes), 4)
        self.assertEqual(post.parts[3].getInstrument().instrumentName, 'Acoustic Guitar')
        self.assertEqual(len(post.parts[3].notes), 3)

        #environLocal.printDebug(['post processing'])
        #post.show('t')


    def testPartitionByInstrumentD(self):
        from music21 import instrument, stream, note

        # basic case of instruments in Parts
        s = stream.Score()
        p1 = stream.Part() 
        p1.append(instrument.Piano())
        p1.repeatAppend(note.Note('a'), 6)
        # will go in next available offset
        p1.append(instrument.AcousticGuitar())
        p1.repeatAppend(note.Note('b'), 3)
        p1.append(instrument.Piano())
        p1.repeatAppend(note.Note('e'), 5)
        
        p2 = stream.Part() 
        p2.append(instrument.Piccolo())
        p2.repeatAppend(note.Note('c'), 2)
        p2.append(instrument.Flute())
        p2.repeatAppend(note.Note('d'), 4)
        p2.append(instrument.Piano())
        p2.repeatAppend(note.Note('f'), 1)

        s.insert(0, p1)
        s.insert(0, p2)

        post = instrument.partitionByInstrument(s)
        self.assertEqual(len(post), 4) # 4 instruments
        self.assertEqual(len(post.flat.getElementsByClass('Instrument')), 4)
        # piano spans are joined together
        self.assertEqual(post.parts[0].getInstrument().instrumentName, 'Piano')
        self.assertEqual(len(post.parts[0].notes), 12)

        self.assertEqual([n.offset for n in post.parts[0].notes], [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 9.0, 10.0, 11.0, 12.0, 13.0])

        #environLocal.printDebug(['post processing'])
        #post.show('t')


    def testPartitionByInstrumentE(self):
        from music21 import instrument, stream, note

        # basic case of instruments in Parts
        #s = stream.Score()
        p1 = stream.Part() 
        p1.append(instrument.Piano())
        p1.repeatAppend(note.Note('a'), 6)
        # will go in next available offset
        p1.append(instrument.AcousticGuitar())
        p1.repeatAppend(note.Note('b'), 3)
        p1.append(instrument.Piano())
        p1.repeatAppend(note.Note('e'), 5)
        
        p1.append(instrument.Piccolo())
        p1.repeatAppend(note.Note('c'), 2)
        p1.append(instrument.Flute())
        p1.repeatAppend(note.Note('d'), 4)
        p1.append(instrument.Piano())
        p1.repeatAppend(note.Note('f'), 1)

        s = p1

        post = instrument.partitionByInstrument(s)
        self.assertEqual(len(post), 4) # 4 instruments
        self.assertEqual(len(post.flat.getElementsByClass('Instrument')), 4)
        # piano spans are joined together
        self.assertEqual(post.parts[0].getInstrument().instrumentName, 'Piano')
        self.assertEqual(len(post.parts[0].notes), 12)
        offsetList = []
        ppn = post.parts[0].notes
        for n in ppn:
            offsetList.append(n.offset)

        self.assertEqual(offsetList, [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 9.0, 10.0, 11.0, 12.0, 13.0, 20.0])


    def testPartitionByInstrumentF(self):
        from music21 import instrument, stream, note

        s1 = stream.Stream()
        s1.append(instrument.AcousticGuitar())
        s1.append(note.Note())
        s1.append(instrument.Tuba())
        s1.append(note.Note())

        post = instrument.partitionByInstrument(s1)
        self.assertEqual(len(post), 2) # 4 instruments




#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [Instrument]


if __name__ == "__main__":
    # sys.arg test options will be used in mainTest()
    import music21
    music21.mainTest(Test)



#------------------------------------------------------------------------------
# eof

