# -*- coding: utf-8 -*-

import codecs

from music21.braille import translate

from music21 import stream
from music21 import meter
from music21 import note

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
    bm = stream.Score()
    #bm.append(meter.TimeSignature('3/4'))
    m1 = stream.Measure()
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
    return bm
    
if __name__ == '__main__':    
    t = translate.translateLine(melodyA())
    f = codecs.open('tester.txt', encoding='utf-8', mode='w+')
    f.write(t)
    f.close()
