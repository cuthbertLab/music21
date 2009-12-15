#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         testPerformance.py
# Purpose:      Tests keep track of long-term performance targets
#
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2009 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------




import doctest, unittest

import music21
from music21 import common, corpus

from music21 import environment
_MOD = 'test/testPerformance.py'
environLocal = environment.Environment(_MOD)

#-------------------------------------------------------------------------------
class Test(unittest.TestCase):


    def runTest(self):
        pass

    def testTimingTolerance(self):
        '''Test the performance of loading various files
        This may not produce errors as such, but is used to provide reference
        if overall perforamance has changed.
        '''
        # provide work and expected min/max in seconds
        for known, max in [
            ('beethoven/opus59no2/movement3', 9),
            ('haydn/opus74no1/movement3', 6),
            ('schumann/opus41no1/movement2', 7),

            ]:
            pass

            t = common.Timer()
            t.start()
            x = corpus.parseWork(known, forceSource=True)
            t.stop()
            dur = t()
            environLocal.printDebug(['timing tolarance for', known, t])
            self.assertEqual(True, dur <= max) # performance test




if __name__ == "__main__":
    music21.mainTest(Test)

