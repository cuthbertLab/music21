# -*- coding: utf-8 -*-

import music21
import unittest
import collections

from music21 import pitch
from music21 import note
from music21 import chord
from music21 import stream
from music21 import interval
from music21 import key
from music21 import meter

c = {'128th':   u'\u2819',
     '64th':    u'\u2839',
     '32nd':    u'\u281d',
     '16th':    u'\u283d',
     'eighth':  u'\u2819',
     'quarter': u'\u2839',
     'half':    u'\u281d',
     'whole':   u'\u283d'}

d = {'128th':   u'\u2811',
     '64th':    u'\u2831',
     '32nd':    u'\u2815',
     '16th':    u'\u2835',
     'eighth':  u'\u2811',
     'quarter': u'\u2831',
     'half':    u'\u2815',
     'whole':   u'\u2835'}

e = {'128th':   u'\u280b',
     '64th':    u'\u282b',
     '32nd':    u'\u280f',
     '16th':    u'\u282f',
     'eighth':  u'\u280b',
     'quarter': u'\u282b',
     'half':    u'\u280f',
     'whole':   u'\u282f'}

f = {'128th':   u'\u281b',
     '64th':    u'\u283b',
     '32nd':    u'\u281f',
     '16th':    u'\u283f',
     'eighth':  u'\u281b',
     'quarter': u'\u283b',
     'half':    u'\u281f',
     'whole':   u'\u283f'}

g = {'128th':   u'\u2813',
     '64th':    u'\u2833',
     '32nd':    u'\u2817',
     '16th':    u'\u2837',
     'eighth':  u'\u2813',
     'quarter': u'\u2833',
     'half':    u'\u2817',
     'whole':   u'\u2837'}

a = {'128th':   u'\u280a',
     '64th':    u'\u282a',
     '32nd':    u'\u280e',
     '16th':    u'\u282e',
     'eighth':  u'\u280a',
     'quarter': u'\u282a',
     'half':    u'\u280e',
     'whole':   u'\u282e'}

b = {'128th':   u'\u281a',
     '64th':    u'\u283a',
     '32nd':    u'\u281e',
     '16th':    u'\u283e',
     'eighth':  u'\u281a',
     'quarter': u'\u283a',
     'half':    u'\u281e',
     'whole':   u'\u283e'}

pitchNameToNotes = {'C': c,
                    'D': d,
                    'E': e,
                    'F': f,
                    'G': g,
                    'A': a,
                    'B': b}

octaves = {1: u'\u2808',
           2: u'\u2818',
           3: u'\u2838',
           4: u'\u2810',
           5: u'\u2828',
           6: u'\u2830',
           7: u'\u2820'}

accidentals = {'sharp':          u'\u2829',
               'double-sharp':   u'\u2829\u2829',
               'flat':           u'\u2823',
               'double-flat':    u'\u2823\u2823',
               'natural':        u'\u2821'}

intervals = {2: u'\u280c',
             3: u'\u282c',
             4: u'\u283c',
             5: u'\u2814',
             6: u'\u2834',
             7: u'\u2812',
             8: u'\u2824'}

keySignatures = {-7:    u'\u283c\u281b\u2823',
                 -6:    u'\u283c\u280b\u2823',
                 -5:    u'\u283c\u2811\u2823',
                 -4:    u'\u283c\u2819\u2823',
                 -3:    u'\u2823\u2823\u2823',
                 -2:    u'\u2823\u2823',
                 -1:    u'\u2823',
                 0:     u'',
                 1:     u'\u2829',
                 2:     u'\u2829\u2829',
                 3:     u'\u2829\u2829\u2829',
                 4:     u'\u283c\u2819\u2829',
                 5:     u'\u283c\u2811\u2829',
                 6:     u'\u283c\u280b\u2829',
                 7:     u'\u283c\u281b\u2829'}

numbers = {0: u'\u281a',
           1: u'\u2801',
           2: u'\u2803',
           3: u'\u2809',
           4: u'\u2819',
           5: u'\u2811',
           6: u'\u280b',
           7: u'\u281b',
           8: u'\u2813',
           9: u'\u280a'}

beatUnits = {2: u'\u2806',
             4: u'\u2832',
             8: u'\u2826'}          

def keySigToBraille(sampleKeySig = key.KeySignature(1)):
    '''
    Takes in a :class:`~music21.key.KeySignature` and returns its
    representation in braille as a string in utf-8 unicode.
    
    >>> from music21.braille import translate
    >>> from music21 import key
    >>> ksFourSharps = key.KeySignature(4)
    >>> translate.keySigToBraille(ksFourSharps)
    u'\u283c\u2819\u2829'
    '''
    return keySignatures[sampleKeySig.sharps]

