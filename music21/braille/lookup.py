# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------------
# Name:         lookup.py
# Purpose:      music21 class which contains lookup tables between print and braille
# Authors:      Jose Cabal-Ugaz
#               Bo-cheng Jhan
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2011, 2016 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-----------------------------------------------------------------------------------
'''
This file contains some basic lookups for symbols (used where there is not much more
logical code to deduce).


Music21 standards generally follow Mary Turner De Garmo, 
Introduction to Braille Music Transcription (2005) (called "degarmo" or "IMBT2005" below).

Signs from other books will be accepted if
and only if there is no conflict between them and BRL signs listed in IBMT2005.

A place where other signs are found generally is 
New International Manual of Braille Music Notation (by Bettye Krolick), which we will cite as
"Krolick" or "krolick".
'''

import itertools

_DOC_IGNORE_MODULE_OR_PACKAGE = True

try:
    unichr # @UndefinedVariable
except NameError:
    unichr = chr

def makeBrailleDictionary():
    u'''
    return a dictionary mapping six-dot braille characters to lists of dot orders.
    
    >>> B = braille.lookup.makeBrailleDictionary()
    >>> print(B[124])
    ⠋
    >>> print(B[126])
    ⠣
    
    A special character (unicode 0x2800)
    
    >>> print(B[0])
    ⠀
    '''
    braille_dict = {}
    _BRAILLE_START = 0x2800
    i = 0
    
    for bTuple in itertools.product((False, True), repeat=6):
        bList = []
        for pos, trueOrFalse in enumerate(bTuple):
            posBackOffset = 6 - pos
            bList.append(str(posBackOffset) if trueOrFalse is True else "")
        bText = ''.join(reversed(bList))
        bVal = int(bText) if bText != "" else 0
        currentStrValue = unichr(_BRAILLE_START + i)
        braille_dict[bVal] = currentStrValue
        #print(bVal, currentStrValue)
        i += 1
    return braille_dict


_B = makeBrailleDictionary()

def dotsAdd(dotIter):
    u'''
    takes in an iterable of dots and returns them added together.
    
    >>> print(braille.lookup.dotsAdd([12, 3, 4]))
    ⠏

    Order does not matter:
    
    >>> print(braille.lookup.dotsAdd([4, 31, 2]))
    ⠏    
    '''
    dotsOut = []
    for n in dotIter:
        nStr = str(n)
        for nSub in nStr:
            if nSub == '0':
                continue # skip zeros
            dotsOut.append(int(nSub))
    dotsOut.sort()
    return _B[int(''.join(str(d) for d in dotsOut))]

def makePitchNameToNotes():
    stepNames = {'C': 145,
            'D': 15,
            'E': 124,
            'F': 1245,
            'G': 125,
            'A': 24,
            'B': 245,
            }
    durationTypes = {'128th': 0,
              '64th': 6,
              '32nd': 3,
              '16th': 36,
              'eighth': 0,
              'quarter': 6,
              'half': 3,
              'whole': 36              
              }
    stepDicts = {}
    for step in stepNames:
        stepDictSingle = {}
        for duration in durationTypes:
            stepDictSingle[duration] = dotsAdd([stepNames[step], durationTypes[duration]])
        whole = stepDictSingle['whole'] 
        stepDictSingle['breve'] = whole + _B[45] + _B[14] + whole
        stepDictSingle['longa'] = whole + _B[45] + _B[14] + _B[45] + _B[14] + whole
        stepDicts[step] = stepDictSingle
    return stepDicts
        
pitchNameToNotes = makePitchNameToNotes()

_lowOctave = _B[4]
_highOctave = _B[6]

octaves = {0: _lowOctave + _lowOctave,
           1: _lowOctave,
           2: _B[45],
           3: _B[456],
           4: _B[5],
           5: _B[46],
           6: _B[56],
           7: _highOctave,
           8: _highOctave + _highOctave,
           }

_sharp = _B[146]
_flat = _B[126]

