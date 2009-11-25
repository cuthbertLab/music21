#-------------------------------------------------------------------------------
# Name:         tempo.py
# Purpose:      Classes and tools relating to tempo
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    (c) 2009 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

_MOD = "tempo.py"

import unittest, doctest

import music21
import music21.note

class TempoMark(music21.Music21Object):
    def __init__(self, value):
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
    def __init__(self, number, referent = None):
        TempoMark.__init__(self, number)

        self.number = number
        self.referent = referent # should be a music21.note.Duration object
    
    def __repr__(self):
        return "<music21.tempo.MetronomeMark %s>" % str(self.number)



#-------------------------------------------------------------------------------
class Test(unittest.TestCase):
    def runTest(self):
        pass

    def setupTest(self):
        MM1 = MetronomeMark(60, music21.note.QuarterNote() )
        self.assertEqual(MM1.number, 60)

        TM1 = TempoMark("Lebhaft")
        self.assertEqual(TM1.value, "Lebhaft")
        
if __name__ == "__main__":
    music21.mainTest(Test)