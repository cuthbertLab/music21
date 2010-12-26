#!/usr/bin/env python

'''
aug30.py -- Short algorithmic composition demo in music21

written on August 30, 2008
converted to new system on Dec. 26, 2010
'''

import music21
from music21 import *
from music21.instrument import *
import copy
import random

def rhythmLine(baseNote = note.QuarterNote(), minLength = 8.0, maxProbability = 0.5):
    newStream = stream.Part()
    while newStream.duration.quarterLength < minLength:
        currentProbability = (newStream.duration.quarterLength / minLength) * maxProbability
        newNote = copy.deepcopy(baseNote)

        x = random.random()
        while x < currentProbability:
#            print(x, currentProbability)
            newNote.duration = alterRhythm(newNote.duration)
            currentProbability *= .75
            x = random.random()

        y = random.random()
        z = random.random()
        
        if z < 0.5:
            direction = 1
        else:
            direction = -1
        while y < currentProbability:
#            print(x, currentProbability)
            newNote.ps += direction
            currentProbability *= .75
            y = random.random()

        
        newNote.articulations.append(articulations.Staccatissimo())
        newStream.append(newNote)
        #newStream.getNoteTimeInfo()
        
    return newStream

def alterRhythm(baseDuration):
    x = random.random()
    if x < .5:
        newDuration = addOrSubtractDot(baseDuration)
    else:
        newDuration = nextOrPreviousType(baseDuration)

    return newDuration

def addOrSubtractDot(baseDuration):
    newDuration = copy.deepcopy(baseDuration)
    if baseDuration.dots > 0:
        x = random.random()
        if x < .5:
            newDuration.dots = newDuration.dots - 1
        else:
            newDuration.dots = newDuration.dots + 1
    else:
        newDuration.dots = 1
        
    return newDuration

def nextOrPreviousType(baseDuration):
    newDuration = copy.deepcopy(baseDuration)
    ordinalType = baseDuration.ordinal
    x = random.random()
    if x < .5:
        ordinalType = ordinalType - 1
    else:
        ordinalType = ordinalType + 1
    
    newDuration.type = duration.ordinalTypeFromNum[ordinalType]
    return newDuration

def addPart(minLength = 80, maxProbability = 0.7, instrument = None):
    s1 = rhythmLine(minLength = minLength, maxProbability = maxProbability)
    ts1 = meter.TimeSignature("4/4")
    s1.insert(0, ts1)
    s1.insert(0, tempo.MetronomeMark(number = 180, value = "very fast"))
    if instrument is not None:
        s1.insert(0, instrument)
    s1.makeAccidentals()
    s1.makeMeasures(inPlace = True)
    for n in s1.flat.notes:
        if n.tie is not None and n.tie.type != 'start':
            n.__class__ = note.Rest
    
    return s1
    

def test():
    sc1 = stream.Score()
#    instruments = [Piccolo(), Glockenspiel(), 72, 69, 41, 27, 47, 1, 1, 1, 1, 34]
    instrument = [Piccolo(),Xylophone(),Clarinet(),Oboe(),Violin(),ElectricGuitar(),Harp(),Piano(),Piano(),Piano(),Piano(),ElectricBass()]
    instrumentOctave = [3, 2, 2, 2, 1, 1, 1, 2, 1, 0, -1, -2]
    
    for i in range(12):
        inst = instrument[i]
        if i < 9:
            inst.midiChannel = i
        else:
            inst.midiChannel = i+1
        part = addPart(instrument = inst)
        if instrumentOctave[i] != 0:
            part.transpose(12 * instrumentOctave[i], inPlace = True)
        sc1.insert(0, part)
    sc1.show()
    
if (__name__ == "__main__"):
    test()

#------------------------------------------------------------------------------
# eof

