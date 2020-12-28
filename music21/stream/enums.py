# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Name:         stream/enums.py
# Purpose:      enumerations for streams
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2020 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# -----------------------------------------------------------------------------
import enum

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


if __name__ == '__main__':
    from music21 import mainTest
    mainTest()
