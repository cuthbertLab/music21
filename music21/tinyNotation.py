# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         tinyNotation.py
# Purpose:      A simple notation input format.
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    (c) 2009-2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------


'''
tinyNotation is a simple way of specifying single line melodies
that uses a notation somewhat similar to Lilypond but with WAY fewer 
options.  It was originally developed to notate trecento (medieval Italian)
music, but it is pretty useful for a lot of short examples, so we have
made it a generally supported music21 format


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
'''

import unittest, doctest
import copy
from re import compile, search, match
import collections

import music21
import music21.note
import music21.duration

from music21 import common
from music21 import stream
from music21 import tie
from music21 import expressions
from music21 import meter
from music21 import pitch


class TinyNotationStream(stream.Stream):
    '''
    A TinyNotationStream takes in a string representation 
    similar to Lilypond format
    but simplified somewhat and an optional time signature 
    string (or TimeSignature object).
    
    
    Example in 3/4:
    
    >>> from music21 import *
    >>> stream1 = tinyNotation.TinyNotationStream("3/4 E4 r f# g=lastG trip{b-8 a g} c4~ c")
    >>> stream1.show('text')
    {0.0} <music21.meter.TimeSignature 3/4>
    {0.0} <music21.note.Note E>
    {1.0} <music21.note.Rest rest>
    {2.0} <music21.note.Note F#>
    {3.0} <music21.note.Note G>
    {4.0} <music21.note.Note B->
    {4.33333333333} <music21.note.Note A>
    {4.66666666667} <music21.note.Note G>
    {5.0} <music21.note.Note C>
    {6.0} <music21.note.Note C>

    >>> stream1.getElementById("lastG").step
    'G'
    >>> stream1.notesAndRests[1].isRest
    True
    >>> stream1.notesAndRests[0].octave
    3    
    >>> stream1.notes[-2].tie.type
    'start'
    >>> stream1.notes[-1].tie.type
    'stop'
    '''

    TRIP    = compile('trip\{')
    QUAD    = compile('quad\{')
    ENDBRAC = compile('\}')
    TIMESIG = compile('(\d+\/\d+)')
    
    def __init__(self, stringRep = "", timeSignature = None):
        stream.Stream.__init__(self)
        self.stringRep = stringRep
        noteStrs = self.stringRep.split()

        if (timeSignature is None):
            barDuration = music21.duration.Duration()
            barDuration.type = "whole"    ## assume 4/4
        elif (hasattr(timeSignature, "barDuration")): # is a TimeSignature object
            barDuration = timeSignature.barDuration
        else: # is a string
            timeSignature = meter.TimeSignature(timeSignature)
            barDuration = timeSignature.barDuration

        noteList = []
        if timeSignature is not None and hasattr(timeSignature, "barDuration"):
            noteList.append(timeSignature)

        
        parseStatus = { 
                        'inTrip': False,
                        'inQuad': False,
                        'beginTuplet': False,
                        'endTuplet': False,
                        'lastDuration': None, 
                        'barDuration': barDuration,
                        'lastNoteTied': False, }

        for thisNoteStr in noteStrs:
            if self.TRIP.match(thisNoteStr):
                thisNoteStr = self.TRIP.sub('', thisNoteStr)
                parseStatus['inTrip'] = True
                parseStatus['beginTuplet'] = True
            elif self.QUAD.match(thisNoteStr):
                thisNoteStr = self.QUAD.sub('', thisNoteStr)
                parseStatus['inQuad'] = True
                parseStatus['beginTuplet'] = True
            elif self.ENDBRAC.search(thisNoteStr):
                thisNoteStr = self.ENDBRAC.sub('', thisNoteStr)
                parseStatus['endTuplet'] = True
            elif self.TIMESIG.match(thisNoteStr):
                newTime = self.TIMESIG.match(stringRep).group(1)
                timeSignature = meter.TimeSignature(newTime)
                barDuration = timeSignature.barDuration
                parseStatus['barDuration'] = barDuration
                noteList.append(timeSignature)
                continue
                    

            tN = None
            try:
                tN = self.getNote(thisNoteStr, parseStatus)
            except music21.duration.DurationException, (value):
                raise music21.duration.DurationException(str(value) + " in context " + str(thisNoteStr))
