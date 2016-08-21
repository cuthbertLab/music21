# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         trecento/cadencebook.py
# Purpose:      classes for reading in trecento cadences from a MS Excel spreadsheet
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2009, 2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
The file trecento/cadences.xls contains (in a modified TinyNotation format) incipits
and cadences for hundreds of trecento ballatas (in a sheet called "fischer_ballata")
and several other works (sanctus, etc.).  This module contains methods and classes
for working with this encoding, including transforming it into music21 Streams.
'''

import unittest
import re
import os
import copy

from music21 import common
from music21 import duration
from music21 import expressions
from music21 import metadata
from music21 import stream

from music21.ext import xlrd
from music21.alpha.trecento import trecentoCadence
from music21.alpha.trecento import polyphonicSnippet

class TrecentoSheet(object):
    '''
    A TrecentoSheet represents a single worksheet of an excel spreadsheet 
    that contains data about particular pieces of trecento music.
    
    
    Users can iterate over the rows to get TrecentoCadenceWork objects for each row.
    
    
    
    See the specialized subclasses below, esp. BallataSheet for more details.


    
    >>> kyrieSheet = alpha.trecento.cadencebook.TrecentoSheet(sheetname = 'kyrie')
    >>> for thisKyrie in kyrieSheet:
    ...     print(thisKyrie.title)
    Questa Fanc.
    Kyrie Summe Clementissime
    Kyrie rondello
    '''

    filename  = "cadences.xls"
    sheetname = "fischer_caccia"
    
    def __init__(self, **keywords):
        self.iterIndex = 2
        if ("filename" in keywords): 
            self.filename = keywords["filename"]
        if self.filename:
            try:
                xbook = xlrd.open_workbook(self.filename)        
            except IOError:
                xbook = xlrd.open_workbook(os.path.join(common.getSourceFilePath(), 
                                                        'alpha', 'trecento',
                                                        self.filename))

            
            if ("sheetname" in keywords): 
                self.sheetname = keywords["sheetname"]
            
            self.sheet = xbook.sheet_by_name(self.sheetname)
            self.totalRows = self.sheet.nrows
            self.rowDescriptions = self.sheet.row_values(0)
                

    def __iter__(self):
        self.iterIndex = 2 ## row 1 is a header
        return self

    def next(self):
        if self.iterIndex > self.totalRows:
            raise StopIteration
        work = self.makeWork(self.iterIndex)
        self.iterIndex += 1
        return work

    def __next__(self):
        return self.next()

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
        
        
        >>> ballataSheet = alpha.trecento.cadencebook.BallataSheet()
        >>> b = ballataSheet.makeWork(3)
        >>> print(b.title)
        Ad(d)io, amore mio
        '''
        rowvalues = self.sheet.row_values(rownumber - 1)
        return TrecentoCadenceWork(rowvalues, self.rowDescriptions)

    def workByTitle(self, title):
        '''
        return the first work with TITLE in the work's title.  Case insensitive
        
        
        >>> ballataSheet = alpha.trecento.cadencebook.BallataSheet()
        >>> farina = ballataSheet.workByTitle('farina')
        >>> print(farina.title)
        De mia farina
        >>> farina.incipit.parts[0].show('text')
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.clef.TrebleClef>
            {0.0} <music21.meter.TimeSignature 3/4>
            {0.0} <music21.note.Rest rest>
            {1.0} <music21.note.Rest rest>
            {2.0} <music21.note.Note C>
            {2.5} <music21.note.Note D>
        {3.0} <music21.stream.Measure 2 offset=3.0>
            {0.0} <music21.note.Note E>
            {1.0} <music21.note.Note G>
            {2.0} <music21.note.Note G>
        {6.0} <music21.stream.Measure 3 offset=6.0>
            {0.0} <music21.note.Note G>
            {1.0} <music21.note.Note E>
            {2.0} <music21.note.Note D>
            {3.0} <music21.bar.Barline style=final>
        '''
        title = title.lower()
        for i in range(self.totalRows):
            rowValues = self.sheet.row_values(i)
            if rowValues[1] is None:
                continue
            elif title in rowValues[1].lower():
                return self.makeWork(i+1)
        return None


class CacciaSheet(TrecentoSheet):
    '''
    shortcut to a worksheet containing all the caccia cadences encoded
    
    
    2011-May: none encoded.
    
    
    
    >>> cacciaSheet = alpha.trecento.cadencebook.CacciaSheet()
    '''
    
    sheetname = "fischer_caccia"

