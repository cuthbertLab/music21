# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         alpha.trecento.notation.py
# Purpose:      music21 classes for representing Trecento notation
#
# Authors:      Varun Ramaswamy
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#------------------------------------------------------------------------------

'''
Tools for creating Punctus and Divisione objects unique to Trecento notation.

Other objects found in medieval and renaissance music (such as rests, notes,
and clef) can be found in the module `music21.medren`.

Also contains functions for converting Trecento notation to modern notation.
'''
import unittest


from music21 import base
from music21 import clef
from music21 import common
from music21 import duration
from music21 import exceptions21
from music21 import meter
from music21 import note
from music21 import stream
from music21 import tie
from music21 import tinyNotation

from music21 import environment
_MOD = "trecento/notation.py"  
environLocal = environment.Environment(_MOD)


_validDivisiones = {
    (None, None): 0,
    ('quaternaria', '.q.'): 4,
    ('senaria imperfecta', '.i.'): 6,
    ('senaria perfecta', '.p.'): 6,
    ('novenaria', '.n.'): 9,
    ('octonaria', '.o.'): 8,
    ('duodenaria', '.d.'): 12,
    }


class ClefToken(tinyNotation.Token):
    def parse(self, parent):
        from music21.alpha import medren
        t = self.token
        menclef = medren.MensuralClef(t[1])
        if len(t) > 2:
            menclef.line = t[2]
        return menclef

class DivisioneToken(tinyNotation.Token):
    def parse(self, parent):
        return Divisione(self.token)

class PunctusToken(tinyNotation.Token):
    def parse(self, parent):
        return Punctus()
    
class LigatureState(tinyNotation.State):
    '''
    defines that the notes in here will be in a ligature
    '''
    def start(self):
        from music21.alpha import medren
        self.ligature = medren.Ligature()
        self.ligature.state = self
        self.obliqueNums = []
        self.squareNums = []
        self.ligatureStems = []
        self.reverseNums = []

    def end(self):
        for o in self.obliqueNums:
            self.ligature.makeOblique(o)
        for s in self.squareNums:
            self.ligature.makeSquare(s)
        for i, d, o in self.ligatureStems:
            self.ligature.setStem(i, d, o)
        for i in self.reverseNums:
            self.ligature.setReverse(i, True)
        del(self.ligature.state)
        return self.ligature # not nothing
    
    def affectTokenAfterParseBeforeModifiers(self, n):
        n.activeLigature = self.ligature
        n.numberInLigature = len(self.affectedTokens)
        self.ligature.pitches = self.ligature.pitches + [n.pitch]
        return n
    
    def affectTokenAfterParse(self, n):
        super(LigatureState, self).affectTokenAfterParse(n)
        #        n.ligatureParent = self
        return None # do not add note to Stream

class MensuralTypeModifier(tinyNotation.Modifier):
    def postParse(self, n):
        mensuralType = self.modifierData
        if mensuralType in ['Mx','L','B','SB','M','SM']:
            n.mensuralType = mensuralType
        if hasattr(n, 'activeLigature') and mensuralType == 'Mx':
            n.activeLigature.setMaxima(n.numberInLigature, True)
        parent = common.unwrapWeakref(self.parent)
        parent.stateDict['previousMensuralType'] = mensuralType
        return n

class StemsModifier(tinyNotation.Modifier):
    def postParse(self, m21Obj):
        direction = {'': None, 'S': 'side', 'D': 'down', 'U':'up'}
        for stem in self.modifierData.split('/'):
            if stem in direction:
                m21Obj.setStem(direction[stem])
            else:
                raise TrecentoNotationException('could not determine stem direction from %s' % stem)

        return m21Obj

class FlagsModifier(tinyNotation.Modifier):
    def postParse(self, m21Obj):
        direction = {'': None, 'S': 'side', 'D': 'down', 'U':'up'}
        orientation = {'': None,'L': 'left', 'R': 'right'}
        for flag in self.modifierData.split('/'):
            if len(flag) > 1 and (flag[0] in direction) and (flag[1] in orientation):
                m21Obj.setFlag(direction[flag[0]], orientation[flag[1]])
            else:
                raise TrecentoNotationException('cannot determine flag from %s' % flag)
        return m21Obj

class LigatureStemsModifier(tinyNotation.Modifier):
    def postParse(self, m21Obj):
        direction = {'D': 'down', 'U':'up'}
        orientation = {'L': 'left', 'R': 'right'}
        try:
            d = direction[self.modifierData[0]]
            o = orientation[self.modifierData[1]]
            tup = (m21Obj.numberInLigature, d, o)
            m21Obj.activeLigature.state.ligatureStems.append(tup)
        except (IndexError, KeyError):
            raise TrecentoNotationException('cannot determine ligature stem from %s' % self.modifierData)
        return m21Obj


class LigatureNoteheadModifier(tinyNotation.Modifier):
    def postParse(self, m21Obj):
        try:
            n = self.modifierData[0]
            if n == 'o':
                m21Obj.activeLigature.state.obliqueNums.append(m21Obj.numberInLigature)
            elif n == 's':
                m21Obj.activeLigature.state.squareNums.append(m21Obj.numberInLigature)
            else:
                raise IndexError
        except (IndexError, KeyError):
            raise TrecentoNotationException('cannot make out notehead shape from %s' % self.modifierData)
        return m21Obj

class LigatureReverseModifier(tinyNotation.Modifier):
    def __init__(self, modifierData, modifierString, parent):
        self.modifierData = modifierData
        self.modifierString = modifierString
        self.parent = common.wrapWeakref(parent)
        
    def postParse(self, n):
        n.activeLigature.state.reverseNums.append(n.numberInLigature)
# #------------------------------------------------------------------------------
# def breakString(string, startBreakChar, endBreakChar,
#     func=lambda s: s.split()):
# 
#     broken = []
#     while len(string) > 0:
#         startInd = string.find(startBreakChar)
#         endInd = string.find(endBreakChar) + 1
# 
#         if startInd == -1 and endInd == 0:
#             broken += string.split()
#             break
# 
#         elif startInd != -1 and endInd != 0:
#             while string[startInd] != ' ':
#                 startInd -= 1
# 
#             broken += func(string[:startInd])
#             broken.append(string[startInd:endInd])
#             string = string[endInd + 1:]
# 
#         else:
#             raise TrecentoNotationException('%s, %s invalid indices' % (startInd, endInd))
#     return broken


class TrecentoTinyConverter(tinyNotation.Converter):
    r'''
    These are modified from a standard lilypond format called TinyNotation.

    Here are some important points about how to create notes and streams:

    1.  Note names are: a,b,c,d,e,f,g. r indicates a rest, and p indicates a
        punctus.

    2.  Note octaves are specified as follows:

        :CC to BB:
            from C below bass clef to second-line B in bass clef

        :C to B:
            from bass clef C to B below middle C.

        :c  to b:
            from middle C to the middle of treble clef

        :c' to b':
            from C in treble clef to B above treble clef (make sure you’re NOT
            putting in smart quotes)

    In 14th c. music, C to B and c to b will be most common

    3.  Flats, sharps, and naturals are notated as #,- (not b), and (if needed)
        n. If the accidental is above the staff (i.e., editorial), enclose it
        in parentheses: (#), etc.  Make sure that flats in the key signatures
        are explicitly specified.

    4.  The syntax structure for a mensural note is as follows:

        ::

            pitch(mensuralType)[stems]_flags

        A mensuralType may be any of Mx for maxima, L for longa, B for brevis,
        SB for semibrevis, M for minima, or SM for semimina. For more
        information on mensural types, please see the documentation for
        :class:`music21.medren.generalMensuralNote`.

        If no mensural type is specified, it is assumed to be the same as the
        previous note. I.e., c(SB) B c d is a string of semibreves.

    >>> tTNN = alpha.trecento.notation.TrecentoTinyConverter('a(M)').parse().stream.flat.notes[0]
    >>> tTNN.pitch
    <music21.pitch.Pitch A4>

    >>> tTNN.mensuralType
    'minima'

    An additional stem may be added by specifying direction: S for a sidestem,
    D for a downstem, and an empty string to reset.

    For example, adding [D] to a note string would add a downstem to that note.
    Stems must still follow the rules outlined in
    :meth:`music21.medren.MensuralNote.setStem()`.

    >>> tTNN = alpha.trecento.notation.TrecentoTinyConverter('a(SB)[S]').parse().stream.flat.notes[0]
    >>> tTNN.getStems()
    ['side']

    >>> tTNN = alpha.trecento.notation.TrecentoTinyConverter('a(M)[D]').parse().stream.flat.notes[0]
    >>> tTNN.getStems()
    ['up', 'down']

    A flag may be added by specifying direction of stem and orientation of
    flag. Valid directions are U for up, D for down, and an empty string to
    reset (sidestems cannot have flags). Valid orientations are L for left, R
    for right, and an empty string to reset. For example, adding _DL to a note
    string would add a left flag to that note's downstem. Flags must still
    follow the rules outlined in :meth:`music21.medren.MensuralNote.setFlag()`.

    >>> tTNN = alpha.trecento.notation.TrecentoTinyConverter('a(SM)_UL').parse().stream.flat.notes[0]
    >>> tTNN.getStems()
    ['up']

    >>> flags = tTNN.getFlags()
    >>> sorted(list(flags.keys()))
    ['up']
    >>> flags['up']
    'left'

    Multiple flags may be added by placing a slash between
    direction-orientation pairs, as shown in the following complex example:

    >>> tTNN = alpha.trecento.notation.TrecentoTinyConverter(
    ...     'a(SM)[D]_UL/DR').parse().stream.flat.notes[0]
    >>> tTNN.pitch
    <music21.pitch.Pitch A4>
    >>> tTNN.getStems()
    ['up', 'down']

    >>> flags = tTNN.getFlags()
    >>> sorted(list(flags.keys()))
    ['down', 'up']
    >>> flags['down']
    'right'
    >>> flags['up']
    'left'

    5.  It is also possible to create ligatures using the
        TinyTrecentoNotationNote class. Put all notes in a ligature within `lig{`
        and `}` symbols.

    >>> ttc = alpha.trecento.notation.TrecentoTinyConverter('lig{f g a g f }').parse()
    >>> ts = ttc.stream
    >>> ts.show('text')
    {0.0} <music21.stream.Measure 1 offset=0.0>
        {0.0} <music21.clef.TrebleClef>
        {0.0} <music21.meter.TimeSignature 4/4>
        {0.0} <music21...medren.Ligature object at 0x...>
        {0.0} <music21.bar.Barline style=final>
    >>> tTNN = ts.flat.getElementsByClass('Ligature')[0]
    >>> tTNN
    <music21...medren.Ligature...>
    >>> [str(p) for p in tTNN.pitches]
    ['F4', 'G4', 'A4', 'G4', 'F4', 'C4']

    The notes within a ligature have the syntax pitch<notehead>[stems](maxima).
    Valid notehead shapes are s for square and o for oblique. Valid stem
    directions are U for up and D for down, and valid orientations are L for
    left and R for right. To set a note of a ligature as a maxima, append (Mx)
    to the note string. To set a note of a ligature as reversed, append a
    forward slash followed by an R ("/R") to the note string.

    Note, ligatures must follow the rules outlined by
    :class:`music21.medren.Ligature`.

    Examples:

    >>> ts = alpha.trecento.notation.TrecentoTinyConverter(r'lig{f a[DL]/R}').parse().stream
    >>> tTNN = ts.flat.getElementsByClass('Ligature')[0]
    >>> tTNN.getStem(1)
    ('down', 'left')

    >>> tTNN.isReversed(1)
    True


    >>> tTNN = alpha.trecento.notation.TrecentoTinyConverter(
    ...     'lig{f<o> g a[UR] g f(Mx)}').parse().stream.flat.getElementsByClass('Ligature')[0]        
    >>> print([n.mensuralType for n in tTNN.notes])
    ['longa', 'brevis', 'semibrevis', 'semibrevis', 'maxima']

    >>> tTNN.getNoteheadShape(1)
    'oblique'

    6.  Separate objects in a tiny notation by spaces. To add a mensural
        clef to the stream, add $, followed by the clef type (F or C) to the
        string. If the clef line on the staff is non-standard, include that
        after the type.

        For example, $F2 would indicate an F-clef on the second line of the
        staff. To add a divisione to a tiny notation stream, simply include the
        divisione abbreviation in the string. For example, .p. would indicate
        senaria perfecta.

    >>> tTNS = alpha.trecento.notation.TrecentoTinyConverter(
    ...     '$C3 .p. c(SB) d e p d(B) lig{e d c}').parse().stream.flat
    >>> tTNS.show('text')
    {0.0} <music21.bar.Barline style=final>
    {0.0} <music21.clef.MensuralClef>
    {0.0} <music21.alpha.trecento.notation.Divisione .p.>
    {0.0} <music21...medren.MensuralNote semibrevis C>
    {0.0} <music21...medren.MensuralNote semibrevis D>
    {0.0} <music21...medren.MensuralNote semibrevis E>
    {0.0} <music21.alpha.trecento.notation.Punctus...>
    {0.0} <music21...medren.MensuralNote brevis D>
    {0.0} <music21...medren.Ligature...>
    '''

    def __init__(self, stringRep=""):
        super(TrecentoTinyConverter, self).__init__(stringRep)
        self.tokenMap = [
                         (r'(\$[A-Z]\d?)', ClefToken),
                         (r'(\.[a-z]\.)', DivisioneToken),
                         (r'(p)', PunctusToken),
                         (r'r(\S*)', TrecentoRestToken),
                         (r'(\S*)', TrecentoNoteToken)
                         ]
        self.stateMap = [
                        (r'trip\{', tinyNotation.TripletState),
                        (r'lig\{', LigatureState)                          
                         ]
        self.modifierMap = [
                        (r'\(([A-Z][A-Za-z]?)\)', MensuralTypeModifier),
                        (r'\[([A-Z]?(\/[A-Z])*)\]', StemsModifier),
                        (r'\_(([A-Z][A-Z])?(\/[A-Z][A-Z])*)', FlagsModifier),
                        (r'\[([A-Z][A-Z])\]', LigatureStemsModifier),
                        (r'\<([a-z])\>', LigatureNoteheadModifier),
                        (r'(\/R)', LigatureReverseModifier),    
                        ]
        self.stateDict['lastDuration'] = 0.0
        self.stateDict['previousMensuralType'] = None


