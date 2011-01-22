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

from music21 import environment
_MOD = 'analysis/search.py'
environLocal = environment.Environment(_MOD)





class SearchModuleException(Exception):
    pass



def findConsecutiveScale(source, targetScale, degreesRequired=5, 
        stepwiseRequired=True, comparisonAttribute='name',   
        repeatsAllowed=True, restsAllowed=False):
    '''
    Given a concrete scale, return references to the elements found within this scale.

    Note that this only looks for complete degree spelling, not degree order

    `comparisonAttribute` can force enharmonic or permit pitch class matching. 
    '''

    if not isinstance(targetScale, scale.ConcreteScale):
        raise SearchModuleException('scale must be a concrete scale class')

    errors = 0
    degreeLast = None
    pLast = None
    directionLast = None

    collPitches = []
    collElements = []
    collDegrees = set() # use a set to remove redundancies

    clearCollect = False
    clearCollectKeepLast = False
    match = False
    collMatch = [] # return a list of streams
    pNextAscending = None
    pNextDescending = None

    
    # assume 0 to max unique; this is 1 to 7 for diatonic
    dMax = targetScale.abstract.getStepMaxUnique()
    targetDegrees = set(range(1, dMax))

    # if rests are allowed, first
    # strip them out of a copy of the source
    sourceClean = stream.Stream()
    for e in source:
        if 'Chord' in e.classes:
            continue # do not insert for now
        if 'Rest' in e.classes and restsAllowed:
            continue # do not insert if allowed

        # just takes notes or pitches
        if 'Note' in e.classes or 'Pitch' in e.classes:
            sourceClean.insert(e.getOffsetBySite(source), e)
    
    # not taking flat
    for eCount, e in enumerate(sourceClean):
        subPitches = []

        # at this time, not handling chords

        if eCount < len(source) - 1:
            eNext = source[eCount+1]
        else:
            eNext = None

        if hasattr(e, 'pitch'):
            p = e.pitch
            if eNext is not None and hasattr(eNext, 'pitch'):
                pNext = eNext.pitch
            else:
                pNext = None

            environLocal.printDebug(['examining pitch', p, 'pNext', pNext, 'pLast', pLast])
            collect = False
            # first, see if this is a degreeLast
            d = targetScale.getScaleDegreeFromPitch(p, 
                comparisonAttribute=comparisonAttribute)
        
            # if this is not a scale degree, this is the end of a collection
            if d is None:
                clearCollect = True
                environLocal.printDebug(['not collecting pitch', 'd', d, 'p', p])

            # second, see if the degrees are consecutive with the last
            else:
                if pLast is not None:
                    pScaleAscending = targetScale.next(pLast, 
                        direction='ascending')
                    pScaleDescending = targetScale.next(pLast, 
                        direction='descending')                

                if degreeLast is None: # if we do not have a previous
                    collect = True
                    # cannot determine direction here
                # this will permit octave shifts; need to compare pitch
                # attributes
                elif repeatsAllowed and degreeLast-d == 0:
                    collect = True
                # we know have a previous pitch/degree