def timeSigToBraille(sampleTimeSig = meter.TimeSignature('3/4')):
    '''
    Takes in a :class:`~music21.meter.TimeSignature` and returns its
    representation in braille as a string in utf-8 unicode.
    
    
    The format for a numerical time signature in braille is the number
    symbol + beat count as a braille number + beat units, also a braille
    number but brought down in the cell.
    
    >>> from music21.braille import translate
    >>> from music21 import meter
    >>> translate.timeSigToBraille(sampleTimeSig = meter.TimeSignature('3/4'))
    u'\u283c\u2809\u2832'
    >>> translate.timeSigToBraille(sampleTimeSig = meter.TimeSignature('12/8'))
    u'\u283c\u2801\u2803\u2826'
    >>> translate.timeSigToBraille(sampleTimeSig = meter.TimeSignature('4/4'))
    u'\u283c\u2819\u2832'
    '''
    timeSigTrans = []
    numberSign = u'\u283c'
    timeSigTrans.append(numberSign)
    
    beatCount = str(sampleTimeSig.numerator)
    for digit in beatCount:
        timeSigTrans.append(numbers[int(digit)])
    
    timeSigTrans.append(beatUnits[sampleTimeSig.denominator])
    
    return ''.join(timeSigTrans)
    
def noteToBraille(sampleNote = note.Note('C4'), showOctave = True):
    '''
    Given a :class:`~music21.note.Note`, returns the appropriate braille 
    characters as a string in utf-8 unicode.
    
    
    The format for note display in braille is the accidental (if necessary)
    + octave (if necessary) + pitch name with length.
    
    
    If the note has an :class:`~music21.pitch.Accidental`, the accidental is always 
    displayed unless its :attr:`~music21.pitch.Accidental.displayStatus` is set to 
    False. The octave of the note is only displayed if showOctave is set to True.
    
    
    >>> from music21.braille import translate
    >>> from music21 import note
    >>> C4 = note.Note('C4')
    >>> translate.noteToBraille(sampleNote = C4)
    u'\u2810\u2839'
    >>> C4.quarterLength = 2.0
    >>> translate.noteToBraille(sampleNote = C4)
    u'\u2810\u281d'
    >>> Ds4 = note.Note('D#4')
    >>> translate.noteToBraille(sampleNote = Ds4)
    u'\u2829\u2810\u2831'
    >>> translate.noteToBraille(sampleNote = Ds4, showOctave = False)
    u'\u2829\u2831'
    >>> Ds4.pitch.setAccidentalDisplay(False)
    >>> translate.noteToBraille(sampleNote = Ds4)
    u'\u2810\u2831'
    >>> A2 = note.Note('A2')
    >>> A2.quarterLength = 3.0
    >>> translate.noteToBraille(sampleNote = A2)
    u'\u2818\u280e\u2804'
    '''
    noteTrans = []
    notesInStep = pitchNameToNotes[sampleNote.step]
    
    if not(sampleNote.accidental == None):
        if not(sampleNote.accidental.displayStatus == False):
            try:
                noteTrans.append(accidentals[sampleNote.accidental.name])
            except KeyError:
                raise BrailleTranslateException("Accidental type cannot be translated to braille.")  
    
    if showOctave:
        noteTrans.append(octaves[sampleNote.octave])

    try:
        nameWithLength = notesInStep[sampleNote.duration.type]
        noteTrans.append(nameWithLength) 
        for dot in range(sampleNote.duration.dots):
            noteTrans.append(u'\u2804')
    except KeyError:
        raise BrailleTranslateException("Note duration cannot be translated to braille.")
        
    return ''.join(noteTrans)

def partToBraille(samplePart = stream.Part()):
    # TODO: Fix inconsistencies.
    allMeasures = samplePart.getElementsByClass('Measure')
    ks = keySigToBraille(allMeasures[0].getKeySignatures()[0])
    ts = timeSigToBraille(allMeasures[0].getTimeSignatures()[0])
    kts = unicode(ks + ts).center(40, u'\u2800')
    
    allNotes = allMeasures.flat.notesAndRests
    previousNote = allNotes[0]
    partTrans = collections.defaultdict(list)
    partTrans[previousNote.measureNumber].append(noteToBraille(sampleNote = previousNote, showOctave = True))

    for nextNote in allNotes[1:]:
        i = interval.notesToInterval(previousNote, nextNote)
        isSixthOrGreater = i.generic.undirected >= 6
        isFourthOrFifth = i.generic.undirected == 4 or i.generic.undirected == 5
        sameAsPrevious = previousNote.octave == nextNote.octave
        doShowOctave = False
        if isSixthOrGreater or (isFourthOrFifth and not sameAsPrevious):
            doShowOctave = True
        partTrans[nextNote.measureNumber].append(noteToBraille(sampleNote = nextNote, showOctave = doShowOctave))
        previousNote = nextNote

    x = []
    for measureNumber in partTrans.keys():
        for element in partTrans[measureNumber]:
            x.append(element)
        x.append(u'\u2800') #space
    return kts + '\n' + ''.join(x[0:-1])    
    

class BrailleTranslateException(music21.Music21Exception):
    pass
    
#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

if __name__ == "__main__":
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof