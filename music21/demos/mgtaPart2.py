#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         mgtaPart2.py
# Purpose:      demonstration
#
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------


import unittest, doctest
import sys

import music21
from music21 import clef
from music21 import chord
from music21 import converter
from music21 import instrument
from music21 import interval
from music21 import note
from music21 import stream
from music21 import pitch

from music21 import environment
_MOD = 'mgtaPart2.py'
environLocal = environment.Environment(_MOD)


#-------------------------------------------------------------------------------
# all are tests
class Test(unittest.TestCase):

    def runTest(self):
        ''' 
        '''
        pass

#-------------------------------------------------------------------------------
# CHAPTER 6
#-------------------------------------------------------------------------------
# Basic Elements
#-------------------------------------------------------------------------------
# I. Writing generic intervals (melodic)

    
    def test_Ch6_basic_I_A(self, *arguments, **keywords):

        pitches = ['d4', 'f4', 'e4', 'c4', 'a4']
        # these are generic intervals
        intervals = [2, 5, 3, 7, 4]
    
        s = stream.Stream()
        for i, p in enumerate(pitches):
            p = pitch.Pitch(p) # convert string to obj
            iObj = interval.Interval(
                # convert generic to chromatic
                interval.convertGenericToSemitone(intervals[i])) 
            c = chord.Chord([p, p.transpose(iObj)], type='whole')
        
            s.append(c)

        if 'show' in keywords.keys() and keywords['show']:
            s.show()    

        self.assertEqual(len(s), 5)
        self.assertEqual(s[0].forteClass, '2-2')
        self.assertEqual(s[1].forteClass, '2-5')
        self.assertEqual(s[2].forteClass, '2-4')
        self.assertEqual(s[3].forteClass, '2-1')
        self.assertEqual(s[4].forteClass, '2-5')







if __name__ == "__main__":
    import music21
    import sys

    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)

    elif len(sys.argv) > 1:
        t = Test()

        t.test_Ch6_basic_I_A(show=False)
