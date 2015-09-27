# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         text.py
# Purpose:      music21 classes for text processing
#
# Authors:      Michael Scott Cuthbert
# Authors:      Christopher Ariza
#
# Copyright:    Copyright © 2009-2012, 2015 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
Utility routines for processing text in scores and other musical objects. 
'''

import unittest
import os
import random
import codecs

#import music21 # needed to properly do isinstance checking

from music21 import base
from music21 import common
from music21 import exceptions21
from music21 import environment

_MOD = "text.py"  
environLocal = environment.Environment(_MOD)



# using ISO 639-1 Code from here:
# http://www.loc.gov/standards/iso639-2/php/code_list.php
# nice article reference here:
# http://en.wikipedia.org/wiki/Article_(grammar)
articleReference = {
    # arabic
    'ar' : ['al-'],
    # english
    'en' : ['the', 'a', 'an'],
    # german
    'de' : ['der', 'die', 'das', 'des', 'dem', 'den', 'ein', 'eine', 'einer', 'einem', 'einen'],
    # dutch
    'nl' : ['de', 'het', 'een'],
    # spanish
    'es' : ['el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas'],
    # portuguese
    'pt' : ['o', 'a', 'os', 'as', 'um', 'uma', 'uns', 'umas'],
    # french
    'fr' : ['le', 'la', 'les', 'un', 'une', 'des', 'du', 'de la', 'des'],
    # italian
    'it' : ['il', 'lo', 'la', 'i', 'gli', 'le', 'un', 'uno', 'una', 'del', 'dello', 'della', 'dei', 'degli', 'delle'],
    }

#-------------------------------------------------------------------------------
def assembleLyrics(streamIn, lineNumber=1):
    '''
    Concatenate text from a stream. The Stream is automatically flattened. 

    The `lineNumber` parameter determines which line of text is assembled.
    
    
    >>> s = stream.Stream()
    >>> n1 = note.Note()
    >>> n1.lyric = "Hi"
    >>> n2 = note.Note()
    >>> n2.lyric = "there"
    >>> s.append(n1)
    >>> s.append(n2)
    >>> text.assembleLyrics(s)
    'Hi there'
    '''
    word = []
    words = []
    noteStream = streamIn.flat.notesAndRests
    # need to find maximum number of lyrics on each note
    for n in noteStream:
        try:
            lyricObj = n.lyrics[lineNumber-1] # a list of lyric objs
        except IndexError:
            continue
        #environLocal.printDebug(['lyricObj', 'lyricObj.text', lyricObj.text, 'lyricObj.syllabic', lyricObj.syllabic, 'word', word])

        # need to match case of non-defined syllabic attribute
        if lyricObj.text != '_': # continuation syllable in many pieces
            if lyricObj.syllabic in ['begin', 'middle']:
                if lyricObj.text is not None: # should not be possible but sometimes happens
                    word.append(lyricObj.text)
            elif lyricObj.syllabic in ['end', 'single', None]:
                if lyricObj.text is not None: # should not be possible but sometimes happens
                    word.append(lyricObj.text)
                #environLocal.printDebug(['word pre-join', word])
                words.append(''.join(word))
                word = []
            else:
                raise Exception('no known Text syllabic setting: %s' % lyricObj.syllabic)
    return ' '.join(words)
        
def assembleAllLyrics(streamIn, maxLyrics = 10, lyricSeparation='\n'):
    r'''
    Concatenate all Lyrics text from a stream. The Stream is automatically flattened. 

    uses assembleLyrics to do the heavy work.
    
    maxLyrics just determines how many times we should parse through the score, since it is
    not easy to determine what the maximum number of lyrics exist in the score.  

    Here is a demo with one note and five lyrics.

    >>> f = corpus.parse('demos/multiple-verses.xml')
    >>> l = text.assembleAllLyrics(f)
    >>> l
    '\n1. First\n2. Second\n3. Third\n4. Fourth\n5. Fifth'
    '''
    lyrics = ''
    for i in range(1, maxLyrics):
        l = assembleLyrics(streamIn, i)
        if l != '':
            lyrics += lyricSeparation + l
    return lyrics




def prependArticle(src, language=None):
    '''
    Given a text string, if an article is found in a trailing position with a comma, 
    place the article in front and remove the comma. 

    
    >>> text.prependArticle('Ale is Dear, The')
    'The Ale is Dear'
    >>> text.prependArticle('Ale is Dear, The', 'en')
    'The Ale is Dear'
    >>> text.prependArticle('Ale is Dear, The', 'it')
    'Ale is Dear, The'
    >>> text.prependArticle('Combattimento di Tancredi e Clorinda, Il', 'it') 
    'Il Combattimento di Tancredi e Clorinda'
    '''
    if ',' not in src: # must have a comma
        return src

    if language == None: # get all languages?
        ref = []
        for key in articleReference:
            ref += articleReference[key]
    else:
        ref = articleReference[language]

    trailing = src.split(',')[-1].strip()
    match = None
    for candidate in ref:
        if trailing.lower() == candidate:
            match = trailing
            break
    if match != None:
        # recombine everything except the last comma split
        return match + ' ' + ','.join(src.split(',')[:-1])
    else: # not match
        return src


def postpendArticle(src, language=None):
    '''Given a text string, if an article is found in a leading position, place it at the end with a comma. 

    
    >>> text.postpendArticle('The Ale is Dear')
    'Ale is Dear, The'
    >>> text.postpendArticle('The Ale is Dear', 'en')
    'Ale is Dear, The'
    >>> text.postpendArticle('The Ale is Dear', 'it') 
    'The Ale is Dear'
    >>> text.postpendArticle('Il Combattimento di Tancredi e Clorinda', 'it') 
    'Combattimento di Tancredi e Clorinda, Il'
    '''
    if ' ' not in src: # must have at least one space
        return src

    if language == None: # get all languages?
        ref = []
        for key in articleReference:
            ref += articleReference[key]
    else:
        ref = articleReference[language]
    
    leading = src.split(' ')[0].strip()
    match = None
    for candidate in ref:
        if leading.lower() == candidate:
            match = leading
            break
    if match != None:
        # recombine everything except the last comma split
        return ' '.join(src.split(' ')[1:]) + ', %s' % match
    else: # not match
        return src


#-------------------------------------------------------------------------------
class TextException(exceptions21.Music21Exception):
    pass


#-------------------------------------------------------------------------------
class TextFormatException(exceptions21.Music21Exception):
    pass

class TextFormat(object):
    '''
    An object for defining text formatting. 
    This object can be multiple-inherited by objects that need storage and i/o of text settings. 

    See :class:`music21.expressions.TextExpression` for an example. 
    '''
    def __init__(self):
        # these could all be in a text s
        self._justify = None
        self._style = None
        self._weight = None
        self._size = None
        self._letterSpacing = None

        # TODO: a comma separated list; can also be generic font styles
        self._fontFamily = None 

    def _getJustify(self):
        return self._justify    
    
    def _setJustify(self, value):
        if value is None:
            self._justify = None
        else:
            if value.lower() not in ['left', 'center', 'right']:
                raise TextFormatException('Not a supported justification: %s' % value)
            self._justify = value.lower()

    justify = property(_getJustify, _setJustify, 
        doc = '''Get or set the justification.

        
        >>> tf = text.TextFormat()
        >>> tf.justify = 'center'
        >>> tf.justify
        'center'
        ''')

    def _getStyle(self):
        return self._style    
    
    def _setStyle(self, value):
        if value is None:
            self._style = None
        else:
            if value.lower() not in ['italic', 'normal', 'bold', 'bolditalic']:
                raise TextFormatException('Not a supported justification: %s' % value)
            self._style = value.lower()

    style = property(_getStyle, _setStyle, 
        doc = '''Get or set the style, as normal, italic, bold, and bolditalic.

        
        >>> tf = text.TextFormat()
        >>> tf.style = 'bold'
        >>> tf.style
        'bold'
        ''')

    def _getWeight(self):
        return self._weight    
    
    def _setWeight(self, value):
        if value is None:
            self._weight = None
        else:
            if value.lower() not in ['normal', 'bold']:
                raise TextFormatException('Not a supported justification: %s' % value)
            self._weight = value.lower()

    weight = property(_getWeight, _setWeight, 
        doc = '''Get or set the weight, as normal, or bold.

        
        >>> tf = text.TextFormat()
        >>> tf.weight = 'bold'
        >>> tf.weight
        'bold'
        ''')

    def _getSize(self):
        return self._size    
    
    def _setSize(self, value):
        if value is not None:
            try:
                value = float(value)
            except ValueError:
                raise TextFormatException('Not a supported size: %s' % value)
        self._size = value

    size = property(_getSize, _setSize, 
        doc = '''Get or set the size.

        
        >>> tf = text.TextFormat()
        >>> tf.size = 20
        >>> tf.size
        20.0
        ''')

    def _getLetterSpacing(self):
        return self._letterSpacing    
    
    def _setLetterSpacing(self, value):
        
        if value != 'normal' and value is not None:            
            # convert to number
            try:
                value = float(value)
            except ValueError:
                raise TextFormatException('Not a supported size: %s' % value)

        self._letterSpacing = value

    letterSpacing = property(_getLetterSpacing, _setLetterSpacing, 
        doc = '''Get or set the letter spacing.

        
        >>> tf = text.TextFormat()
        >>> tf.letterSpacing = 20
        >>> tf.letterSpacing
        20.0
        >>> tf.letterSpacing = 'normal'
        ''')

#-------------------------------------------------------------------------------
class TextBoxException(exceptions21.Music21Exception):
    pass

#-------------------------------------------------------------------------------
class TextBox(base.Music21Object, TextFormat):
    '''
    A TextBox is arbitrary text that might be positioned anywhere on a page, 
    independent of notes or staffs. A page attribute specifies what page this text is found on; 
    positionVertical and positionHorizontal position the text from the bottom left corner in 
    units of tenths.

    This object is similar to the TextExpression object, but does not have as many position 
    parameters, enclosure attributes, and the ability to convert to 
    RepeatExpressions and TempoTexts. 

    >>> from music21 import text, stream
    >>> y = 1000 # set a fixed vertical distance
    >>> s = stream.Stream()
    >>> # specify character, x position, y position
    >>> tb = text.TextBox('m', 250, y)
    >>> tb.size = 40
    >>> tb.alignVertical = 'bottom'
    >>> s.append(tb)
    >>> tb = text.TextBox('u', 300, y)
    >>> tb.size = 60
    >>> tb.alignVertical = 'bottom'
    >>> s.append(tb)
    >>> tb = text.TextBox('s', 550, y)
    >>> tb.size = 120
    >>> tb.alignVertical = 'bottom'
    >>> s.append(tb)        
    >>> tb = text.TextBox('ic', 700, y)
    >>> tb.alignVertical = 'bottom'
    >>> tb.size = 20
    >>> tb.style = 'italic'
    >>> s.append(tb)
    >>> tb = text.TextBox('21', 850, y)
    >>> tb.alignVertical = 'bottom'
    >>> tb.size = 80
    >>> tb.weight = 'bold'
    >>> tb.style = 'italic'
    >>> s.append(tb)
    >>> #_DOCS_SHOW s.show()

    .. image:: images/textBoxes-01.*
        :width: 600

    '''
    classSortOrder = -31 # text expressions are -30

    def __init__(self, content=None, x=500, y=500):
        base.Music21Object.__init__(self)
        # numerous properties are inherited from TextFormat
        TextFormat.__init__(self)

        # the text string to be displayed; not that line breaks
        # are given in the xml with this non-printing character: (#)
        self._content = None
        self.content = content   # use property

        self._page = 1 # page one is deafault
        self._positionDefaultX = x    
        self._positionDefaultY = y
        self._alignVertical = 'top'
        self._alignHorizontal = 'center'


    def __repr__(self):
        if self._content is not None and len(self._content) > 10:
            return '<music21.text.%s "%s...">' % (self.__class__.__name__, self._content[:10])
        elif self._content is not None:
            return '<music21.text.%s "%s">' % (self.__class__.__name__, self._content)
        else:
            return '<music21.text.%s>' % (self.__class__.__name__)


    def _getContent(self):
        return self._content
    
    def _setContent(self, value):
        if not common.isStr(value):
            self._content = str(value)
        else:
            self._content = value    
    
    content = property(_getContent, _setContent, 
        doc = '''Get or set the content.

        
        >>> te = text.TextBox('testing')
        >>> te.content
        'testing'
        >>> te.justify = 'center'
        >>> te.justify
        'center'

        ''')

    def _getPage(self):
        return self._page
    
    def _setPage(self, value):
        if value != None:
            self._page = int(value) # must be an integer
        # do not set otherwise
    
    page = property(_getPage, _setPage, 
        doc = '''Get or set the page number. The first page (page 1) is the default. 

        
        >>> te = text.TextBox('testing')
        >>> te.content
        'testing'
        >>> te.page
        1
        ''')

    def _getPositionVertical(self):
        return self._positionDefaultY
    
    def _setPositionVertical(self, value):
        if value is not None:
            self._positionDefaultY = value
    
    positionVertical = property(_getPositionVertical, _setPositionVertical, 
        doc = '''
        Get or set the vertical position.

        
        >>> te = text.TextBox('testing')
        >>> te.positionVertical = 1000
        >>> te.positionVertical
        1000
        ''')

    def _getPositionHorizontal(self):
        return self._positionDefaultX
    
    def _setPositionHorizontal(self, value):
        if value is not None:
            self._positionDefaultX = value
    
    positionHorizontal = property(_getPositionHorizontal,     
        _setPositionHorizontal, 
        doc = '''
        Get or set the vertical position.

        
        >>> te = text.TextBox('testing')
        >>> te.positionHorizontal = 200
        >>> te.positionHorizontal
        200

        ''')


    # note: this properties might be moved into the TextFormat object?

    def _getAlignVertical(self):
        return self._alignVertical
    
    def _setAlignVertical(self, value):
        if value in [None, 'top', 'middle', 'bottom', 'baseline']:
            self._alignVertical = value 
        else:
            raise TextBoxException('invalid vertical align: %s' % value)
    
    alignVertical = property(_getAlignVertical, _setAlignVertical, 
        doc = '''
        Get or set the vertical align. Valid values are top, middle, bottom, and baseline

        
        >>> te = text.TextBox('testing')
        >>> te.alignVertical = 'top'
        >>> te.alignVertical
        'top'
        ''')

    def _getAlignHorizontal(self):
        return self._alignHorizontal
    
    def _setAlignHorizontal(self, value):
        if value in [None, 'left', 'right', 'center']:
            self._alignHorizontal = value
        else:
            raise TextBoxException('invalid horizontal align: %s' % value)
    
    alignHorizontal = property(_getAlignHorizontal,     
        _setAlignHorizontal, 
        doc = '''
        Get or set the horicontal align.

        
        >>> te = text.TextBox('testing')
        >>> te.alignHorizontal = 'right'
        >>> te.alignHorizontal
        'right'

        ''')


#-------------------------------------------------------------------------------
class LanguageDetector(object):
    '''
    Attempts to detect language on the basis of trigrams
    
    uses code from 
    http://code.activestate.com/recipes/326576-language-detection-using-character-trigrams/
    unknown author.  No license given.
    
    See Trigram docs below...
    '''
    languageCodes = ['en', 'fr', 'it', 'de', 'cn', 'la', 'nl']
    languageLong = {'en': 'English',
                    'fr': 'French',
                    'it': 'Italian',
                    'de': 'German',
                    'cn': 'Chinese',
                    'la': 'Latin',
                    'nl': 'Dutch',
                    }
    
    def __init__(self, text = None):
        self.text = text
        self.trigrams = {}
        self.readExcerpts()
    
    def readExcerpts(self):
        for languageCode in self.languageCodes:
            thisExcerpt = os.path.join(common.getSourceFilePath(),
                                       'languageExcerpts',
                                       languageCode + '.txt')
            
            with codecs.open(thisExcerpt, encoding='utf-8') as f:
                excerptWords = f.read().split()
                self.trigrams[languageCode] = Trigram(excerptWords)
            
    def mostLikelyLanguage(self, excerpt):
        '''
        returns the code of the most likely language for a passage, works on 
        unicode or ascii. current languages: en, fr, de, it, cn
        
        >>> ld = text.LanguageDetector()
        >>> ld.mostLikelyLanguage("Hello there, how are you doing today? I haven't seen you in a while.")
        'en'
        >>> ld.mostLikelyLanguage("Ciao come stai? Sono molto lento oggi, ma non so perche.")
        'it'
        >>> ld.mostLikelyLanguage("Credo in unum deum. Patrem omnipotentem. Factorum celi et terre")
        'la'
        '''
        excTrigram = Trigram(excerpt)
        maxLang = ""
        maxDifference = 1.0
        for lang in self.languageCodes:
            langDiff = self.trigrams[lang] - excTrigram
            if langDiff < maxDifference:
                maxLang = lang
                maxDifference = langDiff
        
        return maxLang
        

    def mostLikelyLanguageNumeric(self, excerpt = None):
        '''
        returns a number representing the most likely language for a passage
        or 0 if there is no text.
        
        Useful for feature extraction.
        
        The codes are the index of the language name in LanguageDetector.languageCodes + 1
        
        >>> ld = text.LanguageDetector()
        >>> for i in range(0, len(ld.languageCodes)):
        ...    print(str(i+1) + " " +  ld.languageCodes[i])
        1 en
        2 fr
        3 it
        4 de
        5 cn
        6 la
        7 nl
        >>> numLang = ld.mostLikelyLanguageNumeric("Hello there, how are you doing today? I haven't seen you in a while.")
        >>> numLang
        1
        >>> ld.languageCodes[numLang - 1]
        'en'
        '''
        if excerpt is None or excerpt == "":
            return 0
        else:
            langCode = self.mostLikelyLanguage(excerpt)
            for i in range(len(self.languageCodes)):
                if self.languageCodes[i] == langCode:
                    return i+1            
            raise TextException("got a language that was not in the codes; should not happen")

#-------------------------------------------------------------------------------
class Trigram(object):
    '''
    See LanguageDector above.  From http://code.activestate.com/recipes/326576-language-detection-using-character-trigrams/
    
    The frequency of three character
    sequences is calculated.  When treated as a vector, this information
    can be compared to other trigrams, and the difference between them
    seen as an angle.  The cosine of this angle varies between 1 for
    complete similarity, and 0 for utter difference.  Since letter
    combinations are characteristic to a language, this can be used to
    determine the language of a body of text. For example:

    >>> #_DOCS_SHOW reference_en = Trigram('/path/to/reference/text/english')
    >>> #_DOCS_SHOW reference_de = Trigram('/path/to/reference/text/german')
    >>> #_DOCS_SHOW unknown = Trigram('url://pointing/to/unknown/text')
    >>> #_DOCS_SHOW unknown.similarity(reference_de)
    #_DOCS_SHOW 0.4
    >>> #_DOCS_SHOW unknown.similarity(reference_en)
    #_DOCS_SHOW 0.95
    
    would indicate the unknown text is almost cetrtainly English.  As
    syntax sugar, the minus sign is overloaded to return the difference
    between texts, so the above objects would give you:

    #_DOCS_SHOW >>> unknown - reference_de
    #_DOCS_SHOW 0.6
    #_DOCS_SHOW >>> reference_en - unknown    # order doesn't matter.
    #_DOCS_SHOW 0.05

    As it stands, the Trigram ignores character set information, which
    means you can only accurately compare within a single encoding
    (iso-8859-1 in the examples).  A more complete implementation might
    convert to unicode first.

    As an extra bonus, there is a method to make up nonsense words in the
    style of the Trigram's text.

    #_DOCS_SHOW >>> reference_en.makeWords(30)
    #_DOCS_SHOW My withillonquiver and ald, by now wittlectionsurper, may sequia, tory, I ad my notter. Marriusbabilly She lady for rachalle spen hat knong al elf


    '''    

    def __init__(self, excerptList = None):
        self.lut = {}
        self._length = None
        if excerptList is not None:
            self.parseExcerpt(excerptList)

    @property
    def length(self):
        if self._length is None:
            return self.measure()
        else:
            return self._length
        
    def parseExcerpt(self, excerpt):
        pair = u'  '
        if isinstance(excerpt, list):
            for line in excerpt:
                for letter in line.strip() + u' ':
                    d = self.lut.setdefault(pair, {})
                    d[letter] = d.get(letter, 0) + 1
                    pair = pair[1] + letter
        else:
            for letter in excerpt:
                d = self.lut.setdefault(pair, {})
                d[letter] = d.get(letter, 0) + 1
                pair = pair[1] + letter
        self.measure()
    
    def measure(self):
        """calculates the scalar length of the trigram vector and
        stores it in self.length."""
        total = 0
        for y in self.lut.values():
            total += sum([ x * x for x in y.values() ])
        thisLength = total ** 0.5
        self._length = thisLength

    def similarity(self, other):
        """
        returns a number between 0 and 1 indicating similarity between
        two trigrams.
        1 means an identical ratio of trigrams;
        0 means no trigrams in common.
        """
        if not isinstance(other, Trigram):
            raise TypeError("can't compare Trigram with non-Trigram")
        lut1 = self.lut
        lut2 = other.lut
        total = 0
        for k in lut1:
            if k in lut2:
                a = lut1[k]
                b = lut2[k]
                for x in a:
                    if x in b:
                        total += a[x] * b[x]
        
        #environLocal.warn([self.length, "self"])
        #environLocal.warn([other.length, "other"])

        return float(total) / (self.length * other.length)

    def __sub__(self, other):
        """indicates difference between trigram sets; 1 is entirely
        different, 0 is entirely the same."""
        return 1 - self.similarity(other)

    def makeWords(self, count):
        """returns a string of made-up words based on the known text."""
        text = []
        k = '  '
        while count:
            n = self.likely(k)
            text.append(n)
            k = k[1] + n
            if n in ' \t':
                count -= 1
        return ''.join(text)


    def likely(self, k):
        """Returns a character likely to follow the given string
        two character string, or a space if nothing is found."""
        if k not in self.lut:
            return ' '
        # if you were using this a lot, caching would a good idea.
        letters = []
        for k, v in self.lut[k].items():
            letters.append(k * v)
        letters = ''.join(letters)
        return random.choice(letters)



#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testBasic(self):
        from music21 import converter, corpus

        a = converter.parse(corpus.getWork('haydn/opus74no2/movement4.xml'))
        post = assembleLyrics(a)
        self.assertEqual(post, '') # no lyrics!

        a = converter.parse(corpus.getWork('luca/gloria'))
        post = assembleLyrics(a)
        self.assertEqual(post.startswith('Et in terra pax hominibus bone voluntatis'), True) 


    def testAssembleLyricsA(self):
        from music21 import stream, note
        s = stream.Stream()
        for syl in ['hel-', '-lo', 'a-', '-gain']:
            n = note.Note()
            n.lyric = syl
            s.append(n)
        post = assembleLyrics(s)
        self.assertEqual(post, 'hello again')
        
        s = stream.Stream()
        for syl in ['a-', '-ris-', '-to-', '-crats', 'are', 'great']:
            n = note.Note()
            n.lyric = syl
            s.append(n)
        post = assembleLyrics(s)
        self.assertEqual(post, 'aristocrats are great')


    def testLanguageDetector(self):
        ld = LanguageDetector()
        #print ld.trigrams['fr'] - ld.trigrams['it'] 
        #print ld.trigrams['fr'] - ld.trigrams['de'] 
        #print ld.trigrams['fr'] - ld.trigrams['cn'] 
        
        diffFrIt = ld.trigrams['fr'] - ld.trigrams['it']
        self.assertTrue(0.50 < diffFrIt < 0.55)
        self.assertTrue(0.67 < ld.trigrams['fr'] - ld.trigrams['de'] < 0.70)
        self.assertTrue(0.99 < ld.trigrams['fr'] - ld.trigrams['cn'] < 1.0)
        
        self.assertEqual('en', ld.mostLikelyLanguage(u"hello friends, this is a test of the ability of language detector to tell what language I am writing in."))
        self.assertEqual('it', ld.mostLikelyLanguage(u"ciao amici! cosÃ¬ trovo in quale lingua ho scritto questo passaggio. Spero che troverÃ² che Ã¨ stata scritta in italiano"))

        ## TODO: Replace
        #messiahGovernment = corpus.parse('handel/hwv56/movement1-13.md')
        #forUntoUs = assembleLyrics(messiahGovernment)
        #self.assertTrue(forUntoUs.startswith('For unto us a child is born'))
        #forUntoUs = forUntoUs.replace('_', '')
        #self.assertEqual('en', ld.mostLikelyLanguage(forUntoUs))


#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [TextBox, TextFormat]


if __name__ == "__main__":
    import music21
    music21.mainTest(Test)


#------------------------------------------------------------------------------
# eof





