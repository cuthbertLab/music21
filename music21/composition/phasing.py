# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         phasing.py
# Purpose:      Modeling musical phasing structures in MusicXML
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2010-2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------

import sys
import copy
import unittest
#import random

from music21 import bar
from music21 import chord
from music21 import clef
from music21 import converter
from music21 import duration
from music21 import key
from music21 import instrument
from music21 import metadata
from music21 import note
from music21 import pitch
from music21 import scale
from music21 import tempo
from music21 import stream
# DOENST WORK from music21 import *

def pitchedPhase(cycles=None, show=False):
    '''
    Creates a phase composition in the style of 
    1970s minimalism, but bitonally.
    
    The source code describes how this works.
    
    
    >>> #_DOCS_SHOW composition.phasing.pitchedPhase(cycles = 4, show = True)
    
    .. image:: images/phasingDemo.*
            :width: 576

    '''

    sSrc = converter.parse("""tinynotation: 12/16 E16 F# B c# d F# E c# B F# d c# 
                              E16 F# B c# d F# E c# B F# d c#""", makeNotation=False)
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
        
        #randInterval = random.randint(-12,12)
        #sMod.transpose(randInterval, inPlace=True)
        sPost.parts[1].append(sMod)


    if show:
        sPost.show('midi')
        sPost.show()
    else: # get musicxml
        pass


def partPari(show = True):
    '''
    generate the score of Arvo Pärt's "Pari Intervallo" algorithmically
    using music21.scale.ConcreteScale() to simulate Tintinabulation.
    '''
    s = stream.Score()
    cminor = key.Key('c')
    #real Paert
    main = converter.parse("tinynotation: 4/4 E-1 C D E- F G F E- D C D E- G A- F G E- F G F E- D F G c B- c G A- B- c B- A- B- G c e- d c d c B- A- G F E- F G c E- F G E- D E- F E- D C E- G F E- C F E- D C E- D C D C~ C")
    
    # fake Paert
    #main = converter.parse("E-1 F G A- G F c d e- G A- F E- D d e- c B- A- c d A- G F G F A- B- A- c d A- B- c B- A- G F G F E-~ E-", '4/4')
    main.__class__ = stream.Part
    main.transpose('P8', inPlace=True)
    main.insert(0, cminor)
    main.insert(0, instrument.Recorder())
    bass = copy.deepcopy(main.flat)
    for n in bass.notes:
        n.pitch.diatonicNoteNum = n.pitch.diatonicNoteNum - 9
        if (n.pitch.step == 'A' or n.pitch.step == 'B') and n.pitch.octave == 2:
            n.accidental = pitch.Accidental('natural')
        else:
            n.accidental = cminor.accidentalByStep(n.step)
        if n.offset == (2-1) * 4 or n.offset == (74-1) * 4:
            n.pitch = pitch.Pitch("C3") # exceptions to rule
        elif n.offset == (73 - 1) * 4:
            n.tie = None
            n.pitch = pitch.Pitch("C3") 
    top = copy.deepcopy(main.flat)
    main.insert(0, clef.Treble8vbClef())
    middle = copy.deepcopy(main.flat)
    
    
    cMinorArpeg = scale.ConcreteScale(pitches = ["C2","E-2","G2"])
    # dummy test on other data
    #myA = pitch.Pitch("A2")
    #myA.microtone = -15
    #cMinorArpeg = scale.ConcreteScale(pitches = ["C2", "E`2", "F~2", myA])
    
    lastNote = top.notes[-1]
    top.remove(lastNote)
    for n in top:
        if 'Note' in n.classes:
            n.pitch = cMinorArpeg.next(n.pitch, stepSize=2)
            if n.offset != (73-1)*4.0:  # m. 73 is different
                n.duration.quarterLength = 3.0
                top.insert(n.offset + 3, note.Rest())
            else:
                n.duration.quarterLength = 6.0
                n.tie = None
    r1 = note.Rest(type = 'half')
    top.insertAndShift(0, r1)
    top.getElementsByClass(key.Key)[0].setOffsetBySite(top, 0)
    lastNote = middle.notes[-1]
    middle.remove(lastNote)
   
    for n in middle:
        if 'Note' in n.classes:
            n.pitch = cMinorArpeg.next(n.pitch, direction=scale.DIRECTION_DESCENDING, stepSize=2)
            if n.offset != (73-1)*4.0:  # m. 73 is different
                n.duration.quarterLength = 3.0
                middle.insert(n.offset + 3, note.Rest())
            else:
                n.duration.quarterLength = 5.0
                n.tie = None
    r2 = note.Rest(quarterLength = 3.0)
    middle.insertAndShift(0, r2)    
    middle.getElementsByClass(key.Key)[0].setOffsetBySite(middle, 0)

    ttied = top.makeMeasures().makeTies(inPlace=False)
    mtied = middle.makeMeasures().makeTies(inPlace=False)
    bass.makeMeasures(inPlace = True)
    main.makeMeasures(inPlace = True)
    
    s.insert(0, ttied)
    s.insert(0, main)
    s.insert(0, mtied)
    s.insert(0, bass)
    
    for p in s.parts:
        p.getElementsByClass(stream.Measure)[-1].rightBarline = bar.Barline('final')

    if show == True:
        s.show()

