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
'''Classes and functions for creating and processing metadata associated with scores, works, and fragments, such as titles, movements, authors, publishers, and regions.

The :class:`~music21.metadata.Metadata` object is the main public interface to metadata components. A Metadata object can be added to a Stream and used to set common score attributes, such as title and composer. A Metadata object found at offset zero can be accessed through a Stream's :attr:`~music21.stream.Stream.metadata` property. 

The following example creates a :class:`~music21.stream.Stream` object, adds a :class:`~music21.note.Note` object, and configures and adds the :attr:`~music21.metadata.Metadata.title` and :attr:`~music21.metadata.Metadata.composer` properties of a Metadata object. 

>>> from music21 import *
>>> s = stream.Stream()
>>> s.append(note.Note())
>>> s.insert(metadata.Metadata())
>>> s.metadata.title = 'title'
>>> s.metadata.composer = 'composer'
>>> #_DOCS_SHOW s.show()

.. image:: images/moduleMetadata-01.*
    :width: 600

'''


import unittest, doctest
import datetime
import json
import os
import inspect
import re

import music21
from music21 import common
from music21 import musicxml
from music21 import text


from music21 import environment
_MOD = "metadata.py"
environLocal = environment.Environment(_MOD)



#-------------------------------------------------------------------------------
class MetadataException(Exception):
    pass


#-------------------------------------------------------------------------------
# utility dictionaries and conversion functions; used by objects defined in this
# module

# error can be designated with either symbol in string date representations
APPROXIMATE = ['~', 'x']
UNCERTAIN = ['?', 'z']

def errorToSymbol(value):
    '''Convert an error string (appoximate, uncertain) into a symbol.

    >>> errorToSymbol('approximate')
    '~'
    >>> errorToSymbol('uncertain')
    '?'
    '''
    if value.lower() in APPROXIMATE + ['approximate']:
        return APPROXIMATE[0]
    if value.lower() in UNCERTAIN + ['uncertain']:
        return UNCERTAIN[0]


roleAbbreviationsDict = {
    'com' : 'composer',
    'coa' : 'attributedComposer',
    'cos' : 'suspectedComposer',
    'col' : 'composerAlias',
    'coc' : 'composerCorporate',
    'lyr' : 'lyricist',
    'lib' : 'librettist',
    'lar' : 'arranger',
    'lor' : 'orchestrator',
    'trn' : 'translator',
    }
# !!!COM: Composer's name.
# !!!COA: Attributed composer.
# !!!COS: Suspected composer.
# !!!COL: Composer abbreviated, alias, 
# !!!COC: Composer(s) corporate name.
# !!!LYR: Lyricist. 
# !!!LIB: Librettist. 
# !!!LAR: Arranger. 
# !!!LOR: Orchestrator. 
# !!!TRN: Translator of text. 

# contributors can have ROLE_ABBREVIATIONS
ROLE_ABBREVIATIONS = roleAbbreviationsDict.keys()
ROLES = roleAbbreviationsDict.values()

def abbreviationToRole(value):
    '''Get ROLE_ABBREVIATIONS as string-like attributes, used for Contributors. 

    >>> abbreviationToRole('com')
    'composer'
    >>> abbreviationToRole('lib')
    'librettist'
    >>> for id in ROLE_ABBREVIATIONS: 
    ...    post = abbreviationToRole(id)
    '''
    value = value.lower()
    if value in roleAbbreviationsDict.keys():
        return roleAbbreviationsDict[value]
    else:
        raise MetadataException('no such role: %s' % value)


def roleToAbbreviation(value):
    '''Get a role id from a string representation.

    >>> roleToAbbreviation('composer')
    'com'
    >>> for n in ROLES:
    ...     post = roleToAbbreviation(n)
    '''
    # note: probably not the fastest way to do this
    for id in ROLE_ABBREVIATIONS:
        if value.lower() == roleAbbreviationsDict[id].lower():
            return id
    raise MetadataException('no such role: %s' % value)


workIdAbbreviationDict = {
    'otl' : 'title',
    'otp' : 'popularTitle',
    'ota' : 'alternativeTitle',
    'opr' : 'parentTitle',
    'oac' : 'actNumber',

    'osc' : 'sceneNumber',
    'omv' : 'movementNumber',
    'omd' : 'movementName',
    'ops' : 'opusNumber',
    'onm' : 'number',

    'ovm' : 'volume',
    'ode' : 'dedication',
    'oco' : 'commission',
    'gtl' : 'groupTitle',
    'gaw' : 'associatedWork',

    'gco' : 'collectionDesignation',
    'txo' : 'textOriginalLanguage',
    'txl' : 'textLanguage',

    'ocy' : 'countryOfComposition',
    'opc' : 'localeOfComposition', # origin in abc
    }

# store a reference dictionary for quick lookup, with full attr names
# as keys
workIdLookupDict = {}
for key, value in workIdAbbreviationDict.items(): 
    workIdLookupDict[value.lower()] = key

# !!!OTL: Title. 
# !!!OTP: Popular Title.
# !!!OTA: Alternative title.
# !!!OPR: Title of larger (or parent) work 
# !!!OAC: Act number.
# !!!OSC: Scene number.
# !!!OMV: Movement number.
# !!!OMD: Movement designation or movement name. 
# !!!OPS: Opus number. 
# !!!ONM: Number.
# !!!OVM: Volume.
# !!!ODE: Dedication. 
# !!!OCO: Commission
# !!!GTL: Group Title. 
# !!!GAW: Associated Work. 
# !!!GCO: Collection designation. 
# !!!TXO: Original language of vocal/choral text. 
# !!!TXL: Language of the encoded vocal/choral text. 
# !!!OCY: Country of composition. 
# !!!OPC: City, town or village of composition. 

WORK_ID_ABBREVIATIONS = workIdAbbreviationDict.keys()
WORK_IDS = workIdAbbreviationDict.values()

def abbreviationToWorkId(value):
    '''Get work id abbreviations.

    >>> abbreviationToWorkId('otl')
    'title'
    >>> for id in WORK_ID_ABBREVIATIONS: 
    ...    post = abbreviationToWorkId(id)
    '''
    value = value.lower()
    if value in workIdAbbreviationDict.keys():
        return workIdAbbreviationDict[value]
    else:
        raise MetadataException('no such work id: %s' % value)

def workIdToAbbreviation(value):
    '''Get a role id from a string representation.

    >>> workIdToAbbreviation('localeOfComposition')
    'opc'
    >>> for n in WORK_IDS:
    ...     post = workIdToAbbreviation(n)
    '''
    # NOTE: this is a performance critical function
    try:
        # try direct access, where keys are already lower case
        return workIdLookupDict[value] 
    except KeyError:
        pass

    # slow approach
    for id in WORK_ID_ABBREVIATIONS:
        if value.lower() == workIdAbbreviationDict[id].lower():
            return id
    raise MetadataException('no such role: %s' % value)









#-------------------------------------------------------------------------------
class Text(music21.JSONSerializer):
    '''One unit of text data: a title, a name, or some other text data. Store the string and a language name or code. This object can be used and/or subclassed for a variety for of text storage.
    '''
    def __init__(self, data='', language=None):
        '''
        >>> td = Text('concerto in d', 'en')
        >>> str(td)
        'concerto in d'
        '''
        if isinstance(data, Text): # if this is a Text obj, get data
            # accessing private attributes here; not desirable
            self._data = data._data
            self._language = data._language
        else:            
            self._data = data
            self._language = language

    def __str__(self):
        #print type(self._data)
        if isinstance(self._data, unicode):
            return str(self._data.encode('utf-8'))
        else:
            return str(self._data)

    def _setLanguage(self, value):
        self._language = value

    def _getLanguage(self):
        return self._language

    language = property(_getLanguage, _setLanguage, 
        doc = '''Set the language of the Text stored within.

        >>> t = Text('my text')
        >>> t.language = 'en'
        >>> t.language  
        'en'
        ''')

    def getNormalizedArticle(self):
        '''Return a string representation with normalized articles.

        >>> from music21 import *
        >>> td = metadata.Text('Ale is Dear, The', 'en')
        >>> str(td)
        'Ale is Dear, The'
        >>> td.getNormalizedArticle()
        'The Ale is Dear'
        '''
        return text.prependArticle(self.__str__(), self._language)

    #---------------------------------------------------------------------------

    def jsonAttributes(self):
        '''Define all attributes of this object that should be JSON serialized for storage and re-instantiation. Attributes that name basic Python objects or :class:`~music21.base.JSONSerializer` subclasses, or dictionaries or lists that contain Python objects or :class:`~music21.base.JSONSerializer` subclasses, can be provided.
        '''
        return ['_data', '_language']





