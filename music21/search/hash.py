# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         hash.py
# Purpose:      Hash musical notation
#
# Authors:      Emily Zhang
#
# Copyright:    Copyright © 2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------

import unittest

import copy
import collections
import difflib

from music21 import base
from music21 import common
from music21 import environment
from music21 import exceptions21
from music21 import note
from music21 import search
from music21 import stream

class Hasher(object):

	def __init__(self, stream):
		self.stream = stream

	def basicHash(self):

		"""
		proof of concept, likely incomplete feature

		hashes notes in a stream based on pitch, duration, beat
		pitch: absolute in this sense; maps to midi value between 21 and 108
		duration: length of note 
		beat: offset of each note, relative to the beginning of the stream

		leaves out rests for now
		"""
		NoteHash = collections.namedtuple('NoteHash', ['pitch', 'duration', 'beat'])
		note_container = []
		# TODO: perhaps change container to be a deque? ordered dict?
		stream_notes = self.stream.getElementsByClass(note.Note)
		for n in stream_notes:
			note_container.append(NoteHash(n.pitch.midi, n.duration.quarterLength, n.offset))
		return note_container

class Test(unittest.TestCase):
	def runTest(self):
		pass
	def testBasicHash(self):
		from music21 import *
		s1 = stream.Stream()
		note1 = note.Note("C4")
		note1.duration.type = 'half'
		note2 = note.Note("F#4")
		note3 = note.Note("B-2")
		cMinor = chord.Chord(["C4","G4","E-5"])
		cMinor.duration.type = 'half'
		s1.append(note1)
		s1.append(note2)
		s1.append(note3)
		s1.append(cMinor)
		h = Hasher(s1)
		print h.basicHash()


class TestExternal(unittest.TestCase):
	def runTest(self):
		pass

	def testBasicHash(self):
		from music21 import corpus
		s1 = corpus.parse('xmlscores/Bologna_596_Nulla_Pitie')
		print basicHash(s1)

if __name__ == "__main__":
    import music21
    music21.mainTest(Test) 
