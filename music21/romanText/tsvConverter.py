# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         romanText/tsvConverter.py
# Purpose:      Converter for the DCMLab's tabular format for representing harmonic analysis.
#
# Authors:      Mark Gotham
#
# Copyright:    Copyright © 2019 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
Converter for parsing the tabular representations of harmonic analysis such as the
DCMLab's Annotated Beethoven Corpus (Neuwirth et al. 2018).
'''
from __future__ import annotations

import abc
import csv
import fractions
import re
import string
import types
import typing as t
import unittest

from music21 import chord
from music21 import common
from music21 import environment
from music21 import harmony
from music21 import key
from music21 import metadata
from music21 import meter
from music21 import roman
from music21 import spanner
from music21 import stream

environLocal = environment.Environment()

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
    'volta': str,
    'globalkey': str,
    'localkey': str,
    'pedal': str,
    'numeral': str,
    'form': str,
    'figbass': str,
    'changes': str,
    'relativeroot': str,
    'phraseend': str,
    'label': str,
})

HEADERS = {1: V1_HEADERS, 2: V2_HEADERS}

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

DCML_HEADERS = {1: DCML_V1_HEADERS, 2: DCML_V2_HEADERS}

class TabChordBase(abc.ABC):
    '''
    Abstract base class for intermediate representation format for moving
    between tabular data and music21 chords.
    '''

    def __init__(self) -> None:
        super().__init__()
        self.numeral: str = ''
        self.relativeroot: str | None = None
        self.representationType: str | None = None  # Added (not in DCML)
        self.extra: dict[str, str] = {}
        self.dcml_version = -1

        # shared between DCML v1 and v2
        self.chord: str = ''
        self.timesig: str = ''
        self.pedal: str | None = None
        self.form: str | None = None
        self.figbass: str | None = None
        self.changes: str | None = None
        self.phraseend: str | None = None

        # the following attributes are overwritten by properties in TabChordV2
        # because of changed column names in DCML v2
        self.local_key: str = ''
        self.global_key: str = ''
        self.beat: float = 1.0
        self.measure: int = 1

    @property
    def combinedChord(self) -> str:
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
    def combinedChord(self, value: str):
        self.chord = value

    def _changeRepresentation(self) -> None:
        '''
        Converts the representationType of a TabChordBase subclass between the
        music21 and DCML conventions.

        To demonstrate, let's set up a dummy TabChordV2().

        >>> tabCd = romanText.tsvConverter.TabChordV2()
        >>> tabCd.global_key = 'F'
        >>> tabCd.local_key = 'vi'
        >>> tabCd.numeral = 'ii'
        >>> tabCd.chord = 'ii%7(6)'
        >>> tabCd.representationType = 'DCML'

        >>> tabCd.representationType
        'DCML'

        >>> tabCd.chord
        'ii%7(6)'

        >>> tabCd._changeRepresentation()
        >>> tabCd.representationType
        'm21'

        >>> tabCd.chord
        'iiø7[no5][add6]'
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
                                        minor=isMinor(self.global_key),
                                        direction=direction)

        # previously, '%' (indicating half-diminished) was not being parsed
        #   properly.
        if direction == 'DCML-m21':
            self.form = self.form.replace('%', 'ø') if self.form is not None else None
            if self.dcml_version == 2:
                self.chord = self.chord.replace('%', 'ø')
                self.chord = handleAddedTones(self.chord)
                if (
                    self.extra.get('chord_type', '') == 'Mm7'
                    and self.numeral != 'V'
                ):
                    # we need to make sure not to match [add4] and the like
                    self.chord = re.sub(r'(\d+)(?!])', r'd\1', self.chord)

        # Local - relative and figure
        if isMinor(self.local_key):
            if self.relativeroot:  # If there's a relative root ...
                if isMinor(self.relativeroot):  # ... and it's minor too, change it and the figure
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
                if isMinor(self.relativeroot):  # ... and it's minor, change it and the figure
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

    def tabToM21(self) -> harmony.Harmony:
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
        if self.representationType == 'DCML':
            self._changeRepresentation()
        if self.numeral in ('@none', None):
            thisEntry: harmony.Harmony = harmony.NoChord()
        else:
            if self.dcml_version == 2 and self.chord:
                combined = self.chord
            else:
                # previously this code only included figbass in combined if form
                # was not falsy, which seems incorrect
                combined = ''.join(
                    attr for attr in (self.numeral, self.form, self.figbass) if attr
                )

                if self.relativeroot:  # special case requiring '/'.
                    combined += '/' + self.relativeroot
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
            thisEntry = roman.RomanNumeral(
                combined,
                localKeyNonRoman,
                sixthMinor=roman.Minor67Default.FLAT,
                seventhMinor=roman.Minor67Default.FLAT
            )

            if isinstance(self, TabChord):
                # following metadata attributes seem to be missing from
                # dcml_version 2 tsv files
                thisEntry.editorial.op = self.extra.get('op', '')
                thisEntry.editorial.no = self.extra.get('no', '')
                thisEntry.editorial.mov = self.extra.get('mov', '')

            thisEntry.editorial.pedal = self.pedal
            thisEntry.editorial.phraseend = None
        # if dcml_version == 2, we need to calculate the quarterLength
        #   later
        thisEntry.quarterLength = 0.0
        return thisEntry

    def populateFromRow(
        self,
        row: list[str],
        headIndices: dict[str, tuple[int, type]],
        extraIndices: dict[int, str]
    ) -> None:
        # To implement without calling setattr we would need to repeat lines
        #   similar to the following three lines for every attribute (with
        #   attributes specific to subclasses in their own methods that would
        #   then call __super__()).
        for col_name, (i, type_to_coerce_to) in headIndices.items():
            if not hasattr(self, col_name):
                pass  # would it be appropriate to emit a warning here?
            else:
                setattr(self, col_name, type_to_coerce_to(row[i]))
        self.extra = {
            col_name: row[i] for i, col_name in extraIndices.items() if row[i]
        }

