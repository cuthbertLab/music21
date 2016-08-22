# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         primitives.py
# Purpose:      music21 classes for representing score and work meta-data
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2010, 2012 Michael Scott Cuthbert and the music21
# Project License:      LGPL, see license.txt
#------------------------------------------------------------------------------
__all__ = ['Date', 'DateSingle', 'DateRelative', 'DateBetween',
           'DateSelection',
           'Text',
           'Contributor',
           'Creator',
           'Imprint',
           'Copyright']

import datetime
import os
import unittest

from music21 import common
from music21 import exceptions21

from music21.ext import six
if six.PY3:
    unicode = str
#------------------------------------------------------------------------------


from music21 import environment
environLocal = environment.Environment(os.path.basename(__file__))


#------------------------------------------------------------------------------


class Date(object):
    r'''
    A single date value, specified by year, month, day, hour, minute, and
    second. Note that this class has been created, instead of using Python's
    datetime, to provide greater flexibility for processing unconventional
    dates, ancient dates, dates with error, and date ranges.

    The :attr:`~music21.metadata.Date.datetime` property can be used to
    retrieve a datetime object when necessary.

    Additionally, each value can be specified as `uncertain` or `approximate`;
    if None, assumed to be certain.

    Data objects are fundamental components of
    :class:`~music21.metadata.DateSingle` and related subclasses that represent
    single dates and date ranges.

    >>> a = metadata.Date(year=1843, yearError='approximate')
    >>> a.year
    1843

    >>> a.yearError
    'approximate'

    >>> a = metadata.Date(year='1843?')
    >>> a.yearError
    'uncertain'

    '''

    ### CLASS VARIABLES ###

    approximateSymbols = ('~', 'x')
    uncertainSymbols = ('?', 'z')
    priorTimeSymbols = ('<', '{', '>', '}')

    ### INITIALIZER ###

    def __init__(self, *args, **keywords):
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
        self.attrStrFormat = [
            '%04.i', '%02.i', '%02.i', '%02.i', '%02.i', '%006.2f']
        # set any keywords supplied
        for attr in self.attrNames:
            if attr in keywords:
                value, error = self._stripError(keywords[attr])
                setattr(self, attr, value)
                if error is not None:
                    setattr(self, attr + 'Error', error)
        for attr in self.attrNames:
            attr = attr + 'Error'
            if attr in keywords:
                setattr(self, attr, keywords[attr])

    ### SPECIAL METHODS ###
    def __str__(self):
        r'''
        Return a string representation, including error if defined.

        >>> d = metadata.Date()
        >>> d.loadStr('1030?/12~/?4')
        >>> str(d)
        '1030?/12~/04?'
        '''
        # datetime.strftime("%Y.%m.%d")
        # cannot use this, as it does not support dates lower than 1900!
        msg = []
        if self.hour is None and self.minute is None and self.second is None:
            breakIndex = 3  # index
        for i in range(len(self.attrNames)):
            if i >= breakIndex:
                break
            attr = self.attrNames[i]
            value = getattr(self, attr)
            error = getattr(self, attr + 'Error')
            if value is None:
                msg.append('--')
            else:
                fmt = self.attrStrFormat[i]
                if error is not None:
                    sub = fmt % value + Date.errorToSymbol(error)
                else:
                    sub = fmt % value
                if (six.PY3):
                    sub = str(sub)
                msg.append(sub)
        return '/'.join(msg)

    ### PRIVATE METHODS ###

    def _stripError(self, value):
        r'''
        Strip error symbols from a numerical value. Return cleaned source and
        sym. Only one error symbol is expected per string.

        >>> d = metadata.Date()
        >>> d._stripError('1247~')
        ('1247', 'approximate')

        >>> d._stripError('234.43?')
        ('234.43', 'uncertain')

        >>> d._stripError('234.43')
        ('234.43', None)

        '''
        if common.isNum(value):  # if a number, let pass
            return value, None
        else:
            dateStr = value
        sym = self.approximateSymbols + self.uncertainSymbols + self.priorTimeSymbols
        found = None
        for char in dateStr:
            if char in sym:
                found = char
                break
        if found is None:
            return dateStr, None
        elif found in self.approximateSymbols:
            dateStr = dateStr.replace(found, '')
            return dateStr, 'approximate'
        elif found in self.uncertainSymbols:
            dateStr = dateStr.replace(found, '')
            return dateStr, 'uncertain'
        elif found in self.priorTimeSymbols:
            dateStr = dateStr.replace(found, '')
            return dateStr, 'priority'


    ### PUBLIC METHODS ###

    @staticmethod
    def errorToSymbol(value):
        r'''
        Convert an error string (approximate, uncertain) into a symbol.

        >>> metadata.Date.errorToSymbol('approximate')
        '~'

        >>> metadata.Date.errorToSymbol('uncertain')
        '?'
        '''
        if value.lower() in Date.approximateSymbols + ('approximate',):
            return Date.approximateSymbols[0]
        if value.lower() in Date.uncertainSymbols + ('uncertain',):
            return Date.uncertainSymbols[0]

    def load(self, value):
        r'''
        Load values by string, datetime object, or Date object:

        >>> a = metadata.Date(year=1843, month=3, day=3)
        >>> b = metadata.Date()
        >>> b.load(a)
        >>> b.year
        1843
        '''
        if isinstance(value, datetime.datetime):
            self.loadDatetime(value)
        elif isinstance(value, six.string_types):
            self.loadStr(value)
        elif isinstance(value, Date):
            self.loadOther(value)
        else:
            raise exceptions21.MetadataException('Cannot load data: %s' % value)

    def loadDatetime(self, dt):
        r'''
        Load time data from a datetime object:

        >>> import datetime
        >>> dt = datetime.datetime(2005, 2, 1)
        >>> dt
        datetime.datetime(2005, 2, 1, 0, 0)

        >>> m21mdDate = metadata.Date()
        >>> m21mdDate.loadDatetime(dt)
        >>> str(m21mdDate)
        '2005/02/01'
        '''
        for attr in self.attrNames:
            if hasattr(dt, attr):
                # names here are the same, so we can directly map
                value = getattr(dt, attr)
                if value not in [0, None]:
                    setattr(self, attr, value)

    def loadOther(self, other):
        r'''
        Load values based on another Date object:

        >>> a = metadata.Date(year=1843, month=3, day=3)
        >>> b = metadata.Date()
        >>> b.loadOther(a)
        >>> b.year
        1843
        '''
        for attr in self.attrNames:
            if getattr(other, attr) is not None:
                setattr(self, attr, getattr(other, attr))

    def loadStr(self, dateStr):
        r'''
        Load a string date representation.

        Assume `year/month/day/hour:minute:second`:

        >>> d = metadata.Date()
        >>> d.loadStr('1030?/12~/?4')
        >>> d.month, d.monthError
        (12, 'approximate')

        >>> d.year, d.yearError
        (1030, 'uncertain')

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
        dateStr = dateStr.replace(':', '/')
        dateStr = dateStr.replace(' ', '')
        for chunk in dateStr.split('/'):
            value, error = self._stripError(chunk)
            post.append(value)
            postError.append(error)
        # as error is stripped, we can now convert to numbers
        if post and post[0] != '':
            post = [int(x) for x in post]
        # assume in order in post list
        for i in range(len(self.attrNames)):
            if len(post) > i:  # only assign for those specified
                setattr(self, self.attrNames[i], post[i])
                if postError[i] is not None:
                    setattr(self, self.attrNames[i] + 'Error', postError[i])

    ### PUBLIC PROPERTIES ###

    @property
    def datetime(self):
        r'''
        Get a datetime object from a metadata.Date() object

        >>> a = metadata.Date(year=1843, month=3, day=3)
        >>> str(a)
        '1843/03/03'

        >>> a.datetime
        datetime.datetime(1843, 3, 3, 0, 0)

        Lack of a required date element raises an exception:

        >>> a = metadata.Date(year=1843, month=3)
        >>> str(a)
        '1843/03/--'

        >>> a.datetime
        Traceback (most recent call last):
        TypeError: Required argument 'day' (pos 3) not found
        '''
        # pylint: disable=no-value-for-parameter
        post = []
        # order here is order for datetime
        # TODO: need defaults for incomplete times.
        for attr in self.attrNames:
            # need to be integers
            value = getattr(self, attr)
            if value is None:
                break
            post.append(int(value))
        return datetime.datetime(*post)

    @property
    def hasTime(self):
        r'''
        Return True if any time elements are defined:

        >>> a = metadata.Date(year=1843, month=3, day=3)
        >>> a.hasTime
        False

        >>> b = metadata.Date(year=1843, month=3, day=3, minute=3)
        >>> b.hasTime
        True
        '''
        if (self.hour is not None or
                self.minute is not None or
                self.second is not None):
            return True
        else:
            return False

    @property
    def hasError(self):
        r'''
        Return True if any data points have error defined:

        >>> a = metadata.Date(
        ...     year=1843,
        ...     month=3,
        ...     day=3,
        ...     dayError='approximate',
        ...     )
        >>> a.hasError
        True

        >>> b = metadata.Date(
        ...     year=1843,
        ...     month=3,
        ...     day=3,
        ...     minute=3,
        ...     )
        >>> b.hasError
        False

        '''
        for attr in self.attrNames:
            if getattr(self, attr + 'Error') is not None:
                return True
        return False


#------------------------------------------------------------------------------


class DateSingle(object):
    r'''
    Store a date, either as certain, approximate, or uncertain relevance.

    The relevance attribute is limited within each DateSingle subclass
    depending on the design of the class. Alternative relevance types should be
    configured as other DateSingle subclasses.

    >>> dd = metadata.DateSingle('2009/12/31', 'approximate')
    >>> str(dd)
    '2009/12/31'

    >>> dd.relevance
    'approximate'

    >>> dd = metadata.DateSingle('1805/3/12', 'uncertain')
    >>> str(dd)
    '1805/03/12'
    '''

    ### CLASS VARIABLES ###

    isSingle = True

    ### INITIALIZER ###

    def __init__(self, data='', relevance='certain'):
        self._data = []  # store a list of one or more Date objects
        self._relevance = None  # managed by property
        # not yet implemented
        # store an array of values marking if date data itself
        # is certain, approximate, or uncertain
        # here, dataError is relevance
        self._dataError = []  # store a list of one or more strings
        self._prepareData(data)
        self.relevance = relevance  # will use property

    ### SPECIAL METHODS ###

    def __str__(self):
        return str(self._data[0])  # always the first

    ### PRIVATE METHODS ###

    def _prepareData(self, data):
        r'''
        Assume a string is supplied as argument
        '''
        # here, using a list to store one object; this provides more
        # compatability  w/ other formats
        self._data = []  # clear list
        self._data.append(Date())
        self._data[0].load(data)

    ### PUBLIC PROPERTIES ###

    @property
    def datetime(self):
        r'''
        Get a datetime object.

        >>> a = metadata.DateSingle('1843/03/03')
        >>> str(a)
        '1843/03/03'

        >>> a.datetime
        datetime.datetime(1843, 3, 3, 0, 0)

        >>> a = metadata.DateSingle('1843/03')
        >>> str(a)
        '1843/03/--'
        '''
        # get from stored Date object
        return self._data[0].datetime

    @property
    def relevance(self):
        return self._relevance

    @relevance.setter
    def relevance(self, value):
        if value in ('certain', 'approximate', 'uncertain'):
            self._relevance = value
            self._dataError = []
            # only here is dataError the same as relevance
            self._dataError.append(value)
        else:
            raise exceptions21.MetadataException(
                'Relevance value is not supported by this object: '
                '{0!r}'.format(value))



#------------------------------------------------------------------------------


class DateRelative(DateSingle):
    r'''
    Store a relative date, sometime `prior` or sometime `after`, `onorbefore`, or onorafter`.

    >>> dd = metadata.DateRelative('2009/12/31', 'prior')
    >>> str(dd)
    'prior to 2009/12/31'
    >>> dd.relevance = 'after'
    >>> str(dd)
    'after 2009/12/31'


    >>> dd = metadata.DateRelative('2009/12/31', 'certain')
    Traceback (most recent call last):
    music21.exceptions21.MetadataException: Relevance value is not 
        supported by this object: 'certain'
    '''

    ### CLASS VARIABLES ###

    isSingle = True

    ### INITIALIZER ###

    def __init__(self, data='', relevance='after'):
        DateSingle.__init__(self, data, relevance)

    ### PUBLIC PROPERTIES ###

    def __str__(self):
        r = self.relevance
        ds = super(DateRelative, self).__str__()
        if r == 'prior':
            return 'prior to ' + ds
        elif r == 'onorbefore':
            return ds + ' or earlier'
        elif r == 'onorafter':
            return ds + ' or later'
        else:
            return 'after ' + ds

    @property
    def relevance(self):
        return self._relevance

    @relevance.setter
    def relevance(self, value):
        if value == 'before':
            value = 'prior'
        
        if value.lower() not in ('prior', 'after', 'onorbefore', 'onorafter'):
            raise exceptions21.MetadataException(
                'Relevance value is not supported by this object: '
                '{0!r}'.format(value))
        self._relevance = value.lower()



#------------------------------------------------------------------------------


class DateBetween(DateSingle):
    r'''
    Store a relative date, sometime between two dates:

    >>> dd = metadata.DateBetween(['2009/12/31', '2010/1/28'])
    >>> str(dd)
    '2009/12/31 to 2010/01/28'

    >>> dd = metadata.DateBetween(['2009/12/31', '2010/1/28'], 'certain')
    Traceback (most recent call last):
    music21.exceptions21.MetadataException: Relevance value is not 
        supported by this object: 'certain'
    '''

    ### CLASS VARIABLES ###

    isSingle = False

    ### INITIALIZER ###

    def __init__(self, data=None, relevance='between'):
        if data is None:
            data = []
        super(DateBetween, self).__init__(data, relevance)

    ### SPECIAL METHODS ###

    def __str__(self):
        msg = []
        for d in self._data:
            msg.append(str(d))
        return ' to '.join(msg)

    ### PRIVATE METHODS ###

    def _prepareData(self, data):
        r'''
        Assume a list of dates as strings is supplied as argument
        '''
        self._data = []
        self._dataError = []
        for part in data:
            d = Date()
            d.load(part)
            self._data.append(d)  # a list of Date objects
            # can look at Date and determine overall error
            self._dataError.append(None)

    ### PUBLIC PROPERTIES ###

    @property
    def relevance(self):
        return self._relevance

    @relevance.setter
    def relevance(self, value):
        if value != 'between':
            raise exceptions21.MetadataException(
                'Relevance value is not supported by this object: '
                '{0!r}'.format(value))
        self._relevance = value



#------------------------------------------------------------------------------


class DateSelection(DateSingle):
    r'''
    Store a selection of dates, or a collection of dates that might all be
    possible

    >>> dd = metadata.DateSelection(
    ...     ['2009/12/31', '2010/1/28', '1894/1/28'],
    ...     'or',
    ...     )
    >>> str(dd)
    '2009/12/31 or 2010/01/28 or 1894/01/28'

    >>> dd = metadata.DateSelection(
    ...     ['2009/12/31', '2010/1/28'],
    ...     'certain',
    ...     )
    Traceback (most recent call last):
    music21.exceptions21.MetadataException: Relevance value is not 
        supported by this object: 'certain'
    '''

    ### CLASS VARIABLES ###

    isSingle = False

    ### INITIALIZER ###

    def __init__(self, data='', relevance='or'):
        DateSingle.__init__(self, data, relevance)

    ### SPECIAL METHODS ###

    def __str__(self):
        msg = []
        for d in self._data:
            msg.append(str(d))
        return ' or '.join(msg)

    ### PRIVATE METHODS ###

    def _prepareData(self, data):
        r'''
        Assume a list of dates as strings is supplied as argument.
        '''
        self._data = []
        self._dataError = []
        for part in data:
            d = Date()
            d.load(part)
            self._data.append(d)  # a lost of Date objects
            # can look at Date and determine overall error
            self._dataError.append(None)

    ### PUBLIC PROPERTIES ###

    @property
    def relevance(self):
        return self._relevance

    @relevance.setter
    def relevance(self, value):
        if value != 'or':
            raise exceptions21.MetadataException(
                'Relevance value is not supported by this object: '
                '{0!r}'.format(value))
        self._relevance = value



#------------------------------------------------------------------------------


class Text(object):
    r'''
    One unit of text data: a title, a name, or some other text data. Store the
    string and a language name or code. This object can be used and/or
    subclassed for a variety for of text storage.

    >>> td = metadata.Text('concerto in d', 'en')
    >>> str(td)
    'concerto in d'
    '''

    ### INITIALIZER ###

    def __init__(self, data='', language=None):
        if isinstance(data, type(self)):  # if this is a Text obj, get data
            # accessing private attributes here; not desirable
            self._data = data._data
            self._language = data._language
        else:
            self._data = data
            self._language = language

    ### SPECIAL METHODS ###

    def __str__(self):
        # print type(self._data)
        if six.PY3:
            if isinstance(self._data, bytes):
                return self._data.decode('UTF-8')
            elif not isinstance(self._data, str):
                return str(self._data)
            else:
                return self._data
        else:      
            if isinstance(self._data, unicode): #unicode in PY2, str in PY3
                # not sure if this should be wrapped in in str() call
                return self._data.encode('utf-8')
            elif not isinstance(self._data, str):
                return str(self._data)
            else:
                return self._data

    def __unicode__(self):
        return self.__str__().decode('utf-8')

    ### PUBLIC PROPERTIES ###

    @property
    def language(self):
        r'''
        Set the language of the Text stored within.

        >>> t = metadata.Text('my text')
        >>> t.language = 'en'
        >>> t.language
        'en'
        '''
        return self._language

    @language.setter
    def language(self, value):
        self._language = value


    ### PUBLIC METHODS ###

    def getNormalizedArticle(self):
        r'''
        Return a string representation with normalized articles.

        >>> td = metadata.Text('Ale is Dear, The', 'en')
        >>> str(td)
        'Ale is Dear, The'

        >>> td.getNormalizedArticle()
        'The Ale is Dear'

        >>> td.language = 'de'
        >>> td.getNormalizedArticle()
        'Ale is Dear, The'
        '''
        from music21 import text
        return text.prependArticle(str(self), self._language)


#------------------------------------------------------------------------------


class Contributor(object):
    r'''
    A person that contributed to a work. Can be a composer, lyricist, arranger,
    or other type of contributor.  In MusicXML, these are "creator" elements.

    >>> td = metadata.Contributor(role='composer', name='Chopin, Fryderyk')
    >>> td.role
    'composer'

    >>> td.name
    'Chopin, Fryderyk'

    >>> td.relevance
    'contributor'
    
    >>> td
    <music21.metadata.primitives.Contributor composer:Chopin, Fryderyk>
    '''

    ### CLASS VARIABLES ###

    relevance = 'contributor'

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


    # TODO: add editor...

    roleAbbreviationsDict = {
        'com': 'composer',
        'coa': 'attributedComposer',
        'cos': 'suspectedComposer',
        'col': 'composerAlias',
        'coc': 'composerCorporate',
        'lyr': 'lyricist',
        'lib': 'librettist',
        'lar': 'arranger',
        'lor': 'orchestrator',
        'trn': 'translator',
        }

    roleAbbreviations = roleAbbreviationsDict.keys()

    roleNames = roleAbbreviationsDict.values()

    ### INITIALIZER ###

    def __init__(self, *args, **keywords):
        self._role = None
        if 'role' in keywords:
            # stored in self._role
            self.role = keywords['role']  # validated with property
        else:
            self.role = None
        # a list of Text objects to support various spellings or
        # language translatiions
        self._names = []
        if 'name' in keywords:  # a single
            self._names.append(Text(keywords['name']))
        if 'names' in keywords:  # many
            for n in keywords['names']:
                self._names.append(Text(n))
        # store the nationality, if known
        self._nationality = []
        # store birth and death of contributor, if known
        self._dateRange = [None, None]
        if 'birth' in keywords:
            self._dateRange[0] = DateSingle(keywords['birth'])
        if 'death' in keywords:
            self._dateRange[1] = DateSingle(keywords['death'])

    def __repr__(self):
        return '<music21.metadata.primitives.{} {}:{}>'.format(                                                           
                                self.__class__.__name__, self.role, self.name)

    ### PUBLIC METHODS ###

    def age(self):
        r'''
        Calculate the age at death of the Contributor, returning a
        datetime.timedelta object.

        >>> a = metadata.Contributor(
        ...     name='Beethoven, Ludwig van',
        ...     role='composer',
        ...     birth='1770/12/17',
        ...     death='1827/3/26',
        ...     )
        >>> a.role
        'composer'

        >>> a.age()
        datetime.timedelta(20552)

        >>> str(a.age())
        '20552 days, 0:00:00'

        >>> a.age().days // 365
        56
        '''
        if self._dateRange[0] is not None and self._dateRange[1] is not None:
            b = self._dateRange[0].datetime
            d = self._dateRange[1].datetime
            return d - b
        else:
            return None

    ### PUBLIC PROPERTIES ###

    @property
    def name(self):
        r'''
        Returns the text name, or the first of many names entered.

        >>> td = metadata.Contributor(
        ...     role='composer',
        ...     names=['Chopin, Fryderyk', 'Chopin, Frederick'],
        ...     )
        >>> td.name
        'Chopin, Fryderyk'

        >>> td.names
        ['Chopin, Fryderyk', 'Chopin, Frederick']
        '''
        # return first name
        if len(self._names) > 0:
            return str(self._names[0])
        else:
            return None

    @name.setter
    def name(self, value):
        # return first name
        self._names = []  # reset
        self._names.append(Text(value))


    @property
    def names(self):
        r'''
        Returns all names in a list.

        >>> td = metadata.Contributor(
        ...     role='composer',
        ...     names=['Chopin, Fryderyk', 'Chopin, Frederick'],
        ...     )
        >>> td.names
        ['Chopin, Fryderyk', 'Chopin, Frederick']
        '''
        # return first name
        msg = []
        for n in self._names:
            msg.append(str(n))
        return msg

    @property
    def role(self):
        r'''
        The role is what part this Contributor plays in the work.  Both
        full roll strings and roll abbreviations may be used.

        >>> td = metadata.Contributor()
        >>> td.role = 'composer'
        >>> td.role
        'composer'

        >>> td.role = 'lor'
        >>> td.role
        'orchestrator'
        '''
        return self._role

    @role.setter
    def role(self, value):
        if value is None or value in self.roleAbbreviationsDict.values():
            self._role = value
        elif value in self.roleAbbreviationsDict.keys():
            self._role = self.roleAbbreviationsDict[value]
        else:
            raise exceptions21.MetadataException(
                'Role value is not supported by this object: '
                '{0!r}'.format(value))


    @staticmethod
    def abbreviationToRole(abbreviation):
        r'''
        Convert `abbreviation` to role name:

        >>> metadata.Contributor.abbreviationToRole('com')
        'composer'

        >>> metadata.Contributor.abbreviationToRole('lib')
        'librettist'
        '''
        abbreviation = abbreviation.lower()
        if abbreviation in Contributor.roleAbbreviationsDict:
            return Contributor.roleAbbreviationsDict[abbreviation]
        else:
            raise exceptions21.MetadataException(
                'no such role: {0!r}'.format(abbreviation))

    @staticmethod
    def roleToAbbreviation(roleName):
        '''Convert `roleName` to role abbreviation:

        >>> metadata.Contributor.roleToAbbreviation('composer')
        'com'
        '''
        # note: probably not the fastest way to do this
        for role_id in Contributor.roleAbbreviationsDict:
            if roleName.lower() == Contributor.roleAbbreviationsDict[role_id].lower():
                return role_id
        raise exceptions21.MetadataException('No such role: %s' % roleName)

#------------------------------------------------------------------------------


class Creator(Contributor):
    r'''
    A person that created a work. Can be a composer, lyricist, arranger, or
    other type of contributor.

    In MusicXML, these are "creator" elements.

    >>> td = metadata.Creator(role='composer', name='Chopin, Fryderyk')
    >>> td.role
    'composer'

    >>> td.name
    'Chopin, Fryderyk'

    >>> td.relevance
    'creator'
    '''

    ### CLASS VARIABLES ###

    relevance = 'creator'

    ### INITIALIZER ###

    def __init__(self, *args, **keywords):
        Contributor.__init__(self, *args, **keywords)


#------------------------------------------------------------------------------


class Imprint(object):
    r'''
    An object representation of imprint, or publication.
    '''
    def __init__(self, *args, **keywords):
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


#------------------------------------------------------------------------------


class Copyright(object):
    r'''
    An object representation of copyright.
    '''
    def __init__(self, *args, **keywords):
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

#------------------------------------------------------------------------------
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


#------------------------------------------------------------------------------


class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testText(self):
        from music21 import freezeThaw
        from music21 import metadata
        import json

        text = metadata.primitives.Text('my text')
        text.language = 'en'
        jsf = freezeThaw.JSONFreezer(text)
        jsonDict = json.loads(jsf.json)
        self.assertEqual(sorted(list(jsonDict['__attr__'].keys())), [u'_data', u'_language'])

        textNew = metadata.primitives.Text()
        jst = freezeThaw.JSONThawer(textNew)
        jst.json = jsf.json

        self.assertEqual(textNew._data, 'my text')
        self.assertEqual(textNew._language, 'en')

    def testContributor(self):
        from music21 import freezeThaw
        from music21 import metadata

        contributor = metadata.primitives.Contributor(
            role='composer',
            name='Gilles Binchois',
            )
        self.assertEqual(contributor.role, 'composer')
        self.assertEqual(contributor.relevance, 'contributor')
        jsonStr = freezeThaw.JSONFreezer(contributor).json
        contributorNew = metadata.primitives.Contributor()
        freezeThaw.JSONThawer(contributorNew).json = jsonStr
        self.assertEqual(contributorNew.role, 'composer')
        self.assertEqual(contributorNew.name, 'Gilles Binchois')
        self.assertEqual(contributorNew.relevance, 'contributor')

    def testCreator(self):
        from music21 import freezeThaw
        from music21 import metadata

        creator = metadata.primitives.Creator(
            role='composer',
            name='Gilles Binchois',
            )
        self.assertEqual(creator.role, 'composer')
        self.assertEqual(creator.relevance, 'creator')

        jsonStr = freezeThaw.JSONFreezer(creator).json
        creatorNew = metadata.primitives.Contributor()
        freezeThaw.JSONThawer(creatorNew).json = jsonStr
        self.assertEqual(creatorNew.role, 'composer')
        self.assertEqual(creatorNew.name, 'Gilles Binchois')
        self.assertEqual(creatorNew.relevance, 'creator')

    def testDate(self):
        from music21 import freezeThaw
        from music21 import metadata

        date1 = metadata.primitives.Date(year=1843, yearError='approximate')
        date2 = metadata.primitives.Date(year='1843?')

        dateNew = metadata.primitives.Date()

        jsonStr = freezeThaw.JSONFreezer(date1).json
        freezeThaw.JSONThawer(dateNew).json = jsonStr

        self.assertEqual(dateNew.year, 1843)
        self.assertEqual(dateNew.yearError, 'approximate')

        dateNew = metadata.primitives.Date()

        jsonStr = freezeThaw.JSONFreezer(date2).json
        freezeThaw.JSONThawer(dateNew).json = jsonStr

        self.assertEqual(dateNew.year, '1843')
        self.assertEqual(dateNew.yearError, 'uncertain')

    def testDateSingle(self):
        from music21 import freezeThaw
        from music21 import metadata

        dateSingle = metadata.primitives.DateSingle(
            '2009/12/31', 'approximate')
        self.assertEqual(str(dateSingle), '2009/12/31')
        self.assertEqual(len(dateSingle._data), 1)

        dateSingleNew = metadata.primitives.DateSingle()
        self.assertEqual(len(dateSingleNew._data), 1)

        jsonStr = freezeThaw.JSONFreezer(dateSingle).json
        freezeThaw.JSONThawer(dateSingleNew).json = jsonStr

        self.assertEqual(len(dateSingleNew._data), 1)
        self.assertEqual(dateSingleNew._relevance, 'approximate')
        self.assertEqual(dateSingleNew._dataError, ['approximate'])
        self.assertEqual(str(dateSingleNew), '2009/12/31')

    def testDateRelative(self):
        from music21 import freezeThaw
        from music21 import metadata

        dateRelative = metadata.primitives.DateRelative('2001/12/31', 'prior')
        self.assertEqual(str(dateRelative), 'prior to 2001/12/31')
        self.assertEqual(dateRelative.relevance, 'prior')
        self.assertEqual(len(dateRelative._data), 1)

        dateSingleNew = metadata.primitives.DateSingle()

        jsonStr = freezeThaw.JSONFreezer(dateRelative).json
        freezeThaw.JSONThawer(dateSingleNew).json = jsonStr

        self.assertEqual(len(dateSingleNew._data), 1)
        self.assertEqual(dateSingleNew._relevance, 'prior')
        self.assertEqual(dateSingleNew._dataError, [])
        self.assertEqual(str(dateSingleNew), '2001/12/31')

    def testDateBetween(self):
        from music21 import freezeThaw
        from music21 import metadata

        dateBetween = metadata.primitives.DateBetween(
            ('2009/12/31', '2010/1/28'))
        self.assertEqual(str(dateBetween), '2009/12/31 to 2010/01/28')
        self.assertEqual(dateBetween.relevance, 'between')
        self.assertEqual(dateBetween._dataError, [None, None])
        self.assertEqual(len(dateBetween._data), 2)

        dateBetweenNew = metadata.primitives.DateBetween()

        jsonStr = freezeThaw.JSONFreezer(dateBetween).json
        freezeThaw.JSONThawer(dateBetweenNew).json = jsonStr

        self.assertEqual(len(dateBetweenNew._data), 2)
        self.assertEqual(dateBetweenNew._relevance, 'between')
        self.assertEqual(dateBetweenNew._dataError, [None, None])
        self.assertEqual(str(dateBetweenNew), '2009/12/31 to 2010/01/28')

    def testDateSelection(self):
        from music21 import freezeThaw
        from music21 import metadata

        dateSelection = metadata.primitives.DateSelection(
            ['2009/12/31', '2010/1/28', '1894/1/28'],
            'or',
            )
        self.assertEqual(str(dateSelection),
            '2009/12/31 or 2010/01/28 or 1894/01/28')
        self.assertEqual(dateSelection.relevance, 'or')
        self.assertEqual(dateSelection._dataError, [None, None, None])
        self.assertEqual(len(dateSelection._data), 3)

        dateSelectionNew = metadata.primitives.DateSelection()

        jsonStr = freezeThaw.JSONFreezer(dateSelection).json
        freezeThaw.JSONThawer(dateSelectionNew).json = jsonStr

        self.assertEqual(len(dateSelectionNew._data), 3)
        self.assertEqual(dateSelectionNew._relevance, 'or')
        self.assertEqual(dateSelectionNew._dataError, [None, None, None])
        self.assertEqual(str(dateSelectionNew),
            '2009/12/31 or 2010/01/28 or 1894/01/28')


#------------------------------------------------------------------------------


_DOC_ORDER = (
    Text,
    Date,
    DateSingle,
    DateRelative,
    DateBetween,
    DateSelection,
    Contributor,
    )

__all__ = [
    'Contributor',
    'Copyright',
    'Creator',
    'Date',
    'DateBetween',
    'DateRelative',
    'DateSelection',
    'DateSingle',
    'Imprint',
    'Text',
    ]

if __name__ == "__main__":
    import music21
    music21.mainTest(Test)


#------------------------------------------------------------------------------
