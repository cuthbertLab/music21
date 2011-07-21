# -*- coding: utf-8 -*-


import music21
import unittest

from music21 import pitch
from music21 import note
from music21 import stream
from music21 import interval

c = {'eighth':  u'\u2819',
     'quarter': u'\u2839',
     'half':    u'\u281D',
     'whole':   u'\u283D'}

d = {'eighth':  u'\u2811',
     'quarter': u'\u2831',
     'half':    u'\u2815',
     'whole':   u'\u2835'}

e = {'eighth':  u'\u280B',
     'quarter': u'\u282B',
     'half':    u'\u280F',
     'whole':   u'\u282F'}

f = {'eighth':  u'\u281B',
     'quarter': u'\u283B',
     'half':    u'\u281F',
     'whole':   u'\u283F'}

g = {'eighth':  u'\u2813',
     'quarter': u'\u2833',
     'half':    u'\u2817',
     'whole':   u'\u2837'}

a = {'eighth':  u'\u280A',
     'quarter': u'\u282A',
     'half':    u'\u280E',
     'whole':   u'\u282E'}

b = {'eighth':  u'\u281A',
     'quarter': u'\u283A',
     'half':    u'\u281E',
     'whole':   u'\u283E'}

pitchNameToNotes = {'C': c,
                    'D': d,
                    'E': e,
                    'F': f,
                    'G': g,
                    'A': a,
                    'B': b}

typeEquivalent = {'128th': 'eighth',
                  '64th': 'quarter',
                  '32nd': 'half',
                  '16th': 'whole'}

octave = {1: u'\u2808',
          2: u'\u2818',
          3: u'\u2838',
          4: u'\u2810',
          5: u'\u2828',
          6: u'\u2830',
          7: u'\u2820'}

accidental = {'sharp':          u'\u2829',
              'double-sharp':   u'\u2829\u2829',
              'flat':           u'\u2823',
              'double-flat':    u'\u2823\u2823',
              'natural':        u'\u2821'}

def translateLine(sampleLine = stream.Part()):
    if len(sampleLine.getElementsByClass('Measure')) == 0:
        sampleLine = sampleLine.makeMeasures(inPlace = False)

    mn = 0    
    for measure in sampleLine:
        for sampleNote in measure.flat.notes:
            sampleNote._brailleMeasureNumber = mn
        mn += 1
    
    allNotes = sampleLine.flat.notes 
    previousNote = allNotes[0]
    translation = []
    translation.append(translateNote(sampleNote = previousNote, withOctave = True))

    for nextNote in allNotes[1:]:
        if not(nextNote._brailleMeasureNumber == previousNote._brailleMeasureNumber):
            translation.append(u'\u2800') #space
        i = interval.notesToInterval(previousNote, nextNote)
        isSixthOrGreater = i.generic.undirected >= 6
        isFourthOrFifth = i.generic.undirected == 4 or i.generic.undirected == 5
        sameAsPrevious = previousNote.octave == nextNote.octave
        wo = False
        if isSixthOrGreater or (isFourthOrFifth and not sameAsPrevious):
            wo = True
        translation.append(translateNote(sampleNote = nextNote, withOctave = wo))
        previousNote = nextNote

    return ''.join(translation)

def translateNote(sampleNote = note.Note('C4'), withOctave = False):
    pitchNameDict = pitchNameToNotes[sampleNote.step]
    translation = []
    if withOctave:
        translation.append(octave[sampleNote.octave])
    
    if not(sampleNote.step == sampleNote.name):
        try:
            translation.append(accidental[sampleNote.accidental.name])
        except KeyError:
            raise BrailleTranslateException("Accidental type cannot be translated to braille.")
    
    try:
        if sampleNote.duration.type in typeEquivalent.keys():
            nameWithLength = pitchNameDict[typeEquivalent[sampleNote.duration.type]]
        else:
            nameWithLength = pitchNameDict[sampleNote.duration.type]

        translation.append(nameWithLength) 
        for dot in range(sampleNote.duration.dots):
            translation.append(u'\u2804') #dot          
    except KeyError:
        raise BrailleTranslateException("Note duration cannot be translated to braille.")
        
    return ''.join(translation)


def translateAccidental():
    pass



class BrailleTranslateException(music21.Music21Exception):
    pass
    
#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

if __name__ == "__main__":
    print translateNote(note.Note('C##4', quarterLength = 2.0))
    #music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof