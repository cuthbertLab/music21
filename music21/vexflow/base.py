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
	Here's the heirarchy:
	A VexflowContext can be used to display multiple VexflowParts.
	Each VexflowPart contains multiple VexflowStaves (one for each measure)
	Each VexflowStave might contain multilpe VexflowVoices
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

defaultCanvasWidth = '($(window).width()-10)'
defaultCanvasHeight = '$(window).height()'
defaultCanvasMargin = 10

defaultStaveWidth = 500
defaultStaveHeight = 90 #Derived from the vexflow.stave.JS file
defaultStavePosition = (10,0)
defaultStaveClef = 'treble'
defaultStaveKeySignature = 'C'

defaultInterSystemMargin = 60
defaultIntraSystemMargin = 20

defaultMeasureWidth = 500
defaultMeasuresPerStave = 4
defaultMeasureMargin = 50

defaultVoiceNumBeats = 4
defaultVoiceBeatValue = 4

defaultBeamingStatus = True #Just until it's working properly

defaultAccidentalDisplayStatus = False
defaultClefDisplayStatus = False
defaultKeySignatureDisplayStatus = False

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

vexflowSharpsToKeySignatures = {
	-7: 'Cb',
	-6: 'Gb',
	-5: 'Db',
	-4: 'Ab',
	-3: 'Eb',
	-2: 'Bb',
	-1: 'F',
	0: 'C',
	1: 'G',
	2: 'D',
	3: 'A',
	4: 'E',
	5: 'B',
	6: 'F#',
	7: 'C#'
}

#XXX: Delete this before committing!
vexflowLocalCopy = '<script src="http://localhost/uap/raffazizzi-vexflow-d8660e5/src/header.js">\
\n</script><script src="http://localhost/uap/raffazizzi-vexflow-d8660e5/src/vex.js"></script>\
\n<script src="http://localhost/uap/raffazizzi-vexflow-d8660e5/src/flow.js"></script>\
\n<script src="http://localhost/uap/raffazizzi-vexflow-d8660e5/src/tables.js"></script>\n\
<script src="http://localhost/uap/raffazizzi-vexflow-d8660e5/src/fonts/vexflow_font.js"></script>\
\n<script src="http://localhost/uap/raffazizzi-vexflow-d8660e5/src/glyph.js"></script>\
\n<script src="http://localhost/uap/raffazizzi-vexflow-d8660e5/src/stave.js"></script>\
\n<script src="http://localhost/uap/raffazizzi-vexflow-d8660e5/src/staveconnector.js"></script>\
\n<script src="http://localhost/uap/raffazizzi-vexflow-d8660e5/src/tabstave.js"></script>\
\n<script src="http://localhost/uap/raffazizzi-vexflow-d8660e5/src/tickcontext.js"></script>\
\n<script src="http://localhost/uap/raffazizzi-vexflow-d8660e5/src/tickable.js"></script>\
\n<script src="http://localhost/uap/raffazizzi-vexflow-d8660e5/src/note.js"></script>\
\n<script src="http://localhost/uap/raffazizzi-vexflow-d8660e5/src/barnote.js"></script>\
\n<script src="http://localhost/uap/raffazizzi-vexflow-d8660e5/src/ghostnote.js"></script>\
\n<script src="http://localhost/uap/raffazizzi-vexflow-d8660e5/src/stavenote.js"></script>\
\n<script src="http://localhost/uap/raffazizzi-vexflow-d8660e5/src/tabnote.js"></script>\
\n<script src="http://localhost/uap/raffazizzi-vexflow-d8660e5/src/beam.js"></script>\
\n<script src="http://localhost/uap/raffazizzi-vexflow-d8660e5/src/voice.js"></script>\
\n<script src="http://localhost/uap/raffazizzi-vexflow-d8660e5/src/voicegroup.js"></script>\
\n<script src="http://localhost/uap/raffazizzi-vexflow-d8660e5/src/modifier.js"></script>\
\n<script src="http://localhost/uap/raffazizzi-vexflow-d8660e5/src/modifiercontext.js"></script>\
\n<script src="http://localhost/uap/raffazizzi-vexflow-d8660e5/src/accidental.js"></script>\
\n<script src="http://localhost/uap/raffazizzi-vexflow-d8660e5/src/dot.js"></script>\
\n<script src="http://localhost/uap/raffazizzi-vexflow-d8660e5/src/formatter.js"></script>\
\n<script src="http://localhost/uap/raffazizzi-vexflow-d8660e5/src/stavetie.js"></script>\
\n<script src="http://localhost/uap/raffazizzi-vexflow-d8660e5/src/tabtie.js"></script>\
\n<script src="http://localhost/uap/raffazizzi-vexflow-d8660e5/src/tabslide.js"></script>\
\n<script src="http://localhost/uap/raffazizzi-vexflow-d8660e5/src/bend.js"></script>\
\n<script src="http://localhost/uap/raffazizzi-vexflow-d8660e5/src/vibrato.js"></script>\
\n<script src="http://localhost/uap/raffazizzi-vexflow-d8660e5/src/annotation.js"></script>\
\n<script src="http://localhost/uap/raffazizzi-vexflow-d8660e5/src/articulation.js"></script>\
\n<script src="http://localhost/uap/raffazizzi-vexflow-d8660e5/src/tuning.js"></script>\
\n<script src="http://localhost/uap/raffazizzi-vexflow-d8660e5/src/stavemodifier.js"></script>\
\n<script src="http://localhost/uap/raffazizzi-vexflow-d8660e5/src/keysignature.js"></script>\
\n<script src="http://localhost/uap/raffazizzi-vexflow-d8660e5/src/timesignature.js"></script>\
\n<script src="http://localhost/uap/raffazizzi-vexflow-d8660e5/src/clef.js"></script>\
\n<script src="http://localhost/uap/raffazizzi-vexflow-d8660e5/src/music.js"></script>\
\n<script src="http://localhost/uap/raffazizzi-vexflow-d8660e5/src/keymanager.js"></script>\
\n<script src="http://localhost/uap/raffazizzi-vexflow-d8660e5/src/renderer.js"></script>\
\n<script src="http://localhost/uap/raffazizzi-vexflow-d8660e5/src/raphaelcontext.js"></script>\
\n<script src="http://localhost/uap/raffazizzi-vexflow-d8660e5/src/stavevolta.js"></script>\
\n<script src="http://localhost/uap/raffazizzi-vexflow-d8660e5/src/staverepetition.js"></script>\
\n<script src="http://localhost/uap/raffazizzi-vexflow-d8660e5/src/stavebarline.js"></script>\
\n<script src="http://localhost/uap/raffazizzi-vexflow-d8660e5/src/stavesection.js"></script>\
\n<script src="http://localhost/uap/raffazizzi-vexflow-d8660e5/src/stavehairpin.js"></script>\
\n<script src="http://localhost/uap/raffazizzi-vexflow-d8660e5/src/tuplet.js"></script>'

