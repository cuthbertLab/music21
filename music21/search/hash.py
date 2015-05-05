# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         hash.py
# Purpose:      Hash musical notation
#
# Authors:      Emily Zhang
#
# Copyright:    Copyright © 2015 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------

import unittest

import copy
import collections
import difflib
import sys

from music21 import base
from music21 import common
from music21 import environment
from music21 import exceptions21
from music21 import note, chord
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
		self.hashOctave = False
		self.hashDuration = True
		self.roundDuration = False
		self.hashOffset = True
		self.roundOffset = True
		self.granularity = 32
		self.hashIntervalFromLastNote = False
		self.hashIsAccidental = False
		self.hashIsTied = False

		self.hashChordsAsNotes = True
		self.hashChordsAsChords = False # hashes information about chords instead of its note components
		self.hashNormalFormString = False
		self.hashOrderedPitchClassesString = False
		# --- end note properties to hash ---

		self.tupleList = []
		self.validTypes = []
		self.stateVars = {} # keeps track of last note, key sig
		self.hashingFunctions = {}

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

		# -- Begin Individual Hashing Functions ---
	def _hashDuration(self, e, c=None):
		return e.duration.quarterLengthFloat

	def _hashRoundedDuration(self, e, c=None):
		return self._getApproxDurOrOffset(n.duration.quarterLengthFloat)

	def _hashMIDIPitchName(self, e, c=None):
		if type(e) == chord.Chord and self.hashChordsAsChords:
			return None
		elif type(e) == note.Rest:
			return None
		return e.pitch.midi

	def _hashPitchName(self, e, c=None):
		if type(e) == chord.Chord and self.hashChordsAsChords:
			return None
		elif type(e) == note.Rest:
			return None
		return str(e.pitch)

	def _hashOctave(self, e, c=None):
		if type(e) == chord.Chord and self.hashChordsAsChords:
			return None
		elif type(e) == note.Rest:
			return None
		return _convertPsToOct(e.pitch.midi)

	def _hashIsAccidental(self, e, c=None):
		pass

	def _hashRoundedOffset(self, e, c=None):
		if c:
			return self._getApproxDurOrOffset(c.offset)
		return self._getApproxDurOrOffset(e.offset)

	def _hashOffset(self, e, c=None):
		if c:
			return self._getApproxDurOrOffset(e.offset)
		return e.offset.quarterLengthFloat

	def _hashIntervalFromLastNote(self, e, c=None):
		if type(e) == chord.Chord and self.hashChordsAsChords:
			return None
		elif type(e) == note.Rest:
			return None
		return interval.Interval(e.previous('Note'), e)

	def _hashOrderedPitchClassesString(self, e, c=None):
		return c.orderedPitchClassesString

	def _hashChordNormalFormString(self, e, c=None):
		return c.normalFormString

	# --- End Indivdual Hashing Functions

	def setupTupleList(self):
		tupleList = []

		if self.hashPitch:
			tupleList.append("Pitch")
			if self.hashMIDI:
				self.hashingFunctions["Pitch"] = self._hashMIDIPitchName
			elif not self.hashMIDI:
				self.hashingFunctions["Pitch"] = self._hashPitchName
				
			if self.hashIsAccidental:
				tupleList.append("IsAccidental")
				self.hashingFunctions["IsAccidental"] = self._hashIsAccidental

		if self.hashOctave:
			tupleList.append("Octave")
			self.hashingFunctions["Octave"] = self._hashOctave

		if self.hashChords:
			if self.hashChordsAsNotes:
				pass
			elif self.hashChordsAsChords:
				if self.hashNormalFormString:
					tupleList.append("ChordNormalFormString")
					self.hashingFunctions["ChordNormalFormString"] = self._hashChordNormalFormString
				if self.hashOrderedPitchClassesString:
					tupleList.append("OrderedPitchClassesString")
					self.hashingFunctions["OrderedPitchClassesString"] = self._hashOrderedPitchClassesString


		if self.hashDuration:
			tupleList.append("Duration")
			if self.roundDuration:
				self.hashingFunctions["Duration"] = self._hashRoundedDuration
			else:
				self.hashingFunctions["Duration"] = self._hashDuration

		if self.hashOffset:
			tupleList.append("Offset")
			if self.roundOffset:
				self.hashingFunctions["Offset"] = self._hashRoundedOffset
			else:
				self.hashingFunctions["Offset"] = self._hashOffset

		if self.hashIntervalFromLastNote:
			tupleList.append("IntervalFromLastNote")
			self.hashingFunctions["IntervalFromLastNote"] = hashIntervalFromLastNote
		

		self.tupleList = tupleList
		self.tupleClass = collections.namedtuple('NoteHash', tupleList)


	def preprocessStream(self, s):
		if self.stripTies:
			s = s.stripTies()
		return s
		# TODO: more preprocessing options??

	def hash(self, s):
		finalHash = []
		self.setupValidTypesAndStateVars()
		s = self.preprocessStream(s)
		finalEltsToBeHashed = [elt for elt in s if type(elt) in self.validTypes]
		self.setupTupleList()
		
		for elt in finalEltsToBeHashed:
			# single_note_hash = []
			if self.hashIsAccidental and type(elt) == key.KeySignature:
				self.stateVars["currKeySig"] = elt
			elif type(elt) == chord.Chord:
				if self.hashChordsAsNotes:
					for n in elt:
						single_note_hash = [self.hashingFunctions[prop](n, c=elt) for prop in self.tupleList]		
						finalHash.append(self.tupleClass._make(single_note_hash))
				elif self.hashChordsAsChords:
					single_note_hash = [self.hashingFunctions[prop](elt) for prop in self.tupleList]
					finalHash.append(self.tupleClass._make(single_note_hash))
			else: #type(elt) == note.Note or type(elt) == note.Rest
				single_note_hash = [self.hashingFunctions[prop](elt) for prop in self.tupleList]
				finalHash.append(self.tupleClass._make(single_note_hash))
		return finalHash

	# --- Begin Rounding Helper Functions ---
	# def maprange(self, num, originalRange, rangeToMapTo = (-sys.maxint - 1, sys.maxint)):
	# 	(or1, or2), (mtr1, mtr2) = originalRange, rangeToMapTo
	# 	return  b1 + ((s - a1) * (mtr2 - mtr1) / (a2 - a1))

	def _getApproxDurOrOffset(self, durOrOffset):
		return round(durOrOffset*self.granularity)/self.granularity
	

	def _approximatelyEqual(self, a, b, sig_fig = 2):
		"""
		use to look at whether beat lengths are close, within a certain range
		probably can use for other things that are approx. equal
		"""
		return (a==b or int(a*10**sig_fig) == int(b*10**sig_fig))

	# --- End Rounding Helper Functions ---

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
		NoteHash = collections.namedtuple('NoteHash', ["Pitch", "Duration", "Offset"])
		hashes_in_format = [NoteHash(Pitch=x, Duration=y, Offset=z) for (x, y, z) in hashes_plain_numbers]
		self.assertEqual(h.hash(s1), hashes_in_format)
		# print h.hash(s1)

class TestExternal(unittest.TestCase):
	def runTest(self):
		pass

	def testBasicHash(self):
		from music21 import converter
		s1 = converter.parse('../xmlscores/Bologna_596_Nulla_Pitie.xml')
		h = Hasher()
		print h.hash(s1.recurse())
		# classList = ['Note', 'Rest']
		# for elt in s1.recurse(): # use this to look in order at things instead of flat
		# 	if not elt.isClassOrSubclass(classList): # use this to set up what kind of elements to look at 
		# 		continue
		# 	print elt


if __name__ == "__main__":
    import music21
    music21.mainTest(TestExternal) 
