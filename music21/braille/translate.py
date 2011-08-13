# -*- coding: utf-8 -*-
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

naturals = {0: u'',
            1: u'\u2821',
            2: u'\u2821\u2821',
            3: u'\u2821\u2821\u2821',
            4: u'\u283c\u2819\u2821',
            5: u'\u283c\u2811\u2821',
            6: u'\u283c\u280b\u2821',
            7: u'\u283c\u281b\u2821'}

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
           'cut': u'\u2838\u2809',
           'music_hyphen': u'\u2810',
           'music_asterisk': u'\u281c\u2822\u2814',
           'music_parenthesis': u''}

ascii_chars = {u'\u2800': ' ',
               u'\u2801': 'A',
               u'\u2802': '1',
               u'\u2803': 'B',
               u'\u2804': '\'',
               u'\u2805': 'K',
               u'\u2806': '2',
               u'\u2807': 'L',
               u'\u2808': '@',
               u'\u2809': 'C',
               u'\u280a': 'I',
               u'\u280b': 'F',
               u'\u280c': '/',
               u'\u280d': 'M',
               u'\u280e': 'S',
               u'\u280f': 'P',
               u'\u2810': '"',
               u'\u2811': 'E',
               u'\u2812': '3',
               u'\u2813': 'H',
               u'\u2814': '9',
               u'\u2815': 'O',
               u'\u2816': '6',
               u'\u2817': 'R',
               u'\u2818': '^',
               u'\u2819': 'D',
               u'\u281a': 'J',
               u'\u281b': 'G',
               u'\u281c': '>',
               u'\u281d': 'N',
               u'\u281e': 'T',
               u'\u281f': 'Q',
               u'\u2820': ',',     
               u'\u2821': '*',
               u'\u2822': '5',
               u'\u2823': '<',
               u'\u2824': '-',
               u'\u2825': 'U',
               u'\u2826': '8',
               u'\u2827': 'V',
               u'\u2828': '.',
               u'\u2829': '%',
               u'\u282a': '[',
               u'\u282b': '$',
               u'\u282c': '+',
               u'\u282d': 'X',
               u'\u282e': '!',
               u'\u282f': '&',
               u'\u2830': ';',     
               u'\u2831': ':',
               u'\u2832': '4',
               u'\u2833': '\\',
               u'\u2834': '0',
               u'\u2835': 'Z',
               u'\u2836': '7',
               u'\u2837': '(',
               u'\u2838': '_',
               u'\u2839': '?',
               u'\u283a': 'W',
               u'\u283b': ']',
               u'\u283c': '#',
               u'\u283d': 'Y',
               u'\u283e': ')',
               u'\u283f': '='}

binary_dots = {u'\u2800': ('00','00','00'),
               u'\u2801': ('10','00','00'),
               u'\u2802': ('00','10','00'),
               u'\u2803': ('10','10','00'),
               u'\u2804': ('00','00','10'),
               u'\u2805': ('10','00','10'),
               u'\u2806': ('00','10','10'),
               u'\u2807': ('10','10','10'),
               u'\u2808': ('01','00','00'),
               u'\u2809': ('11','00','00'),
               u'\u280a': ('01','10','00'),
               u'\u280b': ('11','10','00'),
               u'\u280c': ('01','00','10'),
               u'\u280d': ('11','00','10'),
               u'\u280e': ('01','10','10'),
               u'\u280f': ('11','10','10'),
               u'\u2810': ('00','01','00'),
               u'\u2811': ('10','01','00'),
               u'\u2812': ('00','11','00'),
               u'\u2813': ('10','11','00'),
               u'\u2814': ('00','01','10'),
               u'\u2815': ('10','01','10'),
               u'\u2816': ('00','11','10'),
               u'\u2817': ('10','11','10'),
               u'\u2818': ('01','01','00'),
               u'\u2819': ('11','01','00'),
               u'\u281a': ('01','11','00'),
               u'\u281b': ('11','11','00'),
               u'\u281c': ('01','01','10'),
               u'\u281d': ('11','01','10'),
               u'\u281e': ('01','11','10'),
               u'\u281f': ('11','11','10'),
               u'\u2820': ('00','00','01'),    
               u'\u2821': ('10','00','01'),
               u'\u2822': ('00','10','01'),
               u'\u2823': ('10','10','01'),
               u'\u2824': ('00','00','11'),
               u'\u2825': ('10','00','11'),
               u'\u2826': ('00','10','11'),
               u'\u2827': ('10','10','11'),
               u'\u2828': ('01','00','01'),
               u'\u2829': ('11','00','01'),
               u'\u282a': ('01','10','01'),
               u'\u282b': ('11','10','01'),
               u'\u282c': ('01','00','11'),
               u'\u282d': ('11','00','11'),
               u'\u282e': ('01','10','11'),
               u'\u282f': ('11','10','11'),
               u'\u2830': ('00','01','01'),     
               u'\u2831': ('10','01','01'),
               u'\u2832': ('00','11','01'),
               u'\u2833': ('10','11','01'),
               u'\u2834': ('00','01','11'),
               u'\u2835': ('10','01','11'),
               u'\u2836': ('00','11','11'),
               u'\u2837': ('01','11','11'),
               u'\u2838': ('01','01','01'),
               u'\u2839': ('11','01','01'),
               u'\u283a': ('01','11','01'),
               u'\u283b': ('11','11','01'),
               u'\u283c': ('01','01','11'),
               u'\u283d': ('11','01','11'),
               u'\u283e': ('01','11','11'),
               u'\u283f': ('11','11','11')}

