# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         common/enums.py
# Purpose:      Music21 Enumerations
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2021 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
from enum import Enum, EnumMeta


class StrEnumMeta(EnumMeta):
    def __contains__(cls, item):
        if isinstance(item, str):
            if item in cls.__members__.values():
                return True
            else:
                return False
        try:
            return super().__contains__(item)
        except TypeError:  # pragma: no cover
            return False


class BooleanEnum(Enum):
    '''
    An enum that replaces a boolean, except the "is" part, and
    allows specifying multiple values that can specify whether they
    equate to True or False.

    Useful for taking an element that was previously True/False and
    replacing it in a backwards-compatible way with an Enum.

    >>> from music21.common.enums import BooleanEnum
    >>> class Maybe(BooleanEnum):
    ...    YES = True
    ...    NO = False
    ...    MAYBE = 0.5
    ...    NOT_A_CHANCE = (False, 'not a chance')
    ...    DEFINITELY = (True, 'of course!')
    >>> bool(Maybe.YES)
    True
    >>> bool(Maybe.NO)
    False
    >>> bool(Maybe.MAYBE)
    True
    >>> bool(Maybe.NOT_A_CHANCE)
    False
    >>> bool(Maybe.DEFINITELY)
    True
    >>> Maybe.MAYBE == 0.5
    True
    >>> Maybe.NOT_A_CHANCE == 'not a chance'
    True
    >>> Maybe.NOT_A_CHANCE == False
    True
    >>> Maybe.NOT_A_CHANCE == True
    False
    >>> Maybe.NOT_A_CHANCE == 'not any chance'
    False
    >>> Maybe.DEFINITELY == 'of course!'
    True
    >>> Maybe.NOT_A_CHANCE == (False, 'not a chance')
    True
    '''
    @staticmethod
    def is_bool_tuple(v):
        if isinstance(v, tuple) and len(v) == 2 and isinstance(v[0], bool):
            return True
        else:
            return False

    # pylint having Enum problems with classes as usual.
    # pylint: disable=comparison-with-callable
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return super().__eq__(other)
        v = self.value
        if v == other:
            return True
        elif self.is_bool_tuple(v):
            if v[0] is other:
                return True
            return v[1] == other
        return False

    def __bool__(self):
        v = self.value
        if self.is_bool_tuple(v):
            return v[0]
        return bool(self.value)

    def __repr__(self):
        return f'<{self.__class__.__name__}.{self.name}>'


class StrEnum(str, Enum, metaclass=StrEnumMeta):
    '''
    An enumeration where strings can equal the value.

    See :class:`music21.common.enums.OffsetSpecial` for an
    example of how these work.
    '''
    def __repr__(self):
        return f'<{self.__class__.__name__}.{self.name}>'

    def __str__(self):
        '''
        >>> from music21.common.enums import OffsetSpecial
        >>> str(OffsetSpecial.AT_END)
        'highestTime'
        '''
        return str(self.value)


class ElementSearch(StrEnum):
    '''
    An enum representing the element search directions that can be provided
    to :meth:`~music21.base.Music21Object.getContextByClass`.
    '''
    BEFORE = 'getElementBefore'
    AFTER = 'getElementAfter'
    AT_OR_BEFORE = 'getElementAtOrBefore'
    AT_OR_AFTER = 'getElementAtOrAfter'
    BEFORE_OFFSET = 'getElementBeforeOffset'
    AFTER_OFFSET = 'getElementAfterOffset'
    AT_OR_BEFORE_OFFSET = 'getElementAtOrBeforeOffset'
    AT_OR_AFTER_OFFSET = 'getElementAtOrAfterOffset'
    BEFORE_NOT_SELF = 'getElementBeforeNotSelf'
    AFTER_NOT_SELF = 'getElementAfterNotSelf'
    ALL = 'all'


class OffsetSpecial(StrEnum):
    '''
    An enum that represents special offsets.

    The enum `AT_END` is equal to the string 'highestTime'

    >>> from music21.common.enums import OffsetSpecial
    >>> OffsetSpecial.AT_END
    <OffsetSpecial.AT_END>
    >>> 'highestTime' == OffsetSpecial.AT_END
    True
    >>> 'crazyOffset' in OffsetSpecial
    False
    >>> 6.0 in OffsetSpecial
    False
    >>> 'lowestOffset' in OffsetSpecial
    True
    >>> str(OffsetSpecial.AT_END)
    'highestTime'

    New in v7.
    '''
    AT_END: str = 'highestTime'
    LOWEST_OFFSET: str = 'lowestOffset'
    HIGHEST_OFFSET: str = 'highestOffset'


class GatherSpanners(BooleanEnum):
    '''
    An enumeration for how to gather missing spanners

    >>> from music21.common.enums import GatherSpanners

    Indicates all relevant spanners will be gathered:

    >>> GatherSpanners.ALL
    <GatherSpanners.ALL>
    >>> bool(GatherSpanners.ALL)
    True

    Indicates no relevant spanners will be gathered:

    >>> GatherSpanners.NONE
    <GatherSpanners.NONE>
    >>> bool(GatherSpanners.NONE)
    False

    Indicates only spanners where all of their members are in the excerpt
    will be gathered:

    >>> GatherSpanners.COMPLETE_ONLY
    <GatherSpanners.COMPLETE_ONLY>
    >>> bool(GatherSpanners.COMPLETE_ONLY)
    True
    '''
    ALL = True
    NONE = False
    COMPLETE_ONLY = 'completeOnly'


class MeterDivision(StrEnum):
    '''
    Represents an indication of how to divide a TimeSignature

    new in v7.
    '''
    FAST = 'fast'
    SLOW = 'slow'
    NONE = 'none'


if __name__ == '__main__':
    import music21
    music21.mainTest()
