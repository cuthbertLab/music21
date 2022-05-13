# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         common/types.py
# Purpose:      Music21 Typing aids
#
# Authors:      Michael Scott Asato Cuthbert
#
# Copyright:    Copyright © 2021 Michael Scott Asato Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
from fractions import Fraction
from typing import (Union, TypeVar, TYPE_CHECKING, Iterable, Type, Literal, Callable,
                    List)

from music21.common.enums import OffsetSpecial

if TYPE_CHECKING:
    import music21

DocOrder = List[Union[str, Callable]]
OffsetQL = Union[float, Fraction]
OffsetQLSpecial = Union[float, Fraction, OffsetSpecial]
OffsetQLIn = Union[int, float, Fraction]

StreamType = TypeVar('StreamType', bound='music21.stream.Stream')
StreamType2 = TypeVar('StreamType2', bound='music21.stream.Stream')
M21ObjType = TypeVar('M21ObjType', bound='music21.base.Music21Object')
M21ObjType2 = TypeVar('M21ObjType2', bound='music21.base.Music21Object')  # when you need another

ClassListType = Union[str, Iterable[str], Type[M21ObjType], Iterable[Type[M21ObjType]]]
StepName = Literal['C', 'D', 'E', 'F', 'G', 'A', 'B']
