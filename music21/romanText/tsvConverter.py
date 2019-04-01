# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         romanText/tsvConverter.py
# Purpose:      Convertor for the DCMLab's tabular format for representing harmonic analysis.
#
# Authors:      Mark Gotham
#
# Copyright:    Copyright © 2019 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
# ------------------------------------------------------------------------------
'''
Convertor for parsing the tabular representations of harmonic analysis such as the
DCML lab's Annotated Beethoven Corpus (Neuwirth et al. 2018).
'''

import csv
import unittest

from music21 import common
from music21 import key
from music21 import metadata
from music21 import meter
from music21 import note
from music21 import pitch
from music21 import chord
from music21 import roman
from music21 import stream

from music21 import exceptions21

from music21 import environment
environLocal = environment.Environment()

#------------------------------------------------------------------------------

class TsvException(exceptions21.Music21Exception):
    pass

#------------------------------------------------------------------------------

class TabChord:
    __attrs__= ('combinedChord',  # 'chord' in DCML's ABC, otherwise names the same
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
                'representationType',  # Added (not in DCML)
                )

    def attrs(self):
        "Return attrs in a dict"
        return [(field_name, getattr(self, field_name))
                for field_name in self.__attrs__]

    def __iter__(self):
        for field_name in self.__attrs__:
            yield getattr(self, field_name)

    def __getitem__(self, index):
        "getitem by tuple-style index"
        return getattr(self, self.__slots__[index])

    def changeRepresentation(self):
        '''
        Converts the representation type of a TabChord between the music21 and DCML conventions.
        '''

        if self.representationType == 'm21':
            direction = 'm21-DCML'
            self.representationType = 'DCML'  # Becomes the case during this function.

        elif self.representationType == 'DCML':
            direction = 'DCML-m21'
            self.representationType = 'm21'  # Becomes the case during this function.

        else:
            raise ValueError("Data source must specify representation type as 'm21' or 'DCML'.")

        self.local_key = characterSwaps(self.local_key, minor=is_minor(self.global_key), direction=direction)

        # Local - relative and figure
        if is_minor(self.local_key):
            if self.relativeroot:  # If there's a relative root ...
                if is_minor(self.relativeroot):  # ... and it's minor too, change it and the figure
                    self.relativeroot = characterSwaps(self.relativeroot, minor=True, direction=direction)
                    self.numeral = characterSwaps(self.numeral, minor=True, direction=direction)
                else:  # ... rel. root but not minor
                    self.relativeroot = characterSwaps(self.relativeroot, minor=False, direction=direction)
            else:  # No relative root
                self.numeral = characterSwaps(self.numeral, minor=True, direction=direction)
        else:  # local key not minor
            if self.relativeroot:  # if there's a relativeroot ...
                if is_minor(self.relativeroot):  # ... and it's minor, change it and the figure
                    self.relativeroot = characterSwaps(self.relativeroot, minor=False, direction=direction)
                    self.numeral = characterSwaps(self.numeral, minor=True, direction=direction)
                else:  # ... rel. root but not minor
                    self.relativeroot = characterSwaps(self.relativeroot, minor=False, direction=direction)
            else:  # No relative root
                self.numeral = characterSwaps(self.numeral, minor=False, direction=direction)

    def tabToM21(self):
        '''
        Creates a music21.roman.RomanNumeral() object from a TabChord with all shared attributes.
        NB: call changeRepresentation() first if moving into a music21 stream.
        '''

        if self.numeral:
            combined = ''.join([self.numeral, self.form, self.figbass])

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

#------------------------------------------------------------------------------

