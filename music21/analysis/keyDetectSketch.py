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

def runKeyFinder(a):
    ''' Takes in windows size as argument to run key detection
    '''
    
    
    ''' Get work from corpus, extract part, and fill pitch class distribution table
    '''
    sStream = converter.parse(corpus.getWork('opus133.xml'))
    #v2Part = sStream[1]
    #pcGroup = [n.pitchClass for n in v2Part.pitches]
    v2Part = sStream[1].measures
    
    ''' Run key detection over all possible "half-piece" segments
    '''
    for i in range(len(v2Part)-(len(v2Part)/a)):
        pitchClassDist = [0]*12
        pcGroup = [n.pitchClass for n in v2Part[(0+i):((len(v2Part)/a)+i)].pitches]
        for j in pcGroup:
            pitchClassDist[j] = pitchClassDist[j] + 1
        print "pass", i
        keyDetect(pitchClassDist)


def keyDetect(a):    
    ''' Takes in a pitch class distribution and algorithmically detects
        probable keys using convoluteKey() and getLikelyKeys()
    '''
    
    # this is the sample distribution used in the paper, for some testing purposes
    #pitchClassDist = [7,0,5,0,7,16,0,16,0,15,6,0]
    
    keyResults = convoluteKey(a)   
    likelyKeys = getLikelyKeys(keyResults)
        
    #print "Key probabilities ordered by pitch class:", keyResults
    #print keySorted
    #print "Possible keys, from most likely to least likely", likelyKeys
    print "Key of analyzed segment:", likelyKeys[0], "(runners up", likelyKeys[1], "and", likelyKeys[2], ")"


def convoluteKey(a):
    ''' Takes in a pitch class distribution as a list and convolutes it
        over Sapp's given distribution for finding key, returning the result. 
    '''
    keyFinder = [6.35, 2.33, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
    b = [0]*12
    
    for i in range(len(b)):
        for j in range(len(a)):
            b[i] = b[i] + (a[(j+i)%12] * keyFinder[j])
    
    for i in range(len(b)):
        b[i] = round(b[i])
        
    return b

def getLikelyKeys(a):
    ''' Takes in a list of probably key results in points and returns a
        list of keys in letters, sorted from most likely to least likely
    '''
    likelyKeys = [0]*12
    #keySorted = [0]*12
    b = sorted(a)
    b.reverse()
    
    for i in range(len(b)):
        likelyKeys[i] = Pitch(a.index(b[i]))
    
    return likelyKeys

if (__name__ == "__main__"):
    runKeyFinder(20)