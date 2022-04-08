# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         harmonicFunction.py
# Purpose:      Mapping between Roman numeral figures and harmonic function labels
#
# Authors:      Mark Gotham
#
# Copyright:    Copyright © 2022 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------

from typing import Union
import unittest

from music21 import common
from music21 import key
from music21 import roman
from music21 import scale

from music21 import environment
_MOD = 'analysis.harmonicFunction'
environLocal = environment.Environment(_MOD)


class FUNKTION(common.enums.StrEnum):

    TONIKA_DUR = 'T'
    TONIKA_DUR_PARALLELKLANG_MOLL = 'Tp'
    TONIKA_DUR_GEGENKLANG_MOLL = 'Tg'

    TONIKA_MOLL = 't'
    TONIKA_MOLL_PARALLELKLANG_DUR = 'tP'
    TONIKA_MOLL_GEGENKLANG_DUR = 'tG'

    SUBDOMINANT_DUR = 'S'
    SUBDOMINANT_DUR_PARALLELKLANG_MOLL = 'Sp'
    SUBDOMINANT_DUR_GEGENKLANG_MOLL = 'Sg'

    SUBDOMINANT_MOLL = 's'
    SUBDOMINANT_MOLL_PARALLELKLANG_DUR = 'sP'
    SUBDOMINANT_MOLL_GEGENKLANG_DUR = 'sG'

    DOMINANT_DUR = 'D'
    DOMINANT_DUR_PARALLELKLANG_MOLL = 'Dp'
    DOMINANT_DUR_GEGENKLANG_MOLL = 'Dg'

    DOMINANT_MOLL = 'd'
    DOMINANT_MOLL_PARALLELKLANG_DUR = 'dP'
    DOMINANT_MOLL_GEGENKLANG_DUR = 'dG'


_functionFigureTuplesKeyNeutral = (

    ('T', 'I'),
    ('t', 'i'),

    ('sG', 'bII'),

    ('Sp', 'ii'),

    ('S', 'IV'),
    ('s', 'iv'),

    ('D', 'V'),
    ('d', 'v'),

    ('Tp', 'vi'),  # Note first: Tp generally preferred over Sg
    ('Sg', 'vi'),

    ('Dg', 'bvii')

    )

functionFigureTuplesMajor = (

    ('tP', 'bIII'),  # Note first: tP generally preferred over dG
    ('dG', 'bIII'),

    ('Dp', 'iii'),  # Note first: Dp generally preferred over Tg
    ('Tg', 'iii'),

    ('sP', 'bVI'),  # Note first: sP generally preferred over tG
    ('tG', 'bVI'),

    ('dP', 'bVII'),

    )

functionFigureTuplesMajor += _functionFigureTuplesKeyNeutral

functionFigureTuplesMinor = (

    ('tP', 'III'),  # Note first: tP generally preferred over dG
    ('dG', 'III'),

    ('Dp', '#iii'),  # Note first: Dp generally preferred over Tg
    ('Tg', '#iii'),

    ('sP', 'VI'),  # Note first: sP generally preferred over tG
    ('tG', 'VI'),

    ('dP', 'VII'),

    )

functionFigureTuplesMinor += _functionFigureTuplesKeyNeutral


