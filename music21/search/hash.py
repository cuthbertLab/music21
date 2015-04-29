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
	def __init__(self):
		self.stream = stream
		
		# --- begin general types of things to hash ---
		self.hashNotes = True
		self.hashRests = True
		self.hashChords = True
		# --- end general types of things to hash ---

		# --- begin hashing settings --- 
		self.stripTies = False
		
		# self.key = None # useful if available to see if notes are in key maybe?
		# --- end hashing settings ---

		# --- begin note properties to hash ---
		self.hashPitch = True
		self.hashMIDI = True # otherwise, hash string "C-- instead of 58"
		self.hashDuration = True
		self.roundDuration = True
		self.hashOffset = True
		self.roundOffset = True
		self.granularity = 32
		self.hashIntervalFromLastNote = False
		# self.outOfKey = False
		# self.isAccidental = False
		self.hashisTied = False
		# --- end note properties to hash ---

		# self.tupleList = []
		self.hashingFunctions = {}
		self.hash()

	def setupTupleList(self):
		tupleList = []
		if self.hashNotes:
			tupleList.append(self.buildNoteHashes())
		if self.hashRests:
			tupleList.append(self.buildRestHashes())
		if self.hashChords:
			pass

		self.tupleList = tupleList
		self.tupleClass = collections.namedtuple('NoteHash', tupleList)

	def buildNoteHashes(self):
		noteHashes = []
		if self.hashPitch:
			noteHashes.append("Pitch")
			if self.hashMIDI:
				self.hashingFunctions["Pitch"] = "hashMIDIPitch"
			elif not self.hashMIDI:
				self.hashingFunctions["Pitch"] = "hashNotePitch" 
				# note to self: look at pitch.py functions

				# if self.isAccidental:
				# 	noteHashes.append("IsAccidental")

		if self.hashDuration:
			noteHashes.append("Duration")
			if self.roundDuration:
				self.hashingFunctions["Duration"] = "hashRoundedDuration"
			else:
				self.hashingFunctions["Duration"] = "hashDuration"

		if self.hashOffset:
			noteHashes.append("Offset")
			if self.roundOffset:
				self.hashingFunctions["Offset"] = "hashRoundedOffset"
			else:
				self.hashingFunctions["Offset"] = "hashOffset"

		if self.hashIntervalFromLastNote:
			noteHashes.append("IntervalFromLastNote")
			self.hashingFunctions["IntervalFromLastNote"] = "hashIntervalFromLastNote"

	def buildRestHashes(self):
		# see buildNoteHashes for example
		pass

	def buildChordHashes(self):
		# see buildNoteHashes for example
		pass

	def preprocessStream(self, stream):
		if self.stripTies:
			stream = stream.stripTies()
		return stream
		# TODO: more preprocessing options

	def hash(self, stream):
		self.setupTupleList()
		stream = self.preprocessStream(stream)
		

	# --- Begin Rounding Helper Functions ---
	def _getApproxDurOrOffset(self, durOrOffset):
		return round(durOrOffset*self.granularity)/self.granularity
	

	def _approximatelyEqual(self, a, b, sig_fig = 2):
		"""
		use to look at whether beat lengths are close, within a certain range
		probably can use for other things that are approx. equal
		"""
		return (a==b or int(a*10**sig_fig) == int(b*10**sig_fig))

	# --- End Rounding Helper Functions ---

	# --- Begin Hashing Functions --- 

	def generalHash(self, stream):
		"""
		hasher with ability to turn certain parts off/on
		"""
		note_container = []
		stream_notes = self.stream.getElementsByClass(note.GeneralNote)
		for n in stream_notes:
			if n.isNote and self.hashNotes:
				if self.hashDuration:
					if self.roundDuration:
						note_dur = _getApproxDurOrOffset(n.duration.quarterLength)
					else: 
						note_dur = n.duration.quarterLength
				else: note_dur = None

				if self.hashOffset:
					if self.roundOffset:
						note_offset = _getApproxDurOrOffset(n.offset)
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
				print Exception("Not a note, rest, or chord; shouldn't get here!")
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
		h = Hasher()
		hashes_plain_numbers = [(60, 2.0, 0.0), (66, 1.0, 2.0), (46, 1.0, 3.0), (60, 2.0, 4.0), (67, 2.0, 4.0), (75, 2.0, 4.0), (None, 1.5, 6.0)]
		hashes_in_format = [NoteHash(pitch=x, duration=y, beat=z) for (x, y, z) in hashes_plain_numbers]
		self.assertEqual(h.basicHash(s1), hashes_in_format)


class TestExternal(unittest.TestCase):
	def runTest(self):
		pass

	def testBasicHash(self):
		from music21 import corpus
		s1 = corpus.parse('xmlscores/Bologna_596_Nulla_Pitie')
		print basicHash(s1.parts[0])

if __name__ == "__main__":
    import music21
    music21.mainTest(Test) 
