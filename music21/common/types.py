# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         common/types.py
# Purpose:      Music21 Typing aids
#
# Authors:      Michael Scott Asato Cuthbert
#
# Copyright:    Copyright © 2021-2023 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
from __future__ import annotations

from collections.abc import Callable, Iterable
from fractions import Fraction
import typing as t

from music21.common.enums import OffsetSpecial

if t.TYPE_CHECKING:
    import music21  # pylint: disable=unused-import

DocOrder = list[str | Callable]
OffsetQL = float | Fraction
OffsetQLSpecial = float | Fraction | OffsetSpecial
OffsetQLIn = int | float | Fraction

StreamType = t.TypeVar('StreamType', bound='music21.stream.Stream')
StreamType2 = t.TypeVar('StreamType2', bound='music21.stream.Stream')
M21ObjType = t.TypeVar('M21ObjType', bound='music21.base.Music21Object')
M21ObjType2 = t.TypeVar('M21ObjType2', bound='music21.base.Music21Object')  # when you need another

# does not seem to like the | way of spelling
ClassListType = t.Union[str, Iterable[str], type[M21ObjType], Iterable[type[M21ObjType]]]
StepName = t.Literal['C', 'D', 'E', 'F', 'G', 'A', 'B']
