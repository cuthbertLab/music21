# -*- coding: utf-8 -*-

import codecs

from music21.braille import translate

from music21 import stream
from music21 import meter
from music21 import note
from music21 import key
from music21 import meter
from music21 import tinyNotation

def example2_1():
    bm = tinyNotation.TinyNotationStream("g8 r8 e8 f8 r8 a8 g8 r8 f8 e8 r8 r8 e8 r8 c8 d8 r8 f8 e8 r8 d8 c8 r8 r8 \
    d8 r8 f8 e8 r8 g8 f8 g8 a8 g8 r8 r8 a8 r8 f8 g8 r8 e8 f8 e8 d8 c8 r8 r8")
    bm.insert(0, key.KeySignature(0))
    bm.insert(0, meter.TimeSignature('3/8'))
    bm.makeMeasures(inPlace = True)
    return bm

def example2_2():
    bm = tinyNotation.TinyNotationStream("r8 r8 r8 d8 d8 c8 B8 d8 c8 B8 A8 c8 B8 A8 G8 B8 A8 A8 D8 r8 E8 E8 G8 E8 D8 E8 G8 B8 D8 C8 B8 A8 G8 G8 G8 r8")
    bm.insert(0, key.KeySignature(0))
    bm.insert(0, meter.TimeSignature('4/8'))
    bm.makeMeasures(inPlace = True)
    return bm

def melodyA():
    '''
    "My Bonnie Lies Over the Ocean"
    page 168, Dictionary of Braille Music Signs
    Krolick, Bettye
    National Library Service
    for the Blind and Physically Handicapped
    Library of Congress
    Washington, D.C. 20542 1979
    '''
    bm = stream.Part()
    m1 = stream.Measure()
    m1.append(key.KeySignature(0))
    m1.append(meter.TimeSignature('3/4'))
    m1.append(note.Note('C4'))    
    m2 = stream.Measure()
    m2.append(note.Note('A4'))
    m2.append(note.Note('G4'))
    m2.append(note.Note('F4'))
    m3 = stream.Measure()
    m3.append(note.Note('G4'))
    m3.append(note.Note('F4'))
    m3.append(note.Note('D4'))
    m4 = stream.Measure()
    m4.append(note.Note('C4'))
    m4.append(note.Note('A3', quarterLength = 2.0)) 
    bm.append([m1, m2, m3, m4])
    bm.makeAccidentals()
    return bm
    
def melodyB():
    '''
    Same source as before.
    '''
    bm = stream.Part()
    bm.append(meter.TimeSignature('3/4'))
    bm.append(note.Note('C4', quarterLength = 3.0))
    bm.append(note.Note('F4', quarterLength = 3.0))
    bm.append(note.Note('D4', quarterLength = 3.0))
    bm.append(note.Note('G4', quarterLength = 2.0))
    bm.append(note.Note('F4'))
    bm.append(note.Note('E4'))
    bm.append(note.Note('E4'))
    bm.append(note.Note('E4'))
    bm.append(note.Note('E4'))
    bm.append(note.Note('D4'))
    bm.append(note.Note('E4'))
    return bm

def melodyC():
    bm = stream.Score()
    topPart = stream.Part()
    bottomPart = stream.Part()
    
    topPart.append(key.KeySignature(0))
    bottomPart.append(key.KeySignature(0))
    
    topPart.append(note.Note('B4', quarterLength = 2.0))
    topPart.append(note.Note('C5', quarterLength = 2.0))
    bottomPart.append(note.Note('F4'))
    bottomPart.append(note.Note('G4'))
    bottomPart.append(note.Note('E4'))
    bottomPart.append(note.Note('G#4'))
    
    topPart.makeAccidentals()
    bottomPart.makeAccidentals()
    
    print topPart.haveAccidentalsBeenMade()
    print bottomPart.haveAccidentalsBeenMade()
    
    bm.insert(0, topPart)
    bm.insert(0, bottomPart)
    
    return bm
    

if __name__ == '__main__':
    from music21 import corpus
    jmf = corpus.parse('bach/bwv227.1.xml') # Jesu meine freude
    #jmf.show('text')
    t = translate.partToBraille(jmf[1])
    #f = codecs.open('jesu meine freude.txt', encoding='utf-8', mode='w+')
    for i in sorted(t.keys()):
        print t[i]
        #f.write(t[i] + u"\n")
    #f.close()