# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Name:         primitives.py
# Purpose:      music21 classes for representing score and work metadata
#
# Authors:      Christopher Ariza
#               Michael Scott Asato Cuthbert
#               Greg Chapman
#
# Copyright:    Copyright © 2010-22 Michael Scott Asato Cuthbert and the music21
# License:      BSD, see license.txt
# -----------------------------------------------------------------------------
from __future__ import annotations

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

from collections.abc import Iterable
import datetime
import typing as t
import unittest

from music21 import common
from music21 import environment
from music21 import exceptions21
from music21 import prebase

# -----------------------------------------------------------------------------

environLocal = environment.Environment('metadata.primitives')



# -----------------------------------------------------------------------------

class Date(prebase.ProtoM21Object):
    r'''
    A single date value, specified by year, month, day, hour, minute, and
    second. Note that this class has been created, instead of using Python's
    datetime, to provide greater flexibility for processing unconventional
    dates, ancient dates, dates with error, and date ranges.

    The :attr:`~music21.metadata.Date.datetime` property can be used to
    retrieve a datetime object when necessary.

    Additionally, each value can be specified as `uncertain` or `approximate`;
    if None, assumed to be certain.

    Date objects are fundamental components of
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

    >>> d = metadata.Date(year=1805, month=3, monthError='approximate')
    >>> str(d)
    '1805/03~/--'

    Note that milliseconds are not retained, as this is a tool for musicology
    and not for file timestamps.  However, unlike datetime objects, dates
    in the distant past are supported (though not currently BC/BCE dates).
    '''
    # CLASS VARIABLES #
    approximateSymbols = ('~', 'x')
    uncertainSymbols = ('?', 'z')
    priorTimeSymbols = ('<', '{', '>', '}')

    # INITIALIZER #

    def __init__(self,
                 *,
                 year: int | str | None = None,
                 month: int | str | None = None,
                 day: int | str | None = None,
                 hour: int | str | None = None,
                 minute: int | str | None = None,
                 second: int | float | str | None = None,
                 yearError: str | None = None,
                 monthError: str | None = None,
                 dayError: str | None = None,
                 hourError: str | None = None,
                 minuteError: str | None = None,
                 secondError: str | None = None):
        if year is not None and yearError is None:
            year, yearError = self._stripError(year)
        if month is not None and monthError is None:
            month, monthError = self._stripError(month)
        if day is not None and dayError is None:
            day, dayError = self._stripError(day)
        if hour is not None and hourError is None:
            hour, hourError = self._stripError(hour)
        if minute is not None and minuteError is None:
            minute, minuteError = self._stripError(minute)
        if second is not None and secondError is None:
            second, secondError = self._stripError(second)

        self._sanityCheck(year=year, month=month, day=day, hour=hour, minute=minute, second=second)

        self.year = t.cast(int | None, year)
        self.month = t.cast(int | None, month)
        self.day = t.cast(int | None, day)
        self.hour = t.cast(int | None, hour)
        self.minute = t.cast(int | None, minute)
        self.second = t.cast(int | None, second)

        # error: can be 'approximate', 'uncertain' or None.
        # None is assumed to be certain
        self.yearError: str | None = yearError
        self.monthError: str | None = monthError
        self.dayError: str | None = dayError
        self.hourError: str | None = hourError
        self.minuteError: str | None = minuteError
        self.secondError: str | None = secondError
        self.attrNames = ('year', 'month', 'day', 'hour', 'minute', 'second')

    # SPECIAL METHODS #
    def __eq__(self, other) -> bool:
        return str(self) == str(other)

    def __str__(self):
        r'''
        Return a string representation, including error if defined.

        >>> d = metadata.Date()
        >>> d.loadStr('1030?/12~/?4')
        >>> str(d)
        '1030?/12~/04?'
        '''
        # Note, cannot use datetime.strftime('%Y.%m.%d') even if all are not-None,
        # as it does not support dates lower than 1900!
        msg = []
        if self.hour is None and self.minute is None and self.second is None:
            breakIndex = 3  # index
        else:
            breakIndex = 7

        for i, attr in enumerate(self.attrNames):
            if i >= breakIndex:
                break
            value = t.cast(str, getattr(self, attr))
            error = t.cast(str, getattr(self, attr + 'Error'))
            if value is None:
                msg.append('--')
            else:
                if attr == 'year':
                    fmt = '%04.i'
                else:
                    fmt = '%02.i'
                sub = fmt % value
                if error is not None:
                    sub += Date.errorToSymbol(error)
                sub = str(sub)
                msg.append(sub)
        out = '/'.join(msg[:4])
        if len(msg) > 4:
            out += ':' + ':'.join(msg[4:])
        return out

    # PRIVATE METHODS #
    def _stripError(self,
                    value: int | float | str,
                    ) -> tuple[int, str | None]:
        r'''
        Strip error symbols from a numerical value. Return cleaned source and
        sym. Only one error symbol is expected per string.

        >>> d = metadata.Date()
        >>> d._stripError('1247~')
        (1247, 'approximate')

        >>> d._stripError('63?')
        (63, 'uncertain')

        Milliseconds are not retained -- this is for musicology, not computers...

        >>> d._stripError('4.43')
        (4, None)
        '''
        uncertainty: str | None = None
        if isinstance(value, str):  # if a number, let pass
            sym = self.approximateSymbols + self.uncertainSymbols + self.priorTimeSymbols
            found = None
            for char in value:
                if char in sym:
                    found = char
                    break
            if found in self.approximateSymbols:
                value = value.replace(found, '')
                uncertainty = 'approximate'
            elif found in self.uncertainSymbols:
                value = value.replace(found, '')
                uncertainty = 'uncertain'
            elif found in self.priorTimeSymbols:
                value = value.replace(found, '')
                uncertainty = 'priority'

        # cannot convert string '4.43' directly to int...
        value = float(value)
        return int(value), uncertainty

    def _sanityCheck(self, *, year, month, day, hour, minute, second):
        def month_fail(m, d, y):
            # not checking Gregorian leap year viability, as it changes historically.
            return ((month in (4, 6, 9, 11) and day == 31)
                    or (month == 2 and day > 29)
                    or (month == 2 and day == 29 and year is not None and year % 4))

        if month is not None and (month < 1 or month > 12):
            raise ValueError(f'Month must be between 1 and 12, not {month}.')
        if day is not None and (
                day > 31
                or day < 1
                or month is not None and month_fail(month, day, year)):
            raise ValueError(f'Day {day} is not possible with month {month}.')
        if hour is not None and (hour < 0 or hour > 23):
            raise ValueError('Hour must be between 0 and 23')
        if minute is not None and (minute < 0 or minute > 59):
            raise ValueError('Minute must be between 0 and 59')
        if second is not None and (second < 0 or second > 59):
            raise ValueError('Second must be between 0 and 59')

    # PUBLIC METHODS #

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

    def load(self, value: DateParseType):
        r'''
        Load values by string, datetime object, or Date object:

        >>> a = metadata.Date(year=1843, month=3, day=3)
        >>> b = metadata.Date()
        >>> b.load(a)
        >>> b.year
        1843

        If there is an error, a ValueError is raised, but the
        incorrect values are retained:

        >>> d = metadata.Date()
        >>> d.load('1999/14/32/25:60:61')
        Traceback (most recent call last):
        ValueError: Month must be between 1 and 12, not 14.
        >>> str(d)
        '1999/14/32/25:60:61'
        '''
        if isinstance(value, datetime.datetime):
            self.loadDatetime(value)
        elif isinstance(value, str):
            self.loadStr(value)
        elif isinstance(value, int):
            self.loadStr(str(value))
        elif isinstance(value, Date):
            self.loadOther(value)
        else:
            raise exceptions21.MetadataException(f'Cannot load data: {value}')
        self._sanityCheck(year=self.year, month=self.month, day=self.day,
                          hour=self.hour, minute=self.minute, second=self.second)

    def loadDatetime(self, dt: datetime.datetime) -> None:
        # noinspection PyShadowingNames
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
                if value not in (0, None):
                    setattr(self, attr, value)

    def loadOther(self, other: Date) -> None:
        r'''
        Load values based on another Date object.  (the "Other" in "loadOther"
        means another Date object, not just anything.

        >>> a = metadata.Date(year=1843, month=3, day=3, yearError='approximate')
        >>> b = metadata.Date()
        >>> b.loadOther(a)
        >>> b.year
        1843
        >>> b.yearError
        'approximate'
        '''
        for attr in self.attrNames:
            if getattr(other, attr) is not None:
                setattr(self, attr, getattr(other, attr))
                errorAttr = attr + 'Error'
                if getattr(other, errorAttr) is not None:
                    setattr(self, errorAttr, getattr(other, errorAttr))

    def loadStr(self, dateStr: str) -> None:
        r'''
        Load a string date representation, which might have approximate
        symbols.

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
        post: list[int | None] = []
        postError: list[str | None] = []
        dateStr = dateStr.replace(':', '/')
        dateStr = dateStr.replace(' ', '')
        for chunk in dateStr.split('/'):
            if chunk == '--':
                value, error = None, None
            else:
                value, error = self._stripError(chunk)
            post.append(value)
            postError.append(error)
        # assume in order in post list
        for i in range(len(self.attrNames)):
            if len(post) > i:  # only assign for those specified
                setattr(self, self.attrNames[i], post[i])
                if postError[i] is not None:
                    setattr(self, self.attrNames[i] + 'Error', postError[i])

    # PUBLIC PROPERTIES #

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
        TypeError: ...argument 'day' (pos 3)...
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
        if (self.hour is not None
                or self.minute is not None
                or self.second is not None):
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


# -----------------------------------------------------------------------------
class DatePrimitive(prebase.ProtoM21Object):
    '''
    A default class for all date objects, which can have different types
    and different "relevance" values.

    Note that the interaction between uncertainty on an entire DatePrimitive object
    vs uncertainty on a particular Date value, like month, is ill-defined
    and needs work.
    '''
    # INITIALIZER #

    def __init__(self, relevance: str = 'certain'):
        self._data: list[Date] = []
        self._relevance = ''  # managed by property
        # not yet implemented
        # store an array of values marking if date data itself
        # is certain, approximate, or uncertain
        # here, dataError is relevance
        self._dataUncertainty: list[str | None] = []
        self.relevance = relevance  # will use property

    # SPECIAL METHODS #

    def __eq__(self, other) -> bool:
        '''
        >>> dd = metadata.DateSingle('1805/3/12', 'uncertain')
        >>> dd2 = metadata.DateSingle('1805/3/12', 'uncertain')
        >>> str(dd)
        '1805/03/12'
        >>> dd == dd2
        True
        >>> dd2.relevance='certain'
        >>> dd == dd2
        False
        '''
        return (type(self) is type(other)
                    and self._data == other._data
                    and self._dataUncertainty == other._dataUncertainty
                    and self.relevance == other.relevance)

    def _reprInternal(self) -> str:
        return str(self)

    def __str__(self):
        if len(self._data) == 0:
            return ''
        elif len(self._data) == 1:
            return str(self._data[0])
        else:
            return str([str(d) for d in self._data])

    # PUBLIC PROPERTIES #

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
        '''
        The relevance attribute takes one of three
        values, `'certain'`, `'approximate'`, or
        `'uncertain'`.
        '''
        return self._relevance

    @relevance.setter
    def relevance(self, value):
        if value in ('certain', 'approximate', 'uncertain'):
            self._relevance = value
            self._dataUncertainty = []
            # only here is dataError the same as relevance
            self._dataUncertainty.append(value)
        else:
            raise exceptions21.MetadataException(
                f'Relevance value is not supported by this object: {value!r}')


class DateSingle(DatePrimitive):
    r'''
    Store a date, either as certain, approximate, or uncertain relevance.

    The relevance attribute is limited within each DateSingle subclass
    depending on the design of the class. Alternative relevance types should be
    configured as other DateSingle subclasses.

    >>> dd = metadata.DateSingle('2009/12/31', 'approximate')
    >>> dd
    <music21.metadata.primitives.DateSingle 2009/12/31>

    >>> str(dd)
    '2009/12/31'

    >>> dd.relevance
    'approximate'

    >>> dd = metadata.DateSingle('1805/3/12', 'uncertain')
    >>> str(dd)
    '1805/03/12'
    '''
    def __init__(self, data: DateParseType = '', relevance='certain'):
        super().__init__(relevance)
        self._prepareData(data)

    def __str__(self):
        return str(self._data[0])

    def _prepareData(self, data: DateParseType):
        r'''
        Assume a string is supplied as argument
        '''
        # here, using a list to store one object; this provides more
        # compatibility  w/ other formats
        self._data = []  # clear list
        self._dataUncertainty = [self.relevance]
        self._data.append(Date())
        self._data[0].load(data)



# -----------------------------------------------------------------------------


class DateRelative(DatePrimitive):
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

    # INITIALIZER #

    def __init__(self, data: DateParseType = '', relevance='after'):
        # not a useless constructor because default value for relevance changed
        super().__init__(relevance)
        self._prepareData(data)

    # PUBLIC PROPERTIES #

    def __str__(self):
        r = self.relevance
        ds = super().__str__()
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
        '''
        The relevance attribute takes one of four
        values, `'prior'`, `'after'`, or
        `'onorbefore'` or `'onorafter'`.
        '''
        return self._relevance

    @relevance.setter
    def relevance(self, value):
        if value == 'before':
            value = 'prior'

        if value.lower() not in ('prior', 'after', 'onorbefore', 'onorafter'):
            raise exceptions21.MetadataException(
                f'Relevance value is not supported by this object: {value!r}')
        self._relevance = value.lower()

    def _prepareData(self, data: DateParseType):
        r'''
        Assume a string is supplied as argument
        '''
        # here, using a list to store one object; this provides more
        # compatibility  w/ other formats
        self._data = []  # clear list
        self._dataUncertainty = [None]
        self._data.append(Date())
        self._data[0].load(data)
# -----------------------------------------------------------------------------


class DateBetween(DatePrimitive):
    r'''
    Store a relative date, sometime between two dates:

    >>> dd = metadata.DateBetween(['2009/12/31', '2010/1/28'])
    >>> str(dd)
    '2009/12/31 to 2010/01/28'

    >>> dd = metadata.DateBetween(['2009/12/31', '2010/1/28'], 'certain')
    Traceback (most recent call last):
    music21.exceptions21.MetadataException: Relevance value is not
        supported by this object: 'certain'

    >>> d1 = metadata.Date(year=1605)
    >>> d2 = metadata.Date(year=1608, month='11?')
    >>> dd = metadata.DateBetween([d1, d2])
    >>> str(dd)
    '1605/--/-- to 1608/11?/--'
    '''
    # INITIALIZER #

    def __init__(self, data: Iterable[DateParseType] = (), relevance='between'):
        super().__init__(relevance)
        self._prepareData(data)

    # SPECIAL METHODS #

    def __str__(self):
        msg = []
        for d in self._data:
            msg.append(str(d))
        return ' to '.join(msg)

    # PRIVATE METHODS #

    def _prepareData(self, data: Iterable[DateParseType]):
        r'''
        Assume a list of dates as strings is supplied as argument
        '''
        self._data = []
        self._dataUncertainty = []
        for part in data:
            d = Date()
            d.load(part)
            self._data.append(d)  # a list of Date objects
            # can look at Date and determine overall error
            self._dataUncertainty.append(None)

    # PUBLIC PROPERTIES #

    @property
    def relevance(self):
        '''
        The relevance attribute takes only one value:
        `'between'`.
        '''
        return self._relevance

    @relevance.setter
    def relevance(self, value):
        if value != 'between':
            raise exceptions21.MetadataException(
                f'Relevance value is not supported by this object: {value!r}')
        self._relevance = value


# -----------------------------------------------------------------------------


class DateSelection(DatePrimitive):
    r'''
    Store a selection of dates, or a collection of dates that might all be
    possible

    >>> dd = metadata.DateSelection(
    ...     ['2009/12/31', '2010/1/28', '1894/1/28'],
    ...     )
    >>> str(dd)
    '2009/12/31 or 2010/01/28 or 1894/01/28'

    >>> dd = metadata.DateSelection(
    ...     [1750, '1775/03?'],
    ...     'and'
    ...     )
    >>> str(dd)
    '1750/--/-- and 1775/03?/--'

    >>> dd = metadata.DateSelection(
    ...     ['2009/12/31', '2010/1/28'],
    ...     'certain',
    ...     )
    Traceback (most recent call last):
    music21.exceptions21.MetadataException: Relevance value is not
        supported by this object: 'certain'

    Note that '1350 or 1351 and 1375' is not supported yet.
    '''

    # CLASS VARIABLES #

    isSingle = False

    # INITIALIZER #

    def __init__(self,
                 data: Iterable[DateParseType] = (),
                 relevance='or'):
        super().__init__(relevance)
        self._prepareData(data)

    # SPECIAL METHODS #

    def __str__(self):
        msg = []
        for d in self._data:
            msg.append(str(d))
        return f' {self._relevance} '.join(msg)

    # PRIVATE METHODS #

    def _prepareData(self, data: Iterable[DateParseType]):
        r'''
        Assume a list of dates as strings is supplied as argument.
        '''
        self._data = []
        self._dataUncertainty = []
        for part in data:
            d = Date()
            d.load(part)
            self._data.append(d)  # a list of Date objects
            # can look at Date and determine overall error
            self._dataUncertainty.append(None)

    # PUBLIC PROPERTIES #

    @property
    def relevance(self):
        '''
        The relevance attribute takes only two values:
        `'or'` or `'and'`.
        '''
        return self._relevance

    @relevance.setter
    def relevance(self, value):
        if value not in ('or', 'and'):
            raise exceptions21.MetadataException(
                f'Relevance value is not supported by this object: {value!r}')
        self._relevance = value


# -----------------------------------------------------------------------------


# This was enhanced in music21 v8 to add an optional encoding scheme (e.g. URI, DCMIPoint,
# etc) as well as whether the text is translated, or in the original language.
class Text(prebase.ProtoM21Object):
    r'''
    One unit of text data: a title, a name, or some other text data. Store the
    string and a language name or code. This object can be used and/or
    subclassed for a variety for of text storage.

    >>> td = metadata.Text('concerto in d', 'en')
    >>> str(td)
    'concerto in d'
    >>> td.language
    'en'
    '''

    # INITIALIZER #

    def __init__(self,
                 data: str | Text = '',
                 language: str | None = None,
                 isTranslated: bool | None = None,   # True, False, or None (unknown)
                 encodingScheme: str | None = None):
        if isinstance(data, Text):
            # accessing private attributes here; not desirable
            self._data: str | Text = data._data
            self._language: str | None = data._language
            self.isTranslated: bool | None = data.isTranslated
            self.encodingScheme: str | None = data.encodingScheme
        else:
            self._data = data
            self._language = language
            self.isTranslated = isTranslated
            self.encodingScheme = encodingScheme

    # SPECIAL METHODS #

    def __str__(self):
        if isinstance(self._data, bytes):
            return self._data.decode('UTF-8')
        elif not isinstance(self._data, str):
            return str(self._data)
        else:
            return self._data

    def _reprInternal(self):
        return str(self)

    def __eq__(self, other) -> bool:
        '''
        >>> t1 = metadata.Text('some text')
        >>> t2 = metadata.Text('some text')
        >>> t1 == t2
        True

        Language, isTranslated, and encodingScheme must all exactly match for equality.

        >>> t2 = metadata.Text('some text', language='en')
        >>> t1 == t2
        False
        >>> t2 = metadata.Text('some text', isTranslated=True)
        >>> t1 == t2
        False
        >>> t2 = metadata.Text('some text', encodingScheme='scheme42')
        >>> t1 == t2
        False

        Comparison with non-Text types, including bare strings,
        will always be considered unequal.

        >>> t1 == 'some text'
        False
        '''
        if type(other) is not type(self):
            return False
        if self._data != other._data:
            return False
        if self.language != other.language:
            return False
        if self.isTranslated != other.isTranslated:
            return False
        if self.encodingScheme != other.encodingScheme:
            return False
        return True


    def __lt__(self, other):
        '''
        Allows for alphabetically sorting two elements
        '''
        if type(other) is not type(self):
            return NotImplemented
        return (
            (self._data, self.language, self.isTranslated, self.encodingScheme)
            < (other._data, other.language, other.isTranslated, other.encodingScheme)
        )


    # PUBLIC PROPERTIES #

    @property
    def language(self):
        r'''
        Set the language of the Text stored within.

        >>> myText = metadata.Text('my text')
        >>> myText.language = 'en'
        >>> myText.language
        'en'
        '''
        return self._language

    @language.setter
    def language(self, value):
        self._language = value

    # PUBLIC METHODS #

    def getNormalizedArticle(self):
        r'''
        Return a string representation with normalized articles.

        >>> td = metadata.Text('Ale is Dear, The', language='en')
        >>> str(td)
        'Ale is Dear, The'

        >>> td.getNormalizedArticle()
        'The Ale is Dear'

        The language will determine whether the article is moved:

        >>> td.language = 'de'
        >>> td.getNormalizedArticle()
        'Ale is Dear, The'
        '''
        from music21 import text
        return text.prependArticle(str(self), self._language)

# -----------------------------------------------------------------------------


class Copyright(Text):
    '''
    A subclass of text that can also have a role

    >>> c = metadata.primitives.Copyright('Copyright 1945 Florence Price')
    >>> c
    <music21.metadata.primitives.Copyright Copyright 1945 Florence Price>
    >>> c.role is None
    True
    >>> str(c)
    'Copyright 1945 Florence Price'

    The text, language, isTranslated, role, etc. must be identical for equality.

    >>> c2 = metadata.Copyright('Copyright 1945 Florence Price')
    >>> c == c2
    True
    >>> c2 = metadata.Copyright('Copyright © 1945 Florence Price')
    >>> c == c2
    False
    >>> c2 = metadata.Copyright('Copyright 1945 Florence Price', language='en')
    >>> c == c2
    False
    >>> c2 = metadata.Copyright('Copyright 1945 Florence Price', isTranslated=True)
    >>> c == c2
    False
    >>> c2 = metadata.Copyright('Copyright 1945 Florence Price', role='other')
    >>> c == c2
    False

    Comparison against a non-Copyright object will always return False.

    >>> c == 1945
    False
    '''

    def __init__(self,
                 data: str | Text = '',
                 language: str | None = None,
                 isTranslated: bool | None = None,   # True, False, or None (unknown)
                 *, role=None):
        super().__init__(data, language, isTranslated)
        self.role = role

    def __eq__(self, other) -> bool:
        if type(other) is not type(self):
            return False
        if self._data != other._data:
            return False
        if self.language != other.language:
            return False
        if self.isTranslated != other.isTranslated:
            return False
        if self.role != other.role:
            return False
        return True


# -----------------------------------------------------------------------------


class Contributor(prebase.ProtoM21Object):
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

    # CLASS VARIABLES #

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

    # INITIALIZER #

    def __init__(self,
                 *,
                 name: str | Text | None = None,
                 names: Iterable[str | Text] = (),
                 role: str | Text | None = None,
                 birth: None | DateSingle | str = None,
                 death: None | DateSingle | str = None,
                 **keywords):
        self._role = None
        if role:
            # stored in self._role
            self.role = role  # validated with property
        else:
            self.role = None
        # a list of Text objects to support various spellings or
        # language translations
        self._names: list[Text] = []
        if name:  # a single
            if isinstance(name, Text):
                self._names.append(name)
            else:
                self._names.append(Text(name))
        if names:  # many
            for n in names:
                if isinstance(n, Text):
                    self._names.append(n)
                else:
                    self._names.append(Text(n))
        # store the nationality, if known (not currently used)
        self._nationality: list[Text] = []

        self.birth: DateSingle | None = None
        self.death: DateSingle | None = None

        if birth is not None:
            if not isinstance(birth, DateSingle):
                birthDS = DateSingle(birth)
            else:
                birthDS = birth
            self.birth = birthDS
        if death is not None:
            if not isinstance(death, DateSingle):
                deathDS = DateSingle(death)
            else:
                deathDS = death
            self.death = deathDS

    def _reprInternal(self):
        return f'{self.role}:{self.name}'

    def __str__(self):
        if not self.name:
            return ''
        return self.name

    def __eq__(self, other) -> bool:
        '''
        >>> c1 = metadata.Contributor(
        ...         role='composer',
        ...         name='The Composer',
        ...         birth='1923',
        ...         death='2013'
        ... )
        >>> c2 = metadata.Contributor(
        ...         role='composer',
        ...         name='The Composer',
        ...         birth='1923',
        ...         death='2013'
        ... )

        Names, role, birth, and death must all be identical for equality.

        >>> c1 == c2
        True
        >>> c2.role = 'lyricist'
        >>> c1 == c2
        False
        >>> c2 = metadata.Contributor(
        ...         role='composer',
        ...         name='A Composer',
        ...         birth='1923',
        ...         death='2013'
        ... )
        >>> c1 == c2
        False
        >>> c2 = metadata.Contributor(
        ...         role='composer',
        ...         names=['A Composer', 'The Composer'],
        ...         birth='1923',
        ...         death='2013'
        ... )
        >>> c1 == c2
        False
        >>> c2 = metadata.Contributor(
        ...         role='composer',
        ...         name='The Composer',
        ...         birth='1924',
        ...         death='2013'
        ... )
        >>> c1 == c2
        False
        >>> c2 = metadata.Contributor(
        ...         role='composer',
        ...         name='The Composer',
        ...         birth='1923',
        ...         death='2012'
        ... )
        >>> c1 == c2
        False

        Comparison with a non-Contributor object always returns False.

        >>> c1 == 'The Composer'
        False
        '''
        if type(other) is not type(self):
            return False
        if self._role != other._role:
            return False
        if len(self._names) != len(other._names):
            return False
        for name, otherName in zip(sorted(self._names), sorted(other._names)):
            if name != otherName:
                return False
        if self.birth != other.birth:
            return False
        if self.death != other.death:
            return False
        return True

    # PUBLIC METHODS #

    def age(self) -> datetime.timedelta | None:
        r'''
        Calculate the age at death of the Contributor, returning a
        datetime.timedelta object.

        >>> a = metadata.Contributor(
        ...     name='Beethoven, Ludwig van',
        ...     role='composer',
        ...     birth='1770/12/17',
        ...     death='1827/3/26',
        ...     )

        >>> a.birth
        <music21.metadata.primitives.DateSingle 1770/12/17>

        >>> a.age()
        datetime.timedelta(days=20552)

        >>> a.age().days
        20552

        >>> years = a.age().days // 365
        >>> years
        56

        If the composer is still alive, it returns the composer's current age.

        >>> shaw = metadata.Contributor(
        ...     name='Shaw, Caroline',
        ...     role='composer',
        ...     birth='1982/08/01',
        ...     )
        >>> shaw_years = shaw.age().days // 365

        This test will fail in 2067:

        >>> 36 < shaw_years < 85
        True
        '''
        if self.birth is None:
            return None

        if self.death is not None:
            d = self.death.datetime
            b = self.birth.datetime
            return d - b
        else:
            return datetime.datetime.now() - self.birth.datetime

    # PUBLIC PROPERTIES #

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
        if self._names:
            return str(self._names[0])
        else:
            return None

    @name.setter
    def name(self, value):
        # set first name
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

        >>> td.names = ['Czerny', 'Spohr']
        >>> td.names
        ['Czerny', 'Spohr']
        '''
        # return first name
        msg = []
        for n in self._names:
            msg.append(str(n))
        return msg

    @names.setter
    def names(self, values):
        if not common.isIterable(values):
            raise exceptions21.MetadataException(
                '.names must be a list -- do you mean .name instead?')
        self._names = []  # reset
        for n in values:
            self._names.append(Text(n))

    @property
    def role(self):
        r'''
        The role is what part this Contributor plays in the work.  Both
        full roll strings and roll abbreviations may be used.

        >>> td = metadata.Contributor()
        >>> td.role = 'composer'
        >>> td.role
        'composer'

        In case of a Humdrum role abbreviation, the role that is set
        is the full name:

        >>> td.role = 'lor'
        >>> td.role
        'orchestrator'

        Roles can be created on the fly:

        >>> td.role = 'court jester'
        >>> td.role
        'court jester'
        '''
        return self._role

    @role.setter
    def role(self, value):
        if value is None or value in self.roleAbbreviationsDict.values():
            self._role = value
        elif value in self.roleAbbreviationsDict:
            self._role = self.roleAbbreviationsDict[value]
        else:
            self._role = value

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
                f'no such role: {abbreviation!r}')

    @staticmethod
    def roleToAbbreviation(roleName):
        '''
        Convert `roleName` to role abbreviation:

        >>> metadata.Contributor.roleToAbbreviation('composer')
        'com'
        '''
        # note: probably not the fastest way to do this
        for role_id in Contributor.roleAbbreviationsDict:
            if roleName.lower() == Contributor.roleAbbreviationsDict[role_id].lower():
                return role_id
        raise exceptions21.MetadataException(f'No such role: {roleName}')

