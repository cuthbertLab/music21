# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         translate.py
# Purpose:      music21 class which allows translation of music21 objects to braille.
# Authors:      Jose Cabal-Ugaz
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------


'''Objects for exporting music21 data as braille.
'''


import collections
import music21
import unittest



from music21 import chord
from music21 import instrument
from music21 import interval
from music21 import key
from music21 import meter
from music21 import note
from music21 import pitch
from music21 import stream
from music21 import tempo

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

rests = {'128th':   u'\u282d',
         '64th':    u'\u2827',
         '32nd':    u'\u2825',
         '16th':    u'\u280d',
         'eighth':  u'\u282d',
         'quarter': u'\u2827',
         'half':    u'\u2825',
         'whole':   u'\u280d'}

barlines = {'light-heavy': u'\u2823\u2805',
            'light-light': u'\u2823\u2805\u2804'}

alphabet = {'a': u'\u2801',
            'b': u'\u2803',
            'c': u'\u2809',
            'd': u'\u2819',
            'e': u'\u2811',
            'f': u'\u280b',
            'g': u'\u281b',
            'h': u'\u2813',
            'i': u'\u280a',
            'j': u'\u281a',
            'k': u'\u2805',
            'l': u'\u2807',
            'm': u'\u280d',
            'n': u'\u281d',
            'o': u'\u2815',
            'p': u'\u280f',
            'q': u'\u281f',
            'r': u'\u2817',
            's': u'\u280e',
            't': u'\u281e',
            'u': u'\u2825',
            'v': u'\u2827',
            'w': u'\u283a',
            'x': u'\u282d',
            'y': u'\u283d',
            'z': u'\u2835',
            '!': u'\u2816',
            '\'': u'\u2804',
            ',': u'\u2802',
            '-': u'\u2834',
            '.': u'\u2832',
            '?': u'\u2826'}

def instrumentToBraille(sampleInstrument = instrument.Instrument()):
    return wordStringToBraille(sampleInstrument.bestName())

def tempoTextToBraille(sampleTempoText = tempo.TempoText("adagio")):
    return wordStringToBraille(sampleTempoText.text)

def metronomeMarkToBraille(sampleMetronomeMark = tempo.MetronomeMark(number = 80, referent = note.HalfNote())):
    metroTrans = []
    metroTrans.append(c[sampleMetronomeMark.referent.type])
    metroTrans.append(u'\u2836')
    metroTrans.append(u'\u283c')
    for digit in str(sampleMetronomeMark.number):
        metroTrans.append(numbers[int(digit)])
    
    return ''.join(metroTrans)

def wordStringToBraille(sampleWordString = "Lento assai, cantante e tranquillo", returnSplit = False):
    # Can return either:
    # 1) The entire expression
    # 2) A divided expression
    
    wordStringTrans = []
    allWords = sampleWordString.split()
    for word in allWords:
        wordStringTrans.append(wordToBraille(word))
        
    if returnSplit:
        return wordStringTrans
    else:
        return u'\u2800'.join(wordStringTrans)

def wordToBraille(sampleWord = 'andante'):
    '''
    >>> from music21.braille import translate
    '''
    wordTrans = []
    for letter in sampleWord:
        if letter.isupper():
            wordTrans.append(u'\u2820' + alphabet[letter.lower()])
        else:
            wordTrans.append(alphabet[letter])
        
    return ''.join(wordTrans)

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
        return ''.join(noteTrans)
    except KeyError:
        raise BrailleTranslateException("Note duration cannot be translated to braille.")

def restToBraille(sampleRest = note.Rest()):
    '''
    Given a :class:`~music21.note.Rest`, returns the appropriate braille 
    characters as a string in utf-8 unicode.
    
    
    Currently, only supports single rests with or without dots.
    Compound rests are not supported.
    
    >>> from music21.braille import translate
    >>> from music21 import note
    >>> dottedQuarter = note.Rest(quarterLength = 1.5)
    >>> translate.restToBraille(dottedQuarter)
    u'\u2827\u2804'
    >>> whole = note.Rest(quarterLength = 4.0)
    >>> translate.restToBraille(whole)
    u'\u280d'
    >>> quarterPlusSixteenth = note.Rest(quarterLength = 1.25)
    >>> translate.restToBraille(quarterPlusSixteenth)
    Traceback (most recent call last):
    BrailleTranslateException: Rest duration cannot be translated to braille.
    '''
    try:
        restTrans = []
        simpleRest = rests[sampleRest.duration.type]
        restTrans.append(simpleRest)
        for dot in range(sampleRest.duration.dots):
            restTrans.append(u'\u2804')
        return ''.join(restTrans)
    except KeyError:
        raise BrailleTranslateException("Rest duration cannot be translated to braille.")

