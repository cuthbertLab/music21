#!/usr/bin/python

'''Runs a series of tests against the database to see if any of the following unidentified fragments are in there...'''


import music21

from music21.note import Note
from music21 import interval
from music21.lily import LilyString

from music21.trecento import cadencebook
from re import match

class IntervalSearcher(object):
    def __init__(self, intervalList = []):
        self.intervalList = intervalList
        self.intervalLength = len(intervalList)

    def compareToStream(self, stream):
        streamLength = len(stream.notes)
        if streamLength < self.intervalLength: return False
        intervalListLength = len(stream.intervalOverRestsList)
        if self.intervalLength > intervalListLength: return False
        #print "Length of Stream: " + str(streamLength)
        for i in range(0, intervalListLength+1 - self.intervalLength):
            for j in range(0, self.intervalLength):
                streamInterval = stream.intervalOverRestsList[i+j]
                genI1 = self.intervalList[j].diatonic.generic.simpleDirected
                genI2 = streamInterval.diatonic.generic.simpleDirected
                if genI1 != genI2:
                    break
            else:
                for colorNote in range(i, self.intervalLength):
                    ## does not exactly work because of rests, oh well
                    stream.notes[colorNote].editorial.color = "blue"
                return True
        return False

class NoteSearcher(object):
    '''Needs an exact list -- make sure no rests!'''
    def __init__(self, noteList = []):
        self.noteList = noteList
        self.noteLength = len(noteList)

    def compareToStream(self, stream):
        sN = stream.notes
        streamLength = len(sN)
        if streamLength < self.noteLength: return False
        for i in range(streamLength + 1 - self.noteLength):
            for j in range(self.noteLength):
                streamNote = sN[i+j]
                if self.noteList[j].isRest != streamNote.isRest:
                    break
                if streamNote.isNote and (self.noteList[j].step != streamNote.step):
                    break
            else:  ## success!
                for colorNote in range(i, self.noteLength):
                    sN[colorNote].editorial.color = "blue"
                return True
        return False

def searchForNotes(notesStr):
    '''the notesStr is a string of notes in the following form:
    "C4 D4 E4 B3 C4"
    that's it: name, octave. With no accidentals.  If octave is 0 then
    it means do not bother checking for octaves.
    
    Currently octave is ignored anyhow.
    '''
    notesArr = notesStr.split()
    noteObjArr = []
    for tN in notesArr:
        tNObj = Note()
        tNObj.name = tN[0]
        tNObj.octave = int(tN[1])
        noteObjArr.append(tNObj)
    ballataObj  = cadencebook.BallataSheet()
    searcher1 = NoteSearcher(noteObjArr) 
    streamLily = ""

    for thisWork in ballataObj:
        for thisCadence in thisWork.snippets:
            if (thisCadence is None or thisCadence.streams is None):
                continue
            for i in range(len(thisCadence.streams)):
                if searcher1.compareToStream(thisCadence.streams[i]) is True:
                    notesList = ""
                    for thisNote in thisCadence.streams[i].notes:
                        #thisNote.editorial.color = "blue"
                        if hasattr(thisNote.lily, "value"):
                            notesList += thisNote.lily.value + " "
                    streamLily += "\\score {" + \
                            "<< \\time " + str(thisCadence.timeSig) + \
                            "\n \\new Staff {" + str(thisCadence.streams[i].lily) + "} >>" + \
                            thisCadence.header() + "\n}\n"
                    print("In piece %r found in stream %d: %s" % (thisWork.title, i, notesList))
    if streamLily:
        lS = LilyString(streamLily)
        lS.showPNG()

