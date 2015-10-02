#!/usr/bin/python
# -*- coding: utf-8 -*-

'''Runs a series of tests against the database to see if any of the following unidentified fragments are in there...'''


from music21 import metadata
from music21 import interval
from music21 import note
from music21 import stream

from music21.alpha.trecento import cadencebook

class IntervalSearcher(object):
    def __init__(self, intervalList = []):
        self.intervalList = intervalList
        self.intervalLength = len(intervalList)

    def compareToStream(self, cmpStream):
        streamLength = len(cmpStream.flat.notesAndRests)
        if self.intervalLength > streamLength: 
            return False
        stIntervalList = cmpStream.melodicIntervals(skipRests = True)
        if stIntervalList is None:
            return False
        stIntervalListLength = len(stIntervalList)
        if self.intervalLength > stIntervalListLength: 
            return False
        #print "Length of Stream: " + str(streamLength)
        for i in range(0, stIntervalListLength+1 - self.intervalLength):
            for j in range(0, self.intervalLength):
                streamInterval = stIntervalList[i+j]
                genI1 = self.intervalList[j].diatonic.generic.simpleDirected
                genI2 = streamInterval.diatonic.generic.simpleDirected
                if genI1 != genI2:
                    break
            else:
                for colorNote in range(i, i + self.intervalLength):
                    ## does not exactly work because of rests, oh well
                    cmpStream.notesAndRests[colorNote].editorial.color = "blue"
                return True
        return False

class NoteSearcher(object):
    '''Needs an exact list -- make sure no rests!'''
    def __init__(self, noteList = []):
        self.noteList = noteList
        self.noteLength = len(noteList)

    def compareToStream(self, cmpStream):
        sN = cmpStream.notesAndRests
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
        tNName = tN[0]
        if tNName.lower() != "r":
            tNObj = note.Note()
            tNObj.name = tN[0]
            tNObj.octave = int(tN[1])
        else:
            tNObj = note.Rest()
        noteObjArr.append(tNObj)
    ballataObj  = cadencebook.BallataSheet()
    searcher1 = NoteSearcher(noteObjArr) 
    streamOpus = stream.Opus()

    for thisWork in ballataObj:
        for thisCadence in thisWork.snippets:
            if thisCadence is None:
                continue
            for i in range(len(thisCadence.parts)):
                if searcher1.compareToStream(thisCadence.parts[i].flat) is True:
                    notesStr = ""
                    for thisNote in thisCadence.parts[i].flat.notesAndRests:
                        #thisNote.editorial.color = "blue"
                        if thisNote.isRest is False:
                            notesStr += thisNote.nameWithOctave + " "
                        else:
                            notesStr += "r "
                    streamOpus.insert(0, thisCadence)
#                    streamLily += "\\score {" + \
#                            "<< \\time " + str(thisCadence.timeSig) + \
#                            "\n \\new Staff {" + str(thisCadence.parts[i].lily) + "} >>" + \
#                            thisCadence.header() + "\n}\n"
                    print(u"In piece %r found in stream %d: %s" % (thisWork.title, i, notesStr))
    if any(streamOpus):
        streamOpus.show('lily.png')

def searchForIntervals(notesStr):
    '''
    notesStr is the same as above.  Now however we check to see
    if the generic intervals are the same, rather than the note names.
    Useful if the clef is missing.
    '''
    notesArr = notesStr.split()
    noteObjArr = []
    for tN in notesArr:
        tNObj = note.Note()
        tNObj.name = tN[0]
        tNObj.octave = int(tN[1])
        noteObjArr.append(tNObj)
    
    interObjArr = []
    for i in range(len(noteObjArr) - 1):
        int1 = interval.notesToInterval(noteObjArr[i], noteObjArr[i+1])
        interObjArr.append(int1)
    #print interObjArr

    searcher1 = IntervalSearcher(interObjArr) 
    ballataObj  = cadencebook.BallataSheet()

    streamOpus = stream.Opus()

    for thisWork in ballataObj:
        print(thisWork.title)
        for thisCadence in thisWork.snippets:
            if thisCadence is None:
                continue
            for i in range(len(thisCadence.parts)):
                if searcher1.compareToStream(thisCadence.parts[i].flat) is True:
                    notesStr = ""
                    for thisNote in thisCadence.parts[i].flat.notesAndRests:
                        #thisNote.editorial.color = "blue"
                        if thisNote.isRest is False:
                            notesStr += thisNote.nameWithOctave + " "
                        else:
                            notesStr += "r "
                    streamOpus.insert(0, thisCadence)
