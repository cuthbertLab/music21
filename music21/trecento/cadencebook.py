#-------------------------------------------------------------------------------
# Name:         trecento/cadencebook.py
# Purpose:      classes for reading in trecento cadences from a MS Excel spreadsheet
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    (c) 2009 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import doctest
import unittest
import random
import os

import music21
import music21.duration
from music21.duration import DurationException

from music21 import lily
from music21 import meter
from music21 import note

from music21.trecento import xlrd
from music21.trecento.xlrd import sheet # may not be necessary
from music21.trecento import trecentoCadence
from music21.trecento import polyphonicSnippet
from music21.trecento.polyphonicSnippet import *


class TrecentoSheet(object):
    '''
    A TrecentoSheet represents a single worksheet of an excel spreadsheet 
    that contains data about particular pieces of trecento music

    >>> sanctusSheet = TrecentoSheet(sheetname = 'sanctus')
    >>> for thisSanctus in sanctusSheet:
    ...     pass
    
    '''

    sheetname = "fischer_caccia"
    filename  = "cadences.xls"
    
    def __init__(self, **keywords):
        if ("filename" in keywords): 
            self.filename = keywords["filename"]
        if self.filename:
            try:
                xbook = xlrd.open_workbook(self.filename)        
            except IOError:
                xbook = xlrd.open_workbook(music21.trecento.__path__[0] + os.sep + self.filename)

            
            if ("sheetname" in keywords): 
                self.sheetname = keywords["sheetname"]
            
            self.sheet = xbook.sheet_by_name(self.sheetname)
            self.totalRows = self.sheet.nrows
            self.rowDescriptions = self.sheet.row_values(0)
                

    def __iter__(self):
        self.iterIndex = 2 ## row 1 is a header
        return self

    def next(self):
        if self.iterIndex == self.totalRows:
            raise StopIteration
        work = self.makeWork(self.iterIndex)
        self.iterIndex += 1
        return work

    def __getitem__(self, key):
        if isinstance(key, int):
            return self.makeWork(key)
    
        elif isinstance(key, slice): # get a slice of index values
            found = []
            start = key.start
            if start is None:
                start = 0
            stop = key.stop
            if stop is None:
                stop = self.totalRows + 1
            step = key.step
            if step is None:
                step = 1
            for i in range(start, stop, step):
                found.append(self.makeWork(i))
            return found

    def makeWork(self, rownumber = 2):
        '''
        Returns the TrecentoCadenceWork at the given row number
        Same as using getItem above, but without slices...
        
        We use Excel Row numbers, NOT Python row numbers: 
        in other words, makeWork(1) = Excel row 1 (python row 0)

        Row 1 is a header, so makeWork(2) gives the first piece.
        
        >>> a = BallataSheet()
        >>> b = a.makeWork(3)
        >>> print(b.title)
        Ad(d)io, amore mio
        '''
        rowvalues = self.sheet.row_values(rownumber - 1)
        return TrecentoCadenceWork(rowvalues, self.rowDescriptions)

class CacciaSheet(TrecentoSheet):
    '''
    shortcut to a worksheet containing all the caccia cadences encoded
    
    >>> cacciaSheet = CacciaSheet()
    '''
    
    sheetname = "fischer_caccia"

class MadrigalSheet(TrecentoSheet):
    '''
    shortcut to a worksheet containing all the madrigal cadences encoded
    '''
    
    sheetname = "fischer_madr"
    
class BallataSheet(TrecentoSheet):
    '''
    shortcut to a worksheet containing all the ballata cadences encoded
    '''

    sheetname = "fischer_ballata"

    def makeWork(self, rownumber = 1):
        rowvalues = self.sheet.row_values(rownumber - 1)
        return Ballata(rowvalues, self.rowDescriptions)

class KyrieSheet(TrecentoSheet):
    sheetname = "kyrie"
class GloriaSheet(TrecentoSheet):
    sheetname = "gloria"    
class CredoSheet(TrecentoSheet):
    sheetname = "credo"
class SanctusSheet(TrecentoSheet):
    sheetname = "sanctus"
class AgnusDeiSheet(TrecentoSheet):
    sheetname = "agnus"

