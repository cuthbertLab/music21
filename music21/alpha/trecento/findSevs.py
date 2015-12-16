# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         trecento/findSevs.py
# Purpose:      methods for finding all sevenths (which might be coding errors) in
#               the cadence books
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2007, 2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------

_DOC_IGNORE_MODULE_OR_PACKAGE = True


from music21.alpha.trecento import cadencebook
#this is a terrible way of doing this...
from music21 import stream


def find(startRow=2, endRow=469, searchInterval=7):
    opus = stream.Opus()
    ballatas = cadencebook.BallataSheet()
    for row in range(startRow, endRow):
        ballata = ballatas.makeWork(row)
        if findInWork(ballata, searchInterval):                
            print(ballata.title + ' has a generic interval of %d somewhere' % searchInterval)
            opus.insert(0, ballata.asScore())
    if any(opus):
        opus.show('lily.pdf')

def findInWork(work, searchInterval = 7):
    ballata = work
    streams = ballata.getAllStreams()
    containsInterval = False
    for astream in streams:
        intervals = astream.flat.melodicIntervals(skipRests = True)
        #genints = []
        for thisInterval in intervals:
            if thisInterval is not None:
                #genints.append(thisInterval.generic)
                if thisInterval.generic.undirected == searchInterval:
                    containsInterval = True
#                    try:
                    thisInterval.noteStart.editorial.color = 'blue'
                    thisInterval.noteEnd.editorial.color = 'blue'
#                    except:
#                        pass # not worth dying if the startNote can't be found
                    #print(thisInterval.note1.nameWithOctave + ' -- ' + 
                    #    thisInterval.note2.nameWithOctave)
                    #interval.note1.editorial.color = "blue" #this doesn't actually work yet....
                    #interval.note2.editorial.color = "blue"
    return containsInterval

if __name__ == "__main__":
    find(2,459,7)

#------------------------------------------------------------------------------
# eof

