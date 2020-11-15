# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         scale.intervalNetwork.py
# Purpose:      A graph of intervals, for scales and harmonies.
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2010-2012, 2015-16 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
An IntervalNetwork defines a scale or harmonic unit as a (weighted)
digraph, or directed graph, where pitches are nodes and intervals are
edges. Nodes, however, are not stored; instead, an ordered list of edges
(Intervals) is provided as an archetype of adjacent nodes.

IntervalNetworks are unlike conventional graphs in that each graph must
define a low and high terminus. These points are used to create a cyclic
graph and are treated as point of cyclical overlap.

IntervalNetwork permits the definition of conventional octave repeating
scales or harmonies (abstract chords), non-octave repeating scales and
chords, and ordered interval sequences that might move in multiple
directions.

A scale or harmony may be composed of one or more IntervalNetwork objects.

Both nodes and edges can be weighted to suggest tonics, dominants,
finals, or other attributes of the network.
'''
import copy
import unittest

from collections import OrderedDict
try:
    import networkx
except ImportError:
    # lacking this does nothing
    networkx = None
    # _missingImport.append('networkx')

from music21 import exceptions21
from music21 import interval
from music21 import common
from music21 import pitch
from music21 import prebase

from music21 import environment
_MOD = 'scale.intervalNetwork'
environLocal = environment.Environment(_MOD)


# these are just symbols/place holders; values do not matter as long
# as they are not positive ints
TERMINUS_LOW = 'terminusLow'
TERMINUS_HIGH = 'terminusHigh'
DIRECTION_BI = 'bi'
DIRECTION_ASCENDING = 'ascending'
DIRECTION_DESCENDING = 'descending'


def _gte(a, b):
    '''
    check if a > b or abs(a - b) < epsilon
    '''
    if a > b:
        return True
    elif abs(a - b) < 0.00001:
        return True
    return False


def _lte(a, b):
    '''
    check if a < b or abs(a - b) < epsilon
    '''
    if a < b:
        return True
    elif abs(a - b) < 0.00001:
        return True
    return False


# a dictionary of dicts.  First level is simplificationMethod: innerDict
# innerDict maps the repr of an interval object to a nameWithAccidental
_transposePitchAndApplySimplificationCache = {}


class EdgeException(exceptions21.Music21Exception):
    pass


class Edge(prebase.ProtoM21Object):
    '''
    Abstraction of an Interval as an Edge.

    Edges store an Interval object as well as a pathway direction specification.
    The pathway is the route through the network from terminus to terminus,
    and can either by ascending or descending.

    For directed Edges, the direction of the Interval may be used to
    suggest non-pitch ascending movements (even if the pathway direction is ascending).

    Weight values, as well as other attributes, can be stored.

    >>> i = interval.Interval('M3')
    >>> e = scale.intervalNetwork.Edge(i)
    >>> e.interval is i
    True
    >>> e.direction
    'bi'

    Return the stored Interval object

    >>> i = interval.Interval('M3')
    >>> e1 = scale.intervalNetwork.Edge(i, id=0)
    >>> n1 = scale.intervalNetwork.Node(id=0)
    >>> n2 = scale.intervalNetwork.Node(id=1)
    >>> e1.addDirectedConnection(n1, n2, 'ascending')
    >>> e1.interval
    <music21.interval.Interval M3>

    Return the direction of the Edge.

    >>> i = interval.Interval('M3')
    >>> e1 = scale.intervalNetwork.Edge(i, id=0)
    >>> n1 = scale.intervalNetwork.Node(id=0)
    >>> n2 = scale.intervalNetwork.Node(id=1)
    >>> e1.addDirectedConnection(n1, n2, 'ascending')
    >>> e1.direction
    'ascending'
    '''
    # pylint: disable=redefined-builtin

    def __init__(self,
                 intervalData=None,
                 id=None,  # id is okay: @ReservedAssignment
                 direction=DIRECTION_BI):
        if isinstance(intervalData, str):
            i = interval.Interval(intervalData)
        else:
            i = intervalData
        self.interval = i
        # direction will generally be set when connections added
        self.direction = direction  # can be bi, ascending, descending
        self.weight = 1.0
        # store id
        self.id = id

        # one or two pairs of Node ids that this Edge connects
        # if there are two, it is a bidirectional, w/ first ascending
        self._connections = []

    def __eq__(self, other):
        '''

        >>> i1 = interval.Interval('M3')
        >>> i2 = interval.Interval('M3')
        >>> i3 = interval.Interval('m3')
        >>> e1 = scale.intervalNetwork.Edge(i1)
        >>> e2 = scale.intervalNetwork.Edge(i2)
        >>> e3 = scale.intervalNetwork.Edge(i3)
        >>> e1 == e2
        True
        >>> e1 == e3
        False
        '''
        return (isinstance(other, self.__class__)
                and self.__dict__ == other.__dict__)

    def _reprInternal(self):
        return f'{self.direction} {self.interval.name} {self._connections!r}'

    def addDirectedConnection(self, node1, node2, direction=None):
        '''
        Provide two Node objects that are connected by this Edge,
        in the direction from the first to the second.

        When calling directly, a direction, either
        ascending or descending, should be set here;
        this will override whatever the interval is.
        If None, this will not be set.

        >>> i = interval.Interval('M3')
        >>> e1 = scale.intervalNetwork.Edge(i, id=0)

        >>> n1 = scale.intervalNetwork.Node(id=0)
        >>> n2 = scale.intervalNetwork.Node(id=1)

        >>> e1.addDirectedConnection(n1, n2, 'ascending')
        >>> e1.connections
        [(0, 1)]
        >>> e1
        <music21.scale.intervalNetwork.Edge ascending M3 [(0, 1)]>
        '''
        # may be Node objects, or number, or string
        if isinstance(node1, str) or common.isNum(node1):
            n1Id = node1
        else:  # assume an Node
            n1Id = node1.id

        if isinstance(node2, str) or common.isNum(node2):
            n2Id = node2
        else:  # assume an Node
            n2Id = node2.id

        self._connections.append((n1Id, n2Id))

        # must specify a direction
        if (direction not in [DIRECTION_ASCENDING, DIRECTION_DESCENDING]):
            raise EdgeException('must request a direction')
        self.direction = direction

    def addBiDirectedConnections(self, node1, node2):
        '''
        Provide two Edge objects that pass through
        this Node, in the direction from the first to the second.

        >>> i = interval.Interval('M3')
        >>> e1 = scale.intervalNetwork.Edge(i, id=0)
        >>> n1 = scale.intervalNetwork.Node(id='terminusLow')
        >>> n2 = scale.intervalNetwork.Node(id=1)

        >>> e1.addBiDirectedConnections(n1, n2)
        >>> e1.connections
        [('terminusLow', 1), (1, 'terminusLow')]
        >>> e1
        <music21.scale.intervalNetwork.Edge bi M3 [('terminusLow', 1), (1, 'terminusLow')]>
        '''
        # must assume here that n1 to n2 is ascending; need to know
        self.addDirectedConnection(node1, node2, DIRECTION_ASCENDING)
        self.addDirectedConnection(node2, node1, DIRECTION_DESCENDING)
        self.direction = DIRECTION_BI  # can be ascending, descending

    def getConnections(self, direction=None):
        '''
        Callable as a property (.connections) or as a method
        (.getConnections(direction)):

        Return a list of connections between Nodes, represented as pairs
        of Node ids. If a direction is specified, and if the Edge is
        directional, only the desired directed values will be returned.


        >>> i = interval.Interval('M3')
        >>> e1 = scale.intervalNetwork.Edge(i, id=0)
        >>> n1 = scale.intervalNetwork.Node(id='terminusLow')
        >>> n2 = scale.intervalNetwork.Node(id=1)

        >>> e1.addBiDirectedConnections(n1, n2)
        >>> e1.connections
        [('terminusLow', 1), (1, 'terminusLow')]
        >>> e1.getConnections('ascending')
        [('terminusLow', 1)]
        >>> e1.getConnections('descending')
        [(1, 'terminusLow')]

        '''
        if direction is None:
            direction = self.direction  # assign native direction

        # do not need to supply direction, because direction is defined
        # in this Edge.
        if self.direction == direction:
            return self._connections

        # if requesting bi from a mono directional edge is an error
        if (direction in [DIRECTION_BI]
                and self.direction in [DIRECTION_ASCENDING, DIRECTION_DESCENDING]):
            raise EdgeException('cannot request a bi direction from a mono direction')

        # if bi and we get an ascending/descending request
        if (direction in [DIRECTION_ASCENDING, DIRECTION_DESCENDING]
                and self.direction == DIRECTION_BI):

            # assume that in a bi-representation, the first is ascending
            # the second is descending
            # NOTE: this may not mean that we are actually ascending, we may
            # use the direction of the interval to determine
            if direction == DIRECTION_ASCENDING:
                return [self._connections[0]]
            elif direction == DIRECTION_DESCENDING:
                return [self._connections[1]]
        # if no connections are possible, return none
        return None

    # keep separate property, since getConnections takes a direction argument.
    connections = property(getConnections)


class Node(prebase.ProtoM21Object, common.SlottedObjectMixin):
    '''
    Abstraction of an unrealized Pitch Node.

    The Node `id` is used to store connections in Edges and has no real meaning.

    Terminal Nodes have special ids: 'terminusLow', 'terminusHigh'

    The Node `degree` is translated to scale degrees in various applications,
    and is used to request a pitch from the network.

    The `weight` attribute is used to probabilistically select between
    multiple nodes when multiple nodes satisfy either a branching option in a pathway
    or a request for a degree.

    TODO: replace w/ NamedTuple; eliminate id, and have a terminus: low, high, None
    '''
    __slots__ = ('id', 'degree', 'weight')

    # pylint: disable=redefined-builtin
    def __init__(self, id=None, degree=None, weight=1.0):  # id is okay: @ReservedAssignment
        # store id, either as string, such as terminusLow, or a number.
        # ids are unique to any node in the network
        self.id = id
        # the degree is used to define ordered node counts from the bottom
        # the degree is analogous to scale degree or degree
        # more than one node may have the same degree
        self.degree = degree
        # node weight might be used to indicate importance of scale positions
        self.weight = weight

    def __hash__(self):
        hashTuple = (self.id, self.degree, self.weight)
        return hash(hashTuple)

    def __eq__(self, other):
        '''
        Nodes are equal if everything in the object.__slots__ is equal.

        >>> n1 = scale.intervalNetwork.Node(id=3)
        >>> n2 = scale.intervalNetwork.Node(id=3)
        >>> n3 = scale.intervalNetwork.Node(id=2)
        >>> n1 == n2
        True
        >>> n1 == n3
        False
        >>> n2.weight = 2.0
        >>> n1 == n2
        False
        '''
        return hash(self) == hash(other)

    def _reprInternal(self):
        return f'id={self.id!r}'


# ------------------------------------------------------------------------------
class IntervalNetworkException(exceptions21.Music21Exception):
    pass


# presently edges are interval objects, can be marked as
# ascending, descending, or bi-directional
# edges are stored in dictionary by index values

# nodes are undefined pitches; pitches are realized on demand
# nodes are stored as an unordered list of coordinate pairs
# pairs are edge indices: showing which edges connect to this node
# could model multiple connections within an object

# up:    a M2 b m2 C M2 D
# down:  a M2 b   m3    D

# edges M2(1+-), m2(2+), M2(3+)
# edges m3(4-)


# ------------------------------------------------------------------------------

class IntervalNetwork:
    '''
    A graph of undefined Pitch nodes connected by a defined,
    ordered list of :class:`~music21.interval.Interval` objects as edges.

    An `octaveDuplicating` boolean, if defined, can be used
    to optimize pitch realization routines.

    The `deterministic` boolean, if defined, can be used to declare that there
    is no probabilistic or multi-pathway segments of this network.

    The `pitchSimplification` method specifies how to simplify the pitches
    if they spiral out into double and triple sharps, etc.  The default is
    'maxAccidental' which specifies that each note can have at most one
    accidental; double-flats and sharps are not allowed.  The other choices
    are 'simplifyEnharmonic' (which also converts C-, F-, B#, and E# to
    B, E, C, and F respectively, see :meth:`~music21.pitch.Pitch.simplifyEnharmonic`),
    'mostCommon' (which adds to simplifyEnharmonic the requirement that the
    most common accidental forms be used, so A# becomes B-, G- becomes
    F#, etc. the only ambiguity allowed is that both G# and A- are acceptable),
    and None (or 'none') which does not do any simplification.
    '''

    def __init__(self,
                 edgeList=None,
                 octaveDuplicating=False,
                 deterministic=True,
                 pitchSimplification='maxAccidental'):
        # store each edge with an index that is incremented when added
        # these values have no fixed meaning but are only for reference
        self.edgeIdCount = 0
        self.nodeIdCount = 0

        # a dictionary of Edge object, where keys are edgeIdCount values
        # Edges store directed connections between Node ids
        self.edges = OrderedDict()

        # nodes suggest Pitches, but Pitches are not stored
        self.nodes = OrderedDict()

        if edgeList is not None:  # auto initialize
            self.fillBiDirectedEdges(edgeList)

        # define if pitches duplicate each octave
        self.octaveDuplicating = octaveDuplicating
        self.deterministic = deterministic

        # could be 'simplifyEnharmonic', 'mostCommon' or None
        self.pitchSimplification = pitchSimplification

        # store segments
        self._ascendingCache = OrderedDict()
        self._descendingCache = OrderedDict()
        # store min/max, as this is evaluated before getting cache values
        self._minMaxCache = OrderedDict()
        self._nodeDegreeDictionaryCache = {}

    def clear(self):
        '''
        Remove and reset all Nodes and Edges.
        '''
        self.edgeIdCount = 0
        self.nodeIdCount = 0
        self.edges = OrderedDict()
        self.nodes = OrderedDict()
        self._ascendingCache = OrderedDict()
        self._descendingCache = OrderedDict()
        self._nodeDegreeDictionaryCache = {}

    def __eq__(self, other):
        '''

        >>> edgeList1 = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        >>> edgeList2 = ['M2', 'M2', 'm2', 'M2', 'A3', 'm2']

        >>> net1 = scale.intervalNetwork.IntervalNetwork()
        >>> net1.fillBiDirectedEdges(edgeList1)

        >>> net2 = scale.intervalNetwork.IntervalNetwork()
        >>> net2.fillBiDirectedEdges(edgeList1)

        >>> net3 = scale.intervalNetwork.IntervalNetwork()
        >>> net3.fillBiDirectedEdges(edgeList2)

        >>> net1 == net2
        True
        >>> net1 == net3
        False
        '''
        # compare all nodes and edges; if the same, and all keys are the same,
        # then matched
        return (isinstance(other, self.__class__)
                and self.__dict__ == other.__dict__)

    def fillBiDirectedEdges(self, edgeList):
        '''
        Given an ordered list of bi-directed edges given as :class:`~music21.interval.Interval`
        specifications, create and define appropriate Nodes. This
        assumes that all edges are bi-directed and all all edges are in order.

        >>> edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        >>> net = scale.intervalNetwork.IntervalNetwork()
        >>> net.nodes
        OrderedDict()
        >>> net.edges
        OrderedDict()


        >>> net.fillBiDirectedEdges(edgeList)
        >>> net.nodes
        OrderedDict([('terminusLow', <music21.scale.intervalNetwork.Node id='terminusLow'>),
                     (0, <music21.scale.intervalNetwork.Node id=0>),
                     (1, <music21.scale.intervalNetwork.Node id=1>),
                     ...
                     (5, <music21.scale.intervalNetwork.Node id=5>),
                     ('terminusHigh', <music21.scale.intervalNetwork.Node id='terminusHigh'>)])
        >>> net.edges
        OrderedDict([(0, <music21.scale.intervalNetwork.Edge bi M2
                            [('terminusLow', 0), (0, 'terminusLow')]>),
                     (1, <music21.scale.intervalNetwork.Edge bi M2 [(0, 1), (1, 0)]>),
                     (2, <music21.scale.intervalNetwork.Edge bi m2 [(1, 2), (2, 1)]>),
                     ...
                     (5, <music21.scale.intervalNetwork.Edge bi M2 [(4, 5), (5, 4)]>),
                     (6, <music21.scale.intervalNetwork.Edge bi m2
                            [(5, 'terminusHigh'), ('terminusHigh', 5)]>)])

        >>> [str(p) for p in net.realizePitch('g4')]
        ['G4', 'A4', 'B4', 'C5', 'D5', 'E5', 'F#5', 'G5']
        >>> net.degreeMin, net.degreeMax
        (1, 8)

        Using another fill method creates a new network

        >>> net.fillBiDirectedEdges(['M3', 'M3', 'M3'])
        >>> [str(p) for p in net.realizePitch('g4')]
        ['G4', 'B4', 'D#5', 'G5']
        >>> net.degreeMin, net.degreeMax
        (1, 4)

        >>> net.fillBiDirectedEdges([interval.Interval('M3'),
        ...                          interval.Interval('M3'),
        ...                          interval.Interval('M3')])
        >>> [str(p) for p in net.realizePitch('c2')]
        ['C2', 'E2', 'G#2', 'B#2']
        '''
        self.clear()

        degreeCount = 1  # steps start from one

        nLow = Node(id=TERMINUS_LOW, degree=degreeCount)
        degreeCount += 1
        self.nodes[nLow.id] = nLow

        nPrevious = nLow
        for i, eName in enumerate(edgeList):

            # first, create the next node
            if i < len(edgeList) - 1:  # if not last
                n = Node(id=self.nodeIdCount, degree=degreeCount)
                self.nodeIdCount += 1
                degreeCount += 1
                nFollowing = n
            else:  # if last
                # degree is same as start
                nHigh = Node(id=TERMINUS_HIGH, degree=degreeCount)
                nFollowing = nHigh

            # add to node dictionary
            self.nodes[nFollowing.id] = nFollowing

            # then, create edge and connection
            e = Edge(eName, id=self.edgeIdCount)
            self.edges[e.id] = e  # store
            self.edgeIdCount += 1

            e.addBiDirectedConnections(nPrevious, nFollowing)
            # update previous with the node created after this edge
            nPrevious = nFollowing

    def fillDirectedEdges(self, ascendingEdgeList, descendingEdgeList):
        '''
        Given two lists of edges, one for ascending :class:`~music21.interval.Interval`
        objects and
        another for  descending, construct appropriate Nodes and Edges.

        Note that the descending :class:`~music21.interval.Interval` objects
        should be given in ascending form.
        '''
        self.clear()

        # if both are equal, than assigning steps is easy
        if len(ascendingEdgeList) != len(descendingEdgeList):
            # problem here is that we cannot automatically assign degree values
            raise IntervalNetworkException('cannot manage unequal sized directed edges')

        degreeCount = 1  # steps start from one
        nLow = Node(id=TERMINUS_LOW, degree=degreeCount)
        degreeCount += 1
        self.nodes[nLow.id] = nLow

        nPrevious = nLow
        for i, eName in enumerate(ascendingEdgeList):

            # first, create the next node
            if i < len(ascendingEdgeList) - 1:  # if not last
                n = Node(id=self.nodeIdCount, degree=degreeCount)
                self.nodeIdCount += 1
                degreeCount += 1
                nFollowing = n
            else:  # if last
                nHigh = Node(id=TERMINUS_HIGH, degree=degreeCount)  # degree is same as start
                nFollowing = nHigh

            # add to node dictionary
            self.nodes[nFollowing.id] = nFollowing

            # then, create edge and connection; eName is interval
            e = Edge(eName, id=self.edgeIdCount)
            self.edges[e.id] = e
            self.edgeIdCount += 1

            e.addDirectedConnection(nPrevious, nFollowing,
                                    direction='ascending')
            # update previous with the node created after this edge
            nPrevious = nFollowing

        # repeat for descending, but reverse direction, and use
        # same low and high nodes
        degreeCount = 1  # steps start from one
        nLow = self.nodes[TERMINUS_LOW]  # get node; do not need to add
        degreeCount += 1
        nPrevious = nLow
        for i, eName in enumerate(descendingEdgeList):

            # first, create the next node
            if i < len(descendingEdgeList) - 1:  # if not last
                n = Node(id=self.nodeIdCount, degree=degreeCount)
                self.nodeIdCount += 1
                degreeCount += 1
                nFollowing = n
                # add to node dictionary
                self.nodes[nFollowing.id] = nFollowing
            else:  # if last
                nHigh = self.nodes[TERMINUS_HIGH]
                nFollowing = nHigh

            # then, create edge and connection
            e = Edge(eName, id=self.edgeIdCount)
            self.edges[e.id] = e
            self.edgeIdCount += 1

            # order here is reversed from above
            e.addDirectedConnection(nFollowing, nPrevious, direction='descending')
            # update previous with the node created after this edge
            nPrevious = nFollowing

    def fillArbitrary(self, nodes, edges):
        '''
        Fill any arbitrary network given node and edge definitions.

        Nodes must be defined by a dictionary of id and degree values.
        There must be a terminusLow and terminusHigh id as string::

            nodes = ({'id':'terminusLow', 'degree':1},
                     {'id':0, 'degree':2},
                     {'id':'terminusHigh', 'degree':3},
                    )

        Edges must be defined by a dictionary of :class:`~music21.interval.Interval`
        strings and connections. Id values will be automatically assigned.
        Each connection must define direction and pairs of valid node ids::

            edges = ({'interval':'m2', connections:(
                            ['terminusLow', 0, 'bi'],
                        )},
                    {'interval':'M3', connections:(
                            [0, 'terminusHigh', 'bi'],
                        )},
                    )



        >>> nodes = ({'id':'terminusLow', 'degree':1},
        ...          {'id':0, 'degree':2},
        ...          {'id':'terminusHigh', 'degree':3})
        >>> edges = ({'interval':'m2', 'connections':(['terminusLow', 0, 'bi'],)},
        ...          {'interval':'M3', 'connections':([0, 'terminusHigh', 'bi'],)},)

        >>> net = scale.intervalNetwork.IntervalNetwork()
        >>> net.fillArbitrary(nodes, edges)
        >>> net.realizePitch('c4', 1)
        [<music21.pitch.Pitch C4>, <music21.pitch.Pitch D-4>, <music21.pitch.Pitch F4>]
        '''
        self.clear()

        for nDict in nodes:
            n = Node(id=nDict['id'], degree=nDict['degree'])
            if 'weight' in nDict:
                n.weight = nDict['weight']
            self.nodes[n.id] = n

        eId = 0
        for eDict in edges:
            e = Edge(eDict['interval'], id=eId)
            for nId1, nId2, direction in eDict['connections']:
                # do not need to access from nodes dictionary here
                # but useful as a check that the node has been defined.
                if direction == DIRECTION_BI:
                    e.addBiDirectedConnections(self.nodes[nId1], self.nodes[nId2])
                else:
                    e.addDirectedConnection(self.nodes[nId1],
                                            self.nodes[nId2], direction=direction)
            self.edges[e.id] = e
            eId += 1

    def fillMelodicMinor(self):
        '''
        A convenience routine for testing a complex, bi-directional scale.

        >>> net = scale.intervalNetwork.IntervalNetwork()
        >>> net.fillMelodicMinor()
        >>> [str(p) for p in net.realizePitch('c4')]
        ['C4', 'D4', 'E-4', 'F4', 'G4', 'A4', 'B4', 'C5']

        '''
        nodes = ({'id': 'terminusLow', 'degree': 1},  # a
                 {'id': 0, 'degree': 2},  # b
                 {'id': 1, 'degree': 3},  # c
                 {'id': 2, 'degree': 4},  # d
                 {'id': 3, 'degree': 5},  # e

                 {'id': 4, 'degree': 6},  # f# ascending
                 {'id': 5, 'degree': 6},  # f
                 {'id': 6, 'degree': 7},  # g# ascending
                 {'id': 7, 'degree': 7},  # g
                 {'id': 'terminusHigh', 'degree': 8},  # a
                 )

        edges = ({'interval': 'M2', 'connections': (
            [TERMINUS_LOW, 0, DIRECTION_BI],  # a to b
        )},
            {'interval': 'm2', 'connections': (
                [0, 1, DIRECTION_BI],  # b to c
            )},
            {'interval': 'M2', 'connections': (
                [1, 2, DIRECTION_BI],  # c to d
            )},
            {'interval': 'M2', 'connections': (
                [2, 3, DIRECTION_BI],  # d to e
            )},

            {'interval': 'M2', 'connections': (
                [3, 4, DIRECTION_ASCENDING],  # e to f#
            )},
            {'interval': 'M2', 'connections': (
                [4, 6, DIRECTION_ASCENDING],  # f# to g#
            )},
            {'interval': 'm2', 'connections': (
                [6, TERMINUS_HIGH, DIRECTION_ASCENDING],  # g# to a
            )},

            {'interval': 'M2', 'connections': (
                [TERMINUS_HIGH, 7, DIRECTION_DESCENDING],  # a to g
            )},
            {'interval': 'M2', 'connections': (
                [7, 5, DIRECTION_DESCENDING],  # g to f
            )},
            {'interval': 'm2', 'connections': (
                [5, 3, DIRECTION_DESCENDING],  # f to e
            )},
        )

        self.fillArbitrary(nodes, edges)
        self.octaveDuplicating = True
        self.deterministic = True

    # --------------------------------------------------------------------------
    # for weighted selection of nodes

    def weightedSelection(self, edges, nodes):
        '''
        Perform weighted random selection on a parallel list of
        edges and corresponding nodes.

        >>> n1 = scale.intervalNetwork.Node(id='a', weight=1000000)
        >>> n2 = scale.intervalNetwork.Node(id='b', weight=1)
        >>> e1 = scale.intervalNetwork.Edge(interval.Interval('m3'), id='a')
        >>> e2 = scale.intervalNetwork.Edge(interval.Interval('m3'), id='b')
        >>> net = scale.intervalNetwork.IntervalNetwork()
        >>> e, n = net.weightedSelection([e1, e2], [n1, n2])
        >>> e.id  # note: this may fail as there is a slight chance to get 'b'
        'a'
        >>> n.id
        'a'
        '''
        # use index values as values
        iValues = range(len(edges))
        weights = [n.weight for n in nodes]
        # environLocal.printDebug(['weights', weights])
        i = common.weightedSelection(iValues, weights)
        # return corresponding edge and node
        return edges[i], nodes[i]

    # --------------------------------------------------------------------------
    @property
    def degreeMin(self):
        '''
        Return the lowest degree value.

        >>> edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        >>> net = scale.intervalNetwork.IntervalNetwork()
        >>> net.fillBiDirectedEdges(edgeList)
        >>> net.degreeMin
        1
        '''
        x = None
        for n in self.nodes.values():
            if x is None:
                x = n.degree
            if n.degree < x:
                x = n.degree
        return x

    @property
    def degreeMax(self):
        '''
        Return the largest degree value.

        >>> edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        >>> net = scale.intervalNetwork.IntervalNetwork()
        >>> net.fillBiDirectedEdges(edgeList)
        >>> net.degreeMax    # returns eight, as this is the last node
        8
        '''
        x = None
        for n in self.nodes.values():
            if x is None:
                x = n.degree
            if n.degree > x:
                x = n.degree
        return x

    @property
    def degreeMaxUnique(self):
        '''
        Return the largest degree value that represents a pitch level
        that is not a terminus of the scale.

        >>> edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        >>> net = scale.intervalNetwork.IntervalNetwork()
        >>> net.fillBiDirectedEdges(edgeList)
        >>> net.degreeMaxUnique
        7
        '''
        x = None
        for nId, n in self.nodes.items():
            # reject terminus high, as this duplicates terminus low
            if nId == TERMINUS_HIGH:
                continue
            if x is None:
                x = n.degree
            if n.degree > x:
                x = n.degree
        return x

    @property
    def terminusLowNodes(self):
        '''
        Return a list of first Nodes, or Nodes that contain "terminusLow".

        >>> edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        >>> net = scale.intervalNetwork.IntervalNetwork()
        >>> net.fillBiDirectedEdges(edgeList)
        >>> net.terminusLowNodes
        [<music21.scale.intervalNetwork.Node id='terminusLow'>]
        '''
        post = []
        # for now, there is only one
        post.append(self.nodes[TERMINUS_LOW])
        return post

    @property
    def terminusHighNodes(self):
        '''
        Return a list of last Nodes, or Nodes that contain "terminusHigh".

        >>> edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        >>> net = scale.intervalNetwork.IntervalNetwork()
        >>> net.fillBiDirectedEdges(edgeList)
        >>> net.terminusHighNodes
        [<music21.scale.intervalNetwork.Node id='terminusHigh'>]
        '''
        post = []
        # for now, there is only one
        post.append(self.nodes[TERMINUS_HIGH])
        return post

    # --------------------------------------------------------------------------

    def getNodeDegreeDictionary(self, equateTermini=True):
        '''Return a dictionary of node id, node degree pairs.
        The same degree may be given for each node

        There may not be unambiguous way to determine degree.
        Or, a degree may have different meanings when ascending or descending.

        If `equateTermini` is True, the terminals will be given the same degree.
        '''
        if equateTermini in self._nodeDegreeDictionaryCache:
            pass
            # return self._nodeDegreeDictionaryCache[equateTermini]

        post = OrderedDict()
        for nId, n in self.nodes.items():
            if equateTermini:
                if nId == TERMINUS_HIGH:
                    # get the same degree as the low
                    post[nId] = self.nodes[TERMINUS_LOW].degree
                else:
                    post[nId] = n.degree
            else:  # directly assign from attribute
                post[nId] = n.degree

        # environLocal.printDebug(['getNodeDegreeDictionary()', post])
        self._nodeDegreeDictionaryCache[equateTermini] = post

        return post

    def nodeIdToDegree(self, nId, direction=None):
        '''Given a strict node id (the .id attribute of the Node), return the degree.

        There may not be unambiguous way to determine degree.
        Or, a degree may have different meanings when ascending or descending.
        '''
        nodeStep = self.getNodeDegreeDictionary()
        return nodeStep[nId]  # gets degree integer

    def nodeIdToEdgeDirections(self, nId):
        '''
        Given a Node id, find all edges associated
        with this node and report on their directions

        >>> net = scale.intervalNetwork.IntervalNetwork()
        >>> net.fillMelodicMinor()
        >>> net.nodeIdToEdgeDirections('terminusLow')
        ['bi']
        >>> net.nodeIdToEdgeDirections(0)
        ['bi', 'bi']
        >>> net.nodeIdToEdgeDirections(6)
        ['ascending', 'ascending']
        >>> net.nodeIdToEdgeDirections(5)
        ['descending', 'descending']

        This node has bi-directional (from below),
        ascending (to above), and descending (from above)
        edge connections connections

        >>> net.nodeIdToEdgeDirections(3)
        ['bi', 'ascending', 'descending']

        '''
        collection = []

        if isinstance(nId, Node):
            nObj = nId
            nId = nObj.id
        else:
            nObj = self.nodes[nId]

        for eId in self.edges:
            eObj = self.edges[eId]
            # environLocal.printDebug(['nodeIdToEdgeDirections()', eObj])
            for x, y in eObj.connections:  # pairs of node ids
                if x == nId:  # this node is a source
                    collection.append(eObj.direction)
                    break  # only get one direction for each edge
                elif y == nId:  # this node is a destination
                    collection.append(eObj.direction)
                    break
        if not collection:
            raise IntervalNetworkException('failed to match any edges', nObj)
        return collection

    def degreeModulus(self, degree):
        '''
        Return the degree modulus degreeMax - degreeMin.

        >>> edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        >>> net = scale.intervalNetwork.IntervalNetwork()
        >>> net.fillBiDirectedEdges(edgeList)
        >>> net.degreeModulus(3)
        3
        >>> net.degreeModulus(8)
        1
        >>> net.degreeModulus(9)
        2
        >>> net.degreeModulus(0)
        7
        '''
        if degree is None:
            raise IntervalNetworkException('Degree of None given to degreeModulus')
        # TODO: these need to be cached
        sMin = self.degreeMin
        sMax = self.degreeMax
        # the number of unique values; assumes redundancy in
        # top and bottom value, so 8 steps, from 1 to 8, have
        # seven unique values
        spanCount = sMax - sMin
        # assume continuous span, assume start at min
        # example for diatonic scale degree 3:
        # ((3 - 1) % 7) + 1
        # if (((id - 1) % spanCount) + sMin) == nStep:

        return ((degree - 1) % spanCount) + sMin

    def nodeNameToNodes(self, nodeId,
                         equateTermini=True, permitDegreeModuli=True):
        '''
        The `nodeName` parameter may be a :class:`~music21.scale.intervalNetwork.Node` object,
        a node degree (as a number), a terminus string, or a None (indicating 'terminusLow').

        Return a list of Node objects that match this identifications.

        If `equateTermini` is True, and the name given is a degree number,
        then the first terminal will return both the first and last.

        >>> edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        >>> net = scale.intervalNetwork.IntervalNetwork()
        >>> net.fillBiDirectedEdges(edgeList)
        >>> net.nodeNameToNodes(1)[0]
        <music21.scale.intervalNetwork.Node id='terminusLow'>
        >>> net.nodeNameToNodes('high')
        [<music21.scale.intervalNetwork.Node id='terminusHigh'>]
        >>> net.nodeNameToNodes('low')
        [<music21.scale.intervalNetwork.Node id='terminusLow'>]

        Test using a nodeStep, or an integer nodeName

        >>> net.nodeNameToNodes(1)
        [<music21.scale.intervalNetwork.Node id='terminusLow'>,
         <music21.scale.intervalNetwork.Node id='terminusHigh'>]
        >>> net.nodeNameToNodes(1, equateTermini=False)
        [<music21.scale.intervalNetwork.Node id='terminusLow'>]
        >>> net.nodeNameToNodes(2)
        [<music21.scale.intervalNetwork.Node id=0>]

        With degree moduli, degree zero is the top-most non-terminal
        (as terminals are redundant

        >>> net.nodeNameToNodes(0)
        [<music21.scale.intervalNetwork.Node id=5>]
        >>> net.nodeNameToNodes(-1)
        [<music21.scale.intervalNetwork.Node id=4>]
        >>> net.nodeNameToNodes(8)
        [<music21.scale.intervalNetwork.Node id='terminusLow'>,
         <music21.scale.intervalNetwork.Node id='terminusHigh'>]
        '''
        # if a number, this is interpreted as a node degree
        if common.isNum(nodeId):
            post = []
            nodeStep = self.getNodeDegreeDictionary(
                equateTermini=equateTermini)
            for nId, nStep in nodeStep.items():
                if nodeId == nStep:
                    post.append(self.nodes[nId])
            # if no matches, and moduli comparisons are permitted
            if post == [] and permitDegreeModuli:
                for nId, nStep in nodeStep.items():
                    if self.degreeModulus(nodeId) == nStep:
                        post.append(self.nodes[nId])
            return post
        elif isinstance(nodeId, str):
            if nodeId.lower() in ('terminuslow', 'low'):
                return self.terminusLowNodes  # returns a list
            elif nodeId.lower() in ('terminushigh', 'high'):
                return self.terminusHighNodes  # returns a list
            else:
                raise IntervalNetworkException('got a string that has no match: ' + nodeId)
        elif isinstance(nodeId, Node):
            # look for direct match
            for nId in self.nodes:
                n = self.nodes[nId]
                if n is nodeId:  # could be a == comparison?
                    return [n]  # return only one
        else:  # match coords
            raise IntervalNetworkException('cannot filter by: %s' % nodeId)

    def getNext(self, nodeStart, direction):
        '''Given a Node, get two lists, one of next Edges, and one of next Nodes,
        searching all Edges to find all matches.

        There may be more than one possibility. If so, the caller must look
        at the Edges and determine which to use

        >>> edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        >>> net = scale.intervalNetwork.IntervalNetwork()
        >>> net.fillBiDirectedEdges(edgeList)
        >>> net.nodeNameToNodes(1)[0]
        <music21.scale.intervalNetwork.Node id='terminusLow'>
        '''

        postEdge = []
        postNodeId = []
        # search all edges to find Edges that start with this node id
        srcId = nodeStart.id

        # if we are at terminus low and descending, must wrap around
        if srcId == TERMINUS_LOW and direction == DIRECTION_DESCENDING:
            srcId = TERMINUS_HIGH
        # if we are at terminus high and ascending, must wrap around
        elif srcId == TERMINUS_HIGH and direction == DIRECTION_ASCENDING:
            srcId = TERMINUS_LOW

        for k in self.edges:
            e = self.edges[k]
            # only getting ascending connections
            pairs = e.getConnections(direction)
            if pairs is None:
                continue
            for src, dst in pairs:
                # environLocal.printDebug(['getNext()', 'src, dst', src, dst,
                #                         'trying to match source', srcId])
                if src == srcId:
                    postEdge.append(e)
                    postNodeId.append(dst)

        # this should actually never happen
        if not postEdge:
            environLocal.printDebug(['nodeStart', nodeStart, 'direction', direction,
                                     'postEdge', postEdge])
            # return None
            raise IntervalNetworkException('could not find any edges')

        # if we have multiple edges, we may need to select based on weight
        postNode = [self.nodes[nId] for nId in postNodeId]
        return postEdge, postNode

    def processAlteredNodes(self, alteredDegrees, n, p, direction):
        '''
        Return an altered pitch for given node, if an alteration is specified
        in the alteredDegrees dictionary
        '''
        if not alteredDegrees:
            return p
        if n.degree not in alteredDegrees:
            return p

        directionSpec = alteredDegrees[n.degree]['direction']
        # environLocal.printDebug(['processing altered node', n, p,
        #        'direction', direction, 'directionSpec', directionSpec])

        match = False
        # if ascending or descending, and this is a bi-directional alteration
        # then apply

        if direction == directionSpec:
            match = True
        # if request is bidrectional and the spec is for ascending and
        # descending
        elif (direction == DIRECTION_BI
              and directionSpec in (DIRECTION_ASCENDING, DIRECTION_DESCENDING)):
            match = True

        elif (direction in (DIRECTION_ASCENDING, DIRECTION_DESCENDING)
              and directionSpec == DIRECTION_BI):
            match = True

        if match:
            # environLocal.printDebug(['matched direction', direction])
            pPost = self.transposePitchAndApplySimplification(
                alteredDegrees[n.degree]['interval'], p)
            return pPost

        return p

    def getUnalteredPitch(self, pitchObj, nodeObj, direction=DIRECTION_BI, alteredDegrees=None):
        '''
        Given a node and alteredDegrees get the unaltered pitch, or return the current object
        '''
        if not alteredDegrees:
            return pitchObj

        # TODO: need to take direction into account
        # do reverse transposition
        if nodeObj.degree in alteredDegrees:
            p = self.transposePitchAndApplySimplification(
                alteredDegrees[nodeObj.degree]['interval'].reverse(), pitchObj)
            return p

        return pitchObj

    def nextPitch(self,
                  pitchReference,
                  nodeName,
                  pitchOrigin,
                  direction=DIRECTION_ASCENDING,
                  stepSize=1,
                  alteredDegrees=None,
                  getNeighbor=True):
        '''
        Given a pitchReference, nodeName, and a pitch origin, return the next pitch.

        The `nodeName` parameter may be a :class:`~music21.scale.intervalNetwork.Node` object,
        a node degree, a terminus string, or a None (indicating 'terminusLow').

        The `stepSize` parameter can be configured to permit different sized steps
        in the specified direction.

        >>> edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        >>> net = scale.intervalNetwork.IntervalNetwork()
        >>> net.fillBiDirectedEdges(edgeList)
        >>> net.nextPitch('g', 1, 'f#5', 'ascending')
        <music21.pitch.Pitch G5>
        >>> net.nextPitch('g', 1, 'f#5', 'descending')
        <music21.pitch.Pitch E5>
        >>> net.nextPitch('g', 1, 'f#5', 'ascending', 2)  # two steps
        <music21.pitch.Pitch A5>
        >>> alteredDegrees = {2: {'direction': 'bi', 'interval': interval.Interval('-a1')}}
        >>> net.nextPitch('g', 1, 'g2', 'ascending', alteredDegrees=alteredDegrees)
        <music21.pitch.Pitch A-2>
        >>> net.nextPitch('g', 1, 'a-2', 'ascending', alteredDegrees=alteredDegrees)
        <music21.pitch.Pitch B2>
        '''
        if pitchOrigin is None:
            raise Exception('No pitch origin for calling next on this pitch!')

        if isinstance(pitchOrigin, str):
            pitchOrigin = pitch.Pitch(pitchOrigin)
        else:
            pitchOrigin = copy.deepcopy(pitchOrigin)

        pCollect = None

        # get the node id that we are starting with
        nodeId = self.getRelativeNodeId(pitchReference,
                                        nodeName=nodeName,
                                        pitchTarget=pitchOrigin,
                                        direction=direction,
                                        alteredDegrees=alteredDegrees)

        # environLocal.printDebug(['nextPitch()', 'got node Id', nodeId,
        #  'direction', direction, 'self.nodes[nodeId].degree', self.nodes[nodeId].degree,
        #  'pitchOrigin', pitchOrigin])
        usedNeighbor = False
        # if no match, get the neighbor
        if (nodeId is None and getNeighbor in (
                True, DIRECTION_ASCENDING, DIRECTION_DESCENDING, DIRECTION_BI
        )):
            usedNeighbor = True
            lowId, highId = self.getNeighborNodeIds(pitchReference=pitchReference,
                                                    nodeName=nodeName,
                                                    pitchTarget=pitchOrigin,
                                                    direction=direction)  # must add direction

            # environLocal.printDebug(['nextPitch()', 'looking for neighbor',
            #                         'getNeighbor', getNeighbor, 'source nodeId', nodeId,
            #                         'lowId/highId', lowId, highId])

            # replace the node with the nearest neighbor
            if getNeighbor == DIRECTION_DESCENDING:
                nodeId = lowId
            else:
                nodeId = highId

        # realize the pitch from the found node degree
        # we may be getting an altered
        # tone, and we need to transpose an unaltered tone, thus
        # leave out altered nodes argument
        p = self.getPitchFromNodeDegree(
            pitchReference=pitchReference,
            nodeName=nodeName,
            nodeDegreeTarget=self.nodes[nodeId].degree,
            direction=direction,
            minPitch=None,  # not using a range here to
            maxPitch=None,  # get natural expansion
            alteredDegrees=None  # need unaltered tone here, thus omitted
        )

        # environLocal.printDebug(['nextPitch()', 'pitch obtained based on nodeName',
        # nodeName, 'p', p, 'nodeId', nodeId, 'self.nodes[nodeId].degree',
        # self.nodes[nodeId].degree])

        # transfer octave from origin to new pitch derived from node
        # note: this assumes octave equivalence and may be a problem
        p.octave = pitchOrigin.octave

        # correct for derived pitch crossing octave boundary
        # https://github.com/cuthbertLab/music21/issues/319
        alterSemitones = 0
        degree = self.nodeIdToDegree(nodeId)
        if alteredDegrees and degree in alteredDegrees:
            alterSemitones = alteredDegrees[degree]['interval'].semitones
        if (usedNeighbor and getNeighbor == DIRECTION_DESCENDING) or (
                not usedNeighbor and direction == DIRECTION_ASCENDING):
            while p.transpose(alterSemitones) > pitchOrigin:
                p.octave -= 1
        else:
            while p.transpose(alterSemitones) < pitchOrigin:
                p.octave += 1

        # pitchObj = p
        n = self.nodes[nodeId]
        # pCollect = p  # usually p, unless altered

        for i in range(stepSize):
            postEdge, postNode = self.getNext(n, direction)
            if len(postEdge) > 1:
                # do weighted selection based on node weights,
                e, n = self.weightedSelection(postEdge, postNode)
                intervalObj = e.interval
            else:
                intervalObj = postEdge[0].interval  # get first
                n = postNode[0]  # n is passed on

            # environLocal.printDebug(['nextPitch()', 'intervalObj', intervalObj,
            #  'p', p, 'postNode', postNode])
            # n = postNode[0]

            # for now, only taking first edge
            if direction == DIRECTION_ASCENDING:
                p = self.transposePitchAndApplySimplification(intervalObj, p)
            else:
                p = self.transposePitchAndApplySimplification(intervalObj.reverse(), p)
            pCollect = self.processAlteredNodes(alteredDegrees=alteredDegrees,
                                                 n=n,
                                                 p=p,
                                                 direction=direction)

        return pCollect

    # TODO: need to collect intervals as well

    def _getCacheKey(self, nodeObj, pitchReference, minPitch, maxPitch,
                     includeFirst=None):
        '''
        Return key for caching based on critical components.
        '''
        if minPitch is not None:
            minKey = minPitch.nameWithOctave
        else:
            minKey = None

        if maxPitch is not None:
            maxKey = maxPitch.nameWithOctave
        else:
            maxKey = None
        return (nodeObj.id, pitchReference.nameWithOctave,
                minKey, maxKey, includeFirst)

    def realizeAscending(
            self,
            pitchReference,
            nodeId=None,
            minPitch=None,
            maxPitch=None,
            alteredDegrees=None,
            fillMinMaxIfNone=False):
        '''
        Given a reference pitch, realize upwards to a maximum pitch.

        >>> edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']

        >>> net = scale.intervalNetwork.IntervalNetwork()
        >>> net.fillBiDirectedEdges(edgeList)
        >>> (pitches, nodeKeys) = net.realizeAscending('c2', 1, 'c5', 'c6')
        >>> [str(p) for p in pitches]
        ['C5', 'D5', 'E5', 'F5', 'G5', 'A5', 'B5', 'C6']
        >>> nodeKeys
        ['terminusHigh', 0, 1, 2, 3, 4, 5, 'terminusHigh']

        >>> net = scale.intervalNetwork.IntervalNetwork(octaveDuplicating=True)
        >>> net.fillBiDirectedEdges(edgeList)
        >>> (pitches, nodeKeys) = net.realizeAscending('c2', 1, 'c5', 'c6')
        >>> [str(p) for p in pitches]
        ['C5', 'D5', 'E5', 'F5', 'G5', 'A5', 'B5', 'C6']
        >>> nodeKeys
        ['terminusLow', 0, 1, 2, 3, 4, 5, 'terminusHigh']
        '''
        if isinstance(pitchReference, str):
            pitchReference = pitch.Pitch(pitchReference)
        else:
            pitchReference = copy.deepcopy(pitchReference)

        # get first node if no node is provided
        if isinstance(nodeId, Node):
            nodeObj = nodeId
        elif nodeId is None:  # assume first
            nodeObj = self.terminusLowNodes[0]
        else:
            nodeObj = self.nodeNameToNodes(nodeId)[0]

        # must set an octave for pitch reference, even if not given
        if pitchReference.octave is None:
            pitchReference.octave = pitchReference.implicitOctave

        if isinstance(minPitch, str):
            minPitch = pitch.Pitch(minPitch)
        if isinstance(maxPitch, str):
            maxPitch = pitch.Pitch(maxPitch)
        if fillMinMaxIfNone and minPitch is None and maxPitch is None:
            minPitch, maxPitch = self.realizeMinMax(pitchReference,
                                                    nodeObj,
                                                    alteredDegrees=alteredDegrees)

        # when the pitch reference is altered, we need to get the
        # unaltered version of this pitch.
        pitchReference = self.getUnalteredPitch(pitchReference,
                                                nodeObj,
                                                direction=DIRECTION_ASCENDING,
                                                alteredDegrees=alteredDegrees)

        # see if we can get from cache
        if self.deterministic:
            # environLocal.printDebug('using cached scale segment')
            ck = self._getCacheKey(nodeObj,
                                   pitchReference,
                                   minPitch,
                                   maxPitch)
            if ck in self._ascendingCache:
                return self._ascendingCache[ck]
        else:
            ck = None

        # if this network is octaveDuplicating, than we can shift
        # reference up octaves to just below minPitch
        if self.octaveDuplicating and minPitch is not None:
            pitchReference.transposeBelowTarget(minPitch, minimize=True, inPlace=True)

        # first, go upward from this pitch to the high terminus
        n = nodeObj
        p = pitchReference  # we start with the pitch that is the reference
        pCollect = p  # usually p, unless the tone has been altered
        post = []
        postNodeId = []  # store node ids as well
        # environLocal.printDebug(['realizeAscending()', 'n', n])

        attempts = 0
        maxAttempts = 100
        while attempts < maxAttempts:
            attempts += 1
            # environLocal.printDebug(['realizeAscending()', 'p', p])
            appendPitch = False

            if (minPitch is not None
                    and _gte(pCollect.ps, minPitch.ps)
                    and maxPitch is not None
                    and _lte(pCollect.ps, maxPitch.ps)):
                appendPitch = True
            elif (minPitch is not None
                  and _gte(pCollect.ps, minPitch.ps)
                  and maxPitch is None):
                appendPitch = True
            elif (maxPitch is not None
                  and _lte(pCollect.ps, maxPitch.ps)
                  and minPitch is None):
                appendPitch = True
            elif minPitch is None and maxPitch is None:
                appendPitch = True

            if appendPitch:
                post.append(pCollect)
                postNodeId.append(n.id)
            if maxPitch is not None and _gte(p.ps, maxPitch.ps):
                break

            # environLocal.printDebug(['realizeAscending()', 'n', n, 'n.id', n.id])
            # must check first, and at end
            if n.id == TERMINUS_HIGH:
                if maxPitch is None:  # if not defined, stop at terminus high
                    break
                n = self.terminusLowNodes[0]
            # this returns a list of possible edges and nodes
            nextBundle = self.getNext(n, DIRECTION_ASCENDING)
            # environLocal.printDebug(['realizeAscending()', 'n', n, 'nextBundle', nextBundle])

            # if we cannot continue to ascend, then we must break
            if nextBundle is None:
                break
            postEdge, postNode = nextBundle
            # make probabilistic selection here if more than one
            if len(postEdge) > 1:
                # do weighted selection based on node weights,
                # return on edge, one node
                # environLocal.printDebug(['realizeAscending()', 'doing weighted selection'])
                e, n = self.weightedSelection(postEdge, postNode)
                intervalObj = e.interval
            else:
                intervalObj = postEdge[0].interval  # get first
                n = postNode[0]  # n is passed on

            p = self.transposePitchAndApplySimplification(intervalObj, p)
            pCollect = p
            pCollect = self.processAlteredNodes(alteredDegrees=alteredDegrees,
                                                 n=n,
                                                 p=p,
                                                 direction=DIRECTION_ASCENDING)

        if attempts >= maxAttempts:
            raise IntervalNetworkException(
                'Cannot realize these pitches; is your scale '
                + "well-formed? (especially check if you're giving notes without octaves)")

        # store in cache
        if self.deterministic:
            self._ascendingCache[ck] = post, postNodeId

        # environLocal.printDebug(['realizeAscending()', 'post', post, 'postNodeId', postNodeId])

        return post, postNodeId

    def realizeDescending(self,
                          pitchReference,
                          nodeId=None,
                          minPitch=None,
                          maxPitch=None,
                          alteredDegrees=None,
                          includeFirst=False,
                          fillMinMaxIfNone=False,
                          reverse=True):
        '''
        Given a reference pitch, realize downward to a minimum.

        If no minimum is is given, the terminus is used.

        If `includeFirst` is False, the starting (highest) pitch will not be included.

        If `fillMinMaxIfNone` is True, a min and max will be artificially
        derived from an ascending scale and used as min and max values.


        >>> edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        >>> net = scale.intervalNetwork.IntervalNetwork()
        >>> net.fillBiDirectedEdges(edgeList)
        >>> net.realizeDescending('c2', 1, 'c3')  # minimum is above ref
        ([], [])
        >>> (pitches, nodeKeys) = net.realizeDescending('c3', 1, 'c2')
        >>> [str(p) for p in pitches]
        ['C2', 'D2', 'E2', 'F2', 'G2', 'A2', 'B2']
        >>> nodeKeys
        ['terminusLow', 0, 1, 2, 3, 4, 5]
        >>> (pitches, nodeKeys) = net.realizeDescending('c3', 1, 'c2', includeFirst=True)
        >>> [str(p) for p in pitches]
        ['C2', 'D2', 'E2', 'F2', 'G2', 'A2', 'B2', 'C3']
        >>> nodeKeys
        ['terminusLow', 0, 1, 2, 3, 4, 5, 'terminusLow']

        >>> (pitches, nodeKeys) = net.realizeDescending('a6', 'high')
        >>> [str(p) for p in pitches]
        ['A5', 'B5', 'C#6', 'D6', 'E6', 'F#6', 'G#6']
        >>> nodeKeys
        ['terminusLow', 0, 1, 2, 3, 4, 5]

        >>> (pitches, nodeKeys) = net.realizeDescending('a6', 'high', includeFirst=True)
        >>> [str(p) for p in pitches]
        ['A5', 'B5', 'C#6', 'D6', 'E6', 'F#6', 'G#6', 'A6']
        >>> nodeKeys
        ['terminusLow', 0, 1, 2, 3, 4, 5, 'terminusHigh']

        >>> net = scale.intervalNetwork.IntervalNetwork(octaveDuplicating=True)
        >>> net.fillBiDirectedEdges(edgeList)
        >>> (pitches, nodeKeys) = net.realizeDescending('c2', 1, 'c0', 'c1')
        >>> [str(p) for p in pitches]
        ['C0', 'D0', 'E0', 'F0', 'G0', 'A0', 'B0']
        >>> nodeKeys
        ['terminusLow', 0, 1, 2, 3, 4, 5]
        '''
        ck = None

        if isinstance(pitchReference, str):
            pitchReference = pitch.Pitch(pitchReference)
        else:
            pitchReference = copy.deepcopy(pitchReference)

        # must set an octave for pitch reference, even if not given
        if pitchReference.octave is None:
            pitchReference.octave = 4

        # get first node if no node is provided
        if isinstance(nodeId, Node):
            nodeObj = nodeId
        elif nodeId is None:  # assume low terminus by default
            # this is useful for appending a descending segment with an
            # ascending segment
            nodeObj = self.terminusLowNodes[0]
        else:
            nodeObj = self.nodeNameToNodes(nodeId)[0]

        if isinstance(minPitch, str):
            minPitch = pitch.Pitch(minPitch)
        if isinstance(maxPitch, str):
            maxPitch = pitch.Pitch(maxPitch)

        if fillMinMaxIfNone and minPitch is None and maxPitch is None:
            # environLocal.printDebug(['realizeDescending()', 'fillMinMaxIfNone'])
            minPitch, maxPitch = self.realizeMinMax(pitchReference,
                                                    nodeObj,
                                                    alteredDegrees=alteredDegrees)

        # when the pitch reference is altered, we need to get the
        # unaltered version of this pitch.
        pitchReference = self.getUnalteredPitch(pitchReference,
                                                nodeObj,
                                                direction=DIRECTION_DESCENDING,
                                                alteredDegrees=alteredDegrees)

        # see if we can get from cache
        if self.deterministic:
            ck = self._getCacheKey(nodeObj,
                                   pitchReference,
                                   minPitch,
                                   maxPitch,
                                   includeFirst)
            if ck in self._descendingCache:
                return self._descendingCache[ck]

        # if this network is octaveDuplicating, than we can shift
        # reference down octaves to just above minPitch
        if self.octaveDuplicating and maxPitch is not None:
            pitchReference.transposeAboveTarget(maxPitch, minimize=True, inPlace=True)

        n = nodeObj
        p = pitchReference
        pCollect = p  # usually p, unless the tone has been altered
        pre = []
        preNodeId = []  # store node ids as well

        isFirst = True
        while True:
            appendPitch = False
            if (minPitch is not None
                    and _gte(p.ps, minPitch.ps)
                    and maxPitch is not None
                    and _lte(p.ps, maxPitch.ps)):
                appendPitch = True
            elif (minPitch is not None
                  and _gte(p.ps, minPitch.ps)
                  and maxPitch is None):
                appendPitch = True
            elif (maxPitch is not None
                  and _lte(p.ps, maxPitch.ps)
                  and minPitch is None):
                appendPitch = True
            elif minPitch is None and maxPitch is None:
                appendPitch = True

            # environLocal.printDebug(['realizeDescending', 'appending pitch', pCollect,
            #        'includeFirst', includeFirst])

            if (appendPitch and not isFirst) or (appendPitch and isFirst and includeFirst):
                pre.append(pCollect)
                preNodeId.append(n.id)

            isFirst = False

            if minPitch is not None and p.ps <= minPitch.ps:
                break
            if n.id == TERMINUS_LOW:
                if minPitch is None:  # if not defined, stop at terminus high
                    break
                # get high and continue
                n = self.terminusHighNodes[0]
            if n.id == TERMINUS_LOW:
                if minPitch is None:  # if not defined, stop at terminus high
                    break

            nextBundle = self.getNext(n, DIRECTION_DESCENDING)
            # environLocal.printDebug(['realizeDescending()', 'n', n, 'nextBundle', nextBundle])

            if nextBundle is None:
                break
            postEdge, postNode = nextBundle
            if len(postEdge) > 1:
                # do weighted selection based on node weights,
                # return on edge, one node
                # environLocal.printDebug(['realizeDescending()', 'doing weighted selection'])
                e, n = self.weightedSelection(postEdge, postNode)
                intervalObj = e.interval
            else:
                intervalObj = postEdge[0].interval  # get first
                n = postNode[0]  # n is passed on

            p = self.transposePitchAndApplySimplification(intervalObj.reverse(), p)
            pCollect = self.processAlteredNodes(alteredDegrees=alteredDegrees,
                                                 n=n,
                                                 p=p,
                                                 direction=DIRECTION_DESCENDING)

        if reverse:
            pre.reverse()
            preNodeId.reverse()

        # store in cache
        if self.deterministic:
            self._descendingCache[ck] = pre, preNodeId

        return pre, preNodeId

    def realize(self,
                pitchReference,
                nodeId=None,
                minPitch=None,
                maxPitch=None,
                direction=DIRECTION_ASCENDING,
                alteredDegrees=None,
                reverse=False):
        '''
        Realize the nodes of this network based on a pitch assigned to a
        valid `nodeId`, where `nodeId` can be specified by integer
        (starting from 1) or key (a tuple of origin, destination keys).

        Without a min or max pitch, the given pitch reference is assigned
        to the designated node, and then both ascends to the terminus and
        descends to the terminus.

        The `alteredDegrees` dictionary permits creating mappings between
        node degree and direction and :class:`~music21.interval.Interval`
        based transpositions.

        Returns two lists, a list of pitches, and a list of Node keys.


        >>> edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        >>> net = scale.intervalNetwork.IntervalNetwork()
        >>> net.fillBiDirectedEdges(edgeList)
        >>> (pitches, nodeKeys) = net.realize('c2', 1, 'c2', 'c3')
        >>> [str(p) for p in pitches]
        ['C2', 'D2', 'E2', 'F2', 'G2', 'A2', 'B2', 'C3']
        >>> nodeKeys
        ['terminusLow', 0, 1, 2, 3, 4, 5, 'terminusHigh']


        >>> alteredDegrees = {7:{'direction':'bi', 'interval':interval.Interval('-a1')}}
        >>> (pitches, nodeKeys) = net.realize('c2', 1, 'c2', 'c4', alteredDegrees=alteredDegrees)
        >>> [str(p) for p in pitches]
        ['C2', 'D2', 'E2', 'F2', 'G2', 'A2', 'B-2', 'C3',
         'D3', 'E3', 'F3', 'G3', 'A3', 'B-3', 'C4']
        >>> nodeKeys
        ['terminusLow', 0, 1, 2, 3, 4, 5, 'terminusHigh', 0, 1, 2, 3, 4, 5, 'terminusHigh']
        '''
        # get first node if no node is provided
        # environLocal.printDebug(['got pre pitch:', pre])
        # environLocal.printDebug(['got pre node:', preNodeId])

        if isinstance(pitchReference, str):
            pitchReference = pitch.Pitch(pitchReference)
        else:  # make a copy b/c may manipulate
            pitchReference = copy.deepcopy(pitchReference)
        if pitchReference is None:
            raise IntervalNetworkException('pitchReference cannot be None')
        # must set an octave for pitch reference, even if not given
        if pitchReference.octave is None:
            pitchReference.octave = pitchReference.implicitOctave

        if isinstance(minPitch, str):
            minPitch = pitch.Pitch(minPitch)
        if isinstance(maxPitch, str):
            maxPitch = pitch.Pitch(maxPitch)

        directedRealization = False
        if self.octaveDuplicating:
            directedRealization = True

        # environLocal.printDebug(['directedRealization', directedRealization,
        #            'direction', direction, 'octaveDuplicating', self.octaveDuplicating])

        # realize by calling ascending/descending
        if directedRealization:
            # assumes we have min and max pitch as not none
            if direction == DIRECTION_ASCENDING:
                # move pitch reference to below minimum
                if self.octaveDuplicating and minPitch is not None:
                    pitchReference.transposeBelowTarget(minPitch, inPlace=True)

                mergedPitches, mergedNodes = self.realizeAscending(
                    pitchReference=pitchReference,
                    nodeId=nodeId,
                    minPitch=minPitch,
                    maxPitch=maxPitch,
                    alteredDegrees=alteredDegrees,
                    fillMinMaxIfNone=True)

            elif direction == DIRECTION_DESCENDING:
                # move pitch reference to above minimum
                if self.octaveDuplicating and maxPitch is not None:
                    pitchReference.transposeAboveTarget(maxPitch, inPlace=True)

                # fillMinMaxIfNone will result in a complete scale
                # being returned if no min and max are given (otherwise
                # we would just get the reference pitch.

                mergedPitches, mergedNodes = self.realizeDescending(
                    pitchReference=pitchReference,
                    nodeId=nodeId,
                    minPitch=minPitch,
                    maxPitch=maxPitch,
                    alteredDegrees=alteredDegrees,
                    includeFirst=True,
                    fillMinMaxIfNone=True)

            elif direction == DIRECTION_BI:
                # this is a union of both ascending and descending
                pitchReferenceA = copy.deepcopy(pitchReference)
                pitchReferenceB = copy.deepcopy(pitchReference)

                if self.octaveDuplicating and minPitch is not None:
                    pitchReferenceA.transposeBelowTarget(minPitch, inPlace=True)

                # pitchReferenceA.transposeBelowTarget(minPitch, inPlace=True)

                post, postNodeId = self.realizeAscending(pitchReference=pitchReferenceA,
                                                          nodeId=nodeId,
                                                          minPitch=minPitch,
                                                          maxPitch=maxPitch,
                                                          alteredDegrees=alteredDegrees)

                if self.octaveDuplicating and maxPitch is not None:
                    pitchReferenceB.transposeAboveTarget(maxPitch, inPlace=True)

                # pitchReferenceB.transposeAboveTarget(maxPitch, inPlace=True)

                pre, preNodeId = self.realizeDescending(pitchReference=pitchReferenceB,
                                                         nodeId=nodeId,
                                                         minPitch=minPitch,
                                                         maxPitch=maxPitch,
                                                         alteredDegrees=alteredDegrees,
                                                         includeFirst=True)

                # need to create union of both lists, but keep order, as well
                # as keep the node id list in order

                merged = []
                foundPitches = []  # just for membership comparison
                i = 0
                j = 0
                preventPermanentRecursion = 9999
                while preventPermanentRecursion > 0:
                    preventPermanentRecursion -= 1
                    if i < len(post) and post[i] not in foundPitches:
                        foundPitches.append(post[i])
                        merged.append((post[i], postNodeId[i]))
                    i += 1
                    if j < len(pre) and pre[j] not in foundPitches:
                        foundPitches.append(pre[j])
                        merged.append((pre[j], preNodeId[j]))
                    j += 1
                    # after increment, will be eq to len of list
                    # when both complete, break
                    if i >= len(post) and j >= len(pre):
                        break
                # transfer to two lists
                mergedPitches = []
                mergedNodes = []
                for x, y in merged:
                    mergedPitches.append(x)
                    mergedNodes.append(y)
            else:
                raise IntervalNetworkException(
                    'cannot match direction specification: %s' % direction)

        else:  # non directed realization
            # TODO: if not octave repeating, and ascending or descending,
            # have to travel to a pitch
            # at the proper extreme, and then go the opposite way
            # presently, this will realize ascending from reference,
            # then descending from reference
            post, postNodeId = self.realizeAscending(pitchReference=pitchReference,
                                                      nodeId=nodeId,
                                                      minPitch=minPitch,
                                                      maxPitch=maxPitch,
                                                      alteredDegrees=alteredDegrees)
            pre, preNodeId = self.realizeDescending(pitchReference=pitchReference,
                                                     nodeId=nodeId,
                                                     minPitch=minPitch,
                                                     maxPitch=maxPitch,
                                                     alteredDegrees=alteredDegrees,
                                                     includeFirst=False)

            # environLocal.printDebug(['realize()', 'pre', pre, preNodeId])
            mergedPitches, mergedNodes = pre + post, preNodeId + postNodeId

        if reverse:
            mergedPitches.reverse()
            mergedNodes.reverse()

        return mergedPitches, mergedNodes

    def realizePitch(self,
                     pitchReference,
                     nodeId=None,
                     minPitch=None,
                     maxPitch=None,
                     direction=DIRECTION_ASCENDING,
                     alteredDegrees=None,
                     reverse=False):
        '''
        Realize the native nodes of this network based on a pitch
        assigned to a valid `nodeId`, where `nodeId` can be specified by integer
        (starting from 1) or key (a tuple of origin, destination keys).

        The nodeId, when a simple, linear network, can be used as a scale degree
        value starting from one.


        >>> edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        >>> net = scale.intervalNetwork.IntervalNetwork()
        >>> net.fillBiDirectedEdges(edgeList)
        >>> [str(p) for p in net.realizePitch(pitch.Pitch('G3'))]
        ['G3', 'A3', 'B3', 'C4', 'D4', 'E4', 'F#4', 'G4']

        G3 is the fifth (scale) degree

        >>> [str(p) for p in net.realizePitch(pitch.Pitch('G3'), 5)]
        ['C3', 'D3', 'E3', 'F3', 'G3', 'A3', 'B3', 'C4']

        G3 is the seventh (scale) degree

        >>> [str(p) for p in net.realizePitch(pitch.Pitch('G3'), 7) ]
        ['A-2', 'B-2', 'C3', 'D-3', 'E-3', 'F3', 'G3', 'A-3']

        >>> [str(p) for p in net.realizePitch(pitch.Pitch('f#3'), 1, 'f2', 'f3') ]
        ['E#2', 'F#2', 'G#2', 'A#2', 'B2', 'C#3', 'D#3', 'E#3']

        >>> [str(p) for p in net.realizePitch(pitch.Pitch('a#2'), 7, 'c6', 'c7')]
        ['C#6', 'D#6', 'E6', 'F#6', 'G#6', 'A#6', 'B6']


        Circle of fifths


        >>> edgeList = ['P5'] * 6 + ['d6'] + ['P5'] * 5
        >>> net5ths = scale.intervalNetwork.IntervalNetwork()
        >>> net5ths.fillBiDirectedEdges(edgeList)
        >>> [str(p) for p in net5ths.realizePitch(pitch.Pitch('C1'))]
        ['C1', 'G1', 'D2', 'A2', 'E3', 'B3', 'F#4', 'D-5', 'A-5', 'E-6', 'B-6', 'F7', 'C8']
        >>> [str(p) for p in net5ths.realizePitch(pitch.Pitch('C2'))]
        ['C2', 'G2', 'D3', 'A3', 'E4', 'B4', 'F#5', 'D-6', 'A-6', 'E-7', 'B-7', 'F8', 'C9']

        '''
        components = self.realize(
            pitchReference=pitchReference,
            nodeId=nodeId,
            minPitch=minPitch,
            maxPitch=maxPitch,
            direction=direction,
            alteredDegrees=alteredDegrees,
            reverse=reverse)
        return components[0]  # just return first component

    def realizeIntervals(self,
                         nodeId=None,
                         minPitch=None,
                         maxPitch=None,
                         direction=DIRECTION_ASCENDING,
                         alteredDegrees=None,
                         reverse=False):
        '''Realize the sequence of intervals between the specified pitches, or the termini.


        >>> edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        >>> net = scale.intervalNetwork.IntervalNetwork()
        >>> net.fillBiDirectedEdges(edgeList)
        >>> net.realizeIntervals()
        [<music21.interval.Interval M2>, <music21.interval.Interval M2>,
         <music21.interval.Interval m2>, <music21.interval.Interval M2>,
         <music21.interval.Interval M2>, <music21.interval.Interval M2>,
         <music21.interval.Interval m2>]
        '''
        # note: there may be a more efficient way to do this, but we still
        # need to realize the intervals due to probabilistic selection

        # provide an arbitrary pitch reference
        pitchReference = 'c4'

        pList = self.realize(pitchReference=pitchReference,
                             nodeId=nodeId,
                             minPitch=minPitch,
                             maxPitch=maxPitch,
                             direction=direction,
                             alteredDegrees=alteredDegrees,
                             reverse=reverse)[0]  # just return first component

        iList = []
        for i, p1 in enumerate(pList):
            if i < len(pList) - 1:
                p2 = pList[i + 1]
                iList.append(interval.Interval(p1, p2))
        return iList

    def realizeTermini(self, pitchReference, nodeId=None, alteredDegrees=None):
        '''
        Realize the pitches of the 'natural' terminus of a network. This (presently)
        must be done by ascending, and assumes only one valid terminus for both extremes.

        This suggests that in practice termini should not be affected by directionality.


        >>> edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        >>> net = scale.intervalNetwork.IntervalNetwork()
        >>> net.fillBiDirectedEdges(edgeList)
        >>> net.realizeTermini(pitch.Pitch('G3'))
        (<music21.pitch.Pitch G3>, <music21.pitch.Pitch G4>)
        >>> net.realizeTermini(pitch.Pitch('a6'))
        (<music21.pitch.Pitch A6>, <music21.pitch.Pitch A7>)
        '''
        # must do a non-directed realization with no min/max
        # will go up from reference, then down from reference, stopping
        # at the termini

        post, postNodeId = self.realizeAscending(
            pitchReference=pitchReference, nodeId=nodeId,
            alteredDegrees=alteredDegrees,
            fillMinMaxIfNone=False)  # avoid recursion by setting false
        pre, preNodeId = self.realizeDescending(
            pitchReference=pitchReference, nodeId=nodeId,
            alteredDegrees=alteredDegrees, includeFirst=False,
            fillMinMaxIfNone=False)  # avoid recursion by setting false

        # environLocal.printDebug(['realize()', 'pre', pre, preNodeId])
        mergedPitches, unused_mergedNodes = pre + post, preNodeId + postNodeId

        # environLocal.printDebug(['realizeTermini()', 'pList', mergedPitches,
        #            'pitchReference', pitchReference, 'nodeId', nodeId])
        return mergedPitches[0], mergedPitches[-1]

    def realizeMinMax(self, pitchReference, nodeId=None, alteredDegrees=None):
        '''
        Realize the min and max pitches of the scale, or the min and max values
        found between two termini.

        This suggests that min and max might be beyond the terminus.

        >>> edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        >>> net = scale.intervalNetwork.IntervalNetwork()
        >>> net.fillBiDirectedEdges(edgeList)

        >>> net.realizeMinMax(pitch.Pitch('C4'))
        (<music21.pitch.Pitch C4>, <music21.pitch.Pitch C6>)
        >>> net.realizeMinMax(pitch.Pitch('B-5'))
        (<music21.pitch.Pitch B-5>, <music21.pitch.Pitch B-7>)

        Note that it might not always be two octaves apart

        #  s = scale.AbstractDiatonicScale('major')
        #  s._net.realizeMinMax(pitch.Pitch('D2'))
        #  (<music21.pitch.Pitch D2>, <music21.pitch.Pitch D3>)

        '''
        # only cache if altered degrees is None
        if not alteredDegrees:
            # if pitch reference is a string, take it as it is
            if isinstance(pitchReference, str):
                cacheKey = (pitchReference, nodeId)
            else:
                cacheKey = (pitchReference.nameWithOctave, nodeId)
        else:
            cacheKey = None

        if cacheKey in self._minMaxCache:
            pass
            # return self._minMaxCache[cacheKey]

        # first, get termini, then extend by an octave.
        low, high = self.realizeTermini(pitchReference=pitchReference,
                                        nodeId=nodeId,
                                        alteredDegrees=alteredDegrees)

        # note: in some cases this range may need to be extended
        low = low.transpose(-12)
        high = high.transpose(12)
        post, postNodeId = self.realizeAscending(
            pitchReference=pitchReference,
            nodeId=nodeId,
            alteredDegrees=alteredDegrees,
            minPitch=low,
            maxPitch=high,
            fillMinMaxIfNone=False)  # avoid recursion by setting false
        pre, preNodeId = self.realizeDescending(
            pitchReference=pitchReference,
            nodeId=nodeId,
            minPitch=low,
            maxPitch=high,
            alteredDegrees=alteredDegrees,
            includeFirst=True,
            fillMinMaxIfNone=False)  # avoid recursion by setting false
        # environLocal.printDebug(['realizeMinMax()', 'post', post, 'postNodeId', postNodeId])

        postPairs = []
        collect = False
        for i, nId in enumerate(postNodeId):
            p = post[i]
            # if first id is a terminus, skip
            if i == 0 and nId in (TERMINUS_LOW, TERMINUS_HIGH):
                continue
            # turn off collection after finding next terminus
            elif nId in (TERMINUS_LOW, TERMINUS_HIGH) and collect is True:
                postPairs.append((p, nId))
                break
            elif nId in (TERMINUS_LOW, TERMINUS_HIGH) and collect is False:
                collect = True
            if collect:
                postPairs.append((p, nId))
        # environLocal.printDebug(['realizeMinMax()', 'postPairs', postPairs])

        prePairs = []
        collect = False
        for i, nId in enumerate(preNodeId):
            p = pre[i]
            # if first id is a terminus, skip
            if i == 0 and nId in (TERMINUS_LOW, TERMINUS_HIGH):
                continue
            # turn off collection after finding next terminus
            elif nId in (TERMINUS_LOW, TERMINUS_HIGH) and collect is True:
                prePairs.append((p, nId))
                break
            elif nId in (TERMINUS_LOW, TERMINUS_HIGH) and collect is False:
                collect = True
            if collect:
                prePairs.append((p, nId))
        # environLocal.printDebug(['realizeMinMax()', 'prePairs', prePairs])

        # now, we have pairs that are one span, from each terminus; need to
        # now find lowest and highest pitch
        minPitch = post[-1]
        maxPitch = post[0]
        for p, nId in postPairs + prePairs:
            if p.ps < minPitch.ps:
                minPitch = p
            if p.ps > maxPitch.ps:
                maxPitch = p

        # store if possible
        if cacheKey is not None:
            self._minMaxCache[cacheKey] = (minPitch, maxPitch)

        # may not be first or last to get min/max
        return minPitch, maxPitch

    def realizePitchByDegree(
            self,
            pitchReference,
            nodeId=None,
            nodeDegreeTargets=(1,),
            minPitch=None,
            maxPitch=None,
            direction=DIRECTION_ASCENDING,
            alteredDegrees=None
    ):
        '''
        Realize the native nodes of this network based on
        a pitch assigned to a valid `nodeId`, where `nodeId` can
        be specified by integer (starting from 1) or key
        (a tuple of origin, destination keys).

        The `nodeDegreeTargets` specifies the degrees to be
        included within the specified range.

        Example: build a network of the Major scale:


        >>> edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        >>> net = scale.intervalNetwork.IntervalNetwork()
        >>> net.fillBiDirectedEdges(edgeList)

        Now for every "scale" where G is the 3rd degree, give me the
        tonic if that note is between C2 and C3.
        (There's only one such note: E-2).

        >>> net.realizePitchByDegree('G', 3, [1], 'c2', 'c3')
        [<music21.pitch.Pitch E-2>]

        But between c2 and f3 there are two, E-2 and E-3 (it doesn't matter that the G
        which is scale degree 3 for E-3 is above F3):

        >>> net.realizePitchByDegree('G', 3, [1], 'c2', 'f3')
        [<music21.pitch.Pitch E-2>, <music21.pitch.Pitch E-3>]

        Give us nodes 1, 2, and 5 for scales where G is node 5 (e.g., C major's dominant)
        where any pitch is between C2 and F4

        >>> pitchList = net.realizePitchByDegree('G', 5, [1, 2, 5], 'c2', 'f4')
        >>> print(' '.join([str(p) for p in pitchList]))
        C2 D2 G2 C3 D3 G3 C4 D4

        There are no networks based on the major scale's edge-list where
        with node 1 (i.e. "tonic") between C2 and F2 where
        G is scale degree 7

        >>> net.realizePitchByDegree('G', 7, [1], 'c2', 'f2')
        []
        '''
        realizedPitch, realizedNode = self.realize(
            pitchReference=pitchReference,
            nodeId=nodeId,
            minPitch=minPitch,
            maxPitch=maxPitch,
            direction=direction,
            alteredDegrees=alteredDegrees)

        # take modulus of all
        nodeDegreeTargetsModulus = [self.degreeModulus(s) for s in nodeDegreeTargets]

        # environLocal.printDebug(['realizePitchByDegree(); nodeDegreeTargets', nodeDegreeTargets])

        post = []
        for i, p in enumerate(realizedPitch):
            # get the node
            n = self.nodes[realizedNode[i]]
            # environLocal.printDebug(['realizePitchByDegree(); p', p, n.degree])
            if self.degreeModulus(n.degree) in nodeDegreeTargetsModulus:
                post.append(p)
        return post

    def getNetworkxGraph(self):
        '''
        Create a networkx graph from the raw Node representation.

        Return a networks Graph object representing a realized version
        of this IntervalNetwork if networkx is installed

        '''
        weight = 1
        style = 'solid'

        def sortTerminusLowThenIntThenTerminusHigh(a):
            '''
            return a two-tuple where the first element is -1 if 'TERMINUS_LOW',
            0 if an int, and 1 if 'TERMINUS_HIGH' or another string, and
            the second element is the value itself.
            '''
            sortFirst = 0
            if isinstance(a, str):
                if a.upper() == 'TERMINUS_LOW':
                    sortFirst = -1
                else:
                    sortFirst = 1
            return (sortFirst, a)

        # g = networkx.DiGraph()
        g = networkx.MultiDiGraph()

        for unused_eId, e in self.edges.items():
            if e.direction == DIRECTION_ASCENDING:
                weight = 0.9  # these values are just for display
                style = 'solid'
            elif e.direction == DIRECTION_DESCENDING:
                weight = 0.6
                style = 'solid'
            elif e.direction == DIRECTION_BI:
                weight = 1.0
                style = 'solid'
            for src, dst in e.connections:
                g.add_edge(src, dst, weight=weight, style=style)

        # set positions of all nodes based on degree, where y value is degree
        # and x is count of values at that degree
        degreeCount = OrderedDict()  # degree, count pairs
        # sorting nodes will help, but not insure, proper positioning
        nKeys = list(self.nodes.keys())
        nKeys.sort(key=sortTerminusLowThenIntThenTerminusHigh)
        for nId in nKeys:
            n = self.nodes[nId]
            if n.degree not in degreeCount:
                degreeCount[n.degree] = 0
            g.node[nId]['pos'] = (degreeCount[n.degree], n.degree)
            degreeCount[n.degree] += 1
        environLocal.printDebug(['got degree count', degreeCount])
        return g

    def plot(self, pitchObj=None, nodeId=None, minPitch=None, maxPitch=None,
             *args, **keywords):
        '''
        Given a method and keyword configuration arguments, create and display a plot.

        Requires networkx to be installed.
        '''
#
#         >>> s = corpus.parse('bach/bwv324.xml') #_DOCS_HIDE
#         >>> s.plot('pianoroll', doneAction=None) #_DOCS_HIDE
#         >>> #_DOCS_SHOW s = corpus.parse('bach/bwv57.8')
#         >>> #_DOCS_SHOW s.plot('pianoroll')

#         .. image:: images/PlotHorizontalBarPitchSpaceOffset.*
#             :width: 600
        if pitchObj is None:
            pitchObj = pitch.Pitch('C4')

        # import is here to avoid import of matplotlib problems
        from music21 import graph
        # first ordered arg can be method type
        g = graph.primitives.GraphNetworxGraph(
            networkxGraph=self.getNetworkxGraph())

        # networkxGraph=self.getNetworkxRealizedGraph(pitchObj=pitchObj,
        #                    nodeId=nodeId, minPitch=minPitch, maxPitch=maxPitch))
        g.process()

    def getRelativeNodeId(self,
                          pitchReference,
                          nodeName,
                          pitchTarget,
                          comparisonAttribute='ps',
                          direction=DIRECTION_ASCENDING,
                          alteredDegrees=None):
        '''
        Given a reference pitch assigned to node id, determine the
        relative node id of pitchTarget, even if displaced over multiple octaves

        The `nodeName` parameter may be
        a :class:`~music21.scale.intervalNetwork.Node` object, a node degree,
        a terminus string, or a None (indicating 'terminusLow').

        Returns None if no match.

        If `getNeighbor` is True, or direction, the nearest node will be returned.

        If more than one node defines the same pitch, Node weights are used
        to select a single node.


        >>> edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        >>> net = scale.intervalNetwork.IntervalNetwork(edgeList)
        >>> net.getRelativeNodeId('a', 1, 'a4')
        'terminusLow'
        >>> net.getRelativeNodeId('a', 1, 'b4')
        0
        >>> net.getRelativeNodeId('a', 1, 'c#4')
        1
        >>> net.getRelativeNodeId('a', 1, 'c4', comparisonAttribute = 'step')
        1
        >>> net.getRelativeNodeId('a', 1, 'c', comparisonAttribute = 'step')
        1
        >>> net.getRelativeNodeId('a', 1, 'b-4') is None
        True
        '''
        # TODO: this always takes the first: need to add weighted selection
        if nodeName is None:  # assume first
            nodeId = self.getTerminusLowNodes()[0]
        else:
            nodeId = self.nodeNameToNodes(nodeName)[0]

        # environLocal.printDebug(['getRelativeNodeId', 'result of nodeNameToNodes',
        #   self.nodeNameToNodes(nodeName)])

        if isinstance(pitchTarget, str):
            pitchTarget = pitch.Pitch(pitchTarget)
        elif 'Note' in pitchTarget.classes:
            pitchTarget = pitchTarget.pitch

        saveOctave = pitchTarget.octave
        if saveOctave is None:
            pitchTarget.octave = pitchTarget.implicitOctave

        # try an octave spread first
        # if a scale degree is larger than an octave this will fail
        minPitch = pitchTarget.transpose(-12, inPlace=False)
        maxPitch = pitchTarget.transpose(12, inPlace=False)

        realizedPitch, realizedNode = self.realize(pitchReference,
                                                   nodeId,
                                                   minPitch=minPitch,
                                                   maxPitch=maxPitch,
                                                   direction=direction,
                                                   alteredDegrees=alteredDegrees)

        # environLocal.printDebug(['getRelativeNodeId()', 'nodeId', nodeId,
        #    'realizedPitch', realizedPitch, 'realizedNode', realizedNode])

        post = []  # collect more than one
        for i in range(len(realizedPitch)):
            # environLocal.printDebug(['getRelativeNodeId', 'comparing',
            #   realizedPitch[i], realizedNode[i]])

            # comparison of attributes, not object
            match = False
            if (getattr(pitchTarget, comparisonAttribute)
                    == getattr(realizedPitch[i], comparisonAttribute)):
                match = True
            if match:
                if realizedNode[i] not in post:  # may be more than one match
                    post.append(realizedNode[i])

        if saveOctave is None:
            pitchTarget.octave = None

        if not post:
            return None
        elif len(post) == 1:
            return post[0]
        else:  # do weighted selection
            # environLocal.printDebug(['getRelativeNodeId()', 'got multiple matches', post])
            # use node keys stored in post, get node, and collect weights
            return common.weightedSelection(post,
                                            [self.nodes[x].weight for x in post])

    def getNeighborNodeIds(self,
                           pitchReference,
                           nodeName,
                           pitchTarget,
                           direction=DIRECTION_ASCENDING,
                           alteredDegrees=None):
        '''
        Given a reference pitch assigned to a node id, determine the node ids
        that neighbor this pitch.

        Returns None if an exact match.


        >>> edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        >>> net = scale.intervalNetwork.IntervalNetwork(edgeList)
        >>> net.getNeighborNodeIds('c4', 1, 'b-')
        (4, 5)
        >>> net.getNeighborNodeIds('c4', 1, 'b')
        (5, 'terminusHigh')
        '''
        # TODO: this takes the first, need to add probabilistic selection
        if nodeName is None:  # assume first
            nodeId = self.getTerminusLowNodes()[0]
        else:
            nodeId = self.nodeNameToNodes(nodeName)[0]

        if isinstance(pitchTarget, str):
            pitchTarget = pitch.Pitch(pitchTarget)

        savedOctave = pitchTarget.octave
        if savedOctave is None:
            # don't alter permanently, in case a Pitch object was passed in.
            pitchTarget.octave = pitchTarget.implicitOctave
        # try an octave spread first
        # if a scale degree is larger than an octave this will fail
        minPitch = pitchTarget.transpose(-12, inPlace=False)
        maxPitch = pitchTarget.transpose(12, inPlace=False)

        realizedPitch, realizedNode = self.realize(pitchReference,
                                                   nodeId,
                                                   minPitch=minPitch,
                                                   maxPitch=maxPitch,
                                                   direction=direction,
                                                   alteredDegrees=alteredDegrees)

        lowNeighbor = None
        highNeighbor = None
        for i in range(len(realizedPitch)):
            if pitchTarget.ps < realizedPitch[i].ps:
                highNeighbor = realizedNode[i]
                # low neighbor may be a previously-encountered pitch
                return lowNeighbor, highNeighbor
            lowNeighbor = realizedNode[i]

        if savedOctave is None:
            pitchTarget.octave = savedOctave
        return None

    def getRelativeNodeDegree(self,
                              pitchReference,
                              nodeName,
                              pitchTarget,
                              comparisonAttribute='ps',
                              direction=DIRECTION_ASCENDING,
                              alteredDegrees=None):
        '''
        Given a reference pitch assigned to node id,
        determine the relative node degree of pitchTarget,
        even if displaced over multiple octaves

        Comparison Attribute determines what will be used to determine
        equality.  Use `ps` (default) for post-tonal uses.  `name` for
        tonal, and `step` for diatonic.


        >>> edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        >>> net = scale.intervalNetwork.IntervalNetwork(edgeList)
        >>> [str(p) for p in net.realizePitch(pitch.Pitch('e-2')) ]
        ['E-2', 'F2', 'G2', 'A-2', 'B-2', 'C3', 'D3', 'E-3']

        >>> net.getRelativeNodeDegree('e-2', 1, 'd3')  # if e- is tonic, what is d3
        7

        For an octave repeating network, the neither pitch's octave matters:

        >>> net.getRelativeNodeDegree('e-', 1, 'd5')  # if e- is tonic, what is d3
        7
        >>> net.getRelativeNodeDegree('e-2', 1, 'd')  # if e- is tonic, what is d3
        7

        >>> net.getRelativeNodeDegree('e3', 1, 'd5') is None
        True
        >>> net.getRelativeNodeDegree('e3', 1, 'd5', comparisonAttribute='step')
        7
        >>> net.getRelativeNodeDegree('e3', 1, 'd', comparisonAttribute='step')
        7

        >>> net.getRelativeNodeDegree('e-3', 1, 'b-3')
        5

        >>> net.getRelativeNodeDegree('e-3', 1, 'e-5')
        1
        >>> net.getRelativeNodeDegree('e-2', 1, 'f3')
        2
        >>> net.getRelativeNodeDegree('e-3', 1, 'b6') is None
        True

        >>> net.getRelativeNodeDegree('e-3', 1, 'e-2')
        1
        >>> net.getRelativeNodeDegree('e-3', 1, 'd3')
        7
        >>> net.getRelativeNodeDegree('e-3', 1, 'e-3')
        1
        >>> net.getRelativeNodeDegree('e-3', 1, 'b-1')
        5


        >>> edgeList = ['p4', 'p4', 'p4']  # a non octave-repeating scale
        >>> net = scale.intervalNetwork.IntervalNetwork(edgeList)
        >>> [str(p) for p in net.realizePitch('f2')]
        ['F2', 'B-2', 'E-3', 'A-3']
        >>> [str(p) for p in net.realizePitch('f2', 1, 'f2', 'f6')]
        ['F2', 'B-2', 'E-3', 'A-3', 'D-4', 'G-4', 'C-5', 'F-5', 'A5', 'D6']

        >>> net.getRelativeNodeDegree('f2', 1, 'a-3')  # could be 4 or 1
        1
        >>> net.getRelativeNodeDegree('f2', 1, 'd-4')  # 2 is correct
        2
        >>> net.getRelativeNodeDegree('f2', 1, 'g-4')  # 3 is correct
        3
        >>> net.getRelativeNodeDegree('f2', 1, 'c-5')  # could be 4 or 1
        1
        >>> net.getRelativeNodeDegree('f2', 1, 'e--6')  # could be 4 or 1
        1

        >>> [str(p) for p in net.realizePitch('f6', 1, 'f2', 'f6')]
        ['G#2', 'C#3', 'F#3', 'B3', 'E4', 'A4', 'D5', 'G5', 'C6', 'F6']

        >>> net.getRelativeNodeDegree('f6', 1, 'd5')
        1
        >>> net.getRelativeNodeDegree('f6', 1, 'g5')
        2
        >>> net.getRelativeNodeDegree('f6', 1, 'a4')
        3
        >>> net.getRelativeNodeDegree('f6', 1, 'e4')
        2
        >>> net.getRelativeNodeDegree('f6', 1, 'b3')
        1

        '''
        nId = self.getRelativeNodeId(
            pitchReference=pitchReference,
            nodeName=nodeName,
            pitchTarget=pitchTarget,
            comparisonAttribute=comparisonAttribute,
            alteredDegrees=alteredDegrees,
            direction=direction)

        if nId is None:
            return None
        else:
            return self.nodeIdToDegree(nId)

    def getPitchFromNodeDegree(self,
                               pitchReference,
                               nodeName,
                               nodeDegreeTarget,
                               direction=DIRECTION_ASCENDING,
                               minPitch=None,
                               maxPitch=None,
                               alteredDegrees=None,
                               equateTermini=True):
        '''
        Given a reference pitch assigned to node id,
        determine the pitch for the target node degree.

        >>> edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        >>> net = scale.intervalNetwork.IntervalNetwork(edgeList)
        >>> [str(p) for p in net.realizePitch(pitch.Pitch('e-2')) ]
        ['E-2', 'F2', 'G2', 'A-2', 'B-2', 'C3', 'D3', 'E-3']
        >>> net.getPitchFromNodeDegree('e4', 1, 1)
        <music21.pitch.Pitch E4>
        >>> net.getPitchFromNodeDegree('e4', 1, 7)  # seventh scale degree
        <music21.pitch.Pitch D#5>
        >>> net.getPitchFromNodeDegree('e4', 1, 8)
        <music21.pitch.Pitch E4>
        >>> net.getPitchFromNodeDegree('e4', 1, 9)
        <music21.pitch.Pitch F#4>
        >>> net.getPitchFromNodeDegree('e4', 1, 3, minPitch='c2', maxPitch='c3')
        <music21.pitch.Pitch G#2>


        This will always get the lowest pitch:

        >>> net.getPitchFromNodeDegree('e4', 1, 3, minPitch='c2', maxPitch='c10')
        <music21.pitch.Pitch G#2>

        >>> net.fillMelodicMinor()
        >>> net.getPitchFromNodeDegree('c', 1, 5)
        <music21.pitch.Pitch G4>
        >>> net.getPitchFromNodeDegree('c', 1, 6, 'ascending')
        <music21.pitch.Pitch A4>
        >>> net.getPitchFromNodeDegree('c', 1, 6, 'descending')
        <music21.pitch.Pitch A-4>
        '''
        # these are the reference node -- generally one except for bidirectional
        # scales.
        nodeListForNames = self.nodeNameToNodes(nodeName)
        # environLocal.printDebug(['getPitchFromNodeDegree()', 'node reference',
        #    nodeId, 'node degree', nodeId.degree,
        #    'pitchReference', pitchReference, 'alteredDegrees', alteredDegrees])

        # here, we give a node degree, and may return 1 or more valid nodes;
        # need to select the node that is appropriate to the directed
        # realization
        nodeTargetId = None
        nodeTargetIdList = self.nodeNameToNodes(nodeDegreeTarget,
                                                permitDegreeModuli=True,
                                                equateTermini=equateTermini)

        # environLocal.printDebug(['getPitchFromNodeDegree()',
        #    'result of nodeNameToNodes', nodeTargetIdList,
        #    'nodeDegreeTarget', nodeDegreeTarget])

        if len(nodeTargetIdList) == 1:
            nodeTargetId = nodeTargetIdList[0]  # easy case
        # case where we equate terminals and get both min and max
        elif [n.id for n in nodeTargetIdList] == [TERMINUS_LOW, TERMINUS_HIGH]:
            # get first, terminus low
            nodeTargetId = nodeTargetIdList[0]  # easy case
        else:  # have more than one node that is defined for a given degree
            for nId in nodeTargetIdList:
                dirList = self.nodeIdToEdgeDirections(nId)
                # environLocal.printDebug(['getPitchFromNodeDegree()',
                #   'comparing dirList', dirList])
                # for now, simply find the nId that has the requested
                # direction. a more sophisticated matching may be needed
                if direction in dirList:
                    nodeTargetId = nId
                    break
        if nodeTargetId is None:
            # environLocal.printDebug(['getPitchFromNodeDegree()',
            #    'cannot select node based on direction', nodeTargetIdList])
            nodeTargetId = nodeTargetIdList[0]  # easy case

        # environLocal.printDebug(['getPitchFromNodeDegree()', 'nodeTargetId', nodeTargetId])

        # get a realization to find the node
        # pass direction as well when getting realization

        # TODO: need a way to force that we get a realization that
        #     may goes through a particular node; we could start at that node?
        #     brute force approach might make multiple attempts to realize
        # TODO: BUG: Does not work with bidirectional scales.

        # TODO: possibly cache results
        for unused_counter in range(10):
            realizedPitch, realizedNode = self.realize(
                pitchReference=pitchReference,
                nodeId=nodeListForNames[0],
                minPitch=minPitch,
                maxPitch=maxPitch,
                direction=direction,
                alteredDegrees=alteredDegrees)

            # environLocal.printDebug(['getPitchFromNodeDegree()',
            #    'realizedPitch', realizedPitch, 'realizedNode', realizedNode,
            #    'nodeTargetId', nodeTargetId,])

            # get the pitch when we have a node id to match match
            for i, nId in enumerate(realizedNode):
                # environLocal.printDebug(['comparing', nId, 'nodeTargetId', nodeTargetId])

                if nId == nodeTargetId.id:
                    return realizedPitch[i]
                # NOTE: this condition may be too generous, and was added to solve
                # an non tracked problem.
                # only match this generously if we are equating termini
                if equateTermini:
                    if ((nId in (TERMINUS_HIGH, TERMINUS_LOW))
                         and (nodeTargetId.id in (TERMINUS_HIGH, TERMINUS_LOW))):
                        return realizedPitch[i]

            # environLocal.printDebug(['getPitchFromNodeDegree() on trial', trial, ',
            #    failed to find node', nodeTargetId])

    def filterPitchList(self, pitchTarget):
        '''Given a list or one pitch, check if all are pitch objects; convert if necessary.

        >>> net = scale.intervalNetwork.IntervalNetwork()
        >>> net.filterPitchList('c#')
        ([<music21.pitch.Pitch C#>],
         <music21.pitch.Pitch C#>,
         <music21.pitch.Pitch C#>)

        >>> net.filterPitchList(['c#4', 'f5', 'd3'])
        ([<music21.pitch.Pitch C#4>, <music21.pitch.Pitch F5>, <music21.pitch.Pitch D3>],
         <music21.pitch.Pitch D3>,
         <music21.pitch.Pitch F5>)
        '''
        if not common.isListLike(pitchTarget):
            if isinstance(pitchTarget, str):
                pitchTarget = pitch.Pitch(pitchTarget)
            pitchTarget = [pitchTarget]
        else:
            # convert a list of string into pitch objects
            temp = []
            for p in pitchTarget:
                if isinstance(p, str):
                    temp.append(pitch.Pitch(p))
            if len(temp) == len(pitchTarget):
                pitchTarget = temp

        # automatically derive a min and max from the supplied pitch
        sortList = [(pitchTarget[i].ps, i) for i in range(len(pitchTarget))]
        sortList.sort()
        minPitch = pitchTarget[sortList[0][1]]  # first index
        maxPitch = pitchTarget[sortList[-1][1]]  # last index

        return pitchTarget, minPitch, maxPitch

    def match(self,
              pitchReference,
              nodeId,
              pitchTarget,
              comparisonAttribute='pitchClass',
              alteredDegrees=None):
        '''Given one or more pitches in `pitchTarget`, return a
        tuple of a list of matched pitches, and a list of unmatched pitches.


        >>> edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        >>> net = scale.intervalNetwork.IntervalNetwork(edgeList)
        >>> [str(p) for p in net.realizePitch('e-2')]
        ['E-2', 'F2', 'G2', 'A-2', 'B-2', 'C3', 'D3', 'E-3']

        >>> net.match('e-2', 1, 'c3')  # if e- is tonic, is 'c3' in the scale?
        ([<music21.pitch.Pitch C3>], [])

        >>> net.match('e-2', 1, 'd3')
        ([<music21.pitch.Pitch D3>], [])

        >>> net.match('e-2', 1, 'd#3')
        ([<music21.pitch.Pitch D#3>], [])

        >>> net.match('e-2', 1, 'e3')
        ([], [<music21.pitch.Pitch E3>])

        >>> pitchTarget = [pitch.Pitch('b-2'), pitch.Pitch('b2'), pitch.Pitch('c3')]
        >>> net.match('e-2', 1, pitchTarget)
        ([<music21.pitch.Pitch B-2>, <music21.pitch.Pitch C3>], [<music21.pitch.Pitch B2>])

        >>> pitchTarget = ['b-2', 'b2', 'c3', 'e-3', 'e#3', 'f2', 'e--2']
        >>> (matched, unmatched) = net.match('e-2', 1, pitchTarget)
        >>> [str(p) for p in matched]
        ['B-2', 'C3', 'E-3', 'E#3', 'F2', 'E--2']
        >>> unmatched
        [<music21.pitch.Pitch B2>]

        '''
        # these return a Node, not a nodeId
        # TODO: just getting first
        if nodeId is None:  # assume first
            nodeId = self.getTerminusLowNodes()[0]
        else:
            nodeId = self.nodeNameToNodes(nodeId)[0]

        pitchTarget, minPitch, maxPitch = self.filterPitchList(pitchTarget)

        # TODO: need to do both directions
        nodesRealized = self.realizePitch(pitchReference,
                                          nodeId,
                                          minPitch,
                                          maxPitch,
                                          alteredDegrees=alteredDegrees)

        matched = []
        noMatch = []
        # notFound = []

        for target in pitchTarget:
            found = False
            for p in nodesRealized:
                # enharmonic switch here
                match = False
                if getattr(p, comparisonAttribute) == getattr(target, comparisonAttribute):
                    match = True

                if match:
                    matched.append(target)
                    found = True
                    break
            if not found:
                noMatch.append(target)
        return matched, noMatch

    def findMissing(self,
                    pitchReference,
                    nodeId,
                    pitchTarget,
                    comparisonAttribute='pitchClass',
                    minPitch=None,
                    maxPitch=None,
                    direction=DIRECTION_ASCENDING,
                    alteredDegrees=None):
        '''
        Find all pitches in the realized scale that are not in the
        pitch target network based on the comparison attribute.


        >>> edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        >>> net = scale.intervalNetwork.IntervalNetwork(edgeList)
        >>> [str(p) for p in net.realizePitch('G3')]
        ['G3', 'A3', 'B3', 'C4', 'D4', 'E4', 'F#4', 'G4']
        >>> net.findMissing('g', 1, ['g', 'a', 'b', 'd', 'f#'])
        [<music21.pitch.Pitch C5>, <music21.pitch.Pitch E5>]
        '''
        # these return a Node, not a nodeId
        if nodeId is None:  # assume first
            nodeId = self.getTerminusLowNodes()[0]
        else:
            nodeId = self.nodeNameToNodes(nodeId)[0]

        # TODO: need to do both directions
        nodesRealized = self.realizePitch(pitchReference,
                                          nodeId,
                                          minPitch=minPitch,
                                          maxPitch=maxPitch,
                                          alteredDegrees=alteredDegrees)

        # note: reassigns min and max
        pitchTarget, minPitch, maxPitch = self.filterPitchList(pitchTarget)

        # environLocal.printDebug(['nodesRealized:', nodesRealized,])
        post = []
        for target in nodesRealized:
            match = False
            for p in pitchTarget:
                # enharmonic switch here
                if getattr(p, comparisonAttribute) == getattr(target, comparisonAttribute):
                    match = True
                    break
            # environLocal.printDebug(['looking at:', target, p, 'match', match])
            if not match:
                post.append(target)
        return post

    def find(self,
             pitchTarget,
             resultsReturned=4,
             comparisonAttribute='pitchClass',
             alteredDegrees=None):
        '''
        Given a collection of pitches, test all transpositions of a realized
        version of this network, and return the number of matches in each for
        each pitch assigned to the first node.


        >>> edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        >>> net = scale.intervalNetwork.IntervalNetwork(edgeList)

        a network built on G or D as

        >>> net.find(['g', 'a', 'b', 'd', 'f#'])
        [(5, <music21.pitch.Pitch G>), (5, <music21.pitch.Pitch D>),
         (4, <music21.pitch.Pitch A>), (4, <music21.pitch.Pitch C>)]

        >>> net.find(['g', 'a', 'b', 'c', 'd', 'e', 'f#'])
        [(7, <music21.pitch.Pitch G>), (6, <music21.pitch.Pitch D>),
         (6, <music21.pitch.Pitch C>), (5, <music21.pitch.Pitch A>)]

        If resultsReturned is None then return every such scale.
        '''
        nodeId = self.terminusLowNodes[0]
        sortList = []

        # for now, searching 12 pitches; this may be more than necessary
#         for p in [pitch.Pitch('c'), pitch.Pitch('c#'),
#                   pitch.Pitch('d'), pitch.Pitch('d#'),
#                   pitch.Pitch('e'), pitch.Pitch('f'),
#                   pitch.Pitch('f#'), pitch.Pitch('g'),
#                   pitch.Pitch('g#'), pitch.Pitch('a'),
#                   pitch.Pitch('a#'), pitch.Pitch('b'),
#                 ]:

        for p in [pitch.Pitch('c'), pitch.Pitch('c#'), pitch.Pitch('d-'),
                  pitch.Pitch('d'), pitch.Pitch('d#'), pitch.Pitch('e-'),
                  pitch.Pitch('e'), pitch.Pitch('f'),
                  pitch.Pitch('f#'), pitch.Pitch('g'),
                  pitch.Pitch('g#'), pitch.Pitch('a'), pitch.Pitch('b-'),
                  pitch.Pitch('b'), pitch.Pitch('c-'),
                  ]:  # TODO: Study this: can it be sped up with cached Pitch objects?

            # realize scales from each pitch, and then compare to pitchTarget
            # pitchTarget may be a list of pitches
            matched, unused_noMatch = self.match(
                p,
                nodeId,
                pitchTarget,
                comparisonAttribute=comparisonAttribute,
                alteredDegrees=alteredDegrees)
            sortList.append((len(matched), p))

        sortList.sort()
        sortList.reverse()  # want most matches first
        if resultsReturned is not None:
            return sortList[:resultsReturned]
        else:
            return sortList

    def transposePitchAndApplySimplification(self, intervalObj, pitchObj):
        '''
        transposes the pitch according to the given interval object and
        uses the simplification of the `pitchSimplification` property
        to simplify it afterwards.

        >>> b = scale.intervalNetwork.IntervalNetwork()
        >>> b.pitchSimplification  # default
        'maxAccidental'
        >>> i = interval.Interval('m2')
        >>> p = pitch.Pitch('C4')
        >>> allPitches = []
        >>> for j in range(15):
        ...    p = b.transposePitchAndApplySimplification(i, p)
        ...    allPitches.append(p.nameWithOctave)
        >>> allPitches
        ['D-4', 'D4', 'E-4', 'F-4', 'F4', 'G-4', 'G4', 'A-4', 'A4',
         'B-4', 'C-5', 'C5', 'D-5', 'D5', 'E-5']


        >>> b.pitchSimplification = 'mostCommon'
        >>> p = pitch.Pitch('C4')
        >>> allPitches = []
        >>> for j in range(15):
        ...    p = b.transposePitchAndApplySimplification(i, p)
        ...    allPitches.append(p.nameWithOctave)
        >>> allPitches
        ['C#4', 'D4', 'E-4', 'E4', 'F4', 'F#4', 'G4', 'A-4', 'A4', 'B-4',
         'B4', 'C5', 'C#5', 'D5', 'E-5']


        PitchSimplification can also be specified in the creation of the IntervalNetwork object

        >>> b = scale.intervalNetwork.IntervalNetwork(pitchSimplification=None)
        >>> p = pitch.Pitch('C4')
        >>> allPitches = []
        >>> for j in range(5):
        ...    p = b.transposePitchAndApplySimplification(i, p)
        ...    allPitches.append(p.nameWithOctave)
        >>> allPitches
        ['D-4', 'E--4', 'F--4', 'G---4', 'A----4']

        Note that beyond quadruple flats or sharps, pitchSimplification is automatic:

        >>> p
        <music21.pitch.Pitch A----4>
        >>> b.transposePitchAndApplySimplification(i, p)
        <music21.pitch.Pitch F#4>
        '''
        pitchSimplification = self.pitchSimplification

        if (pitchSimplification in (None, 'none')
            and ((hasattr(intervalObj, 'implicitDiatonic') and intervalObj.implicitDiatonic)
                 or (isinstance(intervalObj, interval.ChromaticInterval)))):
            pitchSimplification = 'mostCommon'

        # check cache...
        cacheKey = (repr(intervalObj), pitchObj.nameWithOctave)
        if pitchSimplification not in _transposePitchAndApplySimplificationCache:
            _transposePitchAndApplySimplificationCache[pitchSimplification] = {}
        intervalToPitchMap = _transposePitchAndApplySimplificationCache[pitchSimplification]
        if cacheKey in intervalToPitchMap:
            pass
            # return pitch.Pitch(intervalToPitchMap[cacheKey])

        if pitchSimplification == 'maxAccidental':
            pPost = intervalObj.transposePitch(pitchObj, maxAccidental=1)
        else:
            pPost = intervalObj.transposePitch(pitchObj)
            if pPost.accidental:
                if pitchSimplification == 'simplifyEnharmonic':
                    pPost.simplifyEnharmonic(inPlace=True)
                elif pitchSimplification == 'mostCommon':
                    pPost.simplifyEnharmonic(inPlace=True, mostCommon=True)
                elif pitchSimplification in (None, 'none'):
                    pass
                else:
                    raise IntervalNetworkException(
                        'unknown pitchSimplification type {0},'.format(pitchSimplification)
                        + ' allowable values are "maxAccidental" (default), "simplifyEnharmonic", '
                        + '"mostCommon", or None (or "none")')

        intervalToPitchMap[cacheKey] = pPost.nameWithOctave
        return pPost


class BoundIntervalNetwork(IntervalNetwork):
    '''
    This class is kept only because of the ICMC Paper.  Just use IntervalNetwork instead.
    '''
    pass


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
        from music21.scale import intervalNetwork
        # define ordered list of intervals
        edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        net = intervalNetwork.IntervalNetwork(edgeList)

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
        net = intervalNetwork.IntervalNetwork(edgeList)

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
        from music21.scale import intervalNetwork

        # can define a chord type as a sequence of intervals
        # to assure octave redundancy, must provide top-most interval to octave
        # this could be managed in specialized subclass

        edgeList = ['M3', 'm3', 'P4']
        net = intervalNetwork.IntervalNetwork(edgeList)

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
        net = intervalNetwork.IntervalNetwork(edgeList)
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
        from music21.scale import intervalNetwork

        # start with a major scale
        edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        netScale = intervalNetwork.IntervalNetwork(edgeList)

        # take a half diminished seventh chord
        edgeList = ['m3', 'm3', 'M3', 'M2']
        netHarmony = intervalNetwork.IntervalNetwork(edgeList)
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
        from music21.scale import intervalNetwork
        edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        net = intervalNetwork.IntervalNetwork()
        net.fillBiDirectedEdges(edgeList)

        self.assertEqual(sorted(list(net.edges.keys())), [0, 1, 2, 3, 4, 5, 6])
        self.assertEqual(sorted([str(x) for x in net.nodes.keys()]),
                         ['0', '1', '2', '3', '4', '5', 'terminusHigh', 'terminusLow'])

        self.assertEqual(repr(net.nodes[0]), '<music21.scale.intervalNetwork.Node id=0>')
        self.assertEqual(repr(net.nodes['terminusLow']),
                         "<music21.scale.intervalNetwork.Node id='terminusLow'>")

        self.assertEqual(
            repr(net.edges[0]),
            "<music21.scale.intervalNetwork.Edge bi M2 [('terminusLow', 0), (0, 'terminusLow')]>"
        )

        self.assertEqual(repr(net.edges[3]),
                         "<music21.scale.intervalNetwork.Edge bi M2 [(2, 3), (3, 2)]>")

        self.assertEqual(
            repr(net.edges[6]),
            "<music21.scale.intervalNetwork.Edge bi m2 [(5, 'terminusHigh'), ('terminusHigh', 5)]>"
        )

        # getting connections: can filter by direction
        self.assertEqual(repr(net.edges[6].getConnections(
            DIRECTION_ASCENDING)), "[(5, 'terminusHigh')]")
        self.assertEqual(repr(net.edges[6].getConnections(
            DIRECTION_DESCENDING)), "[('terminusHigh', 5)]")
        self.assertEqual(repr(net.edges[6].getConnections(
            DIRECTION_BI)), "[(5, 'terminusHigh'), ('terminusHigh', 5)]")

        # in calling get next, get a lost of edges and a lost of nodes that all
        # describe possible pathways
        self.assertEqual(net.getNext(net.nodes['terminusLow'], 'ascending'),
                         ([net.edges[0]], [net.nodes[0]]))

        self.assertEqual(net.getNext(net.nodes['terminusLow'], 'descending'),
                         ([net.edges[6]], [net.nodes[5]]))

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
                         + "['terminusLow', 0, 1, 2, 3, 4, 5, 'terminusHigh'])")

        self.assertEqual(self.realizePitchOut(net.realize('c#4', 7)),
                         '([D3, E3, F#3, G3, A3, B3, C#4, D4], '
                         + "['terminusLow', 0, 1, 2, 3, 4, 5, 'terminusHigh'])")

    def testDirectedA(self):
        from music21.scale import intervalNetwork

        # test creating a harmonic minor scale by using two complete
        # ascending and descending scales

        ascendingEdgeList = ['M2', 'm2', 'M2', 'M2', 'M2', 'M2', 'm2']
        # these are given in ascending order
        descendingEdgeList = ['M2', 'm2', 'M2', 'M2', 'm2', 'M2', 'M2']

        net = intervalNetwork.IntervalNetwork()
        net.fillDirectedEdges(ascendingEdgeList, descendingEdgeList)

        # returns a list of edges and notes
        self.assertEqual(
            repr(net.getNext(net.nodes[TERMINUS_LOW], 'ascending')),
            '([<music21.scale.intervalNetwork.Edge ascending M2 '
            + "[('terminusLow', 0)]>], [<music21.scale.intervalNetwork.Node id=0>])")

        self.assertEqual(
            repr(net.getNext(net.nodes[TERMINUS_LOW], 'descending')),
            '([<music21.scale.intervalNetwork.Edge descending M2 '
            + "[('terminusHigh', 11)]>], [<music21.scale.intervalNetwork.Node id=11>])")

        # high terminus gets the same result, as this is the wrapping point
        self.assertEqual(
            repr(net.getNext(net.nodes[TERMINUS_HIGH], 'ascending')),
            '([<music21.scale.intervalNetwork.Edge ascending M2 '
            + "[('terminusLow', 0)]>], [<music21.scale.intervalNetwork.Node id=0>])")

        self.assertEqual(
            repr(net.getNext(net.nodes[TERMINUS_LOW], 'descending')),
            '([<music21.scale.intervalNetwork.Edge descending M2 '
            + "[('terminusHigh', 11)]>], [<music21.scale.intervalNetwork.Node id=11>])")

        # this is ascending from a4 to a5, then descending from a4 to a3
        # this seems like the right thing to do
        self.assertEqual(self.realizePitchOut(net.realize('a4', 1, 'a3', 'a5')),
                         '([A3, B3, C4, D4, E4, F4, G4, A4, B4, C5, D5, E5, F#5, G#5, A5], '
                         + "['terminusLow', 6, 7, 8, 9, 10, 11, "
                         + "'terminusLow', 0, 1, 2, 3, 4, 5, 'terminusHigh'])")

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
        from music21.scale import intervalNetwork
        from music21 import scale

        sc1 = scale.MajorScale('g')
        self.assertEqual(sorted([str(x) for x in sc1.abstract._net.nodes.keys()]),
                         ['0', '1', '2', '3', '4', '5', 'terminusHigh', 'terminusLow'])
        self.assertEqual(sorted(sc1.abstract._net.edges.keys()),
                         [0, 1, 2, 3, 4, 5, 6])

        nodes = ({'id': 'terminusLow', 'degree': 1},
                 {'id': 0, 'degree': 2},
                 {'id': 'terminusHigh', 'degree': 3},
                 )

        edges = ({'interval': 'm2',
                  'connections': (
                      ['terminusLow', 0, 'bi'],
                  )},
                 {'interval': 'M3',
                  'connections': (
                      [0, 'terminusHigh', 'bi'],
                  )},
                 )

        net = intervalNetwork.IntervalNetwork()
        net.fillArbitrary(nodes, edges)
        self.assertTrue(common.whitespaceEqual(str(net.edges),
                                               '''
            OrderedDict(
            [(0, <music21.scale.intervalNetwork.Edge bi m2
                    [('terminusLow', 0), (0, 'terminusLow')]>),
             (1, <music21.scale.intervalNetwork.Edge bi M3
                     [(0, 'terminusHigh'), ('terminusHigh', 0)]>)])'''
                                               ))

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
        self.assertEqual(str(nodes), "['terminusLow', 0, 1, 2, 3, 4, 5]")

        self.assertEqual(self.realizePitchOut(net.realizeDescending('c3', 'high', minPitch='c2')),
                         "([C2, D2, E2, F2, G2, A2, B2], ['terminusLow', 0, 1, 2, 3, 4, 5])")

        # this only gets one pitch as this is descending and includes reference
        # pitch
        self.assertEqual(str(net.realizeDescending('c3', 1, includeFirst=True)),
                         "([<music21.pitch.Pitch C3>], ['terminusLow'])")

        self.assertTrue(common.whitespaceEqual(self.realizePitchOut(
            net.realizeDescending('g3', 1, 'g0', includeFirst=True)),
            '''([G0, A0, B0, C1, D1, E1, F#1,
                 G1, A1, B1, C2, D2, E2, F#2,
                 G2, A2, B2, C3, D3, E3, F#3, G3],
                ['terminusLow', 0, 1, 2, 3, 4, 5,
                 'terminusLow', 0, 1, 2, 3, 4, 5,
                 'terminusLow', 0, 1, 2, 3, 4, 5,
                 'terminusLow'])'''))

        self.assertEqual(self.realizePitchOut(
            net.realizeDescending('d6', 5, 'd4', includeFirst=True)),
            '([D4, E4, F#4, G4, A4, B4, C5, D5, E5, F#5, G5, A5, B5, C6, D6], '
            + "[3, 4, 5, 'terminusLow', 0, 1, 2, 3, 4, 5, 'terminusLow', 0, 1, 2, 3])"
        )

        self.assertEqual(self.realizePitchOut(net.realizeAscending('c3', 1)),
                         '([C3, D3, E3, F3, G3, A3, B3, C4], '
                         + "['terminusLow', 0, 1, 2, 3, 4, 5, 'terminusHigh'])")

        self.assertEqual(self.realizePitchOut(net.realizeAscending('g#2', 3)),
                         "([G#2, A2, B2, C#3, D#3, E3], [1, 2, 3, 4, 5, 'terminusHigh'])")

        self.assertEqual(self.realizePitchOut(net.realizeAscending('g#2', 3, maxPitch='e4')),
                         '([G#2, A2, B2, C#3, D#3, E3, F#3, G#3, A3, B3, C#4, D#4, E4], '
                         + "[1, 2, 3, 4, 5, 'terminusHigh', 0, 1, 2, 3, 4, 5, 'terminusHigh'])")

    def testBasicB(self):
        from music21.scale import intervalNetwork
        net = intervalNetwork.IntervalNetwork()
        net.fillMelodicMinor()

        self.assertEqual(self.realizePitchOut(net.realize('g4')),
                         '([G4, A4, B-4, C5, D5, E5, F#5, G5], '
                         + "['terminusLow', 0, 1, 2, 3, 4, 6, 'terminusHigh'])")

        # here, min and max pitches are assumed based on ascending scale
        # otherwise, only a single pitch would be returned (the terminus low)
        self.assertEqual(
            self.realizePitchOut(net.realize('g4', 1, direction=DIRECTION_DESCENDING)),
            '([G4, A4, B-4, C5, D5, E-5, F5, G5], '
            + "['terminusLow', 0, 1, 2, 3, 5, 7, 'terminusLow'])")

        # if explicitly set terminus to high, we get the expected range,
        # but now the reference pitch is the highest pitch
        self.assertEqual(self.realizePitchOut(net.realize(
            'g4', 'high', direction=DIRECTION_DESCENDING)),
            '([G3, A3, B-3, C4, D4, E-4, F4, G4], '
            + "['terminusLow', 0, 1, 2, 3, 5, 7, 'terminusHigh'])")

        # get nothing from if try to request a descending scale from the
        # lower terminus
        self.assertEqual(net.realizeDescending('g4', 'low', fillMinMaxIfNone=False),
                         ([], []))

        self.assertEqual(self.realizePitchOut(
            net.realizeDescending('g4', 'low', fillMinMaxIfNone=True)),
            "([G4, A4, B-4, C5, D5, E-5, F5], ['terminusLow', 0, 1, 2, 3, 5, 7])")

        # if we include first, we get all values
        descReal = net.realizeDescending('g4', 'low', includeFirst=True, fillMinMaxIfNone=True)
        self.assertEqual(self.realizePitchOut(descReal),
                         "([G4, A4, B-4, C5, D5, E-5, F5, G5], "
                         + "['terminusLow', 0, 1, 2, 3, 5, 7, 'terminusLow'])")

        # because this is octave repeating, we can get a range when min
        # and max are defined
        descReal = net.realizeDescending('g4', 'low', 'g4', 'g5')
        self.assertEqual(self.realizePitchOut(descReal),
                         "([G4, A4, B-4, C5, D5, E-5, F5], ['terminusLow', 0, 1, 2, 3, 5, 7])")

    def testGetPitchFromNodeStep(self):
        from music21.scale import intervalNetwork
        net = intervalNetwork.IntervalNetwork()
        net.fillMelodicMinor()
        self.assertEqual(str(net.getPitchFromNodeDegree('c4', 1, 1)), 'C4')
        self.assertEqual(str(net.getPitchFromNodeDegree('c4', 1, 5)), 'G4')

#         # ascending is default
        self.assertEqual(str(net.getPitchFromNodeDegree('c4', 1, 6)), 'A4')

        self.assertEqual(str(net.getPitchFromNodeDegree('c4', 1, 6, direction='ascending')), 'A4')

        environLocal.printDebug(['descending degree 6'])

        self.assertEqual(str(net.getPitchFromNodeDegree('c4', 1, 6, direction='descending')),
                         'A-4')

    def testNextPitch(self):
        from music21.scale import intervalNetwork
        net = intervalNetwork.IntervalNetwork()
        net.fillMelodicMinor()

        # ascending from known pitches
        self.assertEqual(str(net.nextPitch('c4', 1, 'g4', 'ascending')), 'A4')
        self.assertEqual(str(net.nextPitch('c4', 1, 'a4', 'ascending')), 'B4')
        self.assertEqual(str(net.nextPitch('c4', 1, 'b4', 'ascending')), 'C5')

        # descending
        self.assertEqual(str(net.nextPitch('c4', 1, 'c5', 'descending')), 'B-4')
        self.assertEqual(str(net.nextPitch('c4', 1, 'b-4', 'descending')), 'A-4')
        self.assertEqual(str(net.nextPitch('c4', 1, 'a-4', 'descending')), 'G4')

        # larger degree sizes
        self.assertEqual(str(net.nextPitch('c4', 1, 'c5', 'descending', stepSize=2)), 'A-4')
        self.assertEqual(str(net.nextPitch('c4', 1, 'a4', 'ascending', stepSize=2)), 'C5')

        # moving from a non-scale degree

        # if we get the ascending neighbor, we move from the d to the e-
        self.assertEqual(
            str(
                net.nextPitch(
                    'c4', 1, 'c#4', 'ascending', getNeighbor='ascending'
                )
            ),
            'E-4'
        )

        # if we get the descending neighbor, we move from c to d
        self.assertEqual(str(net.nextPitch('c4', 1, 'c#4', 'ascending',
                                           getNeighbor='descending')), 'D4')

        # if on a- and get ascending neighbor, move from a to b-
        self.assertEqual(str(net.nextPitch('c4', 1, 'a-', 'ascending',
                                           getNeighbor='ascending')), 'B4')

        # if on a- and get descending neighbor, move from g to a
        self.assertEqual(str(net.nextPitch('c4', 1, 'a-', 'ascending',
                                           getNeighbor='descending')), 'A4')

        # if on b, ascending neighbor, move from c to b-
        self.assertEqual(str(net.nextPitch('c4', 1, 'b3', 'descending',
                                           getNeighbor='ascending')), 'B-3')

        # if on c-4, use mode derivation instead of neighbor, move from b4 to c4
        self.assertEqual(str(net.nextPitch('c4', 1, 'c-4', 'ascending')), 'C4')

        self.assertEqual(net.getNeighborNodeIds(
            pitchReference='c4', nodeName=1, pitchTarget='c#'),
            ('terminusHigh', 0))

        self.assertEqual(net.getNeighborNodeIds(
            pitchReference='c4', nodeName=1, pitchTarget='d#'), (1, 2))

        self.assertEqual(net.getNeighborNodeIds(
            pitchReference='c4', nodeName=1, pitchTarget='b'), (6, 'terminusHigh'))

        self.assertEqual(net.getNeighborNodeIds(
            pitchReference='c4', nodeName=1, pitchTarget='b-'), (4, 6))

        self.assertEqual(
            net.getNeighborNodeIds(
                pitchReference='c4', nodeName=1,
                pitchTarget='b', direction='descending'),
            (7, 'terminusLow'))

        self.assertEqual(
            net.getNeighborNodeIds(
                pitchReference='c4', nodeName=1,
                pitchTarget='b-', direction='descending'),
            (7, 'terminusLow'))

        # if on b, descending neighbor, move from b- to a-
        self.assertEqual(
            str(net.nextPitch(
                'c4', 1, 'b4', 'descending',
                getNeighbor='descending')),
            'A-4')


# ------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [IntervalNetwork, Node, Edge]

if __name__ == '__main__':
    import music21
    music21.mainTest(Test)

