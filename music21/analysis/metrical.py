#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         metrical.py
# Purpose:      Tools for metrical analysis
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    (c) 2009-2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
import music21.stream
import music21.meter

def labelBeatDepth(streamIn):
    ts = streamIn.flat.getElementsByClass(
         music21.meter.TimeSignature)[0]
    
    ts.beat.partition(1)
    for h in range(len(ts.beat)):
        ts.beat[h] = ts.beat[h].subdivide(2)
        for i in range(len(ts.beat[h])):
            ts.beat[h][i] = \
                ts.beat[h][i].subdivide(2)
            for j in range(len(ts.beat[h][i])):
                ts.beat[h][i][j] = \
                    ts.beat[h][i][j].subdivide(2)
    
    for m in streamIn.getElementsByClass(music21.stream.Measure):
        for n in m.notes:
            for i in range(ts.getBeatDepth(n.offset)):
                n.addLyric('*')

    return streamIn