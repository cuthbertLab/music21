# -*- coding: utf-8 -*-
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

    
    def xtest_Ch6_basic_I_A(self, *arguments, **keywords):
        '''p55
        Write a whole note on the specified generic interval. Do not add sharps or flats. 
        
        
        MSC: 2013 Oct -- No longer works now that convertGenericToSemitone() [buggy] has been removed.
        '''
        # note: sharps and flats are still being added: need generic transposition or scale-based approach
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



    

#-------------------------------------------------------------------------------
# II. Writing major and perfect pitch intervals

    def test_Ch6_basic_II_A(self, *arguments, **keywords):
        '''p. 55
        Write the specified melodic interval above the given note.
        '''
        # combines 1 and 2

        pitches1 = ['e-4', 'f#4', 'a-4', 'd4', 'f4']
        intervals1 = ['M6', 'p5', 'M3', 'M7', 'P4']

        pitches2 = ['c#4', 'f3', 'a3', 'b-3', 'e-3']
        intervals2 = ['-M6', '-p5', '-M7', '-M2', '-P4']

        pitches = pitches1 + pitches2
        intervals = intervals1 + intervals2

        s = stream.Stream()
        for i, p in enumerate(pitches):
            if i == 0:
                s.append(clef.TrebleClef())
            if i == len(pitches1):
                s.append(clef.BassClef())

            p = pitch.Pitch(p) # convert string to obj
            iObj = interval.Interval(intervals[i])
            c = chord.Chord([p, p.transpose(iObj)], type='whole')
            s.append(c)

        if 'show' in keywords.keys() and keywords['show']:
            s.show()    

        match = []
        for c in s.getElementsByClass('Chord'):
            # append second pitch as a string
            match.append(str(c.pitches[1]))
        self.assertEqual(match, ['C5', 'C#5', 'C5', 'C#5', 'B-4', 'E3', 'B-2', 'B-2', 'A-3', 'B-2'])


    def test_Ch6_basic_II_B(self, *arguments, **keywords):
        pass

#-------------------------------------------------------------------------------
# III. Writing major, minor, and perfect pitch intervals


#-------------------------------------------------------------------------------
# IV. Writing diminished and augmented pitch intervals

#-------------------------------------------------------------------------------
# V. Enharmonically equivalent intervals


#-------------------------------------------------------------------------------
# VI. Interval inversion


#-------------------------------------------------------------------------------
# VII. Interval class



#-------------------------------------------------------------------------------
# VII. Interval class



#-------------------------------------------------------------------------------
# Writing Exercises
#-------------------------------------------------------------------------------
# Writing intervals


#-------------------------------------------------------------------------------
# Analysis
#-------------------------------------------------------------------------------
# I. Harmonic and melodic intervals



#-------------------------------------------------------------------------------
# II. Melodic intervals, compound intervals, and interval class





#-------------------------------------------------------------------------------
# CHAPTER 7: Triads and Seventh Chords
#-------------------------------------------------------------------------------
# Basic Elements
#-------------------------------------------------------------------------------
# I. Building triads above a scale



#-------------------------------------------------------------------------------
# II. Spelling isolated triads


#-------------------------------------------------------------------------------
# III. Scale-degree triads


#-------------------------------------------------------------------------------
# IV. Building seventh chords above a scale


#-------------------------------------------------------------------------------
# V. Spelling isolated seventh chords



#-------------------------------------------------------------------------------
# VI. Scale-degree triads and seventh chords in inversion


#-------------------------------------------------------------------------------
# Analysis
#-------------------------------------------------------------------------------
# I. Brief analysis


#-------------------------------------------------------------------------------
# II. Examining a lead sheet







#-------------------------------------------------------------------------------
# CHAPTER 8: Intervals in Action
#-------------------------------------------------------------------------------
# Basic Elements
#-------------------------------------------------------------------------------
# I. Opening and closing patterns in note-against-note counterpoint












if __name__ == "__main__":
    import music21
    import sys

    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)

    elif len(sys.argv) > 1:
        t = Test()

        #t.test_Ch6_basic_II_A(show=True)