#            except Exception, (value):
#                raise Exception(str(value) + "in context " + str(thisNoteStr) + ": " + str(stringRep) )
            
            noteList.append(tN.note)

            if parseStatus['endTuplet'] == True:
                parseStatus['endTuplet'] = False
                
                if parseStatus['inTrip'] == True:
                    parseStatus['inTrip'] = False
                elif parseStatus['inQuad'] == True:
                    parseStatus['inQuad'] = False
                else:
                    raise TinyNotationException("unexpected end bracket in TinyNotationStream")

            parseStatus['beginTuplet'] = False

        
        for thisNote in noteList:
            self.append(thisNote)
                
        
    def getNote(self, stringRep, storedDict = common.DefaultHash()):
        '''
        called out so as to be subclassable, returns a 
        :class:`~music21.tinyNotation.TinyNotationNote` object
        '''
        return TinyNotationNote(stringRep, storedDict)


class TinyNotationNote(object):
    ''' 
    Class defining a single note in TinyNotation.  The "note" attribute
    returns a :class:`~music21.note.Note` object.


    See docs for :class:`~music21.tinyNotation.TinyNotationStream` for
    usage.
    

    Simple example:


    >>> from music21 import *
    >>> tnN = tinyNotation.TinyNotationNote("c8")
    >>> m21Note = tnN.note
    >>> m21Note
    <music21.note.Note C>
    >>> m21Note.octave
    4
    >>> m21Note.duration
    <music21.duration.Duration 0.5>
    
    
    Very complex example:


    >>> tnN = tinyNotation.TinyNotationNote("AA-4.~=aflat_hel-")
    >>> m21Note = tnN.note
    >>> m21Note.name
    'A-'
    >>> m21Note.octave
    2
    >>> m21Note.lyric
    'hel'
    >>> m21Note.id
    'aflat'



    The optional third element is a dictionary of stored information
    from previous notes that might affect parsing of this note:
    
    
    >>> storedDict = {}
    >>> storedDict['lastNoteTied'] = True
    >>> storedDict['inTrip'] = True
    >>> tnN = tinyNotation.TinyNotationNote("d''#4", storedDict)
    >>> tnN.note.tie
    <music21.tie.Tie stop>
    >>> tnN.note.duration.quarterLength
    0.6666666...


    OMIT_FROM_DOCS

    
    >>> tcn2 = tinyNotation.TinyNotationNote("c''##16").note
    >>> tcn2.accidental
    <accidental double-sharp>
    >>> tcn2.octave
    6
    >>> tcn2.quarterLength
    0.25


    >>> tcn3 = tinyNotation.TinyNotationNote("d''(---)16").note
    >>> tcn3.editorial.ficta
    <accidental triple-flat>
    
    
    Test instantiating without any parameters:
    
    
    >>> tcn4 = tinyNotation.TinyNotationNote()
    
    '''
    
    REST    = compile('r')
    OCTAVE2 = compile('([A-G])+[A-G]')
    OCTAVE3 = compile('([A-G])')
    OCTAVE5 = compile('([a-g])(\'+)') 
    OCTAVE4 = compile('([a-g])')
    EDSHARP = compile('\((\#+)\)')
    EDFLAT  = compile('\((\-+)\)')
    EDNAT   = compile('\(n\)')
    SHARP   = compile('^[A-Ga-g]+\'*(\#+)')  # simple notation finds 
    FLAT    = compile('^[A-Ga-g]+\'*(\-+)')  # double sharps too
    TYPE    = compile('(\d+)')
    TIE     = compile('.\~') # not preceding ties
    PRECTIE = compile('\~')  # front ties
    DBLDOT  = compile('\.\.') 
    DOT     = compile('\.')
    ID_EL   = compile('\=([A-Za-z0-9]*)')
    LYRIC   = compile('\_(.*)')


    def __init__(self, stringRep = None, storedDict = common.DefaultHash(default = False)):
        self.debug = False
        self.stringRep = stringRep
        self.storedDict = storedDict
        self._note = None
        
    def _getNote(self):
        if self._note is not None:
            return self._note
        noteObj = None
        storedtie = None

        stringRep = self.stringRep
        storedDict = self.storedDict
        
        if stringRep is None:
            raise TinyNotationException('Cannot return a note without some parameters')
        
        
        if self.PRECTIE.match(stringRep):
            if self.debug is True: print("FOUND FRONT TIE")
            stringRep = self.PRECTIE.sub("", stringRep)
            storedtie = music21.tie.Tie("stop")
            storedDict['lastNoteTied'] = False

        elif 'lastNoteTied' in storedDict and storedDict['lastNoteTied'] is True:
            storedtie = music21.tie.Tie("stop")
            storedDict['lastNoteTied'] = False

        x = self.customPitchMatch(stringRep, storedDict)
        
        if x is not None:
            noteObj = x
        elif (self.REST.match(stringRep) is not None): # rest
            noteObj = music21.note.Rest()
        elif (self.OCTAVE2.match(stringRep)): # BB etc.
            nn = self.OCTAVE2.match(stringRep)
            noteObj = self._getPitch(nn, 3 - len(nn.group(1)))
        elif (self.OCTAVE3.match(stringRep)):
            noteObj = self._getPitch(self.OCTAVE3.match(stringRep), 3)
        elif (self.OCTAVE5.match(stringRep)): # must match octave 5 then 4!
            nn = self.OCTAVE5.match(stringRep)
            noteObj = self._getPitch(nn, 4 + len(nn.group(2)))
        elif (self.OCTAVE4.match(stringRep)): 
            noteObj = self._getPitch(self.OCTAVE4.match(stringRep), 4)
        else:
            raise TinyNotationException("could not get pitch information from " + str(stringRep))

        if storedtie: 
            noteObj.tie = storedtie

        ## get duration
        usedLastDuration = False
        
        if (self.TYPE.search(stringRep)):
            typeNum = self.TYPE.search(stringRep).group(1)
            if (typeNum == "0"): ## special case = full measure + fermata
                noteObj.duration = storedDict['barDuration']
                newFerm = expressions.Fermata()
                noteObj.expressions.append(newFerm)
            else:
                noteObj.duration.type = music21.duration.typeFromNumDict[int(typeNum)]
        else:
            noteObj.duration = copy.deepcopy(storedDict['lastDuration'])
            usedLastDuration = True
            if (noteObj.duration.tuplets):
                noteObj.duration.tuplets[0].type = ""
                # if it continues a tuplet it cannot be start; maybe end

        ## get dots; called out because subclassable
        self.getDots(stringRep, noteObj)
        
        ## get ties
        if self.TIE.search(stringRep):
            if self.debug is True: 
                print("FOUND TIE")
            storedDict['lastNoteTied'] = True
            if noteObj.tie is None:
                noteObj.tie = music21.tie.Tie("start")
            else:
                noteObj.tie.type = 'continue'
        
        ## use dict to set tuplets
        if ((('inTrip' in storedDict and storedDict['inTrip'] == True) or 
             ('inQuad' in storedDict and storedDict['inQuad'] == True)) and usedLastDuration == False):
            newTup = music21.duration.Tuplet()
            newTup.durationActual.type = noteObj.duration.type
            newTup.durationNormal.type = noteObj.duration.type
            if 'inQuad' in storedDict and storedDict['inQuad'] == True:
                newTup.numNotesActual = 4.0
                newTup.numNotesNormal = 3.0            
            if 'beginTuplet' in storedDict and storedDict['beginTuplet'] == True:
                newTup.type = "start"
            noteObj.duration.appendTuplet(newTup)

        if ((('inTrip' in storedDict and storedDict['inTrip'] == True) or
             ('inQuad' in storedDict and storedDict['inQuad'] == True)) and 
             ('endTuplet' in storedDict and storedDict['endTuplet'] == True)):
            noteObj.duration.tuplets[0].type = "stop"
        
        storedDict['lastDuration'] = noteObj.duration

        ## get accidentals
        if (isinstance(noteObj, music21.note.Note)):
            if (self.EDSHARP.search(stringRep)): # must come before sharp
                alter = len(self.EDSHARP.search(stringRep).group(1))
                acc1 = pitch.Accidental(alter)
                noteObj.editorial.ficta = acc1
                noteObj.editorial.misc['pmfc-ficta'] = acc1
            elif (self.EDFLAT.search(stringRep)): # must come before flat
                alter = -1 * len(self.EDFLAT.search(stringRep).group(1))
                acc1 = pitch.Accidental(alter)
                noteObj.editorial.ficta = acc1
                noteObj.editorial.misc['pmfc-ficta'] = acc1
            elif (self.EDNAT.search(stringRep)):
                acc1 = pitch.Accidental("natural")
                noteObj.editorial.ficta = acc1
                noteObj.editorial.misc['pmfc-ficta'] = acc1
                noteObj.accidental = acc1
            elif (self.SHARP.search(stringRep)):
                alter = len(self.SHARP.search(stringRep).group(1))
                noteObj.accidental = pitch.Accidental(alter)
            elif (self.FLAT.search(stringRep)):
                alter = -1 * len(self.FLAT.search(stringRep).group(1))
                noteObj.accidental = pitch.Accidental(alter)

        self.customNotationMatch(noteObj, stringRep, storedDict)

        if self.ID_EL.search(stringRep):
            noteObj.id = self.ID_EL.search(stringRep).group(1)
        
        if self.LYRIC.search(stringRep):
            noteObj.lyric = self.LYRIC.search(stringRep).group(1)
            
        self._note = noteObj
        return self._note
    
    note = property(_getNote)

    def getDots(self, stringRep, noteObj):
        '''
        Subclassable method to set the dots attributes of 
        the duration object.
        
        It is subclassed in music21.trecento.cadencebook.TrecentoNote
        where double dots are redefined as referring to multiply by
        2.25 (according to a practice used by some Medieval musicologists).
        '''
        
        if (self.DBLDOT.search(stringRep)):
            noteObj.duration.dots = 2
        elif (self.DOT.search(stringRep)):
            noteObj.duration.dots = 1
        
    def _getPitch(self, matchObj, octave):
        noteObj = music21.note.Note()
        noteObj.step = matchObj.group(1).upper()
        noteObj.octave = octave
        return noteObj

    def customPitchMatch(self, stringRep, storedDict):
        '''
        method to create a note object in sub classes of tiny notation.  
        Should return a Note-like object or None
        '''
        return None

    def customNotationMatch(self, m21NoteObject, stringRep, storedDict):
        return None

