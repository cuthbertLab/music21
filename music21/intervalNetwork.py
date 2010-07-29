#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         intervalNetwork.py
# Purpose:      A graph of intervals, for scales and harmonies. 
#
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------


'''An IntervalNetwork defines a graph, where pitches are nodes and intervals are edges. Nodes, however, are not stored; instead, an ordered list of edges (Intervals) is provided as an archetype of adjacent nodes. 

Edges between non adjacent (non ordered) can be defined and manipulated if necessary. 

IntervalNetwork permits the definition of conventional octave repeating scales or harmonies (abstract chords), non-octave repeating scales and chords, and ordered interval sequences that might move in multiple directions. 

A scale or harmony may be composed of one or more IntervalNetwork objects. 

Both nodes and edges can be weighted to suggest tonics, dominants, finals, or other attributes of the network. 
'''

import unittest, doctest

import music21
from music21 import interval
from music21 import common
from music21 import pitch

from music21 import environment
_MOD = "intervalNetwork.py"
environLocal = environment.Environment(_MOD)


class IntervalNetwork:
    '''A graph of undefined Pitch nodes connected by a defined, ordered list of Interval objects as edges. 
    '''

    def __init__(self, edgeList=None):
        self._edgesOrdered = []
        self._nodesOrdered = []
    
        # these are just symbols/place holders; values do not matter as long
        # as they are not positive ints
        self._start = 'start'
        self._end = 'end'

        if edgeList != None: # auto initialize
            self.setEdges(edgeList)

    def _updateNodes(self):
        low = self._start
        high = None
        for i in range(len(self._edgesOrdered)-1):
            pair = (low, i)
            self._nodesOrdered.append(pair)
            low = i
        # add last to end
        self._nodesOrdered.append((i, self._end))


    def setEdges(self, edgeList):
        '''Given a list of edges (Interval specifications), store and define nodes.
    
        >>> edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        >>> net = IntervalNetwork()
        >>> net.setEdges(edgeList)
        >>> net._nodesOrdered
        [('start', 0), (0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 'end')]

        '''
        for edge in edgeList:
            i = interval.Interval(edge)
            self._edgesOrdered.append(i)
        self._updateNodes()


    #---------------------------------------------------------------------------
    def _getFirstNode(self):
        return self._nodesOrdered[0]
    
    firstNode = property(_getFirstNode, 
        doc='''Return the last Node.

        >>> edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        >>> net = IntervalNetwork()
        >>> net.setEdges(edgeList)
        >>> net.firstNode
        ('start', 0)
        ''')

    def _getLastNode(self):
        return self._nodesOrdered[-1]
    
    lastNode = property(_getLastNode, 
        doc='''Return the last Node.

        >>> edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        >>> net = IntervalNetwork()
        >>> net.setEdges(edgeList)
        >>> net.lastNode
        (5, 'end')
        ''')


    #---------------------------------------------------------------------------
    def _filterNodeId(self, id):
        '''
        >>> edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        >>> net = IntervalNetwork()
        >>> net.setEdges(edgeList)
        >>> net._filterNodeId(1)
        ('start', 0)
        >>> net._filterNodeId([3,4])
        (3, 4)
        >>> net._filterNodeId('last')
        (5, 'end')
        >>> net._filterNodeId('first')
        ('start', 0)
        '''
        if common.isNum(id):
            # assume counting nodes from 1
            return self._nodesOrdered[id-1 % len(self._nodesOrdered)]
        if common.isStr(id):
            if id.lower() in ['start', 'first']:
                return self._getFirstNode()
            elif id.lower() in ['end', 'last']:
                return self._getLastNode()

        else: # match coords
            if tuple(id) in self._nodesOrdered:
                return tuple(id)

    
    def _fitRange(self, nodesRealized, minPitch=None, maxPitch=None):
        '''Given a realized pitch range, extend or crop between min and max.

        >>> from music21 import *
        >>> edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        >>> net = IntervalNetwork()
        >>> net.setEdges(edgeList)
        >>> net.realize(pitch.Pitch('G3'))
        [G3, A3, B3, C4, D4, E4, F#4, G4]

        >>> net._fitRange(net.realize(pitch.Pitch('G3')), 'g3', 'g5')
        [G3, A3, B3, C4, D4, E4, F#4, G4, A4, B4, C5, D5, E5, F#5, G5]

        >>> net._fitRange(net.realize(pitch.Pitch('G3')), 'g3', 'f6')
        [G3, A3, B3, C4, D4, E4, F#4, G4, A4, B4, C5, D5, E5, F#5, G5, A5, B5, C6, D6, E6]

        >>> net._fitRange(net.realize(pitch.Pitch('G3')), 'g7', 'd8')
        [G7, A7, B7, C8, D8]

        >>> net._fitRange(net.realize(pitch.Pitch('G3')), 'g2', 'g4')
        [G2, A2, B2, C3, D3, E3, F#3, G3, A3, B3, C4, D4, E4, F#4, G4]


        >>> net._fitRange(net.realize(pitch.Pitch('G3')), 'f#3', 'g4')
        [F#3, G3, A3, B3, C4, D4, E4, F#4, G4]

        >>> net._fitRange(net.realize(pitch.Pitch('G3')), 'b3', 'd4')
        [B3, C4, D4]

        >>> net._fitRange(net.realize(pitch.Pitch('G3')), 'b1', 'd2')
        [B1, C2, D2]

        >>> net._fitRange(net.realize(pitch.Pitch('G3')), 'c2', 'f#2')
        [C2, D2, E2, F#2]
        '''

        localMin = nodesRealized[0]
        localMax = nodesRealized[-1]

        if minPitch == None:
            minPitch = localMin
        elif common.isStr(minPitch):
            minPitch = pitch.Pitch(minPitch)

        if maxPitch == None:
            maxPitch = localMax
        elif common.isStr(maxPitch):
            maxPitch = pitch.Pitch(maxPitch)

        if minPitch.ps == localMin.ps and maxPitch.ps == localMax.ps:
            # do nothing
            return nodesRealized


        # first, extend upward, starting with the topmost interval   
        post = []
        if maxPitch.ps > localMax.ps:
            i = 0
            ref = localMax
            while True:
                intervalObj = self._edgesOrdered[i % len(self._edgesOrdered)]
                p = intervalObj.transposePitch(ref)
                if p.ps > maxPitch.ps:
                    break
                post.append(p)
                ref = p
                i += 1

        # second, extend downward, starting with bottom most interval 
        pre = []
        if minPitch.ps < localMin.ps:
            i = -1
            ref = localMin
            while True:
                intervalObj = self._edgesOrdered[i % len(self._edgesOrdered)]
                # reverse direction
                p = intervalObj.reverse().transposePitch(ref)
                if p.ps < minPitch.ps:
                    break
                pre.append(p)
                ref = p
                i -= 1
            pre.reverse() # must flip

        # only one boundary different
        if minPitch.ps == localMin.ps and maxPitch.ps > localMax.ps:
            return nodesRealized + post
        elif minPitch.ps < localMin.ps and maxPitch.ps == localMax.ps:
            return pre + nodesRealized
        # last: crop what we already have        
        else:
            out = []
            for p in pre + nodesRealized + post:
                if p.ps >= minPitch.ps and p.ps <= maxPitch.ps:
                    out.append(p)
            return out



    def realize(self, pitchObj, nodeId=None, minPitch=None, maxPitch=None):
        '''Realize the native nodes of this network based on a pitch assigned to a valid `nodeId`, where `nodeId` can be specified by integer (starting from 1) or key (a tuple of start, stop). 

        >>> from music21 import *
        >>> edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        >>> net = IntervalNetwork()
        >>> net.setEdges(edgeList)
        >>> net.realize(pitch.Pitch('G3'))
        [G3, A3, B3, C4, D4, E4, F#4, G4]

        >>> net.realize(pitch.Pitch('G3'), 5) # fifth (scale) degree
        [C3, D3, E3, F3, G3, A3, B3, C4]

        >>> net.realize(pitch.Pitch('G3'), 7) # seventh (scale) degree
        [A-2, B-2, C3, D-3, E-3, F3, G3, A-3]

        >>> net.realize(pitch.Pitch('G3'), 1) # seventh (scale) degree
        [G3, A3, B3, C4, D4, E4, F#4, G4]

        >>> net.realize(pitch.Pitch('f#3'), 1, 'f2', 'f3') 
        [E#2, F#2, G#2, A#2, B2, C#3, D#3, E#3]

        >>> net.realize(pitch.Pitch('a#2'), 7, 'c6', 'c7') 
        [C#6, D#6, E6, F#6, G#6, A#6, B6]
        '''
        if nodeId == None: # assume first
            nodeId = self._getFirstNode()
        else:
            nodeId = self._filterNodeId(nodeId)
            
        if common.isStr(pitchObj):
            pitchObj = pitch.Pitch(pitchObj)

        post = []
        post.append(pitchObj)

        # first, go upward
        ref = pitchObj
