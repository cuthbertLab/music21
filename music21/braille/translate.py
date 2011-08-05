# -*- coding: utf-8 -*-
#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         translate.py
# Purpose:      music21 class which allows translation of music21 data to braille.
# Authors:      Jose Cabal-Ugaz
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------


'''
Objects for exporting music21 data as braille.
'''


import collections
import music21
import unittest

from music21 import bar
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
     'whole':   u'\u283d',
     'breve':   u'\u283d\u2818\u2809\u283d'}

d = {'128th':   u'\u2811',
     '64th':    u'\u2831',
     '32nd':    u'\u2815',
     '16th':    u'\u2835',
     'eighth':  u'\u2811',
     'quarter': u'\u2831',
     'half':    u'\u2815',
     'whole':   u'\u2835',
     'breve':   u'\u2835\u2818\u2809\u2835'}

e = {'128th':   u'\u280b',
     '64th':    u'\u282b',
     '32nd':    u'\u280f',
     '16th':    u'\u282f',
     'eighth':  u'\u280b',
     'quarter': u'\u282b',
     'half':    u'\u280f',
     'whole':   u'\u282f',
     'breve':   u'\u282f\u2818\u2809\u282f'}

f = {'128th':   u'\u281b',
     '64th':    u'\u283b',
     '32nd':    u'\u281f',
     '16th':    u'\u283f',
     'eighth':  u'\u281b',
     'quarter': u'\u283b',
     'half':    u'\u281f',
     'whole':   u'\u283f',
     'breve':   u'\u283f\u2818\u2809\u283f'}

g = {'128th':   u'\u2813',
     '64th':    u'\u2833',
     '32nd':    u'\u2817',
     '16th':    u'\u2837',
     'eighth':  u'\u2813',
     'quarter': u'\u2833',
     'half':    u'\u2817',
     'whole':   u'\u2837',
     'breve':   u'\u2837\u2818\u2809\u2837'}

a = {'128th':   u'\u280a',
     '64th':    u'\u282a',
     '32nd':    u'\u280e',
     '16th':    u'\u282e',
     'eighth':  u'\u280a',
     'quarter': u'\u282a',
     'half':    u'\u280e',
     'whole':   u'\u282e',
     'breve':   u'\u282e\u2818\u2809\u282e'}

b = {'128th':   u'\u281a',
     '64th':    u'\u283a',
     '32nd':    u'\u281e',
     '16th':    u'\u283e',
     'eighth':  u'\u281a',
     'quarter': u'\u283a',
     'half':    u'\u281e',
     'whole':   u'\u283e',
     'breve':   u'\u283e\u2818\u2809\u283e'}

pitchNameToNotes = {'C': c,
                    'D': d,
                    'E': e,
                    'F': f,
                    'G': g,
                    'A': a,
                    'B': b}

octaves = {0: u'\u2808\u2808',
           1: u'\u2808',
           2: u'\u2818',
           3: u'\u2838',
           4: u'\u2810',
           5: u'\u2828',
           6: u'\u2830',
           7: u'\u2820',
           8: u'\u2820\u2820'}

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
         'whole':   u'\u280d',
         'breve':   u'\u280d\u2818\u2809\u280d'}

barlines = {'final': u'\u2823\u2805',
            'double': u'\u2823\u2805\u2804'}

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

symbols = {'space': u'\u2800',
           'double-space': u'\u2800\u2800',
           'number': u'\u283c',
           'dot': u'\u2804',
           'tie': u'\u2808\u2809',
           'uppercase': u'\u2820',
           'metronome': u'\u2836',
           'common': u'\u2828\u2809',
           'cut': u'\u2838\u2809'}

