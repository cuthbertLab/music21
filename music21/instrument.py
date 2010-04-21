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

import unittest, doctest


import music21
from music21 import musicxml
from music21 import common
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
        elif self.instrumentName != None:
            return self.instrumentName
        elif self.partAbbreviation != None:
            return self.partAbbreviation
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
         


    #---------------------------------------------------------------------------
    def _getMX(self):
        '''
        '''
        mxScorePart = musicxml.ScorePart()

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
            self.midiProgram = mxMIDIInstrument.get('midiProgram')
            self.midiChannel = mxMIDIInstrument.get('midiChannel')


    mx = property(_getMX, _setMX)


class StringInstrument(Instrument):
    
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
        self.lowestNote = pitch.Pitch("G3")
        self._stringPitches = ["G3","D4","A4","E5"]

class Viola(StringInstrument):
    def __init__(self):
        StringInstrument.__init__(self)
        self.lowestNote = pitch.Pitch("C3")
        

class Violoncello(StringInstrument):
    def __init__(self):
        StringInstrument.__init__(self)
        self.lowestNote = pitch.Pitch("C2")




#-------------------------------------------------------------------------------
class WoodwindInstrument(Instrument):
    def __init__(self):
        Instrument.__init__(self)


class Bassoon(WoodwindInstrument):
    def __init__(self):
        WoodwindInstrument.__init__(self)





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


#     def testBruteMusicXML(self):
#         from music21 import corpus
# 
#         post = []
#         doc = musicxml.Document()
#         doc.open(corpus.mozart[0])
#         partList = doc.score.get('partList')
#         for mxObj in partList:
#             if isinstance(mxObj, music21.musicxml.ScorePart):
#                 a = Instrument()    
#                 a.mx = mxObj
#                 post.append(a)




#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [Instrument]


if __name__ == "__main__":
    music21.mainTest(Test)