# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         harmonicFunction.py
# Purpose:      Mapping between Roman numeral figures and harmonic function labels
#
# Authors:      Mark Gotham
#
# Copyright:    Copyright © 2021 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------

from typing import Union
import unittest

from music21 import roman

from music21 import environment
_MOD = 'analysis.harmonicFunction'
environLocal = environment.Environment(_MOD)


functionFigureTuples = (
    # Scale degrees (major)
    # 1:
    ('T', 'I'),
    ('t', 'i'),
    # b2:
    ('sL', 'bII'),
    # 2:
    ('Sp', 'ii'),
    # b3:
    ('tP', 'III'),  # Note first: tP generally preferred over dL
    ('dL', 'III'),
    # 3:
    ('Dp', 'iii'),  # Note first: Dp generally preferred over tL
    ('Tl', 'iii'),
    # 4:
    ('S', 'IV'),
    ('s', 'iv'),
    # 5:
    ('D', 'V'),
    ('D7', 'V7'),
    ('d', 'v'),
    # b6:
    ('sP', 'VI'),  # Note first: sP generally preferred over tL
    ('tL', 'VI'),
    # 6:
    ('Tp', 'vi'),  # Note first: Tp generally preferred over Sl
    ('Sl', 'vi'),
    # b7:
    ('dP', 'VII'),
    # 7:
    ('Đ7', 'viio'),
    ('Dl', '#VII'))


def functionToFigure(harmonicFunctionLabel: str):
    '''
    Takes a Roman numeral figure (e.g., 'I') and
    returns the corresponding functional label (here, 'T' for major tonic).

    >>> analysis.harmonicFunction.functionToFigure('T')
    'I'

    Note that this is case sensitive.

    >>> analysis.harmonicFunction.functionToFigure('t')
    'i'

    The reverse operation is handled by the complementary
    :func:`~music21.analysis.harmonicFunction.figureToFunction`.

    There are 18 main functional label supported in all, for
    the three functional categories
    (T for tonic,
    S for subdominant,
    and D for dominant) and
    three relevant transformation types (none, P, and L)
    all in upper and lower case (for major/minor):
    T, Tp, Tl, t, tP, tL,
    S, Sp, Sl, s, sP, sL,
    D, Dp, Dl, d, dP, dL.

    Two additional labels are included for common and clearcut
    dominant functions chords:
    'D7' for 'V7', and
    'Đ7' for 'viio'.

    Some of the 18 main functions overlap, with two functional labels
    referring to the same Roman numeral figure.
    That makes no difference to this function,
    for instance both 'Tl' and 'Dp' simply map to 'iii':

    >>> analysis.harmonicFunction.functionToFigure('Tl')
    'iii'

    >>> analysis.harmonicFunction.functionToFigure('Dp')
    'iii'

    In the reverse case,
    :func:`~music21.analysis.harmonicFunction.figureToFunction`
    follows the convention of dispreferring the L-version.
    For this example, 'iii' will return 'Dp' (i.e. not 'Tl').

    >>> analysis.harmonicFunction.figureToFunction('iii')
    'Dp'

    Finally, both functions return False if the input is not recognised
    (i.e. in this case, not one of those functional label listed above).
    '''
    for entry in functionFigureTuples:
        if harmonicFunctionLabel == entry[0]:
            return entry[1]
    return False


def figureToFunction(romanNumeralFigure: Union[str, roman.RomanNumeral],
                     simplified: bool = False):
    '''
    Maps a Roman numeral figure to an harmonic function label.
    >>> analysis.harmonicFunction.figureToFunction('VI')
    'sP'

    Returns False in the case of no match.

    Optionally, return a simplified version which excludes any modications of
    the basic set of 6: t, T, s, S, d, D
    (major and minor forms of tonic, subdominant and dominant functions).
    >>> analysis.harmonicFunction.figureToFunction('VI', simplified=True)
    's'

    Inversions are not considered.
    If the input is a string, then no match will be found (returns False).
    If the input is a roman.RomanNumeral object they will be ignored
    (using the romanNumeralAlone attribute).
    >>> rn = roman.RomanNumeral('VI65')
    >>> analysis.harmonicFunction.figureToFunction(rn)
    'sP'

    See further notes on the complementary
    :func:`~music21.analysis.harmonicFunction.functionToFigure`.
    '''
    if isinstance(romanNumeralFigure, roman.RomanNumeral):
        romanNumeralFigure = romanNumeralFigure.romanNumeralAlone

    for entry in functionFigureTuples:
        if romanNumeralFigure == entry[1]:
            if simplified:
                return entry[0][0]
            else:
                return entry[0]
    return False


# ------------------------------------------------------------------------------

class Test(unittest.TestCase):

    def testInitialCases(self):
        self.assertEqual(functionToFigure('T'), 'I')
        self.assertEqual(figureToFunction('i'), 't')

    def testSimplifiedCases(self):
        self.assertEqual(figureToFunction('III'), 'tP')
        self.assertEqual(figureToFunction('III', simplified=True), 't')

    def testRomanNumeralObjects(self):
        self.assertEqual(figureToFunction(roman.RomanNumeral('IV')), 'S')
        self.assertEqual(figureToFunction(roman.RomanNumeral('iv')), 's')

    def testIgnoresInversion(self):
        self.assertEqual(figureToFunction('V42'), False)
        self.assertEqual(figureToFunction(roman.RomanNumeral('i6')), 't')


# -----------------------------------------------------------------------------

if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