def headingToBraille(sampleTempoText = tempo.TempoText("Allegretto"), sampleKeySig = key.KeySignature(5), sampleTimeSig = meter.TimeSignature('3/8'),
                     sampleMetronomeMark = tempo.MetronomeMark(number = 135, referent = note.EighthNote())):
    
    kts_braille = keyAndTimeSigToBraille(sampleKeySig = sampleKeySig, sampleTimeSig = sampleTimeSig)
    tt_braille = tempoTextToBraille(sampleTempoText = sampleTempoText)
    mm_braille = metronomeMarkToBraille(sampleMetronomeMark = sampleMetronomeMark)
    
    mm_kts_braille = None
    if not kts_braille == None:
        if not mm_braille == None:
            mm_kts_braille = mm_braille + symbols['space'] + kts_braille
        else:
            mm_kts_braille = kts_braille
            
    tt_mm_kts_braille = None
    if not tt_braille == None:
        if not mm_kts_braille == None:
            allLines = tt_braille.splitlines()
            if len(allLines) == 1 and len(allLines[0]) + len(mm_kts_braille) + 1 <= 34:
                tt_mm_kts_braille = (allLines[0] + symbols['space'] + mm_kts_braille).center(40, symbols['space'])
            else:
                allLines.append(mm_kts_braille)
                tt_mm_kts_braille = []
                for line in allLines:
                    tt_mm_kts_braille.append(line.center(40, symbols['space']))
                tt_mm_kts_braille = u"\n".join(tt_mm_kts_braille)
        else:
            tt_mm_kts_braille = tt_braille
    else:
        if not mm_kts_braille == None:
            tt_mm_kts_braille = mm_kts_braille.center(40, symbols['space'])
    
    return tt_mm_kts_braille

def numberToBraille(sampleNumber = 12):
    '''
    >>> from music21.braille import translate
    >>> translate.numberToBraille(sampleNumber = 12)
    u'\u283c\u2801\u2803'
    >>> translate.numberToBraille(sampleNumber = 7)
    u'\u283c\u281b'
    >>> translate.numberToBraille(sampleNumber = 37)
    u'\u283c\u2809\u281b'
    '''
    numberTrans = []
    numberTrans.append(symbols['number'])
    for digit in str(sampleNumber):
        numberTrans.append(numbers[int(digit)])
    
    return ''.join(numberTrans)

def instrumentToBraille(sampleInstrument = instrument.Instrument()):
    return wordStringToBraille(sampleInstrument.bestName())

def tempoTextToBraille(sampleTempoText = tempo.TempoText("Lento assai, cantante e tranquillo")):
    if sampleTempoText == None:
        return None
        
    allPhrases = sampleTempoText.text.split(",")
    braillePhrases = []
    for samplePhrase in allPhrases:
        allWords = samplePhrase.split()
        phraseTrans = []
        for sampleWord in allWords:
            brailleWord = wordToBraille(sampleWord)
            if not (len(phraseTrans) + len(brailleWord) + 1 > 34):
                phraseTrans.append(brailleWord)
                phraseTrans.append(symbols['space'])
            else:
                phraseTrans.append(u"\n")
                phraseTrans.append(brailleWord)
                phraseTrans.append(symbols['space'])
        braillePhrases.append(u"".join(phraseTrans[0:-1]))
    
    brailleText = []
    for braillePhrase in braillePhrases:
        brailleText.append(braillePhrase)
        brailleText.append(alphabet[","])
        brailleText.append(u"\n")
        
    brailleText = brailleText[0:-2]
    brailleText.append(alphabet["."]) # literary period
    return u"".join(brailleText)

def wordToBraille(sampleWord = 'Andante'):
    '''
    >>> from music21.braille import translate
    '''
    wordTrans = []
    for letter in sampleWord:
        if letter.isupper():
            wordTrans.append(symbols['uppercase'] + alphabet[letter.lower()])
        else:
            wordTrans.append(alphabet[letter])
        
    return ''.join(wordTrans)

def metronomeMarkToBraille(sampleMetronomeMark = tempo.MetronomeMark(number = 80, referent = note.HalfNote())):
    if sampleMetronomeMark == None:
        return None
    metroTrans = []
    metroTrans.append(noteToBraille(note.Note('C4', quarterLength = sampleMetronomeMark.referent.quarterLength), showOctave = False))
    metroTrans.append(symbols['metronome'])
    metroTrans.append(numberToBraille(sampleMetronomeMark.number))
    
    return ''.join(metroTrans)

def keySigToBraille(sampleKeySig = key.KeySignature(0)):
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
    if len(sampleTimeSig.symbol) != 0:
        if sampleTimeSig.symbol == 'common':
            return symbols['common']
        elif sampleTimeSig.symbol == 'cut':
            return symbols['cut']

    timeSigTrans = []
    numberSign = symbols['number']
    timeSigTrans.append(numberSign)
    
    beatCount = str(sampleTimeSig.numerator)
    for digit in beatCount:
        timeSigTrans.append(numbers[int(digit)])
    
    timeSigTrans.append(beatUnits[sampleTimeSig.denominator])
    
    return ''.join(timeSigTrans)

