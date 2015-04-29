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
		# --- begin general types of things to hash ---
		self.hashNotes = True
		self.hashRests = True
		self.hashChords = True
		# --- end general types of things to hash ---

		# --- begin general hashing settings --- 
		self.stripTies = False
		
		# --- end general hashing settings ---

		# --- begin note properties to hash ---
		self.hashPitch = True
		self.hashMIDI = True # otherwise, hash string "C-- instead of 58"
		self.hashDuration = True
		self.roundDuration = True
		self.hashOffset = True
		self.roundOffset = True
		self.granularity = 32
		self.hashIntervalFromLastNote = False
		self.hashIsAccidental = False
		self.hashIsTied = False
		# --- end note properties to hash ---

		self.tupleList = []
		self.validTypes = []
		self.stateVars = {} # keeps track of last note, key sig
		self.hashingFunctions = {}
		# self.hash()

	def setupValidTypesAndStateVars(self):
		if self.hashNotes:
			self.validTypes.append(note.Note)

		if self.hashRests:
			self.validTypes.append(note.Rest)

		if self.hashChords:
			self.validTypes.append(chord.Chord)

		if self.hashIntervalFromLastNote:
			self.stateVars["IntervalFromLastNote"] = None

		if self.hashIsAccidental:
			self.validTypes.append(key.KeySignature)
			self.stateVars["KeySignature"] = None

	def setupTupleList(self):
		tupleList = []

		if self.hashPitch:
			tupleList.append("Pitch")
			if self.hashMIDI:
				self.hashingFunctions["Pitch"] = hashMIDIPitch
			elif not self.hashMIDI:
				self.hashingFunctions["Pitch"] = hashNotePitch
				# note to self: look at pitch.py functions
				
			if self.hashIsAccidental:
				tupleList.append("IsAccidental")
				self.hashingFunctions["IsAccidental"] = hashIsAccidental


		if self.hashDuration:
			tupleList.append("Duration")
			if self.roundDuration:
				self.hashingFunctions["Duration"] = hashRoundedDuration
			else:
				self.hashingFunctions["Duration"] = hashDuration

		if self.hashOffset:
			tupleList.append("Offset")
			if self.roundOffset:
				self.hashingFunctions["Offset"] = hashRoundedOffset
			else:
				self.hashingFunctions["Offset"] = hashOffset

		if self.hashIntervalFromLastNote:
			tupleList.append("IntervalFromLastNote")
			self.hashingFunctions["IntervalFromLastNote"] = hashIntervalFromLastNote
		

		self.tupleList = tupleList
		self.tupleClass = collections.namedtuple('NoteHash', tupleList)


	def hashDuration(self, n):
		# if type(n) in self.validTypes:
		return n.duration.quarterLengthFloat

	def hashRoundedDuration(self, n):
		return _getApproxDurOrOffset(n.duration.quarterLengthFloat)


	def preprocessStream(self, s):
		if self.stripTies:
			s = s.stripTies()
		return s
		# TODO: more preprocessing options

	def hash(self, s):
		finalHash = []
		self.setupValidTypesAndStateVars()
		s = self.preprocessStream(s)
		finalEltsToBeHashed = [elt in s if type(elt) in self.validTypes]
		self.setupTupleList()
		
		for n in finalEltsToBeHashed:
			for prop in self.tupleList:
				finalHash.append(self.hashingFunctions[prop](n))

		return finalHash

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

	# def generalHash(self, s):
	# 	"""
	# 	hasher with ability to turn certain parts off/on
	# 	"""
	# 	note_container = []
	# 	stream_notes = s.getElementsByClass(note.GeneralNote)
	# 	for n in stream_notes:
	# 		if n.isNote and self.hashNotes:
	# 			if self.hashDuration:
	# 				if self.roundDuration:
	# 					note_dur = _getApproxDurOrOffset(n.duration.quarterLength)
	# 				else: 
	# 					note_dur = n.duration.quarterLength
	# 			else: note_dur = None

	# 			if self.hashOffset:
	# 				if self.roundOffset:
	# 					note_offset = _getApproxDurOrOffset(n.offset)
	# 				else:
	# 					note_offset = n.offset
	# 			else:
	# 				note_offset = None

	# 			note_container.append(NoteHash(n.pitch.midi, note_dur, note_offset))
	# 		elif n.isChord and self.hashChords:
	# 			for p in n.pitches:
	# 				note_container.append(NoteHash(p.midi, note_dur, note_offset))
	# 		elif n.isRest and self.hashRests: # n is Rest
	# 			note_container.append(NoteHash(None, note_dur, note_offset))

	# 		else:
	# 			print Exception("Not a note, rest, or chord; shouldn't get here!")
	# 	return note_container
			 

	# def basicHash(self):
	# 	"""
	# 	proof of concept, likely incomplete feature

	# 	hashes notes in a stream based on pitch, duration, beat
	# 	pitch: absolute in this sense; maps to midi value between 21 and 108
	# 	duration: length of note 
	# 	beat: offset of each note, relative to the beginning of the stream
	# 	"""	
	# 	note_container = []
	# 	# TODO: perhaps change container to be a deque? ordered dict?
	# 	stream_notes = self.stream.getElementsByClass(note.GeneralNote)
	# 	for n in stream_notes:
	# 		if n.isNote:
	# 			note_container.append(NoteHash(n.pitch.midi, n.duration.quarterLength, n.offset))
	# 		elif n.isChord:
	# 			for p in n.pitches:
	# 				note_container.append(NoteHash(p.midi, n.duration.quarterLength, n.offset))
	# 		else: # n is Rest
	# 			note_container.append(NoteHash(None, n.duration.quarterLength, n.offset))
	# 	return note_container
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
		from music21 import converter
		s1 = converter.parse('../xmlscores/Bologna_596_Nulla_Pitie.xml')
		classList = ['Note', 'Rest']
		for elt in s1.recurse(): # use this to look in order at things instead of flat
			if not elt.isClassOrSubclass(classList): # use this to set up what kind of elements to look at 
				continue
			print elt


if __name__ == "__main__":
    import music21
    music21.mainTest(TestExternal) 
