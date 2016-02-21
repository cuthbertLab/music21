# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         scoreDiff.py
# Purpose:      NAME
#
# Authors:      Emily Zhang
#               Evan Lynch
#
# Copyright:    Copyright © 2009-2015 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
Various tools and utilities to find correlations between disparate objects in a Stream.

See the chapter :ref:`overviewFormats` for more information and examples of 
converting formats into and out of music21.
'''
from __future__ import print_function

"""
modification/redo of the algorithm used in variant.py

Hash measures based on pitch, use levenshtein distance to figure out "closest" measure

"""

class Variant(object):

	def __init__(self, streamX, streamY):
		self.streamX = streamX
		self.streamY = streamY
		self.variant = None
		self.naiveVariant = None

	def runStreamAnalyses(self):
		classesX = self.streamX.classes
		if "Score" in classesX:
			pass
		elif "Part" in classesX or len(self.streamX.getElementsByClass("Measure")) > 0:
			pass
		elif len(self.streamX.notesAndRests) > 0 and self.streamX.duration.quarterLength == self.streamY.duration.quarterLength:
			pass
		else:
			raise Exception("Could not determine what merging method to use. Try using a more specific merging function.")

	def createVariantsNaive(self):
		"""
		parts from Evan's original variant.py
		doesn't use difference metric
		self.naiveVariant = output
		"""
		pass

	def createVariants(self, recurse = True):
		"""
		- split self.streamX into its components, based on runStreamAnalyses
		- hash measures of each part
		- run each part through metric, perhaps recursively 
		- self.Variant = output
		"""
		pass
		# encoded_part = []
		# for part in Variant:
		# 	for measure in part:
		#		encoded_part += hashMeasure(measure)
		#


	def hashMeasure(self, measure):
		"""
		note-based hash of a measure
		possibly timed-based in future as well?
		"""
		pass

	def getMostLikelyOperations(self):

		pass

	def getLevenshteinDist(self, streamhash1, streamhash2):
		"""
		helper method for computing edit distances between two measures(?) 
		(poassibly bigger streams)
		for the dp min edit distance finder of two strea,s

		"""
		# D(streamhash1[i], 0) = streamhash1[i].toNumber
		
		pass

	def getMostLikelyOperation(self, stream1, stream2):
		"""
		returns the most likely operation that happened to a certain stream in the context of the other stream
		"""
		pass