#-------------------------------------------------------------------------------
class Date(music21.JSONSerializer):
    '''A single date value, specified by year, month, day, hour, minute, and second. Note that this class has been created, instead of using Python's datetime, to provide greater flexibility for processing unconventional dates, ancient dates, dates with error, and date ranges. 

    The :attr:`~music21.metadata.Date.datetime` property can be used to retrieve a datetime object when necessary.

    Additionally, each value can be specified as `uncertain` or `approximate`; if None, assumed to be certain.

    Data objects are fundamental components of :class:`~music21.metadata.DateSingle` and related subclasses that represent single dates and date ranges. 

    '''
    def __init__(self, *args, **keywords):
        '''
        >>> from music21 import *
        >>> a = metadata.Date(year=1843, yearError='approximate')
        >>> a.year
        1843
        >>> a.yearError
        'approximate'

        >>> a = metadata.Date(year='1843?')
        >>> a.yearError
        'uncertain'

        '''
        self.year = None
        self.month = None
        self.day = None
        self.hour = None
        self.minute = None
        self.second = None

        # error: can be 'approximate', 'uncertain'
        # None is assumed to be certain
        self.yearError = None
        self.monthError = None
        self.dayError = None
        self.hourError = None
        self.minuteError = None
        self.secondError = None

        self.attrNames = ['year', 'month', 'day', 'hour', 'minute', 'second']
        # format strings for data components
        self.attrStrFormat = ['%04.i', '%02.i', '%02.i', 
                              '%02.i', '%02.i', '%006.2f']

        # set any keywords supplied
        for attr in self.attrNames:
            if attr in keywords.keys():
                value, error = self._stripError(keywords[attr])
                setattr(self, attr, value)
                if error != None:
                    setattr(self, attr+'Error', error)            
        for attr in self.attrNames:
            attr = attr + 'Error'
            if attr in keywords.keys():
                setattr(self, attr, keywords[attr])

    def _stripError(self, value):
        '''Strip error symbols from a numerical value. Return cleaned source and sym. Only one error symbol is expected per string.

        >>> d = Date()
        >>> d._stripError('1247~')
        ('1247', 'approximate')
        >>> d._stripError('234.43?')
        ('234.43', 'uncertain')
        >>> d._stripError('234.43')
        ('234.43', None)

        '''
        if common.isNum(value): # if a number, let pass
            return value, None
        else:
            str = value
        sym = APPROXIMATE + UNCERTAIN
        found = None
        for char in str:
            if char in sym:
                found = char
                break
        if found == None:
            return str, None
        elif found in APPROXIMATE:
            str = str.replace(found, '')
            return  str, 'approximate'
        elif found in UNCERTAIN:
            str = str.replace(found, '')
            return  str, 'uncertain'

    def _getHasTime(self):
        if self.hour != None or self.minute != None or self.second != None:
            return True
        else:
            return False
       
    hasTime = property(_getHasTime, 
        doc = '''Return True if any time elements are defined.

        >>> a = Date(year=1843, month=3, day=3)
        >>> a.hasTime
        False
        >>> b = Date(year=1843, month=3, day=3, minute=3)
        >>> b.hasTime
        True
        ''')

    def _getHasError(self):
        for attr in self.attrNames:
            if getattr(self, attr+'Error') != None:
                return True
        return False
       
    hasError = property(_getHasError, 
        doc = '''Return True if any data points have error defined. 

        >>> a = Date(year=1843, month=3, day=3, dayError='approximate')
        >>> a.hasError
        True
        >>> b = Date(year=1843, month=3, day=3, minute=3)
        >>> b.hasError
        False
        ''')

    def __str__(self):
        '''Return a string representation, including error if defined. 

        >>> d = Date()
        >>> d.loadStr('3030?/12~/?4')
        >>> str(d)
        '3030?/12~/04?'
        '''
        # datetime.strftime("%Y.%m.%d")
        # cannot use this, as it does not support dates lower than 1900!
        msg = []

        if self.hour == None and self.minute == None and self.second == None:
            breakIndex = 3 # index

        for i in range(len(self.attrNames)):
            if i >= breakIndex:
                break
            attr = self.attrNames[i]
            value = getattr(self, attr)
            error = getattr(self, attr+'Error')
            if value == None:
                msg.append('--')
            else:
                fmt = self.attrStrFormat[i]
                if error != None:
                    sub = fmt % value + errorToSymbol(error)
                else:
                    sub = fmt % value
                msg.append(sub)

        return '/'.join(msg)


    def loadStr(self, str):
        '''Load a string date representation.
        
        Assume year/month/day/hour:minute:second

        >>> from music21 import *
        >>> d = metadata.Date()
        >>> d.loadStr('3030?/12~/?4')
        >>> d.month, d.monthError
        (12, 'approximate')
        >>> d.year, d.yearError
        (3030, 'uncertain')
        >>> d.month, d.monthError
        (12, 'approximate')
        >>> d.day, d.dayError
        (4, 'uncertain')

        >>> d = metadata.Date()
        >>> d.loadStr('1834/12/4/4:50:32')
        >>> d.minute, d.second
        (50, 32)

        '''
        post = []
        postError = []

        str = str.replace(':', '/')
        str = str.replace(' ', '')

        for chunk in str.split('/'):
            value, error = self._stripError(chunk)
            post.append(value) 
            postError.append(error)

        # as error is stripped, we can now convert to numbers
        if len(post) > 0 and post[0] != '':
            post = [int(x) for x in post]

        # assume in order in post list
        for i in range(len(self.attrNames)):
            if len(post) > i: # only assign for those specified
                setattr(self, self.attrNames[i], post[i])
                if postError[i] != None:
                    setattr(self, self.attrNames[i]+'Error', postError[i])            


    def loadDatetime(self, dt):
        '''Load time data from a datetime object.

        >>> import datetime
        >>> dt = datetime.datetime(2005, 02, 01)
        >>> dt
        datetime.datetime(2005, 2, 1, 0, 0)
        >>> a = Date()
        >>> a.loadDatetime(dt)
        >>> str(a)
        '2005/02/01'
        '''
        for attr in self.attrNames:
            if hasattr(dt, attr):
                # names here are the same, so we can directly map
                value = getattr(dt, attr)
                if value not in [0, None]:
                    setattr(self, attr, value)

    def loadOther(self, other):
        '''Load values based on another Date object:

        >>> a = Date(year=1843, month=3, day=3)
        >>> b = Date()
        >>> b.loadOther(a)
        >>> b.year
        1843
        '''
        for attr in self.attrNames:
            if getattr(other, attr) != None:
                setattr(self, attr, getattr(other, attr))

    def load(self, value):
        '''Load values by string, datetime object, or Date object.

        >>> a = Date(year=1843, month=3, day=3)
        >>> b = Date()
        >>> b.load(a)
        >>> b.year
        1843
        '''

        if isinstance(value, datetime.datetime):
            self.loadDatetime(value)
        elif common.isStr(value):
            self.loadStr(value)
        elif isinstance(value, Date):
            self.loadOther(value)
        else:
            raise MetadataException('cannot load data: %s' % value)    
    
    def _getDatetime(self):
        '''Get a datetime object.

        >>> a = Date(year=1843, month=3, day=3)
        >>> str(a)
        '1843/03/03'
        >>> a.datetime
        datetime.datetime(1843, 3, 3, 0, 0)

        >>> a = Date(year=1843, month=3)
        >>> str(a)
        '1843/03/--'
        '''
        post = []
        # order here is order for datetime
        # TODO: need defaults for incomplete times. 
        for attr in self.attrNames:
            # need to be integers
            value = getattr(self, attr)
            if value == None:
                break
            post.append(int(value))
        return datetime.datetime(*post)

    datetime = property(_getDatetime, 
        doc = '''Return a datetime object representation. 

        >>> a = Date(year=1843, month=3, day=3)
        >>> a.datetime
        datetime.datetime(1843, 3, 3, 0, 0)
        ''')


    #---------------------------------------------------------------------------
    # overridden methods for json processing 

    def jsonAttributes(self):
        '''Define all attributes of this object that should be JSON serialized for storage and re-instantiation. Attributes that name basic Python objects or :class:`~music21.base.JSONSerializer` subclasses, or dictionaries or lists that contain Python objects or :class:`~music21.base.JSONSerializer` subclasses, can be provided.
        '''
        return ['year', 'month', 'day', 'hour', 'minute', 'second',
                'yearError', 'monthError', 'dayError', 'hourError', 'minuteError', 'secondError']




