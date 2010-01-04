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


from music21 import environment
_MOD = "instrument.py"
environLocal = environment.Environment(_MOD)



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




if __name__ == "__main__":
    music21.mainTest(Test)