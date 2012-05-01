# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         vexflow/base.py
# Purpose:      music21 classes for converting music21 objects to vexflow
#
# Authors:      Christopher Reyes
#
# Copyright:    (c) 2012 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

#XXX Note: vexflow is not finalized yet! Functions may change without notice
#XXX While the vexflow class is under construction, please help me keep track
#XXX of dependencies!!
#XXX
#XXX music21/environment
#XXX music21/common.py
#XXX music21/base.py


#TODO: review variable names for consistency
#TODO: use new modular key and duration from note functions in classes
#TODO: make classes inherit from object


'''Objects for transcribing music21 objects as Vex Flow code
'''

import unittest
import music21
from numbers import Number

from music21 import environment
_MOD = 'vexflow.base.py'
environLocal = environment.Environment(_MOD)

#Class variables
global UIDCounter 
UIDCounter = 0L

supportedDisplayModes = ['txt', 'html']

defaultCanvasWidth = 525
defaultCanvasHeight = 120

defaultStaveWidth = 500
defaultStavePosition = (10,0)
defaultStaveClef = 'treble'

defaultMeasureWidth = 500

defaultVoiceNumBeats = 4
defaultVoiceBeatValue = 4

defaultAccidentalDisplayStatus = True 

defaultNoteQuarterLength = 1

vexflowAlterationToAccidental = {
	-2.0: 'bb',
	-1.0: 'b',
	0: 'n',
	1.0: '#',
	2.0: '##'
}

vexflowDurationToTicks = {
	'8': 2048,
	'8d': 3072,
	'8h': 2048,
	'8m': 2048,
	'8r': 2048,
	'16': 1024,
	'16d': 1536,
	'16h': 1024,
	'16m': 1024,
	'16r': 1024,
	'32': 512,
	'32d': 768,
	'32h': 512,
	'32m': 512,
	'32r': 512,
	'64': 256,
	'64d': 384,
	'64h': 256,
	'64m': 256,
	'64r': 256,
	'b': 512,
	'h': 8192,
	'hd': 12288,
	'hh': 8192,
	'hm': 8192,
	'hr': 8192,
	'q': 4096,
	'qd': 6144,
	'qh': 4096,
	'qm': 4096,
	'qr': 4096,
	'w': 16384,
	'wh': 16384,
	'wm': 16384,
	'wr': 16384
}

vexflowQuarterLengthToDuration = {
	0.0625: '64',
	0.09375: '64d',
	0.125: '32',
	0.1875: '32d',
	0.25: '16',
	0.375: '16d',
	0.5: '8',
	0.75: '8d',
	1.0: 'q',
	1.5: 'qd',
	2.0: 'h',
	3.0: 'hd',
	4.0: 'w',
	6.0: 'wd'
}

htmlPreamble = "\n<!DOCTYPE HTML>\n<html>\n<head>\n\t<meta name='author' content=\
'Music21' />\n\t<script src='http://code.jquery.com/jquery-latest.js'></script>\n\
\t<script src='http://www.vexflow.com/vexflow.js'/></script>\n</head>\n<body>\n\t<canvas\
 width=525 height=120 id='music21canvas'></canvas>\n\t<script>\n\t\t$(document)\
.ready(function(){"

vexflowPreamble = "\n\t\t\tvar canvas = $('#music21canvas')[0];\n\t\t\tvar \
renderer = new Vex.Flow.Renderer(canvas, Vex.Flow.Renderer.Backends.CANVAS);\n \
\t\t\tvar ctx = renderer.getContext();"

htmlConclusion = "\t\t});\n\t</script>\n</body>\n</html>"

#-------------------------------------------------------------------------------
#Exception classes

class VexFlowUnsupportedException(music21.Music21Exception):
	'''
	This feature or object cannot yet be transcribed from music21 to Vex Flow
	'''
	pass

#-------------------------------------------------------------------------------
def parse(music21Object, mode='txt'):
	'''
	Parses a music21 object into Vex Flow code
	
	Supported modes: txt
	Supported music21 Objects: 
	'''
	if mode not in supportedDisplayModes:
		raise VexFlowUnsupportedException, 'Unsupported mode: ' + str(mode)
	pass

def fromObject(thisObject, mode='txt'):
	'''
	translates an arbitrary Music21Object into vexflow

	Currently only works for Measures...

	'''
	if 'Note' in thisObject.classes:
		return fromNote(thisObject, mode)
	elif 'Rest' in thisObject.classes:
		return fromRest(thisObject, mode)
	elif 'Chord' in thisObject.classes:
		return fromChord(thisObject, mode)
	elif 'Measure' in thisObject.classes:
		return fromMeasure(thisObject, mode)
	else:
		raise VexFlowUnsupportedException, 'Unsupported object type: ' + str(thisObject)

def fromScore(thisScore, mode='txt'):
	'''
	Parses a music21 score into Vex Flow code
	#TODO
	'''
	if mode not in supportedDisplayModes:
		raise VexFlowUnsupportedException, 'Unsupported mode: ' + str(mode)
	thisScore2 = thisScore.makeNotation()
	raise VexFlowUnsupportedException, 'Cannot display full scores yet'

