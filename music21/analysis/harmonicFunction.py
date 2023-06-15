# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         harmonicFunction.py
# Purpose:      Mapping between Roman numeral figures and harmonic function labels
#
# Authors:      Mark Gotham
#
# Copyright:    Copyright © 2022-2023 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
from __future__ import annotations

import unittest

from music21 import common
from music21 import key
from music21 import roman
from music21 import scale


class HarmonicFunction(common.enums.StrEnum):
    TONIC_MAJOR = 'T'
    TONIC_MAJOR_PARALLELKLANG_MINOR = 'Tp'
    TONIC_MAJOR_GEGENKLANG_MINOR = 'Tg'

    TONIC_MINOR = 't'
    TONIC_MINOR_PARALLELKLANG_MAJOR = 'tP'
    TONIC_MINOR_GEGENKLANG_MAJOR = 'tG'

    SUBDOMINANT_MAJOR = 'S'
    SUBDOMINANT_MAJOR_PARALLELKLANG_MINOR = 'Sp'
    SUBDOMINANT_MAJOR_GEGENKLANG_MINOR = 'Sg'

    SUBDOMINANT_MINOR = 's'
    SUBDOMINANT_MINOR_PARALLELKLANG_MAJOR = 'sP'
    SUBDOMINANT_MINOR_GEGENKLANG_MAJOR = 'sG'

    DOMINANT_MAJOR = 'D'
    DOMINANT_MAJOR_PARALLELKLANG_MINOR = 'Dp'
    DOMINANT_MAJOR_GEGENKLANG_MINOR = 'Dg'

    DOMINANT_MINOR = 'd'
    DOMINANT_MINOR_PARALLELKLANG_MAJOR = 'dP'
    DOMINANT_MINOR_GEGENKLANG_MAJOR = 'dG'


_functionFigureTuplesKeyNeutral = {
    HarmonicFunction.TONIC_MAJOR: 'I',  # 'T'
    HarmonicFunction.TONIC_MINOR: 'i',  # 't'

    HarmonicFunction.SUBDOMINANT_MINOR_GEGENKLANG_MAJOR: 'bII',  # 'sG'

    HarmonicFunction.SUBDOMINANT_MAJOR_PARALLELKLANG_MINOR: 'ii',  # 'Sp'

    HarmonicFunction.SUBDOMINANT_MAJOR: 'IV',  # 'S'
    HarmonicFunction.SUBDOMINANT_MINOR: 'iv',  # 's'

    HarmonicFunction.DOMINANT_MAJOR: 'V',  # 'D'
    HarmonicFunction.DOMINANT_MINOR: 'v',  # 'd'

    HarmonicFunction.TONIC_MAJOR_PARALLELKLANG_MINOR: 'vi',  # 'Tp'
    HarmonicFunction.SUBDOMINANT_MAJOR_GEGENKLANG_MINOR: 'vi',  # 'Sg'

    HarmonicFunction.DOMINANT_MAJOR_GEGENKLANG_MINOR: 'bvii',  # 'Dg'
}

functionFigureTuplesMajor = {
    HarmonicFunction.TONIC_MINOR_PARALLELKLANG_MAJOR: 'bIII',  # 'tP', note first
    HarmonicFunction.DOMINANT_MINOR_GEGENKLANG_MAJOR: 'bIII',  # 'dG'

    HarmonicFunction.DOMINANT_MAJOR_PARALLELKLANG_MINOR: 'iii',  # 'Dp', note first
    HarmonicFunction.TONIC_MAJOR_GEGENKLANG_MINOR: 'iii',  # 'Tg'

    HarmonicFunction.SUBDOMINANT_MINOR_PARALLELKLANG_MAJOR: 'bVI',  # 'sP', note first
    HarmonicFunction.TONIC_MINOR_GEGENKLANG_MAJOR: 'bVI',  # 'tG'

    HarmonicFunction.DOMINANT_MINOR_PARALLELKLANG_MAJOR: 'bVII',  # 'dP'
}

functionFigureTuplesMajor = {
    **functionFigureTuplesMajor,
    **_functionFigureTuplesKeyNeutral,
}

functionFigureTuplesMinor = {
    HarmonicFunction.TONIC_MINOR_PARALLELKLANG_MAJOR: 'III',  # 'tP', note first
    HarmonicFunction.DOMINANT_MINOR_GEGENKLANG_MAJOR: 'III',  # 'dG'

    HarmonicFunction.DOMINANT_MAJOR_PARALLELKLANG_MINOR: '#iii',  # 'Dp', note first
    HarmonicFunction.TONIC_MAJOR_GEGENKLANG_MINOR: '#iii',  # 'Tg'

    HarmonicFunction.SUBDOMINANT_MINOR_PARALLELKLANG_MAJOR: 'VI',  # 'sP', note first
    HarmonicFunction.TONIC_MINOR_GEGENKLANG_MAJOR: 'VI',  # 'tG'

    HarmonicFunction.DOMINANT_MINOR_PARALLELKLANG_MAJOR: 'VII',  # 'dP'
}

