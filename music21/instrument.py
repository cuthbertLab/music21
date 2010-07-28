#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         instrument.py
# Purpose:      Class for basic insturment information
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    (c) 2009 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

'''This module defines object models for instrument representations. Metadata for instrument realizations, including transpositions and default MIDI program numbers, are also included. 
'''

import unittest, doctest

import music21
from music21 import musicxml
from music21 import common
from music21 import defaults
from music21 import pitch

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
         

    def midiChannelAutoAssign(self, usedChannels=[]):
        '''Force a midi channel
        '''
        filter = []
        for e in usedChannels:
            if e != None:
                filter.append(e)

        if len(filter) == 0:
            self.midiChannel = 0
        else:
            ch = max(filter)
            ch += 1
            if ch == 10:  # skip 10 /perc for now
                ch += 1
            ch = ch % 16 # wrap around if out
            self.midiChannel = ch


    #---------------------------------------------------------------------------
    def _getMX(self):
        '''
        >>> from music21 import *
        >>> i = instrument.Celesta()
        >>> mxScorePart = i.mx
        >>> len(mxScorePart.scoreInstrumentList)
        1
        >>> mxScorePart.scoreInstrumentList[0].instrumentName
        'Celesta'
        >>> mxScorePart.midiInstrumentList[0].midiProgram
        9
        '''
        mxScorePart = musicxml.ScorePart()

        # get a random id if None set
        if self.partId == None:
            self.partIdRandomize()

        if self.instrumentId == None:
            self.instrumentIdRandomize()

        # note: this is id, not partId!
        mxScorePart.set('id', self.partId)

        if self.partName != None:
            mxScorePart.partName = self.partName
        elif self.partName == None: # get default, as required
            mxScorePart.partName = defaults.partName

        if self.partAbbreviation != None:
            mxScorePart.partAbbreviation = self.partAbbreviation

        if self.instrumentName != None or self.instrumentAbbreviation != None:
            mxScoreInstrument = musicxml.ScoreInstrument()
            # set id to same as part for now
            mxScoreInstrument.set('id', self.instrumentId)
            # can set these to None
            mxScoreInstrument.instrumentName = self.instrumentName
            mxScoreInstrument.instrumentAbbreviation = self.instrumentAbbreviation
            # add to mxScorePart
            mxScorePart.scoreInstrumentList.append(mxScoreInstrument)

        if self.midiProgram != None:
            mxMIDIInstrument = musicxml.MIDIInstrument()
            mxMIDIInstrument.set('id', self.instrumentId)
            # shift to start from 1
            mxMIDIInstrument.midiProgram = self.midiProgram + 1 

            if self.midiChannel == None:
                # TODO: need to allocate channels from a higher level
                self.midiChannelAutoAssign()
            mxMIDIInstrument.midiChannel = self.midiChannel + 1
            # add to mxScorePart
            mxScorePart.midiInstrumentList.append(mxMIDIInstrument)

        return mxScorePart
        

    def _setMX(self, mxScorePart):
        '''
        provide a score part object
        '''
        self.partId = mxScorePart.get('id')
        self.partName = mxScorePart.get('partName')
        self.partAbbreviation = mxScorePart.get('partAbbreviation')

        # for now, just get first instrument
        if len(mxScorePart.scoreInstrumentList) > 0:
            mxScoreInstrument = mxScorePart.scoreInstrumentList[0]
            self.instrumentName = mxScoreInstrument.get('instrumentName')
            self.instrumentAbbreviation = mxScoreInstrument.get(
                                            'instrumentAbbreviation')
        if len(mxScorePart.midiInstrumentList) > 0:
            # for now, just get first midi instrument
            mxMIDIInstrument = mxScorePart.midiInstrumentList[0]
            # musicxml counts from 1, not zero
            self.midiProgram = int(mxMIDIInstrument.get('midiProgram')) - 1
            self.midiChannel = int(mxMIDIInstrument.get('midiChannel')) - 1

    mx = property(_getMX, _setMX)



#-------------------------------------------------------------------------------
class KeyboardInstrument(Instrument):

    def __init__(self):
        Instrument.__init__(self)


class Piano(KeyboardInstrument):   
    def __init__(self):
        KeyboardInstrument.__init__(self)

        self.instrumentName = 'Piano'
        self.instrumentAbbreviation = 'Pno'
        self.midiProgram = 0

class Harpsichord(KeyboardInstrument):   
    def __init__(self):
        KeyboardInstrument.__init__(self)

        self.instrumentName = 'Harpsichord'
        self.instrumentAbbreviation = 'Hpschd'
        self.midiProgram = 6


class Clavichord(KeyboardInstrument):   
    def __init__(self):
        KeyboardInstrument.__init__(self)

        self.instrumentName = 'Clavichord'
        self.instrumentAbbreviation = 'Clv'
        self.midiProgram = 7

class Celesta(KeyboardInstrument):   
    def __init__(self):
        KeyboardInstrument.__init__(self)

        self.instrumentName = 'Celesta'
        self.instrumentAbbreviation = 'Clst'
        self.midiProgram = 8




#-------------------------------------------------------------------------------

class StringInstrument(Instrument):

    def __init__(self):
        Instrument.__init__(self)
    
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

        self.lowestNote = pitch.Pitch("G3")
        self._stringPitches = ["G3","D4","A4","E5"]

class Viola(StringInstrument):
    def __init__(self):
        StringInstrument.__init__(self)

        self.instrumentName = 'Viola'
        self.instrumentAbbreviation = 'Vla'
        self.midiProgram = 41

        self.lowestNote = pitch.Pitch("C3")
        

class Violoncello(StringInstrument):
    def __init__(self):
        StringInstrument.__init__(self)

        self.instrumentName = 'Violoncello'
        self.instrumentAbbreviation = 'Vc'
        self.midiProgram = 42

        self.lowestNote = pitch.Pitch("C2")

class Contrabass(StringInstrument):
    def __init__(self):
        StringInstrument.__init__(self)

        self.instrumentName = 'Contrabass'
        self.instrumentAbbreviation = 'Cb'
        self.midiProgram = 43

        self.lowestNote = pitch.Pitch("C2")




#-------------------------------------------------------------------------------
class WoodwindInstrument(Instrument):
    def __init__(self):
        Instrument.__init__(self)


class Bassoon(WoodwindInstrument):
    def __init__(self):
        WoodwindInstrument.__init__(self)

        self.instrumentName = 'Bassoon'
        self.instrumentAbbreviation = 'Bs'
        self.midiProgram = 70



#-------------------------------------------------------------------------------
class TestExternal(unittest.TestCase):
    
    def runTest(self):
        pass
    

class Test(unittest.TestCase):
    
    def runTest(self):
        pass

    def testCopyAndDeepcopy(self):
        '''Test copyinng all objects defined in this module
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
        a = Test()
        a.testMusicXMLExport()