class HarmonyStream(TinyNotationStream):
    '''
    HarmonyStream provides an
    example of subclassing :class:`~music21.tinyNotation.TinyNotationStream`
    to include harmonies and lyrics encoded in a simple format.
    
    >>> from music21 import *

    >>> michelle = "c2*F*_Mi- c_chelle r4*B-m7* d-_ma A-2_belle "
    >>> michelle += "G4*E-*_these c_are A-_words G_that "
    >>> michelle += "F*Ddim*_go A-_to- Bn_geth- A-_er"
    
    >>> hns = tinyNotation.HarmonyStream(michelle, "4/4")
    >>> ns = hns.notesAndRests
    >>> ns[0].step
    'C'
    >>> ns[0].editorial.misc['harmony']
    'F'
    >>> ns[0].lyric # note that hyphens are removed
    'Mi'
    >>> ns[2].isRest
    True
    >>> ns[5].name
    'G'
    >>> ns[7].name
    'A-'

    '''
    def getNote(self, stringRep, storedDict = {}):
        return HarmonyNote(stringRep, storedDict)

class HarmonyNote(TinyNotationNote):
    HARMONY   = compile('\*(.*)\*')
    
    def customNotationMatch(self, m21NoteObject, stringRep, storedDict):
        '''
        checks to see if a note has markup in the form *TEXT* and if
        so, stores TEXT in the notes editorial.misc[] dictionary object
        
        See the demonstration in the docs for class HarmonyLine.
        '''
        if self.HARMONY.search(stringRep):
            harmony = self.HARMONY.search(stringRep).group(1)
            m21NoteObject.editorial.misc['harmony'] = harmony