vexflowGlobalCopy = "<script src='http://www.vexflow.com/vexflow.js'/></script>"

htmlPreamble = "\n<!DOCTYPE HTML>\n<html>\n<head>\n\t<meta name='author' content=\
'Music21' />\n\t<script src='http://code.jquery.com/jquery-latest.js'></script>\n\
\t" + vexflowGlobalCopy + "\n</head>\n<body>\n\t<canvas\
 width=525 height=120 id='music21canvas'></canvas>\n\t<script>\n\t\t$(document)\
.ready(function(){"

htmlCanvasPreamble= "\n<!DOCTYPE HTML>\n<html>\n<head>\n\t<meta name='author' content=\
'Music21' />\n\t<script src='http://code.jquery.com/jquery-latest.js'></script>\n\
\t" + vexflowGlobalCopy + "\n</head>\n<body>\n\t"

htmlCanvasPostamble="<script>\n\t\t$(document)\
.ready(function(){"

vexflowPreamble = "\n\t\t\tvar canvas = $('#music21canvas')[0];\n\t\t\tvar \
renderer = new Vex.Flow.Renderer(canvas, Vex.Flow.Renderer.Backends.CANVAS);\n \
\t\t\tvar ctx = renderer.getContext();"

htmlConclusion = "\n\t\t});\n\t</script>\n</body>\n</html>"

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
	elif 'Part' in thisObject.classes:
		return fromPart(thisObject, mode)
	elif 'Score' in thisObject.classes:
		return fromScore(thisObject, mode)
	elif 'Stream' in thisObject.classes:
		return fromStream(thisObject, mode)
	else:
		raise VexFlowUnsupportedException, 'Unsupported object type: ' + str(thisObject)

def fromScore(thisScore, mode='txt'):
	'''
	Parses a music21 score into Vex Flow code
	#TODO

	Here's the game plan:
		Create a VexflowPart for each part
			Each VexflowPart creates VexflowStaves
		Create a VexflowContext to house all of the parts
	'''
	if mode not in supportedDisplayModes:
		raise VexFlowUnsupportedException, 'Unsupported mode: ' + str(mode)

	return VexflowScore(thisScore.makeNotation(inPlace=False)).generateCode(mode)

def fromStream(thisStream, mode='txt'):
	'''
	Parses a music21 stream into Vex Flow code

	Checks if it has parts. If so, parses like a Score.
	Otherwise, just flattens it and parses it like a Part
	'''
	if mode not in supportedDisplayModes:
		raise VexFlowUnsupportedException, 'Unsupported mode: ' + str(mode)

	theseParts = thisStream.getElementsByClass('Part')
	if len(theseParts) == 0:
		return VexflowPart(music21.stream.Part(thisStream.flat).makeNotation(inPlace=False)).generateCode(mode)
	return VexflowScore(music21.stream.Score(thisStream).makeNotation(inPlace=False)).generateCode(mode)

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
	return VexflowPart(thisPart.makeNotation(inPlace=False)).generateCode(mode)

def fromMeasure(thisMeasure, mode='txt'):
	r'''
	Parses a music21 measure into Vex Flow code

	TODO: Fix tests
	TODO: thisMeasure2 = thisMeasure.makeNotation()
	
	>>> from music21 import *
	>>> b = corpus.parse('bwv1.6.mxl')
	>>> m = b.parts[0].measures(0,1)[2]
	>>> d = vexflow.fromMeasure(m)
	>>> print d
	var music21Voice0 = new Vex.Flow.Voice({num_beats: 4.0, beat_value: 4, resolution: Vex.Flow.RESOLUTION});
	var music21Voice0Notes = [new Vex.Flow.StaveNote({keys: ["Gn/4"], duration: "8", stem_direction: Vex.Flow.StaveNote.STEM_UP}), new Vex.Flow.StaveNote({keys: ["Cn/4"], duration: "8", stem_direction: Vex.Flow.StaveNote.STEM_UP}), new Vex.Flow.StaveNote({keys: ["Fn/4"], duration: "8", stem_direction: Vex.Flow.StaveNote.STEM_UP}), new Vex.Flow.StaveNote({keys: ["Fn/3"], duration: "8", stem_direction: Vex.Flow.StaveNote.STEM_UP}), new Vex.Flow.StaveNote({keys: ["An/3"], duration: "8", stem_direction: Vex.Flow.StaveNote.STEM_UP}), new Vex.Flow.StaveNote({keys: ["Fn/3"], duration: "8", stem_direction: Vex.Flow.StaveNote.STEM_UP}), new Vex.Flow.StaveNote({keys: ["An/3"], duration: "8", stem_direction: Vex.Flow.StaveNote.STEM_UP}), new Vex.Flow.StaveNote({keys: ["Cn/4"], duration: "8", stem_direction: Vex.Flow.StaveNote.STEM_UP})];
	music21Voice0.addTickables(music21Voice0Notes);

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
				var music21Voice0 = new Vex.Flow.Voice({num_beats: 4.0, beat_value: 4, resolution: Vex.Flow.RESOLUTION});
	var music21Voice0Notes = [new Vex.Flow.StaveNote({keys: ["Gn/4"], duration: "8", stem_direction: Vex.Flow.StaveNote.STEM_UP}), new Vex.Flow.StaveNote({keys: ["Cn/4"], duration: "8", stem_direction: Vex.Flow.StaveNote.STEM_UP}), new Vex.Flow.StaveNote({keys: ["Fn/4"], duration: "8", stem_direction: Vex.Flow.StaveNote.STEM_UP}), new Vex.Flow.StaveNote({keys: ["Fn/3"], duration: "8", stem_direction: Vex.Flow.StaveNote.STEM_UP}), new Vex.Flow.StaveNote({keys: ["An/3"], duration: "8", stem_direction: Vex.Flow.StaveNote.STEM_UP}), new Vex.Flow.StaveNote({keys: ["Fn/3"], duration: "8", stem_direction: Vex.Flow.StaveNote.STEM_UP}), new Vex.Flow.StaveNote({keys: ["An/3"], duration: "8", stem_direction: Vex.Flow.StaveNote.STEM_UP}), new Vex.Flow.StaveNote({keys: ["Cn/4"], duration: "8", stem_direction: Vex.Flow.StaveNote.STEM_UP})];
	music21Voice0.addTickables(music21Voice0Notes);
				var formatter = new Vex.Flow.Formatter().joinVoices([music21Voice0]).format([music21Voice0], 500);
				music21Voice0.draw(ctx, stave);
			});
		</script>
	</body>
	</html>

	>>> assert(c.split('\n')[2] == '<html>') #_DOCS_HIDE
	'''

	if mode not in supportedDisplayModes:
		raise VexFlowUnsupportedException, 'Unsupported mode: ' + str(mode)
	
	return VexflowVoice(thisMeasure.makeNotation(inPlace=False)).generateCode(mode)

