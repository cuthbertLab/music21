#-------------------------------------------------------------------------------
# Name:         tempo.py
# Purpose:      Classes and tools relating to tempo
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    (c) 2009-10 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

_MOD = "tempo.py"

import unittest, doctest

import music21
import music21.note

class TempoMark(music21.Music21Object):
    '''
    >>> tm = TempoMark("adagio")
    >>> tm.value
    'adagio'
    '''
    
    def __init__(self, value = None):
        music21.Music21Object.__init__(self)
        self.value = value
    
    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, self.value)



class MetronomeMark(TempoMark):
    '''
    >>> a = MetronomeMark(40)
    >>> a.number
    40
    '''
    def __init__(self, number = 60, referent = None):
        TempoMark.__init__(self, number)

        self.number = number
        self.referent = referent # should be a music21.note.Duration object
    
    def __repr__(self):
        return "<music21.tempo.MetronomeMark %s>" % str(self.number)



#-------------------------------------------------------------------------------
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
            obj = getattr(sys.modules[self.__module__], part)
            if callable(obj) and not isinstance(obj, types.FunctionType):
                a = copy.copy(obj)
                b = copy.deepcopy(obj)


    def setupTest(self):
        MM1 = MetronomeMark(60, music21.note.QuarterNote() )
        self.assertEqual(MM1.number, 60)

        TM1 = TempoMark("Lebhaft")
        self.assertEqual(TM1.value, "Lebhaft")
        


#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [TempoMark, MetronomeMark]


if __name__ == "__main__":
    music21.mainTest(Test)