class TrecentoRestToken(tinyNotation.RestToken):
    def parse(self, parent):
        from music21.alpha import medren
        r = medren.MensuralRest()  # to-do -- affect..
        r.mensuralType = parent.stateDict['previousMensuralType']

class TrecentoNoteToken(tinyNotation.NoteToken):
    '''
    For documentation please see :class:`music21.alpha.trecento.notation.TrecentoTinyConverter`.
    '''
    def parse(self, parent):
        from music21.alpha import medren
        n = medren.MensuralNote()
        self.getPitch(n, self.token)
        n.mensuralType = parent.stateDict['previousMensuralType']
        return n

#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

class Punctus(base.Music21Object):
    '''
    An object representing a punctus, found in Trecento notation.
    '''
    def __init__(self):
        self._fontString = '0x70'
        base.Music21Object.__init__(self)

    def _getFontString(self):
        return self._fontString

    fontString = property(_getFontString,
                          doc = '''The utf-8 code corresponding the punctus in Cicionia font''')

class Divisione(meter.TimeSignature):
    '''
    An object representing a divisione found in Trecento Notation.
    Takes one argument, nameOrSymbol. This is the name of the divisione, or its corresponding letter.
    The default value for this argument is '.p.'

    Valid names are 'quaternaria', 'senaria imperfect', 'senaria perfecta', 'novenaria', 'octonaria', and 'duodenaria'.
    The corresponding symbols are '.q.', '.i.', '.p.', '.n.', '.o.', and '.d.'.

    >>> d = alpha.trecento.notation.Divisione('senaria imperfecta')
    >>> d.standardSymbol
    '.i.'

    >>> d = alpha.trecento.notation.Divisione('.p.')
    >>> d.name
    'senaria perfecta'

    >>> d = alpha.trecento.notation.Divisione('q')
    >>> d.standardSymbol
    '.q.'

    '''
    def __init__(self, nameOrSymbol = '.p.'):
        self.name = None
        self.standardSymbol = None
        self._minimaPerBrevis = 0

        if len(nameOrSymbol) == 1:
            nameOrSymbol = '.' + str(nameOrSymbol) + '.'

        for d in _validDivisiones:
            if nameOrSymbol in d:
                self.name = d[0]
                self.standardSymbol = d[1]
                self._minimaPerBrevis = _validDivisiones[d]

        if self.standardSymbol == None:
            self.timeString = None
        elif self.standardSymbol == '.q.':
            self.timeString = '2/4'
        elif self.standardSymbol == '.i.':
            self.timeString = '6/8'
        elif self.standardSymbol == '.p.':
            self.timeString = '3/4'
        elif self.standardSymbol == '.n.':
            self.timeString = '9/8'
        elif self.standardSymbol == '.o.':
            self.timeString = '2/4'
        elif self.standardSymbol == '.d.':
            self.timeString = '3/4'
        else:
            raise TrecentoNotationException('cannot make out the divisione from name or symbol %s' % nameOrSymbol)

        if self.timeString is not None:
            meter.TimeSignature.__init__(self, self.timeString)

    def __str__(self):
        return '<music21.alpha.trecento.notation.Divisione %s>' % self.standardSymbol

    __repr__ = __str__

    def _getMinimaPerBrevis(self):
        return self._minimaPerBrevis

    def _setMinimaPerBrevis(self, mPM):
        self._minimaPerBrevis = mPM

    minimaPerBrevis = property(_getMinimaPerBrevis, _setMinimaPerBrevis,
                                doc = '''Used to get and set the number of minima in a 'measure' (the number of minima before a punctus occurs) under the given divisione.


                                >>> n = alpha.trecento.notation.Divisione('.n.')
                                >>> n.minimaPerBrevis
                                9
                                >>> n.minimaPerBrevis = 18
                                >>> n.minimaPerBrevis
                                18

                                ''')

def convertTrecentoStream(inpStream, inpDiv = None):
    u'''
    Take one argument: input stream.
    Converts an entire stream containing only mensural and trecento objects into one containing modern clef, note, and time signature objects.
    The converted stream preserves the structure of the original stream, converting only the mensural and trecento objects.

    This stream must have all of the qualifications present in the documentation for :meth:`music21.medren.breakMensuralStreamIntoBrevisLengths`. Furthermore, no non-mensural or non-trecento objects (other than streams and formatting) may be present in the input streams.

    Examples:

    .. image:: images/medren_SePerDureca.*
        :width: 600

    Anonymous, Se per dureça.  Padua, Biblioteca Universitaria, MS 1115.  Folio Ar.

    >>> upperString = ".p. $C1 g(B) g(M) f e g f e p g(SB) f(SM) e d e(M) f p e(SB) e(SM) f e d(M) c p "
    >>> upperString += "d(SB) r e p f(M) e d e d c p d(SB) c(M) d c d p e(SB) r(M) g f e p g(SB) a(SM) g f e(M) d p "
    >>> upperString += "e(SB) f(SM) e d c(M) d e(L) a(SB) a p b(M) a g a g f p g f e f e f p "
    >>> upperString += "g(SB) g(SM) a g f e d p e(SB) r(M) f(SM) e d e(M) p d(SB) r e(M) f p "
    >>> upperString += "g(SB) d r(M) e p f e d e d c p d(SB) d(M) e(SB) c(M) p d(SB) c(M) d c B c(L) "
    >>> upperString += "c'(SB)[D] c' p c'(SM) b a  b(M) c' b c' p b(SM) a g a(M) b a b p "
    >>> upperString += "g(SB) g(SM) a g f e d p e(SB) r e(M) f p g f e f e f p g(SB) r g(M) f p "
    >>> upperString += "g(SB) f(SM) e d e(M) f e(L) a(M) b a b g(SB) p c'(M) b a c' b a p "
    >>> upperString += "b c' b a g a p b(SB) c'(SM) b a g(M) f p a(SB) a(M) g(SB) f(M) p "
    >>> upperString += "e(SB) r g(M) f p g f e f e d p c(SB) d r p a g(SM) a g f e d p e(M) r f(SM) e d e(SB) d(Mx)"

    >>> lowerString = ".p. $C3 c(L) G(B) A(SB) B c p d c r p A B c p d c B p lig{A<o>[DL] G} A c B A(L) "
    >>> lowerString += "A(SB) A p  G A B p c c(M) B(SB) A(M) p G(SB) G p A B c p d A r p G[D] A p "
    >>> lowerString += "B B(M) c(SB) c(M) p d(SB) d(M) A(SB) A(M) p G(SB) A B C(L) "
    >>> lowerString += "c(SB)[D] c e(B) d c(SB) c d p e d r p c c(M) d(SB) d(M) p c(SB) r r p "
    >>> lowerString += "c d c(M) d e(L) d(SB)[D] e p c[D] d p e e(M) d(SB) c(M) p B(SB) A B(M) c p "
    >>> lowerString += "d(SB) d(M) c(SB) d(M) p e(SB) d r p c c(M) A(SB) B(M) p c(SB) B B p A B[D] p A B c d(Mx)"

    >>> SePerDureca = stream.Stream()
    >>> SePerDureca.append(alpha.trecento.notation.TrecentoTinyConverter(upperString).parse().stream.flat)
    >>> SePerDureca.append(alpha.trecento.notation.TrecentoTinyConverter(lowerString).parse().stream.flat)

    >>> SePerDurecaConverted = alpha.trecento.notation.convertTrecentoStream(SePerDureca)
    <BLANKLINE>
    Converting stream ... 
    ...

    >>> #_DOCS_HIDE SePerDurecaConverted.show()

    .. image:: images/medren_SePerDurecaConverted.*
        :width: 600

    '''
    from music21.alpha import medren

    div = inpDiv
    offset = 0
    # hierarchy = ['measure', 'part', 'score']

    convertedStream = None
    if 'measure' in inpStream.classes:
        convertedStream = stream.Measure()
    elif 'part' in inpStream.classes:
        convertedStream = stream.Part()
    elif 'score' in inpStream.classes:
        convertedStream = stream.Measure()
    else:
        convertedStream = stream.Stream()

    measuredStream = medren.breakMensuralStreamIntoBrevisLengths(inpStream, inpDiv)
    print('')

    for e in measuredStream:

        if ('Metadata' in e.classes) or  ('TextBox' in e.classes): #Formatting
            convertedStream.append(e)

        elif 'MensuralClef' in e.classes:
            pass

        elif 'Divisione' in e.classes:
            div = e

        elif e.isMeasure:
            print('    Converting measure %s' % e.number)
            measureList = convertBrevisLength(e, convertedStream, inpDiv = div, measureNumOffset = offset)
            for m in measureList:
                convertedStream.append(m)

        elif e.isStream:
            print('Converting stream %s' % e)
            convertedPart = convertTrecentoStream(e, inpDiv = div)
            convertedStream.insert(0, convertedPart)

        else:
            raise medren.MedRenException('Object %s cannot be processed as part of a trecento stream' % e)

    return convertedStream