def fromRest(thisRest, mode='txt'):
	'''
	Parses a music21 rest into Vex Flow code
	'''
	if mode not in supportedDisplayModes:
		raise VexFlowUnsupportedException, 'Unsupported mode: ' + str(mode)
	return VexflowRest(thisRest).generateCode(mode)

def fromNote(thisNote, mode='txt'):
	'''
	Parses a music21 note into Vex Flow code
	'''
	if mode not in supportedDisplayModes:
		raise VexFlowUnsupportedException, 'Unsupported mode: ' + str(mode)
	return VexflowNote(thisNote).generateCode(mode)

def fromChord(thisChord, mode='txt'):
	'''
	Parses a music21 chord into Vex Flow code
	'''
	if mode not in supportedDisplayModes:
		raise VexFlowUnsupportedException, 'Unsupported mode: ' + str(mode)
	return VexflowChord(thisChord).generateCode(mode)


def fromPart(thisPart, mode='txt'):
	'''
	Parses a music21 part into Vex Flow code
	'''
	if mode not in supportedDisplayModes:
		raise VexFlowUnsupportedException, 'Unsupported mode: ' + str(mode)
	raise VexFlowUnsupportedException, 'Cannot display full parts yet'

def fromMeasure(rawMeasure, mode='txt'):
	r'''
	Parses a music21 measure into Vex Flow code

	TODO: Write tests
	TODO: thisMeasure2 = thisMeasure.makeNotation()
	
	>>> from music21 import *
	>>> b = corpus.parse('bwv1.6.mxl')
	>>> m = b.parts[0].measures(0,1)[2]
	>>> d = vexflow.fromMeasure(m)
	>>> print d
	var notes = [new Vex.Flow.StaveNote({keys: ["Gn/4"], duration: "8"}), new Vex.Flow.StaveNote({keys: ["Cn/4"], duration: "8"}), new Vex.Flow.StaveNote({keys: ["Fn/4"], duration: "8"}), new Vex.Flow.StaveNote({keys: ["Fn/3"], duration: "8"}), new Vex.Flow.StaveNote({keys: ["An/3"], duration: "8"}), new Vex.Flow.StaveNote({keys: ["Fn/3"], duration: "8"}), new Vex.Flow.StaveNote({keys: ["An/3"], duration: "8"}), new Vex.Flow.StaveNote({keys: ["Cn/4"], duration: "8"})];

	>>> c = vexflow.fromMeasure(m, 'html')
	>>> print c
	<BLANKLINE>
	<!DOCTYPE HTML>
	<html>
	<head>
		<meta name='author' content='Music21' />
		<script src='http://code.jquery.com/jquery-latest.js'></script>
		<script src='http://www.vexflow.com/vexflow.js'/></script>
	</head>
	<body>
		<canvas width=525 height=120 id='music21canvas'></canvas>
		<script>
			$(document).ready(function(){
				var canvas = $('#music21canvas')[0];
				var renderer = new Vex.Flow.Renderer(canvas, Vex.Flow.Renderer.Backends.CANVAS);
	 			var ctx = renderer.getContext();
				var stave = new Vex.Flow.Stave(10,0,500);
				stave.addClef('treble').setContext(ctx).draw();
				var notes = [
					new Vex.Flow.StaveNote({keys: ["Gn/4"], duration: "8"}),
					new Vex.Flow.StaveNote({keys: ["Cn/4"], duration: "8"}),
					new Vex.Flow.StaveNote({keys: ["Fn/4"], duration: "8"}),
					new Vex.Flow.StaveNote({keys: ["Fn/3"], duration: "8"}),
					new Vex.Flow.StaveNote({keys: ["An/3"], duration: "8"}),
					new Vex.Flow.StaveNote({keys: ["Fn/3"], duration: "8"}),
					new Vex.Flow.StaveNote({keys: ["An/3"], duration: "8"}),
					new Vex.Flow.StaveNote({keys: ["Cn/4"], duration: "8"})
				];
				var voice = new Vex.Flow.Voice({
					num_beats: 4,
					beat_value: 4,
					resolution: Vex.Flow.RESOLUTION
				});
				voice.addTickables(notes);
				var formatter = new Vex.Flow.Formatter().joinVoices([voice]).format([voice], 500);
				voice.draw(ctx, stave);
			});
		</script>
	</body>
	</html>

	>>> assert(c.split('\n')[2] == '<html>') #_DOCS_HIDE
	'''

	if mode not in supportedDisplayModes:
		raise VexFlowUnsupportedException, 'Unsupported mode: ' + str(mode)
	
	thisMeasure = rawMeasure.makeNotation()
	theseNotes = thisMeasure.flat.notes
	numNotes = len(theseNotes)
	if mode == 'txt':
		resultingText = "var notes = ["
		for i in xrange(numNotes):
			thisNote = theseNotes[i]
			thisVexflow = VexflowNote(thisNote)
			resultingText += thisVexflow.generateCode('txt')
			if i < numNotes - 1:
				resultingText += ", "
		resultingText += "];"
		return resultingText

	if mode == 'html':
		resultingText = htmlPreamble + vexflowPreamble + "\n\t\t\tvar stave ="+\
			" new Vex.Flow.Stave(10,0,500);\n\t\t\tstave.addClef('treble')." + \
			"setContext(ctx).draw();"
		resultingText += "\n\t\t\tvar notes = [\n\t\t\t"
		for i in xrange(numNotes):
			thisNote = theseNotes[i]
			thisVexflow = VexflowNote(thisNote)
			resultingText += "\t" + thisVexflow.generateCode('txt')
			if i < numNotes - 1:
				resultingText += ","
			resultingText += "\n\t\t\t"

		#XXX Need to intelligently set the num_beats in the measure. can I get the quarter length of the whole measure?
		numbeats = 4
		beatvalue = 4
		resultingText += "];\n\t\t\tvar voice = new Vex.Flow.Voice({\n\t\t\t" +\
			"\tnum_beats: " + str(numbeats) +\
			",\n\t\t\t\tbeat_value: " + str(beatvalue) + ",\n\t\t\t\tresolution: Vex.Flow.RESO"+\
			"LUTION\n\t\t\t});\n\t\t\tvoice.addTickables(notes);\n\t\t\tv"+\
			"ar formatter = new Vex.Flow.Formatter().joinVoices([voice])."+\
			"format([voice], 500);\n\t\t\tvoice.draw(ctx, stave);\n"
		resultingText += htmlConclusion
		return resultingText

