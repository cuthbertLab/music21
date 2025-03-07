# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         midi/__init__.py
# Purpose:      Access to MIDI library / music21 classes for dealing with midi data
#
# Authors:      Christopher Ariza
#               Michael Scott Asato Cuthbert
#               (Will Ware -- see docs)
#
# Copyright:    Copyright © 2011-2013, 2019 Michael Scott Asato Cuthbert
#               Some parts of this module are in the Public Domain, see details.
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
Submodule for working with MIDI Data.  Files that used to be here are now
in base.py as of 2025.

Objects and tools for processing MIDI data.  Converts from MIDI files to
:class:`~music21.midi.base.MidiEvent`, :class:`~music21.midi.base.MidiTrack`, and
:class:`~music21.midi.base.MidiFile` objects, and vice versa.

Further conversion to-and-from MidiEvent/MidiTrack/MidiFile and music21 Stream,
Note, etc., objects takes place in :ref:`moduleMidiTranslate`.
'''
from __future__ import annotations

from music21 import environment

from music21.midi import base
from music21.midi import realtime
from music21.midi import percussion
from music21.midi import tests
from music21.midi import translate

from music21.midi.base import (
    MidiException,
    charToBinary,
    intsToHexBytes,
    getNumber,
    getVariableLengthNumber,
    getNumbersAsList,
    putNumber,
    putVariableLengthNumber,
    putNumbersAsList,
    ChannelVoiceMessages,
    ChannelModeMessages,
    MetaEvents,
    SysExEvents,
    METAEVENT_MARKER,
    MidiEvent,
    DeltaTime,
    MidiTrack,
    MidiFile,
)

__all__ = [
    'base', 'realtime', 'percussion', 'tests', 'translate',
    # from base
    'MidiException',
    'charToBinary',
    'intsToHexBytes',
    'getNumber',
    'getVariableLengthNumber',
    'getNumbersAsList',
    'putNumber',
    'putVariableLengthNumber',
    'putNumbersAsList',

    'ChannelVoiceMessages',
    'ChannelModeMessages',
    'MetaEvents',
    'SysExEvents',
    'METAEVENT_MARKER',
    'MidiEvent',
    'DeltaTime',
    'MidiTrack',
    'MidiFile',
]

environLocal = environment.Environment('midi')


# ------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER: list[type] = [MidiEvent, DeltaTime, MidiTrack, MidiFile]

if __name__ == '__main__':
    import music21
    music21.mainTest()


