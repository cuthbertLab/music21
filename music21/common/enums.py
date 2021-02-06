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
from fractions import Fraction

class StrEnumMeta(EnumMeta):
    def __contains__(self, item):
        if isinstance(item, str):
            if item in self.__members__.values():
                return True
            else:
                return False
        try:
            return super().__contains__(item)
        except TypeError:
            return False

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
        return str(self.value)

if __name__ == '__main__':
    import music21
    music21.mainTest()