class TabChord(TabChordBase):
    '''
    An intermediate representation format for moving between tabular data in
    DCML v1 and music21 chords.
    '''
    def __init__(self) -> None:
        # self.numeral and self.relativeroot defined in super().__init__()
        super().__init__()
        self.altchord: str | None = None
        self.totbeat: str | None = None
        self.length: fractions.Fraction | float | None = None
        self.dcml_version: int = 1

class TabChordV2(TabChordBase):
    '''
    An intermediate representation format for moving between tabular data in
    DCML v2 and music21 chords.
    '''
    def __init__(self) -> None:
        # self.numeral and self.relativeroot defined in super().__init__()
        super().__init__()
        self.mn: int = 0
        self.mn_onset: float = 0.0
        self.volta: str = ''
        self.globalkey: str = ''
        self.localkey: str = ''
        self.dcml_version: int = 2

    @property
    def beat(self) -> float:
        '''
        'beat' has been removed from DCML v2 in favor of 'mn_onset' and
        'mc_onset'. 'mn_onset' is equivalent to 'beat', except that 'mn_onset'
        is zero-indexed where 'beat' was 1-indexed, and 'mn_onset' is in
        fractions of a whole-note rather than in quarter notes.

        >>> tabCd = romanText.tsvConverter.TabChordV2()
        >>> tabCd.mn_onset = 0.0
        >>> tabCd.beat
        1.0

        >>> tabCd.mn_onset = 0.5
        >>> tabCd.beat
        3.0

        >>> tabCd.beat = 1.5
        >>> tabCd.beat
        1.5
        '''
        # beat is zero-indexed in v2 but one-indexed in v1
        # moreover, beat is in fractions of a whole-note in v2
        return self.mn_onset * 4.0 + 1.0

    @beat.setter
    def beat(self, beat: float):
        self.mn_onset = (beat - 1.0) / 4.0 if beat is not None else None

    @property
    def measure(self) -> int:
        '''
        'measure' has been removed from DCML v2 in favor of 'mn' and 'mc'. 'mn'
        is equivalent to 'measure', so this property is provided as an alias.
        '''
        return int(self.mn)

    @measure.setter
    def measure(self, measure: int):
        self.mn = int(measure) if measure is not None else None

    @property
    def local_key(self) -> str:
        '''
        'local_key' has been renamed 'localkey' in DCML v2. This property is
        provided as an alias for 'localkey' so that TabChord and TabChordV2 can
        be used in the same way.
        '''
        return self.localkey

    @local_key.setter
    def local_key(self, k: str):
        self.localkey = k

    @property
    def global_key(self) -> str:
        '''
        'global_key' has been renamed 'globalkey' in DCML v2. This property is
        provided as an alias for 'globalkey' so that TabChord and TabChordV2 can
        be used in the same way.
        '''
        return self.globalkey

    @global_key.setter
    def global_key(self, k: str):
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

    And for our last trick, we can put the whole collection in a music21 stream.

    >>> out_stream = handler.toM21Stream()
    >>> out_stream.parts[0].measure(1)[roman.RomanNumeral][0].figure
    'I'

    '''
    def __init__(self, tsvFile: str, dcml_version: int = 1):
        if dcml_version == 1:
            self.heading_names = HEADERS[1]
            self._tab_chord_cls: type[TabChordBase] = TabChord
        elif dcml_version == 2:
            self.heading_names = HEADERS[2]
            self._tab_chord_cls = TabChordV2
        else:
            raise ValueError(f'dcml_version {dcml_version} is not in (1, 2)')
        self.tsvFileName = tsvFile
        self.chordList: list[TabChordBase] = []
        self.m21stream: stream.Score | None = None
        self._head_indices: dict[str, tuple[int, type | t.Any]] = {}
        self._extra_indices: dict[int, str] = {}
        self.dcml_version = dcml_version
        self.tsvData = self._importTsv()  # converted to private

    def _get_heading_indices(self, header_row: list[str]) -> None:
        '''
        Private method to get column name/column index correspondences.

        Expected column indices (those in HEADERS, which correspond to TabChord
        attributes) are stored in self._head_indices. Others go in
        self._extra_indices.
        '''
        self._head_indices = {}
        self._extra_indices = {}
        for i, col_name in enumerate(header_row):
            if col_name in self.heading_names:
                type_to_coerce_col_to = self.heading_names[col_name]
                self._head_indices[col_name] = (i, type_to_coerce_col_to)
            else:
                self._extra_indices[i] = col_name

    def _importTsv(self) -> list[list[str]]:
        '''
        Imports TSV file data for further processing.
        '''

        fileName = self.tsvFileName

        with open(fileName, 'r', encoding='utf-8') as f:
            tsvreader = csv.reader(f, delimiter='\t', quotechar='"')
            # The first row is the header
            self._get_heading_indices(next(tsvreader))
            return list(tsvreader)

    def _makeTabChord(self, row: list[str]) -> TabChordBase:
        '''
        Makes a TabChord out of a list imported from TSV data
        (a row of the original tabular format -- see TsvHandler.importTsv()).
        '''
        # this method replaces the previously stand-alone makeTabChord function
        thisEntry = self._tab_chord_cls()
        thisEntry.populateFromRow(row, self._head_indices, self._extra_indices)
        thisEntry.representationType = 'DCML'  # Added

        return thisEntry

    def tsvToChords(self) -> None:
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

    def toM21Stream(self) -> stream.Score:
        '''
        Takes a list of TabChords (self.chordList, prepared by .tsvToChords()),
        converts those TabChords in RomanNumerals
        (converting to the music21 representation format as necessary),
        creates a suitable music21 stream (by running .prepStream() using data from the TabChords),
        and populates that stream with the new RomanNumerals.
        '''
        if not self.chordList:
            self.tsvToChords()

        s = self.prepStream()
        p = s.parts.first()  # Just to get to the part, not that there are several.

        if p is None:
            # in case stream has no parts
            return s

        for thisChord in self.chordList:
            offsetInMeasure = thisChord.beat - 1  # beats always measured in quarter notes
            if isinstance(thisChord, TabChordV2) and thisChord.volta:
                measureNumber: str | int = (
                    f'{thisChord.measure}{string.ascii_lowercase[int(thisChord.volta) - 1]}'
                )
            else:
                measureNumber = thisChord.measure
            m21Measure = p.measure(measureNumber)
            if m21Measure is None:
                raise ValueError('m21Measure should not be None')

            thisM21Chord = thisChord.tabToM21()  # In either case.
            # Store any otherwise unhandled attributes of the chord
            thisM21Chord.editorial.update(thisChord.extra)

            m21Measure.insert(offsetInMeasure, thisM21Chord)

        s.flatten().extendDuration(harmony.Harmony, inPlace=True)
        last_harmony = s[harmony.Harmony].last()
        if last_harmony is not None:
            last_harmony.quarterLength = (
                s.quarterLength - last_harmony.activeSite.offset - last_harmony.offset
            )

        self.m21stream = s
        return s

    def prepStream(self) -> stream.Score:
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
            title = []
            if 'op' in firstEntry.extra:
                s.metadata.opusNumber = firstEntry.extra['op']
                title.append('Op' + s.metadata.opusNumber)
            if 'no' in firstEntry.extra:
                s.metadata.number = firstEntry.extra['no']
                title.append('No' + s.metadata.number)
            if 'mov' in firstEntry.extra:
                s.metadata.movementNumber = firstEntry.extra['mov']
                title.append('Mov' + s.metadata.movementNumber)
            if title:
                s.metadata.title = '_'.join(title)

        startingKeySig = str(self.chordList[0].global_key)
        ks = key.Key(startingKeySig)

        currentTimeSig = str(self.chordList[0].timesig)
        ts = meter.TimeSignature(currentTimeSig)

        currentMeasureLength = ts.barDuration.quarterLength

        currentOffset: float | fractions.Fraction = 0.0

        previousMeasure: int = self.chordList[0].measure - 1  # Covers pickups
        previousVolta: str = ''
        repeatBracket: t.Optional[spanner.RepeatBracket] = None
        for entry in self.chordList:
            if isinstance(entry, TabChordV2) and entry.volta != previousVolta:
                if entry.volta:
                    # Should we warn the user that, although we're writing
                    # repeat brackets, we aren't writing repeat signs since
                    # the .tsv file doesn't tell us where the forward repeat
                    # should be?
                    repeatBracket = spanner.RepeatBracket(number=entry.volta)
                    # According to the docs at
                    # https://web.mit.edu/music21/doc/moduleReference/moduleSpanner.html#spanner
                    #   "the convention is to put the spanner at the beginning
                    #   of the innermost Stream that contains all the Spanners"
                    p.insert(0, repeatBracket)
                else:
                    repeatBracket = None
                previousVolta = entry.volta
            elif entry.measure == previousMeasure:
                # NB we only want to continue here if the 'volta' (ending) has
                #   not changed, hence the elif
                continue
            if entry.measure > previousMeasure + 1:  # Not every measure has a chord change.
                for mNo in range(previousMeasure + 1, entry.measure + 1):
                    m = stream.Measure(number=mNo)
                    m.offset = currentOffset + currentMeasureLength

                    p.insert(m)
                    currentOffset = m.offset
                    previousMeasure = mNo
            else:  # entry.measure <= previousMeasure + 1
                if isinstance(entry, TabChordV2) and entry.volta:
                    measureNumber: str | int = (
                        f'{entry.measure}{string.ascii_lowercase[int(entry.volta) - 1]}'
                    )
                else:
                    measureNumber = entry.measure
                m = stream.Measure(number=measureNumber)
                # 'totbeat' column (containing the current offset) has been
                # removed from v2 so instead we calculate the offset directly
                # to be portable across versions
                currentOffset = m.offset = currentOffset + currentMeasureLength
                p.insert(m)
                if entry.timesig != currentTimeSig:
                    newTS = meter.TimeSignature(entry.timesig)
                    m.insert(entry.beat - 1, newTS)
                    currentTimeSig = entry.timesig or ''
                    currentMeasureLength = newTS.barDuration.quarterLength

                previousMeasure = entry.measure
            if repeatBracket is not None:
                repeatBracket.addSpannedElements(m)

        s.append(p)
        first_measure = s[stream.Measure].first()
        if first_measure is not None:
            first_measure.insert(0, ks)
            first_measure.insert(0, ts)
        return s


# ------------------------------------------------------------------------------
class M21toTSV:
    '''
    Conversion starting with a music21 stream.
    Exports to tabular data format and (optionally) writes the file.

    >>> bachHarmony = corpus.parse('bach/choraleAnalyses/riemenschneider001.rntxt')
    >>> bachHarmony.parts[0].measure(1)[0].figure
    'I'

    The initialization includes the preparation of a list of lists, so

    >>> initial = romanText.tsvConverter.M21toTSV(bachHarmony, dcml_version=2)
    >>> tsvData = initial.tsvData
    >>> from music21.romanText.tsvConverter import DCML_V2_HEADERS
    >>> tsvData[1][DCML_V2_HEADERS.index('chord')]
    'I'
    '''

    def __init__(self, m21Stream: stream.Score, dcml_version: int = 2):
        self.version = dcml_version
        self.m21Stream = m21Stream
        if dcml_version == 1:
            self.dcml_headers = DCML_HEADERS[1]
        elif dcml_version == 2:
            self.dcml_headers = DCML_HEADERS[2]
        else:
            raise ValueError(f'dcml_version {dcml_version} is not in (1, 2)')
        self.tsvData = self.m21ToTsv()

    def m21ToTsv(self) -> list[list[str]]:
        '''
        Converts a list of music21 chords to a list of lists
        which can then be written to a tsv file with toTsv(), or processed another way.
        '''
        if self.version == 1:
            return self._m21ToTsv_v1()
        return self._m21ToTsv_v2()

    def _m21ToTsv_v1(self) -> list[list[str]]:
        tsvData = []
        # take the global_key from the first item
        global_key = next(
            self.m21Stream.recurse().getElementsByClass('RomanNumeral')
        ).key.tonicPitchNameWithCase

        for thisRN in self.m21Stream[roman.RomanNumeral]:

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
            thisEntry.measure = thisRN.measureNumber if thisRN.measureNumber is not None else 1
            thisEntry.beat = float(thisRN.beat)
            thisEntry.totbeat = None
            ts = thisRN.getContextByClass(meter.TimeSignature)
            if ts is None:
                thisEntry.timesig = ''
            else:
                thisEntry.timesig = ts.ratioString
            thisEntry.extra['op'] = self.m21Stream.metadata.opusNumber or ''
            thisEntry.extra['no'] = self.m21Stream.metadata.number or ''
            thisEntry.extra['mov'] = self.m21Stream.metadata.movementNumber or ''
            thisEntry.length = thisRN.quarterLength
            thisEntry.global_key = global_key
            thisEntry.local_key = thisRN.key.tonicPitchNameWithCase
            thisEntry.pedal = None
            thisEntry.numeral = thisRN.romanNumeral
            thisEntry.form = getForm(thisRN)
            # Strip any leading non-digits from figbass (e.g., M43 -> 43)
            figbassMatch = re.match(r'^\D*(\d.*|)', thisRN.figuresWritten)
            if figbassMatch is not None:
                thisEntry.figbass = figbassMatch.group(1)
            else:
                thisEntry.figbass = ''
            thisEntry.changes = None  # TODO
            thisEntry.relativeroot = relativeroot
            thisEntry.phraseend = None

            thisInfo = [
                getattr(thisEntry, name, thisRN.editorial.get(name, ''))
                for name in self.dcml_headers
            ]
            tsvData.append(thisInfo)

        return tsvData

    def _m21ToTsv_v2(self) -> list[list[str]]:
        tsvData: list[list[str]] = []

        # take the global_key from the first item
        first_rn = self.m21Stream[roman.RomanNumeral].first()
        if first_rn is None:
            return tsvData
        global_key_obj = first_rn.key
        global_key = global_key_obj.tonicPitchNameWithCase
        for thisRN in self.m21Stream.recurse().getElementsByClass(
            [roman.RomanNumeral, harmony.NoChord]
        ):
            thisEntry = TabChordV2()
            thisEntry.mn = thisRN.measureNumber
            # for a reason I do not understand, thisRN.beat in V2 seems to
            #   always be beat 1. In neither v1 is thisRN set explicitly;
            #   the offset/beat seems to be determined by
            #   m21Measure.insert(offsetInMeasure, thisM21Chord) above. I'm at
            #   a loss why there is an issue here but using thisRN.offset works
            #   just fine.
            thisEntry.mn_onset = thisRN.offset / 4
            timesig = thisRN.getContextByClass(meter.TimeSignature)
            if timesig is None:
                thisEntry.timesig = ''
            else:
                thisEntry.timesig = timesig.ratioString
            thisEntry.global_key = global_key
            if isinstance(thisRN, harmony.NoChord):
                thisEntry.numeral = '@none'
                thisEntry.chord = '@none'
            else:
                local_key = localKeyAsRn(thisRN.key, global_key_obj)
                relativeroot = None
                if thisRN.secondaryRomanNumeral:
                    relativeroot = thisRN.secondaryRomanNumeral.figure
                    relativeroot = characterSwaps(
                        relativeroot, isMinor(local_key), direction='m21-DCML'
                    )
                thisEntry.chord = thisRN.figure  # NB: slightly different from DCML: no key.
                thisEntry.pedal = None
                thisEntry.numeral = thisRN.romanNumeral
                thisEntry.form = getForm(thisRN)
                # Strip any leading non-digits from figbass (e.g., M43 -> 43)
                figbassm = re.match(r'^\D*(\d.*|)', thisRN.figuresWritten)
                # implementing the following check according to the review
                # at https://github.com/cuthbertLab/music21/pull/1267/files/a1ad510356697f393bf6b636af8f45e81ad6ccc8#r936472302 #pylint: disable=line-too-long
                # but the match should always exist because either:
                #   1. there is a digit in the string, in which case it matches
                #       because of the left side of the alternation operator
                #   2. there is no digit in the string, in which case it matches
                #       because of the right side of the alternation operator
                #       (an empty string)
                if figbassm is not None:
                    thisEntry.figbass = figbassm.group(1)
                else:
                    thisEntry.figbass = ''
                thisEntry.changes = None
                thisEntry.relativeroot = relativeroot
                thisEntry.phraseend = None
                thisEntry.local_key = local_key

            thisInfo = [
                getattr(thisEntry, name, thisRN.editorial.get(name, ''))
                for name in self.dcml_headers
            ]
            tsvData.append(thisInfo)
        return tsvData

    def write(self, filePathAndName: str):
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

def getForm(rn: roman.RomanNumeral) -> str:
    '''
    Takes a music21.roman.RomanNumeral object and returns the string indicating
    'form' expected by the DCML standard.

    >>> romanText.tsvConverter.getForm(roman.RomanNumeral('V'))
    ''
    >>> romanText.tsvConverter.getForm(roman.RomanNumeral('viio7'))
    'o'
    >>> romanText.tsvConverter.getForm(roman.RomanNumeral('IVM7'))
    'M'
    >>> romanText.tsvConverter.getForm(roman.RomanNumeral('III+'))
    '+'
    >>> romanText.tsvConverter.getForm(roman.RomanNumeral('IV+M7'))
    '+M'
    >>> romanText.tsvConverter.getForm(roman.RomanNumeral('viiø7'))
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


