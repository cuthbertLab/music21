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


'''Objects for transcribing music21 objects as Vex Flow code
'''

import unittest
#try:
#    import StringIO # python 2 
#except:
#    from io import StringIO # python3 (also in python 2.6+)


import music21

from music21 import environment
_MOD = 'vexflow.base.py'
environLocal = environment.Environment(_MOD)

#TODO Here go variables for base.py
supportedDisplayModes = ['txt', 'html']

global UIDCounter 
UID = 0

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
#TODO Here go exception classes

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
	if 'Measure' in thisObject.classes:
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
	pass

def fromNote(thisNote, mode='txt'):
	'''
	Parses a music21 note into Vex Flow code
	'''
	if mode not in supportedDisplayModes:
		raise VexFlowUnsupportedException, 'Unsupported mode: ' + str(mode)
	return VexflowNote(thisNote).show(mode)

def fromPart(thisPart, mode='txt'):
	'''
	Parses a music21 part into Vex Flow code
	'''
	if mode not in supportedDisplayModes:
		raise VexFlowUnsupportedException, 'Unsupported mode: ' + str(mode)
	pass

def fromMeasure(thisMeasure, mode='txt'):
	r'''
	Parses a music21 measure into Vex Flow code

	TODO: Write tests
	
	>>> from music21 import *
	>>> from music21 import vexflow
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
	
	if mode == 'txt':
		resultingText = "var notes = ["
#TODO Cache measure.notes and len()
		for i in xrange(len(thisMeasure.notes)):
			thisNote = thisMeasure.notes[i]
			thisVexflow = VexflowNote(thisNote)
			resultingText += thisVexflow.show('txt')
			if i < len(thisMeasure.notes) - 1:
				resultingText += ", "
		resultingText += "];"
		return resultingText

	if mode == 'html':
		resultingText = htmlPreamble + vexflowPreamble + "\n\t\t\tvar stave ="+\
			" new Vex.Flow.Stave(10,0,500);\n\t\t\tstave.addClef('treble')." + \
			"setContext(ctx).draw();"
		resultingText += "\n\t\t\tvar notes = [\n\t\t\t"
		for i in xrange(len(thisMeasure.notes)):
			thisNote = thisMeasure.notes[i]
			thisVexflow = VexflowNote(thisNote)
			resultingText += "\t" + thisVexflow.show('txt')
			if i < len(thisMeasure.notes) - 1:
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



#-------------------------------------------------------------------------------
class VexflowNote:
	'''
	A VexflowNote object has a .show() method which produces VexFlow code to 
	represent a :class:`music21.note.Note` object.

	TODO: This should probably inherit from music21.music21Object or 
	note.GeneralNote or something

	TODO: Verify that I'm not overwriting any base attribute names of music21

	TODO: add setters/getters

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
		'''

		self.originalNote = music21note

		thisPitchName = music21note.pitch.name
		thisPitchOctave = music21note.pitch.implicitOctave
		thisPitch = thisPitchName + str(thisPitchOctave)
		thisAccidental = music21note.accidental
		if thisAccidental != None:
			if thisAccidental.alter in vexflowAlterationToAccidental:
				self.vexflowAccidental =\
					 vexflowAlterationToAccidental[thisAccidental.alter]
			else:
				raise VexFlowUnsupportedException, "VexFlow doesn't support "\
					+ "this accidental type. " + str(thisAccidental.fullName)
		else:
			self.vexflowAccidental = 'n'

		self.vexflowKey = thisPitch[0] + self.vexflowAccidental + '/' \
			+ thisPitch[-1]

		thisQuarterLength = music21note.duration.quarterLength
		if thisQuarterLength in vexflowQuarterLengthToDuration:
			self.vexflowDuration = \
				vexflowQuarterLengthToDuration[thisQuarterLength]
		else:
			raise VexFlowUnsupportedException, "VexFlow doesn't support this "\
				+ "duration. " + str(music21note.duration.fullName)

		self.vexflowCode = 'new Vex.Flow.StaveNote({keys: ["'+self.vexflowKey+ \
			'"], duration: "' + self.vexflowDuration + '"})'
	
	def show(self, mode="txt"):
		'''
		Returns the VexFlow code in the desired display mode

		Currently supported modes:
			txt: returns the VexFlow code which can be used in conjunction with
				 other VexFlow code
			html: returns standalone HTML code for displaying just this note

		>>> from music21 import *
		>>> n = note.Note('C-')
		>>> v = vexflow.VexflowNote(n)
		>>> v.show('txt')
		'new Vex.Flow.StaveNote({keys: ["Cb/4"], duration: "q"})'

		>>> print v.show('html')
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
		if mode == 'txt':
			return self.vexflowCode
		elif mode == 'html':
			result = htmlPreamble + vexflowPreamble
			result += "\n\t\t\tvar stave = new Vex.Flow.Stave(10,0,500);\n\t" +\
				"\t\tstave.addClef('treble').setContext(ctx).draw();"
			result += "\n\t\t\tvar notes = [" + self.vexflowCode + "];\n\t\t" +\
				"\tvar voice = new Vex.Flow.Voice({\n\t\t\t\tnum_beats: " + \
				str(self.originalNote.duration.quarterLength) + ",\n" + \
				"\t\t\t\tbeat_value: 4,\n\t\t\t\tresolution: Vex.Flow.RESOLU" +\
				"TION\n\t\t\t});\n\t\t\tvoice.addTickables(notes);\n\t\t\tvar"+\
				" formatter = new Vex.Flow.Formatter().joinVoices([voice]).fo"+\
				"rmat([voice], 500);\n\t\t\tvoice.draw(ctx, stave);\n"
			result += htmlConclusion
			return result

class VexflowVoice:
	pass

#-------------------------------------------------------------------------------
#TODO Here go Tests
class Test(unittest.TestCase):
    
    def runTest(self):
        pass
    
#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = []


if __name__ == "__main__":
    # sys.arg test options will be used in mainTest()
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof




