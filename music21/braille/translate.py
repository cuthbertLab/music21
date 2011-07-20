from music21 import pitch
from music21 import note
from music21 import stream
from music21 import interval

c = {0.5: u'\u2819',
     1.0: u'\u2839',
     2.0: u'\u281D',
     4.0: u'\u283D'}

d = {0.5: u'\u2811',
     1.0: u'\u2831',
     2.0: u'\u2815',
     4.0: u'\u2835'}

e = {0.5: u'\u280B',
     1.0: u'\u282B',
     2.0: u'\u280F',
     4.0: u'\u282F'}

f = {0.5: u'\u281B',
     1.0: u'\u283B',
     2.0: u'\u281F',
     4.0: u'\u283F'}

g = {0.5: u'\u2813',
     1.0: u'\u2833',
     2.0: u'\u2817',
     4.0: u'\u2837'}

a = {0.5: u'\u280A',
     1.0: u'\u282A',
     2.0: u'\u280E',
     4.0: u'\u282E'}

b = {0.5: u'\u281A',
     1.0: u'\u283A',
     2.0: u'\u281E',
     4.0: u'\u283E'}

pitchNameToNotes = {'C': c,
                    'D': d,
                    'E': e,
                    'F': f,
                    'G': g,
                    'A': a,
                    'B': b}

qlEquivalent = {0.03125: 0.5,
                0.0625: 1.0,
                0.125: 2.0,
                0.25: 4.0}

octave = {1: u'\u2808',
          2: u'\u2818',
          3: u'\u2838',
          4: u'\u2810',
          5: u'\u2828',
          6: u'\u2830',
          7: u'\u2820'}

def translateLine(sampleLine = stream.Part()):
    allNotes = sampleLine.flat.notes 
    previousNote = allNotes[0]
    translation = []
    translation.append(translateNote(sampleNote = previousNote, withOctave = True))
    
    for nextNote in allNotes[1:]:
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
    pitchNameDict = pitchNameToNotes[sampleNote.name]
    nameWithLength = None
    try:
        nameWithLength = pitchNameDict[sampleNote.quarterLength]
    except KeyError:
        try:
            nameWithLength = pitchNameDict[qlEquivalent[sampleNote.quarterLength]]
        except KeyError:
            raise Exception("Cannot translate quarterLength to braille.")

    if withOctave:
        octaveNumber = octave[sampleNote.octave]
        return octaveNumber + nameWithLength
    
    return nameWithLength
        
def translateAccidental():
    pass


if __name__ == '__main__':
    print translateNote(withOctave = True)