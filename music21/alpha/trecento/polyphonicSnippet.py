# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         trecento/polyphonicSnippet.py
# Purpose:      subclasses for the trecento cadences from a MS Excel spreadsheet
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2009, 2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------

import copy
import unittest

from music21 import metadata
from music21 import meter
from music21 import note
from music21 import stream


class PolyphonicSnippet(stream.Score):
    '''
    A polyphonic snippet is a little Score-ette that represents an incipit or a 
    cadence or something of that sort of a piece
    
    It is initialized with the contents of five excel cells -- the first three 
    represent the notation of the cantus, tenor, and contratenor, respectively.  
    
    The fourth is the cadence type (optional), the fifth is the time signature 
    if not the same as the time signature of the parentPiece.
    
    >>> cantus = alpha.trecento.trecentoCadence.CadenceConverter("6/8 c'2. d'8 c'4 a8 f4 f8 a4 c'4 c'8").parse().stream
    >>> tenor = alpha.trecento.trecentoCadence.CadenceConverter("6/8 F1. f2. e4. d").parse().stream
    >>> ps = alpha.trecento.polyphonicSnippet.PolyphonicSnippet([cantus, tenor, None, "8-8", "6/8"], parentPiece = alpha.trecento.cadencebook.BallataSheet().makeWork(3))
    >>> ps.elements
    (<music21.metadata.Metadata object at 0x...>, <music21.stream.Part C>, <music21.stream.Part T>)

    >>> ps.parts[0] is cantus
    True

    >>> #_DOCS_SHOW ps.show()
        
    .. image:: images/trecento-polyphonicSnippet1.*
            :width: 450

    OMIT_FROM_DOCS
    
    >>> dummy = alpha.trecento.polyphonicSnippet.PolyphonicSnippet()
    >>> dummy.elements
    ()

    >>> dumClass = dummy.__class__
    >>> dumClass
    <class 'music21.alpha.trecento.polyphonicSnippet.PolyphonicSnippet'>

    >>> dumdum = dumClass()
    >>> dumdum.__class__
    <class 'music21.alpha.trecento.polyphonicSnippet.PolyphonicSnippet'>

    >>> ps2 = ps.__class__()
    >>> ps2.elements
    ()
    
    >>> dummy2 = alpha.trecento.polyphonicSnippet.Incipit()
    >>> dummy2.elements
    ()    
    '''
    snippetName = ""

    def __init__(self, fiveExcelCells = None, parentPiece = None):
        stream.Score.__init__(self)
        if fiveExcelCells == None:
            fiveExcelCells = []
        if fiveExcelCells != []:        
            if len(fiveExcelCells) != 5:
                raise Exception("Need five Excel Cells to make a PolyphonicSnippet object")
    
            for part in fiveExcelCells[0:3]:
                if part is not None and hasattr(part, 'isStream') and part.isStream == True:
                    part.__class__ = stream.Part
            
            self.cadenceType = fiveExcelCells[3]
            self.timeSig = meter.TimeSignature(fiveExcelCells[4])
            self.parentPiece = parentPiece
            self.cantus = fiveExcelCells[0]
            self.tenor  = fiveExcelCells[1]
            self.contratenor = fiveExcelCells[2]
            
            if self.contratenor == "" or self.contratenor is None: 
                self.contratenor = None
            else:
                self.contratenor.id = 'Ct'
            if self.tenor == "" or self.tenor is None: 
                self.tenor = None
            else:
                self.tenor.id = 'T'

            if self.cantus == "" or self.cantus is None: 
                self.cantus = None
            else:
                self.cantus.id = 'C'

            md = metadata.Metadata()
            md.title = self.header()
            self.insert(0, md)    
            self._appendParts()
            self._padParts()

    def _appendParts(self):
        '''
        appends each of the parts to the current score.
        '''
        foundTs = False
        for thisVoice in [self.cantus, self.contratenor, self.tenor]:        
            # thisVoice is a type of stream.Stream()
            
            if thisVoice is not None:
                if foundTs == False and len(thisVoice.getElementsByClass(meter.TimeSignature)) > 0:
                    foundTs = True
                thisVoice.makeNotation(inPlace = True)
                self.insert(0, thisVoice)
                
        self.rightBarline = 'final'


    def _padParts(self):
        for thisVoice in self.parts:        
            # thisVoice is a type of stream.Stream()
            
            if thisVoice is not None:
                if hasattr(self, 'frontPadLine'):
                    self.frontPadLine(thisVoice)
                elif hasattr(self, 'backPadLine'):
                    self.backPadLine(thisVoice)
    
    def header(self):
        '''returns a string that prints an appropriate header for this cadence'''
        if self.snippetName == "":
            if (self.parentPiece is not None):
                headOut = ""
                parentPiece = self.parentPiece
                if (parentPiece.fischerNum):
                    headOut += str(parentPiece.fischerNum) + ". " 
                if parentPiece.title:
                    headOut += parentPiece.title
                if (parentPiece.pmfcVol and parentPiece.pmfcPageRange()):
                    headOut += " PMFC " + str(parentPiece.pmfcVol) + " " + parentPiece.pmfcPageRange()
                return headOut
            else:
                return ""
        else:
            if (self.parentPiece is not None):
                headOut = self.parentPiece.title + " -- " + self.snippetName
            else:
                return self.snippetName
                    
    def findLongestCadence(self):
        '''
        returns the length. (in quarterLengths) for the longest line
        in the parts
        
        
        >>> s1 = stream.Part([note.Note(type='whole')])
        >>> s2 = stream.Part([note.Note(type='half')])
        >>> s3 = stream.Part([note.Note(type='quarter')])
        >>> fiveExcelRows = [s1, s2, s3, '', '2/2']
        >>> ps = alpha.trecento.polyphonicSnippet.PolyphonicSnippet(fiveExcelRows)
        >>> ps.findLongestCadence()
        4.0
        
        '''
        longestLineLength = 0
        for thisStream in self.parts:
            if thisStream is None:
                continue
            thisLength = thisStream.duration.quarterLength
            if thisLength > longestLineLength:
                longestLineLength = thisLength
        self.longestLineLength = longestLineLength
        return longestLineLength

    def measuresShort(self, thisStream):
        '''
        returns the number of measures short that each stream is compared to the longest stream.
        
        >>> s1 = stream.Part([note.Note(type='whole')])
        >>> s2 = stream.Part([note.Note(type='half')])
        >>> s3 = stream.Part([note.Note(type='quarter')])
        >>> fiveExcelRows = [s1, s2, s3, '', '1/2']
        >>> ps = alpha.trecento.polyphonicSnippet.PolyphonicSnippet(fiveExcelRows)
        >>> ps.findLongestCadence()
        4.0
        >>> ps.measuresShort(s2)
        1.0
        >>> ps.measuresShort(s3)
        1.5
        >>> ps.measuresShort(s1)
        0.0
        '''

        
        timeSigLength = self.timeSig.barDuration.quarterLength
        thisStreamLength = thisStream.duration.quarterLength
        shortness = self.findLongestCadence() - thisStreamLength
        shortmeasures = shortness/timeSigLength
        return shortmeasures



