
import music21
import music21.duration
from music21 import tinyNotation
from music21.duration import DurationException
import xlrd
import xlrd.sheet
import trecentoCadence
import random
from music21 import lily
from music21 import meter
import polyphonicSnippet
from polyphonicSnippet import *
from music21 import note

class TrecentoSheet(object):
    '''represents a single worksheet of an excel spreadsheet 
    that contains
    data about particular pieces of trecento music
    '''

    sheetname = "fischer_caccia"
    filename  = "cadences.xls"
    
    def __init__(self, **keywords):
        if (keywords.has_key("filename")): self.filename = keywords["filename"]
        xbook = xlrd.open_workbook(self.filename)
        
        if (keywords.has_key("sheetname")): self.sheetname = keywords["sheetname"]
        
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

    def makeWork(self, rownumber = 1):
        ''' We use Excel Row numbers, NOT Python row numbers: 
        in other words, makeWork(1) = Excel row 1 (python row 0)
        '''
        rowvalues = self.sheet.row_values(rownumber - 1)
        return TrecentoCadenceWork(rowvalues, self.rowDescriptions)

class CacciaSheet(TrecentoSheet):
    sheetname = "fischer_caccia"

class MadrigalSheet(TrecentoSheet):
    sheetname = "fischer_madr"
    
class BallataSheet(TrecentoSheet):
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

        self.snippetBlocks = []
        self.snippetBlocks.append(self.getIncipit())
        otherS = self.getOtherSnippets()
        if otherS is not None:
            self.snippetBlocks += otherS        
                
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
        '''
        rowBlock = self.rowvalues[8:12]
        rowBlock.append(self.rowvalues[7])
        if (rowBlock[0] == "" or self.timeSigBegin == ""):
            return None
        else: 
            self.convertBlockToStreams(rowBlock)
            return Incipit(rowBlock, self)

    def getOtherSnippets(self):
        returnSnips = []
        for i in range(12, len(self.rowvalues)-1, 5):
            thisSnippet = self.getSnippetAtPosition(i)
            if thisSnippet is not None:
                returnSnips.append(thisSnippet)
        return returnSnips

    def getSnippetAtPosition(self, snippetPosition):
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
        currentTimeSig = thisBlock[4]
        for i in range(0,3):
            thisVoice = thisBlock[i]
            thisVoice = thisVoice.strip()
            if (thisVoice):
                try:
                    tc1 = music21.tinyNotation.TinyNotationLine(thisVoice, currentTimeSig)
                    thisBlock[i] = tc1.stream
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

    def allNotation(self):
        '''returns a list of all the 
        PolyphonicSnippet objects in the database; currently 
        this is the incipit and all the cadences
        '''
        return self.snippetBlocks

    def allCadences(self):
        '''returns a list of all the PolyphonicSnippet 
        objects which are actually cadences
        '''
        x = len(self.snippetBlocks)
        return self.snippetBlocks[1:x]

    def incipitClass(self):
        return self.snippetBlocks[0]

    def cadenceAClass(self):
        try:
            fc = self.snippetBlocks[1]
        except IndexError:
            return None
        if fc is not None:
            fc.cadenceName = "A section cadence"
        return fc

    def cadenceB1Class(self):
        try:
            fc = self.snippetBlocks[2]
        except IndexError:
            return None
        if fc is not None:
            fc.cadenceName = "B section cadence (1st or only ending)"
        return fc
    
    def cadenceB2Class(self):
        try:
            fc = self.snippetBlocks[3]
        except IndexError:
            return None        
        if fc is not None:
            fc.cadenceName = "B section cadence (2nd ending)"
        return fc

    def getAllStreams(self):
        '''Get all streams in the work, losing association with
        the other polyphonic units.
        '''
        snippets = self.allNotation()
        streams = []
        for thisPolyphonicSnippet in snippets:
            PSStreams = thisPolyphonicSnippet.streams
            for thisStream in PSStreams:
                streams.append(thisStream)
        return streams
    
    def getAllLily(self):
        '''Get the total lily output
        '''
        all = self.allNotation()
        alllily = ''
        for thing in all:
            if thing.lily != '' and thing.lily != ' ' and thing.lily is not None:
                alllily = alllily + thing.lily
        return alllily

    def pmfcPageRange(self):
        if (self.pmfcPageStart != self.pmfcPageEnd):
            return str("pp. " + str(self.pmfcPageStart) + "-" + str(self.pmfcPageEnd))
        else:
            return str("p. " + str(self.pmfcPageStart))

class Ballata(TrecentoCadenceWork):
    def getOtherSnippets(self):
        for i in [12, 17, 22]:
            thisSnippet = self.getSnippetAtPosition(i)
            if thisSnippet is not None:
                self.snippetBlocks.append(thisSnippet)

if (__name__ == "__main__"):
    cs1 = CredoSheet() #filename = r'd:\docs\trecento\fischer\cadences.xls')
#    cs1 = BallataSheet()
    credo1 = cs1.makeWork(2)
    inc1 = credo1.snippetBlocks[4]
    inc1.lily.showPNG()