def functionToRoman(harmonicFunction: FUNKTION,
                    keyOrScale: Union[key.Key, scale.Scale, str] = 'C'):
    '''
    Takes an harmonic function labels (such as 'T' for major tonic)
    with a key (keyOrScale, default = 'C') and
    returns the corresponding :class:`~music21.roman.RomanNumeral` object.

    >>> analysis.harmonicFunction.functionToRoman('T')
    <music21.roman.RomanNumeral I in C major>

    The harmonicFunction argument can be a string (as shown),
    though stictly speaking, it's handled through a special FUNKTION enum object.

    >>> fn = analysis.harmonicFunction.FUNKTION.TONIKA_DUR
    >>> str(fn)
    'T'

    >>> analysis.harmonicFunction.functionToRoman(fn).figure
    'I'

    As with Roman numerals, this is case sensitive.
    For instance, 't' indicates a minor tonic
    as distinct from the major tonic, 'T'.

    >>> analysis.harmonicFunction.functionToRoman('t').figure
    'i'

    There are 18 main functional labels supported in all, for
    the three functional categories
    (T for tonic, S for subdominant, and D for dominant) and
    three relevant transformation types (none, P, and G)
    all in upper and lower case (for major/minor):
    T, Tp, Tg, t, tP, tG,
    S, Sp, Sg, s, sP, sG,
    D, Dp, Dg, d, dP, dG.

    Note that this module uses terminology from modern German music theory
    where Functional notation ('Funktionstheorie') is typically used
    throughout the curriculum in preference over Roman numerals ('Stufentheorie').

    First, note the false friend: here 'P' for 'Parallel'
    connects a major triad with the minor triad a minor third below (e.g. C-a).
    (in English-speaking traditions this would usually be 'relative').

    Second, note that this module uses
    'G' (and 'g'), standing for
    'Gegenklänge' or 'Gegenparallelen'.
    'L' (and 'l') for Leittonwechselklänge is equivalent to this.
    (Again, 'G' is more common in modern German-language music theory).

    Use the keyOrScale argement to specify a key.
    This makes a difference where 6th and 7th degrees of minor are involved.

    >>> analysis.harmonicFunction.functionToRoman('sP', keyOrScale='C').figure
    'bVI'

    >>> analysis.harmonicFunction.functionToRoman('sP', keyOrScale='a').figure
    'VI'

    Some of the 18 main functions overlap, with two functional labels
    referring to the same Roman numeral figure.
    For instance both 'Tg' and 'Dp' simply map to 'iii':

    >>> analysis.harmonicFunction.functionToRoman('Tp').figure
    'vi'

    >>> analysis.harmonicFunction.functionToRoman('Sg').figure
    'vi'

    The reverse operation is handled by the complementary
    :func:`~music21.analysis.harmonicFunction.romanToFunction`.
    In this case, :func:`~music21.analysis.harmonicFunction.romanToFunction`
    follows the convention of preferring the P-version over alternatives.

    >>> rn = roman.RomanNumeral('vi')
    >>> str(analysis.harmonicFunction.romanToFunction(rn))
    'Tp'

    '''
    if type(keyOrScale) == str:
        keyOrScale = key.Key(keyOrScale)

    referenceTuples = functionFigureTuplesMajor
    if keyOrScale.mode == 'minor':
        referenceTuples = functionFigureTuplesMinor

    for entry in referenceTuples:
        if str(harmonicFunction) == entry[0]:
            return roman.RomanNumeral(entry[1], keyOrScale)

    return False


def romanToFunction(rn: roman.RomanNumeral,
                    onlyHauptfunktion: bool = False
                    ):
    '''
    Takes a Roman numeral and returns a corresponding harmonic function label.

    >>> rn1 = roman.RomanNumeral('VI', 'a')
    >>> fn1 = analysis.harmonicFunction.romanToFunction(rn1)
    >>> fn1
    <FUNKTION.SUBDOMINANT_MOLL_PARALLELKLANG_DUR>

    This can be converted into a string:

    >>> str(fn1)
    'sP'

    Optionally, set onlyHauptfunktion to True to return
    a simplified version with only the Hauptfunktion
    (one of t, T, s, S, d, D: major and minor forms of the tonic, subdominant and dominant).

    >>> fn1 = analysis.harmonicFunction.romanToFunction(rn1, onlyHauptfunktion=True)
    >>> fn1
    <FUNKTION.SUBDOMINANT_MOLL>

    >>> str(fn1)
    's'

    Inversions are not currently considered (they may be in a future version of this).
    This function simply uses the romanNumeral attribute of the roman.RomanNumeral object.
    This excludes inversions, but
    includes, where applicable, the frontAlterationAccidental.modifier.

    >>> rn2 = roman.RomanNumeral('bII6', 'g')
    >>> fn2 = analysis.harmonicFunction.romanToFunction(rn2)
    >>> fn2
    <FUNKTION.SUBDOMINANT_MOLL_GEGENKLANG_DUR>

    >>> str(fn2)
    'sG'

    See further notes on the complementary
    :func:`~music21.analysis.harmonicFunction.functionToRoman`.
    '''

    referenceTuples = functionFigureTuplesMajor
    if rn.key:  # RomanNumeral object can be created without one.
        if rn.key.mode == 'minor':
            referenceTuples = functionFigureTuplesMinor

    for entry in referenceTuples:
        if rn.romanNumeral == entry[1]:
            if onlyHauptfunktion:
                return FUNKTION(entry[0][0])
            else:
                return FUNKTION(entry[0])
    return False


# ------------------------------------------------------------------------------

class Test(unittest.TestCase):

    def testAllFunctionLabelsInEnum(self):
        '''
        Test that all the string entries in the functionFigureTuples
        (both major and minor) are represented in the FUNKTION enum.
        '''
        for func in functionFigureTuplesMajor:
            FUNKTION(func[0])
        for func in functionFigureTuplesMinor:
            FUNKTION(func[0])

    def testFunctionToRoman(self):
        self.assertEqual(functionToRoman('T').figure, 'I')

    def testSimplified(self):
        rn = roman.RomanNumeral('III', 'f')
        self.assertEqual(str(romanToFunction(rn)), 'tP')
        self.assertEqual(str(romanToFunction(rn, onlyHauptfunktion=True)), 't')

    def testIgnoresInversion(self):
        self.assertEqual(romanToFunction(roman.RomanNumeral('i6')), 't')


# -----------------------------------------------------------------------------

if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
