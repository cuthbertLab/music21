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
class TextData(object):
    '''One unit of text data: a title, a name, or some other text data. Store the string and a language name or code.
    '''
    def __init__(self, data='', language=None):
        '''
        >>> td = TextData('concerto in d', 'en')
        >>> str(td)
        'concerto in d'
        '''
        self._data = data
        self._language = language
    

    def __str__(self):
        return str(self._data)


#-------------------------------------------------------------------------------
class DateSingle(object):
    '''Store a date, either as an exact known date, or an approximation or prior to or after representation.
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

    def __init__(self, data='', relevance=None):
        '''
        >>> dd = DateSingle('2009/12/31', 'approximate')
        >>> str(dd)
        '2009.12.31'

        >>> dd = DateSingle('1805.3.12', 'approximate')
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
    

    def _strDateToList(self, str):
        post = []
        if '.' in str:
            for chunk in str.split('.'):
                post.append(chunk) # assume year, month date
        elif '/' in str:
            for chunk in str.split('/'):
                post.append(chunk) # assume year, month date
        post = [int(x) for x in post]
        return post

    def _dateTimeToStr(self, dateTimeObj):
        # cannot use this, as it does not support dates lower than 1900!
        # self._data.strftime("%Y.%m.%d")
        msg = []
        msg.append(str(dateTimeObj.year))

        s = '%2i' % dateTimeObj.month
        msg.append(s.replace(' ', '0'))

        s = '%2i' % dateTimeObj.day
        msg.append(s.replace(' ', '0'))
        return '.'.join(msg)

    def _prepareData(self, data):
        '''Assume a string is supplied as argument
        '''
        numerical = [] # a list of year, month, day, hour, min sec
        if common.isStr(data):
            numerical = self._strDateToList(data)
        #environLocal.printDebug(numerical)
        self._data = datetime.datetime(*numerical)

    def _setRelevance(self, value):
        if value in ['certain', 'approximate']:
            self._relevance = value
        else:
            raise MetadataException('relevance value is not supported by this object: %s' % value)

    def _getRelevance(self):
        return self._relevance

    relevance = property(_getRelevance, _setRelevance)


    def __str__(self):
        return self._dateTimeToStr(self._data)


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
        numerical = [] # a list of year, month, day, hour, min sec
        for part in data:
            if common.isStr(part):
                numerical.append(self._strDateToList(part))
        #environLocal.printDebug(numerical)
        self._data = []
        for part in numerical:
            self._data.append(datetime.datetime(*part))


    def __str__(self):
        msg = []
        for part in self._data:
            msg.append(self._dateTimeToStr(part))
        return ' to '.join(msg)


    def _setRelevance(self, value):
        if value in ['between']:
            self._relevance = value
        else:
            raise MetadataException('relevance value is not supported by this object: %s' % value)

    relevance = property(DateSingle._getRelevance, _setRelevance)



class DateSelection(DateSingle):
    '''Store a relative date, or a collection of dates that might all be possible
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
        numerical = [] # a list of year, month, day, hour, min sec
        for part in data:
            if common.isStr(part):
                numerical.append(self._strDateToList(part))
        #environLocal.printDebug(numerical)
        self._data = []
        for part in numerical:
            self._data.append(datetime.datetime(*part))

    def __str__(self):
        msg = []
        for part in self._data:
            msg.append(self._dateTimeToStr(part))
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
_DOC_ORDER = [TextData]


if __name__ == "__main__":
    import sys
    import music21
    
    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)
    elif len(sys.argv) > 1:
        a = Test()
        a.testAugmentOrDiminish()