
### CHAPTER 1 

import music21
from music21 import clef
from music21 import instrument

def ch1():
 def basic():
  def II():
   def A():
    def ex1():
        '''
        p3.
        Write letter names and octave designations for the pitches written in the treble and bass clefs below.
    
        (Data in Finale/musicxml format)
        '''
        exercise = music21.parseData("p3_II_A_1.xml")
        for thisNote in exercise.notes:
            thisNote.lyric = thisNote.noteNameWithOctave
        exercise.show()

 def writing():
  def I():
   def B():
    def ex3():
        '''
        p. 7.
        Transcribe Purcell, "Music for a While" for bassoon in tenor clef
        '''
        purcellScore = music21.parseData("Music_for_a_while.musicxml")
        thisClef = purcellScore.getElementsByClass(clef.Clef)[0]
        thisClef.__class__ = clef.TenorClef
        purcellScore.insert(0, instrument.Instrument('bassoon'))
        assert purcellScore.allInRange() is True
        purcellScore.playMidi()   ## will play on bassoon
        purcellScore.show() 
