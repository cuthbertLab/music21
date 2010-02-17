#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         keyDetectSketch.py
# Purpose:      Test module for future keyDetect functionality
#
# Authors:      Jared Sadoian
#
# Copyright:    (c) 2009 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import sys

import music21
from music21 import common
from music21 import converter
from music21 import corpus

from music21 import environment
_MOD = 'keyDetectSketch.py'
environLocal = environment.Environment(_MOD)


''' Initialize list values, 
'''
pitchClassTest = [0,0,0,0,0,0,0,0,0,0,0,0]
keyFinder = [6.35,2.33,3.48,2.33,4.38,4.09,2.52,5.19,2.39,3.66,2.29,2.88]
keyShifted = [0,0,0,0,0,0,0,0,0,0,0,0]

''' Get work from corpus, extract part, and fill pitch class distribution table
'''
sStream = converter.parse(corpus.getWork('opus133.xml'))
v2Part = sStream[1]
pcGroup = [n.pitchClass for n in v2Part.pitches]
for i in pcGroup:
    pitchClassTest[i] = pitchClassTest[i] + 1

''' this is the sample distribution used in the paper
'''
#pitchClassTest = [7,0,5,0,7,16,0,16,0,15,6,0]

''' run one iteration of shifting multiplication algorithm from paper
'''
for i in range(len(keyShifted)):
    for j in range(len(pitchClassTest)):
        keyShifted[i] = keyShifted[i] + (pitchClassTest[(j+i)%12] * keyFinder[j])

for i in range(len(keyShifted)):
    keyShifted[i] = round(keyShifted[i])
        
print keyShifted

''' Convert index of maximum to a letter 
'''
keyValue = keyShifted.index(max(keyShifted))
if keyValue == 0:
    print 'C'
if keyValue == 1:
    print 'C#, Db'
if keyValue == 2:
    print 'D'
if keyValue == 3:
    print 'D#, Eb'
if keyValue == 4:
    print 'E'
if keyValue == 5:
    print 'F'
if keyValue == 6:
    print 'F#, Gb'
if keyValue == 7:
    print 'G'
if keyValue == 8:
    print 'G#, Ab'
if keyValue == 9:
    print 'A'
if keyValue == 10:
    print 'A#, Bb'
if keyValue == 11:
    print 'B'