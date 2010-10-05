from music21 import *
import copy

#-------------------------------------------------------------------------------
# Name:         quodJactatur.py
# Purpose:      module for exploring the properties of QuodJactatur
#
# Author:       Michael Scott Cuthbert
#
# Copyright:    (c) 2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

'''
Johannes Ciconia (ca. 1370-1412) was born in Liege, emigrated to Padua, and 
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



def reverse(self, inPlace = False, 
                classesToMove = (key.KeySignature, meter.TimeSignature, clef.Clef, metadata.Metadata, instrument.Instrument, layout.SystemLayout), 
                makeNotation = False,
                ):
        '''
        synonym: retrograde()
        
        reverse the order of stream members both in the .elements list but also by offset, so that the piece
        sounds properly backwards.  Automatically sorts the stream as well.  If inPlace is True (no by default)
        the elements are reversed in the current stream.  if inPlace is False then a new stream is returned.

        all elements of class classesToMove get moved to their current end locations before being reversed.  
        This puts the clefs, TimeSignatures, etc. in their proper locations.  DOES NOT YET WORK
        '''
        highestTime = self.highestTime

        returnObj = stream.Part()

        if inPlace is True:
            raise Exception("Whoops haven't written inPlace = True yet for reverse")

        currentContexts = common.defHash()
        sf = self.flat
        for myEl in sf:
            if isinstance(myEl, classesToMove):
                continue

            if myEl.duration is not None:
                releaseTime = myEl.getOffsetBySite(sf) + myEl.duration.quarterLength
            else:
                releaseTime = myEl.getOffsetBySite(sf) 
            newOffset = highestTime - releaseTime
            
#            for thisContext in classesToMove:
#                curCon = myEl.getContextByClass(thisContext)
#                if currentContexts[thisContext.__name__] is not curCon:
#                    returnObj.insert(newOffset, curCon)
#                    currentContexts[thisContext.__name__] = curCon
            returnObj.insert(newOffset, myEl)

            
        returnObj.insert(0, sf.getElementsByClass(layout.SystemLayout)[0])
        returnObj.insert(0, sf.getElementsByClass(clef.Clef)[0])
        returnObj.insert(0, sf.getElementsByClass(key.KeySignature)[0])
        returnObj.insert(0, sf.getElementsByClass(meter.TimeSignature)[0])
        returnObj.insert(0, sf.getElementsByClass(instrument.Instrument)[0])
        for thisP in returnObj.flat.pitches:
            if thisP.accidental is not None:
                thisP.accidental.displayStatus = None
 
        if makeNotation is True:
            return returnObj.makeNotation()
        else:
            return returnObj

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
            if n.step != 'B':
                n.pitch.accidental = None
            else:
                n.pitch.accidental = pitch.Accidental('flat')
                n.pitch.accidental.displayStatus = None
#            n.pitch.accidental = n.getContextByClass(key.KeySignature).accidentalByStep(n.pitch.step)
    return myStream

def transposeStreamDiatonic(myStream, diatonicInterval = 1):
    if diatonicInterval == 1:
        return myStream
#    genericInterval = interval.GenericInterval(diatonicNumber)
    
    for n in myStream.flat.notes:
        if n.isRest is False:
            if diatonicInterval >= 1:
                n.pitch.diatonicNoteNum += diatonicInterval - 1
            else:
                n.pitch.diatonicNoteNum += diatonicInterval + 1
            if n.pitch.step == 'B':
                n.pitch.name = 'B-'
            else:
                n.pitch.name = n.pitch.step
                n.pitch.accidental = None
                
#            n.pitch.accidental = n.getContextByClass(key.KeySignature).accidentalByStep(n.pitch.step)
    return myStream    


PERFCONS = ['P1', 'P5', 'P8']
IMPERFCONS = ['m3','M3','m6','M6']

cachedParts = {}

def getQJ():
    qj = corpus.parseWork("ciconia/quod_jactatur")
    qjPart = qj.getElementsByClass(stream.Part)[0]
    qjPart.transpose("P-8", inPlace = True)
    qjPart.replace(qjPart.flat.getElementsByClass(clef.Clef)[0], clef.BassClef())
    cachedParts['1-0-False-False'] = copy.deepcopy(qjPart)
    return qjPart

def prepareSolutionOld(triplumTup, ctTup, tenorTup):
    qjSolved = stream.Score()

    for transpose, delay, invert, retro in [triplumTup, ctTup, tenorTup]:
        idString = "%d-%d-%s-%s" % (transpose, delay, invert, retro)
        if idString in cachedParts:
            qjPart = copy.deepcopy(cachedParts[idString])
        else:
            qjPart = copy.deepcopy(cachedParts["1-0-False-False"])
            if retro is True:
                qjPart = reverse(qjPart, makeNotation = False)
            if invert is True:
                invertStreamAroundNote(qjPart, qjPart.flat.notes[0])
            if transpose != 1:
                transposeStreamDiatonic(qjPart, transpose)
            if delay > 0:
                qjPart = prependBlankMeasures(qjPart, delay)
            cachedParts[idString] = copy.deepcopy(qjPart)
        qjSolved.insert(0, qjPart)

    p = qjSolved.parts
    for i in range(len(p)):
        for j in range(len(p)):
            if i == j:
                continue
            

       
    qjTriplum = qjSolved.parts[0]
    qjCt = qjSolved.parts[1]
    qjTenor = qjSolved.parts[2] 
    qjT2 = copy.deepcopy(qjTriplum)
    qjT2.id = 'qjT2'

    qjTriplum.flat.attachIntervalsBetweenStreams(qjTenor.flat)
    qjCt.flat.attachIntervalsBetweenStreams(qjTenor.flat)
    qjT2.flat.attachIntervalsBetweenStreams(qjCt.flat)

    consScore = 0
    totIntervals = 1

    for thisSt in [qjTriplum, qjCt, qjT2]:
        thisStid = thisSt.id
        for n in thisSt.flat.notes:
            if "Rest" in n.classes: continue
            if n.editorial.harmonicInterval is None: continue
            if n.offset == int(n.offset):
                ssn = n.editorial.harmonicInterval.semiSimpleName
                
                thisScore = 0 
                if ssn in PERFCONS:
                    thisScore = 2
                elif ssn in IMPERFCONS:
                    thisScore = 1
                elif ssn == 'P4' and thisStid == 'qjT2':
                    thisScore = 1
                else:
                    thisScore = -4
                if (n.offset/2.0) == int(n.offset/2.0):
                    thisScore = thisScore * 2
                consScore += thisScore
                totIntervals += 1
                n.lyric = str(thisScore)
                n.editorial.harmonicInterval = None
                
    return (qjSolved, (consScore/(totIntervals + 0.0)))

def prepareSolution(triplumTup, ctTup, tenorTup):
    qjSolved = stream.Score()

    for transpose, delay, invert, retro in [triplumTup, ctTup, tenorTup]:
        idString = "%d-%d-%s-%s" % (transpose, delay, invert, retro)
        if idString in cachedParts:
            qjPart = copy.deepcopy(cachedParts[idString])
        else:
            qjPart = copy.deepcopy(cachedParts["1-0-False-False"])
            if retro is True:
                qjPart = reverse(qjPart, makeNotation = False)
            if invert is True:
                invertStreamAroundNote(qjPart, qjPart.flat.notes[0])
            if transpose != 1:
                transposeStreamDiatonic(qjPart, transpose)
            if delay > 0:
                qjPart = prependBlankMeasures(qjPart, delay)
            cachedParts[idString] = copy.deepcopy(qjPart)
        qjSolved.insert(0, qjPart.flat)

    #DOESN'T WORK -- am I doing something wrong?
    #for tp in qjSolved.parts:
    #    tp.makeMeasures(inPlace = True)
    qjChords = qjSolved.chordify()

    consScore = 0
    totIntervals = 1

    startCounting = False

    for n in qjChords.flat.notes:
        if not 'Chord' in n.classes: continue
        if (startCounting is False or n.offset >= 70) and len(n.pitches) < 2:
            continue
        else:
            startCounting = True
        if (n.offset/2.0) == int(n.offset/2.0): # downbeat
            strength = 4
        elif (n.offset) == int(n.offset): # strong beat
            strength = 2
        else:
            strength = 0.5
              
        if n.isConsonant():
            thisScore = strength
        else:
            thisScore = -2 * strength
        
        consScore += thisScore
        totIntervals += 1
        n.lyric = str(thisScore)
                
    return (qjChords, (consScore/(totIntervals + 0.0)), qjSolved)
    
    

def bentWolfSolution():
    getQJ()
    triplum = (5, 10, False, False)  # transpose, delay, invert, retro
    ct = (1, 5, False, False)
    tenor = (-5, 0, False, False)

    qjChords, avgScore, fullScore = prepareSolution(triplum, ct, tenor)
    fullScore.show('musicxml')
    print avgScore
    print cachedParts
    
def possibleSolution():
    getQJ()
    
    qjChords, avgScore, qjSolved = prepareSolution((1, 10, True, True), (-5, 0, False, False), (-5, 0, True, False))
    qjSolved.show('musicxml')
    qjChords.show('musicxml')
    print avgScore
    print cachedParts
 
def multipleSolve():
    import csv
    csvFile = csv.writer(open('d:/desktop/quodJ2.csv', 'wb'))

    getQJ()
    
    transposeIntervals = [-5, -4, 1, 4, 5]
    delayAmounts = [0, 5, 10]

    maxScore = -100
    i = 0
    for lowestTrans in range(len(transposeIntervals)):
     for middleTrans in range(lowestTrans, len(transposeIntervals)):
      for highestTrans in range(middleTrans, len(transposeIntervals)):
       transLowest = transposeIntervals[lowestTrans]
       transMiddle = transposeIntervals[middleTrans]
       transHighest = transposeIntervals[highestTrans]
       if transLowest != 1 and transMiddle != 1 and transHighest != 1:
           continue
       
       for delayLowest in delayAmounts:
        for delayMiddle in delayAmounts:
         for delayHighest in delayAmounts:
          if delayLowest != 0 and delayMiddle != 0 and delayHighest != 0:
              continue
          for lowestInvert in [False, True]:
           for middleInvert in [False, True]:
            for highestInvert in [False, True]:
             if lowestInvert is True and middleInvert is True and highestInvert is True:
                 continue  # very low probability
             for lowestRetro in [False, True]:
              for middleRetro in [False, True]:
               for highestRetro in [False, True]:
                if lowestRetro is True and middleRetro is True and highestRetro is True:
                    continue
                if ((delayLowest == delayMiddle and lowestInvert == middleInvert and lowestRetro == middleRetro) or
                    (delayLowest == delayHighest and lowestInvert == highestInvert and lowestRetro == highestRetro) or
                    (delayMiddle == delayHighest and middleInvert == highestInvert and middleRetro == highestRetro)):
                        continue # no continuous parallel motion            
                if (transLowest == transMiddle and delayLowest == delayMiddle and lowestRetro == False and middleRetro == True):
                    continue # same as lowestRetro == True and middleRetro == False
                if (transLowest == transMiddle and delayLowest == delayMiddle and lowestInvert == False and middleInvert == True):
                    continue # same as lowestInvert == True and middleInvert == False
                if (transLowest == 1 and transMiddle == 1):
                    continue # if transHighest == 4 then it's the same as (-4, -4, 1) except for a few tritones
                             # if transHighest == 5 then it's the same as (-5, -5, 1) except for a few tritones 
                
                
                i += 1
                triplum = (transHighest, delayHighest, highestInvert, highestRetro)
                ct = (transMiddle, delayMiddle, middleInvert, middleRetro)
                tenor = (transLowest, delayLowest, lowestInvert, lowestRetro)
                qjSolved, avgScore, fullScore = prepareSolution(triplum, ct, tenor)
                #writeLine = (tripT, ctT, tenT, tripDelay, ctDelay, tenDelay, tripInvert, ctInvert, tenInvert, tripRetro, ctRetro, tenRetro, avgScore)
                writeLine = (transHighest, delayHighest, highestInvert, highestRetro, transMiddle, delayMiddle, middleInvert, middleRetro, transLowest, delayLowest, lowestInvert, lowestRetro, avgScore)
                if avgScore > 0:
                    print ""
                    if avgScore > maxScore:
                        maxScore = avgScore
                        print "***** ",
                    print writeLine
                else:
                    print str(i) + " ",
                csvFile.writerow(writeLine)

if __name__ == "__main__":
    pass
    #multipleSolve()
    #bentWolfSolution()
    possibleSolution()