class TrecentoCadenceWork(object):
    '''
    A class representing a work that takes one line in the Trecento Cadence excel workbook 
    
    Takes in two lists: one containing a value for each column in the excel spreadsheet
    and another containing a description for each column (generally, the excel header row)
    
    contains the following attributes:
        fisherNum    -- the work number assigned by Kurt von Fischer (only applies to pieces discovered before 1956)
        title        -- may contain unicode characters
        composer      -- "." = anonymous
        encodedVoices -- a string representing the number of voices, a period, then the number of texted voices
        pmfcVol      -- the volume of Polyphonic Music of the Fourteenth Century where the piece might be found (if any)
        pmfcPageStart -- the initial page number in that PMFC volume 
        pmfcPageEnd   -- the final page number
        timeSignBegin -- the starting time signature (as a string) for the piece
        entryNotes    -- comments
    '''

    snippetPositions = []
    
    def __init__(self, rowvalues = [], rowDescriptions = []):
        self.rowvalues     = rowvalues
        self.rowDescriptions = rowDescriptions
        self.fischerNum    = rowvalues[0]
        self.title         = rowvalues[1]
        self.composer      = rowvalues[2]
        self.encodedVoices = rowvalues[3]
        self.pmfcVol       = rowvalues[4]
        self.pmfcPageStart = rowvalues[5]
        self.pmfcPageEnd   = rowvalues[6]
        self.timeSigBegin  = rowvalues[7]
        self.entryNotes    = rowvalues[-1]

        self.snippets = []
        self.snippets.append(self.getIncipit())
        otherS = self.getOtherSnippets()
        if otherS is not None:
            self.snippets += otherS        
                
        if isinstance(self.fischerNum, float):
            self.fischerNum = int(self.fischerNum)
        if self.pmfcVol:
            try:
                self.pmfcVol = int(self.pmfcVol)
            except:
                self.pmfcVol = 0
        if self.pmfcPageStart:
            self.pmfcPageStart = int(self.pmfcPageStart)
        if self.pmfcPageEnd:
            self.pmfcPageEnd = int(self.pmfcPageEnd)
            self.totalPmfcPages = ((self.pmfcPageEnd - self.pmfcPageStart) + 1)
        else:
            self.totalPmfcPage  = None

        if self.composer == ".":
            self.isAnonymous = True
        else:
            self.isAnonymous = False

    def getIncipit(self):
        '''the first incipit keeps its time signature
        in a different location from all the other snippets.
        hence, it's a little different
        
        Returns None if the piece or timeSignature is 
        undefined
        
        >>> bs = BallataSheet()
        >>> accur = bs.makeWork(2)
        >>> accurIncipit = accur.incipit
        >>> print(accurIncipit)
        <music21.trecento.polyphonicSnippet.Incipit object at 0x...>
        '''
        rowBlock = self.rowvalues[8:12]
        rowBlock.append(self.rowvalues[7])
        if (rowBlock[0] == "" or self.timeSigBegin == ""):
            return None
        else: 
            self.convertBlockToStreams(rowBlock)
            return Incipit(rowBlock, self)

    incipit = property(getIncipit)

    def getOtherSnippets(self):
        '''
        returns a list of bits of music notation encoded as
        FrontPaddedCadence objects.  That is, usually, all but the incipit

        >>> bs = BallataSheet()
        >>> accur = bs.makeWork(2)
        >>> accurSnippets = accur.getOtherSnippets()
        >>> for thisSnip in accurSnippets:
        ...     print(thisSnip)
        <music21.trecento.polyphonicSnippet.FrontPaddedCadence object at 0x...>
        <music21.trecento.polyphonicSnippet.FrontPaddedCadence object at 0x...>
         
        '''

        snippetPositions = self.snippetPositions ## overridden in class Ballata
        if snippetPositions == []:
            snippetPositions = range(12, len(self.rowvalues)-1, 5)
        returnSnips = []
        for i in snippetPositions:
            thisSnippet = self.getSnippetAtPosition(i)
            if thisSnippet is not None:
                returnSnips.append(thisSnippet)
        return returnSnips

    def getSnippetAtPosition(self, snippetPosition):
        '''
        gets a "snippet" which is a collection of up to 3 lines of music, a timeSignature
        and a description of the cadence.

        >>> bs = BallataSheet()
        >>> accur = bs.makeWork(2)
        >>> print(accur.getSnippetAtPosition(12))
        <music21.trecento.polyphonicSnippet.FrontPaddedCadence object at 0x...>
        '''
        
        if self.rowvalues[snippetPosition].strip() != "":
            thisBlock = self.rowvalues[snippetPosition:snippetPosition+5]
            if thisBlock[4].strip() == "":
                if self.timeSigBegin == "":
                    return None  ## need a timesig
                thisBlock[4] = self.timeSigBegin
            self.convertBlockToStreams(thisBlock)
            if self.isIncipitType(snippetPosition):
                return Incipit(thisBlock, self)
            else:
                return FrontPaddedCadence(thisBlock, self)

    def convertBlockToStreams(self, thisBlock):
        '''
        Takes a block of music information and converts it to a list of Streams and other information
        
        >>> block1 = ['e4 f g a', 'g4 a b cc', '', 'no-cadence', '2/4']
        >>> bs = BallataSheet()
        >>> dummyPiece = bs.makeWork(2)
        >>> dummyPiece.convertBlockToStreams(block1)
        >>> for x in block1:
        ...     print(x)
        <music21.trecento.trecentoCadence.TrecentoCadenceStream object at 0x...>
        <music21.trecento.trecentoCadence.TrecentoCadenceStream object at 0x...>
        <BLANKLINE>
        no-cadence
        2/4
        >>> block1[0].show('text')
        {0.0} <music21.meter.TimeSignature 2/4>
        {0.0} <music21.note.Note E>
        {1.0} <music21.note.Note F>
        {2.0} <music21.note.Note G>
        {3.0} <music21.note.Note A>
        <BLANKLINE> 
        '''
        
        currentTimeSig = thisBlock[4]
        for i in range(0,3):
            thisVoice = thisBlock[i]
            thisVoice = thisVoice.strip()
            if (thisVoice):
                try:
                    thisBlock[i] = trecentoCadence.TrecentoCadenceStream(thisVoice, currentTimeSig)
                except DurationException, (value):
                    raise DurationException("Problems in line %s: specifically %s" % (thisVoice,  value))
