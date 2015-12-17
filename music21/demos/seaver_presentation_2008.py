# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         demos/seaver_presentation_2008.py
# Purpose:      Demonstrations for the Seaver 2008 demo
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2008 Michael Scott Cuthbert and the music21 Project
# License:      BSD or LGPL, see license.txt
#-------------------------------------------------------------------------------
'''
This script was used to create the musical examples used in the presentation given by MSC to the
Seaver Institute in October 2008 which resulted in the original funding for music21.  It
has no other purpose but to demonstrate where music21 was at in October 2008.

The lilypond routines have been updated.  The demo was originally trecento/seaver_presentation.py 
and earlier history can be found there.
'''

import music21
from music21 import converter


def createEasyScale():
    s1 = converter.parse("tinynotation: 3/4 d8 e f g a b")
#    s1.timeSignature = time1
#    s1.showTimeSignature = True
    s1.show('lily.png')
    
def createSleep():
    s1 = converter.parse("tinynotation: A1 r4 G G G8 F G2 G c2 c8 c c B c2 c", makeNotation=False)
    
    s1.clef = music21.clef.Treble8vbClef()
    s1.show('lily.png')
    s1.show('midi')

def createOrphee():
    '''section = measures from Orphee, Act I, no. 1, m.15 by Gluck
    tempo = moderato, timeSig = cut time
    random = randomly generated melody from rolling dice.
    '''
    #random = " g4 b-8 b-16 b- b-32 b- b-64 e- r32 r8 r4"
    #random2 = " g4 a-8 a-8 d'-16 b16 a-16 c'16 c'4 c'8 g8 e-8 f8 f4 a-4"
    random3 = " f4 g4. a8 a4. d'8 b4 a4 c'4 r4 c'4. c'8 g8 e-8 f4 f4 a-2."
    
    section = "g4 g2 c'4 c'2 b4 b8 c' c'2. g4 a-2 g4 "
    section += random3

    s1 = converter.parse(section, format="tinynotation")
    s1.show('lily.png')
    s1.show('midi')
    
def badMeter():
    myScale = "3/4 a2 a2"
    s1 = converter.parse(myScale, format="tinynotation")
    s1.show('lily.png')
    s1.show('midi')
    
def capuaReg1():
    myScale = "g4 f4 g4 r4 r2 g4 f#4 g2"
    s1 = converter.parse(myScale, format="tinynotation")
    s1.show('lily.png')
    s1.show('midi')

def capuaReg2():
    myScale = "d4 e f g r r r r d e f# g2"
    s1 = converter.parse(myScale, format="tinynotation")
    s1.show('lily.png')
    s1.show('midi')

def capuaReg3():
    myScale = "a4 f g r r r r a f# g2"
    s1 = converter.parse(myScale, format="tinynotation")
    s1.show('lily.png')
    s1.show('midi')
    
def major3rd():
    myScale = "a-2 c'2"
    s1 = converter.parse(myScale, format="tinynotation")
    s1.show('lily.png')
    s1.show('midi')

#def redoLandini():
#    bs = cadencebook.BallataSheet()
#    w1 = bs.makeWork(260)
#    lilyAll = lily.lilyString.LilyString(r'''
#    \score {
#<< \time 3/4
#  \new Staff {     \set Staff.midiInstrument = "oboe" \clef "treble" g'2. d'4 \times 2/3 {e'8 d'8 c'8} d'8 e'8 c'8 d'8 c'8 bes8 bes8 a8 g4 r4 f4  } 
#  \new Staff { \set Staff.midiInstrument = "clarinet" \clef "bass" g2.~ g2. c4 ees4 f4 r4 g4 a4  } 
#>>
# \header { 
# piece = "D'amor mi biasmo -- A section cadence  " 
#}
#    \layout {}
#    \midi { \context { \Score tempoWholesPerMinute = #(ly:make-moment 88 4) } }
#}
#    ''')
#    lilyAll.showPNGandPlayMIDI()


if (__name__ == "__main__"):
#    redoLandini()
    major3rd()
    capuaReg3()
    createOrphee()
    createEasyScale()
    badMeter()

#------------------------------------------------------------------------------
# eof

