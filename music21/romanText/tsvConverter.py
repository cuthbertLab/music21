# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         romanText/tsvConverter.py
# Purpose:      Converter for the DCMLab's tabular format for representing harmonic analysis.
#
# Authors:      Mark Gotham
#
# Copyright:    Copyright © 2019 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
Converter for parsing the tabular representations of harmonic analysis such as the
DCMLab's Annotated Beethoven Corpus (Neuwirth et al. 2018).
'''

import csv
import unittest

from music21 import common
from music21 import key
from music21 import metadata
from music21 import meter
from music21 import note
from music21 import roman
from music21 import stream

from music21 import exceptions21

from music21 import environment
environLocal = environment.Environment()

# ------------------------------------------------------------------------------


class TsvException(exceptions21.Music21Exception):
    pass

# ------------------------------------------------------------------------------


class TabChord:
    '''
    An intermediate representation format for moving between tabular data and music21 chords.
    '''
    def __init__(self):
        self.combinedChord = None  # 'chord' in ABC original, otherwise names the same
        self.altchord = None
        self.measure = None
        self.beat = None
        self.totbeat = None
        self.timesig = None
        self.op = None
        self.no = None
        self.mov = None
        self.length = None
        self.global_key = None
        self.local_key = None
        self.pedal = None
        self.numeral = None
        self.form = None
        self.figbass = None
        self.changes = None
        self.relativeroot = None
        self.phraseend = None
        self.representationType = None  # Added (not in DCML)

    def _changeRepresentation(self):
        '''
        Converts the representation type of a TabChord between the music21 and DCML conventions,
        especially for the different handling of expectations in minor.

        First, let's set up a TabChord().

        >>> tabCd = romanText.tsvConverter.TabChord()
        >>> tabCd.global_key = 'F'
        >>> tabCd.local_key = 'vi'
        >>> tabCd.numeral = '#vii'
        >>> tabCd.representationType = 'DCML'

        There's no change for a major-key context, but for a minor-key context
        (given here by 'relativeroot') the 7th degree is handled differently.

        >>> tabCd.relativeroot = 'v'
        >>> tabCd.representationType
        'DCML'

        >>> tabCd.numeral
        '#vii'

        >>> tabCd._changeRepresentation()
        >>> tabCd.representationType
        'm21'

        >>> tabCd.numeral
        'vii'
        '''

        if self.representationType == 'm21':
            direction = 'm21-DCML'
            self.representationType = 'DCML'  # Becomes the case during this function.

        elif self.representationType == 'DCML':
            direction = 'DCML-m21'
            self.representationType = 'm21'  # Becomes the case during this function.

        else:
            raise ValueError("Data source must specify representation type as 'm21' or 'DCML'.")

        self.local_key = characterSwaps(self.local_key,
                                        minor=is_minor(self.global_key),
                                        direction=direction)

        # Local - relative and figure
        if is_minor(self.local_key):
            if self.relativeroot:  # If there's a relative root ...
                if is_minor(self.relativeroot):  # ... and it's minor too, change it and the figure
                    self.relativeroot = characterSwaps(self.relativeroot,
                                                        minor=True,
                                                        direction=direction)
                    self.numeral = characterSwaps(self.numeral,
                                                        minor=True,
                                                        direction=direction)
                else:  # ... rel. root but not minor
                    self.relativeroot = characterSwaps(self.relativeroot,
                                                        minor=False,
                                                        direction=direction)
            else:  # No relative root
                self.numeral = characterSwaps(self.numeral,
                                                minor=True,
                                                direction=direction)
        else:  # local key not minor
            if self.relativeroot:  # if there's a relativeroot ...
                if is_minor(self.relativeroot):  # ... and it's minor, change it and the figure
                    self.relativeroot = characterSwaps(self.relativeroot,
                                                        minor=False,
                                                        direction=direction)
                    self.numeral = characterSwaps(self.numeral,
                                                    minor=True,
                                                    direction=direction)
                else:  # ... rel. root but not minor
                    self.relativeroot = characterSwaps(self.relativeroot,
                                                        minor=False,
                                                        direction=direction)
            else:  # No relative root
                self.numeral = characterSwaps(self.numeral,
                                                minor=False,
                                                direction=direction)

    def tabToM21(self):
        '''
        Creates and returns a music21.roman.RomanNumeral() object
        from a TabChord with all shared attributes.
        NB: call changeRepresentation() first if .representationType is not 'm21'
        but you plan to process it with m21 (e.g. moving it into a stream).

        >>> tabCd = romanText.tsvConverter.TabChord()
        >>> tabCd.numeral = 'vii'
        >>> tabCd.global_key = 'F'
        >>> tabCd.local_key = 'V'
        >>> tabCd.representationType = 'm21'
        >>> m21Ch = tabCd.tabToM21()

        Now we can check it's a music21 RomanNumeral():

        >>> m21Ch.figure
        'vii'
        '''

        if self.numeral:
            if self.form:
                if self.figbass:
                    combined = ''.join([self.numeral, self.form, self.figbass])
                else:
                    combined = ''.join([self.numeral, self.form])
            else:
                combined = self.numeral

            if self.relativeroot:  # special case requiring '/'.
                combined = ''.join([combined, '/', self.relativeroot])

            localKeyNonRoman = getLocalKey(self.local_key, self.global_key)

            thisEntry = roman.RomanNumeral(combined, localKeyNonRoman)
            thisEntry.quarterLength = self.length

            thisEntry.op = self.op
            thisEntry.no = self.no
            thisEntry.mov = self.mov

            thisEntry.pedal = self.pedal

            thisEntry.phraseend = None

        else:  # handling case of '@none'
            thisEntry = note.Rest()
            thisEntry.quarterLength = self.length

        return thisEntry

# ------------------------------------------------------------------------------


def makeTabChord(row):
    '''
    Makes a TabChord out of a list imported from TSV data
    (a row of the original tabular format -- see TsvHandler.importTsv()).

    This is how to make the TabChord:

    >>> tabRowAsString1 = ['.C.I6', '', '1', '1.0', '1.0', '2/4', '1', '2', '3', '2.0',
    ...                                        'C', 'I', '', 'I', '', '', '', '', 'false']
    >>> testTabChord1 = romanText.tsvConverter.makeTabChord(tabRowAsString1)

    And now let's check that it really is a TabChord:

    >>> testTabChord1.numeral
    'I'
    '''

    thisEntry = TabChord()

    thisEntry.combinedChord = str(row[0])
    thisEntry.altchord = str(row[1])
    thisEntry.measure = int(row[2])
    thisEntry.beat = float(row[3])
    thisEntry.totbeat = float(row[4])
    thisEntry.timesig = row[5]
    thisEntry.op = row[6]
    thisEntry.no = row[7]
    thisEntry.mov = row[8]
    thisEntry.length = float(row[9])
    thisEntry.global_key = str(row[10])
    thisEntry.local_key = str(row[11])
    thisEntry.pedal = str(row[12])
    thisEntry.numeral = str(row[13])
    thisEntry.form = str(row[14])
    thisEntry.figbass = str(row[15])
    thisEntry.changes = str(row[16])
    thisEntry.relativeroot = str(row[17])
    thisEntry.phraseend = str(row[18])
    thisEntry.representationType = 'DCML'  # Added

    return thisEntry

# ------------------------------------------------------------------------------


class TsvHandler:
    '''
    Conversion starting with a TSV file.

    First we need to get a score. (Don't worry about this bit.)

    >>> name = 'tsvEg.tsv'
    >>> path = common.getSourceFilePath() / 'romanText' / name
    >>> handler = romanText.tsvConverter.TsvHandler(path)
    >>> handler.tsvToChords()

    These should be TabChords now.

    >>> testTabChord1 = handler.chordList[0]
    >>> testTabChord1.combinedChord
    '.C.I6'

    Good. We can make them into music21 Roman-numerals.

    >>> m21Chord1 = testTabChord1.tabToM21()
    >>> m21Chord1.figure
    'I'

    And for our last trick, we can put the whole lot in a music21 stream.

    >>> out_stream = handler.toM21Stream()
    >>> out_stream.parts[0].measure(1)[0].figure
    'I'

    '''

    def __init__(self, tsvFile):
        self.tsvFileName = tsvFile
        self.tsvData = self.importTsv()
        self.chordList = []
        self.m21stream = None
        self.preparedStream = None

    def importTsv(self):
        '''
        Imports TSV file data for further processing.

        See docs at :class:`music.romanText.TsvHandler`.
        '''

        fileName = self.tsvFileName

        with open(fileName, 'r') as f:
            data = []
            for row_num, line in enumerate(f):
                if row_num == 0:  # Ignore first row (headers)
                    continue
                values = line.strip().split('\t')
                data.append([v.strip('\"') for v in values])
        f.close()

        return data

    def tsvToChords(self):
        '''
        Converts a list of lists (of the type imported by importTsv)
        into TabChords (i.e. a list of TabChords).

        See docs at :class:`music.romanText.TsvHandler`.
        '''

        data = self.tsvData

        chordList = []

        for entry in data:
            thisEntry = makeTabChord(entry)
            if thisEntry is None:
                continue
            else:
                chordList.append(thisEntry)

        self.chordList = chordList

    def toM21Stream(self):
        '''
        Takes a list of TabChords (self.chordList, prepared by .tsvToChords()),
        converts those TabChords in RomanNumerals
        (converting to the music21 representation format as necessary),
        creates a suitable music21 stream (by running .prepStream() using data from the TabChords),
        and populates that stream with the new RomanNumerals.

        See docs at :class:`music.romanText.TsvHandler`.
        '''

        self.prepStream()

        s = self.preparedStream
        p = s.parts[0]  # Just to get to the part, not that there are several.

        for thisChord in self.chordList:
            offsetInMeasure = thisChord.beat - 1  # beats always measured in quarter notes
            measureNumber = thisChord.measure

            if thisChord.representationType == 'DCML':
                thisChord._changeRepresentation()

            thisM21Chord = thisChord.tabToM21()  # In either case.

            p.measure(measureNumber).insert(offsetInMeasure, thisM21Chord)

        self.m21stream = s

        return s

    def prepStream(self):
        '''
        Prepares a music21 stream for the harmonic analysis to go into.
        Specifically: creates the score, part, and measure streams,
        as well as some (the available) metadata based on the original TSV data.
        Works like the .template() method,
        except that we don't have a score to base the template on as such.

        See docs at :class:`music.romanText.TsvHandler`.
        '''

        s = stream.Score()
        p = stream.Part()

        s.insert(0, metadata.Metadata())

        firstEntry = self.chordList[0]  # Any entry will do
        s.metadata.opusNumber = firstEntry.op
        s.metadata.number = firstEntry.no
        s.metadata.movementNumber = firstEntry.mov
        s.metadata.title = 'Op' + firstEntry.op + '_No' + firstEntry.no + '_Mov' + firstEntry.mov

        startingKeySig = str(self.chordList[0].global_key)
        ks = key.Key(startingKeySig)
        p.insert(0, ks)

        currentTimeSig = str(self.chordList[0].timesig)
        ts = meter.TimeSignature(currentTimeSig)
        p.insert(0, ts)

        currentMeasureLength = ts.barDuration.quarterLength

        currentOffset = 0

        previousMeasure = self.chordList[0].measure - 1  # Covers pickups
        for entry in self.chordList:
            if entry.measure == previousMeasure:
                continue
            elif entry.measure != previousMeasure + 1:  # Not every measure has a chord change.
                for mNo in range(previousMeasure + 1, entry.measure):
                    m = stream.Measure(number=mNo)
                    m.offset = currentOffset + currentMeasureLength
                    p.insert(m)

                    currentOffset = m.offset
                    previousMeasure = mNo
            else:  # entry.measure = previousMeasure + 1
                m = stream.Measure(number=entry.measure)
                m.offset = entry.totbeat
                p.insert(m)
                if entry.timesig != currentTimeSig:
                    newTS = meter.TimeSignature(entry.timesig)
                    m.insert(entry.beat - 1, newTS)

                    currentTimeSig = entry.timesig
                    currentMeasureLength = newTS.barDuration.quarterLength

                previousMeasure = entry.measure
                currentOffset = entry.totbeat

        s.append(p)

        self.preparedStream = s

        return s


# ------------------------------------------------------------------------------
class M21toTSV:
    '''
    Conversion starting with a music21 stream.
    Exports to tabular data format and (optionally) writes the file.

    >>> bachHarmony = corpus.parse('bach/choraleAnalyses/riemenschneider001.rntxt')
    >>> bachHarmony.parts[0].measure(1)[0].figure
    'I'

    The initialisation includes the preparation of a list of lists, so

    >>> initial = romanText.tsvConverter.M21toTSV(bachHarmony)
    >>> tsvData = initial.tsvData
    >>> tsvData[1][0]
    'I'
    '''

    def __init__(self, m21Stream):
        self.m21Stream = m21Stream
        self.tsvData = self.m21ToTsv()

    def m21ToTsv(self):
        '''
        Converts a list of music21 chords to a list of lists
        which can then be written to a tsv file with toTsv(), or processed another way.

        See docs at :class:`music.romanText.M21toTSV`.
        '''

        tsvData = []

        for thisRN in self.m21Stream.recurse().getElementsByClass('RomanNumeral'):

            relativeroot = None
            if thisRN.secondaryRomanNumeral:
                relativeroot = thisRN.secondaryRomanNumeral.figure

            altChord = None
            if thisRN.secondaryRomanNumeral:
                if thisRN.secondaryRomanNumeral.key == thisRN.key:
                    altChord = thisRN.secondaryRomanNumeral.figure

            thisEntry = TabChord()

            thisEntry.combinedChord = thisRN.figure  # NB: slightly different from DCML: no key.
            thisEntry.altchord = altChord
            thisEntry.measure = thisRN.measureNumber
            thisEntry.beat = thisRN.beat
            thisEntry.totbeat = None
            thisEntry.timesig = thisRN.getContextByClass('TimeSignature').ratioString
            thisEntry.op = self.m21Stream.metadata.opusNumber
            thisEntry.no = self.m21Stream.metadata.number
            thisEntry.mov = self.m21Stream.metadata.movementNumber
            thisEntry.length = thisRN.quarterLength
            thisEntry.global_key = None
            thisEntry.local_key = thisRN.key
            thisEntry.pedal = None
            thisEntry.numeral = thisRN.romanNumeralAlone
            thisEntry.form = None
            thisEntry.figbass = thisRN.figuresWritten
            thisEntry.changes = None  # TODO
            thisEntry.relativeroot = relativeroot
            thisEntry.phraseend = None

            thisInfo = [thisEntry.combinedChord,
                        thisEntry.altchord,
                        thisEntry.measure,
                        thisEntry.beat,
                        thisEntry.totbeat,
                        thisEntry.timesig,
                        thisEntry.op,
                        thisEntry.no,
                        thisEntry.mov,
                        thisEntry.length,
                        thisEntry.global_key,
                        thisEntry.local_key,
                        thisEntry.pedal,
                        thisEntry.numeral,
                        thisEntry.form,
                        thisEntry.figbass,
                        thisEntry.changes,
                        thisEntry.relativeroot,
                        thisEntry.phraseend
                        ]

            tsvData.append(thisInfo)

        return tsvData

    def write(self, filePathAndName):
        '''
        Writes a list of lists (e.g. from m21ToTsv()) to a tsv file.
        '''
        with open(filePathAndName, 'a') as csvFile:
            csvOut = csv.writer(csvFile,
                                delimiter='\t',
                                quotechar='"',
                                quoting=csv.QUOTE_MINIMAL)

            headers = (
                'chord',
                'altchord',
                'measure',
                'beat',
                'totbeat',
                'timesig',
                'op',
                'no',
                'mov',
                'length',
                'global_key',
                'local_key',
                'pedal',
                'numeral',
                'form',
                'figbass',
                'changes',
                'relativeroot',
                'phraseend',
            )

            csvOut.writerow(headers)

            for thisEntry in self.tsvData:
                csvOut.writerow(thisEntry)

# ------------------------------------------------------------------------------
def is_minor(test_key):
    '''
    Checks whether a key is minor or not simply by upper vs lower case.

    >>> romanText.tsvConverter.is_minor('F')
    False

    >>> romanText.tsvConverter.is_minor('f')
    True
    '''
    return test_key == test_key.lower()


def characterSwaps(preString, minor=True, direction='m21-DCML'):
    '''
    Character swap function to coordinate between the two notational versions, for instance
    swapping between '%' and '/o' for the notation of half diminished (for example).

    >>> testStr = 'ii%'
    >>> romanText.tsvConverter.characterSwaps(testStr, minor=False, direction='DCML-m21')
    'iiø'

    In the case of minor key, additional swaps for the different default 7th degrees:
    - raised in m21 (natural minor)
    - not raised in DCML (melodic minor)

    >>> testStr1 = '.f.vii'
    >>> romanText.tsvConverter.characterSwaps(testStr1, minor=True, direction='m21-DCML')
    '.f.#vii'

    >>> testStr2 = '.f.#vii'
    >>> romanText.tsvConverter.characterSwaps(testStr2, minor=True, direction='DCML-m21')
    '.f.vii'
    '''
    search = ''
    insert = ''
    if direction == 'm21-DCML':
        characterDict = {'/o': '%',
                         'ø': '%',
                         }
    elif direction == 'DCML-m21':
        characterDict = {'%': 'ø',  # Preferred over '/o'
                         'M7': '7',  # 7th types not specified in m21
                         }
    else:
        raise ValueError("Direction must be 'm21-DCML' or 'DCML-m21'.")

    for thisKey in characterDict:  # Both major and minor
        preString = preString.replace(thisKey, characterDict[thisKey])

    if not minor:
        return preString
    else:
        if direction == 'm21-DCML':
            search = 'b'
            insert = '#'
        elif direction == 'DCML-m21':
            search = '#'
            insert = 'b'

        if 'vii' in preString.lower():
            position = preString.lower().index('vii')
            prevChar = preString[position - 1]  # the previous character,  # / b.
            if prevChar == search:
                postString = preString[:position - 1] + preString[position:]
            else:
                postString = preString[:position] + insert + preString[position:]
        else:
            postString = preString

    return postString


def getLocalKey(local_key, global_key, convertDCMLToM21=False):
    '''
    Re-casts comparative local key (e.g. 'V of G major') in its own terms ('D').

    >>> romanText.tsvConverter.getLocalKey('V', 'G')
    'D'

    >>> romanText.tsvConverter.getLocalKey('ii', 'C')
    'd'

    By default, assumes an m21 input, and operates as such:

    >>> romanText.tsvConverter.getLocalKey('vii', 'a')
    'g#'

    Set convert=True to convert from DCML to m21 formats. Hence;

    >>> romanText.tsvConverter.getLocalKey('vii', 'a', convertDCMLToM21=True)
    'g'
    '''
    if convertDCMLToM21:
        local_key = characterSwaps(local_key, minor=is_minor(global_key[0]), direction='DCML-m21')

    asRoman = roman.RomanNumeral(local_key, global_key)
    rt = asRoman.root().name
    if asRoman.isMajorTriad():
        newKey = rt.upper()
    elif asRoman.isMinorTriad():
        newKey = rt.lower()
    else:  # pragma: no cover
        raise ValueError('local key must be major or minor')

    return newKey


def getSecondaryKey(rn, local_key):
    '''
    Separates comparative Roman-numeral for tonicisiations like 'V/vi' into the component parts of
    a Roman-numeral (V) and
    a (very) local key (vi)
    and expresses that very local key in relation to the local key also called (DCML column 11).

    While .getLocalKey() work on the figure and key pair:

    >>> romanText.tsvConverter.getLocalKey('vi', 'C')
    'a'

    With .getSecondaryKey(), we're interested in the relative root of a secondaryRomanNumeral:

    >>> romanText.tsvConverter.getSecondaryKey('V/vi', 'C')
    'a'
    '''
    if '/' not in rn:
        very_local_as_key = local_key
    else:
        position = rn.index('/')
        very_local_as_roman = rn[position + 1:]
        very_local_as_key = getLocalKey(very_local_as_roman, local_key)

    return very_local_as_key

# ------------------------------------------------------------------------------


class Test(unittest.TestCase):

    def testTsvHandler(self):
        name = 'tsvEg.tsv'
        # A short and improbably complicated test case complete with:
        # '@none' (rest entry), '/' relative root, and time signature changes.
        path = common.getSourceFilePath() / 'romanText' / name

        handler = TsvHandler(path)

        # Raw
        self.assertEqual(handler.tsvData[0][0], '.C.I6')
        self.assertEqual(handler.tsvData[1][0], '#viio6/ii')

        # Chords
        handler.tsvToChords()
        testTabChord1 = handler.chordList[0]  # Also tests makeTabChord()
        testTabChord2 = handler.chordList[1]
        self.assertIsInstance(testTabChord1, TabChord)
        self.assertEqual(testTabChord1.combinedChord, '.C.I6')
        self.assertEqual(testTabChord1.numeral, 'I')
        self.assertEqual(testTabChord2.combinedChord, '#viio6/ii')
        self.assertEqual(testTabChord2.numeral, '#vii')

        # Change Representation
        self.assertEqual(testTabChord1.representationType, 'DCML')
        testTabChord1._changeRepresentation()
        self.assertEqual(testTabChord1.numeral, 'I')
        testTabChord2._changeRepresentation()
        self.assertEqual(testTabChord2.numeral, 'vii')

        # M21 RNs
        m21Chord1 = testTabChord1.tabToM21()
        m21Chord2 = testTabChord2.tabToM21()
        self.assertEqual(m21Chord1.figure, 'I')
        self.assertEqual(m21Chord2.figure, 'viio6/ii')
        self.assertEqual(m21Chord1.key.name, 'C major')
        self.assertEqual(m21Chord2.key.name, 'C major')

        # M21 stream
        out_stream = handler.toM21Stream()
        self.assertEqual(out_stream.parts[0].measure(1)[0].figure, 'I')  # First item in measure 1

    def testM21ToTsv(self):
        from music21 import corpus

        bachHarmony = corpus.parse('bach/choraleAnalyses/riemenschneider001.rntxt')
        initial = M21toTSV(bachHarmony)
        tsvData = initial.tsvData
        self.assertEqual(bachHarmony.parts[0].measure(1)[0].figure, 'I')  # NB pickup measure 0.
        self.assertEqual(tsvData[1][0], 'I')

        # Test .write
        envLocal = environment.Environment()
        tempF = envLocal.getTempFile()
        from os import path
        path = path.split(tempF)[0]
        newFileName = 'TestTsvFile'
        initial.write(path + newFileName)
        handler = TsvHandler(path + newFileName)
        self.assertEqual(handler.tsvData[0][0], 'I')

    def testIsMinor(self):
        self.assertTrue(is_minor('f'))
        self.assertFalse(is_minor('F'))

    def testOfCharacter(self):
        startText = 'before%after'
        newText = ''.join([characterSwaps(x, direction='DCML-m21') for x in startText])

        self.assertIsInstance(startText, str)
        self.assertIsInstance(newText, str)
        self.assertEqual(len(startText), len(newText))
        self.assertEqual(startText, 'before%after')
        # noinspection SpellCheckingInspection
        self.assertEqual(newText, 'beforeøafter')

        testStr1in = 'ii%'
        testStr1out = characterSwaps(testStr1in, minor=False, direction='DCML-m21')

        self.assertEqual(testStr1in, 'ii%')
        self.assertEqual(testStr1out, 'iiø')

        testStr2in = 'vii'
        testStr2out = characterSwaps(testStr2in, minor=True, direction='m21-DCML')

        self.assertEqual(testStr2in, 'vii')
        self.assertEqual(testStr2out, '#vii')

        testStr3in = '#vii'
        testStr3out = characterSwaps(testStr3in, minor=True, direction='DCML-m21')

        self.assertEqual(testStr3in, '#vii')
        self.assertEqual(testStr3out, 'vii')

    def testGetLocalKey(self):
        test1 = getLocalKey('V', 'G')
        self.assertEqual(test1, 'D')

        test2 = getLocalKey('ii', 'C')
        self.assertEqual(test2, 'd')

        test3 = getLocalKey('vii', 'a')
        self.assertEqual(test3, 'g#')

        test4 = getLocalKey('vii', 'a', convertDCMLToM21=True)
        self.assertEqual(test4, 'g')

    def testGetSecondaryKey(self):
        testRN = 'V/vi'
        testLocalKey = 'D'

        veryLocalKey = getSecondaryKey(testRN, testLocalKey)

        self.assertIsInstance(veryLocalKey, str)
        self.assertEqual(veryLocalKey, 'b')

# ------------------------------------------------------------------------------


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
