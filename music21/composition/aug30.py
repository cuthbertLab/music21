#!/usr/bin/env python

'''aug30.py -- new composition on August 30

Short algorithmic composition in music21
'''

import sys, os

import music21
from music21 import note
from music21.note import Note
from music21.duration import Duration, DurationException
from music21 import stream
from music21 import expressions
from music21 import meter
from music21.lily import LilyString
import random

class QuarterNote(Duration):
    type = "quarter"

def rhythmLine(baseDuration = QuarterNote(), minLength = 8.0, maxProbability = 0.5):
    newStream = stream.Stream()
    while newStream.duration.quarterLength < minLength:
        currentProbability = (newStream.duration.quarterLength / minLength) * maxProbability
        newNote = Note()
        newNote.duration =  baseDuration.clone()

        x = random.random()
        while x < currentProbability:
            print(x, currentProbability)
            newNote.duration = alterRhythm(newNote.duration)
            x = random.random()
        newStream.append(newNote)
        #newStream.getNoteTimeInfo()
        
    return newStream

def alterRhythm(baseDuration = QuarterNote()):
    x = random.random()
    if x < .5:
        newDuration = addOrSubtractDot(baseDuration)
    else:
        newDuration = nextOrPreviousType(baseDuration)

    return newDuration

def addOrSubtractDot(baseDuration = QuarterNote()):
    newDuration = baseDuration.clone()
    if baseDuration.dots > 0:
        x = random.random()
        if x < .5:
            newDuration.dots = newDuration.dots - 1
        else:
            newDuration.dots = newDuration.dots + 1
    else:
        newDuration.dots = 1
        
    return newDuration

def nextOrPreviousType(baseDuration = QuarterNote()):
    newDuration = baseDuration.clone()
    ordinalType = baseDuration.ordinal
    x = random.random()
    if x < .5:
        ordinalType = ordinalType - 1
    else:
        ordinalType = ordinalType + 1
    
    newDuration.type = newDuration.ordinalTypeFromNum[ordinalType]
    return newDuration


def test():
    s1 = rhythmLine(minLength = 30, maxProbability = 0.7)
    ts1 = meter.TimeSignature("4/4")
    s1.applyTimeSignature(ts1)
    print(s1.lily)
    s1.sliceDurationsForMeasures(ts1)
    print(s1.lily)
    
if (__name__ == "__main__"):
    test()