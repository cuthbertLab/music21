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
from __future__ import division

import sys
import copy
import unittest
#import random

from music21 import chord
from music21 import clef
from music21 import converter
from music21 import duration
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


    >>> #_DOCS_SHOW composition.phasing.pitchedPhase(cycles=4, show=True)

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
        cycles = int(round(1 / increment)) + 1

    for i in range(cycles):
        sPost.parts[0].append(copy.deepcopy(sSrc))
        sMod = copy.deepcopy(sSrc)
        # increment last note
        sMod.notesAndRests[-1].quarterLength += increment

        # randInterval = random.randint(-12, 12)
        # sMod.transpose(randInterval, inPlace=True)
        sPost.parts[1].append(sMod)


    if show:
        sPost.show('midi')
        sPost.show()
    else: # get musicxml
        pass




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
        while j < (jMax + 1.0):
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
                c.append(p)
                
            j += loopLength/(maxNotesPerLoop - totalParts + i)
            #j += (8+(8-i))/8.0
        p = octo.next(p, stepSize = scaleStepSize)


    parts[0].insert(0, tempo.MetronomeMark(number=120, referent=duration.Duration(2.0)))
    for i in range(4):
        parts[i].insert(int((jMax + 4.0) / 4) * 4, note.Rest(quarterLength=4.0))
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

class TestExternal(unittest.TestCase): # pragma: no cover

    def runTest(self):
        pass


    def testBasic(self, cycles=8, show=True):
        # run a reduced version
        pitchedPhase(cycles=cycles, show=show)

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

