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



class DateData(object):
    '''Store a date, either as an exact known date, or an approximation or prior to or after representation.
    '''
    # can be approximate, uncertain, before, or after
    # humdrum can specify a certain year but an uncertain day
    # humdrum can specify date as between two dates or one of two dates
    # boudaries can be < prior or > after

    def __init__(self, data='', relevance=None):
        '''
        >>> dd = DateData('10/12/09', 'approximate')
        '''
        self._data = data
    
        # can be approximate, uncertain, before, or after
        self._relevance = relevance
    


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