import copy
import unittest, doctest


import music21
from music21 import meter
from music21 import lily as lilyModule
from music21 import note
from music21 import stream


class PolyphonicSnippet(stream.Score):
    '''
    a polyphonic snippet is a little Score-ette that represents an incipit or a cadence or something of that sort of a piece
    
    it is initialized with the contents of five excel cells -- the first three represent the notation of the 
    cantus, tenor, and contratenor, respectively.  the fourth is the cadence type (optional), the fifth
    is the time signature if not the same as the time signature of the parentPiece.
    

    >>> from music21 import *
    >>> cantus = trecento.trecentoCadence.TrecentoCadenceStream("c'2. d'8 c'4 a8 f4 f8 a4 c'4 c'8", '6/8')
    >>> tenor = trecento.trecentoCadence.TrecentoCadenceStream("F1. f2. e4. d", '6/8')
    >>> ps = trecento.polyphonicSnippet.PolyphonicSnippet([cantus, tenor, None, "8-8", "6/8"], parentPiece = "mom")
    >>> ps.elements
    [<music21.stream.Part ...>, <music21.stream.Part ...>]
    >>> ps.elements[0] is cantus
    True
    >>> #_DOCS_SHOW ps.show()
    
    
    
    .. image:: images/trecento-polyphonicSnippet1.*
            :width: 450

    
    
    OMIT_FROM_DOCS
    
    >>> dummy = trecento.polyphonicSnippet.PolyphonicSnippet()
    >>> dummy.elements
    []
    >>> dumClass = dummy.__class__
    >>> dumClass
    <class 'music21.trecento.polyphonicSnippet.PolyphonicSnippet'>
    >>> dumdum = dumClass()
    >>> dumdum.__class__
    <class 'music21.trecento.polyphonicSnippet.PolyphonicSnippet'>
    >>> ps2 = ps.__class__()
    >>> ps2.elements
    []
    
    >>> dummy2 = trecento.polyphonicSnippet.Incipit()
    >>> dummy2.elements
    []
    
    '''
    
    def __init__(self, fiveExcelCells = [], parentPiece = None):
        stream.Score.__init__(self)
        if fiveExcelCells != []:        
            if len(fiveExcelCells) != 5:
                raise Exception("Need five Excel Cells to make a PolyphonicSnippet object")
    
            self.partStreams = fiveExcelCells[0:3]  # first three
            for part in self.partStreams:
                if part is not None:
                    part.__class__ = stream.Part
            
            
            self.cadenceType = fiveExcelCells[3]
            self.timeSig = meter.TimeSignature(fiveExcelCells[4])
            self.parentPiece = parentPiece
            self.cantus = self.partStreams[0]
            self.tenor  = self.partStreams[1]
            self.contratenor = self.partStreams[2]
            
            if self.contratenor == "": 
                self.contratenor = None
                self.partStreams.pop(2)
            if self.tenor == "": 
                self.tenor = None
                self.partStreams.pop(1)
            if self.cantus == "": 
                self.cantus = None
                self.partStreams.pop(0)
    
            self._appendParts()

    def _appendParts(self):
        '''
        appends each of the partStreams to the current score.
        '''
        foundTs = False
        for thisVoice in [self.cantus, self.contratenor, self.tenor]:        
            # thisVoice is a type of stream.Stream()
            
            if thisVoice is not None:
                if hasattr(self, 'frontPadLine'):
                    self.frontPadLine(thisVoice)
                elif hasattr(self, 'backPadLine'):
                    self.backPadLine(thisVoice)
                if foundTs == False and len(thisVoice.getElementsByClass(meter.TimeSignature)) > 0:
                    foundTs = True
                thisVoice.makeNotation(inPlace = True)
                self.insert(0, thisVoice)
                
        if foundTs == False:
            self.insert(0, self.timeSig)
        self.rightBarline = 'final'

        

    def headerWithPageNums(self):
        '''returns a string that prints an appropriate header for this cadence'''
        if (self.parentPiece is not None):
            parentPiece = self.parentPiece
            headOut = " \\header { \n piece = \\markup \\bold \""
            if (parentPiece.fischerNum):
                headOut += str(parentPiece.fischerNum) + ". " 
            if parentPiece.title:
                headOut += parentPiece.title
            if (parentPiece.pmfcVol and parentPiece.pmfcPageRange()):
                headOut += " PMFC " + str(parentPiece.pmfcVol) + " " + parentPiece.pmfcPageRange()
            headOut += "\" \n}\n";
            return headOut
        else:
            return ""

    def headerWithCadenceName(self):
        pass
    
    def header(self):
        return self.headerWithPageNums()
                    
    def lilyFromStream(self, thisStream):
        lilyOut = lilyModule.LilyString("  \\new Staff { " + thisStream.bestClef().lily.value + " " + thisStream.lily.value + " } \n")
        return lilyOut
    
    def _getLily(self):
        thesepartStreams = self.partStreams
        timeSig = self.timeSig

        lilyOut = lilyModule.LilyString("\\score {\n")
        lilyOut += "<< \\time " + str(timeSig) + "\n"
        for thisStream in thesepartStreams:
            lilyOut += self.lilyFromStream(thisStream)

        lilyOut += ">>\n"
        lilyOut += self.header() + "}\n"
        return lilyOut

    lily = property(_getLily)

    def findLongestCadence(self):
        longestLineLength = 0
        for thisStream in self.partStreams:
            if thisStream is None:
                continue
            thisLength = thisStream.duration.quarterLength
            if thisLength > longestLineLength:
                longestLineLength = thisLength
        self.longestLineLength = longestLineLength
        return longestLineLength

    def measuresShort(self, thisStream):
        timeSigLength = self.timeSig.barDuration.quarterLength
        thisStreamLength = thisStream.duration.quarterLength
        shortness = self.findLongestCadence() - thisStreamLength
        shortmeasures = shortness/timeSigLength
        return shortmeasures



