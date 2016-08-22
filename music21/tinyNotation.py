# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         tinyNotation.py
# Purpose:      A simple notation input format.
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2009-2012, 2015 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
tinyNotation is a simple way of specifying single line melodies
that uses a notation somewhat similar to Lilypond but with WAY fewer 
options.  It was originally developed to notate trecento (medieval Italian)
music, but it is pretty useful for a lot of short examples, so we have
made it a generally supported music21 format.


N.B.: TinyNotation is not meant to expand to cover every single case.  Instead
it is meant to be subclassable to extend to the cases *your* project needs.
See for instance the harmony examples in HarmonyStream and HarmonyNote
or the Trecento specific examples in trecento/cadencebook.py


Here are the most important rules:

1. Note names are: a,b,c,d,e,f,g and r for rest
2. Flats, sharps, and naturals are notated as #,- (not b), and (if needed) n.  
   If the accidental is above the staff (i.e., editorial), enclose it in 
   parentheses: (#), etc.  Make sure that flats in the key signatures are
   explicitly specified.  
3. Note octaves are specified as follows::

     CC to BB = from C below bass clef to second-line B in bass clef
     C to B = from bass clef C to B below middle C.
     c  to b = from middle C to the middle of treble clef
     c' to b' = from C in treble clef to B above treble clef
    
   Octaves below and above these are specified by further doublings of
   letter (CCC) or apostrophes (c'') -- this is one of the note name
   standards found in many music theory books.
4. After the note name, a number may be placed indicating the note 
   length: 1 = whole note, 2 = half, 4 = quarter, 8 = eighth, 16 = sixteenth.  
   etc.  If the number is omitted then it is assumed to be the same 
   as the previous note.  I.e., c8 B c d  is a string of eighth notes.
5. After the number, a ~ can be placed to show a tie to the next note.  
   A "." indicates a dotted note.  (If you are entering
   data via Excel or other spreadsheet, be sure that "capitalize the 
   first letter of sentences" is turned off under "Tools->AutoCorrect,"
   otherwise the next letter will be capitalized, and the octave will
   be screwed up.)
6. For triplets use this notation:  `trip{c4 d8}`  indicating that these 
   two notes both have "3s" over them.  For 4 in the place of 3, 
   use `quad{c16 d e8}`.  No other tuplets are supported.


Again, see the :class:`~music21.tinyNotation.HarmonyStream` (below) and 
trecento.cadencebook examples
to see how to make TinyNotation useful for your own needs.

(Currently, final notes with fermatas (or any very long final note), 
take 0 for the note length.  But expect this to disappear from the
TinyNotation specification soon, as it's too Trecento specific.)



an alpha complete rewrite of tinyNotation.

tinyNotation was one of the first modules of music21 and one of my first attempts to
program in Python.  and it shows.

this is what the module should have been... from mistakes
learned and insights from ABC etc. parsing.

keeping both until this becomes stable.


    >>> tnc = tinyNotation.Converter("3/4 E4 r f# g=lastG trip{b-8 a g} c4~ c")
    >>> stream1 = tnc.parse().stream
    >>> stream1.show('text')
    {0.0} <music21.stream.Measure 1 offset=0.0>
        {0.0} <music21.clef.TrebleClef>
        {0.0} <music21.meter.TimeSignature 3/4>
        {0.0} <music21.note.Note E>
        {1.0} <music21.note.Rest rest>
        {2.0} <music21.note.Note F#>
    {3.0} <music21.stream.Measure 2 offset=3.0>
        {0.0} <music21.note.Note G>
        {1.0} <music21.note.Note B->
        {1.3333} <music21.note.Note A>
        {1.6667} <music21.note.Note G>
        {2.0} <music21.note.Note C>
    {6.0} <music21.stream.Measure 3 offset=6.0>
        {0.0} <music21.note.Note C>
        {1.0} <music21.bar.Barline style=final>

    >>> stream1.flat.getElementById("lastG").step
    'G'
    >>> stream1.flat.notesAndRests[1].isRest
    True
    >>> stream1.flat.notesAndRests[0].octave
    3    
    >>> stream1.flat.notes[-2].tie.type
    'start'
    >>> stream1.flat.notes[-1].tie.type
    'stop'
    
    
    Changing time signatures are supported:
    
    >>> s1 = converter.parse('tinynotation: 3/4 C4 D E 2/4 F G A B 1/4 c')
    >>> s1.show('t')
    {0.0} <music21.stream.Measure 1 offset=0.0>
        {0.0} <music21.clef.BassClef>
        {0.0} <music21.meter.TimeSignature 3/4>
        {0.0} <music21.note.Note C>
        {1.0} <music21.note.Note D>
        {2.0} <music21.note.Note E>
    {3.0} <music21.stream.Measure 2 offset=3.0>
        {0.0} <music21.meter.TimeSignature 2/4>
        {0.0} <music21.note.Note F>
        {1.0} <music21.note.Note G>
    {5.0} <music21.stream.Measure 3 offset=5.0>
        {0.0} <music21.note.Note A>
        {1.0} <music21.note.Note B>
    {7.0} <music21.stream.Measure 4 offset=7.0>
        {0.0} <music21.meter.TimeSignature 1/4>
        {0.0} <music21.note.Note C>
        {1.0} <music21.bar.Barline style=final>
'''
import unittest
import copy
import re
import sre_parse

from music21 import note
from music21 import duration
from music21 import common
from music21 import exceptions21
from music21 import stream
from music21 import tie
from music21 import expressions
from music21 import meter
from music21 import pitch

from music21 import environment
_MOD = "tinyNotation.py"
environLocal = environment.Environment(_MOD)

class TinyNotationException(exceptions21.Music21Exception):
    pass

class State(object):
    '''
    State tokens apply something to 
    every note found within it.
    '''
    autoExpires = False # expires after N tokens or never.
    
    def __init__(self, parent, stateInfo):
        self.affectedTokens = []
        self.parent = common.wrapWeakref(parent)
        self.stateInfo = stateInfo
        #print("Adding state", self, parent.activeStates)
        
    def start(self):
        '''
        called when the state is initiated
        '''
        pass

    def end(self):
        '''
        called just after removing state
        '''
        pass
    
    def affectTokenBeforeParse(self, tokenStr):
        '''
        called to modify the string of a token.
        '''
        return tokenStr

    def affectTokenAfterParseBeforeModifiers(self, m21Obj):
        '''
        called after the object has been acquired but before modifiers have been applied.
        '''
        return m21Obj

    def affectTokenAfterParse(self, m21Obj):
        '''
        called to modify the tokenObj after parsing
        
        tokenObj may be None if another
        state has deleted it.
        '''
        self.affectedTokens.append(m21Obj)
        if self.autoExpires is not False:
            if len(self.affectedTokens) == self.autoExpires:
                self.end()
                p = common.unwrapWeakref(self.parent)
                for i in range(len(p.activeStates)):
                    backCount = -1 * (i+1)
                    if p.activeStates[backCount] is self:
                        p.activeStates.pop(backCount)
                        break
        return m21Obj

class TieState(State):
    '''
    A TieState is an autoexpiring state that applies a tie start to this note and a 
    tie stop to the next note.
    '''
    autoExpires = 2

    def end(self):
        '''
        end the tie state by applying tie ties to the appropriate notes
        '''
        if self.affectedTokens[0].tie is None:
            self.affectedTokens[0].tie = tie.Tie('start')
        else:
            self.affectedTokens[0].tie.type = 'continue'
        if len(self.affectedTokens) > 1: # could be end...            
            self.affectedTokens[1].tie = tie.Tie('stop')


class TupletState(State):
    '''
    a tuplet state applies tuplets to notes while parsing and sets 'start' and 'stop'
    on the first and last note when end is called.
    '''
    actual = 3
    normal = 2
    
    def end(self):
        '''
        end a tuplet by putting start on the first note and stop on the last.
        '''
        if len(self.affectedTokens) == 0:
            return 
        self.affectedTokens[0].duration.tuplets[0].type = 'start'
        self.affectedTokens[-1].duration.tuplets[0].type = 'stop'
            
    
    def affectTokenAfterParse(self, n):
        '''
        puts a tuplet on the note
        '''
        super(TupletState, self).affectTokenAfterParse(n)
        newTup = duration.Tuplet()
        newTup.durationActual = duration.durationTupleFromTypeDots(n.duration.type, 0)
        newTup.durationNormal = duration.durationTupleFromTypeDots(n.duration.type, 0)
        newTup.numberNotesActual = self.actual
        newTup.numberNotesNormal = self.normal
        n.duration.appendTuplet(newTup)
        return n      

class TripletState(TupletState):
    '''
    a 3:2 tuplet
    '''
    actual = 3
    normal = 2

class QuadrupletState(TupletState):
    '''
    a 4:3 tuplet
    '''    
    actual = 4
    normal = 3

class Modifier(object):
    '''
    a modifier is something that changes the current
    token, like setting the Id or Lyric.
    '''
    def __init__(self, modifierData, modifierString, parent):
        self.modifierData = modifierData
        self.modifierString = modifierString
        self.parent = common.wrapWeakref(parent)
        
    def preParse(self, tokenString):
        '''
        called before the tokenString has been
        turned into an object
        '''
        pass
    
    def postParse(self, m21Obj):
        '''
        called after the tokenString has been
        truend into an m21Obj.  m21Obj may be None
        '''
        pass


class IdModifier(Modifier):
    '''
    sets the .id of the m21Obj, called with =
    '''
    def postParse(self, m21Obj):
        if hasattr(m21Obj, 'id'):
            m21Obj.id = self.modifierData

class LyricModifier(Modifier):
    '''
    sets the .lyric of the m21Obj, called with _
    '''
    def postParse(self, m21Obj):
        if hasattr(m21Obj, 'lyric'):
            m21Obj.lyric = self.modifierData

class StarModifier(Modifier):
    '''
    does nothing, but easily subclassed.  Uses *...* to make it happen
    '''
    pass


class Token(object):
    '''
    A single token made from the parser.
    
    Call .parse(parent) to make it work.
    '''
    def __init__(self, token=""):
        self.token = token

    def parse(self, parent):
        '''
        do NOT store parent -- probably
        too slow
        '''
        pass
        

class TimeSignatureToken(Token):
    '''
    Represents a single time signature, like 1/4
    '''
    def parse(self, parent):
        tsObj = meter.TimeSignature(self.token)
        parent.stateDict['currentTimeSignature'] = tsObj
        return tsObj

class NoteOrRestToken(Token):
    '''
    represents a Note or Rest.  Chords are represented by Note objects
    '''
    def __init__(self, token=""):
        super(NoteOrRestToken, self).__init__(token)
        self.durationMap = [
                            (r'(\d+)', 'durationType'),
                            (r'(\.+)', 'dots'),
        ]  ## tie later...
    
        
        self.durationFound = False

    def applyDuration(self, n, t, parent):
        '''
        takes the information in the string `t` and creates a Duration object for the 
        note or rest `n`.
        '''
        for pm, method in self.durationMap:
            searchSuccess = re.search(pm, t)
            if searchSuccess:
                callFunc = getattr(self, method)
                t = callFunc(n, searchSuccess, pm, t, parent)
        
        if self.durationFound is False and hasattr(parent, 'stateDict'):
            n.duration.quarterLength = parent.stateDict['lastDuration']

        # do this by quarterLength here, so that applied tuplets do not persist.        
        if hasattr(parent, 'stateDict'):
            parent.stateDict['lastDuration'] = n.duration.quarterLength
        
        return t

    def durationType(self, n, search, pm, t, parent):
        '''
        The result of a successful search for a duration type: puts a Duration in the right place.
        '''
        self.durationFound = True
        typeNum = int(search.group(1))
        if typeNum == 0:
            if parent.stateDict['currentTimeSignature'] is not None:
                n.duration = copy.deepcopy(parent.stateDict['currentTimeSignature'].barDuration)
                n.expressions.append(expressions.Fermata())
        else:
            n.duration.type = duration.typeFromNumDict[typeNum]
        t = re.sub(pm, '', t)
        return t
    
    def dots(self, n, search, pm, t, parent):
        '''
        adds the appropriate number of dots to the right place.
        
        Subclassed in TrecentoNotation where two dots has a different meaning.
        '''
        n.duration.dots = len(search.group(1))
        t = re.sub(pm, '', t)
        return t
    

class RestToken(NoteOrRestToken):
    '''
    A token starting with 'r', representing a rest.
    '''
    def parse(self, parent=None):    
        r = note.Rest()
        self.applyDuration(r, self.token, parent)        
        return r

class NoteToken(NoteOrRestToken):
    '''
    A NoteToken represents a single Note with pitch
    
    >>> c3 = tinyNotation.NoteToken('C')
    >>> c3
    <music21.tinyNotation.NoteToken object at 0x10b07bf98>
    >>> n = c3.parse()
    >>> n
    <music21.note.Note C>
    >>> n.nameWithOctave
    'C3'
    
    >>> bFlat6 = tinyNotation.NoteToken("b''-")
    >>> bFlat6
    <music21.tinyNotation.NoteToken object at 0x10b07bf98>
    >>> n = bFlat6.parse()
    >>> n
    <music21.note.Note B->
    >>> n.nameWithOctave
    'B-6'
    
    '''    
    pitchMap = [
        (r'([A-G]+)', 'lowOctave'),
        (r'([a-g])(\'*)', 'highOctave'),
        (r'\(([\#\-n]+)\)(.*)', 'editorialAccidental'),
        (r'(\#+)', 'sharps'),
        (r'(\-+)', 'flats'),
        (r'(n)', 'natural'),
    ]
    def __init__(self, token=""):
        super(NoteToken, self).__init__(token)
        self.isEditorial = False
    
    def parse(self, parent=None):
        '''
        Extract the pitch from the note.
        '''
        t = self.token
        
        n = note.Note()
        t = self.getPitch(n, t)
        if parent:
            self.applyDuration(n, t, parent)
        return n

    def getPitch(self, n, t):
        for pm, method in self.pitchMap:
            searchSuccess = re.search(pm, t)
            if searchSuccess:
                callFunc = getattr(self, method)
                t = callFunc(n, searchSuccess, pm, t)
        return t

    def editorialAccidental(self, n, search, pm, t):
        '''
        indicates that the accidental is in parentheses, so set it up to be stored in ficta.
        '''
        self.isEditorial = True
        t = search.group(1) + search.group(2)
        return t

    def _addAccidental(self, n, alter, pm, t):
        '''
        helper function for all accidental types.
        '''
        acc = pitch.Accidental(alter)
        if self.isEditorial:
            n.editorial.ficta = acc
        else:
            n.pitch.accidental = acc
        t = re.sub(pm, '', t)
        return t

    def sharps(self, n, search, pm, t):
        '''
        called when one or more sharps have been found.
        '''
        alter = len(search.group(1))
        return self._addAccidental(n, alter, pm, t)

    def flats(self, n, search, pm, t):
        '''
        called when one or more flats have been found.
        '''
        alter = -1 * len(search.group(1))
        return self._addAccidental(n, alter, pm, t)

    def natural(self, n, search, pm, t):
        '''
        called when an explicit natural has been found.  All pitches are natural without
        being specified, so not needed.
        '''
        return self._addAccidental(n, 0, pm, t)

    def lowOctave(self, n, search, pm, t):
        '''
        Called when a note of octave 3 or below is encountered.
        '''
        stepName = search.group(1)[0].upper()
        octaveNum = 4 - len(search.group(1))
        n.step = stepName
        n.octave = octaveNum
        t = re.sub(pm, '', t)
        return t

    def highOctave(self, n, search, pm, t):
        '''
        Called when a note of octave 4 or higher is encountered.
        '''
        stepName = search.group(1)[0].upper()
        octaveNum = 4 + len(search.group(2))
        n.step = stepName
        n.octave = octaveNum
        t = re.sub(pm, '', t)
        return t


class Converter(object):
    '''
    Main conversion object for TinyNotation.
    
    Accepts one keyword: makeNotation=False to get "classic" TinyNotation formats.
    
    '''
    def __init__(self, stringRep = "", **keywords):
        self.stateMap = [ 
            (r'trip\{', TripletState),
            (r'quad\{', QuadrupletState),
            (r'\~', TieState)
            ]
    
        self.endState = re.compile(r'\}$')
        
        self.tokenMap = [
                    (r'(\d+\/\d+)', TimeSignatureToken),
                    (r'r(\S*)', RestToken),
                    (r'(\S*)', NoteToken), # last
        ]
        
        self.modifierMap = [
                    (r'\=([A-Za-z0-9]*)', IdModifier),
                    (r'_(.*)', LyricModifier),
                    (r'\*(.*)\*', StarModifier),
        ]

        self.keywords = keywords
        if 'makeNotation' in keywords:
            self.makeNotation = keywords['makeNotation']
        else:
            self.makeNotation = True
        
        self.stream = stream.Part()
        self.stateDict = {'currentTimeSignature': None,
                          'lastDuration': 1.0
                          }
        self.stringRep = stringRep
        #self.regexps = {}
        self.activeStates = []
        self.preTokens = [] # space-separated strings
    
        self._stateMapRe = None
        self._tokenMapRe = None
        self._modifierMapRe = None
            
    def splitPreTokens(self):
        '''
        splits the string into textual tokens.
        
        Right now just splits on spaces, but might be smarter to ignore spaces in
        quotes, etc. later.
        '''
        self.preTokens = self.stringRep.split() # do something better...
    
    def setupRegularExpressions(self):
        '''
        Regular expressions get compiled for faster
        usage.
        '''
        self._stateMapRe = []
        for rePre, classCall in self.stateMap:
            try:
                self._stateMapRe.append( (re.compile(rePre), classCall) )
            except sre_parse.error as e:
                raise TinyNotationException("Error in compiling state, %s: %s" % (rePre, str(e)))


        self._tokenMapRe = []
        for rePre, classCall in self.tokenMap:
            try:
                self._tokenMapRe.append( (re.compile(rePre), classCall) )
            except sre_parse.error as e:
                raise TinyNotationException("Error in compiling token, %s: %s" % (rePre, str(e)))
        
        self._modifierMapRe = []
        for rePre, classCall in self.modifierMap:
            try:
                self._modifierMapRe.append( (re.compile(rePre), classCall) )
            except sre_parse.error as e:
                raise TinyNotationException("Error in compiling modifier, %s: %s" % (rePre, str(e)))
        
    def parse(self):
        '''
        splitPreTokens, setupRegularExpressions, then run through each preToken, and run postParse.
        '''
        if self.preTokens == [] and self.stringRep != "":
            self.splitPreTokens()
        if self._tokenMapRe is None:
            self.setupRegularExpressions()
        
        for i, t in enumerate(self.preTokens):
            self.parseOne(i, t)
        self.postParse()
        return self

    def parseOne(self, i, t):
        '''
        parse a single token at position i, with
        text t.
        
        Checks for state changes, modifiers, tokens, and end-state brackets.
        '''        
        endBrackets = 0
        
        for s, c in self._stateMapRe:
            matchSuccess = s.search(t)
            if matchSuccess is not None:
                stateData = matchSuccess.group(0)
                t = s.sub('', t)
                stateObj = c(self, stateData)
                stateObj.start()
                self.activeStates.append(stateObj)

        while self.endState.search(t):
            t = self.endState.sub('', t)
            endBrackets += 1

        
        modifiers = []
        for m, c in self._modifierMapRe:
            matchSuccess = m.search(t)
            if matchSuccess is not None:
                modifierData = matchSuccess.group(1)
                t = m.sub('', t)
                modObj = c(modifierData, t, self)
                modifiers.append(modObj)
                
        for mObj in modifiers:
            mObj.preParse(t)
        
        for s in self.activeStates[:]:
            t = s.affectTokenBeforeParse(t)
        
        m21Obj = None
        tokenObj = None   
        # parse token...with state...
        for tokenRe, c in self._tokenMapRe:
            matchSuccess = tokenRe.search(t)
            if matchSuccess is not None:
                tokenData = matchSuccess.group(1)
                tokenObj = c(tokenData)
                m21Obj = tokenObj.parse(self)
                if m21Obj is not None:
                    break

        for s in self.activeStates[:]: # iterate over copy so we can remove....
            m21Obj = s.affectTokenAfterParseBeforeModifiers(m21Obj)


        for m in modifiers:
            m.postParse(m21Obj)
        
        for s in self.activeStates[:]: # iterate over copy so we can remove....
            m21Obj = s.affectTokenAfterParse(m21Obj)
        
        for i in range(endBrackets):
            stateToRemove = self.activeStates.pop()
            tempObj = stateToRemove.end()
            if tempObj is not None:
                m21Obj = tempObj

        if m21Obj is not None:
            self.stream._appendCore(m21Obj)
    
    def postParse(self):
        '''
        Call postParse calls on .stream, currently just .makeMeasures.
        '''
        if self.makeNotation is not False:
            self.stream.makeMeasures(inPlace=True)
        
class Test(unittest.TestCase):
    parseTest = "1/4 trip{C8~ C~_hello C=mine} F~ F~ 2/8 F F# quad{g--16 a## FF(n) g#} g16 F0"
    
    def runTest(self):
        pass
    
    def testOne(self):
        c = Converter(self.parseTest)
        c.parse()
        s = c.stream
        sfn = s.flat.notes
        self.assertEqual(sfn[0].tie.type, 'start')
        self.assertEqual(sfn[1].tie.type, 'continue')
        self.assertEqual(sfn[2].tie.type, 'stop')
        self.assertEqual(sfn[0].step, 'C')
        self.assertEqual(sfn[0].octave, 3)
        self.assertEqual(sfn[1].lyric, "hello")
        self.assertEqual(sfn[2].id, "mine")
        self.assertEqual(sfn[6].pitch.accidental.alter, 1)
        self.assertEqual(sfn[7].pitch.accidental.alter, -2)
        self.assertEqual(sfn[9].editorial.ficta.alter, 0)
        self.assertEqual(sfn[12].duration.quarterLength, 1.0)
        self.assertEqual(sfn[12].expressions[0].classes, expressions.Fermata().classes)

class TestExternal(unittest.TestCase):
    def runTest(self):
        pass
    
    def testOne(self):
        c = Converter(Test.parseTest)
        c.parse()
        c.stream.show('musicxml.png')


### TODO: Chords
        
if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
        