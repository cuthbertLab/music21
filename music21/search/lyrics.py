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
from collections import namedtuple
from typing import Optional, List

from music21.exceptions21 import Music21Exception
# from music21 import common


class IndexedLyric(namedtuple('IndexedLyric', 'el start end measure lyric text')):
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
    }


class SearchMatch(namedtuple('SearchMatch', 'mStart mEnd matchText els indices')):
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
                 'indices': '''A list'''
                 }

    def __repr__(self):
        return 'SearchMatch(mStart={0}, mEnd={1}, matchText={2}, els={3}, indices=[...])'.format(
            repr(self.mStart), repr(self.mEnd), repr(self.matchText), repr(self.els)
        )


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

    Restriction:  Currently searches the first lyric only.

    TODO: let any lyric be searched.

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
        return self._indexText

    def index(self, s=None) -> List[IndexedLyric]:
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
             lyric=<music21.note.Lyric number=1 syllabic=single text='Et'>, text='Et'),
         IndexedLyric(el=<music21.note.Note D>, start=3, end=5, measure=2,
             lyric=<music21.note.Lyric number=1 syllabic=single text='in'>, text='in'),
         IndexedLyric(el=<music21.note.Note F>, start=6, end=9, measure=2,
             lyric=<music21.note.Lyric number=1 syllabic=begin text='ter'>, text='ter'),
         IndexedLyric(el=<music21.note.Note F>, start=9, end=11, measure=3,
             lyric=<music21.note.Lyric number=1 syllabic=end text='ra'>, text='ra'),
         IndexedLyric(el=<music21.note.Note A>, start=12, end=15, measure=3,
             lyric=<music21.note.Lyric number=1 syllabic=single text='pax'>, text='pax')]
        '''
        if s is None:
            s = self.stream
        else:
            self.stream = s

        index = []
        iText = ''
        lastSyllabic = None

        for n in s.recurse().getElementsByClass('NotRest'):
            ls = n.lyrics
            if not ls:
                continue
            ly = ls[0]
            if ly is not None and ly.text != '' and ly.text is not None:
                posStart = len(iText)
                mNum = n.measureNumber
                txt = ly.text
                if lastSyllabic in ('begin', 'middle', None):
                    iText += txt
                else:
                    iText += ' ' + txt
                    posStart += 1
                il = IndexedLyric(n, posStart, posStart + len(txt), mNum, ly, txt)
                index.append(il)
                lastSyllabic = ly.syllabic

        self._indexTuples = index
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
                        indices=[...])]

        Search a regular expression that takes into account non-word characters such as commas

        >>> agnus = re.compile(r'agnus dei\W+filius patris', re.IGNORECASE)
        >>> sm = ls.search(agnus)
        >>> sm
        [SearchMatch(mStart=49, mEnd=55, matchText='Agnus Dei, Filius Patris',
                        els=(<music21.note.Note G>,...<music21.note.Note G>), indices=[...])]
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
                '{0} is not a string or RE with the finditer() function'.format(textOrRe))

        if plainText is True:
            return self._plainTextSearch(textOrRe)
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
            if i.end >= posStart and i.start <= posEnd:
                indices.append(i)
        if not indices:
            raise LyricSearcherException(f'Could not find position {posStart} in text')
        return indices

    def _plainTextSearch(self, t: str) -> List[SearchMatch]:
        '''
        Take in a string and find in the indexed text where t is in the lyrics.
        '''
        locations = []
        start = 0
        tLen = len(t)

        loopBreaker = 10000000
        while True and loopBreaker:
            loopBreaker -= 1
            foundPos: int = self._indexText.find(t, start)
            if foundPos == -1:
                break

            indices: List[IndexedLyric] = self._findObjsInIndexByPos(
                foundPos,
                foundPos + tLen - 1
            )
            indexStart = indices[0]
            indexEnd = indices[-1]

            sm = SearchMatch(mStart=indexStart.measure,
                             mEnd=indexEnd.measure,
                             matchText=t,
                             els=tuple(thisIndex.el for thisIndex in indices),
                             indices=indices)
            locations.append(sm)
            start = foundPos + 1

        return locations

    def _reSearch(self, r) -> List[SearchMatch]:
        locations = []
        for m in r.finditer(self._indexText):
            foundPos, endPos = m.span()
            matchText = m.group(0)
            indices = self._findObjsInIndexByPos(foundPos, endPos - 1)
            indexStart = indices[0]
            indexEnd = indices[-1]

            sm = SearchMatch(mStart=indexStart.measure,
                             mEnd=indexEnd.measure,
                             matchText=matchText,
                             els=tuple(thisIndex.el for thisIndex in indices),
                             indices=indices)
            locations.append(sm)
        return locations


# ------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [LyricSearcher]

if __name__ == '__main__':
    import music21
    music21.mainTest()

