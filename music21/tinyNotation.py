# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------------
# Name:         tinyNotation.py
# Purpose:      A simple notation input format.
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2009-2012, 2015 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# -------------------------------------------------------------------------------
'''
tinyNotation is a simple way of specifying single line melodies
that uses a notation somewhat similar to Lilypond but with WAY fewer
options.  It was originally developed to notate trecento (medieval Italian)
music, but it is pretty useful for a lot of short examples, so we have
made it a generally supported music21 format.


N.B.: TinyNotation is not meant to expand to cover every single case.  Instead
it is meant to be subclassable to extend to the cases *your* project needs.

Here are the most important rules by default:

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

Here is an example of TinyNotation in action.

>>> stream1 = converter.parse("tinyNotation: 3/4 E4 r f# g=lastG trip{b-8 a g} c4~ c")
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
    {1.0} <music21.bar.Barline type=final>
>>> stream1.flat.getElementById('lastG').step
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
    {1.0} <music21.bar.Barline type=final>



Here is an equivalent way of doing the example above, but using the lower level
:class:`music21.tinyNotation.Converter` object:

>>> tnc = tinyNotation.Converter('3/4 E4 r f# g=lastG trip{b-8 a g} c4~ c')
>>> stream2 = tnc.parse().stream
>>> len(stream1.recurse()) == len(stream2.recurse())
True

This lower level is needed in case you want to add additional features.  For instance,
here we will set the "modifierStar" to change the color of notes:

>>> class ColorModifier(tinyNotation.Modifier):
...     def postParse(self, m21Obj):
...         m21Obj.style.color = self.modifierData
...         return m21Obj

>>> tnc = tinyNotation.Converter('3/4 C4*pink* D4*green* E4*blue*')
>>> tnc.modifierStar = ColorModifier
>>> s = tnc.parse().stream
>>> for n in s.recurse().getElementsByClass('Note'):
...     print(n.step, n.style.color)
C pink
D green
E blue

Or more usefully, and often desired:

>>> class HarmonyModifier(tinyNotation.Modifier):
...     def postParse(self, n):
...         cs = harmony.ChordSymbol(n.pitch.name + self.modifierData)
...         cs.duration = n.duration
...         return cs
>>> tnc = tinyNotation.Converter('4/4 C2_maj7 D4_m E-_sus4')
>>> tnc.modifierUnderscore = HarmonyModifier
>>> s = tnc.parse().stream
>>> s.show('text')
{0.0} <music21.stream.Measure 1 offset=0.0>
    {0.0} <music21.clef.BassClef>
    {0.0} <music21.meter.TimeSignature 4/4>
    {0.0} <music21.harmony.ChordSymbol Cmaj7>
    {2.0} <music21.harmony.ChordSymbol Dm>
    {3.0} <music21.harmony.ChordSymbol E-sus4>
    {4.0} <music21.bar.Barline type=final>
>>> for cs in s.recurse().getElementsByClass('ChordSymbol'):
...     print([p.name for p in cs.pitches])
['C', 'E', 'G', 'B']
['D', 'F', 'A']
['E-', 'A-', 'B-']

The supported modifiers are:
    * `=data` (`modifierEquals`, default action is to set `.id`)
    * `_data` (`modifierUnderscore`, default action is to set `.lyric`)
    * `[data]` (`modifierSquare`, no default action)
    * `<data>` (`modifierAngle`, no default action)
    * `(data)` (`modifierParens`, no default action)
    * `*data*` (`modifierStar`, no default action)


Another example: TinyNotation does not support key signatures -- well, no problem! Let's
create a new Token type and add it to the tokenMap

>>> class KeyToken(tinyNotation.Token):
...     def parse(self, parent):
...         keyName = self.token
...         return key.Key(keyName)
>>> keyMapping = (r'k(.*)', KeyToken)
>>> tnc = tinyNotation.Converter('4/4 kE- G1 kf# A1')
>>> tnc.tokenMap.append(keyMapping)
>>> s = tnc.parse().stream
>>> s.show('text')
{0.0} <music21.stream.Measure 1 offset=0.0>
    {0.0} <music21.clef.BassClef>
    {0.0} <music21.key.Key of E- major>
    {0.0} <music21.meter.TimeSignature 4/4>
    {0.0} <music21.note.Note G>
{4.0} <music21.stream.Measure 2 offset=4.0>
    {0.0} <music21.key.Key of f# minor>
    {0.0} <music21.note.Note A>
    {4.0} <music21.bar.Barline type=final>


TokenMap should be passed a string, representing a regular expression with exactly one
group (which can be the entire expression), and a subclass of :class:`~music21.tinyNotation.Token`
which will handle the parsing of the string.

Tokens can take advantage of the `parent` variable, which is a reference to the `Converter`
object, to use the `.stateDict` dictionary to store information about state.  For instance,
the `NoteOrRestToken` uses `parent.stateDict['lastDuration']` to get access to the last
duration.

There is also the concept of "State" which affects multiple tokens.  The best way to create
a new State is to define a subclass of the :class:`~music21.tinyNotation.State`  and add it
to `bracketStateMapping` of the converter.  Here's one that a lot of people have asked for
over the years:

>>> class ChordState(tinyNotation.State):
...    def affectTokenAfterParse(self, n):
...        super().affectTokenAfterParse(n)
...        return None  # do not append Note object
...    def end(self):
...        ch = chord.Chord(self.affectedTokens)
...        ch.duration = self.affectedTokens[0].duration
...        return ch
>>> tnc = tinyNotation.Converter("2/4 C4 chord{C4 e g'} F.4 chord{D8 F# A}")
>>> tnc.bracketStateMapping['chord'] = ChordState
>>> s = tnc.parse().stream
>>> s.show('text')
{0.0} <music21.stream.Measure 1 offset=0.0>
    {0.0} <music21.clef.BassClef>
    {0.0} <music21.meter.TimeSignature 2/4>
    {0.0} <music21.note.Note C>
    {1.0} <music21.chord.Chord C3 E4 G5>
{2.0} <music21.stream.Measure 2 offset=2.0>
    {0.0} <music21.note.Note F>
    {1.5} <music21.chord.Chord D3 F#3 A3>
    {2.0} <music21.bar.Barline type=final>

If you want to create a very different dialect, you can subclass tinyNotation.Converter
and set it up once to use the mappings above.   See
:class:`~music21.alpha.trecento.notation.TrecentoTinyConverter` (especially the code)
for details on how to do that.
'''
import collections
import copy
import re
import sre_parse
import unittest

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
_MOD = 'tinyNotation'
environLocal = environment.Environment(_MOD)


