#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         search.py
# Purpose:      Tools for searching analysis
#
# Authors:      Christopher Ariza
#
# Copyright:    (c) 20011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------


import unittest

import music21

from music21 import scale
from music21 import stream
from music21 import chord



class SearchModuleException(Exception):
    pass



def findConsecutiveScale(source, targetScale, degreesRequired=5, 
        stepwiseRequired=True, comparisonAttribute='name',   
        pitchSpaceRequired=False, repeatsAllowed=True, restsAllowed=False):
    '''
    Given a concrete scale, return references to the elements found within this scale.

    Note that this only looks for complete degree spelling, not degree order

    `comparisonAttribute` can force enharmonic or permit pitch class matching. 
    '''

    if not isinstance(targetScale, scale.ConcreteScale):
        raise SearchModuleException('scale must be a concrete scale class')

    errors = 0
    degreeLast = None

    collPitches = []
    collElements = []
    collDegrees = set() # use a set to remove redundancies

    clearCollect = False
    match = False
    collMatch = [] # return a list of streams
    
    # assume 0 to max unique; this is 1 to 7 for diatonic
    dMax = targetScale.abstract.getStepMaxUnique()
    targetDegrees = set(range(1, dMax))


    # not taking flat
    for e in source:
        subPitches = []
        # always start with appending the element
        collElements.append(e)

        if hasattr(e, 'pitch'): # case of notes
            subPitches = [e.pitch]
        # case of chords
        # not just looking at pitches, b/c that could get a Stream
        elif isinstance(e, chord.Chord) and hasattr(e, 'pitch'):
            subPitches = e.pitches
        for p in subPitches:

            collect = False
            # first, see if this is a degreeLast
            d = targetScale.getScaleDegreeFromPitch(p, comparisonAttribute=comparisonAttribute)
        
            # if this is not a scale degree, this is the end of a collection
            if d is None:
                clearCollect = True
            # second, see if the degrees are consecutive with the last
            else:
                if degreeLast is None:
                    collect = True
                 # make sure that this degree is 1 away from the modulus
                 # this is 7 in a diatonic scale
                elif repeatsAllowed and degreeLast-d == 0:
                    collect = True
                elif (abs(degreeLast-d) == 1 or 
                    (degreeLast == dMax and d == 0) or 
                    (degreeLast == 0 and d == dMax)):
                    collect = True
                # gather pitch and degree
                if collect:
                    collDegrees.add(d)
                    collPitches.append(p)

            degreeLast = d # set it here

            # test at for each new pitch; set will measure original instances
            if len(collDegrees) >= degreesRequired:
                match = True

            if match:
                post = stream.Stream()
                for e in collElements:
                    # use source offset positions
                    post.insert(e.getOffsetBySite(source), e)
                collMatch.append(post)
                clearCollect = True
                match = False

            if clearCollect:
                degreeLast = None
                collPitches = []
                collDegrees = set()
                clearCollect = False

    return collMatch









#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testfindConsecutiveScaleA(self):
        from music21 import corpus, scale

        sc = scale.MajorScale('a')

        s = corpus.parseWork('bwv66.6')
        part = s['Soprano']
        #part.show()

        
        # todo: presently this is still permitting gaps
        post = findConsecutiveScale(part.flat, sc)

        ex = stream.Score()
        for sub in post:
            m = stream.Measure()
            for e in sub:
                m.append(e)
            ex.append(m)
        #ex.show()



#------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    if len(sys.argv) == 1:
        music21.mainTest(Test)
    else:
        t = Test()
        t.testfindConsecutiveScaleA()