def handleAddedTones(dcmlChord: str) -> str:
    '''
    Converts DCML added-tone syntax to music21.

    >>> romanText.tsvConverter.handleAddedTones('V(64)')
    'Cad64'

    >>> romanText.tsvConverter.handleAddedTones('i(4+2)')
    'i[no3][add4][add2]'

    >>> romanText.tsvConverter.handleAddedTones('Viio7(b4-5)/V')
    'Viio7[no3][no5][addb4]/V'

    When in root position, 7 does not replace 8:
    >>> romanText.tsvConverter.handleAddedTones('vi(#74)')
    'vi[no3][add#7][add4]'

    When not in root position, 7 does replace 8:
    >>> romanText.tsvConverter.handleAddedTones('ii6(11#7b6)')
    'ii6[no8][no5][add11][add#7][addb6]'

    '0' can be used to indicate root-replacement by 7 in a root-position chord.
    We need to change '0' to '7' because music21 changes the 0 to 'o' (i.e.,
    a diminished chord).
    >>> romanText.tsvConverter.handleAddedTones('i(#0)')
    'i[no1][add#7]'
    '''
    m = re.match(
        r'(?P<primary>.*?(?P<figure>\d*(?:/\d+)*))\((?P<added_tones>.*)\)(?P<secondary>/.*)?',
        dcmlChord
    )
    if not m:
        return dcmlChord
    primary = m.group('primary')
    added_tones = m.group('added_tones')
    secondary = m.group('secondary') if m.group('secondary') is not None else ''
    figure = m.group('figure')
    if primary == 'V' and added_tones == '64':
        return 'Cad64' + secondary
    added_tone_tuples: list[tuple[str, str, str, str]] = re.findall(
        r'''
            (\+|-)?  # indicates whether to add or remove chord factor
            (\^|v)?  # indicates whether tone replaces chord factor above/below
            (\#+|b+)?  # alteration
            (1\d|\d)  # figures 0-19, in practice 0-14
        ''',
        added_tones,
        re.VERBOSE
    )
    additions: list[str] = []
    omissions: list[str] = []
    if figure in ('', '5', '53', '5/3', '3', '7'):
        omission_threshold = 7
    else:
        omission_threshold = 8
    for added_or_removed, above_or_below, alteration, factor_str in added_tone_tuples:
        if added_or_removed == '-':
            omissions.append(f'[no{factor_str}]')
            continue
        factor = int(factor_str)
        if added_or_removed == '+' or factor >= omission_threshold:
            replace_above = None
        elif factor in (1, 3, 5):
            replace_above = None
        elif factor in (2, 4, 6):
            # added scale degrees 2, 4, 6 replace lower neighbor unless
            #   - alteration = #
            #   - above_or_below = ^
            replace_above = alteration == '#' or above_or_below == '^'
        else:
            # Do we need to handle double sharps/flats?
            replace_above = alteration != 'b' and above_or_below != 'v'
        if replace_above is not None:
            if replace_above:
                omissions.append(f'[no{factor + 1}]')
            else:
                omissions.append(f'[no{factor - 1}]')
        if factor == 0:
            factor = 7
        additions.append(f'[add{alteration}{factor}]')
    return primary + ''.join(omissions) + ''.join(additions) + secondary


