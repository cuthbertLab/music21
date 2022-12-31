# ------------------------------------------------------------------------------
# Name:         scale.test_intervalNetwork.py
# Purpose:      Tests for scale/intervalNetwork.py
#
# Authors:      Christopher Ariza
#               Michael Scott Asato Cuthbert
#
# Copyright:    Copyright © 2010-2023 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
from __future__ import annotations

import unittest

from music21 import common
from music21 import scale
from music21.scale.intervalNetwork import Terminus, Direction, IntervalNetwork

# ------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def pitchOut(self, listIn):
        out = '['
        for p in listIn:
            out += str(p) + ', '
        if listIn:
            out = out[0:len(out) - 2]
        out += ']'
        return out

    def realizePitchOut(self, pitchTuple):
        out = '('
        out += self.pitchOut(pitchTuple[0])
        out += ', '
        out += str(pitchTuple[1])
        out += ')'
        return out

    def testScaleModel(self):
        # define ordered list of intervals
        edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        net = IntervalNetwork(edgeList)

        # get this scale for any pitch at any degree over any range
        # need a major scale with c# as the third degree
        match = net.realizePitch('c#', 3)
        self.assertEqual(self.pitchOut(match), '[A3, B3, C#4, D4, E4, F#4, G#4, A4]')

        # need a major scale with c# as the leading tone in a high octave
        match = net.realizePitch('c#', 7, 'c8', 'c9')
        self.assertEqual(self.pitchOut(match), '[C#8, D8, E8, F#8, G8, A8, B8]')

        # for a given realization, we can find out the scale degree of any pitch
        self.assertEqual(net.getRelativeNodeDegree('b', 7, 'c2'), 1)

        # if c# is the leading tone, what is d? 1
        self.assertEqual(net.getRelativeNodeDegree('c#', 7, 'd2'), 1)
        # if c# is the mediant, what is d? 4
        self.assertEqual(net.getRelativeNodeDegree('c#', 3, 'd2'), 4)

        # we can create non-octave repeating scales too
        edgeList = ['P5', 'P5', 'P5']
        net = IntervalNetwork(edgeList)
        match = net.realizePitch('c4', 1)
        self.assertEqual(self.pitchOut(match), '[C4, G4, D5, A5]')
        match = net.realizePitch('c4', 1, 'c4', 'c11')
        self.assertEqual(self.pitchOut(match),
                         '[C4, G4, D5, A5, E6, B6, F#7, C#8, G#8, D#9, A#9, E#10, B#10]')

        # based on the original interval list, can get information on scale steps,
        # even for non-octave repeating scales
        self.assertEqual(net.getRelativeNodeDegree('c4', 1, 'e#10'), 3)

        # we can also search for realized and possible matches in a network
        edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        net = IntervalNetwork(edgeList)

        # if we know a realized version, we can test if pitches
        # match in that version; returns matched, not found, and no match lists
        # f i s found in a scale where e- is the tonic
        matched, unused_noMatch = net.match('e-', 1, 'f')
        self.assertEqual(self.pitchOut(matched), '[F]')

        # can search a list of pitches, isolating non-scale tones
        # if e- is the tonic, which pitches are part of the scale
        matched, noMatch = net.match('e-', 1, ['b-', 'd-', 'f'])
        self.assertEqual(self.pitchOut(matched), '[B-, F]')
        self.assertEqual(self.pitchOut(noMatch), '[D-]')

        # finally, can search the unrealized network; all possible realizations
        # are tested, and the matched score is returned
        # the first top 4 results are returned by default

        # in this case, the nearest major keys are G and D
        results = net.find(['g', 'a', 'b', 'd', 'f#'])
        self.assertEqual(str(results),
                         '[(5, <music21.pitch.Pitch G>), (5, <music21.pitch.Pitch D>), '
                         + '(4, <music21.pitch.Pitch A>), (4, <music21.pitch.Pitch C>)]')

        # with an f#, D is the most-matched first node pitch
        results = net.find(['g', 'a', 'b', 'c#', 'd', 'f#'])
        self.assertEqual(str(results),
                         '[(6, <music21.pitch.Pitch D>), (5, <music21.pitch.Pitch A>), '
                         + '(5, <music21.pitch.Pitch G>), (4, <music21.pitch.Pitch E>)]')

    def testHarmonyModel(self):
        # can define a chord type as a sequence of intervals
        # to assure octave redundancy, must provide top-most interval to octave
        # this could be managed in specialized subclass

        edgeList = ['M3', 'm3', 'P4']
        net = IntervalNetwork(edgeList)

        # if g# is the root, or first node
        match = net.realizePitch('g#', 1)
        self.assertEqual(self.pitchOut(match), '[G#4, B#4, D#5, G#5]')

        # if g# is the fifth, or third node
        # a specialized subclass can handle this mapping
        match = net.realizePitch('g#', 3)
        self.assertEqual(self.pitchOut(match), '[C#4, E#4, G#4, C#5]')

        # if g# is the third, or second node, across a wide range
        match = net.realizePitch('g#', 2, 'c2', 'c5')
        self.assertEqual(self.pitchOut(match), '[E2, G#2, B2, E3, G#3, B3, E4, G#4, B4]')

        # can match pitches to a realization of this chord
        # given a chord built form node 2 as g#, are e2 and b6 in this network
        matched, unused_noMatch = net.match('g#', 2, ['e2', 'b6'])
        self.assertEqual(self.pitchOut(matched), '[E2, B6]')

        # can find a first node (root) that match any provided pitches
        # this is independent of any realization
        results = net.find(['c', 'e', 'g'])
        self.assertEqual(str(results),
                         '[(3, <music21.pitch.Pitch C>), (1, <music21.pitch.Pitch A>), '
                         + '(1, <music21.pitch.Pitch G#>), (1, <music21.pitch.Pitch G>)]')

        # in this case, most likely an e triad
        results = net.find(['e', 'g#'])
        self.assertEqual(str(results),
                         '[(2, <music21.pitch.Pitch E>), (1, <music21.pitch.Pitch A>), '
                         + '(1, <music21.pitch.Pitch G#>), (1, <music21.pitch.Pitch D->)]')

        # we can do the same with larger or more complicated chords
        # again, we must provide the interval to the octave
        edgeList = ['M3', 'm3', 'M3', 'm3', 'm7']
        net = IntervalNetwork(edgeList)
        match = net.realizePitch('c4', 1)
        self.assertEqual(self.pitchOut(match), '[C4, E4, G4, B4, D5, C6]')

        # if we want the same chord where c4 is the 5th node, or the ninth
        match = net.realizePitch('c4', 5)
        self.assertEqual(self.pitchOut(match), '[B-2, D3, F3, A3, C4, B-4]')

        # we can of course provide any group of pitches and find the value
        # of the lowest node that provides the best fit
        results = net.find(['e', 'g#', 'b', 'd#'])
        self.assertEqual(str(results),
                         '[(3, <music21.pitch.Pitch E>), (2, <music21.pitch.Pitch C>), '
                         + '(1, <music21.pitch.Pitch B>), (1, <music21.pitch.Pitch G#>)]')

    def testScaleAndHarmony(self):
        # start with a major scale
        edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        netScale = IntervalNetwork(edgeList)

        # take a half diminished seventh chord
        edgeList = ['m3', 'm3', 'M3', 'M2']
        netHarmony = IntervalNetwork(edgeList)
        match = netHarmony.realizePitch('b4', 1)
        self.assertEqual(self.pitchOut(match), '[B4, D5, F5, A5, B5]')

        # given a half dim seventh chord built on c#, what scale contains
        # these pitches?
        results = netScale.find(netHarmony.realizePitch('c#', 1))
        # most likely, a  D
        self.assertEqual(str(results),
                         '[(5, <music21.pitch.Pitch D>), (4, <music21.pitch.Pitch B>), '
                         + '(4, <music21.pitch.Pitch A>), (4, <music21.pitch.Pitch E>)]')
        # what scale degree is c# in this scale? the seventh
        self.assertEqual(netScale.getRelativeNodeDegree('d', 1, 'c#'), 7)

    def testGraphedOutput(self):
        # note this relies on networkx
        edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        unused_netScale = IntervalNetwork(edgeList)
        # netScale.plot(pitchObj='F#', nodeId=3, minPitch='c2', maxPitch='c5')

    def testBasicA(self):
        edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        net = IntervalNetwork()
        net.fillBiDirectedEdges(edgeList)

        self.assertEqual(sorted(list(net.edges.keys())),
                         [0, 1, 2, 3, 4, 5, 6])

        # must convert to string to compare int to Terminus
        self.assertEqual(sorted([str(x) for x in net.nodes.keys()]),
                         ['0', '1', '2', '3', '4', '5', 'Terminus.HIGH', 'Terminus.LOW'])

        self.assertEqual(repr(net.nodes[0]), '<music21.scale.intervalNetwork.Node id=0>')
        self.assertEqual(repr(net.nodes[Terminus.LOW]),
                         '<music21.scale.intervalNetwork.Node id=Terminus.LOW>')

        self.assertEqual(
            repr(net.edges[0]),
            '<music21.scale.intervalNetwork.Edge Direction.BI M2 '
            + '[(Terminus.LOW, 0), (0, Terminus.LOW)]>'
        )

        self.assertEqual(
            repr(net.edges[3]),
            '<music21.scale.intervalNetwork.Edge Direction.BI M2 [(2, 3), (3, 2)]>')

        self.assertEqual(
            repr(net.edges[6]),
            '<music21.scale.intervalNetwork.Edge Direction.BI m2 '
            + '[(5, Terminus.HIGH), (Terminus.HIGH, 5)]>'
        )

        # getting connections: can filter by direction
        self.assertEqual(
            repr(net.edges[6].getConnections(Direction.ASCENDING)),
            '[(5, Terminus.HIGH)]'
        )
        self.assertEqual(
            repr(net.edges[6].getConnections(Direction.DESCENDING)),
            '[(Terminus.HIGH, 5)]'
        )
        self.assertEqual(
            repr(net.edges[6].getConnections(Direction.BI)),
            '[(5, Terminus.HIGH), (Terminus.HIGH, 5)]'
        )

        # in calling get next, get a lost of edges and a lost of nodes that all
        # describe possible pathways
        self.assertEqual(
            net.getNext(net.nodes[Terminus.LOW], Direction.ASCENDING),
            ([net.edges[0]], [net.nodes[0]])
        )

        self.assertEqual(
            net.getNext(net.nodes[Terminus.LOW], Direction.DESCENDING),
            ([net.edges[6]], [net.nodes[5]])
        )

        self.assertEqual(self.pitchOut(net.realizePitch('c4', 1)),
                         '[C4, D4, E4, F4, G4, A4, B4, C5]')

        self.assertEqual(self.pitchOut(net.realizePitch('c4', 1, maxPitch='c6')),
                         '[C4, D4, E4, F4, G4, A4, B4, C5, D5, E5, F5, G5, A5, B5, C6]')

        self.assertEqual(self.pitchOut(net.realizePitch('c4', 1, minPitch='c3')),
                         '[C3, D3, E3, F3, G3, A3, B3, C4, D4, E4, F4, G4, A4, B4, C5]')

        self.assertEqual(self.pitchOut(net.realizePitch('c4', 1, minPitch='c3', maxPitch='c6')),
                         '[C3, D3, E3, F3, G3, A3, B3, C4, D4, E4, '
                         + 'F4, G4, A4, B4, C5, D5, E5, F5, G5, A5, B5, C6]')

        self.assertEqual(self.pitchOut(net.realizePitch('f4', 1, minPitch='c3', maxPitch='c6')),
                         '[C3, D3, E3, F3, G3, A3, B-3, C4, D4, E4, '
                         + 'F4, G4, A4, B-4, C5, D5, E5, F5, G5, A5, B-5, C6]')

        self.assertEqual(self.pitchOut(net.realizePitch('C#', 7)),
                         '[D3, E3, F#3, G3, A3, B3, C#4, D4]')

        self.assertEqual(self.pitchOut(net.realizePitch('C#4', 7, 'c8', 'c9')),
                         '[C#8, D8, E8, F#8, G8, A8, B8]')

        self.assertEqual(self.realizePitchOut(net.realize('c4', 1)),
                         '([C4, D4, E4, F4, G4, A4, B4, C5], '
                         + '[Terminus.LOW, 0, 1, 2, 3, 4, 5, Terminus.HIGH])')

        self.assertEqual(self.realizePitchOut(net.realize('c#4', 7)),
                         '([D3, E3, F#3, G3, A3, B3, C#4, D4], '
                         + '[Terminus.LOW, 0, 1, 2, 3, 4, 5, Terminus.HIGH])')

    def testDirectedA(self):
        # test creating a harmonic minor scale by using two complete
        # ascending and descending scales

        ascendingEdgeList = ['M2', 'm2', 'M2', 'M2', 'M2', 'M2', 'm2']
        # these are given in ascending order
        descendingEdgeList = ['M2', 'm2', 'M2', 'M2', 'm2', 'M2', 'M2']

        net = IntervalNetwork()
        net.fillDirectedEdges(ascendingEdgeList, descendingEdgeList)

        # returns a list of edges and notes
        self.assertEqual(
            repr(net.getNext(net.nodes[Terminus.LOW], Direction.ASCENDING)),
            '([<music21.scale.intervalNetwork.Edge Direction.ASCENDING M2 '
            + '[(Terminus.LOW, 0)]>], [<music21.scale.intervalNetwork.Node id=0>])')

        self.assertEqual(
            repr(net.getNext(net.nodes[Terminus.LOW], Direction.DESCENDING)),
            '([<music21.scale.intervalNetwork.Edge Direction.DESCENDING M2 '
            + '[(Terminus.HIGH, 11)]>], [<music21.scale.intervalNetwork.Node id=11>])')

        # high terminus gets the same result, as this is the wrapping point
        self.assertEqual(
            repr(net.getNext(net.nodes[Terminus.HIGH], Direction.ASCENDING)),
            '([<music21.scale.intervalNetwork.Edge Direction.ASCENDING M2 '
            + '[(Terminus.LOW, 0)]>], [<music21.scale.intervalNetwork.Node id=0>])')

        self.assertEqual(
            repr(net.getNext(net.nodes[Terminus.LOW], Direction.DESCENDING)),
            '([<music21.scale.intervalNetwork.Edge Direction.DESCENDING M2 '
            + '[(Terminus.HIGH, 11)]>], [<music21.scale.intervalNetwork.Node id=11>])')

        # this is ascending from a4 to a5, then descending from a4 to a3
        # this seems like the right thing to do
        self.assertEqual(self.realizePitchOut(net.realize('a4', 1, 'a3', 'a5')),
                         '([A3, B3, C4, D4, E4, F4, G4, A4, B4, C5, D5, E5, F#5, G#5, A5], '
                         + '[Terminus.LOW, 6, 7, 8, 9, 10, 11, '
                         + 'Terminus.LOW, 0, 1, 2, 3, 4, 5, Terminus.HIGH])')

        # can get a descending form by setting reference pitch to top of range
        self.assertEqual(self.pitchOut(net.realizePitch('a5', 1, 'a4', 'a5')),
                         '[A4, B4, C5, D5, E5, F5, G5, A5]')

        # can get a descending form by setting reference pitch to top of range
        self.assertEqual(self.pitchOut(net.realizePitch('a4', 1, 'a4', 'a5')),
                         '[A4, B4, C5, D5, E5, F#5, G#5, A5]')

        # if we try to get a node by a name that is a degree, we will get
        # two results, as one is the ascending and one is the descending
        # form
        self.assertEqual(
            str(net.nodeNameToNodes(3)),
            '[<music21.scale.intervalNetwork.Node id=1>, '
            + '<music21.scale.intervalNetwork.Node id=7>]')
        self.assertEqual(
            str(net.nodeNameToNodes(7)),
            '[<music21.scale.intervalNetwork.Node id=5>, '
            + '<music21.scale.intervalNetwork.Node id=11>]')
        # net.plot()

    def testScaleArbitrary(self):
        sc1 = scale.MajorScale('g')
        self.assertEqual(sorted([str(x) for x in sc1.abstract._net.nodes.keys()]),
                         ['0', '1', '2', '3', '4', '5', 'Terminus.HIGH', 'Terminus.LOW'])
        self.assertEqual(sorted(sc1.abstract._net.edges.keys()),
                         [0, 1, 2, 3, 4, 5, 6])

        nodes = ({'id': Terminus.LOW, 'degree': 1},
                 {'id': 0, 'degree': 2},
                 {'id': Terminus.HIGH, 'degree': 3},
                 )

        edges = ({'interval': 'm2',
                  'connections': (
                      [Terminus.LOW, 0, Direction.BI],
                  )},
                 {'interval': 'M3',
                  'connections': (
                      [0, Terminus.HIGH, Direction.BI],
                  )},
                 )

        net = IntervalNetwork()
        net.fillArbitrary(nodes, edges)
        self.assertTrue(common.whitespaceEqual(str(net.edges),
                                               '''
            OrderedDict([(0, <music21.scale.intervalNetwork.Edge Direction.BI m2
                                [(Terminus.LOW, 0), (0, Terminus.LOW)]>),
                         (1, <music21.scale.intervalNetwork.Edge Direction.BI M3
                                [(0, Terminus.HIGH), (Terminus.HIGH, 0)]>)])'''
                                               ),
                        str(net.edges))

        self.assertEqual(net.degreeMax, 3)
        self.assertEqual(net.degreeMaxUnique, 2)

        self.assertEqual(self.pitchOut(net.realizePitch('c4', 1)), '[C4, D-4, F4]')

    def testRealizeDescending(self):
        edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        net = IntervalNetwork()
        net.fillBiDirectedEdges(edgeList)

        pitches, nodes = net.realizeDescending('c3', 1, 'c2')
        self.assertEqual(self.pitchOut(pitches),
                         '[C2, D2, E2, F2, G2, A2, B2]')
        self.assertEqual(str(nodes),
                         '[Terminus.LOW, 0, 1, 2, 3, 4, 5]'
                         )

        self.assertEqual(
            self.realizePitchOut(net.realizeDescending('c3', Terminus.HIGH, minPitch='c2')),
            '([C2, D2, E2, F2, G2, A2, B2], [Terminus.LOW, 0, 1, 2, 3, 4, 5])'
        )

        # this only gets one pitch as this is descending and includes reference
        # pitch
        self.assertEqual(str(net.realizeDescending('c3', 1, includeFirst=True)),
                         '([<music21.pitch.Pitch C3>], [Terminus.LOW])')

        self.assertTrue(
            common.whitespaceEqual(
                self.realizePitchOut(net.realizeDescending('g3', 1, 'g0', includeFirst=True)),
                '''([G0, A0, B0, C1, D1, E1, F#1,
                     G1, A1, B1, C2, D2, E2, F#2,
                     G2, A2, B2, C3, D3, E3, F#3, G3],
                    [Terminus.LOW, 0, 1, 2, 3, 4, 5,
                     Terminus.LOW, 0, 1, 2, 3, 4, 5,
                     Terminus.LOW, 0, 1, 2, 3, 4, 5,
                     Terminus.LOW])'''
            )
        )

        self.assertEqual(self.realizePitchOut(
            net.realizeDescending('d6', 5, 'd4', includeFirst=True)),
            '([D4, E4, F#4, G4, A4, B4, C5, D5, E5, F#5, G5, A5, B5, C6, D6], '
            + '[3, 4, 5, Terminus.LOW, 0, 1, 2, 3, 4, 5, Terminus.LOW, 0, 1, 2, 3])'
        )

        self.assertEqual(self.realizePitchOut(net.realizeAscending('c3', 1)),
                         '([C3, D3, E3, F3, G3, A3, B3, C4], '
                         + '[Terminus.LOW, 0, 1, 2, 3, 4, 5, Terminus.HIGH])')

        self.assertEqual(self.realizePitchOut(net.realizeAscending('g#2', 3)),
                         '([G#2, A2, B2, C#3, D#3, E3], [1, 2, 3, 4, 5, Terminus.HIGH])')

        self.assertEqual(self.realizePitchOut(net.realizeAscending('g#2', 3, maxPitch='e4')),
                         '([G#2, A2, B2, C#3, D#3, E3, F#3, G#3, A3, B3, C#4, D#4, E4], '
                         + '[1, 2, 3, 4, 5, Terminus.HIGH, 0, 1, 2, 3, 4, 5, Terminus.HIGH])')

    def testBasicB(self):
        net = IntervalNetwork()
        net.fillMelodicMinor()

        self.assertEqual(self.realizePitchOut(net.realize('g4')),
                         '([G4, A4, B-4, C5, D5, E5, F#5, G5], '
                         + '[Terminus.LOW, 0, 1, 2, 3, 4, 6, Terminus.HIGH])')

        # here, min and max pitches are assumed based on ascending scale
        # otherwise, only a single pitch would be returned (the terminus low)
        self.assertEqual(
            self.realizePitchOut(net.realize('g4', 1, direction=Direction.DESCENDING)),
            '([G4, A4, B-4, C5, D5, E-5, F5, G5], '
            + '[Terminus.LOW, 0, 1, 2, 3, 5, 7, Terminus.LOW])')

        # if explicitly set terminus to high, we get the expected range,
        # but now the reference pitch is the highest pitch
        self.assertEqual(
            self.realizePitchOut(net.realize('g4', Terminus.HIGH, direction=Direction.DESCENDING)),
            '([G3, A3, B-3, C4, D4, E-4, F4, G4], '
            + '[Terminus.LOW, 0, 1, 2, 3, 5, 7, Terminus.HIGH])'
        )

        # get nothing from if try to request a descending scale from the
        # lower terminus
        self.assertEqual(
            net.realizeDescending('g4', Terminus.LOW, fillMinMaxIfNone=False),
            ([], [])
        )

        self.assertEqual(
            self.realizePitchOut(net.realizeDescending('g4', Terminus.LOW, fillMinMaxIfNone=True)),
            '([G4, A4, B-4, C5, D5, E-5, F5], [Terminus.LOW, 0, 1, 2, 3, 5, 7])')

        # if we include first, we get all values
        descReal = net.realizeDescending('g4',
                                         Terminus.LOW,
                                         includeFirst=True,
                                         fillMinMaxIfNone=True)
        self.assertEqual(self.realizePitchOut(descReal),
                         '([G4, A4, B-4, C5, D5, E-5, F5, G5], '
                         + '[Terminus.LOW, 0, 1, 2, 3, 5, 7, Terminus.LOW])')

        # because this is octave repeating, we can get a range when min
        # and max are defined
        descReal = net.realizeDescending('g4', Terminus.LOW, 'g4', 'g5')
        self.assertEqual(self.realizePitchOut(descReal),
                         '([G4, A4, B-4, C5, D5, E-5, F5], [Terminus.LOW, 0, 1, 2, 3, 5, 7])')

    def testGetPitchFromNodeStep(self):
        net = IntervalNetwork()
        net.fillMelodicMinor()
        self.assertEqual(str(net.getPitchFromNodeDegree('c4', 1, 1)), 'C4')
        self.assertEqual(str(net.getPitchFromNodeDegree('c4', 1, 5)), 'G4')

        #         # ascending is default
        self.assertEqual(str(net.getPitchFromNodeDegree('c4', 1, 6)), 'A4')

        self.assertEqual(
            str(net.getPitchFromNodeDegree('c4', 1, 6, direction=Direction.ASCENDING)),
            'A4'
        )

        # environLocal.printDebug(['descending degree 6'])

        self.assertEqual(
            str(net.getPitchFromNodeDegree('c4', 1, 6, direction=Direction.DESCENDING)),
            'A-4'
        )

    def testNextPitch(self):
        net = IntervalNetwork()
        net.fillMelodicMinor()

        # ascending from known pitches
        self.assertEqual(str(net.nextPitch('c4', 1, 'g4', direction=Direction.ASCENDING)),
                         'A4')
        self.assertEqual(str(net.nextPitch('c4', 1, 'a4', direction=Direction.ASCENDING)),
                         'B4')
        self.assertEqual(str(net.nextPitch('c4', 1, 'b4', direction=Direction.ASCENDING)),
                         'C5')

        # descending
        self.assertEqual(str(net.nextPitch('c4', 1, 'c5', direction=Direction.DESCENDING)),
                         'B-4')
        self.assertEqual(str(net.nextPitch('c4', 1, 'b-4', direction=Direction.DESCENDING)),
                         'A-4')
        self.assertEqual(str(net.nextPitch('c4', 1, 'a-4',
                                           direction=Direction.DESCENDING)),
                         'G4')

        # larger degree sizes
        self.assertEqual(str(net.nextPitch('c4', 1, 'c5',
                                           direction=Direction.DESCENDING,
                                           stepSize=2)),
                         'A-4')
        self.assertEqual(str(net.nextPitch('c4', 1, 'a4',
                                           direction=Direction.ASCENDING,
                                           stepSize=2)),
                         'C5')

        # moving from a non-scale degree

        # if we get the ascending neighbor, we move from the d to the e-
        self.assertEqual(
            str(
                net.nextPitch(
                    'c4', 1, 'c#4',
                    direction=Direction.ASCENDING,
                    getNeighbor=Direction.ASCENDING
                )
            ),
            'E-4'
        )

        # if we get the descending neighbor, we move from c to d
        self.assertEqual(str(net.nextPitch('c4', 1, 'c#4',
                                           direction=Direction.ASCENDING,
                                           getNeighbor=Direction.DESCENDING)),
                         'D4')

        # if on a- and get ascending neighbor, move from a to b-
        self.assertEqual(str(net.nextPitch('c4', 1, 'a-',
                                           direction=Direction.ASCENDING,
                                           getNeighbor=Direction.ASCENDING)),
                         'B4')

        # if on a- and get descending neighbor, move from g to a
        self.assertEqual(str(net.nextPitch('c4', 1, 'a-',
                                           direction=Direction.ASCENDING,
                                           getNeighbor=Direction.DESCENDING)),
                         'A4')

        # if on b, ascending neighbor, move from c to b-
        self.assertEqual(str(net.nextPitch('c4', 1, 'b3',
                                           direction=Direction.DESCENDING,
                                           getNeighbor=Direction.ASCENDING)),
                         'B-3')

        # if on c-4, use mode derivation instead of neighbor, move from b4 to c4
        self.assertEqual(str(net.nextPitch('c4', 1, 'c-4',
                                           direction=Direction.ASCENDING)),
                         'C4')

        self.assertEqual(
            net.getNeighborNodeIds(pitchReference='c4', nodeName=1, pitchTarget='c#'),
            (Terminus.HIGH, 0)
        )

        self.assertEqual(
            net.getNeighborNodeIds(pitchReference='c4', nodeName=1, pitchTarget='d#'),
            (1, 2)
        )

        self.assertEqual(
            net.getNeighborNodeIds(pitchReference='c4', nodeName=1, pitchTarget='b'),
            (6, Terminus.HIGH)
        )

        self.assertEqual(
            net.getNeighborNodeIds(
                pitchReference='c4',
                nodeName=1,
                pitchTarget='b-'),
            (4, 6)
        )

        self.assertEqual(
            net.getNeighborNodeIds(
                pitchReference='c4',
                nodeName=1,
                pitchTarget='b',
                direction=Direction.DESCENDING),
            (7, Terminus.LOW))

        self.assertEqual(
            net.getNeighborNodeIds(
                pitchReference='c4',
                nodeName=1,
                pitchTarget='b-',
                direction=Direction.DESCENDING),
            (7, Terminus.LOW))

        # if on b, descending neighbor, move from b- to a-
        self.assertEqual(
            str(net.nextPitch(
                'c4',
                1,
                'b4',
                direction=Direction.DESCENDING,
                getNeighbor=Direction.DESCENDING)),
            'A-4')

    def test_realize_descending_reversed_cached(self):
        net = IntervalNetwork()
        net.fillMelodicMinor()

        descending_melodic_minor, _ = net.realizeDescending(
            'C4', minPitch='C4', maxPitch='C5', reverse=False)
        self.assertEqual(descending_melodic_minor[0].nameWithOctave, 'B-4')
        self.assertEqual(descending_melodic_minor[-1].nameWithOctave, 'C4')

        descending_melodic_minor_reversed, _ = net.realizeDescending(
            'C4', minPitch='C4', maxPitch='C5', reverse=True)
        self.assertEqual(descending_melodic_minor_reversed[0].nameWithOctave, 'C4')  # was B-4
        self.assertEqual(descending_melodic_minor_reversed[-1].nameWithOctave, 'B-4')  # was C4


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