class MadrigalSheet(TrecentoSheet):
    '''
    shortcut to a worksheet containing all the madrigal cadences encoded
    
    
    2011-May: none encoded.
    
    
    '''
    
    sheetname = "fischer_madr"
    
class BallataSheet(TrecentoSheet):
    '''
    shortcut to a worksheet containing all the ballata cadences encoded.
    
    
    2011-May: over 400 of 460 encoded; unencoded pieces are mostly fragmentary.
    
    '''

    sheetname = "fischer_ballata"

    def makeWork(self, rownumber = 1):
        rowvalues = self.sheet.row_values(rownumber - 1)
        return Ballata(rowvalues, self.rowDescriptions)

class KyrieSheet(TrecentoSheet):
    sheetname = "kyrie"
class GloriaSheet(TrecentoSheet):
    '''
    shortcut to a worksheet containing all the known 14th and early 15th c.
    French, Spanish, and Italian Gloria's openings of the Et in Terra, Dominus Deus,
    Qui Tollis, encoded along with the ends of the Cum Sancto and Amen.
    
    
    2011-August: all encoded except some very fragmentary pieces.
    
    
    
    >>> cadenceSpreadSheet = alpha.trecento.cadencebook.GloriaSheet()
    >>> gloriaNo20 = cadenceSpreadSheet.makeWork(20)
    >>> incipit = gloriaNo20.incipit
    >>> incipit.show('text')
    {0.0} <music21.metadata.Metadata object at 0x...>
    {0.0} <music21.stream.Part C>
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.clef.TrebleClef>
            {0.0} <music21.meter.TimeSignature 2/4>
            {0.0} <music21.note.Note D>
        {2.0} <music21.stream.Measure 2 offset=2.0>
            {0.0} <music21.note.Note D>
        ...
            {2.0} <music21.bar.Barline style=final>
    {0.0} <music21.stream.Part Ct>
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.clef.BassClef>
            {0.0} <music21.meter.TimeSignature 2/4>
            {0.0} <music21.note.Note D>
        {2.0} <music21.stream.Measure 2 offset=2.0>
            {0.0} <music21.note.Note F#>
        ...
        {16.0} <music21.stream.Measure 9 offset=16.0>
            {0.0} <music21.note.Note B>
            {2.0} <music21.bar.Barline style=final>
    {0.0} <music21.stream.Part T>
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.clef.BassClef>
            {0.0} <music21.meter.TimeSignature 2/4>
            {0.0} <music21.note.Note D>
        {2.0} <music21.stream.Measure 2 offset=2.0>
            {0.0} <music21.note.Note D>
        ...
        {16.0} <music21.stream.Measure 9 offset=16.0>
            {0.0} <music21.note.Note E>
            {2.0} <music21.bar.Barline style=final>
    
    '''

    sheetname = "gloria"

    def makeWork(self, rownumber = 1):
        rowvalues = self.sheet.row_values(rownumber - 1)
        return Gloria(rowvalues, self.rowDescriptions)

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
    
    
    contains the following attributes::
    
        fisherNum     -- the work number assigned by Kurt von Fischer 
            (only applies to pieces discovered before 1956)
        title         -- may contain unicode characters
        composer      -- "." = anonymous
        encodedVoices -- a string representing the number of voices, a period, 
            then the number of texted voices
        pmfcVol       -- the volume of Polyphonic Music of the Fourteenth Century 
            where the piece might be found (if any)
        pmfcPageStart -- the initial page number in that PMFC volume 
        pmfcPageEnd   -- the final page number
        timeSignBegin -- the starting time signature (as a string) for the piece
        entryNotes    -- comments

    attributes shared with all members of the class::
    
        beginSnippetPositions -- a list of the excel 
            spreadsheet columns in which an incipit of some section can be found. (default = [8])
        endSnippetPositions   -- a list of the excel 
            spreadsheet columns in which an cadence of some section can be found. (default = [])
    
    OMIT_FROM_DOCS
    
    test just creating an empty TrecentoCadenceWork:
    
    
    >>> tcw = alpha.trecento.cadencebook.TrecentoCadenceWork()
    '''
    beginSnippetPositions = [8]
    endSnippetPositions = []
    
    def __init__(self, rowvalues=None, rowDescriptions=None):
        if rowvalues is None:
            rowvalues = ["", "", "", "", "", "", "", "", "", "", "", "", ""]
        if rowDescriptions is None:
            rowDescriptions = ["Catalog Number", "Title", "Composer", "EncodedVoices", 
                               "PMFC/CMM Vol.", "PMFC Page Start", "PMFC Page End", 
                               "Time Signature Beginning", "Incipit C", "Incipit T", 
                               "Incipit Ct", "Incipit Type", "Notes"]
        self.rowvalues = rowvalues
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
        self.snippets.append(self.incipit)
        try:
            otherS = self.getOtherSnippets()
            if otherS is not None:
                self.snippets += otherS        
        except IndexError: # no rowvalues, etc. probably from documentation building...
            pass
                
        if isinstance(self.fischerNum, float):
            self.fischerNum = int(self.fischerNum)
        if self.pmfcVol:
            try:
                self.pmfcVol = int(self.pmfcVol)
            except ValueError:
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
        self.totalVoices = 0
        try:
            self.totalVoices = int(self.encodedVoices)
        except ValueError:
            try:
                self.totalVoices = int(self.encodedVoices[0])
            except (ValueError, IndexError):
                pass

    def asOpus(self):
        '''
        returns all snippets as a :class:`~music21.stream.Opus` object

        >>> deduto = alpha.trecento.cadencebook.BallataSheet().workByTitle('deduto')
        >>> deduto.title
        'Deduto sey a quel'
        >>> dedutoScore = deduto.asOpus()
        >>> dedutoScore
        <music21.stream.Opus ...>
        >>> #_DOCS_SHOW dedutoScore.show('lily.png')
        '''
        o = stream.Opus()
        md = metadata.Metadata()
        o.insert(0, md)
        o.metadata.composer = self.composer
        o.metadata.title = self.title   
        
        bs = self.snippets
        for thisSnippet in bs:
            if thisSnippet is None:
                continue
            if (thisSnippet.tenor is None  
                    and thisSnippet.cantus is None 
                    and thisSnippet.contratenor is None):
                continue
            s = stream.Score()
            for dummy in range(self.totalVoices):
                s.insert(0, stream.Part())

            for partNumber, snippetPart in enumerate(
                        thisSnippet.getElementsByClass('TrecentoCadenceStream')):
                if thisSnippet.snippetName != "" and partNumber == self.totalVoices - 1:
                    textEx = expressions.TextExpression(thisSnippet.snippetName)
                    textEx.positionVertical = 'below'
                    if 'FrontPaddedSnippet' in thisSnippet.classes:
                        if snippetPart.hasMeasures():
                            snippetPart.getElementsByClass('Measure')[-1].insert(0, textEx)
                        else:
                            snippetPart.append(textEx)
                    else:
                        if snippetPart.hasMeasures():
                            snippetPart.getElementsByClass('Measure')[0].insert(0, textEx)
                        else:
                            snippetPart.insert(0, textEx)
#                if currentTs is None or timeSig != currentTs:
#                    s.append(timeSig)
#                    currentTs = timeSig
                try:
                    currentScorePart = s.parts[partNumber]
                except IndexError:
                    continue  # error in coding
                for thisElement in snippetPart:
                    if 'TimeSignature' in thisElement.classes:
                        continue
                    currentScorePart.append(thisElement) 
            o.insert(0, s)
        return o
        
        

    def asScore(self):
        '''
        returns all snippets as a score chunk

        
        >>> deduto = alpha.trecento.cadencebook.BallataSheet().workByTitle('deduto')
        >>> deduto.title
        'Deduto sey a quel'
        >>> dedutoScore = deduto.asScore()
        >>> dedutoScore
        <music21.stream.Score ...>
        >>> #_DOCS_HIDE dedutoScore.show()

        Changes made to a snippet are reflected in the asScore() score object:
        
        >>> deduto.snippets[0].parts[0].flat.notes[0].name = "C###"
        >>> deduto.asScore().parts[0].flat.notes[0].name
        'C###'
        '''
        s = stream.Score()
        md = metadata.Metadata()
        s.insert(0, md)
        s.metadata.composer = self.composer
        s.metadata.title = self.title   
        
        for dummy in range(self.totalVoices):
            s.insert(0, stream.Part())
        bs = self.snippets
        for thisSnippet in bs:
            if thisSnippet is None:
                continue
            if (thisSnippet.tenor is None and 
                    thisSnippet.cantus is None and 
                    thisSnippet.contratenor is None):
                continue
            for partNumber, snippetPart in enumerate(thisSnippet.getElementsByClass('Stream')):
                if thisSnippet.snippetName != "" and partNumber == self.totalVoices - 1:
                    textEx = expressions.TextExpression(thisSnippet.snippetName)
                    textEx.positionVertical = 'below'
                    if 'FrontPaddedSnippet' in thisSnippet.classes:
                        if snippetPart.hasMeasures():
                            snippetPart.getElementsByClass('Measure')[-1].insert(0, textEx)
                        else:
                            snippetPart.append(textEx)
                    else:
                        if snippetPart.hasMeasures():
                            snippetPart.getElementsByClass('Measure')[0].insert(0, textEx)
                        else:
                            snippetPart.insert(0, textEx)
#                if currentTs is None or timeSig != currentTs:
#                    s.append(timeSig)
#                    currentTs = timeSig
                try:
                    currentScorePart = s.parts[partNumber]
                except IndexError:
                    continue  # error in coding
                for thisElement in snippetPart:
                    if 'TimeSignature' in thisElement.classes:
                        continue
                    currentScorePart.append(thisElement) 

        return s

    @property
    def incipit(self):
        '''
        Gets the Incipit PolyphonicSnippet of the piece.
        
        The incipit keeps its time signature
        in a different location from all the other snippets.
        hence, it's a little different
        
        Returns None if the piece or timeSignature is 
        undefined
        
        >>> bs = alpha.trecento.cadencebook.BallataSheet()
        >>> accur = bs.makeWork(2)
        >>> accurIncipit = accur.incipit
        >>> print(accurIncipit)
        <music21.alpha.trecento.polyphonicSnippet.Incipit ...>
        '''
        rowBlock = self.rowvalues[8:12]
        rowBlock.append(self.rowvalues[7])
        if (rowBlock[0] == "" or self.timeSigBegin == ""):
            return None
        else: 
            blockOut = self.convertBlockToStreams(rowBlock)
            return polyphonicSnippet.Incipit(blockOut, self)
 
    def getOtherSnippets(self):
        '''
        returns a list of bits of music notation that are not the actual
        incipits of the piece.


        
        >>> bs = alpha.trecento.cadencebook.BallataSheet()
        >>> accur = bs.makeWork(2)
        >>> accurSnippets = accur.getOtherSnippets()
        >>> for thisSnip in accurSnippets:
        ...     print(thisSnip)
        <music21.alpha.trecento.polyphonicSnippet.FrontPaddedSnippet ...>
        <music21.alpha.trecento.polyphonicSnippet.FrontPaddedSnippet ...>
         
        '''
        beginSnippetPositions = self.beginSnippetPositions
        endSnippetPositions = self.endSnippetPositions ## overridden in class Ballata
        if endSnippetPositions == []:
            endSnippetPositions = range(12, len(self.rowvalues)-1, 5)
        returnSnips = []
        for i in beginSnippetPositions:
            if i == beginSnippetPositions[0]:
                continue
            thisSnippet = self.getSnippetAtPosition(i, snippetType="begin")
            if thisSnippet is not None:
                thisSnippet.snippetName = self.rowDescriptions[i]
                thisSnippet.snippetName = re.sub(r'cad\b', 'cadence', thisSnippet.snippetName)
                thisSnippet.snippetName = re.sub(r'\s*C$', '', thisSnippet.snippetName)
                returnSnips.append(thisSnippet)
        for i in endSnippetPositions:
            thisSnippet = self.getSnippetAtPosition(i, snippetType="end")
            if thisSnippet is not None:
                thisSnippet.snippetName = self.rowDescriptions[i]
                thisSnippet.snippetName = re.sub('cad ', 'cadence ', thisSnippet.snippetName)
                thisSnippet.snippetName = re.sub(r'\s*C$', '', thisSnippet.snippetName)
                returnSnips.append(thisSnippet)
        return returnSnips

    def getSnippetAtPosition(self, snippetPosition, snippetType="end"):
        '''
        gets a "snippet" which is a collection of up to 3 lines of music, a timeSignature
        and a description of the cadence.

        
        >>> bs = alpha.trecento.cadencebook.BallataSheet()
        >>> accur = bs.makeWork(2)
        >>> print(accur.getSnippetAtPosition(12))
        <music21.alpha.trecento.polyphonicSnippet.FrontPaddedSnippet ...>
        '''
        
        if self.rowvalues[snippetPosition].strip() != "":
            thisBlock = self.rowvalues[snippetPosition:snippetPosition+5]
            if thisBlock[4].strip() == "":
                if self.timeSigBegin == "":
                    return None  ## need a timesig
                thisBlock[4] = self.timeSigBegin
            blockOut = self.convertBlockToStreams(thisBlock)
            if snippetType == 'begin':
                return polyphonicSnippet.Incipit(blockOut, self)
            else:
                return polyphonicSnippet.FrontPaddedSnippet(blockOut, self)

    def convertBlockToStreams(self, thisBlock):
        '''
        Takes a block of music information (in 
        :class:`~music21.alpha.trecento.trecentoCadence.TrecentoCadenceStream` notation)
        and returns a list of Streams and other information
        
        
        
        >>> block1 = ['e4 f g a', 'g4 a b cc', '', 'no-cadence', '2/4']
        >>> bs = alpha.trecento.cadencebook.BallataSheet()
        >>> dummyPiece = bs.makeWork(2)
        >>> blockStreams = dummyPiece.convertBlockToStreams(block1)
        >>> for x in blockStreams:
        ...     print(x)
        <music21.stream.Part ...>
        <music21.stream.Part ...>
        None
        no-cadence
        2/4
        >>> blockStreams[0].show('text')
        {0.0} <music21.stream.Measure 1 offset=0.0>
            {0.0} <music21.clef.TrebleClef>
            {0.0} <music21.meter.TimeSignature 2/4>
            {0.0} <music21.note.Note E>
            {1.0} <music21.note.Note F>
        {2.0} <music21.stream.Measure 2 offset=2.0>
            {0.0} <music21.note.Note G>
            {1.0} <music21.note.Note A>
            {2.0} <music21.bar.Barline style=final>
    

        '''
        returnBlock = [None, None, None, None, None]
        currentTimeSig = thisBlock[4]
        returnBlock[4] = currentTimeSig
        returnBlock[3] = thisBlock[3]
        for i in range(0,3):
            thisVoice = thisBlock[i]
            thisVoice = thisVoice.strip()
            if (thisVoice):
                try:
                    returnBlock[i] = trecentoCadence.CadenceConverter(currentTimeSig + " " + 
                                                                      thisVoice).parse().stream
                except duration.DurationException as value:
                    raise duration.DurationException("Problems in line %s: specifically %s" % 
                                                     (thisVoice,  value))
#                except Exception, (value):
#                    raise Exception("Unknown Problems in line %s: specifically %s" % 
#                    (thisVoice,  value))

        return returnBlock

    def allCadences(self):
        '''
        returns a list of all the PolyphonicSnippet 
        objects which are actually cadences (and not incipits)
        '''
        x = len(self.snippets)
        return self.snippets[1:x]


    @property
    def cadenceA(self):
        '''
        returns the snippet which represents the cadence at the end of
        the A section of the piece.
        '''
        try:
            fc = self.snippets[1]
        except IndexError:
            return None
        if fc is not None:
            fc.snippetName = "A section cadence"
        return fc

    @property
    def cadenceB(self):
        '''
        returns the snippet that represents the open cadence of the B section
        or the only cadence if there are no open and close endings.
        '''
        try:
            fc = self.snippets[2]
        except IndexError:
            return None
        if fc is not None:
            fc.snippetName = "B section cadence (1st or only ending)"
        return fc

    @property    
    def cadenceBClos(self):
        '''
        Returns the second B cadence -- that is, the 2nd or clos ending.
        '''
        try:
            fc = self.snippets[3]
        except IndexError:
            return None        
        if fc is not None:
            fc.snippetName = "B section cadence (2nd ending)"
        return fc

    def getAllStreams(self):
        '''
        Get all streams in the work as a List, losing association with
        the other polyphonic units.
        
        
        >>> b = alpha.trecento.cadencebook.BallataSheet().makeWork(20)
        >>> sList = b.getAllStreams()
        >>> sList
        [<music21.stream.Part ...>, <music21.stream.Part ...>, ...] 
        
        '''
        snippets = self.snippets
        streams = []
        for thisPolyphonicSnippet in snippets:
            if thisPolyphonicSnippet is not None:
                PSStreams = thisPolyphonicSnippet.parts
                for thisStream in PSStreams:
                    streams.append(thisStream)
        return streams
    
    def pmfcPageRange(self):
        '''
        returns a nicely formatted string giving the page numbers in PMFC where the piece
        can be found
        
        >>> bs = alpha.trecento.cadencebook.BallataSheet()
        >>> altroCheSospirar = bs.makeWork(4)
        >>> altroCheSospirar.title
        'Altro che sospirar'
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
    beginSnippetPositions = [8]
    endSnippetPositions = [12, 17, 22]
    

