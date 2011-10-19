# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         text.py
# Purpose:      music21 classes for text processing
#
# Authors:      Michael Scott Cuthbert
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2009-2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
'''Utility routines for processing text in scores and other musical objects. 
'''

import doctest, unittest
import os

import music21 # needed to properly do isinstance checking

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
    
    >>> from music21 import *
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
                word.append(lyricObj.text)
            elif lyricObj.syllabic in ['end', 'single', None]:
                word.append(lyricObj.text)
                #environLocal.printDebug(['word pre-join', word])
                words.append(''.join(word))
                word = []
            else:
                raise Exception('no known Text syllabic setting: %s' % lyricObj.syllabic)
    return ' '.join(words)
        

def prependArticle(src, language=None):
    '''Given a text string, if an article is found in a trailing position with a comma, place the article in front and remove the comma. 

    >>> from music21 import *
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
        for key in articleReference.keys():
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

    >>> from music21 import *
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
        for key in articleReference.keys():
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
class TextFormatException(music21.Music21Exception):
    pass

class TextFormat(object):
    '''An object for defining text formatting. This object can be multiple-inherited by objects that need storage and i/o of text settings. 

    See :class:`music21.expressions.TextExpression` for an example. 
    '''
    def __init__(self):
        # these could all be in a text s
        self._justify = None
        self._style = None
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
        doc = '''Get or set the the justification.

        >>> from music21 import *
        >>> tf = TextFormat()
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

        >>> from music21 import *
        >>> tf = TextFormat()
        >>> tf.style = 'bold'
        >>> tf.style
        'bold'
        ''')

    def _getSize(self):
        return self._size    
    
    def _setSize(self, value):
        if value is not None:
            try:
                value = float(value)
            except (ValueError):
                raise TextFormatException('Not a supported size: %s' % value)
        self._size = value

    size = property(_getSize, _setSize, 
        doc = '''Get or set the size.

        >>> from music21 import *
        >>> tf = TextFormat()
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
            except (ValueError):
                raise TextFormatException('Not a supported size: %s' % value)

        self._letterSpacing = value

    letterSpacing = property(_getLetterSpacing, _setLetterSpacing, 
        doc = '''Get or set the letter spacing.

        >>> from music21 import *
        >>> tf = TextFormat()
        >>> tf.letterSpacing = 20
        >>> tf.letterSpacing
        20.0
        >>> tf.letterSpacing = 'normal'
        ''')


#     def _getMxParameters(self):
#         '''Return a dictionary with the attribute of this object notated as needed for MusicXML output
# 
#         >>> from music21 import *
#         >>> tf = TextFormat()
#         >>> tf.style = 'bolditalic'
#         >>> tf._getMxParameters()['font-weight']
#         'bold'
#         >>> tf._getMxParameters()['font-style']
#         'italic'
#         '''
#         post = {}
#         post['justify'] = self._justify
# 
#         post['font-style'] = 'normal'
#         post['font-weight'] = 'normal'
#         if self._style == 'normal':
#             pass            
#         elif self._style == 'italic':
#             post['font-style'] = 'italic'
#         elif self._style == 'bold':
#             post['font-weight'] = 'bold'
#         elif self._style == 'bolditalic':
#             post['font-weight'] = 'bold'
#             post['font-style'] = 'italic'
# 
#         post['font-size'] = self._getSize()
#         post['letter-spacing'] = self._getLetterSpacing()
# 
#         # font family not yet being specified
#         return post