def localKeyAsRn(local_key: key.Key, global_key: key.Key) -> str:
    '''
    Takes two music21.key.Key objects and returns the roman numeral for
    `local_key` relative to `global_key`.

    >>> k1 = key.Key('C')
    >>> k2 = key.Key('e')
    >>> romanText.tsvConverter.localKeyAsRn(k1, k2)
    'VI'
    >>> k3 = key.Key('C#')
    >>> romanText.tsvConverter.localKeyAsRn(k3, k2)
    '#VI'
    >>> romanText.tsvConverter.localKeyAsRn(k2, k1)
    'iii'
    '''
    letter = local_key.tonicPitchNameWithCase
    rn = roman.RomanNumeral(
        'i' if letter.islower() else 'I', keyOrScale=local_key
    )
    r = roman.romanNumeralFromChord(chord.Chord(rn.pitches), keyObj=global_key)
    # Temporary hack: for some reason this gives VI and VII instead of #VI and #VII *only*
    #   when local_key is major and global_key is minor.
    # see issue at https://github.com/cuthbertLab/music21/issues/1349#issue-1327713452
    if (local_key.mode == 'major' and global_key.mode == 'minor'
            and r.romanNumeral in ('VI', 'VII')
            and (r.pitchClasses[0] - global_key.pitches[0].pitchClass) % 12 in (9, 11)):
        return '#' + r.romanNumeral
    return r.romanNumeral