accidentals = {'sharp':                _sharp,
               'double-sharp':         _sharp + _sharp,
               'triple-sharp':         _sharp + _sharp + _sharp, # extrapolated -- non-attested
               'quadruple-sharp':      _sharp + _sharp + _sharp + _sharp,
               'half-sharp':           _B[4] + _sharp,    # half sharps/flats from
               'one-and-a-half-sharp': _B[456] + _sharp,  # Bettye Krolick (NIM of BMN)
               'flat':                 _flat,
               'double-flat':          _flat + _flat,
               'triple-flat':          _flat + _flat + _flat,
               'quadruple-flat':       _flat + _flat + _flat + _flat,
               'half-flat':            _B[4] + _flat,
               'one-and-a-half-flat':  _B[456] + _flat,
               'natural':              _B[16],
               }

del _sharp
del _flat

intervals = {2: _B[34],
             3: _B[346],
             4: _B[3456],
             5: _B[35],
             6: _B[356],
             7: _B[25],
             8: _B[36]}

keySignatures = {-7:    _B[3456] + _B[1245] + _B[126],
                 -6:    _B[3456] + _B[124]  + _B[126],
                 -5:    _B[3456] + _B[15]   + _B[126],
                 -4:    _B[3456] + _B[145]  + _B[126],
                 -3:    _B[126]  + _B[126]  + _B[126],
                 -2:    _B[126]  + _B[126],
                 -1:    _B[126],
                 0:     u'',
                 1:     _B[146],
                 2:     _B[146]  + _B[146],
                 3:     _B[146]  + _B[146]  + _B[146],
                 4:     _B[3456] + _B[145]  + _B[146],
                 5:     _B[3456] + _B[15]   + _B[146],
                 6:     _B[3456] + _B[124]  + _B[146],
                 7:     _B[3456] + _B[1245] + _B[146]}

naturals = {0: u'',
            1: _B[16],
            2: _B[16] + _B[16],
            3: _B[16] + _B[16] + _B[16],
            4: _B[3456] + _B[145] + _B[16],
            5: _B[3456] + _B[15] + _B[16],
            6: _B[3456] + _B[124] + _B[16],
            7: _B[3456] + _B[1245] + _B[16]}

numbersUpper = {0: _B[245],
           1: _B[1],
           2: _B[12],
           3: _B[14],
           4: _B[145],
           5: _B[15],
           6: _B[124],
           7: _B[1245],
           8: _B[125],
           9: _B[24]}
numbersLower = {0: _B[356],
           1: _B[2],
           2: _B[23],
           3: _B[25],
           4: _B[256],
           5: _B[26],
           6: _B[235],
           7: _B[2356],
           8: _B[236],
           9: _B[35]}

rests = {'dummy':   _B[3],
         '128th':   _B[1346],
         '64th':    _B[1236],
         '32nd':    _B[136],
         '16th':    _B[134],
         'eighth':  _B[1346],
         'quarter': _B[1236],
         'half':    _B[136],
         'whole':   _B[134],
         'breve':   _B[134] + _B[45] + _B[14] + _B[134],
         'longa':   _B[134] + _B[45] + _B[14] + _B[45] + _B[14] + _B[134],         
         }

lengthPrefixes = {
        'larger': _B[45] + _B[126] + _B[2], # whole to eighth inclusive + longer (degarmo 15)
        'smaller': _B[6] + _B[126] + _B[2], # 16th to 128th inclusive
        'xsmall': _B[56] + _B[126] + _B[2], # 256th notes + presumably shorter?
                  
        }

barlines = {'final': _B[126] + _B[13],
            'double':_B[126] + _B[13] + _B[3],
            'dashed': _B[13],
            'heavy': _B[123], # use "unusual circumstances barline
            }

fingerMarks = {'1': _B[1],
               '2': _B[12],
               '3': _B[123],
               '4': _B[2],
               '5': _B[13]}

clefs = {'prefix': _B[345],
         'G': {1: _B[34] + octaves[1],
               2: _B[34],
               3: _B[34] + octaves[3],
               4: _B[34] + octaves[4],
               5: _B[34] + octaves[5]},
         'C': {1: _B[346] + octaves[1],
               2: _B[346] + octaves[2],
               3: _B[346],
               4: _B[346] + octaves[4],
               5: _B[346] + octaves[5]},
         'F': {1: _B[3456] + octaves[1],
               2: _B[3456] + octaves[2],
               3: _B[3456] + octaves[3],
               4: _B[3456],
               5: _B[3456] + octaves[5]},
         'suffix': {False: _B[123],
                    True: _B[13]}
        }
bowingSymbols = {}

