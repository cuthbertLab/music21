# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         demos/trecento/largestAmbitus.py
# Purpose:      find Trecento/ars nova pieces with large ambitus
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
On September 11, 2012, Camilla Cavicchi reported to me the finding of
a new fragment in the Ferrara archives.  One unknown piece has an extraordinary
large range in the top voice: a 15th within a few notes.  The clefs can't 
be read and the piece is an adaptation into
Stroke notation, so it's unlikely to have an exact match in the database
(also the piece is probably from the 1430s [MSC, guess, not CC], so it's
not likely to be in the Trecento database anyhow).  

This demo uses the .analyze('ambitus') function of music21 to try
to find a match for the ambitus (or at least narrow down the search for others)
by finding all parts within pieces where the range is at least a 15th.
'''
from music21 import corpus, converter

def main():
    trecentoFiles = corpus.getWork('trecento')
    for t in trecentoFiles:
        print (t)
        tparsed = converter.parse(t)
        for p in tparsed.parts:
            ambi = p.analyze('ambitus')
            distance = ambi.diatonic.generic.undirected
            if distance >= 15:
                print ("************ GOT ONE!: {0} ************".format(ambi))
            elif distance >= 9:
                print (ambi)
            else:
                pass

#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = []


if __name__ == "__main__":
    main()

#------------------------------------------------------------------------------
# eof

