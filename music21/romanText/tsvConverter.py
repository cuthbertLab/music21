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

import abc
import csv
import re
import types
import unittest

from music21 import chord
from music21 import common
from music21 import harmony
from music21 import key
from music21 import metadata
from music21 import meter
from music21 import roman
from music21 import stream

from music21 import exceptions21

from music21 import environment
environLocal = environment.Environment()

# ------------------------------------------------------------------------------


class TsvException(exceptions21.Music21Exception):
    pass


# ------------------------------------------------------------------------------

# V1_HEADERS and V2_HEADERS specify the columns that we process from the DCML
# files, together with the type that the columns should be coerced to (usually
# str)

V1_HEADERS = types.MappingProxyType({
    'chord': str,
    'altchord': str,
    'measure': int,
    'beat': float,
    'totbeat': str,
    'timesig': str,
    'op': str,
    'no': str,
    'mov': str,
    'length': float,
    'global_key': str,
    'local_key': str,
    'pedal': str,
    'numeral': str,
    'form': str,
    'figbass': str,
    'changes': str,
    'relativeroot': str,
    'phraseend': str,
})

MN_ONSET_REGEX = re.compile(
    r'(?P<numer>\d+(?:\.\d+)?)/(?P<denom>\d+(?:\.\d+)?)'
)

def _float_or_frac(value):
    # mn_onset in V2 is sometimes notated as a fraction like '1/2'; we need
    # to handle such cases
    try:
        return float(value)
    except ValueError:
        m = re.match(MN_ONSET_REGEX, value)
        return float(m.group('numer')) / float(m.group('denom'))


V2_HEADERS = types.MappingProxyType({
    'chord': str,
    'mn': int,
    'mn_onset': _float_or_frac,
    'timesig': str,
    'globalkey': str,
    'localkey': str,
    'pedal': str,
    'numeral': str,
    'form': str,
    'figbass': str,
    'changes': str,
    'relativeroot': str,
    'phraseend': str,
})

HEADERS = (V1_HEADERS, V2_HEADERS)

