# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         clercqTemperley.py
# Purpose:      Routines to parse the popular music
#               Roman Numeral encoding system used by Clercq-Temperley
#
# Authors:      Beth Hadley
#               Michael Scott Asato Cuthbert
#
# Copyright:    Copyright © 2011-12, 2015 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
Parses the de Clercq-Temperley popular music flavor of RomanText.
The Clercq-Temperley file format and additional rock corpus analysis
information may be located at http://rockcorpus.midside.com
'''
from __future__ import annotations

import copy
import io
import pathlib
import re
import typing as t
import unittest

from collections import OrderedDict

from music21 import common
from music21 import environment
from music21 import exceptions21
from music21 import key
from music21 import metadata
from music21 import meter
from music21 import note
from music21 import prebase
from music21 import roman
from music21 import stream
from music21 import tie

if t.TYPE_CHECKING:
    from music21 import chord

environLocal = environment.Environment('romanText.clercqTemperley')

# clercqTemperley test files used as tests throughout this module
BlitzkriegBopCT = '''
% Blitzkrieg Bop

BP: I | IV V | %THIS IS A COMMENT
In: $BP*3 I IV | I | $BP*3 I IV | I | R |*4 I |*4
Vr: $BP*3 I IV | I |
Br: IV | | I | IV I | IV | | ii | IV V |
Co: R |*4 I |*4
S: [A] $In $Vr $Vr $Br $Vr $Vr $Br $Vr $Vr $Co
'''

RockClockCT = '''
% Rock Around the Clock
% just a general comment
In: I | | | | | | V | |
Vr: I | | | | IVd7 | | I | | V7 | | I | | %a comment on verse
Vrf: I | | | | IVd7 | | I | | V7 | | I | IV iv | V | . I |
S: [A] $In $Vr $Vr $Vr $Vr $Vr $Vr $Vrf    % 3rd and 6th verses are instrumental
'''
textString = '''
% Simple Gifts
% A wonderful shaker melody
Vr: I | I | %incomplete verse
S: [A] $Vr % Not quite finished!'''

changeIsGonnaCome = r'''
% A Change is Gonna Come
Vr: I | | ii7 | vi | I | ii7 . IV V/vi | vi | I |
Br: ii7 | I | ii7 | vi | ii7 | vi | V7/V | V7 |
In: I V6 vi I64 | ii65 V43/ii ii vi6 | bVIId7 . VId7 . | V |
S: [Bb] [12/8] $In $Vr $Vr $Vr $Br $Vr I |
'''

exampleClercqTemperley = '''
% Brown-Eyed Girl

VP: I | IV | I | V |
In: $VP*2
Vr: $VP*4 IV | V | I | vi | IV | V | I | V |       % Second half could be called chorus
Ch: V | | $VP*2 I |*4
Ch2: V | | $VP*3     % Fadeout
S: [G] $In $Vr $Vr $Ch $VP $Vr $Ch2
'''
RingFireCT = ('''
% Ring Of Fire

In: [3/4] I . IV | [4/4] I | [3/4] . . V7 | [4/4] I |
Vr: I . . IV | [3/4] I . IV | [4/4] I | . . . V | [3/4] I . V | [4/4] I | '''
              + 'I . . IV | [3/4] I . IV | [4/4] I | [3/4] . . V | [4/4] I |\n'
              + 'Vr2: I . . IV | [3/4] I . IV | [4/4] I | . . . V | [3/4] I . V | '
              + '[4/4] I | I . IV I | . . . IV | I | . . . V | I | % Or (alternate barring) '
              + '| [3/4] I . IV | [2/4] I | [3/4] . . IV | [4/4] I | . . . V | I |\n'
              + 'Ch: V | IV I | V | IV I | [2/4] | [4/4] . . . V | I . . V | I |       '
              + '''% Or the 2/4 measure could be one measure later
Fadeout: I . . V | I . . V | I . . V |
Co: [2/4] I | [4/4] . . . V | I . . V | $Fadeout
S: [G] $In $Vr $Ch $In*2 $Ch $Vr2 $Ch $Ch $Co
''')


class CTSongException(exceptions21.Music21Exception):
    pass


class CTSong(prebase.ProtoM21Object):
    # noinspection PyShadowingNames
    r"""
    This parser is an object-oriented approach to parsing clercqTemperley text files into music.
    It is an advanced method.  Most people should just run:

    >>> #_DOCS_SHOW p = converter.parse('clercqTemperley/dt/BrownEyedGirl.cttxt')

    or if the file ends in .txt then give the format explicitly as either 'clerqTemperley'
    or 'cttxt':

    >>> #_DOCS_SHOW p = converter.parse('BrownEyedGirl.txt', format='clercqTemperley')

    Advanced: if you want access to a CTSong object itself (for manipulating the input before
    converting to a string, etc. then create a CTSong object with one of the following inputs:

    1. by passing in the string, with newline characters (\\n) at the end of each line

    2. by passing in the filename as a string or path, and have Python
       open the file and read the text

    Given this file, you could create a CTSong object with:

    >>> exampleClercqTemperley = '''
    ... % Brown-Eyed Girl
    ... VP: I | IV | I | V |
    ... In: $VP*2
    ... Vr: $VP*4 IV | V | I | vi | IV | V | I | V | % Second half could be called chorus
    ... Ch: V | | $VP*2 I |*4
    ... Ch2: V | | $VP*3     % Fadeout
    ... S: [G] $In $Vr $Vr $Ch $VP $Vr $Ch2
    ... '''

    >>> exCT = romanText.clercqTemperley.exampleClercqTemperley  #_DOCS_HIDE
    >>> s = romanText.clercqTemperley.CTSong(exCT)  #_DOCS_HIDE

    Or:

    >>> #_DOCS_SHOW s = romanText.clercqTemperley.CTSong('C:/Brown-Eyed_Girl.txt')

    When you call the .toPart() method on the newly created CTSong object,
    the code extracts meaningful properties (such as title, text, comments,
    year, rules, home time Signature, and home Key Signature) from the text file
    and returns a new Part object.  It also makes these properties available on the
    CTSong object.

    The toPart() method has two optional labeling parameters, labelRomanNumerals and
    labelSubsectionsOnScore. Both are set to True by default. Thus, the created score
    will have labels (on the chord's lyric) for each roman numeral as well as for each
    section in the song (LHS). In case of a recursive definition (a rule contains a reference
    to another rule), both labels are printed, with the deepest
    reference on the smallest lyric line.

    >>> p = s.toPart()
    >>> #_DOCS_SHOW p.show()

    .. image:: images/ClercqTemperleyExbrown-eyed_girl.png
       :width: 500

    >>> firstRN = p[roman.RomanNumeral][0]
    >>> firstRN.lyric
    'I\nVP\nIn'

    All roman numerals mark which formal division they are in:

    >>> 'formalDivision' in firstRN.editorial
    True
    >>> firstRN.editorial.formalDivision
    ['VP', 'In']

    The second RomanNumeral is at the start of no formal divisions

    >>> secondRN = p[roman.RomanNumeral][1]
    >>> secondRN.lyric
    'IV'
    >>> secondRN.editorial.formalDivision
    []

    >>> s.title
    'Brown-Eyed Girl'

    >>> s.homeTimeSig
    <music21.meter.TimeSignature 4/4>

    >>> s.homeKey
    <music21.key.Key of G major>

    >>> s.comments
    [['Vr:', 'Second half could be called chorus'], ['Ch2:', 'Fadeout']]

    Year is not defined as part of the Clercq-Temperley format, but it will be helpful
    to have it as a property. So let's assign a year to this song:

    >>> s.year = 1967
    >>> s.year
    1967

    Upon calling toPart(), CTRule objects are also created. CTRule objects are
    the individual rules that make up the song object. For example,

    >>> s.rules
    OrderedDict([('VP', <music21.romanText.clercqTemperley.CTRule
                         text='VP: I | IV | I | V |'>),
                 ('In', <music21.romanText.clercqTemperley.CTRule text='In: $VP*2'>),
                 ('Vr', <music21.romanText.clercqTemperley.CTRule
                         text='Vr: $VP*4 IV | V | I | vi | IV | V | I | V |
                                     % Second half could be called chorus'>),
                 ('Ch', <music21.romanText.clercqTemperley.CTRule
                         text='Ch: V | | $VP*2 I |*4'>),
                 ('Ch2', <music21.romanText.clercqTemperley.CTRule
                         text='Ch2: V | | $VP*3     % Fadeout'>),
                 ('S', <music21.romanText.clercqTemperley.CTRule
                         text='S: [G] $In $Vr $Vr $Ch $VP $Vr $Ch2'>)])

    The parser extracts meaningful properties to each rule, such as sectionName,
    home time signature of that rule, home key of that rule, and of course the individual
    stream from the song corresponding to the rule.

    The following examples display the instantiated properties of the second rule (list indexes
    start at one) as created above.

    >>> rule = s.rules['In']
    >>> rule.text
    'In: $VP*2'

    >>> rule.sectionName
    'Introduction'


    With this object-oriented approach to parsing the clercq-temperley text file format,
    we now have the ability to analyze a large corpus (200 files) of popular music
    using the full suite of harmonic tools of music21. We can not only analyze each
    song as a whole, as presented in Clercq and Temperley's research, but we can also analyze each
    individual section (or rule) of a song. This may provide interesting insight
    into popular music beyond our current understanding.

    Examples used throughout this class utilize the following Clercq-Temperley text file

    >>> BlitzkriegBopCT = '''
    ... % Blitzkrieg Bop
    ... BP: I | IV V | %THIS IS A COMMENT
    ... In: $BP*3 I IV | I | $BP*3 I IV | I | R |*4 I |*4
    ... Vr: $BP*3 I IV | I |
    ... Br: IV | | I | IV I | IV | | ii | IV V |
    ... Co: R |*4 I |*4
    ... S: [A] $In $Vr $Vr $Br $Vr $Vr $Br $Vr $Vr $Co
    ... '''

    Another example using a different Clercq-Temperley file

    RockClockCT =
    % Rock Around the Clock
    % just a general comment
    In: I | | | | | | V | |
    Vr: I | | | | IVd7 | | I | | V7 | | I | | %a comment on verse
    Vrf: I | | | | IVd7 | | I | | V7 | | I | IV iv | V | . I |
    S: [A] $In $Vr $Vr $Vr $Vr $Vr $Vr $Vrf    % 3rd and 6th verses are instrumental

    >>> s = romanText.clercqTemperley.CTSong(romanText.clercqTemperley.RockClockCT)
    >>> part = s.toPart()
    >>> part.highestTime
    376.0

    >>> s.title
    'Rock Around the Clock'

    >>> s.homeTimeSig
    <music21.meter.TimeSignature 4/4>

    >>> s.homeKey
    <music21.key.Key of A major>

    >>> s.comments
    [['just a general comment'],
     ['Vr:', 'a comment on verse'],
     ['S:', '3rd and 6th verses are instrumental']]

    >>> s.year = 1952
    >>> s.year
    1952

    >>> s.rules
    OrderedDict([('In', <music21.romanText.clercqTemperley.CTRule
                            text='In: I | | | | | | V | |'>),
                 ('Vr', <music21.romanText.clercqTemperley.CTRule
                         text='Vr: I | | | | IVd7 | | I | | V7 | | I | | %a comment on verse'>),
                 ('Vrf', <music21.romanText.clercqTemperley.CTRule
                         text='Vrf: I | | | | IVd7 | | I | | V7 | | I | IV iv | V | . I |'>),
                 ('S', <music21.romanText.clercqTemperley.CTRule
                         text='S: [A] $In $Vr $Vr $Vr $Vr $Vr $Vr $Vrf
                                     % 3rd and 6th verses are instrumental'>)])


    >>> rule = s.rules['In']
    >>> rule.text
    'In: I | | | | | | V | |'

    >>> rule.sectionName
    'Introduction'

    OMIT_FROM_DOCS

    one more example...the bane of this parser's existence...::

        % Ring Of Fire

        In: [3/4] I . IV | [4/4] I | [3/4] . . V7 | [4/4] I |
        Vr: I . . IV | [3/4] I . IV | [4/4] I | . . . V | [3/4] I . V | [4/4] I |
                    I . . IV | [3/4] I . IV | [4/4] I | [3/4] . . V | [4/4] I |
        Vr2: I . . IV | [3/4] I . IV | [4/4] I | . . . V | [3/4] I . V | [4/4] I |
                    I . IV I | . . . IV | I | . . . V | I |
                    % Or (alternate barring) | [3/4] I . IV | [2/4] I |
                    [3/4] . . IV | [4/4] I | . . . V | I |
        Ch: V | IV I | V | IV I | [2/4] | [4/4] . . . V |
                    I . . V | I |       % Or the 2/4 measure could be one measure later
        Fadeout: I . . V | I . . V | I . . V |
        Co: [2/4] I | [4/4] . . . V | I . . V | $Fadeout
        S: [G] $In $Vr $Ch $In*2 $Ch $Vr2 $Ch $Ch $Co


    """
    _DOC_ORDER = ['text', 'toPart', 'title', 'homeTimeSig', 'homeKey', 'comments', 'rules']
    _DOC_ATTR: dict[str, str] = {
        'year': '''
            The year of the CTSong; not formally defined
            by the Clercq-Temperley format.
            ''',
    }

    def __init__(self, textFile: str | pathlib.Path = '', **keywords):
        self._title = None
        self.text = ''
        self.lines: list[str] = []
        # Dictionary of all component rules of the type CTRule
        self._rules: dict[str, CTRule] = OrderedDict()
        # keeps a list of all keys in the Score -- avoids duplicates
        self.keyObjList: list[key.Key] = []
        # same for time signatures
        self.tsList: list[meter.TimeSignature] = []

        self._partObj = stream.Part()
        self.year = None

        self._homeTimeSig = None
        self._homeKey = None

        self.labelRomanNumerals = True
        self.labelSubsectionsOnScore = True

        for kw in keywords:
            if kw == 'title':
                self._title = kw
            if kw == 'year':
                self.year = kw

        self.parse(textFile)

    def _reprInternal(self):
        return f'title={self.title!r} year={self.year}'

    # --------------------------------------------------------------------------
    def parse(self, textFile: str | pathlib.Path):
        '''
        Called when a CTSong is created by passing a string or filename;
        in the second case, it opens the file
        and removes all blank lines, and adds in new line characters
        returns pieceString that CTSong can call .expand() on.

        >>> exCT = romanText.clercqTemperley.exampleClercqTemperley

        This calls parse implicitly:

        >>> s = romanText.clercqTemperley.CTSong(exCT)

        >>> print(s.text)
        % Brown-Eyed Girl
        VP: I | IV | I | V |
        In: $VP*2
        Vr: $VP*4 IV | V | I | vi | IV | V | I | V |       % Second half could be called chorus
        Ch: V | | $VP*2 I |*4
        Ch2: V | | $VP*3     % Fadeout
        S: [G] $In $Vr $Vr $Ch $VP $Vr $Ch2

        >>> s.lines[0]
        '% Brown-Eyed Girl'

        >>> s.lines[-1]
        'S: [G] $In $Vr $Vr $Ch $VP $Vr $Ch2'
        '''
        if isinstance(textFile, str) and '|' in textFile and 'S:' in textFile:
            lines = textFile.split('\n')
        else:
            try:
                with io.open(textFile, 'r', encoding='utf-8', errors='replace') as fileOpened:
                    lines = fileOpened.readlines()
            except FileNotFoundError:
                raise CTSongException(f'Cannot find file: {textFile}')
            except Exception:
                raise CTSongException(
                    f'Invalid File Format; must be string or text file: {textFile}')

        lines = [e for e in lines if len(e) != 0]
        for i in range(len(lines)):
            lines[i] = lines[i].strip()
        self.lines = lines
        pieceString = '\n'.join(lines)

        self.text = pieceString

    @property
    def title(self):
        '''
        Get or set the title of the CTSong. If not specified
        explicitly but the clercq-Temperley text exists,
        this attribute searches first few lines of text file for title (a string preceded by a '%')
        if found, sets title attribute to this string and returns this title)

        >>> s = romanText.clercqTemperley.CTSong(romanText.clercqTemperley.textString)
        >>> s.title
        'Simple Gifts'
        '''
        if self._title not in (None, ''):
            return self._title

        line = self.lines[0]
        title = line.replace('%', '').strip()
        self._title = title
        return title

    @property
    def comments(self):
        r"""
        Get the comments list of all CTRule objects.

        comments are stored as a list of comments, each comment on a line as a list. If the
        comment is on a rule line, the list contains both the line's LHS (like "In:")
        and the comment if the comment is on a line of its own, only the comment is
        appended as a list of length one.

        The title is not a comment. The title is stored under self.title

        #_DOCS_HIDE Please note: the backslashes included in the file
        #_DOCS_HIDE below are for sphinx documentation
        #_DOCS_HIDE purposes only. They are not permitted in the clercq-temperley file format

            | textString = '''
            | %Simple Gifts
            | % A wonderful shaker melody
            | Vr: I \| I \| %incomplete verse
            | S: [A] $Vr % Not quite finished!'''

        >>> s = romanText.clercqTemperley.CTSong(romanText.clercqTemperley.textString)
        >>> s
        <music21.romanText.clercqTemperley.CTSong title='Simple Gifts' year=None>
        >>> s.comments
        [['A wonderful shaker melody'], ['Vr:', 'incomplete verse'], ['S:', 'Not quite finished!']]
        """
        comments = []
        for line in self.lines[1:]:
            if '%' in line:
                if line.split()[0].endswith(':'):
                    comments.append([line.split()[0],
                                     (line[line.index('%') + 1:].strip())])
                else:
                    comments.append([line[line.index('%') + 1:].strip()])
        return comments

    @property
    def rules(self):
        # noinspection PyShadowingNames
        '''
        Get the rules of a CTSong. the Rules is an OrderedDict of
        objects of type CTRule. If only a text file
        provided, this goes through text file and creates the
        rule object out of each line containing
        an LHS including the Song line, which should always be last.

        >>> s = romanText.clercqTemperley.CTSong(romanText.clercqTemperley.BlitzkriegBopCT)
        >>> len(s.rules)
        6
        >>> for rule in s.rules:
        ...   (rule, s.rules[rule])
        ('BP', <music21.romanText.clercqTemperley.CTRule
                    text='BP: I | IV V | %THIS IS A COMMENT'>)
        ('In', <music21.romanText.clercqTemperley.CTRule
                    text='In: $BP*3 I IV | I | $BP*3 I IV | I | R |*4 I |*4'>)
        ('Vr', <music21.romanText.clercqTemperley.CTRule
                    text='Vr: $BP*3 I IV | I |'>)
        ('Br', <music21.romanText.clercqTemperley.CTRule
                    text='Br: IV | | I | IV I | IV | | ii | IV V |'>)
        ('Co', <music21.romanText.clercqTemperley.CTRule
                    text='Co: R |*4 I |*4'>)
        ('S', <music21.romanText.clercqTemperley.CTRule
                    text='S: [A] $In $Vr $Vr $Br $Vr $Vr $Br $Vr $Vr $Co'>)

        Rules S is where we begin:

        >>> s.rules['S']
        <music21.romanText.clercqTemperley.CTRule
            text='S: [A] $In $Vr $Vr $Br $Vr $Vr $Br $Vr $Vr $Co'>
        '''
        if self._rules:
            return self._rules

        for line in self.lines:
            ls = line.split()
            if ls and ls[0].endswith(':'):
                rule = CTRule(line, parent=self)
                self._rules[rule.LHS] = rule

        return self._rules

    @property
    def homeTimeSig(self):
        r'''
        gets the initial, or 'home', time signature in a song by looking at the 'S' substring
        and returning the provided time signature. If not present, returns a default music21
        time signature of 4/4

        >>> s = romanText.clercqTemperley.CTSong(romanText.clercqTemperley.textString)
        >>> s.homeTimeSig
        <music21.meter.TimeSignature 4/4>

        >>> change = romanText.clercqTemperley.CTSong(romanText.clercqTemperley.changeIsGonnaCome)
        >>> change.homeTimeSig
        <music21.meter.TimeSignature 12/8>
        >>> change.homeTimeSig.beatSequence
        <music21.meter.core.MeterSequence {{1/8+1/8+1/8}+{1/8+1/8+1/8}+{1/8+1/8+1/8}+{1/8+1/8+1/8}}>
        '''
        if self._homeTimeSig:
            return self._homeTimeSig

        # look at 'S' Rule and grab the home time Signature
        if self.text and 'S:' in self.text:
            lines = self.text.split('\n')
            for line in lines:
                if line.startswith('S:'):
                    for atom in line.split()[1:3]:
                        if '[' not in atom:
                            self._homeTimeSig = meter.TimeSignature('4/4')
                            return self._homeTimeSig
                        elif '/' in atom:
                            self._homeTimeSig = meter.TimeSignature(atom[1:-1])
                            return self._homeTimeSig
                        else:
                            pass
        return self._homeTimeSig

    @property
    def homeKey(self):
        '''
        gets the initial, or 'home', Key by looking at the music text and locating
        the key signature at the start of the S: rule.

        >>> s = romanText.clercqTemperley.CTSong(romanText.clercqTemperley.textString)
        >>> s.homeKey
        <music21.key.Key of A major>
        '''
        if self._homeKey:
            return self._homeKey

        # look at 'S' Rule and grab the home key
        if self.text and 'S:' in self.text:
            lines = self.text.split('\n')
            for line in lines:
                if line.startswith('S:'):
                    for atom in line.split()[1:3]:
                        if '[' not in atom:
                            self._homeKey = key.Key('C')
                            return self._homeKey
                        elif '/' not in atom:
                            m21keyStr = key.convertKeyStringToMusic21KeyString(atom[1:-1])
                            self._homeKey = key.Key(m21keyStr)
                            return self._homeKey
                        else:
                            pass
        return self._homeKey

    def toPart(self, labelRomanNumerals=True, labelSubsectionsOnScore=True) -> stream.Part:
        # noinspection PyShadowingNames
        '''
        creates a Part object out of a from CTSong...also creates CTRule objects in the process,
        filling their .streamFromCTSong attribute with the corresponding smaller inner stream.
        Individual attributes of a rule are defined by the entire CTSong, such as
        meter and time signature, so creation of CTRule objects typically occurs
        only from this method and directly from the clercqTemperley text.

        >>> s = romanText.clercqTemperley.CTSong(romanText.clercqTemperley.BlitzkriegBopCT)
        >>> partObj = s.toPart()
        >>> partObj.highestOffset
        380.0
        '''
        self.labelRomanNumerals = labelRomanNumerals
        self.labelSubsectionsOnScore = labelSubsectionsOnScore
        if self._partObj[stream.Measure].first():
            return self._partObj
        partObj = stream.Part()
        startRule = self.rules['S']
        measures = startRule.expand()
        for i, m in enumerate(measures):
            m.number = i + 1
        partObj.append(measures)

        partObj.insert(0, metadata.Metadata())
        partObj.metadata.title = self.title

        self._partObj = partObj
        return partObj

    def toScore(self, labelRomanNumerals=True, labelSubsectionsOnScore=True) -> stream.Part:
        '''
        DEPRECATED: use .toPart() instead.  This method will be removed in v.10
        '''
        return self.toPart(labelRomanNumerals=labelRomanNumerals,
                           labelSubsectionsOnScore=labelSubsectionsOnScore)

class CTRuleException(exceptions21.Music21Exception):
    pass


class CTRule(prebase.ProtoM21Object):
    '''
    CTRule objects correspond to the individual lines defined in a
    :class:`~music21.romanText.clercqTemperley.CTSong` object. They are typically
    created by the parser after a CTSong object has been created and the .toPart() method
    has been called on that object. The usefulness of each CTRule object is that each
    has a :meth:`~music21.romanText.clercqTemperley.CTRUle.streamFromCTSong` attribute,
    which is the stream from the entire score that the rule corresponds to.

    To parse, put the text into the
    '''
    _DOC_ORDER = ['LHS', 'sectionName', 'musicText', 'homeTimeSig', 'homeKey', 'comments']
    _DOC_ATTR: dict[str, str] = {
        'text': '''
            The full text of the CTRule, including the LHS, chords, and comments.''',
    }

    SPLITMEASURES = re.compile(r'(\|\*?\d*)')
    REPETITION = re.compile(r'\*(\d+)')

    def __init__(self, text='', parent: CTSong | None = None):
        self._parent = None
        if parent is not None:
            self.parent = parent

        self.ts = (self.parent.homeTimeSig if self.parent else None) or meter.TimeSignature('4/4')
        self.keyObj = (self.parent.homeKey if self.parent else None) or key.Key('C')

        self.text = text  # full text of CTRule input (includes LHS, chords, and comments)
        self._musicText = ''  # just the text above without the rule string or comments
        self._LHS = ''  # left hand side: rule name string, such as "In"

        self.measures: list[stream.Measure] = []
        self.lastRegularAtom: str = ''
        self.lastChord: chord.Chord | None = None
        self._lastChordIsInSameMeasure: bool = False


    def _reprInternal(self):
        return f'text={self.text!r}'

    # --------------------------------------------------------------------------
    def _getParent(self):
        return common.unwrapWeakref(self._parent)

    def _setParent(self, parent):
        self._parent = common.wrapWeakref(parent)

    parent = property(_getParent, _setParent, doc=r'''
    A reference to the CTSong object housing the CTRule if any.
    ''')
    # --------------------------------------------------------------------------

    def expand(
        self,
        tsContext: meter.TimeSignature | None = None,
        keyContext: key.Key | None = None,
    ) -> list[stream.Measure]:
        '''
        The meat of it all -- expand one rule completely and return a list of Measure objects.

        Parses within the local time signature context and key context.
        '''
        saveTs = self.ts
        saveKey = self.keyObj

        if tsContext:
            self.ts = tsContext
        if keyContext:
            self.keyObj = keyContext

        self.measures.clear()

        for content, sep, numReps in self._measureGroups():
            if sep == '$':
                self.expandExpansionContent(content, numReps)
            elif sep == '|':
                self.expandSimpleContent(content, numReps)
            else:
                environLocal.warn(
                    f'Rule found without | or $, ignoring: {content!r},{sep!r}: in {self.text!r}')
                # pass
        if self.measures:
            for m in self.measures:
                noteIter = m.recurse().notes
                if (noteIter
                        and (self.parent is None
                             or self.parent.labelSubsectionsOnScore is True)
                        and self.LHS != 'S'):
                    rn = noteIter[0]
                    lyricNum = len(rn.lyrics) + 1
                    rn.lyrics.append(note.Lyric(self.LHS, number=lyricNum))
                    rn.editorial.formalDivision.append(self.LHS)
                    break

        self.ts = saveTs
        self.keyObj = saveKey

        return self.measures

    def expandExpansionContent(
        self,
        content: str,
        numReps: int,
    ) -> None:
        '''
        Expand a rule that contains an expansion (i.e., a $) in it.

        Requires CTSong parent to be set.
        '''
        if not self.parent or content not in self.parent.rules:
            raise CTRuleException(f'Cannot expand rule {content} in {self}')
        rule = self.parent.rules[content]
        for i in range(numReps):
            returnedMeasures = rule.expand(self.ts, self.keyObj)
            self.insertKsTs(returnedMeasures[0], self.ts, self.keyObj)
            for returnedTs in [m.getElementsByClass(meter.TimeSignature)
                               for m in returnedMeasures]:
                if returnedTs is not self.ts:
                    # the TS changed mid-rule; create a new one for return.
                    self.ts = copy.deepcopy(self.ts)

            self.measures.extend(returnedMeasures)

    def expandSimpleContent(
        self,
        content: str,
        numReps: int,
    ) -> None:
        lastChordIsInSameMeasure = False

        m = stream.Measure()
        atoms = content.split()
        # key/timeSig pass...
        regularAtoms: list[str] = []
        for atom in atoms:
            if atom.startswith('['):
                atomContent = atom[1:-1]
                if atomContent == '0':
                    self.ts = meter.TimeSignature('4/4')
                    # irregular meter.  Cannot fully represent;
                    # TODO: replace w/ senza misura when possible.

                elif '/' in atomContent:  # only one key / ts per measure.
                    self.ts = meter.TimeSignature(atomContent)
                else:
                    self.keyObj = key.Key(key.convertKeyStringToMusic21KeyString(atomContent))

            elif atom == '.':
                if not self.lastRegularAtom:
                    raise CTRuleException(f' . w/o previous atom: {self}')
                regularAtoms.append(self.lastRegularAtom)
            elif not atom:
                pass
            else:
                regularAtoms.append(atom)
                self.lastRegularAtom = atom
        numAtoms = len(regularAtoms)
        if numAtoms == 0:
            return  # maybe just ts and keyObj setting

        self.insertKsTs(m, self.ts, self.keyObj)

        atomLength = common.opFrac(self.ts.barDuration.quarterLength / numAtoms)
        for atom in regularAtoms:
            if atom == 'R':
                rest = note.Rest(quarterLength=atomLength)
                rest.editorial.formalDivision = []
                self.lastChord = None
                lastChordIsInSameMeasure = False
                m.append(rest)
            else:
                atom = self.fixupChordAtom(atom)
                rn = roman.RomanNumeral(atom, self.keyObj)
                rn.editorial.formalDivision = []
                if self.isSame(rn, self.lastChord) and lastChordIsInSameMeasure:
                    if t.TYPE_CHECKING:
                        assert self.lastChord is not None  # isSame asserted this.
                    self.lastChord.duration.quarterLength += atomLength
                    m.coreElementsChanged()
                else:
                    rn.duration.quarterLength = atomLength
                    self.addOptionalTieAndLyrics(rn, self.lastChord)
                    self.lastChord = rn
                    lastChordIsInSameMeasure = True
                    m.append(rn)
        self.measures.append(m)
        for i in range(1, numReps):
            newM = copy.deepcopy(m)
            newM.removeByClass([meter.TimeSignature, key.Key])
            self.measures.append(newM)

    def _measureGroups(self) -> list[tuple[str, str, int]]:
        '''
        Returns a list of 3-tuples where each tuple consists of the
        str content, either "|" (a normal measure ) or "$" (an expansion),
        and the number of repetitions.  Comments are stripped.

        >>> rs = ('In: [A] [4/4] $Vr $BP*3 I IV | I | ' +
        ...          '$BP*3 I IV | I | | R |*4 I |*4 % This is a comment')
        >>> s = romanText.clercqTemperley.CTRule(rs)
        >>> s._measureGroups()
        [('[A] [4/4]', '|', 1),
         ('Vr', '$', 1), ('BP', '$', 3), ('I IV', '|', 1), ('I', '|', 1),
         ('BP', '$', 3), ('I IV', '|', 1), ('I', '|', 1), ('.', '|', 1),
         ('R', '|', 4), ('I', '|', 4)]

        >>> r = romanText.clercqTemperley.CTRule('In: $IP*3 I | | | $BP*2')
        >>> r._measureGroups()
        [('IP', '$', 3), ('I', '|', 1), ('.', '|', 1), ('.', '|', 1), ('BP', '$', 2)]

        >>> r = romanText.clercqTemperley.CTRule('In: [4/4] I V | | | IV |')
        >>> r._measureGroups()
        [('[4/4] I V', '|', 1), ('.', '|', 1), ('.', '|', 1), ('IV', '|', 1)]
        >>> measures = r.expand()
        >>> measures[2].show('text')
        {0.0} <music21.key.Key of C major>
        {0.0} <music21.meter.TimeSignature 4/4>
        {0.0} <music21.roman.RomanNumeral V in C major>

        >>> r = romanText.clercqTemperley.CTRule('Vr: [4/4] bVII | IV | | [2/4] |')
        >>> r._measureGroups()
        [('[4/4] bVII', '|', 1), ('IV', '|', 1), ('.', '|', 1), ('[2/4] .', '|', 1)]
        >>> measures = r.expand()
        >>> measures[2].show('text')
        {0.0} <music21.key.Key of C major>
        {0.0} <music21.meter.TimeSignature 4/4>
        {0.0} <music21.roman.RomanNumeral IV in C major>
        >>> measures[3].show('text')
        {0.0} <music21.key.Key of C major>
        {0.0} <music21.meter.TimeSignature 2/4>
        {0.0} <music21.roman.RomanNumeral IV in C major>
        >>> measures[3][-1].quarterLength
        2.0
        '''
        measureGroups1: list[tuple[str, str]] = []
        measureGroups2: list[tuple[str, str, int]] = []
        measureGroups3: list[tuple[str, str, int]] = []
        measureGroupTemp: list[str] = self.SPLITMEASURES.split(self.musicText)
        # first pass -- separate by | or |*3, etc.
        for i in range(0, len(measureGroupTemp), 2):
            content = measureGroupTemp[i].strip()
            if i + 1 < len(measureGroupTemp):
                sep = measureGroupTemp[i + 1]
            else:
                sep = ''
            if content != '' or sep != '':
                measureGroups1.append((content, sep))
        # second pass -- filter out expansions.
        for content, sep in measureGroups1:
            contentList = content.split()
            contentOut: list[str] = []

            for atom in contentList:
                if atom.startswith('$'):  # $BP or $Vr*3, etc.
                    if contentOut:  # clear existing content
                        measureGroups2.append((' '.join(contentOut), '?', 1))
                        contentOut = []

                    repetitions = self.REPETITION.search(atom)
                    if repetitions is not None:
                        expandReps = int(repetitions.group(1))
                        atom = self.REPETITION.sub('', atom)
                    else:
                        expandReps = 1
                    measureGroups2.append((atom[1:], '$', expandReps))
                else:
                    contentOut.append(atom)

            # normally get repetitions from |*3 info
            repetitions = self.REPETITION.search(sep)
            if repetitions is not None:
                numReps = int(repetitions.group(1))
                sep = self.REPETITION.sub('', sep)
            else:
                numReps = 1

            if contentOut or sep == '|':
                measureGroups2.append((' '.join(contentOut), sep, numReps))

        # third pass, make empty content duplicate previous content.
        for content, sep, numReps in measureGroups2:
            contentSplit = content.split()
            if sep == '|' and all(y.startswith('[') or y == '' for y in contentSplit):
                content = ' '.join(contentSplit)
                if content:
                    content += ' '
                content += '.'
            elif sep == '?':  # implied continuation
                sep = '|'
            measureGroups3.append((content, sep, numReps))

        return measureGroups3

    # --------------------------------------------------------------------------
    def isSame(self, rn: roman.RomanNumeral, lastChord: chord.Chord | None) -> bool:
        '''
        Returns True if the pitches of the RomanNumeral are the same as the pitches
        of lastChord.  Returns False if lastChord is None.
        '''
        if lastChord is None:
            same = False
        else:
            rnP = [p.nameWithOctave for p in rn.pitches]
            lcP = [p.nameWithOctave for p in lastChord.pitches]
            if rnP == lcP:
                same = True
            else:
                same = False
        return same

    def addOptionalTieAndLyrics(
        self,
        rn: roman.RomanNumeral,
        lastChord: chord.Chord | None
    ) -> None:
        '''
        Adds ties to chords that are the same.  Adds lyrics to chords that change.
        '''
        same = self.isSame(rn, lastChord)
        if same is False and lastChord is not None and lastChord.tie is not None:
            lastChord.tie.type = 'stop'
        if same is False and (self.parent is None or self.parent.labelRomanNumerals is True):
            rn.lyrics.append(note.Lyric(rn.figure, number=1))

        if same is True and lastChord is not None and lastChord.tie is None:
            lastChord.tie = tie.Tie('start')
            rn.tie = tie.Tie('stop')
        elif same is True and lastChord is not None and lastChord.tie is not None:
            lastChord.tie.type = 'continue'
            rn.tie = tie.Tie('stop')

    def insertKsTs(self,
                   m: stream.Measure,
                   ts: meter.TimeSignature,
                   keyObj: key.Key) -> None:
        '''
        Insert a new time signature or Key into measure m, if it's
        not already in the stream somewhere.

        Note that the name "ks" is slightly misnamed.  It requires a Key,
        not KeySignature object.
        '''
        if self.parent is None:
            m.timeSignature = ts
            m.keySignature = keyObj
            return

        if ts not in self.parent.tsList:
            m.timeSignature = ts
            self.parent.tsList.append(ts)
        if keyObj not in self.parent.keyObjList:
            m.keySignature = keyObj
            self.parent.keyObjList.append(keyObj)

    def fixupChordAtom(self, atom: str) -> str:
        '''
        changes some CT values into music21 values

        >>> s = romanText.clercqTemperley.CTRule()
        >>> s.fixupChordAtom('iix')
        'iio'
        >>> s.fixupChordAtom('viih7')
        'vii/o7'
        >>> s.fixupChordAtom('iia')
        'ii+'

        '''
        if 'x' in atom:
            atom = atom.replace('x', 'o')
        if 'h' in atom:
            atom = atom.replace('h', '/o')
        if atom[0].islower() and 'a' in atom:  # TODO: what about biia ?
            atom = atom.replace('a', '+')
        return atom
    # --------------------------------------------------------------------------

    def _setMusicText(self, value: str) -> None:
        self._musicText = str(value)

    def _getMusicText(self):
        if self._musicText:
            return self._musicText

        if not self.text:
            return ''

        text = self.text[len(self.LHS) + 1:]
        if '%' in text:
            commentStartIndex = text.index('%')
            text = text[0:commentStartIndex]

        self._musicText = text.strip()
        return self._musicText

    musicText = property(_getMusicText, _setMusicText, doc='''
        Gets just the music text of the CTRule, excluding the left hand side and comments

        >>> rs = 'In: $BP*3 I IV | I | $BP*3 I IV | I | R |*4 I |*4 % This is a comment'
        >>> s = romanText.clercqTemperley.CTRule(rs)
        >>> s.text
        'In: $BP*3 I IV | I | $BP*3 I IV | I | R |*4 I |*4 % This is a comment'
        >>> s.musicText
        '$BP*3 I IV | I | $BP*3 I IV | I | R |*4 I |*4'
        ''')

    @property
    def comment(self) -> str | None:
        '''
        Get the comment of a CTRule object.

        >>> rs = 'In: $BP*3 I IV | I | $BP*3 I IV | I | R |*4 I |*4 % This is a comment'
        >>> s = romanText.clercqTemperley.CTRule(rs)
        >>> s.comment
        'This is a comment'
        '''
        if '%' in self.text:
            return self.text[self.text.index('%') + 1:].strip()
        return None

    def _getLHS(self) -> str:
        if self._LHS:
            return self._LHS

        LHS = ''
        if self.text and self.text.split()[0].endswith(':'):
            for char in self.text:
                if char == ':':
                    self._LHS = LHS.strip()
                    return self._LHS
                LHS = LHS + char
            # no colon found -- will not happen; it's in self.text
            return ''  # pragma: no cover
        else:
            return ''

    def _setLHS(self, value: str) -> None:
        self._LHS = str(value)

    LHS = property(_getLHS, _setLHS, doc='''
        Get the LHS (Left Hand Side) of the CTRule.
        If not specified explicitly but CTtext present, searches
        first characters up until ':' for rule and returns string)

        >>> rs = 'In: $BP*3 I IV | R |*4 I |*4 % This is a comment'
        >>> s = romanText.clercqTemperley.CTRule(rs)
        >>> s.LHS
        'In'
        ''')

    @property
    def sectionName(self):
        '''
        Returns the expanded version of the Left-hand side (LHS) such as
        Introduction, Verse, etc. if
        text is present (uses LHS to expand)

        Currently supported abbreviations:

        * In: Introduction
        * Br: Bridge
        * Vr: Verse
        * Ch: Chorus
        * Fadeout: Fadeout
        * S: Song

        >>> s = romanText.clercqTemperley.CTRule('Vr2: $BP*3 I IV | I |')
        >>> s.sectionName
        'Verse2'
        '''
        sectionName = ''
        if 'In' in self.LHS:
            sectionName = 'Introduction' + self.LHS[2:]
        elif 'Br' in self.LHS:
            sectionName = 'Bridge' + self.LHS[2:]
        elif 'Vr' in self.LHS:
            sectionName = 'Verse' + self.LHS[2:]
        elif 'Ch' in self.LHS:
            sectionName = 'Chorus' + self.LHS[2:]
        elif 'Tg' in self.LHS:
            sectionName = 'Tag' + self.LHS[2:]
        elif self.LHS == 'S':
            sectionName = 'Song' + self.LHS[1:]
        elif self.LHS == 'Fadeout':
            sectionName = 'Fadeout'
        else:
            sectionName = self.LHS
        return sectionName


# ------------------------------------------------------------------------------
class Test(unittest.TestCase):
    pass


class TestExternal(unittest.TestCase):
    show = True

    def testB(self):
        from music21.romanText import clercqTemperley
        s = clercqTemperley.CTSong(BlitzkriegBopCT)
        partObj = s.toPart()
        if self.show:
            partObj.show()

    def x_testA(self):
        pass
        # from music21.romanText import clercqTemperley
        #
        # dt = 'C:/clercqTemperley/dt'
        # tdc = 'C:/clercqTemperley/tdc'
        #
        # for x in os.listdir(tdc):
        #     print(x)
        #     f = open(os.path.join(tdc, x), 'r')
        #     txt = f.read()
        #
        #     s = clercqTemperley.CTSong(txt)
        #     for chord in s.toPart().flatten().getElementsByClass(chord.Chord):
        #         try:
        #             x = chord.pitches
        #         except:
        #             print(x, chord)
        #
        #
        # for num in range(1, 200):
        #     try:
        #         fileName = 'C:\\dt\\' + num + '.txt'
        #         s = clercqTemperley.CTSong(fileName)
        #         print(s.toPart().highestOffset, 'Success', num)
        #     except:
        #         print('ERROR', num)
        # s = clercqTemperley.CTSong(exampleClercqTemperley)

        # sc = s.toPart()
        # print(sc.highestOffset)
        # sc.show()


# --------------------------------------------------------------------------
# define presented class order in documentation
_DOC_ORDER: list[type] = [CTSong, CTRule]

if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