class LanguageDetector(object):
    '''
    attempts to detect language on the basis of trigrams
    
    uses code from 
    http://code.activestate.com/recipes/326576-language-detection-using-character-trigrams/
    unknown author.  No license given.
    
    
    '''
    languageCodes = ['en', 'fr', 'it', 'de', 'cn']
    languageLong = {'en': 'English',
                    'fr': 'French',
                    'it': 'Italian',
                    'de': 'German',
                    'cn': 'Chinese',}
    
    def __init__(self, text = None):
        self.text = text
        self.trigrams = {}
        self.readExcerpts()
    
    def readExcerpts(self):
        for languageCode in self.languageCodes:
            pair = '  '
            f = open(os.path.dirname(music21.languageExcerpts.__file__) + os.path.sep + languageCode + '.txt')                
            self.trigrams[languageCode] = Trigram(f.read().split())
            f.close()

    def mostLikelyLanguage(self, excerpt):
        '''
        returns the code of the most likely language for a passage, works on unicode or ascii.
        current languages: en, fr, de, it, cn

        >>> from music21 import *
        >>> ld = text.LanguageDetector()
        >>> ld.mostLikelyLanguage("Hello there, how are you doing today? I haven't seen you in a while.")
        'en'
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
        
        >>> ld = LanguageDetector()
        >>> for i in range(0, len(ld.languageCodes)):
        ...    print i+1, ld.languageCodes[i]
        1 en
        2 fr
        3 it
        4 de
        5 cn
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
            else:
                raise TextException("got a language that was not in the codes; should not happen")

class Trigram(object):
    '''the frequency of three character
    sequences is calculated.  When treated as a vector, this information
    can be compared to other trigrams, and the difference between them
    seen as an angle.  The cosine of this angle varies between 1 for
    complete similarity, and 0 for utter difference.  Since letter
    combinations are characteristic to a language, this can be used to
    determine the language of a body of text. For example:

        #>>> reference_en = Trigram('/path/to/reference/text/english')
        #>>> reference_de = Trigram('/path/to/reference/text/german')
        #>>> unknown = Trigram('url://pointing/to/unknown/text')
        #>>> unknown.similarity(reference_de)
        #0.4
        #>>> unknown.similarity(reference_en)
        #0.95
    
    would indicate the unknown text is almost cetrtainly English.  As
    syntax sugar, the minus sign is overloaded to return the difference
    between texts, so the above objects would give you:

    #>>> unknown - reference_de
    #0.6
    #>>> reference_en - unknown    # order doesn't matter.
    #0.05

    As it stands, the Trigram ignores character set information, which
    means you can only accurately compare within a single encoding
    (iso-8859-1 in the examples).  A more complete implementation might
    convert to unicode first.

    As an extra bonus, there is a method to make up nonsense words in the
    style of the Trigram's text.

    #>>> reference_en.makeWords(30)
    My withillonquiver and ald, by now wittlectionsurper, may sequia,
    tory, I ad my notter. Marriusbabilly She lady for rachalle spen
    hat knong al elf
    '''    

    def __init__(self, excerptList = None):
        self.lut = {}
        if excerptList is not None:
            self.parseExcerpt(excerptList)

    
    def parseExcerpt(self, excerpt):
        pair = u'  '
        if isinstance(excerpt, list):
            for line in excerpt:
                try:
                    line = unicode(line, 'utf8') # just in case
                except UnicodeDecodeError:
                    continue # skip this line
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
        self.length = total ** 0.5

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

#---------------------------------------
class TextException(music21.Music21Exception):
    pass


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
        from music21 import text, stream, note
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
        from music21 import corpus
        ld = LanguageDetector()
        ld.trigrams
        #print ld.trigrams['fr'] - ld.trigrams['it'] 
        #print ld.trigrams['fr'] - ld.trigrams['de'] 
        #print ld.trigrams['fr'] - ld.trigrams['cn'] 
        
        self.assertTrue(0.50 < ld.trigrams['fr'] - ld.trigrams['it'] < 0.55)
        self.assertTrue(0.67 < ld.trigrams['fr'] - ld.trigrams['de'] < 0.70)
        self.assertTrue(0.99 < ld.trigrams['fr'] - ld.trigrams['cn'] < 1.0)
        
        self.assertEqual('en', ld.mostLikelyLanguage(u"hello friends, this is a test of the ability of language detector to tell what language I am writing in."))
        self.assertEqual('it', ld.mostLikelyLanguage(u"ciao amici! così trovo in quale lingua ho scritto questo passaggio. Spero che troverò che è stata scritta in italiano"))

        messiahGovernment = corpus.parse('handel/hwv56/movement1-13.md')
        forUntoUs = assembleLyrics(messiahGovernment)
        self.assertTrue(forUntoUs.startswith('For unto us a child is born'))
        forUntoUs = forUntoUs.replace('_', '')
        self.assertEqual('en', ld.mostLikelyLanguage(forUntoUs))

if __name__ == "__main__":
    music21.mainTest(Test)


#------------------------------------------------------------------------------
# eof





