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

from music21 import environment
_MOD = "analysis.metrical.py"
environLocal = environment.Environment(_MOD)




def labelBeatDepth(streamIn):
    '''
    Modify a Stream in place by annotating metrical analysis symbols.
    '''
    ts = streamIn.flat.getElementsByClass(
         music21.meter.TimeSignature)[0]
    
    ts.beat.partition(1)
    environLocal.printDebug(['ts numerator', ts.numerator])

    # use a fixed mapping for first divider; may be a good algo solution
    if ts.numerator in [2, 4, 8, 16, 32]:
        divFirst = 2
    elif ts.numerator in [3, 6, 9, 12, 15]:
        divFirst = 3
    else:
        divFirst = ts.numerator

    for h in range(len(ts.beat)): # this will return 1
        # this needs to be subdivided here by the LCM of the numerator
        ts.beat[h] = ts.beat[h].subdivide(divFirst)
        for i in range(len(ts.beat[h])):
            ts.beat[h][i] = \
                ts.beat[h][i].subdivide(2)
            for j in range(len(ts.beat[h][i])):
                ts.beat[h][i][j] = \
                    ts.beat[h][i][j].subdivide(2)
    
    for m in streamIn.getElementsByClass(music21.stream.Measure):
        for n in m.notes:
            
            if n.tie != None:
                environLocal.printDebug(['note, tie', n, n.tie, n.tie.type])
                if n.tie.type == 'stop':
                    continue
            for i in range(ts.getBeatDepth(n.offset)):
                n.addLyric('*')

    return streamIn