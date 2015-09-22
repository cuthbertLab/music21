# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         search/lyrics.py
# Purpose:      music21 classes for searching lyrics
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2015 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
from collections import namedtuple

from music21.ext import six
from music21.exceptions21 import Music21Exception
#from music21 import common

IndexedLyric = namedtuple('IndexedLyric', 'el start end measure lyric text')
SearchMatch = namedtuple('SearchMatch', 'mStart mEnd matchText els tups')

class LyricSearcherException(Music21Exception):
    pass

class LyricSearcher(object):
    '''
    An object that can find lyrics that match a certain regular expression
    and return relevant information about the match.
    
    Currently searches the first lyric only.
    '''
    def __init__(self, s=None):
        self.stream = s
        self._indexText = None
        self._indexTuples = None

    def index(self, s=None):
        '''
        >>> from pprint import pprint as pp
        
        >>> p0 = corpus.parse('luca/gloria').parts[0]
        >>> ls = search.lyrics.LyricSearcher(p0)
        >>> pp(ls.index()[0:5]) 
        [IndexedLyric(el=<music21.note.Note C>, start=0, end=2, measure=1, lyric=<music21.note.Lyric number=1 syllabic=single text="Et">, text=...'Et'),
         IndexedLyric(el=<music21.note.Note D>, start=3, end=5, measure=2, lyric=<music21.note.Lyric number=1 syllabic=single text="in">, text=...'in'),
         IndexedLyric(el=<music21.note.Note F>, start=6, end=9, measure=2, lyric=<music21.note.Lyric number=1 syllabic=begin text="ter">, text=...'ter'),
         IndexedLyric(el=<music21.note.Note F>, start=9, end=11, measure=3, lyric=<music21.note.Lyric number=1 syllabic=end text="ra">, text=...'ra'),
         IndexedLyric(el=<music21.note.Note A>, start=12, end=15, measure=3, lyric=<music21.note.Lyric number=1 syllabic=single text="pax">, text=...'pax')]        
        '''
        if s is None:
            s = self.stream
        else:
            self.stream = s

        index = []
        iText = ""
        lastSyllabic = None
        
        for n in s.recurse(classFilter='NotRest'):
            ls = n.lyrics
            if len(ls) == 0:
                continue
            l = ls[0]
            if l is not None and l.text != "" and l.text is not None:
                posStart = len(iText)
                mNum = n.measureNumber
                txt = l.text
                if lastSyllabic in ('begin', 'middle', None):
                    iText += txt
                else:
                    iText += " " + txt
                    posStart += 1
                il = IndexedLyric(n, posStart, posStart + len(txt), mNum, l, txt)
                index.append(il)
                lastSyllabic = l.syllabic
                
        self._indexTuples = index
        self._indexText = iText
        return index

    def search(self, textOrRe, s=None):
        r'''
        >>> from pprint import pprint as pp
        >>> import re
        
        >>> p0 = corpus.parse('luca/gloria').parts[0]
        >>> ls = search.lyrics.LyricSearcher(p0)
        >>> ls.search('pax') # ellipsis because of unicode in Py2
        [SearchMatch(mStart=3, mEnd=3, matchText=...'pax', els=(<music21.note.Note A>,), tups=[IndexedLyric(...)])]

        Search a regular expression that takes into account non-word characters such as commas

        >>> agnus = re.compile(r'agnus dei\W+filius patris', re.IGNORECASE)
        >>> sm = ls.search(agnus)
        >>> sm
        [SearchMatch(mStart=49, mEnd=55, matchText=...'Agnus Dei, Filius Patris', els=(<music21.note.Note G>,...<music21.note.Note G>), 
                     tups=[IndexedLyric(el=<music21.note.Note G>, start=251, end=252, measure=49, lyric=<...>, text=...'A'), 
                           ...
                           IndexedLyric(el=<music21.note.Note G>, ...text=...'tris.')])]
        >>> sm[0].mStart, sm[0].mEnd
        (49, 55)
        '''
        if s is None:
            s = self.stream
        
        if s is not self.stream or self._indexTuples is None:
            self.index(s)
        
        if isinstance(textOrRe, six.string_types):
            plainText = True
        elif hasattr(textOrRe, 'finditer'):
            plainText = False
        else:
            raise LyricSearcherException('{0} is not a string or RE with the finditer() function'.format(textOrRe))
        
        if plainText is True:
            return self._plainTextSearch(textOrRe)
        else:
            return self._reSearch(textOrRe)
    
    def _findObjInIndexByPos(self, pos):
        '''
        Finds an object in ._indexTuples by search position.
        
        Runs in O(n) time on number of lyrics. Would not be hard to do in O(log(n)) for very large lyrics
        '''
        for i in self._indexTuples:
            if pos >= i.start and pos <= i.end:
                return i

        raise LyricSearcherException("Could not find position {0} in text".format(pos))

    def _findObjsInIndexByPos(self, posStart, posEnd=999999):
        '''
        Finds a list of objects in ._indexTuples by search position (inclusive)        
        '''
        tups = []
        for i in self._indexTuples:
            if i.end >= posStart and i.start <= posEnd:
                tups.append(i)
        if len(tups) == 0:
            raise LyricSearcherException("Could not find position {0} in text".format(posStart))
        return tups

    
    def _plainTextSearch(self, t):
        locs = []
        start = 0
        continueIt = True
        tLen = len(t)
        while continueIt is True:
            foundPos = self._indexText.find(t, start)
            if foundPos == -1:
                continueIt = False
                break
            matchText = self._indexText[foundPos:foundPos+tLen]
            tups = self._findObjsInIndexByPos(foundPos, foundPos + tLen - 1)
            tupStart = tups[0]
            tupEnd = tups[-1]
            
            sm = SearchMatch(mStart=tupStart.measure, mEnd=tupEnd.measure, matchText=matchText, 
                             els=tuple(tup.el for tup in tups), tups=tups)
            locs.append(sm)
            start = foundPos + 1
        
        return locs
    
    def _reSearch(self, r):
        locs = []
        for m in r.finditer(self._indexText):
            foundPos, endPos = m.span()
            matchText = m.group(0)
            tups = self._findObjsInIndexByPos(foundPos, endPos - 1)
            tupStart = tups[0]
            tupEnd = tups[-1]
            
            sm = SearchMatch(mStart=tupStart.measure, mEnd=tupEnd.measure, matchText=matchText, 
                             els=tuple(tup.el for tup in tups), tups=tups)
            locs.append(sm)
        return locs


#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [LyricSearcher]

if __name__ == "__main__":
    import music21
    music21.mainTest()

#------------------------------------------------------------------------------
# eof


                