def keySigToBraille(sampleKeySig = key.KeySignature(0), oldKeySig = None):
    '''
    Takes in a :class:`~music21.key.KeySignature` and returns its representation 
    in braille as a string in utf-8 unicode.
    
    >>> from music21.braille import translate
    >>> from music21 import key
    >>> print translate.keySigToBraille(sampleKeySig = key.KeySignature(4))
    ⠼⠙⠩
       
    
    If given an old key signature, then its cancellation will be applied before
    and in relation to the new key signature.
     

    >>> print translate.keySigToBraille(sampleKeySig = key.KeySignature(0), oldKeySig = key.KeySignature(-3))
    ⠡⠡⠡
    '''
    if sampleKeySig == None:
        raise BrailleTranslateException("No key signature provided!")
    ks_braille = keySignatures[sampleKeySig.sharps]
    if oldKeySig == None:
        return ks_braille

    trans = []
    if sampleKeySig.sharps == 0 or oldKeySig.sharps == 0 or \
        not (oldKeySig.sharps / abs(oldKeySig.sharps) == sampleKeySig.sharps / abs(sampleKeySig.sharps)):
        trans.append(naturals[abs(oldKeySig.sharps)])
    elif not (abs(oldKeySig.sharps) < abs(sampleKeySig.sharps)):
        trans.append(naturals[abs(oldKeySig.sharps - sampleKeySig.sharps)])

    trans.append(ks_braille)
    return u''.join(trans)

def timeSigToBraille(sampleTimeSig = meter.TimeSignature('4/4')):
    '''
    Takes in a :class:`~music21.meter.TimeSignature` and returns its
    representation in braille as a string in utf-8 unicode.
    

    >>> from music21.braille import translate
    >>> from music21 import meter
    >>> print translate.timeSigToBraille(sampleTimeSig = meter.TimeSignature('4/4'))
    ⠼⠙⠲
    >>> print translate.timeSigToBraille(sampleTimeSig = meter.TimeSignature('3/4'))
    ⠼⠉⠲
    >>> print translate.timeSigToBraille(sampleTimeSig = meter.TimeSignature('12/8'))
    ⠼⠁⠃⠦
    >>> print translate.timeSigToBraille(sampleTimeSig = meter.TimeSignature('c'))
    ⠨⠉
    '''
    if sampleTimeSig == None:
        raise BrailleTranslateException("No time signature provided!")
    if len(sampleTimeSig.symbol) != 0:
        try:
            return symbols[sampleTimeSig.symbol]
        except KeyError:
            pass

    timeSigTrans = []
    timeSigTrans.append(numberToBraille(sampleTimeSig.numerator))    
    timeSigTrans.append(beatUnits[sampleTimeSig.denominator])
    return u''.join(timeSigTrans)

def numberToBraille(sampleNumber = 12):
    '''
    >>> from music21.braille import translate
    >>> print translate.numberToBraille(sampleNumber = 12)
    ⠼⠁⠃
    >>> print translate.numberToBraille(sampleNumber = 7)
    ⠼⠛
    >>> print translate.numberToBraille(sampleNumber = 37)
    ⠼⠉⠛
    '''
    numberTrans = []
    numberTrans.append(symbols['number'])
    for digit in str(sampleNumber):
        numberTrans.append(numbers[int(digit)])
    
    return u''.join(numberTrans)

def showOctaveWithNote(previousNote = note.Note('C3'), currentNote = note.Note('D3')):
    '''
    Determines whether a currentNote carries an octave designation in relation to a previousNote.
    
    
    Rules:
    
    * If currentNote is found within a second or third 
      of previousNote, currentNote does not
      carry an octave designation.
    
    * If currentNote is found a sixth or 
      more away from previousNote, currentNote does carry 
      an octave designation.
    
    * If currentNote is found within a fourth or fifth 
      of previousNote, currentNote carries
      an octave designation if and only if currentNote and 
      previousNote are not found in the
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
    
def headingToBraille(sampleTempoText = tempo.TempoText("Allegretto"), sampleKeySig = key.KeySignature(5), sampleTimeSig = meter.TimeSignature('3/8'),
                     sampleMetronomeMark = tempo.MetronomeMark(number = 135, referent = note.EighthNote())):
    try:
        kts_braille = keyAndTimeSigToBraille(sampleKeySig = sampleKeySig, sampleTimeSig = sampleTimeSig)
    except BrailleTranslateException:
        kts_braille = None
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

def instrumentToBraille(sampleInstrument = instrument.Instrument()):
    return wordStringToBraille(sampleInstrument.bestName())

def tempoTextToBraille(sampleTempoText = tempo.TempoText("Lento assai, cantante e tranquillo")):
    '''
    >>> from music21.braille import translate
    >>> print translate.tempoTextToBraille()
    ⠠⠇⠑⠝⠞⠕⠀⠁⠎⠎⠁⠊⠂
    ⠉⠁⠝⠞⠁⠝⠞⠑⠀⠑⠀⠞⠗⠁⠝⠟⠥⠊⠇⠇⠕⠲
    '''
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
    >>> print translate.noteToBraille(sampleNote = C4)
    ⠐⠹
    >>> C4.quarterLength = 2.0
    >>> print translate.noteToBraille(sampleNote = C4)
    ⠐⠝
    >>> Ds4 = note.Note('D#4')
    >>> print translate.noteToBraille(sampleNote = Ds4)
    ⠩⠐⠱
    >>> print translate.noteToBraille(sampleNote = Ds4, showOctave = False)
    ⠩⠱
    >>> Ds4.pitch.setAccidentalDisplay(False)
    >>> print translate.noteToBraille(sampleNote = Ds4)
    ⠐⠱
    >>> A2 = note.Note('A2')
    >>> A2.quarterLength = 3.0
    >>> print translate.noteToBraille(sampleNote = A2)
    ⠘⠎⠄
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
    >>> print translate.restToBraille(dottedQuarter)
    ⠧⠄
    >>> whole = note.Rest(quarterLength = 4.0)
    >>> print translate.restToBraille(whole)
    ⠍
    >>> quarterPlusSixteenth = note.Rest(quarterLength = 1.25)
    >>> print translate.restToBraille(quarterPlusSixteenth)
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
    translates :class:`~music21.note.Note`, :class:`~music21.note.Rest`, and
    :class:`~music21.bar.Barline` objects.
    
    
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

    if not sampleMeasure.rightBarline == None:
        measureTrans.append(barlines[element.style])    
    return u''.join(measureTrans)
    
def partToBraille(samplePart = stream.Part()):
    '''
    Given a :class:`~music21.stream.Part`, returns the appropriate braille 
    characters as a string in utf-8 unicode.
    
    
    A thing to keep in mind: there is a 40 braille character limit per line.
    All spaces are filled in with empty six-cell braille characters. 
    '''
    brailleLines = collections.defaultdict(str)
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
            brailleLines[lineIndex] = sampleLine
            lineIndex += 1

    brailleLines[lineIndex] = symbols['number'] + numbers[allMeasures[0].number]
    previousNote = None
    previousMeasure = None
    
    previousKeySig = allMeasures[0].keySignature
    if previousKeySig is None:
        previousKeySig = key.KeySignature(0)
    
    for measure in allMeasures:
        showOctave = True
        if not previousMeasure == None:
            try:
                kts_braille = keyAndTimeSigToBraille(measure.keySignature, measure.timeSignature, previousKeySig)
                previousNote = None
                if not measure.keySignature == None:
                    previousKeySig = measure.keySignature
                if not(len(brailleLines[lineIndex]) + len(kts_braille) + 1) > 40:
                    brailleLines[lineIndex] += (symbols['space'] + kts_braille)
                else:
                    brailleLines[lineIndex] = brailleLines[lineIndex].ljust(40, symbols['space'])
                    lineIndex += 1
                    brailleLines[lineIndex] = symbols['double-space'] + kts_braille
            except BrailleTranslateException:
                pass
        if not len(measure.flat.notes) == 0:
            if not previousNote == None:
                showOctave = showOctaveWithNote(previousNote, measure.flat.notes[0])
            previousNote = measure.flat.notes[-1]
        mtb = measureToBraille(measure, showLeadingOctave = showOctave)
        if not(len(brailleLines[lineIndex]) + len(mtb) + 1) > 40:
            brailleLines[lineIndex] += (symbols['space'] + mtb)
        else:
            brailleLines[lineIndex] = brailleLines[lineIndex].ljust(40, symbols['space'])
            lineIndex += 1
            mtb = measureToBraille(measure, showLeadingOctave = True)  
            brailleLines[lineIndex] = symbols['double-space'] + mtb
        previousMeasure = measure
    
    brailleLines[lineIndex] = brailleLines[lineIndex].ljust(40, symbols['space'])
    allLines = []
    for i in range(lineIndex + 1):
        allLines.append(brailleLines[i])
    
    return u'\n'.join(allLines)

def keyAndTimeSigToBraille(sampleKeySig = key.KeySignature(5), sampleTimeSig = meter.TimeSignature('3/8'), oldKeySig = None):
    if sampleTimeSig == None and (sampleKeySig == None or (sampleKeySig.sharps == 0 and oldKeySig == None)):
            raise BrailleTranslateException("No key or time signature change!")
    
    trans = []
    if not sampleKeySig == None:
        trans.append(keySigToBraille(sampleKeySig = sampleKeySig, oldKeySig = oldKeySig))
    if not sampleTimeSig == None:
        trans.append(timeSigToBraille(sampleTimeSig))
        
    return u''.join(trans)

def brailleUnicodetoBrailleAscii(sampleBraille = u'\u2800'):
    brailleLines = sampleBraille.splitlines()
    asciiLines = []
    
    for sampleLine in brailleLines:
        allChars = []
        for char in sampleLine:
            allChars.append(ascii_chars[char])
        asciiLines.append(u''.join(allChars))
        
    return u'\n'.join(asciiLines)

def brailleAsciiToBrailleUnicode(sampleAscii = "_>^H9_F^H9_J_D9IH9_J"):
    braille_chars = {}
    for key in ascii_chars:
        braille_chars[ascii_chars[key]] = key
        
    asciiLines = sampleAscii.splitlines()
    brailleLines = []
    
    for sampleLine in asciiLines:
        allChars = []
        for char in sampleLine:
            allChars.append(braille_chars[char.upper()])
        brailleLines.append(u''.join(allChars))
    
    return u'\n'.join(brailleLines)

def brailleUnicodeToSymbols(sampleBraille = u'\u2800', filledSymbol = 'o', emptySymbol = u'\u00B7'):
    symbolTrans = {'00': '{symbol1}{symbol2}'.format(symbol1 = emptySymbol, symbol2 = emptySymbol),
                   '01': '{symbol1}{symbol2}'.format(symbol1 = emptySymbol, symbol2 = filledSymbol),
                   '10': '{symbol1}{symbol2}'.format(symbol1 = filledSymbol, symbol2 = emptySymbol),
                   '11': '{symbol1}{symbol2}'.format(symbol1 = filledSymbol, symbol2 = filledSymbol)}
    
    brailleLines = sampleBraille.splitlines()
    binaryLines = []

    for sampleLine in brailleLines:
        binaryLine1 = []
        binaryLine2 = []
        binaryLine3 = []
        for char in sampleLine:
            (dots14, dots25, dots36) = binary_dots[char]
            binaryLine1.append(symbolTrans[dots14])
            binaryLine2.append(symbolTrans[dots25])
            binaryLine3.append(symbolTrans[dots36])
        binaryLines.append(u'  '.join(binaryLine1))
        binaryLines.append(u'  '.join(binaryLine2))
        binaryLines.append(u'  '.join(binaryLine3))
        binaryLines.append(u'')
        
    return u'\n'.join(binaryLines[0:-1])

def brailleUnicodeToBinary(sampleBraille = u'\u2800'):
    brailleLines = sampleBraille.splitlines()
    binaryLines = []

    for sampleLine in brailleLines:
        binaryLine1 = []
        binaryLine2 = []
        binaryLine3 = []
        for char in sampleLine:
            (dots14, dots25, dots36) = binary_dots[char]
            binaryLine1.append(dots14)
            binaryLine2.append(dots25)
            binaryLine3.append(dots36)
        binaryLines.append(u'  '.join(binaryLine1))
        binaryLines.append(u'  '.join(binaryLine2))
        binaryLines.append(u'  '.join(binaryLine3))
        binaryLines.append(u'')
    return u'\n'.join(binaryLines)


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