class TsvHandler:
    '''
    Conversion starting with a TSV file.
    '''

    def __init__(self, tsvFile):
        self.tsvFileName = tsvFile
        self.tsvData = self.importTsv()
        self.chordList = []

    def importTsv(self):
        '''
        Imports TSV file data for further processing.
        '''

        fileName = self.tsvFileName

        try:
            f = open(fileName, 'r')
            data = []
            for row_num, line in enumerate(f):
                values = line.strip().split('\t')
                if row_num != 0:  # Ignore first row (headers)
                    data.append([v.strip('\"') for v in values])
            f.close()

            return data

        except FileNotFoundError:
            raise TsvException('Cannot find file: %s' % fileName)
        except Exception:
            raise TsvException(
                'Invalid File Format; must be a .tsv file: %s' % fileName)

    def tsvToChords(self, convert=False):
        '''
        Converts tsvData (i.e. list of lists) to TabChords (i.e. list of TabChords).
        '''

        data = self.tsvData

        chordList = []

        for entry in data:
            thisEntry = self.makeTabChord(entry, convert=convert)
            if thisEntry is None:
                continue
            else:
                chordList.append(thisEntry)

        self.chordList = chordList

    def makeTabChord(self, rawData, convert=False):
        '''
        Makes a TabChord out of a row of raw TSV data.
        Optionally, converts those TabChords into the music21 representation style
        by swapping equivalent text representations for the same Roman Numeral.
        '''

        thisEntry = TabChord()

        thisEntry.combinedChord = str(rawData[0])
        thisEntry.altchord = str(rawData[1])
        thisEntry.measure = int(rawData[2])
        thisEntry.beat = float(rawData[3])
        thisEntry.totbeat = float(rawData[4])
        thisEntry.timesig = rawData[5]
        thisEntry.op = rawData[6]
        thisEntry.no = rawData[7]
        thisEntry.mov = rawData[8]
        thisEntry.length = float(rawData[9])
        thisEntry.global_key = str(rawData[10])
        thisEntry.local_key = str(rawData[11])
        thisEntry.pedal = str(rawData[12])
        thisEntry.numeral = str(rawData[13])
        thisEntry.form = str(rawData[14])
        thisEntry.figbass = str(rawData[15])
        thisEntry.changes = str(rawData[16])
        thisEntry.relativeroot = str(rawData[17])
        thisEntry.phraseend = str(rawData[18])
        # Added:
        thisEntry.representationType = 'DCML'

        if convert:
            return thisEntry.changeRepresentation()
        else:
            return thisEntry

    def toM21Stream(self):
        '''
        Creates a music21 stream with data from a list of TabChords
        via music21.roman.RomanNumerals,
        converting to the music21 representation format as necessary.
        '''

        self.prepStream()

        s = self.prepdStream
        p = s.parts[0] # Just to get to the part, not that there are several.

        for thisChord in self.chordList:
            offsetInMeasure = thisChord.beat - 1
            measure = thisChord.measure

            if thisChord.representationType == 'DCML':
                thisChord.changeRepresentation()

            thisM21Chord = thisChord.tabToM21() # In either case.

            try:
                p.measure(measure).insert(offsetInMeasure, thisM21Chord)
            except:
                pass

        self.m21stream = s

        return s

    def prepStream(self):
        '''
        Prepares a music21 stream for the harmonic analysis to go into.
        Specifically: creates the score, part, and measure streams,
        as well as some (the available) metadata based on the original TSV data.
        '''

        s = stream.Score()
        p = stream.Part()

        s.insert(0, metadata.Metadata())

        scl0 = self.chordList[0]
        s.metadata.opusNumber = scl0.op
        s.metadata.number = scl0.no
        s.metadata.movementNumber = scl0.mov
        s.metadata.title = 'Op'+scl0.op+'_No'+scl0.no+'_Mov'+scl0.mov

        startingKeySig = str(self.chordList[0].global_key)
        ks = key.Key(startingKeySig)
        p.insert(0, ks)

        currentTimeSig = str(self.chordList[0].timesig)
        ts = meter.TimeSignature(currentTimeSig)
        p.insert(0, ts)

        currentMeasureLength = ts.barDuration.quarterLength

        previousMeasure = self.chordList[0].measure - 1  # Covers anacruses
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

        self.prepdStream = s

        return s

# ------------------------------------------------------------------------------

