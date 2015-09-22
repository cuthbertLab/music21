# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         quodJactatur.py
# Purpose:      module for exploring the properties of QuodJactatur
#
# Author:       Michael Scott Cuthbert
#
# Copyright:    Copyright © 2010 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
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
from __future__ import print_function

from music21 import clef
#from music21 import common
from music21 import corpus
from music21 import exceptions21
from music21 import instrument
from music21 import interval
from music21 import key
from music21 import layout
from music21 import metadata
from music21 import meter
from music21 import note
from music21 import stream

import copy
import unittest

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
    This puts the clefs, TimeSignatures, etc. in their proper locations.  (THIS DOES NOT YET WORK)
    
    '''
    highestTime = self.highestTime
    
    if inPlace is True:
        returnObj = self 
        raise Exception("Whoops haven't written inPlace = True yet for reverse")
    else:
        returnObj = stream.Part()
    
    
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

def prependBlankMeasures(myStream, measuresToAppend = 1, inPlace = True):
    '''
    adds one (default) or more blank measures (filled with
    rests) to be beginning of myStream
    
    
    >>> from music21.alpha.trecento import quodJactatur
    >>> qj = quodJactatur.getQJ()
    >>> qj.duration.quarterLength
    70.0
    >>> qj.flat.notesAndRests[0]
    <music21.note.Note C>
    >>> len(qj.getElementsByClass(stream.Measure))
    35
    >>> qj2 = quodJactatur.prependBlankMeasures(qj, 10, inPlace = False)
    >>> qj2.duration.quarterLength
    90.0
    >>> qj2.flat.notesAndRests[0]
    <music21.note.Rest rest>
    >>> len(qj2.getElementsByClass(stream.Measure))
    45
    '''
    
    measureDuration = myStream.flat.getElementsByClass(meter.TimeSignature)[0].barDuration.quarterLength
    
    if inPlace == True:
        ms = myStream
    else:
        ms = copy.deepcopy(myStream)
    
    for dummy in range(measuresToAppend):
        qjBlankM = stream.Measure()
        hr = note.Rest()
        hr.duration.quarterLength = measureDuration
        qjBlankM.append(hr)
        ms.insertAndShift(0, qjBlankM)
    return ms


def transposeStreamDiatonic(myStream, diatonicInterval = 1):
    if diatonicInterval == 1:
        return myStream
#    genericInterval = interval.GenericInterval(diatonicNumber)
    
    for n in myStream.flat.notesAndRests:
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
    '''
    loads Quod Jactatur from the corpus, transposes it to
    an easy to view range and stores it in the cache.

    >>> from music21.alpha.trecento import quodJactatur
    >>> qj = quodJactatur.getQJ()
    >>> qj.flat.notesAndRests[0]
    <music21.note.Note C>
    '''
    
    qj = corpus.parse("ciconia/quod_jactatur")
    qjPart = qj.getElementsByClass(stream.Part)[0]
    qjPart.transpose("P-8", inPlace = True)
    qjPart.replace(qjPart.flat.getElementsByClass(clef.Clef)[0], clef.BassClef())
    cachedParts['1-0-False-False'] = copy.deepcopy(qjPart)
    return qjPart

def findRetrogradeVoices(show = True):
    '''
    the structure of the piece strongly suggests a retrograde solution
    (e.g., there is a cadence in m5 and five measures from the end and one
    at the exact center).  This method tries all transpositions of one
    voice vs. the other and gives positive points to intervals of 3, 4,
    5, 6, and 8 (incl. tritones, since they might be fixed w/ other voices;
    4th is included since there could be a 3rd or 5th below it).
    '''
    
    for transpose in [1, 2, -2, 3, -3, 4, -4]:
        for invert in [False, True]:
            qj1 = getQJ()
            qj2 = getQJ()
            if transpose != 1:
                transposeStreamDiatonic(qj2, transpose)            
            if invert is True:
                qj2.invertDiatonic(qj2.flat.notesAndRests[0], inPlace = True)
            qj2 = reverse(qj2, makeNotation = False)
            qj = stream.Score()
            qj.insert(0, qj2.flat)
            qj.insert(0, qj1.flat)
            qjChords = qj.chordify()
            consScore = 0
            totIntervals = 0
            for n in qjChords.flat.notesAndRests:
                strength = getStrengthForNote(n)
                if n.isRest is True or len(n.pitches) < 2:
                    thisScore = strength
                else:
                    int1 = interval.Interval(n.pitches[0], n.pitches[1])
                    #print int1.generic.simpleUndirected
                    if int1.generic.simpleUndirected in [1,3,4,5]:
                        thisScore = strength
                    elif int1.generic.simpleUndirected == 6: # less good
                        thisScore = strength/2.0
                    else:
                        thisScore = -2 * strength
                if n.duration.quarterLength < 2:
                    thisScore = thisScore * n.duration.quarterLength
                else:
                    thisScore = thisScore * 8
                consScore += thisScore
                totIntervals += 1
                n.lyric = str(thisScore)
            
            finalScore = int(100*(consScore + 0.0)/totIntervals)
            qj.insert(0, qjChords.flat)
            qj2.flat.notesAndRests[0].addLyric('Trans: ' + str(transpose))
            qj2.flat.notesAndRests[0].addLyric('Invert: ' + str(invert))
            qj1.flat.notesAndRests[0].addLyric('Score: ' + str(finalScore))
            
            if show == True:
                qj.show()
            else:
                if invert == True:
                    invStr = "Invert"
                else:
                    invStr = "      "
                print(str(transpose) + " " + invStr + " " + str(finalScore))
    
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
                qjPart.invertDiatonic(qjPart.flat.notesAndRests[0], inPlace = True)
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
        if not 'Chord' in n.classes: 
            continue
        if (startCounting is False or n.offset >= 70) and len(n.pitches) < 2:
            continue
        else:
            startCounting = True
        strength = getStrengthForNote(n)
              
        if n.isConsonant():
            thisScore = strength
        else:
            thisScore = -2 * strength
        
        consScore += thisScore
        totIntervals += 1
        n.lyric = str(thisScore)
                
    return (qjChords, (consScore/(totIntervals + 0.0)), qjSolved)
    
def getStrengthForNote(n):
    '''
    returns a number (4, 2, 0.5) depending on if the
    note is on a downbeat (4), a strong beat (2) or another beat (0.5)
    
    Used for weighing consonance vs. dissonance.
    
    For speed, it uses n.offset not n.beat; more general purpose
    solutions should use n.beat
    '''
        
    if (n.offset/2.0) == int(n.offset/2.0): # downbeat
        strength = 4
    elif (n.offset) == int(n.offset): # strong beat
        strength = 2
    else:
        strength = 0.5

    strength = strength * n.duration.quarterLength * 2
    return strength
    

def bentWolfSolution():
    getQJ()
    triplum = (5, 10, False, False)  # transpose, delay, invert, retro
    ct = (1, 5, False, False)
    tenor = (-5, 0, False, False)

    unused_qjChords, avgScore, fullScore = prepareSolution(triplum, ct, tenor)
    fullScore.show('musicxml')
    print(avgScore)
    print(cachedParts)
    
def possibleSolution():
    getQJ()

    triplum = (5, 5, False, False)  # transpose, delay, invert, retro
    ct = (5, 5, True, False)
    tenor = (1, 0, False, False)

#     # very good score and fits the description...
#     triplum = (5, 5, False, False)
#     ct = (5, 10, True, True)
#     tenor = (1, 0, False, False)
    
    
    unused_qjChords, avgScore, qjSolved = prepareSolution(tenor, triplum, ct)
    print(avgScore)
#    qjSolved.insert(0, stream.Part())
#    qjSolved.insert(0, qjChords)
    qjSolved.show('musicxml')
    #qjChords.show('musicxml')
 
def multipleSolve():
    import csv
    csvFile = csv.writer(open('d:/desktop/quodJ3.csv', 'wb'))

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
                                                    unused_qjSolved, avgScore, unused_fullScore = prepareSolution(triplum, ct, tenor)
                                                    #writeLine = (tripT, ctT, tenT, tripDelay, ctDelay, tenDelay, tripInvert, ctInvert, tenInvert, tripRetro, ctRetro, tenRetro, avgScore)
                                                    writeLine = (transHighest, delayHighest, highestInvert, highestRetro, transMiddle, delayMiddle, middleInvert, middleRetro, transLowest, delayLowest, lowestInvert, lowestRetro, avgScore)
                                                    if avgScore > 0:
                                                        print("")
                                                        if avgScore > maxScore:
                                                            maxScore = avgScore
                                                            print("***** ", end="")
                                                        print(writeLine)
                                                    else:
                                                        print(str(i) + " ", end="")
                                                    csvFile.writerow(writeLine)

class QuodJactaturException(exceptions21.Music21Exception):
    pass

class Test(unittest.TestCase):

    def runTest(self):
        pass



if __name__ == "__main__":
    import music21
    music21.mainTest()
#    bentWolfSolution()
#    possibleSolution()
#    findRetrogradeVoices()
    pass
#------------------------------------------------------------------------------
# eof