def searchForIntervals(notesStr):
    '''notesStr is the same as above.  Now however we check to see
    if the generic intervals are the same, rather than the note names.
    Useful if the clef is missing.
    '''
    notesArr = notesStr.split()
    noteObjArr = []
    for tN in notesArr:
        tNObj = Note()
        tNObj.name = tN[0]
        tNObj.octave = int(tN[1])
        noteObjArr.append(tNObj)
    
    interObjArr = []
    for i in range(len(noteObjArr) - 1):
        int1 = interval.notesToInterval(noteObjArr[i], noteObjArr[i+1])
        interObjArr.append(int1)
    searcher1 = IntervalSearcher(interObjArr) 
    ballataObj  = cadencebook.BallataSheet()
    streamLily = ""

    for thisWork in ballataObj:
        for thisCadence in thisWork.snippets:
            if (thisCadence is None or thisCadence.streams is None):
                continue
            for i in range(len(thisCadence.streams)):
                if searcher1.compareToStream(thisCadence.streams[i]) is True:
                    notesList = ""
                    for thisNote in thisCadence.streams[i].notes:
                        notesList += thisNote.name + " "
                        #thisNote.editorial.color = "blue"
                    streamLily += "\\score {" + \
                            "<< \\time " + str(thisCadence.timeSig) + \
                            "\n \\new Staff {" + thisCadence.streams[i].lily + "} >>" + \
                            thisCadence.header() + "\n}\n"
                    print("In piece %r found in stream %d: %s" % (thisWork.title, i, notesList))

    if streamLily:
        print(streamLily)
        LilyString(streamLily).showPDF()

def findRandomVerona():
    searchForNotes("A4 F4 G4 E4 F4 G4")  #p. 4 cadence 1
    searchForNotes("F4 G4 A4 G4 A4 F4 G4 A4") #p. 4 incipit 2

def findCasanatense522():
    searchForIntervals("D4 E4 D4 C4 D4 E4 F4")

def findRavi3ORegina():
    searchForNotes("G16 G16 F8 E16") # should be cadence A, cantus


def searchForVat1969():
    '''There is a particular piece in Vatican MS 1969 that I have been searching for forever, its first
    ending concludes DED and second ending CDC, OR SOME TRANSPOSITION of these notes.  Find it!'''
    
    ballataObj = cadencebook.BallataSheet()
    for thisWork in ballataObj:
        cadB1 = thisWork.cadenceB1Class()
        cadB2 = thisWork.cadenceB2Class()
        if (cadB2 is None or cadB2.streams is None): continue
        if (cadB1 is None or cadB1.streams is None): continue
    for i in range(0, len(cadB2.streams)): 
        strB1 = cadB1.streams[i]
        strB2 = cadB2.streams[i]
        if len(strB1.notes) < 3 or len(strB2.notes) < 3:
            break
            if findUpDown(strB1.notes[-3], strB1.notes[-2], strB1.notes[-1]):
                if findUpDown(strB2.notes[-3], strB2.notes[-2], strB2.notes[-1]):
                    print(thisWork.title.encode('utf-8') + "   ",)
                    b1b2int = interval.Interval(note1 = strB1.notes[-1], note2 = strB2.notes[-1])
                    print(b1b2int.diatonic.generic.niceName)
                  
def findUpDown(n1, n2, n3):
    if n1.isRest or n2.isRest or n3.isRest: return False
    i1 = interval.Interval(note1 = n1, note2 = n2)
    if i1.diatonic.generic.simpleDirected != 2: return False
    i2 = interval.Interval(note1 = n2, note2 = n3)
    if i2.diatonic.generic.simpleDirected != -2: return False
    return True

if __name__ == "__main__":
#    searchForIntervals("E4 C4 C4 B3") # Assisi 187.1
#    searchForIntervals("D4 C4 C4 C4")   # Assisi 187.2
#    searchForIntervals("D4 A3 A3 A3 B3 C4") # Donna si to fallito TEST
#    searchForIntervals("F3 C3 C3 F3 G3") # Bologna Archivio: Per seguirla TEST
#    searchForNotes("D4 D4 C4 D4") # Fortuna Rira Seville 25 TEST! CANNOT FIND    
#    searchForNotes("D4 C4 B3 A3 G3") # Tenor de monaco so tucto Seville 25
#    searchForNotes("E4 D4 C4 B3 A3 B3 C4") # Benedicamus Domino Seville 25
#    searchForNotes("D4 E4 C4 D4 E4 D4 C4") # Benedicamus Domino Seville 25
######    searchForIntervals("A4 A4 G4 A4 G4 A4") # Reina f. 18r top. = QUAL NOVITA
#    searchForIntervals("G4 F4 F4 E4 E4 D4 D4 C4") # london 29987 88v C
     searchForIntervals("C4 B3 A3 A3 G3 G3 A3") # London 29987 88v T

#    landiniTonality()
#    findCasanatense522()
#    findRandomVerona()
#    findRavi3ORegina()
#    pass

