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
		

		# --- begin general types of things to hash ---
		self.hashNotes = True # is this even necessary?
		self.hashRests = True
		self.hashChords = True
		# --- end general types of things to hash ---

		# --- begin note properties to hash ---
		self.hashPitch = True
		self.hashDuration = True
		self.roundDuration = True
		self.hashOffset = True
		self.roundOffset = True
		self.outOfKey = False
		self.isAccidental = False
		self.isTied = False
		# --- end note properties to hash ---

	def setSmartDefaults(self):
		"""
		maybe multiple of these kind of functions to set defaults that aid certain types of hashes
		"""
		pass

	# --- Begin Rounding Helper Functions ---
	def _getApproxDurOrOffset(self, durOrOffset, granularity=32):
		return round(durOrOffset*granularity)/granularity
	

	def _approximatelyEqual(self, a, b, sig_fig = 2):
		"""
		use to look at whether beat lengths are close, within a certain range
		probably can use for other things that are approx. equal
		"""
		return (a==b or int(a*10**sig_fig) == int(b*10**sig_fig))

	# --- End Rounding Helper Functions ---

	# --- Begin Hashing Functions --- 

	def generalHash(self, granularity=32):
		"""
		hasher with ability to turn certain parts off/on
		"""
		note_container = []
		stream_notes = self.stream.getElementsByClass(note.GeneralNote)
		for n in stream_notes:
			if n.isNote and self.hashNotes:
				if self.hashDuration:
					if self.roundDuration:
						note_dur = _getApproxDurOrOffset(n.duration.quarterLength, granularity)
					else: 
						note_dur = n.duration.quarterLength
				else: note_dur = None

				if self.hashOffset:
					if self.roundOffset:
						note_offset = _getApproxDurOrOffset(n.offset, granularity)
					else:
						note_offset = n.offset
				else:
					note_offset = None

				note_container.append(NoteHash(n.pitch.midi, note_dur, note_offset))
			elif n.isChord and self.hashChords:
				for p in n.pitches:
					note_container.append(NoteHash(p.midi, note_dur, note_offset))
			elif n.isRest and self.hashRests: # n is Rest
				note_container.append(NoteHash(None, note_dur, note_offset))

			else:
				raise Exception("Not a note, rest, or chord; shouldn't get here!")
		return note_container
			 

	def basicHash(self):
		"""
		proof of concept, likely incomplete feature

		hashes notes in a stream based on pitch, duration, beat
		pitch: absolute in this sense; maps to midi value between 21 and 108
		duration: length of note 
		beat: offset of each note, relative to the beginning of the stream
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
	# --- End Hashing Functions ---

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
