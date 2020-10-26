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

from music21 import exceptions21
from music21 import environment
environLocal = environment.Environment()


# ------------------------------------------------------------------------------

class WriteRomanException(exceptions21.Music21Exception):
    pass


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
                 composer: str = '',
                 title: str = '',
                 analyst: str = '',
                 proofreader: str = '',
                 note: str = ''
                 ):

        self.score = score

        self.romanNumerals = self.score.parts[0].recurse().getElementsByClass('RomanNumeral')
        self.firstMeasureNumber = self.romanNumerals[0].measureNumber
        self.lastMeasureNumber = self.romanNumerals[-1].measureNumber

        self.timeSignatures = []
        self.timeSigMeasureDict = {}
        self.getTSs()

        # Metadata / preamble
        self.composer = composer
        self.title = title
        self.analyst = analyst
        self.proofreader = proofreader
        self.note = note

        self.preamble = []
        self.prepPreamble()

        self.analysisDict = {}
        self.combinedList = []

    def getTSs(self):
        '''
        Retrieve all time signatures from the scores and make a timeSignatures dict where the
        keys are measure numbers for time signature changes and the
        values are time signatures ratioStrings (e.g. '4/4').
        '''

        self.timeSignatures = self.score.parts[0].recurse().getElementsByClass('TimeSignature')
        self.timeSigMeasureDict = {}
        for x in self.timeSignatures:
            self.timeSigMeasureDict[x.measureNumber] = x.ratioString

    def prepPreamble(self):
        '''
        Prepare metadata from user-defined and / or score metadata.
        User defined values take priority (set in the init),
        followed by anything retrievable from the score, and
        placeholders stand in where the information is not given by either source.
        '''

        if self.composer:
            self.preamble.append(f'Composer: {self.composer}')
        else:  # default unless set
            if self.score.metadata.composer:
                self.composer = self.score.metadata.composer  # overwrite
                self.preamble.append(f'Composer: {self.composer}')
            else:
                self.composer = 'Unknown'
                self.preamble.append('Composer: ')

        if self.title:
            self.preamble.append(f'Title: {self.title}')
        else:
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
                self.preamble.append(f'Title: {self.title}')
            else:
                self.title = 'Unknown'
                self.preamble.append('Title: ')

        if not self.analyst:
            self.analyst = 'Unknown'
        self.preamble.append(f'Analyst: {self.analyst}')

        if not self.proofreader:
            self.proofreader = 'Unknown'
        self.preamble.append(f'Proofreader: {self.proofreader}')

        if self.note:  # Blank if none
            self.preamble.append(f'Note: {self.note}')

# ------------------------------------------------------------------------------

    def makeMeasureStrings(self):
        '''
        Takes information from the Roman numerals and
        and converts it into separate rntxt strings to print for each measure
        stored in an dict such that analysisDict[measureNumber] = string
        (corresponding directly to the structure for the time signatures).
        '''

        currentMeasure = -100  # i.e. fake
        currentString = None
        currentKey = ''

        for rn in self.romanNumerals:
            keyString = str(rn.key).split(' ')[0].replace('-', 'b')
            if keyString != currentKey:
                chordString = f'{keyString}: {rn.figure}'
                currentKey = keyString
            else:
                chordString = str(rn.figure)

            if rn.measureNumber == currentMeasure:  # continue an existing string
                currentString = rnString(measure=rn.measureNumber,
                                         beat=rn.beat,
                                         chordString=chordString,
                                         inString=currentString)
            else:
                self.analysisDict[currentMeasure] = currentString  # Save previous string ...
                currentString = rnString(measure=rn.measureNumber,  # ... and start a new one.
                                         beat=rn.beat,
                                         chordString=chordString)
            currentMeasure = rn.measureNumber

        # Special case of last entry.
        self.analysisDict[currentMeasure] = currentString

    def prepList(self):
        '''
        Prepares a sequential list of text lines, integrating the timeSignatures and romanNumerals
        from their respective dicts.
        I.e. this prepares all lines other than the metadata preamble (handled separately)
        '''

        tsMeasures = self.timeSigMeasureDict.keys()

        if not self.analysisDict:
            self.makeMeasureStrings()

        for x in range(self.firstMeasureNumber, self.lastMeasureNumber + 1):

            if x in tsMeasures:  # First, before corresponding measure string
                ts = self.timeSigMeasureDict[x]
                self.combinedList.append(f'\nTime Signature: {ts}')

            if x in self.analysisDict.keys():
                self.combinedList.append(self.analysisDict[x])

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

        if not fileName:  # Never an empty string: placeholders set by prepPreamble as needed.
            fileName = f'{self.composer}_-_{self.title}'
            fileName = fileName.replace('.', '')
            fileName = fileName.replace(':', '')
            fileName = fileName.replace(' ', '_')

        text_file = open(os.path.join(outPath, f'{fileName}.txt'), "w")
        [text_file.write(entry + "\n") for entry in self.preamble]
        text_file.write("\n")  # One extra line to separate metadata preamble from analysis
        [text_file.write(entry + "\n") for entry in self.combinedList]
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
    Accepts input as string, int or float.
    '''

    options = [str, int, float, fractions.Fraction]

    if type(beat) not in options:
        raise ValueError(f'Beat, (currently {beat}) must be one of {options}.')

    if type(beat) in [str, fractions.Fraction]:
        beat = float(beat)

    if int(beat) == beat:
        return int(beat)
    else:
        return round(float(beat), roundValue)


# ------------------------------------------------------------------------------

class Test(unittest.TestCase):
    '''
    Tests for both main analysis cases - one full, one partial - and for a template.
    Additional test for smaller static functions.
    '''

    def testTwoCorpusPieces(self):

        from music21 import corpus

        scoreBach = corpus.parse('bach/choraleAnalyses/riemenschneider001.rntxt',
                                 format='RomanText')
        rnaBach = RnWriter(scoreBach)
        rnaBach.prepList()

        self.assertEqual(rnaBach.combinedList[0], '\nTime Signature: 3/4')
        self.assertEqual(rnaBach.combinedList[15], 'm14 b1 IV b3 I')  # NB m14 due to anacrusis

        monte = corpus.parse('monteverdi/madrigal.3.1.rntxt',
                             format='RomanText')
        monte = RnWriter(monte)
        monte.prepList()

        self.assertEqual(monte.composer, 'Claudio Monteverdi')
        self.assertEqual(monte.title, 'La Giovinetta Pianta')
        self.assertEqual(monte.combinedList[0], '\nTime Signature: 4/4')
        self.assertEqual(monte.combinedList[15], 'm15 b1 I b2 IV6 b3 Bb: ii b4 V')

# ------------------------------------------------------------------------------

    def testRnString(self):
        test = rnString(1, 1, 'G: I')
        self.assertEqual(test, 'm1 b1 G: I')

# ------------------------------------------------------------------------------

    def testIntBeat(self):
        test = intBeat(1, roundValue=2)
        self.assertEqual(test, 1)
        test = intBeat(1.5, roundValue=2)
        self.assertEqual(test, 1.5)
        test = intBeat(1.11111111, roundValue=2)
        self.assertEqual(test, 1.11)
        test = intBeat(8 / 3, roundValue=2)
        self.assertEqual(test, 2.67)


# ------------------------------------------------------------------------------

if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
