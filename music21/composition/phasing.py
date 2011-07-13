#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         phasing.py
# Purpose:      Modeling musical phasing structures in MusicXML
#
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import sys
import copy
import unittest
import random

import music21
from music21 import clef
from music21 import converter
from music21 import duration
from music21 import key
from music21 import meter
from music21 import note
from music21 import pitch
from music21 import stream
# DOENST WORK from music21 import *

def pitchedPhase(cycles=None, show=False):
    '''
    Creates a phase composition in the style of 
    1970s minimalism, but bitonally.
    
    The source code describes how this works.
    
    >>> from music21 import *
    >>> #_DOCS_SHOW composition.phasing.pitchedPhase(cycles = 4, show = True)
    
    .. image:: images/phasingDemo.*
            :width: 576

    '''

    sSrc = music21.parse("""E16 F# B c# d F# E c# B F# d c# 
                              E16 F# B c# d F# E c# B F# d c#""", '12/16')
    sPost = stream.Score()
    sPost.title = 'phasing experiment'
    sPost.insert(0, stream.Part())
    sPost.insert(0, stream.Part())

    durationToShift = duration.Duration('64th')
    increment = durationToShift.quarterLength
    if cycles == None:
        cycles = int(round(1/increment)) + 1

    for i in range(cycles):
        sPost.parts[0].append(copy.deepcopy(sSrc))
        sMod = copy.deepcopy(sSrc)
        # increment last note
        sMod.notesAndRests[-1].quarterLength += increment
        
        randInterval = random.randint(-12,12)
        #sMod.transpose(randInterval, inPlace=True)
        sPost.parts[1].append(sMod)


    if show:
        sPost.show('midi')
        sPost.show()
    else: # get musicxml
        post = sPost.musicxml



def partPari(show = True):
    s = stream.Score()
    cminor = key.Key('c')
    main = converter.parse("E-1 C D E- F G F E- D C D E- G A- F G E- F G F E- D F G c B- c G A- B- c B- A- B- G c e- d c d c B- A- G F E- F G c E- F G E- D E- F E- D C E- G F E- C F E- D C E- D C D C~ C", '4/4')
    main.transpose('P8', inPlace=True)
    main.insert(0, cminor)
    bass = copy.deepcopy(main.flat)
    for n in bass.notes:
        n.pitch.diatonicNoteNum = n.pitch.diatonicNoteNum - 9
        if n.diatonicNoteNum == 20 or n.diatonicNoteNum == 21:
            n.accidental = pitch.Accidental('natural')
        else:
            n.accidental = cminor.accidentalByStep(n.step)
    top = copy.deepcopy(main.flat)
    main.insert(0, clef.Treble8vbClef())
    middle = copy.deepcopy(main.flat)
    topAdjust = {'C': 4, 'D': 3, 'E-': 5, 'F': 4, 'G': 5, 'A-': 4, 'B-': 3}
    for n in top:
        if 'Note' in n.classes:
            n.pitch.diatonicNoteNum += topAdjust[n.pitch.name]
            n.accidental = cminor.accidentalByStep(n.step)
            n.duration.quarterLength = 3.0
            top.insert(n.offset + 3, note.Rest())
    r1 = note.Rest(type = 'half')
    top.insertAndShift(0, r1)
    
    middleAdjust = {'C': -5, 'D': -4, 'E-': -5, 'F': -3, 'G': -4, 'A-': -3, 'B-': -4}
    
    for n in middle:
        if 'Note' in n.classes:
            n.pitch.diatonicNoteNum += middleAdjust[n.pitch.name]
            n.accidental = cminor.accidentalByStep(n.step)
            n.duration.quarterLength = 3.0
            middle.insert(n.offset + 3, note.Rest())
    r2 = note.Rest(quarterLength = 3.0)
    middle.insertAndShift(0, r2)    

    ttied = top.makeMeasures().makeTies()
    print ttied.musicxml
    s.insert(0, ttied)
    s.insert(0, main.flat)
    s.insert(0, middle.makeMeasures().makeTies())
    s.insert(0, bass)
    s.show()

#-------------------------------------------------------------------------------
class Test(unittest.TestCase):
   
    def runTest(self):
        pass
   

    def testBasic(self, cycles=4, show=False):
        # run a reduced version
        pitchedPhase(cycles=cycles, show=show)

class TestExternal(unittest.TestCase):

    def runTest(self):
        pass
   

    def testBasic(self, cycles=8, show=True):
        # run a reduced version
        pitchedPhase(cycles=cycles, show=show)


if __name__ == "__main__":
    partPari()
    exit()
    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(TestExternal)

    elif len(sys.argv) > 1:
        t = Test()
        t.testBasic(cycles=None, show=True)




#------------------------------------------------------------------------------
# eof