#-------------------------------------------------------------------------------
class DateSingle(music21.JSONSerializer):
    '''Store a date, either as certain, approximate, or uncertain relevance.

    The relevance attribute is limited within each DateSingle subclass depending on the design of the class. Alternative relevance types should be configured as other DateSingle subclasses. 
    '''
    isSingle = True

    def __init__(self, data='', relevance='certain'):
        '''
        >>> dd = DateSingle('2009/12/31', 'approximate')
        >>> str(dd)
        '2009/12/31'
        >>> dd.relevance
        'approximate'

        >>> dd = DateSingle('1805/3/12', 'uncertain')
        >>> str(dd)
        '1805/03/12'
        '''
        self._data = [] # store a list of one or more Date objects
        self._relevance = None # managed by property

        # not yet implemented
        # store an array of values marking if date data itself
        # is certain, approximate, or uncertain
        # here, dataError is relevance
        self._dataError = [] # store a list of one or more strings

        self._prepareData(data)
        self.relevance = relevance # will use property
    
    def _prepareData(self, data):
        '''Assume a string is supplied as argument
        '''
        # here, using a list to store one object; this provides more 
        # compatability  w/ other formats
        self._data = [] # clear list
        self._data.append(Date())
        self._data[0].load(data)

    def _setRelevance(self, value):
        if value in ['certain', 'approximate', 'uncertain']:
            self._relevance = value
            self._dataError = []
            self._dataError.append(value) # only here is dataError the same as relevance
        else:
            raise MetadataException('relevance value is not supported by this object: %s' % value)

    def _getRelevance(self):
        return self._relevance

    relevance = property(_getRelevance, _setRelevance)

    def __str__(self):
        return str(self._data[0]) # always the first

    def _getDatetime(self):
        '''Get a datetime object.

        >>> a = Date(year=1843, month=3, day=3)
        >>> str(a)
        '1843/03/03'
        >>> a.datetime
        datetime.datetime(1843, 3, 3, 0, 0)

        >>> a = Date(year=1843, month=3)
        >>> str(a)
        '1843/03/--'
        '''
        # get from stored Date object
        return self._data[0].datetime

    datetime = property(_getDatetime, 
        doc = '''Return a datetime object representation. 

        >>> d = Date(year=1843, month=3, day=3)
        >>> ds = DateSingle(d)
        >>> ds.datetime
        datetime.datetime(1843, 3, 3, 0, 0)
        ''')


    #---------------------------------------------------------------------------
    # overridden methods for json processing 

    def jsonAttributes(self):
        '''Define all attributes of this object that should be JSON serialized for storage and re-instantiation. Attributes that name basic Python objects or :class:`~music21.base.JSONSerializer` subclasses, or dictionaries or lists that contain Python objects or :class:`~music21.base.JSONSerializer` subclasses, can be provided.
        '''
        return ['_relevance',  '_dataError', '_data'] 

    def jsonComponentFactory(self, idStr):
        if '.Date' in idStr:
            return Date()
        else:
            raise MetadataException('cannot instantiate an object from id string: %s' % idStr)






