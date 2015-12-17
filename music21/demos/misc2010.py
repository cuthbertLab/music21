# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         misc2010.py
# Purpose:      demos from 2010
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2010 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------

from music21 import note, stream, corpus, converter, voiceLeading, pitch, chord
import copy

# def richardBreedGetWell():
#     '''
#     Richard Breed is a donor who supports the purchases of early music materials at M.I.T. --
#     I used this code as part of a get well card for him, it finds the name BREED in the Beethoven
#     quartets.  (well something close, B-rest-E-E-D returned nothing, so I instead did b-r-E-d, where
#     the e has to be long...)
# 
#     finds a few places in opus132 and nothing else
#     '''
#     for workName in corpus.getBeethovenStringQuartets('.xml'):
#         if 'opus132' not in workName:
#             continue
#         beethovenScore = converter.parse(workName)
#         for partNum in range(len(beethovenScore)):
#             print(workName, str(partNum))
#             thisPart = beethovenScore[partNum]
#             thisPart.title = workName + str(partNum)
#             display = stream.Stream()
#             notes = thisPart.flat.notesAndRests 
#             for i in range(len(notes) - 5):
#                 if (notes[i].isNote and notes[i].name == 'B') and \
#                     notes[i+1].isRest is True and \
#                    (notes[i+2].isNote and notes[i+2].name == 'E') and \
#                    (notes[i+3].isNote and notes[i+3].name == 'D') and \
#                    (notes[i+2].duration.quarterLength > notes[i].duration.quarterLength) and \
#                    (notes[i+2].duration.quarterLength > notes[i+1].duration.quarterLength) and \
#                    (notes[i+2].duration.quarterLength > notes[i+3].duration.quarterLength):
#                         
#                         measureNumber = 0
#                         lastMeasure = None
#                         for j in range(4):
#                             thisMeasure = notes[i+j].getContextByClass(stream.Measure)
#                             if thisMeasure is not None and thisMeasure is not lastMeasure:
#                                 lastMeasure = thisMeasure
#                                 measureNumber = thisMeasure.number
#                                 thisMeasure.insert(0, thisMeasure.bestClef())
#                                 display.append(thisMeasure)
#                         notes[i].lyric = workName + " " + str(thisPart.id) + " " + str(measureNumber)
# 
#             if len(display) > 0:
#                 display.show()

def annotateWithGerman():
    '''
    annotates a score with the German notes for each note
    '''
    bwv295 = corpus.parse('bach/bwv295')
    for thisNote in bwv295.flat.notes:
        thisNote.addLyric(thisNote.pitch.german)
    bwv295.show()


def bachParallels():
    '''
    find all instances of parallel fifths or octaves in Bach chorales.
    Checking the work of George Fitsioris and Darrell Conklin, 
    "Parallel successions of perfect fifths in the Bach chorales"
    Proceedings of the fourth Conference on Interdisciplinary Musicology (CIM08)
    Thessaloniki, Greece, 3-6 July 2008, http://web.auth.gr/cim08/
    '''
    for fn in corpus.chorales.Iterator(returnType='filename'):
        print(fn)
        c = corpus.parse(fn)
        displayMe = False
        for i in range(len(c.parts) - 1):
            iName = c.parts[i].id
            if iName.lower() not in ['soprano', 'alto', 'tenor', 'bass']:
                continue
            ifn = c.parts[i].flat.notesAndRests
            omi = ifn.offsetMap
            for j in range(i+1, len(c.parts)):
                jName = c.parts[j].id
                if jName.lower() not in ['soprano', 'alto', 'tenor', 'bass']:
                    continue

                jfn = c.parts[j].flat.notesAndRests
                for k in range(len(omi) - 1):
                    n1pi = omi[k]['element']
                    n2pi = omi[k+1]['element']                    
                    n1pj = jfn.getElementsByOffset(offsetStart = omi[k]['endTime'] - .001, offsetEnd = omi[k]['endTime'] - .001, mustBeginInSpan = False)[0]
                    n2pj = jfn.getElementsByOffset(offsetStart = omi[k+1]['offset'], offsetEnd = omi[k+1]['offset'], mustBeginInSpan = False)[0]
                    if n1pj is n2pj:
                        continue # no oblique motion
                    if n1pi.isRest or n2pi.isRest or n1pj.isRest or n2pj.isRest:
                        continue
                    if n1pi.isChord or n2pi.isChord or n1pj.isChord or n2pj.isChord:
                        continue

                    vlq = voiceLeading.VoiceLeadingQuartet(n1pi, n2pi, n1pj, n2pj)
                    if vlq.parallelMotion('P8') is False and vlq.parallelMotion('P5') is False:
                        continue
                    displayMe = True
                    n1pi.addLyric('par ' + str(vlq.vIntervals[0].name))
                    n2pi.addLyric(' w/ ' + jName)
