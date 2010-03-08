#!/usr/bin/python

import unittest, doctest

import music21
from music21 import lily
from music21 import tinyNotation
from music21.tinyNotation import *

class TrecentoCadenceStream(TinyNotationStream):
    '''
    Subclass of Tiny Notation that calls TrecentoCadenceNote instead of TinyNotationNote
    '''
    def getNote(self, stringRep, storedDict = {}):
        try:
            tcN = TrecentoCadenceNote(stringRep, storedDict)
            return tcN
        except TinyNotationException, inst:
            raise TinyNotationException(inst.args[0] + "\nLarger context: " + self.stringRep)

class TrecentoCadenceNote(TinyNotationNote):
    '''
    Subclass of TinyNotationNote where 2.. represents a dotted dotted half note (that is, a dotted
    half tied to a dotted quarter) instead of a double dotted note.  This makes entering Trecento
    music (which uses this note value often) much easier.  1.. and 4.. etc. are similarly transformed. 
    '''
    ## for trecento notation: a double dotted half = 9 eighths, not 7;
    def getDots(self, stringRep, noteObj):
        if (self.DBLDOT.search(stringRep)):
            noteObj.duration.dots = 1
            noteObj.duration.dotGroups = [1]
        elif (self.DOT.search(stringRep)):
            noteObj.duration.dots = 1

###### test routines

class Test(unittest.TestCase):

    def testTrecentoNote(self):
        cn = TrecentoCadenceNote('AA-4.~')
        a = cn.note # returns the stored music21 note.
        self.assertEqual(music21.note.sendNoteInfo(a),
                          '''Name: A-
Step: A
Octave: 2
Accidental: flat
Tie: start
Duration Type: quarter
QuarterLength: 1.5
''')

    def testDotGroups(self):
        cn = TrecentoCadenceNote('c#2..')
        a = cn.note # returns the stored music21 note.

        # TODO: FIX!  not working right now because dot groups aren't. should be QL 4.5
        self.assertEqual(music21.note.sendNoteInfo(a),
                          '''Name: C#
Step: C
Octave: 4
Accidental: sharp
Duration Type: half
QuarterLength: 3.0
''')

    
class TestExternal(unittest.TestCase):
    '''
    These objects generate PNGs, etc.
    '''
    
    def testTrecentoLine(self):
        '''
        should display a 6 beat long line with some triplets
        '''
        st = TrecentoCadenceStream('e2 f8 e f trip{g16 f e} d8 c B trip{d16 c B}')
        #for thisNote in st:
        #    print note.sendNoteInfo(thisNote)
        #    print "--------"
        self.assertAlmostEqual(st.duration.quarterLength, 6.0)
        st.lily.showPNG()
    
if __name__ == "__main__":
    music21.mainTest(Test, TestExternal)