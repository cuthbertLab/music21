# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         common/enums.py
# Purpose:      Music21 Enumerations
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2009-2015 Michael Scott Cuthbert and the music21 Project
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
    An enum that replaces a boolean, except the "is"

    >>> from music21.common.enums import BooleanEnum
    >>> class Maybe(BooleanEnum):
    ...    YES = True
    ...    NO = False
    ...    MAYBE = 0.5
    >>> bool(Maybe.YES)
    True
    >>> bool(Maybe.NO)
    False
    >>> Maybe.MAYBE == 0.5
    True
    '''
    def __eq__(self, other):
        if super().__eq__(other):
            return True
        return self.value() == other

    def __bool__(self):
        return bool(self.value)

    def __repr__(self):
        return f'<{self.__class__.__name__}.{self.name}>'


class OffsetSpecial(str, Enum, metaclass=StrEnumMeta):
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

    New in v7.
    '''
    AT_END: str = 'highestTime'
    LOWEST_OFFSET: str = 'lowestOffset'
    HIGHEST_OFFSET: str = 'highestOffset'

    def __repr__(self):
        return f'<{self.__class__.__name__}.{self.name}>'

    def __str__(self):
        '''
        >>> from music21.common.enums import OffsetSpecial
        >>> str(OffsetSpecial.AT_END)
        'highestTime'
        '''
        return str(self.value)


class GatherSpanners(BooleanEnum):
    '''
    An enumeration for how to gather missing spanners

    >>> from music21.common.enums import GatherSpanners

    Indicates all relevant spanners will be gathered:

    >>> GatherSpanners.ALL
    <GatherSpanners.ALL>

    Indicates no relevant spanners will be gathered:

    >>> GatherSpanners.NONE
    <GatherSpanners.NONE>

    Indicates only spanners where all of their members are in the excerpt
    will be gathered:

    >>> GatherSpanners.COMPLETE_ONLY
    <GatherSpanners.COMPLETE_ONLY>
    '''
    ALL = True
    NONE = False
    COMPLETE_ONLY = 'completeOnly'


if __name__ == '__main__':
    import music21
    music21.mainTest()
