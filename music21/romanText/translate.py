# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         romanText/translate.py
# Purpose:      Translation routines for roman numeral analysis text files
#
# Authors:      Christopher Ariza
#               Michael Scott Asato Cuthbert
#
# Copyright:    Copyright © 2011-2023 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
Translation routines for roman numeral analysis text files, as defined
and demonstrated by Dmitri Tymoczko.  Also used for the ClercqTemperley
format which is similar but a little different.

This module is really only needed for people extending the parser,
for others it's simple to get Harmony, RomanNumeral, Key (or KeySignature)
and other objects out of an rntxt file by running this:


>>> monteverdi = corpus.parse('monteverdi/madrigal.3.1.rntxt')
>>> monteverdi.show('text')
{0.0} <music21.metadata.Metadata object at 0x...>
{0.0} <music21.stream.Part ...>
    {0.0} <music21.stream.Measure 1 offset=0.0>
        {0.0} <music21.key.KeySignature of 1 flat>
        {0.0} <music21.meter.TimeSignature 4/4>
        {0.0} <music21.roman.RomanNumeral vi in F major>
        {3.0} <music21.roman.RomanNumeral V[no3] in F major>
    {4.0} <music21.stream.Measure 2 offset=4.0>
        {0.0} <music21.roman.RomanNumeral I in F major>
        {3.0} <music21.roman.RomanNumeral IV in F major>
    ...

Then the stream can be analyzed with something like this, storing
the data to make a histogram of scale degree usage within a key:

>>> degreeDictionary = {}
>>> for el in monteverdi.recurse():
...    if isinstance(el, roman.RomanNumeral):
...         print(f'{el.figure} {el.key}')
...         for p in el.pitches:
...              degree, accidental = el.key.getScaleDegreeAndAccidentalFromPitch(p)
...              if accidental is None:
...                   degreeString = str(degree)
...              else:
...                   degreeString = str(degree) + str(accidental.modifier)
...              if degreeString not in degreeDictionary:
...                   degreeDictionary[degreeString] = 1
...              else:
...                   degreeDictionary[degreeString] += 1
...              degTuple = (str(p), degreeString)
...              print(degTuple)
    vi F major
    ('D5', '6')
    ('F5', '1')
    ('A5', '3')
    V[no3] F major
    ('C5', '5')
    ('G5', '2')
    I F major
    ('F4', '1')
    ('A4', '3')
    ('C5', '5')
    ...
    V6 g minor
    ('F#5', '7#')
    ('A5', '2')
    ('D6', '5')
    i g minor
    ('G4', '1')
    ('B-4', '3')
    ('D5', '5')
    ...

Now if we'd like we can get a Histogram of the data.
It's a little complex, but worth seeing in full:

>>> import operator
>>> histogram = graph.primitives.GraphHistogram()
>>> i = 0
>>> data = []
>>> xLabels = []
>>> values = []
>>> ddList = list(degreeDictionary.items())
>>> for deg,value in sorted(ddList, key=operator.itemgetter(1), reverse=True):
...    data.append((i, degreeDictionary[deg]), )
...    xLabels.append((i+.5, deg), )
...    values.append(degreeDictionary[deg])
...    i += 1
>>> histogram.data = data


These commands give nice labels for the data; optional:

>>> histogram.setIntegerTicksFromData(values, 'y')
>>> histogram.setTicks('x', xLabels)
>>> histogram.setAxisLabel('x', 'ScaleDegree')

Now generate the histogram:

>>> #_DOCS_HIDE histogram.process()

.. image:: images/romanTranslatePitchDistribution.*
    :width: 600


OMIT_FROM_DOCS

>>> x = converter.parse('romantext: m1 a: VI')
>>> [str(p) for p in x[roman.RomanNumeral].first().pitches]
['F5', 'A5', 'C6']

>>> x = converter.parse('romantext: m1 a: vi')
>>> [str(p) for p in x[roman.RomanNumeral].first().pitches]
['F#5', 'A5', 'C#6']

