#-------------------------------------------------------------------------------
# Name:         testDocumentation.py
# Purpose:      tests from or derived from the Documentation
#
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import copy, types, random
import doctest, unittest



import music21
from music21 import corpus, stream, note, meter



def test():
    '''Doctest placeholder

    >>> True
    True
    '''
    pass



#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass



    def testMeterOverview(self):

        sSrc = corpus.parseWork('bach/bwv13.6.xml')
        sPart = sSrc.getElementById('Bass')

        # create a new set of measure partitioning
        # we now have the same notes in new measure objects
        sMeasures = sPart.flat.notes.makeMeasures(meter.TimeSignature('6/8'))

        # measure 2 is at index 1
        self.assertEquals(sMeasures[1].measureNumber, 2)

        # getting a measure by context, we should 
        # get the most recent measure that was this note was in
        mCanddiate = sMeasures[1][0].getContextByClass(stream.Measure,
                     sortByCreationTime=True)

        self.assertEquals(mCanddiate, sMeasures[1])


        # from the docs:
        sSrc = corpus.parseWork('bach/bwv57.8.xml')
        sPart = sSrc.getElementById('Alto')
        post = sPart.musicxml

        # we get 3/4
        self.assertEquals(sPart.measures[0].timeSignature.numerator, 3)
        self.assertEquals(sPart.measures[1].timeSignature, None)

        sPart.measures[0].timeSignature = meter.TimeSignature('5/4')
        self.assertEquals(sPart.measures[0].timeSignature.numerator, 5)
        post = sPart.musicxml

        sNew = sPart.flat.notes
        sNew.insert(0, meter.TimeSignature('2/4'))
        post = sNew.musicxml



if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)
    elif len(sys.argv) > 1:
        a = Test()