class M21toTSV:
    '''
    Exports a music21 stream to tabular data and (optionally) writes the file.
    '''

    def __init__(self, m21Stream):
        self.m21Stream = m21Stream
        self.tsvData = self.m21ToTsv()

    def m21ToTsv(self):
        '''
        Converts a list of music21 chords to a list of lists
        which can then be written to a tsv file with toTsv(), or processed another way.
        '''

        tsvData = []

        for thisEntry in self.m21Stream.recurse():
            if 'RomanNumeral' in thisEntry.classes:

                relativeroot = None
                if thisEntry.secondaryRomanNumeral:
                    relativeroot = thisEntry.secondaryRomanNumeral.figure

                altChord = None
                if thisEntry.secondaryRomanNumeral:
                    if thisEntry.secondaryRomanNumeral.key == thisEntry.key:
                        altChord = thisEntry.secondaryRomanNumeral.figure,

                thisInfo = [thisEntry.figure,  # NB: slightly different from DCML: no key.
                            altChord,
                            thisEntry.measureNumber,
                            thisEntry.beat,
                            None,  # 'totbeat'
                            thisEntry.getContextByClass('TimeSignature').ratioString,
                            self.m21Stream.metadata.opusNumber,
                            self.m21Stream.metadata.number,
                            self.m21Stream.metadata.movementNumber,
                            thisEntry.quarterLength,
                            None,  # 'global_key',
                            thisEntry.key,  # 'local_key',
                            None,  # 'pedal',
                            thisEntry.romanNumeralAlone,  # numeral
                            None,  # 'form',
                            thisEntry.figuresWritten,  # figbass
                            None,  # 'changes',
                            relativeroot,
                            None,  # 'phraseend'
                            ]
                tsvData.append(thisInfo)

        return tsvData

    def write(self, outFilePath='./', outFileName='TSV_FILE.tsv',):
        '''
        Writes a list of lists (e.g. from m21ToTsv()) to a tsv file.
        '''

        if outFileName=='TSV_FILE.tsv':  # I.e. if not set by user
            if self.m21Stream.metadata.title:
                outFileName = self.m21Stream.metadata.title

        with open(outFilePath+outFileName, 'a') as csvfile:
            csvOut = csv.writer(csvfile, delimiter='\t',
                                quotechar='"', quoting=csv.QUOTE_MINIMAL)

            headers = ('chord',
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
                        'phraseend',)

            csvOut.writerow([x for x in headers])

            for thisEntry in self.tsvData:
                csvOut.writerow([x for x in thisEntry])

# ------------------------------------------------------------------------------

# Static.

def is_minor(key):
    return key == key.lower()

def characterSwaps(preString, minor=True, direction='m21-DCML'):
    '''
    Character swap function to coordinate between the two notational versions, for instance
    swapping between '%' and '/o' for the notation of half diminished (for example).

    >>> testStr = 'ii%'
    >>> romanText.tsvConverter.characterSwaps(testStr, minor=False, direction='DCML-m21')
    'ii/o'

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

    if direction == 'm21-DCML':
        characterDict = {'/o': '%',
                        }
    elif direction == 'DCML-m21':
        characterDict = {'%': '/o',  # Reverse direction.
                         'M7': '7',  # 7th types not specified in m21
                        }
    else:
        raise ValueError("Direction must be 'm21-DCML' or 'DCML-m21'.")

    for key in characterDict:  # Both major and minor
        preString = preString.replace(key, characterDict[key])

    if not minor:  # == False:
        return preString
    else:  # minor == True:
        if direction == 'm21-DCML':
            search = 'b'
            insert = '#'
        elif direction == 'DCML-m21':
            search = '#'
            insert = 'b'
        else:  # Should be redundant: covered above.
            raise ValueError("Direction must be 'm21-DCML' or 'DCML-m21'.")

        if 'vii' in preString.lower():
            position = preString.lower().index('vii')
            prevChar = preString[position-1] # the previous character,  # / b.
            if prevChar == search:
                postString = preString[:position-1]+preString[position:]
            else:
                postString = preString[:position]+insert+preString[position:]
        else:
            postString = preString

    return postString

def getLocalKey(local_key, global_key, convert=False):
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
    >>> romanText.tsvConverter.getLocalKey('vii', 'a', convert=True)
    'g'
    '''

    if convert==True:
        local_key = characterSwaps(local_key, minor=is_minor(global_key[0]), direction='DCML-m21')

    asRoman = roman.RomanNumeral(local_key, global_key)
    rt = asRoman.root().name
    if asRoman.isMajorTriad():
        newKey = rt.upper()
    elif asRoman.isMinorTriad():
        newKey = rt.lower()

    return newKey

