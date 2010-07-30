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
        # edges are stored Interval objects, in order
        self._edgesOrdered = []
        # nodes suggest Pitches, but Pitches are not stored
        # instead, nodes are keys, pairs defining the two edges that connect
        # to this node
        self._nodesOrdered = []
    
        # attributes (weights, etc) for edges might be defined as dictionaries
        # for each index position in the self._edgesOrdered list
        self._edgeAttributes = {}
        # attributes for nodes can be defined as dictionaries for each
        # store node key (a pair between edges) 
        self._nodeAttributes = {}

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



    def _filterPitchList(self, pitchTest):
        '''Given a list or one pitch, check if all are pitch objects; convert if necessary.
        '''
        if not common.isListLike(pitchTest):
            if common.isStr(pitchTest):
                pitchTest = pitch.Pitch(pitchTest)
            pitchTest = [pitchTest]
        else:
            # convert a list of string into pitch objects
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

        return pitchTest, minPitch, maxPitch


    def match(self, pitchReference, nodeId, pitchTest, permitEnharmonic=True):
        '''Given one or more pitches in pitchTest, determine the number of pitch matches, pitch omissions, and non pitch tones in a realized network. 

        Need flags for pitch class and enharmonic comparison. 

        >>> from music21 import *
        >>> edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        >>> net = IntervalNetwork(edgeList)
        >>> net.realize('e-2')
        [E-2, F2, G2, A-2, B-2, C3, D3, E-3]

        >>> net.match('e-2', 1, 'c3')
        ([C3], [])

        >>> net.match('e-2', 1, 'd3')
        ([D3], [])

        >>> net.match('e-2', 1, 'd#3')
        ([D#3], [])

        >>> net.match('e-2', 1, 'e3')
        ([], [E3])

        >>> pitchTest = [pitch.Pitch('b-2'), pitch.Pitch('b2'), pitch.Pitch('c3')]
        >>> net.match('e-2', 1, pitchTest)
        ([B-2, C3], [B2])

        >>> pitchTest = ['b-2', 'b2', 'c3', 'e-3', 'e#3', 'f2', 'e--2']
        >>> net.match('e-2', 1, pitchTest)
        ([B-2, C3, E-3, E#3, F2, E--2], [B2])

        '''
        if nodeId == None: # assume first
            nodeId = self._getFirstNode()
        else:
            nodeId = self._filterNodeId(nodeId)

        pitchTest, minPitch, maxPitch = self._filterPitchList(pitchTest)
        nodesRealized = self.realize(pitchReference, nodeId, minPitch, maxPitch)

        matched = []
        noMatch = []

        for target in pitchTest:
            found = False
            for p in nodesRealized:
                # enharmonic switch here
                match = False
                if permitEnharmonic:
                    if target.ps == p.ps:
                        match = True
                else:
                    if target == p:
                        match = True
                if match:
                    matched.append(target)
                    found = True
                    break
            if not found:
                noMatch.append(target)

#         for p in nodesRealized:
#             if p not in matched:
#                 notFound.append(p)
            
        return matched, noMatch
                
            

    def find(self, pitchTest, resultsReturned=4):
        '''Given a collection of pitches, test all transpositions of a realized version of this network, and return the number of matches in each for each pitch assigned to the first node. 

        >>> from music21 import *
        >>> edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        >>> net = IntervalNetwork(edgeList)
        >>> net.find(['g', 'a', 'b', 'd', 'f#'])
        [(5, G), (5, D), (4, A), (4, C)]

        >>> net.find(['g', 'a', 'b', 'c', 'd', 'e', 'f#'])
        [(7, G), (6, D), (6, C), (5, A)]

        '''

        nodeId = self._getFirstNode()
        sortList = []

        # for now, searchin 12 pitches; this may be more than necessary
        for p in [pitch.Pitch('c'), pitch.Pitch('c#'),
                  pitch.Pitch('d'), pitch.Pitch('d#'),
                  pitch.Pitch('e'), pitch.Pitch('f'),
                  pitch.Pitch('f#'), pitch.Pitch('g'),
                  pitch.Pitch('g#'), pitch.Pitch('a'),
                  pitch.Pitch('a#'), pitch.Pitch('b'),
                ]:
            matched, noMatch = self.match(p, nodeId, pitchTest,
                                         permitEnharmonic=True)

            sortList.append((len(matched), p))

        sortList.sort()
        sortList.reverse() # want most amtches first
        return sortList[:resultsReturned]  



#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass
    

    def testScaleModel(self):

        # define ordered list of intervals
        edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        net = IntervalNetwork(edgeList)
        
        # get this scale for any pitch at any step over any range
        # need a major scale with c# as the third degree
        match = net.realize('c#', 3)        
        self.assertEqual(str(match), '[A3, B3, C#, D4, E4, F#4, G#4, A4]')
        
        # need a major scale with c# as the leading tone in a high octave
        match = net.realize('c#', 7, 'c8', 'c9')        
        self.assertEqual(str(match), '[C#8, D8, E8, F#8, G8, A8, B8]')
        
        # for a given realization, we can find out the scale degree of any pithc
        self.assertEqual(net.getRelativeNodeId('c#', 7, 'd2'), 1)
        self.assertEqual(net.getRelativeNodeId('c#', 3, 'd2'), 4)
        
        
        # we can create non-octave repeating scales too
        edgeList = ['P5', 'P5', 'P5']
        net = IntervalNetwork(edgeList)
        match = net.realize('c4', 1)        
        self.assertEqual(str(match), '[C4, G4, D5, A5]')
        match = net.realize('c4', 1, 'c4', 'c11')        
        self.assertEqual(str(match), '[C4, G4, D5, A5, E6, B6, F#7, C#8, G#8, D#9, A#9, E#10, B#10]')
        
        # based on the original interval list, can get information on scale steps, even for non-octave repeating scales
        self.assertEqual(net.getRelativeNodeId('c4', 1, 'e#10'), 3)
        
        
        # we can also search for realized and possible matches in a network
        edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        net = IntervalNetwork(edgeList)
        
        # if we know a realized version, we can test if pitches match in that version; returns matched, not found, and no match lists
        matched, noMatch = net.match('e-', 1, 'f')
        self.assertEqual(str(matched), '[F]')
        
        # can search a list of pitches, isolating non-scale tones
        matched, noMatch = net.match('e-', 1, ['b-', 'd-', 'f'])
        self.assertEqual(str(matched), '[B-, F]')
        self.assertEqual(str(noMatch), '[D-]')
        
        # finally, can search the unrealized network; all possible realizations
        # are tested, and the matched score is returned
        # the first top 4 results are returned by default
        
        # in this case, the nearest major keys are G and D
        results = net.find(['g', 'a', 'b', 'd', 'f#'])
        self.assertEqual(str(results), '[(5, G), (5, D), (4, A), (4, C)]')
        
        # with an f#, D is the most-matched first node pitch
        results = net.find(['g', 'a', 'b', 'c#', 'd', 'f#'])
        self.assertEqual(str(results), '[(6, D), (5, A), (5, G), (4, E)]')


    def testHarmonyModel(self):

        # can define a chord type as a sequence of intervals
        # to assure octave redundancy, must provide top-most interval to octave
        # this could be managed in specialized subclass
        
        edgeList = ['M3', 'm3', 'P4']
        net = IntervalNetwork(edgeList)
        
        # if g# is the root, or first node
        match = net.realize('g#', 1)        
        self.assertEqual(str(match), '[G#, B#4, D#5, G#5]')
        
        # if g# is the fifth, or third node
        match = net.realize('g#', 3)        
        self.assertEqual(str(match), '[C#4, E#4, G#, C#5]')
        
        # if g# is the third, or second node, across a wide range
        match = net.realize('g#', 2, 'c2', 'c5')        
        self.assertEqual(str(match), '[E2, G#2, B2, E3, G#3, B3, E4, G#, B4]')
        
        # can match pitches to a realization of this chord
        # given a chord built form node 2 as g#, are e2 and b6 in this network
        matched, noMatch = net.match('g#', 2, ['e2', 'b6'])
        self.assertEqual(str(matched), '[E2, B6]')
        
        # can find a first node (root) that match any provided pitches
        # this is independent of any realization
        results = net.find(['c', 'e', 'g'])
        self.assertEqual(str(results), '[(3, C), (1, A), (1, G#), (1, G)]')
        
        # in this case, most likely an e triad
        results = net.find(['e', 'g#'])
        self.assertEqual(str(results), '[(2, E), (1, A), (1, G#), (1, C#)]')
        
        
        # we can do the same with larger or more complicated chords
        # again, we must provide the interval to the octave
        edgeList = ['M3', 'm3', 'M3', 'm3', 'm7']
        net = IntervalNetwork(edgeList)
        match = net.realize('c4', 1)        
        self.assertEqual(str(match), '[C4, E4, G4, B4, D5, C6]')
        
        # if we want the same chord where c4 is the 5th node, or the ninth
        match = net.realize('c4', 5)        
        self.assertEqual(str(match), '[B-2, D3, F3, A3, C4, B-4]')
        
        # we can of course provide any group of pitches and find the value
        # of the lowest node that provides the best fit
        results = net.find(['e', 'g#', 'b', 'd#'])
        self.assertEqual(str(results), '[(3, E), (2, C), (1, B), (1, G#)]')


    def testScaleAndHarmony(self):

        # start with a major scale
        edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        netScale = IntervalNetwork(edgeList)
        
        # take a half diminished seventh chord
        edgeList = ['m3', 'm3', 'M3', 'M2']
        netHarmony = IntervalNetwork(edgeList)
        match = netHarmony.realize('b4', 1)        
        self.assertEqual(str(match), '[B4, D5, F5, A5, B5]')
        
        
        # given a half dim seventh chord built on c#, what scale contains
        # these pitches?
        results = netScale.find(netHarmony.realize('c#', 1))
        # most likely, a  D
        self.assertEqual(str(results), '[(5, D), (4, B), (4, A), (4, E)]')
        # what scale degree is c# in this scale? the seventh
        self.assertEqual(netScale.getRelativeNodeId('d', 1, 'c#'), 7)



if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)
    elif len(sys.argv) > 1:
        a = Test()

