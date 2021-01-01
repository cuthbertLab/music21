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

from typing import List, Optional, Union

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
    Extracts the relevant information from a source
    (usually a :class:`~music21.stream.Stream` of
    :class:`~music21.roman.RomanNumeral` objects) for
    writing to text files in the 'RomanText' format (rntxt).

    Writing rntxt is handled externally in the
    :meth:`~music21.converter.subConverters.WriteRoman` so
    most users will never need to call this class directly, only invoking
    it indirectly through .write('rntxt').
    Possible exceptions include users who want to convert Roman numerals into rntxt type
    strings and want to work with those strings directly, without writing to disk.

    For consistency with the
    :meth:`~music21.base.Music21Object.show` and :meth:`~music21.base.Music21Object.write`
    methods across music21, this class is theoretically callable on
    any type of music21 object.
    Most relevant use cases will involve calling a
    stream containing one or more Roman numerals.
    This class supports any such stream:
    an :class:`~music21.stream.Opus` object of one or more scores,
    a :class:`~music21.stream.Score` with or without :class:`~music21.stream.Part` (s),
    a :class:`~music21.stream.Part`, or
    a :class:`~music21.stream.Measure`.

    >>> scoreBach = corpus.parse('bach/choraleAnalyses/riemenschneider004.rntxt')
    >>> rnWriterFromScore = romanText.writeRoman.RnWriter(scoreBach)

    The strings are stored in the RnWriter's combinedList variable, starting with the metadata:

    >>> rnWriterFromScore.combinedList[0]
    'Composer: J. S. Bach'

    Composer and work metadata is inherited from score metadata wherever possible.
    A composer entry will register directly as will any entries for
    workTitle, movementNumber, and movementName
    (see :meth:`~music21.romanText.writeRoman.RnWriter.prepTitle` for details).

    >>> rnWriterFromScore.combinedList[0] == 'Composer: ' + rnWriterFromScore.composer
    True

    As always, these metadata entries are user-settable.
    Make any adjustments to the metadata before calling this class.

    After the metadata, the list continues with strings for each measure in order.
    Here's the last in our example:

    >>> rnWriterFromScore.combinedList[-1]
    'm10 V6/V b2 V b3 I'

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
    'm0 a: viio64'

    OMIT_FROM_DOCS

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
    '''

    def __init__(self,
                 obj: base.Music21Object,
                 ):

        self.composer = 'Composer unknown'
        self.title = 'Title unknown'

        if obj.isStream:

            if isinstance(obj, stream.Opus):
                constituentElements = [RnWriter(x) for x in obj]
                self.combinedList = []
                for scoreOrSim in constituentElements:
                    for x in scoreOrSim.combinedList:
                        self.combinedList.append(x)
                    self.combinedList.append('\n')  # one between scores
                return

            elif isinstance(obj, stream.Score):
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
                self._makeContainer(obj)

            if obj.metadata:  # Check the obj (not container) for metadata if obj is a stream
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

        if not self.container.recurse().getElementsByClass('TimeSignature'):
            self.container.insert(0, meter.TimeSignature('4/4'))  # Placeholder

        self.currentKeyString: str = ''
        self.prepSequentialListOfLines()

    def _makeContainer(self,
                       obj: Union[stream.Stream, List]):
        '''
        Makes a placeholder container for the unusual cases where this class is called on
        generic- or non-stream object as opposed to
        a :class:`~music21.stream.Score`, :class:`~music21.stream.Part`,
        or :class:`~music21.stream.Measure`.
        '''
        m = stream.Measure()
        for x in obj:
            m.append(x)
        self.container = stream.Part()
        self.container.insert(0, m)

    def prepTitle(self,
                  md: metadata):
        '''
        Attempt to prepare a single work title from the score metadata looking at each of
        the title, movementNumber and movementName attributes.
        Failing that, a placeholder 'Title unknown' stands in.

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
        'm0 G: V'
        '''

        for thisMeasure in self.container.getElementsByClass('Measure'):
            # TimeSignatures  # TODO KeySignatures
            tsThisMeasure = thisMeasure.getElementsByClass('TimeSignature')
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
                if rn.tie is None or rn.tie.type == 'start':  # Ignore tied to Roman numerals
                    chordString = self.getChordString(rn)
                    measureString = rnString(measureNumber=thisMeasure.measureNumber,  # Suffix?
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
    measure line.

    If the inString is not given, None, or an empty string then this function starts a new line.

    >>> lineStarter = romanText.writeRoman.rnString(14, 1, 'G: I')
    >>> lineStarter
    'm14 G: I'

    For any other inString, that string is the start of a measure line continued by the new values

    >>> continuation = romanText.writeRoman.rnString(14, 2, 'viio6', 'm14 G: I')
    >>> continuation
    'm14 G: I b2 viio6'

    Naturally, this function requires the measure number of any such continuation to match
    that of the inString and raises an error where that is not the case.

    As these examples show, the chordString can be a Roman numeral alone (e.g. 'viio6')
    or one prefixed by a change of key ('G: I').

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
    if bt == 1:
        newString = f'{inString} {chordString}'  # no 'b1' needed for beat 1
    else:
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

    Raises an error if called on a negative value.
    '''

    options = (str, int, float, fractions.Fraction)
    if not isinstance(beat, options):
        raise TypeError(f'Beat, (currently {beat}) must be one of {options}.')

    if type(beat) in [str, fractions.Fraction]:
        beat = float(beat)

    # beat is now either float or int, so we can test < 0
    if beat < 0:
        negativeErrorMessage = f'Beat (currently {beat}) must not be negative.'
        raise ValueError(negativeErrorMessage)

    if isinstance(beat, int):  # non-negative int
        return beat

    # beat is now a non-negative float
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
    for handling the special case of opus objects.
    '''

    def testOpus(self):
        '''
        As the rntxt input parser handles Opus objects
        (i.e. more than one score within the same rntxt files),
        this RnWriter also needs to accept that type.

        This test parses a fake (tiny) Opus file in three (really tiny!) movements.
        Checks ensure that the parsed version is indeed an Opus object and that
        the data is faithfully transferred through that process.

        In practice, Opus handling will bypass this module in the typical case of a simple
        .write() because writing Opus objects explicitly separates them into their constituent
        score files prior to invoking this module.
        '''

        from music21 import converter

        testOpusString = """Composer: Fake composer
        Piece: Fake piece
        Movement: 1
        m1 C: I b3 IV b4 V
        m2 I

        Movement: 2
        m1 G: I
        m3 IV
        m4 V
        m5 I

        Movement: 3
        m1 C: I
        m2 V
        m3 I
        """

        testOpus = converter.parse('romantext: ' + testOpusString)
        self.assertIsInstance(testOpus, stream.Opus)

        testOpusRnWriter = RnWriter(testOpus)
        self.assertIn('Title: Fake piece - No.1:', testOpusRnWriter.combinedList)
        self.assertIn('Title: Fake piece - No.2:', testOpusRnWriter.combinedList)
        self.assertIn('Title: Fake piece - No.3:', testOpusRnWriter.combinedList)
        self.assertIn('m2 I', testOpusRnWriter.combinedList)  # mvt 1
        self.assertIn('m5 I', testOpusRnWriter.combinedList)  # mvt 2
        self.assertIn('m3 I', testOpusRnWriter.combinedList)  # mvt 3

    def testTwoCorpusPiecesAndTwoCorruptions(self):
        '''
        Tests for two analysis cases (the smallest rntxt files in the music21 corpus)
        along with two test by modifying those scores.
        '''

        from music21 import corpus

        scoreBach = corpus.parse('bach/choraleAnalyses/riemenschneider004.rntxt')  # Smallest file

        rnaBach = RnWriter(scoreBach)
        self.assertIn('m10 V6/V b2 V b3 I', rnaBach.combinedList)

        # --------------------

        scoreBach.parts[0].measure(3).insert(0, meter.TimeSignature('10/8'))
        scoreBach.parts[0].measure(3).insert(1, meter.TimeSignature('5/8'))

        wonkyBach = RnWriter(scoreBach)

        tsString1 = 'Time Signature: 10/8'
        tsString2 = "Note: further time signature change(s) unprocessed: ['5/8']"

        self.assertIn(tsString1, wonkyBach.combinedList)
        self.assertIn(tsString2, wonkyBach.combinedList)

        self.assertEqual(wonkyBach.combinedList.index(tsString2),
                         wonkyBach.combinedList.index(tsString1) + 1)

        # --------------------

        scoreMonte = corpus.parse('monteverdi/madrigal.3.8.rntxt')  # Smallest file
        rnMonte = RnWriter(scoreMonte)

        self.assertEqual(rnMonte.composer, 'Monteverdi')
        self.assertEqual(rnMonte.title, "La piaga c'ho nel core")
        self.assertEqual(rnMonte.combinedList[-1], 'm57 I')

        # --------------------

        # (Re-)assign metadata in the normal way
        scoreMonte.metadata.title = 'Fake title'
        scoreMonte.metadata.movementNumber = 123456789
        scoreMonte.metadata.movementName = 'Fake movementName'

        adjustedMonte = RnWriter(scoreMonte)
        self.assertEqual(adjustedMonte.title, 'Fake title - No.123456789: Fake movementName')

    def testTypeParses(self):
        '''
        Tests successful init on a range of supported objects (score, part, even RomanNumeral).
        '''

        s = stream.Score()
        romanText.writeRoman.RnWriter(s)  # Works on a score

        p = stream.Part()
        romanText.writeRoman.RnWriter(p)  # or on a part

        s.insert(p)
        romanText.writeRoman.RnWriter(s)  # or on a score with part

        m = stream.Measure()
        RnWriter(m)  # or on a measure

        v = stream.Voice()
        # or theoretically on a voice, but will be empty for lack of measures
        emptyWriter = RnWriter(v)
        self.assertEqual(emptyWriter.combinedList, [
            'Composer: Composer unknown',
            'Title: Title unknown',
            'Analyst: ',
            'Proofreader: ',
            '',
        ])

        rn = roman.RomanNumeral('viio6', 'G')
        RnWriter(rn)  # and even (perhaps dubiously) directly on other music21 objects

# ------------------------------------------------------------------------------

    def testRnString(self):

        test = rnString(1, 1, 'G: I')
        self.assertEqual(test, 'm1 G: I')  # no beat number given for b1

        test = rnString(0, 4, 'b: V')
        self.assertEqual(test, 'm0 b4 b: V')  # beat number given for all other cases

        with self.assertRaises(ValueError):  # error when the measure numbers don't match
            rnString(15, 1, 'viio6', 'm14 G: I')

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

        with self.assertRaises(TypeError):  # TypeError when called on an unsupported object
            intBeat([0, 1, 2])

        with self.assertRaises(ValueError):  # ValueError when called on a negative number
            intBeat(-1.5)


# ------------------------------------------------------------------------------

if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
