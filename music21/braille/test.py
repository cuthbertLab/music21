# -*- coding: utf-8 -*-

import codecs

from music21.braille import translate

from music21 import stream
from music21 import meter
from music21 import note
from music21 import key

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
    t = translate.partToBraille(jmf[1])
    print t