#                    m1 = stream.Measure()
#                    m1.append(n1pi)
#                    m1.append(n2pi)
#                    r1 = note.Rest()
#                    r1.duration.quarterLength = 8 - m1.duration.quarterLength
#                    m1.append(r1)
#                    m2 = stream.Measure()
#                    m2.append(n1pj)
#                    m2.append(n2pj)
#                    r2 = note.Rest()
#                    r2.duration.quarterLength = 8 - m2.duration.quarterLength
#                    m2.append(r2)
#
#                    p1.append(m1)
#                    p2.append(m2)
                    
#        sc.append(p1)
#        sc.append(p2)
#        sc.show()
        if displayMe:
            c.show()
    
def towersOfHanoi(show = False, numParts = 6, transpose = False):
    '''
    generates a score solution to the Tower of Hanoi problem
    similar in spirit to the one that Tom Johnson made, but
    with any number of parts.  iterating over numParts(1...8) and
    setting transpose to False gives the same solution as 
    Tom Johnson found.
    '''
    sc = stream.Score()
    lowPitch = pitch.Pitch("C5")
    medPitch = pitch.Pitch("D5")
    highPitch = pitch.Pitch("E5")

    descendingPitches = [medPitch, lowPitch, highPitch]
    ascendingPitches = [lowPitch, medPitch, highPitch]

    if (numParts/2.0) == int(numParts/2.0):
        oddPitches = descendingPitches
        evenPitches = ascendingPitches
    else:
        oddPitches = ascendingPitches
        evenPitches = descendingPitches
    
    for i in range(1, numParts + 1):
        baseQuarterLength = 2**(i-2) # .5, 1, 2, 4, etc.
        firstNote = note.Note("E5")
        firstNote.quarterLength = baseQuarterLength

        if (i/2.0) == int(i/2.0):
            pitchCycle = copy.deepcopy(evenPitches)
        else:
            pitchCycle = copy.deepcopy(oddPitches)
        
        if transpose == True and i != 1:
            for pe in pitchCycle: # take down P4s
                pe.transpose(-5 * (i-1), inPlace = True)
            firstNote.transpose(-5 * (i-1), inPlace = True)

                
        
        p = stream.Part()
        p.id = "v. " + str(i)
        p.append(firstNote)
        pc = -1
        
        maxNumber = 2**(numParts-i)
        for j in range(maxNumber):
            pc += 1
            if pc > 2:
                pc = 0
            n = note.Note()
            n.duration.quarterLength = baseQuarterLength * 2
            n.pitch = pitchCycle[pc]
            if j == maxNumber - 1: # last note
                n.duration.quarterLength = (baseQuarterLength) + 3.0
            p.append(n)
        
        finalRest = note.Rest()
        finalRest.duration.quarterLength = 1
        p.append(finalRest)
        
        sc.insert(0, p)
    
    if show == True:
        sc.show()

def pcsFromHumdrum(show = False):
    '''
    show how music21 can read Humdrum code to append the forte name to
    each vertical simultaneity in a score.
    
    Asked by Fabio Kaiser on 12/8/2010
    '''
    from music21.humdrum import testFiles
    myScore = converter.parse(testFiles.mazurka6)
    onePartScore = myScore.chordify()
    output = ""
    for thisChord in onePartScore.flat.getElementsByClass(chord.Chord):
        output = output + thisChord.forteName + "\n"
    if show == True:
        print (output)
        


#-------------------------------------------------------------------------------
if (__name__ == "__main__"):
#    richardBreedGetWell()
#    annotateWithGerman()
#    countCs()
    bachParallels()
#    towersOfHanoi(show = False, transpose = False, numParts = 8)
#    pcsFromHumdrum(show = True)
#------------------------------------------------------------------------------
# eof

