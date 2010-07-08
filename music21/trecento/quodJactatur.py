from music21 import *
import copy

#-------------------------------------------------------------------------------
# Name:         quodJactatur.py
# Purpose:      module for exploring the properties of QuodJactatur
#
# Author:      Michael Scott Cuthbert
#
# Copyright:    (c) 2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

'''
Johannes Ciconia (ca. 1370-1412), born in Liege, emigrated to Padua, and 
was one of Italy's most important composers in the early fifteenth century.
Ciconia left us with two canons with enigmatic properties, Le Ray au Soylel,
first successfully transcribed by Margaret Bent and Anne Hallmark in
Polyphonic Music of the Fourteenth Century, vol. 24, and Quod Jactatur.

Quod Jactatur has never been successfully transcribed.  Its canon,
"Tenor quem contratenor triplumque fugant temporibus in quinque" and
text "Quod Jactatur qui virtus opere non demonstratur / Ut aqua pissis 
sepius scientia dejugatur" (not "denegatur") together with the given clefs suggest a 
resolution in fifths, five breves apart.  But none of the transcriptions
have seemed successful.  Previous scholars seemed to neglect two important
aspects of the composition.  First that important resting points happen 5
measures from the beginning of the piece, 5 measures from the end of the
piece, and at the exact middle: strongly suggesting a retrograde solution
where two voices enter at the same time (as the top two voices do in
Machaut's "Ma fin est mon comencement").  Second, that the three clefs 
are not C5, C3, C1, but C3 followed by C1 and C5 written directly 
above each other -- the importance of this
ordering can be seen by closely looking at the manuscript, Modena,
Biblioteca Estense, Alpha.5.24, fol. 20v (old fol. 21v), edited recently
by Anne Stone.  The clefs were originally written as C5 followed by
C3 followed by C1, but the scribe erased the first two scribes and
rewrote them in the correct order.  (The C5 clef was also written as C4 first
but changed to C5 later)

Solving this canon seemed a great use of music21, since we could
try out different solutions, moving notes over a measure or two, etc.
without any problems.  Working on this problem also gave a great test
of music21's ability to manipulate diatonic Streams.
'''




def reverse(self, inPlace = False, recursive = True, 
                classesToMove = (key.KeySignature, meter.TimeSignature, clef.Clef, metadata.Metadata, instrument.Instrument) ):
        '''
        synonym: retrograde()
        
        reverse the order of stream members both in the .elements list but also by offset, so that the piece
        sounds properly backwards.  Automatically sorts the stream as well.  If inPlace is True (yes by default)
        the elements are reversed in the current stream.  if inPlace is False then a new stream is returned.

        all elements of class classesToMove get moved to
        '''
        highestTime = self.highestTime

        returnObj = stream.Part()

        currentContexts = common.defHash()
        sf = self.flat
        for myEl in sf:
            if isinstance(myEl, classesToMove):
                continue

            releaseTime = myEl.getOffsetBySite(sf) + myEl.duration.quarterLength
            newOffset = highestTime - releaseTime
            
#            for thisContext in classesToMove:
#                curCon = myEl.getContextByClass(thisContext)
#                if currentContexts[thisContext.__name__] is not curCon:
#                    returnObj.insert(newOffset, curCon)
#                    currentContexts[thisContext.__name__] = curCon
                    
            returnObj.insert(newOffset, myEl)
 
        returnObj.insert(0, sf.getElementsByClass(clef.Clef)[0])
        returnObj.insert(0, sf.getElementsByClass(key.KeySignature)[0])
        returnObj.insert(0, sf.getElementsByClass(meter.TimeSignature)[0])
        returnObj.insert(0, sf.getElementsByClass(instrument.Instrument)[0])
        ros = returnObj.sorted
        ros2 = ros.makeMeasures()
        return ros2.makeBeams()

def prependBlankMeasures(myStream, measuresToAppend = 1):
    for i in range(measuresToAppend):
        qjBlankM = stream.Measure()
        hr = note.Rest()
        hr.duration.quarterLength = 2
        qjBlankM.append(hr)
        myStream.insertAndShift(0, qjBlankM)
    return myStream.sorted

def invertStreamAroundNote(myStream, inversionNote = note.Note() ):
    inversionDNN = inversionNote.diatonicNoteNum
    for n in myStream.flat.notes:
        if n.isRest is False:
            n.pitch.diatonicNoteNum = (2*inversionDNN) - n.pitch.diatonicNoteNum
#            n.pitch.accidental = n.getContextByClass(key.KeySignature).accidentalByStep(n.pitch.step)
    return myStream

def transposeStreamDiatonic(myStream, diatonicInterval = 1):
    for n in myStream.flat.notes:
        if n.isRest is False:
            if diatonicInterval >= 1:
                n.pitch.diatonicNoteNum += diatonicInterval - 1                
            else:
                n.pitch.diatonicNoteNum += diatonicInterval + 1
#            n.pitch.accidental = n.getContextByClass(key.KeySignature).accidentalByStep(n.pitch.step)
    return myStream    

def bentWolfSolution():
    qj = corpus.parseWork("ciconia/quod_jactatur")
    qjPart = qj.getElementsByClass(stream.Part)[0]
    qjPart.replace(qjPart.flat.getElementsByClass(clef.Clef)[0], clef.BassClef())
    
    qjSolved = stream.Score()
    
    qjTriplum = copy.deepcopy(qjPart)
    qjCt      = copy.deepcopy(qjPart)
    qjTenor   = copy.deepcopy(qjPart)
    
#   qjCtR = reverse(qjCt)
    
    transposeStreamDiatonic(qjTenor, -12)
    transposeStreamDiatonic(qjCt, -8)
    transposeStreamDiatonic(qjTriplum, -4)

#    invertStreamAroundNote(qjCtR, note.Note("A2"))
    
    qjTriplum = prependBlankMeasures(qjTriplum, 10)
    qjCt     = prependBlankMeasures(qjCt, 5)
    
    qjSolved.insert(0, qjTriplum)
    qjSolved.insert(0, qjCt)
    qjSolved.insert(0, qjTenor)
    
    qjSolved.show('musicxml')
    
def cuthZazSolution():    
    qj = corpus.parseWork("ciconia/quod_jactatur")
    qjPart = qj.getElementsByClass(stream.Part)[0]
    qjPart.replace(qjPart.flat.getElementsByClass(clef.Clef)[0], clef.BassClef())
    
    qjSolved = stream.Score()
    
    qjTriplum = copy.deepcopy(qjPart)
    qjCt      = copy.deepcopy(qjPart)
    qjTenor   = copy.deepcopy(qjPart)
    
    qjCtR = reverse(qjCt)
#    qjCtR = qjCt
    
#    transposeStreamDiatonic(qjTenor, 1)
    transposeStreamDiatonic(qjTriplum, 5)
    transposeStreamDiatonic(qjCtR, -2)
#    invertStreamAroundNote(qjCtR, qjCtR.flat.notes[0])
    
    qjTriplum = prependBlankMeasures(qjTriplum, 5)
    qjCtR     = prependBlankMeasures(qjCtR, 3)
    
    qjSolved.insert(0, qjTriplum)
    qjSolved.insert(0, qjCtR)
    qjSolved.insert(0, qjTenor)
 
    for i in qjSolved.flat.notes:
        if i.isRest is False:
            if i.step == 'B':
                i.accidental = pitch.Accidental('flat')
            else:
                i.accidental = None
    
    qjSolved.show('musicxml')
    print qjSolved.write('musicxml')

#bentWolfSolution()
cuthZazSolution()