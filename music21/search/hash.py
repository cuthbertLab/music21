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

	def basicHash(self, stream):

		"""
		proof of concept, likely incomplete feature

		hashes notes in a stream based on pitch, duration, beat
		pitch: absolute in this sense; maps to midi value between 21 and 108
		duration: length of note 
		beat: offset of each note, relative to the beginning of the stream

		leaves out rests for now
		"""
		note_hash = collections.namedtuple('NoteHash', ['pitch', 'duration', 'beat'])
		note_container = []
		# TODO: perhaps change container to be a deque? ordered dict?
		stream_notes = s.getElementsByClass(note.Note)
		for note in stream_notes:
			note_container.append(NoteHash(note.pitch.midi, note.duration.quarterLength, note.offset))
		return note_container