def vexflowKeyFromNote(music21note):
	'''
	Given a music21 Note (or Pitch) object, returns the vexflow 'key'

	TODO: unit tests
	'''
	if 'Pitch' in music21note.classes:
		thisPitch = music21note
	elif 'Note' in music21note.classes:
		thisPitch = music21note.pitch
	elif 'Rest' in music21note.classes:
		thisPitch = pitch.Pitch('B')
		thisPitch.duration = music21note.duration
	else:
		raise TypeError, "Expected music21 Pitch, Note, or Rest. Got: " + \
			str(type(music21note))

	thisPitchName = thisPitch.step
	thisPitchOctave = thisPitch.implicitOctave
	thisKey = thisPitchName + str(thisPitchOctave)
	thisAccidental = thisPitch.accidental
	if thisAccidental != None:
		if thisAccidental.alter in vexflowAlterationToAccidental:
			thisVexflowAccidental =\
				 vexflowAlterationToAccidental[thisAccidental.alter]
		else:
			raise VexFlowUnsupportedException, "VexFlow doesn't support "\
				+ "this accidental type. " + str(thisAccidental.fullName)
	else:
		thisVexflowAccidental = 'n'

	thisVexflowKey = str(thisPitchName) + str(thisVexflowAccidental) + '/' \
		+ str(thisPitchOctave)
	return thisVexflowKey

def vexflowKeyAndAccidentalFromNote(music21note):
	'''
	Given a music21 Note (or Pitch) object, returns the vexflow 'key'

	TODO: unit tests
	'''
	if 'Pitch' in music21note.classes:
		thisPitch = music21note
	elif 'Note' in music21note.classes:
		thisPitch = music21note.pitch
	elif 'Rest' in music21note.classes:
		thisPitch = pitch.Pitch('B')
		thisPitch.duration = music21note.duration
	else:
		raise TypeError, "Expected music21 Pitch, Note, or Rest. Got: " + \
			str(type(music21note))

	thisPitchName = thisPitch.step
	thisPitchOctave = thisPitch.implicitOctave
	thisKey = thisPitchName + str(thisPitchOctave)
	thisAccidental = thisPitch.accidental
	if thisAccidental != None:
		if thisAccidental.alter in vexflowAlterationToAccidental:
			thisVexflowAccidental =\
				 vexflowAlterationToAccidental[thisAccidental.alter]
		else:
			raise VexFlowUnsupportedException, "VexFlow doesn't support "\
				+ "this accidental type. " + str(thisAccidental.fullName)
	else:
		thisVexflowAccidental = 'n'

	thisVexflowKey = str(thisPitchName) + str(thisVexflowAccidental) + '/' \
		+ str(thisPitchOctave)
	return (thisVexflowKey, thisVexflowAccidental)

def vexflowDurationFromNote(music21note):
	'''
	Given a music21 Note (or Pitch) object, returns the vexflow duration

	TODO: unit tests
	'''
	thisQuarterLength = music21note.duration.quarterLength
	if thisQuarterLength in vexflowQuarterLengthToDuration:
		thisVexflowDuration = \
			vexflowQuarterLengthToDuration[thisQuarterLength]
	else:
		raise VexFlowUnsupportedException, "VexFlow doesn't support this "\
			+ "duration. " + str(music21note.duration.fullName)
	return thisVexflowDuration

