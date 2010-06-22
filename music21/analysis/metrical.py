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
'''Various tools and utilities for doing metrical or rhythmic analysis. 

See the chapter :ref:`overviewMeters` for more information on defining metrical structures in music21.
'''


import music21.stream
import music21.meter
import unittest, doctest


from music21 import environment
_MOD = "analysis.metrical.py"
environLocal = environment.Environment(_MOD)




def labelBeatDepth(streamIn):
    '''
    Modify a Stream in place by annotating metrical analysis symbols.

    This assumes that the Stream is already partitioned into Measures.
    '''
#     ts = streamIn.flat.getElementsByClass(
#          music21.meter.TimeSignature)[0]
    

    
    for m in streamIn.getElementsByClass(music21.stream.Measure):

        # this will search contexts
        ts = m.getTimeSignatures(sortByCreationTime=False)[0]


        ts.beat.partition(1)
        environLocal.printDebug(['ts numerator', ts.numerator])
        # use a fixed mapping for first divider; may be a good algo solution
        if ts.numerator in [2, 4, 8, 16, 32]:
            divFirst = 2
        elif ts.numerator in [3, 6, 9, 12, 15]:
            divFirst = 3
        else:
            divFirst = ts.numerator
    
        for h in range(len(ts.beat)): # this will return 1 part
            # this needs to be subdivided here by the LCM of the numerator
            ts.beat[h] = ts.beat[h].subdivide(divFirst)
            for i in range(len(ts.beat[h])):
                ts.beat[h][i] = \
                    ts.beat[h][i].subdivide(2)
                for j in range(len(ts.beat[h][i])):
                    ts.beat[h][i][j] = \
                        ts.beat[h][i][j].subdivide(2)

        for n in m.notes:
            
            if n.tie != None:
                environLocal.printDebug(['note, tie', n, n.tie, n.tie.type])
                if n.tie.type == 'stop':
                    continue
            for i in range(ts.getBeatDepth(n.offset)):
                n.addLyric('*')

    return streamIn






#-------------------------------------------------------------------------------
class TestExternal(unittest.TestCase):
    
    def runTest(self):
        pass
    
    def testSingle(self):
        '''Need to test direct meter creation w/o stream
        '''
        from music21 import stream, note, meter
        s = stream.Stream()
        ts = meter.TimeSignature('4/4')

        s.append(ts)
        n = note.Note()
        n.quarterLength = 1
        s.repeatAppend(n, 4)

        n = note.Note()
        n.quarterLength = .5
        s.repeatAppend(n, 8)

        s = s.makeMeasures()
        s = labelBeatDepth(s)

        s.show()            



class Test(unittest.TestCase):
    '''Unit tests
    '''

    def runTest(self):
        pass
    

    def setUp(self):
        pass



if __name__ == "__main__":
    music21.mainTest(Test, TestExternal)



