import copy

import music21
from music21 import meter
from music21 import lily as lilyModule
from music21 import note
from music21 import stream


class PolyphonicSnippet(music21.Music21Object):
    def __init__(self, fiveExcelCells, parentPiece):
        if len(fiveExcelCells) != 5:
            raise Exception("Need five Excel Cells to make a PolyphonicSnippet object")
        self.streams = fiveExcelCells[0:3]  # first three
        self.cadenceType = fiveExcelCells[3]
        self.timeSig = meter.TimeSignature(fiveExcelCells[4])
        self.parentPiece = parentPiece
        self.cantus = self.streams[0]
        self.tenor  = self.streams[1]
        self.contratenor = self.streams[2]
        
        if self.contratenor == "": 
            self.contratenor = None
            self.streams.pop(2)
        if self.tenor == "": 
            self.tenor = None
            self.streams.pop(1)
        if self.cantus == "": 
            self.cantus = None
            self.streams.pop(0)

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
        theseStreams = self.streams
        timeSig = self.timeSig

        lilyOut = lilyModule.LilyString("\\score {\n")
        lilyOut += "<< \\time " + str(timeSig) + "\n"
        for thisStream in theseStreams:
            lilyOut += self.lilyFromStream(thisStream)

        lilyOut += ">>\n"
        lilyOut += self.header() + "}\n"
        return lilyOut

    lily = property(_getLily)

class Incipit(PolyphonicSnippet):
    pass

class FrontPaddedCadence(PolyphonicSnippet):
    cadenceName = ""

    def findLongestCadence(self):
        longestLineLength = 0
        for thisStream in self.streams:
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
        shortness = self.longestLineLength - thisStreamLength
        shortmeasures = shortness/timeSigLength
        return shortmeasures

    def frontPadLine(self, thisStream):
        '''Pads a line with a bunch of rests at the
        front to make it the same length as the longest line
        '''
        shortmeasures = int(self.measuresShort(thisStream))
        if (shortmeasures > 0):
            shortDuration = self.timeSig.barDuration
            newNotes = stream.Stream()
            for i in range(0, shortmeasures):
                newRest = note.Rest()
                newRest.duration = copy.deepcopy(shortDuration)
                newRest.transparent = 1
                newNotes.append(newRest)
            newNotes[0].startTransparency = 1
            newNotes[-1].stopTransparency = 1
            thisStream.elements = newNotes.elements + thisStream.elements

    def header(self):
        headOut = " \\header { \n piece = \"" + self.parentPiece.title
        if (self.cadenceName):
            headOut += " -- " + self.cadenceName + " "
        headOut += " \" \n}\n";
        return headOut

    def __init__(self, fiveExcelCells, parentPiece):
        PolyphonicSnippet.__init__(self, fiveExcelCells, parentPiece)
        self.findLongestCadence()
        for thisStream in self.streams:
            self.frontPadLine(thisStream)