def vexflowKeyAndDurationFromNote(music21note):
	'''
	Given a music21 Note (or Pitch) object, returns the vexflow key and duration

	TODO: unit tests
	'''
	if 'Pitch' in music21note.classes:
		thisPitch = music21note
	elif 'Note' in music21note.classes:
		thisPitch = music21note.pitch
	elif 'Rest' in music21note.classes:
		thisPitch = pitch.Pitch('B')
		thisPitch.duration = music21note.duration
	else:
		raise TypeError, "Expected music21 Pitch, Note, or Rest. Got: " + \
			str(type(music21note))

	if thisPitch.duration.quarterLength == 0:
		thisPitch.duration.quarterLength = defaultNoteQuarterLength

	thisPitchName = thisPitch.step
	thisPitchOctave = thisPitch.implicitOctave
	thisKey = thisPitchName + str(thisPitchOctave)
	thisAccidental = thisPitch.accidental
	if thisAccidental != None:
		if thisAccidental.alter in vexflowAlterationToAccidental:
			thisVexflowAccidental =\
				 vexflowAlterationToAccidental[thisAccidental.alter]
		else:
			raise VexFlowUnsupportedException, "VexFlow doesn't support "\
				+ "this accidental type. " + str(thisAccidental.fullName)
	else:
		thisVexflowAccidental = 'n'

	thisVexflowKey = str(thisPitchName) + str(thisVexflowAccidental) + '/' \
		+ str(thisPitchOctave)

	thisQuarterLength = thisPitch.duration.quarterLength
	if thisQuarterLength in vexflowQuarterLengthToDuration:
		thisVexflowDuration = \
			vexflowQuarterLengthToDuration[thisQuarterLength]
	else:
		raise VexFlowUnsupportedException, "VexFlow doesn't support this "\
			+ "duration. " + str(thisPitch.duration.fullName)
	return (thisVexflowKey, thisVexflowDuration)

def vexflowKeyAccidentalAndDurationFromNote(music21note):
	'''
	Given a music21 Note (or Pitch) object, returns the vexflow key and duration

	TODO: unit tests
	'''
	if 'Pitch' in music21note.classes:
		thisPitch = music21note
	elif 'Note' in music21note.classes:
		thisPitch = music21note.pitch
		thisPitch.duration = music21note.duration
	elif 'Rest' in music21note.classes:
		thisPitch = pitch.Pitch('B')
		thisPitch.duration = music21note.duration
	else:
		raise TypeError, "Expected music21 Pitch, Note, or Rest. Got: " + \
			str(type(music21note))

	if thisPitch.duration.quarterLength == 0:
		thisPitch.duration.quarterLength = defaultNoteQuarterLength

	thisPitchName = thisPitch.step
	thisPitchOctave = thisPitch.implicitOctave
	thisKey = thisPitchName + str(thisPitchOctave)
	thisAccidental = thisPitch.accidental
	if thisAccidental != None:
		if thisAccidental.alter in vexflowAlterationToAccidental:
			thisVexflowAccidental =\
				 vexflowAlterationToAccidental[thisAccidental.alter]
		else:
			raise VexFlowUnsupportedException, "VexFlow doesn't support "\
				+ "this accidental type. " + str(thisAccidental.fullName)
	else:
		thisVexflowAccidental = 'n'

	thisVexflowKey = str(thisPitchName) + str(thisVexflowAccidental) + '/' \
		+ str(thisPitchOctave)

	thisQuarterLength = thisPitch.duration.quarterLength
	if thisQuarterLength in vexflowQuarterLengthToDuration:
		thisVexflowDuration = \
			vexflowQuarterLengthToDuration[thisQuarterLength]
	else:
		raise VexFlowUnsupportedException, "VexFlow doesn't support this "\
			+ "duration. " + str(thisPitch.duration.fullName)
	return (thisVexflowKey, thisVexflowAccidental, thisVexflowDuration)


