# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         musedata/__init__.py
# Purpose:      parses Walter Hewlett's MuseData format
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2010, 2014 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
**N.B. in Dec. 2014 MuseData access was removed from music21 because the rights conflicted with
access computationally from music21.  This module is retained for anyone who has such access,
however it is completely untested now and errors cannot and will not be fixed.**

Objects and resources for processing MuseData.

MuseData conversion from a file or URL to a :class:`~music21.stream.Stream` is available through
the music21 converter module's :func:`~music21.converter.parse` function.

>>> #_DOCS_SHOW from music21 import *
>>> #_DOCS_SHOW abcScore = converter.parse('d:/data/musedata/myScore.stage2')

Low level MuseData conversion is facilitated by the objects in this module and
:func:`music21.musedata.translate.museDataToStreamScore`.
'''

import unittest
import os
import pathlib

from music21 import exceptions21
from music21.musedata import base12_26
from music21.musedata import base40
from music21.musedata import translate

from music21 import common
from music21 import prebase

from music21 import environment
_MOD = 'musedata'
environLocal = environment.Environment(_MOD)

# for implementation
# see http://www.ccarh.org/publications/books/beyondmidi/online/musedata/
# and http://www.ccarh.org/publications/books/beyondmidi/online/musedata/record-organization/


# ------------------------------------------------------------------------------
class MuseDataException(exceptions21.Music21Exception):
    pass


# ------------------------------------------------------------------------------
class MuseDataRecord(prebase.ProtoM21Object):
    '''
    Object for extracting data from a Note or other related record, or a
    single line of musedata data.
    '''

    def __init__(self, src='', parent=None):
        # environLocal.printDebug(['creating MuseDataRecord'])
        self.src = src  # src here is one line of text
        self.parent = parent

        if self.parent is not None:
            # form measure, then part
            self.stage = self.parent.parent.stage
        else:
            self.stage = None
        # store frequently used values
        self._cache = {}

    def isRest(self):
        '''Return a boolean if this record is a rest.

        >>> mdr = musedata.MuseDataRecord('D4     1        s     d  ]]')
        >>> mdr.isRest()
        False
        >>> mdr = musedata.MuseDataRecord('measure 1       A')
        >>> mdr.isRest()
        False

        '''
        if self.src and self.src[0] == 'r':
            return True
        return False

    def isTied(self):
        '''Return a boolean if this record is tied.


        >>> mdr = musedata.MuseDataRecord('D4     8-       h     d        -')
        >>> mdr.isTied()
        True


        >>> mdr = musedata.MuseDataRecord('C4     1        s     u  [[')
        >>> mdr.isTied()
        False
        '''
        if self.stage == 1:
            if len(self.src) > 7 and self.src[7] == '-':
                return True
            return False
        else:
            if len(self.src) > 8 and self.src[8] == '-':
                return True
            return False

    def isNote(self):
        if self.src and self.src[0] in 'ABCDEFG':
            return True
        return False

    def isChord(self):
        '''
        Chords are specified as additional note records following a main chord tone.
        The blank space defines this as chord tone.
        '''
        # second character must be a pitch definition
        if len(self.src) > 1 and self.src[0] == ' ' and self.src[1] in 'ABCDEFG':
            return True
        return False

    def isCueOrGrace(self):
        if self.src and self.src[0] in 'cg':
            return True
        return False

    def isBack(self):
        '''
        >>> mdr = musedata.MuseDataRecord('back   4')
        >>> mdr.isBack()
        True
        '''
        if len(self.src) >= 4 and self.src[0:4] == 'back':
            return True
        return False

    def _getPitchParameters(self):
        '''

        >>> mdr = musedata.MuseDataRecord('Ef4    1        s     d  ==')
        >>> mdr.isNote()
        True
        >>> mdr._getPitchParameters()
        'E-4'

        >>> mdr = musedata.MuseDataRecord('F#4    1        s #   d  ==')
        >>> mdr.isNote()
        True
        >>> mdr._getPitchParameters()
        'F#4'
        '''
        if self.isNote():
            data = self.src[0:].split()[0]
        elif self.isCueOrGrace() or self.isChord():
            data = self.src[1:].split()[0]
        else:
            raise MuseDataException('cannot get pitch parameters from this kind of record')

        pStr = [data[0]]  # first element will be A...G
        if '#' in data:
            pStr.append('#')
        elif '##' in data:
            pStr.append('##')
        elif 'f' in data:
            pStr.append('-')
        elif 'ff' in data:
            pStr.append('--')

        # probably a faster way to do this
        numbers, junk = common.getNumFromStr(data)
        pStr.append(numbers)
        # environLocal.printDebug(['pitch parameters', ''.join(pStr), 'src', self.src])
        return ''.join(pStr)

    def _getAccidentalObject(self):
        '''Return a music21 Accidental object for the representation.


        >>> mdr = musedata.MuseDataRecord('Ef4    1        s     d  ==')
        >>> mdr._getAccidentalObject()
        >>> mdr = musedata.MuseDataRecord('F#4    1        s #   d  ==')
        >>> mdr._getAccidentalObject()
        <accidental sharp>
        >>> mdr._getAccidentalObject().displayStatus == True
        True
        >>> mdr = musedata.MuseDataRecord('F#4    1        s ')
        >>> mdr._getAccidentalObject() is None
        True
        '''
        # this is not called by stage 1
        from music21 import pitch
        if len(self.src) <= 18:
            return None

        data = self.src[18]
        acc = None
        if data == '#':
            acc = pitch.Accidental('sharp')
        elif data == 'n':
            acc = pitch.Accidental('natural')
        elif data == 'f':
            acc = pitch.Accidental('flat')
        elif data == 'x':
            acc = pitch.Accidental('double-sharp')
        elif data == 'X':
            # this is sharp sharp, cannot distinguish
            acc = pitch.Accidental('double-sharp')
        elif data == '&':
            acc = pitch.Accidental('double-flat')
        elif data == 'S':
            # natural sharp; cannot yet do
            acc = pitch.Accidental('sharp')
        elif data == 'F':
            # natural flat; cannot yet do
            acc = pitch.Accidental('flat')
        # if no match or ' ', return None

        if acc is not None:
            # not sure what the expectation is here: could be 'normal'
            # 'unless-repeated'
            acc.displayType = 'always'
            acc.displayStatus = True
        return acc

    def getPitchObject(self):
        '''
        Get the Pitch object defined by this record. This may be a note, chord, or grace pitch.

        >>> mdr = musedata.MuseDataRecord('Ef4    1        s     d  ==')
        >>> p = mdr.getPitchObject()
        >>> p.nameWithOctave
        'E-4'
        >>> mdr = musedata.MuseDataRecord('F#4    1        s #   d  ==')
        >>> p = mdr.getPitchObject()
        >>> p.nameWithOctave
        'F#4'
        >>> p.accidental.displayStatus
        True


        Double sharps were giving octave problems.

        >>> mdr = musedata.MuseDataRecord('F##5   2        e x   d')
        >>> p = mdr.getPitchObject()
        >>> p.nameWithOctave
        'F##5'

        '''
        from music21 import pitch
        pp = self._getPitchParameters()
        p = pitch.Pitch(pp)

        if self.stage == 1:
            # no accidental information stored; have to just use pitch given
            return p
        else:
            # bypass using property, as that sets pitch space value as needing
            # update, and pitch space value should be correct
            acc = self._getAccidentalObject()
            # only set if not None, as otherwise default accidental will already
            # be created
            if p.accidental is not None:
                # set display to hidden, as explicit display accidentals
                # are given with an acc parameter
                p.accidental.displayStatus = False
            if acc is not None:
                p._accidental = self._getAccidentalObject()

            if p.accidental is not None and self.hasCautionaryAccidental():
                p.accidental.displayStatus = True

            # environLocal.printDebug(['p', p])
            return p

    def getQuarterLength(self, divisionsPerQuarterNote=None):
        '''
        Gets the quarterLength of the note given the prevailing divisionsPerQuarterNote

        Here there is one division:

        >>> mdr = musedata.MuseDataRecord('Ef4    1        s     d  ==')
        >>> mdr.getQuarterLength(4)
        0.25
        >>> mdr.getQuarterLength(8)
        0.125

        >>> mdr = musedata.MuseDataRecord('Ef4    6        s     d  ==')
        >>> mdr.getQuarterLength(4)
        1.5

        >>> mdr = musedata.MuseDataRecord('back   4')
        >>> mdr.getQuarterLength(4)
        1.0
        '''
        if self.stage == 1:
            divisions = int(self.src[5:7])
        else:
            divisions = int(self.src[5:8])

        shouldBeBlank = self.src[4:5]
        if shouldBeBlank != ' ':
            try:
                divHundreds = int(shouldBeBlank)
                divisions += 100 * divHundreds
                print('Error in parsing: '
                      + self.src
                      + '\n   Column 5 must be blank. Parsing as a part of the divisions')
            except ValueError:
                raise MuseDataException(
                    'Error in parsing: ' + self.src + '\n   Column 5 must be blank.')

        # the parent is the measure, and the parent of that is the part
        if self.parent is not None:
            dpq = self.parent.parent.getDivisionsPerQuarterNote()
        elif divisionsPerQuarterNote is not None:
            dpq = divisionsPerQuarterNote
        else:
            raise MuseDataException('cannot access parent container of this record '
                                    + 'to obtain divisions per quarter')
        return divisions / dpq

    def getDots(self):
        if self.stage == 1:
            return None
        else:
            if len(self.src) > 17:
                if self.src[17] == '.':
                    return 1
                if self.src[17] == ':':
                    return 2
            return 0

#    def getType(self):
#        # TODO: column 17 self.src[16] defines the graphic note type
#        # this may or may not align with derived quarter length
#        if self.stage == 1:
#            return None
#        else:
#            if len(self.src) == 0:
#                return None
#            data = self.src[16]
#            return data

    def getLyrics(self):
        '''Return lyrics as a list.


        >>> mdr = musedata.MuseDataRecord('D4     2        e     u                    con-')
        >>> mdr.stage = 2
        >>> mdr.getLyrics()
        ['con-']
        '''
        data = None
        if self.stage == 1:
            return None
        else:
            # print(self.src, len(self.src))
            if len(self.src) < 44:
                return None
            raw = self.src[43:]
            # | used to delimit multiple versus
            data = [x.strip() for x in raw.split('|')]
        return data

    def getBeams(self):
        '''Return complete span of characters defining beams.


        >>> mdr = musedata.MuseDataRecord('E2     1        s     u  =')
        >>> mdr.getBeams()
        '='
        >>> mdr = musedata.MuseDataRecord('E2     1        s     u  ]\')
        >>> mdr.getBeams()
        ']\'
        >>> mdr = musedata.MuseDataRecord('E2     4        q     u')
        >>> mdr.getBeams() is None
        True

        '''
        if self.stage == 1:
            return None
        else:
            data = self.src[25:31]  # def as cols 26 to 31 inclusive
            if data == '':
                return None
            # on trim trailing white space, not leading
            return data.rstrip()

    # TODO: need to get slurs from this indication:
    # (), {}, []

    def _getAdditionalNotations(self):
        '''Return an articulation object or None


        >>> mdr = musedata.MuseDataRecord('C4    12        e     u  [      .p')
        >>> mdr._getAdditionalNotations()
        '.p'

        >>> mdr = musedata.MuseDataRecord('C4    12        e     u  =      .')
        >>> mdr._getAdditionalNotations()
        '.'

        >>> mdr = musedata.MuseDataRecord('G4    24        q     u        (')
        >>> mdr._getAdditionalNotations()
        '('
        '''
        # these are cached b/c they are requested for many operations
        try:
            return self._cache['_getAdditionalNotations']
        except KeyError:
            pass

        if len(self.src) < 31:
            data = None
        else:
            # accumulate chars 32-43, index 31, 42
            data = []
            i = 31
            while i <= 42 and i < len(self.src):
                data.append(self.src[i])
                i += 1
            data = ''.join(data).strip()
        self._cache['_getAdditionalNotations'] = data
        return data

    def getArticulationObjects(self):
        '''Return a list of 0 or more music21 Articulation objects


        >>> mdr = musedata.MuseDataRecord('C4    12        e     u  [      .p')
        >>> mdr.getArticulationObjects()
        [<music21.articulations.Staccato>]

        >>> mdr = musedata.MuseDataRecord('C4    12        e     u  [      .p>')
        >>> mdr.getArticulationObjects()
        [<music21.articulations.Staccato>, <music21.articulations.Accent>]

        '''
        from music21 import articulations
        post = []
        data = self._getAdditionalNotations()
        if data is None:
            return post
        for char in data:
            if char == 'A':
                # vertical accent up
                post.append(articulations.StrongAccent())
            elif char == 'V':
                # vertical accent down
                post.append(articulations.StrongAccent())
            elif char == '>':
                # horizontal accents; normal
                post.append(articulations.Accent())
            elif char == '.':
                post.append(articulations.Staccato())
            elif char == '_':
                post.append(articulations.Tenuto())
            elif char == '=':
                post.append(articulations.DetachedLegato())
            elif char == 'i':
                post.append(articulations.Spiccato())
            elif char == ',':
                post.append(articulations.BreathMark())
        return post

    def getExpressionObjects(self):
        '''Return a list of 0 or more music21 Articulation objects


        >>> mdr = musedata.MuseDataRecord('C4    12        e     u  [      t')
        >>> mdr.getExpressionObjects()
        [<music21.expressions.Trill>]

        >>> mdr = musedata.MuseDataRecord('C4    12        e     u  [      .p>F')
        >>> mdr.getExpressionObjects()
        [<music21.expressions.Fermata>]

        '''
        from music21 import expressions
        post = []
        data = self._getAdditionalNotations()
        if data is None:
            return post

        for char in data:
            if char == 'F':
                # upright fermata
                post.append(expressions.Fermata())
            elif char == 'E':
                # inverted Fermata
                post.append(expressions.Fermata())
            elif char == 't':  # trill
                post.append(expressions.Trill())
            elif char == 'r':
                post.append(expressions.Turn())
            elif char == 'M':
                post.append(expressions.Mordent())
        return post

    def getDynamicObjects(self):
        '''Return a list of 0 or more music21 Dynamic objects


        >>> mdr = musedata.MuseDataRecord('C5    12        e     u         ff')
        >>> mdr.getDynamicObjects()
        [<music21.dynamics.Dynamic ff>]

        >>> mdr = musedata.MuseDataRecord('E4    48        h     u        (pp')
        >>> mdr.getDynamicObjects()
        [<music21.dynamics.Dynamic pp>]

        '''
        from music21 import dynamics
        post = []
        data = self._getAdditionalNotations()
        if data is None:
            return post
        # find targets from largest to smallest
        targets = ['ppp', 'fff',
                    'pp', 'ff', 'fp', 'mp', 'mf',
                    'p', 'f', 'm', 'Z', 'Zp', 'R']
        for t in targets:
            pos = data.find(t)
            if pos < 0:
                continue
            # remove from data to avoid double hits
            data = data[:pos] + data[pos + len(t):]
            # those that can be directedly created
            if t in ['ppp', 'fff', 'pp', 'ff', 'p', 'f', 'mp', 'mf', 'fp']:
                post.append(dynamics.Dynamic(t))
            elif t == 'm':
                post.append(dynamics.Dynamic('mp'))
            elif t == 'Z':  # sfz
                post.append(dynamics.Dynamic('sf'))
            elif t == 'Zp':  # sfp
                post.append(dynamics.Dynamic('sf'))
            elif t == 'R':  # rfz
                post.append(dynamics.Dynamic('sf'))
        # environLocal.printDebug(['got dynamics', post])
        return post

    def hasCautionaryAccidental(self):
        '''
        Return a boolean if this note has a cautionary accidental.

        >>> mdr = musedata.MuseDataRecord('F5     3        t n   d  ==[   (+')
        >>> mdr.hasCautionaryAccidental()
        True

        >>> mdr = musedata.MuseDataRecord('C4    12        e     u  [')
        >>> mdr.hasCautionaryAccidental()
        False

        '''
        data = self._getAdditionalNotations()
        if data is None:
            return False
        if '+' in data:
            return True
        return False

# ------------------------------------------------------------------------------


class MuseDataRecordIterator:
    '''
    Create MuseDataRecord objects on demand, in order
    '''

    def __init__(self, src, parent):
        self.src = src  # the lost of all record lines
        self.index = 0
        self.parent = parent

    def __iter__(self):
        return self

    def __next__(self):
        if self.index >= len(self.src):
            raise StopIteration
        # add one b/c end is inclusive
        mdr = MuseDataRecord(self.src[self.index], self.parent)
        self.index += 1
        return mdr

# ------------------------------------------------------------------------------


class MuseDataMeasure(prebase.ProtoM21Object):
    '''
    A MuseDataMeasure is an abstraction of the data contained within a measure definitions.

    This needs to be an object to gracefully handle the following cases.
    Some Measures do not have any notes, for example, and the end of encoding where a
    final bar line is defined. Some measures do not have numbers or barlin definitions,
    such as pickup notes. Some measures define barline characteristics.
    Backup and forward presumably only is contained within a measure.
    '''

    def __init__(self, src=None, parent=None):
        if src is None:
            src = []
        # environLocal.printDebug(['creating MuseDataMeasure'])
        self.src = src  # a list of character lines for this measure
        # store reference to parent Part
        self.parent = parent

        if self.parent is not None:
            # form measure, then part
            self.stage = self.parent.stage
        else:
            self.stage = None

    def _reprInternal(self):
        return 'size={len(self.src)}'

    def getBarObject(self):
        '''
        Return a configured music21 bar object. This can be used with the current
        Measure or applied to a previous Measure.
        '''
        # get bar objects
        from music21 import bar

        data = self.src[0].strip()  # get first line
        # not all measure first-lines begin w/ measures, such as pickups
        if data[0] != 'm':  # a normal data record
            data = 'measure'

        dataBar = data[1:7]
        # environLocal.printDebug(['getBarObject: dataBar', dataBar])
        if dataBar == 'easure':  # regular
            barlineType = 'regular'
        elif dataBar == 'dotted':
            barlineType = 'dotted'
        elif dataBar == 'double':
            barlineType = 'light-light'
        elif dataBar in ['heavy1', 'heavy']:
            barlineType = 'heavy'
        elif dataBar == 'heavy2':
            barlineType = 'light-heavy'
        elif dataBar == 'heavy3':
            barlineType = 'heavy-light'
        elif dataBar in ['heavy4', 'heave4']:
            barlineType = 'heavy-heavy'
        else:
            raise MuseDataException(f'cannot process bar data definition: {dataBar}')

        bl = bar.Barline(barlineType)

        # numerous flags might be stored at the end of line
        # some flags include A for segno, ~ for wavy line continuation
        if len(data) > 16 and data[16:].strip() != '':
            dataFlag = data[16:].strip()
            if ':|' in dataFlag:
                unused_repeatForm = None  # can be first, second
                bl = bar.Repeat(direction='end')
                bl.type = barlineType
            elif '|:' in dataFlag:
                unused_repeatForm = None  # can be first, second
                bl = bar.Repeat(direction='start')
                bl.type = barlineType
        return bl

    def getMeasureObject(self):
        '''Return a configured music21 :class:`~music21.stream.Measure`.
        '''
        from music21 import stream

        data = self.src[0].strip()  # get first line
        # not all measure first-lines begin w/ measures, such as pickups
        if data[0] != 'm':  # a normal data record
            data = 'measure'

        # see if there is a measure number
        mNumber = '1'
        if len(data) >= 9 and data[8:].strip() != '':
            mNumber, junk = common.getNumFromStr(data)

        m = stream.Measure()
        # assume that this definition refers to this bar; this is not
        # always the case
        m.leftBarline = self.getBarObject()
        # m.rightBarline = None

        if mNumber != '':
            m.number = int(mNumber)
        return m

    def hasNotes(self):
        '''
        Return True of if this Measure has Notes
        '''
        for line in self.src:
            if line and line[0] in 'ABCDEFGrgc':
                return True
        return False

    def hasVoices(self):
        '''Return True of if this Measure defines one or more 'back' indication.

        Note: this does not instantiate MuseDataRecord instances.
        '''
        for line in self.src:
            if line and line.startswith('back'):
                return True
        return False

    def __iter__(self):
        '''
        Iterating over this part returns MuseDataMeasure objects
        '''
        return MuseDataRecordIterator(self.src, self)

    def getRecords(self):
        '''Return a lost of all records stored in this measure as MuseDataRecord.
        '''
        return list(self)


# ------------------------------------------------------------------------------
class MuseDataMeasureIterator:
    '''Create MuseDataMeasure objects on demand, in order
    '''

    def __init__(self, src, boundaries, parent):
        self.src = src  # the lost of all record lines
        self.boundaries = boundaries  # pairs of all boundaries
        self.index = 0
        self.parent = parent

    def __iter__(self):
        return self

    def __next__(self):
        if self.index >= len(self.boundaries):
            raise StopIteration
        start, end = self.boundaries[self.index]
        # add one b/c end is inclusive
        mdm = MuseDataMeasure(self.src[start:end + 1], self.parent)
        self.index += 1
        return mdm

# ------------------------------------------------------------------------------


class MuseDataPart(prebase.ProtoM21Object):
    '''A MuseData part is defined by collection of lines
    '''

    def __init__(self, src=None, stage=None):
        if src is None:
            src = []
        # environLocal.printDebug(['creating MuseDataPart'])
        self.src = src  # a list of character lines for this part

        # a list of start, end indicies for each defined measure
        self._measureBoundaries = []
        self._divisionsPerQuarter = None  # store

        # set to None until called the first time, then return stored value
        self._divisionsPerQuarterNote = None

        self.stage = stage
        if self.stage is None and self.src:
            self.stage = self._determineStage()
        if self.stage == 1:
            self.src = self._scrubStage1(self.src)
        # environLocal.printDebug(['MuseDataPart: stage:', self.stage])

    def _reprInternal(self):
        return ''

    def _determineStage(self):
        '''
        Determine the stage of this file. This is done by looking for an
        attributes record starting with a $; if not found, it is stage 1. if it is found
        it is stage 2.
        '''
        for i in range(len(self.src)):
            if self.src[i].startswith('$'):
                return 2
        return 1

    def _scrubStage1(self, src):
        '''
        Some stage1 files start with a leading line of space.
        This needs to be removed, as each line matters. Provide a list of character lines.
        '''
        if len(src) <= 1:
            raise MuseDataException('cannot scrub empty source')

        check = True
        post = []
        # remove all spaces found in leading lines
        for line in src:
            if check:
                if line.strip() == '':
                    continue
                else:
                    check = False
            post.append(line)
        return post

    def _getDigitsFollowingTag(self, line, tag):
        '''

        >>> mdp = musedata.MuseDataPart()
        >>> mdp._getDigitsFollowingTag('junk WK#:2345', 'WK#:')
        '2345'
        >>> mdp._getDigitsFollowingTag('junk WK#: 2345 junk', 'WK#:')
        '2345'
        >>> mdp._getDigitsFollowingTag('$ K:-3   Q:4   T:3/4   C:22', 'Q:')
        '4'
        >>> mdp._getDigitsFollowingTag('$ K:-3   Q:4   T:3/4   C:22', 'T:')
        '3/4'
        >>> mdp._getDigitsFollowingTag('$ K:-3   Q:4', 'T:')
        ''
        '''
        post = []
        if tag in line:
            i = line.find(tag) + len(tag)
            while i < len(line):
                if line[i].isdigit():
                    post.append(line[i])
                elif line[i].isspace():
                    pass
                elif line[i] in '-/':  # chars to permit
                    post.append(line[i])
                else:  # anything other than space ends gather
                    break
                i += 1
        return ''.join(post)

    def _getAlphasFollowingTag(self, line, tag, keepSpace=False,
                               keepCase=False):
        '''

        >>> mdp = musedata.MuseDataPart()
        >>> mdp._getAlphasFollowingTag('Group memberships: sound, score', 'Group memberships:')
        'sound,score'
        '''
        if not keepCase:
            line = line.lower()
            tag = tag.lower()
        post = []
        if tag in line:
            i = line.find(tag) + len(tag)
            while i < len(line):
                if line[i].isalpha():
                    post.append(line[i])
                elif line[i].isspace() and not keepSpace:
                    pass
                elif line[i].isspace() and keepSpace:
                    post.append(line[i])
                elif line[i] in ',':  # chars to permit
                    post.append(line[i])
                else:  # anything other than space ends gather
                    break
                i += 1
        return ''.join(post)

    def getWorkNumber(self):
        '''
        Returns a String not an int, representing an opus number

        >>> fp1 = (common.getSourceFilePath() / 'musedata' / 'testPrimitive'
        ...                    / 'test01' / '01.md')
        >>> mdw = musedata.MuseDataWork()
        >>> mdw.addFile(fp1)
        >>> mdw.getParts()[0].getWorkNumber()
        '581'
        '''
        if self.stage == 1:
            # seems to be the first half of the second line
            # may have a comma
            # seems to
            data = self.src[1][0:6].strip()
            if ',' in data:
                data = data.split(',')[1]  # get what follows comma
            return data
        else:
            return self._getDigitsFollowingTag(self.src[4], 'WK#:')

    def getMovementNumber(self):
        '''
        Returns a string, not an int.

        >>> fp1 = (common.getSourceFilePath() / 'musedata' / 'testPrimitive'
        ...                    / 'test01' / '01.md')
        >>> mdw = musedata.MuseDataWork()
        >>> mdw.addFile(fp1)
        >>> mdw.getParts()[0].getMovementNumber()
        '3'
        '''
        if self.stage == 1:
            # get the header number: not sure what this is for now
            return self.src[1][6:].strip()
        else:
            return self._getDigitsFollowingTag(self.src[4], 'MV#:')

    def getDirective(self):
        '''
        The directive field is generally used to store tempo indications.
        This indication, however, is frequently not provided.

        >>> fp1 = (common.getSourceFilePath() / 'musedata' / 'testPrimitive'
        ...                    / 'test01' / '01.md')
        >>> mdw = musedata.MuseDataWork()
        >>> mdw.addFile(fp1)
        >>> mdw.getParts()[0].getDirective() is None
        True
        '''
        if self.stage == 1:
            # nothing seems to be defined in stage 1
            return None
        else:
            line = self._getAttributesRecord()
            alphas = self._getAlphasFollowingTag(line, 'D:', keepSpace=True,
                                                 keepCase=True)
            if alphas == '':
                return None
            else:
                return alphas.strip()

    def getSource(self):
        '''
        >>> fp1 = (common.getSourceFilePath() / 'musedata' / 'testPrimitive'
        ...                    / 'test01' / '01.md')
        >>> mdw = musedata.MuseDataWork()
        >>> mdw.addFile(fp1)
        >>> mdw.getParts()[0].getSource()
        'Breitkopf & H...rtel, Vol. 13'
        '''
        if self.stage == 1:
            # get the header number: not sure what this is for now
            data = []
            for line in [self.src[2], self.src[3], self.src[4]]:
                data.append(line.strip())
            # there may be other info packed into this data to strip
            return ''.join(data)
        else:
            return self.src[5]

    def getWorkTitle(self):
        '''
        For stage 1 just gets the catalogue number

        >>> fp1 = (common.getSourceFilePath() / 'musedata' / 'testPrimitive'
        ...                    / 'test01' / '01.md')
        >>> mdw = musedata.MuseDataWork()
        >>> mdw.addFile(fp1)
        >>> mdw.getParts()[0].getWorkTitle()
        'Clarinet Quintet'
        '''
        if self.stage == 1:
            # this does not seem defined for stage 1, so taking catalog number
            return self.src[0].strip()
        else:
            return self.src[6]

    def getMovementTitle(self):
        '''
        >>> fp1 = (common.getSourceFilePath() / 'musedata' / 'testPrimitive'
        ...                    / 'test01' / '01.md')
        >>> mdw = musedata.MuseDataWork()
        >>> mdw.addFile(fp1)
        >>> mdw.getParts()[0].getMovementTitle()
        'Trio II'
        '''
        if self.stage == 1:
            return None
        else:
            return self.src[7]

    def getPartName(self):
        '''
        >>> fp1 = (common.getSourceFilePath() / 'musedata' / 'testPrimitive'
        ...                    / 'test01' / '01.md')
        >>> mdw = musedata.MuseDataWork()
        >>> mdw.addFile(fp1)
        >>> mdw.getParts()[0].getPartName()
        'Clarinet in A'
        '''
        if self.stage == 1:
            return None
        else:
            return self.src[8].strip()

    def getGroupMemberships(self):
        '''
        >>> fp1 = (common.getSourceFilePath() / 'musedata' / 'testPrimitive'
        ...                    / 'test01' / '01.md')
        >>> mdw = musedata.MuseDataWork()
        >>> mdw.addFile(fp1)
        >>> mdw.getParts()[0].getGroupMemberships()
        ['sound', 'score']
        '''
        if self.stage == 1:
            return []
        else:
            raw = self._getAlphasFollowingTag(self.src[10],
                                              'group memberships:')
            post = []
            for entry in raw.split(','):
                if entry.strip() != '':
                    post.append(entry.strip())
            return post

    def getGroupMembershipsTotal(self, membership='score'):
        '''
        >>> fp1 = str(common.getSourceFilePath() /'musedata' / 'testPrimitive'
        ...                    / 'test01' / '01.md')
        >>> mdw = musedata.MuseDataWork()
        >>> mdw.addFile(fp1)
        >>> mdw.getParts()[0].getGroupMembershipsTotal()
        5
        '''
        if self.stage == 1:
            # first value is total number
            return int(self.src[5].split(' ')[0])
        else:
            i = 11  # start with index 11, move to line tt starts with $
            raw = None
            while not self.src[i].startswith('$'):
                line = self.src[i]
                if line.startswith(membership):
                    raw = self._getDigitsFollowingTag(line, 'of')
                    break
                i += 1
            if raw is None:
                return None
            else:
                return int(raw)

    def getGroupMembershipNumber(self, membership='score'):
        '''
        >>> fp1 = (common.getSourceFilePath() / 'musedata' / 'testPrimitive'
        ...                    / 'test01' / '01.md')
        >>> mdw = musedata.MuseDataWork()
        >>> mdw.addFile(fp1)
        >>> mdw.getParts()[0].getGroupMembershipNumber()
        1
        '''
        if self.stage == 1:
            # second value is this works part number
            return self.src[5].split(' ')[1]
        else:
            i = 11  # start with index 11, move to line tt starts with $
            raw = None
            while not self.src[i].startswith('$'):
                line = self.src[i]
                if line.startswith(membership):
                    raw = self._getDigitsFollowingTag(line, 'part')
                    break
                i += 1
            if raw is None:
                return None
            else:
                return int(raw)

    def _getAttributesRecord(self):
        '''
        The attributes record is not in a fixed position,
        but is the first line that starts with a $.


        >>> fp1 = (common.getSourceFilePath() / 'musedata' / 'testPrimitive'
        ...                    / 'test01' / '01.md')
        >>> mdw = musedata.MuseDataWork()
        >>> mdw.addFile(fp1)
        >>> mdw.getParts()[0]._getAttributesRecord()
        '$  K:0   Q:6   T:3/4   X:-11   C:4'
        '''
        if self.stage == 1:
            # combine the two lines into one, all space separated
            record = self.src[6].strip() + ' ' + self.src[7].strip()
            # environLocal.printDebug(['got attributes record:', record])
            return record
        else:
            i = 11  # start with index 11, move to line tt starts with $
            while not self.src[i].startswith('$'):
                i += 1
            return self.src[i]

    def getKeyParameters(self):
        '''
        >>> fp1 = (common.getSourceFilePath() / 'musedata' / 'testPrimitive'
        ...                   / 'test01' / '01.md')
        >>> mdw = musedata.MuseDataWork()
        >>> mdw.addFile(fp1)
        >>> mdw.getParts()[0].getKeyParameters()
        0
        '''
        line = self._getAttributesRecord()
        if self.stage == 1:
            return int(line.split(' ')[1])
        else:
            # '$ K:-3   Q:4   T:3/4   C:22', 'Q:'
            return int(self._getDigitsFollowingTag(line, 'K:'))

    def getKeySignature(self):
        '''
        >>> fp1 = (common.getSourceFilePath() / 'musedata' / 'testPrimitive'
        ...                    / 'test01' / '01.md')
        >>> mdw = musedata.MuseDataWork()
        >>> mdw.addFile(fp1)
        >>> mdw.getParts()[0].getKeySignature()
        <music21.key.KeySignature of no sharps or flats>
        '''
        from music21 import key
        return key.KeySignature(self.getKeyParameters())

    def getTimeSignatureParameters(self):
        '''
        >>> fp1 = (common.getSourceFilePath() / 'musedata' / 'testPrimitive'
        ...                   / 'test01' / '01.md')
        >>> mdw = musedata.MuseDataWork()
        >>> mdw.addFile(fp1)
        >>> mdw.getParts()[0].getTimeSignatureParameters()
        '3/4'
        '''
        line = self._getAttributesRecord()
        if self.stage == 1:
            n = int(line.split(' ')[4])
            d = int(line.split(' ')[5])
        else:
            # '$ K:-3   Q:4   T:3/4   C:22', 'Q:'
            n, d = self._getDigitsFollowingTag(line, 'T:').split('/')
            n, d = int(n), int(d)
        # usage of 1/1 is common and seems to need replacement to 4/4, or
        # common time
        if (n == 1 and d == 1) or d == 0:
            return '4/4'
        else:
            return f'{n}/{d}'

    def getTimeSignatureObject(self):
        '''
        >>> fp1 = (common.getSourceFilePath() / 'musedata' / 'testPrimitive'
        ...                    / 'test01' / '01.md')
        >>> mdw = musedata.MuseDataWork()
        >>> mdw.addFile(fp1)
        >>> mdw.getParts()[0].getTimeSignatureObject()
        <music21.meter.TimeSignature 3/4>
        '''
        from music21 import meter
        return meter.TimeSignature(self.getTimeSignatureParameters())

    def _getNumberOfStaves(self):
        '''
        >>> fp1 = (common.getSourceFilePath() / 'musedata' / 'testPrimitive'
        ...                    / 'test01' / '01.md')
        >>> mdw = musedata.MuseDataWork()
        >>> mdw.addFile(fp1)
        >>> mdw.getParts()[0]._getNumberOfStaves()
        1
        '''
        if self.stage == 1:
            # may always be 1
            return 1
        else:
            line = self._getAttributesRecord()
            # '$ K:-3   Q:4   T:3/4   C:22', 'Q:'
            raw = self._getDigitsFollowingTag(line, 'S:')
            if raw == '':
                return 1  # default
            else:
                return int(raw)

    def _getClefParameters(self):
        '''
        >>> fp1 = (common.getSourceFilePath() / 'musedata' / 'testPrimitive'
        ...                   / 'test01' / '01.md')
        >>> mdw = musedata.MuseDataWork()
        >>> mdw.addFile(fp1)
        >>> mdw.getParts()[0]._getClefParameters()
        ['4']
        '''
        # clef may be givne as C: or Cn:, where n is the number for
        # a staff, if multiple staves are included in this parts

        line = self._getAttributesRecord()

        if self.stage == 1:
            # this seems to be the clef value, though numbers do not
            # match that found in stage 2
            data = line.split(' ')[8]
            return [data]
        else:
            # '$ K:-3   Q:4   T:3/4   C:22', 'Q:'
            # keep as string, as these are two-char codes
            post = []
            raw = self._getDigitsFollowingTag(line, 'C:')
            if raw != '':
                post.append(raw)
            if raw == '':
                # find max number of staffs
                for i in range(1, self._getNumberOfStaves() + 1):
                    raw = self._getDigitsFollowingTag(line, f'C{i}:')
                    if raw != '':
                        post.append(raw)
            return post

    def getClefObject(self, voice=1):
        '''Return a music21 clef object based on a two character clef definition.

        >>> fp1 = (common.getSourceFilePath() / 'musedata' / 'testPrimitive'
        ...                    / 'test01' / '01.md')
        >>> mdw = musedata.MuseDataWork()
        >>> mdw.addFile(fp1)
        >>> mdw.getParts()[0].getClefObject().sign
        'G'
        '''
        if self.stage == 1:
            return None  # cannot yet determine
        else:
            # there may be more than one clef definition
            charPair = self._getClefParameters()[voice - 1]
            # convert to int and back to string to strip zeros
            charPair = str(int(charPair))
            from music21 import clef

            if charPair == '5':
                return clef.FrenchViolinClef()
            elif charPair == '4':  # line 4 is 2nd from bottom
                return clef.TrebleClef()

            elif charPair == '34':  # 3 here is G 8vb
                return clef.Treble8vbClef()
            elif charPair == '64':  # 6 here is G 8va
                return clef.Treble8vaClef()
            elif charPair == '3':
                return clef.GSopranoClef()

            elif charPair == '11':
                return clef.CBaritoneClef()
            elif charPair == '12':
                return clef.TenorClef()
            elif charPair == '13':
                return clef.AltoClef()
            elif charPair == '14':
                return clef.MezzoSopranoClef()
            elif charPair == '15':  # 5 is lowest line
                return clef.SopranoClef()

            elif charPair == '22':
                return clef.BassClef()
            elif charPair == '23':  # middle line:
                return clef.FBaritoneClef()

            elif charPair == '52':  # 5 is transposed down f-clef
                return clef.Bass8vbClef()
            elif charPair == '82':  # 8 is transposed up f-clef
                return clef.Bass8vaClef()
            else:
                raise MuseDataException('cannot determine clef from:', charPair)

    def _getTranspositionParameters(self):
        '''
        Get the transposition, if defined, from the Metadata header.


        >>> fp1 = (common.getSourceFilePath() / 'musedata' / 'testPrimitive'
        ...                    / 'test01' / '01.md')
        >>> fp2 = (common.getSourceFilePath() / 'musedata' / 'testPrimitive'
        ...                    / 'test01' / '02.md')
        >>> mdw = musedata.MuseDataWork()
        >>> mdw.addFile(fp1)
        >>> mdw.addFile(fp2)
        >>> mdw.getParts()[0]._getTranspositionParameters()
        -11
        >>> mdw.getParts()[1]._getTranspositionParameters() is None
        True
        '''
        line = self._getAttributesRecord()
        if self.stage == 1:
            return None  # not sure if or if, how, this is defined
        else:
            raw = self._getDigitsFollowingTag(line, 'X:')
            if raw == '':
                return None
            else:
                return int(raw)

    def getTranspositionIntervalObject(self):
        '''If this part defines a transposition, return a corresponding Interval object.

        >>> fp1 = (common.getSourceFilePath() / 'musedata' / 'testPrimitive'
        ...                    / 'test01' / '01.md')
        >>> fp2 = (common.getSourceFilePath() / 'musedata' / 'testPrimitive'
        ...                    / 'test01' / '02.md')
        >>> mdw = musedata.MuseDataWork()
        >>> mdw.addFile(fp1)
        >>> mdw.addFile(fp2)
        >>> mdw.getParts()[0].getTranspositionIntervalObject()
        <music21.interval.Interval m-3>
        '''
        # transposition intervals are given in base40; must convert to intervals
        args = self._getTranspositionParameters()
        if args is None:
            return None
        else:
            return base40.base40DeltaToInterval(args)

    def getDivisionsPerQuarterNote(self):
        '''
        >>> fp1 = (common.getSourceFilePath() / 'musedata' / 'testPrimitive'
        ...                    / 'test01' / '01.md')
        >>> mdw = musedata.MuseDataWork()
        >>> mdw.addFile(fp1)
        >>> mdw.getParts()[0].getDivisionsPerQuarterNote()
        6
        '''
        if self._divisionsPerQuarterNote is None:
            # set once the first time this is called
            line = self._getAttributesRecord()

            if self.stage == 1:
                # this value is divisions per bar, not quarter here
                data = int(line.split(' ')[2])
                ts = self.getTimeSignatureObject()
                # data here is divisions per bar; need to divide by ts
                # quarter length
                self._divisionsPerQuarterNote = data / ts.barDuration.quarterLength
                # environLocal.printDebug(['stage1: self._divisionsPerQuarterNote',
                #        self._divisionsPerQuarterNote])
            else:
                # '$ K:-3   Q:4   T:3/4   C:22', 'Q:'
                self._divisionsPerQuarterNote = int(
                    self._getDigitsFollowingTag(line, 'Q:'))

        return self._divisionsPerQuarterNote

    # --------------------------------------------------------------------------
    # dealing with measures and notes

    def _getMeasureBoundaryIndices(self, src=None):
        '''

        >>> mdp = musedata.MuseDataPart()
        >>> mdp.stage is None
        True
        >>> mdp._getMeasureBoundaryIndices(['$', 'A', 'B', 'm', 'C', 'm', 'D'])
        [(1, 2), (3, 4), (5, 6)]
        >>> mdp._getMeasureBoundaryIndices(['$', 'm', 'B', 'C', 'm', 'D', 'E', 'm', 'F', 'D'])
        [(1, 3), (4, 6), (7, 9)]
        >>> mdp._getMeasureBoundaryIndices(['$', 'B', 'C', 'm', 'D', 'E'])
        [(1, 2), (3, 5)]
        '''
        if src is None:
            src = self.src
        boundaries = []
        mIndices = []
        firstPostAttributesIndex = None
        lastIndex = len(src) - 1

        if self.stage == 1:
            # pickup measures use measure 0 for stage 1
            for i, line in enumerate(src):
                if line.startswith('m'):
                    mIndices.append(i)
            # always the measure definition found
            firstPostAttributesIndex = mIndices[0]
        else:
            # first, get index positions
            mAttributeRecordCount = 0  # store number of $ found
            # all comment lines have already been stripped from the representaiton
            for i, line in enumerate(src):
                if line.startswith('$'):
                    mAttributeRecordCount += 1
                    continue
                if mAttributeRecordCount > 0 and firstPostAttributesIndex is None:
                    firstPostAttributesIndex = i
                    # do not continue, as this may also be a measure start
                if line.startswith('m'):
                    mIndices.append(i)

        # second, match pairs
        # if start of music is start of measure
        startIterIndex = None
        if mIndices[0] == firstPostAttributesIndex:
            if len(mIndices) == 1:
                boundaries.append((mIndices[0], lastIndex))
                startIterIndex = None
            else:
                boundaries.append((mIndices[0], mIndices[1] - 1))
                startIterIndex = 1
        # if there is a pickup measure
        else:
            boundaries.append((firstPostAttributesIndex, mIndices[0] - 1))
            startIterIndex = 0

        if startIterIndex is not None:
            for i in range(startIterIndex, len(mIndices)):
                # if the last
                if i == len(mIndices) - 1:
                    boundaries.append((mIndices[i], lastIndex))
                else:
                    boundaries.append((mIndices[i], mIndices[i + 1] - 1))

        return boundaries

    def update(self):
        '''
        After setting the source string, this method must be called to configure
        the _measureNumberToLine method and set additional attributes.
        '''
        self._divisionsPerQuarter = self.getDivisionsPerQuarterNote()
        self._measureBoundaries = self._getMeasureBoundaryIndices()

    def __iter__(self):
        '''
        Iterating over this part returns MuseDataMeasure objects
        '''
        return MuseDataMeasureIterator(self.src, self._measureBoundaries, self)

    def getMeasures(self):
        '''Return a list of all measures stored in this part as MuseDataMeasure objects.
        '''
        return list(self)


# ------------------------------------------------------------------------------
class MuseDataFile(prebase.ProtoM21Object):
    '''
    A MuseDataFile file may describe one or more MuseDataPart;
    a Score might need multiple files for complete definition.
    A MuseDataFile object can be created from a string.

    When read, one or more MuseDataPart objects are created and stored on self.parts.
    '''

    def __init__(self):
        self.parts = []  # a lost of MuseDataPart objects

        self.filename = None
        self.file = None

    def _reprInternal(self):
        return ''

    def open(self, fp):
        # self.file = io.open(filename, encoding='utf-8')

        self.file = open(fp, 'rb')
        self.filename = fp

    def read(self):
        # call readstr with source string from file
        fileContents = self.file.read()
        try:
            fileContents = fileContents.decode('utf-8')
        except UnicodeDecodeError:
            fileContents = fileContents.decode('ISO-8859-1', 'ignore')
        return self.readstr(fileContents)

    def close(self):
        self.file.close()

    def readstr(self, input_str):
        '''
        Read a string, dividing it into individual parts.
        '''
        # environLocal.printDebug(['readstr()', 'len(str)', len(str)])
        # need to split the string into individual parts, as more than
        # one part might be defined
        commentToggle = False

        lines = []
        srcLines = input_str.split('\n')
        # lastLineIndex = len(srcLines) - 1
        for i, line in enumerate(srcLines):
            # environLocal.printDebug(['reading line', i, line])

            # each part, or the entire file, will end with /END
            if line.startswith('&'):
                if commentToggle:
                    commentToggle = False
                    continue
                else:
                    commentToggle = True
                    continue

            if commentToggle:
                continue  # skip block comment lines
            elif line and line[0] == '@':
                continue
            # stage 1 files use END, stage 2 uses /END
            elif line.startswith('/END') or line.startswith('END'):
                # environLocal.printDebug(['found last line', i, repr(line),
                #        'length of lines', len(lines)])
                # anticipate malformed files that have more than one END at END
                if len(lines) <= 1:
                    lines = []  # clear storage
                    continue
                mdp = MuseDataPart(lines)
                # update sets measure boundaries, divisions
                mdp.update()
                self.parts.append(mdp)
                lines = []  # clear storage
            # mostly redundant; seems to follow /END; do not include
            elif line.startswith('/eof'):
                pass
            else:  # gather all else
                lines.append(line)


# ------------------------------------------------------------------------------
class MuseDataWork(prebase.ProtoM21Object):
    '''A work might consist of one or more files.
    '''

    def __init__(self):
        self.files = []  # a list of one or more MuseDataFile objects

    def addFile(self, fp):
        '''
        Open and read this file path or list of paths as MuseDataFile objects
        and set self.files
        '''
        if not common.isIterable(fp):
            fpList = [fp]
        else:
            fpList = fp

        for fpInner in fpList:
            mdf = MuseDataFile()
            # environLocal.printDebug('processing MuseData file: %s' % fp)
            mdf.open(fpInner)
            mdf.read()  # process string and break into parts
            mdf.close()
            self.files.append(mdf)

    def addString(self, input_str):
        r'''
        Add a string representation acting like a part file

        >>> mdw = musedata.MuseDataWork()
        >>> mdw.addString('WK#:581       MV#:3c\nBreitkopf & Hartel, Vol. 13\n' +
        ...               'Clarinet Quintet\n' +
        ...               'Trio II\n' +
        ...               '$  K:0   Q:6   T:3/4   X:-11   C:4\n' +
        ...               'C5     3        e     d  [     (&0p\n' +
        ...               'E5     3        e     d  ]')

        # TODO: Okay, so what? did we test this or demo anything?
        '''
        # environLocal.printDebug(['addString str', str])
#         if str.strip() == '':
#             raise MuseDataException('passed in empty string to add string')
        if not common.isIterable(input_str):
            strList = [input_str]
        else:
            strList = input_str

        for thisString in strList:
            mdf = MuseDataFile()
            mdf.readstr(thisString)  # process string and break into parts
            self.files.append(mdf)

    # --------------------------------------------------------------------------

    def getParts(self):
        '''
        Get all parts contained in all files associated with this work.
        A list of MuseDataPart objects that were created in a MuseDataFile.
        '''
        # TODO: may need to sort parts by group membership values and
        # numbers
        post = []
        for mdf in self.files:
            for mdp in mdf.parts:
                post.append(mdp)
        return post


# ------------------------------------------------------------------------------
class MuseDataDirectory(prebase.ProtoM21Object):
    '''
    This class manages finding musedata files stored in a directory,
    comparing file names and examining sub directories to determine which files are parts.

    Once found, a MuseDataWork, or a list of paths, can be returned

    A directory, or a list of file path stubs, such as that obtained within a zip file,
    can both be provided.
    '''

    def __init__(self, dirOrList):
        self.paths = []
        self.groups = {}  # use fp as key; store 'number'

        self._prepareGroups(dirOrList)

    def _prepareGroups(self, dirOrList):
        # environLocal.printDebug(['_prepareGroups', dirOrList])

        allPaths = []
        # these two were unused variables.
        # sep = '/'
        # source = None  # set where files are coming from
        if common.isIterable(dirOrList):
            # assume a flat list from a zip file
            # sep = '/'  # sep is always backslash for zip files
            # source = 'zip'
            allPaths = dirOrList
            # for fp in dirOrList:
            #     if self.isMusedataFile(fp):
            #         self.paths.append(fp)
        elif os.path.isdir(dirOrList):
            # source = 'dir'
            # sep = os.sep
            # first, get the contents of the dir and see if it has md files
            for fn in sorted(os.listdir(dirOrList)):
                allPaths.append(os.path.join(dirOrList, fn))
                # if not self.isMusedataFile(fn):
                #     continue
                # numStr, nonNumStr = common.getNumFromStr(fn)
                # # if we cannot get a number out of the file name
                # if numStr == '':
                #     continue
                # else:
                #     self.paths.append(os.path.join(dirOrList, fn))
        else:
            raise MuseDataException('cannot get files from the following entity', dirOrList)

        for fp in allPaths:
            unused_directory, fn = os.path.split(fp)
            if not self.isMusedataFile(fn):
                continue
            numStr, nonNumStr = common.getNumFromStr(fn)
            # if we cannot get a number out of the file name
            if numStr == '':
                continue
            else:
                self.paths.append(fp)

        # on second pass, remove any score file if we have part files
        # score files start with an s
        popList = []
        if len(self.paths) > 1:
            for i, fp in enumerate(self.paths):
                unused_directory, fn = os.path.split(fp)
                # if it has a number and starts with s
                numStr, nonNumStr = common.getNumFromStr(fn)
                if numStr != '' and nonNumStr.startswith('s'):
                    popList.append(i)
            popList.reverse()
            for i in popList:
                self.paths.pop(i)
        else:  # if only one file, use it
            pass

        # after gathering paths, may need to sort/get by groups
        self.paths.sort()
        # environLocal.printDebug(['self.paths', self.paths])

    # noinspection SpellCheckingInspection
    def isMusedataFile(self, fp):
        # look for file extension; not often used
        # cannot open file and look, as names from a zip archive are not
        # directly openable
        # environLocal.printDebug(['isMusedataFile: checking:', fp])
        unused_dir, fn = os.path.split(fp)
        if fp.endswith('.md'):
            return True
        elif fn.startswith('mchan'):  # ignore midi declaration files
            return False
        # directories from a zip will end in '/', or os.sep
        elif (fp.endswith('.py')
              or fp.endswith('/')
              or fp.endswith(os.sep)
              or fn.startswith('.')
              or fp.endswith('.svn-base')):
            return False
        return True

    def getPaths(self, group=None):
        '''Return sorted paths for a group, or None
        '''
        # environLocal.printDebug(['getPaths() called with self.paths', self.paths])
        return self.paths


# ------------------------------------------------------------------------------
# noinspection SpellCheckingInspection
class Test(unittest.TestCase):

    # def testLoadFromString(self):
    #     from music21.musedata import testFiles
    #
    #     mdw = MuseDataWork()
    #     mdw.addString(testFiles.bach_cantata5_mvmt3)
    #
    #     mdpObjs = mdw.getParts()
    #     self.assertEqual(len(mdpObjs), 3)
    #     # first line of src strings
    #     self.assertEqual(mdpObjs[0].src[1],
    #            'ID: {bach/bg/cant/0005/stage2/03/01} [KHM:1658122244]')
    #
    #     self.assertEqual(mdpObjs[1].src[1],
    #            'ID: {bach/bg/cant/0005/stage2/03/02} [KHM:1658122244]')
    #
    #     self.assertEqual(mdpObjs[2].src[1],
    #            'ID: {bach/bg/cant/0005/stage2/03/03} [KHM:1658122244]')
    #
    #     for i in range(3):
    #         self.assertEqual(mdpObjs[i].getWorkNumber(), '5')
    #         self.assertEqual(mdpObjs[i].getMovementNumber(), '3')
    #         self.assertEqual(mdpObjs[i].getSource(), 'Bach Gesellschaft i')
    #         self.assertEqual(mdpObjs[i].getWorkTitle(), 'Wo soll ich fliehen hin')
    #         self.assertEqual(mdpObjs[i].getMovementTitle(), 'Aria')
    #
    #
    #     self.assertEqual(mdpObjs[0].getKeyParameters(), -3)
    #     self.assertEqual(mdpObjs[0].getTimeSignatureParameters(), '3/4')
    #     self.assertEqual(mdpObjs[0].getDivisionsPerQuarterNote(), 4)

    def testLoadFromFile(self):
        fp = str(common.getSourceFilePath() / 'musedata' / 'testPrimitive')

        mdw = MuseDataWork()

        dirLib = os.path.join(fp, 'test01')
        for fn in ['01.md', '02.md', '03.md', '04.md', '05.md']:
            fp = os.path.join(dirLib, fn)
            # environLocal.printDebug([fp])

            mdw.addFile(fp)

        mdpObjs = mdw.getParts()
        self.assertEqual(len(mdpObjs), 5)
        # first line of src strings
        self.assertEqual(mdpObjs[0].src[4], 'WK#:581       MV#:3c')
        self.assertEqual(mdpObjs[0].src[12], 'score: part 1 of 5')

        self.assertEqual(mdpObjs[1].src[4], 'WK#:581       MV#:3c')
        self.assertEqual(mdpObjs[1].src[12], 'score: part 2 of 5')

        self.assertEqual(mdpObjs[2].src[4], 'WK#:581       MV#:3c')
        self.assertEqual(mdpObjs[2].src[12], 'score: part 3 of 5')

        self.assertEqual(mdpObjs[3].src[4], 'WK#:581       MV#:3c')
        self.assertEqual(mdpObjs[3].src[12], 'score: part 4 of 5')

        self.assertEqual(mdpObjs[4].src[4], 'WK#:581       MV#:3c')
        self.assertEqual(mdpObjs[4].src[12], 'score: part 5 of 5')

        # all files have the same metadata
        for i in range(4):
            self.assertEqual(mdpObjs[i].getWorkNumber(), '581')
            self.assertEqual(mdpObjs[i].getMovementNumber(), '3')
            self.assertTrue(mdpObjs[i].getSource().startswith('Breitkopf'))
            self.assertEqual(mdpObjs[i].getWorkTitle(), 'Clarinet Quintet')
            self.assertEqual(mdpObjs[i].getMovementTitle(), 'Trio II')

            self.assertEqual(mdpObjs[i].getGroupMemberships(), ['sound', 'score'])

            self.assertEqual(mdpObjs[i].getGroupMembershipsTotal('score'), 5)
            self.assertEqual(mdpObjs[i].getGroupMembershipsTotal('sound'), 5)

        self.assertEqual(mdpObjs[0].getGroupMembershipNumber('score'), 1)
        self.assertEqual(mdpObjs[0].getGroupMembershipNumber('sound'), 1)
        self.assertEqual(mdpObjs[1].getGroupMembershipNumber('score'), 2)
        self.assertEqual(mdpObjs[1].getGroupMembershipNumber('sound'), 2)
        self.assertEqual(mdpObjs[2].getGroupMembershipNumber('score'), 3)
        self.assertEqual(mdpObjs[2].getGroupMembershipNumber('sound'), 3)

        self.assertEqual(mdpObjs[3].getGroupMembershipNumber('score'), 4)
        self.assertEqual(mdpObjs[3].getGroupMembershipNumber('sound'), 4)
        self.assertEqual(mdpObjs[4].getGroupMembershipNumber('score'), 5)
        self.assertEqual(mdpObjs[4].getGroupMembershipNumber('sound'), 5)

        self.assertEqual(mdpObjs[0].getKeyParameters(), 0)
        self.assertEqual(mdpObjs[0].getTimeSignatureParameters(), '3/4')
        self.assertEqual(mdpObjs[0].getDivisionsPerQuarterNote(), 6)


    # def testIterateMeasuresFromString(self):
    #
    #     from music21.musedata import testFiles
    #
    #     mdw = MuseDataWork()
    #     mdw.addString(testFiles.bach_cantata5_mvmt3)
    #     mdpObjs = mdw.getParts()
    #     # can iterate over measures, creating them as iterating
    #     for m in mdpObjs[0]:
    #         self.assertIsInstance(m, MuseDataMeasure)
    #
    #         # iterate over measures to get notes
    #         for n in m:
    #             self.assertIsInstance(n, MuseDataRecord)
    #
    #     # cannot access them as in a list, however
    #     # self.assertTrue(mdpObjs[0][0])
    #
    #     # try using stored objects
    #     measures = mdpObjs[0].getMeasures()
    #     self.assertIsInstance(measures[0], MuseDataMeasure)
    #     self.assertEqual(len(measures), 106)
    #
    #     records = measures[4].getRecords()
    #     self.assertIsInstance(records[0], MuseDataRecord)
    #     self.assertEqual(len(records), 13)

    def testMuseDataDirectory(self):
        # from music21 import converter
        # fp = os.path.join(common.getSourceFilePath(), 'musedata', 'testZip.zip')

        fpDir = str(common.getSourceFilePath() / 'musedata' / 'testPrimitive' / 'test01')

        unused_mdd = MuseDataDirectory(fpDir)

        # from archive: note: this is a stage 1 file
        # fpArchive = str(common.getSourceFilePath() / 'musedata' / 'testZip.zip')
        # af = converter.ArchiveManager(fpArchive)
        # unused_mdd = MuseDataDirectory(af.getNames())

    # def testStage1A(self):
    #
    #     from music21.musedata import testFiles
    #     mdw = MuseDataWork()
    #     mdw.addString(testFiles.bachContrapunctus1_part1)
    #     mdw.addString(testFiles.bachContrapunctus1_part2)
    #
    #     mdpObjs = mdw.getParts()
    #
    #     # all files have the same metadata
    #     for i in range(2):
    #         self.assertEqual(mdpObjs[i].getWorkNumber(), '1080')
    #         self.assertEqual(mdpObjs[i].getMovementNumber(), '1')
    #         self.assertEqual(mdpObjs[i].getSource(), 'Bach Gesellschaft xxv,1')
    #         self.assertEqual(mdpObjs[i].getGroupMembershipsTotal(), 4)
    #
    #     self.assertEqual(mdpObjs[0].getKeyParameters(), -1)
    #     self.assertEqual(mdpObjs[0].getTimeSignatureParameters(), '2/2')
    #     self.assertEqual(mdpObjs[0].getDivisionsPerQuarterNote(), 4.0)

    def testGetLyrics(self):
        mdr = MuseDataRecord('D4     2        e     u                    con-')
        mdr.stage = 2
        self.assertEqual(mdr.getLyrics(), ['con-'])

        mdr = MuseDataRecord('F#4    2        e     u                    a')
        mdr.stage = 2
        self.assertEqual(mdr.getLyrics(), ['a'])

        mdr = MuseDataRecord('F#4    2        e     u                    a | b')
        mdr.stage = 2
        self.assertEqual(mdr.getLyrics(), ['a', 'b'])


    # def testMeasureNumberImport(self):
    #     from music21 import corpus
    #     s = corpus.parse('symphony94/02')
    #     for p in s.parts:
    #         match = []
    #         for m in p.getElementsByClass('Measure'):
    #             match.append(m.number)
    #         self.assertEqual(len(match), 156)
    #         # make sure there are no empty strings
    #         self.assertEqual(match.count(''), 0)
    #
    #     self.assertEqual(len(s.parts[-1].flat.notes), 287)
# ------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [MuseDataWork]


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)