def isMinor(test_key: str) -> bool:
    '''
    Checks whether a key is minor or not simply by upper vs lower case.

    >>> romanText.tsvConverter.isMinor('F')
    False

    >>> romanText.tsvConverter.isMinor('f')
    True
    '''
    return test_key == test_key.lower()


def characterSwaps(preString: str, minor: bool = True, direction: str = 'm21-DCML') -> str:
    '''
    Character swap function to coordinate between the two notational versions, for instance
    swapping between '%' and '/o' for the notation of half diminished (for example).

    >>> testStr = 'ii%'
    >>> romanText.tsvConverter.characterSwaps(testStr, minor=False, direction='DCML-m21')
    'iiø'
    '''
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

    return preString


def getLocalKey(local_key: str, global_key: str, convertDCMLToM21: bool = False) -> str:
    '''
    Re-casts comparative local key (e.g. 'V of G major') in its own terms ('D').

    >>> romanText.tsvConverter.getLocalKey('V', 'G')
    'D'

    >>> romanText.tsvConverter.getLocalKey('ii', 'C')
    'd'

    >>> romanText.tsvConverter.getLocalKey('i', 'C')
    'c'

    By default, assumes an m21 input, and operates as such:

    >>> romanText.tsvConverter.getLocalKey('#vii', 'a')
    'g#'

    Set convert=True to convert from DCML to m21 formats. Hence;

    >>> romanText.tsvConverter.getLocalKey('vii', 'a', convertDCMLToM21=True)
    'g'


    '''
    if convertDCMLToM21:
        local_key = characterSwaps(local_key, minor=isMinor(global_key[0]), direction='DCML-m21')

    asRoman = roman.RomanNumeral(
        local_key,
        global_key,
        sixthMinor=roman.Minor67Default.FLAT,
        seventhMinor=roman.Minor67Default.FLAT
    )
    rt = asRoman.root().name
    if asRoman.isMajorTriad():
        newKey = rt.upper()
    elif asRoman.isMinorTriad():
        newKey = rt.lower()
    else:  # pragma: no cover
        raise ValueError('local key must be major or minor')

    return newKey