#-------------------------------------------------------------------------------
class VexflowNote(object):
	'''
	A VexflowNote object has a .generateCode() method which produces VexFlow 
	code to represent a :class:`music21.note.Note` object.

	TODO: This should probably inherit from music21.music21Object or 
		  note.GeneralNote or something

	TODO: Verify that I'm not overwriting any base attribute names of music21

	TODO: add setters/getters

	TODO: __str__

	>>> from music21 import *
	>>> n = note.Note('C-')
	>>> v = vexflow.VexflowNote(n)
	>>> v.vexflowAccidental
	'b'

	>>> v.vexflowKey
	'Cb/4'

	>>> v.vexflowDuration
	'q'

	>>> v.vexflowCode
	'new Vex.Flow.StaveNote({keys: ["Cb/4"], duration: "q"})'

	>>> n = tinyNotation.TinyNotationNote('c##2.').note
	>>> v = VexflowNote(n)
	>>> v.vexflowAccidental
	'##'

	>>> v.vexflowKey
	'C##/4'

	>>> v.vexflowDuration
	'hd'

	>>> v.vexflowCode
	'new Vex.Flow.StaveNote({keys: ["C##/4"], duration: "hd"})'
	'''

	def __init__(self, music21note):
		'''
		music21note must be a :class:`music21.note.Note` object.
		'''
		self.originalNote = music21note
		self.accidentalDisplayStatus = None
		self._generateVexflowCode()

	def _generateVexflowCode(self):
		'''
		Creates the vexflow code for this note and stores in self.vexflowCode

		access via generateCode()
		'''
		if self.accidentalDisplayStatus == None and self.originalNote.accidental != None and \
			self.originalNote.accidental.displayStatus != None:

			self.accidentalDisplayStatus = \
				self.originalNote.accidental.displayStatus
		elif self.accidentalDisplayStatus == None:
			self.accidentalDisplayStatus = defaultAccidentalDisplayStatus

		#otherwise keep the previous accidentalDisplayStatus

		(self.vexflowKey, self.vexflowAccidental, self.vexflowDuration) = \
			vexflowKeyAccidentalAndDurationFromNote(self.originalNote)

		self.vexflowCode = 'new Vex.Flow.StaveNote({keys: ["'+self.vexflowKey+ \
			'"], duration: "' + self.vexflowDuration + '"})'
		if self.accidentalDisplayStatus:
			self.vexflowCode += '.addAccidental(0, new Vex.Flow.Accidental(' +\
				'"' + self.vexflowAccidental + '"))'

	
	def generateCode(self, mode="txt", cache=True):
		'''
		Returns the VexFlow code in the desired display mode

		Currently supported modes:
			txt: returns the VexFlow code which can be used in conjunction with
				 other VexFlow code
			html: returns standalone HTML code for displaying just this note

		>>> from music21 import *
		>>> n = note.Note('C-')
		>>> v = vexflow.VexflowNote(n)
		>>> v.generateCode('txt')
		'new Vex.Flow.StaveNote({keys: ["Cb/4"], duration: "q"})'

		>>> print v.generateCode('html')
		<BLANKLINE>
		<!DOCTYPE HTML>
		<html>
		<head>
			<meta name='author' content='Music21' />
			<script src='http://code.jquery.com/jquery-latest.js'></script>
			<script src='http://www.vexflow.com/vexflow.js'/></script>
		</head>
		<body>
			<canvas width=525 height=120 id='music21canvas'></canvas>
			<script>
				$(document).ready(function(){
					var canvas = $('#music21canvas')[0];
					var renderer = new Vex.Flow.Renderer(canvas, Vex.Flow.Renderer.Backends.CANVAS);
		 			var ctx = renderer.getContext();
					var stave = new Vex.Flow.Stave(10,0,500);
					stave.addClef('treble').setContext(ctx).draw();
					var notes = [new Vex.Flow.StaveNote({keys: ["Cb/4"], duration: "q"})];
					var voice = new Vex.Flow.Voice({
						num_beats: 1.0,
						beat_value: 4,
						resolution: Vex.Flow.RESOLUTION
					});
					voice.addTickables(notes);
					var formatter = new Vex.Flow.Formatter().joinVoices([voice]).format([voice], 500);
					voice.draw(ctx, stave);
				});
			</script>
		</body>
		</html>
		'''

		if mode not in supportedDisplayModes:
			raise VexFlowUnsupportedException, "VexFlow doesn't support this "\
				+ "display mode yet. " + str(mode)

		if not cache:
			self._generateVexflowCode()

		if mode == 'txt':
			return self.vexflowCode
		elif mode == 'html':
			result = htmlPreamble + vexflowPreamble
			result += "\n\t\t\tvar stave = new Vex.Flow.Stave(" + \
				str(defaultStavePosition[0]) + "," + \
				str(defaultStavePosition[1]) + "," + \
				str(defaultStaveWidth) + ");\n\t\t\tstave.add"+\
				"Clef('" + str(defaultStaveClef) + "').setCon"+\
				"text(ctx).draw();\n\t\t\tvar notes = [" + \
				self.vexflowCode + "];\n\t\t\tvar voice = new"+\
				" Vex.Flow.Voice({\n\t\t\t\tnum_beats: " + \
				str(self.originalNote.duration.quarterLength) +\
				 ",\n\t\t\t\tbeat_value: 4,\n\t\t\t\tresoluti"+\
				"on: Vex.Flow.RESOLUTION\n\t\t\t});\n\t\t\tvo"+\
				"ice.addTickables(notes);\n\t\t\tvar formatte"+\
				"r = new Vex.Flow.Formatter().joinVoices([voi"+\
				"ce]).format([voice], "+str(defaultStaveWidth)+\
				");\n\t\t\tvoice.draw(ctx, stave);\n"
			result += htmlConclusion
			return result

	def show(self, mode='txt'):
		'''
		Displays the Vex Flow javascript for rendering this object
		'''
		if mode not in supportedDisplayModes:
			raise VexFlowUnsupportedException, 'Unsupported display mode:', mode

		if mode == 'txt':
			print self.generateCode('txt')
		elif mode == 'html':
			self.originalNote.show('vexflow')