class DateRelative(DateSingle):
    '''Store a relative date, sometime prior or sometime after
    '''
    isSingle = True

    def __init__(self, data='', relevance='after'):
        '''
        >>> dd = DateRelative('2009/12/31', 'prior')
        >>> str(dd)
        '2009/12/31'

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
        '2009/12/31 to 2010/01/28'

        >>> dd = DateBetween(['2009/12/31', '2010/1/28'], 'certain')
        Traceback (most recent call last):
        MetadataException: relevance value is not supported by this object: certain
        '''
        DateSingle.__init__(self, data, relevance)

    def _prepareData(self, data):
        '''Assume a list of dates as strings is supplied as argument
        '''
        self._data = []
        self._dataError = []
        for part in data:
            d = Date()
            d.load(part)
            self._data.append(d) # a list of Date objects
            # can look at Date and determine overall error
            self._dataError.append(None)


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
        '2009/12/31 or 2010/01/28 or 1894/01/28'

        >>> dd = DateSelection(['2009/12/31', '2010/1/28'], 'certain')
        Traceback (most recent call last):
        MetadataException: relevance value is not supported by this object: certain
        '''
        DateSingle.__init__(self, data, relevance)

    def _prepareData(self, data):
        '''Assume a list of dates as strings is supplied as argument
        '''
        self._data = []
        self._dataError = []
        for part in data:
            d = Date()
            d.load(part)
            self._data.append(d) # a lost of Date objects
            # can look at Date and determine overall error
            self._dataError.append(None)

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
class Contributor(music21.JSONSerializer):
    '''A person that contributed to a work. Can be a composer, lyricist, arranger, or other type of contributor. In MusicXML, these are "creator" elements.  
    '''
    relevance = 'contributor'

    def __init__(self, *args, **keywords ):
        '''
        >>> td = Contributor(role='composer', name='Chopin, Fryderyk')
        >>> td.role
        'composer'
        >>> td.name
        'Chopin, Fryderyk'
        >>> td.relevance
        'contributor'

        '''
        if 'role' in keywords.keys():
            # stored in self._role
            self.role = keywords['role'] # validated with property
        else:
            self.role = None

        # a list of Text objects to support various spellings or 
        # language translatiions
        self._names = []
        if 'name' in keywords.keys(): # a single
            self._names.append(Text(keywords['name']))
        if 'names' in keywords.keys(): # many
            for n in keywords['names']:
                self._names.append(Text(n))

        # store the nationality, if known
        self._nationality = []

        # store birth and death of contributor, if known
        self._dateRange = [None, None]
        if 'birth' in keywords.keys():
            self._dateRange[0] = DateSingle(keywords['birth'])
        if 'death' in keywords.keys():
            self._dateRange[1] = DateSingle(keywords['death'])

    def _getRole(self):
        return self._role

    def _setRole(self, value):
        if value == None or value in ROLES:
            self._role = value
        elif value in ROLE_ABBREVIATIONS:
            self._role = roleAbbreviationsDict[value]
        else:
            raise MetadataException('role value is not supported by this object: %s' % value)

    role = property(_getRole, _setRole, 
        doc = '''The role is what part this Contributor plays in the work. Both full roll strings and roll abbreviations may be used.

        >>> td = Contributor()
        >>> td.role = 'composer'
        >>> td.role
        'composer'
        >>> td.role = 'lor'
        >>> td.role
        'orchestrator'
        ''')

    def _setName(self, value):
        # return first name
        self._names = [] # reset
        self._names.append(Text(value))

    def _getName(self):
        # return first name
        return str(self._names[0])

    name = property(_getName, _setName,
        doc = '''Returns the text name, or the first of many names entered. 

        >>> td = Contributor(role='composer', names=['Chopin, Fryderyk', 'Chopin, Frederick'])
        >>> td.name
        'Chopin, Fryderyk'
        >>> td.names
        ['Chopin, Fryderyk', 'Chopin, Frederick']

        ''')

    def _getNames(self):
        # return first name
        msg = []
        for n in self._names:
            msg.append(str(n))
        return msg

    names = property(_getNames, 
        doc = '''Returns all names in a list.

        >>> td = Contributor(role='composer', names=['Chopin, Fryderyk', 'Chopin, Frederick'])
        >>> td.names
        ['Chopin, Fryderyk', 'Chopin, Frederick']
        ''')

    def age(self):
        '''Calculate the age of the Contributor, returning a datetime.timedelta object.

        >>> a = Contributor(name='Beethoven, Ludwig van', role='composer', birth='1770/12/17', death='1827/3/26')
        >>> a.role
        'composer'
        >>> a.age()
        datetime.timedelta(20552)
        >>> str(a.age())
        '20552 days, 0:00:00'
        >>> a.age().days / 365
        56
        '''
        if self._dateRange[0] != None and self._dateRange[1] != None:
            b = self._dateRange[0].datetime
            d = self._dateRange[1].datetime
            return d-b
        else:
            return None


    #---------------------------------------------------------------------------
    # overridden methods for json processing 

    def jsonAttributes(self):
        '''Define all attributes of this object that should be JSON serialized for storage and re-instantiation. Attributes that name basic Python objects or :class:`~music21.base.JSONSerializer` subclasses, or dictionaries or lists that contain Python objects or :class:`~music21.base.JSONSerializer` subclasses, can be provided.
        '''
        return ['_role', 'relevance', '_names', '_dateRange']


    def jsonComponentFactory(self, idStr):
        if '.Text' in idStr:
            return Text()
        else:
            raise MetadataException('cannot instantiate an object from id string: %s' % idStr)




    #---------------------------------------------------------------------------

    def _getMX(self):
        '''Return a mxCreator object based on this object. 

        >>> from music21 import *
        >>> md = metadata.Metadata()
        >>> md.composer = 'frank'
        >>> mxCreator = md._contributors[0].mx
        >>> mxCreator.get('charData')
        'frank'
        >>> mxCreator.get('type')
        'composer'
        '''
        mxCreator = musicxml.Creator()
        # not sure what do if we have multiple names
        mxCreator.set('type', self.role)
        mxCreator.set('charData', self.name)        
        return mxCreator

    def _setMX(self, mxCreator):
        '''Given an mxCreator, fill the necessary parameters of a Contributor.

        >>> from music21 import *
        >>> from music21 import musicxml
        >>> mxCreator = musicxml.Creator()
        >>> mxCreator.set('type', 'composer')
        >>> mxCreator.set('charData', 'Beethoven, Ludwig van')
        >>> c = Contributor()
        >>> c.mx = mxCreator
        >>> c.role
        'composer'
        >>> c.name
        'Beethoven, Ludwig van'
        '''
        mxCreatorType = mxCreator.get('type')
        if mxCreatorType != None and mxCreatorType in ROLES:
            self.role = mxCreatorType
        else: # roles are not defined in musicxml
            environLocal.printDebug(['_setMX:', 'received unknown Contributor role: %s' % mxCreatorType])
        self.name = mxCreator.get('charData')


    mx = property(_getMX, _setMX)    
        


class Creator(Contributor):
    '''A person that created a work. Can be a composer, lyricist, arranger, or other type of contributor. In MusicXML, these are "creator" elements.  
    '''

    relevance = 'creator'

    def __init__(self, *args, **keywords):
        '''
        >>> td = Creator(role='composer', name='Chopin, Fryderyk')
        >>> td.role
        'composer'
        >>> td.name
        'Chopin, Fryderyk'
        >>> td.relevance
        'creator'
        '''
        Contributor.__init__(self, *args, **keywords)




#-------------------------------------------------------------------------------
# as these have Date and Text fields, these need to be specialized objects

class Imprint(object):
    '''An object representation of imprint, or publication.
    '''
    def __init__(self, *args, **keywords ):
        pass
# !!!PUB: Publication status. 
# !!!PPR: First publisher. 
# !!!PDT: Date first published. 
# !!!PPP: Place first published. 
# !!!PC#: Publisher's catalogue number. 
# !!!SCT: Scholarly catalogue abbreviation and number. E.g. BWV 551
# !!!SCA: Scholarly catalogue (unabbreviated) name. E.g.Koechel 117.
# !!!SMS: Manuscript source name. 
# !!!SML: Manuscript location. 
# !!!SMA: Acknowledgement of manuscript access.


class Copyright(object):
    '''An object representation of copyright.
    '''
    def __init__(self, *args, **keywords ):
        pass
# !!!YEP: Publisher of electronic edition. 
# !!!YEC: Date and owner of electronic copyright. 
# !!!YER: Date electronic edition released.
# !!!YEM: Copyright message. 
# !!!YEN: Country of copyright. 
# !!!YOR: Original document. 
# !!!YOO: Original document owner. 
# !!!YOY: Original copyright year.
# !!!YOE: Original editor. 


#-------------------------------------------------------------------------------
# supported work ids and abbreviations

#     'otl' : 'title',
#     'otp' : 'popularTitle',
#     'ota' : 'alternativeTitle',
#     'opr' : 'parentTitle',
#     'oac' : 'actNumber',
# 
#     'osc' : 'sceneNumber',
#     'omv' : 'movementNumber',
#     'omd' : 'movementName',
#     'ops' : 'opusNumber',
#     'onm' : 'number',
# 
#     'ovm' : 'volume',
#     'ode' : 'dedication',
#     'oco' : 'commission',
#     'gtl' : 'groupTitle',
#     'gaw' : 'associatedWork',
# 
#     'gco' : 'collectionDesignation',
#     'txo' : 'textOriginalLanguage',
#     'txl' : 'textLanguage',
# 
#     'ocy' : 'countryOfComposition',
#     'opc' : 'localeOfComposition', # origin in abc

class Metadata(music21.Music21Object):
    '''Metadata represent data for a work or fragment, including title, composer, dates, and other relevant information.

    Metadata is a :class:`~music21.base.Music21Object` subclass, meaing that it can be positioned on a Stream by offset and have a :class:`~music21.duration.Duration`.

    In many cases, each Stream will have a single Metadata object at the zero offset position. 
    '''

    #classSortOrder = -1 # TODO: check that this is a good value

    def __init__(self, *args, **keywords):
        '''
        >>> md = Metadata(title='Concerto in F')
        >>> md.title
        'Concerto in F'
        >>> md = Metadata(otl='Concerto in F') # can use abbreviations
        >>> md.title
        'Concerto in F'
        >>> md.setWorkId('otl', 'Rhapsody in Blue')
        >>> md.otl
        'Rhapsody in Blue'
        >>> md.title
        'Rhapsody in Blue'
        '''
        music21.Music21Object.__init__(self)

        # a list of Contributor objects
        # there can be more than one composer, or any other combination
        self._contributors = []
        self._date = None

        # store one or more URLs from which this work came; this could
        # be local file paths or otherwise
        self._urls = []

        # TODO: need a specific object for copyright and imprint
        self._imprint = None
        self._copyright = None

        # a dictionary of Text elements, where keys are work id strings
        # all are loaded with None by default
        self._workIds = {}
        for abbr, id in workIdAbbreviationDict.items():
            #abbr = workIdToAbbreviation(id)
            if id in keywords.keys():
                self._workIds[id] = Text(keywords[id])
            elif abbr in keywords.keys():
                self._workIds[id] = Text(keywords[abbr])
            else:
                self._workIds[id] = None

        # search for any keywords that match attributes 
        # these are for direct Contributor access, must have defined
        # properties
        for attr in ['composer', 'date', 'title']:
            if attr in keywords.keys():
                setattr(self, attr, keywords[attr])
        
        # used for the search() methods to determine what attributes
        # are made available by default; add more as properties/import 
        # exists
        self._searchAttributes = ['date', 'title', 'alternativeTitle', 'movementNumber', 'movementName', 'number', 'opusNumber', 'composer', 'localeOfComposition']


    def __getattr__(self, name):
        '''Utility attribute access for attributes that do not yet have property definitions. 
        '''
        match = None
        for abbr, id in workIdAbbreviationDict.items():
        #for id in WORK_IDS:
            #abbr = workIdToAbbreviation(id)
            if name == id:
                match = id 
                break
            elif name == abbr:
                match = id 
                break
        if match == None:
            raise AttributeError('object has no attribute: %s' % name)
        post = self._workIds[match]
        # always return string representation for now
        return str(post)

#         if isinstance(post, Text):
#             return str(post)
#         elif isinstance(post, Date):
#             return str(post)

    #---------------------------------------------------------------------------
    # property access to things that are not stored in the work ids

    def _getDate(self):
        return str(self._date)

    def _setDate(self, value):
        if isinstance(value, DateSingle): # all inherit date single
            self._date = value
        else:
            ds = DateSingle(value) # assume date single; could be other sublcass
            self._date = ds

    date = property(_getDate, _setDate, 
        doc = '''Get or set the date of this work as one of the following date objects: :class:`~music21.metadata.DateSingle`, :class:`~music21.metadata.DateRelative`, :class:`~music21.metadata.DateBetween`,  :class:`~music21.metadata.DateSelection`, 

        >>> from music21 import *
        >>> md = metadata.Metadata(title='Third Symphony', popularTitle='Eroica', composer='Beethoven, Ludwig van')
        >>> md.date = '2010'
        >>> md.date
        '2010/--/--'

        >>> md.date = metadata.DateBetween(['2009/12/31', '2010/1/28'])
        >>> md.date
        '2009/12/31 to 2010/01/28'
        ''')


    #---------------------------------------------------------------------------
    def setWorkId(self, idStr, value):
        '''Directly set a workd id, given either as a full string name or as a three character abbreviation. 

        >>> md = Metadata(title='Quartet')
        >>> md.title
        'Quartet'
        >>> md.setWorkId('otl', 'Trio')
        >>> md.title
        'Trio'
        >>> md.setWorkId('sdf', None)
        Traceback (most recent call last):
        MetadataException: no work id available with id: sdf

        '''
        idStr = idStr.lower()
        match = False
        for abbr, id in workIdAbbreviationDict.items():
        #for id in WORK_IDS:
            #abbr = workIdToAbbreviation(id)
            if id.lower() == idStr:
                self._workIds[id] = Text(value)
                match = True
                break
            elif abbr == idStr:
                self._workIds[id] = Text(value)
                match = True
                break
        if not match:
            raise MetadataException('no work id available with id: %s' % idStr)

    #---------------------------------------------------------------------------
    def _getTitle(self):
        searchId = ['title', 'popularTitle', 'alternativeTitle', 'movementName']
        post = None
        match = None
        for key in searchId:
            post = self._workIds[key]
            if post != None: # get first matched
                # get a string from this Text object
                # get with normalized articles
                return self._workIds[key].getNormalizedArticle()

    def _setTitle(self, value):
        self._workIds['title'] = Text(value)

    title = property(_getTitle, _setTitle, 
        doc = '''Get the title of the work, or the next matched title string available from related parameter fields. 

        >>> md = Metadata(title='Third Symphony')
        >>> md.title
        'Third Symphony'
        
        >>> md = Metadata(popularTitle='Eroica')
        >>> md.title
        'Eroica'
        
        >>> md = Metadata(title='Third Symphony', popularTitle='Eroica')
        >>> md.title
        'Third Symphony'
        >>> md.popularTitle
        'Eroica'
        >>> md.otp
        'Eroica'
        ''')


    def _getAlternativeTitle(self):
        post = self._workIds['alternativeTitle']
        if post == None:
            return None
        return str(self._workIds['alternativeTitle'])

    def _setAlternativeTitle(self, value):
        self._workIds['alternativeTitle'] = Text(value)

    alternativeTitle = property(_getAlternativeTitle, _setAlternativeTitle, 
        doc = '''Get or set the alternative title. 

        >>> md = Metadata(popularTitle='Eroica')
        >>> md.alternativeTitle = 'Cantus'
        >>> md.alternativeTitle
        'Cantus'

        ''')


    def _getMovementNumber(self):
        post = self._workIds['movementNumber']
        if post == None:
            return None
        return str(self._workIds['movementNumber'])

    def _setMovementNumber(self, value):
        self._workIds['movementNumber'] = Text(value)

    movementNumber = property(_getMovementNumber, _setMovementNumber, 
        doc = '''Get or set the movement number. 
        ''')


    def _getMovementName(self):
        post = self._workIds['movementName']
        if post == None:
            return None
        return str(self._workIds['movementName'])

    def _setMovementName(self, value):
        self._workIds['movementName'] = Text(value)

    movementName = property(_getMovementName, _setMovementName, 
        doc = '''Get or set the movement title. 
        ''')


    def _getNumber(self):
        post = self._workIds['number']
        if post == None:
            return None
        return str(self._workIds['number'])

    def _setNumber(self, value):
        self._workIds['number'] = Text(value)

    number = property(_getNumber, _setNumber, 
        doc = '''Get or set the number of the work.  
        ''')


    def _getOpusNumber(self):
        post = self._workIds['opusNumber']
        if post == None:
            return None
        return str(self._workIds['opusNumber'])

    def _setOpusNumber(self, value):
        self._workIds['opusNumber'] = Text(value)

    opusNumber = property(_getOpusNumber, _setOpusNumber, 
        doc = '''Get or set the opus number. 
        ''')



    def _getLocaleOfComposition(self):
        post = self._workIds['localeOfComposition']
        if post == None:
            return None
        return str(self._workIds['localeOfComposition'])

    def _setLocaleOfComposition(self, value):
        self._workIds['localeOfComposition'] = Text(value)

    localeOfComposition = property(_getLocaleOfComposition, 
                                 _setLocaleOfComposition, 
        doc = '''Get or set the locale of composition, or origin, of the work. 
        ''')


    #---------------------------------------------------------------------------
    # provide direct access to common Contributor roles
    def getContributorsByRole(self, value):
        '''Return a :class:`~music21.metadata.Contributor` if defined for a provided role. 

        >>> md = Metadata(title='Third Symphony')
        >>> c = Contributor()
        >>> c.name = 'Beethoven, Ludwig van'
        >>> c.role = 'composer'
        >>> md.addContributor(c)
        >>> cList = md.getContributorsByRole('composer')
        >>> cList[0].name
        'Beethoven, Ludwig van'

        '''
        post = [] # there may be more than one per role
        for c in self._contributors:
            if c.role == value:
                post.append(c)
        if len(post) > 0:
            return post 
        else:
            return None

    def addContributor(self, c):
        '''Assign a :class:`~music21.metadata.Contributor` object to this Metadata.

        >>> md = Metadata(title='Third Symphony')
        >>> c = Contributor()
        >>> c.name = 'Beethoven, Ludwig van'
        >>> c.role = 'composer'
        >>> md.addContributor(c)
        >>> md.composer
        'Beethoven, Ludwig van'
        >>> md.composer = 'frank'
        >>> md.composers
        ['Beethoven, Ludwig van', 'frank']
        '''
        if not isinstance(c, Contributor):
            raise MetadataException('supplied object is not a Contributor: %s' % c)
        self._contributors.append(c)


    def _getComposers(self):
        post = self.getContributorsByRole('composer')
        if post == None:
            return None
        # get just the name of the first composer
        return [x.name for x in post]

    composers = property(_getComposers,  
        doc = '''Get a list of all :class:`~music21.metadata.Contributor` objects defined as composer of this work.
        ''')

    def _getComposer(self):
        post = self.getContributorsByRole('composer')
        if post == None:
            return None
        # get just the name of the first composer
        return str(post[0].name)

    def _setComposer(self, value):
        c = Contributor()
        c.name = value
        c.role = 'composer'
        self._contributors.append(c)

    composer = property(_getComposer, _setComposer, 
        doc = '''Get or set the composer of this work. More than one composer may be specified.

        The composer attribute does not live in Metadata, but creates a :class:`~music21.metadata.Contributor` object in the Metadata object.

        >>> md = Metadata(title='Third Symphony', popularTitle='Eroica', composer='Beethoven, Ludwig van')
        >>> md.composer
        'Beethoven, Ludwig van'
        ''')



    #---------------------------------------------------------------------------
    # searching and matching
    def search(self, query, field=None):
        '''Search one or all fields with a query, given either as a string or a regular expression match.

        >>> from music21 import *
        >>> md = Metadata()
        >>> md.composer = 'Beethoven, Ludwig van'
        >>> md.title = 'Third Symphony'

        >>> md.search('beethoven', 'composer')
        (True, 'composer')
        >>> md.search('beethoven', 'compose')
        (True, 'composer')
        >>> md.search('frank', 'composer')
        (False, None)
        >>> md.search('frank')
        (False, None)

        >>> md.search('third')
        (True, 'title')
        >>> md.search('third', 'composer')
        (False, None)
        >>> md.search('third', 'title')
        (True, 'title')

        >>> md.search('third|fourth')
        (True, 'title')
        >>> md.search('thove(.*)')
        (True, 'composer')

        '''
        valueFieldPairs = []

        if field != None:
            match = False
            try:
                value = getattr(self, field)
                valueFieldPairs.append((value, field))
                match = True
            except AttributeError:
                pass

            if not match:
                for f in self._searchAttributes:
                    #environLocal.printDebug(['comparing fields:', f, field])
                    # look for partial match in all fields
                    if field.lower() in f.lower():
                        value = getattr(self, f)
                        valueFieldPairs.append((value, f))
                        match = True
                        break
            # if cannot find a match for any field, return 
            if not match:
                return False, None

        else: # get all fields
            for f in self._searchAttributes:
                value = getattr(self, f)
                valueFieldPairs.append((value, f))

        # for now, make all queries strings
        # ultimately, can look for regular expressions by checking for
        # .search
        useRegex = False
        if hasattr(query, 'search'):
            useRegex = True
            reQuery = query # already compiled
        # look for regex characters
        elif common.isStr(query) and ('*' in query or '.' in query or '|' in query or '+' in query or '?' in query or '{' in query or '}' in query):
            useRegex = True
            reQuery = re.compile(query, flags=re.I) 

        if useRegex:
            for v, f in valueFieldPairs:
                # re.I makes case insensitive
                match = reQuery.search(str(v))
                if match is not None:
                    return True, f
        else:
            query = str(query)
            for v, f in valueFieldPairs:
                if common.isStr(v):
                    if query.lower() in v.lower():
                        return True, f
                elif query == v: 
                    return True, f
                
        return False, None
            


    #---------------------------------------------------------------------------
    # overridden methods for json processing 

    def jsonAttributes(self):
        '''Define all attributes of this object that should be JSON serialized for storage and re-instantiation. Attributes that name basic Python objects or :class:`~music21.base.JSONSerializer` subclasses, or dictionaries or lists that contain Python objects or :class:`~music21.base.JSONSerializer` subclasses, can be provided.
        '''
        return ['_date', '_imprint', '_copyright', '_workIds', '_urls', '_contributors']

    def jsonComponentFactory(self, idStr):
        if '.Contributor' in idStr:
            return Contributor()
        elif '.Creator' in idStr:
            return Creator()
        elif '.Text' in idStr:
            return Text()
        elif '.DateSingle' in idStr:
            return DateSingle()
        elif '.DateRelative' in idStr:
            return DateRelative()
        elif '.DateBetween' in idStr:
            return DateBetween()
        elif '.DateSelection' in idStr:
            return DateSelection()
        else:
            raise MetadataException('cannot instantiate an object from id string: %s' % idStr)


    #---------------------------------------------------------------------------
    def _getMX(self):
        '''Return a mxScore object, to be merged or used in final musicxml output
        '''
        mxScore = musicxml.Score()

        # create and add work obj
        mxWork = musicxml.Work()
        match = False
        if self.title not in [None, '']:
            environLocal.printDebug(['_getMX, got title', self.title])
            match = True
            mxWork.set('workTitle', str(self.title))
            #mxWork.set('workNumber', None)
        if match == True: # only attach if needed
            mxScore.set('workObj', mxWork)

        # musicxml often defaults to show only movement title       
        # if no movement title is found, get the .title attr
        if self.movementName not in [None, '']:
            mxScore.set('movementTitle', str(self.movementName))
        else: # it is none
            if self.title != None:
                mxScore.set('movementTitle', str(self.title))

        if self.movementNumber not in [None, '']:
            mxScore.set('movementNumber', str(self.movementNumber))

        # create and add identification obj
        mxId = musicxml.Identification()
        match = False
        mxCreatorList = []
        for c in self._contributors: # look at each contributor
            match = True # if more than zero
            # get an mx object
            mxCreatorList.append(c.mx)
        if match == True: # only attach if needed
            mxId.set('creatorList', mxCreatorList)        
            mxScore.set('identificationObj', mxId)

        return mxScore


    def _setMX(self, mxScore):
        '''Given an mxScore, fill the necessary parameters of a Metadata.
        '''
        mxMovementNumber = mxScore.get('movementNumber')
        if mxMovementNumber != None:
            self.movementNumber = mxMovementNumber

        # xml calls this title not name
        mxName = mxScore.get('movementTitle')
        if mxName != None:
            self.movementName = mxName

        mxWork = mxScore.get('workObj')
        if mxWork != None: # may be set to none
            self.title = mxWork.get('workTitle')
            environLocal.printDebug(['_setMX, got title', self.title])
            self.number = mxWork.get('workNumber')
            self.opusNumber = mxWork.get('opus')

        mxIdentification = mxScore.get('identificationObj')
        if mxIdentification != None:
            for mxCreator in mxIdentification.get('creatorList'):
                # do an mx conversion for mxCreator to Contributor
                c = Contributor()
                c.mx = mxCreator
                self._contributors.append(c)

        # not yet supported; an encoding is also found in identification obj
        mxEncoding = mxScore.get('encodingObj')

    mx = property(_getMX, _setMX)    


#     def _getMusicXML(self):
#         '''Provide a complete MusicXML representation. 
#         '''
#         mxScore = self._getMX()
#         return mxScore.xmlStr()
# 
#     musicxml = property(_getMusicXML,
#         doc = '''Return a complete MusicXML reprsentatoin as a string. 
#         ''')
# 

