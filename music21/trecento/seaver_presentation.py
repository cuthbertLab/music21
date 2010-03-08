## Seaver Foundation presentation October 2008

import music21
from music21 import note
from music21.note import Note
from music21.note import QuarterNote
from music21 import stream
from music21.stream import Stream
from music21.lily import LilyString
from music21 import tinyNotation
from music21.tinyNotation import TinyNotationStream
from music21.meter import TimeSignature
from music21 import clef
from music21 import trecento
from music21.trecento import cadencebook
from music21.trecento import capua

def createScalePart():
    c = QuarterNote(); c.step = "C"
    d = QuarterNote(); d.step = "D"
    # etc
    b = QuarterNote(); b.step = "B"
    
    s1 = Stream()
    s1.append([c, d, b])
    print(s1.lily)
    lS1 = LilyString("{" + s1.lily + "}")
    lS1.showPNG()

def createEasyScale():
    myScale = "d8 e f g a b"
    time1 = TimeSignature("3/4")
    s1 = TinyNotationStream(myScale, time1)
    s1.insert(0, time1)
#    s1.timeSignature = time1
#    s1.showTimeSignature = True
    print(s1.lily)
    lS1 = LilyString("{" + s1.lily.value + "}")
    lS1.showPDF()
    
def createSleep():
    section = "A1 r4 G G G8 F G2 G c2 c8 c c B c2 c"
    s1 = TinyNotationStream(section)
    
    s1.clef = music21.clef.Treble8vbClef()
#    lS1 = LilyString("\\score { {" + s1.lily + "} \\layout {} \\midi {} }")
    lS1 = LilyString(s1.lily)
    #print lS1.value
    
    lS1.showPNGandPlayMIDI()

def createOrphee():
    '''section = measures from Orphee, Act I, no. 1, m.15 by Gluck
    tempo = moderato, timeSig = cut time
    random = randomly generated melody from rolling dice.
    '''
    random = " g4 b-8 b-16 b- b-32 b- b-64 e- r32 r8 r4"
    random2 = " g4 a-8 a-8 d'-16 b16 a-16 c'16 c'4 c'8 g8 e-8 f8 f4 a-4"
    random3 = " f4 g4. a8 a4. d'8 b4 a4 c'4 r4 c'4. c'8 g8 e-8 f4 f4 a-2."
    
    section = "g4 g2 c'4 c'2 b4 b8 c' c'2. g4 a-2 g4 "
    section += random3

    s1 = TinyNotationStream(section)
    lS1 = LilyString(s1.lily)
    lS1.showPNGandPlayMIDI()
    
def badMeter():
    myScale = "a2 a2"
    time1 = TimeSignature("3/4")
    s1 = TinyNotationStream(myScale, time1)
    print(s1.lily)
    s1.lily.showPNG()
    
def capuaReg1():
    myScale = "g4 f4 g4 r4 r2 g4 f#4 g2"
    s1 = TinyNotationStream(myScale)
    lS1 = LilyString(s1.lily)
    lS1.showPNGandPlayMIDI()
    print(lS1.midiFilename)

def capuaReg2():
    myScale = "d4 e f g r r r r d e f# g2"
    s1 = TinyNotationStream(myScale)
    lS1 = LilyString(s1.lily)
    lS1.showPNGandPlayMIDI()
    print(lS1.midiFilename)

def capuaReg3():
    myScale = "a4 f g r r r r a f# g2"
    s1 = TinyNotationStream(myScale)
    lS1 = LilyString(s1.lily)
    lS1.showPNGandPlayMIDI()
    print(lS1.midiFilename)
    
def major3rd():
    myScale = "a-2 c'2"
    s1 = TinyNotationStream(myScale)
    lS1 = LilyString(s1.lily)
    lS1.showPDF()

def redoLandini():
    bs = cadencebook.BallataSheet()
    w1 = bs.makeWork(260)
    lilyAll = LilyString(r'''
    \score {
<< \time 3/4
  \new Staff {     \set Staff.midiInstrument = "oboe" \clef "treble" g'2. d'4 \times 2/3 {e'8 d'8 c'8} d'8 e'8 c'8 d'8 c'8 bes8 bes8 a8 g4 r4 f4  } 
  \new Staff { \set Staff.midiInstrument = "clarinet" \clef "bass" g2.~ g2. c4 ees4 f4 r4 g4 a4  } 
>>
 \header { 
 piece = "D'amor mi biasmo -- A section cadence  " 
}
    \layout {}
    \midi { \context { \Score tempoWholesPerMinute = #(ly:make-moment 88 4) } }
}
    ''')
#    lilyAll += w1.incipitClass().lily()
#    print w1.incipitClass().lily()
    #print lilyAll.value
    lilyAll.showPNGandPlayMIDI()


if (__name__ == "__main__"):
#    redoLandini()
    major3rd()
    capuaReg3()
    createOrphee()
    createEasyScale()
    badMeter()