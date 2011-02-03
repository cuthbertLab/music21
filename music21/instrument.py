#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         instrument.py
# Purpose:      Class for basic instrument information
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#               Neena Parikh
#
# Copyright:    (c) 2009-11 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

'''
This module represents instruments through objects that contain general information
such as Metadata for instrument names, classifications, transpositions and default 
MIDI program numbers.  It also contains information specific to each instrument
or instrument family, such as string pitches, etc.  Information about instrumental
ensembles is also included here though it may later be separated out into its own
ensemble.py module. 
'''

import unittest, doctest

import music21
from music21 import musicxml
from music21 import common
from music21 import defaults
from music21 import pitch
from music21 import interval
from music21.musicxml import translate as musicxmlTranslate

from music21 import environment
_MOD = "instrument.py"
environLocal = environment.Environment(_MOD)

#def fromName(name):
#    '''
#    returns a new Instrument object of the proper class given
#    a name as a string.  Currently must be uppercase first letter,
#    lower for rest.
#    '''
#    eval(name + "()")


class InstrumentException(Exception):
    pass

class Instrument(music21.Music21Object):
    '''
    Base class for all musical instruments.  Designed
    for subclassing, though usually a more specific
    instrument class (such as StringInstrument) would
    be better to subclass.
    '''
    
    classSortOrder = 1

    def __init__(self):
        music21.Music21Object.__init__(self)

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

        self.transposition = None

    def __str__(self):
        return '%s: %s: %s' % (self.partId, self.partName, self.instrumentName)

    def __repr__(self):
        return "<music21.instrument.Instrument %s>" % self.__str__()

    def bestName(self):
        '''Find a viable name, looking first at instrument, then part, then 
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
        '''Force a unique id by using an MD5
        '''
        idNew = 'P%s' % common.getMd5()
        #environLocal.printDebug(['incrementing instrument from', 
        #                         self.partId, 'to', idNew])
        self.partId = idNew
         
    def instrumentIdRandomize(self):
        '''Force a unique id by using an MD5
        '''
        idNew = 'I%s' % common.getMd5()
        #environLocal.printDebug(['incrementing instrument from', 
        #                         self.partId, 'to', idNew])
        self.instrumentId = idNew
         

    def autoAssignMidiChannel(self, usedChannels=[]):
        '''
        Assign an unused midi channel given a list of
        used ones.

        assigns the number to self.midiChannel and returns
        it as an int.

        Note that midi channel 10 is special, and
        thus is skipped.

        Currently only 16 channels are used.

        >>> from music21 import instrument
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
        maxMidi = 16
        filter = []
        for e in usedChannels:
            if e != None:
                filter.append(e)

        if len(filter) == 0:
            self.midiChannel = 0
            return 0
        elif len(filter) >= maxMidi:
            raise InstrumentException("we are out of midi channels! help!")
        else:
            for ch in range(maxMidi):
                if ch in filter:
                    continue
                elif ch % 16 == 10:
                    continue # skip 10 /perc for now
                else:
                    self.midiChannel = ch
                    return ch
            raise InstrumentException("we are out of midi channels and this was not already detected PROGRAM BUG!")
            


    #---------------------------------------------------------------------------
    def _getMX(self):
        '''Return a mxScorePart based on this instrument.
        '''
        return musicxmlTranslate.instrumentToMx(self)