def getSecondaryKey(rn: str, local_key: str) -> str:
    '''
    Separates comparative Roman-numeral for tonicizations like 'V/vi' into the component parts of
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
        test_files = {
            1: ('tsvEg_v1.tsv',),
            2: ('tsvEg_v2major.tsv', 'tsvEg_v2minor.tsv'),
        }
        for version in (1, 2):  # test both versions
            for name in test_files[version]:
                # A short and improbably complicated test case complete with:
                # '@none' (rest entry), '/' relative root, and time signature changes.
                path = common.getSourceFilePath() / 'romanText' / name

                if 'minor' not in name:
                    handler = TsvHandler(path, dcml_version=version)
                    headers = DCML_HEADERS[version]
                    chord_i = headers.index('chord')
                    # Raw
                    # not sure about v1 but in v2 '.C.I6' is 'label', not 'chord'
                    self.assertEqual(handler.tsvData[0][chord_i], 'I6' if version == 2 else '.C.I6')
                    self.assertEqual(handler.tsvData[1][chord_i], '#viio6/ii')

                    # Chords
                    handler.tsvToChords()
                    testTabChord1 = handler.chordList[0]  # Also tests makeTabChord()
                    testTabChord2 = handler.chordList[1]
                    self.assertIsInstance(testTabChord1, TabChordBase)
                    self.assertEqual(testTabChord1.combinedChord, 'I6' if version == 2 else '.C.I6')
                    self.assertEqual(testTabChord1.numeral, 'I')
                    self.assertEqual(testTabChord2.combinedChord, '#viio6/ii')
                    self.assertEqual(testTabChord2.numeral, '#vii')

                    # Change Representation
                    self.assertEqual(testTabChord1.representationType, 'DCML')
                    testTabChord1._changeRepresentation()
                    self.assertEqual(testTabChord1.numeral, 'I')
                    testTabChord2._changeRepresentation()
                    self.assertEqual(testTabChord2.numeral, '#vii')

                    # M21 RNs
                    m21Chord1 = testTabChord1.tabToM21()
                    m21Chord2 = testTabChord2.tabToM21()
                    # MIEs in v1, .figure is 'I' rather than 'I6'. This seems wrong
                    # but leaving the implementation as-is.
                    self.assertEqual(m21Chord1.figure, 'I6' if version == 2 else 'I')
                    self.assertEqual(m21Chord2.figure, '#viio6/ii')
                    self.assertEqual(m21Chord1.key.name, 'C major')
                    self.assertEqual(m21Chord2.key.name, 'C major')

                    # M21 stream
                    out_stream = handler.toM21Stream()
                    self.assertEqual(
                        out_stream.parts[0].measure(1)[roman.RomanNumeral][0].figure,
                        'I6' if version == 2 else 'I'
                    )

                # test tsv -> m21 -> tsv -> m21; compare m21 streams to make sure
                #   they're equal
                envLocal = environment.Environment()

                forward1 = TsvHandler(path, dcml_version=version)
                stream1 = forward1.toM21Stream()

                # Write back to tsv
                temp_tsv2 = envLocal.getTempFile()
                M21toTSV(stream1, dcml_version=version).write(temp_tsv2)

                # Convert back to m21 again
                forward2 = TsvHandler(temp_tsv2, dcml_version=version)
                stream2 = forward2.toM21Stream()
                os.remove(temp_tsv2)

                # Ensure that both m21 streams are the same
                self.assertEqual(len(stream1.recurse()), len(stream2.recurse()))
                for i, (item1, item2) in enumerate(zip(
                    stream1[harmony.Harmony], stream2[harmony.Harmony]
                )):
                    self.assertEqual(
                        item1, item2, msg=f'item {i}, version {version}: {item1} != {item2}'
                    )
                first_harmony = stream1[harmony.Harmony].first()
                first_offset = first_harmony.activeSite.offset + first_harmony.offset
                self.assertEqual(
                    sum(
                        h.quarterLength
                        for h in stream1.recurse().getElementsByClass(harmony.Harmony)
                    ),
                    stream1.quarterLength - first_offset
                )

    def testM21ToTsv(self):
        import os
        from music21 import corpus

        bachHarmony = corpus.parse('bach/choraleAnalyses/riemenschneider001.rntxt')
        for version in (1, 2):
            initial = M21toTSV(bachHarmony, dcml_version=version)
            tsvData = initial.tsvData
            numeral_i = DCML_HEADERS[version].index('numeral')
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
        self.assertTrue(isMinor('f'))
        self.assertFalse(isMinor('F'))

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


    def testGetLocalKey(self):
        test1 = getLocalKey('V', 'G')
        self.assertEqual(test1, 'D')

        test2 = getLocalKey('ii', 'C')
        self.assertEqual(test2, 'd')

        test3 = getLocalKey('#vii', 'a')
        self.assertEqual(test3, 'g#')

        test4 = getLocalKey('vii', 'a', convertDCMLToM21=True)
        self.assertEqual(test4, 'g')

    def testGetSecondaryKey(self):
        testRN = 'V/vi'
        testLocalKey = 'D'

        veryLocalKey = getSecondaryKey(testRN, testLocalKey)

        self.assertIsInstance(veryLocalKey, str)
        self.assertEqual(veryLocalKey, 'b')

    def testRepeats(self):
        def _test_ending_contents(
            rb: spanner.RepeatBracket, expectedMeasures: t.List[str]
        ) -> None:
            measure_nos = [m.measureNumberWithSuffix() for m in rb[stream.Measure]]
            self.assertEqual(measure_nos, expectedMeasures)

        path = common.getSourceFilePath() / 'romanText' / 'tsvEg_v2_repeats.tsv'

        # The test file corresponds to the following romanText but is somewhat
        #   harder to read:
        # Time Signature: 2/4
        # m1 C: I
        # m2a V :||
        # m2b I

        handler = TsvHandler(path, dcml_version=2)
        stream1 = handler.toM21Stream()
        rb_iter = stream1[spanner.RepeatBracket]
        self.assertEqual(len(rb_iter), 2)
        first_ending, second_ending = rb_iter
        _test_ending_contents(first_ending, ['2a'])
        _test_ending_contents(second_ending, ['2b'])

# ------------------------------------------------------------------------------


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
