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

NoteHash = collections.namedtuple('NoteHash', ['pitch', 'duration', 'beat'])

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
		note_container = []
		# TODO: perhaps change container to be a deque? ordered dict?
		stream_notes = self.stream.getElementsByClass(note.GeneralNote)
		for n in stream_notes:
			if n.isNote:
				note_container.append(NoteHash(n.pitch.midi, n.duration.quarterLength, n.offset))
			elif n.isChord:
				for p in n.pitches:
					note_container.append(NoteHash(p.midi, n.duration.quarterLength, n.offset))
			else: # n is Rest
				note_container.append(NoteHash(None, n.duration.quarterLength, n.offset))
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
		r = note.Rest(quarterLength=1.5)
		s1.append(note1)
		s1.append(note2)
		s1.append(note3)
		s1.append(cMinor)
		s1.append(r)
		h = Hasher(s1)
		hashes_plain_numbers = [(60, 2.0, 0.0), (66, 1.0, 2.0), (46, 1.0, 3.0), (60, 2.0, 4.0), (67, 2.0, 4.0), (75, 2.0, 4.0), (None, 1.5, 6.0)]
		hashes_in_format = [NoteHash(pitch=x, duration=y, beat=z) for (x, y, z) in hashes_plain_numbers]
		self.assertEqual(h.basicHash(), hashes_in_format)


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