#-------------------------------------------------------------------------------
class RichMetadata(Metadata):
    '''RichMetadata adds to Metadata information about the contents of the Score it is attached to. TimeSignature, KeySignature and related analytical is stored. RichMetadata are generally only created in the process of creating stored JSON metadata. 
    '''

    def __init__(self, *args, **keywords):
        '''
        >>> md = RichMetadata(title='Concerto in F')
        >>> md.title
        'Concerto in F'
        >>> md = RichMetadata(otl='Concerto in F') # can use abbreviations
        >>> md.title
        'Concerto in F'
        >>> md.setWorkId('otl', 'Rhapsody in Blue')
        >>> md.otl
        'Rhapsody in Blue'
        >>> md.title
        'Rhapsody in Blue'
        >>> 'keySignatureFirst' in md._searchAttributes
        True
        '''
        Metadata.__init__(self, *args, **keywords)

        self.keySignatureFirst = None
        self.keySignatures = []
        self.timeSignatureFirst = None
        self.timeSignatures = []
        self.tempoFirst = None
        self.tempos = []

        self.ambitus = None
        self.pitchHighest = None
        self.pitchLowest = None

        # append to existing search attributes from Metdata
        self._searchAttributes += ['keySignatureFirst', 'timeSignatureFirst', 'pitchHighest', 'pitchLowest'] 



    #---------------------------------------------------------------------------
    # overridden methods for json processing 

    def jsonAttributes(self):
        '''Define all attributes of this object that should be JSON serialized for storage and re-instantiation. Attributes that name basic Python objects or :class:`~music21.base.JSONSerializer` subclasses, or dictionaries or lists that contain Python objects or :class:`~music21.base.JSONSerializer` subclasses, can be provided.
        '''
        # add new names to base-class names
        return ['keySignatureFirst', 'timeSignatureFirst', 'pitchHighest', 'pitchLowest'] + Metadata.jsonAttributes(self)

    def jsonComponentFactory(self, idStr):
        from music21 import meter
        from music21 import key

        try:
            obj = Metadata.jsonComponentFactory(self, idStr)
            return obj
        except MetadataException:
            pass

        if '.TimeSignature' in idStr:
            return meter.TimeSignature()
        elif '.KeySignature' in idStr:
            return key.KeySignature()
        else:
            raise MetadataException('cannot instantiate an object from id string: %s' % idStr)


    #---------------------------------------------------------------------------
    def merge(self, other, favorSelf=False):
        '''Given another Metadata object, combine
        all attributes and return a new object.

        >>> md = Metadata(title='Concerto in F')
        >>> md.title
        'Concerto in F'
        >>> rmd = RichMetadata()
        >>> rmd.merge(md)
        >>> rmd.title
        'Concerto in F'
        '''
        # specifically name attributes to copy, as do not want to get all
        # Metadata is a m21 object
        localNames = ['_contributors', '_date', '_urls', '_imprint',
                      '_copyright', '_workIds']

        environLocal.printDebug(['RichMetadata: calling merge()'])
        for name in localNames: 
            localValue = getattr(self, name)
            # if not set, and favoring self, then only then set
            # this will not work on dictionaries
            if localValue != None and favorSelf:
                continue
            else:
                otherValue = getattr(other, name)
                if otherValue is not None:
                    setattr(self, name, otherValue)


    def update(self, streamObj):
        '''Given a Stream object, update attributes with stored objects. 
        '''
        environLocal.printDebug(['RichMetadata: calling update()'])

        # must be a method-level import
        from music21.analysis import discrete

        # clear all old values
        self.keySignatureFirst = None
        #self.keySignatures = []
        self.timeSignatureFirst = None
        #self.timeSignatures = []
        self.tempoFirst = None
        #self.tempos = []

        self.ambitus = None
        self.pitchHighest = None
        self.pitchLowest = None


        # get flat sorted stream
        flat = streamObj.flat.sorted

        tsStream = flat.getElementsByClass('TimeSignature')
        if len(tsStream) > 0:
            # just store the string representation  
            # re-instantiating TimeSignature objects is expensive
            self.timeSignatureFirst = str(tsStream[0])
        
        # this presently does not work properly b/c ts comparisons are not
        # built-in; need to add __eq__ methods to MeterTerminal
