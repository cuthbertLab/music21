# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         noteworthy/__init__.py
# Purpose:      parses NWCTXT Notation
#
# Authors:      Jordi Bartolome
#               Michael Scott Asato Cuthbert
#
# Copyright:    Copyright © 2006-2011 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
from __future__ import annotations

__all__ = ['translate', 'binaryTranslate']

from music21.noteworthy import binaryTranslate
from music21.noteworthy import translate

dictionaryNoteLength = {
    'Whole': 4, 'Half': 2, '4th': 1, '8th': 0.5,
    '16th': 0.25, '32nd': 0.125, '64th': 0.0625,
    0: 0,
}

dictionaryTreble = {1: 'C', 2: 'D', 3: 'E', 4: 'F', 5: 'G', 6: 'A', 7: 'B', 'octave': 5}
dictionaryBass = {-1: 'C', 0: 'D', 1: 'E', 2: 'F', 3: 'G', 4: 'A', 5: 'B', 'octave': 3}
dictionaryAlto = {0: 'C', 1: 'D', 2: 'E', 3: 'F', 4: 'G', 5: 'A', 6: 'B', 'octave': 4}
dictionaryTenor = {-5: 'C', -4: 'D', -3: 'E', -2: 'F', -1: 'G', 0: 'A', 1: 'B', 'octave': 3}
dictionarySharp = {1: 'F', 2: 'C', 3: 'G', 4: 'D', 5: 'A', 6: 'E', 7: 'B'}
dictionaryFlat = {1: 'B', 2: 'E', 3: 'A', 4: 'D', 5: 'G', 6: 'C', 7: 'F'}
dictionaries = {
    'dictionaryNoteLength': dictionaryNoteLength,
    'dictionaryTreble': dictionaryTreble,
    'dictionaryAlto': dictionaryAlto,
    'dictionaryTenor': dictionaryTenor,
    'dictionaryBass': dictionaryBass,
    'dictionarySharp': dictionarySharp,
    'dictionaryFlat': dictionaryFlat,
}