class TinyNotationException(exceptions21.Music21Exception):
    pass


class State:
    '''
    State tokens apply something to
    every note found within it.

    State objects can have "autoExpires" set, which is False if it does not expire
    or an integer if it expires after a certain number of tokens have been processed.

    >>> tnc = tinyNotation.Converter()
    >>> ts = tinyNotation.TieState(tnc, '~')
    >>> isinstance(ts, tinyNotation.State)
    True
    >>> ts.autoExpires
    2
    '''
    autoExpires = False  # expires after N tokens or never.

    def __init__(self, parent=None, stateInfo=None):
        self.affectedTokens = []
        self.parent = common.wrapWeakref(parent)
        self.stateInfo = stateInfo
        # print('Adding state', self, parent.activeStates)

    def start(self):
        '''
        called when the state is initiated
        '''
        pass

    def end(self):
        '''
        called just after removing state
        '''
        return None

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
                # this is a hack that should be done away with...
                p = common.unwrapWeakref(self.parent)
                for i in range(len(p.activeStates)):
                    backCount = -1 * (i + 1)
                    if p.activeStates[backCount] is self:
                        p.activeStates.pop(backCount)
                        break
        return m21Obj


class TieState(State):
    '''
    A TieState is an auto-expiring state that applies a tie start to this note and a
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
        if len(self.affectedTokens) > 1:  # could be end.
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
        if not self.affectedTokens:
            return None
        self.affectedTokens[0].duration.tuplets[0].type = 'start'
        self.affectedTokens[-1].duration.tuplets[0].type = 'stop'
        return None

    def affectTokenAfterParse(self, n):
        '''
        puts a tuplet on the note
        '''
        super().affectTokenAfterParse(n)
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


class Modifier:
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
        turned into an m21Obj.  m21Obj may be None

        Important: must return the m21Obj, or a different object!
        '''
        return m21Obj


