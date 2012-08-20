# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         trecento.notation.py
# Purpose:      music21 classes for representing Trecento notation
#
# Authors:      Varun Ramaswamy
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

''' 
Tools for creating Punctus and Divisione objects unique to Trecento notation. Other objects found in medieval and renaissance music (such as rests, notes, and clef) can be found in the module `music21.medren`.
Also contains functions for converting Trecento notation to modern notation.
'''

import copy
from re import compile, search, match

from music21 import base
from music21 import clef
from music21 import common
from music21 import duration
from music21 import exceptions21
from music21 import interval
from music21 import meter
from music21 import note
from music21 import stream
from music21 import tempo
from music21 import tinyNotation
import unittest, doctest

_validDivisiones = {(None, None):0, ('quaternaria','.q.'):4, ('senaria imperfecta', '.i.'):6, ('senaria perfecta', '.p.'):6, ('novenaria', '.n.'):9, ('octonaria', '.o.'):8, ('duodenaria', '.d.'):12}


#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

class TinyTrecentoNotationStream(tinyNotation.TinyNotationStream):
    '''
    These are modified from a standard lilypond format called TinyNotation.
    
    Here are some important points about how to create notes and streams:
    
    1. Note names are: a,b,c,d,e,f,g. r indicates a rest, and p indicates a punctus.
    
    
    2. Note octaves are specified as follows:
        CC to BB = from C below bass clef to second-line B in bass clef
        C to B = from bass clef C to B below middle C.
        c  to b = from middle C to the middle of treble clef
        c' to b' = from C in treble clef to B above treble clef (make sure you’re NOT putting in smart quotes)
    In 14th c. music, C to B and c to b will be most common
    
    
    3. Flats, sharps, and naturals are notated as #,- (not b), and (if needed) n.  
    If the accidental is above the staff (i.e., editorial), enclose it in parentheses: (#), etc.  Make sure that flats in the key signatures are explicitly specified.  
    
    
    4. The syntax structure for a mensural note is as follows: pitch(mensuralType)[stems]{flags}
    A mensuralType may be any of Mx for maxima, L for longa, B for brevis, SB for semibrevis, M for minima, or SM for semimina. 
    For more information on mensural types, please see the documentation for :class:`music21.medren.generalMensuralNote`.
    If no mensural type is specified, it is assumed to be the same as the previous note. I.e., c(SB) B c d is a string of semibrevises. 
    
    >>> from music21 import *
    >>> tTNN = trecento.notation.TinyTrecentoNotationNote('a(M)')
    >>> tTNN.note.pitch
    A4
    >>> tTNN.note.mensuralType
    'minima'
    
    An additional stem may be added by specifying direction: S for a sidestem, D for a downstem, and an empty string to reset. 
    For example, adding [D] to a note string would add a downstem to that note. Stems must still follow the rules outlined in :meth:`music21.medren.MensuralNote.setStem()`.
    
    >>> from music21 import *
    >>> tTNN = trecento.notation.TinyTrecentoNotationNote('a(SB)[S]')
    >>> tTNN.note.getStems()
    ['side']
    >>> 
    >>> tTNN = trecento.notation.TinyTrecentoNotationNote('a(M)[D]')
    >>> tTNN.note.getStems()
    ['up', 'down']
    
    A flag may be added by specifying direction of stem and orientation of flag. Valid directions are U for up, D for down, and an empty string to reset (sidestems cannot have flags).
    Valid orietations are L for left, R for right, and an empty string to reset. For example, adding {DL} to a note string would add a left flag to that note's downstem.
    Flags must still follow the rules outlined in :meth:`music21.medren.MensuralNote.setFlag()`.
    
    >>> from music21 import *
    >>> tTNN = trecento.notation.TinyTrecentoNotationNote('a(SM){UL}')
    >>> tTNN.note.getStems()
    ['up']
    >>> tTNN.note.getFlags()
    {'up': 'left'}
    
    Multiple flags may be added by placing a space between direction-orientation pairs, as shown in the following complex example:
    
    >>> from music21 import *
    >>> tTNN = trecento.notation.TinyTrecentoNotationNote('a(SM)[D]{UL DR}')
    >>> tTNN.note.getStems()
    ['up', 'down']
    >>> tTNN.note.getFlags()
    {'down': 'right', 'up': 'left'}
    
    
    5. It is also possible to create ligatures using the TinyTrecentoNotationNote class. Put all notes in a ligature within < and > symbols.
    
    >>> from music21 import *
    >>> tTNN = trecento.notation.TinyTrecentoNotationNote('<f g a g f >')
    >>> tTNN.note 
    <music21.medren.Ligature...>
    
    The notes within a ligature have the syntax pitch*notehead*[stems](maxima). Valid notehead shapes are s for square and o for oblique. Valid stem directions are U for up and D for down, and valid orientations are L for left and R for right.
    To set a note of a ligature as a maxima, append (Mx) to the note string. To set a note of a ligature as reversed, append a forward slash to the note string.
    Note, ligatures must follow the rules outlined by :class:`music21.medren.Ligature`.
    Examples:
    
    >>> from music21 import*
    >>> tTNN = trecento.notation.TinyTrecentoNotationNote('<f a[DL]/>')
    >>> tTNN.note.getStem(1)
    ('down', 'left')
    >>> tTNN.note.isReversed(1)
    True
    >>>
    >>> tTNN = trecento.notation.TinyTrecentoNotationNote('<f*o* g a[UR] g f(Mx)>')
    >>> print [n.mensuralType for n in tTNN.note.notes]
    ['longa', 'brevis', 'semibrevis', 'semibrevis', 'maxima']
    >>> tTNN.note.getNoteheadShape(1)
    'oblique'
    
    
    6. Separate objects in a TinyNotationStream by spaces. To add a mensural clef to the stream, add $, followed by the clef type (F or C) to the string. If the clef line on the staff is non-standard, include that after the type.
    For example, $F2 would indicate an F-clef on the second line of the staff. To add a divisione to a tiny notation stream, simply include the divisione abbreviation in the string. For example, .p. would indicate senaria perfecta.
    
    >>> from music21 import *
    >>> tTNS = trecento.notation.TinyTrecentoNotationStream('$C3 .p. c(SB) d e p d(B) <e d c>')
    >>> tTNS.show('text')
    {0.0} <music21.clef.MensuralClef>
    {0.0} <music21.trecento.notation.Divisione .p.>
    {0.0} <music21.medren.MensuralNote semibrevis C>
    {0.0} <music21.medren.MensuralNote semibrevis D>
    {0.0} <music21.medren.MensuralNote semibrevis E>
    {0.0} <music21.trecento.notation.Punctus...>
    {0.0} <music21.medren.MensuralNote brevis D>
    {0.0} <music21.medren.Ligature...>
    '''
    CLEF = compile('(\$[A-Z]\d?)')
    DIVISIONE = compile('(\.[a-z]\.)')
    
    def __init__(self, stringRep = "", div = None):
        tinyNotation.TinyNotationStream.__init__(self)
        self.stringRep = stringRep
        divisione, mensuralClef = None, None
        storedDict = {}
        objList = []
        
        noteStrs  = []
        from music21 import medren

        def breakString(string, startBreakChar, endBreakChar, func = lambda s: s.split()):
            
            broken = []
            while len(string) > 0:
                startInd = string.find(startBreakChar)
                endInd = string.find(endBreakChar) + 1
                
                if startInd == -1 and endInd == 0:
                    broken += string.split()
                    break
                
                elif startInd != -1 and endInd != 0:
                    while string[startInd] != ' ':
                        startInd -= 1
                    
                    broken += func(string[:startInd])
                    broken.append(string[startInd:endInd])
                    string = string[endInd+1:]
                
                else:
                    raise TrecentoNotationException('%s, %s invalid ligature indices' % (startInd, endInd))
            return broken
            
            
        noteStrs = breakString(stringRep, '<', '>', lambda s: breakString(s, '{', '}'))    
                
        if div is not None:
            divisione = div
        
        for ns in noteStrs:
            ns = ns.strip()
            
            if self.CLEF.match(ns) is not None:
                clefString = self.CLEF.match(ns).group()[1:]
                clef = medren.MensuralClef(clefString[0])
                if len(clefString) > 1:
                    clef.line = clefString[1]
                objList.append(clef)
            
            elif self.DIVISIONE.match(ns) is not None:
                divisioneString = self.DIVISIONE.match(ns).group()
                objList.append(Divisione(divisioneString))
            
            else:
                tTN = None
                try:
                    tTN = self.getNote(ns, storedDict)
                    objList.append(tTN.note)
                except TrecentoNotationException, (value):
                    raise TrecentoNotationException('%s in context %s' % (value, ns))
        
        for obj in objList:
            self.append(obj)
        
    def getNote(self, stringRep, storedDict = {}):
        
        return TinyTrecentoNotationNote(stringRep, storedDict)    

