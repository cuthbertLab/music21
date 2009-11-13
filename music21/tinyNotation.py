#!/usr/bin/python

'''tinyNotation -- a simple way of specifying single line melodies
that uses a notation somewhat similar to Lilypond but with WAY fewer 
examples.  Originally developed to notate trecento (medieval Italian)
music, but it's pretty useful for a lot of short examples.  

tinyNotation is not meant to expand to cover every single case.  I
might expand it to add specific ids to notes so they can be found easier
to do complex things to.

Trecento specific examples have migrated into the trecento directory
'''

import music21
import music21.note
import music21.duration

from re import compile, search, match
import collections
from music21 import common
from music21 import stream
from music21 import notationMod
from music21 import meter

import unittest, doctest

class TinyNotationLine(object):
    '''A TinyNotationLine begins as a string representation similar to Lilypond format
    but simplified somewhat.  This object holds the string representation and converts
    it to music21 format as best it can
    
    example in 3/4:
    e4 r f# g trip{b-8 a g} c' 
    '''

    TRIP    = compile('trip\{')
    QUAD    = compile('quad\{')
    ENDBRAC = compile('\}')
    
    def __init__(self, stringRep = "", timeSignature = None):
        self.stringRep = stringRep
        noteStrs = self.stringRep.split()

        if (timeSignature is None):
            barDuration = music21.duration.Duration()
            barDuration.type = "whole"    ## assume 4/4
        elif (hasattr(timeSignature, "barDuration")): # is a TimeSignature object
            barDuration = timeSignature.barDuration
        else: # is a string
            tempTs = meter.TimeSignature(timeSignature)
            barDuration = tempTs.barDuration

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
                    raise TinyNotationException("unexpected end bracket in cadence")

            dict1['beginTuplet'] = False

        self.stream = stream.Stream()
        if timeSignature is not None and hasattr(timeSignature, "barDuration"):
            self.stream.append(timeSignature)
        for thisNote in noteList:
            self.stream.addNext(thisNote)
        
    def getNote(self, stringRep, storedDict = {}):
        try:
            tcN = TinyNotationNote(stringRep, storedDict)
            return tcN
        except TinyNotationException, inst:
            raise TinyNotationException(inst.args[0] + "\nLarger context: " + self.stringRep)

class TinyNotationNote(object):
    ''' tcN = TinyNotationNote("AA-4.~")
    note1 = tcN.note
    note1.name # A-
    '''
    
    REST    = compile('r')
    OCTAVE2 = compile('([A-G])[A-G]')
    OCTAVE3 = compile('([A-G])')
    OCTAVE5 = compile('([a-g])\'') 
    OCTAVE4 = compile('([a-g])')
    EDSHARP = compile('\(\#\)')
    EDFLAT  = compile('\(\-\)')
    EDNAT   = compile('\(n\)')
    SHARP   = compile('\#')  # simple notation has 
    FLAT    = compile('\-')  # no need for double sharps etc
    TYPE    = compile('(\d+)')
    TIE     = compile('.\~') # not preceding ties
    PRECTIE = compile('\~')  # front ties
    DBLDOT  = compile('\.\.') 
    DOT     = compile('\.')

    debug = False

    def __init__(self, stringRep, storedDict = common.defHash(default = False)):
        noteObj = None
        storedtie = None
        
        if self.PRECTIE.match(stringRep):
            if self.debug is True: print "FOUND FRONT TIE"
            stringRep = self.PRECTIE.sub("", stringRep)
            storedtie = music21.note.Tie("stop")

        if (self.REST.match(stringRep) is not None): # rest
            noteObj = music21.note.Rest()
        elif (self.OCTAVE2.match(stringRep)): # BB etc.
            noteObj = self._getPitch(self.OCTAVE2.match(stringRep), 2)
        elif (self.OCTAVE3.match(stringRep)):
            noteObj = self._getPitch(self.OCTAVE3.match(stringRep), 3)
        elif (self.OCTAVE5.match(stringRep)): # note match 5 then 4!
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
                newFerm = notationMod.Fermata()
                noteObj.notations.append(newFerm)
            else:
                noteObj.duration.type = music21.duration.typeFromNumDict[int(typeNum)]
        else:
            noteObj.duration = storedDict['lastDuration'].clone()
            usedLastDuration = True
            if (noteObj.duration.tuplets):
                noteObj.duration.tuplets[0].type = ""
                # if it continues a tuplet it cannot be start; maybe end

        ## get dots; called out because subclassable
        self.getDots(stringRep, noteObj)
        
        ## get ties
        if self.TIE.search(stringRep):
            if self.debug is True: print "FOUND TIE"
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
            noteObj.duration.tuplets.append(newTup)

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

        self.note = noteObj

    def getDots(self, stringRep, noteObj):
        if (self.DBLDOT.search(stringRep)):
            noteObj.duration.dots = 2
        elif (self.DOT.search(stringRep)):
            noteObj.duration.dots = 1
        
    def _getPitch(self, matchObj, octave):
        noteObj = music21.note.Note()
        noteObj.step = matchObj.group(1).upper()
        noteObj.octave = octave
        return noteObj

class TinyNotationException(Exception):
    pass

###### test routines
class Test(unittest.TestCase):

    def runTest(self):
        pass
    
    def testTinyNotationNote(self):
        cn = TinyNotationNote('AA-4.~')
        a = cn.note
        self.assertEqual(a.compactNoteInfo(), "A- A 2 flat (Tie: start) quarter 1.5")
    
    def testTinyNotationLine(self):
        tl = TinyNotationLine('e2 f#8 r f trip{g16 f e-} d8 c B trip{d16 c B}')
        st = tl.stream
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
    
class TestExternal(unittest.TestCase):    

    def testCreateEasyScale(self):
        myScale = "d8 e f g a b"
        time1 = meter.TimeSignature("3/4")
        tinyNotation = TinyNotationLine(myScale, time1)
        s1 = tinyNotation.stream
        s1.lily.showPDF()


if __name__ == "__main__":
    music21.mainTest(Test)