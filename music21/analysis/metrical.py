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

    >>> from music21 import *
    >>> s = stream.Stream()
    >>> ts = meter.TimeSignature('4/4')
    >>> s.insert(0, ts)
    >>> n = note.Note()
    >>> s.repeatAppend(n, 4)
    >>> post = analysis.metrical.labelBeatDepth(s)
    >>> ts.beatSequence
    <MeterSequence {{1/8+1/8}+{1/8+1/8}+{1/8+1/8}+{1/8+1/8}}>
    '''
#     ts = streamIn.flat.getElementsByClass(
#          music21.meter.TimeSignature)[0]
    

    for m in streamIn.getElementsByClass(music21.stream.Measure):

        # this will search contexts
        ts = m.getTimeSignatures(sortByCreationTime=False)[0]

        ts.beatSequence.subdivideNestedHierarchy(depth=3)

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


#------------------------------------------------------------------------------
# eof