def convertBrevisLength(brevisLength, convertedStream, inpDiv = None, measureNumOffset = 0):
    '''
    Takes two required arguments, a measure object and a stream containing modern objects.
    Takes two optional arguments, inpDiv and measureNumOffset.

    :meth:`music21.alpha.trecento.notation.convertBrevisLength` converts each of the objects in the measure to their modern equivalents using the BrevisLengthTranslator object.
    inpDiv is a divisione possibly coming from a some higher context. measureNumOffset helps calculate measure number.

    This acts as a helper method to improve the efficiency of :meth:`music21.alpha.trecento.notation.convertTrecentoStream`.
    '''
    div = inpDiv
    m = stream.Measure(number = brevisLength.number + measureNumOffset)
    rem = None
    measureList = []

    mList = list(brevisLength.recurse())[1:]

    tempTBL = BrevisLengthTranslator(div, mList)

    lenList = tempTBL.getKnownLengths()

    for item in mList:
        if 'Divisione' in item.classes:
            if div is None:
                div = item
            else:
                raise TrecentoNotationException('divisione %s not consistent within heirarchy' % item)
                #Should already be caught by medren.breakMensuralStreamIntoBrevisLengths, but just in case...
    mDur = 0
    if div is not None:
        rem = div.barDuration.quarterLength

        if brevisLength.number == 0:
            m.append(clef.TrebleClef())
            m.append(meter.TimeSignature(div.timeString)) #Trusting that divisione won't change while one voice is holding.
        if div.standardSymbol in ['.o.', '.d.']:
            mDur = 0.25
        else:
            mDur = 0.5
    else:
        raise TrecentoNotationException('Cannot find or determine  or divisione')

    if lenList[0] > div.minimaPerBrevis: #Longa, Maxima
        startNote = note.Note(mList[0].pitch)
        startNote.duration = div.barDuration
        startNote.tie = tie.Tie('start')
        m.append(startNote)
        measureList.append(m)

        for dummy in range(int(lenList[0]/div.minimaPerBrevis) - 2):
            measureNumOffset += 1

            tempMeasure = stream.Measure(number = brevisLength.number + measureNumOffset)
            tempNote = note.Note(mList[0].pitch)
            tempNote.duration = div.barDuration
            tempNote.tie = tie.Tie('continue')
            tempMeasure.append(tempNote)
            measureList.append(tempMeasure)

        measureNumOffset += 1
        finalMeasure = stream.Measure(number = brevisLength.number + measureNumOffset)
        finalNote = note.Note(mList[0].pitch)
        finalNote.duration = div.barDuration
        finalNote.tie = tie.Tie('stop')
        finalMeasure.append(finalNote)
        measureList.append(finalMeasure)

    else:
        for i in range(len(mList)):
            if 'MensuralRest' in mList[i].classes:
                n = note.Rest()
            elif 'MensuralNote' in mList[i].classes:
                n = note.Note(mList[i].pitch)

            dur = lenList[i]*mDur

            if (rem - dur) > -0.0001: #Fits w/i measure up to rounding error
                n.duration = duration.Duration(dur)
                m.append(n)
                rem -= dur
            else: #Syncopated across barline
                n.duration = duration.Duration(rem)
                n.tie = tie.Tie('start')
                m.append(n)
                measureList.append(m)
                measureNumOffset += 1

                m = stream.Measure(number = brevisLength.number + measureNumOffset)
                n_tied = note.Note(mList[i].pitch)
                n_tied.duration = duration.Duration(dur - rem)
                n_tied.tie = tie.Tie('end')
                m.append(n_tied)
                rem = div.barDuration.quarterLength - dur + rem
        measureList.append(m)

    return measureList