class Incipit(PolyphonicSnippet):
    snippetName = ""

    def backPadLine(self, thisStream):
        '''
        Pads a Stream with a bunch of rests at the
        end to make it the same length as the longest line

        
        >>> ts = meter.TimeSignature('1/4')
        >>> s1 = stream.Part([ts])
        >>> s1.repeatAppend(note.Note(type='quarter'), 4)
        >>> s2 = stream.Part([ts])
        >>> s2.repeatAppend(note.Note(type='quarter'), 2)
        >>> s3 = stream.Part([ts])
        >>> s3.repeatAppend(note.Note(type='quarter'), 1)
        >>> fiveExcelRows = [s1, s2, s3, '', '1/4']
        >>> ps = alpha.trecento.polyphonicSnippet.Incipit(fiveExcelRows)
        >>> ps.backPadLine(s2)
        >>> s2.show('text')
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.clef.TrebleClef>
            {0.0} <music21.meter.TimeSignature 1/4>
            {0.0} <music21.note.Note C>
        {1.0} <music21.stream.Measure 2 offset=1.0>
            {0.0} <music21.note.Note C>
        {2.0} <music21.stream.Measure 3 offset=2.0>
            {0.0} <music21.note.Rest rest>
        {3.0} <music21.stream.Measure 4 offset=3.0>
            {0.0} <music21.note.Rest rest>
            {1.0} <music21.bar.Barline style=final>
            
        '''
        shortMeasures = int(self.measuresShort(thisStream))

        if (shortMeasures > 0):
            shortDuration = self.timeSig.barDuration
            hasMeasures = thisStream.hasMeasures()
            if hasMeasures:
                lastMeasure = thisStream.getElementsByClass('Measure')[-1]
                maxMeasures = lastMeasure.number
                oldRightBarline = lastMeasure.rightBarline
                lastMeasure.rightBarline = None

            for i in range(0, shortMeasures):
                newRest = note.Rest()
                newRest.duration = copy.deepcopy(shortDuration)    
                newRest.transparent = 1
                if hasMeasures:
                    m = stream.Measure()
                    m.number = maxMeasures + 1 + i
                    m.append(newRest)
                    thisStream.append(m)
                else:
                    thisStream.append(newRest)
                
                if i == 0:
                    newRest.startTransparency = 1
                elif i == (shortMeasures - 1):
                    newRest.stopTransparency = 1

            if hasMeasures:
                lastMeasure = thisStream.getElementsByClass('Measure')[-1]
                lastMeasure.rightBarline = oldRightBarline



class FrontPaddedSnippet(PolyphonicSnippet):
    snippetName = ""

    def frontPadLine(self, thisStream):
        '''Pads a line with a bunch of rests at the
        front to make it the same length as the longest line
        
        
        >>> ts = meter.TimeSignature('1/4')
        >>> s1 = stream.Part([ts])
        >>> s1.repeatAppend(note.Note(type='quarter'), 4)
        >>> s2 = stream.Part([ts])
        >>> s2.repeatAppend(note.Note(type='quarter'), 2)
        >>> s3 = stream.Part([ts])
        >>> s3.repeatAppend(note.Note(type='quarter'), 1)
        >>> fiveExcelRows = [s1, s2, s3, '', '1/4']
        >>> ps = alpha.trecento.polyphonicSnippet.FrontPaddedSnippet(fiveExcelRows)
        >>> ps.frontPadLine(s2)
        >>> s2.show('text')
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.clef.TrebleClef>
            {0.0} <music21.meter.TimeSignature 1/4>
            {0.0} <music21.note.Rest rest>
        {1.0} <music21.stream.Measure 2 offset=1.0>
            {0.0} <music21.note.Rest rest>
        {2.0} <music21.stream.Measure 3 offset=2.0>
            {0.0} <music21.note.Note C>
        {3.0} <music21.stream.Measure 4 offset=3.0>
            {0.0} <music21.note.Note C>
            {1.0} <music21.bar.Barline style=final>
            
        '''
        shortMeasures = int(self.measuresShort(thisStream))

        if (shortMeasures > 0):
            shortDuration = self.timeSig.barDuration
            offsetShift = shortDuration.quarterLength * shortMeasures        
            hasMeasures = thisStream.hasMeasures()


            if hasMeasures:
                allM = thisStream.getElementsByClass('Measure')
                oldFirstM = allM[0]
                for m in allM:
                    m.number += shortMeasures
                    m.setOffsetBySite(thisStream, thisStream.elementOffset(m) + offsetShift)
            else:
                for thisNote in thisStream.iter.notesAndRests:
                    thisNote.setOffsetBySite(thisStream, thisStream.elementOffset(m) + offsetShift) 


            for i in range(0, shortMeasures):
                newRest = note.Rest()
                newRest.duration = copy.deepcopy(shortDuration)    
                newRest.transparent = True
                if hasMeasures:
                    m = stream.Measure()
                    m.number = 1 + i
                    m.append(newRest)
                    thisStream.insert(shortDuration.quarterLength * i, m)
                else:
                    thisStream.insert(shortDuration.quarterLength * i, newRest)                
                if i == 0:
                    newRest.startTransparency = True
                elif i == (shortMeasures - 1):
                    newRest.stopTransparency = True

            if hasMeasures:
                newFirstM = thisStream.getElementsByClass('Measure')[0]
                oldFirstMEls = copy.copy(oldFirstM.elements)
                for n in oldFirstMEls:
                    if isinstance(n, note.GeneralNote):
                        pass
                    else:
                        nOffset = n.offset
                        oldFirstM.remove(n)
                        newFirstM.insert(nOffset, n)
        





class Test(unittest.TestCase):
    pass

    def runTest(self):
        pass

    def testCopyAndDeepcopy(self):
        '''Test copying all objects defined in this module
        '''
        import sys
        for part in sys.modules[self.__module__].__dict__:
            if part.startswith('_') or part.startswith('__'):
                continue
            elif part in ['Test', 'TestExternal']:
                continue
            elif callable(part):
                #environLocal.printDebug(['testing copying on', part])
                obj = getattr([self.__module__, part])()
                a = copy.copy(obj)
                b = copy.deepcopy(obj)
                self.assertNotEqual(a, obj)
                self.assertNotEqual(b, obj)


class TestExternal(unittest.TestCase):
    pass

    def runTest(self):
        pass
    def testLily(self):
        from music21.alpha import trecento
        cantus = trecento.trecentoCadence.CadenceConverter("6/8 c'2. d'8 c'4 a8 f4 f8 a4 c'4 c'8").parse().stream
        tenor = trecento.trecentoCadence.CadenceConverter("6/8 F1. f2. e4. d").parse().stream
        ps = PolyphonicSnippet([cantus, tenor, None, "8-8", "6/8"], parentPiece = trecento.cadencebook.BallataSheet().makeWork(3) )
        ps.show('musicxml.png')

if __name__ == "__main__":
    import music21
    music21.mainTest(Test, TestExternal)

#------------------------------------------------------------------------------
# eof

