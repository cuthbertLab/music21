#-------------------------------------------------------------------------------
# Name:         key.py
# Purpose:      Classes for keys
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    (c) 2009 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
import doctest, unittest


import music21

from music21 import note
from music21 import stream
from music21 import interval


class Key(music21.Music21Object):
    '''
    Note that a key is a sort of hypothetical/conceptual object.
    It probably has a scale (or scales) associated with it and a KeySignature,
    but not necessarily.
    '''
    
    def __init__(self, stream1 = None):
        self.stream1 = stream1
        self.step = ''
        self.accidental = ''
        self.type = ''

        self.stepList = music21.pitch.STEPNAMES

        # this information might be better dervied from somewhere in 
        # note.py
        self.accidentalList = ['--', '-', None, '#', '##']
        self.typeList = ['major', 'minor']

    def generateKey(self):
        # want to use Krumhansl-Kessler algorithm; need to find explicit instructions
        pass

    def setKey(self, name = "C", accidental = None, type = "major"):
        self.step = name
        self.accidental = accidental
        self.type = type

def keyFromString(strKey):
    #TODO: Write keyFromString
    return None
    #raise KeyException("keyFromString not yet written")


class KeySignature(object):
    numberSharps = None  # None is different from 0; negative used for flats.

    def __init__(self, numSharps = None):
        self.numberSharps = numSharps

    def strSharpsFlats(self):
        ns = self.numberSharps
        if ns > 1:
            return "%s sharps" % str(ns)
        elif ns == 1:
            return "1 sharp"
        elif ns == 0:
            return "no sharps or flats"
        elif ns == -1:
            return "1 flat"
        else:
            return "%s flats" % str(abs(ns))
        
    def __repr__(self):
        return "<music21.key.KeySignature of %s>" % self.strSharpsFlats()
        







#-------------------------------------------------------------------------------
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


    def testBasic(self):
        a = KeySignature()
        self.assertEqual(a.numberSharps, None)


if __name__ == "__main__":
    music21.mainTest(Test)