class VexflowChord(object):
	'''
	A simultaneous grouping of notes

	TODO: Gracefully handle rests in a chord
	TODO: __str__ should just call the str() method on the original notes
	TODO: support music21.chord.Chord as input
			Also store original notes as Chord object
	TODO: write unit tests
	'''

	def __init__(self, notes):
		'''
		notes must be an array_like grouping of either Music21 or VexFlow Notes
		notes can instead be a music21.chord.Chord object
		'''
		try:
			if 'Chord' not in notes.classes:
				raise VexFlowUnsupportedException, 'Cannot create a Chord from'\
					 + str(notes)
			self.originalChord = notes
		except AttributeError:
			if not hasattr(notes, '__contains__'):
				raise TypeError, 'notes must be a chord.Chord object or an ' +\
					'iterable collection of notes'
			assert len(notes) > 0, 'cannot create an empty VexflowChord'
			self.originalChord = chord.Chord(notes)

		self.accidentalDisplayStatus = None
		self._generateVexflowCode()

	def _generateVexflowCode(self):
		#self.notes = []
		self.vexflowDuration = \
			vexflowQuarterLengthToDuration[self.originalChord.duration.quarterLength]
		self.vexflowCode = 'new Vex.Flow.StaveNote({keys: ["'

		thesePitches = self.originalChord.pitches
		theseAccidentals = []

		for index in xrange(len(thesePitches)):
			thisPitch = thesePitches[index]
			(thisKey, thisAccidental) = \
				vexflowKeyAndAccidentalFromNote(thisPitch)
			self.vexflowCode += thisKey + '", "'

			#The following ensures that the accidentalDisplayStatus is set for
			#	each note in the chord
			if self.accidentalDisplayStatus == None and \
				thisPitch.accidental != None and \
				thisPitch.accidental.displayStatus != None:
					self.accidentalDisplayStatus = [None]*len(thesePitches)
					self.accidentalDisplayStatus[index] = \
						thisPitch.accidental.displayStatus
			elif self.accidentalDisplayStatus == None and \
				thisPitch.accidental != None and \
				thisPitch.accidental.displayStatus == None:
					self.accidentalDisplayStatus = [None]*len(thesePitches)
					self.accidentalDisplayStatus[index] = \
						defaultAccidentalDisplayStatus
			elif self.accidentalDisplayStatus == None:
				self.accidentalDisplayStatus = [None]*len(thesePitches)
				self.accidentalDisplayStatus[index] = False
			elif self.accidentalDisplayStatus[index] == None and \
				thisPitch.accidental != None and \
				thisPitch.accidental.displayStatus != None:
					self.accidentalDisplayStatus[index] = \
						thisPitch.accidental.displayStatus
			elif self.accidentalDisplayStatus[index] == None and \
				thisPitch.accidental != None and \
				thisPitch.accidental.displayStatus == None:
					self.accidentalDisplayStatus[index] = \
						defaultAccidentalDisplayStatus

			if self.accidentalDisplayStatus[index]:
				theseAccidentals += ['.addAccidental(' + str(index) + ', new '+\
					'Vex.Flow.Accidental("' + str(thisAccidental) + '"))']

		self.vexflowCode = self.vexflowCode[:-3] + '], duration: "' + \
			self.vexflowDuration + '"})' + ''.join(theseAccidentals)
	
	def generateCode(self, mode='txt'):
		'''
		generates the Vex Flow javascript to render this chord object

		Supported Modes:
		txt: code to represent just this chord
		html: standalone html which can be displayed in a browser
		'''
		if mode not in supportedDisplayModes:
			raise VexFlowUnsupportedException, 'Unsupported display mode:', mode

		if mode == 'txt':
			return self.vexflowCode
		elif mode == 'html':
			result = htmlPreamble + vexflowPreamble
			result += "\n\t\t\tvar stave = new Vex.Flow.Stave(" + \
				str(defaultStavePosition[0]) + "," + \
				str(defaultStavePosition[1]) + "," + \
				str(defaultStaveWidth) + ");\n\t\t\tstave.add"+\
				"Clef('" + str(defaultStaveClef) + "').setCon"+\
				"text(ctx).draw();\n\t\t\tvar notes = [" + \
				self.vexflowCode + "];\n\t\t\tvar voice = new"+\
				" Vex.Flow.Voice({\n\t\t\t\tnum_beats: " + \
				str(self.originalChord.duration.quarterLength) +\
				 ",\n\t\t\t\tbeat_value: 4,\n\t\t\t\tresoluti"+\
				"on: Vex.Flow.RESOLUTION\n\t\t\t});\n\t\t\tvo"+\
				"ice.addTickables(notes);\n\t\t\tvar formatte"+\
				"r = new Vex.Flow.Formatter().joinVoices([voi"+\
				"ce]).format([voice], "+str(defaultStaveWidth)+\
				");\n\t\t\tvoice.draw(ctx, stave);\n"
			result += htmlConclusion
			return result
	
	def show(self, mode='txt'):
		'''
		Displays the Vex Flow javascript for rendering this object
		'''
		if mode not in supportedDisplayModes:
			raise VexFlowUnsupportedException, 'Unsupported display mode:', mode

		if mode == 'txt':
			print self.generateCode('txt')
		else:
			self.originalChord.show('vexflow')

		