#                 elif (abs(degreeLast-d) == 1 or 
#                     (degreeLast == dMax and d == 0) or 
#                     (degreeLast == 0 and d == dMax)):
                elif targetScale.isNext(p, pLast, 'ascending', stepSize=1,
                    comparisonAttribute=comparisonAttribute) and directionLast in [None, 'ascending']:

                    environLocal.printDebug(['found ascending degree', 'degreeLast', degreeLast, 'd', d])
                    collect = True
                    directionLast = 'ascending'

                elif targetScale.isNext(p, pLast, 'descending', stepSize=1,
                    comparisonAttribute=comparisonAttribute) and directionLast in [None, 'descending']:

                    environLocal.printDebug(['found descending degree', 'degreeLast', degreeLast, 'd', d])
                    collect = True
                    directionLast = 'descending'

                else:
                    # if this condition is not met, then we need to test
                    # and clear the collection
                    collect = False
                    # this is a degree, so we want to keep it for the 
                    # next potential sequence
                    clearCollectKeepLast = True
                    environLocal.printDebug(['no conditions matched for pitch', p, 'collect = False, clearCollectKeepLAst = True'])

                # gather pitch and degree
                if collect:
                    environLocal.printDebug(['collecting pitch', 'd', d, 'p', p])
                    collDegrees.add(d)
                    collPitches.append(p)
                    collElements.append(e)

            # directionLast is set above
            degreeLast = d # set it here
            pLast = p

        # test at for each new pitch; set will measure original instances
        if len(collDegrees) >= degreesRequired:
            # if next pitch is appropriate, than do not collect
            # this makes gathering greedy

            temp = targetScale.next(p, directionLast, stepSize=1)
            environLocal.printDebug(['temp', temp, 'p', p, 'directionLast', directionLast])

            if targetScale.isNext(pNext, p, directionLast, stepSize=1,
                    comparisonAttribute=comparisonAttribute):
                environLocal.printDebug(['matched degree count but next pitch is in scale and direction', 'collDegrees', collDegrees])
            else:
                environLocal.printDebug(['matched degree count', 'collDegrees', collDegrees, 'pNext', pNext])
                match = True

        if match:
            post = stream.Stream()
            for e in collElements:
                # use source offset positions
                post.insert(e.getOffsetBySite(source), e)
            collMatch.append(post)
            match = False

            # if we have not explicitly said to keep the last
            # then we should 
            if clearCollect is False and clearCollectKeepLast is False:
                #clearCollectKeepLast = True
                clearCollect = True

        if clearCollect:
            degreeLast = None
            directionLast = None
            collDegrees = set()
            collPitches = []
            collElements = []
            clearCollect = False

        # case where we need to keep the element that broke
        # the chain; as in a leep to a new degree in the scale
        if clearCollectKeepLast:
            #degreeLast = None keep
            # always clear direction last
            directionLast = None 
            collDegrees = set()
            collDegrees.add(d)
            collPitches = [p]
            collElements = [e]
            clearCollectKeepLast = False


    return collMatch









#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testfindConsecutiveScaleA(self):
        from music21 import corpus, scale, note

        sc = scale.MajorScale('a4')

#         s = corpus.parseWork('bwv66.6')
#         part = s['Soprano']
#         #part.show()
# 
# 
# 
        # fixed collection
        part = stream.Stream()
        for pn in ['a4', 'b4', 'c#4', 'd4', 'e4', 'f#4', 'g#4', 'a4']:
            n = note.Note(pn)
            part.append(n)
        
        # todo: presently this is still permitting gaps
        post = findConsecutiveScale(part, sc, degreesRequired=4)
        self.assertEqual(len(post), 1) # one group
        self.assertEqual(len(post[0]), 8) # has all 8 elements



        part = stream.Stream()
        for pn in ['a4', 'b4', 'c#4', 'd4', 'e4', 'f#4', 'g#4', 'a4']:
            n = note.Note(pn)
            part.append(n)
        
        # todo: presently this is still permitting gaps
        post = findConsecutiveScale(part, sc, degreesRequired=4, comparisonAttribute='nameWithOctave')
        self.assertEqual(len(post), 1) # one group
        self.assertEqual(len(post[0]), 6) # has last 6 elements


        part = stream.Stream()
        for pn in ['a4', 'b4', 'c#5', 'd5', 'e5', 'a4', 'b4', 'c#5', 'd5', 'e5']:
            n = note.Note(pn)
            part.append(n)
        
        post = findConsecutiveScale(part, sc, degreesRequired=4, comparisonAttribute='nameWithOctave')
        self.assertEqual(len(post), 2) # two groups
        self.assertEqual(len(post[0]), 5) # has last 6 elements
        self.assertEqual(len(post[1]), 5) # has last 6 elements


        # with octave shifts
        part = stream.Stream()
        for pn in ['a4', 'b8', 'c#3', 'd3', 'e4', 'a4', 'b9', 'c#2', 'd4', 'e12']:
            n = note.Note(pn)
            part.append(n)
        
        # todo: presently this is still permitting gaps
        post = findConsecutiveScale(part, sc, degreesRequired=4, comparisonAttribute='name')
        self.assertEqual(len(post), 2) # two groups
        self.assertEqual(len(post[0]), 5) # has last 6 elements
        self.assertEqual(len(post[1]), 5) # has last 6 elements


#         ex = stream.Score()
#         for sub in post:
#             m = stream.Measure()
#             for e in sub:
#                 m.append(e)
#             ex.append(m)
#         ex.show()



#------------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    if len(sys.argv) == 1:
        music21.mainTest(Test)
    else:
        t = Test()
        t.testfindConsecutiveScaleA()