# Headers for Digital and Cognitive Musicology Lab Standard v1 as in the ABC
# corpus at
# https://github.com/DCMLab/ABC/tree/2e8a01398f8ad694d3a7af57bed8b14ac57120b7
DCML_V1_HEADERS = (
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

# Headers for Digital and Cognitive Musicology Lab Standard v2 as in the ABC
# corpus at
# https://github.com/DCMLab/ABC/tree/65c831a559c47180d74e2679fea49aa117fd3dbb
DCML_V2_HEADERS = (
    'mc',
    'mn',
    'mc_onset',
    'mn_onset',
    'timesig',
    'staff',
    'voice',
    'volta',
    'label',
    'globalkey',
    'localkey',
    'pedal',
    'chord',
    'special',
    'numeral',
    'form',
    'figbass',
    'changes',
    'relativeroot',
    'cadence',
    'phraseend',
    'chord_type',
    'globalkey_is_minor',
    'localkey_is_minor',
    'chord_tones',
    'added_tones',
    'root',
    'bass_note',
)

DCML_HEADERS = (DCML_V1_HEADERS, DCML_V2_HEADERS)

class TabChordBase(abc.ABC):
    '''
    Abstract base class for intermediate representation format for moving
    between tabular data and music21 chords.
    '''

    def __init__(self):
        super().__init__()
        self.numeral = None
        self.relativeroot = None
        self.representationType = self.extra = None  # Added (not in DCML)


    @property
    @abc.abstractmethod
    def dcml_version(self):
        pass

    @property
    def combinedChord(self):
        '''
        For easier interoperability with the DCML standards, we now use the
        column name 'chord' from the DCML file. But to preserve backwards-
        compatibility, we add this property, which is an alias for 'chord'.

        >>> tabCd = romanText.tsvConverter.TabChord()
        >>> tabCd.chord = 'viio7'
        >>> tabCd.combinedChord
        'viio7'
        >>> tabCd.combinedChord = 'IV+'
        >>> tabCd.chord
        'IV+'
        '''
        return self.chord

    @combinedChord.setter
    def combinedChord(self, value):
        self.chord = value

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

        # self.local_key is an ordinary attribute of TabChordV1 but a property
        # of TabChordV2, so we can't define it in the __init__ of the base
        # class. Thus we need to disable the pylint warning here.
        self.local_key = characterSwaps(self.local_key,  # pylint: disable=attribute-defined-outside-init
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

        if self.numeral in ('@none', None):
            thisEntry = harmony.NoChord()
        else:
            # previously this code only included figbass in combined if form
            # was not falsy, which seems incorrect
            combined = ''.join(
                [attr for attr in (self.numeral, self.form, self.figbass) if attr]
            )

            if self.relativeroot:  # special case requiring '/'.
                combined = ''.join([combined, '/', self.relativeroot])
            if self.local_key is not None and re.match(
                r'.*(i*v|v?i+).*', self.local_key, re.IGNORECASE
            ):
                # if self.local_key contains a roman numeral, express it
                # as a pitch, relative to the global key
                localKeyNonRoman = getLocalKey(self.local_key, self.global_key)
            else:
                # otherwise, we assume self.local_key is already a pitch and
                # pass it through unchanged
                localKeyNonRoman = self.local_key
            thisEntry = roman.RomanNumeral(combined, localKeyNonRoman)

            if self.dcml_version == 1:
                thisEntry.quarterLength = self.length
                # following metadata attributes seem to be missing from
                # dcml_version 2 tsv files
                thisEntry.op = self.op
                thisEntry.no = self.no
                thisEntry.mov = self.mov

            thisEntry.pedal = self.pedal

            thisEntry.phraseend = None

        return thisEntry

class TabChord(TabChordBase):
    '''
    An intermediate representation format for moving between tabular data in
    DCML v1 and music21 chords.
    '''
    _dcml_version = 1
    def __init__(self):
        # self.numeral and self.relativeroot defined in super().__init__()
        super().__init__()
        self.chord = None
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
        self.form = None
        self.figbass = None
        self.changes = None
        self.phraseend = None

    @property
    def dcml_version(self):
        return self._dcml_version



class TabChordV2(TabChordBase):
    '''
    An intermediate representation format for moving between tabular data in
    DCML v2 and music21 chords.
    '''
    _dcml_version = 2
    def __init__(self):
        # self.numeral and self.relativeroot defined in super().__init__()
        super().__init__()
        self.chord = None
        self.mn = None
        self.mn_onset = None
        self.timesig = None
        self.globalkey = None
        self.localkey = None
        self.pedal = None
        self.form = None
        self.figbass = None
        self.changes = None
        self.phraseend = None

    @property
    def dcml_version(self):
        return self._dcml_version

    @property
    def beat(self):
        '''
        'beat' has been removed from DCML v2 in favor of 'mn_onset' and
        'mc_onset'. 'mn_onset' is equivalent to 'beat', except that 'mn_onset'
        is zero-indexed where 'beat' was 1-indexed. This property reproduces
        the former 'beat' by adding 1 to 'mn_onset'.
        >>> tabCd = romanText.tsvConverter.TabChordV2()
        >>> tabCd.mn_onset = 0
        >>> tabCd.beat
        1
        '''
        # beat is zero-indexed in v2 but one-indexed in v1
        return self.mn_onset + 1

    @property
    def measure(self):
        '''
        'measure' has been removed from DCML v2 in favor of 'mn' and 'mc'. 'mn'
        is equivalent to 'measure', so this property is provided as an alias.
        '''
        return int(self.mn)

    @property
    def local_key(self):
        '''
        'local_key' has been renamed 'localkey' in DCML v2. This property is
        provided as an alias for 'localkey' so that TabChord and TabChordV2 can
        be used in the same way.
        '''
        return self.localkey

    @local_key.setter
    def local_key(self, k):
        self.localkey = k

    @property
    def global_key(self):
        '''
        'global_key' has been renamed 'globalkey' in DCML v2. This property is
        provided as an alias for 'globalkey' so that TabChord and TabChordV2 can
        be used in the same way.
        '''
        return self.globalkey

    @global_key.setter
    def global_key(self, k):
        self.globalkey = k

# ------------------------------------------------------------------------------


class TsvHandler:
    '''
    Conversion starting with a TSV file.

    First we need to get a score. (Don't worry about this bit.)

    >>> name = 'tsvEg_v1.tsv'
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
    def __init__(self, tsvFile, dcml_version=1):
        self.heading_names = HEADERS[dcml_version - 1]
        self.tsvFileName = tsvFile
        self.chordList = None
        self.m21stream = None
        self.preparedStream = None
        self._head_indices = None
        self._extra_indices = None
        self._tab_chord_cls = (TabChord, TabChordV2)[dcml_version - 1]
        self.dcml_version = dcml_version
        self.tsvData = self.importTsv()

    def _get_heading_indices(self, header_row):
        self._head_indices, self._extra_indices = {}, {}
        for i, item in enumerate(header_row):
            if item in self.heading_names:
                self._head_indices[i] = item, self.heading_names[item]
            else:
                self._extra_indices[i] = item

    def importTsv(self):
        '''
        Imports TSV file data for further processing.
        '''

        fileName = self.tsvFileName

        with open(fileName, 'r', encoding='utf-8') as f:
            tsvreader = csv.reader(f, delimiter='\t', quotechar='"')
            # The first row is the header
            self._get_heading_indices(next(tsvreader))
            return list(tsvreader)

    def _makeTabChord(self, row):
        '''
        Makes a TabChord out of a list imported from TSV data
        (a row of the original tabular format -- see TsvHandler.importTsv()).
        '''
        # this method replaces the previously stand-alone makeTabChord function
        thisEntry = self._tab_chord_cls()
        for i, (name, type_) in self._head_indices.items():
            setattr(thisEntry, name, type_(row[i]))
        thisEntry.extra = {
            name: row[i] for i, name in self._extra_indices.items() if row[i]
        }
        thisEntry.representationType = 'DCML'  # Added

        return thisEntry

    def tsvToChords(self):
        '''
        Converts a list of lists (of the type imported by importTsv)
        into TabChords (i.e. a list of TabChords).
        '''

        data = self.tsvData

        self.chordList = []

        for entry in data:
            thisEntry = self._makeTabChord(entry)
            if thisEntry is None:
                continue
            else:
                self.chordList.append(thisEntry)

    def toM21Stream(self):
        '''
        Takes a list of TabChords (self.chordList, prepared by .tsvToChords()),
        converts those TabChords in RomanNumerals
        (converting to the music21 representation format as necessary),
        creates a suitable music21 stream (by running .prepStream() using data from the TabChords),
        and populates that stream with the new RomanNumerals.
        '''

        if self.chordList is None:
            self.tsvToChords()
        self.prepStream()

        s = self.preparedStream
        p = s.parts.first()  # Just to get to the part, not that there are several.

        for thisChord in self.chordList:
            offsetInMeasure = thisChord.beat - 1  # beats always measured in quarter notes
            measureNumber = thisChord.measure
            m21Measure = p.measure(measureNumber)

            if thisChord.representationType == 'DCML':
                thisChord._changeRepresentation()

            thisM21Chord = thisChord.tabToM21()  # In either case.
            # Store any otherwise unhandled attributes of the chord
            thisM21Chord.editorial.update(thisChord.extra)

            m21Measure.insert(offsetInMeasure, thisM21Chord)

        self.m21stream = s

        return s

    def prepStream(self):
        '''
        Prepares a music21 stream for the harmonic analysis to go into.
        Specifically: creates the score, part, and measure streams,
        as well as some (the available) metadata based on the original TSV data.
        Works like the .template() method,
        except that we don't have a score to base the template on as such.
        '''
        s = stream.Score()
        p = stream.Part()
        if self.dcml_version == 1:
            # This sort of metadata seems to have been removed altogether from the
            # v2 files
            s.insert(0, metadata.Metadata())

            firstEntry = self.chordList[0]  # Any entry will do
            s.metadata.opusNumber = firstEntry.op
            s.metadata.number = firstEntry.no
            s.metadata.movementNumber = firstEntry.mov
            s.metadata.title = (
                'Op' + firstEntry.op + '_No' + firstEntry.no + '_Mov' + firstEntry.mov
            )

        startingKeySig = str(self.chordList[0].global_key)
        ks = key.Key(startingKeySig)
        p.insert(0, ks)

        currentTimeSig = str(self.chordList[0].timesig)
        ts = meter.TimeSignature(currentTimeSig)
        p.insert(0, ts)

        currentMeasureLength = ts.barDuration.quarterLength

        currentOffset = 0

        previousMeasure: int = self.chordList[0].measure - 1  # Covers pickups
        for entry in self.chordList:
            if entry.measure == previousMeasure:
                continue
            elif entry.measure != previousMeasure + 1:  # Not every measure has a chord change.
                for mNo in range(previousMeasure + 1, entry.measure + 1):
                    m = stream.Measure(number=mNo)
                    m.offset = currentOffset + currentMeasureLength
                    p.insert(m)

                    currentOffset = m.offset
                    previousMeasure = mNo
            else:  # entry.measure = previousMeasure + 1
                m = stream.Measure(number=entry.measure)
                # 'totbeat' column (containing the current offset) has been
                # removed from v2 so instead we calculate the offset directly
                # to be portable across versions
                currentOffset = m.offset = currentOffset + currentMeasureLength
                p.insert(m)
                if entry.timesig != currentTimeSig:
                    newTS = meter.TimeSignature(entry.timesig)
                    m.insert(entry.beat - 1, newTS)

                    currentTimeSig = entry.timesig
                    currentMeasureLength = newTS.barDuration.quarterLength

                previousMeasure = entry.measure

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

    >>> initial = romanText.tsvConverter.M21toTSV(bachHarmony, dcml_version=2)
    >>> tsvData = initial.tsvData
    >>> tsvData[1][14] # 14 is index to 'chord' in v2
    'I'
    '''

    def __init__(self, m21Stream, dcml_version=2):
        self.version = dcml_version
        self.m21Stream = m21Stream
        self.dcml_headers = DCML_HEADERS[dcml_version - 1]
        self.tsvData = self.m21ToTsv()

    def m21ToTsv(self):
        '''
        Converts a list of music21 chords to a list of lists
        which can then be written to a tsv file with toTsv(), or processed another way.
        '''
        if self.version == 1:
            return self._m21ToTsv_v1()
        return self._m21ToTsv_v2()

    def _m21ToTsv_v1(self):
        tsvData = []
        # take the global_key from the first item
        global_key = next(
            self.m21Stream.recurse().getElementsByClass('RomanNumeral')
        ).key.tonicPitchNameWithCase

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
            thisEntry.global_key = global_key
            local_key = thisRN.key.name.split()[0]
            if thisRN.key.mode == 'minor':
                local_key = local_key.lower()
            thisEntry.local_key = local_key
            thisEntry.pedal = None
            thisEntry.numeral = thisRN.romanNumeral
            thisEntry.form = get_form(thisRN)
            # Strip any leading non-digits from figbass (e.g., M43 -> 43)
            thisEntry.figbass = re.match(r"^\D*(\d.*|)", thisRN.figuresWritten).group(1)
            thisEntry.changes = None  # TODO
            thisEntry.relativeroot = relativeroot
            thisEntry.phraseend = None

            thisInfo = [
                getattr(thisEntry, name, thisRN.editorial.get(name, ''))
                for name in self.dcml_headers
            ]
            tsvData.append(thisInfo)

        return tsvData

    def _m21ToTsv_v2(self):
        tsvData = []

        # take the global_key from the first item
        global_key_obj = next(
            self.m21Stream.recurse().getElementsByClass('RomanNumeral')
        ).key
        global_key = global_key_obj.tonicPitchNameWithCase
        for thisRN in self.m21Stream.recurse().getElementsByClass(
            ['RomanNumeral', 'NoChord']
        ):
            thisEntry = TabChordV2()
            thisEntry.mn = thisRN.measureNumber
            thisEntry.mn_onset = thisRN.beat
            thisEntry.timesig = thisRN.getContextByClass(
                'TimeSignature'
            ).ratioString
            thisEntry.global_key = global_key
            if isinstance(thisRN, harmony.NoChord):
                thisEntry.numeral = thisEntry.chord = '@none'
            else:
                relativeroot = None
                if thisRN.secondaryRomanNumeral:
                    relativeroot = thisRN.secondaryRomanNumeral.figure
                thisEntry.chord = (
                    thisRN.figure
                )  # NB: slightly different from DCML: no key.
                thisEntry.pedal = None
                thisEntry.numeral = thisRN.romanNumeral
                thisEntry.form = get_form(thisRN)
                # Strip any leading non-digits from figbass (e.g., M43 -> 43)
                thisEntry.figbass = re.match(r"^\D*(\d.*|)", thisRN.figuresWritten).group(1)
                thisEntry.changes = None
                thisEntry.relativeroot = relativeroot
                thisEntry.phraseend = None
                local_key = local_key_as_rn(thisRN.key, global_key_obj)
                thisEntry.local_key = local_key

            thisInfo = [
                getattr(thisEntry, name, thisRN.editorial.get(name, ''))
                for name in self.dcml_headers
            ]

            tsvData.append(thisInfo)

        return tsvData

    def write(self, filePathAndName):
        '''
        Writes a list of lists (e.g. from m21ToTsv()) to a tsv file.
        '''
        with open(filePathAndName, 'a', newline='', encoding='utf-8') as csvFile:
            csvOut = csv.writer(csvFile,
                                delimiter='\t',
                                quotechar='"',
                                quoting=csv.QUOTE_MINIMAL)
            csvOut.writerow(self.dcml_headers)

            for thisEntry in self.tsvData:
                csvOut.writerow(thisEntry)

# ------------------------------------------------------------------------------

def get_form(rn):
    '''
    Takes a music21.roman.RomanNumeral object and returns the string indicating
    "form" expected by the DCML standard.

    >>> romanText.tsvConverter.get_form(roman.RomanNumeral('V'))
    ''
    >>> romanText.tsvConverter.get_form(roman.RomanNumeral('viio7'))
    'o'
    >>> romanText.tsvConverter.get_form(roman.RomanNumeral('IVM7'))
    'M'
    >>> romanText.tsvConverter.get_form(roman.RomanNumeral('III+'))
    '+'
    >>> romanText.tsvConverter.get_form(roman.RomanNumeral('IV+M7'))
    '+M'
    >>> romanText.tsvConverter.get_form(roman.RomanNumeral('viiø7'))
    '%'
    '''
    if 'ø' in rn.figure:
        return '%'
    if 'o' in rn.figure:
        return 'o'
    if '+M' in rn.figure:
        # Not sure whether there is more than one way for an augmented major seventh to be
        # indicated, in which case this condition needs to be updated.
        return '+M'
    if '+' in rn.figure:
        return '+'
    if 'M' in rn.figure:
        return 'M'
    return ''


def local_key_as_rn(local_key, global_key):
    '''
    Takes two music21.key.Key objects and returns the roman numeral for
    `local_key` relative to `global_key`.

    >>> k1 = key.Key('C')
    >>> k2 = key.Key('e-')
    >>> romanText.tsvConverter.local_key_as_rn(k1, k2)
    'VI'

    >>> romanText.tsvConverter.local_key_as_rn(k2, k1)
    'biii'
    '''
    letter = local_key.tonicPitchNameWithCase
    rn = roman.RomanNumeral(
        'i' if letter.islower() else 'I', keyOrScale=local_key
    )
    r = roman.romanNumeralFromChord(chord.Chord(rn.pitches), keyObj=global_key)
    return r.romanNumeral

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
        import os
        import urllib.request
        for version in (1, 2):  # test both versions
            name = f'tsvEg_v{version}.tsv'
            # A short and improbably complicated test case complete with:
            # '@none' (rest entry), '/' relative root, and time signature changes.
            path = common.getSourceFilePath() / 'romanText' / name

            handler = TsvHandler(path, dcml_version=version)
            headers = DCML_HEADERS[version - 1]
            chord_i = headers.index('chord')
            # Raw
            self.assertEqual(handler.tsvData[0][chord_i], '.C.I6')
            self.assertEqual(handler.tsvData[1][chord_i], '#viio6/ii')

            # Chords
            handler.tsvToChords()
            testTabChord1 = handler.chordList[0]  # Also tests makeTabChord()
            testTabChord2 = handler.chordList[1]
            self.assertIsInstance(testTabChord1, TabChordBase)
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
            self.assertEqual(
                out_stream.parts[0].measure(1)[0].figure, 'I'  # First item in measure 1
            )

            # Download a real tsv file to test the conversion on.

            urls = [
                # pylint: disable=line-too-long
                'https://raw.githubusercontent.com/DCMLab/ABC/2e8a01398f8ad694d3a7af57bed8b14ac57120b7/data/tsv/op.%2018%20No.%201/op18_no1_mov1.tsv',
                'https://raw.githubusercontent.com/DCMLab/ABC/65c831a559c47180d74e2679fea49aa117fd3dbb/harmonies/n01op18-1_01.tsv',
            ]
            url = urls[version - 1]
            envLocal = environment.Environment()
            temp_tsv1 = envLocal.getTempFile()
            with urllib.request.urlopen(url) as f:
                tsv_contents = f.read().decode('utf-8')
            with open(temp_tsv1, 'w', encoding='utf-8') as outf:
                outf.write(tsv_contents)

            # Convert to m21
            forward1 = TsvHandler(temp_tsv1, dcml_version=version)
            stream1 = forward1.toM21Stream()

            # Write back to tsv
            temp_tsv2 = envLocal.getTempFile()
            M21toTSV(stream1, dcml_version=version).write(temp_tsv2)

            # Convert back to m21 again
            forward2 = TsvHandler(temp_tsv2, dcml_version=version)
            stream2 = forward2.toM21Stream()
            os.remove(temp_tsv1)
            os.remove(temp_tsv2)

            # Ensure that both m21 streams are the same
            self.assertEqual(len(stream1.recurse()), len(stream2.recurse()))
            for i, (item1, item2) in enumerate(zip(
                stream1.recurse().getElementsByClass('RomanNumeral'),
                stream2.recurse().getElementsByClass('RomanNumeral')
            )):
                try:
                    self.assertEqual(
                        item1, item2, msg=f"item {i}, version {version}: {item1} != {item2}"
                    )
                except AssertionError:
                    # Augmented sixth figures will not agree, e.g.,
                    # - Ger6 becomes Ger65
                    # - Fr6 becomes Fr43
                    # This doesn't seem important, but we can at least
                    # assert that both items are augmented sixth chords of
                    # the same type.
                    m = re.match("Ger|Fr", item1.figure)
                    self.assertIsNotNone(m)
                    aug6_type = m.group(0)
                    self.assertTrue(item2.figure.startswith(aug6_type))

    def testM21ToTsv(self):
        import os
        from music21 import corpus

        bachHarmony = corpus.parse('bach/choraleAnalyses/riemenschneider001.rntxt')
        for version in (1, 2):
            initial = M21toTSV(bachHarmony, dcml_version=version)
            tsvData = initial.tsvData
            numeral_i = DCML_HEADERS[version - 1].index('numeral')
            self.assertEqual(bachHarmony.parts[0].measure(1)[0].figure, 'I')  # NB pickup measure 0.
            self.assertEqual(tsvData[1][numeral_i], 'I')

            # Test .write
            envLocal = environment.Environment()
            tempF = envLocal.getTempFile()
            initial.write(tempF)
            handler = TsvHandler(tempF)
            self.assertEqual(handler.tsvData[0][numeral_i], 'I')
            os.remove(tempF)

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