# -----------------------------------------------------------------------------


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

    # CLASS VARIABLES #

    relevance = 'creator'


# -----------------------------------------------------------------------------


class Imprint(prebase.ProtoM21Object):
    r'''
    An object representation of imprint, or publication.
    '''
    def __init__(self, **keywords):
        self.keywords = keywords

# !!!PUB: Publication status.
# !!!PPR: First publisher.
# !!!PDT: Date first published.
# !!!PPP: Place first published.
# !!!PC#: Publisher's catalogue number.
# !!!SCT: Scholarly catalogue abbreviation and number. E.g. BWV 551
# !!!SCA: Scholarly catalogue (unabbreviated) name. E.g.Köchel 117.
# !!!SMS: Manuscript source name.
# !!!SML: Manuscript location.
# !!!SMA: Acknowledgement of manuscript access.


# -----------------------------------------------------------------------------


# !!!YEP: Publisher of electronic edition.
# !!!YEC: Date and owner of electronic copyright.
# !!!YER: Date electronic edition released.
# !!!YEM: Copyright message.
# !!!YEN: Country of copyright.
# !!!YOR: Original document.
# !!!YOO: Original document owner.
# !!!YOY: Original copyright year.
# !!!YOE: Original editor.

# -----------------------------------------------------------------------------
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
#     'opc' : 'localeOfComposition',  # origin in abc