#         for ts in tsStream:
#             if ts not in self.timeSignatures:
#                 self.timeSignatures.append(ts)

        ksStream = flat.getElementsByClass('KeySignature')
        if len(ksStream) > 0:
            self.keySignatureFirst = str(ksStream[0])
#         for ks in ksStream:
#             if ks not in self.keySignatures:
#                 self.keySignatures.append(ts)

        
        analysisObj = discrete.Ambitus(streamObj)    
        psRange = analysisObj.getPitchSpan(streamObj)
        if psRange != None: # may be none if no pitches are stored
            # presently, these are numbers; convert to pitches later
            self.pitchLowest = str(psRange[0]) 
            self.pitchHighest = str(psRange[1])
# 
#         self.ambitus = analysisObj.getSolution(streamObj)





#-------------------------------------------------------------------------------
class MetadataBundle(music21.JSONSerializer):
    '''An object that provides access to, searches within, and storage and loading of multiple Metadata objects.

    Additionally, multiple MetadataBundles can be merged for additional processing
    '''
    def __init__(self, name='default'):

        # all keys are strings, all value are Metadata
        # there is apparently a performance boost for using all-string keys
        self._storage = {}
        
        # name is used to write storage file and acess this bundle from multiple # bundles
        self._name = name

        # need to store local abs file path of each component
        # this will need to be refreshed after loading json data
        # keys are the same for self._storage
        self._accessPaths = {}

    #---------------------------------------------------------------------------
    # overridden methods for json processing 

    def jsonAttributes(self):
        '''Define all attributes of this object that should be JSON serialized for storage and re-instantiation. Attributes that name basic Python objects or :class:`~music21.base.JSONSerializer` subclasses, or dictionaries or lists that contain Python objects or :class:`~music21.base.JSONSerializer` subclasses, can be provided.
        '''
        return ['_storage', '_name']

    def jsonComponentFactory(self, idStr):
        if '.Metadata' in idStr:
            return Metadata()
        elif '.RichMetadata' in idStr:
            return RichMetadata()
        else:
            raise MetadataException('cannot instantiate an object from id string: %s' % idStr)

    #---------------------------------------------------------------------------
    def corpusPathToKey(self, fp, number=None):
        '''Given a file path or corpus path, return the meta-data path
    
        >>> from music21 import *
        >>> mb = MetadataBundle()
        >>> mb.corpusPathToKey('bach/bwv1007/prelude').endswith('bach_bwv1007_prelude')
        True
        >>> mb.corpusPathToKey('/beethoven/opus59no1/movement1.xml').endswith('beethoven_opus59no1_movement1_xml')
        True
        '''
        if 'corpus' in fp and 'music21' in fp:
            cp = fp.split('corpus')[-1] # get fp after corpus
        else:
            cp = fp
    
        if cp.startswith(os.sep):
            cp = cp[1:]
    
        cp = cp.replace('/', '_')
        cp = cp.replace(os.sep, '_')
        cp = cp.replace('.', '_')
    
        # append name to metadata path
        if number == None:
            return cp
        else:
            # append work number
            return cp+'_%s' % number
    
    

    def addFromPaths(self, pathList):
        '''Parse and store metadata from numerous files

        >>> from music21 import *
        >>> mb = MetadataBundle()
        >>> mb.addFromPaths(corpus.getWorkList('bwv66.6'))
        >>> len(mb._storage)
        1
        '''
        # converter imports modules that import metadata
        from music21 import converter
        for fp in pathList:
            environLocal.printDebug(['updateMetadataCache: examining:', fp])
            cp = self.corpusPathToKey(fp)
            post = converter.parse(fp, forceSource=True)
            if 'Opus' in post.classes:
                # need to get scores from each opus?
                # problem here is that each sub-work has metadata, but there
                # is only a single source file
                for s in post.scores:
                    md = s.metadata
                    # updgrade md to rmd
                    rmd = RichMetadata()
                    rmd.merge(md)
                    rmd.update(s) # update based on Stream
                    if md.number == None:
                        environLocal.printDebug(['addFromPaths: got Opus that contains Streams that do not have work numbers:', fp])
                    else:
                        # update path to include work number
                        cp = self.corpusPathToKey(fp, number=md.number)
                        environLocal.printDebug(['addFromPaths: storing:', cp])
                        self._storage[cp] = rmd
            else:
                md = post.metadata
                if md is None:
                    continue    
                rmd = RichMetadata()
                rmd.merge(md)
                rmd.update(post) # update based on Stream
                environLocal.printDebug(['updateMetadataCache: storing:', cp])
                self._storage[cp] = rmd


    def addFromVirtualWorks(self, pathList):
        pass


    def write(self):
        '''Write the JSON storage of all Metadata or RichMetadata contained in this object. 
        '''
        fp = os.path.join(common.getMetadataCacheFilePath(), self._name + '.json')
        environLocal.printDebug(['MetadataBundle: writing:', fp])
        self.jsonWrite(fp)


    def read(self, fp=None):
        '''Load self from the file path suggested by the _name of this MetadataBundle
        '''

        t = common.Timer()
        t.start()
        if fp == None:
            fp = os.path.join(common.getMetadataCacheFilePath(), self._name + '.json')
        self.jsonRead(fp)

        environLocal.printDebug(['MetadataBundle: loading time:', self._name, t, 'md items:', len(self._storage)])


    def updateAccessPaths(self, pathList):
        '''For each stored Metatadata object, create an entry for a complete, local file path that returns this.

        The `pathList` parameter is a list of all file paths on the users local system. 

        >>> from music21 import *
        >>> mb = MetadataBundle()
        >>> mb.addFromPaths(corpus.getWorkList('bwv66.6'))
        >>> len(mb._accessPaths)
        0
        >>> mb.updateAccessPaths(corpus.getWorkList('bwv66.6'))
        >>> len(mb._accessPaths)
        1
        '''
        # always clear first
        self._accessPaths = {}
        # create a copy to manipulate
        keyOptions = self._storage.keys()

        for fp in pathList:
    
            # this key may not be valid if it points to an Opus work that
            # has multiple numbers; thus, need to get a stub that can be 
            # used for conversion
            cp = self.corpusPathToKey(fp)
            # a version of the path that may not have a work number
            cpStub = '_'.join(cp.split('_')[:-1]) # get all but last underscore
    
            match = False
            try:
                md = self._storage[cp]
                self._accessPaths[cp] = fp
                match = True
            except KeyError:
                pass

            if not match:
                # see if there is work id alternative
                for candidate in keyOptions:
                    if candidate.startswith(cpStub):
                        self._accessPaths[candidate] = fp
    
        #environLocal.printDebug(['metadata grouping time:', t, 'md bundles found:', len(post)])
        #return post

    def search(self, query, field=None, extList=None):
        '''Perform search, on all stored metadata, permit regular expression matching. 

        Return pairs of file paths and work numbers, or None

        >>> from music21 import *
        >>> mb = MetadataBundle()
        >>> mb.addFromPaths(corpus.getWorkList('ciconia'))
        >>> mb.updateAccessPaths(corpus.getWorkList('ciconia'))
        >>> post = mb.search('cicon', 'composer')
        >>> len(post[0])
        2
        >>> post = mb.search('cicon', 'composer', extList=['.krn'])
        >>> len(post) # no files in this format
        0
        >>> post = mb.search('cicon', 'composer', extList=['.xml'])
        >>> len(post) # no files in this format
        1
        '''
        post = []
        for key in self._storage.keys():
            md = self._storage[key]
            match, fieldPost = md.search(query, field)
            if match:
                # returns a pair of file path, work number
                result = (self._accessPaths[key], md.number)
                include = False

                if extList != None:
                    for ext in extList:
                        if result[0].endswith(ext):
                            include = True
                            break
                else:
                    include = True

                if include and result not in post:
                    post.append(result)  
        return post



