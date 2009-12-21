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
class TestPerformance(unittest.TestCase):

    def runTest(self):
        pass

    def testTimingTolerance(self):
        '''Test the performance of loading various files
        This may not produce errors as such, but is used to provide reference
        if overall performance has changed.
        '''
        # provide work and expected min/max in seconds
        for known, max, best in [
            ('beethoven/opus59no2/movement3', 9, 
                {'2009.12.14': 7.42, '2009.12.15': 6.686}),
            ('haydn/opus74no1/movement3', 5, 
                {'2009.12.14': 4.08, '2009.12.15': 3.531}),
            ('schumann/opus41no1/movement2', 7, 
                {'2009.12.14': 5.88, '2009.12.15': 5.126}),
            ('luca/gloria', 4,
                {'2009.12.14': 3.174, '2009.12.15': 2.954}),
            ]:

            t = common.Timer()
            t.start()
            x = corpus.parseWork(known, forceSource=True)
            t.stop()
            dur = t()
            environLocal.printDebug(['timing tolerance for', known, 
                'this run:', t, 'best runs:', 
                ['%s: %s' % (x, y) for x, y in best.items()]])
            self.assertEqual(True, dur <= max) # performance test




if __name__ == "__main__":
    music21.mainTest(TestPerformance)