# -----------------------------------------------------------------------------


class Test(unittest.TestCase):

    def testText(self):
        from music21 import metadata

        text = metadata.primitives.Text('my text')
        text.language = 'en'
        self.assertEqual(text._data, 'my text')
        self.assertEqual(text._language, 'en')

    def testContributor(self):
        from music21 import metadata

        contributor = metadata.primitives.Contributor(
            role='composer',
            name='Gilles Binchois',
        )
        self.assertEqual(contributor.role, 'composer')
        self.assertEqual(contributor.relevance, 'contributor')
        self.assertEqual(contributor.name, 'Gilles Binchois')

    def testCreator(self):
        from music21 import metadata

        creator = metadata.primitives.Creator(
            role='composer',
            name='Gilles Binchois',
        )
        self.assertEqual(creator.role, 'composer')
        self.assertEqual(creator.relevance, 'creator')
        self.assertEqual(creator.name, 'Gilles Binchois')

    def testDate(self):
        from music21 import metadata

        date1 = metadata.primitives.Date(year=1843, yearError='approximate')
        date2 = metadata.primitives.Date(year='1843?')

        self.assertEqual(date1.year, 1843)
        self.assertEqual(date1.yearError, 'approximate')

        self.assertEqual(date2.year, 1843)
        self.assertEqual(date2.yearError, 'uncertain')

    def testDateValueError(self):
        with self.assertRaisesRegex(ValueError, 'Month must be.*not 13'):
            Date(month=13)

        for d, m, y in ((32, None, None),
                        (0, None, None),
                        (31, 4, None),
                        (30, 2, None),
                        (29, 2, 1999),
                        ):
            with self.assertRaisesRegex(ValueError, 'Day.*is not possible'):
                Date(year=y, month=m, day=d)

        with self.assertRaisesRegex(ValueError, 'Hour'):
            Date(hour=24)
        with self.assertRaisesRegex(ValueError, 'Minute'):
            Date(minute=61)
        with self.assertRaisesRegex(ValueError, 'Second'):
            Date(second=-1)

        self.assertIsNotNone(Date(year=2000, month=2, day=29))
        self.assertIsNotNone(Date(month=2, day=29))
        self.assertIsNotNone(Date(month=12, day=31))
        self.assertIsNotNone(Date(hour=23, minute=59, second=59))

    def testDateSingle(self):
        from music21 import metadata

        dateSingle = metadata.primitives.DateSingle(
            '2009/12/31', 'approximate')
        self.assertEqual(str(dateSingle), '2009/12/31')
        self.assertEqual(len(dateSingle._data), 1)
        self.assertEqual(dateSingle._relevance, 'approximate')
        self.assertEqual(dateSingle._dataUncertainty, ['approximate'])

    def testDateRelative(self):
        from music21 import metadata

        dateRelative = metadata.primitives.DateRelative('2001/12/31', 'prior')
        self.assertEqual(str(dateRelative), 'prior to 2001/12/31')
        self.assertEqual(dateRelative.relevance, 'prior')
        self.assertEqual(len(dateRelative._data), 1)
        self.assertEqual(dateRelative._dataUncertainty, [None])

    def testDateBetween(self):
        from music21 import metadata

        dateBetween = metadata.primitives.DateBetween(
            ('2009/12/31', '2010/1/28'))
        self.assertEqual(str(dateBetween), '2009/12/31 to 2010/01/28')
        self.assertEqual(dateBetween.relevance, 'between')
        self.assertEqual(dateBetween._dataUncertainty, [None, None])
        self.assertEqual(len(dateBetween._data), 2)

    def testDateSelection(self):
        from music21 import metadata

        dateSelection = metadata.primitives.DateSelection(
            ['2009/12/31', '2010/1/28', '1894/1/28'],
            'or',
        )
        self.assertEqual(str(dateSelection),
                         '2009/12/31 or 2010/01/28 or 1894/01/28')
        self.assertEqual(dateSelection.relevance, 'or')
        self.assertEqual(dateSelection._dataUncertainty, [None, None, None])
        self.assertEqual(len(dateSelection._data), 3)


# -----------------------------------------------------------------------------


_DOC_ORDER = (
    Text,
    Date,
    DateSingle,
    DateRelative,
    DateBetween,
    DateSelection,
    Contributor,
    Copyright,
)

DateParseType = Date | datetime.datetime | str
ValueType = DatePrimitive | Text | Contributor | Copyright | int


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)


# -----------------------------------------------------------------------------