class BrevisLengthTranslator(object):
    '''
    The class :class:`music21.alpha.trecento.notation.BrevisLengthTranslator` takes a
    divisione sign and a list comprising one brevis length's worth of mensural
    or trecento objects as arguments.

    The method
    :meth:`music21.alpha.trecento.notation.BrevisLengthTranslator.getKnownLengths`
    takes no arguments, and returns a list of floats corresponding to the
    length (in minima) of each object in the list.

    Currently, this class is used only to improve the efficiency of
    :attr:`music21.medren.GeneralMensuralNote.duration`.

    This acts a helper class to improve the efficiency of
    :class:`music21.alpha.trecento.notation.convertBrevisLength`.

#    >>> names = ['SM', 'SM', 'SM', 'SM', 'SB', 'SB', 'SB', 'SB', 'SB', 'SM', 'SM', 'SM']
#    >>> BL = [medren.MensuralNote('A', n) for n in names]
#    >>> BL[3] = medren.MensuralRest('SM')
#    >>> for mn in BL[-3:]:
#    ...    mn.setFlag('up', 'left')
#    >>> for mn in BL[4:9]:
#    ...    mn.setStem('down')
#    >>> TBL = alpha.trecento.notation.BrevisLengthTranslator(div, BL)
#    >>> TBL.getKnownLengths()
#    [0.5, 0.5, 0.5, 0.5, 4.0, 4.0, 4.0, 4.0, 4.0, 0.666..., 0.666..., 0.666...]

    '''

    def __init__(self, divisione = None, BL = [], pDS = False):

        self.div = divisione
        self.brevisLength = BL

        self.unchangeableNoteLengthsList = []
        self.unknownLengthsDict = {'semibrevis':[],
                                   'semibrevis_downstem':[],
                                   'semiminima_right_flag':[],
                                   'seminima_left_flag':[],
                                   'semiminima_rest':[]
                                   }
        self.knownLengthsList = []

        self.numberOfBreves = 0
        self.numberOfDownstems = 0
        self.numberOfLeftFlags = 0
        self.numberOfRightFlags = 0
        self.numberOfSMRests = 0

        self.minimaRemaining = float(self.div.minimaPerBrevis)
        self.minRem_tracker = pDS
        self.doubleNum = 0

    def getKnownLengths(self):
        if 'Divisione' in self.div.classes:
            self.knownLengthsList = self.translate()
        else:
            raise TrecentoNotationException('%s not recognized as divisione' % self.div)
        return self.knownLengthsList

    def getBreveStrength(self, lengths):
        '''
        :meth:`BrevisLengthTranslator._evaluateBL` takes divisione, a brevis
        length's worth of mensural or trecento objects in a list, and a list of lengths
        corresponding to each of those objects as arguments.

        This method returns the *strength* of the list based on those lengths.
        A *strong* list has longer notes on its stronger beats. Only valid for Trecento notation.

        In this example, we test two possible interpretations for the same measure
        and see that the second is more logical.  Note that the strength itself is meaningless
        except when compared to other possible lengths for the same notes.

        >>> from music21.alpha import medren

        >>> div = alpha.trecento.notation.Divisione('.n.')
        >>> names = ['SB', 'M', 'M', 'M', 'SB']
        >>> BL = [medren.MensuralNote('A', n) for n in names]
        >>> TBL = alpha.trecento.notation.BrevisLengthTranslator(div, BL)
        >>> TBL.getBreveStrength([2.0, 1.0, 1.0, 1.0, 4.0])
        2.0555...
        >>> TBL.getBreveStrength([3.0, 1.0, 1.0, 1.0, 3.0])
        2.8333...

        '''
        div = self.div
        BL = self.brevisLength
        typeStrength = {'semibrevis': 1.0, 'minima': 0.5, 'semiminima':0.25}

        beatStrength = 0
        strength = 0
        curBeat = 0
        for i in range(len(lengths)):
            if common.almostEquals(curBeat - round(curBeat), 0): #Rounding error
                curBeat = round(curBeat)

            if div.standardSymbol in ['.i.', '.n.']:
                if common.almostEquals(curBeat % 3, 0):
                    beatStrength = 1.0
                elif curBeat % 3 - 1 or i % 3 == 2:
                    beatStrength = float(1.0)/3
                else:
                    beatStrength = float(1.0)/9
            elif div.standardSymbol in ['.q.', '.o.', '.d.']:
                if curBeat % 4 == 0:
                    beatStrength = 1.0
                elif curBeat % 4 == 2:
                    beatStrength = 0.5
                elif curBeat % 2 == 1:
                    beatStrength = 0.25
                else:
                    beatStrength = 0.125
            else:
                if curBeat % 6 == 0:
                    beatStrength = 1.0
                elif curBeat % 2 == 0 and curBeat % 3 != 0:
                    beatStrength = 0.5
                elif curBeat % 2 == 1:
                    beatStrength = 0.25
                else:
                    beatStrength = 0.125
            strength += typeStrength[BL[i].mensuralType] * beatStrength
            lengthI = lengths[i]
            if lengthI is None:
                lengthI = 0.0
            curBeat += lengthI

        lastSBLen = div.minimaPerBrevis
        if  ((any(self.unknownLengthsDict['semibrevis'])) and
                (self.unknownLengthsDict['semibrevis'][-1] == len(self.brevisLength) - 1)):
            lastSBLen = lengths[ self.unknownLengthsDict['semibrevis'][-1] ]

        strength -= abs(div.minimaPerBrevis - curBeat)

        from music21.alpha import medren
        for i, item in enumerate(self.brevisLength):
            if isinstance(item, medren.MensuralNote) and (not 'down' in item.getStems()) and (lengths[i] > lastSBLen):
                strength = 0

        return strength

    def determineStrongestMeasureLengths(self, 
                                         lengths, 
                                         change_tup, 
                                         num_tup, 
                                         diff_tup, 
                                         lenRem, 
                                         shrinkable_indices=(), 
                                         multi=None):
        '''
        Gets all possible length combinations. Returns the lengths combination of the "strongest" list,
        along with the remaining length.

        :param lengths: list of lengths to be updated
        :param change_tup: tuple, each element is the sub-list of self.brevisLength to be changed.
        :param num_tup: tuple, each element is an integer, the maximum number of elements in the corresponding list of change_tup that can be changed
        :param diff_tup: tuple, each element is the amount by which to change the elements of the corresponding list in change_tup.
        :param lenRem: input of the remaining SM in the measure. Gets updated and returned.
        :param shrinkable_indices: tuple of indices of elements able to take up slack (i.e. ending SB, or downstem SB)

        >>> from music21.alpha import medren

        >>> div = alpha.trecento.notation.Divisione('.n.')
        >>> names = ['SB', 'M', 'M', 'M', 'SB']
        >>> BL = [medren.MensuralNote('A', n) for n in names]
        >>> TBL = alpha.trecento.notation.BrevisLengthTranslator(div, BL)
        >>> TBL.determineStrongestMeasureLengths([2.0, 1.0, 1.0, 1.0, 4.0], ([0],), (1,), (1.0,), 0.0, shrinkable_indices = (-1,))
        ([3.0, 1.0, 1.0, 1.0, 3.0], 0.0)

        '''

        if not (len(change_tup) == len(num_tup)) and (len(change_tup) == len(diff_tup)):
            raise Exception('Invalid syntax: change_tup, num_tup, and diff_tup must have the same length')

        change = change_tup[0]
        change_num = num_tup[0]
        diff = diff_tup[0]
        release = None

        if shrinkable_indices:
            release = shrinkable_indices[0]

        if multi is None:
            multi = len(change_tup) - 1

        strength = self.getBreveStrength(lengths)
        lengths_changeable = lengths[:]
        lengths_static = lengths[:]
        remain = lenRem
        lenRem_final  = lenRem

        for l in _allCombinations(change, change_num):
            for i in l:
                lengths_changeable[i] += diff
                if release is not None:
                    lengths_changeable[release] -= diff
                    if multi > 0:
                        lengths_changeable, remain = self.determineStrongestMeasureLengths(lengths_changeable, change_tup[1:], num_tup[1:], diff_tup[1:], remain, shrinkable_indices = shrinkable_indices[1:], multi = multi-1)
                else:
                    remain -= diff
                    if multi > 0:
                        lengths_changeable, remain = self.determineStrongestMeasureLengths(lengths_changeable, change_tup[1:], num_tup[1:], diff_tup[1:], remain, shrinkable_indices = (), multi = multi-1)

            newStrength = self.getBreveStrength(lengths_changeable)

            if strength < newStrength and remain > -0.0001:
                lengths = lengths_changeable[:]
                strength = newStrength
                lenRem_final = remain
            lengths_changeable = lengths_static[:]
            remain = lenRem
        return lengths, lenRem_final


    def getUnchangeableNoteLengths(self):
        '''
        takes the music in self.brevisLength and returns a list where element i in this list
        corresponds to the length in minimas of element i in self.brevisLength.  If the length
        cannot be determined without taking into account the context (e.g., semiminims, semibreves)
        then None is placed in that list.
        
        >>> from music21.alpha import medren

        >>> div = alpha.trecento.notation.Divisione('.i.')
        >>> names = ['SB', 'M','SB']
        >>> BL = [medren.MensuralNote('A', n) for n in names]
        >>> TBL = alpha.trecento.notation.BrevisLengthTranslator(div, BL)
        >>> TBL.getUnchangeableNoteLengths()
        [None, 1.0, None]

        >>> names = ['B']
        >>> BL = [medren.MensuralNote('A', n) for n in names]
        >>> TBL = alpha.trecento.notation.BrevisLengthTranslator(div, BL)
        >>> TBL.getUnchangeableNoteLengths()
        [6.0]

        >>> names = ['L']
        >>> BL = [medren.MensuralNote('A', n) for n in names]
        >>> TBL = alpha.trecento.notation.BrevisLengthTranslator(div, BL)
        >>> TBL.getUnchangeableNoteLengths()
        [12.0]

        >>> names = ['Mx']
        >>> BL = [medren.MensuralNote('A', n) for n in names]
        >>> TBL = alpha.trecento.notation.BrevisLengthTranslator(div, BL)
        >>> TBL.getUnchangeableNoteLengths()
        [24.0]

        '''
        unchangeableNoteLengthsList = []
        for obj in self.brevisLength:
            minimaLength = None
            #If its duration is set, doesn't need to be determined

            #Gets rid of everything known
            if obj.mensuralType == 'maxima':
                minimaLength = float(4)*self.div.minimaPerBrevis
            elif obj.mensuralType == 'longa':
                minimaLength = float(2)*self.div.minimaPerBrevis
            elif obj.mensuralType == 'brevis':
                minimaLength = float(self.div.minimaPerBrevis)
            else:
                objC = obj.classes
                if 'GeneralMensuralNote' in objC:
                    #Dep on div
                    if obj.mensuralType == 'semibrevis':
                        if 'MensuralRest' in obj.classes:
                            if self.div.standardSymbol in ['.q.', '.i.']:
                                minimaLength = self.div.minimaPerBrevis/float(2)
                            elif self.div.standardSymbol in ['.p.', '.n.']:
                                minimaLength = self.div.minimaPerBrevis/float(3)
                            else: # we don't know it...
                                pass
                        else:
                            if 'side' in obj.getStems(): # oblique-stemmed semibreve
                                minimaLength = 3.0
                            else: # WHO THe heck knows a semibreve's length!!! :-)
                                pass
                    elif obj.mensuralType == 'minima':
                        if 'MensuralNote' in obj.classes and 'down' in obj.stems:
                            raise TrecentoNotationException('Dragmas currently not supported')
                        elif 'MensuralNote' in obj.classes and 'side' in obj.stems:
                            minimaLength = 1.5
                        else:
                            minimaLength = 1.0
                    elif obj.mensuralType == 'semiminima':
                        pass
            unchangeableNoteLengthsList.append(minimaLength)
        return unchangeableNoteLengthsList


    def classifyUnknownNotesByType(self, unchangeableNoteLengthsList):
        '''
        returns a dictionary where keys are types of notes ('semibrevis_downstem')
        and the values are a list of indices in self.brevisLength (and unchangeableNoteLengthsList)
        which are those types...

        >>> from music21.alpha import medren

        >>> div = alpha.trecento.notation.Divisione('.n.')
        >>> names = ['SB', 'M', 'M', 'M', 'SB', 'M']
        >>> BL = [medren.MensuralNote('A', n) for n in names]
        >>> TBL = alpha.trecento.notation.BrevisLengthTranslator(div, BL)
        >>> unchangeableNoteLengths = TBL.getUnchangeableNoteLengths()
        >>> kldict = TBL.classifyUnknownNotesByType(unchangeableNoteLengths)
        >>> print(kldict['semibrevis'])
        [0, 4]

        '''
        unchangeableNoteLengths = unchangeableNoteLengthsList

        semibrevis_list = []
        semibrevis_downstem = []

        semiminima_right_flag_list = []
        semiminima_left_flag_list = []
        semiminima_rest_list = []

        #Don't need these yet
        #===================================================================
        # dragmas_no_flag = []
        # dragmas_RNo_flag = []
        # dragmas_LNo_flag = []
        # dragmas_NoR_flag = []
        # dragmas_RR_flag = []
        # dragmas_RL_flag = []
        # dragmas_LR_flag = []
        # dragmas_LL_flag = []
        #===================================================================

        for i in range(len(self.brevisLength)):
            obj = self.brevisLength[i]
            knownLength = unchangeableNoteLengths[i]
            if knownLength is not None:
                continue

            if obj.mensuralType == 'semibrevis':
                if 'MensuralRest' in obj.classes:
                    if self.div.standardSymbol not in ['.q.', '.i.', '.p.', '.n.']:
                        semibrevis_list.append(i)
                else:
                    if 'side' in obj.getStems():
                        pass # shouldnt happen since length is known...
                    elif 'down' in obj.getStems():
                        semibrevis_downstem.append(i)
                    else:
                        semibrevis_list.append(i)
            elif obj.mensuralType == 'minima':
                pass
            elif obj.mensuralType == 'semiminima':
                if 'MensuralNote' in obj.classes:
                    if 'down' in obj.getStems():
                        raise TrecentoNotationException('Dragmas currently not supported')
                    elif obj.getFlags()['up'] == 'right':
                        semiminima_right_flag_list.append(i)
                    elif obj.getFlags()['up'] == 'left':
                        semiminima_left_flag_list.append(i)
                if 'MensuralRest' in obj.classes:
                    semiminima_rest_list.append(i)

        retDict = {'semibrevis':semibrevis_list,
                   'semibrevis_downstem':semibrevis_downstem,
                   'semiminima_right_flag':semiminima_right_flag_list,
                   'semiminima_left_flag':semiminima_left_flag_list,
                   'semiminima_rest':semiminima_rest_list,
                   }

        self.numberOfSemibreves = len(retDict['semibrevis'])
        self.numberOfDownstems = len(retDict['semibrevis_downstem'])
        self.numberOfRightFlags = len(retDict['semiminima_right_flag'])
        self.numberOfLeftFlags = len(retDict['semiminima_left_flag'])
        self.numbefOfSMRests = len(retDict['semiminima_rest'])

        self.hasLastSB = False
        if self.numberOfSemibreves > 0:
            self.hasLastSB = ( retDict['semibrevis'][-1] == (len(self.brevisLength) - 1) )

        return retDict

    def translate(self):
        '''
        Translates and returns a list of lengths for all the notes in self.brevisLength
        '''
        self.unchangeableNoteLengthsList = self.getUnchangeableNoteLengths()
        self.unknownLengthsDict = self.classifyUnknownNotesByType(self.unchangeableNoteLengthsList)

        for kl in self.unchangeableNoteLengthsList:
            if kl is not None and kl <= self.minimaRemaining:
                self.minimaRemaining -= kl

        if None in self.unchangeableNoteLengthsList:
            #Process everything else
            if self.div.standardSymbol == '.i.':
                knownLengthsList = self.translateDivI()
            elif self.div.standardSymbol == '.n.':
                knownLengthsList = self.translateDivN()
            elif self.div.standardSymbol == '.q.' or self.div.standardSymbol == '.p.':
                knownLengthsList = self.translateDivPQ()
            else:  # .o. or .d.
                knownLengthsList = self.translateDivOD()
        else:
            self.minRem_tracker = True
            knownLengthsList = self.unchangeableNoteLengthsList[:]

        if not self.minRem_tracker:
            self.doubleNum += 1
            newDiv = Divisione(self.div.standardSymbol)
            newDiv.minimaPerBrevis = 2 * self.div.minimaPerBrevis
            return self.brevisLength
            tempTBL = BrevisLengthTranslator(newDiv, self.brevisLength[:])
            knownLengthsList = tempTBL.getKnownLengths()

        for i in range(len(knownLengthsList)):  # Float errors
            ml = knownLengthsList[i]
            try:
                if abs(ml - round(ml)) < 0.0001:
                    knownLengthsList[i] = round(ml)
            except TypeError:
                raise TypeError('ml is screwed up! %s' % ml)

        return [float(l) for l in knownLengthsList]

    def translateDivI(self, unchangeableNoteLengthsList=None, unknownLengthsDict=None, minRem=None):
        '''

        >>> from music21.alpha import medren

        >>> div = alpha.trecento.notation.Divisione('.i.')
        >>> names = ['SB', 'M', 'SB']
        >>> BL = [medren.MensuralNote('A', n) for n in names]
        >>> TBL = alpha.trecento.notation.BrevisLengthTranslator(div, BL)
        >>> unchlist = TBL.getUnchangeableNoteLengths()
        >>> unchlist
        [None, 1.0, None]
        >>> unkldict = TBL.classifyUnknownNotesByType(unchlist)
        >>> TBL.translateDivI(unchlist, unkldict, 5.0)
        [2.0, 1.0, 3.0]
        '''
        if unchangeableNoteLengthsList is None:
            unchangeableNoteLengthsList = self.unchangeableNoteLengthsList
        else:
            self.unchangeableNoteLengthsList = unchangeableNoteLengthsList

        if unknownLengthsDict is None:
            unknownLengthsDict = self.unknownLengthsDict
        else:
            self.unknownLengthsDict = unknownLengthsDict

        if minRem is None:
            minRem = self.minimaRemaining

        semibrevis_list = unknownLengthsDict['semibrevis']

        knownLengthsList = unchangeableNoteLengthsList[:]

        if self.numberOfSemibreves > 0:
            avgSBLength = minRem/self.numberOfSemibreves
            for ind in semibrevis_list:
                if avgSBLength == 2:
                    knownLengthsList[ind] = 2.0
                    minRem -= 2.0
                elif (2 < avgSBLength) and (avgSBLength < 3):
                    if ind < (len(self.brevisLength)-1) and self.brevisLength[ind+1].mensuralType == 'minima':
                        knownLengthsList[ind] = 2.0
                        minRem -= 2.0
                    else:
                        knownLengthsList[ind] = 3.0
                        minRem -= 3.0
                elif avgSBLength == 3.0:
                    knownLengthsList[ind] = 3.0
                    minRem -= 3.0

        if minRem > -0.0001:
            self.minimaRemaining = minRem
            self.minRem_tracker = True

        return knownLengthsList

    def translateDivN(self, unchangeableNoteLengthsList=None, unknownLengthsDict=None, minRem=None):
        '''
        Translate the Novanaria (9) Divisio; returns the number of minims for each note.
        
        >>> from music21.alpha import medren

        >>> div = alpha.trecento.notation.Divisione('.n.')
        >>> names = ['SB', 'M', 'M', 'M', 'SB', 'M']
        >>> BL = [medren.MensuralNote('A', n) for n in names]
        >>> TBL = alpha.trecento.notation.BrevisLengthTranslator(div, BL)
        >>> unchlist = TBL.getUnchangeableNoteLengths()
        >>> unkldict = TBL.classifyUnknownNotesByType(unchlist)
        >>> TBL.translateDivN(unchlist, unkldict, 5.0)
        [3.0, 1.0, 1.0, 1.0, 2.0, 1.0]

        >>> BL[-2].setStem('down')
        >>> unchlist = TBL.getUnchangeableNoteLengths()
        >>> unkldict = TBL.classifyUnknownNotesByType(unchlist)
        >>> TBL.translateDivN(unchlist, unkldict, 5.0)
        [2.0, 1.0, 1.0, 1.0, 3.0, 1.0]

        >>> names = ['SB', 'M', 'M', 'M', 'SB']
        >>> BL = [medren.MensuralNote('A', n) for n in names]
        >>> TBL = alpha.trecento.notation.BrevisLengthTranslator(div, BL)
        >>> unchlist = TBL.getUnchangeableNoteLengths()
        >>> unkldict = TBL.classifyUnknownNotesByType(unchlist)
        >>> TBL.translateDivN(unchlist, unkldict, 6.0)
        [3.0, 1.0, 1.0, 1.0, 3.0]


        >>> names = ['SB', 'M', 'SB']
        >>> BL = [medren.MensuralNote('A', n) for n in names]
        >>> TBL = alpha.trecento.notation.BrevisLengthTranslator(div, BL)
        >>> unchlist = TBL.getUnchangeableNoteLengths()
        >>> unkldict = TBL.classifyUnknownNotesByType(unchlist)
        >>> TBL.translateDivN(unchlist, unkldict, 8.0)
        [2.0, 1.0, 6.0]

        >>> BL[0].setStem('down')
        >>> TBL = alpha.trecento.notation.BrevisLengthTranslator(div, BL)
        >>> unchlist = TBL.getUnchangeableNoteLengths()
        >>> unkldict = TBL.classifyUnknownNotesByType(unchlist)
        >>> TBL.translateDivN(unchlist, unkldict, 8.0)
        [5.0, 1.0, 3.0]

        '''

        if unchangeableNoteLengthsList is None:
            unchangeableNoteLengthsList = self.unchangeableNoteLengthsList
        else:
            self.unchangeableNoteLengthsList = unchangeableNoteLengthsList

        if unknownLengthsDict is None:
            unknownLengthsDict = self.unknownLengthsDict
        else:
            self.unknownLengthsDict = unknownLengthsDict

        if minRem is None:
            minRem = self.minimaRemaining

        semibrevis_list = unknownLengthsDict['semibrevis']
        semibrevis_downstem = unknownLengthsDict['semibrevis_downstem']
        semibrevis_downstem_index = None

        if self.numberOfDownstems > 0:
            semibrevis_downstem_index = semibrevis_downstem[0] #Only room for one downstem

        knownLengthsList = unchangeableNoteLengthsList[:]
        extend_list = [] #brevises able to be lengthened
        extend_num = 0
        if self.numberOfSemibreves > 0:

            for ind in semibrevis_list[:-1]:
                # make all but final non-downstem semibreves followed by minima = 2.0
                if self.brevisLength[ind+1].mensuralType == 'minima':
                    knownLengthsList[ind] = 2.0
                    minRem -= 2.0
                    extend_list.append(ind)
                else: # if not followed by minima -- make 3.0
                    knownLengthsList[ind] = 3.0
                    minRem -= 3.0

            shrink_tup = ()
            if self.numberOfDownstems > 0:

                if (not self.hasLastSB) and (self.brevisLength[semibrevis_list[-1]+1].mensuralType == 'minima'):
                    knownLengthsList[semibrevis_list[-1]] = 2.0
                    minRem -= 2.0
                    extend_list.append(semibrevis_list[-1])

                else:
                    knownLengthsList[semibrevis_list[-1]] = 3.0
                    minRem -= 3.0

                knownLengthsList[semibrevis_downstem_index] = max(minRem, 3)
                minRem -= knownLengthsList[semibrevis_downstem_index]

                extend_num = min(knownLengthsList[semibrevis_downstem_index] - 3, len(extend_list))
                shrink_tup += semibrevis_downstem_index,

            else: #no downstems

                if self.hasLastSB:
                    knownLengthsList[semibrevis_list[-1]] = max(minRem, 3.0)
                    minRem -= knownLengthsList[-1]

                    extend_num = min(knownLengthsList[-1]- 3, len(extend_list))
                    shrink_tup += -1,

                elif self.numberOfSemibreves > 0: #SBs, but no last SB
                    if (self.brevisLength[semibrevis_list[-1]+1].mensuralType == 'minima'):
                        knownLengthsList[semibrevis_list[-1]] = 2.0
                        minRem -= 2.0
                        extend_list.append(semibrevis_list[-1])

                    else:
                        knownLengthsList[semibrevis_list[-1]] = 3.0
                        minRem -= 3.0

                    extend_num = len(extend_list)

            if (minRem > -0.0001) and (semibrevis_downstem_index != (len(self.brevisLength) - 1)):
                change_tup = (extend_list,)
                num_tup = (extend_num,)
                diff_tup = (1,)

                knownLengthsList, minRem = self.determineStrongestMeasureLengths(knownLengthsList, change_tup, num_tup, diff_tup, minRem, shrinkable_indices = shrink_tup)

        if minRem > -0.0001:
            self.minimaRemaining = minRem
            self.minRem_tracker = True

        return knownLengthsList

    def translateDivPQ(self, unchangeableNoteLengthsList=None, unknownLengthsDict=None, minRem=None):
        '''
        Translates P and Q (6 and 4)

        >>> from music21.alpha import medren
        
        >>> div = alpha.trecento.notation.Divisione('.q.')
        >>> names = ['SB','SB']
        >>> BL = [medren.MensuralNote('A', n) for n in names]
        >>> TBL = alpha.trecento.notation.BrevisLengthTranslator(div, BL)
        >>> unchlist = TBL.getUnchangeableNoteLengths()
        >>> unkldict = TBL.classifyUnknownNotesByType(unchlist)
        >>> TBL.translateDivPQ(unchlist, unkldict, 4.0)
        [2.0, 2.0]

        >>> names = ['M', 'SM', 'SM', 'SM', 'SM', 'SM']
        >>> BL = [medren.MensuralNote('A', n) for n in names]
        >>> BL[4] = medren.MensuralRest('SM')
        >>> BL[1].setFlag('up','left')
        >>> BL[2].setFlag('up', 'left')
        >>> TBL = alpha.trecento.notation.BrevisLengthTranslator(div, BL)
        >>> unchlist = TBL.getUnchangeableNoteLengths()
        >>> unkldict = TBL.classifyUnknownNotesByType(unchlist)
        >>> TBL.translateDivPQ(unchlist, unkldict, 3.0)
        [1.0, 0.5, 0.5, 0.666..., 0.666..., 0.666...]

        >>> div = alpha.trecento.notation.Divisione('.p.')
                >>> names = ['SB','SB', 'SB']
        >>> BL = [medren.MensuralNote('A', n) for n in names]
        >>> TBL = alpha.trecento.notation.BrevisLengthTranslator(div, BL)
        >>> unchlist = TBL.getUnchangeableNoteLengths()
        >>> unkldict = TBL.classifyUnknownNotesByType(unchlist)
        >>> TBL.translateDivPQ(unchlist, unkldict, 6.0)
        [2.0, 2.0, 2.0]

        >>> names = ['M', 'SB', 'SM', 'SM']
        >>> BL = [medren.MensuralNote('A', n) for n in names]
        >>> BL[1].setStem('down')
        >>> TBL = alpha.trecento.notation.BrevisLengthTranslator(div, BL)
        >>> unchlist = TBL.getUnchangeableNoteLengths()
        >>> unkldict = TBL.classifyUnknownNotesByType(unchlist)
        >>> TBL.translateDivPQ(unchlist, unkldict, 5.0)
        [1.0, 4.0, 0.5, 0.5]

        >>> names = ['SM', 'SM', 'SM', 'SM', 'SM', 'SM', 'SM', 'SB']
        >>> BL = [medren.MensuralNote('A', n) for n in names]
        >>> BL[3] = medren.MensuralRest('SM')
        >>> for mn in BL[:3]:
        ...    mn.setFlag('up', 'left')
        >>> TBL = alpha.trecento.notation.BrevisLengthTranslator(div, BL)
        >>> unchlist = TBL.getUnchangeableNoteLengths()
        >>> unkldict = TBL.classifyUnknownNotesByType(unchlist)
        >>> TBL.translateDivPQ(unchlist, unkldict, 6.0)
        [0.666..., 0.666..., 0.666..., 0.5, 0.5, 0.5, 0.5, 2.0]

        '''

        if unchangeableNoteLengthsList is None:
            unchangeableNoteLengthsList = self.unchangeableNoteLengthsList
        else:
            self.unchangeableNoteLengthsList = unchangeableNoteLengthsList

        if unknownLengthsDict is None:
            unknownLengthsDict = self.unknownLengthsDict
        else:
            self.unknownLengthsDict = unknownLengthsDict

        if minRem is None:
            minRem = self.minimaRemaining

        semibrevis_list = unknownLengthsDict['semibrevis']
        semibrevis_downstem = unknownLengthsDict['semibrevis_downstem']
        semiminima_right_flag_list = unknownLengthsDict['semiminima_right_flag']
        semiminima_left_flag_list = unknownLengthsDict['semiminima_left_flag']
        semiminima_rest_list = unknownLengthsDict['semiminima_rest']

        knownLengthsList = unchangeableNoteLengthsList[:]

        extend_list = []
        extend_num = 0

        semibrevis_downstem_index = None
        if self.numberOfDownstems > 0: #Only room for one downstem per brevis length
            semibrevis_downstem_index = semibrevis_downstem[0]

        for ind in semibrevis_list[:-1]:
            knownLengthsList[ind] = 2.0
            minRem -= 2.0

        if semibrevis_downstem_index == (len(self.brevisLength) - 1):

            for ind in semiminima_right_flag_list+semiminima_left_flag_list+semiminima_rest_list:
                knownLengthsList[ind] = 0.5
                minRem -= 0.5

            if self.numberOfSemibreves > 0:
                knownLengthsList[semibrevis_list[-1]] = 2.0
                minRem -= 2.0

            knownLengthsList[semibrevis_downstem_index] = max(minRem, 2.0)
            minRem -= max(minRem, 2.0)

            if minRem > -0.0001:
                self.minimaRemaining = minRem
                self.minRem_tracker = True

        else:
            strength = 0
            knownLengthsList_changeable = knownLengthsList[:]
            knownLengthsList_static = knownLengthsList[:]
            minRem_changeable = minRem
            minRem_static = minRem

            change_tup = ()
            num_tup = ()
            diff_tup = ()
            shrink_tup = ()

            lengths = [(0.5,0.5), (float(2)/3, 0.5), (0.5, float(2)/3), (float(2)/3, float(2)/3)]

            for (left_length, right_length) in lengths:
                for ind in semiminima_left_flag_list:
                    knownLengthsList_changeable[ind] = left_length
                    minRem_changeable -= left_length
                for ind in semiminima_right_flag_list:
                    knownLengthsList_changeable[ind] = right_length
                    minRem_changeable -= right_length

                if left_length == right_length:

                    for ind in semiminima_rest_list:
                        knownLengthsList_changeable[ind] = left_length
                        minRem_changeable -= left_length

                    if self.numberOfDownstems > 0:

                        if self.numberOfSemibreves > 0:
                            knownLengthsList_changeable[semibrevis_list[-1]] = 2.0
                            minRem_changeable -= 2.0

                        knownLengthsList_changeable[semibrevis_downstem_index] = max(2.0, minRem_changeable)
                        minRem_changeable -= knownLengthsList_changeable[semibrevis_downstem_index]

                    else: #no downstems

                        if self.hasLastSB:
                            knownLengthsList_changeable[semibrevis_list[-1]] = max(2.0, minRem_changeable)
                            minRem_changeable -= knownLengthsList_changeable[semibrevis_list[-1]]

                        elif self.numberOfSemibreves > 0: #semibreves, but no ending SB
                            knownLengthsList_changeable[semibrevis_list[-1]] = 2.0
                            minRem_changeable -= 2.0

                else: #left_length != right_length

                    master_list = semiminima_left_flag_list + semiminima_right_flag_list + semiminima_rest_list

                    for ind in semiminima_rest_list:

                        curIndex = int(master_list.index(ind))

                        # SM Rest is first among all SMs, followed by left flag SM
                        # or, SM Rest is last among all SMs, preceded by left flag SM
                        # or, SM Rest is surrounded by left flag SMs.
                        # Then, SM rest = left_length
                        if ( curIndex == 0 and master_list[curIndex+1] in semiminima_left_flag_list ) or \
                             ( curIndex == len(master_list) - 1 and master_list[curIndex - 1] in semiminima_left_flag_list ) or \
                             ( master_list[curIndex-1] in semiminima_left_flag_list and master_list[curIndex+1] in semiminima_left_flag_list ):

                            knownLengthsList_changeable[ind] = left_length
                            minRem_changeable -= left_length

                        # Same as above, but with right flag SMs.
                        # Then, SM rest = right_length
                        elif ( (curIndex == 0 and master_list[curIndex+1] in semiminima_right_flag_list) or
                             (curIndex == len(master_list) - 1 and master_list[curIndex - 1] in semiminima_right_flag_list) or
                             (master_list[curIndex-1] in semiminima_right_flag_list and master_list[curIndex+1] in semiminima_right_flag_list) ):

                            knownLengthsList_changeable[ind] = right_length
                            minRem_changeable -= right_length

                        #Otherwise, we don't know. Append SM Rest to extend list.
                        else:
                            knownLengthsList_changeable[ind] = 0.5
                            extend_list.append(ind)
                        extend_list = _removeRepeatedElements(extend_list) # account for iterations w/o changing order.

                    if self.numberOfDownstems > 0:

                        if self.numberOfSemibreves > 0:
                            knownLengthsList_changeable[semibrevis_list[-1]] = 2.0
                            minRem_changeable -= 2.0

                        knownLengthsList_changeable[semibrevis_downstem_index] = max(minRem_changeable, 2.0)
                        extend_num = min(6*minRem_changeable - 15.0, len(extend_list))
                        minRem_changeable -= knownLengthsList_changeable[semibrevis_downstem_index]

                        shrink_tup += semibrevis_downstem_index,

                    else: #No downstems
                        if self.hasLastSB:

                            knownLengthsList_changeable[semibrevis_list[-1]] = max(minRem_changeable, 2.0)
                            extend_num = min(6*minRem_changeable - 12.0, len(extend_list))
                            minRem_changeable -= max(minRem_changeable, 2.0)

                            shrink_tup += -1,

                        elif self.numberOfSemibreves > 0: #SBs, but no last SB
                            knownLengthsList_changeable[semibrevis_list[-1]] = 2.0
                            minRem_changeable -= 2.0
                            extend_num = len(extend_list)

                    change_tup += extend_list,
                    num_tup += extend_num,
                    diff_tup += float(1)/6,

                    if minRem_changeable > -0.0001:
                        knownLengthsList_changeable, minRem_changeable = self.determineStrongestMeasureLengths(knownLengthsList_changeable, change_tup, num_tup, diff_tup, minRem_changeable, shrinkable_indices = shrink_tup)

                tempStrength = self.getBreveStrength(knownLengthsList_changeable)
                self.minimaRemaining = minRem_changeable

                if (tempStrength > strength) and (minRem_changeable > -0.0001): #Technically, >= 0, but rounding error occurs.
                    knownLengthsList = knownLengthsList_changeable[:]
                    minRem = minRem_changeable
                    strength = tempStrength

                knownLengthsList_changeable = knownLengthsList_static

                if minRem_changeable > -0.0001:
                    self.minRem_tracker = True

                minRem_changeable = minRem_static

        return knownLengthsList

    def translateDivOD(self, unchangeableNoteLengthsList=None, unknownLengthsDict=None, minRem=None):
        '''
        Translates the octonaria and duodenaria divisions

        >>> from music21.alpha import medren

        >>> divO = alpha.trecento.notation.Divisione('.o.')
        >>> names = ['SB', 'SB', 'SB']
        >>> BL = [medren.MensuralNote('A', n) for n in names]
        >>> BL[1].setStem('down')
        >>> TBL = alpha.trecento.notation.BrevisLengthTranslator(divO, BL)
        >>> unchlist = TBL.getUnchangeableNoteLengths()
        >>> unkldict = TBL.classifyUnknownNotesByType(unchlist)
        >>> TBL.translateDivOD(unchlist, unkldict, 8.0)
        [2.0, 4.0, 2.0]

        >>> names = ['SM', 'SM', 'SM', 'SB', 'SB']
        >>> BL = [medren.MensuralNote('A', n) for n in names]
        >>> TBL = alpha.trecento.notation.BrevisLengthTranslator(divO, BL)
        >>> unchlist = TBL.getUnchangeableNoteLengths()
        >>> unkldict = TBL.classifyUnknownNotesByType(unchlist)
        >>> TBL.translateDivOD(unchlist, unkldict, 8.0)
        [0.666..., 0.666..., 0.666..., 2.0, 3.999...]

        >>> divD = alpha.trecento.notation.Divisione('.d.')
        >>> names = ['SB', 'SB']
        >>> BL = [medren.MensuralNote('A', n) for n in names]
        >>> TBL = alpha.trecento.notation.BrevisLengthTranslator(divD, BL)
        >>> unchlist = TBL.getUnchangeableNoteLengths()
        >>> unkldict = TBL.classifyUnknownNotesByType(unchlist)
        >>> TBL.translateDivOD(unchlist, unkldict, 12.0)
        [4.0, 8.0]

        >>> names = ['SB', 'SB', 'SB']
        >>> BL = [medren.MensuralNote('A', n) for n in names]
        >>> TBL = alpha.trecento.notation.BrevisLengthTranslator(divD, BL)
        >>> unchlist = TBL.getUnchangeableNoteLengths()
        >>> unkldict = TBL.classifyUnknownNotesByType(unchlist)
        >>> TBL.translateDivOD(unchlist, unkldict, 12.0)
        [4.0, 4.0, 4.0]

        >>> names = ['SB', 'SB', 'SB', 'SB']
        >>> BL = [medren.MensuralNote('A', n) for n in names]
        >>> TBL = alpha.trecento.notation.BrevisLengthTranslator(divD, BL)
        >>> unchlist = TBL.getUnchangeableNoteLengths()
        >>> unkldict = TBL.classifyUnknownNotesByType(unchlist)
        >>> TBL.translateDivOD(unchlist, unkldict, 12.0)
        [2.0, 2.0, 4.0, 4.0]

        >>> BL[1].setStem('down')
        >>> BL[2].setStem('down')
        >>> TBL = alpha.trecento.notation.BrevisLengthTranslator(divD, BL)
        >>> unchlist = TBL.getUnchangeableNoteLengths()
        >>> unchlist
        [None, None, None, None]
        >>> unkldict = TBL.classifyUnknownNotesByType(unchlist)
        >>> TBL.translateDivOD(unchlist, unkldict, 12.0)
        [2.0, 4.0, 4.0, 2.0]

        >>> names = ['SB', 'SB','SM', 'SM','SM','SM','SB','SB']
        >>> BL = [medren.MensuralNote('A', n) for n in names]
        >>> TBL = alpha.trecento.notation.BrevisLengthTranslator(divD, BL)
        >>> unchlist = TBL.getUnchangeableNoteLengths()
        >>> unkldict = TBL.classifyUnknownNotesByType(unchlist)
        >>> TBL.translateDivOD(unchlist, unkldict, 12.0)
        [2.0, 2.0, 0.5, 0.5, 0.5, 0.5, 2.0, 4.0]
        '''
        if unchangeableNoteLengthsList is None:
            unchangeableNoteLengthsList = self.unchangeableNoteLengthsList
        else:
            self.unchangeableNoteLengthsList = unchangeableNoteLengthsList

        if unknownLengthsDict is None:
            unknownLengthsDict = self.unknownLengthsDict
        else:
            self.unknownLengthsDict = unknownLengthsDict

        if minRem is None:
            minRem = self.minimaRemaining

        semibrevis_list = unknownLengthsDict['semibrevis']
        semibrevis_downstem = unknownLengthsDict['semibrevis_downstem']
        semiminima_right_flag_list = unknownLengthsDict['semiminima_right_flag']
        semiminima_left_flag_list = unknownLengthsDict['semiminima_left_flag']
        semiminima_rest_list = unknownLengthsDict['semiminima_rest']

        knownLengthsList = unchangeableNoteLengthsList[:]

        extend_list_1 = []
        extend_num_1 = 0.0
        extend_list_2 = []
        extend_num_2 = 0.0

        for ind in semibrevis_list[:-1]:
            knownLengthsList[ind] = 2.0
            extend_list_1.append(ind)
            minRem -= 2.0

        knownLengthsList_changeable = knownLengthsList[:]
        minRem_changeable = minRem
        knownLengthsList_static = knownLengthsList[:]
        minRem_static = minRem

        if self.numberOfDownstems == 1 and semibrevis_downstem[0] == len(self.brevisLength) - 1:

            for ind in semiminima_left_flag_list + semiminima_right_flag_list + semiminima_rest_list:
                knownLengthsList[ind] = 0.5
                minRem -= 0.5

            if self.numberOfSemibreves:
                for ind in semibrevis_list:
                    knownLengthsList[ind] = 2.0
                    minRem -= 2.0

            knownLengthsList[semibrevis_downstem[0]] = max(minRem, 2.0)
            minRem -= max(minRem, 2.0)

            if minRem > -0.0001:
                self.minimaRemaining = minRem
                self.minRem_tracker = True

        else:

            lengths = [(0.5,0.5), (float(2)/3, 0.5), (0.5, float(2)/3), (float(2)/3, float(2)/3)]
            strength = 0

            for (left_length, right_length) in lengths:

                change_tup = ()
                num_tup = ()
                diff_tup = ()
                shrink_tup = ()

                for ind in semiminima_left_flag_list:
                    knownLengthsList_changeable[ind] = left_length
                    minRem_changeable -= left_length
                for ind in semiminima_right_flag_list:
                    knownLengthsList_changeable[ind] = right_length
                    minRem_changeable -= right_length

                if left_length == right_length:

                    for ind in semiminima_rest_list:
                        knownLengthsList_changeable[ind] = left_length
                        minRem_changeable -= left_length

                else: #left_length != right_length

                    master_list = semiminima_left_flag_list + semiminima_right_flag_list + semiminima_rest_list

                    for ind in semiminima_rest_list:
                        curIndex = int(master_list.index(ind))
                        if ( curIndex == 0 and master_list[curIndex+1] in semiminima_left_flag_list ) or \
                             ( curIndex == len(master_list) - 1 and master_list[curIndex - 1] in semiminima_left_flag_list ) or \
                             ( master_list[curIndex-1] in semiminima_left_flag_list and 
                                    master_list[curIndex+1] in semiminima_left_flag_list ):
                            knownLengthsList_changeable[ind] = left_length
                            minRem_changeable -= left_length

                        elif ( (curIndex == 0 and master_list[curIndex+1] in semiminima_right_flag_list) or
                             (curIndex == len(master_list) - 1 and master_list[curIndex - 1] in semiminima_right_flag_list) or
                             (master_list[curIndex-1] in semiminima_right_flag_list and 
                                    master_list[curIndex+1] in semiminima_right_flag_list) ):

                            knownLengthsList_changeable[ind] = right_length
                            minRem_changeable -= right_length

                        else:
                            knownLengthsList_changeable[ind] = 0.5
                            #extend_list.append(ind)  ### BUG: extend_list does not exist
                        #extend_list = _removeRepeatedElements(extend_list_2)

                if self.numberOfDownstems > 0:

                    if self.numberOfSemibreves > 0:
                        knownLengthsList_changeable[semibrevis_list[-1]] = 2.0
                        extend_list_1.append(semibrevis_list[-1])
                        minRem_changeable -= 2.0
                    extend_list_1 = _removeRepeatedElements(extend_list_1)
                    extend_num_1 = float(min(len(extend_list_1), 0.5*minRem_changeable - 2.0))
                    extend_num_2 = float(min(len(extend_list_2), 6*minRem_changeable - 24.0))
                    

                    if self.numberOfDownstems < 2:
                        semibrevis_downstem_index = semibrevis_downstem[0]

                        knownLengthsList_changeable[semibrevis_downstem_index] = max(minRem_changeable, 4.0)
                        minRem_changeable -= knownLengthsList_changeable[semibrevis_downstem_index]

                        shrink_tup += semibrevis_downstem_index,
                        if extend_list_2:
                            shrink_tup += semibrevis_downstem_index,

                    else: #downstems >= 2
                        from music21.alpha import medren
                        newMensuralBL = [medren.MensuralNote('A', 'SB') for i in range(len(semibrevis_downstem))]

                        newDiv = Divisione('.d.')
                        newDiv.minimaPerBrevis = minRem_changeable
                        tempTBL = BrevisLengthTranslator(divisione = newDiv, BL = newMensuralBL, pDS = True)
                        dSLengthList = tempTBL.getKnownLengths()
                        
                        for i, ind in enumerate(semibrevis_downstem):
                            knownLengthsList_changeable[ind] = dSLengthList[i]
                        #Don't need shrink_tup. There is no room to extend anything.

                else: #No downstems
                    if self.numberOfSemibreves > 0:
                        if self.hasLastSB:
                            maxVal = max(minRem_changeable, 2.0)
                            knownLengthsList_changeable[semibrevis_list[-1]] = maxVal
                            extend_num_1 = min(float(len(extend_list_1)), int(0.5*minRem_changeable - 1.0))
                            minRem_changeable -= knownLengthsList_changeable[semibrevis_list[-1]]

                            shrink_tup += -1,
                            if extend_list_2:
                                shrink_tup += -1,

                        else:
                            knownLengthsList[semibrevis_list[-1]] = 2.0
                            extend_list_1.append(semibrevis_list[-1])
                            extend_list_1 = _removeRepeatedElements(extend_list_1)
                            extend_num_1 = float(len(extend_list_1))
                            extend_num_2 = float(len(extend_list_2))
                            minRem_changeable -= 2.0

                change_tup += extend_list_1, extend_list_2
                num_tup += extend_num_1, extend_num_2
                diff_tup += 2.0, float(1)/6

                if minRem_changeable > -0.0001:
                    knownLengthsList_changeable, minRem_changeable = self.determineStrongestMeasureLengths(knownLengthsList_changeable, change_tup, num_tup, diff_tup, minRem_changeable, shrinkable_indices = shrink_tup)

                            
                tempStrength = self.getBreveStrength(knownLengthsList_changeable)

                if tempStrength > strength and minRem_changeable > -0.0001:
                    knownLengthsList = knownLengthsList_changeable[:]
                    minRem = minRem_changeable
                    strength = tempStrength

                knownLengthsList_changeable = knownLengthsList_static

                if minRem_changeable > -0.0001:
                    self.minRem_tracker = True

                minRem_changeable = minRem_static

        return knownLengthsList