class Gloria(TrecentoCadenceWork):
    '''
    Class representing a fourteenth-century Gloria.
    
    Overrides the locations of the column numbers in which one finds the cadences.
    '''
    beginSnippetPositions = [8, 12, 17]
    endSnippetPositions = [22, 27]
    

class Test(unittest.TestCase):
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
                obj = getattr(self.__module__, part)()
                a = copy.copy(obj)
                b = copy.deepcopy(obj)
                self.assertNotEqual(a, obj)
                self.assertNotEqual(b, obj)

    def testTrecentoCadenceWorkCopying(self):
        w = TrecentoCadenceWork()
        unused_w1 = copy.copy(w)
        unused_w2 = copy.deepcopy(w)

    def testTrecentoCadenceWorkFromSheetCopying(self):
        w = BallataSheet().makeWork(331)
        unused_w1 = copy.copy(w)
        unused_w2 = copy.deepcopy(w)


    def testGetSnippets(self):
        bs = BallataSheet()
        accur = bs.makeWork(2)
        accurSnippets = accur.getOtherSnippets()
        self.assertEqual(len(accurSnippets), 2)

    def testConvertBlockToStreams(self):
        block1 = ['e4 f g a', 'g4 a b cc', '', 'no-cadence', '2/4']
        bs = BallataSheet()
        dummyPiece = bs.makeWork(2)
        block2 = dummyPiece.convertBlockToStreams(block1)
        self.assertTrue(isinstance(block2[0], stream.Stream))
        
    

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
        opusCredo1 = credo1.asOpus()
        opusCredo1.show('lily.png')
        #conv.showPNG()

    def testBallata(self):
        '''
        testing a Ballata in and Lilypond out
        '''
        
        cs1 = BallataSheet() #filename = r'd:\docs\trecento\fischer\cadences.xls')
        ballata1 = cs1.makeWork(58)
        opusBallata1 = ballata1.asOpus()
        opusBallata1.show('lily.svg')


    def xtestSnippetShow(self):
        '''
        testing a fake snippet in and MusicXML out
        '''
        block1 = ['e4 f g a', 'g4 a b cc', '', 'no-cadence', '2/4']
        bs = BallataSheet()
        dummyPiece = bs.makeWork(2)
        block2 = dummyPiece.convertBlockToStreams(block1)
        unused_fpc1 = polyphonicSnippet.FrontPaddedSnippet(block2, dummyPiece)