#         '''
#         >>> from music21 import *
#         >>> i = instrument.Celesta()
#         >>> mxScorePart = i.mx
#         >>> len(mxScorePart.scoreInstrumentList)
#         1
#         >>> mxScorePart.scoreInstrumentList[0].instrumentName
#         'Celesta'
#         >>> mxScorePart.midiInstrumentList[0].midiProgram
#         9
#         '''
#         mxScorePart = musicxml.ScorePart()
# 
#         # get a random id if None set
#         if self.partId == None:
#             self.partIdRandomize()
# 
#         if self.instrumentId == None:
#             self.instrumentIdRandomize()
# 
#         # note: this is id, not partId!
#         mxScorePart.set('id', self.partId)
# 
#         if self.partName != None:
#             mxScorePart.partName = self.partName
#         elif self.partName == None: # get default, as required
#             mxScorePart.partName = defaults.partName
# 
#         if self.partAbbreviation != None:
#             mxScorePart.partAbbreviation = self.partAbbreviation
# 
#         if self.instrumentName != None or self.instrumentAbbreviation != None:
#             mxScoreInstrument = musicxml.ScoreInstrument()
#             # set id to same as part for now
#             mxScoreInstrument.set('id', self.instrumentId)
#             # can set these to None
#             mxScoreInstrument.instrumentName = self.instrumentName
#             mxScoreInstrument.instrumentAbbreviation = self.instrumentAbbreviation
#             # add to mxScorePart
#             mxScorePart.scoreInstrumentList.append(mxScoreInstrument)
# 
#         if self.midiProgram != None:
#             mxMIDIInstrument = musicxml.MIDIInstrument()
#             mxMIDIInstrument.set('id', self.instrumentId)
#             # shift to start from 1
#             mxMIDIInstrument.midiProgram = self.midiProgram + 1 
# 
#             if self.midiChannel == None:
#                 # TODO: need to allocate channels from a higher level
#                 self.autoAssignMidiChannel()
#             mxMIDIInstrument.midiChannel = self.midiChannel + 1
#             # add to mxScorePart
#             mxScorePart.midiInstrumentList.append(mxMIDIInstrument)
# 
#         return mxScorePart
        

    def _setMX(self, mxScorePart):
        '''
        provide a score part object
        '''
        # load an instrument from a ScorePart into self
        musicxmlTranslate.mxToInstrument(mxScorePart, self)
        
#         self.partId = mxScorePart.get('id')
#         self.partName = mxScorePart.get('partName')
#         self.partAbbreviation = mxScorePart.get('partAbbreviation')
# 
#         # for now, just get first instrument
#         if len(mxScorePart.scoreInstrumentList) > 0:
#             mxScoreInstrument = mxScorePart.scoreInstrumentList[0]
#             self.instrumentName = mxScoreInstrument.get('instrumentName')
#             self.instrumentAbbreviation = mxScoreInstrument.get(
#                                             'instrumentAbbreviation')
#         if len(mxScorePart.midiInstrumentList) > 0:
#             # for now, just get first midi instrument
#             mxMIDIInstrument = mxScorePart.midiInstrumentList[0]
#             # musicxml counts from 1, not zero
#             mp = mxMIDIInstrument.get('midiProgram')
#             if mp is not None:
#                 self.midiProgram = int(mp) - 1
#             mc = mxMIDIInstrument.get('midiChannel')
#             if mc is not None:
#                 self.midiChannel = int(mc) - 1

    mx = property(_getMX, _setMX)



#-------------------------------------------------------------------------------
class KeyboardInstrument(Instrument):

    def __init__(self):
        Instrument.__init__(self)

class Piano(KeyboardInstrument):   
    '''
    >>> import music21
    >>> p = music21.instrument.Piano()
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

class Celesta(KeyboardInstrument):   
    def __init__(self):
        KeyboardInstrument.__init__(self)

        self.instrumentName = 'Celesta'
        self.instrumentAbbreviation = 'Clst'
        self.midiProgram = 8


#------------------------------------------------------
class StringInstrument(Instrument):

    def __init__(self):
        Instrument.__init__(self)

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
            highest[#reentrant]_
            
            >>> vln1 = Violin()
            >>> vln1.stringPitches
            [G3, D4, A4, E5]
            
            instrument.stringPitches are full pitch objects, not just names
            >>> [x.octave for x in vln1.stringPitches]
            [3, 4, 4, 5]
            
            scordatura for Scelsi's *Anahit*. N.B. string to pitch conversion
            >>> vln1.stringPitches = ["G3","G4","B4","D4"]
            >>> vln1.stringPitches
            [G3, G4, B4, D4]
            
            ..[#reentrant] In some tuning methods such as reentrant tuning on the ukulele,
            lute, or five-string banjo the order might not strictly be from lowest to
            highest.  The same would hold true for certain violin scordatura pieces, such
            as some of Biber's *Mystery Sonatas*
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
    For the Contrabass, the stringPitches attribute refers to the sounding pitches
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
        BrassInstrument.__init__(self)

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
        self.transposition = interval.Interval('M-2')

class BassClarinet(Clarinet):
    '''
    >>> from music21 import *
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

        self.midiProgram = 61

