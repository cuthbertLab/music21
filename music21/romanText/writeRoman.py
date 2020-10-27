# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         romanText/writeRoman.py
# Purpose:      Writes Roman text files given a music21 stream of Roman numerals
#
# Authors:      Mark Gotham
#
# Copyright:    Copyright © 2020 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
Writes Roman text files given a music21 stream of Roman numerals
'''

import fractions
import os
import unittest


# ------------------------------------------------------------------------------

class RnWriter:
    '''
    Extracts the relevant information from a stream of Roman numeral objects for
    writing to text files in the 'Roman text' format.

    Includes handling of metadata such that entries for composer, title and more
    can be user defined or extracted from score metadata wherever possible.
    '''

    def __init__(self,
                 score,
                 composer: str = 'Composer unknown',
                 title: str = 'Title unknown',
                 analyst: str = '',
                 proofreader: str = '',
                 note: str = ''
                 ):

        self.score = score

        if self.score.parts:
            self.container = self.score.parts[0]
        else:
            self.container = self.score

        self.measureNumbers = [x.measureNumberWithSuffix() for x in
                               self.container.getElementsByClass('Measure')]

        self.composer = composer
        if self.composer == 'Composer unknown':
            if self.score.metadata:
                if self.score.metadata.composer:
                    self.composer = self.score.metadata.composer

        self.title = title
        if self.title == 'Title unknown':
            self._prepTitle()

        self.analyst = analyst  # or self.score.metadata.analyst  # if supported in future

        self.proofreader = proofreader  # or self.score.metadata.proofreader  # "

        self.note = note

        self.fileName = f'{self.composer}_-_{self.title}'
        self.fileName = self.fileName.replace('.', '')
        self.fileName = self.fileName.replace(':', '')
        self.fileName = self.fileName.replace(' ', '_')

        self.combinedList = [f'Composer: {self.composer}',
                             f'Title: {self.title}',
                             f'Analyst: {self.analyst}',
                             f'Proofreader: {self.proofreader}']
        if self.note:  # optional
            self.combinedList.append(f'Note: {self.note}')

        self.currentKey = ''

    def _prepTitle(self):
        '''
        In the absence of a user-defined title,
        attempt to prepare one from the score metadata looking at each of
        the title, movementNumber and movementName attributes.
        Failing that, a placeholder 'Unknown' stands in.
        '''

        if not self.score.metadata:
            return

        workingTitle = []

        if self.score.metadata.title:
            workingTitle.append(self.score.metadata.title)
        if self.score.metadata.movementNumber:
            workingTitle.append(f'- No.{self.score.metadata.movementNumber}:')  # Spaces later
        if self.score.metadata.movementName:
            if self.score.metadata.movementName != self.score.metadata.title:
                workingTitle.append(self.score.metadata.movementName)

        if len(workingTitle) > 0:
            self.title = ' '.join(workingTitle)

# ------------------------------------------------------------------------------

    def prepList(self):
        '''
        Prepares a sequential list of text lines, with timeSignatures and romanNumerals
        adding this to the (already prepared) metadata preamble ready for printing.
        '''

        for m in self.measureNumbers:

            thisMeasure = self.container.measure(m)

            # TimeSignatures
            tsThisMeasure = [t for t in thisMeasure.getElementsByClass('TimeSignature')]
            if tsThisMeasure:
                firstTS = tsThisMeasure[0]
                self.combinedList.append(f'\nTime Signature: {firstTS.ratioString}')
                if len(tsThisMeasure) > 1:
                    msg = 'further time signature change(s) unprocessed: ' \
                          f'{[x.ratioString for x in tsThisMeasure[1:]]}'
                    self.combinedList.append(f'Note: {msg}')

            # RomanNumerals
            measureString = ''  # Clear for each measure
            rnsThisMeasure = [r for r in thisMeasure.getElementsByClass('RomanNumeral')]
            if rnsThisMeasure:  # probably redundant
                for rn in rnsThisMeasure:
                    chordString = self.getChordString(rn)
                    measureString = rnString(measure=m,
                                             beat=rn.beat,
                                             chordString=chordString,
                                             inString=measureString,  # Creating update
                                             )

            self.combinedList.append(measureString)

    def getChordString(self, rn):
        '''
        Produce a string from a Roman number with the chord and
        the key if that key constitutes a change from the foregoing context.
        '''

        keyString = str(rn.key).split(' ')[0].replace('-', 'b')
        if keyString != self.currentKey:
            self.currentKey = keyString
            return f'{keyString}: {rn.figure}'
        else:
            return str(rn.figure)

# ------------------------------------------------------------------------------

    # To write

    def writeRomanText(self,
                       outPath: str = '.',
                       fileName: str = ''):
        '''
        Writes the combined information to a 'Roman text' file (using the extension .txt).
        '''

        if not self.combinedList:
            self.prepList()

        f = fileName or self.fileName
        text_file = open(os.path.join(outPath, f'{f}.txt'), "w")
        for entry in self.combinedList:
            text_file.write(entry + "\n")
        text_file.close()


# ------------------------------------------------------------------------------

# Static functions

def rnString(measure,
             beat,
             chordString: str,
             inString: str = ''):
    '''
    Writes lines of RNTXT.
    To start a new line: inString = None;
    To extend an existing line: set inString to that existing list.
    '''

    if not inString:  # New line
        inString = f'm{measure}'

    bt = intBeat(beat)

    newString = f'{inString} b{bt} {chordString}'

    return newString


def intBeat(beat,
            roundValue: int = 2):
    '''
    Converts beats to integers if possible, and otherwise to rounded decimals.
    Accepts input as string, int, float, or fractions.Fraction.
    '''

    options = [str, int, float, fractions.Fraction]

    if type(beat) not in options:
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
    Tests for both main analysis cases - one full, one partial - and for a template.
    Additional test for smaller static functions.
    '''

    def testTwoCorpusPiecesAndTwoCorruptions(self):

        from music21 import corpus
        from music21 import meter

        scoreBach = corpus.parse('bach/choraleAnalyses/riemenschneider001.rntxt',
                                 format='RomanText')

        rnaBach = RnWriter(scoreBach)
        rnaBach.prepList()

        self.assertEqual(rnaBach.combinedList[0], 'Composer: J. S. Bach')
        self.assertEqual(rnaBach.combinedList[4], '\nTime Signature: 3/4')
        self.assertEqual(rnaBach.combinedList[5], 'm0 b3 G: I')

        # --------------------

        scoreBach.parts[0].measure(3).insert(0, meter.TimeSignature('10/8'))
        scoreBach.parts[0].measure(3).insert(1, meter.TimeSignature('5/8'))

        wonkyBach = RnWriter(scoreBach)
        wonkyBach.prepList()
        self.assertEqual(wonkyBach.combinedList[8], '\nTime Signature: 10/8')
        self.assertEqual(wonkyBach.combinedList[9],
                         'Note: further time signature change(s) unprocessed: [\'5/8\']')

        # --------------------

        fullMonte = corpus.parse('monteverdi/madrigal.3.1.rntxt',
                                 format='RomanText')
        monte = RnWriter(fullMonte)
        monte.prepList()

        self.assertEqual(monte.composer, 'Claudio Monteverdi')
        self.assertEqual(monte.title, 'La Giovinetta Pianta')
        self.assertEqual(monte.combinedList[4], '\nTime Signature: 4/4')
        self.assertEqual(monte.combinedList[5], 'm1 b1 F: vi b4 V[no3]')
        self.assertEqual(monte.combinedList[19], 'm15 b1 I b2 IV6 b3 Bb: ii b4 V')

        # --------------------

        # Now once more with (terrible) user-defined metadata
        monteAltered = RnWriter(fullMonte,
                                composer='Montius Claudeverdi',
                                title='Don Giovanni',
                                analyst='I, Claudius',
                                proofreader='Berg',
                                note='None of this metadata is accurate')
        self.assertEqual(monteAltered.composer, 'Montius Claudeverdi')
        self.assertEqual(monteAltered.title, 'Don Giovanni')
        self.assertEqual(monteAltered.analyst, 'I, Claudius')
        self.assertEqual(monteAltered.proofreader, 'Berg')
        self.assertEqual(monteAltered.note, 'None of this metadata is accurate')

# ------------------------------------------------------------------------------

    def testMinimialCase(self):
        from music21 import stream
        from music21 import metadata

        s = stream.Score()

        hypothetical1 = RnWriter(s)
        self.assertEqual(hypothetical1.composer, 'Composer unknown')
        self.assertEqual(hypothetical1.title, 'Title unknown')

        md = metadata.Metadata(title='Fake title')
        md.movementNumber = 123456789
        md.movementName = 'Fake movementName'
        s.insert(0, md)

        hypothetical2 = RnWriter(s)
        self.assertEqual(hypothetical2.title, 'Fake title - No.123456789: Fake movementName')
        
# ------------------------------------------------------------------------------

    def testRnString(self):
        test = rnString(1, 1, 'G: I')
        self.assertEqual(test, 'm1 b1 G: I')

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

    @unittest.expectedFailure
    def testIntBeatFail(self):
        '''
        Tests that intBeat fails when called on a list.
        '''
        intBeat([0, 1, 2])


# ------------------------------------------------------------------------------

if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
