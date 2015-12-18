# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         tree/__init__.py
# Purpose:      Tools for grouping notes and chords into a searchable tree
#               organized by start and stop offsets
#
# Authors:      Josiah Wolf Oberholtzer
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2013-15 Michael Scott Cuthbert and the music21
#               Project
# License:      LGPL or BSD, see license.txt
#------------------------------------------------------------------------------
'''
Tools for grouping notes and chords into a searchable tree
organized by start and stop offsets.

This is a lower-level tool that for now at least normal music21
users won't need to worry about.
'''
__all__ = ['analysis', 'core', 'fromStream', 'node', 'spans', 'toStream', 'trees', 'verticality']

import unittest

from music21.tree import analysis 
from music21.tree import core
from music21.tree import fromStream
from music21.tree import node 
from music21.tree import spans 
from music21.tree import toStream
from music21.tree import trees 
from music21.tree import verticality 


#------------------------------------------------------------------------------

# TODO: Test with scores with Voices: cpebach/h186

def makeExampleScore():
    r'''
    Makes example score for use in stream-to-tree conversion docs.

    >>> score = tree.makeExampleScore()
    >>> score.show('text')
    {0.0} <music21.stream.Part ...>
        {0.0} <music21.instrument.Instrument PartA: : >
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.clef.BassClef>
            {0.0} <music21.meter.TimeSignature 2/4>
            {0.0} <music21.note.Note C>
            {1.0} <music21.note.Note D>
        {2.0} <music21.stream.Measure 2 offset=2.0>
            {0.0} <music21.note.Note E>
            {1.0} <music21.note.Note F>
        {4.0} <music21.stream.Measure 3 offset=4.0>
            {0.0} <music21.note.Note G>
            {1.0} <music21.note.Note A>
        {6.0} <music21.stream.Measure 4 offset=6.0>
            {0.0} <music21.note.Note B>
            {1.0} <music21.note.Note C>
            {2.0} <music21.bar.Barline style=final>
    {0.0} <music21.stream.Part ...>
        {0.0} <music21.instrument.Instrument PartB: : >
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.clef.BassClef>
            {0.0} <music21.meter.TimeSignature 2/4>
            {0.0} <music21.note.Note C#>
        {2.0} <music21.stream.Measure 2 offset=2.0>
            {0.0} <music21.note.Note G#>
        {4.0} <music21.stream.Measure 3 offset=4.0>
            {0.0} <music21.note.Note E#>
        {6.0} <music21.stream.Measure 4 offset=6.0>
            {0.0} <music21.note.Note D#>
            {2.0} <music21.bar.Barline style=final>

    '''
    from music21 import converter
    from music21 import stream
    streamA = converter.parse('tinynotation: 2/4 C4 D E F G A B C')
    streamB = converter.parse('tinynotation: 2/4 C#2  G#  E#  D#')
    streamA.makeMeasures(inPlace=True)
    streamB.makeMeasures(inPlace=True)
    partA = stream.Part()
    for x in streamA:
        partA.append(x)
    instrumentA = partA.getInstrument()
    instrumentA.partId = 'PartA'
    partA.insert(0, instrumentA)
    partB = stream.Part()
    for x in streamB:
        partB.append(x)
    instrumentB = partB.getInstrument()
    instrumentB.partId = 'PartB'
    partB.insert(0, instrumentB)
    score = stream.Score(id='exampleScore')
    score.insert(0, partA)
    score.insert(0, partB)
    return score


#------------------------------------------------------------------------------


if __name__ == "__main__":
    import music21
    music21.mainTest()