class Horn(BrassInstrument):
    '''
    >>> from music21 import *
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

class Tuba(BrassInstrument):
    def __init__(self):
        BrassInstrument.__init__(self)

        self.instrumentName = 'Tuba'
        self.instrumentAbbreviation = 'Tba'
        self.midiProgram = 58

        self.lowestNote = pitch.Pitch('E-2')

    
#---------
class PitchedPercussion(Instrument):
    pass

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
        
class TubularBells(PitchedPercussion):
    def __init__(self):
        PitchedPercussion.__init__(self)
        
        self.instrumentName = 'Tubular Bells'
        #TODO: self.instrumentAbbreviation = ''
        self.midiProgram = 14
        
class Celesta(PitchedPercussion):   
    def __init__(self):
        PitchedPercussion.__init__(self)

        self.instrumentName = 'Celesta'
        self.instrumentAbbreviation = 'Clst'
        self.midiProgram = 8
        
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



#-------------
class Percussion(Instrument):
    pass

class Woodblock(Percussion):
    def __init__(self):
        Percussion.__init__(self)
        
        self.instrumentName = 'Woodblock'
        self.instrumentAbbreviation = 'Wd Bl'
        self.midiProgram = 115
        
class TempleBlock(Percussion):
    def __init__(self):
        Percussion.__init__(self)
        
        self.instrumentName = 'Temple Block'
        self.instrumentAbbreviation = 'Temp Bl'
        
class Castanets(Percussion):
    def __init__(self):
        Percussion.__init__(self)
        
        self.instrumentName = 'Castanets'
        self.instrumentAbbreviation = 'Cas'
        
class Maracas(Percussion):
    def __init__(self):
        Percussion.__init__(self)
        
        self.instrumentName = 'Maracas'
        #TODO: self.instrumentAbbreviation = ''
        
class FingerCymbals(Percussion):
    def __init__(self):
        Percussion.__init__(self)
        
        self.instrumentName = 'Finger Cymbals'
        self.instrumentAbbreviation = 'Fing Cym'
        
class CrashCymbals(Percussion):
    def __init__(self):
        Percussion.__init__(self)
        
        self.instrumentName = 'Crash Cymbals'
        self.instrumentAbbreviation = 'Cym'
        
class SuspendedCymbal(Percussion):
    def __init__(self):
        Percussion.__init__(self)
        
        self.instrumentName = 'Suspended Cymbal'
        #TODO: self.instrumentAbbreviation = ''
        
class SizzleCymbal(Percussion):
    def __init__(self):
        Percussion.__init__(self)
        
        self.instrumentName = 'Sizzle Cymbal'
        #TODO: self.instrumentAbbreviation = ''
        
class HiHatCymbal(Percussion):
    def __init__(self):
        Percussion.__init__(self)
        
        self.instrumentName = 'Hi-Hat Cymbal'
        #TODO: self.instrumentAbbreviation = ''
        
class Triangle(Percussion):
    def __init__(self):
        Percussion.__init__(self)
        
        self.instrumentName = 'Triangle'
        self.instrumentAbbreviation = 'Tri'
        
class Cowbells(Percussion):
    def __init__(self):
        Percussion.__init__(self)
        
        self.instrumentName = 'Cowbells'
        self.instrumentAbbreviation = 'Cwb'
        
class Agogo(Percussion):
    def __init__(self):
        Percussion.__init__(self)
        
        self.instrumentName = 'Agogo'
        #TODO: self.instrumentAbbreviation = ''        
        self.midiProgram = 113

class TamTam(Percussion):
    def __init__(self):
        Percussion.__init__(self)
        
        self.instrumentName = 'Tam-Tam'
        #TODO: self.instrumentAbbreviation = ''
        
class SleighBells(Percussion):
    def __init__(self):
        Percussion.__init__(self)
        
        self.instrumentName = 'Sleigh Bells'
        #TODO: self.instrumentAbbreviation = ''
        
class SnareDrum(Percussion):
    def __init__(self):
        Percussion.__init__(self)
        
        self.instrumentName = 'Snare Drum'
        self.instrumentAbbreviation = 'Sn Dr'
    
class TenorDrum(Percussion):
    def __init__(self):
        Percussion.__init__(self)
        
        self.instrumentName = 'Tenor Drum'
        self.instrumentAbbreviation = 'Ten Dr'

class BongoDrums(Percussion):
    def __init__(self):
        Percussion.__init__(self)
        
        self.instrumentName = 'Bongo Drums'
        self.instrumentAbbreviation = 'Bgo Dr'
    
class TomTom(Percussion):
    def __init__(self):
        Percussion.__init__(self)
        
        self.instrumentName = 'Tom-Tom'
        #TODO: self.instrumentAbbreviation = ''
    
class Timbales(Percussion):
    def __init__(self):
        Percussion.__init__(self)
        
        self.instrumentName = 'Timbales'
        self.instrumentAbbreviation = 'Tim'
        
class CongaDrum(Percussion):
    def __init__(self):
        Percussion.__init__(self)
        
        self.instrumentName = 'Conga Drum'
        self.instrumentAbbreviation = 'Cga Dr'
        
class BassDrum(Percussion):
    def __init__(self):
        Percussion.__init__(self)
        
        self.instrumentName = 'Bass Drum'
        self.instrumentAbbreviation = 'B Dr'
        
class Taiko(Percussion):
    def __init__(self):
        Percussion.__init__(self)
        
        self.instrumentName = 'Taiko'
        #TODO: self.instrumentAbbreviation = ''
        self.midiProgram = 116
        
class Tambourine(Percussion):
    def __init__(self):
        Percussion.__init__(self)
        
        self.instrumentName = 'Tambourine'
        self.instrumentAbbreviation = 'Tmbn'
        
class Whip(Percussion):
    def __init__(self):
        Percussion.__init__(self)
        
        self.instrumentName = 'Whip'
        #TODO: self.instrumentAbbreviation = ''
        
class Ratchet(Percussion):
    def __init__(self):
        Percussion.__init__(self)
        
        self.instrumentName = 'Ratchet'
        #TODO: self.instrumentAbbreviation = ''
        
class Siren(Percussion):
    def __init__(self):
        Percussion.__init__(self)
        
        self.instrumentName = 'Siren'
        #TODO: self.instrumentAbbreviation = ''
        
class SandpaperBlocks(Percussion):
    def __init__(self):
        Percussion.__init__(self)
        
        self.instrumentName = 'Sandpaper Blocks'
        self.instrumentAbbreviation = 'Sand Bl'
        
class WindMachine(Percussion):
    def __init__(self):
        Percussion.__init__(self)
        
        self.instrumentName = 'Wind Machine'
        #TODO: self.instrumentAbbreviation = ''


#------------------------------------------------------

class Voice(Instrument):
    def __init__(self):
        Instrument.__init__(self)

        self.midiProgram = 52
        
class Soprano(Voice):
    def __init__(self):
        Voice.__init__(self)
        
        self.instrumentName = 'Soprano'
        self.instrumentAbbreviation = 'S'
        
class MezzoSoprano(Voice):
    def __init__(self):
        Voice.__init__(self)
        
        self.instrumentName = 'Mezzo-Soprano'
        self.instrumentAbbreviation = 'Mez'
        
class Contralto(Voice):
    def __init__(self):
        Voice.__init__(self)
        
        self.instrumentName = 'Contralto'
        self.instrumentAbbreviation = 'C'

class Tenor(Voice):
    def __init__(self):
        Voice.__init__(self)
        
        self.instrumentName = 'Tenor'
        self.instrumentAbbreviation = 'T'
        
class Baritone(Voice):
    def __init__(self):
        Voice.__init__(self)
        
        self.instrumentName = 'Baritone'
        self.instrumentAbbreviation = 'Bar'
 
#------------------------------------------------------       
class InstrumentException(music21.Music21Exception):
    pass

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
    
    >>> from music21 import *
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
        import sys, types, copy
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
                a = copy.copy(obj)
                b = copy.deepcopy(obj)


    def testMusicXMLExport(self):
        from music21 import stream, note, meter

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


#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [Instrument]


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)
    elif len(sys.argv) > 1:
        pass
#        a = Test()
#        a.testMusicXMLExport()

#------------------------------------------------------------------------------
# eof

