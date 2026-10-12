# -----------------------------------------------------------------------------
# Name:         tree/__init__.py
# Purpose:      Tools for grouping notes and chords into a searchable tree
#               organized by start and stop offsets
#
# Authors:      Joséphine Wolf Oberholtzer
#               Michael Scott Asato Cuthbert
#
# Copyright:    Copyright © 2013-2015 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# -----------------------------------------------------------------------------
'''
Tools for grouping notes and chords into a searchable tree
organized by start and stop offsets.

This is a lower-level tool that for now at least normal music21
users won't need to worry about.
'''
from __future__ import annotations

__all__ = [
    'analysis',
    'core',
    'examples',
    'fromStream',
    'makeExampleScore',
    'node',
    'spans',
    'toStream',
    'trees',
    'verticality',
]

# import unittest

from music21.tree import analysis
from music21.tree import core
from music21.tree import examples
from music21.tree.examples import makeExampleScore
from music21.tree import fromStream
from music21.tree import node
from music21.tree import spans
from music21.tree import toStream
from music21.tree import trees
from music21.tree import verticality


if __name__ == '__main__':
    import music21
    music21.mainTest()
