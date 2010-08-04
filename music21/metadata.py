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

import music21
from music21 import common
from music21 import musicxml


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


workIdDict = {
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
    'opc' : 'localeOfComposition',
    }
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

WORK_ID_ABBREVIATIONS = workIdDict.keys()
WORK_IDS = workIdDict.values()

def abbreviationToWorkId(value):
    '''Get work id abbreviations.

    >>> abbreviationToWorkId('otl')
    'title'
    >>> for id in WORK_ID_ABBREVIATIONS: 
    ...    post = abbreviationToWorkId(id)
    '''
    value = value.lower()
    if value in workIdDict.keys():
        return workIdDict[value]
    else:
        raise MetadataException('no such work id: %s' % value)

def workIdToAbbreviation(value):
    '''Get a role id from a string representation.

    >>> workIdToAbbreviation('localeOfComposition')
    'opc'
    >>> for n in WORK_IDS:
    ...     post = workIdToAbbreviation(n)
    '''
    # note: probably not the fastest way to do this
    for id in WORK_ID_ABBREVIATIONS:
        if value.lower() == workIdDict[id].lower():
            return id
    raise MetadataException('no such role: %s' % value)









#-------------------------------------------------------------------------------
class Text(object):
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

#-------------------------------------------------------------------------------
class Date(object):
    '''A single date value, specified by year, month, day, hour, minute, and second. Note that this class has been created, instead of using Python's datetime, to provide greater flexibility for processing unconventional dates, ancient dates, dates with error, and date ranges. 

    The :attr:`~music21.metadata.Date.datetime` property can be used to retrieve a datetime object when necessary.

    Additionally, each value can be specified as `uncertain` or `approximate`; if None, assumed to be certain.

    Data objects are fundamental components of :class:`~music21.metadata.DateSingle` and related subclasses that represent single dates and date ranges. 

    '''
    def __init__(self, *args, **keywords):
        '''
        >>> a = Date(year=1843, yearError='approximate')
        >>> a.year
        1843
        >>> a.yearError
        'approximate'

        >>> a = Date(year='1843?')
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


#-------------------------------------------------------------------------------
class DateSingle(object):
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
        self._data = None
        self._relevance = None # managed by property

        # not yet implemented
        # store an array of values marking if date data itself
        # is certain, approximate, or uncertain
        # here, dataError is relevance
        self._dataError = None

        self._prepareData(data)
        self.relevance = relevance # will use property
    
    def _prepareData(self, data):
        '''Assume a string is supplied as argument
        '''
        self._data = Date()
        self._data.load(data)

    def _setRelevance(self, value):
        if value in ['certain', 'approximate', 'uncertain']:
            self._relevance = value
            self._dataError = value # only here is dataError the same as relevance
        else:
            raise MetadataException('relevance value is not supported by this object: %s' % value)

    def _getRelevance(self):
        return self._relevance

    relevance = property(_getRelevance, _setRelevance)

    def __str__(self):
        return str(self._data)

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
        return self._data.datetime

    datetime = property(_getDatetime, 
        doc = '''Return a datetime object representation. 

        >>> d = Date(year=1843, month=3, day=3)
        >>> ds = DateSingle(d)
        >>> ds.datetime
        datetime.datetime(1843, 3, 3, 0, 0)
        ''')





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
            self._data.append(d) # a lost of Date objects
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
class Contributor(object):
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
class Metadata(music21.Music21Object):
    '''Metadata represent data for a work or fragment, including title, composer, dates, and other relevant information.

    Metadata is a :class:`~music21.base.Music21Object` subclass, meaing that it can be positioned on a Stream by offset and have a :class:`~music21.duration.Duration`.

    In many cases, each Stream will have a single Metadata object at the zero offset position. 
    '''

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

        # a lost of Contributor objects
        # there can be more than one composer, or any other combination
        self._contributors = []
        self._date = None

        # need a specific object for copyright and imprint
        self._imprint = None
        self._copyright = None

        # a dictionary of Text elements, where keys are work id strings
        # all are loaded with None by default
        self._workIds = {}
        for id in WORK_IDS:
            abbr = workIdToAbbreviation(id)
            if id in keywords.keys():
                self._workIds[id] = Text(keywords[id])
            elif abbr in keywords.keys():
                self._workIds[id] = Text(keywords[abbr])
            else:
                self._workIds[id] = None

        # search for any keywords that match attributes 
        # these are for direct Contributor access, must have defined
        # properties
        for attr in ['composer']:
            if attr in keywords.keys():
                setattr(self, attr, keywords[attr])

    def __getattr__(self, name):
        '''Utility attribute access for attributes that do not yet have property definitions. 
        '''
        match = None
        for id in WORK_IDS:
            abbr = workIdToAbbreviation(id)
            if name == id:
                match = id 
                break
            elif name == abbr:
                match = id 
                break
        if match == None:
            raise AttributeError('object has no attribute: %s' % name)
        post = self._workIds[match]
        # if a Text object, return a string representation
        if isinstance(post, Text):
            return str(post)
        elif isinstance(post, Date):
            return str(post)

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
        for id in WORK_IDS:
            abbr = workIdToAbbreviation(id)
            if id.lower() == idStr:
                self._workIds[id] = Text(value)
                match = True
                break
            elif abbr.lower() == idStr:
                self._workIds[id] = Text(value)
                match = True
                break
        if not match:
            raise MetadataException('no work id available with id: %s' % idStr)

    #---------------------------------------------------------------------------
    def _getTitle(self):
        searchId = ['title', 'popularTitle', 'alternativeTitle', 'movementName']
        post = None
        for key in searchId:
            post = self._workIds[key]
            if post != None: # get first matched
                # get a string from this Text object
                return str(self._workIds[key])

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
        self.movementNumber = mxScore.get('movementNumber')
        # xml calls this title not name
        self.movementName = mxScore.get('movementTitle')

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
        a = Test()
        a.testAugmentOrDiminish()