def vLocalKey(rn, local_key):
    '''
    Separates comparative roman numeral for tonicisiations like 'V/vi' into the component parts of
    - a roman numeral (V) and
    - a (very) local key (vi)
    and expresses that very local key in relation to the local key also called (DCML column 11).

    >>> romanText.tsvConverter.getLocalKey('vi', 'C')
    'a'
    >>> romanText.tsvConverter.vLocalKey('V/vi', 'C')
    'a'
    '''

    if '/' not in rn:
        very_local_as_key = local_key
    else:
        position = rn.index('/')
        very_local_as_roman = rn[position+1:]
        very_local_as_key = getLocalKey(very_local_as_roman, local_key)

    return very_local_as_key

# ------------------------------------------------------------------------------

class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testTsvHandler(self):

        name = 'tsvEgOp18No1Mov3.tsv'
        path = common.getSourceFilePath() / 'romanText' / name

        importedTsv = TsvHandler(path)
        # Based on the DCML file, with minor error correction (removing '#viio' of major keys);
        # Also includes a '@none' / rest test case;
        # No time signature changes though - tested separately.

        # Raw
        self.assertEqual(importedTsv.tsvData[0][0], '.F.I')
        self.assertEqual(importedTsv.tsvData[35][0], '#viio6/ii')

        # Chords
        importedTsv.tsvToChords()
        testTabChord1 = importedTsv.chordList[0] # Also tests makeTabChord()
        testTabChord2 = importedTsv.chordList[35]
        self.assertEqual(testTabChord1.combinedChord, '.F.I')
        self.assertEqual(testTabChord1.numeral, 'I')
        self.assertEqual(testTabChord2.combinedChord, '#viio6/ii')
        self.assertEqual(testTabChord2.numeral, '#vii')

        # Change Representation
        testTabChord1.changeRepresentation()
        self.assertEqual(testTabChord1.numeral, 'I')
        testTabChord2.changeRepresentation()
        self.assertEqual(testTabChord2.numeral, 'vii')

        # M21 RNs
        m21Chord1 = testTabChord1.tabToM21()
        m21Chord2 = testTabChord2.tabToM21()
        self.assertEqual(m21Chord1.figure, 'I')
        self.assertEqual(m21Chord2.figure, 'viio6/ii')

        # M21 stream
        strm = importedTsv.toM21Stream()
        self.assertEqual(strm.parts[0].measure(1)[0].figure, 'I') # First item in measure 1

    def testM21ToTsv(self):

        from music21 import converter

        name = 'choraleExample.rntxt'
        path = common.getSourceFilePath() / 'romanText' / name

        bachHarmony = converter.parse(path, format='romanText')
        initial = M21toTSV(bachHarmony)
        tsvData = initial.tsvData
        self.assertEqual(bachHarmony.parts[0].measure(1)[0].figure, 'vi') # NB anacrustic measure 0.
        self.assertEqual(tsvData[0][13], 'I')

        # Test .write
        envLocal = environment.Environment()
        tempF = envLocal.getTempFile()
        from os import path
        path, fileName = path.split(tempF)
        newFileName = 'TestTsvFile'
        initial.write(outFilePath=path, outFileName=newFileName)
        importedTsv = TsvHandler(path+newFileName)
        self.assertEqual(importedTsv.tsvData[0][0], 'I')

    def testIsMinor(self):
        self.assertEqual(is_minor('f'), True)
        self.assertEqual(is_minor('F'), False)

    def testOfCharacter(self):

        startText = 'before%after'
        newText = ''.join([characterSwaps(x, direction='DCML-m21') for x in startText])
        # '%' > '/o'

        self.assertIsInstance(startText, str)
        self.assertIsInstance(newText, str)
        self.assertEqual(len(startText), 12)
        self.assertEqual(len(newText), 13)
        self.assertEqual(startText[6], '%')
        self.assertEqual(newText[6], '/')
        self.assertEqual(newText[7], 'o')

        testStr1in = 'ii%'
        testStr1out = characterSwaps(testStr1in, minor=False, direction='DCML-m21')

        self.assertEqual(testStr1in, 'ii%')
        self.assertEqual(testStr1out, 'ii/o')

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

        test4 = getLocalKey('vii', 'a', convert=True)
        self.assertEqual(test4, 'g')

    def testvLocalKey(self):

        testRN = 'V/vi'
        testLocalKey = 'D'

        veryLocalKey = vLocalKey(testRN, testLocalKey)

        self.assertIsInstance(veryLocalKey, str)
        self.assertEqual(veryLocalKey, 'b')

# ------------------------------------------------------------------------------

if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