#                    streamLily += "\\score {" + \
#                            "<< \\time " + str(thisCadence.timeSig) + \
#                            "\n \\new Staff {" + str(thisCadence.parts[i].lily) + "} >>" + \
#                            thisCadence.header() + "\n}\n"
                    print(u"In piece %r found in stream %d: %s" % (thisWork.title, i, notesStr))
    if any(streamOpus):
        streamOpus.show('lily.png')

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
        if (cadB2 is None or len(cadB2.parts) == 0): continue
        if (cadB1 is None or len(cadB1.parts) == 0): continue
    for i in range(0, len(cadB2.parts)): 
        strB1 = cadB1.parts[i].flat
        strB2 = cadB2.parts[i].flat
        if len(strB1.notesAndRests) < 3 or len(strB2.notesAndRests) < 3:
            break
            if findUpDown(strB1.notesAndRests[-3], strB1.notesAndRests[-2], strB1.notesAndRests[-1]):
                if findUpDown(strB2.notesAndRests[-3], strB2.notesAndRests[-2], strB2.notesAndRests[-1]):
                    print(thisWork.title.encode('utf-8') + "   ",)
                    b1b2int = interval.Interval(note1 = strB1.notesAndRests[-1], note2 = strB2.notesAndRests[-1])
                    print(b1b2int.diatonic.generic.niceName)
                  
def findUpDown(n1, n2, n3):
    if n1.isRest or n2.isRest or n3.isRest: return False
    i1 = interval.Interval(note1 = n1, note2 = n2)
    if i1.diatonic.generic.simpleDirected != 2: return False
    i2 = interval.Interval(note1 = n2, note2 = n3)
    if i2.diatonic.generic.simpleDirected != -2: return False
    return True

def audioVirelaiSearch():
    #from music21 import audioSearch
    from music21.audioSearch import transcriber
    from music21 import search
    virelaisSheet = cadencebook.TrecentoSheet(sheetname = 'virelais')
    
    virelaiCantuses = []
    for i in range(2, 54):
        thisVirelai = virelaisSheet.makeWork(i)
        if thisVirelai.title != "":
            try:
                vc = thisVirelai.incipit.getElementsByClass('Part')[0]
                vc.insert(0, metadata.Metadata(title = thisVirelai.title))
                virelaiCantuses.append(vc)
            except IndexError:
                pass
    searchScore = transcriber.runTranscribe(show = False, plot = False, seconds = 10.0, saveFile = False)
    #from music21 import converter
    #searchScore = converter.parse("c'4 a8 a4 g8 b4. d'4. c8 b a g f4", '6/8')
    #searchScore.show()
    l = search.approximateNoteSearch(searchScore, virelaiCantuses)
    for i in l:
        print(i.metadata.title, i.matchProbability)
    l[0].show()

def findSimilarGloriaParts():
    '''
    Looks in the list of Gloria incipits, cadences, etc. and tries to find ones which are very similar
    to each other.
    '''
    pass


def savedSearches():
#    searchForIntervals("E4 C4 C4 B3") # Assisi 187.1
#    searchForIntervals("D4 C4 C4 C4")   # Assisi 187.2
#    searchForIntervals("D4 A3 A3 A3 B3 C4") # Donna si to fallito TEST
#    searchForNotes("G3 D3 R D3 D3 E3 F3") # Donna si to fallito TEST - last note = F#
#    searchForIntervals("F3 C3 C3 F3 G3") # Bologna Archivio: Per seguirla TEST
#    searchForNotes("F3 E3 F3 G3 F3 E3")  # Mons archive fragment -- see FB Aetas Aurea post
    searchForNotes("F4 G4 F4 B4 G4 A4 G4 F4 E4") # or B-4.  Paris 25406 -- Dominique Gatte pen tests  

#    searchForNotes("D4 D4 C4 D4") # Fortuna Rira Seville 25 TEST! CANNOT FIND    
#    searchForNotes("D4 C4 B3 A3 G3") # Tenor de monaco so tucto Seville 25
#    searchForNotes("E4 D4 C4 B3 A3 B3 C4") # Benedicamus Domino Seville 25
#    searchForNotes("D4 E4 C4 D4 E4 D4 C4") # Benedicamus Domino Seville 25
######    searchForIntervals("A4 A4 G4 A4 G4 A4") # Reina f. 18r top. = QUAL NOVITA
#    searchForIntervals("G4 F4 F4 E4 E4 D4 D4 C4") # london 29987 88v C
#    searchForIntervals("C4 B3 A3 A3 G3 G3 A3") # London 29987 88v T
    #searchForNotes("G3 E3 F3 G3 F3 E3 D3 C3")  # probable French piece, Nuremberg 9, but worth a check    
#    searchForIntervals("A4 A4 G4 G4 F4 E4") # Nuremberg 9a, staff 6 probable French Piece
#    findCasanatense522()
#    findRandomVerona()
#    findRavi3ORegina()
    #searchForIntervals("D4 B4 D4 C4 D4") # cadence formula from 15th c. that Lisa Cotton was searching for in earlier sources -- none found
    #searchForIntervals("G4 A4 G4 F4 E4 F4 G4 E4") # Prague XVII.J.17-14_1r piece 1 -- possible contrafact -- no correct matches
    #searchForIntervals("G4 A4 B4 G4 F4 G4 F4 E4") # Prague XVII.J.17-14_1r piece 2 -- possible contrafact -- no matches
    #searchForIntervals("F4 A4 F4 G4 F4 G4 A4") # Duke white notation manuscript 

if __name__ == "__main__":
    savedSearches()
    #audioVirelaiSearch()



#------------------------------------------------------------------------------
# eof