def measureToBraille(sampleMeasure = stream.Measure(), showLeadingOctave = True):
    '''
    Method for translating a :class:`~music21.stream.Measure` into braille. Currently, only
    translates :class:`~music21.note.Note` and :class:`~music21.note.Rest` objects.
    
    
    If showLeadingOctave is set to True, the first note of the measure carries an octave
    designation. Other notes in the measure carry an octave designation only if applicable.
    (See :meth:`~music21.braille.translate.showOctaveWithNote`.)    
    '''
    # only valid for notes and rests
    measureTrans = []
    allNotesAndRests = sampleMeasure.flat.notesAndRests
    previousNote = None
    
    for generalNote in allNotesAndRests:
        if generalNote.isNote == True:
            if previousNote == None:
                doShowOctave = showLeadingOctave
            else:
                doShowOctave = showOctaveWithNote(previousNote, generalNote)
            measureTrans.append(noteToBraille(sampleNote = generalNote, showOctave = doShowOctave))
            previousNote = generalNote
        elif generalNote.isRest == True:
            measureTrans.append(restToBraille(sampleRest = generalNote))
        else:
            raise BrailleTranslateException("General note cannot be translated to braille.")

    return ''.join(measureTrans)

def showOctaveWithNote(previousNote = note.Note('C3'), currentNote = note.Note('D3')):
    '''
    Determines whether a currentNote carries an octave designation in relation to a previousNote.
    
    
    Rules:
    
    
    * If currentNote is found within a second or third of previousNote, currentNote does not
    carry an octave designation.
    
    
    * If currentNote is found a sixth or more away from previousNote, currentNote does carry 
    an octave designation.
    
    
    * If currentNote is found within a fourth or fifth of previousNote, currentNote carries
    an octave designation if and only if currentNote and previousNote are not found in the
    same octave.
    '''
    i = interval.notesToInterval(previousNote, currentNote)
    isSixthOrGreater = i.generic.undirected >= 6
    isFourthOrFifth = i.generic.undirected == 4 or i.generic.undirected == 5
    sameOctaveAsPrevious = previousNote.octave == currentNote.octave
    doShowOctave = False
    if isSixthOrGreater or (isFourthOrFifth and not sameOctaveAsPrevious):
        doShowOctave = True
        
    return doShowOctave
    
def partToBraille(samplePart = stream.Part()):
    '''
    Given a :class:`~music21.stream.Part`, returns the appropriate braille 
    characters as a string in utf-8 unicode.
    
    
    A thing to keep in mind: there is a 40 braille character limit per line.
    All spaces are filled in with empty six-cell braille characters. 
    '''
    allLines = collections.defaultdict(str)
    lineIndex = 0
    
    allMeasures = samplePart.getElementsByClass('Measure')
    ks = keySigToBraille(allMeasures[0].getKeySignatures()[0])
    ts = timeSigToBraille(allMeasures[0].getTimeSignatures()[0])
    allLines[lineIndex] = unicode(ks + ts).center(40, u'\u2800')
    lineIndex += 1
    
    allLines[lineIndex] = u'\u283c' + numbers[allMeasures[0].number]
    previousNote = None
    
    for measure in allMeasures:
        showOctave = True
        if not len(measure.flat.notes) == 0:
            if previousNote == None:
                showOctave = True
            else:
                showOctave = showOctaveWithNote(previousNote, measure.flat.notes[0])
            previousNote = measure.flat.notes[-1]
        mtb = measureToBraille(measure, showLeadingOctave = showOctave)
        if not(len(allLines[lineIndex]) + len(mtb) + 1) > 40:
            allLines[lineIndex] += (u'\u2800' + mtb)
        else:
            allLines[lineIndex] = allLines[lineIndex].ljust(40, u'\u2800')
            lineIndex += 1
            mtb = measureToBraille(measure, showLeadingOctave = True)  
            allLines[lineIndex] = u'\u2800\u2800' + mtb
    
    allLines[lineIndex] = allLines[lineIndex].ljust(40, u'\u2800')
    return allLines
    

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