# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Name:         stream/__init__.py
# Purpose:      base classes for dealing with groups of positioned objects
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#               Josiah Wolf Oberholtzer
#               Evan Lynch
#
# Copyright:    Copyright © 2008-2020 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# -----------------------------------------------------------------------------
from music21.exceptions21 import StreamException, ImmutableStreamException
from music21.stream.base import (
    Stream, Opus, Score, Part, PartStaff, Measure, Voice,
    SpannerStorage, VariantStorage, System, StreamType
)
from music21.stream import core
from music21.stream import enums
from music21.stream import filters
from music21.stream import iterator
from music21.stream import makeNotation
from music21.stream import streamStatus
from music21.stream import tests