def keyAndTimeSigToBraille(sampleKeySig = key.KeySignature(0), sampleTimeSig = meter.TimeSignature('3/4')):
    '''
    Takes in a :class:`~music21.key.KeySignature` and :class:`~music21.meter.TimeSignature`.
    Returns a unicode string corresponding to the combined key/time signature in braille.
    Returns None if both the key and time signature are None, or if the time signature is
    None and the key signature corresponds to no sharps or flats.
    '''
    if (sampleTimeSig == None) and (sampleKeySig == None or sampleKeySig.sharps == 0):
        return None
    
    if sampleKeySig == None:
        ks_braille = keySigToBraille()
    else:
        ks_braille = keySigToBraille(sampleKeySig)

    if not (sampleTimeSig == None):
        ts_braille = timeSigToBraille(sampleTimeSig)
        return ks_braille + ts_braille
    else:
        return ks_braille
    
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
            noteTrans.append(symbols['dot'])
        if not sampleNote.tie == None and not sampleNote.tie.type == 'stop':
            noteTrans.append(symbols['tie'])
        return ''.join(noteTrans)
    except KeyError:
        raise BrailleTranslateException("Note duration '" + sampleNote.duration.type + "' cannot be translated to braille.")

def restToBraille(sampleRest = note.Rest()):
    '''
    Given a :class:`~music21.note.Rest`, returns the appropriate braille 
    characters as a string in utf-8 unicode.
    
    
    Currently, only supports single rests with or without dots.
    Complex rests are not supported.
    
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
            restTrans.append(symbols['dot'])
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
    measureTrans = []
    previousNote = None
    
    for element in sampleMeasure:
        if isinstance(element, note.Note):
            if previousNote == None:
                doShowOctave = showLeadingOctave
            else:
                doShowOctave = showOctaveWithNote(previousNote, element)
            measureTrans.append(noteToBraille(sampleNote = element, showOctave = doShowOctave))
            previousNote = element
        elif isinstance(element, note.Rest):
            if element.duration == sampleMeasure.duration:
                # if the rest lasts the entire measure, then use whole note rest.
                measureTrans.append(restToBraille(sampleRest = note.Rest(quarterLength = 4.0)))
            else:
                measureTrans.append(restToBraille(sampleRest = element))
        elif isinstance(element, bar.Barline):
            measureTrans.append(barlines[element.style])            
    
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
    tt = None
    try:
        tt = allMeasures[0].getElementsByClass('TempoText')[0]
    except IndexError:
        pass
    
    mm = None
    try:
        mm = allMeasures[0].getElementsByClass('MetronomeMark')[0]
    except IndexError:
        pass

    tt_mm_kts_braille = headingToBraille(sampleKeySig = allMeasures[0].keySignature, sampleTimeSig = allMeasures[0].timeSignature,
                                         sampleTempoText = tt, sampleMetronomeMark = mm)
    
    if not tt_mm_kts_braille == None:
        for sampleLine in tt_mm_kts_braille.splitlines():
            allLines[lineIndex] = tt_mm_kts_braille
            lineIndex += 1

    allLines[lineIndex] = symbols['number'] + numbers[allMeasures[0].number]
    previousNote = None    
    
    for measure in allMeasures:
        if measure.keyIsNew and measure.timeSignatureIsNew:
            pass
        if measure.keyIsNew:
            pass
        if measure.timeSignatureIsNew:
            pass
        showOctave = True
        if not len(measure.flat.notes) == 0:
            if not previousNote == None:
                showOctave = showOctaveWithNote(previousNote, measure.flat.notes[0])
            previousNote = measure.flat.notes[-1]
        mtb = measureToBraille(measure, showLeadingOctave = showOctave)
        if not(len(allLines[lineIndex]) + len(mtb) + 1) > 40:
            allLines[lineIndex] += (symbols['space'] + mtb)
        else:
            allLines[lineIndex] = allLines[lineIndex].ljust(40, symbols['space'])
            lineIndex += 1
            mtb = measureToBraille(measure, showLeadingOctave = True)  
            allLines[lineIndex] = symbols['double-space'] + mtb
    
    allLines[lineIndex] = allLines[lineIndex].ljust(40, symbols['space'])
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