class IdModifier(Modifier):
    '''
    sets the .id of the m21Obj, called with = by default
    '''

    def postParse(self, m21Obj):
        if hasattr(m21Obj, 'id'):
            m21Obj.id = self.modifierData
        return m21Obj

class LyricModifier(Modifier):
    '''
    sets the .lyric of the m21Obj, called with _ by default
    '''

    def postParse(self, m21Obj):
        if hasattr(m21Obj, 'lyric'):
            m21Obj.lyric = self.modifierData
        return m21Obj



class Token:
    '''
    A single token made from the parser.

    Call .parse(parent) to make it work.
    '''

    def __init__(self, token=''):
        self.token = token

    def parse(self, parent):
        '''
        do NOT store parent -- probably
        too slow
        '''
        return None


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

    def __init__(self, token=''):
        super().__init__(token)
        self.durationMap = [
            (r'(\d+)', 'durationType'),
            (r'(\.+)', 'dots'),
        ]  # tie will be dealt with later.


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

    def durationType(self, element, search, pm, t, parent):
        '''
        The result of a successful search for a duration type: puts a Duration in the right place.
        '''
        self.durationFound = True
        typeNum = int(search.group(1))
        if typeNum == 0:
            if parent.stateDict['currentTimeSignature'] is not None:
                element.duration = copy.deepcopy(
                    parent.stateDict['currentTimeSignature'].barDuration
                )
                element.expressions.append(expressions.Fermata())
        else:
            try:
                element.duration.type = duration.typeFromNumDict[typeNum]
            except KeyError as ke:
                raise TinyNotationException(
                    f'Cannot parse token with duration {typeNum}'
                ) from ke
        t = re.sub(pm, '', t)
        return t

    def dots(self, element, search, pm, t, parent):
        '''
        adds the appropriate number of dots to the right place.

        Subclassed in TrecentoNotation where two dots has a different meaning.
        '''
        element.duration.dots = len(search.group(1))
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
    pitchMap = collections.OrderedDict([
        ('lowOctave', r'([A-G]+)'),
        ('highOctave', r'([a-g])(\'*)'),
        ('editorialAccidental', r'\(([\#\-n]+)\)(.*)'),
        ('sharps', r'(\#+)'),
        ('flats', r'(\-+)'),
        ('natural', r'(n)'),
    ])

    def __init__(self, token=''):
        super().__init__(token)
        self.isEditorial = False

    def parse(self, parent=None):
        '''
        Extract the pitch from the note and then returns the Note.
        '''
        t = self.token

        n = note.Note()
        t = self.processPitchMap(n, t)
        if parent:
            self.applyDuration(n, t, parent)
        return n

    def processPitchMap(self, n, t):
        '''
        processes the pitchMap on the object.
        '''
        for method, pm in self.pitchMap.items():
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
        # noinspection PyShadowingNames
        r'''
        helper function for all accidental types.

        >>> nToken = tinyNotation.NoteToken('BB--')
        >>> n = note.Note('B')
        >>> n.octave = 2
        >>> tPost = nToken._addAccidental(n, -2, r'(\-+)', 'BB--')
        >>> tPost
        'BB'
        >>> n.pitch.accidental
        <accidental double-flat>

        >>> nToken = tinyNotation.NoteToken('BB(--)')
        >>> nToken.isEditorial = True
        >>> n = note.Note('B')
        >>> n.octave = 2
        >>> tPost = nToken._addAccidental(n, -2, r'(\-+)', 'BB--')
        >>> tPost
        'BB'
        >>> n.editorial.ficta
        <accidental double-flat>
        '''
        acc = pitch.Accidental(alter)
        if self.isEditorial:
            n.editorial.ficta = acc
        else:
            n.pitch.accidental = acc
        t = re.sub(pm, '', t)
        return t

    def sharps(self, n, search, pm, t):
        # noinspection PyShadowingNames
        r'''
        called when one or more sharps have been found and adds the appropriate accidental to it.

        >>> import re
        >>> tStr = 'C##'
        >>> nToken = tinyNotation.NoteToken(tStr)
        >>> n = note.Note('C')
        >>> n.octave = 3
        >>> searchResult = re.search(nToken.pitchMap['sharps'], tStr)
        >>> tPost = nToken.sharps(n, searchResult, nToken.pitchMap['sharps'], tStr)
        >>> tPost
        'C'
        >>> n.pitch.accidental
        <accidental double-sharp>
        '''
        alter = len(search.group(1))
        return self._addAccidental(n, alter, pm, t)

    def flats(self, n, search, pm, t):
        # noinspection PyShadowingNames
        '''
        called when one or more flats have been found and calls adds
        the appropriate accidental to it.

        >>> import re
        >>> tStr = 'BB--'
        >>> nToken = tinyNotation.NoteToken(tStr)
        >>> n = note.Note('B')
        >>> n.octave = 2
        >>> searchResult = re.search(nToken.pitchMap['flats'], tStr)
        >>> tPost = nToken.flats(n, searchResult, nToken.pitchMap['flats'], tStr)
        >>> tPost
        'BB'
        >>> n.pitch.accidental
        <accidental double-flat>
        '''
        alter = -1 * len(search.group(1))
        return self._addAccidental(n, alter, pm, t)

    def natural(self, n, search, pm, t):
        # noinspection PyShadowingNames
        '''
        called when an explicit natural has been found.  All pitches are natural without
        being specified, so not needed. Adds a natural accidental to it.

        >>> import re
        >>> tStr = 'En'
        >>> nToken = tinyNotation.NoteToken(tStr)
        >>> n = note.Note('E')
        >>> n.octave = 3
        >>> searchResult = re.search(nToken.pitchMap['natural'], tStr)
        >>> tPost = nToken.natural(n, searchResult, nToken.pitchMap['natural'], tStr)
        >>> tPost
        'E'
        >>> n.pitch.accidental
        <accidental natural>
        '''
        return self._addAccidental(n, 0, pm, t)

    def lowOctave(self, n, search, pm, t):
        # noinspection PyShadowingNames
        '''
        Called when a note of octave 3 or below is encountered.

        >>> import re
        >>> tStr = 'BBB'
        >>> nToken = tinyNotation.NoteToken(tStr)
        >>> n = note.Note('B')
        >>> searchResult = re.search(nToken.pitchMap['lowOctave'], tStr)
        >>> tPost = nToken.lowOctave(n, searchResult, nToken.pitchMap['lowOctave'], tStr)
        >>> tPost
        ''
        >>> n.octave
        1
        '''
        stepName = search.group(1)[0].upper()
        octaveNum = 4 - len(search.group(1))
        n.step = stepName
        n.octave = octaveNum
        t = re.sub(pm, '', t)
        return t

    def highOctave(self, n, search, pm, t):
        # noinspection PyShadowingNames
        '''
        Called when a note of octave 4 or higher is encountered.

        >>> import re
        >>> tStr = "e''"
        >>> nToken = tinyNotation.NoteToken(tStr)
        >>> n = note.Note('E')
        >>> searchResult = re.search(nToken.pitchMap['highOctave'], tStr)
        >>> tPost = nToken.highOctave(n, searchResult, nToken.pitchMap['highOctave'], tStr)
        >>> tPost
        ''
        >>> n.octave
        6
        '''
        stepName = search.group(1)[0].upper()
        octaveNum = 4 + len(search.group(2))
        n.step = stepName
        n.octave = octaveNum
        t = re.sub(pm, '', t)
        return t


