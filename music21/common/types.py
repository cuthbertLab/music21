# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         common/types.py
# Purpose:      Music21 Typing aids
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2021 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
from fractions import Fraction
from typing import Union, TypeVar, TYPE_CHECKING

from music21.common.enums import OffsetSpecial

if TYPE_CHECKING:
    import music21

OffsetQL = Union[float, Fraction]
OffsetQLSpecial = Union[float, Fraction, OffsetSpecial]
OffsetQLIn = Union[int, float, Fraction]

StreamType = TypeVar('StreamType', bound='music21.stream.Stream')
M21ObjType = TypeVar('M21ObjType', bound='music21.base.Music21Object')
