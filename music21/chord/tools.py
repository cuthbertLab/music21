# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         chord/tools.py
# Purpose:      Chord utilities too obscure to go on the Chord object
#
# Authors:      Michael Scott Asato Cuthbert
#
# Copyright:    Copyright © 2022-2023 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
Chord utilities too obscure to go on the Chord object, yet still helpful
enough to go in the music21 core library.
'''
from __future__ import annotations

import typing as t

if t.TYPE_CHECKING:
    from music21 import chord
    from music21 import pitch

def allChordSteps(c: chord.Chord) -> dict[int, pitch.Pitch]:
    '''
    Return a dictionary of all chordSteps in the chord.
    If more than one pitch shares the same chordStep such as the third
    in (C, E-, E, G), then only the first will appear in the dictionary.

    The dictionary will be ordered by the order of pitches in the Chord.

    More efficient than calling [getChordStep(x) for x in range(1, 8)]
    which would be O(n^2) on number of pitches.

    Requires `root()` to be defined.

    >>> ch = chord.Chord('C4 E4 G4 B4 C5 D5')
    >>> chord.tools.allChordSteps(ch)
    {1: <music21.pitch.Pitch C4>,
     3: <music21.pitch.Pitch E4>,
     5: <music21.pitch.Pitch G4>,
     7: <music21.pitch.Pitch B4>,
     2: <music21.pitch.Pitch D5>}
    '''
    root_dnn = c.root().diatonicNoteNum
    out_map: dict[int, pitch.Pitch] = {}
    for thisPitch in c.pitches:
        diatonicDistance = ((thisPitch.diatonicNoteNum - root_dnn) % 7) + 1
        if diatonicDistance not in out_map:
            out_map[diatonicDistance] = thisPitch
    return out_map


if __name__ == '__main__':
    import music21
    music21.mainTest()