def vexflowClefFromClef(music21clef, params={}):
	'''
	Given a music21 clef object, returns the vexflow clef
	'''
	if 'TenorClef' in music21clef.classes:
		return 'tenor'
	elif 'BassClef' in music21clef.classes or 'Treble8vbClef' \
		in music21clef.classes:
		return 'bass'
	elif 'AltoClef' in music21clef.classes:
		return 'alto'
	elif 'PercussionClef' in music21clef.classes:
		return 'percussion'
	elif 'TrebleClef' in music21clef.classes or 'GClef' \
		in music21clef.classes:
		return 'treble'
	else:
		raise VexFlowUnsupportedException, 'Vexflow only supports the ' +\
			'following clefs: treble, bass, alto, tenor, percussion. ' +\
			'Cannot parse ', music21clef


def vexflowKeyFromNote(music21note, params={}):
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

	thisAccidental = thisPitch.accidental

	if 'clef' in params and params['clef'] == 'bass':
		#Vexflow renders all notes as if on treble clef, regardless of actual
		#	clef
		thisPitch = thisPitch.transpose(12).transpose('m6')


	thisPitchName = thisPitch.step
	thisPitchOctave = thisPitch.implicitOctave

	thisKey = thisPitchName + str(thisPitchOctave)
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

def vexflowKeyAndAccidentalFromNote(music21note, params={}):
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

	thisAccidental = thisPitch.accidental

	if 'clef' in params and params['clef'] == 'bass':
		#Vexflow renders all notes as if on treble clef, regardless of actual
		#	clef
		thisPitch = thisPitch.transpose(12).transpose('m6')

	thisPitchName = thisPitch.step
	thisPitchOctave = thisPitch.implicitOctave
	thisKey = thisPitchName + str(thisPitchOctave)
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

def vexflowDurationFromNote(music21note, params={}):
	'''
	Given a music21 Note (or Pitch) object, returns the vexflow duration

	TODO: unit tests
	TODO tuplet: handle tuplets and propogate that information out
	'''
	thisQuarterLength = music21note.duration.quarterLength
	if thisQuarterLength in vexflowQuarterLengthToDuration:
		thisVexflowDuration = \
			vexflowQuarterLengthToDuration[thisQuarterLength]
	else:
		raise VexFlowUnsupportedException, "VexFlow doesn't support this "\
			+ "duration. " + str(music21note.duration.fullName)
	return thisVexflowDuration

def vexflowKeyAndDurationFromNote(music21note, params={}):
	'''
	Given a music21 Note (or Pitch) object, returns the vexflow key and duration

	TODO: unit tests
	TODO tuplet: handle tuplets and propogate that information out
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

	thisAccidental = thisPitch.accidental

	if 'clef' in params and params['clef'] == 'bass':
		#Vexflow renders all notes as if on treble clef, regardless of actual
		#	clef
		thisPitch = thisPitch.transpose(12).transpose('m6')

	if thisPitch.duration.quarterLength == 0:
		thisPitch.duration.quarterLength = defaultNoteQuarterLength

	thisPitchName = thisPitch.step
	thisPitchOctave = thisPitch.implicitOctave
	thisKey = thisPitchName + str(thisPitchOctave)
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

def vexflowKeyAccidentalAndDurationFromNote(music21note, params={}):
	'''
	Given a music21 Note (or Pitch) object, returns the vexflow key and duration

	TODO: unit tests
	TODO tuplet: handle tuplets and propogate that information out
		Use duration.tuplets[0].tupletActual which gives us:
			(number of notes in tuplet, duration of what each should look like)
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

	thisAccidental = thisPitch.accidental

	if 'clef' in params and params['clef'] == 'bass':
		#Vexflow renders all notes as if on treble clef, regardless of actual
		#	clef
		thisPitch = thisPitch.transpose(12).transpose('m6')

	if thisPitch.duration.quarterLength == 0:
		thisPitch.duration.quarterLength = defaultNoteQuarterLength

	thisPitchName = thisPitch.step
	thisPitchOctave = thisPitch.implicitOctave
	thisKey = thisPitchName + str(thisPitchOctave)
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

	def __init__(self, music21note, params={}):
		'''
		music21note must be a :class:`music21.note.Note` object.
		'''
		self.originalNote = music21note
		self.accidentalDisplayStatus = None
		self.params = params
		#TODO tuplet: add variables for if it's the start of a tuplet
		self.isTuplet = False
		self.tupletLength = 0
		self.vexflowKey = ''
		self.vexflowDuration = ''
		self.vexflowAccidental = ''
		self.stemDirection = ''
		self.beamStart = False
		self.beamStop = False
		self.tieStart = False
		self.tieStop = False
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

		if self.originalNote.stemDirection == u'up':
			self.stemDirection = 'Vex.Flow.StaveNote.STEM_UP'
		elif self.originalNote.stemDirection == u'down':
			self.stemDirection = 'Vex.Flow.StaveNote.STEM_DOWN'

		if self.originalNote.beams and 'start' in self.originalNote.beams.getTypes():
			self.beamStart = True
		elif self.originalNote.beams and 'stop' in self.originalNote.beams.getTypes():
			self.beamStop = True

		if self.originalNote.tie and self.originalNote.tie.type == 'start':
			self.tieStart = True
		elif self.originalNote.tie and self.originalNote.tie.type == 'stop':
			self.tieStop = True


		(self.vexflowKey, self.vexflowAccidental, self.vexflowDuration) = \
			vexflowKeyAccidentalAndDurationFromNote(self.originalNote, params=self.params)

		self.vexflowCode = 'new Vex.Flow.StaveNote({keys: ["'+self.vexflowKey+ \
			'"], duration: "' + self.vexflowDuration + '"'
		if self.stemDirection != '':
			self.vexflowCode += ', stem_direction: ' + self.stemDirection + '})'
		else:
			self.vexflowCode +=  '})'


		if self.accidentalDisplayStatus:
			self.vexflowCode += '.addAccidental(0, new Vex.Flow.Accidental(' +\
				'"' + self.vexflowAccidental + '"))'

		for thisExpression in  self.originalNote.expressions:
			if 'Fermata' in thisExpression.classes:
				#"a@a" = fermata above staff. "a@u" = fermata below staff
				#setPosition(3) means place this fermata above the staff
				#setPosition(4) would put it below the staff
				self.vexflowCode += '.addArticulation(0, new Vex.Flow.Articu'+\
					'lation("a@a").setPosition(3))' 

		try:
			self.vexflowCode += '.addDotToAll()' * self.originalNote.duration.dots
		except:
			print "Couldn't add dots."
			print "Duration:", self.originalNote.duration
			print "Dots:", self.originalNote.duration.dots

	
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

	def __init__(self, notes, params={}):
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
		self.params = params
		#TODO tuplet: add variables for if it's the start of a tuplet
		self.isTuplet = False
		self.tupletLength = 0
		self.stemDirection = ''
		self.beamStart = False
		self.beamStop = False
		self.tieStart = False
		self.tieStop = False
		self._generateVexflowCode()

	def _generateVexflowCode(self):
		'''
		Generates the vexflow code needed to display this chord in a browser
		Note: this is an internal method. Call generateCode(mode='txt') to 
			access the result of this method
		'''
		#self.notes = []
		self.vexflowDuration = \
			vexflowQuarterLengthToDuration[self.originalChord.duration.quarterLength]
		self.vexflowCode = 'new Vex.Flow.StaveNote({keys: ["'

		#TODO tuplet: set the tuplet variables here

		thesePitches = self.originalChord.pitches
		theseAccidentals = []

		if self.originalChord.stemDirection == u'up':
			self.stemDirection = 'Vex.Flow.StaveNote.STEM_UP'
		elif self.originalChord.stemDirection == u'down':
			self.stemDirection = 'Vex.Flow.StaveNote.STEM_DOWN'

		if self.originalChord.tie and self.originalChord.tie.type == 'start':
			self.tieStart = True
		elif self.originalChord.tie and self.originalChord.tie.type == 'stop':
			self.tieStop = True

		if self.originalChord.beams and 'start' in self.originalChord.beams.getTypes():
			self.beamStart = True
		elif self.originalChord.beams and 'stop' in self.originalChord.beams.getTypes():
			self.beamStop = True

		for index in xrange(len(thesePitches)):
			thisPitch = thesePitches[index]
			(thisKey, thisAccidental) = \
				vexflowKeyAndAccidentalFromNote(thisPitch, params=self.params)
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
			self.vexflowDuration + '"'

		if self.stemDirection != '':
			self.vexflowCode += ', stem_direction: ' + self.stemDirection + '})'
		else:
			self.vexflowCode +=  '})'

		for thisExpression in  self.originalChord.expressions:
			if 'Fermata' in thisExpression.classes:
				#"a@a" = fermata above staff. "a@u" = fermata below staff
				#setPosition(3) means place this fermata above the staff
				#setPosition(4) would put it below the staff
				self.vexflowCode += '.addArticulation(0, new Vex.Flow.Articu'+\
					'lation("a@a").setPosition(3))' 

 		self.vexflowCode += ''.join(theseAccidentals)

		try:
			self.vexflowCode += '.addDotToAll()' * self.originalChord.duration.dots
		except:
			print "Couldn't add dots."
			print "Duration:", self.originalChord.duration
			print "Dots:", self.originalChord.duration.dots
	
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
	def __init__(self, music21rest, position='b/4', params={}):
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
		self.params = params
		#TODO tuplet: add variables for if it's the start of a tuplet
		self.isTuplet = False
		self.tupletLength = 0
		self.vexflowCode = ''
		self._generateVexflowCode()

	def _generateVexflowCode(self):
		'''
		Generates the vexflow code needed to render this rest object
		'''
		thisVexflowDuration = vexflowDurationFromNote(self.originalRest, params=self.params) + 'r'

		self.vexflowCode = 'new Vex.Flow.StaveNote({keys: ["'+self.vexflowKey+ \
			'"], duration: "' + thisVexflowDuration + '"})'

		for thisExpression in  self.originalRest.expressions:
			if 'Fermata' in thisExpression.classes:
				#"a@a" = fermata above staff. "a@u" = fermata below staff
				#setPosition(3) means place this fermata above the staff
				#setPosition(4) would put it below the staff
				self.vexflowCode += '.addArticulation(0, new Vex.Flow.Articu'+\
					'lation("a@a").setPosition(3))' 
		try:
			self.vexflowCode += '.addDotToAll()' * self.originalRest.duration.dots
		except:
			print "Couldn't add dots."
			print "Duration:", self.originalRest.duration
			print "Dots:", self.originalRest.duration.dots

	def getPosition(self):
		'''
		Get the position on the staff of the rest
		'''
		return self.vexflowKey

	def setPosition(self, newPosition):
		'''
		Set the position on the staff of the rest

		NOTE: Must be in the same form as a vexflow key:
			"(note name) / (octave number)"
		for example, to center the rest on middle C, use setPosition('c/4')
		'''
		self.vexflowKey = newPosition

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

