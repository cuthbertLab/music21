# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         humdrum.harmparser.py
# Purpose:      A parser for annotations in **harm spines of Humdrum
#
# Authors:      Nestor Napoles Lopez
#
# Copyright:    Copyright © 2009-2012, 2020 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
Harmonic annotations from humdrum to `music21`.

The `**harm` representation is described here: https://www.humdrum.org/rep/harm/
'''
import re
import unittest
from typing import Dict, Any

def convertHarmToRoman(harmStr):
    # noinspection PyShadowingNames
    '''
    Converts a `**harm` string into a string that
    can be used to instantiate a RomanNumeral object.

    This is necessary because the two notations are not
    identical. For example, a "V7b" in `**harm` turns into "V65".

    Instantiate a HarmParser to process `**harm` strings

    >>> convertHarmToRoman = humdrum.harmparser.convertHarmToRoman

    Convert a few `**harm` strings to music21.roman.RomanNumeral figures

    >>> diatonicTriads = ['I', 'Vc', 'Ib', 'iib', 'V', 'viiob', 'vib']
    >>> [convertHarmToRoman(x) for x in diatonicTriads]
    ['I', 'V64', 'I6', 'ii6', 'V', 'viio6', 'vi6']

    A few seventh-chord inversions
    >>> diatonicSevenths = ['V7', 'viio7c', 'V7d', 'viio7b', 'V7c']
    >>> [convertHarmToRoman(x) for x in diatonicSevenths]
    ['V7', 'viio43', 'V2', 'viio65', 'V43']

    Inversion-wise, augmented sixth chords are a bit tricky
    German and French are treated as seventh-chords (4 notes)
    Italians are treated as triads

    >>> italianSixths = ['Lt', 'Ltb', 'Ltc']
    >>> [convertHarmToRoman(x) for x in italianSixths]
    ['It', 'It6', 'It64']

    >>> frenchSixths = ['Fr', 'Frb', 'Frc', 'Frd']
    >>> [convertHarmToRoman(x) for x in frenchSixths]
    ['Fr7', 'Fr65', 'Fr43', 'Fr2']

    >>> germanSixths = ['Gn', 'Gnb', 'Gnc', 'Gnd']
    >>> [convertHarmToRoman(x) for x in germanSixths]
    ['Ger7', 'Ger65', 'Ger43', 'Ger2']
    '''
    # Parse the input string
    harm = HarmParser().parse(harmStr)

    if not harm:
        return None

    if harm['root'] == "Gn":
        degree = 'Ger'
        harm['intervals'] = ['7']
    elif harm['root'] == 'Lt':
        degree = 'It'
    elif harm['root'] == 'Fr':
        degree = 'Fr'
        harm['intervals'] = ['7']
    else:
        degree = harm['root']
    # Altered scale degrees
    alteration = ''
    if harm['accidental']:
        alteration = harm['accidental']
    # Augmented or diminished qualities
    fifthsQuality = ''
    if harm['attribute']:
        fifthsQuality = harm['attribute']
    # Seventh chords
    isSeventh = False
    if harm['intervals'] and '7' in harm['intervals']:
        isSeventh = True
    # Numeric inversions (although it is more the 'figured bass')
    if harm['inversion']:
        inversionNumber = ['a', 'b', 'c', 'd'].index(harm['inversion'])
    else:
        inversionNumber = 0
    inversion = ''
    if inversionNumber == 0:
        inversion = '7' if isSeventh else ''
    elif inversionNumber == 1:
        inversion = '65' if isSeventh else '6'
    elif inversionNumber == 2:
        inversion = '43' if isSeventh else '64'
    elif inversionNumber == 3:
        # Assume it is a seventh chord or a special chord (e.g., Ger/Fr)
        inversion = '2'
    # Any secondary functions
    secondaryFunctions = []
    if harm['secondary']:
        secondaryFunctions.append('')
        secondary = harm['secondary']
        while secondary:
            secondaryFunctions.append(secondary['root'])
            secondary = secondary['secondary']
    secondary = ''
    if secondaryFunctions:
        secondary = '/'.join(secondaryFunctions)
    return alteration + degree + fifthsQuality + inversion + secondary


class HarmDefs:
    ''' Regular expression definitions for the HarmParser class '''

    # Detect lowered or raised root (-|lowered, #|raised)
    accidental = r'''
    (?P<accidental>          # Named group _accidental
    [#-]{0,2})
    '''

    # The degree or special chord, i.e., I, V, Neapolitan, German augmented sixth, etc.
    roots = r'''
    (?P<root>               # Named group _root_
     i|ii|iii|iv|v|vi|vii|  # Minor mode degrees
     I|II|III|IV|V|VI|VII|  # Major mode degrees
     N|Gn|Lt|Fr|Tr)         # Special chords
    '''

    # Detect diminished or augmented triads (o|diminished, +|augmented)
    attribute = r'''
    (?P<attribute>          # Named group _attribute_
    [o+]?)
    '''

    # Detect added intervals, e.g., M7, m7, DD7, A6, etc.
    # noinspection SpellCheckingInspection
    intervals = r'''
    ((?P<intervals>         # Named group _intervals
    \d+|[mMPAD]\d+|         # Detect minor, Major, Augmented or Diminished intervals
    AA\d+|                  # Double-augmented intervals
    DD\d+)                  # Double-diminished intervals
    *)                      # Not a limit on how many intervals can be added
    '''

    # Detect inversions (b|First inversion, c|Second inversion, d|Third inversion)
    inversion = r'''
    (?P<inversion>          # Named group _inversions_
    [b-d]?)                 # Only third inversions possible so far
    '''

    # Detect implied harmony between parentheses, e.g., (I), (V), (viio/ii), etc.
    implied = r'''
    ^(                      # Match for entire string or fail
    \(                      # Open parenthesis
    (?P<implied_harmony>    # Group the expression
    ([^\(^\)])+             # At least one expression
    )                       # /Group the expression
    \)                      # Closing parenthesis
    )$                      # /Match for entire string or fail
    '''

    # Detect an alternative harmony between brackets, e.g., I[V], I[V/IV], etc.
    alternative = r'''
    (\[                     # Open brackets
    (?P<alternative>        # Named group _alternative_
    ([^\[^\]])+)            # Match at least one time for any expression inside brackets
    \]                      # Close brackets
    )?                      # If no alternative expression, then no brackets should appear at all
    '''

    # Detect secondary functions, e.g., V/V, V/iv/ii, viioD7/iv/v, etc.
    secondary = r'''
    (/                      # Slash implies a secondary function
    (?P<secondary>          # Named group _secondary_
    ([\s\S])+)              # Get all the expression after the slash symbol
    )?                      # If no secondary function, then the slash symbol should not appear
    '''
    # The definition for a harm expr
    harmExpression = (r'^('
        + accidental
        + roots
        + attribute
        + intervals
        + inversion
        + alternative
        + secondary
        + r')$')


class HarmParser:
    '''Parses an expression in `**harm` syntax'''

    defs = HarmDefs()

    def __init__(self):
        self.harmRegExp = re.compile(HarmParser.defs.harmExpression, re.VERBOSE)
        self.impliedRegExp = re.compile(HarmParser.defs.implied, re.VERBOSE)

    def parse(self, harmExpression) -> Dict[str, Any]:
        # Check for implied harmony
        impliedMatch = self.impliedRegExp.match(harmExpression)
        if impliedMatch:
            # This is implied harmony
            impliedHarmony = impliedMatch.groupdict()['implied_harmony']
            # Call the function again over the inner expression
            m = self.parse(impliedHarmony)
            if m:
                m['implied'] = True
            return m
        else:
            # Normal expression
            matchHarmRegExp = self.harmRegExp.match(harmExpression)
            if matchHarmRegExp:
                m: Dict[str, Any] = matchHarmRegExp.groupdict()
                m['implied'] = False
                # Finding alternative harmony
                if m['alternative'] is not None:
                    alternativeExpression = m['alternative']
                    a = self.parse(alternativeExpression)
                    m['alternative'] = a
                # Finding secondary functions
                if m['secondary'] is not None:
                    secondaryExpression = m['secondary']
                    s = self.parse(secondaryExpression)
                    m['secondary'] = s
                return m
            return {}


class Test(unittest.TestCase):

    def testTriads(self):
        # noinspection SpellCheckingInspection
        harmTriads = [
            'I', 'Ib', 'Ic',
            'ii', 'iib', 'iic',
            'iii', 'iiib', 'iiic',
            'IV', 'IVb', 'IVc',
            'V', 'Vb', 'Vc',
            'vi', 'vib', 'vic',
            'viio', 'viiob', 'viioc'
        ]
        groundTruth = (
            'I', 'I6', 'I64',
            'ii', 'ii6', 'ii64',
            'iii', 'iii6', 'iii64',
            'IV', 'IV6', 'IV64',
            'V', 'V6', 'V64',
            'vi', 'vi6', 'vi64',
            'viio', 'viio6', 'viio64'
        )
        romanTriads = [convertHarmToRoman(x) for x in harmTriads]
        self.assertEqual(tuple(romanTriads), groundTruth)

    def testSevenths(self):
        harmSevenths = [
            'I7', 'I7b', 'I7c', 'I7d',
            'ii7', 'ii7b', 'ii7c', 'ii7d',
            'iii7', 'iii7b', 'iii7c', 'iii7d',
            'IV7', 'IV7b', 'IV7c', 'IV7d',
            'V7', 'V7b', 'V7c', 'V7d',
            'vi7', 'vi7b', 'vi7c', 'vi7d',
            'viio7', 'viio7b', 'viio7c', 'viio7d'
        ]
        groundTruth = (
            'I7', 'I65', 'I43', 'I2',
            'ii7', 'ii65', 'ii43', 'ii2',
            'iii7', 'iii65', 'iii43', 'iii2',
            'IV7', 'IV65', 'IV43', 'IV2',
            'V7', 'V65', 'V43', 'V2',
            'vi7', 'vi65', 'vi43', 'vi2',
            'viio7', 'viio65', 'viio43', 'viio2'
        )
        romanSevenths = [convertHarmToRoman(x) for x in harmSevenths]
        self.assertEqual(tuple(romanSevenths), groundTruth)

    def testSpecialChords(self):
        harmSpecialChords = [
            'N', 'Nb', 'Nc',
            'Lt', 'Ltb', 'Ltc',
            'Fr', 'Frb', 'Frc', 'Frd',
            'Gn', 'Gnb', 'Gnc', 'Gnd'
        ]
        groundTruth = (
            'N', 'N6', 'N64',
            'It', 'It6', 'It64',
            'Fr7', 'Fr65', 'Fr43', 'Fr2',
            'Ger7', 'Ger65', 'Ger43', 'Ger2'
        )
        romanSpecialChords = [convertHarmToRoman(x) for x in harmSpecialChords]
        self.assertEqual(tuple(romanSpecialChords), groundTruth)

    def testAlterations(self):
        harmAlterations = [
            '-IIb', '--IIc', '#IV7', '##IV7b'
        ]
        groundTruth = (
            '-II6', '--II64', '#IV7', '##IV65'
        )
        romanAlterations = [convertHarmToRoman(x) for x in harmAlterations]
        self.assertEqual(tuple(romanAlterations), groundTruth)


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
