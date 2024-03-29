# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         search/__init__.py
# Purpose:      music21 classes for searching within files
#
# Authors:      Michael Scott Asato Cuthbert
#
# Copyright:    Copyright © 2011-2013 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
Methods and Classes useful in searching within scores.

For searching a group of scores, see the search functions within
:ref:`moduleCorpus` .
'''
from __future__ import annotations

__all__ = [
    'base', 'lyrics', 'segment', 'serial',

    'Wildcard', 'WildcardDuration', 'SearchMatch', 'StreamSearcher',
    'streamSearchBase', 'rhythmicSearch', 'noteNameSearch', 'noteNameRhythmicSearch',
    'approximateNoteSearch', 'approximateNoteSearchNoRhythm', 'approximateNoteSearchOnlyRhythm',
    'approximateNoteSearchWeighted',
    'translateStreamToString',
    'translateDiatonicStreamToString', 'translateIntervalsAndSpeed',
    'translateStreamToStringNoRhythm', 'translateStreamToStringOnlyRhythm',
    'translateNoteToByte',
    'translateNoteWithDurationToBytes',
    'translateNoteTieToByte',
    'translateDurationToBytes',
    'mostCommonMeasureRhythms',
    'SearchException',
]

from music21.search import base
from music21.search import lyrics
from music21.search import segment
from music21.search import serial

from music21.search.base import *