class VexflowRest(object):
	'''
	Class for representing rests in Vex Flow

	UNDER CONSTRUCTION:
		The initialization is subject to change soon
	'''
	def __init__(self, music21rest, position='b/4'):
		'''
		music21rest must be a :class:`music21.note.Rest` object.
		position is where the rest should appear on the staff
			'b/4' is the middle of the treble clef
		TODO: figure out a good way to do position

		TODO: Consider calling it self.original instead of originalRest
			Then can use same call on any VexFlow object?
		'''

		self.originalRest = music21rest
		self.vexflowKey = position

		thisQuarterLength = music21rest.duration.quarterLength
		if thisQuarterLength in vexflowQuarterLengthToDuration:
			self.vexflowDuration = \
				str(vexflowQuarterLengthToDuration[thisQuarterLength]) + 'r'
		else:
			raise VexFlowUnsupportedException, "VexFlow doesn't support this "\
				+ "duration. " + str(music21rest.duration.fullName)

		self.vexflowCode = 'new Vex.Flow.StaveNote({keys: ["'+self.vexflowKey+ \
			'"], duration: "' + self.vexflowDuration + '"})'

	def generateCode(self, mode='txt'):
		'''
		generates the Vex Flow javascript to render this rest object

		Supported Modes:
		txt: code to represent just this rest
		html: standalone html which can be displayed in a browser
		'''
		if mode not in supportedDisplayModes:
			raise VexFlowUnsupportedException, 'Unsupported display mode:', mode

		if mode == 'txt':
			return self.vexflowCode
		elif mode == 'html':
			result = htmlPreamble + vexflowPreamble
			result += "\n\t\t\tvar stave = new Vex.Flow.Stave(" + \
				str(defaultStavePosition[0]) + "," + \
				str(defaultStavePosition[1]) + "," + \
				str(defaultStaveWidth) + ");\n\t\t\tstave.add"+\
				"Clef('" + str(defaultStaveClef) + "').setCon"+\
				"text(ctx).draw();\n\t\t\tvar notes = [" + \
				self.vexflowCode + "];\n\t\t\tvar voice = new"+\
				" Vex.Flow.Voice({\n\t\t\t\tnum_beats: " + \
				str(self.originalRest.duration.quarterLength) +\
				 ",\n\t\t\t\tbeat_value: 4,\n\t\t\t\tresoluti"+\
				"on: Vex.Flow.RESOLUTION\n\t\t\t});\n\t\t\tvo"+\
				"ice.addTickables(notes);\n\t\t\tvar formatte"+\
				"r = new Vex.Flow.Formatter().joinVoices([voi"+\
				"ce]).format([voice], "+str(defaultStaveWidth)+\
				");\n\t\t\tvoice.draw(ctx, stave);\n"
			result += htmlConclusion
			return result
	
	def show(self, mode='txt'):
		'''
		Displays the Vex Flow javascript for rendering this object
		'''
		if mode not in supportedDisplayModes:
			raise VexFlowUnsupportedException, 'Unsupported display mode:', mode

		if mode == 'txt':
			print self.generateCode('txt')
		else:
			self.originalRest.show('vexflow')

class VexflowVoice(object):
	'''
	A Voice in Vex Flow is a "lateral" grouping of notes
		It's the equivalent to a :class:`~music21.stream.Part`
	
	TODO: Look into music21 Voices
	'''
	
	def __init__(self, params, music21voice = None):
		'''
		params is a dict containing num_beats, beat_value, and other parameters
			to be passed to the voice object
		'''
		if music21voice != None:
			if 'Voice' not in music21voice.classes:
				pass

		self.UID = UIDCounter
		UIDCounter += 1

		self.params = params

		if not 'num_beats' in self.params:
			self.params['num_beats'] = defaultVoiceNumBeats

		if not 'beat_value' in self.params:
			self.params['beat_value'] = defaultVoiceBeatValue

		self.voiceName = 'music21Voice' + str(self.UID)
		self.voiceCode = 'var ' + self.voiceName + ' = new Vex.Flow.Voice({' +\
			'num_beats: ' + str(self.params['num_beats']) + ', ' + \
			'beat_value: ' + str(self.params['beat_value']) + ', ' + \
			'resolution: Vex.Flow.RESOLUTION});'

		self.notes = []

	def getBeaming(self):
		'''
		Beaming is a boolean value determining if the voice should be beamed

		Note: So far only VexFlow's automatic beaming is supported
			Cannot manually modify beams
		'''
		if 'beaming' not in self.params:
			self.params['beaming'] = False
		return self.params['beaming']
	
	def getNumBeats(self):
		return self.params['num_beats']
	
	def getBeatValue(self):
		return self.params['beat_value']
	
	def getNotes(self):
		return self.notes

	def addNotes(self, notes):
		'''
		appends the notes to the already existing notes
		draws by calling VexFlow's addTickables() method sequentially

		TODO: check that notes is a list of VexflowNotes
		TODO: if not, then convert
		'''
		self.notes += [notes]
	
	def setNotes(self, notes):
		'''
		Replaces self.notes with notes.

		USE WITH CARE! Previous notes will be lost!
		'''
		self.notes = notes

	def setBeaming(self, beaming):
		'''
		Beaming is a boolean value determining if the voice should be beamed

		Note: So far only VexFlow's automatic beaming is supported
			Cannot manually modify beams
		'''
		self.params['beaming'] = beaming

	def generateCode(self, mode='txt'):
		#TODO
		pass
			