#        fpc1.show()

    def xtestVirelais(self):
        '''
        test showing a virelai's incipit to see if it works
        '''
        virelaisSheet = TrecentoSheet(sheetname = 'virelais')
        thisVirelai = virelaisSheet.makeWork(54)
        if thisVirelai.title != "":
            print(thisVirelai.title)
            thisVirelai.incipit.show('musicxml')
    
    def xtestRondeaux(self):
        '''
        test showing a rondeaux's incipit to see if it works
        '''
        rondeauxSheet = TrecentoSheet(sheetname = 'rondeaux')
        thisRondeaux = rondeauxSheet.makeWork(41)
        if thisRondeaux.title != "":
            print(thisRondeaux.title)
            thisRondeaux.incipit.show('musicxml')
    
    def xtestGloria(self):
        '''
        test showing a Gloria's incipit to see if it works
        '''
        gloriaS = GloriaSheet()
        thisGloria = gloriaS.makeWork(20)
        if thisGloria.title != "":
            thisGloria.asScore().show()

    def xtestAsScore(self):
        deduto = BallataSheet().workByTitle('deduto')
        self.assertEqual(deduto.title, u'Deduto sey a quel')
#        for s in deduto.snippets:
#            s.show('text')
        dedutoScore = deduto.asScore()
        dedutoScore.show()
        pass


if __name__ == "__main__":
    import music21
    music21.mainTest(Test) #, TestExternal)


#------------------------------------------------------------------------------
# eof

