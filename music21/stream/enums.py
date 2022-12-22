# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Name:         stream/enums.py
# Purpose:      enumerations for streams
#
# Authors:      Michael Scott Asato Cuthbert
#
# Copyright:    Copyright © 2020 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# -----------------------------------------------------------------------------
from __future__ import annotations

import enum

from music21.common.enums import StrEnum

class StaffType(enum.Enum):
    '''
    These are the same as MusicXML staff-type, except uppercase and "other"
    which reflects any other type.  Probably the best way of using "other"
    is to designate what it means with a .editorial.staffTypeExplanation = 'other'

    >>> stream.enums.StaffType.OSSIA
    <StaffType.OSSIA: 'ossia'>

    To get the musicxml name:

    >>> stream.enums.StaffType.OSSIA.value
    'ossia'

    >>> stream.enums.StaffType('cue')
    <StaffType.CUE: 'cue'>

    >>> stream.enums.StaffType('tiny')
    Traceback (most recent call last):
    ValueError: 'tiny' is not a valid StaffType
    '''
    REGULAR = 'regular'
    OSSIA = 'ossia'
    CUE = 'cue'
    EDITORIAL = 'editorial'
    ALTERNATE = 'alternate'
    OTHER = 'other'


class GivenElementsBehavior(StrEnum):
    APPEND = 'append'
    OFFSETS = 'offsets'
    INSERT = 'insert'


class RecursionType(StrEnum):
    ELEMENTS_FIRST = 'elementsFirst'
    FLATTEN = 'flatten'
    ELEMENTS_ONLY = 'elementsOnly'


class ShowNumber(StrEnum):
    DEFAULT = 'default'
    ALWAYS = 'always'
    NEVER = 'never'


if __name__ == '__main__':
    from music21 import mainTest
    mainTest()