class VexflowStave(object):
	'''
	A Stave in Vex Flow is the object for the graphic staff to be displayed
	
	NOTE: Because of the way Vexflow is set up, each measure is contained
		in it's own stave

	TODO: write accessors/modifiers
	TODO: unit tests
	TODO: generate code and show
		generateCode should take a VexflowContext object as a param
	'''
	
	def __init__(self, params):
		'''
		params is a dictionary containing position, width, and other parameters
			to be passed to the stave object
		'''
		self.UID = UIDCounter
		UIDCounter += 1
		self.params = params
		if 'width' not in self.params:
			self.params['width'] = defaultStaveWidth
		if 'position' not in self.params:
			self.params['position'] = defaultStavePosition

		#if context == None:
		#	self.context = vexflow.VexflowContext()
		#else:
		#	if not isinstance(context, vexflow.VexflowContext):
		#		raise VexFlowUnsupportedException, 'Context must be a ' +\
		#			'VexflowContext object, not ' + type(context)
		#	self.context = context

		if 'name' in self.params:
			self.staveName = self.params['name']
		else:
			self.staveName = 'music21Stave' + str(self.UID)

		self.staveCode = 'var ' + self.staveName + ' = new Vex.Flow.STave(' +\
			str(self.params['position'][0])+','+str(self.params['position'][1])\
			+ ',' + str(self.params['width']) + ');'
		
		if 'clef' not in self.params:
			self.params['clef'] = defaultStaveClef
	
	def getWidth(self):
		return self.params['width']

	def getPosition(self):
		'''
		(x,y) position in relation to the top left corner of the canvas
		'''
		return self.params['position']

	def getParam(self, param):
		'''
		Attempts to retrieve an arbitray parameter

		If no such parameter exists, returns None
		'''
		if param in self.params:
			return param
		else:
			return None

	def getClef(self):
		return self.params['clef']

	def generateCode(self, mode='txt'):
		#TODO
		pass

class VexflowContext(object):
	'''
	Contains information about the canvas, formatter, and renderer
	'''

	def __init__(self, params, canvasName = None):
		'''
		canvasName is the name of the canvas within the html code
		params is a dictionary containing width, height, and other parameters
			to be passed to the canvas object
		'''
		self.UID = UIDCounter
		UIDCounter += 1
		self.params = params
		if canvasName == None:
			#XXX Is this sufficient? Should I instead use a random string/hash?
			self.canvasHTMLName = "music21Canvas" + str(self.UID)
		else:
			self.canvasHTMLName = str(canvasName)

		self.canvasJSName = self.canvasHTMLName + 'JS'

		if 'width' not in self.params:
			self.params['width'] = defaultCanvasWidth
		if 'height' not in self.params:
			self.params['height'] = defaultCanvasHeight

	def generateHTML(self, applyAttributes=False):
		'''
		Generates the HTML for the canvas and stores it in self.canvasHTML

		(End users should use the getCanvasHTML() method)

		If applyAttributes is True, then apply the attributes in the
			HTML code instead of in the Javascript

		Note: There is no checking that the values aren't also set
			in Javascript
		'''

		self.canvasHTML = '<canvas '

		if applyAttributes:
			for (parameter, value) in params.items():
				if not isinstance(value, Number) and not value.isdigit():
					value = '"' + str(value) + '"'
				self.canvasHTML += str(parameter) + '=' + str(value) + ' '

		self.canvasHTML += 'id="' + self.canvasHTMLName + '"></canvas>'

	def generateJS(self, applyAttributes=True):
		'''
		Generates the Javascript to set up the canvas for VexFlow and stores it
			in self.canvasJSCode, self.rendererCode, and self.contextCode

		(End users should use the get methods)

		If applyAttributes is True, then apply the attributes in the Javascript
			instead of the HTML.

		Note: applying the attributes in Javascript will overwrite any 
			attributes set in the HTML
		'''
		
		self.canvasJSCode = 'var ' + self.canvasJSName + ' = $("#' + \
			self.canvasHTMLName + '")[0];'
		
		self.rendererName = 'music21Renderer' + str(self.UID)
		self.rendererCode = 'var ' + self.rendererName + ' = new Vex.Flow.' + \
			'Renderer(' + self.canvasJSName + ', Vex.Flow.Renderer.Backends.' +\
			'CANVAS);'
		
		self.contextName = 'music21Context' + str(self.UID)
		self.contextCode = 'var ' + self.contextName+ ' = '+self.rendererName +\
			'.getContext();'
	
	def getCanvasHTMLName(self):
		return self.canvasHTMLName
	
	def getHeight(self):
		return self.params['height']

	def getWidth(self):
		return self.params['width']
	
	def getCanvasHTML(self, cache=True, applyAttributes=False):
		if not cache or not self.canvasHTML:
			self.generateHTML(applyAttributes=applyAttributes)

		return self.canvasHTML
	
	def getCanvasJSName(self):
		return self.canvasJSName
	
	def getRendererName(self):
		return self.rendererName

	def getContextName(self):
		return self.contextName
	
	def getJSCode(self, indentation=1, cache=True, applyAttributes=True):
		if not cache or not self.canvasJSCode or not self.rendererCode or not self.contextCode:
			self.generateJS(applyAttributes=applyAttributes)

		jsCode = self.canvasJSCode + '\n' + ('\t' * indentation)
		jsCode += self.rendererCode + '\n' + ('\t' * indentation)
		jsCode += self.contextCode + '\n' + ('\t' * indentation)
		return jsCode

	def setHeight(self, height):
		self.params['height'] = height

	def setWidth(self, width):
		self.params['width'] = width

#-------------------------------------------------------------------------------
#TODO Here go Tests
class Test(unittest.TestCase):
    
    def runTest(self):
        pass

class TestExternal(unittest.TestCase):
	def runTest(self):
		pass

	def testShowMeasureWithAccidentals(self):
		'''
		TODO: How does this class work?
		'''
		#from music21 import *
		#a = tinyNotation.TinyNotationStream('g--4 g- g# g##')
		#b = stream.Measure(a)
		#b.show('vexflow')
    
#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = []


if __name__ == "__main__":
    # sys.arg test options will be used in mainTest()
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof




