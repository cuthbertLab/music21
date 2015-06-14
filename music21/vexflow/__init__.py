# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         vexflow/__init__.py
# Purpose:      music21 classes for converting music21 objects to vexflow
#
# Authors:      Christopher Reyes
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------

#TODO: review variable names for consistency

'''
Objects for transcribing music21 objects as VexFlow code

Here's the hierarchy:

*    A VexflowContext can be used to display multiple VexflowParts.
*    Each VexflowPart contains multiple VexflowStaves (one for each measure)
*    Each VexflowStave might contain multiple VexflowVoices
'''

import unittest


from music21.vexflow import indent
from music21.vexflow import toMusic21j

from music21 import common
from music21 import exceptions21
from music21 import note
from music21 import pitch
from music21 import stream


from music21 import environment
_MOD = 'vexflow.__init__.py'
environLocal = environment.Environment(_MOD)

#Class variables

'''
Vexflow generateCode() and fromObject() methods currently accept these modes.
'''
supportedDisplayModes = [
    'txt',
    'html',
    'jsbody'
]

'''
Can call fromObject on the following types of music21 objects.
'''
supportedMusic21Classes = [
    'Note',
    'Pitch',
    'Rest',
    'Chord',
    'Measure',
    'Part',
    'Score',
    'Stream',
    'Voice',
]

'''
Valid values for various VexFlow Properties
These come from the Tables.js file
'''
validVexFlowKeySignatures = [
    "C",    "Am",    "F",    "Dm",
    "Bb",    "Gm",    "Eb",    "Cm",
    "Ab",    "Fm",    "Db",    "Bbm",
    "Gb",    "Ebm",    "Cb",    "Abm",
    "G",    "Em",    "D",    "Bm",
    "A",    "F#m",    "E",    "C#m",
    "B",    "G#m",    "F#",    "D#m",
    "C#",    "A#m"
]

#VexFlow calls pitch values "keys"
#Not used...
validVexFlowKeys = []
for pitchName in ['C','D','E','F','G','A']:
    for modifier in ('','N','#','##','B','BB'):
        validVexFlowKeys.append(pitchName + modifier)
validVexFlowKeys.append('X')
validVexFlowKeys.append('R')

#Allow for different glyphs other than standard western notation for notes
#Not used...
validVexFlowNoteheadGlyphs = [
    #  Diamond 
    'D0',    'D1',    'D2',    'D3',
    #  Triangle 
    'T0',    'T1',    'T2',    'T3',
    #  Cross 
    'X0',    'X1',    'X2',    'X3',
]


#Valid vexflow articulation codes and their meanings
#not used...
validVexFlowArticulationsToMeanings = {
    "a.": 'Staccato',
    "av": 'Staccatissimo',
    "a>": 'Accent',
    "a-": 'Tenuto',
    "a^": 'Marcato',
    "a+": 'Left hand pizzicato',
    "ao": 'Snap pizzicato',
    "ah": 'Natural harmonic or open note',
    "a@a": 'Fermata above staff',
    "a@u": 'Fermata below staff',
    "a|": 'Bow up - up stroke',
    "am": 'Bow down - down stroke',
    "a,": 'Choked'
}

#...not used.
ValidVexFlowAccidentals = ['bb','b','n','#','##']


#not used...
validVexFlowDurations = []
#When the duration is followed by an 'h', it displays a 'harmonic' note
#When the duration is followed by an 'm', it displays a 'muted' note
#When the duration is followed by a 'd', it displays a dotted note
#When the duration is followed by an 'r', it displays a rest

for durationTypes in ['w','h','q','8','16','32','64']:
    for modifier in ['','d','h','m','r']:
        validVexFlowDurations.append(durationTypes + modifier)

validVexFlowDurations.append('b') #Has the duration of a thirty-second note

'''
Default canvas parameters. Can be anything that implements __str__
Each should be valid jQuery, javascript, or VexFlow code 
    as those are the only scripts currently imported
'''
defaultCanvasWidth = '($(window).width()-10)'
defaultCanvasHeight = '$(window).height()'
defaultCanvasMargin = 10

'''
Default stave parameters for the VexFlow staves
Can be anything that implements __str__
Each should be valid jQuery, javascript, or Vexflow code
    as those are the only scripts currently imported

>>> assert defaultKeySignature in validVexFlowKeySignatures #_DOCS_HIDE
'''
defaultStaveWidth = 500
defaultStaveHeight = 90 #Derived from the vexflow.stave.JS file
defaultStavePosition = (10,0)
defaultStaveClef = 'treble'
defaultStaveKeySignature = 'C'

'''
Default parameters for postitioning the staves of the score

IntraSystemMargin is the space between staves in the same system
InterSystemMargin is the space between the bottom of one system and the top of
    the next
'''
defaultIntraSystemMargin = 20
defaultInterSystemMargin = 60

'''
Default parameters for setting measures within one staff line
'''
defaultMeasureWidth = 500
defaultMeasuresPerSystem = 4
defaultMeasureMargin = 75

'''
Determines if voices should be beamed by default
Can specify on a measure-by-measure basis
'''
defaultBeamingStatus = True

'''
Determines whether accidentals, clefs, and key signatures should be displayed by
default on this measure.  Can be set for individually notes or measures.
'''
defaultAccidentalDisplayStatus = False
defaultClefDisplayStatus = False
defaultKeySignatureDisplayStatus = False

'''
If the user tries to create a Vexflow21 Object from a musical object without a
    duration, sets the default quarterLength to this property
'''
defaultNoteQuarterLength = 1

'''
Table to go from the alter attribute of a :class:`music21.pitch.Accidental`
    object to the VexFlow code representing that accidental

Not all accidentals supported by Music21 are supported by VexFlow
'''
alterationToVexflowAccidental = {
    -2.0: 'bb',
    -1.0: 'b',
    0: 'n',
    1.0: '#',
    2.0: '##'
}

ticksPerQuarter = 4096

'''
Table going from the quarterLength attribute of a 
    :class:`music21.duration.Duration` object to a VexFlow duration code
'''
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

'''
Table going from the sharps attribute of a :class:`music21.key.KeySignature`
    object to a VexFlow key signature code
'''
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

'''
Variables used in generating full HTML pages within which to view the VexFlow
'''
#vexflowGlobalCopy = "<script src='http://www.vexflow.com/vexflow.js'/></script>"
vexflowGlobalCopy = "<script src='http://www.vexflow.com/support/vexflow-min.js'></script>"
htmlCanvasPreamble = r"""<!DOCTYPE HTML>
<html>
<head>
    <meta name='author' content='Music21' />
    <script src='http://code.jquery.com/jquery-latest.js'></script>
    {vexflowGlobalCopy}
</head>
<body>
""".format(vexflowGlobalCopy=vexflowGlobalCopy)

htmlPreamble = htmlCanvasPreamble + r'''    <canvas width="525" height="120" id='music21canvas'></canvas>
    <script>
        $(document).ready(function(){
'''


htmlCanvasPostamble=r'''
    <script>
        $(document).ready(function(){
'''

vexflowPreamble = """\
var canvas = $('#music21canvas')[0];
var renderer = new Vex.Flow.Renderer(canvas, Vex.Flow.Renderer.Backends.CANVAS);
var ctx = renderer.getContext();
"""

htmlConclusion = r'''
        });
    </script>
</body>
</html>'''

class UIDCounter(object):
    '''
    A generic counter object for keeping track of the number of objects used:
    
    ::

        >>> uidc = vexflow.UIDCounter(UIDStart = 20)
        >>> uidc.UID
        20

    ::

        >>> uidc.readAndIncrement()
        20

    ::

        >>> uidc.readAndIncrement()
        21

    ::

        >>> uidc.UID
        22

    '''
    
    def __init__(self, UIDStart = 0):
        self.UID = UIDStart
    
    def readAndIncrement(self):
        UID = self.UID
        self.UID += 1
        return UID
    

def staffString(xPosStr = str(defaultStavePosition[0]), yPosStr = str(defaultStavePosition[1]), staffWidth = str(defaultStaveWidth), staveName = 'stave'):
    '''
    Returns a string formated new VexFlow Stave.  
    
    Arguments are strings representing the x and y position and the width.
    
    They are strings because a Javascript function can be used in lieu of the number.
    
    ::

        >>> vexflow.staffString()
        'var stave = new Vex.Flow.Stave(10,0,500);'

    ::    

        >>> vexflow.staffString('(0 * (((($(window).width()-10) - (2*10))) / 4) + 10)', '((0 * ((4 * (90 + 20)) + 60)) + 10 + (0*(90+20)))', '(((($(window).width()-10) - (2*10))) / 4)')
        'var stave = new Vex.Flow.Stave((0 * (((($(window).width()-10) - (2*10))) / 4) + 10),((0 * ((4 * (90 + 20)) + 60)) + 10 + (0*(90+20))),(((($(window).width()-10) - (2*10))) / 4));'

    '''

    defaultStaff = "var {staveName} = new Vex.Flow.Stave({xPosStr},{yPosStr},{staffWidth});".format(staveName=staveName,
                                                                                                      xPosStr=xPosStr,
                                                                                                      yPosStr=yPosStr,
                                                                                                      staffWidth=staffWidth)
    return defaultStaff


#-------------------------------------------------------------------------------
#Exception classes


class VexFlowUnsupportedException(exceptions21.Music21Exception):
    '''
    This feature or object is not supported by the VexFlow JavaScript library
    '''
    pass


class Vexflow21UnsupportedException(exceptions21.Music21Exception):
    '''
    This feature or object cannot be converted from music21 to VexFlow code yet
    '''
    pass


#-------------------------------------------------------------------------------


