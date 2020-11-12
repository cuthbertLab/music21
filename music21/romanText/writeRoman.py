# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         romanText/writeRoman.py
# Purpose:      Writer for the 'RomanText' format
#
# Authors:      Mark Gotham
#
# Copyright:    Copyright © 2020 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
Writer for the 'RomanText' format (Tymoczko, Gotham, Cuthbert, & Ariza ISMIR 2019)
'''

import fractions
import unittest

from typing import Optional, Union

from music21 import base
from music21 import metadata
from music21 import meter
from music21 import prebase
from music21 import roman
from music21 import romanText
from music21 import stream


# ------------------------------------------------------------------------------

class RnWriter(prebase.ProtoM21Object):
    '''
    Extracts the relevant information from a stream of Roman numeral objects for
    writing to text files in the 'RomanText' format (rntxt).
    Writing rntxt is handled externally in the subConverters module so
    most users will never need to call this class directly, and will only invoke
    it indirectly through .write('rntxt').
    Possible exceptions include users who want to convert Roman numberals into rntxt type
    strings and want to work with those strings directly, without writing to disc.

    For consistency with .show() across music21, this class theoretically callable on
    any type of Music21Object.
    Within this wide range, more plausibly use cases including calling on
    a score (with or without parts), a part, or a measure containing one or more Roman numerals.

    >>> scoreBach = corpus.parse('bach/choraleAnalyses/riemenschneider004.rntxt')
    >>> rnWriterFromScore = romanText.writeRoman.RnWriter(scoreBach)

    The strings are stored in the RnWriter's combinedList variable, starting with the metadata:

    >>> rnWriterFromScore.combinedList[0]
    'Composer: J. S. Bach'

    >>> rnWriterFromScore.combinedList[0] == 'Composer: ' + rnWriterFromScore.composer
    True

    The list then continues with strings for each measure. Here's the last:

    >>> rnWriterFromScore.combinedList[-1]
    'm10 b1 V6/V b2 V b3 I'

    In the case of the score, the top part is assumed to contain the Roman numerals.
    This is consistent with the parsing of rntxt which involves putting Roman numerals in a part
    (the top, and only part) within a score.

    In all other cases, the objects are iteratively inserted into larger streams until we end up
    with a part object (e.g. measure > part).

    >>> rn = roman.RomanNumeral('viio64', 'a')
    >>> rnWriterFromRn = romanText.writeRoman.RnWriter(rn)
    >>> rnWriterFromRn.combinedList[0]
    'Composer: Composer unknown'

    >>> rnWriterFromRn.combinedList[-1]
    'm0 b1 a: viio64'

    Users can do these insertions themselves, but don't need to:

    >>> m = stream.Measure()
    >>> m.insert(0, rn)
    >>> rnWriterFromMeasure = romanText.writeRoman.RnWriter(m)
    >>> rnWriterFromMeasure.combinedList == rnWriterFromRn.combinedList
    True

    >>> p = stream.Part()
    >>> p.insert(0, m)
    >>> rnWriterFromPart = romanText.writeRoman.RnWriter(p)
    >>> rnWriterFromPart.combinedList == rnWriterFromMeasure.combinedList
    True

    >>> s = stream.Score()
    >>> s.insert(0, m)
    >>> rnWriterFromScoreWithoutPart = romanText.writeRoman.RnWriter(p)
    >>> rnWriterFromScoreWithoutPart.combinedList == rnWriterFromMeasure.combinedList
    True

    In all cases, handling of composer and work metadata is
    extracted from score metadata wherever possible.
    A metadata.composer entry will register directly as will any enties for
    workTitle, movementNumber, and movementName (see the prepTitle method for details).
    As always, these entries are user-settable.
    Make any adjustments to the metadata before calling this class.
    '''

    def __init__(self,
                 obj: base.Music21Object,
                 ):

        self.composer = 'Composer unknown'
        self.title = 'Title unknown'

        if obj.isStream:

            if isinstance(obj, stream.Score):
                if obj.parts:
                    self.container = obj.parts[0]
                else:  # score with no parts
                    self.container = obj

            elif isinstance(obj, stream.Part):
                self.container = obj

            elif isinstance(obj, stream.Measure):
                self.container = stream.Part()
                self.container.insert(0, obj)

            else:  # A stream, but not a measure, part, or score
                objs = [x for x in obj]
                self._makeContainer(objs)

            if obj.metadata:  # sic, obj not container for metadata, and only if it's stream
                self.prepTitle(obj.metadata)
                if obj.metadata.composer:
                    self.composer = obj.metadata.composer

        else:  # Not a stream
            self._makeContainer([obj])

        self.combinedList = [f'Composer: {self.composer}',
                             f'Title: {self.title}',
                             'Analyst: ',
                             'Proofreader: ',
                             '']  # One blank line between metadata and analysis
        # Note: blank analyst and proof reader entries until supported within music21 metadata

        if not self.container.getElementsByClass('TimeSignature'):
            self.container.insert(0, meter.TimeSignature('4/4'))  # Placeholder

        self.currentKeyString: str = ''
        self.prepSequentialListOfLines()

    def _makeContainer(self,
                       objs: list):
        '''
        Makes a placeholder container for the usual cases where this class is called on
        generic- or non-stream object.
        '''
        m = stream.Measure()
        for x in objs:
            m.insert(0, x)
        self.container = stream.Part()
        self.container.insert(0, m)

    def prepTitle(self,
                  md: metadata):
        '''
        Attempt to prepare a single work title from the score metadata looking at each of
        the title, movementNumber and movementName attributes.
        Failing that, a placeholder 'Unknown title' stands in.

        >>> s = stream.Score()
        >>> rnScore = romanText.writeRoman.RnWriter(s)
        >>> rnScore.title
        'Title unknown'

        >>> s.insert(0, metadata.Metadata())
        >>> s.metadata.title = 'Fake title'
        >>> s.metadata.movementNumber = 123456789
        >>> s.metadata.movementName = 'Fake movementName'
        >>> rnScoreWithMD = romanText.writeRoman.RnWriter(s)
        >>> rnScoreWithMD.title
        'Fake title - No.123456789: Fake movementName'
        '''

        workingTitle = []

        if md.title:
            workingTitle.append(md.title)
        if md.movementNumber:
            workingTitle.append(f'- No.{md.movementNumber}:')  # Spaces later
        if md.movementName:
            if md.movementName != md.title:
                workingTitle.append(md.movementName)

        if len(workingTitle) > 0:
            self.title = ' '.join(workingTitle)

# ------------------------------------------------------------------------------

    def prepSequentialListOfLines(self):
        '''
        Prepares a sequential list of text lines, with time signatures and Roman numerals
        adding this to the (already prepared) metadata preamble ready for printing.

        >>> p = stream.Part()
        >>> m = stream.Measure()
        >>> m.insert(0, meter.TimeSignature('4/4'))
        >>> m.insert(0, roman.RomanNumeral('V', 'G'))
        >>> p.insert(0, m)
        >>> testCase = romanText.writeRoman.RnWriter(p)
        >>> testCase.combinedList[-1]  # Last entry, after the metadata
        'm0 b1 G: V'
        '''

        for thisMeasure in self.container.getElementsByClass('Measure'):
            # TimeSignatures
            tsThisMeasure = [t for t in thisMeasure.getElementsByClass('TimeSignature')]
            if tsThisMeasure:
                firstTS = tsThisMeasure[0]
                self.combinedList.append(f'Time Signature: {firstTS.ratioString}')
                if len(tsThisMeasure) > 1:
                    unprocessedTSs = [x.ratioString for x in tsThisMeasure[1:]]
                    msg = f'further time signature change(s) unprocessed: {unprocessedTSs}'
                    self.combinedList.append(f'Note: {msg}')

            # RomanNumerals
            measureString = ''  # Clear for each measure

            rnsThisMeasure = thisMeasure.getElementsByClass('RomanNumeral')

            for rn in rnsThisMeasure:
                chordString = self.getChordString(rn)
                measureString = rnString(measureNumber=thisMeasure.measureNumber,  # WithSuffix ?
                                         beat=rn.beat,
                                         chordString=chordString,
                                         inString=measureString,  # Creating update
                                         )

            if measureString:
                self.combinedList.append(measureString)

    def getChordString(self,
                       rn: roman.RomanNumeral):
        '''
        Produce a string from a Roman number with the chord and
        the key if that key constitutes a change from the foregoing context.

        >>> p = stream.Part()
        >>> m = stream.Measure()
        >>> m.insert(0, meter.TimeSignature('4/4'))
        >>> m.insert(0, roman.RomanNumeral('V', 'G'))
        >>> p.insert(0, m)
        >>> testCase = romanText.writeRoman.RnWriter(p)
        >>> sameKeyChord = testCase.getChordString(roman.RomanNumeral('I', 'G'))
        >>> sameKeyChord
        'I'

        >>> changeKeyChord = testCase.getChordString(roman.RomanNumeral('V', 'D'))
        >>> changeKeyChord
        'D: V'
        '''

        keyString = rn.key.tonicPitchNameWithCase.replace('-', 'b')
        if keyString != self.currentKeyString:
            self.currentKeyString = keyString
            return f'{keyString}: {rn.figure}'
        else:
            return str(rn.figure)


# ------------------------------------------------------------------------------

def rnString(measureNumber: int,
             beat: Union[str, int, float, fractions.Fraction],
             chordString: str,
             inString: Optional[str] = ''):
    '''
    Creates or extends a string of RomanText such that the output corresponds to a single
    measure line with one or more pairs of beat to Roman numeral.

    If the inString is not given, None, or an empty string then this function starts a new line.

    >>> lineStarter = romanText.writeRoman.rnString(14, 1, 'G: I')
    >>> lineStarter
    'm14 b1 G: I'

    For any other inString, that string is the start of a measure line continued by the new values

    >>> continuation = romanText.writeRoman.rnString(14, 2, 'viio6', 'm14 b1 G: I')
    >>> continuation
    'm14 b1 G: I b2 viio6'

    As these examples show, the chordString can be a Roman numeral alone (e.g. 'viio6')
    or one prefixed by a change of key ('G: I').

    Naturally then, this method requires the measure number of any such continuation to match
    that of the inString.
    '''

    if inString:
        inStringMeasureNumber = int(inString.split(' ')[0][1:])
        if inStringMeasureNumber != measureNumber:
            msg = f'The current measureNumber is given as {measureNumber}, but '
            msg += f'the contextual inString ({inString}) refers to '
            msg += 'measure number {measureNumber}. They should match.'
            raise ValueError(msg)
    else:  # inString and therefore start new line
        inString = f'm{measureNumber}'

    bt = intBeat(beat)

    newString = f'{inString} b{bt} {chordString}'

    return newString


def intBeat(beat: Union[str, int, float, fractions.Fraction],
            roundValue: int = 2):
    '''
    Converts beats to integers if possible, and otherwise to rounded decimals.
    Accepts input as string, int, float, or fractions.Fraction.

    >>> testInt = romanText.writeRoman.intBeat(1, roundValue=2)
    >>> testInt
    1

    >>> testFrac = romanText.writeRoman.intBeat(8 / 3, roundValue=2)
    >>> testFrac
    2.67

    >>> testStr = romanText.writeRoman.intBeat('0.666666666', roundValue=2)
    >>> testStr
    0.67

    The roundValue sets the number of decimal places to round to. The default is two:

    >>> testRound2 = romanText.writeRoman.intBeat(1.11111111, roundValue=2)
    >>> testRound2
    1.11

    But this can be set to any integer:

    >>> testRound1 = romanText.writeRoman.intBeat(1.11111111, roundValue=1)
    >>> testRound1
    1.1
    '''

    options = (str, int, float, fractions.Fraction)

    if not isinstance(beat, options):
        raise TypeError(f'Beat, (currently {beat}) must be one of {options}.')

    if isinstance(beat, int):
        return beat

    if type(beat) in [str, fractions.Fraction]:
        beat = float(beat)

    # Now beat is definitely a float
    if int(beat) == beat:
        return int(beat)
    else:
        return round(beat, roundValue)


# ------------------------------------------------------------------------------

class Test(unittest.TestCase):
    '''
    Tests for two analysis cases (the smallest rntxt files in the music21 corpus)
    along with two test by modifying those scores.

    Additional tests for the stand alone functions rnString and intBeat and
    error cases for all three.
    '''

    def testTwoCorpusPiecesAndTwoCorruptions(self):

        from music21 import corpus

        scoreBach = corpus.parse('bach/choraleAnalyses/riemenschneider004.rntxt')  # Smallest file

        rnaBach = RnWriter(scoreBach)
        self.assertIn('m10 b1 V6/V b2 V b3 I', rnaBach.combinedList)  # NB b1

        # --------------------

        scoreBach.parts[0].measure(3).insert(0, meter.TimeSignature('10/8'))
        scoreBach.parts[0].measure(3).insert(1, meter.TimeSignature('5/8'))

        wonkyBach = RnWriter(scoreBach)

        tsString1 = 'Time Signature: 10/8'
        tsString2 = 'Note: further time signature change(s) unprocessed: [\'5/8\']'

        self.assertIn(tsString1, wonkyBach.combinedList)
        self.assertIn(tsString2, wonkyBach.combinedList)

        self.assertEqual(wonkyBach.combinedList.index(tsString2),
                         wonkyBach.combinedList.index(tsString1) + 1)

        # --------------------

        scoreMonte = corpus.parse('monteverdi/madrigal.3.8.rntxt')  # Smallest file
        rnMonte = RnWriter(scoreMonte)

        self.assertEqual(rnMonte.composer, 'Monteverdi')
        self.assertEqual(rnMonte.title, 'La piaga c\'ho nel core')
        self.assertEqual(rnMonte.combinedList[-1], 'm57 b1 I')  # NB b1

        # --------------------

        # (Re-)assign metadata in the normal way
        scoreMonte.metadata.title = 'Fake title'
        scoreMonte.metadata.movementNumber = 123456789
        scoreMonte.metadata.movementName = 'Fake movementName'

        adjustedMonte = RnWriter(scoreMonte)
        self.assertEqual(adjustedMonte.title, 'Fake title - No.123456789: Fake movementName')

    def testTypeParses(self):

        s = stream.Score()
        romanText.writeRoman.RnWriter(s)  # Works on a score

        p = stream.Part()
        romanText.writeRoman.RnWriter(p)  # or on a part

        s.insert(p)
        romanText.writeRoman.RnWriter(s)  # or on a score with part

        m = stream.Measure()
        RnWriter(m)  # or on a measure

        rn = roman.RomanNumeral('viio6', 'G')
        RnWriter(rn)  # and even (perhaps dubiously) directly on other music21 objects

# ------------------------------------------------------------------------------

    def testRnString(self):

        test = rnString(1, 1, 'G: I')
        self.assertEqual(test, 'm1 b1 G: I')

        with self.assertRaises(ValueError):  # error when the measure numbers don't match
            rnString(15, 1, 'viio6', 'm14 b1 G: I')

# ------------------------------------------------------------------------------

    def testIntBeat(self):

        testInt = intBeat(1, roundValue=2)
        self.assertEqual(testInt, 1)

        testOneDec = intBeat(1.5, roundValue=2)
        self.assertEqual(testOneDec, 1.5)

        testRound1 = intBeat(1.11111111, roundValue=2)
        self.assertEqual(testRound1, 1.11)

        testRound2 = intBeat(1.11111111, roundValue=1)
        self.assertEqual(testRound2, 1.1)

        testFrac1 = intBeat(8 / 3, roundValue=2)
        self.assertEqual(testFrac1, 2.67)

        testFrac2 = intBeat(fractions.Fraction(8, 3), roundValue=2)
        self.assertEqual(testFrac2, 2.67)

        testStr = intBeat('0.666666666', roundValue=2)
        self.assertEqual(testStr, 0.67)

        with self.assertRaises(TypeError):  # error when called on a list
            intBeat([0, 1, 2])


# ------------------------------------------------------------------------------

if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