beforeNoteExpr = {'staccato': _B[236],
                  'accent': _B[46] + _B[236],
                  'tenuto': _B[456] + _B[236],
                  'staccatissimo': _B[6] + _B[236],
                  'strong accent': _B[56] + _B[236], # Martellato
                  'detached legato': _B[5] + _B[236], # Legato-staccato
                  }

textExpressions = {'crescendo': _B[345] + _B[14] + _B[1235] + _B[3],
                   'cresc.': _B[345] + _B[14] + _B[1235] + _B[3],
                   'cr.': _B[345] + _B[14] + _B[1235] + _B[3],
                   'decrescendo': _B[345] + _B[145] + _B[15] + _B[14] + _B[1235] + _B[3],
                   'decresc.': _B[345] + _B[145] + _B[15] + _B[14] + _B[1235] + _B[3],
                   'decr.': _B[345] + _B[145] + _B[15] + _B[14] + _B[1235] + _B[3]}

alphabet = {'a': _B[1],
            'b': _B[12],
            'c': _B[14],
            'd': _B[145],
            'e': _B[15],
            'f': _B[124],
            'g': _B[1245],
            'h': _B[125],
            'i': _B[24],
            'j': _B[245],
            'k': _B[13],
            'l': _B[123],
            'm': _B[134],
            'n': _B[1345],
            'o': _B[135],
            'p': _B[1234],
            'q': _B[12345],
            'r': _B[1235],
            's': _B[234],
            't': _B[2345],
            'u': _B[136],
            'v': _B[1236],
            'w': _B[2456],
            'x': _B[1346],
            'y': _B[13456],
            'z': _B[1356],
            '!': _B[235],
            '\'': _B[3],
            ',': _B[2],
            '-': _B[356],
            '.': _B[256],
            '?': _B[236],
            '(': _B[2356],
            ')': _B[2356]}

symbols = {'space': _B[0],
           'double_space': _B[0] + _B[0],
           'number': _B[3456],
           'dot': _B[3],
           'tie': _B[4] + _B[14],
           'uppercase': _B[6],
           'metronome': _B[2356],
           'common': _B[46] + _B[14],
           'cut': _B[456] + _B[14],
           'music_hyphen': _B[5], 
           'transcriber-added_sign': _B[5], # same as music hyphen. degarmo chp 5; GT N. 9, 4.1, 5.2
           'music_asterisk': _B[345] + _B[26] + _B[35],
           'rh_keyboard': _B[46] + _B[345],
           'lh_keyboard': _B[456] + _B[345],
           'word': _B[345],
           'triplet': _B[23],
           'tuplet_prefix': _B[456], # irregular-grouping prefix
           'finger_change': _B[14], # [14.2; Degarmo Example 9-4]
           'first_set_missing_fingermark': _B[6], # [Degarmo 9-6]
           'second_set_missing_fingermark': _B[3], # [Degarmo 9-6]
           'opening_single_slur': _B[14],
           'opening_double_slur': _B[14] + _B[14],
           'closing_double_slur': _B[14],
           'opening_bracket_slur': _B[56] + _B[12],
           'closing_bracket_slur': _B[45] + _B[23],
           'basic_exception': _B[345] + _B[236],
           'full_inaccord': _B[126] + _B[345],
           'repeat': _B[2356],
           'print-pagination': _B[5] + _B[25], # used to indicate page turnover for sighted
           'braille-music-parenthesis': _B[6] + _B[3] # [T17, 17.6, degarmo chp. 10]
           }

fermatas = {'shape': {'normal': _B[126] + _B[123],
                      'angled': _B[45] + _B[126] + _B[123],
                      'square': _B[56] + _B[126] + _B[123],
                      },
            'on barline': _B[456],
            'between notes': _B[5],
            }

