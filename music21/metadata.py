#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         duration.py
# Purpose:      music21 classes for representing score and work meta-data
#
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
'''Classes and functions for creating and processing score meta data, such as titles, movements, authors, publishers, and regions.
'''


import unittest, doctest
import datetime

from music21 import common


from music21 import environment
_MOD = "metadata.py"
environLocal = environment.Environment(_MOD)





class MetadataException(Exception):
    pass


#-------------------------------------------------------------------------------
class Text(object):
    '''One unit of text data: a title, a name, or some other text data. Store the string and a language name or code.
    '''
    def __init__(self, data='', language=None):
        '''
        >>> td = Text('concerto in d', 'en')
        >>> str(td)
        'concerto in d'
        '''
        self._data = data
        self._language = language
    

    def __str__(self):
        return str(self._data)


#-------------------------------------------------------------------------------
class Date(object):
    '''A single date value, specified by year, month, day, hour, minute, and second. 

    Additionally, each value can be specified as `certain`, `approximate`, and 
    '''
    def __init__(self, *args, **keywords):
        '''
        >>> a = Date(year=1843, yearError='approximate')
        >>> a.year
        1843
        >>> a.yearError
        'approximate'

        '''
        self.year = None
        self.month = None
        self.day = None
        self.hour = None
        self.minute = None
        self.second = None

        # certainty: can be 'approximate', 'uncertain'
        # None is assumed to be certain
        self.yearError = None
        self.monthError = None
        self.dayError = None
        self.hourError = None
        self.minuteError = None
        self.secondError = None

        self.attrValues = ['year', 'month', 'day', 'hour', 'minute', 'second']
        self.attrStrFormat = ['%04.i', '%02.i', '%02.i', 
                              '%02.i', '%02.i', '%006.2f']

        for attr in self.attrValues:
            if attr in keywords.keys():
                setattr(self, attr, keywords[attr])

        self.attrErrors = ['yearError', 'monthError', 'dayError',
             'hourError', 'minuteError', 'secondError']
        for attr in self.attrErrors:
            if attr in keywords.keys():
                setattr(self, attr, keywords[attr])


    def __str__(self):
        # cannot use this, as it does not support dates lower than 1900!
        # self._data.strftime("%Y.%m.%d")
        msg = []

        if self.hour == None and self.minute == None and self.second == None:
            breakIndex = 3 # index

        for i in range(len(self.attrValues)):
            if i >= breakIndex:
                break
            attr = self.attrValues[i]
            value = getattr(self, attr)
            if value == None:
                msg.append('--')
            else:
                fmt = self.attrStrFormat[i]
                msg.append(fmt % value)

        return '.'.join(msg)


    def loadStr(self, str):
        '''Load a string date representation.
        
        Assume year/month/day/hour:minute:second
        '''
        post = []
        if '.' in str:
            for chunk in str.split('.'):
                post.append(chunk) # assume year, month date
        elif '/' in str:
            for chunk in str.split('/'):
                post.append(chunk) # assume year, month date
        post = [int(x) for x in post]

        # assume in order in post list
        for i in range(len(self.attrValues)):
            if len(post) > i: # only assign for those specified
                setattr(self, self.attrValues[i], post[i])


    def _getDatetime(self):
        '''Get a datetime object.
        '''
        post = []
        for attr in self.attrValues:
            # need to be integers
            post.append(int(getattr(self, attr)))
        return datetime.datetime(*post)

    datetime = property(_getDatetime, 
        doc = '''Return a datetime object representation. 
        ''')


#-------------------------------------------------------------------------------
class DateSingle(object):
    '''Store a date, either as certain, approximate, or uncertain.

    '''
# z	value uncertain
# x	value approximate

# ?	date uncertain
# ~	date approximate
# <	sometime prior to
# >	sometime after

# ^	"between" conjunction
# |	"or" conjunction

    isSingle = True

    def __init__(self, data='', relevance='certain'):
        '''
        >>> dd = DateSingle('2009/12/31', 'approximate')
        >>> str(dd)
        '2009.12.31'

        >>> dd = DateSingle('1805.3.12', 'uncertain')
        >>> str(dd)
        '1805.03.12'
        '''
        # store an array of values marking if date data positions
        # are certain or not
        self._dataCertainty = None
        self._data = None
        self._relevance = None # managed by property

        self._prepareData(data)
        self.relevance = relevance # will use property
    


    def _prepareData(self, data):
        '''Assume a string is supplied as argument
        '''
        self._data = Date()
        if common.isStr(data):
            self._data.loadStr(data)

    def _setRelevance(self, value):
        if value in ['certain', 'approximate', 'uncertain']:
            self._relevance = value
        else:
            raise MetadataException('relevance value is not supported by this object: %s' % value)

    def _getRelevance(self):
        return self._relevance

    relevance = property(_getRelevance, _setRelevance)


    def __str__(self):
        return str(self._data)


