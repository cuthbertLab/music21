# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         clercqTemperley.py
# Purpose:      Routines to parse the popular music
#               Roman Numeral encoding system used by Clercq-Temperley
#
# Authors:      Beth Hadley
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2011-12, 2015 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
Parses the de Clercq-Temperley popular music flavor of RomanText.
The Clercq-Temperley file format and additional rock corpus analysis
information may be located at http://theory.esm.rochester.edu/rock_corpus/
'''
import copy
import io
import re
import unittest

from collections import OrderedDict

from music21 import exceptions21

from music21 import common
from music21 import key
from music21 import meter
from music21 import stream
from music21 import roman
from music21 import tie
from music21 import note
from music21 import metadata
from music21 import prebase

from music21 import environment
environLocal = environment.Environment()

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

    Create a CTSong object one of two ways:
    1) by passing in the string, with newline characters (\\n) at the end of each line
    2) by passing in the text file as a string, and have python open the file and read the text

    >>> exampleClercqTemperley = '''
    ... % Brown-Eyed Girl
    ... VP: I | IV | I | V |
    ... In: $VP*2
    ... Vr: $VP*4 IV | V | I | vi | IV | V | I | V | % Second half could be called chorus
    ... Ch: V | | $VP*2 I |*4
    ... Ch2: V | | $VP*3     % Fadeout
    ... S: [G] $In $Vr $Vr $Ch $VP $Vr $Ch2
    ... '''

    >>> exCT = romanText.clercqTemperley.exampleClercqTemperley
    >>> s = romanText.clercqTemperley.CTSong(exCT)  #_DOCS_HIDE
    >>> #_DOCS_SHOW s = romanText.clercqTemperley.CTSong('C:/Brown-Eyed_Girl.txt')

    When you call the .toScore() method on the newly created CTSong object,
    the code extracts meaningful properties (such as title, text, comments,
    year, rules, home time Signature, and home Key Signature) from the text file
    and makes these accessible as below.

    The toScore() method has two optional labeling parameters, labelRomanNumerals and
    labelSubsectionsOnScore. Both are set to True by default. Thus, the created score
    will have labels (on the chord's lyric) for each roman numeral as well as for each
    section in the song (LHS). In case of a recursive definition (a rule contains a reference
    to another rule), both labels are printed, with the deepest
    reference on the smallest lyric line.

    >>> #_DOCS_SHOW s.toScore().show()

    .. image:: images/ClercqTemperleyExbrown-eyed_girl.png
       :width: 500

    >>> s.title
    'Brown-Eyed Girl'

    >>> s.homeTimeSig
    <music21.meter.TimeSignature 4/4>

    >>> s.homeKeySig
    <music21.key.Key of G major>

    >>> s.comments
    [['Vr:', 'Second half could be called chorus'], ['Ch2:', 'Fadeout']]

    Year is not defined as part of the Clercq-Temperley format, but it will be helpful
    to have it as a property. So let's assign a year to this song:

    >>> s.year = 1967
    >>> s.year
    1967

    Upon calling toScore(), CTRule objects are also created. CTRule objects are
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

    OMIT_FROM_DOCS

    Another example using a different Clercq-Temperley file

    RockClockCT =
    % Rock Around the Clock
    % just a general comment
    In: I | | | | | | V | |
    Vr: I | | | | IVd7 | | I | | V7 | | I | | %a comment on verse
    Vrf: I | | | | IVd7 | | I | | V7 | | I | IV iv | V | . I |
    S: [A] $In $Vr $Vr $Vr $Vr $Vr $Vr $Vrf    % 3rd and 6th verses are instrumental

    >>> s = romanText.clercqTemperley.CTSong(romanText.clercqTemperley.RockClockCT)
    >>> score = s.toScore()
    >>> score.highestTime
    376.0

    >>> s.title
    'Rock Around the Clock'

    >>> s.homeTimeSig
    <music21.meter.TimeSignature 4/4>

    >>> s.homeKeySig
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
    _DOC_ORDER = ['text', 'toScore', 'title', 'homeTimeSig', 'homeKeySig', 'comments', 'rules']
    _DOC_ATTR = {'year': 'the year of the CTSong; not formally defined '
                         + 'by the Clercq-Temperley format'}

    def __init__(self, textFile, **keywords):
        self._title = None
        self.text = ''
        self.lines = []
        self._rules = OrderedDict()  # Dictionary of all component rules of the type CTRule
        self.ksList = []  # keeps a list of all key signatures in the Score -- avoids duplicates
        self.tsList = []  # same for time signatures

        self._scoreObj = None
        self.year = None

        self._homeTimeSig = None
        self._homeKeySig = None

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
    def parse(self, textFile: str):
        '''
        Called when a CTSong is created by passing a string or filename;
        in the second case, it opens the file
        and removes all blank lines, and adds in new line characters
        returns pieceString that CTSong can parse.
        '''
        if '|' in textFile and 'S:' in textFile:
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
        comment is on a rule line, the list contains both the line's LHS (like In:) and the comment
        if the comment is on a line of its own, only the comment is
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
        a LHS including the Song line, which should always be last.

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
        <MeterSequence {{1/8+1/8+1/8}+{1/8+1/8+1/8}+{1/8+1/8+1/8}+{1/8+1/8+1/8}}>
        '''
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
    def homeKeySig(self):
        '''
        gets the initial, or 'home', key signature by looking at the music text and locating
        the key signature at the start of the S: rule.

        >>> s = romanText.clercqTemperley.CTSong(romanText.clercqTemperley.textString)
        >>> s.homeKeySig
        <music21.key.Key of A major>
        '''
        # look at 'S' Rule and grab the home key Signature
        if self.text and 'S:' in self.text:
            lines = self.text.split('\n')
            for line in lines:
                if line.startswith('S:'):
                    for atom in line.split()[1:3]:
                        if '[' not in atom:
                            self._homeKeySig = key.Key('C')
                            return self._homeKeySig
                        elif '/' not in atom:
                            m21keyStr = key.convertKeyStringToMusic21KeyString(atom[1:-1])
                            self._homeKeySig = key.Key(m21keyStr)
                            return self._homeKeySig
                        else:
                            pass
        return self._homeKeySig

    def toScore(self, labelRomanNumerals=True, labelSubsectionsOnScore=True):
        # noinspection PyShadowingNames
        '''
        creates Score object out of a from CTSong...also creates CTRule objects in the process,
        filling their .streamFromCTSong attribute with the corresponding smaller inner stream.
        Individual attributes of a rule are defined by the entire CTSong, such as
        meter and time signature, so creation of CTRule objects typically occurs
        only from this method and directly from the clercqTemperley text.

        >>> s = romanText.clercqTemperley.CTSong(romanText.clercqTemperley.BlitzkriegBopCT)
        >>> scoreObj = s.toScore()
        >>> scoreObj.highestOffset
        380.0
        '''
        self.labelRomanNumerals = labelRomanNumerals
        self.labelSubsectionsOnScore = labelSubsectionsOnScore
        if self._scoreObj is not None:
            return self._scoreObj
        scoreObj = stream.Part()
        measures = self.rules['S'].expand()
        scoreObj.append(measures)

        scoreObj.insert(0, metadata.Metadata())
        scoreObj.metadata.title = self.title

        self._scoreObj = scoreObj
        return scoreObj


class CTRuleException(exceptions21.Music21Exception):
    pass


class CTRule(prebase.ProtoM21Object):
    '''
    CTRule objects correspond to the individual lines defined in a
    :class:`~music21.romanText.clercqTemperley.CTSong` object. They are typically
    created by the parser after a CTSong object has been created and the .toScore() method
    has been called on that object. The usefulness of each CTRule object is that each
    has a :meth:`~music21.romanText.clercqTemperley.CTRUle.streamFromCTSong` attribute,
    which is the stream from the entire score that the rule corresponds to.
    '''
    _DOC_ORDER = ['LHS', 'sectionName', 'musicText', 'homeTimeSig', 'homeKeySig', 'comments']
    _DOC_ATTR = {'text': 'the full text of the CTRule, including the LHS, chords, and comments'}

    SPLITMEASURES = re.compile(r'(\|\*?\d*)')
    REPETITION = re.compile(r'\*(\d+)')

    def __init__(self, text='', parent=None):
        self._parent = None
        if parent is not None:
            self.parent = parent

        self._musicText = None  # just the text above without the rule string or comments
        self._LHS = None  # rule name string, such as "In"
        self.text = text  # FULL TEXT OF CTRULE (includes LHS, chords, and comments

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

    def expand(self, ts=None, ks=None):
        '''
        The meat of it all -- expand one rule completely and return a list of Measure objects.
        '''
        if ts is None:
            ts = meter.TimeSignature('4/4')
        if ks is None:
            ks = key.Key('C')
        measures = []

        lastRegularAtom = None
        lastChord = None

        for content, sep, numReps in self._measureGroups():
            lastChordIsInSameMeasure = False
            if sep == '$':
                if content not in self.parent.rules:
                    raise CTRuleException(f'Cannot expand rule {content} in {self}')
                rule = self.parent.rules[content]
                for i in range(numReps):
                    returnedMeasures = rule.expand(ts, ks)
                    self.insertKsTs(returnedMeasures[0], ts, ks)
                    for returnedTs in [m.getElementsByClass('TimeSignature')
                                        for m in returnedMeasures]:
                        if returnedTs is not ts:
                            # the TS changed mid-rule; create a new one for return.
                            ts = copy.deepcopy(ts)

                    measures.extend(returnedMeasures)
            elif sep == '|':
                m = stream.Measure()
                atoms = content.split()
                # key/timeSig pass...
                regularAtoms = []
                for atom in atoms:
                    if atom.startswith('['):
                        atomContent = atom[1:-1]
                        if atomContent == '0':
                            ts = meter.TimeSignature('4/4')
                            # irregular meter.  Cannot fully represent;
                            # TODO: replace w/ senza misura when possible.

                        elif '/' in atomContent:  # only one key / ts per measure.
                            ts = meter.TimeSignature(atomContent)
                        else:
                            ks = key.Key(key.convertKeyStringToMusic21KeyString(atomContent))

                    elif atom == '.':
                        if lastRegularAtom is None:
                            raise CTRuleException(f' . w/o previous atom: {self}')
                        regularAtoms.append(lastRegularAtom)
                    elif atom in ('', None):
                        pass
                    else:
                        regularAtoms.append(atom)
                        lastRegularAtom = atom
                numAtoms = len(regularAtoms)
                if numAtoms == 0:
                    continue  # maybe just ts and ks setting

                self.insertKsTs(m, ts, ks)

                atomLength = common.opFrac(ts.barDuration.quarterLength / numAtoms)
                for atom in regularAtoms:
                    if atom == 'R':
                        rest = note.Rest(quarterLength=atomLength)
                        lastChord = None
                        lastChordIsInSameMeasure = False
                        m.append(rest)
                    else:
                        atom = self.fixupChordAtom(atom)
                        rn = roman.RomanNumeral(atom, ks)
                        if self.isSame(rn, lastChord) and lastChordIsInSameMeasure:
                            lastChord.duration.quarterLength += atomLength
                            m.coreElementsChanged()
                        else:
                            rn.duration.quarterLength = atomLength
                            self.addOptionalTieAndLyrics(rn, lastChord)
                            lastChord = rn
                            lastChordIsInSameMeasure = True
                            m.append(rn)
                measures.append(m)
                for i in range(1, numReps):
                    measures.append(copy.deepcopy(m))
            else:
                environLocal.warn(
                    f'Rule found without | or $, ignoring: {content!r},{sep!r}: in {self.text!r}')
                # pass
        if measures:
            for m in measures:
                noteIter = m.recurse().notes
                if (noteIter
                        and (self.parent is None
                             or self.parent.labelSubsectionsOnScore is True)
                        and self.LHS != 'S'):
                    rn = noteIter[0]
                    lyricNum = len(rn.lyrics) + 1
                    rn.lyrics.append(note.Lyric(self.LHS, number=lyricNum))
                    break

        return measures

    def _measureGroups(self):
        '''
        Returns content, "|" (normal) or "$" (expansion), and number of repetitions.

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
        measureGroups1 = []
        measureGroups2 = []
        measureGroups3 = []
        measureGroupTemp = self.SPLITMEASURES.split(self.musicText)
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
            contentOut = []

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
            if sep == '|' and all([y.startswith('[') or y == '' for y in contentSplit]):
                content = ' '.join(contentSplit)
                if content:
                    content += ' '
                content += '.'
            elif sep == '?':  # implied continuation
                sep = '|'
            measureGroups3.append((content, sep, numReps))

        return measureGroups3

    # --------------------------------------------------------------------------
    def isSame(self, rn, lastChord):
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

    def addOptionalTieAndLyrics(self, rn, lastChord):
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

    def insertKsTs(self, m, ts, ks):
        '''
        insert a new time signature or key signature into measure m, if it's
        not already in the stream somewhere.
        '''
        if self.parent is None:
            m.timeSignature = ts
            m.keySignature = ks
            return

        if ts not in self.parent.tsList:
            m.timeSignature = ts
            self.parent.tsList.append(ts)
        if ks not in self.parent.ksList:
            m.keySignature = ks
            self.parent.tsList.append(ks)

    def fixupChordAtom(self, atom):
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

    def _setMusicText(self, value):
        self._musicText = str(value)

    def _getMusicText(self):
        if self._musicText not in (None, ''):
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
    def comment(self):
        '''
        Get the comment of a CTRule object.

        >>> rs = 'In: $BP*3 I IV | I | $BP*3 I IV | I | R |*4 I |*4 % This is a comment'
        >>> s = romanText.clercqTemperley.CTRule(rs)
        >>> s.comment
        'This is a comment'
        '''
        if '%' in self.text:
            return self.text[self.text.index('%') + 1:].strip()
        else:
            return None

    def _setLHS(self, value):
        self._LHS = str(value)

    def _getLHS(self):
        if self._LHS not in (None, ''):
            return self._LHS

        LHS = ''
        if self.text and self.text.split()[0].endswith(':'):
            for char in self.text:
                if char == ':':
                    self._LHS = LHS.strip()
                    return self._LHS
                LHS = LHS + char
        else:
            return ''

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
        Returns the expanded version of the Left hand side (LHS) such as
        Introduction, Verse, etc. if
        text present uses LHS to expand)

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


class TestExternal(unittest.TestCase):  # pragma: no cover

    def testB(self):
        from music21.romanText import clercqTemperley
        s = clercqTemperley.CTSong(BlitzkriegBopCT)
        scoreObj = s.toScore()
        scoreObj.show()

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
        #     for chord in s.toScore().flat.getElementsByClass('Chord'):
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
        #         print(s.toScore().highestOffset, 'Success', num)
        #     except:
        #         print('ERROR', num)
        # s = clercqTemperley.CTSong(exampleClercqTemperley)

        # sc = s.toScore()
        # print(sc.highestOffset)
        # sc.show()
# --------------------------------------------------------------------------

# define presented class order in documentation


_DOC_ORDER = [CTSong, CTRule]

if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