class VexflowScore(object):
	'''
	Represents the code for multiple VexflowPart objects
	'''

	def __init__(self, music21score, params={}):
		self.originalScore = music21score
		self.notatedScore = self.originalScore.makeNotation(inPlace=False)
		self.originalParts = self.notatedScore.parts
		self.numParts = len(self.originalParts)
		self.vexflowParts = [None] * self.numParts
		self.context = None
		self.params = params
		self.partsCode = ''
		self.vexflowCode = ''

		self._generateVexflowCode()

	def _generateVexflowCode(self):
		'''
		Generates the code necessary to display this score
		'''
		previousParams = {'numParts': self.numParts}
		if self.context != None:
			previousParams['context'] = self.context
			previousParams['canvasWidth'] = self.context.getWidth()

		for index in xrange(self.numParts):
			#make a vexflowPart object
			thisPart = self.originalParts[index]
			previousParams['partIndex'] = index
	
			if self.context != None:
				previousParams['context'] = self.context

			thisVexflowPart = VexflowPart(thisPart, previousParams)
			
			if self.context == None:
				self.context = thisVexflowPart.context

			self.vexflowParts[index] = thisVexflowPart
			previousParams = thisVexflowPart.params

		if self.context == None:
			self.context = previousParams['context']

		self.partsCode = '\n'.join([part.generateCode('txt') for part in self.vexflowParts])
		self.vexflowCode = self.context.getJSCode(indentation=3) + '\n'
		self.vexflowCode += 'var lastProblemNote;\n'
		self.vexflowCode += self.partsCode
	
	def generateCode(self, mode = 'txt'):
		'''
		returns the vexflow code needed to render this object in a browser
		'''
		if mode == 'txt':
			return self.vexflowCode
		elif mode=='html':
			result = htmlCanvasPreamble + str(self.context.getCanvasHTML()) + \
				htmlCanvasPostamble + '\n'
			result += self.vexflowCode + '\n'

			tieCode = ''
			partialTies = []
			
			for thisPart in self.vexflowParts:
				for thisStave in thisPart.staves:
					for thisVoice in thisStave.vexflowVoices:
						(beamPreamble, beamPostamble) = thisVoice.beamCode(self.context.getContextName())
						(thisTieCode, thesePartialTies) = thisVoice.tieCode(self.context.getContextName())
						thesePartialTies = [(thisPartialTie + [thisStave.getLineNum()]) for thisPartialTie in thesePartialTies]
						tieCode += '\n' + thisTieCode
						partialTies += thesePartialTies
						result += beamPreamble
						result += str(thisVoice.voiceName) + '.draw(' + \
						str(self.context.getContextName()) + ', ' + \
						str(thisStave.staveName) + ');\n' + \
						str(thisStave.staveName) + '.setContext(' + \
						str(self.context.getContextName()) + ').draw();'
						result += beamPostamble

			tieStart = True
			thisTieStart = None
			thisStartLineNum = None
			tieNum = 0
			for (thisTie, thisName, thisLineNum) in partialTies:
				if tieStart:
					thisTieStart = str(thisName)+'['+str(thisTie[0])+']'
					thisStartLineNum = thisLineNum
					tieStart = False
				else:
					thisTieEnd = str(thisName)+'['+str(thisTie[1])+']'

					if thisTieStart == None or thisTieEnd == None:
						print 'uh oh... got mixed up somewhere'
						print partialTies
						print 'Ignoring'
						tieStart = True
						continue

					if thisLineNum != thisStartLineNum:
						result +='\nvar '+thisTieName+'Start = new Vex.Flow.StaveTie({\n'+'first_note: '+thisTieStart+'\n});'
						result +='\nvar '+thisTieName+'End = new Vex.Flow.StaveTie({\n'+'last_note: '+thisTieEnd+'\n});'
						result += '\n'+thisTieName+'Start.setContext('+str(self.context.getContextName())+').draw();'
						result += '\n'+thisTieName+'End.setContext('+str(self.context.getContextName())+').draw();'
						tieStart = True
						continue


					thisTieName = str(self.context.getContextName()) + 'Tie' + \
						str(tieNum)

					result +='\nvar '+thisTieName+' = new Vex.Flow.StaveTie({\n'+\
						'first_note: '+thisTieStart+',\nlast_note: '+thisTieEnd\
						+',\nfirst_indices: [0],\nlast_indices: [0]\n});'
					result += '\n'+thisTieName+'.setContext('+\
						str(self.context.getContextName())+').draw();'
					tieStart = True


			result += htmlConclusion
			return result


