#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         keyDetectSketch.py
# Purpose:      Test module for future keyDetect functionality
#
# Authors:      Jared Sadoian
#
# Copyright:    (c) 2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import sys

import music21
from music21 import common
from music21 import converter
from music21 import corpus
from music21 import pitch
from music21.pitch import Pitch

from music21 import environment
_MOD = 'keyDetectSketch.py'
environLocal = environment.Environment(_MOD)

def runKeyFinder():
    
    ''' Initialize list values, 
    '''
    keyFinder = [6.35, 2.33, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
    
    pitchClassDist = [0]*12
    keyScores = [0]*12
    keySorted = [0]*12
    
    ''' Get work from corpus, extract part, and fill pitch class distribution table
    '''
    sStream = converter.parse(corpus.getWork('opus133.xml'))
    v2Part = sStream[1]
    pcGroup = [n.pitchClass for n in v2Part.pitches]
    for i in pcGroup:
        pitchClassDist[i] = pitchClassDist[i] + 1
    
    ''' this is the sample distribution used in the paper
    '''
    #pitchClassDist = [7,0,5,0,7,16,0,16,0,15,6,0]
    
    ''' run one iteration of shifting multiplication algorithm from paper
    '''
    for i in range(len(keyScores)):
        for j in range(len(pitchClassDist)):
            keyScores[i] = keyScores[i] + (pitchClassDist[(j+i)%12] * keyFinder[j])
    
    for i in range(len(keyScores)):
        keyScores[i] = round(keyScores[i])
    
    ''' Convert index of maximum to a letter 
    '''
    likelyKeys = [0]*12
    
    keySorted = sorted(keyScores)
    keySorted.reverse()
    
    for i in range(len(keySorted)):
        likelyKeys[i] = Pitch(keyScores.index(keySorted[i]))
    
    ''' Print relevant results to screen
    '''    
    print "Scores ordered by pitch class:", keyScores
    #print keySorted
    #print "Possible keys, from most likely to least likely", likelyKeys
    print "Key of piece:", likelyKeys[0], "(runners up", likelyKeys[1], "and", likelyKeys[2], ")"

if (__name__ == "__main__"):
    runKeyFinder()