def _allCombinations(combinationList, num):
    '''
    >>> alpha.trecento.notation._allCombinations(['a', 'b'], 2)
    [[], ['b'], ['a', 'b'], ['a']]

    >>> alpha.trecento.notation._allCombinations(['a', 'b', 'c'], 2)
    [[], ['c'], ['b', 'c'], ['b'], ['a', 'b'], ['a', 'c'], ['a']]

    '''

    combs = []
    if num > 0:
        for i in range(len(combinationList)):
            comb = [combinationList[i]]
            for c in _allCombinations(combinationList[(i+1):], num-1):
                combs.append(comb + c)
    combs.reverse()
    combs.insert(0, [])
    return combs

def _removeRepeatedElements(listOrTup): #So I don't have to use set

    newListOrTup = None
    if type(listOrTup) == list:
        newListOrTup = []
    elif type(listOrTup) == tuple:
        newListOrTup = ()

    for item in listOrTup:
        if item not in newListOrTup:
            newListOrTup.append(item)
    return newListOrTup


class TrecentoNotationException(exceptions21.Music21Exception):
    pass

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class TestExternal(unittest.TestCase):

    def testTinyTrecentoStream(self):
        from music21.alpha import medren, trecento
        from music21 import text
    
        SePerDureca = stream.Score()
        TinySePerDureca = stream.Score()
        
        SePerDureca.append(text.TextBox('Se Per Dureca'))
        TinySePerDureca.append(text.TextBox('Se Per Dureca'))
    
        upper = stream.Part()
        lower = stream.Part()
    
        def processStream(mStream, pitches, lengths, downStems = []):
            pInd, lInd = 0, 0
            while lInd < len(lengths):
                if lengths[lInd] == 'P':
                    mStream.append(trecento.notation.Punctus())
                    lInd += 1
                else:
                    if pitches[pInd] == 'R':
                        mStream.append(medren.MensuralRest(lengths[lInd]))
                    else:
                        mn = medren.MensuralNote(pitches[pInd], lengths[lInd])
                        if lInd in downStems:
                            mn.setStem('down')
                        mStream.append(mn)
                    lInd += 1
                    pInd += 1
    
        pitches_upper_1 = ['G4','G4','F4','E4','G4','F4','E4','G4','F4','E4','D4','E4','F4','E4','E4','F4','E4','D4','C4','D4','R','E4','F4','E4','D4','E4','D4','C4','D4','C4','D4','C4','D4','E4','R','G4','F4','E4','G4','A4','G4','F4','E4','D4','E4','F4','E4','D4','C4','D4','E4']
        lengths_upper_1 = ['B','M','M','M','M','M','M','P','SB','SM','SM','SM','M','M','P','SB','SM','SM','SM','M','M','P','SB','SB','SB','P','M','M','M','M','M','M','P','SB','M','M','M','M','P','SB','M','M','M','M','P','SB','SM','SM','SM','M','M','P','SB','SM','SM','SM','M','M','L']
        pitches_upper_2 = ['A4','A4','B-4','A4','G4','A4','G4','F4','G4','F4','E4','F4','E4','F4','G4','G4','A4','G4','F4','E4','D4','E4','R','F4','E4','D4','E4','D4','R','E4','F4','G4','D4','R','E4','F4','E','D4','E4','D4','C4','D4','D4','E4','C4','D4','C4','D4','C4','B4','C4']
        lengths_upper_2 = ['SB','SB','P','M','M','M','M','M','M','P','M','M','M','M','M','M','P','SB','SM','SM','SM','SM','SM','SM','P','SB','M','SM','SM','SM','M','P','SB','SB','M','M','P','SB','SB','M','M','P','M','M','M','M','M','M','P','SB','M','SB','M','P','SB','M','M','M','M','L']
        pitches_upper_3 = ['C5','C5','C5','B4','A4','B4','C5','B4','C5','B4','A4','G4','A4','B4','A4','B4','G4','G4','A4','G4','F4','E4','D4','E4','R','E4','F4','G4','F4','E4','F4','E4','F4','G4','R','G4','F4','G4','F4','E4','D4','E4','F4','E4']
        lengths_upper_3 = ['SB','SB','P','SM','SM','SM','M','M','M','M','P','SM','SM','SM','M','M','M','M','P','SB','SM','SM','SM','SM','SM','SM','P','SB','SB','M','M','P','M','M','M','M','M','M','P','SB','SB','M','M','P','SB','SM','SM','SM','M','M','L']
        downStems_upper_3 = [0]
        pitches_upper_4 = ['A4','B4','A4','B4','G4','C5','B4','A4','C5','B4','A4','B4','C5','B4','A4','G4','A4','B4','C5','B4','A4','G4','F4','A4','A4','G4','F4','E4','R','G4','F4','G4','F4','E4','F4','E4','D4','C4','D4','R','A4','G4','A4','G4','F4','E4','D4','E4','R','F4','E4','D4','E4','D4']
        lengths_upper_4 = ['M','M','M','M','SB','P','M','M','M','M','M','M','P','M','M','M','M','M','M','P','SB','SM','SM','SM','M','M','P','SB','M','SB','M','P','SB','SB','M','M','P','M','M','M','M','M','M','P','SB','SB','SB','P','SB','SM','SM','SM','SM','SM','SM','P','M','M','SM','SM','SM','SB','Mx']
        pitches_lower_1 = ['C4','G3','A','B3','C4','D4','C4','R','A3','B3','C4','D4','C4','B3']
        lengths_lower_1 = ['L','B','SB','SB','SB','P','SB','SB','SB','P','SB','SB','SB','P','SB','SB','SB','P']
        lowerlig = medren.Ligature(['A4','B4'])
        lowerlig.makeOblique(0)
        lowerlig.setStem(0, 'down', 'left')
        pitches_lower_2 = ['A4','C5','B4','A4']
        lengths_lower_2 = ['SB','SB','SB','P','L']
        pitches_lower_3 = ['A4','A4','G4','A4','B4','C5','C5','B4','A4','G4','G4','A4','B4','C5','D5','A4','R','G4','A4','B4','B4','C5','C5','D5','D5','A4','A4','G4','A4','B4','C5']
        lengths_lower_3 = ['SB','SB','P','SB','SB','SB','P','SB','M','SB','M','P','SB','SB','P','SB','SB','SB','P','SB','SB','SB','P','SB','SB','P','SB','M','SB','M','P','SB','M','SB','M','P','SB','SB','SB','L']
        downStems_lower_3 = [23]
        pitches_lower_4 = ['C4','C4','E4','D4','C4','C4','D4','E4','D4','R','C4','C4','D4','D4','C4','R','R','C4','D4','C4','D4','E4']
        lengths_lower_4 = ['SB','SB','B','B','SB','SB','SB','P','SB','SB','SB','P','SB','M','SB','M','P','SB','SB','SB','P','SB','SB','M','M','L']
        downStems_lower_4 = [0]
        pitches_lower_5 = ['D4','E4','C4','D4','E4','E4','D4','C4','B3','A3','B3','C4','D4','D4','C4','D4','E4','D4','R','C4','C4','A3','B3','C4','B3','B3','A3','B3','A3','B3','C4','D4']
        lengths_lower_5 = ['SB','SB','P','SB','SB','P','SB','M','SB','M','P','SB','SB','M','M','P','SB','M','SB','M','P','SB','SB','SB','P','SB','M','SB','M','P','SB','SB','SB','P','SB','SB','P','SB','SB','SB','Mx']
        downStems_lower_5 = [0,3]
    
        upperClef = medren.MensuralClef('C')
        upperClef.line = 1
        lowerClef = medren.MensuralClef('C')
        lowerClef.line = 3
    
        upper.append(trecento.notation.Divisione('.p.'))
        upper.append(upperClef)
        processStream(upper, pitches_upper_1, lengths_upper_1)
        processStream(upper, pitches_upper_2, lengths_upper_2)
        processStream(upper, pitches_upper_3, lengths_upper_3, downStems_upper_3)
        processStream(upper, pitches_upper_4, lengths_upper_4)
    
        lower.append(trecento.notation.Divisione('.p.'))
        lower.append(lowerClef)
        processStream(lower, pitches_lower_1, lengths_lower_1)
        lower.append(lowerlig)
        processStream(lower, pitches_lower_2, lengths_lower_2)
        processStream(lower, pitches_lower_3, lengths_lower_3, downStems_lower_3)
        processStream(lower, pitches_lower_4, lengths_lower_4, downStems_lower_4)
        processStream(lower, pitches_lower_5, lengths_lower_5, downStems_lower_5)
    
        SePerDureca.append(upper)
        SePerDureca.append(lower)
    
        upperString = ".p. $C1 g(B) g(M) f e g f e p g(SB) f(SM) e d e(M) f p e(SB) e(SM) f e d(M) c p d(SB) r e p f(M) e d e d c p d(SB) c(M) d c d p e(SB) r(M) g f e p g(SB) a(SM) g f e(M) d p e(SB) f(SM) e d c(M) d e(L) a(SB) a p b(M) a g a g f p g f e f e f p g(SB) g(SM) a g f e d p e(SB) r(M) f(SM) e d e(M) p d(SB) r e(M) f p g(SB) d r(SM) e p f e d e d c p d(SB) d(M) e(SB) c(M) p d(SB) c(M) d c B c(L) c'(SB)[D] c' p c'(SM) b a  b(M) c' b c' p b(SM) a g a(M) b a b p g(SB) g(SM) a g f e d p e(SB) r e(M) f p g f e f e f p g(SB) r g(M) f p g(SB) f(SM) e d e(M) f e(L) a(M) b a b g(SB) p c'(M) b a c' b a p  b c' b a g a p b(SB) c'(SM) b a g(M) f p a(SB) a(M) g(SB) f(M) p e(SB) r g(M) f p g f e f e d p c(SB) d r p a g(SM) a g f e d p e(SB) r f(SM) e d e(SB) d(Mx)"
        lowerString = ".p. $C3 c(L) G(B) A(SB) B c p d c r p A B c p d c B p lig{A<o>[DL] G} A c B A(L) A(SB) A p  G A B p c c(M) B(SB) A(M) p G(SB) G p A B c p d A r p G[D] A p B B(M) c(SB) c(M) p d(SB) d(M) A(SB) A(M) p G(SB) A B C(L) c(SB)[D] c e(B) d c(SB) c d p e d r p c c(M) d(SB) d(M) p c(SB) r r p c d c(M) d e(L) d(SB)[D] e p c[D] d p e e(M) d(SB) c(M) p B(SB) A B(M) c p d(SB) d(M) c(SB) d(M) p e(SB) d r p c c c(M) A(SB) B(M) p c(SB) B B p A B[D] p A B c d(Mx)"
    
        upperConverted = TrecentoTinyConverter(upperString).parse().stream.flat.getElementsNotOfClass('Barline')
        lowerConverted = TrecentoTinyConverter(lowerString).parse().stream.flat.getElementsNotOfClass('Barline')
    
        TinySePerDureca.append(upperConverted)
        TinySePerDureca.append(lowerConverted)
    
        print('''Length comparison
        normal: %s
        tiny: %s
        ''' % (len(list(SePerDureca.recurse())), len(list(TinySePerDureca.recurse()))))
    
        for i in range(2):
            for j in range(len(SePerDureca[i+1])):
                if j < len(TinySePerDureca[i+1]):
                    print('norm: %s' % SePerDureca[i+1][j])
                    print('tiny: %s' % TinySePerDureca[i+1][j])
                    print('')
                else:
                    print('norm only: %s' % SePerDureca[i+1][j])
                    print('')

        #TinySePerDureca.show('text')

class Test(unittest.TestCase):

    def runTest(self):
        pass

if __name__ == '__main__':
    import music21
    music21.mainTest(Test, TestExternal)