class VexflowPart(object):
	'''
	A part is a wrapper for the vexflow code representing multiple measures
		of music that should go in the same musical staff (as opposed to
		a vexflow staff)
	'''

	def __init__(self, music21part, params={}):
		global UIDCounter
		self.UID = UIDCounter
		UIDCounter += 1
		self.originalPart = music21part
		self.staves = []
		self.numMeasures = 0
		self.numLines = 0
		self.lineWidth = 0
		self.measureWidth = 0
		self.leftMargin = 0
		self.topMargin = 0
		self.systemHeight = 0
		self.vexflowCode = ''
		self.params = params
		if 'measuresPerStave' not in self.params:
			self.params['measuresPerStave'] = defaultMeasuresPerStave
		if 'canvasMargin' not in self.params:
			self.params['canvasMargin'] = defaultCanvasMargin
		if 'canvasWidth' not in self.params:
			self.params['canvasWidth'] = defaultCanvasWidth
		if 'staveHeight' not in self.params:
			self.params['staveHeight'] = defaultStaveHeight
		if 'numParts' not in self.params:
			self.params['numParts'] = 1
		if 'partIndex' not in self.params:
			self.params['partIndex'] = 0
		if 'interSystemMargin' not in self.params:
			self.params['interSystemMargin'] = defaultInterSystemMargin
		if 'intraSystemMargin' not in self.params:
			self.params['intraSystemMargin'] = defaultIntraSystemMargin
		if 'measureMargin' not in self.params:
			#Leaves a margin around the notes in a measure
			self.params['measureMargin'] = defaultMeasureMargin
		if 'context' not in self.params:
			self.context = None
		else:
			self.context = self.params['context']

		self._computeParams()
		self._generateVexflowCode()

	def _computeParams(self):
		'''
		Computes parameters necessary for placing the measures in the canvas
		'''
		self.lineWidth = '(' + str(self.params['canvasWidth']) + ' - (2*' + \
			str(self.params['canvasMargin']) + '))'
		self.measureWidth = '((' + str(self.lineWidth) + ') / ' + \
			str(self.params['measuresPerStave']) + ')'
		self.notesWidth = '((' + self.measureWidth + ') - ' + \
			str(self.params['measureMargin']) + ')'
		self.leftMargin = self.params['canvasMargin']
		self.topMargin = self.params['canvasMargin']
		self.systemHeight = '(' + str(self.params['numParts']) + ' * (' + \
			str(self.params['staveHeight']) + ' + ' + \
			str(self.params['intraSystemMargin']) + '))'

		self.clef = vexflowClefFromClef(self.originalPart.flat.getElementsByClass('Clef')[0])
	
	def _generateVexflowCode(self):
		'''
		Generates the vexflow code to display this part
		'''
		self.numMeasures = -1
		self.numLines = 0
		self.staves = []
		previousKeySignature = False
		for thisMeasure in self.originalPart:
			if 'Measure' not in thisMeasure.classes:
				continue
			self.numMeasures += 1
			thisXPosition = '(' + str(self.numMeasures % \
				self.params['measuresPerStave']) + ' * ' + \
				str(self.measureWidth) + ' + ' + str(self.leftMargin) + ')'
			self.numLines = int(self.numMeasures) / \
				int(self.params['measuresPerStave'])
			thisYPosition = '((' + str(self.numLines) + ' * (' + \
				str(self.systemHeight) + ' + ' + \
				str(self.params['interSystemMargin']) + ')) + ' + \
				str(self.topMargin) + ' + (' + str(self.params['partIndex']) + \
				'*(' + str(self.params['staveHeight']) + '+' +\
				str(self.params['intraSystemMargin']) + ')))'
			theseParams = {
				'width': self.measureWidth,
				'position': (thisXPosition, thisYPosition),
				'name': 'stavePart' + str(self.params['partIndex']) + 'Measure' + \
					str(self.numMeasures) + 'Line' + str(self.numLines) + 'ID' + \
					str(self.UID),
				'clef': self.clef,
				'notesWidth': self.notesWidth,
				'lineNum': self.numLines
			}
			
			#Display the clef at the start of new lines
			isNewLine = (self.numMeasures % \
				self.params['measuresPerStave'] == 0)
			theseParams['clefDisplayStatus'] = isNewLine
			theseParams['keySignatureDisplayStatus'] = isNewLine
			
			if previousKeySignature:
				theseParams['keySignature'] = previousKeySignature

			#if theseParams['keySignatureDisplayStatus']:
				#print "Part: %d, Measure: %d, Line: %d" % \
					#(self.params['partIndex'], self.numMeasures, self.numLines)

			thisStave = VexflowStave(params=theseParams)

			thisVoiceBaseName = 'music21Stave' + str(self.numMeasures) +\
				'Part' + str(self.params['partIndex']) + 'Voice'
			voiceParams = theseParams
			voiceParams['name'] = thisVoiceBaseName

			if len(thisMeasure.getElementsByClass('Voice')) == 0:
				theseVoices = VexflowVoice(thisMeasure, \
					params=voiceParams)
				previousKeySignature = theseVoices.keySignature
			else:
				theseVoices = []
				music21voices = thisMeasure.getElementsByClass('Voice')
				voiceParams['name'] += '0'
				for index in xrange(len(music21voices)):
					thisVoice = music21voices[index]
					voiceParams['name'] = voiceParams['name'][:-1] + str(index)
					theseVoices += [VexflowVoice(thisVoice, \
						params=voiceParams)]
					previousKeySignature = thisVoice.keySignature
			thisStave.setVoice(theseVoices)
			self.staves += [thisStave]

		contextParams = {
			'width': self.params['canvasWidth'],
			'height': '((' + str(self.numLines + 1) + ' * ('+str(self.systemHeight)+\
				' + ' + str(self.params['interSystemMargin']) + ')) + 2* ' +\
				str(self.topMargin) + ')'
		}

		if self.context == None:
			self.context = VexflowContext(contextParams)
		else:
			self.context.setWidth(contextParams['width'])
			self.context.setHeight(contextParams['height'])

		self.vexflowCode = ''

		for thisStave in self.staves:
			for thisVoice in thisStave.vexflowVoices:
				self.vexflowCode += thisVoice.generateCode('txt') + '\n'
			self.vexflowCode += thisStave.generateCode('txt') + '\n'

	def beamCode(self, contextName, indentation=3):
		'''
		Generates the code for beaming all of the staves in this part

		Returns as an array containing the preamble and postamble
		'''
		preamble = []
		postamble = []
		for thisStave in self.staves:
			(pre, post) = thisStave.beamCode(contextName, indentation=indentation)
			preamble += [pre]
			postamble += [post]
		return [('\n' + ('\t' * indentation)).join(preamble), ('\n' + ('\t' * indentation)).join(postamble)]

	def generateCode(self, mode='txt'):
		'''
		generates the vexflow code necessary to display this voice in a browser
		'''
		if mode=='txt':
			return self.vexflowCode
		elif mode=='html':
			result = htmlCanvasPreamble + str(self.context.getCanvasHTML()) + \
				htmlCanvasPostamble + '\n'
			result += self.context.getJSCode(indentation=3) + '\n'
			result += self.vexflowCode + '\n'
			for thisStave in self.staves:
				for thisVoice in thisStave.vexflowVoices:
					result += str(thisVoice.voiceName) + '.draw(' + \
					str(self.context.getContextName()) + ', ' + \
					str(thisStave.staveName) + ');\n' + \
					str(thisStave.staveName) + '.setContext(' + \
					str(self.context.getContextName()) + ').draw();'

			result += htmlConclusion
			return result
	
	def getContext(self):
		return self.context