ascii_chars = {_B[0]: ' ',
               _B[1]: 'A',
               _B[2]: '1',
               _B[12]: 'B',
               _B[3]: '\'',
               _B[13]: 'K',
               _B[23]: '2',
               _B[123]: 'L',
               _B[4]: '@',
               _B[14]: 'C',
               _B[24]: 'I',
               _B[124]: 'F',
               _B[34]: '/',
               _B[134]: 'M',
               _B[234]: 'S',
               _B[1234]: 'P',
               _B[5]: '"',
               _B[15]: 'E',
               _B[25]: '3',
               _B[125]: 'H',
               _B[35]: '9',
               _B[135]: 'O',
               _B[235]: '6',
               _B[1235]: 'R',
               _B[45]: '^',
               _B[145]: 'D',
               _B[245]: 'J',
               _B[1245]: 'G',
               _B[345]: '>',
               _B[1345]: 'N',
               _B[2345]: 'T',
               _B[12345]: 'Q',
               _B[6]: ',',     
               _B[16]: '*',
               _B[26]: '5',
               _B[126]: '<',
               _B[36]: '-',
               _B[136]: 'U',
               _B[236]: '8',
               _B[1236]: 'V',
               _B[46]: '.',
               _B[146]: '%',
               _B[246]: '[',
               _B[1246]: '$',
               _B[346]: '+',
               _B[1346]: 'X',
               _B[2346]: '!',
               _B[12346]: '&',
               _B[56]: ';',     
               _B[156]: ':',
               _B[256]: '4',
               _B[1256]: '\\',
               _B[356]: '0',
               _B[1356]: 'Z',
               _B[2356]: '7',
               _B[12356]: '(',
               _B[456]: '_',
               _B[1456]: '?',
               _B[2456]: 'W',
               _B[12456]: ']',
               _B[3456]: '#',
               _B[13456]: 'Y',
               _B[23456]: ')',
               _B[123456]: '='}

binary_dots = {_B[0]:     ('00','00','00'),
               _B[1]:     ('10','00','00'),
               _B[2]:     ('00','10','00'),
               _B[12]:    ('10','10','00'),
               _B[3]:     ('00','00','10'),
               _B[13]:    ('10','00','10'),
               _B[23]:    ('00','10','10'),
               _B[123]:   ('10','10','10'),
               _B[4]:     ('01','00','00'),
               _B[14]:    ('11','00','00'),
               _B[24]:    ('01','10','00'),
               _B[124]:   ('11','10','00'),
               _B[34]:    ('01','00','10'),
               _B[134]:   ('11','00','10'),
               _B[234]:   ('01','10','10'),
               _B[1234]:  ('11','10','10'),
               _B[5]:     ('00','01','00'),
               _B[15]:    ('10','01','00'),
               _B[25]:    ('00','11','00'),
               _B[125]:   ('10','11','00'),
               _B[35]:    ('00','01','10'),
               _B[135]:   ('10','01','10'),
               _B[235]:   ('00','11','10'),
               _B[1235]:  ('10','11','10'),
               _B[45]:    ('01','01','00'),
               _B[145]:   ('11','01','00'),
               _B[245]:   ('01','11','00'),
               _B[1245]:  ('11','11','00'),
               _B[345]:   ('01','01','10'),
               _B[1345]:  ('11','01','10'),
               _B[2345]:  ('01','11','10'),
               _B[12345]: ('11','11','10'),
               _B[6]:     ('00','00','01'),    
               _B[16]:    ('10','00','01'),
               _B[26]:    ('00','10','01'),
               _B[126]:   ('10','10','01'),
               _B[36]:    ('00','00','11'),
               _B[136]:   ('10','00','11'),
               _B[236]:   ('00','10','11'),
               _B[1236]:  ('10','10','11'),
               _B[46]:    ('01','00','01'),
               _B[146]:   ('11','00','01'),
               _B[246]:   ('01','10','01'),
               _B[1246]:  ('11','10','01'),
               _B[346]:   ('01','00','11'),
               _B[1346]:  ('11','00','11'),
               _B[2346]:  ('01','10','11'),
               _B[12346]: ('11','10','11'),
               _B[56]:    ('00','01','01'),     
               _B[156]:   ('10','01','01'),
               _B[256]:   ('00','11','01'),
               _B[1256]:  ('10','11','01'),
               _B[356]:   ('00','01','11'),
               _B[1356]:  ('10','01','11'),
               _B[2356]:  ('00','11','11'),
               _B[12356]: ('01','11','11'),
               _B[456]:   ('01','01','01'),
               _B[1456]:  ('11','01','01'),
               _B[2456]:  ('01','11','01'),
               _B[12456]: ('11','11','01'),
               _B[3456]:  ('01','01','11'),
               _B[13456]: ('11','01','11'),
               _B[23456]: ('01','11','11'),
               _B[123456]: ('11','11','11')}

# make public
brailleDotDict = _B

if __name__ == "__main__":
    import music21
    music21.mainTest()

#------------------------------------------------------------------------------
# eof