class DateRelative(DateSingle):
    '''Store a relative date, sometime prior or sometime after
    '''
    isSingle = True

    def __init__(self, data='', relevance='after'):
        '''
        >>> dd = DateRelative('2009/12/31', 'prior')
        >>> str(dd)
        '2009.12.31'

        >>> dd = DateRelative('2009/12/31', 'certain')
        Traceback (most recent call last):
        MetadataException: relevance value is not supported by this object: certain
        '''
        DateSingle.__init__(self, data, relevance)


    def _setRelevance(self, value):
        if value in ['prior', 'after']:
            self._relevance = value
        else:
            raise MetadataException('relevance value is not supported by this object: %s' % value)

    relevance = property(DateSingle._getRelevance, _setRelevance)



class DateBetween(DateSingle):
    '''Store a relative date, sometime between two dates
    '''
    isSingle = False


    def __init__(self, data=[], relevance='between'):
        '''
        >>> dd = DateBetween(['2009/12/31', '2010/1/28'])
        >>> str(dd)
        '2009.12.31 to 2010.01.28'

        >>> dd = DateBetween(['2009/12/31', '2010/1/28'], 'certain')
        Traceback (most recent call last):
        MetadataException: relevance value is not supported by this object: certain
        '''
        DateSingle.__init__(self, data, relevance)

    def _prepareData(self, data):
        '''Assume a list of dates as strings is supplied as argument
        '''
        self._data = []
        for part in data:
            d = Date()
            if common.isStr(part):
                d.loadStr(part)
            self._data.append(d) # a lost of Date objects

    def __str__(self):
        msg = []
        for d in self._data:
            msg.append(str(d))
        return ' to '.join(msg)

    def _setRelevance(self, value):
        if value in ['between']:
            self._relevance = value
        else:
            raise MetadataException('relevance value is not supported by this object: %s' % value)

    relevance = property(DateSingle._getRelevance, _setRelevance)



class DateSelection(DateSingle):
    '''Store a selection of dates, or a collection of dates that might all be possible
    '''
    isSingle = False

    def __init__(self, data='', relevance='or'):
        '''
        >>> dd = DateSelection(['2009/12/31', '2010/1/28', '1894/1/28'], 'or')
        >>> str(dd)
        '2009.12.31 or 2010.01.28 or 1894.01.28'

        >>> dd = DateSelection(['2009/12/31', '2010/1/28'], 'certain')
        Traceback (most recent call last):
        MetadataException: relevance value is not supported by this object: certain
        '''
        DateSingle.__init__(self, data, relevance)

    def _prepareData(self, data):
        '''Assume a list of dates as strings is supplied as argument
        '''
        self._data = []
        for part in data:
            d = Date()
            if common.isStr(part):
                d.loadStr(part)
            self._data.append(d) # a lost of Date objects

    def __str__(self):
        msg = []
        for d in self._data:
            msg.append(str(d))
        return ' or '.join(msg)

    def _setRelevance(self, value):
        if value in ['or']:
            self._relevance = value
        else:
            raise MetadataException('relevance value is not supported by this object: %s' % value)

    relevance = property(DateSingle._getRelevance, _setRelevance)



#-------------------------------------------------------------------------------
class Contributor(object):
    '''A person that contributed to a work. Can be a composer, lyricist, arranger, or other type of contributor. In MusicXML, these are "creator" elements.  
    '''
# !!!COA: Attributed composer.
# !!!COS: Suspected composer.
# !!!COL: Composer abbreviated, alias, 
# !!!COC: Composer(s) corporate name.
# 
# !!!CDT: Composer dates.
# !!!CNT: Nationality of the composer. 
# !!!LYR: Lyricist. 
# !!!LIB: Librettist. 
# !!!LAR: Arranger. 
# !!!LOR: Orchestrator. 
# !!!TRN: Translator of text. 

    def __init__(self):
        '''
        >>> td = Contributor()
        '''
        self._role = None

        # a list of TextData objects to support various spellings or 
        # language translatiions
        self._textData = []

        # store the nationality, if known
        self._nationality = None

        # store birth and death of contributor, if known
        self._dateRange = [None, None]


    def age(self):
        if self._dateRange[0] != None and self._dateRange != None:
            pass
        else:
            return None



class Metadata(object):
    '''Metadata for a work, including title, composer, dates, and other relevant information.
    '''
# !!!TXO: Original language of vocal/choral text. 
# !!!TXL: Language of the encoded vocal/choral text. 

    def __init__(self):
        '''
        >>> md = Metadata()
        '''
        self._textOriginalLanguage = None
        self._textLanguage = None        




#-------------------------------------------------------------------------------

class Test(unittest.TestCase):

    def runTest(self):
        pass



#-------------------------------------------------------------------------------
_DOC_ORDER = [Text]


if __name__ == "__main__":
    import sys
    import music21
    
    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)
    elif len(sys.argv) > 1:
        a = Test()
        a.testAugmentOrDiminish()