>>> [str(p) for p in
...  converter.parse('romantext: m1 a: vio'
...                  )[roman.RomanNumeral].first().pitches]
['F#5', 'A5', 'C6']
'''
from __future__ import annotations

import copy
import textwrap
import traceback
import typing as t
import unittest

from music21 import bar
from music21 import base
from music21 import common
from music21 import environment
from music21 import exceptions21
from music21 import harmony
from music21 import key
from music21 import metadata
from music21 import meter
from music21 import note
from music21 import repeat
from music21 import roman
from music21.romanText import rtObjects
from music21 import spanner
from music21 import stream
from music21 import tie

environLocal = environment.Environment('romanText.translate')

ROMANTEXT_VERSION = 1.0


USE_RN_CACHE = False
# Not currently using rnCache because of problems with PivotChords,
# See mail from Dmitri, 30 September 2014

# ------------------------------------------------------------------------------


class RomanTextTranslateException(exceptions21.Music21Exception):
    pass


class RomanTextUnprocessedToken(base.ElementWrapper):
    pass


class RomanTextUnprocessedMetadata(base.Music21Object):
    def __init__(self, tag='', data='', **keywords):
        super().__init__(**keywords)
        self.tag = tag
        self.data = data

    def _reprInternal(self) -> str:
        return f'{self.tag}: {self.data}'


def _copySingleMeasure(rtTagged, p, kCurrent):
    '''
    Given a RomanText token, a Part used as the current container,
    and the current Key, return a Measure copied from the past of the Part.

    This is used in cases of definitions such as:
    m23=m21
    '''
    m = None
    # copy from a past location; need to change key
    # environLocal.printDebug(['calling _copySingleMeasure()'])
    targetNumber, unused_targetRepeat = rtTagged.getCopyTarget()
    if len(targetNumber) > 1:  # pragma: no cover
        # this is an encoding error
        raise RomanTextTranslateException(
            'a single measure cannot define a copy operation for multiple measures')
    # TODO: ignoring repeat letters
    target = targetNumber[0]
    for mPast in p.getElementsByClass(stream.Measure):
        if mPast.number == target:
            try:
                m = copy.deepcopy(mPast)
            except TypeError:  # pragma: no cover
                raise RomanTextTranslateException(
                    f'Failed to copy measure {mPast.number}:'
                    + ' did you perhaps parse an RTOpus object with romanTextToStreamScore '
                    + 'instead of romanTextToStreamOpus?')
            m.number = rtTagged.number[0]
            # update all keys
            for rnPast in m.getElementsByClass(roman.RomanNumeral):
                if kCurrent is None:  # pragma: no cover
                    # should not happen
                    raise RomanTextTranslateException(
                        'attempting to copy a measure but no past key definitions are found')
                if rnPast.followsKeyChange:
                    kCurrent = rnPast.key
                elif rnPast.pivotChord is not None:
                    kCurrent = rnPast.pivotChord.key
                else:
                    rnPast.key = kCurrent
                if rnPast.secondaryRomanNumeral is not None:
                    newRN = roman.RomanNumeral(
                        rnPast.figure, copy.deepcopy(kCurrent)
                    )
                    newRN.writeAsChord = True
                    newRN.duration = copy.deepcopy(rnPast.duration)
                    newRN.lyrics = copy.deepcopy(rnPast.lyrics)
                    m.replace(rnPast, newRN)

            break
    return m, kCurrent


def _copyMultipleMeasures(rtMeasure: rtObjects.RTMeasure,
                          p: stream.Part,
                          kCurrent: key.Key | None):
    '''
    Given a RomanText token for a RTMeasure, a
    Part used as the current container, and the current Key,
    return a Measure range copied from the past of the Part.

    This is used for cases such as:
    m23-25 = m20-22
    '''
    # the key provided needs to be the current key
    # environLocal.printDebug(['calling _copyMultipleMeasures()'])

    targetNumbers, unused_targetRepeat = rtMeasure.getCopyTarget()
    if len(targetNumbers) == 1:   # pragma: no cover
        # this is an encoding error
        raise RomanTextTranslateException('a multiple measure range cannot copy a single measure')
    # TODO: ignoring repeat letters
    targetStart = targetNumbers[0]
    targetEnd = targetNumbers[1]

    if rtMeasure.number[1] - rtMeasure.number[0] != targetEnd - targetStart:  # pragma: no cover
        raise RomanTextTranslateException(
            'both the source and destination sections need to have the same number of measures')
    if rtMeasure.number[0] < targetEnd:  # pragma: no cover
        raise RomanTextTranslateException(
            'the source section cannot overlap with the destination section')

    measures = []
    for mPast in p.getElementsByClass(stream.Measure):
        if mPast.number in range(targetStart, targetEnd + 1):
            try:
                m = copy.deepcopy(mPast)
            except TypeError:  # pragma: no cover
                raise RomanTextTranslateException(
                    'Failed to copy measure {0} to measure range {1}-{2}: '.format(
                        mPast.number, targetStart, targetEnd)
                    + 'did you perhaps parse an RTOpus object with romanTextToStreamScore '
                    + 'instead of romanTextToStreamOpus?')

            m.number = rtMeasure.number[0] + mPast.number - targetStart
            measures.append(m)
            # update all keys
            allRNs = list(m.getElementsByClass(roman.RomanNumeral))
            for rnPast in allRNs:
                if kCurrent is None:  # pragma: no cover
                    # should not happen
                    raise RomanTextTranslateException(
                        'attempting to copy a measure but no past key definitions are found')
                if rnPast.followsKeyChange:
                    kCurrent = rnPast.key
                elif rnPast.pivotChord is not None:
                    kCurrent = rnPast.pivotChord.key
                else:
                    rnPast.key = kCurrent
                if rnPast.secondaryRomanNumeral is not None:
                    newRN = roman.RomanNumeral(
                        rnPast.figure, copy.deepcopy(kCurrent)
                    )
                    newRN.writeAsChord = True
                    newRN.duration = copy.deepcopy(rnPast.duration)
                    newRN.lyrics = copy.deepcopy(rnPast.lyrics)
                    m.replace(rnPast, newRN)

        if mPast.number == targetEnd:
            break
    return measures, kCurrent


def _getKeyAndPrefix(rtKeyOrString):
    '''
    Given an RTKey specification, return the Key and a string prefix based
    on the tonic:

    >>> romanText.translate._getKeyAndPrefix('c')
    (<music21.key.Key of c minor>, 'c: ')
    >>> romanText.translate._getKeyAndPrefix('F#')
    (<music21.key.Key of F# major>, 'F#: ')
    >>> romanText.translate._getKeyAndPrefix('Eb')
    (<music21.key.Key of E- major>, 'E-: ')
    >>> romanText.translate._getKeyAndPrefix('Bb')
    (<music21.key.Key of B- major>, 'B-: ')
    >>> romanText.translate._getKeyAndPrefix('bb')
    (<music21.key.Key of b- minor>, 'b-: ')
    >>> romanText.translate._getKeyAndPrefix('b#')
    (<music21.key.Key of b# minor>, 'b#: ')
    >>> romanText.translate._getKeyAndPrefix('Bbb')
    (<music21.key.Key of B-- major>, 'B--: ')
    '''
    if isinstance(rtKeyOrString, str):
        rtKeyOrString = key.convertKeyStringToMusic21KeyString(rtKeyOrString)
        k = key.Key(rtKeyOrString)
    else:
        k = rtKeyOrString.getKey()
    tonicName = k.tonic.name
    if k.mode == 'minor':
        tonicName = tonicName.lower()
    prefix = tonicName + ': '
    return k, prefix


# Cache each of the created keys so that we don't recreate them.
_rnKeyCache: dict[tuple[str, str], roman.RomanNumeral] = {}


class PartTranslator:
    '''
    A refactoring of the previously massive romanTextToStreamScore function
    to allow for more fine-grained testing (eventually), and to
    get past the absurdly high number of nested blocks (the previous translator
    was written under severe time constraints).
    '''

    def __init__(self, md=None):
        if md is None:
            md = metadata.Metadata()
        self.md = md  # global metadata object
        self.p = stream.Part()

        self.romanTextVersion = ROMANTEXT_VERSION

        # ts indication are found in header, and also found elsewhere
        self.tsCurrent = meter.TimeSignature('4/4')  # create default 4/4
        self.tsAtTimeOfLastChord = self.tsCurrent
        self.tsSet = False  # store if set to a measure
        self.lastMeasureToken = None
        self.lastMeasureNumber = 0
        self.previousRn = None
        self.keySigCurrent = None
        self.setKeySigFromFirstKeyToken = True  # set a keySignature
        self.foundAKeySignatureSoFar = False
        self.kCurrent, unused_prefixLyric = _getKeyAndPrefix('C')  # default if none defined
        self.prefixLyric = ''

        self.sixthMinor = roman.Minor67Default.CAUTIONARY
        self.seventhMinor = roman.Minor67Default.CAUTIONARY

        self.repeatEndings = {}

        # reset for each measure
        self.currentMeasureToken = None
        self.previousChordInMeasure = None
        self.pivotChordPossible = False
        self.numberOfAtomsInCurrentMeasure = 0
        self.setKeyChangeToken = False
        self.currentOffsetInMeasure = 0.0

    def translateTokens(self, tokens):
        for token in tokens:
            try:
                self.translateOneLineToken(token)
            except Exception:  # pylint: disable=broad-exception-caught
                tracebackMessage = traceback.format_exc()
                raise RomanTextTranslateException(
                    f'At line {token.lineNumber} for token {token}, '
                    + f'an exception was raised: \n{tracebackMessage}')

        p = self.p
        p.coreElementsChanged()
        fixPickupMeasure(p)
        p.makeBeams(inPlace=True)
        p.makeAccidentals(inPlace=True)
        _addRepeatsFromRepeatEndings(p, self.repeatEndings)  # 1st and second endings...
        return p

    def translateOneLineToken(self, lineToken: rtObjects.RTTagged):
        # noinspection SpellCheckingInspection
        '''
        Translates one line token and set the current settings.

        A token in this case consists of an entire line's worth.
        It might be a token such as 'Title: Neko Funjatta' or
        a composite token such as 'm23 b4 IV6'
        '''
        md = self.md
        # environLocal.printDebug(['token', t])

        # most common case first...
        if lineToken.isMeasure():
            if t.TYPE_CHECKING:
                assert isinstance(lineToken, rtObjects.RTMeasure)
            self.translateMeasureLineToken(lineToken)

        elif lineToken.isTitle():
            md.add('title', lineToken.data)

        elif lineToken.isWork():
            md.add('alternativeTitle', lineToken.data)

        elif lineToken.isPiece():
            md.add('alternativeTitle', lineToken.data)

        elif lineToken.isComposer():
            md.add('composer', lineToken.data)

        elif lineToken.isMovement():
            md.add('movementNumber', lineToken.data)

        elif lineToken.isAnalyst():
            md.add('analyst', lineToken.data)

        elif lineToken.isProofreader():
            md.add('proofreader', lineToken.data)

        elif lineToken.isTimeSignature():
            try:
                self.tsCurrent = meter.TimeSignature(lineToken.data)
                self.tsSet = False
            except exceptions21.Music21Exception:  # pragma: no cover
                environLocal.warn(f'Could not parse TimeSignature tag: {lineToken.data!r}')

            # environLocal.printDebug(['tsCurrent:', tsCurrent])

        elif lineToken.isKeySignature():
            self.parseKeySignatureTag(lineToken)

        elif lineToken.isSixthMinor() or lineToken.isSeventhMinor():
            self.setMinorRootParse(lineToken)

        elif lineToken.isVersion():
            try:
                self.romanTextVersion = float(lineToken.data)
            except ValueError:  # pragma: no cover
                environLocal.warn(f'Could not parse RTVersion tag: {lineToken.data!r}')

        elif isinstance(lineToken, rtObjects.RTTagged):
            otherMetadata = RomanTextUnprocessedMetadata(lineToken.tag, lineToken.data)
            self.p.append(otherMetadata)

        else:  # pragma: no cover
            unprocessed = RomanTextUnprocessedToken(lineToken)
            self.p.append(unprocessed)

    def setMinorRootParse(self, rtTagged: rtObjects.RTTagged):
        '''
        Set Roman Numeral parsing standards from a token.

        >>> pt = romanText.translate.PartTranslator()
        >>> pt.sixthMinor
        <Minor67Default.CAUTIONARY: 2>

        >>> tag = romanText.rtObjects.RTTagged('SixthMinor: Flat')
        >>> tag.isSixthMinor()
        True
        >>> pt.setMinorRootParse(tag)
        >>> pt.sixthMinor
        <Minor67Default.FLAT: 4>

        Harmonic sets to FLAT for sixth and SHARP for seventh

        >>> for config in 'flat sharp quality cautionary harmonic'.split():
        ...     tag = romanText.rtObjects.RTTagged('Seventh Minor: ' + config)
        ...     pt.setMinorRootParse(tag)
        ...     print(pt.seventhMinor)
        Minor67Default.FLAT
        Minor67Default.SHARP
        Minor67Default.QUALITY
        Minor67Default.CAUTIONARY
        Minor67Default.SHARP

        >>> tag = romanText.rtObjects.RTTagged('Sixth Minor: harmonic')
        >>> pt.setMinorRootParse(tag)
        >>> print(pt.sixthMinor)
        Minor67Default.FLAT


        Unknown settings raise a `RomanTextTranslateException`

        >>> tag = romanText.rtObjects.RTTagged('Seventh Minor: asdf')
        >>> pt.setMinorRootParse(tag)
        Traceback (most recent call last):
        music21.romanText.translate.RomanTextTranslateException:
            Cannot parse setting vi or vii parsing: 'asdf'
        '''
        tData = rtTagged.data.lower()
        if tData == 'flat':
            tEnum = roman.Minor67Default.FLAT
        elif tData == 'sharp':
            tEnum = roman.Minor67Default.SHARP
        elif tData == 'quality':
            tEnum = roman.Minor67Default.QUALITY
        elif tData in ('courtesy', 'cautionary'):
            tEnum = roman.Minor67Default.CAUTIONARY
        elif tData == 'harmonic':
            if rtTagged.isSixthMinor():
                tEnum = roman.Minor67Default.FLAT
            else:
                tEnum = roman.Minor67Default.SHARP
        else:
            raise RomanTextTranslateException(
                f'Cannot parse setting vi or vii parsing: {tData!r}')

        if rtTagged.isSixthMinor():
            self.sixthMinor = tEnum
        else:
            self.seventhMinor = tEnum

    def translateMeasureLineToken(self, measureLineToken: rtObjects.RTMeasure):
        '''
        Translate a measure token consisting of a single line such as::

            m21 b3 V b4 C: IV

        Or it might be a variant measure, or a copy instruction.
        '''
        p = self.p
        skipsPriorMeasures = ((measureLineToken.number[0] > self.lastMeasureNumber + 1)
                               and (self.previousRn is not None))
        isSingleMeasureCopy = (len(measureLineToken.number) == 1
                               and measureLineToken.isCopyDefinition)
        isMultipleMeasureCopy = (len(measureLineToken.number) > 1)

        # environLocal.printDebug(['handling measure token:', measureLineToken])
        # if measureLineToken.number[0] % 10 == 0:
        #    print('at number ' + str(measureLineToken.number[0]))
        if measureLineToken.variantNumber is not None:
            # TODO(msc): parse variant numbers
            # environLocal.printDebug([f' skipping variant: {measureLineToken}'])
            return
        if measureLineToken.variantLetter is not None:
            # TODO(msc): parse variant letters
            # environLocal.printDebug([f' skipping variant letter: {measureLineToken}'])
            return

        # if this measure number is more than 1 greater than the last
        # defined measure number, and the previous chord is not None,
        # then fill with copies of the last-defined measure
        if skipsPriorMeasures:
            self.fillToMeasureToken(measureLineToken)

        # create a new measure or copy a past measure
        if isSingleMeasureCopy:  # if not a range
            p.coreElementsChanged()
            m, self.kCurrent = _copySingleMeasure(measureLineToken, p, self.kCurrent)
            p.coreAppend(m)
            self.lastMeasureNumber = m.number
            self.lastMeasureToken = measureLineToken
            romans = m.getElementsByClass(roman.RomanNumeral)
            if romans:
                self.previousRn = romans[-1]

        elif isMultipleMeasureCopy:
            p.coreElementsChanged()
            measures, self.kCurrent = _copyMultipleMeasures(measureLineToken, p, self.kCurrent)
            p.append(measures)  # appendCore does not work with list
            self.lastMeasureNumber = measures[-1].number
            self.lastMeasureToken = measureLineToken
            romans = measures[-1].getElementsByClass(roman.RomanNumeral)
            if romans:
                self.previousRn = romans[-1]

        else:
            m = self.translateSingleMeasure(measureLineToken)
            if m.duration.quarterLength == 0:
                self.fillMeasureFromPreviousRn(m)
            p.coreAppend(m)

    def fillToMeasureToken(self, measureToken: rtObjects.RTMeasure):
        '''
        Create a series of measures which extend the previous RN until the measure number
        implied by `measureToken`.
        '''
        p = self.p
        for i in range(self.lastMeasureNumber + 1, measureToken.number[0]):
            mFill = stream.Measure()
            mFill.number = i
            self.fillMeasureFromPreviousRn(mFill)
            appendMeasureToRepeatEndingsDict(self.lastMeasureToken,
                                             mFill,
                                             self.repeatEndings, i)
            p.coreAppend(mFill)
        self.lastMeasureNumber = measureToken.number[0] - 1
        self.lastMeasureToken = measureToken

    def fillMeasureFromPreviousRn(self, mFill: stream.Measure) -> None:
        if self.previousRn is not None:
            newRn = copy.deepcopy(self.previousRn)
            newRn.lyric = ''
            # set to entire bar duration and tie
            newRn.duration = copy.deepcopy(self.tsAtTimeOfLastChord.barDuration)
            if self.previousRn.tie is None:
                self.previousRn.tie = tie.Tie('start')
            else:
                self.previousRn.tie.type = 'continue'
            # set to stop for now; may extend on next iteration
            newRn.tie = tie.Tie('stop')
            self.previousRn = newRn
            mFill.append(newRn)

    def parseKeySignatureTag(self, rtTagged: rtObjects.RTTagged):
        '''
        Parse a key signature tag which has already been determined to
        be a key signature.

        >>> tag = romanText.rtObjects.RTTagged('KeySignature: -4')
        >>> tag.isKeySignature()
        True
        >>> tag.data
        '-4'

        >>> pt = romanText.translate.PartTranslator()
        >>> pt.keySigCurrent is None
        True
        >>> pt.setKeySigFromFirstKeyToken
        True
        >>> pt.foundAKeySignatureSoFar
        False

        >>> pt.parseKeySignatureTag(tag)
        >>> pt.keySigCurrent
        <music21.key.KeySignature of 4 flats>
        >>> pt.setKeySigFromFirstKeyToken
        False
        >>> pt.foundAKeySignatureSoFar
        True

        >>> tag = romanText.rtObjects.RTTagged('KeySignature: xyz')
        >>> pt.parseKeySignatureTag(tag)
        Traceback (most recent call last):
        music21.romanText.translate.RomanTextTranslateException:
            Cannot parse key signature: 'xyz'
        '''
        data = rtTagged.data
        if data == '':
            self.keySigCurrent = key.KeySignature(0)
        elif data == 'Bb':
            self.keySigCurrent = key.KeySignature(-1)
        else:
            try:
                dataVal = int(data)
                self.keySigCurrent = key.KeySignature(dataVal)
            except ValueError:
                raise RomanTextTranslateException(f'Cannot parse key signature: {data!r}')
        self.setKeySigFromFirstKeyToken = False
        # environLocal.printDebug(['keySigCurrent:', keySigCurrent])
        self.foundAKeySignatureSoFar = True

    def translateSingleMeasure(self, measureToken):
        '''
        Given a measureToken, return a `stream.Measure` object with
        the appropriate atoms set.
        '''
        self.currentMeasureToken = measureToken
        m = stream.Measure()
        m.number = measureToken.number[0]
        appendMeasureToRepeatEndingsDict(measureToken, m, self.repeatEndings)
        self.lastMeasureNumber = measureToken.number[0]
        self.lastMeasureToken = measureToken

        if not self.tsSet:
            m.timeSignature = self.tsCurrent
            self.tsSet = True  # only set when changed
        if not self.setKeySigFromFirstKeyToken and self.keySigCurrent is not None:
            m.insert(0, self.keySigCurrent)
            self.setKeySigFromFirstKeyToken = True  # only set when changed

        self.currentOffsetInMeasure = 0.0  # start offsets at zero
        self.previousChordInMeasure = None
        self.pivotChordPossible = False
        self.numberOfAtomsInCurrentMeasure = len(measureToken.atoms)
        # first RomanNumeral object after a key change should have this set to True
        self.setKeyChangeToken = False
        for i, a in enumerate(measureToken.atoms):
            isLastAtomInMeasure = (i == self.numberOfAtomsInCurrentMeasure - 1)
            self.translateSingleMeasureAtom(a, m, isLastAtomInMeasure=isLastAtomInMeasure)

        # may need to adjust duration of last chord added
        if self.tsCurrent is not None:
            self.previousRn.quarterLength = (self.tsCurrent.barDuration.quarterLength
                                                - self.currentOffsetInMeasure)
        m.coreElementsChanged()
        return m

    def translateSingleMeasureAtom(self, a, m, *, isLastAtomInMeasure=False):
        '''
        Translate a single atom in a measure token.

        `a` is the Atom
        `m` is a `stream.Measure` object.

        Uses coreInsert and coreAppend methods, so must have `m.coreElementsChanged()`
        called afterwards.
        '''
        if (isinstance(a, rtObjects.RTKey)
                or (self.foundAKeySignatureSoFar is False
                    and isinstance(a, rtObjects.RTAnalyticKey))):
            self.setAnalyticKey(a)
            # insert at beginning of measure if at beginning
            #    -- for things like pickups.
            if m.number <= 1:
                m.coreInsert(0, self.kCurrent)
            else:
                m.coreInsert(self.currentOffsetInMeasure, self.kCurrent)
            self.foundAKeySignatureSoFar = True

        elif isinstance(a, rtObjects.RTKeySignature):
            try:  # this sets the keysignature but not the prefix text
                thisSig = a.getKeySignature()
            except (exceptions21.Music21Exception, ValueError):  # pragma: no cover
                raise RomanTextTranslateException(
                    f'cannot get key from {a.src} in line {self.currentMeasureToken.src}')
            # insert at beginning of measure if at beginning
            #     -- for things like pickups.
            if m.number <= 1:
                m.coreInsert(0, thisSig)
            else:
                m.coreInsert(self.currentOffsetInMeasure, thisSig)
            self.foundAKeySignatureSoFar = True

        elif isinstance(a, rtObjects.RTAnalyticKey):
            self.setAnalyticKey(a)

        elif isinstance(a, rtObjects.RTBeat):
            # set new offset based on beat
            try:
                newOffset = a.getOffset(self.tsCurrent)
            except ValueError:  # pragma: no cover
                raise RomanTextTranslateException(
                    'cannot properly get an offset from '
                    + f'beat data {a.src}'
                    + 'under timeSignature {0} in line {1}'.format(
                        self.tsCurrent,
                        self.currentMeasureToken.src))
            if (self.previousChordInMeasure is None
                    and self.previousRn is not None
                    and newOffset > 0):
                # setting a new beat before giving any chords
                firstChord = copy.deepcopy(self.previousRn)
                firstChord.quarterLength = newOffset
                firstChord.lyric = ''
                if self.previousRn.tie is None:
                    self.previousRn.tie = tie.Tie('start')
                else:
                    self.previousRn.tie.type = 'continue'
                firstChord.tie = tie.Tie('stop')
                self.previousRn = firstChord
                self.previousChordInMeasure = firstChord
                m.coreInsert(0, firstChord)
            self.pivotChordPossible = False
            self.currentOffsetInMeasure = newOffset

        elif isinstance(a, rtObjects.RTNoChord):
            # use source to evaluation roman
            self.tsAtTimeOfLastChord = self.tsCurrent
            cs = harmony.NoChord()
            m.coreInsert(self.currentOffsetInMeasure, cs)

            rn = note.Rest()
            if self.pivotChordPossible is False:
                # probably best to find duration
                if self.previousChordInMeasure is None:
                    pass  # use default duration
                else:  # update duration of previous chord in Measure
                    oPrevious = self.previousChordInMeasure.getOffsetBySite(m)
                    newQL = self.currentOffsetInMeasure - oPrevious
                    if newQL <= 0:  # pragma: no cover
                        raise RomanTextTranslateException(
                            f'too many notes in this measure: {self.currentMeasureToken.src}')
                    self.previousChordInMeasure.quarterLength = newQL
                self.prefixLyric = ''
                m.coreInsert(self.currentOffsetInMeasure, rn)
                self.previousChordInMeasure = rn
                self.previousRn = rn
                self.pivotChordPossible = False

        elif isinstance(a, rtObjects.RTChord):
            self.processRTChord(a, m, self.currentOffsetInMeasure)
        elif isinstance(a, rtObjects.RTRepeat):
            if isinstance(a, rtObjects.RTRepeatStop) and isLastAtomInMeasure:
                # This condition needs to be moved here because it is possible
                #   and indeed likely that an end repeat will have an offset of
                #   0 in the case that there is 0 or 1 harmonies in the measure.
                # Is it ok, however, that this condition will match if self.tsCurrent
                #   is None? Previously, that case was excluded below.
                m.rightBarline = bar.Repeat(direction='end')
                if self.tsCurrent is not None:
                    m.setElementOffset(
                        m.rightBarline, self.tsCurrent.barDuration.quarterLength
                    )
            elif self.currentOffsetInMeasure == 0:
                if isinstance(a, rtObjects.RTRepeatStart):
                    m.leftBarline = bar.Repeat(direction='start')
                else:
                    rtt = RomanTextUnprocessedToken(a)
                    m.coreInsert(self.currentOffsetInMeasure, rtt)
            elif (self.tsCurrent is not None
                    and self.tsCurrent.barDuration.quarterLength == self.currentOffsetInMeasure):
                if isinstance(a, rtObjects.RTRepeatStop):
                    m.rightBarline = bar.Repeat(direction='end')
                else:
                    rtt = RomanTextUnprocessedToken(a)
                    m.coreInsert(self.currentOffsetInMeasure, rtt)
            else:  # mid-measure repeat signs
                rtt = RomanTextUnprocessedToken(a)
                m.coreInsert(self.currentOffsetInMeasure, rtt)

        else:
            rtt = RomanTextUnprocessedToken(a)
            m.coreInsert(self.currentOffsetInMeasure, rtt)
            # environLocal.warn(f' Got an unknown token: {a}')

    def processRTChord(self, a, m, currentOffset):
        '''
        Process a single RTChord atom.
        '''
        # use source to evaluation roman
        self.tsAtTimeOfLastChord = self.tsCurrent
        try:
            aSrc = a.src
            # if kCurrent.mode == 'minor':
            #     if aSrc.lower().startswith('vi'):  # vi or vii w/ or w/o o
            #         if aSrc.upper() == a.src:  # VI or VII to bVI or bVII
            #             aSrc = 'b' + aSrc
            cacheTuple = (aSrc, self.kCurrent.tonicPitchNameWithCase)
            if USE_RN_CACHE and cacheTuple in _rnKeyCache:  # pragma: no cover
                # print('Got a match: ' + str(cacheTuple))
                # Problems with Caches not picking up pivot chords...
                #    Not faster, see below.
                rn = copy.deepcopy(_rnKeyCache[cacheTuple])
            else:
                # print('No match for: ' + str(cacheTuple))
                rn = roman.RomanNumeral(aSrc,
                                        copy.deepcopy(self.kCurrent),
                                        sixthMinor=self.sixthMinor,
                                        seventhMinor=self.seventhMinor,
                                        )
                rn.writeAsChord = True
                _rnKeyCache[cacheTuple] = rn
            # surprisingly, not faster... and more dangerous
            # rn = roman.RomanNumeral(aSrc, kCurrent)
            # # SLOWEST!!!
            # rn = roman.RomanNumeral(aSrc, kCurrent.tonicPitchNameWithCase)

            # >>> from timeit import timeit as t
            # >>> t('roman.RomanNumeral("IV", "c#")',
            # ...     'from music21 import roman', number=1000)
            # 45.75
            # >>> t('roman.RomanNumeral("IV", k)',
            # ...     'from music21 import roman, key; k = key.Key("c#")',
            # ...     number=1000)
            # 16.09
            # >>> t('roman.RomanNumeral("IV", copy.deepcopy(k))',
            # ...    'from music21 import roman, key; import copy;
            # ...     k = key.Key("c#")', number=1000)
            # 22.49
            # # key cache, does not help much...
            # >>> t('copy.deepcopy(r)', 'from music21 import roman; import copy;
            # ...        r = roman.RomanNumeral("IV", "c#")', number=1000)
            # 19.01

            if self.setKeyChangeToken is True:
                rn.followsKeyChange = True
                self.setKeyChangeToken = False
            else:
                rn.followsKeyChange = False
        except roman.RomanNumeralException:  # pragma: no cover
            # environLocal.printDebug(f' cannot create RN from: {a.src}')
            rn = note.Note()  # create placeholder

        if self.pivotChordPossible is False:
            # probably best to find duration
            if self.previousChordInMeasure is None:
                pass  # use default duration
            else:  # update duration of previous chord in Measure
                oPrevious = self.previousChordInMeasure.getOffsetBySite(m)
                newQL = currentOffset - oPrevious
                if newQL <= 0:  # pragma: no cover
                    raise RomanTextTranslateException(
                        f'too many notes in this measure: {self.currentMeasureToken.src}')
                self.previousChordInMeasure.quarterLength = newQL

            rn.addLyric(self.prefixLyric + a.src)
            self.prefixLyric = ''
            m.coreInsert(currentOffset, rn)
            self.previousChordInMeasure = rn
            self.previousRn = rn
            self.pivotChordPossible = True
        else:
            self.previousChordInMeasure.lyric += '//' + self.prefixLyric + a.src
            self.previousChordInMeasure.pivotChord = rn
            self.prefixLyric = ''
            self.pivotChordPossible = False

    def setAnalyticKey(self, a):
        '''
        Indicates a change in the analyzed key, not a change in anything
        else, such as the keySignature.
        '''
        try:  # this sets the key and the keysignature
            self.kCurrent, pl = _getKeyAndPrefix(a)
            self.prefixLyric += pl
        except:  # pragma: no cover
            raise RomanTextTranslateException(
                f'cannot get analytic key from {a.src} in line {self.currentMeasureToken.src}')
        self.setKeyChangeToken = True


def romanTextToStreamScore(rtHandler, inputM21=None):
    '''
    The main processing module for single-movement RomanText works.

    Given a romanText handler or string, return or fill a Score Stream.
    '''
    # accept a string directly; mostly for testing
    if isinstance(rtHandler, str):
        rtf = rtObjects.RTFile()
        tokenedRtHandler = rtf.readstr(rtHandler)  # return handler, processes tokens
    else:
        tokenedRtHandler = rtHandler

    # this could be just a Stream, but b/c we are creating metadata,
    # perhaps better to match presentation of other scores.
    if inputM21 is None:
        s = stream.Score()
    else:
        s = inputM21

    # metadata can be first
    md = metadata.Metadata()
    s.insert(0, md)

    partTrans = PartTranslator(md)
    p = partTrans.translateTokens(tokenedRtHandler.tokens)
    s.insert(0, p)

    return s


letterToNumDict = {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 6, 'g': 7, 'h': 8}


def appendMeasureToRepeatEndingsDict(rtMeasureObj: rtObjects.RTMeasure,
                                     m: stream.Measure,
                                     repeatEndings: dict,
                                     measureNumber=None):
    # noinspection PyShadowingNames
    '''
    Takes an RTMeasure object (which might represent one or more
    measures; but currently only one) and a music21 stream.Measure object and
    store it as a tuple in the repeatEndings dictionary to mark where the
    translator should later mark for adding endings.

    If the optional measureNumber is specified, we use that rather than the
    token number to add to the dict.

    This does not yet work for skipped measures.

    >>> rtm = romanText.rtObjects.RTMeasure('m15a V6 b1.5 V6/5 b2 I b3 viio6')
    >>> rtm.repeatLetter
    ['a']
    >>> rtm2 = romanText.rtObjects.RTMeasure('m15b V6 b1.5 V6/5 b2 I')
    >>> rtm2.repeatLetter
    ['b']
    >>> repeatEndings = {}
    >>> m1 = stream.Measure()
    >>> m2 = stream.Measure()
    >>> romanText.translate.appendMeasureToRepeatEndingsDict(rtm, m1, repeatEndings)
    >>> repeatEndings
    {1: [(15, <music21.stream.Measure 0a offset=0.0>)]}
    >>> romanText.translate.appendMeasureToRepeatEndingsDict(rtm2, m2, repeatEndings)
    >>> repeatEndings[1], repeatEndings[2]
    ([(15, <music21.stream.Measure 0a offset=0.0>)],
     [(15, <music21.stream.Measure 0b offset=0.0>)])
    >>> repeatEndings[2][0][1] is m2
    True
    '''
    if not rtMeasureObj.repeatLetter:
        return

    m.numberSuffix = rtMeasureObj.repeatLetter[0]

    for rl in rtMeasureObj.repeatLetter:
        if rl is None or rl == '':
            continue
        if rl not in letterToNumDict:  # pragma: no cover
            raise RomanTextTranslateException(f'Improper repeat letter: {rl}')
        repeatNumber = letterToNumDict[rl]
        if repeatNumber not in repeatEndings:
            repeatEndings[repeatNumber] = []
        if measureNumber is None:
            measureTuple = (rtMeasureObj.number[0], m)
        else:
            measureTuple = (measureNumber, m)
        repeatEndings[repeatNumber].append(measureTuple)


def _consolidateRepeatEndings(repeatEndings):
    # noinspection PyShadowingNames
    '''
    take repeatEndings, which is a dict of integers (repeat ending numbers) each
    holding a list of tuples of measure numbers and measure objects that get this ending,
    and return a list where contiguous endings should appear.  Each element of the list is a
    two-element tuple, where the first element is a list of measure objects that should have
    a bracket and the second element is the repeat number.

    Assumes that the list of measure numbers in each repeatEndings array is sorted.

    For the sake of demo and testing, we will use strings instead of measure objects.

    >>> repeatEndings = {1: [(5, 'm5a'), (6, 'm6a'), (17, 'm17'), (18, 'm18'),
    ...                      (19, 'm19'), (23, 'm23a')],
    ...                  2: [(5, 'm5b'), (6, 'm6b'), (20, 'm20'), (21, 'm21'), (23, 'm23b')],
    ...                  3: [(23, 'm23c')]}
    >>> print(romanText.translate._consolidateRepeatEndings(repeatEndings))
    [(['m5a', 'm6a'], 1), (['m17', 'm18', 'm19'], 1), (['m23a'], 1),
     (['m5b', 'm6b'], 2), (['m20', 'm21'], 2), (['m23b'], 2), (['m23c'], 3)]
    '''
    returnList = []

    for endingNumber in repeatEndings:
        startMeasureNumber = None
        lastMeasureNumber = None
        measureList = []
        for measureNumberUnderEnding, measureObject in repeatEndings[endingNumber]:
            if startMeasureNumber is None:
                startMeasureNumber = measureNumberUnderEnding
                lastMeasureNumber = measureNumberUnderEnding
                measureList.append(measureObject)
            elif measureNumberUnderEnding > lastMeasureNumber + 1:
                myTuple = (measureList, endingNumber)
                returnList.append(myTuple)
                startMeasureNumber = measureNumberUnderEnding
                lastMeasureNumber = measureNumberUnderEnding
                measureList = [measureObject]
            else:
                measureList.append(measureObject)
                lastMeasureNumber = measureNumberUnderEnding
        if startMeasureNumber is not None:
            myTuple = (measureList, endingNumber)
            returnList.append(myTuple)

    return returnList


def _addRepeatsFromRepeatEndings(s, repeatEndings):
    '''
    given a Stream and the repeatEndings dict, add repeats to the stream...
    '''
    consolidatedRepeats = _consolidateRepeatEndings(repeatEndings)
    for repeatEndingTuple in consolidatedRepeats:
        measureList, endingNumber = repeatEndingTuple[0], repeatEndingTuple[1]
        rb = spanner.RepeatBracket(measureList, number=endingNumber)
        rbOffset = measureList[0].getOffsetBySite(s)
        # Adding repeat bracket to stream at beginning of repeated section.
        # Maybe better at end?
        s.insert(rbOffset, rb)
        # should be 'if not max(endingNumbers)', but we can't tell that for each repeat.
        if endingNumber == 1:
            if measureList[-1].rightBarline is None:
                measureList[-1].rightBarline = bar.Repeat(direction='end')


def fixPickupMeasure(partObject):
    # noinspection PyShadowingNames
    '''
    Fix a pickup measure if any.

    We determine a pickup measure by being measure 0 and not having an RN
    object at the beginning.  Will also pad the last measure right and
    cut the duration of the final chord to match.

    Demonstration: an otherwise incorrect part

    >>> p = stream.Part()
    >>> m0 = stream.Measure()
    >>> m0.number = 0
    >>> k0 = key.Key('G')
    >>> m0.insert(0, k0)
    >>> m0.insert(0, meter.TimeSignature('4/4'))
    >>> m0.insert(3, roman.RomanNumeral('I', k0, quarterLength=1.0))
    >>> m1 = stream.Measure()
    >>> m1.number = 1
    >>> m1.append(roman.RomanNumeral('V', k0, quarterLength=4.0))
    >>> m2 = stream.Measure()
    >>> m2.number = 2
    >>> m2.append(roman.RomanNumeral('I', k0, quarterLength=4.0))
    >>> p.insert(0, m0)
    >>> p.insert(4, m1)
    >>> p.insert(8, m2)

    After running fixPickupMeasure()

    >>> romanText.translate.fixPickupMeasure(p)
    >>> p.show('text')
    {0.0} <music21.stream.Measure 0 offset=0.0>
        {0.0} <music21.key.Key of G major>
        {0.0} <music21.meter.TimeSignature 4/4>
        {0.0} <music21.roman.RomanNumeral I in G major>
    {1.0} <music21.stream.Measure 1 offset=1.0>
        {0.0} <music21.roman.RomanNumeral V in G major>
    {5.0} <music21.stream.Measure 2 offset=5.0>
        {0.0} <music21.roman.RomanNumeral I in G major>

    >>> m0.paddingLeft
    3.0
    >>> m2.paddingRight
    1.0
    >>> m2[roman.RomanNumeral].last().duration
    <music21.duration.Duration 3.0>
    '''
    m0 = partObject.measure(0)
    if m0 is None:
        return
    rnObjects = m0.getElementsByClass([roman.RomanNumeral, harmony.NoChord])
    if not rnObjects:
        return
    if rnObjects[0].offset == 0:
        return
    leftPadding = rnObjects[0].offset
    for el in m0:
        if el.offset < leftPadding:  # should be zero for Clefs, etc.
            pass
        else:
            el.offset = el.offset - leftPadding
    m0.paddingLeft = leftPadding
    for el in partObject:  # adjust all other measures etc. backwards
        if el.offset > 0:
            el.offset -= leftPadding
    mLast = partObject.getElementsByClass(stream.Measure).last()
    if mLast is m0:
        return

    lastRN = mLast.getElementsByClass([roman.RomanNumeral, harmony.NoChord]).last()
    if lastRN and lastRN.duration.quarterLength > leftPadding:
        curLastLength = mLast.duration.quarterLength
        lastRN.duration.quarterLength -= curLastLength - leftPadding
        mLast.paddingRight = curLastLength - leftPadding

        with common.classTools.tempAttribute(partObject, 'autoSort', False):
            # cast as list for speed and also temporarily disable sorting until all done.
            partElements = list(partObject)
            i = -1
            while partElements[i] is not mLast:
                # unprocessed metadata after last object
                partElements[i].setOffsetBySite(partObject,
                                                partElements[i].offset - mLast.paddingRight)
                i -= 1


def romanTextToStreamOpus(rtHandler, inputM21=None):
    '''
    The main processing routine for RomanText objects that may or may not
    be multi movement.

    Takes in a romanText.rtObjects.RTFile() object, or a string as rtHandler.

    Runs `romanTextToStreamScore()` as its main work.

    If inputM21 is None then it will create a Score or Opus object.

    Return either a Score object, or, if a multi-movement work is defined, an
    Opus object.
    '''
    if isinstance(rtHandler, str):
        rtf = rtObjects.RTFile()
        rtHandler = rtf.readstr(rtHandler)  # return handler, processes tokens

    if rtHandler.definesMovements():  # create an opus
        if inputM21 is None:
            s = stream.Opus()
        else:
            s = inputM21
        # copy the common header to each of the sub-handlers
        handlerBundles = rtHandler.splitByMovement(duplicateHeader=True)
        # see if we have header information
        for h in handlerBundles:
            # print(h, len(h))
            # append to opus
            s.append(romanTextToStreamScore(h))
        return s  # an opus
    else:  # create a Score
        return romanTextToStreamScore(rtHandler, inputM21=inputM21)


# ------------------------------------------------------------------------------


class TestSlow(unittest.TestCase):  # pragma: no cover
    '''
    These tests are currently too slow to run every time.
    '''
    def testExternalA(self):
        from music21.romanText import testFiles

        for tf in testFiles.ALL:
            rtf = rtObjects.RTFile()
            rth = rtf.readstr(tf)  # return handler, processes tokens
            s = romanTextToStreamScore(rth)
            s.show()

    # noinspection SpellCheckingInspection
    def testBasicA(self):
        from music21.romanText import testFiles

        for tf in testFiles.ALL:
            rtf = rtObjects.RTFile()
            rth = rtf.readstr(tf)  # return handler, processes tokens
            # will run romanTextToStreamScore on all but k273
            s = romanTextToStreamOpus(rth)
            s.show()

        s = romanTextToStreamScore(testFiles.swv23)
        self.assertEqual(s.metadata.composer, 'Heinrich Schutz')
        # this is defined as a Piece tag, but shows up here as a title, after
        # being set as an alternate title
        self.assertEqual(s.metadata.title, 'Warum toben die Heiden, Psalmen Davids no. 2, SWV 23')

        s = romanTextToStreamScore(testFiles.riemenschneider001)
        self.assertEqual(s.metadata.composer, 'J. S. Bach')
        self.assertEqual(s.metadata.title, 'Aus meines Herzens Grunde')

        s = romanTextToStreamScore(testFiles.monteverdi_3_13)
        self.assertEqual(s.metadata.composer, 'Claudio Monteverdi')

    def testMeasureCopyingA(self):
        from music21.romanText import testFiles

        s = romanTextToStreamScore(testFiles.swv23)
        mStream = s.parts[0].getElementsByClass(stream.Measure)
        # the first four measures should all have the same content
        rn1 = mStream[1].getElementsByClass(roman.RomanNumeral).first()
        self.assertEqual([str(x) for x in rn1.pitches], ['D5', 'F#5', 'A5'])
        self.assertEqual(str(rn1.figure), 'V')
        rn2 = mStream[1].getElementsByClass(roman.RomanNumeral)[1]
        self.assertEqual(str(rn2.figure), 'i')

        # make sure that m2, m3, m4 have the same values
        rn1 = mStream[2].getElementsByClass(roman.RomanNumeral)[0]
        self.assertEqual(str(rn1.figure), 'V')
        rn2 = mStream[2].getElementsByClass(roman.RomanNumeral)[1]
        self.assertEqual(str(rn2.figure), 'i')

        rn1 = mStream[3].getElementsByClass(roman.RomanNumeral)[0]
        self.assertEqual(str(rn1.figure), 'V')
        rn2 = mStream[3].getElementsByClass(roman.RomanNumeral)[1]
        self.assertEqual(str(rn2.figure), 'i')

        # test multiple measure copying
        s = romanTextToStreamScore(testFiles.monteverdi_3_13)
        mStream = s.parts[0].getElementsByClass(stream.Measure)

        m1a = None
        m2a = None
        m3a = None
        m1b = None
        m2b = None
        m3b = None

        for m in mStream:
            if m.number == 41:  # m49-51 = m41-43
                m1a = m
            elif m.number == 42:  # m49-51 = m41-43
                m2a = m
            elif m.number == 43:  # m49-51 = m41-43
                m3a = m
            elif m.number == 49:  # m49-51 = m41-43
                m1b = m
            elif m.number == 50:  # m49-51 = m41-43
                m2b = m
            elif m.number == 51:  # m49-51 = m41-43
                m3b = m

        rn = m1a.getElementsByClass(roman.RomanNumeral)[0]
        self.assertEqual(str(rn.figure), 'IV')
        rn = m1a.getElementsByClass(roman.RomanNumeral)[1]
        self.assertEqual(str(rn.figure), 'I')

        rn = m1b.getElementsByClass(roman.RomanNumeral)[0]
        self.assertEqual(str(rn.figure), 'IV')
        rn = m1b.getElementsByClass(roman.RomanNumeral)[1]
        self.assertEqual(str(rn.figure), 'I')

        rn = m2a.getElementsByClass(roman.RomanNumeral)[0]
        self.assertEqual(str(rn.figure), 'I')
        rn = m2a.getElementsByClass(roman.RomanNumeral)[1]
        self.assertEqual(str(rn.figure), 'ii')

        rn = m2b.getElementsByClass(roman.RomanNumeral)[0]
        self.assertEqual(str(rn.figure), 'I')
        rn = m2b.getElementsByClass(roman.RomanNumeral)[1]
        self.assertEqual(str(rn.figure), 'ii')

        rn = m3a.getElementsByClass(roman.RomanNumeral).first()
        self.assertEqual(str(rn.figure), 'V/ii')
        rn = m3b.getElementsByClass(roman.RomanNumeral).first()
        self.assertEqual(str(rn.figure), 'V/ii')

    def testMeasureCopyingB(self):
        from music21 import converter
        from music21.romanText import testFiles
        s = converter.parse(testFiles.monteverdi_3_13)
        m25 = s.measure(25)
        rn = m25.flatten().getElementsByClass(roman.RomanNumeral)
        self.assertEqual(rn[1].figure, 'III')
        self.assertEqual(str(rn[1].key), 'd minor')

        # TODO: this is getting the F#m even though the key and figure are
        # correct
        # self.assertEqual(str(rn[1].pitches), '[F4, A4, C5]')

        # s.show()

    def testOpus(self):
        from music21.romanText import testFiles

        o = romanTextToStreamOpus(testFiles.mozartK279)
        self.assertEqual(o.scores[0].metadata.movementNumber, '1')
        self.assertEqual(o.scores[0].metadata.composer, 'Mozart')
        self.assertEqual(o.scores[1].metadata.movementNumber, '2')
        self.assertEqual(o.scores[1].metadata.composer, 'Mozart')
        self.assertEqual(o.scores[2].metadata.movementNumber, '3')
        self.assertEqual(o.scores[2].metadata.composer, 'Mozart')

        # test using converter.
        from music21 import converter
        s = converter.parse(testFiles.mozartK279)
        self.assertTrue('Opus' in s.classes)
        self.assertEqual(len(s.scores), 3)

        # make sure a normal file is still a Score
        s = converter.parse(testFiles.riemenschneider001)
        self.assertTrue(isinstance(s, stream.Score))


class Test(unittest.TestCase):
    def testMinor67set(self):
        from music21.romanText import testFiles
        s = romanTextToStreamScore(testFiles.testSetMinorRootParse)
        chords = list(s[roman.RomanNumeral])

        def pitchEqual(index, pitchStr):
            ch = chords[index]
            chPitches = ch.pitches
            self.assertEqual(' '.join(p.name for p in chPitches), pitchStr)

        pitchEqual(0, 'C E- G')
        pitchEqual(1, 'B D F')
        pitchEqual(3, 'G B D')
        pitchEqual(4, 'A- C E-')
        pitchEqual(7, 'B- D F')
        pitchEqual(10, 'A C E')

    def testPivotInCopyMultiple(self):
        from music21 import converter
        testCase = '''
m1 G: I
m2 I
m3 V D: I
m4 V
m5 G: I
m6-7 = m3-4
m8 I
'''
        s = converter.parse(testCase, format='romanText')
        m = s.measure(7).flatten()
        self.assertEqual(m.getElementsByClass(roman.RomanNumeral).first().key.name, 'D major')
        m = s.measure(8).flatten()
        self.assertEqual(m.getElementsByClass(roman.RomanNumeral).first().key.name, 'D major')

    def testPivotInCopyMultiple2(self):
        '''
        test whether a chord in a pivot situation outside of copying affects copying
        '''

        from music21 import converter
        testCase = '''
m1 G: I
m2 V D: I
m3 G: IV
m4 V
m5 I
m6-7 = m4-5
m8 I
'''
        s = converter.parse(testCase, format='romanText')
        m = s.measure(5).flatten()
        self.assertEqual(m.getElementsByClass(roman.RomanNumeral).first().key.name, 'G major')

    def testPivotInCopySingle(self):
        from music21 import converter
        testCase = '''
m1 G: I
m2 I
m3 V D: I
m4 G: I
m5 = m3
m6 I
'''
        s = converter.parse(testCase, format='romanText')
        m = s.measure(6).flatten()
        self.assertEqual(m.getElementsByClass(roman.RomanNumeral).first().key.name, 'D major')

    def testSecondaryInCopyMultiple(self):
        '''
        test secondary dominants after copy
        '''

        testSecondaryInCopy = '''
Time Signature: 4/4
m1 g: i
m2 i6
m3 V7/v
m4 d: i
m5-6 = m2-3
m7 = m3
'''

        s = romanTextToStreamScore(testSecondaryInCopy)
        m = s.measure(6).flatten()
        self.assertEqual(m.getElementsByClass(roman.RomanNumeral).first().pitchedCommonName,
                         'E-dominant seventh chord')
        m = s.measure(7).flatten()
        self.assertEqual(m.getElementsByClass(roman.RomanNumeral).first().pitchedCommonName,
                         'E-dominant seventh chord')
        # s.show()

    def testBasicB(self):
        from music21.romanText import testFiles

        unused_s = romanTextToStreamScore(testFiles.riemenschneider001)
        # unused_s.show()

    def testRomanTextString(self):
        from music21 import converter
        s = converter.parse('m1 KS1 I \n m2 V6/5 \n m3 I b3 V7 \n'
                            + 'm4 KS-3 vi \n m5 a: i b3 V4/2 \n m6 I',
                            format='romantext')

        rnStream = s.flatten().getElementsByClass(roman.RomanNumeral).stream()
        self.assertEqual(rnStream[0].figure, 'I')
        self.assertEqual(rnStream[1].figure, 'V6/5')
        self.assertEqual(rnStream[2].figure, 'I')
        self.assertEqual(rnStream[3].figure, 'V7')
        self.assertEqual(rnStream[4].figure, 'vi')
        self.assertEqual(rnStream[5].figure, 'i')
        self.assertEqual(rnStream[6].figure, 'V4/2')
        self.assertEqual(rnStream[7].figure, 'I')

        rnStreamKey = s.flatten().getElementsByClass(key.KeySignature)
        self.assertEqual(rnStreamKey[0].sharps, 1)
        self.assertEqual(rnStreamKey[1].sharps, -3)

        # s.show()

    def testMeasureCopyingB(self):
        from music21 import converter
        from music21 import pitch

        src = '''m1 G: IV || b3 d: III b4 ii
m2 v b2 III6 b3 iv6 b4 ii/o6/5
m3 i6/4 b3 V
m4-5 = m2-3
m6-7 = m4-5
'''
        s = converter.parse(src, format='romantext')
        rnStream = s.flatten().getElementsByClass(roman.RomanNumeral)

        for elementNumber in [0, 6, 12]:
            self.assertEqual(rnStream[elementNumber + 4].figure, 'III6')
            self.assertEqual(str([str(p) for p in rnStream[elementNumber + 4].pitches]),
                             "['A4', 'C5', 'F5']")

            x = rnStream[elementNumber + 4].pitches[2].accidental
            if x is None:
                x = pitch.Accidental('natural')
            self.assertEqual(x.alter, 0)

            self.assertEqual(rnStream[elementNumber + 5].figure, 'iv6')
            self.assertEqual(str([str(p) for p in rnStream[elementNumber + 5].pitches]),
                             "['B-4', 'D5', 'G5']")

            self.assertTrue(rnStream[elementNumber + 5].pitches[0].accidental.displayStatus)

    def testNoChord(self):
        from music21 import converter
        from music21.harmony import NoChord

        src = '''m1 G: IV || b3 d: III b4 NC
m2 b2 III6 b3 iv6 b4 ii/o6/5
m3 NC b3 G: V
'''
        s = converter.parse(src, format='romantext')
        p = s.parts[0]
        m1 = p.getElementsByClass(stream.Measure).first()
        r1 = m1.notesAndRests[-1]
        self.assertIn('Rest', r1.classes)
        self.assertEqual(r1.quarterLength, 1.0)
        noChordObj = m1.getElementsByClass(harmony.Harmony).last()
        self.assertIsInstance(noChordObj, NoChord)

        m2 = p.getElementsByClass(stream.Measure)[1]
        r2 = m2.notesAndRests[0]
        self.assertIn('Rest', r2.classes)
        self.assertEqual(r1.quarterLength, 1.0)
        rn1 = m2.notesAndRests[1]
        self.assertIn(roman.RomanNumeral, rn1.classSet)
        # s.show()

    def testUnprocessed(self):
        from music21 import converter
        from music21.romanText import translate
        src = '''Note: Hello
m1 G: IV || b3 d: III b4 NC
varM1 I
Note: Hi
'''
        s = converter.parse(src, format='romantext')
        p = s.parts[0]
        unprocessedElements = p[translate.RomanTextUnprocessedMetadata]
        self.assertEqual(len(unprocessedElements), 3)
        note1, var1, note2 = unprocessedElements
        self.assertEqual(note1.tag, 'Note')
        self.assertEqual(note2.tag, 'Note')
        self.assertEqual(note1.data, 'Hello')
        self.assertEqual(note2.data, 'Hi')
        self.assertFalse(var1.tag)
        self.assertIn(' I', var1.data)

    def testUnprocessedWithAnacrusis(self):
        from music21.romanText import translate
        src = '''
        Time Signature: 4/4
        m0 b4 f: i
        Note: Internal Note field after anacrusis.
        m1 V
        '''
        s = translate.romanTextToStreamScore(src)
        p = s.parts[0]
        self.assertEqual(len(p), 3)
        self.assertIsInstance(p[0], stream.Measure)
        self.assertEqual(p[0].paddingLeft, 3.0)
        self.assertIsInstance(p[1], translate.RomanTextUnprocessedMetadata)
        self.assertEqual(p[1].offset, 0.0)
        self.assertEqual(p[1].data, 'Internal Note field after anacrusis.')
        self.assertIsInstance(p[2], stream.Measure)
        self.assertEqual(p[2].offset, 1.0)
        self.assertIsInstance(p[2][0], roman.RomanNumeral)
        self.assertEqual(p[2].paddingRight, 1.0)
        self.assertEqual(p[2].duration.quarterLength, 3.0)


    def testSixthMinorParse(self):
        from music21 import converter

        src = '''SixthMinor: flat
m1 c: vi
'''
        s = converter.parse(src, format='romantext')
        p = s.parts[0]
        ch0 = p.recurse().notes[0]
        self.assertEqual(ch0.root().name, 'A-')

    def testSetRTVersion(self):
        src = '''RTVersion: 2.5
m1 C: I'''
        rtf = rtObjects.RTFile()
        rtHandler = rtf.readstr(src)
        pt = PartTranslator()
        pt.translateTokens(rtHandler.tokens)
        self.assertEqual(pt.romanTextVersion, 2.5)

        # gives warning, not raises...
        #         src = '''RTVersion: XYZ
        # m1 C: I'''
        #         rtf = rtObjects.RTFile()
        #         rtHandler = rtf.readstr(src)
        #         pt = PartTranslator()
        #         with self.assertRaises(RomanTextTranslateException):
        #             pt.translateTokens(rtHandler.tokens)

    def testPivotChord(self):
        from music21 import converter

        src = '''m1 G: I b3 v d: i b4 V'''
        s = converter.parse(src, format='romantext')
        p = s.parts[0]
        m1 = p.getElementsByClass(stream.Measure).first()
        allRNs = m1.getElementsByClass(roman.RomanNumeral)
        notPChord = allRNs[0]
        pChord = allRNs[1]
        self.assertEqual(pChord.key.tonic.step, 'G')
        self.assertEqual(pChord.figure, 'v')
        pivot = pChord.pivotChord
        self.assertEqual(pivot.key.tonic.step, 'D')
        self.assertEqual(pivot.figure, 'i')

        self.assertIsNone(notPChord.pivotChord)
        # s.show('text')

    def testTimeSigChanges(self):
        from music21 import converter
        src = '''Time Signature: 4/4
        m1 C: I
        Time Signature: 2/4
        m10 V
        Time Signature: 4/4
        m12 I
        m14-25 = m1-12
        '''
        s = converter.parse(src, format='romantext')
        p = s.parts[0]
        m3 = p.getElementsByClass(stream.Measure)[2]
        self.assertEqual(m3.getOffsetBySite(p), 8.0)
        m10 = p.getElementsByClass(stream.Measure)[9]
        self.assertEqual(m10.getOffsetBySite(p), 36.0)
        m11 = p.getElementsByClass(stream.Measure)[10]
        self.assertEqual(m11.getOffsetBySite(p), 38.0)
        m12 = p.getElementsByClass(stream.Measure)[11]
        self.assertEqual(m12.getOffsetBySite(p), 40.0)
        m13 = p.getElementsByClass(stream.Measure)[12]
        self.assertEqual(m13.getOffsetBySite(p), 44.0)

        m16 = p.getElementsByClass(stream.Measure)[15]
        self.assertEqual(m16.getOffsetBySite(p), 56.0)
        m23 = p.getElementsByClass(stream.Measure)[22]
        self.assertEqual(m23.getOffsetBySite(p), 84.0)
        m24 = p.getElementsByClass(stream.Measure)[23]
        self.assertEqual(m24.getOffsetBySite(p), 86.0)
        m25 = p.getElementsByClass(stream.Measure)[24]
        self.assertEqual(m25.getOffsetBySite(p), 88.0)

    # testEndings (which was incomplete in any case) has been superseded by
    #   testRepeats below

    def testTuplets(self):
        from music21 import converter
        c = converter.parse('m1 C: I b2.66 V', format='romantext')
        n1 = c.flatten().notes[0]
        n2 = c.flatten().notes[1]
        self.assertEqual(n1.duration.quarterLength, common.opFrac(5 / 3))
        self.assertEqual(n2.offset, common.opFrac(5 / 3))
        self.assertEqual(n2.duration.quarterLength, common.opFrac(7 / 3))

        c = converter.parse('TimeSignature: 6/8\nm1 C: I b2.66 V', format='romantext')
        n1 = c.flatten().notes[0]
        n2 = c.flatten().notes[1]
        self.assertEqual(n1.duration.quarterLength, 5 / 2)
        self.assertEqual(n2.offset, 5 / 2)
        self.assertEqual(n2.duration.quarterLength, 1 / 2)

        c = converter.parse('m1 C: I b2.66.5 V', format='romantext')
        n1 = c.flatten().notes[0]
        n2 = c.flatten().notes[1]
        self.assertEqual(n1.duration.quarterLength, common.opFrac(11 / 6))
        self.assertEqual(n2.offset, common.opFrac(11 / 6))
        self.assertEqual(n2.duration.quarterLength, common.opFrac(13 / 6))

    def testCopyEmptyMeasures(self) -> None:
        from music21 import converter
        empty_measures_with_copy = textwrap.dedent(''''
            Time Signature: 2/4
            m1 I
            m2 V
            m3 = m1
            m4-5 = m1-2
        ''')
        s = converter.parse(empty_measures_with_copy, format='romanText')
        assert s.duration.quarterLength == 10

    def testRepeats(self) -> None:
        from music21 import converter

        def _repeat_tester(
            repeat_bar: bar.Repeat, direction: str, offset: float, mNumber: int
        ) -> None:
            self.assertEqual(repeat_bar.direction, direction)
            self.assertEqual(repeat_bar.offset, offset)
            self.assertEqual(repeat_bar.activeSite.number, mNumber)

        def _test_expanded(s: stream.Stream, quarterLength: float) -> None:
            # NB repeat.Expander does not work on stream, only on part. Is this
            #   expected behavior?
            p = next(s[stream.Part])
            e = repeat.Expander(p)
            self.assertTrue(e.repeatBarsAreCoherent())
            p2 = e.process()
            self.assertEqual(p2.quarterLength, quarterLength)

        def _test_ending_contents(
            rb: spanner.RepeatBracket, expectedMeasures: list[str]
        ) -> None:
            measure_nos = [m.measureNumberWithSuffix() for m in rb[stream.Measure]]
            self.assertEqual(measure_nos, expectedMeasures)

        # Test simple repeats
        simple_repeats = textwrap.dedent('''
            Time Signature: 3/4
            m1 ||: V
            m2 I :||
        ''')
        s = converter.parse(simple_repeats, format='romanText')
        br_iter = s[bar.Repeat]
        self.assertEqual(len(br_iter), 2)
        start_repeat, end_repeat = br_iter
        _repeat_tester(start_repeat, 'start', 0.0, 1)
        _repeat_tester(end_repeat, 'end', 3.0, 2)
        _test_expanded(s, 12.0)

        single_bar_repeats = textwrap.dedent('''
            Time Signature: 2/4
            m1 ||: I :||
        ''')
        s = converter.parse(single_bar_repeats, format='romanText')
        br_iter = s[bar.Repeat]
        self.assertEqual(len(br_iter), 2)
        start_repeat, end_repeat = br_iter
        _repeat_tester(start_repeat, 'start', 0.0, 1)
        _repeat_tester(end_repeat, 'end', 2.0, 1)
        _test_expanded(s, 4.0)

        empty_bars_with_repeats = textwrap.dedent('''
            Time Signature: 2/4
            m1 I
            m2 ||:
            m3 :||
            m4 ||: :||
        ''')
        s = converter.parse(empty_bars_with_repeats, format='romanText')
        br_iter = s[bar.Repeat]
        self.assertEqual(len(br_iter), 4)
        start_repeat1, end_repeat1, start_repeat2, end_repeat2 = br_iter
        _repeat_tester(start_repeat1, 'start', 0.0, 2)
        _repeat_tester(end_repeat1, 'end', 2.0, 3)
        _repeat_tester(start_repeat2, 'start', 0.0, 4)
        _repeat_tester(end_repeat2, 'end', 2.0, 4)
        for measure in s[stream.Measure]:
            rn_iter = measure[roman.RomanNumeral]
            self.assertEqual(len(rn_iter), 1)
            # mypy complains about the next line because
            #   RecursiveIterator.first() has X | None type, but we know
            #   it will not be None because we have just asserted that rn_iter
            #   has length 1
            self.assertEqual(rn_iter.first().figure, 'I')  # type: ignore

        _test_expanded(s, 14.0)

        three_endings = textwrap.dedent('''
            Time Signature: 3/4
            m1 ||: I
            m2a IV :||
            m2b V :||
            m2c I
        ''')
        s = converter.parse(three_endings, format='romanText')
        br_iter = s[bar.Repeat]
        self.assertEqual(len(br_iter), 3)
        start_repeat, end_repeat1, end_repeat2 = br_iter
        _repeat_tester(start_repeat, 'start', 0.0, 1)
        _repeat_tester(end_repeat1, 'end', 3.0, 2)
        _repeat_tester(end_repeat2, 'end', 3.0, 2)
        rb_iter = s[spanner.RepeatBracket]
        self.assertEqual(len(rb_iter), 3)
        first_ending, second_ending, third_ending = rb_iter
        _test_ending_contents(first_ending, ['2a'])
        _test_ending_contents(second_ending, ['2b'])
        _test_ending_contents(third_ending, ['2c'])
        _test_expanded(s, 18.0)

        more_complex_example = textwrap.dedent('''
            TimeSignature: 3/4
            m1 ||: I
            m2a IV
            m3a V :||
            m2b V :||
            m2c IV
            m3c V
            m4 I
        ''')
        s = converter.parse(more_complex_example, format='romanText')
        br_iter = s[bar.Repeat]
        self.assertEqual(len(br_iter), 3)
        start_repeat, end_repeat1, end_repeat2 = s[bar.Repeat]
        _repeat_tester(start_repeat, 'start', 0.0, 1)
        _repeat_tester(end_repeat1, 'end', 3.0, 3)
        _repeat_tester(end_repeat2, 'end', 3.0, 2)
        rb_iter = s[spanner.RepeatBracket]
        self.assertEqual(len(rb_iter), 3)
        first_ending, second_ending, third_ending = rb_iter
        _test_ending_contents(first_ending, ['2a', '3a'])
        _test_ending_contents(second_ending, ['2b'])
        _test_ending_contents(third_ending, ['2c', '3c'])
        _test_expanded(s, 27.0)


# ------------------------------------------------------------------------------

# define presented order in documentation
_DOC_ORDER: list[type] = []


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)  # , TestSlow)