#                except Exception, (value):
#                    raise Exception("Unknown Problems in line %s: specifically %s" % (thisVoice,  value))

    def isIncipitType(self, columnNumber):
        '''There are two types of PolyphonicSnippets: 
        those that start together and those that end together.
        
        IncipitTypes start together
        FrontPaddedCadences end together.
        
        override this function in your subclass to specify
        which columns in your excel Workbook contain incipit types
        and which contain 
        '''
        if columnNumber in [8]: return True
        return False

    def allCadences(self):
        '''returns a list of all the PolyphonicSnippet 
        objects which are actually cadences
        '''
        x = len(self.snippets)
        return self.snippets[1:x]

#    def incipitClass(self):
#        return self.snippets[0]

    def cadenceAClass(self):
        try:
            fc = self.snippets[1]
        except IndexError:
            return None
        if fc is not None:
            fc.cadenceName = "A section cadence"
        return fc

    cadenceA = property(cadenceAClass)

    def cadenceB1Class(self):
        try:
            fc = self.snippets[2]
        except IndexError:
            return None
        if fc is not None:
            fc.cadenceName = "B section cadence (1st or only ending)"
        return fc

    cadenceBOuvert = property(cadenceB1Class)
    
    def cadenceB2Class(self):
        try:
            fc = self.snippets[3]
        except IndexError:
            return None        
        if fc is not None:
            fc.cadenceName = "B section cadence (2nd ending)"
        return fc

    cadenceBClos = property(cadenceB2Class)

    def getAllStreams(self):
        '''Get all streams in the work, losing association with
        the other polyphonic units.
        '''
        snippets = self.snippets
        streams = []
        for thisPolyphonicSnippet in snippets:
            if thisPolyphonicSnippet is not None:
                PSStreams = thisPolyphonicSnippet.streams
                for thisStream in PSStreams:
                    streams.append(thisStream)
        return streams
    
    def getAllLily(self):
        '''
        Get the total lily output for the entire work
        '''
        all = self.snippets
        alllily = ''
        for thing in all:
            if thing.lily != '' and thing.lily != ' ' and thing.lily is not None:
                alllily = alllily + thing.lily
        return alllily

    def pmfcPageRange(self):
        '''
        returns a nicely formatted string giving the page numbers in PMFC where the piece
        can be found
        
        >>> bs = BallataSheet()
        >>> altroCheSospirar = bs.makeWork(4)
        >>> altroCheSospirar.title
        u'Altro che sospirar'
        >>> altroCheSospirar.pmfcVol
        11
        >>> altroCheSospirar.pmfcPageRange()
        'pp. 2-4'
        '''
        
        if (self.pmfcPageStart != self.pmfcPageEnd):
            return str("pp. " + str(self.pmfcPageStart) + "-" + str(self.pmfcPageEnd))
        else:
            return str("p. " + str(self.pmfcPageStart))


class Ballata(TrecentoCadenceWork):
    '''
    Class representing a fourteenth-century Ballata.
    
    Overrides the locations of the column numbers in which one finds the cadences.
    '''
    snippetPositions = [12, 17, 22]
    

class Test(unittest.TestCase):
    def runTest(self):
        pass

    def testGetSnippets(self):
        bs = BallataSheet()
        accur = bs.makeWork(2)
        accurSnippets = accur.getOtherSnippets()
        self.assertEqual(len(accurSnippets), 2)

    def testConvertBlockToStreams(self):
        block1 = ['e4 f g a', 'g4 a b cc', '', 'no-cadence', '2/4']
        bs = BallataSheet()
        dummyPiece = bs.makeWork(2)
        dummyPiece.convertBlockToStreams(block1)
        self.assertTrue(isinstance(block1[0], stream.Stream))

class TestExternal(unittest.TestCase):
    def runTest(self):
        pass
    
    def testCredo(self):
        '''
        testing a Credo in and Lilypond out
        '''
        
        cs1 = CredoSheet() #filename = r'd:\docs\trecento\fischer\cadences.xls')
    #    cs1 = BallataSheet()
        credo1 = cs1.makeWork(2)
        inc1 = credo1.snippets[4]
        inc1.lily.showPNG()

    def testSnippetShow(self):
        '''
        testing a fake snippet in and MusicXML out
        '''
        block1 = ['e4 f g a', 'g4 a b cc', '', 'no-cadence', '2/4']
        bs = BallataSheet()
        dummyPiece = bs.makeWork(2)
        dummyPiece.convertBlockToStreams(block1)
        fpc1 = FrontPaddedCadence(block1, dummyPiece)
#       TODO: Make FrontPaddedCadence a subclass of Score!
#        fpc1.show()


if __name__ == "__main__":
    music21.mainTest(Test)