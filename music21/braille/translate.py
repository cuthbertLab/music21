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
import copy
import music21
import unittest

from music21 import bar
from music21 import chord
from music21 import clef
from music21 import duration
from music21 import dynamics
from music21 import instrument
from music21 import interval
from music21 import key
from music21 import meter
from music21 import note
from music21 import pitch
from music21 import spanner
from music21 import stream
from music21 import tempo

UPPER_FIRST_IN_NOTE_FINGERING = True
SHOW_CLEF_SIGNS = False
SLUR_LONG_PHRASE_WITH_BRACKETS = False
SHOW_SHORT_SLURS_AND_TIES_TOGETHER = False
SHOW_LONG_SLURS_AND_TIES_TOGETHER = False

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

fingerMarks = {'1': u'\u2801',
               '2': u'\u2803',
               '3': u'\u2807',
               '4': u'\u2802',
               '5': u'\u2805'}

clefSigns = {'treble': u'\u281c\u280c\u2807',
             'bass': u'\u281c\u283c\u2807',
             'alto': u'\u281c\u282c\u2807',
             'tenor': u'\u281c\u282c\u2810\u2807'}

bowingSymbols = {}

beforeNoteExpr = {'staccato': u'\u2826',
                  'accent': u'\u2828\u2826',
                  'tenuto': u'\u2838\u2826',
                  'staccatissimo': u'\u2820\u2826'}

afterNoteExpr = {}

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
           'double_space': u'\u2800\u2800',
           'number': u'\u283c',
           'dot': u'\u2804',
           'tie': u'\u2808\u2809',
           'uppercase': u'\u2820',
           'metronome': u'\u2836',
           'common': u'\u2828\u2809',
           'cut': u'\u2838\u2809',
           'music_hyphen': u'\u2810',
           'music_asterisk': u'\u281c\u2822\u2814',
           'rh_keyboard': u'\u2805\u281c',
           'lh_keyboard': u'\u2807\u281c',
           'word': u'\u281c',
           'triplet': u'\u2806',
           'finger_change': u'\u2809',
           'first_set_missing_fingermark': u'\u2820',
           'second_set_missing_fingermark': u'\u2804',
           'opening_single_slur': u'\u2809',
           'opening_double_slur': u'\u2809\u2809',
           'closing_double_slur': u'\u2809',
           'opening_bracket_slur': u'\u2830\u2803',
           'closing_bracket_slur': u'\u2818\u2806'}

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

class BrailleText():
    '''
    Object that handles all the formatting associated with braille music notation.
    '''
    def __init__(self):
        self.lineNumber = 1
        self.linePos = 0
        self.allLines = collections.defaultdict(str)
        self.maxLineLength = 40
        
    def addElement(self, **elementKeywords):
        if 'heading' in elementKeywords:
            if not (self.lineNumber == 1 or self.linePos == 0):
                self.lineNumber += 1
                self.linePos = 0
            for headingLine in elementKeywords['heading'].splitlines():
                self.allLines[self.lineNumber] = headingLine
                self.lineNumber += 1
            return
        if 'measureNumber' in elementKeywords:
            if not(len(self.allLines[self.lineNumber]) == 0):
                self.lineNumber += 1
                self.linePos = 0
            self.allLines[self.lineNumber] = elementKeywords['measureNumber']
            self.linePos += len(elementKeywords['measureNumber'])
            return
        if 'keyOrTimeSig' in elementKeywords:
            keyOrTimeSig = elementKeywords['keyOrTimeSig']
            withHyphen = elementKeywords['withHyphen']
            if self.linePos + len(keyOrTimeSig) + 1 + int(withHyphen) > self.maxLineLength:
                self.allLines[self.lineNumber] += symbols['space'] * (self.maxLineLength - self.linePos)
                self.lineNumber += 1
                self.allLines[self.lineNumber] = u"".join([symbols['double_space'], keyOrTimeSig])
                self.linePos = len(keyOrTimeSig) + 2
            else:
                if not len(self.allLines[self.lineNumber]) == 0:
                    if withHyphen:
                        self.allLines[self.lineNumber] += symbols['music_hyphen']
                        self.linePos += 1
                    self.allLines[self.lineNumber] += symbols['space']
                    self.linePos += 1
                self.allLines[self.lineNumber] += keyOrTimeSig
                self.linePos += len(keyOrTimeSig)
            return
        if 'noteGrouping' in elementKeywords:
            noteGrouping = elementKeywords['noteGrouping']
            showLeadingOctave = elementKeywords['showLeadingOctave']
            withHyphen = elementKeywords['withHyphen']
            if self.linePos + len(noteGrouping) + 1 + int(withHyphen) > self.maxLineLength:
                if not(showLeadingOctave == False):
                    self.allLines[self.lineNumber] += symbols['space'] * (self.maxLineLength - self.linePos)
                    self.lineNumber += 1
                    self.allLines[self.lineNumber] = u"".join([symbols['double_space'], noteGrouping])
                    self.linePos = len(noteGrouping) + 2
                else:
                    raise BrailleTextException("Note grouping needs to be recalculated with a leading octave.")
            else:
                if not len(self.allLines[self.lineNumber]) == 0 and not self.linePos == 0:
                    if withHyphen:
                        self.allLines[self.lineNumber] += symbols['music_hyphen']
                        self.linePos += 1
                    self.allLines[self.lineNumber] += symbols['space']
                    self.linePos += 1
                self.allLines[self.lineNumber] += noteGrouping
                self.linePos += len(noteGrouping)
            return
        if 'pair' in elementKeywords:
            (measureNumber, rh_braille, lh_braille) = elementKeywords['pair']
            isFirstOfLine = False
            rh_all = []
            lh_all = []
            if len(self.allLines[self.lineNumber]) == 0:
                rh_all.append((self.highestMeasureNumberLength - len(measureNumber)) * symbols['space'])
                rh_all.append(measureNumber)
                lh_all.append(symbols['space'] * self.highestMeasureNumberLength)
                self.linePos = self.highestMeasureNumberLength
                isFirstOfLine = True
            if self.linePos + len(rh_braille) + 1 > self.maxLineLength or self.linePos + len(lh_braille) + 1 > self.maxLineLength:
                rh_all.append((self.highestMeasureNumberLength - len(measureNumber)) * symbols['space'])
                self.fillLine(self.lineNumber)
                self.fillLine(self.lineNumber + 1)
                self.lineNumber += 2
                rh_all.append(measureNumber)
                lh_all.append(symbols['space'] * self.highestMeasureNumberLength)
                self.linePos = self.highestMeasureNumberLength
                isFirstOfLine = True
            rh_all.append(symbols['space'])
            lh_all.append(symbols['space'])
            rh_length = len(rh_braille)
            lh_length = len(lh_braille)
            if isFirstOfLine:
                rh_all.append(symbols['rh_keyboard'])
                lh_all.append(symbols['lh_keyboard'])
                rh_length += 2
                lh_length += 2
                for dots in binary_dots[rh_braille[0]]:
                    if (dots == '10' or dots == '11'):
                        rh_all.append(symbols['dot'])
                        rh_length += 1
                for dots in binary_dots[lh_braille[0]]:
                    if (dots == '10' or dots == '11'):
                        lh_all.append(symbols['dot'])
                        lh_length += 1
            if rh_length > lh_length:
                rh_all.append(rh_braille)
                lh_all.append(lh_braille)
                #if not(rh_length - lh_length > 6):
                lh_all.append(symbols['space'] * (rh_length - lh_length))
                #else:
                #    lh_all.append(symbols['space'])
                #    lh_all.append(symbols['dot'] * (rh_length - lh_length - 1)) # tracker dots
                self.linePos += rh_length + 1
            else:
                lh_all.append(lh_braille)
                rh_all.append(rh_braille)
                #if not(lh_length - rh_length > 6):
                rh_all.append(symbols['space'] * (lh_length - rh_length))
                #else:
                #    rh_all.append(symbols['space'])
                #    rh_all.append(symbols['dot'] * (lh_length - rh_length - 1)) # tracker dots
                self.linePos += lh_length + 1
            self.allLines[self.lineNumber] += u"".join(rh_all)
            self.allLines[self.lineNumber + 1] += u"".join(lh_all)
            return
        raise BrailleTextException("Invalid Keyword.")
    
    def recenterHeading(self):
        '''
        Temporary method which manually recenters the heading if the melody is too short for a complete line.
        '''
        lineToCenter = self.allLines[1]
        lineToCenter = lineToCenter.strip(symbols['space'])
        nextLineLength = len(self.allLines[2])
        self.allLines[1] = lineToCenter.center(nextLineLength, symbols['space'])

    def fillLine(self, lineNumberToFill):
        self.allLines[lineNumberToFill] += u"".join(symbols['space'] * (self.maxLineLength - self.linePos))

    def __str__(self):
        return u"\n".join([j for (i, j) in sorted(self.allLines.items())])
        

class BrailleTextException(music21.Music21Exception):
    pass

#-------------------------------------------------------------------------------
# music21 objects (except streams) to braille unicode

def keySigToBraille(sampleKeySig = key.KeySignature(0), outgoingKeySig = None):
    '''
    Takes in a :class:`~music21.key.KeySignature` and returns its representation 
    in braille as a string in utf-8 unicode.
    
    >>> from music21.braille import translate
    >>> from music21 import key
    >>> print translate.keySigToBraille(sampleKeySig = key.KeySignature(4))
    ⠼⠙⠩
       
    
    If given an old key signature, then its cancellation will be applied before
    and in relation to the new key signature.
     

    >>> print translate.keySigToBraille(sampleKeySig = key.KeySignature(0), outgoingKeySig = key.KeySignature(-3))
    ⠡⠡⠡
    '''
    if sampleKeySig == None:
        raise BrailleTranslateException("No key signature provided!")
    ks_braille = keySignatures[sampleKeySig.sharps]
    if outgoingKeySig == None:
        return ks_braille

    trans = []
    if sampleKeySig.sharps == 0 or outgoingKeySig.sharps == 0 or \
        not (outgoingKeySig.sharps / abs(outgoingKeySig.sharps) == sampleKeySig.sharps / abs(sampleKeySig.sharps)):
        trans.append(naturals[abs(outgoingKeySig.sharps)])
    elif not (abs(outgoingKeySig.sharps) < abs(sampleKeySig.sharps)):
        trans.append(naturals[abs(outgoingKeySig.sharps - sampleKeySig.sharps)])

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

def keyAndTimeSigToBraille(sampleKeySig = key.KeySignature(0), sampleTimeSig = meter.TimeSignature('4/4'), outgoingKeySig = None):
    '''
    Takes in a :class:`~music21.key.KeySignature` and :class:`~music21.meter.TimeSignature` and returns its representation 
    in braille as a string in utf-8 unicode. If given an old key signature, then its cancellation will be applied before
    and in relation to the new key signature. The default is a zero sharp key signature with a 4/4 time signature.
    
    
    Raises a BrailleTranslateException if the resulting key and time signature is empty, which happens if the time signature
    is None and (a) the key signature is None or (b) the key signature has zero sharps and there is no previous key signature.
    
    >>> from music21.braille import translate
    >>> from music21 import key
    >>> from music21 import meter
    >>> print translate.keyAndTimeSigToBraille(sampleKeySig = key.KeySignature(5), sampleTimeSig = meter.TimeSignature('3/8'))
    ⠼⠑⠩⠼⠉⠦
    >>> print translate.keyAndTimeSigToBraille(sampleKeySig = key.KeySignature(0), sampleTimeSig = None, outgoingKeySig = key.KeySignature(-3))
    ⠡⠡⠡
    '''
    if sampleTimeSig == None and (sampleKeySig == None or (sampleKeySig.sharps == 0 and outgoingKeySig == None)):
            raise BrailleTranslateException("No key or time signature change!")
    
    trans = []
    if not sampleKeySig == None:
        trans.append(keySigToBraille(sampleKeySig = sampleKeySig, outgoingKeySig = outgoingKeySig))
    if not sampleTimeSig == None:
        trans.append(timeSigToBraille(sampleTimeSig))
        
    return u''.join(trans)


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
    
    
    Of course, these rules cease to apply in quite a few cases, which are not directly reflected
    in the results of this method:
    
        
    1) If a braille measure goes to a new line, the first note in the measure carries an 
    octave designation regardless of what the previous note was. 
    
    
    2) If a braille measure contains a new key or time signature, the first note carries
    an octave designation regardless of what the previous note was.
    
    
    3) If a new key or time signature occurs in the middle of a measure, or if a double bar
    line is encountered, both of which would necessitate a music hyphen, the next note after
    those cases needs an octave marking. 
    
    
    If any special case happens, previousNote can be set to None and the method will return
    True.
    
    
    >>> from music21.braille import translate
    >>> from music21 import note
    >>> translate.showOctaveWithNote(previousNote = note.Note('C4'), currentNote = note.Note('E4'))
    False
    >>> translate.showOctaveWithNote(previousNote = note.Note('C4'), currentNote = note.Note('F4'))
    False
    >>> translate.showOctaveWithNote(previousNote = note.Note('C4'), currentNote = note.Note('F3'))
    True
    >>> translate.showOctaveWithNote(previousNote = note.Note('C4'), currentNote = note.Note('A4'))
    True
    '''
    if previousNote == None:
        return True
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
    '''
    Takes in a :class:`~music21.key.KeySignature`, :class:`~music21.meter.TimeSignature`, :class:`~music21.tempo.TempoText`, and
    :class:`~music21.tempo.MetronomeMark` and returns its representation in braille as a string in utf-8 unicode. The contents
    are always centerd on a line, whose width is 40 by default.
    
    
    In most cases, the format is (tempo text)(space)(metronome mark)(space)(key/time signature), centered, although all of
    these need not be included. If all the contents do not fit on one line with at least 3 blank characters on each side, then
    the tempo text goes on the first line (and additional lines if necessary), and the metronome mark + key and time signature
    goes on the last line. 
    
    If the resulting heading is of length zero, a BrailleTranslateException is raised.
    
    >>> from music21.braille import translate
    >>> from music21 import key
    >>> from music21 import meter
    >>> from music21 import note
    >>> from music21 import tempo
    >>> print translate.headingToBraille(sampleTempoText = tempo.TempoText("Allegretto"), sampleKeySig = key.KeySignature(5), sampleTimeSig = meter.TimeSignature('3/8'),\
    sampleMetronomeMark = tempo.MetronomeMark(number = 135, referent = note.EighthNote()))
    ⠀⠀⠀⠀⠀⠀⠀⠠⠁⠇⠇⠑⠛⠗⠑⠞⠞⠕⠲⠀⠙⠶⠼⠁⠉⠑⠀⠼⠑⠩⠼⠉⠦⠀⠀⠀⠀⠀⠀⠀
    >>> print translate.headingToBraille(sampleTempoText = tempo.TempoText("Lento assai, cantante e tranquillo"), sampleKeySig = key.KeySignature(-2),\
    sampleTimeSig = meter.TimeSignature('common'), sampleMetronomeMark = None)
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⠇⠑⠝⠞⠕⠀⠁⠎⠎⠁⠊⠂⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠁⠝⠞⠁⠝⠞⠑⠀⠑⠀⠞⠗⠁⠝⠟⠥⠊⠇⠇⠕⠲⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠣⠣⠨⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    '''
    try:
        kts_braille = keyAndTimeSigToBraille(sampleKeySig = sampleKeySig, sampleTimeSig = sampleTimeSig)
    except BrailleTranslateException:
        kts_braille = None
    try:
        mm_braille = metronomeMarkToBraille(sampleMetronomeMark = sampleMetronomeMark)
    except BrailleTranslateException:
        mm_braille = None
        
    if not kts_braille == None:
        if not mm_braille == None:
            mm_kts_braille = mm_braille + symbols['space'] + kts_braille
        else:
            mm_kts_braille = kts_braille
    else:
        mm_kts_braille = mm_braille
    
    try:
        tt_braille = tempoTextToBraille(sampleTempoText = sampleTempoText)
    except BrailleTranslateException:
        tt_braille = None
  
    tt_mm_kts_braille = None
    if not tt_braille == None:
        if not mm_kts_braille == None:
            allLines = tt_braille.splitlines()
            if len(allLines) == 1 and len(allLines[0]) + len(mm_kts_braille) + 1 <= 34:
                tt_mm_kts_braille = (allLines[0] + symbols['space'] + mm_kts_braille).center(40, symbols['space'])
            elif len(allLines) == 2 and len(allLines[0]) + len(allLines[1]) + len(mm_kts_braille) + 2 <= 34:
                tt_mm_kts_braille = symbols['space'].join([allLines[0], allLines[1], mm_kts_braille]).center(40, symbols['space'])
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
        
    if tt_mm_kts_braille == None:
        raise BrailleTranslateException("No heading can be made.")
    return tt_mm_kts_braille

def tempoTextToBraille(sampleTempoText = tempo.TempoText("Lento assai, cantante e tranquillo")):
    '''
    Takes in a :class:`~music21.tempo.TempoText` and returns its representation in braille 
    as a string in utf-8 unicode. The tempo text is returned uncentered, and is split around
    the comma, each split returned on a separate line. The literary period required at the end
    of every tempo text expression in braille is also included.
    
    
    >>> from music21.braille import translate
    >>> print translate.tempoTextToBraille(sampleTempoText = tempo.TempoText("Lento assai, cantante e tranquillo"))
    ⠠⠇⠑⠝⠞⠕⠀⠁⠎⠎⠁⠊⠂
    ⠉⠁⠝⠞⠁⠝⠞⠑⠀⠑⠀⠞⠗⠁⠝⠟⠥⠊⠇⠇⠕⠲
    >>> print translate.tempoTextToBraille(sampleTempoText = tempo.TempoText("Andante molto grazioso"))
    ⠠⠁⠝⠙⠁⠝⠞⠑⠀⠍⠕⠇⠞⠕⠀⠛⠗⠁⠵⠊⠕⠎⠕⠲
    '''
    if sampleTempoText == None:
        raise BrailleTranslateException("No tempo text provided!")
        
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

def instrumentToBraille(sampleInstrument = instrument.Instrument()):
    '''
    Takes in a :class:`~music21.instrument.Instrument` and returns its "best name"
    as a braille string in utf-8 unicode.
    
    
    >>> from music21.braille import translate
    >>> from music21 import instrument
    >>> print translate.instrumentToBraille(sampleInstrument = instrument.Bassoon())
    ⠠⠃⠁⠎⠎⠕⠕⠝
    >>> print translate.instrumentToBraille(sampleInstrument = instrument.BassClarinet())
    ⠠⠃⠁⠎⠎⠀⠉⠇⠁⠗⠊⠝⠑⠞
    '''
    allWords = sampleInstrument.bestName().split()
    trans = []
    for word in allWords:
        trans.append(wordToBraille(sampleWord = word))
        trans.append(symbols['space'])
    return u''.join(trans[0:-1])

def metronomeMarkToBraille(sampleMetronomeMark = tempo.MetronomeMark(number = 80, referent = note.HalfNote())):
    '''
    Takes in a :class:`~music21.tempo.MetronomeMark` and returns it as a braille string in utf-8 unicode.
    The format is (note C with duration of metronome's referent)(metronome symbol)(number/bpm).
    
    >>> from music21.braille import translate
    >>> print translate.metronomeMarkToBraille(sampleMetronomeMark = tempo.MetronomeMark(number = 80, referent = note.HalfNote())) 
    ⠝⠶⠼⠓⠚
    >>> print translate.metronomeMarkToBraille(sampleMetronomeMark = tempo.MetronomeMark(number = 135, referent = note.Note(quarterLength = 0.5)))
    ⠙⠶⠼⠁⠉⠑
    '''
    if sampleMetronomeMark == None:
        raise BrailleTranslateException("No metronome mark provided!")
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
    
    # articulations
    # -------------
    if not len(sampleNote.articulations) == 0:    
        for a in sampleNote.articulations:
            try:
                noteTrans.append(beforeNoteExpr[a._mxName])
            except KeyError:
                pass
        

    beginLongSlur = False
    endLongSlur = False
    shortSlur = False
    
    try:
        beginLongSlur = sampleNote.beginLongSlur
    except AttributeError:
        pass
    try:
        endLongSlur = sampleNote.endLongSlur
    except AttributeError:
        pass
    try:
        shortSlur = sampleNote.shortSlur
    except AttributeError:
        pass

    '''
    if sampleNote.hasSpannerSite():
        for sp in sampleNote.getSpannerSites():
            if isinstance(sp, spanner.Slur):
                try:
                    delta = abs(sp[1].index - sp[0].index) + 1
                    if delta > 4:
                        if sp.isFirst(sampleNote):
                            beginLongSlur = True
                        elif sp.isLast(sampleNote) and SLUR_LONG_PHRASE_WITH_BRACKETS:
                            endLongSlur = True
                    else:
                        if sp.isFirst(sampleNote):
                            shortSlur = True
                except AttributeError:
                    pass
    else:
        try:
            shortSlur = sampleNote.isPartOfShortSlur
        except AttributeError:
            pass
        try:
            endLongSlur = sampleNote.endLongSlur
        except AttributeError:
            pass
    '''
    
    # opening double slur (before second note, after first note)
    # opening bracket slur
    # closing bracket slur (if also beginning of next long slur)
    # --------------------
    if beginLongSlur:
        if SLUR_LONG_PHRASE_WITH_BRACKETS:
            noteTrans.append(symbols['opening_bracket_slur'])
        else:
            noteTrans.append(symbols['opening_double_slur'])
    if endLongSlur and beginLongSlur and SLUR_LONG_PHRASE_WITH_BRACKETS:
        noteTrans.append(symbols['closing_bracket_slur'])
        
    # accidental
    # ----------
    if not(sampleNote.accidental == None):
        if not(sampleNote.accidental.displayStatus == False):
            try:
                noteTrans.append(accidentals[sampleNote.accidental.name])
            except KeyError:
                raise BrailleTranslateException("Accidental type cannot be translated to braille.")  
    
    # octave mark
    # -----------
    if showOctave:
        noteTrans.append(octaves[sampleNote.octave])

    notesInStep = pitchNameToNotes[sampleNote.step]  
    try:
        # note name with duration
        # -----------------------
        nameWithDuration = notesInStep[sampleNote.duration.type]
        noteTrans.append(nameWithDuration)
        # dot(s)
        # ------
        for dot in range(sampleNote.duration.dots):
            noteTrans.append(symbols['dot'])
        # finger mark
        # -----------
        try:
            noteTrans.append(noteFingeringToBraille(sampleNote.fingering, upperFirstInFingering = UPPER_FIRST_IN_NOTE_FINGERING))
        except AttributeError:
            pass
        # single slur
        # closing double slur (after second to last note, before last note)
        # opening double slur
        # closing bracket slur (unless note also has beginning long slur)
        # ----------------------------------
        if shortSlur:
            noteTrans.append(symbols['opening_single_slur'])
        if not(endLongSlur and beginLongSlur and SLUR_LONG_PHRASE_WITH_BRACKETS):
            if not SLUR_LONG_PHRASE_WITH_BRACKETS:
                if endLongSlur:
                    noteTrans.append(symbols['closing_double_slur'])
            elif endLongSlur and SLUR_LONG_PHRASE_WITH_BRACKETS:
                noteTrans.append(symbols['closing_bracket_slur'])
        # tie
        # ---
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

def noteFingeringToBraille(sampleNoteFingering = '1', upperFirstInFingering = True):
    if len(sampleNoteFingering) == 1:
        return fingerMarks[sampleNoteFingering]
    trans = []
    change = sampleNoteFingering.split('-')
    if len(change) == 2:
        trans.append(fingerMarks[change[0]])
        trans.append(symbols['finger_change'])
        trans.append(fingerMarks[change[1]])
    
    choice = sampleNoteFingering.split('|')
    if len(choice) == 2:
        if upperFirstInFingering:
            trans.append(fingerMarks[choice[0]])
            trans.append(fingerMarks[choice[1]])
        else: # lower fingering first
            trans.append(fingerMarks[choice[1]])
            trans.append(fingerMarks[choice[0]])
        
    pair = sampleNoteFingering.split(',')
    if len(pair) == 2:
        try:
            upper = fingerMarks[pair[0]]
        except KeyError:
            upper = symbols['first_set_missing_fingermark']
        try:
            lower = fingerMarks[pair[1]]
        except KeyError:
            lower = symbols['second_set_missing_fingermark']
            
        if upperFirstInFingering:
            trans.append(upper)
            trans.append(lower)
        else: # lower fingering first
            trans.append(lower)
            trans.append(upper)
            
    if len(trans) == 0:
        raise BrailleTranslateException("Cannot translate note fingering: " + sampleNoteFingering)

    return u"".join(trans)

def noteGroupingsToBraille(sampleMeasure = stream.Measure(), showLeadingOctave = True):
    '''
    Notes, rests, barlines, and dynamics in a measure stream to braille.
    Returns a list of note groupings for a stream.
    Right now, those are divisions based on locations of double barlines.
    '''
    allNoteGroupings = []
    noteGroupingTrans = []
    previousNote = None
    previousElement = None
    for element in sampleMeasure:
        if SHOW_CLEF_SIGNS and isinstance(element, clef.Clef):
            if isinstance(element, clef.TrebleClef):
                noteGroupingTrans.append(clefSigns['treble'])
                previousNote = None
                showLeadingOctave = True
            elif isinstance(element, clef.BassClef):
                noteGroupingTrans.append(clefSigns['bass'])
                previousNote = None
                showLeadingOctave = True
            elif isinstance(element, clef.AltoClef):
                noteGroupingTrans.append(clefSigns['alto'])
                previousNote = None
                showLeadingOctave = True
            elif isinstance(element, clef.TenorClef):
                noteGroupingTrans.append(clefSigns['tenor'])
                previousNote = None
                showLeadingOctave = True
        elif isinstance(element, stream.Measure):
            if previousNote == None:
                doShowOctave = showLeadingOctave
            else:
                doShowOctave = showOctaveWithNote(previousNote, element.notes[0])
            isPrecededByRest = False
            if not(previousElement == None) and isinstance(previousElement, note.Rest) and previousElement.duration.type == element.notes[0].duration.type:
                isPrecededByRest = True
            noteGroupingTrans.append(beamGroupToBraille(sampleBeamGroup = element, showLeadingOctave = doShowOctave, isPrecededByRest = isPrecededByRest))
            previousNote = element.notes[-1]
        elif isinstance(element, note.Note):
            if previousNote == None:
                doShowOctave = showLeadingOctave
            else:
                doShowOctave = showOctaveWithNote(previousNote, element)
            noteGroupingTrans.append(noteToBraille(sampleNote = element, showOctave = doShowOctave))
            previousNote = element                
        elif isinstance(element, note.Rest):
            if element.duration == sampleMeasure.duration:
                noteGroupingTrans.append(restToBraille(sampleRest = note.Rest(quarterLength = 4.0)))
            else:
                noteGroupingTrans.append(restToBraille(sampleRest = element))
        elif isinstance(element, dynamics.Dynamic):
            noteGroupingTrans.append(symbols['word'])
            noteGroupingTrans.append(wordToBraille(element.value))
            previousNote = None
            showLeadingOctave = True
        elif isinstance(element, bar.Barline):
            noteGroupingTrans.append(barlines[element.style])
            allNoteGroupings.append(u"".join(noteGroupingTrans))
            noteGroupingTrans = []
            previousNote = None
            showLeadingOctave = True
        else:
            continue
        if SHOW_CLEF_SIGNS and isinstance(previousElement, clef.Clef):            
            for dots in binary_dots[noteGroupingTrans[-1][0]]:
                if (dots == '10' or dots == '11'):
                    noteGroupingTrans.insert(-1, symbols['dot'])
        previousElement = element
    if not(len(noteGroupingTrans) == 0):
        allNoteGroupings.append(u"".join(noteGroupingTrans))
    return allNoteGroupings

def extractBrailleHeading(sampleMeasure = stream.Measure()):
    '''
    Method to extract a braille heading from a measure. A heading
    consists of a TempoText, a MetronomeMark, a Key Signature and
    a Time Signature, although not all need be included.
    '''
    tt = None
    try:
        tt = sampleMeasure.getElementsByClass('TempoText')[0]
    except IndexError:
        pass
    
    mm = None
    try:
        mm = sampleMeasure.getElementsByClass('MetronomeMark')[0]
    except IndexError:
        pass

    return headingToBraille(sampleKeySig = sampleMeasure.keySignature, sampleTimeSig = sampleMeasure.timeSignature, 
                            sampleTempoText = tt, sampleMetronomeMark = mm)

#-------------------------------------------------------------------------------
# music21 streams to BrailleText objects.

def measureToBraille(sampleMeasure = stream.Measure(), **measureKeywords):
    '''    
    Method for translating a :class:`~music21.stream.Measure` into braille.
    
    
    All possible measureKeywords:
    
    
    * showLeadingOctave: True by default. If set to True, the first note of the measure
    (if there is one) displays an octave mark before it. If set to false, the first note
    does not display an octave mark, unless preceded by a key or time signature within
    the measure itself.
    
    
    * isFirstOfSegment: False by default. If set to True, a heading (see :meth:`~music21.braille.translate.extractBrailleHeading`)
    and a measure number precede the rest of the contents of the measure, unless includeMeasureNumberAfterHeading is set to False.
    
    
    * measureNumberWithHeading: True by default. If set to True, a measure number follows a heading whenever isFirstOfSegment is
    True.
    
    
    * outgoingKeySig: None by default. If provided an old key signature, and the measure contains
    a new key signature, the outgoing key signature is cancelled before the new one is added.
    
    
    * precedingBrailleText: None by default. If provided a BrailleText object, the
    measure contents are added to it, otherwise a new BrailleText object is created.
    
    
    >>> from music21.braille import translate
    '''
    try:
        showLeadingOctave = measureKeywords['showLeadingOctave']
    except KeyError:
        showLeadingOctave = True
        
    try:
        isFirstOfSegment = measureKeywords['isFirstOfSegment']
    except KeyError:
        isFirstOfSegment = False

    try:
        measureNumberWithHeading = measureKeywords['measureNumberWithHeading']
    except KeyError:
        measureNumberWithHeading = True

    try:
        outgoingKeySig = measureKeywords['outgoingKeySig']
    except KeyError:
        outgoingKeySig = None
        
    try:
        bt = measureKeywords['precedingBrailleText']
    except KeyError:
        bt = BrailleText()
    
    sampleMeasure = makeBeamGroups(sampleMeasure = sampleMeasure)
    keyOrTimeSig = sampleMeasure.getElementsByClass([key.KeySignature, meter.TimeSignature])
    offsets = []
    kts_braille = {}
    if len(keyOrTimeSig) == 0:
        startOffset = sampleMeasure.lowestOffset
        endTime = sampleMeasure.highestTime
        offsets.append((startOffset, endTime))
        if isFirstOfSegment:
            try:
                kts_braille[startOffset] = u''.join([extractBrailleHeading(sampleMeasure)])
            except BrailleTranslateException:
                pass
    else:
        startOffset = sampleMeasure.lowestOffset
        endTime = None
        for groupAtOffset in keyOrTimeSig.groupElementsByOffset():
            ks = None
            ts = None
            for item in groupAtOffset:
                endTime = item.offset
                if isinstance(item, key.KeySignature):
                    ks = item
                elif isinstance(item, meter.TimeSignature):
                    ts = item
            if not startOffset == endTime:
                offsets.append((startOffset, endTime))
                startOffset = endTime
            if not isFirstOfSegment or not startOffset == 0.0:
                try:
                    kts_braille[startOffset] = keyAndTimeSigToBraille(sampleKeySig = ks, sampleTimeSig = ts, outgoingKeySig = outgoingKeySig)
                except BrailleTranslateException:
                    if not(ks == None) and ks.sharps == 0 and outgoingKeySig == None:
                        kts_braille[startOffset] =  None
            else:
                kts_braille[startOffset] = u''.join([extractBrailleHeading(sampleMeasure)])
        endTime = sampleMeasure.highestTime
        offsets.append((startOffset, endTime))
    
    isFirstGrouping = True
    measureTrans = []
    for (startOffset, endTime) in offsets:
        groupingTrans = []
        newKeyOrTimeSig = False
        try:
            if isFirstOfSegment and startOffset == 0.0:
                bt.addElement(heading = kts_braille[startOffset])
            else:
                withHyphen = False
                if not isFirstGrouping:
                    withHyphen = True
                try:
                    bt.addElement(keyOrTimeSig = kts_braille[startOffset], withHyphen = withHyphen)
                except TypeError: # kts_braille[startOffset] == None
                    # new key of no sharps or flats, no cancelling of outgoing key sig after double bar, 
                    # but octave mark still needed. (very rare case)
                    pass
            newKeyOrTimeSig = True
        except KeyError:
            pass
        
        if isFirstOfSegment and measureNumberWithHeading:
            bt.addElement(measureNumber = numberToBraille(sampleMeasure.number))
        
        offsetGrouping = \
            sampleMeasure.getElementsByOffset(offsetStart = startOffset, offsetEnd = endTime, mustFinishInSpan = True)
        withHyphen = False
        if newKeyOrTimeSig and not(isFirstOfSegment):
            withHyphen = True
        if not(showLeadingOctave == True):
            if not(isFirstGrouping) or (isFirstGrouping and isFirstOfSegment) or (isFirstGrouping and newKeyOrTimeSig):
                showLeadingOctave = True
        noteGrouping = offsetGrouping.getElementsNotOfClass([key.KeySignature, meter.TimeSignature])
        if len(noteGrouping) == 0:
            continue
        if isinstance(noteGrouping[0], bar.Barline) and not isFirstOfSegment:
            noteGrouping.remove(noteGrouping[0])
        allGroupings = noteGroupingsToBraille(noteGrouping, showLeadingOctave = showLeadingOctave)
        try:
            bt.addElement(noteGrouping = allGroupings[0], showLeadingOctave = showLeadingOctave, withHyphen = False) 
        except BrailleTextException:
            allGroupings = noteGroupingsToBraille(noteGrouping, showLeadingOctave = True)
            bt.addElement(noteGrouping = allGroupings[0], showLeadingOctave = True, withHyphen = False) 
        if len(allGroupings) > 1:
            for ng in allGroupings[1:]:
                bt.addElement(noteGrouping = ng, showLeadingOctave = True, withHyphen = True)     
        isFirstGrouping = False
        
    return bt

def partToBraille(samplePart = stream.Part(), **keywords): 
    '''
    Given a :class:`~music21.stream.Part`, returns the appropriate braille 
    characters as a string in utf-8 unicode.
    
    
    * segmentStartMeasureNumbers: empty list by default
    
    
    * cancelOutgoingKeySig: True by default
    
    
    * measureNumberWithHeading: True by default.
        
    
    * upperFirstInNoteFingering: True by default. When provided a choice fingering for 
    a note, if set to True, provides upper fingering followed by lower fingering.
    
    
    A thing to keep in mind: there is a 40 braille character limit per line.
    All spaces are filled in with empty six-cell braille characters. 
    '''
    segmentStartMeasureNumbers = []
    cancelOutgoingKeySig = True
    measureNumberWithHeading = True
    recenterHeading = False

    if 'segmentStartMeasureNumbers' in keywords:
        segmentStartMeasureNumbers = keywords['segmentStartMeasureNumbers']
    if 'cancelOutgoingKeySig' in keywords:
        cancelOutgoingKeySig = keywords['cancelOutgoingKeySig']
    if 'measureNumberWithHeading' in keywords:
        measureNumberWithHeading = keywords['measureNumberWithHeading']
    if 'recenterHeading' in keywords:
        recenterHeading = keywords['recenterHeading']

    global UPPER_FIRST_IN_NOTE_FINGERING
    global SHOW_CLEF_SIGNS
    global SLUR_LONG_PHRASE_WITH_BRACKETS
    global SHOW_SHORT_SLURS_AND_TIES_TOGETHER
    global SHOW_LONG_SLURS_AND_TIES_TOGETHER
    
    if 'upperFirstInNoteFingering' in keywords:
        UPPER_FIRST_IN_NOTE_FINGERING = keywords['upperFirstInNoteFingering']
    if 'showClefSigns' in keywords:
        SHOW_CLEF_SIGNS = keywords['showClefSigns']
    if 'slurLongPhraseWithBrackets' in keywords:
        SLUR_LONG_PHRASE_WITH_BRACKETS = keywords['slurLongPhraseWithBrackets']
    if 'showShortSlursAndTiesTogether' in keywords:
        SHOW_SHORT_SLURS_AND_TIES_TOGETHER = keywords['showShortSlursAndTiesTogether']
    if 'showLongSlursAndTiesTogether' in keywords:
        SHOW_LONG_SLURS_AND_TIES_TOGETHER = keywords['showLongSlursAndTiesTogether']
    else:
        if SLUR_LONG_PHRASE_WITH_BRACKETS:
            SHOW_LONG_SLURS_AND_TIES_TOGETHER = True

    prepareSlurredNotes(samplePart = samplePart)
    bt = BrailleText()
    partTrans = []
    allMeasures = samplePart.getElementsByClass('Measure')
    measureToBraille(allMeasures[0], isFirstOfSegment = True, precedingBrailleText = bt, measureNumberWithHeading = measureNumberWithHeading)
    precedingNote = None
    if cancelOutgoingKeySig:
        outgoingKeySig = allMeasures[0].keySignature
    else:
        outgoingKeySig = None
    if not(len(allMeasures[0].notes) == 0):
        precedingNote = allMeasures[0].notes[-1]
    
    for sampleMeasure in allMeasures[1:]:
        oldLineNumber = bt.lineNumber
        if not(len(sampleMeasure.notes) == 0):
            firstNote = sampleMeasure.notes[0]
            showLeadingOctave = showOctaveWithNote(previousNote = precedingNote, currentNote = firstNote)
        else:
            showLeadingOctave = None
        if sampleMeasure.number in segmentStartMeasureNumbers:
            measureToBraille(sampleMeasure, showLeadingOctave = showLeadingOctave, outgoingKeySig = outgoingKeySig, precedingBrailleText = bt, isFirstOfSegment = True)
        else:
            measureToBraille(sampleMeasure, showLeadingOctave = showLeadingOctave, outgoingKeySig = outgoingKeySig, precedingBrailleText = bt)
        newLineNumber = bt.lineNumber
        if not(newLineNumber == oldLineNumber):
            precedingNote = None 
        if not(len(sampleMeasure.notes) == 0):
            precedingNote = sampleMeasure.notes[-1]
        if cancelOutgoingKeySig and not(sampleMeasure.keySignature == None):
            if not(sampleMeasure.keySignature == outgoingKeySig):
                outgoingKeySig = sampleMeasure.keySignature

    if recenterHeading:
        bt.recenterHeading()
    
    UPPER_FIRST_IN_NOTE_FINGERING = True
    SHOW_CLEF_SIGNS = False
    SLUR_LONG_PHRASE_WITH_BRACKETS = False
    SHOW_SHORT_SLURS_AND_TIES_TOGETHER = False
    SHOW_LONG_SLURS_AND_TIES_TOGETHER = False
    return bt

def prepareSlurredNotes(samplePart = stream.Part()):
    if not len(samplePart.spannerBundle) > 0:
        return
    allNotes = samplePart.flat.notes
    for slur in samplePart.spannerBundle.getByClass(spanner.Slur):
        slur[0].index = allNotes.index(slur[0])
        slur[1].index = allNotes.index(slur[1])
        beginIndex = slur[0].index
        endIndex = slur[1].index
        delta = abs(endIndex - beginIndex) + 1
        if not SHOW_SHORT_SLURS_AND_TIES_TOGETHER and delta <= 4:
            if allNotes[beginIndex].tie != None and allNotes[beginIndex].tie.type == 'start':
                beginIndex += 1
            if allNotes[endIndex].tie != None and allNotes[endIndex].tie.type == 'stop':
                endIndex -= 1
        if not SHOW_LONG_SLURS_AND_TIES_TOGETHER and delta > 4:
            if allNotes[beginIndex].tie != None and allNotes[beginIndex].tie.type == 'start':
                beginIndex += 1
            if allNotes[endIndex].tie != None and allNotes[endIndex].tie.type == 'stop':
                endIndex -= 1
        if not(delta > 4):
            for noteIndex in range(beginIndex, endIndex):
                allNotes[noteIndex].shortSlur = True
        else:
            if SLUR_LONG_PHRASE_WITH_BRACKETS:
                allNotes[beginIndex].beginLongSlur = True
                allNotes[endIndex].endLongSlur = True
            else:
                allNotes[beginIndex + 1].beginLongSlur = True
                allNotes[endIndex - 1].endLongSlur = True

def keyboardPartsToBraille(keyboardStyle = stream.Part(), **keywords):
    '''
    Translates a stream Part consisting of two stream Parts, a right hand and left hand,
    into braille music bar over bar format.
    '''
    recenterHeading = False
    if 'recenterHeading' in keywords:
        recenterHeading = keywords['recenterHeading']

    rightHand = keyboardStyle[0]
    leftHand = keyboardStyle[1]

    bt = BrailleText()
    bt.addElement(heading = extractBrailleHeading(rightHand[0]))
    bt.highestMeasureNumberLength = len(str(rightHand.getElementsByClass(stream.Measure)[-1].number))
    
    for rhMeasure in rightHand:
        lhMeasure = leftHand.measure(rhMeasure.number)
        rhMeasure = makeBeamGroups(rhMeasure)
        lhMeasure = makeBeamGroups(lhMeasure)
        rh_braille = noteGroupingsToBraille(rhMeasure)[0]
        lh_braille = noteGroupingsToBraille(lhMeasure)[0]
        bt.addElement(pair = (numberToBraille(sampleNumber = rhMeasure.number)[1:], rh_braille, lh_braille))

    if recenterHeading:
        bt.recenterHeading()
    return bt


# A (very) primitive stab at beamed notes
# ----------------------------------------
def makeBeamGroups(sampleMeasure = stream.Measure()):
    splitA = sampleMeasure.splitByClass(None, lambda element: isinstance(element, note.GeneralNote) and not isinstance(element, note.Rest))
    allNotes = splitA[0]
    nonNotes = splitA[1]
    splitB = allNotes.splitByClass(None, lambda sampleNote: not(sampleNote.beams) == None and len(sampleNote.beams) > 0)
    allNotesWithBeams = splitB[0]
    allRemainingNotes = splitB[1]
    splitC = allNotesWithBeams.splitByClass(None, lambda n: n.beams.getByNumber(1).type is 'start' or n.beams.getByNumber(1).type is 'stop')
    startOrStopNotes = splitC[0]
    otherBeamedNotes = splitC[1]
    for noteStartIndex in range(len(startOrStopNotes) / 2):
        startOffset = startOrStopNotes[2 * noteStartIndex].offset
        stopOffset = startOrStopNotes[2 * noteStartIndex + 1].offset
        beamGroup = allNotes.getElementsByOffset(startOffset, stopOffset)
        beamGroup.duration = duration.Duration(beamGroup.highestTime - startOffset)
        beamGroup.label = 'beam_group'
        nonNotes.insert(startOffset, beamGroup)
    for element in otherBeamedNotes:
        if element.beams.getByNumber(1).type == 'partial':
            nonNotes.insert(element.offset, element)
    for nonBeamedNote in allRemainingNotes:
        nonNotes.insert(nonBeamedNote.offset, nonBeamedNote)
    nonNotes.mergeAttributes(sampleMeasure)   
    return nonNotes

def beamGroupToBraille(sampleBeamGroup = stream.Measure(), showLeadingOctave = True, isPrecededByRest = False):
    if len(sampleBeamGroup) < 3:
        return noteGroupingsToBraille(sampleBeamGroup, showLeadingOctave = showLeadingOctave)[0]
    
    previousNote = sampleBeamGroup[0]
    for currentNote in sampleBeamGroup[1:]:
        if not currentNote.duration.type == previousNote.duration.type:
            return noteGroupingsToBraille(sampleBeamGroup, showLeadingOctave = showLeadingOctave)[0]
    
    trans = []
    if not isPrecededByRest:
        previousNote = sampleBeamGroup[0]
    else:
        previousNote = note.Note(sampleBeamGroup[0].pitch, quarterLength = 0.5)
    allTuplets = previousNote.duration.tuplets
    if len(allTuplets) > 0:
        if allTuplets[0].fullName == 'Triplet':
            trans.append(symbols['triplet'])
    trans.append(noteToBraille(previousNote, showOctave = showLeadingOctave))
    for currentNote in sampleBeamGroup[1:]:
        if isinstance(currentNote, note.Note):
            newNote = copy.deepcopy(currentNote)
            newNote.quarterLength = 0.5
            doShowOctave = showOctaveWithNote(previousNote, currentNote)
            trans.append(noteToBraille(newNote, showOctave = doShowOctave))
            previousNote = currentNote
        elif isinstance(currentNote, note.Rest):
            noteGroupingTrans.append(restToBraille(sampleRest = element))
    return u"".join(trans)

#-------------------------------------------------------------------------------
# Translation between braille unicode and ASCII/other symbols.

def brailleUnicodeToBrailleAscii(sampleBraille = u'\u2800'):
    '''
    Translates a braille utf-8 unicode string into braille ASCII,
    which is the format compatible with most braille embossers.
    
    
    .. note:: The method works by corresponding braille symbols to ASCII symbols.
    The table which corresponds said values can be found 
    `here <http://en.wikipedia.org/wiki/Braille_ASCII#Braille_ASCII_values>`_.
    Because of the way in which the braille symbols translate, the resulting
    ASCII string will look like gibberish. Also, the eighth-note notes in braille 
    music are one-off their corresponding letters in both ASCII and written braille.
    The written D is really a C eighth-note, the written E is really a 
    D eighth note, etc. 
    
    
    >>> from music21.braille import translate
    >>> from music21 import note
    >>> translate.brailleUnicodeToBrailleAscii(sampleBraille = u'\u2800')
    ' '
    >>> Cs8 = note.Note('C#4', quarterLength = 0.5)
    >>> Cs8_braille = translate.noteToBraille(sampleNote = Cs8)
    >>> translate.brailleUnicodeToBrailleAscii(sampleBraille = Cs8_braille)
    '%"D'
    >>> Eb8 = note.Note('E-4', quarterLength = 0.5)
    >>> Eb8_braille = translate.noteToBraille(sampleNote = Eb8)
    >>> translate.brailleUnicodeToBrailleAscii(sampleBraille = Eb8_braille)
    '<"F'
    '''
    brailleLines = sampleBraille.splitlines()
    asciiLines = []
    
    for sampleLine in brailleLines:
        allChars = []
        for char in sampleLine:
            allChars.append(ascii_chars[char])
        asciiLines.append(''.join(allChars))
        
    return '\n'.join(asciiLines)

def brailleAsciiToBrailleUnicode(sampleAscii = ",ANDANTE ,MAESTOSO4"):
    '''
    Translates a braille ASCII string to braille utf-8 unicode, which
    can then be displayed on-screen in braille on compatible systems.
    
    
    .. note:: The method works by corresponding ASCII symbols to braille
    symbols in a very direct fashion. It is not a translator from plain
    text to braille, because ASCII symbols may not correspond to their
    equivalents in braille. For example, a literal period is a 4 in 
    braille ASCII. Also, all letters are translated into their lowercase
    equivalents, and any capital letters are indicated by preceding them
    with a comma.
    
    
    >>> from music21.braille import translate
    >>> from music21 import tempo
    >>> t1 = translate.brailleAsciiToBrailleUnicode(sampleAscii = ",ANDANTE ,MAESTOSO4")
    >>> t2 = translate.tempoTextToBraille(sampleTempoText = tempo.TempoText("Andante Maestoso"))
    >>> t1 == t2
    True
    '''
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
    '''
    Translates a braille unicode string into symbols (ASCII or utf-8).
    '''
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

#-------------------------------------------------------------------------------
# Helper Methods

def wordToBraille(sampleWord = 'Andante'):
    '''
    >>> from music21.braille import translate
    >>> print translate.wordToBraille(sampleWord = 'Andante')
    ⠠⠁⠝⠙⠁⠝⠞⠑
    >>> print translate.wordToBraille(sampleWord = 'Fagott')
    ⠠⠋⠁⠛⠕⠞⠞
    '''
    wordTrans = []
    for letter in sampleWord:
        if letter.isupper():
            wordTrans.append(symbols['uppercase'] + alphabet[letter.lower()])
        else:
            wordTrans.append(alphabet[letter])
        
    return u''.join(wordTrans)

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

def splitStreamByClass(sampleMeasure, classFilterList, groupWithPrevious = False):
    '''
    keywords groupWithPrevious, includeF
    '''
    elementsOfClasses = sampleMeasure.getElementsByClass(classFilterList)
    if len(elementsOfClasses) == 0:
        return [sampleMeasure]
    
    elementsByOffset = elementsOfClasses.groupElementsByOffset(returnDict = True)
    if len(elementsByOffset.keys()) == 1 and 0.0 in elementsByOffset:
        return [sampleMeasure]

    allStreams = []
    startIndex = 0
    endIndex = 0
    for offset in elementsByOffset:
        if not(offset == 0.0):
            if not groupWithPrevious:
                endIndex = sampleMeasure.index(elementsByOffset[offset][0])
            else:
                endIndex = sampleMeasure.index(elementsByOffset[offset][-1]) + 1
            allStreams.append(sampleMeasure[startIndex:endIndex])
            startIndex = endIndex
    endIndex = len(sampleMeasure)
    allStreams.append(sampleMeasure[startIndex:endIndex])
    return allStreams


class BrailleTranslateException(music21.Music21Exception):
    pass
    
#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass


if __name__ == "__main__":
    import sys
    reload(sys)
    sys.setdefaultencoding("UTF-8")
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof