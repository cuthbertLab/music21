# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         search/lyrics.py
# Purpose:      music21 classes for searching lyrics
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2015 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
Classes for searching for Lyric objects.
'''
import re
from collections import namedtuple, OrderedDict
from typing import Optional, List
import unittest

from music21.exceptions21 import Music21Exception
from music21 import note
# from music21 import common

LINEBREAK_TOKEN = ' // '

_attrList = 'el start end measure lyric text identifier absoluteStart absoluteEnd'.split()

class IndexedLyric(namedtuple(
    'IndexedLyric',
    'el start end measure lyric text identifier absoluteStart absoluteEnd',
)):
    '''
    A Lyric that has been indexed to its attached element and position in a Stream.

    '''
    __slots__ = ()
    _DOC_ATTR = {
        'el': 'the element that the lyric is attached to',
        'start': '''Suppose that the entire lyric for the stream were a single string:
                 this is the index of the position in the string that this
                 lyric starts at.''',
        'end': '''Suppose that the entire lyric for the stream were a single string:
                 this is the index of the position in the string that this
                 lyric ends at.''',
        'measure': '''The measureNumber of the measure that the element is in
                 in the stream.  Same as .el.measureNumber''',
        'lyric': '''The :class:`~music21.note.Lyric` object itself''',
        'text': '''The text of the lyric as a string.''',
        'identifier': '''The identifier of the lyric''',
        'absoluteStart': '''the position, not in the current identifier, but in all the lyrics''',
        'absoluteEnd': '''the end position in all the lyrics'''
    }
    def __repr__(self):
        return (f'IndexedLyric(el={self.el!r}, start={self.start!r}, end={self.end!r}, '
                + f'measure={self.measure!r}, lyric={self.lyric!r}, text={self.text!r}, '
                + f'identifier={self.identifier!r})')

    def modify(self, **kw):
        '''
        see docs for SortTuple for what this does
        '''
        outList = [kw.get(attr, getattr(self, attr)) for attr in _attrList]
        return self.__class__(*outList)



class SearchMatch(namedtuple('SearchMatch', 'mStart mEnd matchText els indices identifier')):
    '''
    A lightweight object representing the match (if any) for a search.
    '''
    __slots__ = ()
    _DOC_ATTR = {'mStart': '''The measureNumber of the measure that the first
                                matching lyric is in''',
                 'mEnd': '''The measureNumber of the measure that the last
                                matching lyric is in''',
                 'matchText': '''The text of the lyric that matched the search.  For a
                                 plaintext search, this will be the same as the search
                                 term, but for a regular expression
                                 search this will be the text that matched the regular
                                 expression''',
                 'els': '''A list of all lyric-containing elements that matched this text.''',
                 'indices': '''A list of IndexedLyric objects that match''',
                 'identifier': '''The identifier of (presumably all,
                                  but at least the first) lyric to match''',
                 }

    def __repr__(self):
        return (f'SearchMatch(mStart={self.mStart!r}, mEnd={self.mEnd!r}, '
                + f'matchText={self.matchText!r}, els={self.els!r}, indices=[...], '
                + f'identifier={self.identifier!r})')


class LyricSearcherException(Music21Exception):
    pass


class LyricSearcher:
    # noinspection SpellCheckingInspection
    '''
    An object that can find lyrics that match a certain regular expression
    and return relevant information about the match.

    Construct the LyricSearcher by passing in a Stream object (it can be
    a Score or Part or other nested item), and then call ".search()" on it.

    See :ref:`User's Guide, Chapter 28, Lyric Searching <usersGuide_28_lyricSearcher>` for
    full details.

    TODO: Bug that occasionally the previous note will be included; Search luca/gloria for
       "riam tuam." (From Gloriam tuam).  For some reason, the whole "Gloria" is included.
       Does not occur if only "iam tuam." is searched.

    TODO: allow for all intermediate notes during a search to be found.
        includeIntermediateElements.

    TODO: allow for trailing melismas to also be included.

    TODO: Note that because of recursive searching w/ voices, there may be "phantom" lyrics
        found if a work contains multiple voices.
    '''

    def __init__(self, s=None):
        self.stream = s
        self.includeIntermediateElements = False  # currently does nothing
        self.includeTrailingMelisma = False  # currently does nothing

        self._indexText: Optional[str] = None
        self._indexTuples: List[IndexedLyric] = []

    @property
    def indexText(self) -> str:
        '''
        Returns the text that has been indexed (a la, :func:`~music21.text.assembleLyrics`):

        >>> p0 = corpus.parse('luca/gloria').parts[0]
        >>> ls = search.lyrics.LyricSearcher(p0)
        >>> ls.indexText[0:25]
        'Et in terra pax hominibus'
        '''
        if self._indexText is None:
            self.index()
        return self._indexText or ''

    @property
    def indexTuples(self) -> List[IndexedLyric]:
        if self._indexText is None:  # correct -- check text to see if has run.
            self.index()
        return self._indexTuples

    def index(self, s=None) -> List[IndexedLyric]:
        # noinspection PyShadowingNames
        '''
        A method that indexes the Stream's lyrics and returns the list
        of IndexedLyric objects.

        This does not actually need to be run, since calling .search() will call this if
        it hasn't already been called.

        >>> from pprint import pprint as pp

        >>> p0 = corpus.parse('luca/gloria').parts[0]
        >>> ls = search.lyrics.LyricSearcher(p0)
        >>> pp(ls.index()[0:5])
        [IndexedLyric(el=<music21.note.Note C>, start=0, end=2, measure=1,
             lyric=<music21.note.Lyric number=1 syllabic=single text='Et'>, text='Et',
             identifier=1),
         IndexedLyric(el=<music21.note.Note D>, start=3, end=5, measure=2,
             lyric=<music21.note.Lyric number=1 syllabic=single text='in'>, text='in',
             identifier=1),
         IndexedLyric(el=<music21.note.Note F>, start=6, end=9, measure=2,
             lyric=<music21.note.Lyric number=1 syllabic=begin text='ter'>, text='ter',
             identifier=1),
         IndexedLyric(el=<music21.note.Note F>, start=9, end=11, measure=3,
             lyric=<music21.note.Lyric number=1 syllabic=end text='ra'>, text='ra',
             identifier=1),
         IndexedLyric(el=<music21.note.Note A>, start=12, end=15, measure=3,
             lyric=<music21.note.Lyric number=1 syllabic=single text='pax'>, text='pax',
             identifier=1)]

        Changed in v6.7 -- indexed lyrics get an identifier.
        '''
        if s is None:
            s = self.stream
        else:
            self.stream = s

        indexByIdentifier = OrderedDict()
        iTextByIdentifier = OrderedDict()
        lastSyllabicByIdentifier = OrderedDict()

        for n in s.recurse().getElementsByClass('NotRest'):
            ls: List[note.Lyric] = n.lyrics
            if not ls:
                continue
            mNum = n.measureNumber
            for ly in ls:
                if not ly.text:  # not empty and not None
                    continue
                lyIdentifier = ly.identifier
                if lyIdentifier not in iTextByIdentifier:
                    iTextByIdentifier[lyIdentifier] = ''
                    lastSyllabicByIdentifier[lyIdentifier] = None
                    indexByIdentifier[lyIdentifier] = []

                iText = iTextByIdentifier[lyIdentifier]
                lastSyllabic = lastSyllabicByIdentifier[lyIdentifier]
                index = indexByIdentifier[lyIdentifier]

                posStart = len(iText)
                txt = ly.text
                if lastSyllabic in ('begin', 'middle', None):
                    iText += txt
                else:
                    iText += ' ' + txt
                    posStart += 1

                iTextByIdentifier[lyIdentifier] = iText
                il = IndexedLyric(n, posStart, posStart + len(txt), mNum, ly, txt,
                                  lyIdentifier, 0, 0)
                index.append(il)
                if not ly.isComposite:
                    lastSyllabic = ly.syllabic
                else:
                    lastSyllabic = ly.components[-1].syllabic
                lastSyllabicByIdentifier[lyIdentifier] = lastSyllabic

        indexPreliminary = []
        for oneIdentifierIndex in indexByIdentifier.values():
            indexPreliminary.extend(oneIdentifierIndex)

        absolutePosShift = 0
        lastIdentifier = None
        lastEnd = 0
        index = []
        oneIndex: IndexedLyric
        for oneIndex in indexPreliminary:
            if oneIndex.identifier != lastIdentifier:
                absolutePosShift = lastEnd
                if lastEnd != 0:
                    absolutePosShift += len(LINEBREAK_TOKEN)
            lastIdentifier = oneIndex.identifier
            newIndex = oneIndex.modify(absoluteStart=oneIndex.start + absolutePosShift,
                                       absoluteEnd=oneIndex.end + absolutePosShift)
            lastEnd = newIndex.absoluteEnd
            index.append(newIndex)

        self._indexTuples = index
        iText = LINEBREAK_TOKEN.join(iTextByIdentifier.values())
        self._indexText = iText
        return index

    def search(self, textOrRe, s=None) -> List[SearchMatch]:
        # noinspection SpellCheckingInspection
        r'''
        Return a list of SearchMatch objects matching a string or regular expression.

        >>> import re

        >>> p0 = corpus.parse('luca/gloria').parts[0]
        >>> ls = search.lyrics.LyricSearcher(p0)
        >>> ls.search('pax')
        [SearchMatch(mStart=3, mEnd=3, matchText='pax', els=(<music21.note.Note A>,),
                        indices=[...], identifier=1)]

        Search a regular expression that takes into account non-word characters such as commas

        >>> agnus = re.compile(r'agnus dei\W+filius patris', re.IGNORECASE)
        >>> sm = ls.search(agnus)
        >>> sm
        [SearchMatch(mStart=49, mEnd=55, matchText='Agnus Dei, Filius Patris',
                        els=(<music21.note.Note G>,...<music21.note.Note G>), indices=[...],
                        identifier=1)]
        >>> sm[0].mStart, sm[0].mEnd
        (49, 55)
        '''
        if s is None:
            s = self.stream

        if s is not self.stream or not self._indexTuples:
            self.index(s)

        if isinstance(textOrRe, str):
            plainText = True
        elif hasattr(textOrRe, 'finditer'):
            plainText = False
        else:
            raise LyricSearcherException(
                f'{textOrRe} is not a string or RE with the finditer() function')

        if plainText is True:
            return self._reSearch(re.compile(textOrRe))
        else:
            return self._reSearch(textOrRe)

    def _findObjInIndexByPos(self, pos) -> IndexedLyric:
        '''
        Finds an object in ._indexTuples by search position.

        Raises exception if no IndexedLyric for that position.

        Runs in O(n) time on number of lyrics. Would not be
        hard to do in O(log(n)) for very large lyrics
        '''
        for i in self._indexTuples:
            if i.start <= pos <= i.end:
                return i

        raise LyricSearcherException(f'Could not find position {pos} in text')

    def _findObjsInIndexByPos(self, posStart, posEnd=999999) -> List[IndexedLyric]:
        '''
        Finds a list of objects in ._indexTuples by search position (inclusive)
        '''
        indices = []
        for i in self._indexTuples:
            if i.absoluteEnd >= posStart and i.absoluteStart <= posEnd:
                indices.append(i)
        if not indices:
            raise LyricSearcherException(f'Could not find position {posStart} in text')
        return indices

    # def _findLineBreakBeforePos(self, pos: int):
    #     '''
    #     Finds the position of the first character after the closest lineBreak
    #     '''
    #     lineBreakStart = -1 * len(LINEBREAK_TOKEN)
    #
    #     loopBreaker = 10_000
    #     while True and loopBreaker:
    #         loopBreaker -= 1
    #         nextLineBreakPos = self._indexText.find(LINEBREAK_TOKEN,
    #                                                 lineBreakStart + len(LINEBREAK_TOKEN))
    #         if nextLineBreakPos == -1:
    #             break
    #         if nextLineBreakPos > pos:
    #             break
    #         lineBreakStart = nextLineBreakPos
    #
    #     lineBreakStart += len(LINEBREAK_TOKEN)
    #     return lineBreakStart

    def _reSearch(self, r: 're.Pattern') -> List[SearchMatch]:
        # note: cannot use re.Pattern w/o quotes until Python 3.6 is no longer supported
        locations = []
        for m in r.finditer(self._indexText):
            absoluteFoundPos, absoluteEndPos = m.span()
            matchText = m.group(0)

            indices = self._findObjsInIndexByPos(absoluteFoundPos, absoluteEndPos - 1)
            indexStart = indices[0]
            indexEnd = indices[-1]

            sm = SearchMatch(mStart=indexStart.measure,
                             mEnd=indexEnd.measure,
                             matchText=matchText,
                             els=tuple(thisIndex.el for thisIndex in indices),
                             indices=indices,
                             identifier=indices[0].identifier,
                             )
            locations.append(sm)
        return locations


# -----------------------------------------------------------------------------


class Test(unittest.TestCase):
    pass

    def testMultipleLyricsInNote(self):
        '''
        This score uses a non-breaking space as an elision
        '''
        from music21 import converter, search

        partXML = '''
        <score-partwise>
            <part-list>
                <score-part id="P1">
                <part-name>MusicXML Part</part-name>
                </score-part>
            </part-list>
            <part id="P1">
                <measure number="1">
                    <note>
                        <pitch>
                            <step>G</step>
                            <octave>4</octave>
                        </pitch>
                        <duration>1</duration>
                        <voice>1</voice>
                        <type>quarter</type>
                        <lyric number="1">
                            <syllabic>middle</syllabic>
                            <text>la</text>
                            <elision> </elision>
                            <syllabic>middle</syllabic>
                            <text>la</text>
                        </lyric>
                    </note>
                </measure>
            </part>
        </score-partwise>
        '''
        s = converter.parse(partXML, format='MusicXML')
        ly = s.flat.notes[0].lyrics[0]

        def runSearch():
            ls = search.lyrics.LyricSearcher(s)
            self.assertEqual(ls.indexText, "la la")

        runSearch()
        ly.components[0].syllabic = 'begin'
        ly.components[1].syllabic = 'end'
        runSearch()
        ly.components[0].syllabic = 'single'
        ly.components[1].syllabic = 'single'
        runSearch()

    def testMultipleVerses(self):
        from music21 import converter, search

        # noinspection SpellCheckingInspection
        partXML = '''
        <score-partwise>
            <part-list>
                <score-part id="P1">
                <part-name>MusicXML Part</part-name>
                </score-part>
            </part-list>
            <part id="P1">
                <measure number="1">
                    <note>
                        <pitch>
                            <step>G</step>
                            <octave>4</octave>
                        </pitch>
                        <duration>2</duration>
                        <voice>1</voice>
                        <type>half</type>
                        <lyric number="1">
                            <syllabic>single</syllabic>
                            <text>hi</text>
                        </lyric>
                        <lyric number="2">
                            <syllabic>single</syllabic>
                            <text>bye</text>
                        </lyric>
                    </note>
                </measure>
                <measure number="2">
                    <note>
                        <pitch>
                            <step>A</step>
                            <octave>4</octave>
                        </pitch>
                        <duration>1</duration>
                        <voice>1</voice>
                        <type>quarter</type>
                        <lyric number="1">
                            <syllabic>begin</syllabic>
                            <text>there!</text>
                        </lyric>
                        <lyric number="2">
                            <syllabic>begin</syllabic>
                            <text>Mi</text>
                        </lyric>
                    </note>
                    <note>
                        <pitch>
                            <step>B</step>
                            <octave>4</octave>
                        </pitch>
                        <duration>1</duration>
                        <voice>1</voice>
                        <type>quarter</type>
                        <lyric number="2">
                            <syllabic>end</syllabic>
                            <text>chael.</text>
                        </lyric>
                    </note>
                </measure>
            </part>
        </score-partwise>
        '''
        s = converter.parse(partXML, format='MusicXML')
        ls = search.lyrics.LyricSearcher(s)
        self.assertEqual(ls.indexText, "hi there! // bye Michael.")
        tuples = ls.indexTuples
        self.assertEqual(len(tuples), 5)
        notes = list(s.flat.notes)
        self.assertIs(tuples[0].lyric, notes[0].lyrics[0])
        self.assertIs(tuples[1].lyric, notes[1].lyrics[0])
        self.assertIs(tuples[2].lyric, notes[0].lyrics[1])
        self.assertIs(tuples[3].lyric, notes[1].lyrics[1])
        self.assertIs(tuples[4].lyric, notes[2].lyrics[0])

        match = ls.search('Michael')
        self.assertEqual(len(match), 1)
        m0 = match[0]
        self.assertEqual(m0.mStart, 2)
        self.assertEqual(m0.mEnd, 2)
        self.assertEqual(m0.els, (notes[1], notes[2]))
        self.assertEqual(m0.identifier, 2)
        self.assertEqual(len(m0.indices), 2)
        self.assertIs(m0.indices[0].lyric, notes[1].lyrics[1])
        self.assertIs(m0.indices[1].lyric, notes[2].lyrics[0])

        e_with_letter = re.compile(r'e[a-z]')
        match = ls.search(e_with_letter)
        self.assertEqual(len(match), 2)
        m0 = match[0]
        self.assertEqual(m0.mStart, 2)
        self.assertEqual(m0.mEnd, 2)
        self.assertEqual(m0.matchText, 'er')
        self.assertEqual(m0.identifier, 1)
        self.assertEqual(m0.els, (notes[1],))
        m1 = match[1]
        self.assertEqual(m1.mStart, 2)
        self.assertEqual(m1.mEnd, 2)
        self.assertEqual(m1.matchText, 'el')
        self.assertEqual(m1.identifier, 2)
        self.assertEqual(m1.els, (notes[2],))

        match = ls.search('i t')
        self.assertEqual(len(match), 1)
        self.assertEqual(match[0].mStart, 1)
        self.assertEqual(match[0].mEnd, 2)
        self.assertEqual(match[0].identifier, 1)


# ------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [LyricSearcher]


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