#-------------------------------------------------------------------------------

class Test(unittest.TestCase):

    def runTest(self):
        pass


    def testMetadataLoadCorpus(self):
        from music21 import musicxml
        from music21.musicxml import testFiles

        d = musicxml.Document()
        d.read(testFiles.mozartTrioK581Excerpt)
        mxScore = d.score # get the mx score directly
        md = Metadata()
        md.mx = mxScore

        self.assertEqual(md.movementNumber, '3')
        self.assertEqual(md.movementName, 'Menuetto (Excerpt from Second Trio)')
        self.assertEqual(md.title, 'Quintet for Clarinet and Strings')
        self.assertEqual(md.number, 'K. 581')
        # get contributors directly from Metadata interface
        self.assertEqual(md.composer, 'Wolfgang Amadeus Mozart')


        d.read(testFiles.binchoisMagnificat)
        mxScore = d.score # get the mx score directly
        md = Metadata()
        md.mx = mxScore
        self.assertEqual(md.composer, 'Gilles Binchois')


    def testJSONSerialization(self):

        from music21 import metadata
        import json

        # test creation and loading of data in a text
        t1 = metadata.Text('my text')
        t1.language = 'en'
        #environLocal.printDebug([t1.json])
        jsonDict = json.loads(t1.json)
        self.assertEqual(jsonDict['__attr__'].keys(), [u'_language', u'_data'])

        tNew = metadata.Text()
        tNew.json = t1.json
        self.assertEqual(tNew._data, 'my text')
        self.assertEqual(tNew._language, 'en')


        # test contributor
        c1 = metadata.Contributor(role='composer', name='Gilles Binchois')
        self.assertEqual(c1.role, 'composer')
        self.assertEqual(c1.relevance, 'contributor')

        jsonStr = c1.json
        cNew = metadata.Contributor()
        cNew.json = jsonStr
        self.assertEqual(cNew.role, 'composer')
        self.assertEqual(cNew.name, 'Gilles Binchois')
        self.assertEqual(cNew.relevance, 'contributor')


        # test creator
        c1 = metadata.Creator(role='composer', name='Gilles Binchois')
        self.assertEqual(c1.role, 'composer')
        self.assertEqual(c1.relevance, 'creator')

        jsonStr = c1.json
        cNew = metadata.Contributor()
        cNew.json = jsonStr
        self.assertEqual(cNew.role, 'composer')
        self.assertEqual(cNew.name, 'Gilles Binchois')
        self.assertEqual(cNew.relevance, 'creator')


        # test single date object
        d1 = metadata.Date(year=1843, yearError='approximate')
        d2 = metadata.Date(year='1843?')
        
        dNew = metadata.Date()
        dNew.json = d1.json
        self.assertEqual(dNew.year, 1843)
        self.assertEqual(dNew.yearError, 'approximate')

        dNew = metadata.Date()
        dNew.json = d2.json
        self.assertEqual(dNew.year, '1843')
        self.assertEqual(dNew.yearError, 'uncertain')

        # test date single and other objects that store multiple Date objects

        ds = metadata.DateSingle('2009/12/31', 'approximate')   
        self.assertEqual(str(ds), '2009/12/31')
        self.assertEqual(len(ds._data), 1)
        dsNew = metadata.DateSingle()
        self.assertEqual(len(dsNew._data), 1)
        dsNew.json = ds.json

        self.assertEqual(len(dsNew._data), 1)
        self.assertEqual(dsNew._relevance, 'approximate')
        self.assertEqual(dsNew._dataError, ['approximate'])
        self.assertEqual(str(dsNew), '2009/12/31')


        # test sublcasses of DateSingle
        ds = metadata.DateRelative('2001/12/31', 'prior')   
        self.assertEqual(str(ds), '2001/12/31')
        self.assertEqual(ds.relevance, 'prior')
        self.assertEqual(len(ds._data), 1)

        dsNew = metadata.DateSingle()
        dsNew.json = ds.json
        self.assertEqual(len(dsNew._data), 1)
        self.assertEqual(dsNew._relevance, 'prior')
        self.assertEqual(dsNew._dataError, [])
        self.assertEqual(str(dsNew), '2001/12/31')



        db = metadata.DateBetween(['2009/12/31', '2010/1/28'])   
        self.assertEqual(str(db), '2009/12/31 to 2010/01/28')
        self.assertEqual(db.relevance, 'between')
        self.assertEqual(db._dataError, [None, None])
        self.assertEqual(len(db._data), 2)

        dbNew = metadata.DateBetween()
        dbNew.json = db.json
        self.assertEqual(len(dbNew._data), 2)
        self.assertEqual(dbNew._relevance, 'between')
        self.assertEqual(dbNew._dataError, [None, None])
        self.assertEqual(str(dbNew), '2009/12/31 to 2010/01/28')



        ds = metadata.DateSelection(['2009/12/31', '2010/1/28', '1894/1/28'], 'or')   
        self.assertEqual(str(ds), '2009/12/31 or 2010/01/28 or 1894/01/28')
        self.assertEqual(ds.relevance, 'or')
        self.assertEqual(ds._dataError, [None, None, None])
        self.assertEqual(len(ds._data), 3)

        dsNew = metadata.DateSelection()
        dsNew.json = ds.json
        self.assertEqual(len(dsNew._data), 3)
        self.assertEqual(dsNew._relevance, 'or')
        self.assertEqual(dsNew._dataError, [None, None, None])
        self.assertEqual(str(dsNew), '2009/12/31 or 2010/01/28 or 1894/01/28')




    def testJSONSerializationMetadata(self):

        from music21 import musicxml, corpus
        from music21.musicxml import testFiles


        md = Metadata(title='Concerto in F', date='2010', composer='Frank')
        #environLocal.printDebug([str(md.json)])
        self.assertEqual(md.composer, 'Frank')

        #md.jsonPrint()

        mdNew = Metadata()
        mdNew.json = md.json
        self.assertEqual(mdNew.date, '2010/--/--')
        self.assertEqual(mdNew.composer, 'Frank')

        self.assertEqual(mdNew.title, 'Concerto in F')


        # test getting meta data from an imported source

        d = musicxml.Document()
        d.read(testFiles.mozartTrioK581Excerpt)
        mxScore = d.score # get the mx score directly
        md = Metadata()
        md.mx = mxScore

        self.assertEqual(md.movementNumber, '3')
        self.assertEqual(md.movementName, 'Menuetto (Excerpt from Second Trio)')
        self.assertEqual(md.title, 'Quintet for Clarinet and Strings')
        self.assertEqual(md.number, 'K. 581')
        self.assertEqual(md.composer, 'Wolfgang Amadeus Mozart')

        # convert to json and see if data is still there
        #md.jsonPrint()
        jsonStr = md.json
        mdNew = Metadata()
        mdNew.json = jsonStr

        self.assertEqual(mdNew.movementNumber, '3')
        self.assertEqual(mdNew.movementName, 'Menuetto (Excerpt from Second Trio)')
        self.assertEqual(mdNew.title, 'Quintet for Clarinet and Strings')
        self.assertEqual(mdNew.number, 'K. 581')
        self.assertEqual(mdNew.composer, 'Wolfgang Amadeus Mozart')



    def testLoadRichMetadata(self):

        from music21 import corpus

        s = corpus.parseWork('jactatur')
        self.assertEqual(s.metadata.composer, 'Johannes Ciconia')

        rmd = RichMetadata()
        rmd.merge(s.metadata)

        self.assertEqual(rmd.composer, 'Johannes Ciconia')
        # update rmd with stream
        rmd.update(s)

        self.assertEqual(rmd.keySignatureFirst, 'sharps -1, mode major')

        self.assertEqual(str(rmd.timeSignatureFirst), '2/4')

        #rmd.jsonPrint()
        rmdNew = RichMetadata()
        rmdNew.json = rmd.json
        self.assertEqual(rmdNew.composer, 'Johannes Ciconia')

        self.assertEqual(str(rmdNew.timeSignatureFirst), '2/4')
        self.assertEqual(str(rmdNew.keySignatureFirst), 'sharps -1, mode major')

