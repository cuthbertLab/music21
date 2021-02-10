# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         abc/__init__.py
# Purpose:      parses ABC Notation
#
# Authors:      Christopher Ariza
#               Dylan J. Nagler
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2010, 2013 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
ABC is a music format that, while being able to encode all sorts of scores, is especially
strong at representing monophonic music, and folk music in particular.

Modules in the `music21.abcFormat` package deal with importing ABC into music21.  Most people
working with ABC data won't need to use this package.  To convert ABC from a file or URL
to a :class:`~music21.stream.Stream` use the :func:`~music21.converter.parse` function of
the `converter` module:

>>> #_DOCS_SHOW from music21 import *
>>> #_DOCS_SHOW abcScore = converter.parse('/users/ariza/myScore.abc')

For users who will be editing ABC extensively or need a way to have music21 output ABC
(which it doesn't do natively), we suggest using the open source EasyABC package:
http://www.nilsliberg.se/ksp/easyabc/ .  You can set it up as a MusicXML reader through:

>>> #_DOCS_SHOW us = environment.UserSettings()
>>> #_DOCS_SHOW us['musicxmlPath'] = '/Applications/EasyABC.app'

or wherever you have downloaded EasyABC to
(PC users might need: 'c:/program files (x86)/easyabc/easyabc.exe')
(Thanks to Norman Schmidt for the heads up)

There is a two-step process in converting ABC files to Music21 Streams.  First this module
reads in the text-based .abc file and converts all the information into ABCToken objects.  Then
the function :func:`music21.abcFormat.translate.abcToStreamScore` of
the :ref:`moduleAbcFormatTranslate` module
translates those Tokens into music21 objects.
'''
__all__ = [
    'translate',
    'testFiles',
    'ABCTokenException', 'ABCHandlerException', 'ABCFileException',
    'ABCToken',
    'ABCMetadata', 'ABCBar', 'ABCTuplet', 'ABCTie',
    'ABCSlurStart', 'ABCParenStop', 'ABCCrescStart', 'ABCDimStart',
    'ABCStaccato', 'ABCUpbow', 'ABCDownbow', 'ABCAccent', 'ABCStraccent',
    'ABCTenuto', 'ABCGraceStart', 'ABCGraceStop', 'ABCBrokenRhythmMarker',
    'ABCNote', 'ABCChord',
    'ABCHandler', 'ABCHandlerBar',
    'mergeLeadingMetaData',
    'ABCFile',
]

import copy
import io
import pathlib
import re
import unittest
from typing import Union, Optional, List, Tuple, Any

from music21 import common
from music21 import environment
from music21 import exceptions21
from music21 import prebase

from music21.abcFormat import translate

environLocal = environment.Environment('abcFormat')

# for implementation
# see http://abcnotation.com/abc2mtex/abc.txt

# store symbol and m21 naming/class eq
ABC_BARS = [
    (':|1', 'light-heavy-repeat-end-first'),
    (':|2', 'light-heavy-repeat-end-second'),
    ('|]', 'light-heavy'),
    ('||', 'light-light'),
    ('[|', 'heavy-light'),
    ('[1', 'regular-first'),  # preferred format
    ('[2', 'regular-second'),
    ('|1', 'regular-first'),  # gets converted
    ('|2', 'regular-second'),
    (':|', 'light-heavy-repeat-end'),
    ('|:', 'heavy-light-repeat-start'),
    ('::', 'heavy-heavy-repeat-bidirectional'),
    # for comparison, single chars must go last
    ('|', 'regular'),
    (':', 'dotted'),
]

# store a mapping of ABC representation to pitch values
_pitchTranslationCache = {}


# ------------------------------------------------------------------------------
# note inclusion of w: for lyrics
reMetadataTag = re.compile('[A-Zw]:')
rePitchName = re.compile('[a-gA-Gz]')
reChordSymbol = re.compile('"[^"]*"')  # non greedy
reChord = re.compile('[.*?]')  # non greedy
reAbcVersion = re.compile(r'^%abc-((\d+)\.(\d+)\.?(\d+)?)')
reDirective = re.compile(r'^%%([a-z\-]+)\s+([^\s]+)(.*)')


# ------------------------------------------------------------------------------
class ABCTokenException(exceptions21.Music21Exception):
    pass


class ABCHandlerException(exceptions21.Music21Exception):
    pass


class ABCFileException(exceptions21.Music21Exception):
    pass
#


# ------------------------------------------------------------------------------
class ABCToken(prebase.ProtoM21Object):
    '''
    ABC processing works with a multi-pass procedure. The first pass
    breaks the data stream into a list of ABCToken objects. ABCToken
    objects are specialized in subclasses.

    The multi-pass procedure is conducted by an ABCHandler object.
    The ABCHandler.tokenize() method breaks the data stream into
    ABCToken objects. The :meth:`~music21.abcFormat.ABCHandler.tokenProcess` method first
    calls the :meth:`~music21.abcFormat.ABCToken.preParse` method on each token,
    then does contextual
    adjustments to all tokens, then calls :meth:`~music21.abcFormat.ABCToken.parse` on all tokens.

    The source ABC string itself is stored in self.src
    '''
    def __init__(self, src=''):
        self.src: str = src  # store source character sequence

    def _reprInternal(self):
        return repr(self.src)

    @staticmethod
    def stripComment(strSrc):
        '''
        removes ABC-style comments from a string:

        >>> ao = abcFormat.ABCToken()
        >>> ao.stripComment('asdf')
        'asdf'
        >>> ao.stripComment('asdf%234')
        'asdf'
        >>> ao.stripComment('asdf  %     234')
        'asdf  '
        >>> ao.stripComment('[ceg]% this chord appears 50% more often than other chords do')
        '[ceg]'

        This is a static method, so it can also be called on the class itself:

        >>> abcFormat.ABCToken.stripComment('b1 % a b-flat actually')
        'b1 '

        Changed: v6.2 -- made a staticmethod
        '''
        if '%' in strSrc:
            return strSrc.split('%')[0]
        return strSrc

    def preParse(self):
        '''
        Dummy method that is called before contextual adjustments.
        Designed to be subclassed or overridden.
        '''
        pass

    def parse(self):
        '''
        Dummy method that reads self.src and loads attributes.
        It is called after contextual adjustments.

        It is designed to be subclassed or overridden.
        '''
        pass


class ABCMetadata(ABCToken):
    '''
    Defines a token of metadata in ABC.

    >>> md = abcFormat.ABCMetadata('I:linebreak')
    >>> md.src
    'I:linebreak'

    Has two attributes, `tag` and `data` which are strings or None.
    Initially both are set to None:

    >>> print(md.tag)
    None

    After calling `preParse()`, these are separated:

    >>> md.preParse()
    >>> md.tag
    'I'
    >>> md.data
    'linebreak'
    '''
    # given a logical unit, create an object
    # may be a chord, notes, metadata, bars
    def __init__(self, src=''):
        super().__init__(src)
        self.tag: Optional[str] = None
        self.data: Optional[str] = None

    def preParse(self) -> None:
        '''
        Called before contextual adjustments and needs
        to have access to data.  Divides a token into
        .tag (a single capital letter or w) and .data representations.

        >>> x = abcFormat.ABCMetadata('T:tagData')
        >>> x.preParse()
        >>> x.tag
        'T'
        >>> x.data
        'tagData'
        '''
        div = reMetadataTag.match(self.src).end()
        strSrc = self.stripComment(self.src)  # remove any comments
        self.tag = strSrc[:div - 1]  # do not get colon, :
        self.data = strSrc[div:].strip()  # remove leading/trailing

    def parse(self):
        pass

    def isDefaultNoteLength(self) -> bool:
        '''
        Returns True if the tag is "L", False otherwise.
        '''
        if self.tag == 'L':
            return True
        return False

    def isReferenceNumber(self) -> bool:
        '''
        Returns True if the tag is "X", False otherwise.

        >>> x = abcFormat.ABCMetadata('X:5')
        >>> x.preParse()
        >>> x.tag
        'X'
        >>> x.isReferenceNumber()
        True
        '''
        if self.tag == 'X':
            return True
        return False

    def isMeter(self) -> bool:
        '''
        Returns True if the tag is "M" for meter, False otherwise.
        '''
        if self.tag == 'M':
            return True
        return False

    def isTitle(self) -> bool:
        '''
        Returns True if the tag is "T" for title, False otherwise.
        '''
        if self.tag == 'T':
            return True
        return False

    def isComposer(self) -> bool:
        '''
        Returns True if the tag is "C" for composer, False otherwise.
        '''
        if self.tag == 'C':
            return True
        return False

    def isOrigin(self) -> bool:
        '''
        Returns True if the tag is "O" for origin, False otherwise.
        This value is set in the Metadata `localOfComposition` of field.
        '''
        if self.tag == 'O':
            return True
        return False

    def isVoice(self) -> bool:
        '''
        Returns True if the tag is "V", False otherwise.
        '''
        if self.tag == 'V':
            return True
        return False

    def isKey(self) -> bool:
        '''
        Returns True if the tag is "K", False otherwise.
        Note that in some cases a Key will encode clef information.

        (example from corpus: josquin/laDeplorationDeLaMorteDeJohannesOckeghem.abc)
        '''
        if self.tag == 'K':
            return True
        return False

    def isTempo(self) -> bool:
        '''
        Returns True if the tag is "Q" for tempo, False otherwise.
        '''
        if self.tag == 'Q':
            return True
        return False

    def getTimeSignatureParameters(self):
        '''
        If there is a time signature representation available,
        get a numerator, denominator and an abbreviation symbol.
        To get a music21 :class:`~music21.meter.TimeSignature` object, use
        the :meth:`~music21.abcFormat.ABCMetadata.getTimeSignatureObject` method.

        >>> am = abcFormat.ABCMetadata('M:2/2')
        >>> am.preParse()
        >>> am.isMeter()
        True
        >>> am.getTimeSignatureParameters()
        (2, 2, 'normal')

        >>> am = abcFormat.ABCMetadata('M:C|')
        >>> am.preParse()
        >>> am.getTimeSignatureParameters()
        (2, 2, 'cut')

        >>> am = abcFormat.ABCMetadata('M: none')
        >>> am.preParse()
        >>> am.getTimeSignatureParameters() is None
        True

        >>> am = abcFormat.ABCMetadata('M: FREI4/4')
        >>> am.preParse()
        >>> am.getTimeSignatureParameters()
        (4, 4, 'normal')
        '''
        if not self.isMeter():
            raise ABCTokenException('no time signature associated with this metadata')

        if self.data.lower() == 'none':
            return None
        elif self.data == 'C':
            n, d = 4, 4
            symbol = 'common'  # m21 compat
        elif self.data == 'C|':
            n, d = 2, 2
            symbol = 'cut'  # m21 compat
        else:
            n, d = self.data.split('/')
            # using get number from string to handle odd cases such as
            # FREI4/4
            n = int(common.getNumFromStr(n.strip())[0])
            d = int(common.getNumFromStr(d.strip())[0])
            symbol = 'normal'  # m21 compat
        return n, d, symbol

    def getTimeSignatureObject(self):
        '''
        Return a music21 :class:`~music21.meter.TimeSignature`
        object for this metadata tag, if isMeter is True, otherwise raise exception.

        >>> am = abcFormat.ABCMetadata('M:2/2')
        >>> am.preParse()
        >>> ts = am.getTimeSignatureObject()
        >>> ts
        <music21.meter.TimeSignature 2/2>

        >>> am = abcFormat.ABCMetadata('Q:40')
        >>> am.getTimeSignatureObject()
        Traceback (most recent call last):
        music21.abcFormat.ABCTokenException: no time signature associated with
            this non-metrical metadata.
        '''
        if not self.isMeter():
            raise ABCTokenException(
                'no time signature associated with this non-metrical metadata.')
        from music21 import meter
        parameters = self.getTimeSignatureParameters()
        if parameters is None:
            return None
        else:
            numerator, denominator, unused_symbol = parameters
            return meter.TimeSignature(f'{numerator}/{denominator}')

    def getKeySignatureParameters(self):
        # noinspection SpellCheckingInspection
        '''
        Extract key signature parameters, include indications for mode,
        and translate sharps count compatible with m21,
        returning the number of sharps and the mode.

        >>> from music21 import abcFormat

        >>> am = abcFormat.ABCMetadata('K:Eb Lydian')
        >>> am.preParse()
        >>> am.getKeySignatureParameters()
        (-2, 'lydian')

        >>> am = abcFormat.ABCMetadata('K:APhry')
        >>> am.preParse()
        >>> am.getKeySignatureParameters()
        (-1, 'phrygian')

        >>> am = abcFormat.ABCMetadata('K:G Mixolydian')
        >>> am.preParse()
        >>> am.getKeySignatureParameters()
        (0, 'mixolydian')

        >>> am = abcFormat.ABCMetadata('K: Edor')
        >>> am.preParse()
        >>> am.getKeySignatureParameters()
        (2, 'dorian')

        >>> am = abcFormat.ABCMetadata('K: F')
        >>> am.preParse()
        >>> am.getKeySignatureParameters()
        (-1, 'major')

        >>> am = abcFormat.ABCMetadata('K:G')
        >>> am.preParse()
        >>> am.getKeySignatureParameters()
        (1, 'major')

        >>> am = abcFormat.ABCMetadata('K:Gm')
        >>> am.preParse()
        >>> am.getKeySignatureParameters()
        (-2, 'minor')

        >>> am = abcFormat.ABCMetadata('K:Hp')
        >>> am.preParse()
        >>> am.getKeySignatureParameters()
        (2, None)

        >>> am = abcFormat.ABCMetadata('K:G ionian')
        >>> am.preParse()
        >>> am.getKeySignatureParameters()
        (1, 'ionian')

        >>> am = abcFormat.ABCMetadata('K:G aeol')
        >>> am.preParse()
        >>> am.getKeySignatureParameters()
        (-2, 'aeolian')

        '''
        # placing this import in method for now; key.py may import this module
        from music21 import key

        if not self.isKey():
            raise ABCTokenException('no key signature associated with this metadata.')

        # abc uses b for flat in key spec only
        keyNameMatch = ['c', 'g', 'd', 'a', 'e', 'b', 'f#', 'g#', 'a#',
                        'f', 'bb', 'eb', 'd#', 'ab', 'e#', 'db', 'c#', 'gb', 'cb',
                        # HP or Hp are used for highland pipes
                        'hp']

        # if no match, provide defaults,
        # this is probably an error or badly formatted
        standardKeyStr = 'C'
        stringRemain = ''
        # first, get standard key indication
        for target in sorted(keyNameMatch, key=len, reverse=True):
            if target == self.data[:len(target)].lower():
                # keep case
                standardKeyStr = self.data[:len(target)]
                stringRemain = self.data[len(target):]
                break

        if len(standardKeyStr) > 1 and standardKeyStr[1] == 'b':
            standardKeyStr = standardKeyStr[0] + '-'

        mode = None
        stringRemain = stringRemain.strip()
        if stringRemain == '':
            # Assume mode is major by default
            mode = 'major'
        else:
            # only first three characters are parsed
            modeCandidate = stringRemain.lower()
            for match, modeStr in (
                ('dor', 'dorian'),
                ('phr', 'phrygian'),
                ('lyd', 'lydian'),
                ('mix', 'mixolydian'),
                ('maj', 'major'),
                ('ion', 'ionian'),
                ('aeo', 'aeolian'),
                ('m', 'minor'),
            ):
                if modeCandidate.startswith(match):
                    mode = modeStr
                    break

        # Special case for highland pipes
        # replace a flat symbol if found; only the second char
        if standardKeyStr == 'HP':
            standardKeyStr = 'C'  # no sharp or flats
            mode = None
        elif standardKeyStr == 'Hp':
            standardKeyStr = 'D'  # use F#, C#, Gn
            mode = None

        # not yet implemented: checking for additional chromatic alternations
        # e.g.: K:D =c would write the key signature as two sharps
        # (key of D) but then mark every  c  as  natural
        return key.pitchToSharps(standardKeyStr, mode), mode

    def getKeySignatureObject(self):
        # noinspection SpellCheckingInspection,PyShadowingNames
        '''
        Return a music21 :class:`~music21.key.KeySignature` or :class:`~music21.key.Key`
        object for this metadata tag.


        >>> am = abcFormat.ABCMetadata('K:G')
        >>> am.preParse()
        >>> ks = am.getKeySignatureObject()
        >>> ks
        <music21.key.Key of G major>

        >>> am = abcFormat.ABCMetadata('K:Gmin')
        >>> am.preParse()
        >>> ks = am.getKeySignatureObject()
        >>> ks
        <music21.key.Key of g minor>
        >>> ks.sharps
        -2

        Note that capitalization does not matter
        (http://abcnotation.com/wiki/abc:standard:v2.1#kkey)
        so this should still be minor.

        >>> am = abcFormat.ABCMetadata('K:GM')
        >>> am.preParse()
        >>> ks = am.getKeySignatureObject()
        >>> ks
        <music21.key.Key of g minor>
        '''
        if not self.isKey():
            raise ABCTokenException('no key signature associated with this metadata')
        from music21 import key
        # return values of getKeySignatureParameters are sharps, mode
        # need to unpack list w/ *
        sharps, mode = self.getKeySignatureParameters()
        ks = key.KeySignature(sharps)
        if mode in (None, ''):
            return ks
        else:
            return ks.asKey(mode)

    def getClefObject(self) -> Tuple[Optional['music21.clef.Clef'], Optional[int]]:
        '''
        Extract any clef parameters stored in the key metadata token.
        Assume that a clef definition suggests a transposition.
        Return both the Clef and the transposition.

        Returns a two-element tuple of clefObj and transposition in semitones

        >>> am = abcFormat.ABCMetadata('K:Eb Lydian bass')
        >>> am.preParse()
        >>> am.getClefObject()
        (<music21.clef.BassClef>, -24)
        '''
        if not self.isKey():
            raise ABCTokenException(
                'no key signature associated with this metadata; needed for getting Clef Object')

        # placing this import in method for now; key.py may import this module
        clefObj = None
        t = None

        from music21 import clef
        if '-8va' in self.data.lower():
            clefObj = clef.Treble8vbClef()
            t = -12
        elif 'bass' in self.data.lower():
            clefObj = clef.BassClef()
            t = -24

        # if not defined, returns None, None
        return clefObj, t

    def getMetronomeMarkObject(self) -> Optional['music21.tempo.MetronomeMark']:
        '''
        Extract any tempo parameters stored in a tempo metadata token.

        >>> am = abcFormat.ABCMetadata('Q: "Allegro" 1/4=120')
        >>> am.preParse()
        >>> am.getMetronomeMarkObject()
        <music21.tempo.MetronomeMark Allegro Quarter=120.0>

        >>> am = abcFormat.ABCMetadata('Q: 3/8=50 "Slowly"')
        >>> am.preParse()
        >>> am.getMetronomeMarkObject()
        <music21.tempo.MetronomeMark Slowly Dotted Quarter=50.0>

        >>> am = abcFormat.ABCMetadata('Q:1/2=120')
        >>> am.preParse()
        >>> am.getMetronomeMarkObject()
        <music21.tempo.MetronomeMark animato Half=120.0>

        >>> am = abcFormat.ABCMetadata('Q:1/4 3/8 1/4 3/8=40')
        >>> am.preParse()
        >>> am.getMetronomeMarkObject()
        <music21.tempo.MetronomeMark grave Whole tied to Quarter (5 total QL)=40.0>

        >>> am = abcFormat.ABCMetadata('Q:90')
        >>> am.preParse()
        >>> am.getMetronomeMarkObject()
        <music21.tempo.MetronomeMark maestoso Quarter=90.0>

        '''
        if not self.isTempo():
            raise ABCTokenException('no tempo associated with this metadata')
        mmObj = None
        from music21 import tempo
        # see if there is a text expression in quotes
        tempoStr = None
        if '"' in self.data:
            tempoStr = []
            nonText = []
            isOpen = False
            for char in self.data:
                if char == '"' and not isOpen:
                    isOpen = True
                    continue
                if char == '"' and isOpen:
                    isOpen = False
                    continue
                if isOpen:
                    tempoStr.append(char)
                else:  # gather all else
                    nonText.append(char)
            tempoStr = ''.join(tempoStr).strip()
            nonText = ''.join(nonText).strip()
        else:
            nonText = self.data.strip()

        # get a symbolic and numerical value if available
        number = None
        referent = None
        if nonText:
            if '=' in nonText:
                durs, number = nonText.split('=')
                number = float(number)
                # there may be more than one dur divided by a space
                referent = 0.0  # in quarter lengths
                for dur in durs.split(' '):
                    if dur.count('/') > 0:
                        n, d = dur.split('/')
                    else:  # this is an error case
                        environLocal.printDebug(['incorrectly encoded / unparsable duration:', dur])
                        n, d = '1', '1'
                    # n and d might be strings...
                    referent += (float(n) / float(d)) * 4
            else:  # assume we just have a quarter definition, e.g., Q:90
                number = float(nonText)

        # print(nonText, tempoStr)
        if tempoStr is not None or number is not None:
            mmObj = tempo.MetronomeMark(text=tempoStr, number=number,
                                        referent=referent)
        # returns None if not defined
        return mmObj

    def getDefaultQuarterLength(self) -> float:
        r'''
        If there is a quarter length representation available, return it as a floating point value

        >>> am = abcFormat.ABCMetadata('L:1/2')
        >>> am.preParse()
        >>> am.getDefaultQuarterLength()
        2.0

        >>> am = abcFormat.ABCMetadata('L:1/8')
        >>> am.preParse()
        >>> am.getDefaultQuarterLength()
        0.5

        >>> am = abcFormat.ABCMetadata('M:C|')
        >>> am.preParse()
        >>> am.getDefaultQuarterLength()
        0.5


        If taking from meter, find the "fraction" and if < 0.75 use sixteenth notes.
        If >= 0.75 use eighth notes.

        >>> am = abcFormat.ABCMetadata('M:2/4')
        >>> am.preParse()
        >>> am.getDefaultQuarterLength()
        0.25

        >>> am = abcFormat.ABCMetadata('M:3/4')
        >>> am.preParse()
        >>> am.getDefaultQuarterLength()
        0.5


        >>> am = abcFormat.ABCMetadata('M:6/8')
        >>> am.preParse()
        >>> am.getDefaultQuarterLength()
        0.5


        Meter is only used for default length if there is no L:

        >>> x = 'L:1/4\nM:3/4\n\nf'
        >>> sc = converter.parse(x, format='abc')
        >>> sc.flat.notes[0].duration.type
        'quarter'
        '''
        # environLocal.printDebug(['getDefaultQuarterLength', self.data])
        if self.isDefaultNoteLength() and '/' in self.data:
            # should be in L:1/4 form
            n, d = self.data.split('/')
            n = int(n.strip())
            # the notation L: 1/G is found in some essen files
            # this is extremely uncommon and might be an error
            if d == 'G':
                d = 4  # assume a default
            else:
                d = int(d.strip())
            # 1/4 is 1, 1/8 is 0.5
            return n * 4 / d

        elif self.isMeter():
            # if meter auto-set a default not length
            parameters = self.getTimeSignatureParameters()
            if parameters is None:
                return 0.5  # TODO: assume default, need to configure
            n, d, unused_symbol = parameters
            if n / d < 0.75:
                return 0.25  # less than 0.75 the default is a sixteenth note
            else:
                return 0.5  # otherwise it is an eighth note
        else:  # pragma: no cover
            raise ABCTokenException(
                f'no quarter length associated with this metadata: {self.data}')


class ABCBar(ABCToken):
    # given a logical unit, create an object
    # may be a chord, notes, metadata, bars
    def __init__(self, src):
        super().__init__(src)
        self.barType = None  # repeat or barline
        self.barStyle = None  # regular, heavy-light, etc
        self.repeatForm = None  # end, start, bidrectional, first, second

    def parse(self):
        '''
        Assign the bar-type based on the source string.

        >>> ab = abcFormat.ABCBar('|')
        >>> ab.parse()
        >>> ab
        <music21.abcFormat.ABCBar '|'>

        >>> ab.barType
        'barline'
        >>> ab.barStyle
        'regular'

        >>> ab = abcFormat.ABCBar('||')
        >>> ab.parse()
        >>> ab.barType
        'barline'
        >>> ab.barStyle
        'light-light'

        >>> ab = abcFormat.ABCBar('|:')
        >>> ab.parse()
        >>> ab.barType
        'repeat'
        >>> ab.barStyle
        'heavy-light'
        >>> ab.repeatForm
        'start'
        '''
        for abcStr, barTypeString in ABC_BARS:
            if abcStr == self.src.strip():
                # this gets lists of elements like
                # light-heavy-repeat-end
                barTypeComponents = barTypeString.split('-')
                # this is a list of attributes
                if 'repeat' in barTypeComponents:
                    self.barType = 'repeat'
                elif ('first' in barTypeComponents
                      or 'second' in barTypeComponents):
                    self.barType = 'barline'
                    # environLocal.printDebug(['got repeat 1/2:', self.src])
                else:
                    self.barType = 'barline'

                # case of regular, dotted
                if len(barTypeComponents) == 1:
                    self.barStyle = barTypeComponents[0]

                # case of light-heavy, light-light, etc
                elif len(barTypeComponents) >= 2:
                    # must get out cases of the start-tags for repeat boundaries
                    # not yet handling
                    if 'first' in barTypeComponents:
                        self.barStyle = 'regular'
                        self.repeatForm = 'first'  # not a repeat
                    elif 'second' in barTypeComponents:
                        self.barStyle = 'regular'
                        self.repeatForm = 'second'  # not a repeat
                    else:
                        self.barStyle = barTypeComponents[0] + '-' + barTypeComponents[1]
                # repeat form is either start/end for normal repeats
                # get extra repeat information; start, end, first, second
                if len(barTypeComponents) > 2:
                    self.repeatForm = barTypeComponents[3]

    def isRepeat(self):
        if self.barType == 'repeat':
            return True
        else:
            return False

    def isRegular(self) -> bool:
        '''
        Return True if this is a regular, single, light bar line.

        >>> ab = abcFormat.ABCBar('|')
        >>> ab.parse()
        >>> ab.isRegular()
        True
        '''
        if self.barType != 'repeat' and self.barStyle == 'regular':
            return True
        else:
            return False

    def isRepeatBracket(self) -> Union[int, bool]:
        '''
        Return a number if this defines a repeat bracket for an alternate ending
        otherwise returns False.

        >>> ab = abcFormat.ABCBar('[2')
        >>> ab.parse()
        >>> ab.isRepeat()
        False
        >>> ab.isRepeatBracket()
        2
        '''
        if self.repeatForm == 'first':
            return 1  # we need a number
        elif self.repeatForm == 'second':
            return 2
        else:
            return False

    def getBarObject(self) -> Optional['music21.bar.Barline']:
        '''
        Return a music21 bar object

        >>> ab = abcFormat.ABCBar('|:')
        >>> ab.parse()
        >>> barObject = ab.getBarObject()
        >>> barObject
         <music21.bar.Repeat direction=start>
        '''
        from music21 import bar
        if self.isRepeat():
            if self.repeatForm in ('end', 'start'):
                m21bar = bar.Repeat(direction=self.repeatForm)
            # bidirectional repeat tokens should already have been replaced
            # by end and start
            else:  # pragma: no cover
                environLocal.printDebug(
                    [f'found an unsupported repeatForm in ABC: {self.repeatForm}']
                )
                m21bar = None
        elif self.barStyle == 'regular':
            m21bar = None  # do not need an object for regular
        elif self.repeatForm in ('first', 'second'):
            # do nothing, as this is handled in translation
            m21bar = None
        else:
            m21bar = bar.Barline(self.barStyle)
        return m21bar


class ABCTuplet(ABCToken):
    '''
    ABCTuplet tokens always precede the notes they describe.

    In ABCHandler.tokenProcess(), rhythms are adjusted.
    '''
    def __init__(self, src):
        super().__init__(src)

        # self.qlRemain = None  # how many ql are left of this tuplets activity
        # how many notes are affected by this; this assumes equal duration
        self.noteCount = None

        # actual is tuplet represented value; 3 in 3:2
        self.numberNotesActual = None
        # self.durationActual = None

        # normal is underlying duration representation; 2 in 3:2
        self.numberNotesNormal = None
        # self.durationNormal = None

        # store an m21 tuplet object
        self.tupletObj = None

    def updateRatio(self, keySignatureObj=None):
        # noinspection PyShadowingNames
        '''
        Cannot be called until local meter context
        is established.

        >>> at = abcFormat.ABCTuplet('(3')
        >>> at.updateRatio()
        >>> at.numberNotesActual, at.numberNotesNormal
        (3, 2)

        Generally a 5:n tuplet is 5 in the place of 2.

        >>> at = abcFormat.ABCTuplet('(5')
        >>> at.updateRatio()
        >>> at.numberNotesActual, at.numberNotesNormal
        (5, 2)

        Unless it's in a meter.TimeSignature compound (triple) context:

        >>> at = abcFormat.ABCTuplet('(5')
        >>> at.updateRatio(meter.TimeSignature('6/8'))
        >>> at.numberNotesActual, at.numberNotesNormal
        (5, 3)

        Six is 6:2, not 6:4!

        >>> at = abcFormat.ABCTuplet('(6')
        >>> at.updateRatio()
        >>> at.numberNotesActual, at.numberNotesNormal
        (6, 2)

        >>> at = abcFormat.ABCTuplet('(6:4')
        >>> at.updateRatio()
        >>> at.numberNotesActual, at.numberNotesNormal
        (6, 4)

        >>> at = abcFormat.ABCTuplet('(6::6')
        >>> at.updateRatio()
        >>> at.numberNotesActual, at.numberNotesNormal
        (6, 2)

        2 is 2 in 3...

        >>> at = abcFormat.ABCTuplet('(2')
        >>> at.updateRatio()
        >>> at.numberNotesActual, at.numberNotesNormal
        (2, 3)


        Some other types:

        >>> for n in 1, 2, 3, 4, 5, 6, 7, 8, 9:
        ...     at = abcFormat.ABCTuplet(f'({n}')
        ...     at.updateRatio()
        ...     print(at.numberNotesActual, at.numberNotesNormal)
        1 1
        2 3
        3 2
        4 3
        5 2
        6 2
        7 2
        8 3
        9 2

        Tuplets > 9 raise an exception:

        >>> at = abcFormat.ABCTuplet('(10')
        >>> at.updateRatio()
        Traceback (most recent call last):
        music21.abcFormat.ABCTokenException: cannot handle tuplet of form: '(10'
        '''
        if keySignatureObj is None:
            normalSwitch = 2  # 4/4
        elif keySignatureObj.beatDivisionCount == 3:  # if compound
            normalSwitch = 3
        else:
            normalSwitch = 2

        splitTuplet = self.src.strip().split(':')

        tupletNumber = splitTuplet[0]
        normalNotes = None

        if len(splitTuplet) >= 2 and splitTuplet[1] != '':
            normalNotes = int(splitTuplet[1])

        if tupletNumber == '(1':  # not sure if valid, but found
            a, n = 1, 1
        elif tupletNumber == '(2':
            a, n = 2, 3  # actual, normal
        elif tupletNumber == '(3':
            a, n = 3, 2  # actual, normal
        elif tupletNumber == '(4':
            a, n = 4, 3  # actual, normal
        elif tupletNumber == '(5':
            a, n = 5, normalSwitch  # actual, normal
        elif tupletNumber == '(6':
            a, n = 6, 2  # actual, normal
        elif tupletNumber == '(7':
            a, n = 7, normalSwitch  # actual, normal
        elif tupletNumber == '(8':
            a, n = 8, 3  # actual, normal
        elif tupletNumber == '(9':
            a, n = 9, normalSwitch  # actual, normal
        else:
            raise ABCTokenException(f'cannot handle tuplet of form: {tupletNumber!r}')

        if normalNotes is None:
            normalNotes = n

        self.numberNotesActual = a
        self.numberNotesNormal = normalNotes

    def updateNoteCount(self):
        '''
        Update the note count of notes that are
        affected by this tuplet. Can be set by p:q:r style tuplets.
        Also creates a tuplet object.

        >>> at = abcFormat.ABCTuplet('(6')
        >>> at.updateRatio()
        >>> at.updateNoteCount()
        >>> at.noteCount
        6
        >>> at.tupletObj
        <music21.duration.Tuplet 6/2>

        >>> at = abcFormat.ABCTuplet('(6:4:12')
        >>> at.updateRatio()
        >>> at.updateNoteCount()
        >>> at.noteCount
        12
        >>> at.tupletObj
        <music21.duration.Tuplet 6/4>

        >>> at = abcFormat.ABCTuplet('(6::18')
        >>> at.updateRatio()
        >>> at.updateNoteCount()
        >>> at.noteCount
        18
        '''
        if self.numberNotesActual is None:
            raise ABCTokenException('must set numberNotesActual with updateRatio()')

        # nee dto
        from music21 import duration
        self.tupletObj = duration.Tuplet(
            numberNotesActual=self.numberNotesActual,
            numberNotesNormal=self.numberNotesNormal)

        # copy value; this will be dynamically counted down
        splitTuplet = self.src.strip().split(':')
        if len(splitTuplet) >= 3 and splitTuplet[2] != '':
            self.noteCount = int(splitTuplet[2])
        else:
            self.noteCount = self.numberNotesActual

        # self.qlRemain = self._tupletObj.totalTupletLength()


class ABCTie(ABCToken):
    '''
    Handles instances of ties '-' between notes in an ABC score.
    Ties are treated as an attribute of the note before the '-';
    the note after is marked as the end of the tie.
    '''
    def __init__(self, src):
        super().__init__(src)
        self.noteObj = None


class ABCSlurStart(ABCToken):
    '''
    ABCSlurStart tokens always precede the notes in a slur.
    For nested slurs, each open parenthesis gets its own token.
    '''
    def __init__(self, src):
        super().__init__(src)
        self.slurObj = None

    def fillSlur(self):
        '''
        Creates a spanner object for each open paren associated with a slur;
        these slurs are filled with notes until end parens are read.
        '''
        from music21 import spanner
        self.slurObj = spanner.Slur()


class ABCParenStop(ABCToken):
    '''
    A general parenthesis stop;
    comes at the end of a tuplet, slur, or dynamic marking.
    '''


class ABCCrescStart(ABCToken):
    '''
    ABCCrescStart tokens always precede the notes in a crescendo.
    These tokens coincide with the string "!crescendo(";
    the closing string "!crescendo)" counts as an ABCParenStop.
    '''

    def __init__(self, src):
        super().__init__(src)
        self.crescObj = None

    def fillCresc(self):
        from music21 import dynamics
        self.crescObj = dynamics.Crescendo()


class ABCDimStart(ABCToken):
    '''
    ABCDimStart tokens always precede the notes in a diminuendo.
    They function identically to ABCCrescStart tokens.
    '''
    def __init__(self, src):    # previous typo?: used to be __init
        super().__init__(src)
        self.dimObj = None

    def fillDim(self):
        from music21 import dynamics
        self.dimObj = dynamics.Diminuendo()


class ABCStaccato(ABCToken):
    '''
    ABCStaccato tokens "." precede a note or chord;
    they are a property of that note/chord.
    '''


class ABCUpbow(ABCToken):
    '''
    ABCStaccato tokens "." precede a note or chord;
    they are a property of that note/chord.
    '''


class ABCDownbow(ABCToken):
    '''
    ABCStaccato tokens "." precede a note or chord;
    they are a property of that note/chord.
    '''


class ABCAccent(ABCToken):
    '''
    ABCAccent tokens "K" precede a note or chord;
    they are a property of that note/chord.
    These appear as ">" in the output.
    '''


class ABCStraccent(ABCToken):
    '''
    ABCStraccent tokens "k" precede a note or chord;
    they are a property of that note/chord.
    These appear as "^" in the output.
    '''


class ABCTenuto(ABCToken):
    '''
    ABCTenuto tokens "M" precede a note or chord;
    they are a property of that note/chord.
    '''


class ABCGraceStart(ABCToken):
    '''
    Grace note start
    '''


class ABCGraceStop(ABCToken):
    '''
    Grace note end
    '''


class ABCBrokenRhythmMarker(ABCToken):
    '''
    Marks that rhythm is broken with '>>>'
    '''

    def __init__(self, src):
        super().__init__(src)
        self.data = None

    def preParse(self):
        '''Called before context adjustments: need to have access to data

        >>> brokenRhythm = abcFormat.ABCBrokenRhythmMarker('>>>')
        >>> brokenRhythm.preParse()
        >>> brokenRhythm.data
        '>>>'
        '''
        self.data = self.src.strip()


class ABCNote(ABCToken):
    '''
    A model of an ABCNote.

    General usage requires multi-pass processing. After being tokenized,
    each ABCNote needs a number of attributes updates. Attributes to
    be updated after tokenizing, and based on the linear sequence of
    tokens: `inBar`, `inBeam` (not used), `inGrace`,
    `activeDefaultQuarterLength`, `brokenRhythmMarker`, and
    `activeKeySignature`.

    The `chordSymbols` list stores one or more chord symbols (ABC calls
    these guitar chords) associated with this note. This attribute is
    updated when parse() is called.
    '''
    def __init__(self, src='', carriedAccidental=None):
        super().__init__(src)

        # store the ABC accidental string propagated in the measure that
        # must be applied to this note. Note must not be set if the
        # note already has an explicit accidental attached. (The explicit
        # accidental is now the one that will be carried forward.)
        self.carriedAccidental = carriedAccidental

        # store chord string if connected to this note
        self.chordSymbols = []

        # context attributes
        self.inBar = None
        self.inBeam = None
        self.inGrace = None

        # provide default duration from handler; may change during piece
        self.activeDefaultQuarterLength = None
        # store if a broken symbol applies; pair of symbol, position (left, right)
        self.brokenRhythmMarker = None

        # store key signature for pitch processing; this is an m21 object
        self.activeKeySignature = None

        # store a tuplet if active
        self.activeTuplet = None

        # store a spanner if active
        self.applicableSpanners = []

        # store a tie if active
        self.tie = None

        # store articulations if active
        self.articulations = []

        # set to True if a modification of key signature
        # set to False if an altered tone part of a Key
        self.accidentalDisplayStatus = None
        # determined during parse() based on if pitch chars are present
        self.isRest = None
        # pitch/ duration attributes for m21 conversion
        # set with parse() based on all other contextual
        self.pitchName = None  # if None, a rest or chord
        self.quarterLength = None

    @staticmethod
    def _splitChordSymbols(strSrc):
        '''
        Splits chord symbols from other string characteristics.
        Return list of chord symbols and clean, remain chars

        Staticmethod:

        >>> an = abcFormat.ABCNote()
        >>> an._splitChordSymbols('"C"e2')
        (['"C"'], 'e2')
        >>> an._splitChordSymbols('b2')
        ([], 'b2')

        >>> abcFormat.ABCNote._splitChordSymbols('"D7""D"d2')
        (['"D7"', '"D"'], 'd2')
        '''
        if '"' in strSrc:
            chordSymbols = reChordSymbol.findall(strSrc)
            # might remove quotes from chord symbols here

            # index of end of last match
            i = list(reChordSymbol.finditer(strSrc))[-1].end()
            return chordSymbols, strSrc[i:]
        else:
            return [], strSrc

    def getPitchName(
        self,
        strSrc: str,
        forceKeySignature=None
    ) -> Tuple[Optional[str], Union[bool, None]]:
        '''
        Given a note or rest string without a chord symbol,
        return a music21 pitch string or None (if a rest),
        and the accidental display status. This value is paired
        with an accidental display status. Pitch alterations, and
        accidental display status, are adjusted if a key is
        declared in the Note.

        >>> an = abcFormat.ABCNote()
        >>> an.getPitchName('e2')
        ('E5', None)
        >>> an.getPitchName('C')
        ('C4', None)
        >>> an.getPitchName('B,,')
        ('B2', None)
        >>> an.getPitchName('C,')
        ('C3', None)
        >>> an.getPitchName('c')
        ('C5', None)
        >>> an.getPitchName("c'")
        ('C6', None)
        >>> an.getPitchName("c''")
        ('C7', None)
        >>> an.getPitchName("^g")
        ('G#5', True)
        >>> an.getPitchName("_g''")
        ('G-7', True)
        >>> an.getPitchName('=c')
        ('Cn5', True)

        If pitch is a rest (z) then the Pitch name is None:

        >>> an.getPitchName('z4')
        (None, None)

        Grace note:

        >>> an.getPitchName('{c}')
        ('C5', None)


        Given an active KeySignature object, the pitch name might
        change:

        >>> an.activeKeySignature = key.KeySignature(3)
        >>> an.getPitchName('c')
        ('C#5', False)


        Illegal pitch names raise an ABCHandlerException

        >>> an.getPitchName('x')
        Traceback (most recent call last):
        music21.abcFormat.ABCHandlerException: cannot find any pitch information in: 'x'
        '''
        environLocal.printDebug(['getPitchName:', strSrc])

        # skip some articulations parsed with the pitch
        # some characters are errors in parsing or encoding not yet handled
        if len(strSrc) > 1 and strSrc[0] in 'uT':
            strSrc = strSrc[1:]
        strSrc = strSrc.replace('T', '')

        try:
            name = rePitchName.findall(strSrc)[0]
        except IndexError:  # no matches  # pragma: no cover
            raise ABCHandlerException(f'cannot find any pitch information in: {strSrc!r}')

        if name == 'z':
            return (None, None)  # designates a rest

        if forceKeySignature is not None:
            activeKeySignature = forceKeySignature
        else:  # may be None
            activeKeySignature = self.activeKeySignature

        try:  # returns pStr, accidentalDisplayStatus
            return _pitchTranslationCache[(strSrc,
                                           self.carriedAccidental,
                                           str(activeKeySignature))]
        except KeyError:
            pass

        if name.islower():
            octave = 5
        else:
            octave = 4
        # look in source string for register modification
        octave -= strSrc.count(',')
        octave += strSrc.count("'")

        # get an accidental string

        accString = ''
        for dummy in range(strSrc.count('_')):
            accString += '-'  # m21 symbols
        for dummy in range(strSrc.count('^')):
            accString += '#'  # m21 symbols
        for dummy in range(strSrc.count('=')):
            accString += 'n'  # m21 symbols

        carriedAccString = ''
        if self.carriedAccidental:
            # No overriding accidental attached to this note
            # force carrying through the measure.
            for dummy in range(self.carriedAccidental.count('_')):
                carriedAccString += '-'  # m21 symbols
            for dummy in range(self.carriedAccidental.count('^')):
                carriedAccString += '#'  # m21 symbols
            for dummy in range(self.carriedAccidental.count('=')):
                carriedAccString += 'n'  # m21 symbols

        if carriedAccString and accString:
            raise ABCHandlerException('Carried accidentals not rendered moot.')
        # if there is an explicit accidental, regardless of key, it should
        # be shown: this will works for naturals well
        if carriedAccString:
            # An accidental carrying through the measure is supposed to be applied.
            # This will be set iff no explicit accidental is attached to the note.
            accidentalDisplayStatus = None
        elif accString != '':
            accidentalDisplayStatus = True
        # if we do not have a key signature, and have accidentals, set to None
        elif activeKeySignature is None:
            accidentalDisplayStatus = None
        # pitches are key dependent: accidentals are not given
        # if we have a key and find a name, that does not have a n, must be
        # altered
        else:
            alteredPitches = activeKeySignature.alteredPitches
            # just the steps, no accidentals
            alteredPitchSteps = [p.step.lower() for p in alteredPitches]
            # includes #, -
            alteredPitchNames = [p.name.lower() for p in alteredPitches]
            # environLocal.printDebug(['alteredPitches', alteredPitches])

            if name.lower() in alteredPitchSteps:
                # get the corresponding index in the name
                name = alteredPitchNames[alteredPitchSteps.index(name.lower())]
            # set to false, as do not need to show w/ key sig
            accidentalDisplayStatus = False

        # making upper here, but this is not relevant
        if carriedAccString:
            pStr = f'{name.upper()}{carriedAccString}{octave}'
        else:
            pStr = f'{name.upper()}{accString}{octave}'

        # store in global cache for faster speed
        _cacheKey = (
            strSrc,
            self.carriedAccidental,
            str(activeKeySignature)
        )

        _pitchTranslationCache[_cacheKey] = (pStr, accidentalDisplayStatus)
        return (pStr, accidentalDisplayStatus)

    def getQuarterLength(self, strSrc, forceDefaultQuarterLength=None) -> float:
        '''
        Called with parse(), after context processing, to calculate duration

        >>> an = abcFormat.ABCNote()
        >>> an.activeDefaultQuarterLength = 0.5
        >>> an.getQuarterLength('e2')
        1.0
        >>> an.getQuarterLength('G')
        0.5
        >>> an.getQuarterLength('=c/2')
        0.25
        >>> an.getQuarterLength('A3/2')
        0.75
        >>> an.getQuarterLength('A/')
        0.25

        >>> an.getQuarterLength('A//')
        0.125
        >>> an.getQuarterLength('A///')
        0.0625

        >>> an = abcFormat.ABCNote()
        >>> an.activeDefaultQuarterLength = 0.5
        >>> an.brokenRhythmMarker = ('>', 'left')
        >>> an.getQuarterLength('A')
        0.75
        >>> an.brokenRhythmMarker = ('>', 'right')
        >>> an.getQuarterLength('A')
        0.25

        >>> an.brokenRhythmMarker = ('<<', 'left')
        >>> an.getQuarterLength('A')
        0.125
        >>> an.brokenRhythmMarker = ('<<', 'right')
        >>> an.getQuarterLength('A')
        0.875

        >>> an.brokenRhythmMarker = ('<<<', 'left')
        >>> an.getQuarterLength('A')
        0.0625
        >>> an.brokenRhythmMarker = ('<<<', 'right')
        >>> an.getQuarterLength('A')
        0.9375

        >>> an.getQuarterLength('A', forceDefaultQuarterLength=1)
        1.875
        '''
        if forceDefaultQuarterLength is not None:
            activeDefaultQuarterLength = forceDefaultQuarterLength
        else:  # may be None
            activeDefaultQuarterLength = self.activeDefaultQuarterLength

        if activeDefaultQuarterLength is None:
            raise ABCTokenException(
                'cannot calculate quarter length without a default quarter length')

        numStr = []
        for c in strSrc:
            if c.isdigit() or c == '/':
                numStr.append(c)
        numStr = ''.join(numStr)
        numStr = numStr.strip()

        # environLocal.printDebug(['numStr', numStr])

        # get default
        if numStr == '':
            ql = activeDefaultQuarterLength
        # if only, shorthand for /2
        elif numStr == '/':
            ql = activeDefaultQuarterLength * 0.5
        elif numStr == '//':
            ql = activeDefaultQuarterLength * 0.25
        elif numStr == '///':
            ql = activeDefaultQuarterLength * 0.125
        # if a half fraction
        elif numStr.startswith('/'):
            ql = activeDefaultQuarterLength / int(numStr.split('/')[1])
        # uncommon usage: 3/ short for 3/2
        elif numStr.endswith('/'):
            n = int(numStr.split('/')[0].strip())
            d = 2
            ql = activeDefaultQuarterLength * n / d
        # if we have two, this is usually an error
        elif numStr.count('/') == 2:  # pragma: no cover
            environLocal.printDebug(['incorrectly encoded / unparsable duration:', numStr])
            ql = 1  # provide a default

        # assume we have a complete fraction
        elif '/' in numStr:
            n, d = numStr.split('/')
            n = int(n.strip())
            d = int(d.strip())
            ql = activeDefaultQuarterLength * n / d
        # not a fraction; a multiplier
        else:
            ql = activeDefaultQuarterLength * int(numStr)

        if self.brokenRhythmMarker is not None:
            symbol, direction = self.brokenRhythmMarker
            if symbol == '>':
                modPair = (1.5, 0.5)
            elif symbol == '<':
                modPair = (0.5, 1.5)
            elif symbol == '>>':
                modPair = (1.75, 0.25)
            elif symbol == '<<':
                modPair = (0.25, 1.75)
            elif symbol == '>>>':
                modPair = (1.875, 0.125)
            elif symbol == '<<<':
                modPair = (0.125, 1.875)
            else:  # pragma: no cover
                modPair = (1, 1)

            # apply based on direction
            if direction == 'left':
                ql *= modPair[0]
            elif direction == 'right':
                ql *= modPair[1]

        return ql

    def parse(
        self,
        forceDefaultQuarterLength=None,
        forceKeySignature=None
    ) -> None:
        # environLocal.printDebug(['parse', self.src])
        self.chordSymbols, nonChordSymStr = self._splitChordSymbols(self.src)
        # get pitch name form remaining string
        # rests will have a pitch name of None

        try:
            pn, accDisp = self.getPitchName(nonChordSymStr,
                                            forceKeySignature=forceKeySignature)
        except ABCHandlerException:
            environLocal.warn(['Could not get pitch information from note: ',
                               f'{nonChordSymStr}, assuming C'])
            pn = 'C'
            accDisp = False

        self.pitchName, self.accidentalDisplayStatus = pn, accDisp

        if self.pitchName is None:
            self.isRest = True
        else:
            self.isRest = False

        self.quarterLength = self.getQuarterLength(
            nonChordSymStr,
            forceDefaultQuarterLength=forceDefaultQuarterLength)

        # environLocal.printDebug(['ABCNote:', 'pitch name:', self.pitchName,
        #                            'ql:', self.quarterLength])


class ABCChord(ABCNote):
    '''
    A representation of an ABC Chord, which contains within its delimiters individual notes.

    A subclass of ABCNote.
    '''

    def __init__(self, src: str = ''):
        super().__init__(src)
        # store a list of component objects
        self.subTokens = []

    def parse(self, forceKeySignature=None, forceDefaultQuarterLength=None):
        '''
        Handles the following types of chords:

        * Chord without length modifier: [ceg]

        * Chords with outer length modifier: [ceg]2, [ceg]/2

        * Chords with inner length modifier: [c2e2g2], [c2eg]

        * Chords with inner and outer length modifier: [c2e2g2]/2, [c/2e/2g/2]2
        '''

        self.chordSymbols, nonChordSymStr = self._splitChordSymbols(self.src)

        # position of the closing bracket
        pos = nonChordSymStr.index(']')
        # Length modifier string behind the chord brackets
        outerLengthModifierStr = nonChordSymStr[pos + 1:]
        # String in the chord brackets
        tokenStr = nonChordSymStr[1:pos]

        # environLocal.printDebug(['ABCChord:', nonChordSymStr, 'tokenStr', tokenStr, '
        # outerLengthModifierStr', outerLengthModifierStr])

        # Get the outer chord length modifier if present
        outer_lengthModifier = self.getQuarterLength(outerLengthModifierStr,
                                                     forceDefaultQuarterLength=1.0)

        if forceKeySignature is not None:
            activeKeySignature = forceKeySignature
        else:  # may be None
            activeKeySignature = self.activeKeySignature

        # create a handler for processing internal chord notes
        ah = ABCHandler()
        # only tokenizing; not calling process() as these objects
        # have no metadata
        # may need to supply key?
        ah.tokenize(tokenStr)

        inner_quarterLength = 0
        # tokens contained here are each ABCNote instances
        for t in ah.tokens:
            # environLocal.printDebug(['ABCChord: subTokens', t])
            # parse any tokens individually, supply local data as necessary
            if isinstance(t, ABCNote):
                t.parse(
                    forceDefaultQuarterLength=self.activeDefaultQuarterLength,
                    forceKeySignature=activeKeySignature)

                if t.isRest:
                    continue

                # get the quarter length from the sub-tokens
                # All the notes within a chord should normally have the same length,
                # but if not, the chord duration is that of the first note.
                if not inner_quarterLength:
                    inner_quarterLength = t.quarterLength

                self.subTokens.append(t)


        # When both inside and outside the chord length modifiers are used,
        # they should be multiplied. Example: [C2E2G2]3 has the same meaning as [CEG]6.
        self.quarterLength = outer_lengthModifier * inner_quarterLength


# ------------------------------------------------------------------------------
class ABCHandler:
    '''
    An ABCHandler is able to divide elements of a character stream into objects and handle
    store in a list, and passes global information to components

    Optionally, specify the (major, minor, patch) version of ABC to process--
    e.g., (1.2.0). If not set, default ABC 1.3 parsing is performed.

    If lineBreaksDefinePhrases is True then new lines within music elements
    define new phrases.  This is useful for parsing extra information from
    the Essen Folksong repertory

    New in v6.3 -- lineBreaksDefinePhrases -- does not yet do anything
    '''
    def __init__(self, abcVersion=None, lineBreaksDefinePhrases=False):
        # tokens are ABC objects import n a linear stream
        self.abcVersion = abcVersion
        self.abcDirectives = {}
        self.tokens = []
        self.activeParens = []
        self.activeSpanners = []
        self.lineBreaksDefinePhrases = lineBreaksDefinePhrases
        self.pos = -1
        self.skipAhead = 0
        self.isFirstComment = True
        self.strSrc = ''
        self.srcLen = len(self.strSrc)  # just documenting this.
        self.currentCollectStr = ''

    @staticmethod
    def _getLinearContext(source, i: int) -> Tuple[Any, Any, Any, Any]:
        '''
        Find the local context of a string or iterable of objects
        beginning at a particular index.

        Returns a tuple of charPrev, charThis, charNext, charNextNext.

        Staticmethod

        >>> ah = abcFormat.ABCHandler()
        >>> ah._getLinearContext('12345', 0)
        (None, '1', '2', '3')
        >>> ah._getLinearContext('12345', 1)
        ('1', '2', '3', '4')
        >>> abcFormat.ABCHandler._getLinearContext('12345', 3)
        ('3', '4', '5', None)
        >>> abcFormat.ABCHandler._getLinearContext('12345', 4)
        ('4', '5', None, None)

        >>> abcFormat.ABCHandler._getLinearContext([32, None, 8, 11, 53], 4)
        (11, 53, None, None)
        >>> ah._getLinearContext([32, None, 8, 11, 53], 2)
        (None, 8, 11, 53)
        >>> ah._getLinearContext([32, None, 8, 11, 53], 0)
        (None, 32, None, 8)
        '''
        # Note: this is performance critical method
        lastIndex = len(source) - 1
        if i > lastIndex:
            raise ABCHandlerException(f'bad index value {i}, max is {lastIndex}')

        # find local area of iterable
        cPrev = None
        if i > 0:
            cPrev = source[i - 1]

        # set current characters or items
        c = source[i]

        cNext = None
        if i < len(source) - 1:
            cNext = source[i + 1]

        # get 2 entries forward
        cNextNext = None
        if i < len(source) - 2:
            cNextNext = source[i + 2]

        return cPrev, c, cNext, cNextNext
        # return cPrevNotSpace, cPrev, c, cNext, cNextNotSpace, cNextNext

    @staticmethod
    def _getNextLineBreak(strSrc: str, i: int) -> Optional[int]:
        r'''
        Return index of next line break after character i.

        Staticmethod

        >>> ah = abcFormat.ABCHandler()
        >>> inputString = 'de  we\n wer bfg\n'
        >>> ah._getNextLineBreak(inputString, 0)
        6
        >>> inputString[0:6]
        'de  we'

        from last line break

        >>> abcFormat.ABCHandler._getNextLineBreak(inputString, 6)
        15
        >>> inputString[ah._getNextLineBreak(inputString, 0):]
        '\n wer bfg\n'
        '''
        lastIndex = len(strSrc) - 1
        for j in range(i + 1, lastIndex + 1):
            if strSrc[j] == '\n':
                return j
        return lastIndex + 1

    @staticmethod
    def barlineTokenFilter(token: str) -> List[ABCBar]:
        '''
        Some single barline tokens are better replaced
        with two tokens. This method, given a token,
        returns a list of tokens. If there is no change
        necessary, the provided token will be returned in the list.

        A staticmethod.  Call on the class itself.

        >>> abcFormat.ABCHandler.barlineTokenFilter('::')
        [<music21.abcFormat.ABCBar ':|'>, <music21.abcFormat.ABCBar '|:'>]

        >>> abcFormat.ABCHandler.barlineTokenFilter('|2')
        [<music21.abcFormat.ABCBar '|'>, <music21.abcFormat.ABCBar '[2'>]

        >>> abcFormat.ABCHandler.barlineTokenFilter(':|1')
        [<music21.abcFormat.ABCBar ':|'>, <music21.abcFormat.ABCBar '[1'>]

        If nothing matches, the original token is returned as an ABCBar object:

        >>> abcFormat.ABCHandler.barlineTokenFilter('hi')
        [<music21.abcFormat.ABCBar 'hi'>]
        '''
        barTokens: List[ABCBar] = []
        if token == '::':
            # create a start and and an end
            barTokens.append(ABCBar(':|'))
            barTokens.append(ABCBar('|:'))
        elif token == '|1':
            # create a start and and an end
            barTokens.append(ABCBar('|'))
            barTokens.append(ABCBar('[1'))
        elif token == '|2':
            # create a start and and an end
            barTokens.append(ABCBar('|'))
            barTokens.append(ABCBar('[2'))
        elif token == ':|1':
            # create a start and and an end
            barTokens.append(ABCBar(':|'))
            barTokens.append(ABCBar('[1'))
        elif token == ':|2':
            # create a start and and an end
            barTokens.append(ABCBar(':|'))
            barTokens.append(ABCBar('[2'))
        else:  # append unaltered
            barTokens.append(ABCBar(token))
        return barTokens

    # --------------------------------------------------------------------------
    # token processing

    def _accidentalPropagation(self) -> str:
        '''
        Determine how accidentals should 'carry through the measure.'

        >>> ah = abcFormat.ABCHandler(abcVersion=(1, 3, 0))
        >>> ah._accidentalPropagation()
        'not'
        >>> ah = abcFormat.ABCHandler(abcVersion=(2, 0, 0))
        >>> ah._accidentalPropagation()
        'pitch'
        '''
        minVersion = (2, 0, 0)
        if not self.abcVersion or self.abcVersion < minVersion:
            return 'not'
        if 'propagate-accidentals' in self.abcDirectives:
            return self.abcDirectives['propagate-accidentals']
        return 'pitch'  # Default per abc 2.1 standard

    def parseCommentForVersionInformation(self, commentLine: str):
        '''
        If this is the first comment then searches for a version
        match and set it as .abcVersion

        If not isFirstComment then does nothing:

        >>> ah = abcFormat.ABCHandler()
        >>> ah.abcVersion is None
        True
        >>> ah.isFirstComment
        True

        >>> ah.parseCommentForVersionInformation('%abc-2.3.2')
        >>> ah.abcVersion
        (2, 3, 2)
        >>> ah.isFirstComment
        False

        Now will do nothing since isFirstComment is False

        >>> ah.parseCommentForVersionInformation('%abc-4.9.7')
        >>> ah.abcVersion
        (2, 3, 2)
        '''
        if not self.isFirstComment:
            return
        self.isFirstComment = False
        verMats = reAbcVersion.match(commentLine)
        if verMats:
            abcMajor = int(verMats.group(2))
            abcMinor = int(verMats.group(3))
            if verMats.group(4):
                abcPatch = int(verMats.group(4))
            else:
                abcPatch = 0
            verTuple = (abcMajor, abcMinor, abcPatch)
            self.abcVersion = verTuple

    def processComment(self):
        r'''
        Processes the comment at self.pos in self.strSrc, setting self.skipAhead,
        possibly self.abcVersion, and self.abcDirectives for the directiveKey.

        TODO: store the comment in the stream also.

        >>> from textwrap import dedent
        >>> ah = abcFormat.ABCHandler()
        >>> data = dedent("""
        ...    Hello % this is a comment
        ...    Bye
        ...    """)
        >>> ah.strSrc = data
        >>> ah.pos = 6
        >>> ah.processComment()
        >>> ah.skipAhead
        19
        >>> len(' this is a comment\n')
        19
        '''
        self.skipAhead = self._getNextLineBreak(
            self.strSrc, self.pos
        ) - (self.pos + 1)
        commentLine = self.strSrc[self.pos:self.pos + self.skipAhead + 1]
        self.parseCommentForVersionInformation(commentLine)
        directiveMatches = reDirective.match(commentLine)
        if directiveMatches:
            directiveKey = directiveMatches.group(1)
            directiveValue = directiveMatches.group(2)
            self.abcDirectives[directiveKey] = directiveValue
        # environLocal.printDebug(['got comment:', repr(self.strSrc[i:j + 1])])

    @staticmethod
    def startsMetadata(c: str, cNext: Optional[str], cNextNext: Optional[str]) -> bool:
        '''
        Returns True if this context describes the start of a metadata section, like

        A:something

        Metadata: capital letter, with next char as ':' and some following character

        >>> ah = abcFormat.ABCHandler
        >>> ah.startsMetadata('A', ':', 's')
        True

        lowercase w: is a special case for lyric defs

        >>> ah.startsMetadata('w', ':', 's')
        True

        Following char must be ":"

        >>> ah.startsMetadata('A', ' ', 's')
        False

        Pipe after colon indicates not metadata (bar info).
        For example need to not misinterpret repeat bars as metadata
        e.g. `dAG FED:|2 dAG FGA|`

        this is incorrect, but we can avoid it by
        looking for a leading pipe and returning False

        >>> ah.startsMetadata('A', ':', '|')
        False

        >>> ah.startsMetadata('A', ':', None)
        False
        '''
        if cNext != ':':
            return False
        elif cNextNext is None:
            return False
        elif cNextNext == '|':
            return False
        elif c == 'w':
            return True  # special case, w:...
        elif c.isalpha() and c.isupper():
            return True
        return False


    def tokenize(self, strSrc: str) -> None:
        '''
        Walk the abc string, creating ABC objects along the way.

        This may be called separately from process(), in the case
        that pre/post parse processing is not needed.

        >>> abch = abcFormat.ABCHandler()
        >>> abch.tokens
        []
        >>> abch.tokenize('X: 1')
        >>> abch.tokens
        [<music21.abcFormat.ABCMetadata 'X: 1'>]

        >>> abch = abcFormat.ABCHandler()
        >>> abch.tokenize('(6f')
        >>> abch.tokens
        [<music21.abcFormat.ABCTuplet '(6'>, <music21.abcFormat.ABCNote 'f'>]

        >>> abch = abcFormat.ABCHandler()
        >>> abch.tokenize('(6:4f')
        >>> abch.tokens
        [<music21.abcFormat.ABCTuplet '(6:4'>, <music21.abcFormat.ABCNote 'f'>]

        >>> abch = abcFormat.ABCHandler()
        >>> abch.tokenize('(6:4:2f')
        >>> abch.tokens
        [<music21.abcFormat.ABCTuplet '(6:4:2'>, <music21.abcFormat.ABCNote 'f'>]

        >>> abch = abcFormat.ABCHandler()
        >>> abch.tokenize('(6::2f')
        >>> abch.tokens
        [<music21.abcFormat.ABCTuplet '(6::2'>, <music21.abcFormat.ABCNote 'f'>]
        '''
        self.srcLen = len(strSrc)
        self.strSrc = strSrc
        self.pos = -1
        self.currentCollectStr = ''
        self.skipAhead = 0
        # noinspection SpellCheckingInspection
        accidentalsAndDecorations = '.~^=_HLMOPSTuv'
        accidentals = '^=_'

        activeChordSymbol = ''  # accumulate, then prepend
        accidentalized = {}
        accidental = None
        abcPitch = None  # ABC substring defining any pitch within the current token
        self.isFirstComment = True

        while self.pos < self.srcLen - 1:
            self.pos += 1
            self.pos += self.skipAhead
            self.skipAhead = 0
            if self.pos > self.srcLen - 1:
                break

            q = self._getLinearContext(self.strSrc, self.pos)
            unused_cPrev, c, cNext, cNextNext = q
            # cPrevNotSpace, cPrev, c, cNext, cNextNotSpace, cNextNext = q

            # comment lines, also encoding defs
            if c == '%':
                self.processComment()
                continue

            if self.startsMetadata(c, cNext, cNextNext):
                # collect until end of line; add one to get line break
                j = self._getNextLineBreak(self.strSrc, self.pos)
                self.skipAhead = j - (self.pos + 1)
                self.currentCollectStr = self.strSrc[self.pos:j].strip()
                # environLocal.printDebug(['got metadata:', repr(self.currentCollectStr)])
                self.tokens.append(ABCMetadata(self.currentCollectStr))
                continue

            # get bars: if not a space and not alphanumeric
            if not c.isspace() and not c.isalnum() and c not in ('~', '('):
                matchBars = False
                for barIndex in range(len(ABC_BARS)):
                    # first of bars tuple is symbol to match
                    # three possible sizes of bar indications: 3, 2, 1
                    barTokenArchetype = ABC_BARS[barIndex][0]
                    if len(barTokenArchetype) == 3:
                        if cNextNext is not None and (c + cNext + cNextNext == barTokenArchetype):
                            self.skipAhead = 2
                            matchBars = True
                            break
                    elif cNext is not None and (len(barTokenArchetype) == 2):
                        if c + cNext == barTokenArchetype:
                            self.skipAhead = 1
                            matchBars = True
                            break
                    elif len(barTokenArchetype) == 1:
                        if c == barTokenArchetype:
                            self.skipAhead = 0
                            matchBars = True
                            break
                if matchBars is True:
                    accidentalized = {}
                    accidental = None
                    j = self.pos + self.skipAhead + 1
                    self.currentCollectStr = self.strSrc[self.pos:j]
                    # filter and replace with 2 tokens if necessary
                    for tokenSub in self.barlineTokenFilter(self.currentCollectStr):
                        self.tokens.append(tokenSub)
                    # environLocal.printDebug(['got bars:', repr(self.currentCollectStr)])
                    # if self.currentCollectStr == '::':
                    #     # create a start and and an end
                    #     self.tokens.append(ABCBar(':|'))
                    #     self.tokens.append(ABCBar('|:'))
                    # else:
                    #     self.tokens.append(ABCBar(self.currentCollectStr))
                    continue

            # get tuplet indicators: (2, (3, (p:q:r or (3::
            if c == '(' and cNext is not None and cNext.isdigit():
                self.skipAhead = 1
                j = self.pos + self.skipAhead + 1  # always two characters
                unused1, possibleColon, qChar, unused2 = self._getLinearContext(self.strSrc, j)
                if possibleColon == ':':
                    j += 1
                    self.skipAhead += 1
                    if qChar is not None and qChar.isdigit():
                        j += 1
                        self.skipAhead += 1
                    unused1, possibleColon, rChar, unused2 = self._getLinearContext(self.strSrc, j)
                    if possibleColon == ':':
                        j += 1  # include the r characters
                        self.skipAhead += 1
                        if rChar is not None and rChar.isdigit():
                            j += 1
                            self.skipAhead += 1

                self.currentCollectStr = self.strSrc[self.pos:j]
                # environLocal.printDebug(['got tuplet start:', repr(self.currentCollectStr)])
                self.tokens.append(ABCTuplet(self.currentCollectStr))
                continue

            # get broken rhythm modifiers: < or >, >>, up to <<<
            if c in '<>':
                j = self.pos + 1
                while j < self.srcLen - 1 and self.strSrc[j] in '<>':
                    j += 1
                self.currentCollectStr = self.strSrc[self.pos:j]
                # environLocal.printDebug(
                #     ['got bidrectional rhythm mod:', repr(self.currentCollectStr)])
                self.tokens.append(ABCBrokenRhythmMarker(self.currentCollectStr))
                self.skipAhead = j - (self.pos + 1)
                continue

            # get dynamics. skip over the open paren to avoid confusion.
            # NB: Nested crescendos are not an issue (not proper grammar).
            if c == '!':
                exclaimDict = {'!crescendo(!': ABCCrescStart,
                               '!crescendo)!': ABCParenStop,
                               '!diminuendo(!': ABCDimStart,
                               '!diminuendo)!': ABCParenStop,
                               }
                j = self.pos + 1
                while j < self.pos + 20 and j < self.srcLen:  # a reasonable upper bound
                    if self.strSrc[j] == '!':
                        if self.strSrc[self.pos:j + 1] in exclaimDict:
                            exclaimClass = exclaimDict[self.strSrc[self.pos:j + 1]]
                            exclaimObject = exclaimClass(c)
                            self.tokens.append(exclaimObject)
                            self.skipAhead = j - self.pos  # not + 1
                            break
                        # NB: We're currently skipping over all other '!' expressions
                        else:
                            self.skipAhead = j - self.pos  # not + 1
                            break
                    j += 1
                # not found, continue...
                continue

            # get slurs, ensuring that they're not confused for tuplets
            if c == '(' and cNext is not None and not cNext.isdigit():
                self.tokens.append(ABCSlurStart(c))
                continue

            # get slur/tuplet ending; treat it as a general parenthesis stop
            if c == ')':
                self.tokens.append(ABCParenStop(c))
                continue

            # get ties between two notes
            if c == '-':
                self.tokens.append(ABCTie(c))
                continue

            # get chord symbols / guitar chords; collected and joined with
            # chord or notes
            if c == '"':
                j = self.pos + 1
                while j < self.srcLen - 1 and self.strSrc[j] != '"':
                    j += 1
                j += 1  # need character that caused break
                # there may be more than one chord symbol: need to accumulate
                activeChordSymbol += self.strSrc[self.pos:j]
                # environLocal.printDebug(['got chord symbol:', repr(activeChordSymbol)])
                self.skipAhead = j - (self.pos + 1)
                continue

            # get chords
            if c == '[':
                j = self.pos + 1

                # find closing chord bracket
                while j < self.srcLen - 1 and self.strSrc[j] != ']':
                    j += 1

                j += 1  # need character that caused break

                # find outer chord length modifier
                while j < self.srcLen and (self.strSrc[j].isdigit() or self.strSrc[j] in '/'):
                    j += 1

                # prepend chord symbol
                if activeChordSymbol != '':
                    self.currentCollectStr = activeChordSymbol + self.strSrc[self.pos:j]
                    activeChordSymbol = ''  # reset
                else:
                    self.currentCollectStr = self.strSrc[self.pos:j]

                # environLocal.printDebug(['got chord:', repr(self.currentCollectStr)])
                self.tokens.append(ABCChord(self.currentCollectStr))
                self.skipAhead = j - (self.pos + 1)
                # TODO: Chords need to be aware of accidentals too.
                # Also what happens to prefixes and suffixes attached to chords,
                # like ties.
                continue

            if c == '.':
                self.tokens.append(ABCStaccato(c))
                continue

            if c == 'u':
                self.tokens.append(ABCUpbow(c))
                continue

            if c == '{':
                self.tokens.append(ABCGraceStart(c))
                continue

            if c == '}':
                self.tokens.append(ABCGraceStop(c))
                continue

            if c == 'v':
                self.tokens.append(ABCDownbow(c))
                continue

            if c == 'K':
                self.tokens.append(ABCAccent(c))
                continue

            if c == 'k':
                self.tokens.append(ABCStraccent(c))
                continue

            if c == 'M':
                self.tokens.append(ABCTenuto(c))
                continue

            # get the start of a note event: alpha, decoration, or accidental
            if c.isalpha() or c in '~^=_':
                # condition where we start with an alpha that is not an alpha
                # that comes before a pitch indication
                # From the 2.2 draft standard, we see the following "decorations"
                # defined:
                #     .       staccato mark
                #     ~       Irish roll
                #     H       fermata
                #     L       accent or emphasis
                #     M       lower mordent
                #     O       coda
                #     P       upper mordent
                #     S       segno
                #     T       trill
                #     u       up-bow
                #     v       down-bow
                #
                # Accidentals are these:
                #     ^       sharp
                #     ^^      double-sharp
                #     =       natural
                #     _       flat
                #     __      double-flat
                foundPitchAlpha = c.isalpha() and c not in accidentalsAndDecorations
                if foundPitchAlpha:
                    abcPitch = c
                if c in accidentals:
                    accidental = c
                j = self.pos + 1

                while j <= self.srcLen - 1:
                    # if we have not found pitch alpha
                    # decorations and/or accidentals may precede note names
                    if not foundPitchAlpha and self.strSrc[j] in accidentalsAndDecorations:
                        j += 1
                        if self.strSrc[j] in accidentals:
                            accidental += self.strSrc[j]
                        continue
                    # only allow one pitch alpha to be a continue condition
                    elif (not foundPitchAlpha and self.strSrc[j].isalpha()
                          # noinspection SpellCheckingInspection
                          and self.strSrc[j] not in '~wuvhHLTSN'):
                        foundPitchAlpha = True
                        abcPitch = self.strSrc[j]
                        j += 1
                        continue
                    # continue conditions after alpha:
                    # , register modification (, ') or number, rhythm indication
                    # number, /,
                    elif self.strSrc[j].isdigit() or self.strSrc[j] in ',/,\'':
                        if self.strSrc[j] in ',\'':  # Register (octave) modification
                            abcPitch += self.strSrc[j]
                        j += 1
                        continue
                    else:  # space, all else: break
                        break
                # prepend chord symbol
                if activeChordSymbol != '':
                    self.currentCollectStr = activeChordSymbol + self.strSrc[self.pos:j]
                    activeChordSymbol = ''  # reset
                else:
                    self.currentCollectStr = self.strSrc[self.pos:j]
                # environLocal.printDebug(['got note event:', repr(self.currentCollectStr)])

                # NOTE: skipping a number of articulations and other markers
                # that are not yet supported
                # some collections here are not yet supported; others may be
                # the result of errors in encoded files
                # v is up bow; might be: "^Segno"v which also should be dropped
                # H is fermata
                # . dot may be staccato, but should be attached to pitch
                if self.currentCollectStr in ('w', 'u', 'v', 'v.', 'h', 'H', 'vk',
                               'uk', 'U', '~',
                               '.', '=', 'V', 'v.', 'S', 's',
                               'i', 'I', 'ui', 'u.', 'Q', 'Hy', 'Hx',
                               'r', 'm', 'M', 'n', 'N', 'o', 'O', 'P',
                               'l', 'L', 'R',
                               'y', 'T', 't', 'x', 'Z'):
                    pass
                # these are bad chords, or other problematic notations like
                # "D.C."x
                elif (self.currentCollectStr.startswith('"')
                      and (self.currentCollectStr[-1] in ('u', 'v', 'k', 'K', 'Q', '.',
                                                          'y', 'T', 'w', 'h', 'x',)
                           or self.currentCollectStr.endswith('v.'))):
                    pass
                elif (self.currentCollectStr.startswith('x')
                      or self.currentCollectStr.startswith('H')
                      or self.currentCollectStr.startswith('Z')):
                    pass
                # not sure what =20 refers to
                elif (len(self.currentCollectStr) > 1
                      and self.currentCollectStr.startswith('=')
                      and self.currentCollectStr[1].isdigit()):
                    pass
                # only let valid self.currentCollectStr strings be parsed
                elif abcPitch:
                    pitchClass = abcPitch[0].upper()
                    carriedAccidental = None
                    propagation = self._accidentalPropagation()
                    if accidental:
                        # Remember the active accidentals in the measure
                        if propagation == 'octave':
                            accidentalized[abcPitch] = accidental
                        elif propagation == 'pitch':
                            accidentalized[pitchClass] = accidental
                        accidental = None
                    else:
                        if propagation == 'pitch' and pitchClass in accidentalized:
                            carriedAccidental = accidentalized[pitchClass]
                        elif propagation == 'octave' and abcPitch in accidentalized:
                            carriedAccidental = accidentalized[abcPitch]
                    abcNote = ABCNote(self.currentCollectStr, carriedAccidental=carriedAccidental)
                    self.tokens.append(abcNote)
                else:
                    self.tokens.append(ABCNote(self.currentCollectStr))

                self.skipAhead = j - (self.pos + 1)
                continue
            # look for white space: can be used to determine beam groups
            # no action: normal continuation of 1 char
            pass

    def tokenProcess(self):
        '''
        Process all token objects. First, calls preParse(), then
        does context assignments, then calls parse().
        '''
        # need a key object to get altered pitches
        from music21 import key

        # pre-parse : call on objects that need preliminary processing
        # metadata, for example, is parsed
        # lastTimeSignature = None
        for t in self.tokens:
            # environLocal.printDebug(['tokenProcess: calling preParse()', t.src])
            t.preParse()

        # context: iterate through tokens, supplying contextual data
        # as necessary to appropriate objects
        lastDefaultQL = None
        lastKeySignature = None
        lastTimeSignatureObj = None  # an m21 object
        lastTupletToken = None  # a token obj; keeps count of usage
        lastTieToken = None
        lastStaccToken = None
        lastUpToken = None
        lastDownToken = None
        lastAccToken = None
        lastStrAccToken = None
        lastTenutoToken = None
        lastGraceToken = None
        lastNoteToken = None

        for i in range(len(self.tokens)):
            # get context of tokens
            q = self._getLinearContext(self.tokens, i)
            tPrev, t, tNext, unused_tNextNext = q
            # tPrevNotSpace, tPrev, t, tNext, tNextNotSpace, tNextNext = q
            # environLocal.printDebug(['tokenProcess: calling parse()', t])

            if isinstance(t, ABCMetadata):
                if t.isMeter():
                    lastTimeSignatureObj = t.getTimeSignatureObject()
                # restart matching conditions; match meter twice ok
                if t.isDefaultNoteLength() or (t.isMeter() and lastDefaultQL is None):
                    lastDefaultQL = t.getDefaultQuarterLength()
                elif t.isKey():
                    sharpCount, mode = t.getKeySignatureParameters()
                    lastKeySignature = key.KeySignature(sharpCount)
                    if mode not in (None, ''):
                        lastKeySignature = lastKeySignature.asKey(mode)

                if t.isReferenceNumber():
                    # reset any spanners or parens at the end of any piece
                    # in case they aren't closed.
                    self.activeParens = []
                    self.activeSpanners = []
                continue
            # broken rhythms need to be applied to previous and next notes
            if isinstance(t, ABCBrokenRhythmMarker):
                if (isinstance(tPrev, ABCNote)
                        and isinstance(tNext, ABCNote)):
                    # environLocal.printDebug(['tokenProcess: got broken rhythm marker', t.src])
                    tPrev.brokenRhythmMarker = (t.data, 'left')
                    tNext.brokenRhythmMarker = (t.data, 'right')
                else:
                    environLocal.printDebug(
                        ['broken rhythm marker '
                         + f'({t.src}) not positioned between two notes or chords'])

            # need to update tuplets with currently active meter
            if isinstance(t, ABCTuplet):
                t.updateRatio(lastTimeSignatureObj)
                # set number of notes that will be altered
                # might need to do this with ql values, or look ahead to nxt
                # token
                t.updateNoteCount()
                lastTupletToken = t
                self.activeParens.append('Tuplet')

            # notes within slur marks need to be added to the spanner
            if isinstance(t, ABCSlurStart):
                t.fillSlur()
                self.activeSpanners.append(t.slurObj)
                self.activeParens.append('Slur')
            elif isinstance(t, ABCParenStop):
                if self.activeParens:
                    p = self.activeParens.pop()
                    if p in ('Slur', 'Crescendo', 'Diminuendo'):
                        self.activeSpanners.pop()

            if isinstance(t, ABCTie):
                # tPrev is usually an ABCNote but may be a GraceStop.
                if lastNoteToken and lastNoteToken.tie == 'stop':
                    lastNoteToken.tie = 'continue'
                elif lastNoteToken:
                    lastNoteToken.tie = 'start'
                lastTieToken = t

            if isinstance(t, ABCStaccato):
                lastStaccToken = t

            if isinstance(t, ABCUpbow):
                lastUpToken = t

            if isinstance(t, ABCDownbow):
                lastDownToken = t

            if isinstance(t, ABCAccent):
                lastAccToken = t

            if isinstance(t, ABCStraccent):
                lastStrAccToken = t

            if isinstance(t, ABCTenuto):
                lastTenutoToken = t

            if isinstance(t, ABCCrescStart):
                t.fillCresc()
                self.activeSpanners.append(t.crescObj)
                self.activeParens.append('Crescendo')

            if isinstance(t, ABCDimStart):
                t.fillDim()
                self.activeSpanners.append(t.dimObj)
                self.activeParens.append('Diminuendo')

            if isinstance(t, ABCGraceStart):
                lastGraceToken = t

            if isinstance(t, ABCGraceStop):
                lastGraceToken = None

            # ABCChord inherits ABCNote, thus getting note is enough for both
            if isinstance(t, (ABCNote, ABCChord)):
                if lastDefaultQL is None:
                    raise ABCHandlerException(
                        'no active default note length provided for note processing. '
                        + f'tPrev: {tPrev}, t: {t}, tNext: {tNext}'
                    )
                t.activeDefaultQuarterLength = lastDefaultQL
                t.activeKeySignature = lastKeySignature
                t.applicableSpanners = self.activeSpanners[:]  # fast copy of a list
                # ends ties one note after they begin
                if lastTieToken is not None:
                    t.tie = 'stop'
                    lastTieToken = None
                if lastStaccToken is not None:
                    t.articulations.append('staccato')
                    lastStaccToken = None
                if lastUpToken is not None:
                    t.articulations.append('upbow')
                    lastUpToken = None
                if lastDownToken is not None:
                    t.articulations.append('downbow')
                    lastDownToken = None
                if lastAccToken is not None:
                    t.articulations.append('accent')
                    lastAccToken = None
                if lastStrAccToken is not None:
                    t.articulations.append('strongaccent')
                    lastStrAccToken = None
                if lastTenutoToken is not None:
                    t.articulations.append('tenuto')
                    lastTenutoToken = None
                if lastGraceToken is not None:
                    t.inGrace = True
                if lastTupletToken is None:
                    pass
                elif lastTupletToken.noteCount == 0:
                    lastTupletToken = None  # clear, no longer needed
                else:
                    lastTupletToken.noteCount -= 1  # decrement
                    # add a reference to the note
                    t.activeTuplet = lastTupletToken.tupletObj
                lastNoteToken = t

        # parse : call methods to set attributes and parse abc string
        for t in self.tokens:
            # environLocal.printDebug(['tokenProcess: calling parse()', t])
            t.parse()

    def process(self, strSrc: str) -> None:
        self.tokens = []
        self.tokenize(strSrc)
        self.tokenProcess()
        # return list of tokens; stored internally

    # --------------------------------------------------------------------------
    # access tokens

    def __len__(self):
        return len(self.tokens)

    def __add__(self, other):
        '''
        Return a new handler adding the tokens in both

        Contrived example appending two separate keys.

        Used in polyphonic metadata merge


        >>> abcStr = 'M:6/8\\nL:1/8\\nK:G\\n'
        >>> ah1 = abcFormat.ABCHandler()
        >>> junk = ah1.process(abcStr)
        >>> len(ah1)
        3

        >>> abcStr = 'M:3/4\\nL:1/4\\nK:D\\n'
        >>> ah2 = abcFormat.ABCHandler()
        >>> junk = ah2.process(abcStr)
        >>> len(ah2)
        3

        >>> ah3 = ah1 + ah2
        >>> len(ah3)
        6
        >>> ah3.tokens[0] == ah1.tokens[0]
        True
        >>> ah3.tokens[3] == ah2.tokens[0]
        True

        '''
        ah = self.__class__()  # will get the same class type
        ah.tokens = self.tokens + other.tokens
        return ah

    # --------------------------------------------------------------------------
    # utility methods for post processing

    def definesReferenceNumbers(self):
        '''
        Return True if this token structure defines more than 1 reference number,
        usually implying multiple pieces encoded in one file.


        >>> abcStr = 'X:5\\nM:6/8\\nL:1/8\\nK:G\\nB3 A3 | G6 | B3 A3 | G6 ||'
        >>> ah = abcFormat.ABCHandler()
        >>> junk = ah.process(abcStr)
        >>> ah.definesReferenceNumbers()  # only one returns False
        False


        >>> abcStr = 'X:5\\nM:6/8\\nL:1/8\\nK:G\\nB3 A3 | G6 | B3 A3 | G6 ||\\n'
        >>> abcStr += 'X:6\\nM:6/8\\nL:1/8\\nK:G\\nB3 A3 | G6 | B3 A3 | G6 ||'
        >>> ah = abcFormat.ABCHandler()
        >>> junk = ah.process(abcStr)
        >>> ah.definesReferenceNumbers()  # two tokens so returns True
        True
        '''
        if not self.tokens:
            raise ABCHandlerException('must process tokens before calling split')
        count = 0
        for i in range(len(self.tokens)):
            t = self.tokens[i]
            if isinstance(t, ABCMetadata):
                if t.isReferenceNumber():
                    count += 1
                    if count > 1:
                        return True
        return False

    def splitByReferenceNumber(self):
        # noinspection PyShadowingNames
        r'''
        Split tokens by reference numbers.

        Returns a dictionary of ABCHandler instances, where the reference number
        is used to access the music. If no reference numbers are defined,
        the tune is available under the dictionary entry None.


        >>> abcStr = 'X:5\nM:6/8\nL:1/8\nK:G\nB3 A3 | G6 | B3 A3 | G6 ||'
        >>> abcStr += 'X:6\nM:6/8\nL:1/8\nK:G\nB3 A3 | G6 | B3 A3 | G6 ||'
        >>> ah = abcFormat.ABCHandler()
        >>> junk = ah.process(abcStr)
        >>> len(ah)
        28
        >>> ahDict = ah.splitByReferenceNumber()
        >>> 5 in ahDict
        True
        >>> 6 in ahDict
        True
        >>> 7 in ahDict
        False

        Each entry is its own ABCHandler object.

        >>> ahDict[5]
        <music21.abcFormat.ABCHandler object at 0x10b0cf5f8>
        >>> len(ahDict[5].tokens)
        14

        Header information (except for comments) should be appended to all pieces.

        >>> abcStrWHeader = '%abc-2.1\nO: Irish\n' + abcStr
        >>> ah = abcFormat.ABCHandler()
        >>> junk = ah.process(abcStrWHeader)
        >>> len(ah)
        29
        >>> ahDict = ah.splitByReferenceNumber()
        >>> 5 in ahDict
        True
        >>> 6 in ahDict
        True
        >>> 7 in ahDict
        False

        Did we get the origin header in each score?

        >>> ahDict[5].tokens[0]
        <music21.abcFormat.ABCMetadata 'O: Irish'>
        >>> ahDict[6].tokens[0]
        <music21.abcFormat.ABCMetadata 'O: Irish'>
        '''
        if not self.tokens:
            raise ABCHandlerException('must process tokens before calling split')

        ahDict = {}

        # tokens in this list are prepended to all tunes:
        prependToAllList = []
        activeTokens = []
        currentABCHandler = None

        for i, t in enumerate(self.tokens):
            if isinstance(t, ABCMetadata) and t.isReferenceNumber():
                if currentABCHandler is not None:
                    currentABCHandler.tokens = activeTokens
                    activeTokens = []
                currentABCHandler = ABCHandler()
                referenceNumber = int(t.data)
                ahDict[referenceNumber] = currentABCHandler

            if currentABCHandler is None:
                prependToAllList.append(t)
            else:
                activeTokens.append(t)

        if currentABCHandler is not None:
            currentABCHandler.tokens = activeTokens

        if not ahDict:
            ahDict[None] = ABCHandler()

        for thisABCHandler in ahDict.values():
            thisABCHandler.tokens = prependToAllList[:] + thisABCHandler.tokens

        return ahDict

    def getReferenceNumber(self):
        '''
        If tokens are processed, get the first
        reference number defined.


        >>> abcStr = 'X:5\\nM:6/8\\nL:1/8\\nK:G\\nB3 A3 | G6 | B3 A3 | G6 ||'
        >>> ah = abcFormat.ABCHandler()
        >>> junk = ah.process(abcStr)
        >>> ah.getReferenceNumber()
        '5'
        '''
        if not self.tokens:
            raise ABCHandlerException('must process tokens before calling split')
        for t in self.tokens:
            if isinstance(t, ABCMetadata):
                if t.isReferenceNumber():
                    return t.data
        return None

    def definesMeasures(self):
        '''
        Returns True if this token structure defines Measures in a normal Measure form.
        Otherwise False


        >>> abcStr = ('M:6/8\\nL:1/8\\nK:G\\nV:1 name="Whistle" ' +
        ...     'snm="wh"\\nB3 A3 | G6 | B3 A3 | G6 ||\\nV:2 name="violin" ' +
        ...     'snm="v"\\nBdB AcA | GAG D3 | BdB AcA | GAG D6 ||\\nV:3 name="Bass" ' +
        ...     'snm="b" clef=bass\\nD3 D3 | D6 | D3 D3 | D6 ||')
        >>> ah = abcFormat.ABCHandler()
        >>> junk = ah.process(abcStr)
        >>> ah.definesMeasures()
        True

        >>> abcStr = 'M:6/8\\nL:1/8\\nK:G\\nB3 A3 G6 B3 A3 G6'
        >>> ah = abcFormat.ABCHandler()
        >>> junk = ah.process(abcStr)
        >>> ah.definesMeasures()
        False
        '''
        if not self.tokens:
            raise ABCHandlerException('must process tokens before calling split')
        count = 0
        for i in range(len(self.tokens)):
            t = self.tokens[i]
            if isinstance(t, ABCBar):
                # must define at least 2 regular barlines
                # this leave out cases where only double bars are given
                if t.isRegular():
                    count += 1
                    # forcing the inclusion of two measures to count
                    if count >= 2:
                        return True
        return False

    def splitByVoice(self) -> List['ABCHandler']:
        # noinspection PyShadowingNames
        '''
        Given a processed token list, look for voices. If voices exist,
        split into parts: common metadata, then next voice, next voice, etc.

        Each part is returned as a ABCHandler instance.

        >>> abcStr = ('M:6/8\\nL:1/8\\nK:G\\nV:1 name="Whistle" ' +
        ...     'snm="wh"\\nB3 A3 | G6 | B3 A3 | G6 ||\\nV:2 name="violin" ' +
        ...     'snm="v"\\nBdB AcA | GAG D3 | BdB AcA | GAG D6 ||\\nV:3 name="Bass" ' +
        ...     'snm="b" clef=bass\\nD3 D3 | D6 | D3 D3 | D6 ||')
        >>> ah = abcFormat.ABCHandler()
        >>> ah.process(abcStr)
        >>> tokenColls = ah.splitByVoice()
        >>> tokenColls[0]
        <music21.abcFormat.ABCHandler object at 0x...>

        Common headers are first

        >>> [t.src for t in tokenColls[0].tokens]
        ['M:6/8', 'L:1/8', 'K:G']

        Then each voice

        >>> [t.src for t in tokenColls[1].tokens]
        ['V:1 name="Whistle" snm="wh"', 'B3', 'A3', '|', 'G6', '|', 'B3', 'A3', '|', 'G6', '||']
        >>> [t.src for t in tokenColls[2].tokens]
        ['V:2 name="violin" snm="v"', 'B', 'd', 'B', 'A', 'c', 'A', '|',
         'G', 'A', 'G', 'D3', '|', 'B', 'd', 'B', 'A', 'c', 'A', '|', 'G', 'A', 'G', 'D6', '||']
        >>> [t.src for t in tokenColls[3].tokens]
        ['V:3 name="Bass" snm="b" clef=bass', 'D3', 'D3', '|', 'D6', '|',
         'D3', 'D3', '|', 'D6', '||']

        Then later the metadata can be merged at the start of each voice...

        >>> mergedTokens = tokenColls[0] + tokenColls[1]
        >>> mergedTokens
        <music21.abcFormat.ABCHandler object at 0x...>
        >>> [t.src for t in mergedTokens.tokens]
        ['M:6/8', 'L:1/8', 'K:G', 'V:1 name="Whistle" snm="wh"',
         'B3', 'A3', '|', 'G6', '|', 'B3', 'A3', '|', 'G6', '||']
        '''
        # TODO: this procedure should also be responsible for
        #     breaking the passage into voice/lyric pairs

        if not self.tokens:
            raise ABCHandlerException('must process tokens before calling split')

        voiceCount = 0
        pos = []
        for i in range(len(self.tokens)):
            t = self.tokens[i]
            if isinstance(t, ABCMetadata):
                if t.isVoice():
                    # if first char is a number
                    # can be V:3 name="Bass" snm="b" clef=bass
                    if t.data[0].isdigit():
                        pos.append(i)  # store position
                        voiceCount += 1

        abcHandlers = []
        # no voices, or definition of one voice, or use of V: field for
        # something else
        if voiceCount <= 1:
            ah = self.__class__()  # just making a copy
            ah.tokens = self.tokens
            abcHandlers.append(ah)
        # two or more voices
        else:
            # collect start and end pairs of split
            pairs = []
            pairs.append([0, pos[0]])
            i = pos[0]
            for x in range(1, len(pos)):
                j = pos[x]
                pairs.append([i, j])
                i = j
            # add last
            pairs.append([i, len(self)])

            for x, y in pairs:
                ah = self.__class__()
                ah.tokens = self.tokens[x:y]
                abcHandlers.append(ah)

        return abcHandlers

    @staticmethod
    def _buildMeasureBoundaryIndices(
        positionList: List[int],
        lastValidIndex: int
    ) -> List[List[int]]:
        '''
        Staticmethod

        Given a list of indices of a list marking the position of
        each barline or implied barline, and the last valid index,
        return a list of two-element lists, each indicating
        the start and positions of a measure.

        Here's an easy case that makes this method look worthless:

        >>> AH = abcFormat.ABCHandler
        >>> AH._buildMeasureBoundaryIndices([8, 12, 16], 20)
        [[0, 8], [8, 12], [12, 16], [16, 20]]

        But in this case, we need to see that 12 and 13 don't represent different measures but
        probably represent an end and new barline (repeat bar), etc.

        >>> AH._buildMeasureBoundaryIndices([8, 12, 13, 16], 20)
        [[0, 8], [8, 12], [13, 16], [16, 20]]

        Here 115 is both the last barline and the last index, so there is no [115, 115] entry.

        >>> bi = [9, 10, 16, 23, 29, 36, 42, 49, 56, 61, 62, 64, 70, 77, 84, 90, 96, 103, 110, 115]
        >>> AH._buildMeasureBoundaryIndices(bi, 115)
        [[0, 9], [10, 16], [16, 23], [23, 29], [29, 36], [36, 42], [42, 49], [49, 56], [56, 61],
         [62, 64], [64, 70], [70, 77], [77, 84], [84, 90], [90, 96],
         [96, 103], [103, 110], [110, 115]]

        '''
        # collect start and end pairs of split
        pairs = []
        # first chunk is metadata, as first token is probably not a bar
        pairs.append([0, positionList[0]])
        i = positionList[0]  # get first bar position stored
        # iterate through every other bar position (already have first)
        for x in range(1, len(positionList)):
            j = positionList[x]
            if j == i + 1:  # a span of one is skipped
                i = j
                continue
            pairs.append([i, j])
            i = j  # the end becomes the new start
        # add last valid index
        if i != lastValidIndex:
            pairs.append([i, lastValidIndex])
        # environLocal.printDebug(['splitByMeasure(); pairs pre filter', pairs])
        return pairs

    def splitByMeasure(self) -> List['ABCHandlerBar']:
        '''
        Divide a token list by Measures, also
        defining start and end bars of each Measure.

        If a component does not have notes, leave
        as an empty bar. This is often done with leading metadata.

        Returns a list of ABCHandlerBar instances.
        The first usually defines only Metadata

        TODO: Test and examples
        '''
        if not self.tokens:
            raise ABCHandlerException('must process tokens before calling split')

        abcBarHandlers = []
        barIndices = self.tokensToBarIndices()

        # barCount = 0  # not used
        # noteCount = 0  # not used

        # environLocal.printDebug(['splitByMeasure(); raw bar positions', barIndices])
        measureIndices = self._buildMeasureBoundaryIndices(barIndices, len(self) - 1)
        # for x, y in pairs:
        #     environLocal.printDebug(['boundary indices:', x, y])
        #     environLocal.printDebug(['    values at x, y', self.tokens[x], self.tokens[y]])

        # iterate through start and end pairs
        for x, y in measureIndices:
            ah = ABCHandlerBar()
            # this will get the first to last
            # shave of tokens if not needed
            xClip = x
            yClip = y

            # check if first is a bar; if so, assign and remove
            if isinstance(self.tokens[x], ABCBar):
                lbCandidate = self.tokens[x]
                # if we get an end repeat, probably already assigned this
                # in the last measure, so skip
                # environLocal.printDebug(['reading pairs, got token:', lbCandidate,
                #    'lbCandidate.barType', lbCandidate.barType,
                #    'lbCandidate.repeatForm', lbCandidate.repeatForm])
                # skip end repeats assigned (improperly) to the left
                if (lbCandidate.barType == 'repeat'
                        and lbCandidate.repeatForm == 'end'):
                    pass
                else:  # assign
                    ah.leftBarToken = lbCandidate
                    # environLocal.printDebug(['splitByMeasure(); assigning left bar token',
                    #                        lbCandidate])
                # always trim if we have a bar
                xClip = x + 1
                # ah.tokens = ah.tokens[1:]  # remove first, as not done above

            # if x boundary is metadata, do not include it (as it is likely in the previous
            # measure) unless it is at the beginning.
            elif x != 0 and isinstance(self.tokens[x], ABCMetadata):
                xClip = x + 1
            else:
                # if we find a note in the x-clip position, it is likely a pickup the
                # first note after metadata. this we keep, b/c it
                # should be part of this branch
                pass

            if y >= len(self):
                yTestIndex = len(self)
            else:
                yTestIndex = y

            if isinstance(self.tokens[yTestIndex], ABCBar):
                rbCandidate = self.tokens[yTestIndex]
                # if a start repeat, save it to be placed as a left barline
                if not (rbCandidate.barType == 'repeat'
                        and rbCandidate.repeatForm == 'start'):
                    # environLocal.printDebug(['splitByMeasure(); assigning right bar token',
                    #                             lbCandidate])
                    ah.rightBarToken = self.tokens[yTestIndex]
                # always trim if we have a bar
                # ah.tokens = ah.tokens[:-1]  # remove last
                yClip = y - 1
            # if y boundary is metadata, include it
            elif isinstance(self.tokens[yTestIndex], ABCMetadata):
                pass  # no change
            # if y position is a note/chord, and this is the last index,
            # must included it
            elif not (isinstance(self.tokens[yTestIndex], (ABCNote, ABCChord))
                      and yTestIndex == len(self.tokens) - 1):
                # if we find a note in the yClip position, it is likely
                # a pickup, the first note after metadata. we do not include this
                yClip = yTestIndex - 1

            # environLocal.printDebug(['clip boundaries: x,y', xClip, yClip])
            # boundaries are inclusive; need to add one here
            ah.tokens = self.tokens[xClip:yClip + 1]
            # after bar assign, if no bars known, reject
            if not ah:
                continue
            abcBarHandlers.append(ah)

        # for sub in abcBarHandlers:
        #     environLocal.printDebug(['concluded splitByMeasure:', sub,
        #            'leftBarToken', sub.leftBarToken, 'rightBarToken', sub.rightBarToken,
        #            'len(sub)', len(sub), 'sub.hasNotes()', sub.hasNotes()])
        #     for t in sub.tokens:
        #         print('\t', t)
        return abcBarHandlers

    def tokensToBarIndices(self) -> List[int]:
        '''
        Return a list of indices indicating which tokens in self.tokens are
        bar lines or the last piece of metadata before a note or chord.
        '''
        barIndices = []
        tNext = None
        for i, t in enumerate(self.tokens):
            try:
                tNext = self.tokens[i + 1]
            except IndexError:
                tNext = None

            # either we get a bar, or we just complete metadata and we
            # encounter a note (a pickup)
            if isinstance(t, ABCBar):  # or (barCount == 0 and noteCount > 0):
                # environLocal.printDebug(['splitByMeasure()', 'found bar', t])
                barIndices.append(i)  # store position
                # barCount += 1  # not used
            # case of end of metadata and start of notes in a pickup
            # tag the last metadata as the end
            elif (isinstance(t, ABCMetadata)
                  and tNext is not None
                  and isinstance(tNext, (ABCNote, ABCChord))):
                barIndices.append(i)  # store position

        return barIndices

    def hasNotes(self) -> bool:
        '''
        If tokens are processed, return True if ABCNote or
        ABCChord classes are defined


        >>> abcStr = 'M:6/8\\nL:1/8\\nK:G\\n'
        >>> ah1 = abcFormat.ABCHandler()
        >>> junk = ah1.process(abcStr)
        >>> ah1.hasNotes()
        False

        >>> abcStr = 'M:6/8\\nL:1/8\\nK:G\\nc1D2'
        >>> ah2 = abcFormat.ABCHandler()
        >>> junk = ah2.process(abcStr)
        >>> ah2.hasNotes()
        True
        '''
        if not self.tokens:
            raise ABCHandlerException('must process tokens before calling')
        count = 0
        for t in self.tokens:
            if isinstance(t, (ABCNote, ABCChord)):
                count += 1
        # environLocal.printDebug(['hasNotes', count])
        if count > 0:
            return True
        else:
            return False

    def getTitle(self) -> Optional[str]:
        '''
        Get the first title tag. Used for testing.

        Requires tokens to have been processed.
        '''
        if not self.tokens:
            raise ABCHandlerException('must process tokens before calling split')
        for t in self.tokens:
            if isinstance(t, ABCMetadata):
                if t.isTitle():
                    return t.data
        return None


class ABCHandlerBar(ABCHandler):
    '''
    A Handler specialized for storing bars. All left
    and right bars are collected and assigned to attributes.
    '''
    # divide elements of a character stream into objects and handle
    # store in a list, and pass global information to components

    def __init__(self):
        # tokens are ABC objects in a linear stream
        super().__init__()

        self.leftBarToken = None
        self.rightBarToken = None

    def __add__(self, other):
        ah = self.__class__()  # will get the same class type
        ah.tokens = self.tokens + other.tokens
        # get defined tokens
        for barAttr in ('leftBarToken', 'rightBarToken'):
            bOld = getattr(self, barAttr)
            bNew = getattr(other, barAttr)
            if bNew is None and bOld is None:
                pass  # nothing to do
            elif bNew is not None and bOld is None:  # get new
                setattr(ah, barAttr, bNew)
            elif bNew is None and bOld is not None:  # get old
                setattr(ah, barAttr, bOld)
            else:
                # if both ar the same, assign one
                if bOld.src == bNew.src:
                    setattr(ah, barAttr, bNew)
                else:
                    # might resolve this by ignoring standard bars and favoring
                    # repeats or styled bars
                    environLocal.printDebug(['cannot handle two non-None bars yet: got bNew, bOld',
                                             bNew, bOld])
                    # raise ABCHandlerException('cannot handle two non-None bars yet')
                    setattr(ah, barAttr, bNew)

        return ah


def mergeLeadingMetaData(barHandlers: List[ABCHandlerBar]) -> List[ABCHandlerBar]:
    '''
    Given a list of ABCHandlerBar objects, return a list of ABCHandlerBar
    objects where leading metadata is merged, if possible,
    with the bar data following.

    This consolidates all metadata in bar-like entities.
    '''
    mCount = 0
    metadataPos = []  # store indices of handlers that are all metadata
    for i in range(len(barHandlers)):
        if barHandlers[i].hasNotes():
            mCount += 1
        else:
            metadataPos.append(i)
    # environLocal.printDebug(['mergeLeadingMetaData()',
    #                        'metadataPosList', metadataPos, 'mCount', mCount])
    # merge meta data into bars for processing
    mergedHandlers = []
    if mCount <= 1:  # if only one true measure, do not create measures
        ahb = ABCHandlerBar()
        for h in barHandlers:
            ahb += h  # concatenate all
        mergedHandlers.append(ahb)
    else:
        # when we have metadata, we need to pass its tokens with those
        # of the measure that follows it; if we have trailing meta data,
        # we can pass but do not create a measure
        i = 0
        while i < len(barHandlers):
            # if we find metadata and it is not the last valid index
            # merge into a single handler
            if i in metadataPos and i != len(barHandlers) - 1:
                mergedHandlers.append(barHandlers[i] + barHandlers[i + 1])
                i += 2
            else:
                mergedHandlers.append(barHandlers[i])
                i += 1

    return mergedHandlers

# ------------------------------------------------------------------------------


class ABCFile(prebase.ProtoM21Object):
    '''
    ABC File or String access

    The abcVersion attribution optionally specifies the (major, minor, patch)
    version of ABC to process-- e.g., (1.2.0).
    If not set, default ABC 1.3 parsing is performed.
    '''
    def __init__(self, abcVersion=None):
        self.abcVersion = abcVersion
        self.file = None
        self.filename = None

    def open(self, filename):
        '''
        Open a file for reading
        '''
        # try:
        self.file = io.open(filename, encoding='utf-8')
        # except
        # self.file = io.open(filename, encoding='latin-1')
        self.filename = filename

    def openFileLike(self, fileLike):
        '''
        Assign a file-like object, such as those provided by
        StringIO, as an open file object.

        >>> from io import StringIO
        >>> fileLikeOpen = StringIO()
        '''
        self.file = fileLike  # already 'open'

    def _reprInternal(self):
        return ''

    def close(self):
        self.file.close()

    def read(self, number=None):
        '''
        Read a file. Note that this calls readstr,
        which processes all tokens.

        If `number` is given, a work number will be extracted if possible.
        '''
        return self.readstr(self.file.read(), number)

    @staticmethod
    def extractReferenceNumber(strSrc: str, number: int) -> str:
        '''
        Extract the string data relating to a single reference number
        from a file that defines multiple songs or pieces.

        This method permits loading a single work from a collection/opus
        without parsing the entire file.

        Here is sample data that is not correct ABC but demonstrates the basic concept:

        >>> fileData = """
        ...   X:1
        ...   Hello
        ...   X:2
        ...   Aloha
        ...   X:3
        ...   Goodbye
        ...   """

        >>> file2 = abcFormat.ABCFile.extractReferenceNumber(fileData, 2)
        >>> print(file2)
        X:2
        Aloha

        If the number does not exist, raises an ABCFileException:

        >>> abcFormat.ABCFile.extractReferenceNumber(fileData, 99)
        Traceback (most recent call last):
        music21.abcFormat.ABCFileException: cannot find requested
            reference number in source file: 99


        If the same number is defined twice in one file (should not be) only
        the first data is returned.

        Changed in v6.2: now a static method.
        '''
        collect = []
        gather = False
        for line in strSrc.split('\n'):
            # must be a single line definition
            # rstrip because of '\r\n' carriage returns
            if line.strip().startswith('X:') and line.replace(' ', '').rstrip() == f'X:{number}':
                gather = True
            elif line.strip().startswith('X:') and not gather:
                # some numbers are like X:0490 but we may request them as 490...
                try:
                    forcedNum = int(line.replace(' ', '').rstrip().replace('X:', ''))
                    if forcedNum == int(number):
                        gather = True
                except TypeError:
                    pass
            # if already gathering and find another ref number definition
            # stop gathering
            elif gather and line.strip().startswith('X:'):
                break

            if gather:
                collect.append(line)

        if not collect:
            raise ABCFileException(
                f'cannot find requested reference number in source file: {number}')

        referenceNumbers = '\n'.join(collect)
        return referenceNumbers

    def readstr(self, strSrc: str, number: Optional[int] = None) -> ABCHandler:
        '''
        Read a string and process all Tokens.
        Returns a ABCHandler instance.
        '''
        if number is not None:
            # will raise exception if cannot be found
            strSrc = self.extractReferenceNumber(strSrc, number)

        handler = ABCHandler(abcVersion=self.abcVersion)
        # return the handler instance
        handler.process(strSrc)
        return handler


# ------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def testTokenization(self):
        from music21.abcFormat import testFiles

        for (tf, countTokens, noteTokens, chordTokens) in [
            (testFiles.fyrareprisarn, 241, 152, 0),
            (testFiles.mysteryReel, 192, 153, 0),
            (testFiles.aleIsDear, 291, 206, 32),
            (testFiles.testPrimitive, 100, 75, 2),
            (testFiles.williamAndNancy, 127, 93, 0),
            (testFiles.morrisonsJig, 178, 137, 0),
        ]:

            handler = ABCHandler()
            handler.tokenize(tf)
            tokens = handler.tokens  # get private for testing
            self.assertEqual(len(tokens), countTokens)
            countNotes = 0
            countChords = 0
            for o in tokens:
                if isinstance(o, ABCChord):
                    countChords += 1
                elif isinstance(o, ABCNote):
                    countNotes += 1

            self.assertEqual(countNotes, noteTokens)
            self.assertEqual(countChords, chordTokens)

    def testRe(self):

        src = 'A: this is a test'
        post = reMetadataTag.match(src).end()
        self.assertEqual(src[:post], 'A:')
        self.assertEqual(src[post:], ' this is a test')

        src = 'Q: this is a test % and a following comment'
        post = reMetadataTag.match(src).end()
        self.assertEqual(src[:post], 'Q:')

        # chord symbol matches
        src = 'd|"G"e2d B2d|"C"gfe "D7"d2d|"G"e2d B2d|"A7""C"gfe "D7""D"d2c|'
        post = reChordSymbol.findall(src)
        self.assertEqual(post, ['"G"', '"C"', '"D7"', '"G"', '"A7"',
                                '"C"', '"D7"', '"D"'])

        # get index of last match of many
        i = list(reChordSymbol.finditer(src))[-1].end()

        src = '=d2'
        self.assertEqual(rePitchName.findall(src)[0], 'd')

        src = 'A3/2'
        self.assertEqual(rePitchName.findall(src)[0], 'A')

    def testTokenProcessMetadata(self):
        from music21.abcFormat import testFiles

        # noinspection SpellCheckingInspection
        for (tf, titleEncoded, meterEncoded, keyEncoded) in [
            (testFiles.fyrareprisarn, 'Fyrareprisarn', '3/4', 'F'),
            (testFiles.mysteryReel, 'Mystery Reel', 'C|', 'G'),
            (testFiles.aleIsDear, 'Ale is Dear, The', '4/4', 'D', ),
            (testFiles.kitchGirl, 'Kitchen Girl', '4/4', 'D'),
            (testFiles.williamAndNancy, 'William and Nancy', '6/8', 'G'),
        ]:

            handler = ABCHandler()
            handler.tokenize(tf)
            handler.tokenProcess()

            tokens = handler.tokens  # get private for testing
            for t in tokens:
                if isinstance(t, ABCMetadata):
                    if t.tag == 'T':
                        self.assertEqual(t.data, titleEncoded)
                    elif t.tag == 'M':
                        self.assertEqual(t.data, meterEncoded)
                    elif t.tag == 'K':
                        self.assertEqual(t.data, keyEncoded)

    def testTokenProcess(self):
        from music21.abcFormat import testFiles

        for tf in [
            testFiles.fyrareprisarn,
            testFiles.mysteryReel,
            testFiles.aleIsDear,
            testFiles.testPrimitive,
            testFiles.kitchGirl,
            testFiles.williamAndNancy,
        ]:

            handler = ABCHandler()
            handler.tokenize(tf)
            handler.tokenProcess()

    def testNoteParse(self):
        from music21 import key

        an = ABCNote()

        # with a key signature, matching steps are assumed altered
        an.activeKeySignature = key.KeySignature(3)
        self.assertEqual(an.getPitchName('c'), ('C#5', False))

        an.activeKeySignature = None
        self.assertEqual(an.getPitchName('c'), ('C5', None))
        self.assertEqual(an.getPitchName('^c'), ('C#5', True))

        an.activeKeySignature = key.KeySignature(-3)
        self.assertEqual(an.getPitchName('B'), ('B-4', False))

        an.activeKeySignature = None
        self.assertEqual(an.getPitchName('B'), ('B4', None))
        self.assertEqual(an.getPitchName('_B'), ('B-4', True))

    def testSplitByMeasure(self):

        from music21.abcFormat import testFiles

        ah = ABCHandler()
        ah.process(testFiles.hectorTheHero)
        ahm = ah.splitByMeasure()

        for i, l, r in [(0, None, None),  # meta data
                        (2, '|:', '|'),
                        (3, '|', '|'),
                        (-2, '[1', ':|'),
                        (-1, '[2', '|'),
                        ]:
            # print('expecting', i, l, r, ahm[i].tokens)
            # print('have', ahm[i].leftBarToken, ahm[i].rightBarToken)
            # print()
            if l is None:
                self.assertEqual(ahm[i].leftBarToken, None)
            else:
                self.assertEqual(ahm[i].leftBarToken.src, l)

            if r is None:
                self.assertEqual(ahm[i].rightBarToken, None)
            else:
                self.assertEqual(ahm[i].rightBarToken.src, r)

        # for ahSub in ah.splitByMeasure():
        #     environLocal.printDebug(['split by measure:', ahSub.tokens])
        #     environLocal.printDebug(['leftBar:', ahSub.leftBarToken,
        #        'rightBar:', ahSub.rightBarToken, '\n'])

        ah = ABCHandler()
        ah.process(testFiles.theBeggerBoy)
        ahm = ah.splitByMeasure()

        for i, l, r in [(0, None, None),  # meta data
                        (1, None, '|'),
                        (-1, '||', None),  # trailing lyric meta data
                        ]:
            # print(i, l, r, ahm[i].tokens)
            if l is None:
                self.assertEqual(ahm[i].leftBarToken, None)
            else:
                self.assertEqual(ahm[i].leftBarToken.src, l)

            if r is None:
                self.assertEqual(ahm[i].rightBarToken, None)
            else:
                self.assertEqual(ahm[i].rightBarToken.src, r)

        # test a simple string with no bars
        ah = ABCHandler()
        ah.process('M:6/8\nL:1/8\nK:G\nc1D2')
        ahm = ah.splitByMeasure()

        for i, l, r in [(0, None, None),  # meta data
                        (-1, None, None),  # note data, but no bars
                        ]:
            # print(i, l, r, ahm[i].tokens)
            if l is None:
                self.assertEqual(ahm[i].leftBarToken, None)
            else:
                self.assertEqual(ahm[i].leftBarToken.src, l)

            if r is None:
                self.assertEqual(ahm[i].rightBarToken, None)
            else:
                self.assertEqual(ahm[i].rightBarToken.src, r)

    def testMergeLeadingMetaData(self):
        from music21.abcFormat import testFiles

        # a case of leading and trailing meta data
        ah = ABCHandler()
        ah.process(testFiles.theBeggerBoy)
        ahm = ah.splitByMeasure()

        self.assertEqual(len(ahm), 14)

        mergedHandlers = mergeLeadingMetaData(ahm)

        # after merging, one less handler as leading meta data is merged
        self.assertEqual(len(mergedHandlers), 13)
        # the last handler is all trailing metadata
        self.assertTrue(mergedHandlers[0].hasNotes())
        self.assertFalse(mergedHandlers[-1].hasNotes())
        self.assertTrue(mergedHandlers[-2].hasNotes())
        # these are all ABCHandlerBar instances with bars defined
        self.assertEqual(mergedHandlers[-2].rightBarToken.src, '||')

        # a case of only leading meta data
        ah = ABCHandler()
        ah.process(testFiles.theAleWifesDaughter)
        ahm = ah.splitByMeasure()

        self.assertEqual(len(ahm), 10)

        mergedHandlers = mergeLeadingMetaData(ahm)
        # after merging, one less handler as leading meta data is merged
        self.assertEqual(len(mergedHandlers), 10)
        # all handlers have notes
        self.assertTrue(mergedHandlers[0].hasNotes())
        self.assertTrue(mergedHandlers[-1].hasNotes())
        self.assertTrue(mergedHandlers[-2].hasNotes())
        # these are all ABCHandlerBar instances with bars defined
        self.assertEqual(mergedHandlers[-1].rightBarToken.src, '|]')

        # test a simple string with no bars
        ah = ABCHandler()
        ah.process('M:6/8\nL:1/8\nK:G\nc1D2')
        ahm = ah.splitByMeasure()

        # split by measure divides meta data
        self.assertEqual(len(ahm), 2)
        mergedHandlers = mergeLeadingMetaData(ahm)
        # after merging, meta data is merged back
        self.assertEqual(len(mergedHandlers), 1)
        # and it has notes
        self.assertTrue(mergedHandlers[0].hasNotes())

    def testSplitByReferenceNumber(self):
        from music21.abcFormat import testFiles

        # a case of leading and trailing meta data
        ah = ABCHandler()
        ah.process(testFiles.theBeggerBoy)
        ahs = ah.splitByReferenceNumber()
        self.assertEqual(len(ahs), 1)
        self.assertEqual(list(ahs.keys()), [5])
        self.assertEqual(len(ahs[5]), 88)  # tokens
        self.assertEqual(ahs[5].tokens[0].src, 'X:5')  # first is retained
        # noinspection SpellCheckingInspection
        self.assertEqual(ahs[5].getTitle(), 'The Begger Boy')  # tokens

        ah = ABCHandler()
        ah.process(testFiles.testPrimitivePolyphonic)  # has no reference num
        self.assertEqual(len(ah), 47)  # tokens

        ahs = ah.splitByReferenceNumber()
        self.assertEqual(len(ahs), 1)
        self.assertEqual(list(ahs.keys()), [None])
        self.assertEqual(ahs[None].tokens[0].src, 'M:6/8')  # first is retained
        self.assertEqual(len(ahs[None]), 47)  # tokens

        ah = ABCHandler()
        ah.process(testFiles.valentineJigg)  # has no reference num
        self.assertEqual(len(ah), 244)  # total tokens

        ahs = ah.splitByReferenceNumber()
        self.assertEqual(len(ahs), 3)
        self.assertEqual(sorted(list(ahs.keys())), [166, 167, 168])

        self.assertEqual(ahs[168].tokens[0].src, 'X:168')  # first is retained
        self.assertEqual(ahs[168].getTitle(), '168  The Castle Gate   (HJ)')
        self.assertEqual(len(ahs[168]), 89)  # tokens

        self.assertEqual(ahs[166].tokens[0].src, 'X:166')  # first is retained
        # noinspection SpellCheckingInspection
        self.assertEqual(ahs[166].getTitle(), '166  Valentine Jigg   (Pe)')
        self.assertEqual(len(ahs[166]), 67)  # tokens

        self.assertEqual(ahs[167].tokens[0].src, 'X:167')  # first is retained
        self.assertEqual(ahs[167].getTitle(), '167  The Dublin Jig     (HJ)')
        self.assertEqual(len(ahs[167]), 88)  # tokens

    def testExtractReferenceNumber(self):
        from music21 import corpus
        fp = corpus.getWork('essenFolksong/test0')

        af = ABCFile()
        af.open(fp)
        ah = af.read(5)  # returns a parsed handler
        af.close()
        self.assertEqual(len(ah), 74)

        af = ABCFile()
        af.open(fp)
        ah = af.read(7)  # returns a parsed handler
        af.close()
        self.assertEqual(len(ah), 84)

        fp = corpus.getWork('essenFolksong/han1')
        af = ABCFile()
        af.open(fp)
        ah = af.read(339)  # returns a parsed handler
        af.close()
        self.assertEqual(len(ah), 101)

    def testSlurs(self):
        from music21.abcFormat import testFiles
        ah = ABCHandler()
        ah.process(testFiles.slurTest)
        self.assertEqual(len(ah), 70)  # number of tokens

    def testTies(self):
        from music21.abcFormat import testFiles
        ah = ABCHandler()
        ah.process(testFiles.tieTest)
        self.assertEqual(len(ah), 73)  # number of tokens

    def testCresc(self):
        from music21.abcFormat import testFiles
        ah = ABCHandler()
        ah.process(testFiles.crescTest)
        self.assertEqual(len(ah), 75)
        tokens = ah.tokens
        i = 0
        for t in tokens:
            if isinstance(t, ABCCrescStart):
                i += 1
        self.assertEqual(i, 1)

    def testDim(self):
        from music21.abcFormat import testFiles
        ah = ABCHandler()
        ah.process(testFiles.dimTest)
        self.assertEqual(len(ah), 75)
        tokens = ah.tokens
        i = 0
        for t in tokens:
            if isinstance(t, ABCDimStart):
                i += 1
        self.assertEqual(i, 1)

    def testStaccato(self):
        from music21.abcFormat import testFiles
        ah = ABCHandler()
        ah.process(testFiles.staccTest)
        self.assertEqual(len(ah), 80)

    def testBow(self):
        from music21.abcFormat import testFiles
        ah = ABCHandler()
        ah.process(testFiles.bowTest)
        self.assertEqual(len(ah), 83)
        tokens = ah.tokens
        i = 0
        j = 0
        for t in tokens:
            if isinstance(t, ABCUpbow):
                i += 1
            elif isinstance(t, ABCDownbow):
                j += 1
        self.assertEqual(i, 2)
        self.assertEqual(j, 1)

    def testAcc(self):
        from music21.abcFormat import testFiles
        from music21 import abcFormat
        ah = abcFormat.ABCHandler()
        ah.process(testFiles.accTest)
        # noinspection SpellCheckingInspection
        tokensCorrect = '''<music21.abcFormat.ABCMetadata 'X: 979'>
<music21.abcFormat.ABCMetadata 'T: Staccato test, plus accents and tenuto marks'>
<music21.abcFormat.ABCMetadata 'M: 2/4'>
<music21.abcFormat.ABCMetadata 'L: 1/16'>
<music21.abcFormat.ABCMetadata 'K: Edor'>
<music21.abcFormat.ABCNote 'B,2'>
<music21.abcFormat.ABCBar '|'>
<music21.abcFormat.ABCDimStart '!'>
<music21.abcFormat.ABCStaccato '.'>
<music21.abcFormat.ABCNote 'E'>
<music21.abcFormat.ABCNote '^D'>
<music21.abcFormat.ABCStaccato '.'>
<music21.abcFormat.ABCNote 'E'>
<music21.abcFormat.ABCTie '-'>
<music21.abcFormat.ABCNote 'E'>
<music21.abcFormat.ABCParenStop '!'>
<music21.abcFormat.ABCSlurStart '('>
<music21.abcFormat.ABCTuplet '(3'>
<music21.abcFormat.ABCStaccato '.'>
<music21.abcFormat.ABCNote 'G'>
<music21.abcFormat.ABCStaccato '.'>
<music21.abcFormat.ABCNote 'F'>
<music21.abcFormat.ABCStaccato '.'>
<music21.abcFormat.ABCAccent 'K'>
<music21.abcFormat.ABCNote 'G'>
<music21.abcFormat.ABCParenStop ')'>
<music21.abcFormat.ABCNote 'B'>
<music21.abcFormat.ABCNote 'A'>
<music21.abcFormat.ABCParenStop ')'>
<music21.abcFormat.ABCBar '|'>
<music21.abcFormat.ABCNote 'E'>
<music21.abcFormat.ABCNote '^D'>
<music21.abcFormat.ABCTenuto 'M'>
<music21.abcFormat.ABCNote 'E'>
<music21.abcFormat.ABCNote 'F'>
<music21.abcFormat.ABCTuplet '(3'>
<music21.abcFormat.ABCSlurStart '('>
<music21.abcFormat.ABCNote 'G'>
<music21.abcFormat.ABCTie '-'>
<music21.abcFormat.ABCNote 'G'>
<music21.abcFormat.ABCNote 'G'>
<music21.abcFormat.ABCParenStop ')'>
<music21.abcFormat.ABCParenStop ')'>
<music21.abcFormat.ABCNote 'B'>
<music21.abcFormat.ABCStraccent 'k'>
<music21.abcFormat.ABCTenuto 'M'>
<music21.abcFormat.ABCNote 'A'>
<music21.abcFormat.ABCBar '|'>
<music21.abcFormat.ABCSlurStart '('>
<music21.abcFormat.ABCNote 'E'>
<music21.abcFormat.ABCSlurStart '('>
<music21.abcFormat.ABCNote '^D'>
<music21.abcFormat.ABCNote 'E'>
<music21.abcFormat.ABCParenStop ')'>
<music21.abcFormat.ABCNote 'F'>
<music21.abcFormat.ABCParenStop ')'>
<music21.abcFormat.ABCTuplet '(3'>
<music21.abcFormat.ABCSlurStart '('>
<music21.abcFormat.ABCStraccent 'k'>
<music21.abcFormat.ABCNote 'G'>
<music21.abcFormat.ABCAccent 'K'>
<music21.abcFormat.ABCNote 'F'>
<music21.abcFormat.ABCParenStop ')'>
<music21.abcFormat.ABCNote 'G'>
<music21.abcFormat.ABCParenStop ')'>
<music21.abcFormat.ABCNote 'A'>
<music21.abcFormat.ABCTie '-'>
<music21.abcFormat.ABCNote 'A'>
<music21.abcFormat.ABCBar '|'>
<music21.abcFormat.ABCSlurStart '('>
<music21.abcFormat.ABCNote 'E'>
<music21.abcFormat.ABCNote '^D'>
<music21.abcFormat.ABCNote 'E'>
<music21.abcFormat.ABCNote 'F'>
<music21.abcFormat.ABCTuplet '(3'>
<music21.abcFormat.ABCSlurStart '('>
<music21.abcFormat.ABCNote 'G'>
<music21.abcFormat.ABCNote 'F'>
<music21.abcFormat.ABCNote 'G'>
<music21.abcFormat.ABCParenStop ')'>
<music21.abcFormat.ABCParenStop ')'>
<music21.abcFormat.ABCParenStop ')'>
<music21.abcFormat.ABCNote 'B'>
<music21.abcFormat.ABCNote 'A'>
<music21.abcFormat.ABCBar '|'>
<music21.abcFormat.ABCNote 'G6'>
'''.splitlines()
        tokensReceived = [str(x) for x in ah.tokens]
        self.assertEqual(tokensCorrect, tokensReceived)

        self.assertEqual(len(ah), 86)
        tokens = ah.tokens
        i = 0
        j = 0
        k = 0
        for t in tokens:
            if isinstance(t, abcFormat.ABCAccent):
                i += 1
            elif isinstance(t, abcFormat.ABCStraccent):
                j += 1
            elif isinstance(t, abcFormat.ABCTenuto):
                k += 1
        self.assertEqual(i, 2)
        self.assertEqual(j, 2)
        self.assertEqual(k, 2)

    def testGrace(self):
        from music21.abcFormat import testFiles
        ah = ABCHandler()
        ah.process(testFiles.graceTest)
        self.assertEqual(len(ah), 85)

    def testGuineaPig(self):
        from music21.abcFormat import testFiles
        ah = ABCHandler()
        ah.process(testFiles.guineapigTest)
        self.assertEqual(len(ah), 105)


# ------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [ABCFile, ABCHandler, ABCHandlerBar]


if __name__ == '__main__':
    # sys.arg test options will be used in mainTest()
    import music21
    music21.mainTest(Test)