def pendulumMusic(show = True, 
                  loopLength = 160.0, 
                  totalLoops = 1, 
                  maxNotesPerLoop = 40,
                  totalParts = 16,
                  scaleStepSize = 3,
                  scaleType = scale.OctatonicScale,
                  startingPitch = 'C1'
                  ):    
    totalLoops = totalLoops * 1.01
    jMax = loopLength * totalLoops
    
    
    p = pitch.Pitch(startingPitch)
    if isinstance(scaleType, scale.Scale):
        octo = scaleType
    else:
        octo = scaleType(p)
    s = stream.Score()
    s.metadata = metadata.Metadata()
    s.metadata.title = 'Pendulum Waves'
    s.metadata.composer = 'inspired by http://www.youtube.com/watch?v=yVkdfJ9PkRQ'
    parts = [stream.Part(), stream.Part(), stream.Part(), stream.Part()]
    parts[0].insert(0, clef.Treble8vaClef())
    parts[1].insert(0, clef.TrebleClef())
    parts[2].insert(0, clef.BassClef())
    parts[3].insert(0, clef.Bass8vbClef())
    for i in range(totalParts):
        j = 1.0
        while j < (jMax+1.0):
            ps = p.ps
            if ps > 84:
                active = 0
            elif ps >= 60:
                active = 1
            elif ps >= 36:
                active = 2
            elif ps < 36:
                active = 3
            
            jQuant = round(j*8)/8.0

            establishedChords = parts[active].getElementsByOffset(jQuant)
            if len(establishedChords) == 0:
                c = chord.Chord([p])
                c.duration.type = '32nd'
                parts[active].insert(jQuant, c)
            else:
                c = establishedChords[0]
                pitches = c.pitches
                pitches.append(p)
                c.pitches = pitches
            j += loopLength/(maxNotesPerLoop - totalParts + i)
            #j += (8+(8-i))/8.0
        p = octo.next(p, stepSize = scaleStepSize)
            

    parts[0].insert(0, tempo.MetronomeMark(number = 120, referent = duration.Duration(2.0)))
    for i in range(4):
        parts[i].insert(int((jMax + 4.0)/4)*4, note.Rest(quarterLength=4.0))
        parts[i].makeRests(fillGaps=True, inPlace=True)
        parts[i] = parts[i].makeNotation()
        s.insert(0, parts[i])
    
    if show == True:
        #s.show('text')
        s.show('midi')
        s.show()
 

#-------------------------------------------------------------------------------
class Test(unittest.TestCase):
   
    def runTest(self):
        pass
   

    def testBasic(self, cycles=4, show=False):
        # run a reduced version
        pitchedPhase(cycles=cycles, show=show)

    def testArvoPart(self, show=False):
        partPari(show)


class TestExternal(unittest.TestCase):

    def runTest(self):
        pass
   

    def testBasic(self, cycles=8, show=True):
        # run a reduced version
        pitchedPhase(cycles=cycles, show=show)

    def xtestArvoPart(self, show=True):
        partPari(show)

    def xtestPendulumMusic(self, show=True):  
        pendulumMusic(show)
#        pendulumMusic(show = True, 
#                  loopLength = 210.0, 
#                  totalLoops = 1, 
#                  maxNotesPerLoop = 70,
#                  totalParts = 64,
#                  scaleStepSize = 1,
#                  scaleType = scale.ChromaticScale,
#                  startingPitch = 'C1',
#                  )
#        pendulumMusic(show = True, 
#                  loopLength = 210.0, 
#                  totalLoops = 1, 
#                  maxNotesPerLoop = 70,
#                  totalParts = 12,
#                  scaleStepSize = 5,
#                  scaleType = scale.ScalaScale('C3', '13-19.scl'),
#                  startingPitch = 'C2',
#                  )
#        

#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [pitchedPhase]

if __name__ == "__main__":
    if len(sys.argv) == 1: # normal conditions
        import music21
        music21.mainTest(TestExternal)

    elif len(sys.argv) > 1:
        t = Test()
        t.testBasic(cycles=None, show=True)




#------------------------------------------------------------------------------
# eof