class TinyTrecentoNotationNote(tinyNotation.TinyNotationNote):
    ''' 
    For documentation please see :class:`music21.trecento.notation.TinyTrecentoNotationStream`.
    '''
    LIGATURE = compile('\<.+\>')
    PUNCTUS = compile('p')
    MENSURALTYPE = compile('\([A-Z][A-Za-z]?\)')
    STEMS = compile('\[[A-Z]?(\s[A-Z])*\]')
    FLAGS = compile('\{([A-Z][A-Z])?(\s[A-Z][A-Z])*\}')
    LIG_STEMS = compile('\[[A-Z][A-Z]\]')
    LIG_NOTEHEAD = compile('\*[a-z]\*')
    LIG_REVERSE = compile('.\/')
    
    def _getPitch(self, stringRep):
        if (self.OCTAVE2.match(stringRep)) is not None: # BB etc.
            step = self.OCTAVE2.match(stringRep)
            octave = 3 - len(step.group(1))
            pitchObj = pitch.Pitch(step.group(1)[0])
            pitchObj.octave = octave
            
        elif (self.OCTAVE3.match(stringRep)) is not None:
            step = self.OCTAVE3.match(stringRep).group(1)
            octave = 3
            pitchObj = pitch.Pitch(step)
            pitchObj.octave = octave
            
        elif (self.OCTAVE5.match(stringRep)) is not None: # must match octave 5 then 4!
            step = self.OCTAVE5.match(stringRep)
            octave = 4 + len(step.group(2))
            pitchObj = pitch.Pitch(step.group(1)[0])
            pitchObj.octave = octave
            
        elif (self.OCTAVE4.match(stringRep)) is not None: 
            step = self.OCTAVE4.match(stringRep).group(1)
            octave = 4
            pitchObj = pitch.Pitch(step)
            pitchObj.octave = octave
        else:
            raise TrecentoNotationException("could not get pitch information from " + str(stringRep))
        
        return pitchObj
    
    def customPitchMatch(self, stringRep, storedDict):
        from music21 import medren

        noteLikeObject = None
        storedDict['lastDuration'] = duration.ZeroDuration()
            
        if self.LIGATURE.search(stringRep) is not None:
            noteLikeObj = medren.Ligature()
            
        elif self.PUNCTUS.search(stringRep) is not None:
            noteLikeObj = Punctus()
            
        elif self.REST.search(stringRep) is not None:
            noteLikeObj = medren.MensuralRest()
            
        else:
            noteLikeObj = medren.MensuralNote(self._getPitch(stringRep))
        
        return noteLikeObj
    
    def customNotationMatch(self, noteLikeObject, stringRep, storedDict):
        from music21 import medren
        
        if isinstance(noteLikeObject, medren.Ligature): #Ligature syntax
            
            ligString = stringRep[1:-1] 
            ligList = ligString.split()
            noteLikeObject.pitches = [self._getPitch(p[0]) for p in ligList]
            
            index = 0
            direction = {'D': 'down', 'U':'up'}
            orientation = {'L': 'left', 'R': 'right'}

            for ligNote in ligList:
                
                if self.LIG_STEMS.search(ligNote) is not None:
                    ligstem = self.LIG_STEMS.search(ligNote).group()[1:-1]
                    if len(ligstem) > 1 and (ligstem[0] in direction) and (ligstem[1] in orientation): 
                        noteLikeObject.setStem(index, direction[ligstem[0]], orientation[ligstem[1]])
                    else:
                        raise TrecentoNotationException('cannot determine ligature stem from %s' % ligstem)
                
                if self.LIG_NOTEHEAD.search(ligNote) is not None:
                    notehead = self.LIG_NOTEHEAD.search(ligNote).group()[1:-1]
                    if notehead == 'o':
                        noteLikeObject.makeOblique(index)
                    elif notehead == 's':
                        noteLikeObject.makeSquare(index)
                    else:
                        raise TrecentoNotationException('cannot make out notehead shape from %s' % notehead)      
                
                if self.MENSURALTYPE.search(ligNote) is not None:
                    mensuralType = self.MENSURALTYPE.search(ligNote).group()[1:-1]
                    if mensuralType == 'Mx':
                        noteLikeObject.setMaxima(index, True)
                
                if self.LIG_REVERSE.search(ligNote) is not None:
                    noteLikeObject.setReverse(index, True)
                
                index += 1
            
        else: #Note syntax
            
            if self.MENSURALTYPE.search(stringRep) is not None:
                mensuralType = self.MENSURALTYPE.search(stringRep).group()[1:-1]
                
                if mensuralType in ['Mx','L','B','SB','M','SM']:
                    noteLikeObject.mensuralType = mensuralType
                    storedDict['previousMensuralType'] = mensuralType
                else:
                    raise TrecentoNotationException('could not determine mensural type from %s' % mensuralType)
            else:
                if 'previousMensuralType' in storedDict:
                    noteLikeObject.mensuralType = storedDict['previousMensuralType']
                
            direction = {'': None, 'S': 'side', 'D': 'down', 'U':'up'}
            orientation = {'': None,'L': 'left', 'R': 'right'}
            
            if self.STEMS.search(stringRep) is not None:
                stems = self.STEMS.search(stringRep).group()[1:-1]
                
                for stem in stems.split():
                    if stem in direction:
                        noteLikeObject.setStem(direction[stem])
                    else:
                        raise TrecentoNotationException('could not determine stem direction from %s' % stem)
            
            if self.FLAGS.search(stringRep) is not None:
                flags = self.FLAGS.search(stringRep).group()[1:-1]
                
                for flag in flags.split():
                    if len(flag) > 1 and (flag[0] in direction) and (flag[1] in orientation): 
                        noteLikeObject.setFlag(direction[flag[0]], orientation[flag[1]])
                    else:
                        raise TrecentoNotationException('cannot determsine flag from %s' % flag)
        
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

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
    
    >>> from music21 import *
    >>> d = trecento.notation.Divisione('senaria imperfecta')
    >>> d.standardSymbol
    '.i.'
    >>> d = trecento.notation.Divisione('.p.')
    >>> d.name
    'senaria perfecta'
    >>> d = trecento.notation.Divisione('q')
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
        return '<music21.trecento.notation.Divisione %s>' % self.standardSymbol
    
    __repr__ = __str__
    
    def _getMinimaPerBrevis(self):
        return self._minimaPerBrevis
    
    def _setMinimaPerBrevis(self, mPM):
        self._minimaPerBrevis = mPM 
    
    minimaPerBrevis = property(_getMinimaPerBrevis, _setMinimaPerBrevis, 
                                doc = '''Used to get and set the number of minima in a 'measure' (the number of minima before a punctus occurs) under the given divisione.
                                
                                >>> from music21 import *
                                >>> n = trecento.notation.Divisione('.n.')
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
    
    >>> from music21 import *
    >>> upperString = ".p. $C1 g(B) g(M) f e g f e p g(SB) f(SM) e d e(M) f p e(SB) e(SM) f e d(M) c p "
    >>> upperString += "d(SB) r e p f(M) e d e d c p d(SB) c(M) d c d p e(SB) r(M) g f e p g(SB) a(SM) g f e(M) d p "
    >>> upperString += "e(SB) f(SM) e d c(M) d e(L) a(SB) a p b(M) a g a g f p g f e f e f p "
    >>> upperString += "g(SB) g(SM) a g f e d p e(SB) r(M) f(SM) e d e(M) p d(SB) r e(M) f p "
    >>> upperString += "g(SB) d r(SM) e p f e d e d c p d(SB) d(M) e(SB) c(M) p d(SB) c(M) d c B c(L) "
    >>> upperString += "c'(SB)[D] c' p c'(SM) b a  b(M) c' b c' p b(SM) a g a(M) b a b p "
    >>> upperString += "g(SB) g(SM) a g f e d p e(SB) r e(M) f p g f e f e f p g(SB) r g(M) f p "
    >>> upperString += "g(SB) f(SM) e d e(M) f e(L) a(M) b a b g(SB) p c'(M) b a c' b a p "
    >>> upperString += "b c' b a g a p b(SB) c'(SM) b a g(M) f p a(SB) a(M) g(SB) f(M) p "
    >>> upperString += "e(SB) r g(M) f p g f e f e d p c(SB) d r p a g(SM) a g f e d p e(SB) r f(SM) e d e(SB) d(Mx)"

    >>> lowerString = ".p. $C3 c(L) G(B) A(SB) B c p d c r p A B c p d c B p <A*o*[DL] G> A c B A(L) "
    >>> lowerString += "A(SB) A p  G A B p c c(M) B(SB) A(M) p G(SB) G p A B c p d A r p G[D] A p "
    >>> lowerString += "B B(M) c(SB) c(M) p d(SB) d(M) A(SB) A(M) p G(SB) A B C(L) "
    >>> lowerString += "c(SB)[D] c e(B) d c(SB) c d p e d r p c c(M) d(SB) d(M) p c(SB) r r p "
    >>> lowerString += "c d c(M) d e(L) d(SB)[D] e p c[D] d p e e(M) d(SB) c(M) p B(SB) A B(M) c p "
    >>> lowerString += "d(SB) d(M) c(SB) d(M) p e(SB) d r p c c c(M) A(SB) B(M) p c(SB) B B p A B[D] p A B c d(Mx)"

    >>> SePerDureca.append(trecento.notation.TinyTrecentoNotationStream(upperString))
    >>> SePerDureca.append(trecento.notation.TinyTrecentoNotationStream(lowerString))

    >>> SePerDurecaConverted = trecento.notation.convertTrecentoStream(SePerDureca)
    Getting measure 0...
    ...
    
    >>> SePerDurecaConverted2 = medren.convertHouseStyle(SePerDurecaConverted, durationScale = 1, barlineStyle = 'tick')
    >>> #_DOCS_HIDE SePerDurecaConverted2.show()

    .. image:: images/medren_SePerDurecaConverted.*
        :width: 600
    
    '''
    from music21 import medren

    div = inpDiv
    offset = 0

    convertedStream = inpStream.__class__()
    measuredStream = medren.breakMensuralStreamIntoBrevisLengths(inpStream, inpDiv)
    print ''
    
    for e in measuredStream:
        
        if isinstance(e, metadata.Metadata) or \
        isinstance(e, text.TextBox): #Formatting
            convertedStream.append(e)
        
        elif isinstance(e, medren.MensuralClef):
            pass
        
        elif isinstance(e, Divisione):
            div = e
        
        elif isinstance(e, stream.Measure):
            print '    Converting measure %s' % e.number
            measureList = convertBrevisLength(e, convertedStream, inpDiv = div, measureNumOffset = offset)
            for m in measureList:
                convertedStream.append(m)
            
        elif isinstance(e, stream.Stream):
            print 'Converting stream %s' % e
            convertedStream.insert(0, convertTrecentoStream(e, inpDiv = div))
        
        else:
            raise medren.MedRenException('Object %s cannot be processed as part of a trecento stream' % e)
    
    return convertedStream

def convertBrevisLength(brevisLength, convertedStream, inpDiv = None, measureNumOffset = 0):
    '''
    Takes two required arguments, a measure object and a stream containing modern objects.
    Takes two optional arguments, inpDiv and measureNumOffset.
    
    :meth:`music21.trecento.notation.convertBrevisLength` converts each of the objects in the measure to their modern equivalents using the translateBrevisLength object.
    inpDiv is a divisione possibly coming from a some higher context. measureNumOffset helps calculate measure number.
    
    This acts as a helper method to improve the efficiency of :meth:`music21.trecento.notation.convertTrecentoStream`.
    '''
    from music21 import medren
    
    div = inpDiv
    m = stream.Measure(number = brevisLength.number + measureNumOffset)
    rem = None
    measureList = []
        
    mList = brevisLength.recurse()[1:]
    tempTBL = TranslateBrevisLength(div, mList)    
    
    lenList = tempTBL.getMinimaLengths()
    
    for item in mList:
        if isinstance(item, Divisione):
            if div is None:
                div = item
            else:
                raise TrecentoNotationException('divisione %s not consistent within heirarchy' % e) #Should already be caught by medren.breakMensuralStreamIntoBrevisLengths, but just in case...
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
        
        for j in range(int(lenList[0]/div.minimaPerBrevis) - 2):
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
        finalNote.tie = tie.Tie('end')
        finalMeasure.append(finalNote)
        measureList.append(finalMeasure)
        
    else:
        for i in range(len(mList)):
            if isinstance(mList[i], medren.MensuralRest):
                n = note.Rest()
            elif isinstance(mList[i], medren.MensuralNote):
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

class TranslateBrevisLength:
    '''
    The class :class:`music21.trecento.notation.TranslateBrevisLength` takes a divisione sign and a list comprising one brevis length's worth of mensural or trecento objects as arguments.
    The method :meth:`music21.trecento.notation.TranslateBrevisLength.getMinimaLengths` takes no arguments, and returns a list of floats corresponding to the length (in minima) of each object in the list.
    Currently, this class is used only to improve the efficiency of :attr:`music21.medren.GeneralMensuralNote.duration`.
    
    This acts a helper class to improve the efficiency of :class:`music21.trecento.notation.convertBrevisLength`.
    
    >>> from music21 import *
    >>> div = trecento.notation.Divisione('.i.')
    >>> names = ['SB', 'M', 'SB']
    >>> BL = [medren.MensuralNote('A', n) for n in names]
    >>> TBL = trecento.notation.TranslateBrevisLength(div, BL)
    >>> TBL.getMinimaLengths()
    [2.0, 1.0, 3.0]
    >>>
    >>>
    >>> div = trecento.notation.Divisione('.n.')
    >>> names = ['SB', 'M', 'M', 'M', 'SB', 'M']
    >>> BL = [medren.MensuralNote('A', n) for n in names]
    >>> TBL = trecento.notation.TranslateBrevisLength(div, BL)
    >>> TBL.getMinimaLengths()
    [3.0, 1.0, 1.0, 1.0, 2.0, 1.0]
    >>> names = ['SB', 'M', 'SB']
    >>> BL = [medren.MensuralNote('A', n) for n in names]
    >>> TBL = trecento.notation.TranslateBrevisLength(div, BL)
    >>> TBL.getMinimaLengths()
    [2.0, 1.0, 6.0]
    >>> BL[0].setStem('down')
    >>> TBL = trecento.notation.TranslateBrevisLength(div, BL)
    >>> TBL.getMinimaLengths()
    [5.0, 1.0, 3.0]
    >>>
    >>>
    >>> div = trecento.notation.Divisione('.q.')
    >>> names = ['M', 'SM', 'SM', 'SM', 'SM', 'SM']
    >>> BL = [medren.MensuralNote('A', n) for n in names]
    >>> BL[4] = medren.MensuralRest('SM')
    >>> BL[1].setFlag('up','left')
    >>> BL[2].setFlag('up', 'left')
    >>> TBL = trecento.notation.TranslateBrevisLength(div, BL)
    >>> TBL.getMinimaLengths()
    [1.0, 0.5, 0.5, 0.666..., 0.666..., 0.666...]
    >>>
    >>>
    >>> div = trecento.notation.Divisione('.p.')
    >>> names = ['M', 'SB', 'SM', 'SM']
    >>> BL = [medren.MensuralNote('A', n) for n in names]
    >>> BL[1].setStem('down')
    >>> TBL = trecento.notation.TranslateBrevisLength(div, BL)
    >>> TBL.getMinimaLengths()
    [1.0, 4.0, 0.5, 0.5]
    >>> names = ['SM', 'SM', 'SM', 'SM', 'SM', 'SM', 'SM', 'SB']
    >>> BL = [medren.MensuralNote('A', n) for n in names]
    >>> BL[3] = medren.MensuralRest('SM')
    >>> for mn in BL[:3]:
    ...    mn.setFlag('up', 'left')
    >>> TBL = trecento.notation.TranslateBrevisLength(div, BL)
    >>> TBL.getMinimaLengths()
    [0.666..., 0.666..., 0.666..., 0.5, 0.5, 0.5, 0.5, 2.0]
    >>>
    >>>
    >>> div = trecento.notation.Divisione('.o.')
    >>> names = ['SB', 'SB', 'SB']
    >>> BL = [medren.MensuralNote('A', n) for n in names]
    >>> BL[1].setStem('down')
    >>> TBL = trecento.notation.TranslateBrevisLength(div, BL)
    >>> TBL.getMinimaLengths()
    [2.0, 4.0, 2.0]
    >>> names = ['SM', 'SM', 'SM', 'SB', 'SB']
    >>> BL = [medren.MensuralNote('A', n) for n in names]
    >>> TBL = trecento.notation.TranslateBrevisLength(div, BL)
    >>> TBL.getMinimaLengths()
    [0.666..., 0.666..., 0.666..., 2.0, 4.0]
    >>>
    >>>
    >>> div = trecento.notation.Divisione('.d.')
    >>> names = ['SB', 'SB']
    >>> BL = [medren.MensuralNote('A', n) for n in names]
    >>> TBL = trecento.notation.TranslateBrevisLength(div, BL)
    >>> TBL.getMinimaLengths()
    [4.0, 8.0]
    >>> names = ['SB', 'SB', 'SB']
    >>> BL = [medren.MensuralNote('A', n) for n in names]
    >>> TBL = trecento.notation.TranslateBrevisLength(div, BL)
    >>> TBL.getMinimaLengths()
    [4.0, 4.0, 4.0]
    >>> names = ['SB', 'SB', 'SB', 'SB']
    >>> BL = [medren.MensuralNote('A', n) for n in names]
    >>> TBL = trecento.notation.TranslateBrevisLength(div, BL)
    >>> TBL.getMinimaLengths()
    [2.0, 2.0, 4.0, 4.0]
    >>> BL[1].setStem('down')
    >>> BL[2].setStem('down')
    >>> TBL = trecento.notation.TranslateBrevisLength(div, BL)
    >>> TBL.getMinimaLengths()
    [2.0, 4.0, 4.0, 2.0]
    >>> names = ['SM', 'SM', 'SM', 'SM', 'SB', 'SB', 'SB', 'SB', 'SB', 'SM', 'SM', 'SM']
    >>> BL = [medren.MensuralNote('A', n) for n in names]
    >>> BL[3] = medren.MensuralRest('SM')
    >>> for mn in BL[-3:]:
    ...    mn.setFlag('up', 'left')
    >>> for mn in BL[4:9]:
    ...    mn.setStem('down')
    >>> TBL = trecento.notation.TranslateBrevisLength(div, BL)
    >>> TBL.getMinimaLengths()
    [0.5, 0.5, 0.5, 0.5, 4.0, 4.0, 4.0, 4.0, 4.0, 0.666..., 0.666..., 0.666...]
    '''
    
    def __init__(self, divisione = None, BL = [], pDS = False):
                
        self.div = divisione
        self.brevisLength = BL
        self.minimaLengthList = [0 for i in range(len(self.brevisLength))]
        
        self.processing_downstems = pDS
        self.doubleNum = 0
        
    def getMinimaLengths(self):
        if isinstance(self.div, Divisione):
           self.minimaLengthList = self._translate()
        else:
           raise TrecentoNotationException('%s not recognized as divisione' % divisione)
        return self.minimaLengthList
    
    def _evaluateBL(self, div, BL, lengths):
        ''':meth:`TranslateBrevisLength._evaluateBL takes divisione, a brevis length's worth of mensural or trecento objects in a list, and a list of lengths corresponding to each of those objects as arguments.
        This method returns the ``strength'' of the list based on those lengths. A ``strong'' list has longer notes on its stronger beats. Only valid for Trecento notation.'''
    
        typeStrength = {'semibrevis': 1.0, 'minima': 0.5, 'semiminima':0.25}
           
        beatStrength = 0
        strength = 0
        curBeat = 0
        for i in range(len(lengths)):
            if abs(curBeat - round(curBeat)) < 0.0001: #Rounding error
                curBeat = round(curBeat)
            
            if div.standardSymbol in ['.i.', '.n.']:
                if abs(curBeat % 3) < 0.0001:
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
            strength += typeStrength[BL[i].mensuralType]*beatStrength
            curBeat += lengths[i]
        strength -= abs(div.minimaPerBrevis - curBeat)
        return strength
       
    def _translate(self):
        #########################################################################################################################################
        from music21 import medren

        def processBL(bl, lengths, change_list, change_nums, diff_list, lenRem, releases = None, multi = 0):
            '''
            Gets all possible length combinations. Returns the lengths combination of the "strongest" list, along with the remaining length. 
            '''
            
            def allCombinations(list, num):
                combs = [[]]
                if num > 0:
                    for i in range(len(list)):
                        comb = [list[i]]
                        for c in allCombinations(list[(i+1):], num-1):
                            combs.append(comb + c)
                combs.reverse()
                return combs
            
            if isinstance(change_list, tuple):
                change = change_list[0]
            else:
                change = change_list
            if isinstance(change_nums, tuple):
                change_num = change_nums[0]
            else:
                change_num = change_nums
            if isinstance(diff_list, tuple):
                diff = diff_list[0]
            else:
                diff = diff_list
            if releases is not None and isinstance(releases, list):
                release = releases[0]
            else:
                release = releases
                
            strength = self._evaluateBL(self.div, bl, lengths)
            lengths_changeable = lengths[:]
            lengths_static = lengths[:]
            remain = lenRem
            lenRem_final  = lenRem
            
            if multi == 0:
                for l in allCombinations(change, change_num):
                    l.reverse()
                    for i in l:
                        lengths_changeable[i] += diff
                        if release is not None:
                            lengths_changeable[release] -= diff
                        else:
                            remain -= diff
        
                    newStrength = self._evaluateBL(self.div, bl, lengths_changeable)
                    if strength < newStrength and remain >= 0:
                        lengths = lengths_changeable[:]
                        strength = newStrength
                        lenRem_final = remain
                    lengths_changeable = lengths_static[:]
                    remain = lenRem
                return lengths, lenRem_final
            
            else:
                for l in allCombinations(change, change_num):
                    l.reverse()
                    for i in l:
                        lengths_changeable[i] += diff
                        if release is not None:
                            lengths_changeable[release] -= diff
                            lengths_changeable, remain = processBL(bl, lengths_changeable, change_list[1:], change_nums[1:], diff_list[1:], remain, releases[1:], multi-1)
                        else:
                            remain -= diff
                            lengths_changeable, remain = processBL(bl, lengths_changeable, change_list[1:], change_nums[1:], diff_list[1:], remain, multi-1)
                    
                    newStrength = self._evaluateBL(self.div, bl, lengths_changeable)
                    if strength < newStrength and remain >= 0:
                        lengths = lengths_changeable[:]
                        strength = newStrength
                        lenRem_final = remain
                    lengths_changeable = lengths_static[:]
                    remain = lenRem
                return lengths, lenRem_final
        
        ##################################################################################################################################
            
        minRem = self.div.minimaPerBrevis
        minRem_tracker = self.processing_downstems
        minimaLengths = self.minimaLengthList[:]
        
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
            minimaLength = 0
            #If its duration is set, doesn't need to be determined
            
            #Gets rid of everything known 
            if obj.mensuralType == 'maxima':
                minimaLength = float(4)*self.div.minimaPerBrevis
            elif obj.mensuralType == 'longa':
                minimaLength = float(2)*self.div.minimaPerBrevis
            elif obj.mensuralType == 'brevis':
                minimaLength = float(self.div.minimaPerBrevis)
            elif minimaLengths[i] == 0 and \
            ( isinstance(obj, medren.MensuralNote) or isinstance(obj, medren.MensuralRest) ):
                #Dep on div
                if obj.mensuralType == 'semibrevis':
                    if isinstance(obj, medren.MensuralRest):
                        if self.div.standardSymbol in ['.q.', '.i.']:
                            minimaLength = self.div.minimaPerBrevis/float(2)
                        elif self.div.standardSymbol in ['.p.', '.n.']:
                            minimaLength = self.div.minimaPerBrevis/float(3)
                        else: 
                            semibrevis_list.append(i)
                    else:
                        if 'side' in obj.getStems():
                            minimaLength = 3.0
                        elif 'down' in obj.getStems():
                            semibrevis_downstem.append(i)
                        else:
                            semibrevis_list.append(i)
                if obj.mensuralType == 'minima':
                    if isinstance(obj, medren.MensuralNote) and 'down' in obj.stems:
                        raise TrecentoNotationException('Dragmas currently not supported')
                    elif isinstance(obj, medren.MensuralNote) and 'side' in obj.stems:
                        minimaLength = 1.5
                    else:
                        minimaLength = 1.0
                if obj.mensuralType == 'semiminima':
                    if isinstance(obj, medren.MensuralNote):
                        if 'down' in obj.getStems():
                            raise TrecentoNotationException('Dragmas currently not supported')
                        elif obj.getFlags()['up'] == 'right':
                            semiminima_right_flag_list.append(i)
                        elif obj.getFlags()['up'] == 'left':
                            semiminima_left_flag_list.append(i)
                    if isinstance(obj, medren.MensuralRest):
                        semiminima_rest_list.append(i) 
                minRem -= minimaLength
            minimaLengths[i] = minimaLength

        #Process everything else           
        if self.div.standardSymbol == '.i.':
            if len(semibrevis_list) > 0:
                avgSBLength = minRem/len(semibrevis_list)
                for ind in semibrevis_list:
                    if avgSBLength == 2:
                        minimaLengths[ind] = 2.0
                        minRem -= 2.0
                    elif (2 < avgSBLength) and (avgSBLength < 3):
                        if ind < (len(self.brevisLength)-1) and self.brevisLength[ind+1].mensuralType == 'minima':
                            minimaLengths[ind] = 2.0
                            minRem -= 2.0
                        else:
                            minimaLengths[ind] = 3.0
                            minRem -= 3.0
                    elif avgSBLength == 3.0:
                        minimaLengths[ind] = 3.0
                        minRem -= 3.0
            minRem_tracker = minRem_tracker or (minRem > -0.0001) 
        
        elif self.div.standardSymbol == '.n.':
            extend_list = [] #brevises able to be lengthened
            extend_num = 0
            if len(semibrevis_list) > 0:
                if semibrevis_list[-1] == (len(self.brevisLength) - 1) and len(semibrevis_downstem) == 0:
                    for ind in semibrevis_list[:-1]:
                        if self.brevisLength[ind+1].mensuralType == 'minima':
                            minimaLengths[ind] = 2.0
                            minRem -= 2.0
                            extend_list.append(ind)
                        else:
                            minimaLengths[ind] = 3.0
                            minRem -= 3.0
                    minimaLengths[-1] = max(minRem, 3.0)
                    minRem -= max(minRem, 3.0)
            
                    extend_num = min(minimaLengths[-1] - 3, len(extend_list))
                    if minRem >= 0:
                        minimaLengths, minRem = processBL(self.brevisLength, minimaLengths, extend_list, extend_num, 1,  minRem, releases = -1)
                else:
                    for ind in semibrevis_list:
                        if ind < (len(self.brevisLength)-1) and self.brevisLength[ind+1].mensuralType == 'minima':
                            minimaLengths[ind] = 2.0
                            minRem -= 2.0
                            extend_list.append(ind)
                        else:
                            minimaLengths[ind] = 3.0
                            minRem -= 3.0
                    if len(semibrevis_downstem) == 0:
                        extend_num = min(minRem, len(extend_list))
                        if minRem >= 0:
                            minimaLengths, minRem = processBL(self.brevisLength, minimaLengths, extend_list, extend_num, 1, minRem)
                    else:
                        semibrevis_downstem = semibrevis_downstem[0]
                        minimaLengths[semibrevis_downstem] = max(minRem, 3.0)
                        minRem -= max(minRem, 3.0)
                        extend_num = min(minimaLengths[semibrevis_downstem] - 4, len(extend_list))
                        if semibrevis_downstem != len(self.brevisLength) - 1:
                            if minRem >= 0:
                                minimaLengths, minRem = processBL(self.brevisLength, minimaLengths, extend_list, extend_num, 1, minRem, releases = semibrevis_downstem)
                minRem_tracker = minRem_tracker or (minRem > -0.0001)
                        
        elif self.div.standardSymbol == '.q.' or self.div.standardSymbol == '.p.':
            extend_list = []
            extend_num = 0
            
            if len(semibrevis_downstem) == 0:
                semibrevis_downstem = None
            else: #Only room for one downstem per brevis length
                semibrevis_downstem = semibrevis_downstem[0] 
                
            for ind in semibrevis_list[:-1]:
                minimaLengths[ind] = 2.0
                minRem -= 2.0
            
            if semibrevis_downstem == (len(self.brevisLength) - 1):
                for ind in semiminima_right_flag_list+semiminima_left_flag_list+semiminima_rest_list:
                    minimaLengths[ind] = 0.5
                    minRem -= 0.5
                minimaLengths[semibrevis_downstem] = minRem
                minRem = 0
            else:
                strength = 0
                minimaLengths_changeable = minimaLengths[:]
                minimaLengths_static = minimaLengths[:]
                minRem_changeable = minRem 
                minRem_static = minRem
                
                if len(semiminima_right_flag_list) > 0 and len(semiminima_left_flag_list) > 0:
                    lengths = [(0.5,0.5), (float(2)/3, 0.5), (0.5, float(2)/3), (float(2)/3, float(2)/3)]
    
                    for (left_length, right_length) in lengths:
                        for ind in semiminima_left_flag_list:
                            minimaLengths_changeable[ind] = left_length
                            minRem_changeable -= left_length
                        for ind in semiminima_right_flag_list:
                            minimaLengths_changeable[ind] = right_length
                            minRem_changeable -= right_length
                            
                        if left_length == right_length:
                            for ind in semiminima_rest_list:
                                minimaLengths_changeable[ind] = left_length
                                minRem_changeable -= left_length
                            if semibrevis_downstem is not None:
                                if len(semibrevis_list) > 0:
                                    minimaLengths_changeable[semibrevis_list[-1]] = 2.0
                                    minRem_changeable -= 2.0
                                minimaLengths_changeable[semibrevis_downstem] = max(2.0, minRem_changeable)
                                minRem_changeable -= max(2.0, minRem_changeable)
                            else:
                                if len(semibrevis_list) > 0 and semibrevis_list[-1] == len(self.brevisLength) - 1:
                                    minimaLengths_changeable[semibrevis_list[-1]] = max(2.0, minRem_changeable)
                                    minRem_changeable -= max(2.0, minRem_changeable)
                                else:
                                    if len(semibrevis_list) > 0:
                                        minimaLengths_changeable[semibrevis_list[-1]] = 2.0
                                        minRem_changeable -= 2.0
                        else:
                            master_list = semiminima_left_flag_list + semiminima_right_flag_list + semiminima_rest_list
                            
                            for ind in semiminima_rest_list:
                                curIndex = int(master_list.index(ind))
                                if ( curIndex == 0 and master_list[curIndex+1] in semiminima_left_flag_list ) or \
                                     ( curIndex == len(master_list) - 1 and master_list[curIndex - 1] in semiminima_left_flag_list ) or \
                                     ( master_list[curIndex-1] in semiminima_left_flag_list and master_list[curIndex+1] in semiminima_left_flag_list ):
                                    minimaLengths_changeable[ind] = left_length
                                    minRem_changeable -= left_length
                                elif ( (curIndex == 0 and master_list[curIndex+1] in semiminima_right_flag_list) or
                                     (curIndex == len(master_list) - 1 and master_list[curIndex - 1] in semiminima_right_flag_list) or
                                     (master_list[curIndex-1] in semiminima_right_flag_list and master_list[curIndex+1] in semiminima_right_flag_list) ):
                                    minimaLengths_changeable[ind] = right_length
                                    minRem_changeable -= right_length
                                else:
                                    minimaLengths_changeable[ind] = 0.5
                                    extend_list.append(ind)
                                extend_list = list(set(extend_list)) #repeated iterations
                            
                            if semibrevis_downstem is not None:
                                if len(semibrevis_list) > 0:
                                    minimaLengths_changeable[semibrevis_list[-1]] = 2.0
                                    minRem_changeable -= 2.0
                                minimaLengths_changeable[semibrevis_downstem] = max(minRem_changeable, 2.0)
                                extend_num = min(6*minRem_changeable - 15.0, len(extend_list))
                                minRem_changeable -= max(minRem_changeable, 2.0)
                                if minRem_changeable >= 0:
                                    minimaLengths_changeable, minRem_changeable = processBL(self.brevisLength, minimaLengths_changeable, extend_list, extend_num, float(1)/6, minRem_changeable, releases = semibrevis_downstem)
                            else:
                                if len(semibrevis_list) > 0 and semibrevis_list[-1] == len(self.brevisLength) - 1:
                                    minimaLengths_changeable[semibrevis_list[-1]] = max(minRem_changeable, 2.0)
                                    extend_num = min(6*minRem_changeable - 12.0, len(extend_list))
                                    minRem_changeable -= max(minRem_changeable, 2.0)
                                    if minRem_changeable >= 0:
                                        minimaLengths_changeable, minRem_changeable = processBL(self.brevisLength, minimaLengths_changeable, extend_list, extend_num, float(1)/6, minRem_changeable, releases = -1)
                                else:
                                    if len(semibrevis_list) > 0:
                                        minimaLengths_changeable[semibrevis_list[-1]] = 2.0
                                        minRem_changeable -= 2.0
                                    
                                    extend_num = len(extend_list)
                                    if minRem_changeable >= 0:
                                        minimaLengths_changeable, minRem_changeable = processBL(self.brevisLength, minimaLengths_changeable, extend_list, extend_num, float(1)/6, minRem_changeable)                                      
                                    
                        tempStrength = self._evaluateBL(self.div, self.brevisLength, minimaLengths_changeable)      

                        if (tempStrength > strength) and (minRem_changeable > -0.0001): #Technically, >= 0, but rounding error occurs.
                            minimaLengths = minimaLengths_changeable[:]
                            minRem = minRem_changeable
                            strength = tempStrength
                        minimaLengths_changeable = minimaLengths_static
                        minRem_tracker = minRem_tracker or (minRem_changeable > -0.0001)
                        minRem_changeable = minRem_static
                        
                elif len(semiminima_left_flag_list) == 0 and len(semiminima_right_flag_list) == 0:
                    
                    if semibrevis_downstem is not None:
                        if len(semibrevis_list) > 0:
                            minimaLengths[semibrevis_list[-1]] = 2.0
                            minRem -= 2.0
                        minimaLengths[semibrevis_downstem] = max(minRem, 2.0)
                        minRem -= max(minRem, 2.0)
                    else:
                        if len(semibrevis_list) > 0 and semibrevis_list[-1] == len(self.brevisLength) - 1:
                            minimaLengths[semibrevis_list[-1]] = max(minRem, 2.0)
                            minRem -= max(minRem, 2.0)
                        else:
                            if len(semibrevis_list) > 0:
                                minimaLengths[semibrevis_list[-1]] = 2.0
                                minRem -= 2.0
                    minRem_tracker = minRem_tracker or (minRem > -0.0001)            
                else:
                    lengths = [0.5, float(2)/3]
                    master_list = semiminima_left_flag_list + semiminima_right_flag_list + semiminima_rest_list
                    
                    for length in lengths:
                        for ind in master_list:
                            minimaLengths_changeable[ind] = length
                            minRem_changeable -= length
                        
                        if semibrevis_downstem is not None:
                            if len(semibrevis_list) > 0:
                                minimaLengths_changeable[semibrevis_list[-1]] = 2.0
                                minRem_changeable -= 2.0

                            minimaLengths_changeable[semibrevis_downstem] = minRem_changeable
                        else:
                            if len(semibrevis_list) > 0 and semibrevis_list[-1] == len(self.brevisLength) - 1:
                                minimaLengths_changeable[semibrevis_list[-1]] = max(minRem_changeable, 2.0)
                                minRem_changeable -= max(minRem_changeable, 2.0)
                            else:
                                if len(semibrevis_list) > 0:
                                    minimaLengths_changeable[semibrevis_list[-1]] = 2.0
                                    minRem_changeable -= 2.0
                                    
                        tempStrength = self._evaluateBL(self.div, self.brevisLength, minimaLengths_changeable)
                        
                        if (tempStrength > strength) and (minRem_changeable > -0.0001):
                            minimaLengths = minimaLengths_changeable[:]
                            minRem = minRem_changeable
                            strength = tempStrength
                        minimaLengths_changeable = minimaLengths_static  
                        minRem_tracker = minRem_tracker or (minRem_changeable > -0.0001)   
                        minRem_changeable = minRem_static 
                        
        else:
            extend_list_1 = []
            extend_num_1 = 0
            extend_list_2 = []
            extend_num_2 = 0
            
            for ind in semibrevis_list[:-1]:
                minimaLengths[ind] = 2.0
                extend_list_1.append(ind)
                minRem -= 2.0
            
            minimaLengths_changeable = minimaLengths[:]
            minRem_changeable = minRem
            minimaLengths_static = minimaLengths[:]
            minRem_static = minRem
               
            if len(semibrevis_downstem) < 2:
                if len(semibrevis_downstem) > 0 and semibrevis_downstem[0] == len(self.brevisLength) - 1:
                    for ind in semiminima_left_flag_list + semiminima_right_flag_list + semiminima_rest_list:
                        minimaLengths[ind] = 0.5
                        minRem -= 0.5
                    if len(semibrevis_list) > 0:
                        for ind in semibrevis_list:
                            minimaLengths[ind] = 2.0
                            minRem -= 2.0
                            extend_list_1.append(ind)
                    minimaLengths[semibrevis_downstem[0]] = max(minRem, 2.0)
                    minRem -= max(minRem, 2.0)
                else:
                    if len(semiminima_left_flag_list) > 0 and len(semiminima_right_flag_list) > 0:
                        lengths = [(0.5,0.5), (float(2)/3, 0.5), (0.5, float(2)/3), (float(2)/3, float(2)/3)]
                        strength = 0
    
                        for (left_length, right_length) in lengths:
                            
                            for ind in semiminima_left_flag_list:
                                minimaLengths_changeable[ind] = left_length
                                minRem_changeable -= left_length
                            for ind in semiminima_right_flag_list:
                                minimaLengths_changeable[ind] = right_length
                                minRem_changeable -= right_length
                            
                            if left_length == right_length:
                                for ind in semiminima_rest_list:
                                    minimaLengths_changeable[ind] = left_length
                                    minRem_changeable -= left_length
                                
                                if len(semibrevis_downstem) > 0:
                                    downstem = semibrevis_downstem[0]
                                    if len(semibrevis_list) > 0:
                                        minimaLengths_changeable[semibrevis_list[-1]] = 2.0
                                        extend_list_1.append(semibrevis_list[-1])
                                        extend_list_1 = list(set(extend_list_1)) #For repeated iterations
                                        minRem_changeable -= 2.0
                                    
                                    avgSBLen = minRem_changeable/len(semibrevis_list)
                                    extend_num_1 = min(len(extend_list_1), 0.5*minRem_changeable - 2.0)
                                    minimaLengths_changeable[downstem] = max(minRem_changeable, 4.0)
                                    minRem -= max(minRem_changeable, 4.0)
                                    
                                    minimaLengths_changeable, minRem_changeable = processBL(self.brevisLength, minimaLengths_changeable, extend_list_1, extend_num_1, 2.0, minRem_changeable, releases = downstem)
                                
                                else:
                                    if len(semibrevis_list) > 0:
                                        if semibrevis_list[-1] == len(self.brevisLength) - 1:
                                            minimaLengths_changeable[semibrevis_list[-1]] = max(minRem_changeable, 2.0)
                                            extend_num_1 = min(len(extend_list_1), int(0.5*minRem_changeable - 1.0))
                                            minRem -= max(minRem_changeable, 2.0)
                                            
                                            if minRem >= 0:
                                                minimaLengths_changeable, minRem_changeable = processBL(self.brevisLength, minimaLengths_changeable, extend_list_1, extend_num_1, 2.0, minRem_changeable, releases = -1)
                                        else:
                                            minimaLengths[semibrevis_list[-1]] = 2.0
                                            extend_list_1.append(semibrevis_list[-1])
                                            extend_list_1 = list(set(extend_list_1))
                                            extend_num_1 = len(extend_list_1)
                                            minRem -= 2.0
                                            
                                            if minRem >= 0:
                                                minimaLengths_changeable, minRem_changeable = processBL(self.brevisLength, minimaLengths_changeable, extend_list_1, extend_num_1, 2.0, minRem_changeable)
                                
                            else:
                                master_list = semiminima_left_flag_list + semiminima_right_flag_list + semiminima_rest_list
                                
                                for ind in semiminima_rest_list:
                                    curIndex = int(master_list.index(ind))
                                    if ( curIndex == 0 and master_list[curIndex+1] in semiminima_left_flag_list ) or \
                                         ( curIndex == len(master_list) - 1 and master_list[curIndex - 1] in semiminima_left_flag_list ) or \
                                         ( master_list[curIndex-1] in semiminima_left_flag_list and master_list[curIndex+1] in semiminima_left_flag_list ):
                                        minimaLengths_changeable[ind] = left_length
                                        minRem_changeable -= left_length
                                    elif ( curIndex == 0 and master_list[curIndex+1] in semiminima_right_flag_list ) or \
                                         ( curIndex == len(master_list) - 1 and master_list[curIndex - 1] in semiminima_right_flag_list ) or \
                                         ( master_list[curIndex-1] in semiminima_right_flag_list and master_list[curIndex+1] in semiminima_right_flag_list ):
                                        minimaLengths_changeable[ind] = right_length
                                        minRem_changeable -= right_length
                                    else:
                                        minimaLengths_changeable[ind] = 0.5
                                        extend_list_2.append(ind)
                                    extend_list_2 = list(set(extend_list_2))
                                
                                diff_list = (2.0, float(1)/6)
                                if len(semibrevis_downstem) > 0:
                                    downstem = semibrevis_downstem[0]
                                    releases = [downstem, downstem]
                                    
                                    if len(semibrevis_list) > 0:
                                        minimaLengths_changeable[semibrevis_list[-1]] = 2.0
                                        extend_list_1.append(semibrevis_list[-1])
                                        extend_list_1 = list(set(extend_list_1))
                                        change_nums = (len(extend_list_1), len(extend_list_2))
                                        minRem_changeable -= 2.0
                                    
                                    extend_num_1 = min(len(extend_list_1), int(0.5(minRem_changeable - 2.0)))
                                    extend_num_2 = min(len(extend_list_2), 6*minRem_changeable - 12.0)
                                    minimaLengths_changeable[downstem] = max(minRem_changeable, 4.0)
                                    minRem_changeable -= 4.0
                                    change_list = (extend_list_1, extend_list_2)
                                    change_nums = (extend_num_1, extend_num_2)
                                    
                                    minimaLengths_changeable, minRem_changeable = processBL(self.brevisLength, minimaLengths_changeable, change_list, change_nums, diff_list, minRem_changeable, releases = releases, multi = 1)
                                    
                                else:
                                    if len(semibrevis_list) > 0:
                                        releases = [-1, -1]
                                        if semibrevis_list[-1] == len(self.brevisLength) - 1:
                                            minimaLengths_changeable[semibrevis_list[-1]] = max(minRem_changeable, 2.0)
                                            extend_num_1 = min(len(extend_list_1),int(0.5*minRem_changeable - 1.0))
                                            extend_num_2 = min(len(extend_list_2), 6*minRem_changeable - 12.0)
                                            minRem_changeable -= max(minRem_changeable, 2.0)
                                            change_list = (extend_list_1, extend_list_2)
                                            change_nums = (extend_num_1, extend_num_2)
                                           
                                            minimaLengths_changeable, minRem_changeable = processBL(self.brevisLength, minimaLengths_changeable, change_list, change_nums, diff_list, minRem_changeable, releases = releases, multi = 1)
                                        else:
                                            minimaLengths_changeable[semibrevis_list[-1]] = 2.0
                                            extend_list_1.append(semibrevis_list[-1])
                                            extend_list_1 = list(set(extend_list_1))
                                            change_list = (extend_list_1, extend_list_2)
                                            change_nums = (len(extend_list_1), len(extend_list_2))
                                            minRem_changeable -= 2.0
                                            
                                            minimaLengths_changeable, minRem_changeable = processBL(self.brevisLength, minimaLengths_changeable, change_list, change_nums, diff_list, minRem_changeable, multi = 1)
                                    else:
                                        extend_num_2 = len(extend_list_2)
                                        minimaLengths_changeable, minRem_changeable = processBL(self.brevisLength, minimaLengths_changeable, extend_list_2, extend_num_2, float(1)/6, minRem_changeable)
                                          
                            tempStrength = self._evaluateBL(self.div, self.brevisLength, minimaLengths_changeable)
                            
                            if tempStrength > strength and minRem_changeable > -0.0001:
                                minimaLengths = minimaLengths_changeable[:]
                                minRem = minRem_changeable
                                strength = tempStrength
                            minimaLengths_changeable = minimaLengths_static
                            minRem_tracker = minRem_tracker or (minRem_changeable > -0.0001)
                            minRem_changeable = minRem_static
                    
                    elif len(semiminima_left_flag_list) == 0 and len(semiminima_right_flag_list) == 0:
                        if len(semibrevis_downstem) > 0:
                            semibrevis_downstem = semibrevis_downstem[0]
                            if len(semibrevis_list) > 0:
                                minimaLengths[semibrevis_list[-1]] = 2.0
                                extend_list_1.append(semibrevis_list[-1])
                                minRem -= 2.0

                            extend_num_1 = min(len(extend_list_1), int(0.5*minRem - 2.0))
                            minimaLengths[semibrevis_downstem] = max(minRem, 4.0)
                            minRem -= max(minRem, 4.0)                     
                            
                            if minRem >= 0:
                                minimaLengths, minRem = processBL(self.brevisLength, minimaLengths, extend_list_1, extend_num_1, 2.0, minRem, releases = semibrevis_downstem)
                        
                        else:
                            if len(semibrevis_list) > 0:
                                if semibrevis_list[-1] == len(self.brevisLength) - 1:
                                    minimaLengths[semibrevis_list[-1]] = max(minRem, 2.0)
                                    extend_num_1 = min(len(extend_list_1), int(0.5*minRem - 1.0))
                                    minRem -= max(minRem, 2.0)
                                    
                                    if minRem >= 0:
                                        minimaLengths, minRem = processBL(self.brevisLength, minimaLengths, extend_list_1, extend_num_1, 2.0, minRem, releases = -1)
                                else:
                                    minimaLengths[semibrevis_list[-1]] = 2.0
                                    extend_list_1.append(semibrevis_list[-1])
                                    extend_num_1 = len(extend_list_1)
                                    minRem -= 2.0
                                                
                                    if minRem >= 0:
                                        minimaLengths, minRem = processBL(self.brevisLength, minimaLengths, extend_list_1, extend_num_1, 2.0, minRem)
                        minRem_tracker = minRem_tracker or (minRem > -0.0001)
                    
                    else:
                        lengths = [0.5, float(2)/3]
                        strength = 0
                        semiminima_master_list = semiminima_left_flag_list + semiminima_right_flag_list + semiminima_rest_list
                        for length in lengths:
                            for ind in semiminima_master_list:
                                minimaLengths_changeable[ind] = length
                                minRem_changeable -= length
                            
                            if len(semibrevis_downstem) > 0:
                                downstem = semibrevis_downstem[0]
                                if len(semibrevis_list) > 0:
                                    minimaLengths_changeable[semibrevis_list[-1]] = 2.0
                                    extend_list_1.append(semibrevis_list[-1])
                                    extend_list_1 = list(set(extend_list_1))
                                    minRem_changeable -= 2.0
                                
                                extend_list_1 = list(set(extend_list_1))
                                extend_num_1 = min(len(extend_list_1), int(0.5*minRem_changeable - 2.0))
                                minimaLengths_changeable[downstem] = max(minRem_changeable, 4.0)
                                minRem_changeable -= max(minRem_changeable, 4.0)
                                
                                if minRem_changeable >= 0:
                                    minimaLengths_changeable, minRem_changeable = processBL(self.brevisLength, minimaLengths_changeable, extend_list_1, extend_num_1, minRem_changeable, releases = semibrevis_downstem)
                            
                            else:
                                if len(semibrevis_list) > 0: 
                                    if semibrevis_list[-1] == len(self.brevisLength) - 1:
                                        minimaLengths_changeable[semibrevis_list[-1]] = max(minRem_changeable, 2.0)
                                        extend_num_1 = min(len(extend_list_1), int(0.5*minRem_changeable - 1.0))
                                        minRem_changeable -= max(minRem_changeable, 2.0)
                                        
                                        extend_list_1 = list(set(extend_list_1))
                                        
                                        if minRem_changeable >= 0:
                                            minimaLengths_changeable, minRem_changeable = processBL(self.brevisLength, minimaLengths_changeable, extend_list_1, extend_num_1, 2.0, minRem_changeable, releases = -1)
                                    else:
                                        minimaLengths_changeable[semibrevis_list[-1]] = 2.0
                                        extend_list_1.append(semibrevis_list[-1])
                                        extend_num_1 = len(extend_list_1)
                                        minRem_changeable -= 2.0
                                        
                                        extend_list_1 = list(set(extend_list_1))
                                        
                                        if minRem_changeable >= 0:
                                            minimaLengths_changeable, minRem_changeable = processBL(self.brevisLength, minimaLengths_changeable, extend_list_1, extend_num_1, 2.0, minRem_changeable)
                            
                            tempStrength = self._evaluateBL(self.div, self.brevisLength, minimaLengths_changeable)
                            
                            if tempStrength > strength and minRem_changeable > -0.0001:
                                minimaLengths = minimaLengths_changeable[:]
                                minRem = minRem_changeable
                                strength = tempStrength
                            minimaLengths_changeable = minimaLengths_static
                            minRem_tracker = minRem_tracker or (minRem_changeable > -0.0001)
                            minRem_changeable = minRem_static
            
            elif len(semibrevis_downstem) >= 2:
                #Don't need to lengths other SBs, not enough room
                #Hence, skip straight to semiminima 
                
                lengths = [(0.5, 0.5), (float(2)/3, 0.5), (0.5, float(2)/3), (float(2)/3, float(2)/3)]
                strength = 0
                
                for length in lengths:
                    left_length, right_length  = length
                    
                    if len(semibrevis_list) > 0:
                        minimaLengths_changeable[semibrevis_list[-1]] = 2.0
                        minRem_changeable -= 2.0
                    
                    for ind in semiminima_left_flag_list:
                        minimaLengths_changeable[ind] = left_length
                        minRem_changeable -= left_length
                    for ind in semiminima_right_flag_list:
                        minimaLengths_changeable[ind] = right_length
                        minRem_changeable -= right_length
                    
                    if left_length == right_length:
                        for ind in semiminima_rest_list:
                            minimaLengths_changeable[ind] = left_length
                            minRem_changeable -= left_length
                    else:
                        master_list = semiminima_left_flag_list + semiminima_right_flag_list + semiminima_rest_list
                            
                        for ind in semiminima_rest_list:
                            curIndex = int(master_list.index(ind))
                            if ( curIndex == 0 and master_list[curIndex+1] in semiminima_left_flag_list ) or \
                                 ( curIndex == len(master_list) - 1 and master_list[curIndex - 1] in semiminima_left_flag_list ) or \
                                 ( master_list[curIndex-1] in semiminima_left_flag_list and master_list[curIndex+1] in semiminima_left_flag_list ):
                                minimaLengths_changeable[ind] = left_length
                                minRem_changeable -= left_length
                            elif ( curIndex == 0 and master_list[curIndex+1] in semiminima_right_flag_list ) or \
                                 ( curIndex == len(master_list) - 1 and master_list[curIndex - 1] in semiminima_right_flag_list ) or \
                                 ( master_list[curIndex-1] in semiminima_right_flag_list and master_list[curIndex+1] in semiminima_right_flag_list ):
                                minimaLengths_changeable[ind] = right_length
                                minRem_changeable -= right_length
                            else:
                                minimaLengths_changeable[ind] = 0.5
                                extend_list_2.append(ind)
                            
                            extend_num_2 = len(extend_list_2)
                            minimaLengths_changeable, minRem_changeable = minimaLengths_changeable, minRem_changeable = processBL(self.brevisLength, minimaLengths_changeable, extend_list_2, extend_num_2, float(1)/6, minRem_changeable)
                    
                    newMensuralBL = [medren.MensuralNote('A', 'SB') for i in range(len(semibrevis_downstem))]
                    
                    newDiv = Divisione('.d.')
                    newDiv.minimaPerBrevis = minRem_changeable
                        
                    tempTBL = TranslateBrevisLength(divisione = newDiv, BL = newMensuralBL, pDS = True)
                    for i in range(len(semibrevis_downstem)):
                        minimaLengths_changeable[semibrevis_downstem[i]] = max(tempTBL.getMinimaLengths()[i], 4.0)
                        minRem_changeable -= max(tempTBL.getMinimaLengths()[i], 4.0)
                    
                    tempStrength = self._evaluateBL(self.div, self.brevisLength, minimaLengths_changeable)
                    
                    if tempStrength > strength and minRem_changeable > -0.0001:
                        minimaLengths = minimaLengths_changeable[:]
                        minRem = minRem_changeable
                        strength = tempStrength
                    minimaLengths_changeable = minimaLengths_static[:]
                    minRem_tracker = minRem_tracker or (minRem_changeable > -0.0001)
                    minRem_changeable = minRem_static
                    
        
        if not minRem_tracker:
            self.doubleNum += 1
            newDiv = Divisione(self.div.standardSymbol)
            newDiv.minimaPerBrevis = 2*self.div.minimaPerBrevis
            tempTBL = TranslateBrevisLength(newDiv, self.brevisLength)
            minimaLengths = tempTBL.getMinimaLengths()
            
        for i in range(len(minimaLengths)): #Float errors
            ml = minimaLengths[i]
            if abs(ml - round(ml)) < 0.0001:
                minimaLengths[i] = round(ml)
        
        return minimaLengths

class TrecentoNotationException(exceptions21.Music21Exception):
    pass

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def testTinyTrecentoStream():
    from music21 import trecento, duration, meter, stream, note, medren
    from music21 import text, metadata, tinyNotation
    import copy
     
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
    lowerString = ".p. $C3 c(L) G(B) A(SB) B c p d c r p A B c p d c B p <A*o*[DL] G> A c B A(L) A(SB) A p  G A B p c c(M) B(SB) A(M) p G(SB) G p A B c p d A r p G[D] A p B B(M) c(SB) c(M) p d(SB) d(M) A(SB) A(M) p G(SB) A B C(L) c(SB)[D] c e(B) d c(SB) c d p e d r p c c(M) d(SB) d(M) p c(SB) r r p c d c(M) d e(L) d(SB)[D] e p c[D] d p e e(M) d(SB) c(M) p B(SB) A B(M) c p d(SB) d(M) c(SB) d(M) p e(SB) d r p c c c(M) A(SB) B(M) p c(SB) B B p A B[D] p A B c d(Mx)"
    
    TinySePerDureca.append(trecento.notation.TinyTrecentoNotationStream(upperString))
    TinySePerDureca.append(trecento.notation.TinyTrecentoNotationStream(lowerString))
    
    print '''Length comparison
    normal: %s
    tiny: %s
    ''' % (len(SePerDureca.recurse()), len(TinySePerDureca.recurse()))  
    
    for i in range(2):
        for j in range(len(SePerDureca[i+1])):
            if j < len(TinySePerDureca[i+1]):
                print 'norm: %s' % SePerDureca[i+1][j]
                print 'tiny: %s' % TinySePerDureca[i+1][j]
                print ''
            else:
                print 'norm only: %s' % SePerDureca[i+1][j]
                print ''
    
class Test(unittest.TestCase):
    
    def runTest(self):
        pass

if __name__ == '__main__':
    import music21
    music21.mainTest(Test)