functionFigureTuplesMinor = {
    **functionFigureTuplesMinor,
    **_functionFigureTuplesKeyNeutral,
}


def functionToRoman(thisHarmonicFunction: HarmonicFunction,
                    keyOrScale: key.Key | scale.ConcreteScale | str = 'C'
                    ) -> roman.RomanNumeral | None:
    '''
    Takes harmonic function labels (such as 'T' for major tonic)
    with a key (keyOrScale, default = 'C') and
    returns the corresponding :class:`~music21.roman.RomanNumeral` object.

    >>> analysis.harmonicFunction.functionToRoman('T')
    <music21.roman.RomanNumeral I in C major>

    The harmonicFunction argument can be a string (as shown),
    though strictly speaking, it's handled through a special HarmonicFunction enum object.

    >>> fn = analysis.harmonicFunction.HarmonicFunction.TONIC_MAJOR
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
    where Functional notation ('HarmonicFunctionstheorie') is typically used
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
    if isinstance(keyOrScale, str):
        keyOrScale = key.Key(keyOrScale)

    referenceTuples = functionFigureTuplesMajor
    if isinstance(keyOrScale, key.Key) and keyOrScale.mode == 'minor':
        referenceTuples = functionFigureTuplesMinor

    try:
        figure = referenceTuples[thisHarmonicFunction]
    except KeyError:
        return None
    return roman.RomanNumeral(figure, keyOrScale)


def romanToFunction(rn: roman.RomanNumeral,
                    onlyHauptHarmonicFunction: bool = False
                    ) -> HarmonicFunction | None:
    '''
    Takes a Roman numeral and returns a corresponding harmonic function label.

    >>> rn1 = roman.RomanNumeral('VI', 'a')
    >>> fn1 = analysis.harmonicFunction.romanToFunction(rn1)
    >>> fn1
    <HarmonicFunction.SUBDOMINANT_MINOR_PARALLELKLANG_MAJOR>

    This can be converted into a string:

    >>> str(fn1)
    'sP'

    Optionally, set onlyHauptHarmonicFunction to True to return
    a simplified version with only the HauptHarmonicFunction
    (one of t, T, s, S, d, D: major and minor forms of the tonic, subdominant and dominant).

    >>> fn1 = analysis.harmonicFunction.romanToFunction(rn1, onlyHauptHarmonicFunction=True)
    >>> fn1
    <HarmonicFunction.SUBDOMINANT_MINOR>

    >>> str(fn1)
    's'

    Inversions are not currently considered (they may be in a future version of this).
    This function simply uses the romanNumeral attribute of the roman.RomanNumeral object.
    This excludes inversions, but
    includes, where applicable, the frontAlterationAccidental.modifier.

    >>> rn2 = roman.RomanNumeral('bII6', 'g')
    >>> fn2 = analysis.harmonicFunction.romanToFunction(rn2)
    >>> fn2
    <HarmonicFunction.SUBDOMINANT_MINOR_GEGENKLANG_MAJOR>

    >>> str(fn2)
    'sG'

    See further notes on the complementary
    :func:`~music21.analysis.harmonicFunction.functionToRoman`.
    '''

    referenceTuples = functionFigureTuplesMajor
    if rn.key:  # RomanNumeral object can be created without one.
        if rn.key.mode == 'minor':
            referenceTuples = functionFigureTuplesMinor

    for thisKey, thisValue in referenceTuples.items():
        if rn.romanNumeral == thisValue:
            if onlyHauptHarmonicFunction:
                return HarmonicFunction(str(thisKey)[0])
            else:
                return thisKey

    return None


# ------------------------------------------------------------------------------
class Test(unittest.TestCase):
    def testAllFunctionLabelsInEnum(self):
        '''
        Test that all the entries in the functionFigureTuples
        (both major and minor) are represented in the HarmonicFunction enum.

        Also tests one fake (invalid) function label.
        '''
        # All and only valid
        for thisHarmonicFunction in functionFigureTuplesMajor:
            HarmonicFunction(thisHarmonicFunction)
        for thisHarmonicFunction in functionFigureTuplesMinor:
            HarmonicFunction(thisHarmonicFunction)

        # Invalid
        fakeExample = 'TPG'
        self.assertRaises(ValueError, HarmonicFunction, fakeExample)

    def testFunctionToRoman(self):
        self.assertEqual(functionToRoman(HarmonicFunction.TONIC_MAJOR).figure, 'I')

    def testSimplified(self):
        rn = roman.RomanNumeral('III', 'f')

        fn1 = romanToFunction(rn)
        self.assertIs(fn1, HarmonicFunction.TONIC_MINOR_PARALLELKLANG_MAJOR)
        self.assertEqual(str(fn1), 'tP')

        fn2 = romanToFunction(rn, onlyHauptHarmonicFunction=True)
        self.assertIs(fn2, HarmonicFunction.TONIC_MINOR)
        self.assertEqual(str(fn2), 't')

    def testIgnoresInversion(self):
        self.assertEqual(romanToFunction(roman.RomanNumeral('i6')), 't')


# -----------------------------------------------------------------------------
if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
