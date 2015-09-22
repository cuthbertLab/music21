#!/usr/bin/python
# -*- coding: utf-8 -*-
from music21 import converter, interval

def displayIntervals(file):
    """
    displayIntervals reads a music file and then displays it with an enumeration
    of the intervals above the lowest notes in the score at each sonority 
    (after chordification).
    """
    sJosquinPiece = converter.parse(file)
    #dissonant_intervals = ['m2','M2','M7','d5','m7','A4','P4']
    rJosquinPiece = sJosquinPiece.chordify()
    for c in rJosquinPiece.flat.getElementsByClass('Chord'):
        if len(c.pitches)==1:
            c.addLyric('P1',4)
        else:
            for j in range(len(c.pitches)-1,0,-1):
                p = c.pitches[j-1]
                i = interval.Interval(p, c.pitches[len(c.pitches)-1])
                notation = i.semiSimpleName
                c.addLyric(notation,j+3)
                if c.isConsonant() is False:                
                    c.addLyric('d',7)
                    if c.beatStrength >= .5:
                        c.addLyric('sbd',7)
    sJosquinPiece.insert(0,rJosquinPiece)
    sJosquinPiece.show()

#####################################################################################

if __name__ == "__main__":
    import os
    import sys
    
    basedir = "" # "/Users/Victoria/Desktop/"
    filename = "1202a-Missa_Sine_nomine-Kyrie.xml" #argv[1]
    if os.path.isfile(filename):
        displayIntervals(filename)
    elif os.path.isfile(basedir + filename):
        displayIntervals(basedir + filename)
    else:
        print("Cannot find file ", sys.argv[1])
        print("Usage: " + sys.argv[0] + " filename")