#         for i in range(self._nodesOrdered.index(nodeId), len(self._edgesOrdered)):
        i = self._nodesOrdered.index(nodeId)
        while True:
            intervalObj = self._edgesOrdered[i % len(self._edgesOrdered)]
            p = intervalObj.transposePitch(ref)
            post.append(p)
            ref = p
            i += 1
            if i >= len(self._edgesOrdered):
                break

        # second, go downward
        pre = []
        if self._nodesOrdered.index(nodeId) != 0:
            ref = pitchObj # reset to origin
            #for i in range(self._nodesOrdered.index(nodeId)-1, -1, -1):
            j = self._nodesOrdered.index(nodeId) - 1
            while True:
                #environLocal.printDebug([i, self._edgesOrdered[i]])
                intervalObj = self._edgesOrdered[j % len(self._edgesOrdered)]
                # do interval in reverse direction
                p = intervalObj.reverse().transposePitch(ref)
                pre.append(p)
                ref = p
                j -= 1
                if j <= -1:
                    break

        pre.reverse()
        return self._fitRange(pre + post, minPitch, maxPitch)




    def getRelativeNodeId(self, pitchReference, nodeId, pitchTest, 
        permitEnharmonic=True):
        '''Given a reference pitch assigned to node id, determine the relative node id of pitchTest, even if displaced over multiple octaves
        
        Need flags for pitch class and enharmonic comparison. 

        >>> from music21 import *
        >>> edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        >>> net = IntervalNetwork(edgeList)
        >>> net.realize(pitch.Pitch('e-2'))
        [E-2, F2, G2, A-2, B-2, C3, D3, E-3]

        >>> net.getRelativeNodeId('e-2', 1, 'd3')
        7
        >>> net.getRelativeNodeId('e3', 1, 'd5') == None
        True
        >>> net.getRelativeNodeId('e-3', 1, 'b-3')
        5

        >>> net.getRelativeNodeId('e-3', 1, 'e-5')
        1
        >>> net.getRelativeNodeId('e-2', 1, 'f3')
        2
        >>> net.getRelativeNodeId('e-3', 1, 'b6') == None
        True

        >>> net.getRelativeNodeId('e-3', 1, 'e-2')
        1
        >>> net.getRelativeNodeId('e-3', 1, 'd3')
        7
        >>> net.getRelativeNodeId('e-3', 1, 'e-3')
        1
        >>> net.getRelativeNodeId('e-3', 1, 'b-1')
        5


        >>> from music21 import *
        >>> edgeList = ['p4', 'p4', 'p4']
        >>> net = IntervalNetwork(edgeList)
        >>> net.realize('f2')
        [F2, B-2, E-3, A-3]
        >>> net.realize('f2', 1, 'f2', 'f6')
        [F2, B-2, E-3, A-3, D-4, G-4, C-5, F-5,   B--5, E--6]

        >>> net.getRelativeNodeId('f2', 1, 'a-3') # could be 4 or 1
        1
        >>> net.getRelativeNodeId('f2', 1, 'd-4') # 2 is correct
        2
        >>> net.getRelativeNodeId('f2', 1, 'g-4') # 3 is correct
        3
        >>> net.getRelativeNodeId('f2', 1, 'c-5') # could be 4 or 1
        1
        >>> net.getRelativeNodeId('f2', 1, 'e--6') # could be 4 or 1
        1


        >>> net.realize('f6', 1, 'f2', 'f6')
        [G#2, C#3, F#3, B3, E4, A4, D5, G5, C6, F6]

        >>> net.getRelativeNodeId('f6', 1, 'd5') 
        1
        >>> net.getRelativeNodeId('f6', 1, 'g5') 
        2
        >>> net.getRelativeNodeId('f6', 1, 'a4') 
        3
        >>> net.getRelativeNodeId('f6', 1, 'e4') 
        2
        >>> net.getRelativeNodeId('f6', 1, 'b3') 
        1



        '''
        if nodeId == None: # assume first
            nodeId = self._getFirstNode()
        else:
            nodeId = self._filterNodeId(nodeId)

        if common.isStr(pitchTest):
            pitchTest = pitch.Pitch(pitchTest)

        nodesRealized = self.realize(pitchReference, nodeId)

        # check if in notesRealized
        for i in range(len(nodesRealized)):
            # comparison of attributes, not object
            match = False
            if permitEnharmonic:
                if pitchTest.ps == nodesRealized[i].ps:
                    match = True
            else:
                if pitchTest == nodesRealized[i]:
                    match = True
            if match:
                return (i % len(self._edgesOrdered)) + 1 # first node is 1

        # need to look upward
        if pitchTest.ps > nodesRealized[-1].ps:
            # from last to top
            post = self._fitRange(nodesRealized, nodesRealized[-1], pitchTest)

            # start shift to account for nodesRealized
            i = 0
            while True:
                # add enharmonic comparison switch
                if post[i].ps == pitchTest.ps:
                    return (i % len(self._edgesOrdered)) + 1 # first node is 1
                else:
                    i += 1
                if i >= len(post):
                    return None

        # need to look downward
        elif pitchTest.ps < nodesRealized[0].ps:
            post = self._fitRange(nodesRealized, pitchTest, nodesRealized[0])
            # start shift to account for nodesRealized
            i = len(post) - 1
            count = 0 # first is zero position, boundary
            while True:
                #environLocal.printDebug([i, post, post[i]])

                # add enharmonic comparison switch
                if post[i].ps == pitchTest.ps:
                    # remove the length of the post added in before
                    # first node is 1
                    return (count % len(self._edgesOrdered)) + 1 
                else:
                    i -= 1
                    count -= 1
                if i < 0:
                    return None
        return None






    def match(self, pitchReference, nodeId, pitchTest):
        '''Given one or more pitches in pitchTest, determine number of pitch matches, pitch omissions, and non pitch tones. 

        Need flags for pitch class and enharmonic comparison. 

        >>> from music21 import *
        >>> edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        >>> net = IntervalNetwork(edgeList)
        >>> net.realize('e-2')
        [E-2, F2, G2, A-2, B-2, C3, D3, E-3]

        >>> net.match('e-2', 1, 'c3')
        ([C3], [], [])

        >>> net.match('e-2', 1, 'd3')
        ([D3], [], [])

        >>> net.match('e-2', 1, 'd#3')
        ([D#3], [E-3], [])

        >>> net.match('e-2', 1, 'e3')
        ([], [], [E3])

        >>> pitchTest = [pitch.Pitch('b-2'), pitch.Pitch('b2'), pitch.Pitch('c3')]
        >>> net.match('e-2', 1, pitchTest)
        ([B-2, C3], [], [B2])

        >>> pitchTest = ['b-2', 'b2', 'c3', 'e-3', 'e#3', 'f2', 'e--2']
        >>> net.match('e-2', 1, pitchTest)
        ([B-2, C3, E-3, E#3, F2, E--2], [D2, E-2, G2, A-2, D3, F3], [B2])

        '''
        if nodeId == None: # assume first
            nodeId = self._getFirstNode()
        else:
            nodeId = self._filterNodeId(nodeId)

        if not common.isListLike(pitchTest):
            if common.isStr(pitchTest):
                pitchTest = pitch.Pitch(pitchTest)
            minPitch = pitchTest
            maxPitch = pitchTest
            pitchTest = [pitchTest]

        else:
            # could convert a list of string into pitch objects
            temp = []
            for p in pitchTest:
                if common.isStr(p):
                    temp.append(pitch.Pitch(p))
            if len(temp) == len(pitchTest):
                pitchTest = temp

            sortList = [(pitchTest[i].ps, i) for i in range(len(pitchTest))]
            sortList.sort()
            minPitch = pitchTest[sortList[0][1]] # first index
            maxPitch = pitchTest[sortList[-1][1]] # last index


        nodesRealized = self.realize(pitchReference, nodeId, minPitch, maxPitch)

        matched = []
        notFound = []
        noMatch = []

        for target in pitchTest:
            found = False
            for p in nodesRealized:
                # add enharmonic switch here
                if target.ps == p.ps:
                    matched.append(target)
                    found = True
                    break
            if not found:
                noMatch.append(target)

        for p in nodesRealized:
            if p not in matched:
                notFound.append(p)
            
        return matched, notFound, noMatch
                
            


#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass
    



if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)
    elif len(sys.argv) > 1:
        a = Test()