def fromObject(thisObject, mode='txt'):
    '''
    Attempts to translate an arbitrary Music21Object into vexflow

    Able to translate anything in vexflow.supportedMusic21Classes

    TODO: Unit Tests (one for each supportedMusic21Class)

    ::
    
        >>> print(vexflow.fromObject(note.Note('C4')))
        new Vex.Flow.StaveNote({keys: ["Cn/4"], duration: "q"})
    
    ::
    
        >>> print(vexflow.fromObject(pitch.Pitch('C4')))
        new Vex.Flow.StaveNote({keys: ["Cn/4"], duration: "q"})
    
    ::

        >>> print(vexflow.fromObject(note.Rest()))
        new Vex.Flow.StaveNote({keys: ["b/4"], duration: "qr"})

    ::

        >>> print(vexflow.fromObject(chord.Chord(['C4', 'E-4', 'G4'])))
        new Vex.Flow.StaveNote({keys: ["Cn/4", "Eb/4", "Gn/4"], duration: "q"})

    ::

        >>> bwv666 = corpus.parse('bwv66.6')
        >>> soprano = bwv666.parts[0]
        >>> measure1 = soprano.getElementsByClass('Measure')[0]
        >>> trebleVoice = bwv666.partsToVoices()[1][1][0]
        >>> bwv666
        <music21.stream.Score ...>

    ::

        >>> soprano
        <music21.stream.Part Soprano>

    ::

        >>> measure1
        <music21.stream.Measure 0 offset=0.0>

    ::

        >>> trebleVoice
        <music21.stream.Voice 0>

    ::

        >>> print(vexflow.fromObject(measure1))
        var music21Voice0 = new Vex.Flow.Voice({num_beats: 1.0, beat_value: 4, resolution: Vex.Flow.RESOLUTION});
        var music21Voice0Notes = [new Vex.Flow.StaveNote({keys: ["C#/5"], duration: "8", stem_direction: Vex.Flow.StaveNote.STEM_UP}), new Vex.Flow.StaveNote({keys: ["Bn/4"], duration: "8", stem_direction: Vex.Flow.StaveNote.STEM_UP})];
        music21Voice0.addTickables(music21Voice0Notes);

    ::

        >>> print(vexflow.fromObject(trebleVoice))
        var music21Voice0 = new Vex.Flow.Voice({num_beats: 4.0, beat_value: 4, resolution: Vex.Flow.RESOLUTION});
        var music21Voice0Notes = [new Vex.Flow.StaveNote({keys: ["An/4"], duration: "q", stem_direction: Vex.Flow.StaveNote.STEM_UP}), new Vex.Flow.StaveNote({keys: ["Bn/4"], duration: "q", stem_direction: Vex.Flow.StaveNote.STEM_UP}), new Vex.Flow.StaveNote({keys: ["C#/5"], duration: "q", stem_direction: Vex.Flow.StaveNote.STEM_UP}).addArticulation(0, new Vex.Flow.Articulation("a@a").setPosition(3)), new Vex.Flow.StaveNote({keys: ["En/5"], duration: "q", stem_direction: Vex.Flow.StaveNote.STEM_UP})];
        music21Voice0.addTickables(music21Voice0Notes);

    ::

        >>> #print vexflow.fromObject(soprano)
        >>> #print vexflow.fromObject(bwv666)
        >>> #print vexflow.fromObject(converter.parse("tinynotation: 3/4 E4 r f# g=lastG b-8 a g c4~ c"), mode='txt') 

    '''
    if 'Note' in thisObject.classes:
        return fromNote(thisObject, mode)
    elif 'Pitch' in thisObject.classes:
        return fromNote(note.Note(thisObject), mode)
    elif 'Rest' in thisObject.classes:
        return fromRest(thisObject, mode)
    elif 'Chord' in thisObject.classes:
        return fromChord(thisObject, mode)
    elif 'Measure' in thisObject.classes:
        return fromMeasure(thisObject, mode)
    elif 'Voice' in thisObject.classes:
        return fromMeasure(thisObject, mode)
    elif 'Part' in thisObject.classes:
        return fromPart(thisObject, mode)
    elif 'Score' in thisObject.classes:
        return fromScore(thisObject, mode)
    elif 'Stream' in thisObject.classes:
        return fromStream(thisObject, mode)
    else:
        raise Vexflow21UnsupportedException('Unsupported object type: ' + str(thisObject))


def fromScore(thisScore, mode='txt'):
    '''
    Parses a music21 score into VexFlow code

    ::

        >>> a = corpus.parse('bwv66.6')
        >>> #print vexflow.fromScore(a, mode='txt') 
    
    '''
    if mode not in supportedDisplayModes:
        raise Vexflow21UnsupportedException('Unsupported mode: ' + str(mode))

    return VexflowScore(thisScore.makeNotation(inPlace=False)).generateCode(mode)


def fromStream(thisStream, mode='txt'):
    '''
    Parses a music21 stream into VexFlow code

    Checks if it has parts. If so, parses like a Score.
    Otherwise, just flattens it and parses it like a Part
    
    ::

        >>> #print vexflow.fromStream(converter.parse('tinynotation: c8 d8 e-4 dd4 cc2'), mode='txt')
        >>> #print vexflow.fromStream(converter.parse('tinynotation: C8 D8 E-4 d4 c2'), mode='txt')

    '''
    if mode not in supportedDisplayModes:
        raise Vexflow21UnsupportedException('Unsupported mode: ' + str(mode))

    theseParts = thisStream.getElementsByClass('Part')
    if len(theseParts) == 0:
        return VexflowPart(stream.Part(thisStream.flat).makeNotation(inPlace=False)).generateCode(mode)
    return VexflowScore(stream.Score(thisStream).makeNotation(inPlace=False)).generateCode(mode)

def fromRest(thisRest, mode='txt'):
    '''
    Parses a music21 rest into VexFlow code:

    :: 

        >>> a = note.Rest()
        >>> print(vexflow.fromRest(a, mode='txt'))
        new Vex.Flow.StaveNote({keys: ["b/4"], duration: "qr"})

    ::

        >>> print(vexflow.fromRest(a, mode='html'))
        <!DOCTYPE HTML>
        <html>
        <head>
            <meta name='author' content='Music21' />
            <script src='http://code.jquery.com/jquery-latest.js'></script>
            <script src='http://www.vexflow.com/support/vexflow-min.js'></script>
        </head>
        <body>
            <canvas width="525" height="120" id='music21canvas'></canvas>
            <script>
                $(document).ready(function(){
                    var canvas = $('#music21canvas')[0];
                    var renderer = new Vex.Flow.Renderer(canvas, Vex.Flow.Renderer.Backends.CANVAS);
                    var ctx = renderer.getContext();
                    var stave = new Vex.Flow.Stave(10,0,500);
                    stave.addClef('treble').setContext(ctx).draw();
                    var notes = [new Vex.Flow.StaveNote({keys: ["b/4"], duration: "qr"})];
                    var voice = new Vex.Flow.Voice({
                        num_beats: 1.0,
                        beat_value: 4,
                        resolution: Vex.Flow.RESOLUTION
                    });
                    voice.addTickables(notes);
                    var formatter = new Vex.Flow.Formatter()
                    formatter.joinVoices([voice])
                    formatter.format([voice], 500);
                    voice.draw(ctx, stave);
                });
        </script>
        </body>
        </html>

    '''
    if mode not in supportedDisplayModes:
        raise Vexflow21UnsupportedException('Unsupported mode: ' + str(mode))
    return VexflowRest(thisRest).generateCode(mode)


def fromNote(thisNote, mode='txt'):
    '''
    Parses a music21 note into VexFlow string code:
    
    ::
    
        >>> print(vexflow.fromNote(note.Note('C4'), mode='txt'))
        new Vex.Flow.StaveNote({keys: ["Cn/4"], duration: "q"})

    See VexFlowNote.generateCode() for an example of mode='html'.
    '''
    if mode not in supportedDisplayModes:
        raise Vexflow21UnsupportedException('Unsupported mode: ' + str(mode))
    return VexflowNote(thisNote).generateCode(mode)


def fromChord(thisChord, mode='txt'):
    '''
    Parses a music21 chord into VexFlow code:

    ::

        >>> a = chord.Chord(['C3', 'E-3', 'G3', 'C4'])
        >>> print(vexflow.fromChord(a, mode='txt'))
        new Vex.Flow.StaveNote({keys: ["Cn/3", "Eb/3", "Gn/3", "Cn/4"], duration: "q"})

    ::

        >>> print(vexflow.fromChord(a, mode='jsbody'))
        var canvas = $('#music21canvas')[0];
        var renderer = new Vex.Flow.Renderer(canvas, Vex.Flow.Renderer.Backends.CANVAS);
        var ctx = renderer.getContext();
        var stave = new Vex.Flow.Stave(10,0,500);
        stave.addClef('treble').setContext(ctx).draw();
        var notes = [new Vex.Flow.StaveNote({keys: ["Cn/3", "Eb/3", "Gn/3", "Cn/4"], duration: "q"})];
        var voice = new Vex.Flow.Voice({
            num_beats: 1.0,
            beat_value: 4,
            resolution: Vex.Flow.RESOLUTION
        });
        voice.addTickables(notes);
        var formatter = new Vex.Flow.Formatter()
        formatter.joinVoices([voice])
        formatter.format([voice], 500);
        voice.draw(ctx, stave);

    ::

        >>> print(vexflow.fromChord(a, mode='html'))
        <!DOCTYPE HTML>
        <html>
        <head>
            <meta name='author' content='Music21' />
            <script src='http://code.jquery.com/jquery-latest.js'></script>
            <script src='http://www.vexflow.com/support/vexflow-min.js'></script>
        </head>
        <body>
            <canvas width="525" height="120" id='music21canvas'></canvas>
            <script>
                $(document).ready(function(){
                    var canvas = $('#music21canvas')[0];
                    var renderer = new Vex.Flow.Renderer(canvas, Vex.Flow.Renderer.Backends.CANVAS);
                    var ctx = renderer.getContext();
                    var stave = new Vex.Flow.Stave(10,0,500);
                    stave.addClef('treble').setContext(ctx).draw();
                    var notes = [new Vex.Flow.StaveNote({keys: ["Cn/3", "Eb/3", "Gn/3", "Cn/4"], duration: "q"})];
                    var voice = new Vex.Flow.Voice({
                        num_beats: 1.0,
                        beat_value: 4,
                        resolution: Vex.Flow.RESOLUTION
                    });
                    voice.addTickables(notes);
                    var formatter = new Vex.Flow.Formatter()
                    formatter.joinVoices([voice])
                    formatter.format([voice], 500);
                    voice.draw(ctx, stave);
                });
            </script>
        </body>
        </html>

    '''
    if mode not in supportedDisplayModes:
        raise Vexflow21UnsupportedException('Unsupported mode: ' + str(mode))
    return VexflowChord(thisChord).generateCode(mode)


def fromPart(thisPart, mode='txt'):
    '''
    Parses a music21 part into VexFlow code:

    ::

        >>> a = corpus.parse('bwv66.6').parts[1]
        >>> textOut = vexflow.fromPart(a, mode='txt')

    '''
    if mode not in supportedDisplayModes:
        raise Vexflow21UnsupportedException('Unsupported mode: ' + str(mode))
    return VexflowPart(thisPart.makeNotation(inPlace=False)).generateCode(mode)


def fromMeasure(thisMeasure, mode='txt'):
    r'''
    Parses a music21 measure into VexFlow code:

    ::

        >>> b = corpus.parse('bwv1.6.mxl')
        >>> m = b.parts[0].measures(0,1)[2]
        >>> d = vexflow.fromMeasure(m)
        >>> print(d)
        var music21Voice0 = new Vex.Flow.Voice({num_beats: 4.0, beat_value: 4, resolution: Vex.Flow.RESOLUTION});
        var music21Voice0Notes = [new Vex.Flow.StaveNote({keys: ["Gn/4"], duration: "8", stem_direction: Vex.Flow.StaveNote.STEM_UP}), new Vex.Flow.StaveNote({keys: ["Cn/4"], duration: "8", stem_direction: Vex.Flow.StaveNote.STEM_UP}), new Vex.Flow.StaveNote({keys: ["Fn/4"], duration: "8", stem_direction: Vex.Flow.StaveNote.STEM_UP}), new Vex.Flow.StaveNote({keys: ["Fn/3"], duration: "8", stem_direction: Vex.Flow.StaveNote.STEM_UP}), new Vex.Flow.StaveNote({keys: ["An/3"], duration: "8", stem_direction: Vex.Flow.StaveNote.STEM_UP}), new Vex.Flow.StaveNote({keys: ["Fn/3"], duration: "8", stem_direction: Vex.Flow.StaveNote.STEM_UP}), new Vex.Flow.StaveNote({keys: ["An/3"], duration: "8", stem_direction: Vex.Flow.StaveNote.STEM_UP}), new Vex.Flow.StaveNote({keys: ["Cn/4"], duration: "8", stem_direction: Vex.Flow.StaveNote.STEM_UP})];
        music21Voice0.addTickables(music21Voice0Notes);

    ::

        >>> c = vexflow.fromMeasure(m, 'html')
        >>> assert(c.split('\n')[1] == '<html>') #_DOCS_HIDE

    '''

    if mode not in supportedDisplayModes:
        raise Vexflow21UnsupportedException('Unsupported mode: ' + str(mode))
    
    notationMeasure = thisMeasure.makeNotation(inPlace=False)
    vfv = VexflowVoice(notationMeasure)
    return vfv.generateCode(mode)

def vexflowClefFromClef(music21clef):
    '''
    Given a music21 clef object, returns the vexflow clef:

    :: 

        >>> vexflow.vexflowClefFromClef(clef.TrebleClef())
        'treble'

    ::

        >>> vexflow.vexflowClefFromClef(clef.BassClef())
        'bass'

    ::

        >>> vexflow.vexflowClefFromClef(clef.TenorClef())
        'tenor'

    ::

        >>> vexflow.vexflowClefFromClef(clef.AltoClef())
        'alto'

    ::

        >>> vexflow.vexflowClefFromClef(clef.Treble8vbClef())
        'bass'

    ::

        >>> vexflow.vexflowClefFromClef(clef.PercussionClef())
        'percussion'

    ::

        >>> vexflow.vexflowClefFromClef(clef.GClef())
        'treble'

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
        raise VexFlowUnsupportedException('Vexflow only supports the ' +\
            'following clefs: treble, bass, alto, tenor, percussion. ' +\
            'Cannot parse ', music21clef)


#-------------------------------------------------------------------------------
# primitives...


class VexflowObject(object):
    '''
    A general class for all VexflowObjects to inherit from.

    See specific objects such as :class:`~music21.vexflow.VexflowNote`,
    :class:`~music21.vexflow.VexflowChord`, and 
    :class:`~music21.vexflow.VexflowRest` for more details.
    '''
    def __init__(self, music21Object = None, clef=None):
        self.originalObject = music21Object
        self.beamStart = False
        self.beamStop = False
        self.tieStart = False
        self.tieStop = False
        self.clef = clef
        self.indent = " "*4
        self.clefContext = None
        self.setBeamStatus()
        self.setTieStatus()

    def getVoiceString(self, numBeats, voiceName = 'voice', currentIndentLevel=3):
        '''
        Returns a string creating a new Vex.Flow.Voice with the number of beats
        at the current indentation level:
        
        :: 

            >>> vo = vexflow.VexflowObject()
            >>> print(vo.getVoiceString(2.0).rstrip())
                    var voice = new Vex.Flow.Voice({
                        num_beats: 2.0,
                        beat_value: 4,
                        resolution: Vex.Flow.RESOLUTION
                    });

        ::

            >>> print(vo.getVoiceString(3.0, voiceName='myVoice', currentIndentLevel = 0).rstrip())
            var myVoice = new Vex.Flow.Voice({
                num_beats: 3.0,
                beat_value: 4,
                resolution: Vex.Flow.RESOLUTION
            });

        '''
        result = """\
var {voiceName} = new Vex.Flow.Voice({{
    num_beats: {numBeats},
    beat_value: 4,
    resolution: Vex.Flow.RESOLUTION
}});\
        """.format(voiceName=voiceName, 
                   numBeats = str(numBeats))
        return indent.indent(result, self.indent*currentIndentLevel)

    def staveDefaultClefAddString(self):
        return "stave.addClef('{defaultStaveClef}').setContext(ctx).draw();".format(defaultStaveClef=defaultStaveClef)

    def generateCode(self, mode="txt"):
        '''
        Returns the VexFlow code for a single note in the desired display mode.

        Currently supported modes are `txt` (returns the VexFlow code which can be used in conjunction with
        other VexFlow code) and `html` (returns standalone HTML code for displaying just this note.)

        >>> n = note.Note('C-')
        >>> v = vexflow.VexflowNote(n)
        >>> v.generateCode('txt')
        'new Vex.Flow.StaveNote({keys: ["Cb/4"], duration: "q"})'

        >>> print(v.generateCode('jsbody'))
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
        var formatter = new Vex.Flow.Formatter()
        formatter.joinVoices([voice])
        formatter.format([voice], 500);
        voice.draw(ctx, stave);

        >>> print(v.generateCode('html'))
        <!DOCTYPE HTML>
        <html>
        <head>
            <meta name='author' content='Music21' />
            <script src='http://code.jquery.com/jquery-latest.js'></script>
            <script src='http://www.vexflow.com/support/vexflow-min.js'></script>
        </head>
        <body>
            <canvas width="525" height="120" id='music21canvas'></canvas>
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
                    var formatter = new Vex.Flow.Formatter()
                    formatter.joinVoices([voice])
                    formatter.format([voice], 500);
                    voice.draw(ctx, stave);
                });
            </script>
        </body>
        </html>
        '''
        if mode not in supportedDisplayModes:
            raise Vexflow21UnsupportedException("VexFlow doesn't support this "\
                + "display mode yet. " + str(mode))

        if mode == 'txt':
            return self.vexflowCode()
        elif mode == 'jsbody':
            return self.jsBodyCode()
        elif mode == 'html':
            result = htmlPreamble
            result += self.jsBodyCode()
            result += htmlConclusion
            return result

    def jsBodyCode(self):
        result = """
{defaultStaff}
{staveDefaultClef}
var notes = [{vexflowCode}];
{voiceString}
voice.addTickables(notes);
var formatter = new Vex.Flow.Formatter()
formatter.joinVoices([voice])
formatter.format([voice], {defaultStaveWidth});
voice.draw(ctx, stave);""".format(defaultStaff=staffString(),
                   staveDefaultClef=self.staveDefaultClefAddString(),
                   vexflowCode=self.vexflowCode(),
                   voiceString=self.getVoiceString(self.originalObject.duration.quarterLength, currentIndentLevel=0),
                   defaultStaveWidth=defaultStaveWidth)
        return vexflowPreamble + "\n" + result

    def stemDirectionCode(self):
        '''
        Gets the Vexflow StemDirection String:
        
        >>> n = note.Note()
        >>> vfn = vexflow.VexflowNote(n)
        >>> vfn.stemDirectionCode()
        ''

        >>> n.stemDirection = 'up'
        >>> vfn.stemDirectionCode()
        'stem_direction: Vex.Flow.StaveNote.STEM_UP'
        '''
        
        if self.originalObject.stemDirection == 'up':
            stemCode = 'Vex.Flow.StaveNote.STEM_UP'
        elif self.originalObject.stemDirection == 'down':
            stemCode = 'Vex.Flow.StaveNote.STEM_DOWN'
        else:
            return ''
        return 'stem_direction: ' + stemCode
        
    def setBeamStatus(self):
        '''
        Set the beamStatus for a note by setting beamStart to True, beamStop
        to True, or neither.
        '''
        if hasattr(self.originalObject, 'beams') is False:
            return

        if self.originalObject.beams and 'start' in self.originalObject.beams.getTypes():
            self.beamStart = True
        elif self.originalObject.beams and 'stop' in self.originalObject.beams.getTypes():
            self.beamStop = True

    def setTieStatus(self):
        '''
        Set the tieStatus for a note by setting tieStart to True, tieStop to 
        True, or neither.
        '''
        if hasattr(self.originalObject, 'tie') is False:
            return
        if self.originalObject.tie and self.originalObject.tie.type == 'start':
            self.tieStart = True
        elif self.originalObject.tie and self.originalObject.tie.type == 'stop':
            self.tieStop = True

    def dotCode(self):
        '''
        Generates VexFlow code for the number of dots in the object.
        
        Currently Vexflow's layout engine only supports single dotted notes however!
        
        :: 

            >>> n = note.Note()
            >>> n.duration.dots = 1
            >>> vn = vexflow.VexflowNote(n)
            >>> vn.dotCode()
            '.addDotToAll()'

        '''
        return '.addDotToAll()' * self.originalObject.duration.dots

    def fermataCode(self):
        '''
        Returns a string of Vexflow code if there is a fermata and '' if not.

        :: 

            >>> n = note.Note()
            >>> n.expressions.append(expressions.Fermata())
            >>> vn = vexflow.VexflowNote(n)
            >>> vn.fermataCode()
            '.addArticulation(0, new Vex.Flow.Articulation("a@a").setPosition(3))'

        '''
        fermataString = ''
        for thisExpression in  self.originalObject.expressions:
            if 'Fermata' in thisExpression.classes:
                #"a@a" = fermata above staff. "a@u" = fermata below staff
                #setPosition(3) means place this fermata above the staff
                #setPosition(4) would put it below the staff
                fermataString += '.addArticulation(0, new Vex.Flow.Articulation("a@a").setPosition(3))' 
        return fermataString

    def accidentalCode(self, pitch=None, index=0):
        '''
        Returns code to add an accidental to a Vex.Flow.Note or key.

        Index refers to the pitch within a chord to be altered (0 for notes).
        '''
        if pitch is None:
            try:
                acc = self.originalObject.pitch.accidental
                if acc is None:
                    return ''
                pitch = self.originalObject.pitch
            except:
                return ''
        if pitch.accidental is not None:
            displayStatus = pitch.accidental.displayStatus
        else:
            return ''
        
        if displayStatus is not None and displayStatus != False:
            if pitch.accidental.alter in alterationToVexflowAccidental:
                thisVexflowAccidental =\
                     alterationToVexflowAccidental[pitch.accidental.alter]
            else:
                raise VexFlowUnsupportedException("VexFlow doesn't support "\
                    + "this accidental type. " + str(pitch.accidental.fullName))
            
            return '.addAccidental(' + str(index) + ', new Vex.Flow.Accidental("' +\
                 thisVexflowAccidental + '"))'
        else:
            return ''

    def vexflowKey(self, clef = None, usePitch=None):
        '''
        Generate a VexFlow Key from self.originalObject.
        
        Since a VexFlow key is the position on a staff, we need to know the
        current clef in order to give a key.  The key is a position as if
        the clef were treble clef.
        
        Why the accidental is included is beyond me, since it is rendered
        separately, it might store information actual pitch, but that's
        weird since we're storing a position as if it's treble clef.
        
        If usePitch is given then we use this pitch instead of self.originalObject,
        which is needed for iterating through chord pitches
        
        If clef is None then we look at self.clefContext for more information,
        otherwise treble is assumed.  Clef is a Vexflow clef name #TODO: CHANGE THIS!
        
        ::
            >>> vfn1 = vexflow.VexflowNote(note.Note('C4'))
            >>> vfn1
            <music21.vexflow.VexflowNote object at 0x...>

        ::

            >>> vfn1.vexflowKey() #'treble')
            'Cn/4'

        ::

            >>> vfn2 = vexflow.VexflowNote(note.Note('C4'))
            >>> vfn2.vexflowKey('bass')
            'An/5'

        ::
            
            >>> c = chord.Chord(['C4','G#4','E-5'])
            >>> vfc = vexflow.VexflowChord(c)
            >>> vfc.vexflowKey('treble', c.pitches[0])
            'Cn/4'

        ::

            >>> vfc.vexflowKey('treble', c.pitches[1])
            'G#/4'

        ::

            >>> vfc.vexflowKey('treble', c.pitches[2])
            'Eb/5'

        '''
        if clef is None:
    #        if self.clefContext is not None:
    #            clef = self.clefContext
    #        else:
                clef = 'treble'
        if usePitch is not None:
            thisPitch = usePitch
        elif 'Pitch' in self.originalObject.classes:
            thisPitch = self.originalObject
        elif 'Note' in self.originalObject.classes:
            thisPitch = self.originalObject.pitch
        elif 'Rest' in self.originalObject.classes:
            thisPitch = pitch.Pitch('B')
        if thisPitch is None:
            raise Exception("what???")
    
        thisAccidental = thisPitch.accidental
        if thisAccidental != None:
            if thisAccidental.alter in alterationToVexflowAccidental:
                thisVexflowAccidental =\
                     alterationToVexflowAccidental[thisAccidental.alter]
            else:
                raise VexFlowUnsupportedException("VexFlow doesn't support "\
                    + "this accidental type. " + str(thisAccidental.fullName))
        else:
            thisVexflowAccidental = 'n'
    
        if clef == 'treble':
            pass
        elif clef == 'bass':
            #Vexflow renders all notes as if on treble clef, regardless of actual
            #    clef
            thisPitch = thisPitch.transpose('m13')
    
        thisPitchName = thisPitch.step
        thisPitchOctave = thisPitch.implicitOctave
        thisKey = '{p}{a}/{o}'.format(p=thisPitchName,
                                      a=thisVexflowAccidental,
                                      o=str(thisPitchOctave))
        return thisKey

    def vexflowDuration(self):
        '''
        Given a music21 Note (or Pitch) object, returns the vexflow duration.
    
        ::

            >>> n = note.Note()
            >>> vfn = vexflow.VexflowNote(n)
            >>> vfn.vexflowDuration()
            'q'

        ::

            >>> n.quarterLength = 0.75
            >>> vfn.vexflowDuration()
            '8d'

        '''
        m21Duration = self.originalObject.duration
    
        thisQuarterLength = m21Duration.quarterLength
        if thisQuarterLength == 0:
            thisQuarterLength = defaultNoteQuarterLength
        
        if thisQuarterLength in vexflowQuarterLengthToDuration:
            return vexflowQuarterLengthToDuration[thisQuarterLength]
        else:
            raise VexFlowUnsupportedException("VexFlow doesn't support this "\
                + "duration. " + str(m21Duration.fullName))


class VexflowNote(VexflowObject):
    '''
    A VexflowNote object has a .generateCode() method which produces VexFlow 
    code to represent a :class:`music21.note.Note` object.

    TODO: Verify that I'm not overwriting any base attribute names of music21

    TODO: add setters/getters

    TODO: __str__

    ::

        >>> n = note.Note('C-')
        >>> v = vexflow.VexflowNote(n)
        >>> v.vexflowKey()
        'Cb/4'

    ::

        >>> v.vexflowDuration()
        'q'

    ::

        >>> v.vexflowCode()
        'new Vex.Flow.StaveNote({keys: ["Cb/4"], duration: "q"})'

    ::

        >>> n = converter.parse('tinynotation: c##2.').flat.notes[0]
        >>> n.stemDirection = 'up'
        >>> v = vexflow.VexflowNote(n)
        >>> v.vexflowKey()
        'C##/4'

    ::

        >>> v.vexflowDuration()
        'hd'

    ::

        >>> v.stemDirectionCode()
        'stem_direction: Vex.Flow.StaveNote.STEM_UP'

    ::

        >>> v.vexflowCode()
        'new Vex.Flow.StaveNote({keys: ["C##/4"], duration: "hd", stem_direction: Vex.Flow.StaveNote.STEM_UP}).addDotToAll()'

    '''

    def __init__(self, music21note = None, clef=None):
        '''
        music21note must be a :class:`music21.note.Note` object.
        '''
        VexflowObject.__init__(self, music21note, clef)
        #TODO tuplet: add variables for if it's the start of a tuplet
        #self.isTuplet = False
        #self.tupletLength = 0

    def vexflowCode(self):
        '''
        returns a string representing the vexflow code for this note
        '''
        vexflowCode = 'new Vex.Flow.StaveNote({'
        staveParameters = []
        staveParameters.append('keys: ["' + self.vexflowKey(self.clef) + '"]')
        staveParameters.append('duration: "' + self.vexflowDuration() + '"')
        sdc = self.stemDirectionCode()
        if sdc:
            staveParameters.append(sdc)
        vexflowCode += ', '.join(staveParameters)
        
        vexflowCode += '})'

        vexflowCode += self.accidentalCode()
        vexflowCode += self.fermataCode()        
        vexflowCode += self.dotCode()
        return vexflowCode


class VexflowChord(VexflowObject):
    '''
    A simultaneous grouping of notes.

    TODO: __str__ should just call the str() method on the original notes
    TODO: Also store original notes as Chord object
    TODO: write unit tests
    '''

    def __init__(self, music21Chord = None, clef=None):
        '''
        Notes must be an array_like grouping of either Music21 or VexFlow Notes.
        Notes can instead be a music21.chord.Chord object.
        '''
#        try:
#            if 'Chord' not in notes.classes:
#                raise Vexflow21UnsupportedException, 'Cannot create a Chord from'\
#                     + str(notes)
#            self.originalObject = notes
#        except AttributeError:
#            if not hasattr(notes, '__contains__'):
#                raise TypeError, 'notes must be a chord.Chord object or an ' +\
#                    'iterable collection of notes'
#            assert len(notes) > 0, 'cannot create an empty VexflowChord'
#            self.originalObject = chord.Chord(notes)
        VexflowObject.__init__(self, music21Chord, clef)

        #TODO tuplet: add variables for if it's the start of a tuplet
        #self.isTuplet = False
        #self.tupletLength = 0

    def vexflowCode(self):
        '''
        Returns a string showing the vexflow code needed to display this chord in a browser.
        '''
        
        #TODO tuplet: set the tuplet variables here
        vexflowCode = 'new Vex.Flow.StaveNote({'

        keyList = []
        currentClef = self.clef
        for thisPitch in self.originalObject.pitches:
            keyList.append('"' + self.vexflowKey(currentClef, thisPitch) + '"')
        pitchCode = ', '.join(keyList)
        staveParameters = []
        staveParameters.append('keys: [' + pitchCode + ']')
        staveParameters.append('duration: "' + self.vexflowDuration() + '"')
        sdc = self.stemDirectionCode()
        if sdc:
            staveParameters.append(sdc)        
        vexflowCode += ', '.join(staveParameters)
        vexflowCode += '})'

        vexflowCode += self.fermataCode()
        
        accidentalList = []
        for i in range(len(self.originalObject.pitches)):
            accidentalList += self.accidentalCode(pitch = self.originalObject.pitches[i], index=i) 
        vexflowCode += ''.join(accidentalList)
        vexflowCode += self.dotCode()
        return vexflowCode
    
        
class VexflowRest(VexflowObject):
    '''
    Class for representing rests in VexFlow.
    '''

    def __init__(self, music21rest = None, clef=None):
        '''
        music21rest must be a :class:`music21.note.Rest` object.

        position is where the rest should appear on the staff
            'b/4' is the middle of the treble clef
        '''
        VexflowObject.__init__(self, music21rest, clef)
        #TODO tuplet: add variables for if it's the start of a tuplet
        #self.isTuplet = False
        #self.tupletLength = 0
        #self._generateVexflowCode()

    def vexflowCode(self):
        '''
        Returns a string which is the generated the vexflow code needed to render this rest object.

        ::

            >>> r = note.Rest()
            >>> vr = vexflow.VexflowRest(r)
            >>> vr.vexflowCode()
            'new Vex.Flow.StaveNote({keys: ["b/4"], duration: "qr"})'

        '''
        vexflowCode = 'new Vex.Flow.StaveNote({'
        vexflowCode += 'keys: ["b/4"], '
        vexflowCode += 'duration: "' + self.vexflowDuration() + 'r"})'

        vexflowCode += self.fermataCode()        
        vexflowCode += self.dotCode()        
        return vexflowCode


#--------------containers----------------------------------#
#         from smallest to largest                         #


class VexflowVoice(object):
    '''
    A Voice in VexFlow is a "lateral" grouping of notes in one measure
    It's the equivalent to a :class:`~music21.stream.Measure`.

    Requires either a :class:`~music21.stream.Measure` object or a 
    :class:`~music21.stream.Voice` object.

    If those objects aren't already flat, flattens them in the process. 

    `params` is a dict containing various parameters to be passed to the 
    voice object.  Most important is the UIDCounter parameter which keeps
    track of the number of objects created.
    '''
    
    def __init__(self, music21measure = None, params={}):
        if music21measure != None:
            if not ('Measure' in music21measure.classes or \
                'Voice' in music21measure.classes):
                raise TypeError('must pass a music21 Measure object')
            self.originalMeasure = music21measure
            self.originalFlat = music21measure.flat
        else:
            self.originalMeasure = stream.Measure()
            self.originalFlat = self.originalMeasure.flat

        self.indent = " "*4
   
        self.params = params
        
        self._vexflowObjects = None
        self._beamPreamble = None
        self._beamPost = None
        
        self.clefDisplayStatus = defaultClefDisplayStatus
        self.keySignatureDisplayStatus = defaultKeySignatureDisplayStatus

        if 'UIDCounter' in self.params:
            self.UIDCounter = self.params['UIDCounter']
            self.UID = self.UIDCounter.readAndIncrement()
        else:
            self.UIDCounter = UIDCounter()
            self.UID = 0


        if 'name' in self.params:
            self.voiceName = self.params['name']
        else:
            self.voiceName = 'music21Voice' + str(self.UID)
            self.params['name'] = self.voiceName

        #if 'octaveModifier' not in self.params:
            #Used for bass clef
            #self.params['octaveModifier'] = 0

        #Set the clef
        theseClefs = self.originalFlat.getElementsByClass('Clef')
        if len(theseClefs) > 1:
            raise Vexflow21UnsupportedException('Vexflow cannot yet handle ' +\
                'multiple clefs in a single measure')
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
        theseKeySignatures = self.originalFlat.getElementsByClass('KeySignature')
        if len(theseKeySignatures) > 1:
            raise Vexflow21UnsupportedException('Vexflow cannot yet handle ' +\
                'multiple key signatures in a single measure')
        elif len(theseKeySignatures) == 1:
            self.keySignatureDisplayStatus = True
            if theseKeySignatures[0].sharps in vexflowSharpsToKeySignatures:
                self.keySignature = \
                    vexflowSharpsToKeySignatures[theseKeySignatures[0].sharps]
            else:
                raise VexFlowUnsupportedException("VexFlow doesn't support this "+\
                    'Key Signature:', theseKeySignatures[0])
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
        theseTimeSignatures = self.originalFlat.getElementsByClass('TimeSignature')
        if len(theseTimeSignatures) > 1:
            raise Vexflow21UnsupportedException('Vexflow cannot yet handle ' +\
                'multiple time signatures in a single measure')
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

    def voiceCode(self):
        '''
        Creates the code to create a new voice object with the
        name stored in ``self.voiceName``.
        
        ::        

            >>> s = stream.Measure()
            >>> s.append(note.Note('c4'))
            >>> s.append(note.Note('d4'))
            >>> vfv = vexflow.VexflowVoice(s)
            >>> vfv.voiceName = 'myVoice'
            >>> vfv.voiceCode()
            'var myVoice = new Vex.Flow.Voice({num_beats: 2.0, beat_value: 4, resolution: Vex.Flow.RESOLUTION});'

        '''
        
        return """var {vn} = new Vex.Flow.Voice({{num_beats: {nb}, beat_value: {bv}, resolution: Vex.Flow.RESOLUTION}});""".format(vn=str(self.voiceName),
                                                                                                                                 nb=str(self.numBeats),
                                                                                                                                 bv=str(self.beatValue))
    def vexflowObjects(self):
        '''
        Returns a list of all the ``notesAndRests`` in the ``originalMeasure``
        represented as ``VexflowObjects``.

        ::
 
            >>> s = stream.Measure()
            >>> s.append(note.Note('c4'))
            >>> s.append(note.Note('d4'))
            >>> vfv = vexflow.VexflowVoice(s)
            >>> vfv.vexflowObjects()
            [<music21.vexflow.VexflowNote object at 0x...>, <music21.vexflow.VexflowNote object at 0x...>]

        '''
        if self._vexflowObjects is not None:
            return self._vexflowObjects
        else:
            vfo = []
            for thisObject in self.originalFlat.notesAndRests:
                if 'Note' in thisObject.classes:
                    thisVexflowObj = VexflowNote(thisObject, clef = self.clef)
                elif 'Chord' in thisObject.classes:
                    thisVexflowObj = VexflowChord(thisObject, clef = self.clef)
                elif 'Rest' in thisObject.classes:
                    thisVexflowObj = VexflowRest(thisObject, clef= self.clef)
                else:
                    raise Exception("what is it? %s" % thisObject)
                vfo.append(thisVexflowObj)
            self._vexflowObjects = vfo
            return vfo
    
    def notesCode(self):
        '''
        Note the plural. Generates an String that is a Javascript array
        of all the vexflow notes in a measure:

        ::

            >>> s = stream.Measure()
            >>> s.append(note.Note('c4'))
            >>> s.append(note.Note('d4'))
            >>> vfv = vexflow.VexflowVoice(s)
            >>> vfv.voiceName = 'myVoice'
            >>> vfv.notesCode()
            'var myVoiceNotes = [new Vex.Flow.StaveNote({keys: ["Cn/4"], duration: "q"}), new Vex.Flow.StaveNote({keys: ["Dn/4"], duration: "q"})];'

        '''
        notes = []
        for thisVexflowObj in self.vexflowObjects():
            notes.append(thisVexflowObj.vexflowCode())
        noteName = self.voiceName + 'Notes'
        noteCode = 'var ' + noteName + ' = [' + ', '.join(notes) + '];'
        return noteCode

    def vexflowCode(self):
        '''
        Returns a string that generates the code necessary to display this voice.

        ::

            >>> s = stream.Measure()
            >>> s.append(note.Note('c4'))
            >>> s.append(note.Note('d4'))
            >>> vfv = vexflow.VexflowVoice(s)
            >>> vfv.voiceName = 'myVoice'
            >>> print(vfv.vexflowCode())
            var myVoice = new Vex.Flow.Voice({num_beats: 2.0, beat_value: 4, resolution: Vex.Flow.RESOLUTION});
            var myVoiceNotes = [new Vex.Flow.StaveNote({keys: ["Cn/4"], duration: "q"}), new Vex.Flow.StaveNote({keys: ["Dn/4"], duration: "q"})];
            myVoice.addTickables(myVoiceNotes);

        '''
        return self.voiceCode() + '\n' +\
               self.notesCode() + '\n' +\
               str(self.voiceName) + '.addTickables(' + str(self.voiceName) + \
               'Notes);'

    def getBeaming(self):
        '''
        Beaming is a boolean value determining if the voice should be beamed

        .. note:: So far only VexFlow's automatic beaming is supported.
                  We cannot manually modify beams.
        '''
        return self.params['beaming']

    def _beamCode(self, contextName = 'ctx', indentation=3):
        '''
        Returns the preamble and the postamble code for the beams for this voice.

        Returns it as an array containing the beam preamble and postamble.

        Will return code even if it shouldn't be beamed.
        Check self.getBeaming() before applying this.
        '''
        if self._beamPreamble is not None and self._beamPost is not None:
            return [self._beamPreamble, self._beamPost]
        
        baseBeamName = str(self.voiceName) + 'Beam'
        noteGroupName = str(self.voiceName) + 'Notes'
        preamble = ''
        postamble = ''

        theseBeams = []
        beamStartIndex = None
        for index, thisVexflowObj in enumerate(self.vexflowObjects()):
            if not isinstance(thisVexflowObj, VexflowRest):
                if beamStartIndex is None and thisVexflowObj.beamStart:
                    beamStartIndex = index
                elif beamStartIndex is not None and thisVexflowObj.beamStop:
                    beamInfo = (beamStartIndex, index)
                    theseBeams.append(beamInfo)
                    beamStartIndex = None

        for index in range(len(theseBeams)):
            thisBeam = theseBeams[index]
            thisBeamName = baseBeamName + str(index)

            preamble += '\n' + (self.indent*indentation) + 'var ' + thisBeamName +\
                ' = new Vex.Flow.Beam('+noteGroupName+'.slice(' + str(thisBeam[0])+\
                ',' + str(thisBeam[1]+1) + '));'
            postamble += '\n' + (self.indent*indentation) + thisBeamName + \
                '.setContext(' + str(contextName) + ').draw();'

        self._beamPreamble = preamble
        self._beamPost = postamble
        
        return [preamble, postamble]
    
    def createBeamCode(self, contextName = 'ctx', indentation=3):
        '''
        Returns the code to create beams for this staff.
        '''
        return self._beamCode(contextName, indentation)[0]

    def drawBeamCode(self, contextName = 'ctx', indentation=3):
        '''
        Returns the code to draw beams on this staff.
        '''
        return self._beamCode(contextName, indentation)[1]

    
    def tieCode(self, contextName = 'ctx', indentation=3):
        '''
        Returns the code for the ties for this voice.

        Returns it as a two-element tuple containing [0] a list of code
        for the completed ties within this voice,
        and [1] a two-element array for partial ties that go across the bar line
        consisting of (0) a two-element tuple of the start index,
        and end index (None), and (1) the string name of the Note group
        to which element [0][0] belongs.
            
        N.B. Bug: Only the first index of a chord is tied.
        Returns a string that generates the code necessary to display this voice.

        ::

            >>> s = stream.Measure()
            >>> n1 = note.Note('c4')
            >>> n1.tie = tie.Tie("start")
            >>> n2 = note.Note('c4')
            >>> n2.tie = tie.Tie("stop")
            >>> s.append(n1)
            >>> s.append(n2)
            >>> vfv = vexflow.VexflowVoice(s)
            >>> vfv.voiceName = 'myVoice'
            >>> print(vfv.tieCode()[0][0])
                var myVoiceTie0 = new Vex.Flow.StaveTie({
                    first_note: myVoiceNotes[0],
                    last_note: myVoiceNotes[1],
                    first_indices: [0],
                    last_indices: [0]
                });
                myVoiceTie0.setContext(ctx).draw();

        '''
        baseTieName = str(self.voiceName) + 'Tie'
        noteGroupName = str(self.voiceName) + 'Notes'

        tieStarted = False
        theseTies = []
        thisTieStart = None

        for index, thisVexflowObj in enumerate(self.vexflowObjects()):
            if not isinstance(thisVexflowObj, VexflowRest):
                if not tieStarted and thisVexflowObj.tieStart:
                    thisTieStart = index
                    tieStarted = True
                elif not tieStarted and thisVexflowObj.tieStop:
                    #could mean tie began in previous bar
                    theseTies += [(None, index)]
                    tieStarted = False
                elif tieStarted and thisVexflowObj.tieStop:
                    theseTies += [(thisTieStart, index)]
                    tieStarted = False
            
            #TODO tuplet: if the note is the start of a tuplet, remember that it's the start of one and figure out how many
            #    Later we'll do notes.slice(indexOfStart, lengthOfTuplet)
            #    For now, we'll just throw an exception if the tuplet isn't complete

        if tieStarted:
            #Partial tie across the bar, beginning on this page
            theseTies += [(thisTieStart, None)]

        fullTies = []
        partialTies = []

        for index in range(len(theseTies)):
            (tieStartIndex, tieEndIndex) = theseTies[index]
            if tieStartIndex != None and tieEndIndex != None:
                #TODO: add support for multiple ties in a chord
                thisTieName = baseTieName + str(index)
                thisTieCode = """\
var {tn} = new Vex.Flow.StaveTie({{
    first_note: {ngn}[{tsi}],
    last_note: {ngn}[{tei}],
    first_indices: [0],
    last_indices: [0]
}});
{ttn}.setContext({cn}).draw();""".format(tn=thisTieName,
                                         ngn=noteGroupName,
                                         tsi=str(tieStartIndex),
                                         tei=str(tieEndIndex),
                                         ttn=thisTieName,
                                         cn=str(contextName))
                fullTies.append(indent.indent(thisTieCode,self.indent*indentation))
            else:
                partialTies.append([theseTies[index], noteGroupName])
        return (fullTies, partialTies)
    
    def setBeaming(self, beaming):
        '''
        Beaming is a boolean value determining if the voice should be beamed

        .. note:: So far, only VexFlow's automatic beaming is supported.
                  We cannot manually modify beams.
        '''
        self.params['beaming'] = beaming

    def generateCode(self, mode='txt'):
        '''
        Returns the vexflow code necessary to display this Voice in a browser
        as a string.
        
        >>> m = stream.Measure()
        >>> m.append(note.Note('c4', type='half'))
        >>> vfv = vexflow.VexflowVoice(m)
        >>> print(vfv.generateCode(mode="jsbody"))
                    var canvas = $('#music21canvas')[0];
                    var renderer = new Vex.Flow.Renderer(canvas, Vex.Flow.Renderer.Backends.CANVAS);
                    var ctx = renderer.getContext();
                    var stave = new Vex.Flow.Stave(10,0,500);
                    stave.addClef('treble').setContext(ctx).draw();
                    var music21Voice0 = new Vex.Flow.Voice({num_beats: 2.0, beat_value: 4, resolution: Vex.Flow.RESOLUTION});
                    var music21Voice0Notes = [new Vex.Flow.StaveNote({keys: ["Cn/4"], duration: "h"})];
                    music21Voice0.addTickables(music21Voice0Notes);
        <BLANKLINE>
                    var formatter = new Vex.Flow.Formatter().joinVoices([music21Voice0]).format([music21Voice0], 500);
                    music21Voice0.draw(ctx, stave);
        <BLANKLINE>
        '''
        if mode == 'txt':
            return self.vexflowCode()
        elif mode == 'jsbody':
            return self.jsBodyCode()
        elif mode == 'html':
            result = htmlPreamble
            result += self.jsBodyCode()
            result += htmlConclusion
            return result

    def jsBodyCode(self):
        result = vexflowPreamble
        defaultStaff = staffString()
        result += """\
{defaultStaff}
stave.addClef('{defaultStaveClef}').setContext(ctx).draw();
{vexflowCode}
{beamCode}
var formatter = new Vex.Flow.Formatter().joinVoices([{vn}]).format([{vn}], {defaultStaveWidth});
{vn}.draw(ctx, stave);
{drawBeamCode}""".format(defaultStaff=defaultStaff,
                                 defaultStaveClef=str(defaultStaveClef),
                                 vexflowCode=self.vexflowCode(),
                                 beamCode=self.createBeamCode('ctx'),
                                 vn=str(self.voiceName),
                                 defaultStaveWidth=str(defaultStaveWidth),
                                 drawBeamCode=self.drawBeamCode('ctx'))
        return indent.indent(result, self.indent*3) 

class VexflowStave(object):
    '''
    A "Stave"[sic] in VexFlow is the object for the graphic staff to be displayed.
    It usually represents a Measure that might have one or more Voices on it.
    
    TODO: ``generateCode`` should take a ``VexflowContext`` object as a param
    '''
    def __init__(self, params={}):
        '''
        ``params`` is a dictionary containing position, width, and other parameters to be passed to the stave object.
        '''
        self.params = params
        self.vexflowVoices = []
        if 'width' not in self.params:
            self.params['width'] = defaultStaveWidth
        if 'notesWidth' not in self.params:
            self.params['notesWidth'] = '(' + str(self.params['width']) +\
                ' - ' + str(defaultMeasureMargin) + ')'
        if 'position' not in self.params:
            self.params['position'] = defaultStavePosition

        if 'UIDCounter' in self.params:
            self.UIDCounter = self.params['UIDCounter']
            self.UID = self.UIDCounter.readAndIncrement()
        else:
            self.UIDCounter = UIDCounter()
            self.UID = 0

        if 'name' in self.params:
            self.staveName = self.params['name']
        else:
            self.staveName = 'music21Stave' + str(self.UID)


    
    def staveCode(self):
        '''
        JavaScript/VexFlow code for putting clefs, timeSignatures, etc. on the staff.
        '''
        
        staveCode = staffString(str(self.params['position'][0]), str(self.params['position'][1]), str(self.params['width']), self.staveName)
        for thisVoice in self.vexflowVoices:
            if 'clef' not in self.params or not self.params['clef']:
                self.params['clef'] = thisVoice.clef
            if 'timeSignature' not in self.params or not self.params['timeSignature']:
                self.params['timeSignature'] = thisVoice.timeSignature
            if 'keySignature' not in self.params or not self.params['keySignature']:
                self.params['keySignature'] = thisVoice.keySignature

        if 'clefDisplayStatus' in self.params and \
            'clef' in self.params and self.params['clefDisplayStatus']:
            staveCode += '\n' + self.staveName + '.addClef("' + \
                str(self.params['clef']) + '");'
        if 'keySignatureDisplayStatus' in self.params and 'keySignature' in self.params and self.params['keySignatureDisplayStatus']:
            staveCode += '\n' + self.staveName + '.addKeySignature("' + str(self.params['keySignature']) + '");'

        if 'timeSignature' in self.params and self.params['timeSignature']:
            staveCode += '\n' + self.staveName + '.addTimeSignature("' + str(self.params['timeSignature']) + '");'
        return staveCode
    
    def formatterCode(self):
        '''
        Code for setting up a formatter to join voices.
        '''
        if len(self.vexflowVoices) > 0:
            formatterCode = 'var ' + self.staveName + 'Formatter = ' +\
                'new Vex.Flow.Formatter().joinVoices('

            voiceList = []
            for thisVoice in self.vexflowVoices:
                voiceList.append(thisVoice.voiceName)
            voiceListStr = '[' + ', '.join(voiceList) + ']'
            formatterCode += voiceListStr + ').format(' + voiceListStr + ', ' + str(self.params['notesWidth'])  + ');'
            return formatterCode
        else:
            return ''

    def vexflowCode(self):
        # code for joining multiple voices (needed even if only one...
        
        return self.staveCode() + '\n' + self.formatterCode()
    
    def getWidth(self):
        return self.params['width']
    
    def getLineNum(self):
        '''
        Tries to get the line number of this stave.
        '''
        if 'lineNum' in self.params:
            return self.params['lineNum']
        else:
            #XXX Should I do something different here?
            return 0
    
    def beamCode(self, contextName, indentation=3):
        '''
        Generates the code for beaming all of the voices on this stave.

        Returns an array containing the preamble and postamble.
        '''
        preamble = []
        postamble = []
        for thisVoice in self.vexflowVoices:
            if thisVoice.getBeaming():
                (pre, post) = thisVoice.beamCode(contextName, \
                    indentation=indentation)
                preamble += [pre]
                postamble += [post]
        return [('\n' + ('    ' * indentation)).join(preamble), ('\n' + ('    ' * indentation)).join(postamble)]

#    def addVoice(self, thisVexflowVoice):
#        '''
#        Adds thisVexflowVoice (an instance of VexflowVoice) to this VexflowStave
#        '''
#        self.vexflowVoices += [thisVexflowVoice]
#        if 'clefDisplayStatus' not in self.params or not self.params['clefDisplayStatus']:
#            self.params['clefDisplayStatus'] = thisVexflowVoice.clefDisplayStatus
#            
#        if 'keySignatureDisplayStatus' not in self.params or not self.params['keySignatureDisplayStatus']:
#            self.params['keySignatureDisplayStatus'] = thisVexflowVoice.keySignatureDisplayStatus
#
#        #print 'Sig: %s, Display?: %s' % (self.params['keySignature'], self.params['keySignatureDisplayStatus']) #XXX k
            
    def setVoices(self, theseVexflowVoices):
        '''
        Replaces any existing voices attached to this ``Stave`` with
        ``theseVexflowVoices`` (a list of instances of ``VexflowVoice``).
        '''
        if isinstance(theseVexflowVoices, list):
            self.vexflowVoices = theseVexflowVoices
        else:
            self.vexflowVoices = [theseVexflowVoices]
            
        self.params['clef'] = defaultStaveClef
        self.params['keySignature'] = defaultStaveKeySignature
        for thisVoice in self.vexflowVoices:
            if 'clefDisplayStatus' not in self.params or (not self.params['clefDisplayStatus'] and \
                                                          'clefDisplayStatus' in thisVoice.params):
                self.params['clefDisplayStatus'] += thisVoice.params['clefDisplayStatus']
                
            if 'keySignatureDisplayStatus' not in self.params or \
                    (not self.params['keySignatureDisplayStatus'] and \
                    'keySignatureDisplayStatus' in thisVoice.params):
                self.params['keySignatureDisplayStatus'] += thisVoice.params['keySignatureDisplayStatus']

            if thisVoice.clef:
                self.params['clef'] = thisVoice.clef
            if thisVoice.keySignature:
                self.params['keySignature'] = thisVoice.keySignature

        #print 'Sig: %s, Display?: %s' % (self.params['keySignature'], self.params['keySignatureDisplayStatus']) #XXX k
    

    def generateCode(self, mode='txt'):
        '''
        Generates the vexflow code to display this staff in a browser.
        '''
        if mode == 'txt':
            return self.vexflowCode()
        elif mode == 'jsbody':
            return self.jsBodyCode()
        elif mode == 'html':
            result = htmlPreamble 
            result += self.jsBodyCode()
            result += htmlConclusion
            return result

    def jsBodyCode(self):
        result = vexflowPreamble
        drawTheseVoices = []
        drawTheseBeams = []
        for thisVoice in self.vexflowVoices:
            (beamPre, beamPost) = thisVoice.beamCode('ctx')
            result += '\n' + thisVoice.generateCode('txt')
            result += '\n' + beamPre
            drawTheseVoices += [str(thisVoice.voiceName) + '.draw(ctx, ' + str(self.staveName) + ');\n']
            if thisVoice.getBeaming():
                drawTheseBeams += [beamPost]

        result += self.vexflowCode()
        result += '\n' + str(self.staveName) + '.setContext(ctx).draw();'
        result += '\n' + ''.join(drawTheseVoices) + '\n'
        result += '\n'.join(drawTheseBeams)
        return result

class VexflowPart(object):
    '''
    A part is a wrapper for the vexflow code representing multiple measures
    of music that should go in the same musical staff (as opposed to
    a vexflow Stave).
    '''

    def __init__(self, music21part, params={}):
        self.originalPart = music21part
        self.staves = []
        self.numMeasures = 0
        self.numSystems = 0
        self.lineWidth = 0
        self.measureWidth = 0
        self.leftMargin = 0
        self.topMargin = 0
        self.systemHeight = 0
        self.vexflowCode = ''
        self.params = params
        if 'measuresPerSystem' not in self.params:
            self.params['measuresPerSystem'] = defaultMeasuresPerSystem
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

        if 'UIDCounter' in self.params:
            self.UIDCounter = self.params['UIDCounter']
            self.UID = self.UIDCounter.readAndIncrement()
        else:
            self.UIDCounter = UIDCounter()
            self.UID = 0


        self._computeParams()
        self._generateVexflowCode()

    def _computeParams(self):
        '''
        Computes parameters necessary for placing the measures in the canvas.
        '''
        self.lineWidth = '(' + str(self.params['canvasWidth']) + ' - (2*' + \
            str(self.params['canvasMargin']) + '))'
        self.measureWidth = '((' + str(self.lineWidth) + ') / ' + \
            str(self.params['measuresPerSystem']) + ')'
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
        Generates the vexflow code to display this part.
        '''
        self.numMeasures = -1
        self.numSystems = 0
        self.staves = []
        previousKeySignature = False
        for thisMeasure in self.originalPart:
            if 'Measure' not in thisMeasure.classes:
                continue
            self.numMeasures += 1
            thisXPosition = '(' + str(self.numMeasures % \
                self.params['measuresPerSystem']) + ' * ' + \
                str(self.measureWidth) + ' + ' + str(self.leftMargin) + ')'
            self.numSystems = int(self.numMeasures) / \
                int(self.params['measuresPerSystem'])
            thisYPosition = '((' + str(self.numSystems) + ' * (' + \
                str(self.systemHeight) + ' + ' + \
                str(self.params['interSystemMargin']) + ')) + ' + \
                str(self.topMargin) + ' + (' + str(self.params['partIndex']) + \
                '*(' + str(self.params['staveHeight']) + '+' +\
                str(self.params['intraSystemMargin']) + ')))'
            theseParams = {
                'width': self.measureWidth,
                'position': (thisXPosition, thisYPosition),
                'name': 'stavePart' + str(self.params['partIndex']) + 'Measure' + \
                    str(self.numMeasures) + 'Line' + str(self.numSystems) + 'ID' + \
                    str(self.UID),
                'clef': self.clef,
                'notesWidth': self.notesWidth,
                'lineNum': self.numSystems,
                'UIDCounter': self.UIDCounter,
            }
            
            #Display the clef and keySignature at the start of new lines
            isNewLine = (self.numMeasures % \
                self.params['measuresPerSystem'] == 0)
            theseParams['clefDisplayStatus'] = isNewLine
            theseParams['keySignatureDisplayStatus'] = isNewLine
            
            if previousKeySignature:
                theseParams['keySignature'] = previousKeySignature

            #if theseParams['keySignatureDisplayStatus']:
                #print "Part: %d, Measure: %d, Line: %d" % \
                    #(self.params['partIndex'], self.numMeasures, self.numSystems)

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
                for index in range(len(music21voices)):
                    thisVoice = music21voices[index]
                    voiceParams['name'] = voiceParams['name'][:-1] + str(index)
                    theseVoices += [VexflowVoice(thisVoice, \
                        params=voiceParams)]
                    try:
                        previousKeySignature = thisVoice.keySignature
                    except AttributeError: ### SHOULDNT HAPPEN
                        pass
            thisStave.setVoices(theseVoices)
            self.staves += [thisStave]

        contextParams = {
            'width': self.params['canvasWidth'],
            'height': '((' + str(self.numSystems + 1) + ' * ('+str(self.systemHeight)+\
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
        Generates the code for beaming all of the staves in this part.

        Returns as an array containing the preamble and postamble.
        '''
        preamble = []
        postamble = []
        for thisStave in self.staves:
            (pre, post) = thisStave.beamCode(contextName, indentation=indentation)
            preamble += [pre]
            postamble += [post]
        return [('\n' + ('    ' * indentation)).join(preamble), ('\n' + ('    ' * indentation)).join(postamble)]

    def generateCode(self, mode='txt'):
        '''
        Generates the vexflow code necessary to display this part in a browser.
        '''
        if mode=='txt':
            return self.vexflowCode
        elif mode == 'jsbody':
            return self.jsBodyCode()
        elif mode=='html':
            result = htmlCanvasPreamble + self.context.getCanvasHTML() + \
                htmlCanvasPostamble + '\n'
            result += self.context.getCanvasCode(indentation=3) + '\n'
            result += self.jsBodyCode()
            result += htmlConclusion
            return result
    
    def jsBodyCode(self):
        result = self.context.getRenderContextCode(indentation=3) + '\n'
        result += self.vexflowCode + '\n'
        for thisStave in self.staves:
            for thisVoice in thisStave.vexflowVoices:
                result += str(thisVoice.voiceName) + '.draw(' + \
                self.context.contextName + ', ' + \
                str(thisStave.staveName) + ');\n' + \
                str(thisStave.staveName) + '.setContext(' + \
                self.context.contextName + ').draw();'
        return result


