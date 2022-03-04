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
from typing import Union

from music21.common.enums import OffsetSpecial

OffsetQL = Union[float, Fraction]
OffsetQLSpecial = Union[float, Fraction, OffsetSpecial]
OffsetQLIn = Union[int, float, Fraction]
