#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         tinyNotation.py
# Purpose:      A simply notation input format.
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    (c) 2009-2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------


'''tinyNotation -- a simple way of specifying single line melodies
that uses a notation somewhat similar to Lilypond but with WAY fewer 
options.  It was originally developed to notate trecento (medieval Italian)
music, but it is pretty useful for a lot of short examples, so we have
made it a generally supported music21 format

N.B.: TinyNotation is not meant to expand to cover every single case.  Instead
it is meant to be subclassable to extend to the cases *your* project needs.
See for instance the harmony examples in HarmonyStream and HarmonyNote
or the Trecento specific examples in trecento/cadencebook.py

Here are the most important rules:

Note names are: a,b,c,d,e,f,g and r for rest

Flats, sharps, and naturals are notated as #,- (not b), and (if needed) n.  
If the accidental is above the staff (i.e., editorial), enclose it in 
parentheses: (#), etc.  Make sure that flats in the key signatures are
explicitly specified.  

Note octaves are specified as follows:

    CC to BB = from C below bass clef to second-line B in bass clef

    C to B = from bass clef C to B below middle C.

    c  to b = from middle C to the middle of treble clef

    c' to b' = from C in treble clef to B above treble clef

After the note name, a number may be placed indicating the note 
length: 1 = whole note, 2 = half, 4 = quarter, 8 = eighth, 16 = sixteenth.  
etc.  If the number is omitted then it is assumed to be the same 
as the previous note.  I.e., c8 B c d  is a string of eighth notes.

After the number, a ~ can be placed to show a tie to the next note.  
A "." indicates a dotted note.  (If you are entering
data via Excel or other spreadsheet, be sure that "capitalize the 
first letter of sentences" is turned off under "Tools->AutoCorrect,"
otherwise the next letter will be capitalized, and the octave will
be screwed up.

For triplets use this notation:  trip{c4 d8}  indicating that these 
two notes both have "3s" over them.  For 4 in the place of 3, 
use quad{c16 d e8}.  No other tuplets are supported.

Again, see the HarmonyStream (below) and trecento.cadencebook examples
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
from music21 import expressions
from music21 import meter

class TinyNotationStream(stream.Stream):
    '''A TinyNotationStream takes in a string representation similar to Lilypond format
    but simplified somewhat and an optional time signature string (or TimeSignature object).
    
    example in 3/4:
    >>> stream1 = TinyNotationStream("E4 r f# g=lastG trip{b-8 a g} c", "3/4")
    >>> stream1.getElementById("lastG").step
    'G'
    >>> stream1.notes[1].isRest
    True
    >>> stream1.notes[0].octave
    3    
    '''

    TRIP    = compile('trip\{')
    QUAD    = compile('quad\{')
    ENDBRAC = compile('\}')
    
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
        dict1 = { 'inTrip': False,
                  'inQuad': False,
                  'beginTuplet': False,
                  'endTuplet': False,
                  'lastDuration': None, 
                  'barDuration': barDuration }

        for thisNoteStr in noteStrs:
            if self.TRIP.match(thisNoteStr):
                thisNoteStr = self.TRIP.sub('', thisNoteStr)
                dict1['inTrip'] = True
                dict1['beginTuplet'] = True
            elif self.QUAD.match(thisNoteStr):
                thisNoteStr = self.QUAD.sub('', thisNoteStr)
                dict1['inQuad'] = True
                dict1['beginTuplet'] = True
            elif self.ENDBRAC.search(thisNoteStr):
                thisNoteStr = self.ENDBRAC.sub('', thisNoteStr)
                dict1['endTuplet'] = True

            tN = None
            try:
                tN = self.getNote(thisNoteStr, dict1)
            except music21.duration.DurationException, (value):
                raise music21.duration.DurationException(str(value) + " in context " + str(thisNoteStr))
#            except Exception, (value):
#                raise Exception(str(value) + "in context " + str(thisNoteStr) + ": " + str(stringRep) )
            
            noteList.append(tN.note)

            if dict1['endTuplet'] == True:
                dict1['endTuplet'] = False
                
                if dict1['inTrip'] == True:
                    dict1['inTrip'] = False
                elif dict1['inQuad'] == True:
                    dict1['inQuad'] = False
                else:
                    raise TinyNotationException("unexpected end bracket in TinyNotationStream")

            dict1['beginTuplet'] = False

        
        if timeSignature is not None and hasattr(timeSignature, "barDuration"):
            self.append(timeSignature)
        for thisNote in noteList:
            self.append(thisNote)
        
    def getNote(self, stringRep, storedDict = {}):
        '''
        called out so as to be subclassable
        '''
        return TinyNotationNote(stringRep, storedDict)

class TinyNotationNote(object):
    ''' 
    >>> tcN = TinyNotationNote("AA-4.~=aflat_hel-")
    >>> note1 = tcN.note
    >>> note1.name
    'A-'
    >>> note1.octave
    2
    >>> note1.lyric
    'hel-'
    >>> note1.id
    'aflat'
    '''
    
    REST    = compile('r')
    OCTAVE2 = compile('([A-G])[A-G]')
    OCTAVE3 = compile('([A-G])')
    OCTAVE5 = compile('([a-g])\'') 
    OCTAVE4 = compile('([a-g])')
    EDSHARP = compile('\(\#\)')
    EDFLAT  = compile('\(\-\)')
    EDNAT   = compile('\(n\)')
    SHARP   = compile('^[A-Ga-g]+\#')  # simple notation has 
    FLAT    = compile('^[A-Ga-g]+\-')  # no need for double sharps etc
    TYPE    = compile('(\d+)')
    TIE     = compile('.\~') # not preceding ties
    PRECTIE = compile('\~')  # front ties
    DBLDOT  = compile('\.\.') 
    DOT     = compile('\.')
    ID_EL   = compile('\=([A-Za-z0-9]*)')
    LYRIC   = compile('\_(.*)')


    def __init__(self, stringRep, storedDict = common.defHash(default = False)):
        noteObj = None
        storedtie = None
        self.debug = False
        
        if self.PRECTIE.match(stringRep):
            if self.debug is True: print("FOUND FRONT TIE")
            stringRep = self.PRECTIE.sub("", stringRep)
            storedtie = music21.note.Tie("stop")

        x = self.customPitchMatch(stringRep, storedDict)
        
        if x is not None:
            noteObj = x
        elif (self.REST.match(stringRep) is not None): # rest
            noteObj = music21.note.Rest()
        elif (self.OCTAVE2.match(stringRep)): # BB etc.
            noteObj = self._getPitch(self.OCTAVE2.match(stringRep), 2)
        elif (self.OCTAVE3.match(stringRep)):
            noteObj = self._getPitch(self.OCTAVE3.match(stringRep), 3)
        elif (self.OCTAVE5.match(stringRep)): # must match octave 5 then 4!
            noteObj = self._getPitch(self.OCTAVE5.match(stringRep), 5)
        elif (self.OCTAVE4.match(stringRep)): 
            noteObj = self._getPitch(self.OCTAVE4.match(stringRep), 4)
        else:
            raise TinyNotationException("could not get pitch information from " + str(stringRep))

        if storedtie: noteObj.tie = storedtie

        ## get duration
        usedLastDuration = False
        
        if (self.TYPE.search(stringRep)):
            typeNum = self.TYPE.search(stringRep).group(1)
            if (typeNum == "0"): ## special case = full measure + fermata
                noteObj.duration = storedDict['barDuration']
                newFerm = expressions.Fermata()
                noteObj.notations.append(newFerm)
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
            if self.debug is True: print("FOUND TIE")
            noteObj.tie = music21.note.Tie("start")
        
        ## use dict to set tuplets
        if (storedDict['inTrip'] == True or storedDict['inQuad'] == True) and usedLastDuration == False:
            newTup = music21.duration.Tuplet()
            newTup.durationActual.type = noteObj.duration.type
            newTup.durationNormal.type = noteObj.duration.type
            if storedDict['inQuad'] == True:
                newTup.numNotesActual = 4.0
                newTup.numNotesNormal = 3.0            
            if storedDict['beginTuplet']:
                newTup.type = "start"
            noteObj.duration.appendTuplet(newTup)

        if (storedDict['inTrip'] == True and storedDict['endTuplet']):
            noteObj.duration.tuplets[0].type = "stop"
        if (storedDict['inQuad'] == True and storedDict['endTuplet']):
            noteObj.duration.tuplets[0].type = "stop"
        
        storedDict['lastDuration'] = noteObj.duration

        ## get accidentals
        if (isinstance(noteObj, music21.note.Note)):
            if (self.EDSHARP.search(stringRep)): # must come before sharp
                acc1 = music21.note.Accidental("sharp")
                noteObj.editorial.ficta = acc1
                noteObj.editorial.misc['pmfc-ficta'] = acc1
            elif (self.EDFLAT.search(stringRep)): # must come before flat
                acc1 = music21.note.Accidental("flat")
                noteObj.editorial.ficta = acc1
                noteObj.editorial.misc['pmfc-ficta'] = acc1
            elif (self.EDNAT.search(stringRep)):
                acc1 = music21.note.Accidental("natural")
                noteObj.editorial.ficta = acc1
                noteObj.editorial.misc['pmfc-ficta'] = acc1
                noteObj.accidental = acc1
            elif (self.SHARP.search(stringRep)):
                noteObj.accidental = "sharp"
            elif (self.FLAT.search(stringRep)):
                noteObj.accidental = "flat"

        self.customNotationMatch(noteObj, stringRep, storedDict)

        if self.ID_EL.search(stringRep):
            noteObj.id = self.ID_EL.search(stringRep).group(1)
        
        if self.LYRIC.search(stringRep):
            noteObj.lyric = self.LYRIC.search(stringRep).group(1)
            
        self.note = noteObj

    def getDots(self, stringRep, noteObj):
        '''
        subclassable method to set the dots attributes of 
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
    example of subclassing TinyNotationStream to include a possible harmonic representation of the note

    >>> michelle = "c2*F*_Mi- c_chelle r4*B-m7* d-_ma A-2_belle "
    >>> michelle += "G4*E-*_these c_are A-_words G_that "
    >>> michelle += "F*Ddim*_go A-_to- Bn_geth- A-_er"
    
    >>> hns = HarmonyStream(michelle, "4/4")
    >>> ns = hns.notes
    >>> ns[0].step
    'C'
    >>> ns[0].editorial.misc['harmony']
    'F'
    >>> ns[0].lyric
    'Mi-'
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
        nst1 = hns.notes
        self.assertEqual(nst1[0].step, "C")
        self.assertEqual(nst1[0].editorial.misc['harmony'], "F")
        self.assertEqual(nst1[0].lyric, "Mi-")
        self.assertEqual(nst1[2].isRest, True)
        self.assertEqual(nst1[5].name, "G")
        self.assertEqual(nst1[7].name, "A-")

class TestExternal(unittest.TestCase):    

    def xtestCreateEasyScale(self):
        myScale = "d8 e f g a b"
        time1 = meter.TimeSignature("3/4")
        tinyNotation = TinyNotationStream(myScale, time1)
        tinyNotation.lily.showPDF()
    
    def testMusicXMLExt(self):
        cadB = TinyNotationStream("c8 B- B- A c trip{d16 c B-} A8 B- A0", "2/4")
#        last = cadB[10]
#        cadB = stream.Stream()
#        n1 = music21.note.Note()
#        n1.duration.type = "whole"
#        cadB.append(n1)
#        cadB.lily.showPDF()
        cadB.show()



#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [TinyNotationNote, TinyNotationStream, HarmonyStream, HarmonyNote]

if __name__ == "__main__":
    music21.mainTest(TestExternal, Test)