class VexflowScore(object):
    '''
    Represents the code for multiple VexflowPart objects.
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


    def vexflowCode(self):
        '''
        Generates the code necessary to display this score.
        '''
        previousParams = {'numParts': self.numParts}
        if self.context != None:
            previousParams['context'] = self.context
            previousParams['canvasWidth'] = self.context.getWidth()

        for index in range(self.numParts):
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
        vexflowCode = self.context.getJSCode(indentation=3) + '\n'
        vexflowCode += self.partsCode
        return vexflowCode

    def jsBodyCode(self):
        vfc = self.vexflowCode() # sets too many other things currently, such as context
        result = vfc + '\n'

        tieCode = ''
        partialTies = []
        
        for thisPart in self.vexflowParts:
            for thisStave in thisPart.staves:
                for thisVoice in thisStave.vexflowVoices:
                    contextName = self.context.contextName
                    (thisTieCode, thesePartialTies) = thisVoice.tieCode(contextName)
                    thesePartialTies = [(thisPartialTie + [thisStave.getLineNum()]) for thisPartialTie in thesePartialTies]
                    tieCode += '\n'
                    tieCode += '\n'.join(thisTieCode)
                    partialTies += thesePartialTies
                    result += thisVoice.createBeamCode(contextName)
                    result += str(thisVoice.voiceName) + '.draw(' + \
                        contextName + ', ' + \
                        str(thisStave.staveName) + ');\n' + \
                        str(thisStave.staveName) + '.setContext(' + \
                        contextName + ').draw();'
                    result += thisVoice.drawBeamCode(contextName)

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
                    print('uh oh... got mixed up somewhere')
                    print(partialTies)
                    print('Ignoring')
                    tieStart = True
                    continue

                thisTieName = self.context.contextName + 'Tie' + \
                    str(tieNum)

                if thisLineNum != thisStartLineNum:
                    result +='\nvar '+thisTieName+'Start = new Vex.Flow.StaveTie({\n'+'first_note: '+thisTieStart+'\n});'
                    result +='\nvar '+thisTieName+'End = new Vex.Flow.StaveTie({\n'+'last_note: '+thisTieEnd+'\n});'
                    result += '\n'+thisTieName+'Start.setContext('+self.context.contextName+').draw();'
                    result += '\n'+thisTieName+'End.setContext('+self.context.contextName+').draw();'
                    tieStart = True
                    continue

                result +='\nvar '+thisTieName+' = new Vex.Flow.StaveTie({\n'+\
                    'first_note: '+thisTieStart+',\nlast_note: '+thisTieEnd\
                    +',\nfirst_indices: [0],\nlast_indices: [0]\n});'
                result += '\n'+thisTieName+'.setContext('+\
                    self.context.contextName+').draw();'
                tieStart = True
                
        return result
    
    def generateCode(self, mode='txt'):
        '''
        Returns the vexflow code needed to render this object in a browser.
        '''
        if mode == 'txt':
            return self.vexflowCode()
        elif mode == 'jsbody':
            return self.jsBodyCode()
        elif mode=='html':
            jsBody = self.jsBodyCode()
            result = htmlCanvasPreamble + str(self.context.getCanvasHTML()) + \
                htmlCanvasPostamble + '\n'
            result += jsBody
            result += htmlConclusion
            return result

class VexflowContext(object):
    '''
    Contains information about the canvas, formatter, and renderer.
    '''

    def __init__(self, params={}, canvasName = None):
        '''
        ``canvasName`` is the name of the canvas within the html code.
        
        ``params`` is a dictionary containing width, height, and other
        parameters to be passed to the canvas object.
        '''
        self.params = params
        self.canvasHTML = ''
        self.canvasJSCode = ''
        self.rendererName = ''
        self.rendererCode = ''
        self.contextName = ''
        self.contextCode = ''
        if 'UIDCounter' in self.params:
            self.UIDCounter = self.params['UIDCounter']
            self.UID = self.UIDCounter.readAndIncrement()
        else:
            self.UIDCounter = UIDCounter()
            self.UID = 0

        if canvasName == None:
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
        Generates the HTML for the canvas and stores it in ``self.canvasHTML``.

        .. note:: End users should use the ``getCanvasHTML()`` method.

        If ``applyAttributes`` is True, then apply the attributes in the
            HTML code instead of in the Javascript

        .. note:: There is no checking that the values aren't also set
                  in Javascript.
        '''
        self.canvasHTML = '<canvas '

        if applyAttributes:
            for (parameter, value) in self.params.items():
                if not common.isNum(value) and not value.isdigit():
                    value = '"' + str(value) + '"'
                self.canvasHTML += str(parameter) + '=' + str(value) + ' '

        self.canvasHTML += 'id="' + self.canvasHTMLName + '"></canvas>'

    def generateJS(self, applyAttributes=True):
        '''
        Generates the Javascript to set up the canvas for VexFlow and stores it
        in ``self.canvasJSCode``, ``self.rendererCode``, and 
        ``self.contextCode``.

        .. note:: End users should use the get methods.

        If ``applyAttributes`` is True, then apply the attributes in the
        Javascript instead of the HTML.

        .. note:: Applying the attributes in Javascript will overwrite any 
                  attributes set in the HTML.
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
        
    def getHeight(self):
        return self.params['height']

    def getWidth(self):
        return self.params['width']
    
    def getCanvasHTML(self, cache=True, applyAttributes=False):
        if not cache or not self.canvasHTML:
            self.generateHTML(applyAttributes=applyAttributes)

        return self.canvasHTML

    def getCanvasCode(self, indentation=1, cache=True, applyAttributes=True):
        if not cache or not self.canvasJSCode:
            self.generateJS(applyAttributes=applyAttributes)
        jsCode = self.canvasJSCode + '\n' + ('    ' * indentation)
        return jsCode

    def getRenderContextCode(self, indentation=1, cache=True, applyAttributes=True):
        if not cache or not self.rendererCode or not self.contextCode:
            self.generateJS(applyAttributes=applyAttributes)
        jsCode = self.rendererCode + '\n' + ('    ' * indentation)
        jsCode += self.contextCode + '\n' + ('    ' * indentation)
        return jsCode
       
    def getJSCode(self, indentation=1, cache=True, applyAttributes=True):
        if not cache or not self.canvasJSCode or not self.rendererCode or not self.contextCode:
            self.generateJS(applyAttributes=applyAttributes)
        jsCode = self.getCanvasCode(indentation, cache, applyAttributes)
        jsCode += self.getRenderContextCode(indentation, cache, applyAttributes)
        return jsCode

    def setHeight(self, height):
        self.params['height'] = height
        self.generateJS()

    def setWidth(self, width):
        self.params['width'] = width
        self.generateJS()


#-------------------------------------------------------------------------------


class Test(unittest.TestCase):
    def runTest(self):
        pass

    def testVexflowNoteToHTML(self):
        expectedOutput = r'''<!DOCTYPE HTML>
<html>
<head>
    <meta name='author' content='Music21' />
    <script src='http://code.jquery.com/jquery-latest.js'></script>
    <script src='http://www.vexflow.com/support/vexflow-min.js'></script>
</head>
<body>
    <canvas width="525" height="120" id='music21canvas'></canvas>
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
            var formatter = new Vex.Flow.Formatter()
            formatter.joinVoices([voice])
            formatter.format([voice], 500);
            voice.draw(ctx, stave);
        });
    </script>
</body>
</html>'''
        n = note.Note('C-')
        v = VexflowNote(n)
        htmlOut = v.generateCode('html')
        self.maxDiff = 30000
        assert(common.basicallyEqual(htmlOut, expectedOutput))

    def testMeasureParts(self):
        self.maxDiff = 30000
        from music21 import corpus
        b = corpus.parse('bwv1.6.mxl')
        m = b.parts[0].measures(0,1)[2]
        d = fromMeasure(m)
        expectedOutputText = r'''var music21Voice0 = new Vex.Flow.Voice({num_beats: 4.0, beat_value: 4, resolution: Vex.Flow.RESOLUTION});
var music21Voice0Notes = [new Vex.Flow.StaveNote({keys: ["Gn/4"], duration: "8", stem_direction: Vex.Flow.StaveNote.STEM_UP}), new Vex.Flow.StaveNote({keys: ["Cn/4"], duration: "8", stem_direction: Vex.Flow.StaveNote.STEM_UP}), new Vex.Flow.StaveNote({keys: ["Fn/4"], duration: "8", stem_direction: Vex.Flow.StaveNote.STEM_UP}), new Vex.Flow.StaveNote({keys: ["Fn/3"], duration: "8", stem_direction: Vex.Flow.StaveNote.STEM_UP}), new Vex.Flow.StaveNote({keys: ["An/3"], duration: "8", stem_direction: Vex.Flow.StaveNote.STEM_UP}), new Vex.Flow.StaveNote({keys: ["Fn/3"], duration: "8", stem_direction: Vex.Flow.StaveNote.STEM_UP}), new Vex.Flow.StaveNote({keys: ["An/3"], duration: "8", stem_direction: Vex.Flow.StaveNote.STEM_UP}), new Vex.Flow.StaveNote({keys: ["Cn/4"], duration: "8", stem_direction: Vex.Flow.StaveNote.STEM_UP})];
music21Voice0.addTickables(music21Voice0Notes);'''
        self.assertMultiLineEqual(d, expectedOutputText)
        c = fromMeasure(m, 'html')
        expectedOutput = r'''<!DOCTYPE HTML>
<html>
<head>
    <meta name='author' content='Music21' />
    <script src='http://code.jquery.com/jquery-latest.js'></script>
    <script src='http://www.vexflow.com/support/vexflow-min.js'></script>
</head>
<body>
    <canvas width="525" height="120" id='music21canvas'></canvas>
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
            var music21Voice0Beam0 = new Vex.Flow.Beam(music21Voice0Notes.slice(0,2));
            var music21Voice0Beam1 = new Vex.Flow.Beam(music21Voice0Notes.slice(2,4));
            var music21Voice0Beam2 = new Vex.Flow.Beam(music21Voice0Notes.slice(4,6));
            var music21Voice0Beam3 = new Vex.Flow.Beam(music21Voice0Notes.slice(6,8));
            var formatter = new Vex.Flow.Formatter().joinVoices([music21Voice0]).format([music21Voice0], 500);
            music21Voice0.draw(ctx, stave);

            music21Voice0Beam0.setContext(ctx).draw();
            music21Voice0Beam1.setContext(ctx).draw();
            music21Voice0Beam2.setContext(ctx).draw();
            music21Voice0Beam3.setContext(ctx).draw();
        });
    </script>
</body>
</html>'''
        #self.assertMultiLineEqual(c, expectedOutput)
        assert(common.basicallyEqual(c, expectedOutput))  #only whitespace differences


class TestExternal(unittest.TestCase):
    def runTest(self):
        pass

    def testShowMeasureWithAccidentals(self):
        from music21 import corpus
        b = note.Note('B4') 
        #b = corpus.parse('bwv1.6')
        b.show('vexflow')
    
#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = []


if __name__ == "__main__":
    # sys.arg test options will be used in mainTest()
    import music21
    music21.mainTest(Test, TestExternal)

#------------------------------------------------------------------------------
# eof