class Incipit(PolyphonicSnippet):

    def backPadLine(self, thisStream):
        '''
        Pads a Stream with a bunch of rests at the
        end to make it the same length as the longest line

        
        '''
        shortmeasures = int(self.measuresShort(thisStream))

        if (shortmeasures > 0):
            shortDuration = self.timeSig.barDuration

            for i in range(0, shortmeasures):
                newRest = note.Rest()
                newRest.duration = copy.deepcopy(shortDuration)
                newRest.transparent = 1
                thisStream.append(newRest)
                if i == 0:
                    newRest.startTransparency = 1
                elif i == (shortmeasures - 1):
                    newRest.stopTransparency = 1


class FrontPaddedCadence(PolyphonicSnippet):
    cadenceName = ""

    def frontPadLine(self, thisStream):
        '''Pads a line with a bunch of rests at the
        front to make it the same length as the longest line
        '''
        shortmeasures = int(self.measuresShort(thisStream))

        if (shortmeasures > 0):
            shortDuration = self.timeSig.barDuration
            offsetShift = shortDuration.quarterLength * shortmeasures
            for thisNote in thisStream.notesAndRests:
                thisNote.setOffsetBySite(thisStream, thisNote.getOffsetBySite(thisStream) + offsetShift) 

            for i in range(0, shortmeasures):
                newRest = note.Rest()
                newRest.duration = copy.deepcopy(shortDuration)
                newRest.transparent = 1
                thisStream.insert(shortDuration.quarterLength * i, newRest)
                if i == 0:
                    newRest.startTransparency = 1
                elif i == (shortmeasures - 1):
                    newRest.stopTransparency = 1

    def header(self):
        headOut = " \\header { \n piece = \"" + self.parentPiece.title
        if (self.cadenceName):
            headOut += " -- " + self.cadenceName + " "
        headOut += " \" \n}\n";
        return headOut

    def __init__(self, fiveExcelCells, parentPiece):
        PolyphonicSnippet.__init__(self, fiveExcelCells, parentPiece)
        self.findLongestCadence()
        for thisStream in self.partStreams:
            self.frontPadLine(thisStream)


class Test(unittest.TestCase):
    pass

    def runTest(self):
        pass


#------------------------------------------------------------------------------
# eof

if __name__ == "__main__":
    music21.mainTest(Test)