class Converter:
    '''
    Main conversion object for TinyNotation.

    Accepts keywords:

    * `makeNotation=False` to get "classic" TinyNotation formats without
       measures, Clefs, etc.
    * `raiseExceptions=True` to make errors become exceptions.


    >>> tnc = tinyNotation.Converter('4/4 C##4 D e-8 f~ f f# g4 trip{f8 e d} C2=hello')
    >>> tnc.parse()
    <music21.tinyNotation.Converter object at 0x10aeefbe0>
    >>> tnc.stream.show('text')
    {0.0} <music21.stream.Measure 1 offset=0.0>
        {0.0} <music21.clef.TrebleClef>
        {0.0} <music21.meter.TimeSignature 4/4>
        {0.0} <music21.note.Note C##>
        {1.0} <music21.note.Note D>
        {2.0} <music21.note.Note E->
        {2.5} <music21.note.Note F>
        {3.0} <music21.note.Note F>
        {3.5} <music21.note.Note F#>
    {4.0} <music21.stream.Measure 2 offset=4.0>
        {0.0} <music21.note.Note G>
        {1.0} <music21.note.Note F>
        {1.3333} <music21.note.Note E>
        {1.6667} <music21.note.Note D>
        {2.0} <music21.note.Note C>
        {4.0} <music21.bar.Barline type=final>


    Or, breaking down what Parse does bit by bit:

    >>> tnc = tinyNotation.Converter('4/4 C##4 D e-8 f~ f f# g4 trip{f8 e d} C2=hello')
    >>> tnc.stream
    <music21.stream.Part 0x10acee860>
    >>> tnc.makeNotation
    True
    >>> tnc.stringRep
    '4/4 C##4 D e-8 f~ f f# g4 trip{f8 e d} C2=hello'
    >>> tnc.activeStates
    []
    >>> tnc.preTokens
    []
    >>> tnc.splitPreTokens()
    >>> tnc.preTokens
    ['4/4', 'C##4', 'D', 'e-8', 'f~', 'f', 'f#', 'g4', 'trip{f8', 'e', 'd}', 'C2=hello']
    >>> tnc.setupRegularExpressions()

    Then we parse the time signature:

    >>> tnc.parseOne(0, tnc.preTokens[0])
    >>> tnc.stream.coreElementsChanged()
    >>> tnc.stream.show('text')
    {0.0} <music21.meter.TimeSignature 4/4>

    Then the first note:

    >>> tnc.parseOne(1, tnc.preTokens[1])
    >>> tnc.stream.coreElementsChanged()
    >>> tnc.stream.show('text')
    {0.0} <music21.meter.TimeSignature 4/4>
    {0.0} <music21.note.Note C##>

    The next notes to 'g4' are pretty similar:

    >>> for i in range(2, 8):
    ...     tnc.parseOne(i, tnc.preTokens[i])
    >>> tnc.stream.coreElementsChanged()
    >>> tnc.stream.show('text')
    {0.0} <music21.meter.TimeSignature 4/4>
    {0.0} <music21.note.Note C##>
    {1.0} <music21.note.Note D>
    {2.0} <music21.note.Note E->
    {2.5} <music21.note.Note F>
    {3.0} <music21.note.Note F>
    {3.5} <music21.note.Note F#>
    {4.0} <music21.note.Note G>

    The next note starts a "State" since it has a triplet:

    >>> tnc.preTokens[8]
    'trip{f8'
    >>> tnc.parseOne(8, tnc.preTokens[8])
    >>> tnc.activeStates
    [<music21.tinyNotation.TripletState object at 0x10ae9dba8>]
    >>> tnc.activeStates[0].affectedTokens
    [<music21.note.Note F>]

    The state is still active for the next token:

    >>> tnc.preTokens[9]
    'e'
    >>> tnc.parseOne(9, tnc.preTokens[9])
    >>> tnc.activeStates
    [<music21.tinyNotation.TripletState object at 0x10ae9dba8>]
    >>> tnc.activeStates[0].affectedTokens
    [<music21.note.Note F>, <music21.note.Note E>]

    But the next token closes the state:

    >>> tnc.preTokens[10]
    'd}'
    >>> tnc.parseOne(10, tnc.preTokens[10])
    >>> tnc.activeStates
    []
    >>> tnc.stream.coreElementsChanged()
    >>> tnc.stream.show('text')
    {0.0} <music21.meter.TimeSignature 4/4>
    ...
    {4.0} <music21.note.Note G>
    {5.0} <music21.note.Note F>
    {5.3333} <music21.note.Note E>
    {5.6667} <music21.note.Note D>

    The last token has a modifier, which is an IdModifier:

    >>> tnc.preTokens[11]
    'C2=hello'
    >>> tnc.parseOne(11, tnc.preTokens[11])
    >>> tnc.stream.coreElementsChanged()
    >>> tnc.stream.show('text')
    {0.0} <music21.meter.TimeSignature 4/4>
    ...
    {5.6667} <music21.note.Note D>
    {6.0} <music21.note.Note C>
    >>> tnc.stream[-1].id
    'hello'

    Then calling tnc.postParse() runs the makeNotation:

    >>> tnc.postParse()
    >>> tnc.stream.show('text')
    {0.0} <music21.stream.Measure 1 offset=0.0>
        {0.0} <music21.clef.TrebleClef>
        {0.0} <music21.meter.TimeSignature 4/4>
        {0.0} <music21.note.Note C##>
        {1.0} <music21.note.Note D>
        {2.0} <music21.note.Note E->
        {2.5} <music21.note.Note F>
        {3.0} <music21.note.Note F>
        {3.5} <music21.note.Note F#>
    {4.0} <music21.stream.Measure 2 offset=4.0>
        {0.0} <music21.note.Note G>
        {1.0} <music21.note.Note F>
        {1.3333} <music21.note.Note E>
        {1.6667} <music21.note.Note D>
        {2.0} <music21.note.Note C>
        {4.0} <music21.bar.Barline type=final>

    Normally invalid notes or other tokens pass freely and drop the token:

    >>> x = converter.parse('tinyNotation: 4/4 c2 d3 e2')
    >>> x.show('text')
    {0.0} <music21.stream.Measure 1 offset=0.0>
        {0.0} <music21.clef.TrebleClef>
        {0.0} <music21.meter.TimeSignature 4/4>
        {0.0} <music21.note.Note C>
        {2.0} <music21.note.Note E>
        {4.0} <music21.bar.Barline type=final>

    But with the keyword 'raiseExceptions=True' a `TinyNotationException`
    is raised:

    >>> x = converter.parse('tinyNotation: 4/4 c2 d3 e2', raiseExceptions=True)
    Traceback (most recent call last):
    music21.tinyNotation.TinyNotationException: Could not parse token: 'd3'
    '''
    bracketStateMapping = {
        'trip': TripletState,
        'quad': QuadrupletState,
    }
    _modifierEqualsRe = re.compile(r'=([A-Za-z0-9]*)')
    _modifierStarRe = re.compile(r'\*(.*?)\*')
    _modifierAngleRe = re.compile(r'<(.*?)>')
    _modifierParensRe = re.compile(r'\((.*?)\)')
    _modifierSquareRe = re.compile(r'\[(.*?)]')
    _modifierUnderscoreRe = re.compile(r'_(.*)')

    def __init__(self, stringRep='', **keywords):
        self.stream = None
        self.stateDict = None
        self.stringRep = stringRep
        self.activeStates = []
        self.preTokens = None

        self.generalBracketStateRe = re.compile(r'(\w+){')
        self.tieStateRe = re.compile(r'~')

        self.tokenMap = [
            (r'(\d+\/\d+)', TimeSignatureToken),
            (r'r(\S*)', RestToken),
            (r'([a-gA-G]\S*)', NoteToken),  # last
        ]
        self.modifierEquals = IdModifier
        self.modifierStar = None
        self.modifierAngle = None
        self.modifierParens = None
        self.modifierSquare = None
        self.modifierUnderscore = LyricModifier

        self.keywords = keywords

        self.makeNotation = keywords.get('makeNotation', True)
        self.raiseExceptions = keywords.get('raiseExceptions', False)


        self.stateDictDefault = {'currentTimeSignature': None,
                                 'lastDuration': 1.0
                                 }
        self.load(stringRep)
        # will be filled by self.setupRegularExpressions()
        self._tokenMapRe = None

    def load(self, stringRep):
        '''
        Loads a stringRepresentation into `.stringRep`
        and resets the parsing state.

        >>> tnc = tinyNotation.Converter()
        >>> tnc.load('4/4 c2 d e f')
        >>> s = tnc.parse().stream
        >>> tnc.load('4/4 f e d c')
        >>> s2 = tnc.parse().stream
        >>> ns2 = s2.flat.notes

        Check that the duration of 2.0 from the first load did not carry over.

        >>> ns2[0].duration.quarterLength
        1.0
        >>> len(ns2)
        4
        '''
        self.stream = stream.Part()
        self.stateDict = copy.copy(self.stateDictDefault)
        self.stringRep = stringRep
        self.activeStates = []
        self.preTokens = []

    def splitPreTokens(self):
        '''
        splits the string into textual preTokens.

        Right now just splits on spaces, but might be smarter to ignore spaces in
        quotes, etc. later.
        '''
        self.preTokens = self.stringRep.split()  # do something better alter.

    def setupRegularExpressions(self):
        '''
        Regular expressions get compiled for faster
        usage.  This is called automatically by .parse(), but can be
        called separately for testing.  It is also important that it
        is not called in __init__ since subclasses should override the
        tokenMap, etc. for a class.
        '''
        self._tokenMapRe = []
        for rePre, classCall in self.tokenMap:
            try:
                self._tokenMapRe.append((re.compile(rePre), classCall))
            except sre_parse.error as e:
                raise TinyNotationException(
                    f'Error in compiling token, {rePre}: {e}'
                ) from e


    def parse(self):
        '''
        splitPreTokens, setupRegularExpressions, then runs
        through each preToken, and runs postParse.
        '''
        if self.preTokens == [] and self.stringRep != '':
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
        text t, possibly adding it to the stream.

        Checks for state changes, modifiers, tokens, and end-state brackets.
        '''
        t = self.parseStartStates(t)
        t, numberOfStatesToEnd = self.parseEndStates(t)
        t, activeModifiers = self.parseModifiers(t)

        # this copy is done so that an activeState can
        # remove itself from this list:
        for stateObj in self.activeStates[:]:
            t = stateObj.affectTokenBeforeParse(t)

        m21Obj = None
        tokenObj = None

        # parse token with state:
        hasMatch = False
        for tokenRe, tokenClass in self._tokenMapRe:
            matchSuccess = tokenRe.match(t)
            if matchSuccess is None:
                continue

            hasMatch = True
            tokenData = matchSuccess.group(1)
            tokenObj = tokenClass(tokenData)
            try:
                m21Obj = tokenObj.parse(self)
                if m21Obj is not None:  # can only match one.
                    break
            except TinyNotationException as excep:
                if self.raiseExceptions:
                    raise TinyNotationException(f'Could not parse token: {t!r}') from excep

        if not hasMatch and self.raiseExceptions:
            raise TinyNotationException(f'Could not parse token: {t!r}')

        if m21Obj is not None:
            for stateObj in self.activeStates[:]:  # iterate over copy so we can remove.
                m21Obj = stateObj.affectTokenAfterParseBeforeModifiers(m21Obj)

        if m21Obj is not None:
            for modObj in activeModifiers:
                m21Obj = modObj.postParse(m21Obj)

        if m21Obj is not None:
            for stateObj in self.activeStates[:]:  # iterate over copy so we can remove.
                m21Obj = stateObj.affectTokenAfterParse(m21Obj)

        if m21Obj is not None:
            self.stream.coreAppend(m21Obj)

        for i in range(numberOfStatesToEnd):
            stateToRemove = self.activeStates.pop()
            possibleObj = stateToRemove.end()
            if possibleObj is not None:
                self.stream.coreAppend(possibleObj)


    def parseStartStates(self, t):
        # noinspection PyShadowingNames
        '''
        Changes the states in self.activeStates, and starts the state given the current data.
        Returns a newly processed token.

        A contrived example:

        >>> tnc = tinyNotation.Converter()
        >>> tnc.setupRegularExpressions()
        >>> len(tnc.activeStates)
        0
        >>> tIn = 'trip{quad{f8~'
        >>> tOut = tnc.parseStartStates(tIn)
        >>> tOut
        'f8'
        >>> len(tnc.activeStates)
        3
        >>> tripState = tnc.activeStates[0]
        >>> tripState
        <music21.tinyNotation.TripletState object at 0x10afaa630>

        >>> quadState = tnc.activeStates[1]
        >>> quadState
        <music21.tinyNotation.QuadrupletState object at 0x10adcb0b8>

        >>> tieState = tnc.activeStates[2]
        >>> tieState
        <music21.tinyNotation.TieState object at 0x10afab048>

        >>> tieState.parent
        <weakref at 0x10adb31d8; to 'Converter' at 0x10adb42e8>
        >>> tieState.parent() is tnc
        True
        >>> tieState.stateInfo
        '~'
        >>> quadState.stateInfo
        'quad{'


        Note that the affected tokens haven't yet been added:

        >>> tripState.affectedTokens
        []

        Unknown state gives a warning or if `.raisesException=True` raises a
        TinyNotationException

        >>> tnc.raiseExceptions = True
        >>> tIn = 'blah{f8~'
        >>> tOut = tnc.parseStartStates(tIn)
        Traceback (most recent call last):
        music21.tinyNotation.TinyNotationException: Incorrect bracket state: 'blah'
        '''
        bracketMatchSuccess = self.generalBracketStateRe.search(t)
        while bracketMatchSuccess:
            stateData = bracketMatchSuccess.group(0)
            bracketType = bracketMatchSuccess.group(1)
            t = self.generalBracketStateRe.sub('', t, count=1)
            bracketMatchSuccess = self.generalBracketStateRe.search(t)
            if bracketType not in self.bracketStateMapping:
                msg = f'Incorrect bracket state: {bracketType!r}'
                if self.raiseExceptions:
                    raise TinyNotationException(msg)

                # else  # pragma: no cover
                environLocal.warn(msg)
                continue

            stateObj = self.bracketStateMapping[bracketType](self, stateData)
            stateObj.start()
            self.activeStates.append(stateObj)


        tieMatchSuccess = self.tieStateRe.search(t)
        if tieMatchSuccess:
            stateData = tieMatchSuccess.group(0)
            t = self.tieStateRe.sub('', t)
            tieState = TieState(self, stateData)
            tieState.start()
            self.activeStates.append(tieState)

        return t

    def parseEndStates(self, t):
        '''
        Trims the endState token ('}') from the t string
        and then returns a two-tuple of the new token and number
        of states to remove:

        >>> tnc = tinyNotation.Converter()
        >>> tnc.parseEndStates('C4')
        ('C4', 0)
        >>> tnc.parseEndStates('C4}}')
        ('C4', 2)
        '''
        endBrackets = t.count('}')
        t = t.replace('}', '')
        return t, endBrackets

    def parseModifiers(self, t):
        '''
        Parses `modifierEquals`, `modifierUnderscore`, `modifierStar`, etc.
        for a given token and returns the modified token and a
        (possibly empty) list of activeModifiers.

        Modifiers affect only the current token.  To affect
        multiple tokens, use a :class:`~music21.tinyNotation.State` object.
        '''
        activeModifiers = []

        for modifierName in ('Equals', 'Star', 'Angle', 'Parens', 'Square', 'Underscore'):
            modifierClass = getattr(self, 'modifier' + modifierName, None)
            if modifierClass is None:
                continue
            modifierRe = getattr(self, '_modifier' + modifierName + 'Re', None)
            foundIt = modifierRe.search(t)
            if foundIt is not None:  # is not None is necessary
                modifierData = foundIt.group(1)
                t = modifierRe.sub('', t)
                modifierObject = modifierClass(modifierData, t, self)
                activeModifiers.append(modifierObject)

        for modObj in activeModifiers:
            modObj.preParse(t)

        return t, activeModifiers

    def postParse(self):
        '''
        Called after all the tokens have been run.

        Currently runs `.makeMeasures` on `.stream` unless `.makeNotation` is `False`.
        '''
        if self.makeNotation is not False:
            self.stream.makeMeasures(inPlace=True)


class Test(unittest.TestCase):
    parseTest = '1/4 trip{C8~ C~_hello C=mine} F~ F~ 2/8 F F# quad{g--16 a## FF(n) g#} g16 F0'

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
        self.assertEqual(sfn[1].lyric, 'hello')
        self.assertEqual(sfn[2].id, 'mine')
        self.assertEqual(sfn[6].pitch.accidental.alter, 1)
        self.assertEqual(sfn[7].pitch.accidental.alter, -2)
        self.assertEqual(sfn[9].editorial.ficta.alter, 0)
        self.assertEqual(sfn[12].duration.quarterLength, 1.0)
        self.assertEqual(sfn[12].expressions[0].classes, expressions.Fermata().classes)


class TestExternal(unittest.TestCase):  # pragma: no cover

    def testOne(self):
        c = Converter(Test.parseTest)
        c.parse()
        c.stream.show('musicxml.png')


# TODO: Chords
# ------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [Converter, Token, State, Modifier]

if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