#         self.assertEqual(rmd.pitchLowest, 55)
#         self.assertEqual(rmd.pitchHighest, 65)
#         self.assertEqual(str(rmd.ambitus), '<music21.interval.Interval m7>')


        s = corpus.parseWork('bwv66.6')
        rmd = RichMetadata()
        rmd.merge(s.metadata)

        rmd.update(s)
        self.assertEqual(str(rmd.keySignatureFirst), 'sharps 3, mode minor')
        self.assertEqual(str(rmd.timeSignatureFirst), '4/4')

        rmdNew.json = rmd.json
        self.assertEqual(str(rmdNew.timeSignatureFirst), '4/4')
        self.assertEqual(str(rmdNew.keySignatureFirst), 'sharps 3, mode minor')


        # test that work id values are copied
        o = corpus.parseWork('essenFolksong/teste')
        self.assertEqual(len(o), 8)

        s = o.getScoreByNumber(4)
        self.assertEqual(s.metadata.localeOfComposition, 'Asien, Ostasien, China, Sichuan')

        rmd = RichMetadata()
        rmd.merge(s.metadata)
        rmd.update(s)

        self.assertEqual(rmd.localeOfComposition, 'Asien, Ostasien, China, Sichuan')



    def testMetadataSearch(self):
        from music21 import corpus
        s = corpus.parseWork('ciconia')
        print s.metadata.title
        self.assertEqual(s.metadata.search('quod', 'title'), (True, 'title'))
        self.assertEqual(s.metadata.search('qu.d', 'title'), (True, 'title'))
        self.assertEqual(s.metadata.search(re.compile('(.*)canon(.*)')), (True, 'title'))


#-------------------------------------------------------------------------------
_DOC_ORDER = [Text, Date, 
            DateSingle, DateRelative, DateBetween, DateSelection, 
            Contributor, Metadata]


if __name__ == "__main__":
    import sys
    import music21
    
    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)
    elif len(sys.argv) > 1:
        t = Test()
        #t.testAugmentOrDiminish()
        #t.testJSONSerialization()
        #t.testJSONSerializationMetadata()


        t.testMetadataSearch()

#------------------------------------------------------------------------------
# eof

