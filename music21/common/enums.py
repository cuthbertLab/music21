# ------------------------------------------------------------------------------
# Name:         common/enums.py
# Purpose:      Music21 Enumerations
#
# Authors:      Michael Scott Asato Cuthbert
#
# Copyright:    Copyright © 2021-2023 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
from __future__ import annotations

from enum import Enum, IntEnum, StrEnum
import re


class HexEnum(IntEnum):
    '''
    An IntEnum that displays its repr in hex.

    >>> from music21.midi import ChannelVoiceMessages
    >>> ChannelVoiceMessages.NOTE_ON
    <ChannelVoiceMessages.NOTE_ON: 0x90>
    >>> ChannelVoiceMessages.NOTE_ON in ChannelVoiceMessages
    True
    >>> 0x90 in ChannelVoiceMessages
    True

    Note: before v11 this was called `ContainsEnum` and had a `hasValue` to check for
        containment.  Not necessary with Python 3.12 being the minimum version.
        `ContainsEnum` alias will be removed in v12.
    '''
    def __repr__(self) -> str:
        '''
        Display the repr in hex.
        '''
        val = super().__repr__()
        return re.sub(r'(\d+)', lambda m: f'0x{int(m.group(1)):X}', val)

    @classmethod
    def hasValue(cls, item: object|int) -> bool:
        '''
        Deprecated -- to be removed in v12.  Just do `item in cls`
        '''
        return item in cls

ContainsEnum = HexEnum


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
    def is_bool_tuple(v: object) -> bool:
        if isinstance(v, tuple) and len(v) == 2 and isinstance(v[0], bool):
            return True
        else:
            return False

    def __eq__(self, other: object) -> bool:
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

    def __bool__(self) -> bool:
        v = self.value
        if self.is_bool_tuple(v):
            return v[0]
        return bool(self.value)

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__}.{self.name}>'


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

    * New in v7.
    * Note -- a previous note said that the 'highestTime' == OffsetSpecial.AT_END
      would be removed in v9 or an upcoming music21 release.  Since then, Python
      changed direction and in 3.11 added StrEnum to the standard library and in 3.12
      allows for containment checks of strings in StrEnum (such as
      `'lowestOffset' in OffsetSpecial` returning True).  Therefore, there is no
      reason for music21 to ever remove this valuable and backwards compatible
      tool.
    '''
    AT_END = 'highestTime'
    LOWEST_OFFSET = 'lowestOffset'
    HIGHEST_OFFSET = 'highestOffset'


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


class AppendSpanners(StrEnum):
    '''
    An enumeration for how to append related spanners when appending objects to a written file.

    AppendSpanners.NORMAL means append the spanners that start with the object, then append
        the object, then append the spanners that end with the object.
    AppendSpanners.RELATED_ONLY means append the spanners that start with the object, then
        append the spanners that end with the object (i.e. do not append the object).
    AppendSpanners.NONE means do not append the related spanners at all (i.e. only append
        the object).

    * New in v9.
    '''
    NORMAL = 'normal'
    RELATED_ONLY = 'related_only'
    NONE = 'none'


class OrnamentDelay(StrEnum):
    '''
    An enumeration for the delay in an ornament (e.g. a delayed turn).  The delay for an
    ornament can be set to one of these values, or to an OffsetQL for a timed delay.

    OrnamentDelay.NO_DELAY means there is no delay (this is equivalent to setting delay to 0.0)
    OrnamentDelay.DEFAULT_DELAY means the delay is half the duration of the ornamented note.

    * New in v9.
    '''
    NO_DELAY = 'noDelay'
    DEFAULT_DELAY = 'defaultDelay'


class MeterDivision(StrEnum):
    '''
    Represents an indication of how to divide a TimeSignature

    * New in v7.
    '''
    FAST = 'fast'
    SLOW = 'slow'
    NONE = 'none'


if __name__ == '__main__':
    import music21
    music21.mainTest()
