# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         testSerialization.py
# Purpose:      tests for serializing music21 objects
#
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2012 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------


import copy, types, random
import doctest, unittest
import sys
from copy import deepcopy


import music21 # needed to do fully-qualified isinstance name checking

from music21 import environment
_MOD = "testSerialization.py"
environLocal = environment.Environment(_MOD)





#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        '''Need a comment
        '''
        pass

    def testBasicA(self):
        from music21 import note, stream

        t1 = note.Lyric('test')
        #print t1.json

        n1 = note.Note('G#3', quarterLength=3)
        n1.lyric = 'testing'
        self.assertEqual(n1.pitch.nameWithOctave, 'G#3')        
        self.assertEqual(n1.quarterLength, 3.0)        
        self.assertEqual(n1.lyric, 'testing')        
        
        raw = n1.json

        n2 = note.Note()
        n2.json = raw
        
        self.assertEqual(n2.pitch.nameWithOctave, 'G#3')    
        self.assertEqual(n2.quarterLength, 3.0)        
        #self.assertEqual(n2.lyric, 'testing')        

            
    def testBasicB(self):
        from music21 import note, stream, chord

        c1 = chord.Chord(['c2', 'a4', 'e5'], quarterLength=1.25)

        raw = c1.json

        c2 = chord.Chord()
        c2.json = raw
        self.assertEqual(str(c1.pitches), '[C2, A4, E5]')
        self.assertEqual(c1.quarterLength, 1.25)

    # TODO: replace with file-like objects for temporary writing
    def testBasicC(self):
        from music21 import stream, note, converter
        import copy

        s = stream.Stream()
        n1 = note.Note('d2', quarterLength=2.0)
        s.append(n1)
        s.append(note.Note('g~6', quarterLength=.25))

        fp = '/_scratch/test.pickle'
        converter.freeze(s, fp)

        post = converter.unfreeze(fp)
        self.assertEqual(len(post.notes), 2)
        self.assertEqual(str(post.notes[0].pitch), 'D2')


    # TODO: replace with file-like objects for temporary writing
    # this presently fails
    def testBasicD(self):
        from music21 import stream, note, converter, spanner
        import copy

        s = stream.Stream()
        n1 = note.Note('d2', quarterLength=2.0)
        n2 = note.Note('e2', quarterLength=2.0)
        sp = spanner.Slur(n1, n2)
        s.append(n1)
        s.append(n2)
        #s.append(sp)
        temp = converter.freezeStr(s)

        post = converter.unfreezeStr(temp)

        self.assertEqual(len(post.notes), 2)
        self.assertEqual(str(post.notes[0].pitch), 'D2')



#------------------------------------------------------------------------------

if __name__ == "__main__":
    music21.mainTest(Test)


#------------------------------------------------------------------------------
# eof