class TinyNotationException(Exception):
    pass



#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass
    
    def testTinyNotationNote(self):
        cn = TinyNotationNote('AA-4.~')
        a = cn.note
        self.assertEqual(a.compactNoteInfo(), "A- A 2 flat (Tie: start) quarter 1.5")
    
    def testTinyNotationStream(self):
        st = TinyNotationStream('e2 f#8 r f trip{g16 f e-} d8 c B trip{d16 c B}')
        ret = ""
        for thisNote in st:
            ret += thisNote.compactNoteInfo() + "\n"
        
        d1 = st.duration
        l1 = d1.quarterLength
        self.assertAlmostEquals(st.duration.quarterLength, 6.0)
        
        ret += "Total duration of Stream: " + str(st.duration.quarterLength) + "\n"
        canonical = '''
E E 4 half 2.0
F# F 4 sharp eighth 0.5
rest eighth 0.5
F F 4 eighth 0.5
G G 4 16th 0.166666666667 & is a tuplet (in fact STARTS the tuplet)
F F 4 16th 0.166666666667 & is a tuplet
E- E 4 flat 16th 0.166666666667 & is a tuplet (in fact STOPS the tuplet)
D D 4 eighth 0.5
C C 4 eighth 0.5
B B 3 eighth 0.5
D D 4 16th 0.166666666667 & is a tuplet (in fact STARTS the tuplet)
C C 4 16th 0.166666666667 & is a tuplet
B B 3 16th 0.166666666667 & is a tuplet (in fact STOPS the tuplet)
Total duration of Stream: 6.0
'''
        self.assertTrue(common.basicallyEqual(canonical, ret))
    
    def testConvert(self):
        st1 = TinyNotationStream('e2 f#8 r f trip{g16 f e-} d8 c B trip{d16 c B}')
        self.assertEqual(st1[1].offset, 2.0) 
        self.assertTrue(isinstance(st1[2], music21.note.Rest))     

    def testHarmonyNotation(self):
        hns = HarmonyStream("c2*F*_Mi- c_chelle r4*B-m7* d-_ma A-2_belle G4*E-*_these c_are A-_words G_that F*Ddim*_go A-_to- Bn_geth- A-_er", "4/4")
        nst1 = hns.notesAndRests
        self.assertEqual(nst1[0].step, "C")
        self.assertEqual(nst1[0].editorial.misc['harmony'], "F")
        self.assertEqual(nst1[0].lyric, "Mi")
        self.assertEqual(nst1[2].isRest, True)
        self.assertEqual(nst1[5].name, "G")
        self.assertEqual(nst1[7].name, "A-")

class TestExternal(unittest.TestCase):    

    def xtestCreateEasyScale(self):
        myScale = "d8 e f g a b"
        time1 = meter.TimeSignature("3/4")
        tinyNotation = TinyNotationStream(myScale, time1)
        tinyNotation.show('lily.pdf')
    
    def testMusicXMLExt(self):
        cadB = TinyNotationStream("c8 B- B- A c trip{d16 c B-} A8 B- A0", "2/4")
#        last = cadB[10]
#        cadB = stream.Stream()
#        n1 = music21.note.Note()
#        n1.duration.type = "whole"
#        cadB.append(n1)
#        cadB.show('lily.pdf')
        cadB.show()



#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [TinyNotationNote, TinyNotationStream, HarmonyStream, HarmonyNote]

if __name__ == "__main__":
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof

