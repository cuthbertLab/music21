# ------------------------------------------------------------------------------
# Name:         figuredBass/__init__.py
# Purpose:      Figured Bass representation, manipulation, and analysis
#
# Authors:      Jose Cabal-Ugaz
#               Michael Scott Asato Cuthbert
#
# Copyright:    Copyright © 2012-25 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
from __future__ import annotations

__all__ = [
    'FiguredBass',

    'checker',
    'examples',
    'harmony',
    'notation',
    'possibility',
    'realizer',
    'realizerScale',
    'resolution',
    'rules',
    'segment',
]

from music21.figuredBass import checker
from music21.figuredBass import examples
from music21.figuredBass import harmony
from music21.figuredBass.harmony import FiguredBass
from music21.figuredBass import notation
from music21.figuredBass import possibility
from music21.figuredBass import realizer
from music21.figuredBass import realizerScale
from music21.figuredBass import resolution
from music21.figuredBass import rules
from music21.figuredBass import segment