class VexflowVoice(object):
	'''
	A Voice in Vex Flow is a "lateral" grouping of notes in one measure
		It's the equivalent to a :class:`~music21.stream.Measure`

	Requires either a Measure object or a Voice object
		If those objects aren't already flat, flattens them.
	
	'''
	
	def __init__(self, music21measure, params={}):
		'''
		params is a dict containing various parameters to be passed to the 
			voice object
		'''
		global UIDCounter
		self.UID = UIDCounter
		UIDCounter += 1

		if music21measure != None:
			if not ('Measure' in music21measure.classes or \
				'Voice' in music21measure.classes):
				raise TypeError, 'must pass a music21 Measure object'
			self.originalMeasure = music21measure
			self.originalNotes = music21measure.flat

		self.params = params
		self.voiceCode = ''
		self.noteCode = ''
		self.beams = []
		self.ties = []
		self.clefDisplayStatus = defaultClefDisplayStatus
		self.keySignatureDisplayStatus = defaultKeySignatureDisplayStatus

		if 'name' in self.params:
			self.voiceName = self.params['name']
		else:
			self.voiceName = 'music21Voice' + str(self.UID)
			self.params['name'] = self.voiceName

		#if 'octaveModifier' not in self.params:
			#Used for bass clef
			#self.params['octaveModifier'] = 0

		#Set the clef
		theseClefs = self.originalNotes.getElementsByClass('Clef')
		if len(theseClefs) > 1:
			raise VexFlowUnsupportedException, 'Vexflow cannot yet handle ' +\
				'multiple clefs in a single measure'
		elif len(theseClefs) == 1:
			self.clefDisplayStatus = True
			self.clef = vexflowClefFromClef(theseClefs[0])
		else:
			if 'clef' in self.params:
				self.clef = self.params['clef']
			else:
				self.clef = defaultStaveClef
			if 'clefDisplayStatus' in self.params:
				self.clefDisplayStatus = self.params['clefDisplayStatus']

		#Set the key signature
		theseKeySignatures = self.originalNotes.getElementsByClass('KeySignature')
		if len(theseKeySignatures) > 1:
			raise VexFlowUnsupportedException, 'Vexflow cannot yet handle ' +\
				'multiple key signatures in a single measure'
		elif len(theseKeySignatures) == 1:
			self.keySignatureDisplayStatus = True
			if theseKeySignatures[0].sharps in vexflowSharpsToKeySignatures:
				self.keySignature = \
					vexflowSharpsToKeySignatures[theseKeySignatures[0].sharps]
			else:
				raise VexFlowUnsupportedException, "Vexflow doesn't support this "+\
					'Key Signature:', theseKeySignatures[0]
		else:
			if 'keySignature' in self.params:
				self.keySignature = self.params['keySignature']
			else:
				self.keySignature = defaultStaveKeySignature
				#print "%s got the default key" % self.params['name'] #XXX k
				#print 'Params: ', self.params
			if 'keySignatureDisplayStatus' in self.params:
				self.keySignatureDisplayStatus = \
					self.params['keySignatureDisplayStatus']

		#Set the time signature
		theseTimeSignatures = self.originalNotes.getElementsByClass('TimeSignature')
		if len(theseTimeSignatures) > 1:
			raise VexFlowUnsupportedException, 'Vexflow cannot yet handle ' +\
				'multiple time signatures in a single measure'
		elif len(theseTimeSignatures) == 1:
			self.numBeats = self.originalMeasure.highestTime
			self.beatValue = 4
			self.timeSignature='/'.join([str(theseTimeSignatures[0].numerator),\
				str(theseTimeSignatures[0].denominator)])
		else:
			if not 'numBeats' in self.params:
				self.params['numBeats'] = self.originalMeasure.highestTime
	
			if not 'beatValue' in self.params:
				self.params['beatValue'] = 4

			self.numBeats = self.params['numBeats']
			self.beatValue = self.params['beatValue']
			self.timeSignature = False
		
		if 'beaming' not in self.params:
			self.params['beaming'] = defaultBeamingStatus

		self._generateVexflowCode()

	def _generateVexflowCode(self):
		'''
		Generates the code necessary to display this voice
		'''
		self.voiceCode = 'var ' + str(self.voiceName) + ' = new Vex.Flow.Voice({' +\
			'num_beats: ' + str(self.numBeats) + ', ' + \
			'beat_value: ' + str(self.beatValue) + ', ' + \
			'resolution: Vex.Flow.RESOLUTION});'

		noteName = self.voiceName + 'Notes'
		self.noteCode = 'var ' + noteName + ' = ['

		tieStarted = False
		theseTies = []
		thisTieStart = None
		beamStarted = False
		theseBeams = []
		thisBeamStart = None
		index = 0

		for thisNote  in self.originalNotes:
			if 'Note' in thisNote.classes:
				thisVexflowNote = VexflowNote(thisNote, params=\
					{'clef': self.clef})
				self.noteCode += thisVexflowNote.generateCode('txt')
				self.noteCode += ', '

				if not beamStarted and thisVexflowNote.beamStart:
					thisBeamStart = index
					beamStarted = True
				elif beamStarted and thisVexflowNote.beamStop:
					theseBeams += [(thisBeamStart, index)]
					beamStarted = False

				if not tieStarted and thisVexflowNote.tieStart:
					thisTieStart = index
					tieStarted = True
				elif not tieStarted and thisVexflowNote.tieStop:
					#could mean tie began in previous bar
					theseTies += [(None, index)]
					tieStarted = False
				elif tieStarted and thisVexflowNote.tieStop:
					theseTies += [(thisTieStart, index)]
					tieStarted = False

				index+= 1
			elif 'Chord' in thisNote.classes:
				thisVexflowChord = VexflowChord(thisNote, params=\
					{'clef': self.clef})
				self.noteCode += thisVexflowChord.generateCode('txt')
				self.noteCode += ', '

				if not beamStarted and thisVexflowChord.beamStart:
					thisBeamStart = index
					beamStarted = True
				elif beamStarted and thisVexflowChord.beamStop:
					theseBeams += [(thisBeamStart, index)]
					beamStarted = False

				if not tieStarted and thisVexflowNote.tieStart:
					thisTieStart = index
					tieStarted = True
				elif tieStarted and thisVexflowNote.tieStop:
					theseTies += [(thisTieStart, index)]
					tieStarted = False

				index+= 1
			elif 'Rest' in thisNote.classes:
				thisVexflowRest = VexflowRest(thisNote, params=\
					{'clef': self.clef})
				self.noteCode += thisVexflowRest.generateCode('txt')
				self.noteCode += ', '
				index+= 1
			#TODO tuplet: if the note is the start of a tuplet, remember that it's the start of one and figure out how many
			#	Later we'll do notes.slice(indexOfStart, lengthOfTuplet)
			#	For now, we'll just throw an exception if the tuplet isn't complete

		self.beams = theseBeams
		if tieStarted:
			#Partial tie across the bar, beginning on this page
			theseTies += [(thisTieStart, None)]
		self.ties = theseTies
		self.noteCode = self.noteCode[:-2] + '];'

		self.vexflowCode = self.voiceCode + '\n' + self.noteCode + '\n' +\
			str(self.voiceName) + '.addTickables(' + str(self.voiceName) + \
			'Notes);'

	def getBeaming(self):
		'''
		Beaming is a boolean value determining if the voice should be beamed

		Note: So far only VexFlow's automatic beaming is supported
			Cannot manually modify beams
		'''
		return self.params['beaming']

	def beamCode(self, contextName, indentation=3):
		'''
		Returns the code for the beams for this voice

		Returns it as an array containing the beam preamble and postamble

		Will return code even if it shouldn't be beamed
			Check self.getBeaming() before applying this
		'''
		baseBeamName = str(self.voiceName) + 'Beam'
		noteName = str(self.voiceName) + 'Notes'
		preamble = ''
		postamble = ''

		for index in xrange(len(self.beams)):
			thisBeam = self.beams[index]
			thisBeamName = baseBeamName + str(index)

			preamble += '\n' + ('\t' * indentation) + 'var ' + thisBeamName +\
				' = new Vex.Flow.Beam('+noteName+'.slice(' + str(thisBeam[0])+\
				',' + str(thisBeam[1]+1) + '));'
			postamble += '\n' + ('\t'*indentation) + thisBeamName + '.setCont'+\
				'ext(' + str(contextName) + ').draw();'
		return [preamble, postamble]
	
	def tieCode(self, contextName, indentation=3):
		'''
		Returns the code for the ties for this voice

		Returns it as an array containing the completed ties within this voice,
			and the partial ties that go across the bar line
		'''
		baseTieName = str(self.voiceName) + 'Tie'
		noteName = str(self.voiceName) + 'Notes'
		fullTies = []
		partialTies = []

		for index in xrange(len(self.ties)):
			thisTie = self.ties[index]
			if thisTie[0] != None and thisTie[1] != None:
				#TODO: add support for multiple ties in a chord
				thisTieName = baseTieName + str(index)
				thisTieCode = ('\t'*indentation)+'var '+thisTieName+' = new V'+\
					'ex.Flow.StaveTie({\n'+('\t'*(indentation+1))+'first_note'+\
					': '+noteName+'['+str(thisTie[0])+'],\n'+('\t'*(indentation\
					+1))+'last_note: '+noteName+'['+str(thisTie[1])+'],\n'+\
					('\t'*(indentation+1))+'first_indices: [0],\n'+('\t'*\
					(indentation+1))+'last_indices: [0]\n'+('\t'*indentation)+\
					'});'
				thisTieCode += '\n'+('\t'*indentation)+thisTieName+'.setConte'+\
					'xt('+str(contextName)+').draw();'
				fullTies += [thisTieCode]
			else:
				partialTies += [[thisTie, noteName]]

		return ('\n'.join(fullTies), partialTies)
	
	def getNumBeats(self):
		return self.numBeats
	
	def getBeatValue(self):
		return self.params['beatValue']
	
	def setBeaming(self, beaming):
		'''
		Beaming is a boolean value determining if the voice should be beamed

		Note: So far only VexFlow's automatic beaming is supported
			Cannot manually modify beams
		'''
		self.params['beaming'] = beaming

	def generateCode(self, mode='txt'):
		'''
		returns the vexflow code necessary to display this Voice in a browser
			as a string
		'''
		if mode == 'txt':
			return self.vexflowCode
		elif mode == 'html':
			result = htmlPreamble + vexflowPreamble
			result += "\n\t\t\tvar stave = new Vex.Flow.Stave(" + \
				str(defaultStavePosition[0]) + "," + \
				str(defaultStavePosition[1]) + "," + \
				str(defaultStaveWidth) + ");\n\t\t\tstave.addClef('" + \
				str(defaultStaveClef) + "').setContext(ctx).draw();\n\t\t\t" + \
				str(self.vexflowCode)+"\n\t\t\tvar formatter = new Vex.Flow.F"+\
				"ormatter().joinVoices(["+str(self.voiceName)+"]).format([" + \
				str(self.voiceName)+"], "+str(defaultStaveWidth)+");\n\t\t\t" +\
				str(self.voiceName)+".draw(ctx, stave);\n"
			result += htmlConclusion
			return result

			

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
		global UIDCounter
		self.UID = UIDCounter
		UIDCounter += 1
		self.params = params
		self.vexflowVoices = []
		self.voicesCode = ''
		self.staveCode = ''
		self.vexflowCode = ''
		if 'width' not in self.params:
			self.params['width'] = defaultStaveWidth
		if 'notesWidth' not in self.params:
			self.params['notesWidth'] = '(' + str(self.params['width']) +\
				' - ' + str(defaultMeasureMargin) + ')'
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

		self._generateVexflow()
	
	def _generateVexflow(self):
		self.staveCode = 'var ' + str(self.staveName) + ' = new Vex.Flow.Stave(' +\
			str(self.params['position'][0])+','+str(self.params['position'][1])\
			+ ',' + str(self.params['width']) + ');'

		if len(self.vexflowVoices) > 0:
			self.voicesCode = 'var ' + str(self.staveName) + 'Formatter = new'+\
			' Vex.Flow.Formatter().joinVoices('

			voiceList = '['
		
			for thisVoice in self.vexflowVoices:
				voiceList += str(thisVoice.voiceName) + ', '
				if 'clef' not in self.params or not self.params['clef']:
					self.params['clef'] = thisVoice.clef

				if 'timeSignature' not in self.params or not \
					self.params['timeSignature']:
						self.params['timeSignature'] = thisVoice.timeSignature

				if 'keySignature' not in self.params or not \
					self.params['keySignature']:
						self.params['keySignature'] = thisVoice.keySignature

			voiceList = voiceList[:-2] + ']'
			self.voicesCode += str(voiceList) + ').format(' + str(voiceList) + \
				', ' + str(self.params['notesWidth'])  + ');'
		else:
			self.voicesCode = ''
	
		if 'clefDisplayStatus' in self.params and \
			'clef' in self.params and self.params['clefDisplayStatus']:
			self.staveCode += '\n' + str(self.staveName) + '.addClef("' + \
				str(self.params['clef']) + '");'

		if 'keySignatureDisplayStatus' in self.params and \
			'keySignature' in self.params and self.params['keySignatureDisplayStatus']:
			self.staveCode += '\n' + str(self.staveName) + '.addKeySignature('+\
				'"' + str(self.params['keySignature']) + '");'

		if 'timeSignature' in self.params and self.params['timeSignature']:
			self.staveCode += '\n' + str(self.staveName) + '.addTimeSignature'+\
				'("' + str(self.params['timeSignature']) + '");'

		self.vexflowCode = str(self.staveCode) + '\n' + str(self.voicesCode)
	
	def getWidth(self):
		return self.params['width']

	def getPosition(self):
		'''
		(x,y) position in relation to the top left corner of the canvas
		'''
		return self.params['position']
	
	def getLineNum(self):
		'''
		Tries to get the line number of this stave

		Maybe should use getParam('lineNum') instead
		'''
		if 'lineNum' in self.params:
			return self.params['lineNum']
		else:
			#XXX Should I do something different here?
			return 0
	
	def beamCode(self, contextName, indentation=3):
		'''
		Generates the code for beaming all of the voices on this stave

		Returns an array containing the preamble and postamble
		'''
		preamble = []
		postamble = []
		for thisVoice in self.vexflowVoices:
			if thisVoice.getBeaming():
				(pre, post) = thisVoice.beamCode(contextName, indentation=indentation)
				preamble += [pre]
				postamble += [post]
		return [('\n' + ('\t' * indentation)).join(preamble), ('\n' + ('\t' * indentation)).join(postamble)]

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

	def addVoice(self, thisVexflowVoice):
		'''
		Adds thisVexflowVoice (an instance of VexflowVoice) to this 
			VexflowStave
		'''
		self.vexflowVoices += [thisVexflowVoice]
		if 'clefDisplayStatus' not in self.params or \
			not self.params['clefDisplayStatus']:
			self.params['clefDisplayStatus'] = \
				thisVexflowVoice.params['clefDisplayStatus']

		if 'keySignatureDisplayStatus' not in self.params or \
			not self.params['keySignatureDisplayStatus']:
			self.params['keySignatureDisplayStatus'] = \
				thisVexflowVoice.params['keySignatureDisplayStatus']

		#print 'Sig: %s, Display?: %s' % (self.params['keySignature'], self.params['keySignatureDisplayStatus']) #XXX k
		self._generateVexflow()
	
	def setVoice(self, theseVexflowVoices):
		'''
		Identical to setVoices, but implies that you can call with
			single voice instead of a list of voices

		XXX: Should I delete this method?
		'''
		self.setVoices(theseVexflowVoices)
		
	def setVoices(self, theseVexflowVoices):
		'''
		Replaces any existing voices attached to this Stave with 
			theseVexflowVoices (a list of instances of VexflowVoice)
		'''
		if isinstance(theseVexflowVoices, list):
			self.vexflowVoices = theseVexflowVoices
		else:
			self.vexflowVoices = [theseVexflowVoices]

		self.params['clef'] = defaultStaveClef
		self.params['keySignature'] = defaultStaveKeySignature
		for thisVoice in self.vexflowVoices:
			if 'clefDisplayStatus' not in self.params or \
				(not self.params['clefDisplayStatus'] and \
				'clefDisplayStatus' in thisVoice.params):
				self.params['clefDisplayStatus'] += \
					thisVoice.params['clefDisplayStatus']

			if 'keySignatureDisplayStatus' not in self.params or \
				(not self.params['keySignatureDisplayStatus'] and \
				'keySignatureDisplayStatus' in thisVoice.params):
				self.params['keySignatureDisplayStatus'] += \
					thisVoice.params['keySignatureDisplayStatus']

			if thisVoice.clef:
				self.params['clef'] = thisVoice.clef

			if thisVoice.keySignature:
				self.params['keySignature'] = thisVoice.keySignature

		#print 'Sig: %s, Display?: %s' % (self.params['keySignature'], self.params['keySignatureDisplayStatus']) #XXX k
		self._generateVexflow()
	
	def getVoices(self):
		return self.vexflowVoices


	def generateCode(self, mode='txt'):
		'''
		Generates the vexflow code to display this staff in a browser
		'''
		if mode == 'txt':
			return self.vexflowCode
		elif mode == 'html':
			raise VexFlowUnsupportedException, "Sorry, I haven't finished " + \
				'support for standalone staves yet'

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
		global UIDCounter
		self.UID = UIDCounter
		UIDCounter += 1
		self.params = params
		self.canvasHTML = ''
		self.canvasJSCode = ''
		self.rendererName = ''
		self.rendererCode = ''
		self.contextName = ''
		self.contextCode = ''
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

		self.generateHTML()
		self.generateJS()

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

		if applyAttributes:
			self.canvasJSCode += ' ' + self.canvasJSName + '.width =' + \
				str(self.getWidth()) +'; ' + self.canvasJSName + '.height = ' +\
				str(self.getHeight()) + ';'
		
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

