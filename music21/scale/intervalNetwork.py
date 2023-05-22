# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         scale.intervalNetwork.py
# Purpose:      A graph of intervals, for scales and harmonies.
#
# Authors:      Christopher Ariza
#               Michael Scott Asato Cuthbert
#
# Copyright:    Copyright © 2010-2023 Michael Scott Asato Cuthbert
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

Changed in v8: nodeId and nodeName standardized.  TERMINUS and DIRECTION
are now Enums.
'''
from __future__ import annotations

from collections import OrderedDict
from collections.abc import Sequence
import copy
import enum
import typing as t

from music21 import common
from music21 import environment
from music21 import exceptions21
from music21 import interval
from music21 import note
from music21 import pitch
from music21 import prebase

environLocal = environment.Environment('scale.intervalNetwork')

class Terminus(enum.Enum):
    '''
    One of the two Termini of a scale, either Terminus.LOW or
    Terminus.HIGH
    '''
    LOW = 'terminusLow'
    HIGH = 'terminusHigh'

    def __repr__(self):
        return 'Terminus.' + self.name

    def __str__(self):
        return 'Terminus.' + self.name

class Direction(enum.Enum):
    '''
    An enumerated Direction for a scale, either Direction.ASCENDING,
    Direction.DESCENDING, or Direction.BI (bidirectional)
    '''
    BI = 'bi'
    ASCENDING = 'ascending'
    DESCENDING = 'descending'

    def __repr__(self):
        return 'Direction.' + self.name

    def __str__(self):
        return 'Direction.' + self.name


CacheKey = tuple[
    int | Terminus, str, str | None, str | None, bool, bool | None]


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
    Direction.BI

    Return the stored Interval object

    >>> i = interval.Interval('M3')
    >>> e1 = scale.intervalNetwork.Edge(i, id=0)
    >>> n1 = scale.intervalNetwork.Node(id=0, degree=0)
    >>> n2 = scale.intervalNetwork.Node(id=1, degree=1)
    >>> e1.addDirectedConnection(n1, n2, scale.Direction.ASCENDING)
    >>> e1.interval
    <music21.interval.Interval M3>

    Return the direction of the Edge.

    >>> i = interval.Interval('M3')
    >>> e1 = scale.intervalNetwork.Edge(i, id=0)
    >>> n1 = scale.intervalNetwork.Node(id=0, degree=0)
    >>> n2 = scale.intervalNetwork.Node(id=1, degree=1)
    >>> e1.addDirectedConnection(n1, n2, scale.Direction.ASCENDING)
    >>> e1.direction
    Direction.ASCENDING
    '''
    # noinspection PyShadowingBuiltins
    # pylint: disable=redefined-builtin
    def __init__(self,
                 intervalData: interval.Interval | str,
                 id=None,  # id is okay: @ReservedAssignment
                 direction=Direction.BI):
        if isinstance(intervalData, str):
            i = interval.Interval(intervalData)
        else:
            i = intervalData
        self.interval: interval.Interval = i
        # direction will generally be set when connections added
        self.direction: Direction = direction
        self.weight = 1.0
        # store id
        self.id = id

        # one or two pairs of Node ids that this Edge connects
        # if there are two, it is a bidirectional, w/ first ascending
        self._connections: list[tuple[int | Terminus, int | Terminus]] = []

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

    def addDirectedConnection(
        self,
        node1: Node | int | Terminus,
        node2: Node | int | Terminus,
        direction=None
    ) -> None:
        '''
        Provide two Node objects that are connected by this Edge,
        in the direction from the first to the second.

        When calling directly, a direction, either
        ascending or descending, should be set here;
        this will override whatever the interval is.
        If None, this will not be set.

        >>> i = interval.Interval('M3')
        >>> e1 = scale.intervalNetwork.Edge(i, id=0)

        >>> n1 = scale.intervalNetwork.Node(id=0, degree=0)
        >>> n2 = scale.intervalNetwork.Node(id=1, degree=1)

        >>> e1.addDirectedConnection(n1, n2, scale.Direction.ASCENDING)
        >>> e1.connections
        [(0, 1)]
        >>> e1
        <music21.scale.intervalNetwork.Edge Direction.ASCENDING M3 [(0, 1)]>
        '''
        # may be Node objects, or number, or Terminus
        if isinstance(node1, (Terminus, int)):
            n1Id = node1
        else:  # assume an Node
            n1Id = node1.id

        if isinstance(node2, (Terminus, int)):
            n2Id = node2
        else:  # assume an Node
            n2Id = node2.id

        self._connections.append((n1Id, n2Id))

        # must specify a direction
        if direction not in (Direction.ASCENDING, Direction.DESCENDING):
            raise EdgeException('must request a direction')
        self.direction = direction

    def addBiDirectedConnections(self, node1, node2):
        '''
        Provide two Edge objects that pass through
        this Node, in the direction from the first to the second.

        >>> i = interval.Interval('M3')
        >>> e1 = scale.intervalNetwork.Edge(i, id=0)
        >>> n1 = scale.intervalNetwork.Node(id=scale.Terminus.LOW, degree=0)
        >>> n2 = scale.intervalNetwork.Node(id=1, degree=1)

        >>> e1.addBiDirectedConnections(n1, n2)
        >>> e1.connections
        [(Terminus.LOW, 1), (1, Terminus.LOW)]
        >>> e1
        <music21.scale.intervalNetwork.Edge Direction.BI M3
            [(Terminus.LOW, 1), (1, Terminus.LOW)]>
        '''
        # must assume here that n1 to n2 is ascending; need to know
        self.addDirectedConnection(node1, node2, Direction.ASCENDING)
        self.addDirectedConnection(node2, node1, Direction.DESCENDING)
        self.direction = Direction.BI  # can be ascending, descending

    def getConnections(
        self,
        direction: None | Direction = None
    ) -> list[tuple[int | Terminus, int | Terminus]]:
        '''
        Callable as a property (.connections) or as a method
        (.getConnections(direction)):

        Return a list of connections between Nodes, represented as pairs
        of Node ids. If a direction is specified, and if the Edge is
        directional, only the desired directed values will be returned.

        >>> i = interval.Interval('M3')
        >>> e1 = scale.intervalNetwork.Edge(i, id=0)
        >>> n1 = scale.intervalNetwork.Node(id=scale.Terminus.LOW, degree=1)
        >>> n2 = scale.intervalNetwork.Node(id=1, degree=2)

        >>> e1.addBiDirectedConnections(n1, n2)
        >>> e1.connections
        [(Terminus.LOW, 1), (1, Terminus.LOW)]
        >>> e1.getConnections(scale.Direction.ASCENDING)
        [(Terminus.LOW, 1)]
        >>> e1.getConnections(scale.Direction.DESCENDING)
        [(1, Terminus.LOW)]
        '''
        if direction is None:
            direction = self.direction  # assign native direction

        # do not need to supply direction, because direction is defined
        # in this Edge.
        if self.direction == direction:
            return self._connections

        # if requesting bi from a mono directional edge is an error
        if (direction == Direction.BI
                and self.direction in (Direction.ASCENDING, Direction.DESCENDING)):
            raise EdgeException('cannot request a bi direction from a mono direction')

        # if bi and we get an ascending/descending request
        if (direction in (Direction.ASCENDING, Direction.DESCENDING)
                and self.direction == Direction.BI):
            # assume that in a bi-representation, the first is ascending
            # the second is descending
            # NOTE: this may not mean that we are actually ascending, we may
            # use the direction of the interval to determine
            if direction == Direction.ASCENDING:
                return [self._connections[0]]
            elif direction == Direction.DESCENDING:
                return [self._connections[1]]
        # if no connections are possible, return empty list
        return []

    # keep separate property, since getConnections takes a direction argument.
    @property
    def connections(self) -> list[tuple[int | Terminus, int | Terminus]]:
        return self.getConnections()


class Node(prebase.ProtoM21Object, common.SlottedObjectMixin):
    '''
    Abstraction of an unrealized Pitch Node.

    The Node `id` is used to store connections in Edges and has no real meaning.

    Terminal Nodes have special ids: Terminus.LOW, Terminus.HIGH

    The Node `degree` is translated to scale degrees in various applications,
    and is used to request a pitch from the network.

    The `weight` attribute is used to probabilistically select between
    multiple nodes when multiple nodes satisfy either a branching option in a pathway
    or a request for a degree.

    TODO: replace w/ NamedTuple; eliminate id, and have a terminus: low, high, None
    '''
    __slots__ = ('id', 'degree', 'weight')

    # noinspection PyShadowingBuiltins
    # pylint: disable=redefined-builtin
    def __init__(self, id: Terminus | int, degree: int, weight: float = 1.0):
        # store id, either as string, such as terminusLow, or a number.
        # ids are unique to any node in the network
        self.id: Terminus | int = id
        # the degree is used to define ordered node counts from the bottom
        # the degree is analogous to scale degree or degree
        # more than one node may have the same degree
        self.degree: int = degree
        # node weight might be used to indicate importance of scale positions
        self.weight: float = weight

    def __hash__(self):
        hashTuple = (self.id, self.degree, self.weight)
        return hash(hashTuple)

    def __eq__(self, other):
        '''
        Nodes are equal if everything in the object.__slots__ is equal.

        >>> n1 = scale.intervalNetwork.Node(id=3, degree=1)
        >>> n2 = scale.intervalNetwork.Node(id=3, degree=1)
        >>> n3 = scale.intervalNetwork.Node(id=2, degree=1)
        >>> n1 == n2
        True
        >>> n1 == n3
        False
        >>> n2.weight = 2.0
        >>> n1 == n2
        False

        >>> n4 = scale.intervalNetwork.Node(id=scale.Terminus.LOW, degree=1)
        >>> n5 = scale.intervalNetwork.Node(id=scale.Terminus.LOW, degree=1)
        >>> n4 == n5
        True
        '''
        return hash(self) == hash(other)

    def _reprInternal(self):
        return f'id={self.id!r}'


# ------------------------------------------------------------------------------
class IntervalNetworkException(exceptions21.Music21Exception):
    pass


# presently edges are interval objects, can be marked as
# ascending, descending, or bidirectional
# edges are stored in dictionary by index values

# Nodes are undefined pitches; pitches are realized on demand.
# Nodes are stored as an unordered list of coordinate pairs.
# Pairs are edge indices: showing which edges connect to this node
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
                 edgeList: Sequence[interval.Interval | str] = (),
                 octaveDuplicating=False,
                 deterministic=True,
                 pitchSimplification='maxAccidental'):
        # store each edge with an index that is incremented when added
        # these values have no fixed meaning but are only for reference
        self.edgeIdCount = 0
        self.nodeIdCount = 0

        # a dictionary of Edge object, where keys are edgeId values
        # Edges store directed connections between Node ids
        self.edges: OrderedDict[Terminus | int, Edge] = OrderedDict()

        # nodes suggest Pitches, but Pitches are not stored
        self.nodes: OrderedDict[Terminus | int, Node] = OrderedDict()

        if edgeList:  # auto initialize
            self.fillBiDirectedEdges(edgeList)

        # define if pitches duplicate each octave
        self.octaveDuplicating = octaveDuplicating
        self.deterministic = deterministic

        # could be 'simplifyEnharmonic', 'mostCommon' or None
        self.pitchSimplification = pitchSimplification

        # store segments
        self._ascendingCache: OrderedDict[
            CacheKey,
            tuple[list[pitch.Pitch], list[Terminus | int]]
        ] = OrderedDict()
        self._descendingCache: OrderedDict[
            CacheKey,
            tuple[list[pitch.Pitch], list[Terminus | int]]
        ] = OrderedDict()

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
        if not isinstance(other, self.__class__):
            return False
        for attr in ('edgeIdCount', 'nodeIdCount', 'edges', 'nodes',
                     'octaveDuplicating', 'deterministic', 'pitchSimplification'):
            if getattr(self, attr) != getattr(other, attr):
                return False
        return True

    def fillBiDirectedEdges(self, edgeList: Sequence[interval.Interval | str]):
        # noinspection PyShadowingNames
        '''
        Given an ordered list of bi-directed edges given as :class:`~music21.interval.Interval`
        specifications, create and define appropriate Nodes. This
        assumes that all edges are bi-directed and all edges are in order.

        >>> edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        >>> net = scale.intervalNetwork.IntervalNetwork()
        >>> net.nodes
        OrderedDict()
        >>> net.edges
        OrderedDict()


        >>> net.fillBiDirectedEdges(edgeList)
        >>> net.nodes
        OrderedDict([(Terminus.LOW, <music21.scale.intervalNetwork.Node id=Terminus.LOW>),
                     (0, <music21.scale.intervalNetwork.Node id=0>),
                     (1, <music21.scale.intervalNetwork.Node id=1>),
                     ...
                     (5, <music21.scale.intervalNetwork.Node id=5>),
                     (Terminus.HIGH, <music21.scale.intervalNetwork.Node id=Terminus.HIGH>)])
        >>> net.edges
        OrderedDict([(0, <music21.scale.intervalNetwork.Edge Direction.BI M2
                            [(Terminus.LOW, 0), (0, Terminus.LOW)]>),
                     (1, <music21.scale.intervalNetwork.Edge Direction.BI M2 [(0, 1), (1, 0)]>),
                     (2, <music21.scale.intervalNetwork.Edge Direction.BI m2 [(1, 2), (2, 1)]>),
                     ...
                     (5, <music21.scale.intervalNetwork.Edge Direction.BI M2 [(4, 5), (5, 4)]>),
                     (6, <music21.scale.intervalNetwork.Edge Direction.BI m2
                            [(5, Terminus.HIGH), (Terminus.HIGH, 5)]>)])

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

        nLow = Node(id=Terminus.LOW, degree=degreeCount)
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
                nHigh = Node(id=Terminus.HIGH, degree=degreeCount)
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

        # if both are equal, then assigning steps is easy
        if len(ascendingEdgeList) != len(descendingEdgeList):
            # problem here is that we cannot automatically assign degree values
            raise IntervalNetworkException('cannot manage unequal sized directed edges')

        degreeCount = 1  # steps start from one
        nLow = Node(id=Terminus.LOW, degree=degreeCount)
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
                nHigh = Node(id=Terminus.HIGH, degree=degreeCount)  # degree is same as start
                nFollowing = nHigh

            # add to node dictionary
            self.nodes[nFollowing.id] = nFollowing

            # then, create edge and connection; eName is interval
            e = Edge(eName, id=self.edgeIdCount)
            self.edges[e.id] = e
            self.edgeIdCount += 1

            e.addDirectedConnection(nPrevious, nFollowing,
                                    direction=Direction.ASCENDING)
            # update previous with the node created after this edge
            nPrevious = nFollowing

        # repeat for descending, but reverse direction, and use
        # same low and high nodes
        degreeCount = 1  # steps start from one
        nLow = self.nodes[Terminus.LOW]  # get node; do not need to add
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
                nHigh = self.nodes[Terminus.HIGH]
                nFollowing = nHigh

            # then, create edge and connection
            e = Edge(eName, id=self.edgeIdCount)
            self.edges[e.id] = e
            self.edgeIdCount += 1

            # order here is reversed from above
            e.addDirectedConnection(nFollowing, nPrevious, direction=Direction.DESCENDING)
            # update previous with the node created after this edge
            nPrevious = nFollowing

    def fillArbitrary(self, nodes, edges):
        # noinspection PyShadowingNames
        '''
        Fill any arbitrary network given node and edge definitions.

        Nodes must be defined by a dictionary of id and degree values.
        There must be a terminusLow and terminusHigh id as string::

            nodes = ({'id': Terminus.LOW, 'degree': 1},
                     {'id': 0, 'degree': 2},
                     {'id': Terminus.HIGH, 'degree': 3},
                    )

        Edges must be defined by a dictionary of :class:`~music21.interval.Interval`
        strings and connections. Values for `id` will be automatically assigned.
        Each connection must define direction and pairs of valid node ids::

            edges = ({'interval': 'm2',
                      'connections': ([Terminus.LOW, 0, Direction.BI],)
                      },
                     {'interval': 'M3',
                      'connections': ([0, Terminus.HIGH, Direction.BI],)
                      },
                    )


        >>> nodes = ({'id': scale.Terminus.LOW, 'degree': 1},
        ...          {'id': 0, 'degree': 2},
        ...          {'id': scale.Terminus.HIGH, 'degree': 3})
        >>> edges = ({'interval': 'm2',
        ...           'connections': ([scale.Terminus.LOW, 0, scale.Direction.BI],)},
        ...          {'interval': 'M3',
        ...           'connections': ([0, scale.Terminus.HIGH, scale.Direction.BI],)},)

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
                if direction == Direction.BI:
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
        nodes = ({'id': Terminus.LOW, 'degree': 1},  # a
                 {'id': 0, 'degree': 2},  # b
                 {'id': 1, 'degree': 3},  # c
                 {'id': 2, 'degree': 4},  # d
                 {'id': 3, 'degree': 5},  # e

                 {'id': 4, 'degree': 6},  # f# ascending
                 {'id': 5, 'degree': 6},  # f
                 {'id': 6, 'degree': 7},  # g# ascending
                 {'id': 7, 'degree': 7},  # g
                 {'id': Terminus.HIGH, 'degree': 8},  # a
                 )

        edges = ({'interval': 'M2',
                  'connections': ([Terminus.LOW, 0, Direction.BI],)  # a to b
                  },
                 {'interval': 'm2',
                  'connections': ([0, 1, Direction.BI],)  # b to c
                  },
                 {'interval': 'M2',
                  'connections': ([1, 2, Direction.BI],)  # c to d
                  },
                 {'interval': 'M2',
                  'connections': ([2, 3, Direction.BI],)  # d to e
                  },
                 {'interval': 'M2',
                  'connections': ([3, 4, Direction.ASCENDING],)  # e to f#
                  },
                 {'interval': 'M2',
                  'connections': ([4, 6, Direction.ASCENDING],)  # f# to g#
                  },
                 {'interval': 'm2',
                  'connections': ([6, Terminus.HIGH, Direction.ASCENDING],)  # g# to a
                  },
                 {'interval': 'M2',
                  'connections': ([Terminus.HIGH, 7, Direction.DESCENDING],)  # a to g
                  },
                 {'interval': 'M2',
                  'connections': ([7, 5, Direction.DESCENDING],)  # g to f
                  },
                 {'interval': 'm2',
                  'connections': ([5, 3, Direction.DESCENDING],)  # f to e
                  },
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

        >>> n1 = scale.intervalNetwork.Node(id=1, degree=1, weight=1000000)
        >>> n2 = scale.intervalNetwork.Node(id=2, degree=1, weight=1)
        >>> e1 = scale.intervalNetwork.Edge(interval.Interval('m3'), id=1)
        >>> e2 = scale.intervalNetwork.Edge(interval.Interval('m3'), id=2)
        >>> net = scale.intervalNetwork.IntervalNetwork()
        >>> e, n = net.weightedSelection([e1, e2], [n1, n2])

        Note: this may fail as there is a slight chance to get 2

        >>> e.id
        1
        >>> n.id
        1
        '''
        # use index values as values
        iValues = list(range(len(edges)))
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
            if nId == Terminus.HIGH:
                continue
            if x is None:
                x = n.degree
            if n.degree > x:
                x = n.degree
        return x

    @property
    def terminusLowNodes(self) -> list[Node]:
        '''
        Return a list of first Nodes, or Nodes that contain Terminus.LOW.

        >>> edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        >>> net = scale.intervalNetwork.IntervalNetwork()
        >>> net.fillBiDirectedEdges(edgeList)
        >>> net.terminusLowNodes
        [<music21.scale.intervalNetwork.Node id=Terminus.LOW>]

        Note that this list currently always has one element.
        '''
        post = []
        # for now, there is only one
        post.append(self.nodes[Terminus.LOW])
        return post

    @property
    def terminusHighNodes(self):
        '''
        Return a list of last Nodes, or Nodes that contain Terminus.HIGH.

        >>> edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        >>> net = scale.intervalNetwork.IntervalNetwork()
        >>> net.fillBiDirectedEdges(edgeList)
        >>> net.terminusHighNodes
        [<music21.scale.intervalNetwork.Node id=Terminus.HIGH>]
        '''
        post = []
        # for now, there is only one
        post.append(self.nodes[Terminus.HIGH])
        return post

    # --------------------------------------------------------------------------

    def getNodeDegreeDictionary(self, equateTermini: bool = True):
        '''
        Return a dictionary of node-id, node-degree pairs.
        The same degree may be given for each node

        There may not be an unambiguous way to determine the degree.
        Or, a degree may have different meanings when ascending or descending.

        If `equateTermini` is True, the terminals will be given the same degree.
        '''
        post = OrderedDict()
        for nId, n in self.nodes.items():
            if equateTermini:
                if nId == Terminus.HIGH:
                    # get the same degree as the low
                    post[nId] = self.nodes[Terminus.LOW].degree
                else:
                    post[nId] = n.degree
            else:  # directly assign from attribute
                post[nId] = n.degree

        return post

    def nodeIdToDegree(self, nId):
        '''
        Given a strict node id (the .id attribute of the Node), return the degree.

        There may not be an unambiguous way to determine the degree.
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
        >>> net.nodeIdToEdgeDirections(scale.Terminus.LOW)
        [Direction.BI]
        >>> net.nodeIdToEdgeDirections(0)
        [Direction.BI, Direction.BI]
        >>> net.nodeIdToEdgeDirections(6)
        [Direction.ASCENDING, Direction.ASCENDING]
        >>> net.nodeIdToEdgeDirections(5)
        [Direction.DESCENDING, Direction.DESCENDING]

        This node has bi-directional (from below),
        ascending (to above), and descending (from above)
        edge connections connections

        >>> net.nodeIdToEdgeDirections(3)
        [Direction.BI, Direction.ASCENDING, Direction.DESCENDING]
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

    def degreeModulus(self, degree: int) -> int:
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

    def nodeNameToNodes(self,
                        nodeId: Node | int | Terminus | None,
                        *,
                        equateTermini=True,
                        permitDegreeModuli=True):
        '''
        The `nodeId` parameter may be a :class:`~music21.scale.intervalNetwork.Node` object,
        a node degree (as a number), a terminus string, or a None (indicating Terminus.LOW).

        Return a list of Node objects that match this identification.

        If `equateTermini` is True, and the name given is a degree number,
        then the first terminal will return both the first and last.

        >>> edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        >>> net = scale.intervalNetwork.IntervalNetwork()
        >>> net.fillBiDirectedEdges(edgeList)
        >>> net.nodeNameToNodes(1)[0]
        <music21.scale.intervalNetwork.Node id=Terminus.LOW>
        >>> net.nodeNameToNodes(scale.Terminus.HIGH)
        [<music21.scale.intervalNetwork.Node id=Terminus.HIGH>]
        >>> net.nodeNameToNodes(scale.Terminus.LOW)
        [<music21.scale.intervalNetwork.Node id=Terminus.LOW>]

        Test using a nodeStep, or an integer nodeName

        >>> net.nodeNameToNodes(1)
        [<music21.scale.intervalNetwork.Node id=Terminus.LOW>,
         <music21.scale.intervalNetwork.Node id=Terminus.HIGH>]
        >>> net.nodeNameToNodes(1, equateTermini=False)
        [<music21.scale.intervalNetwork.Node id=Terminus.LOW>]
        >>> net.nodeNameToNodes(2)
        [<music21.scale.intervalNetwork.Node id=0>]

        With degree moduli, degree zero is the top-most non-terminal
        (since terminals are redundant)

        >>> net.nodeNameToNodes(0)
        [<music21.scale.intervalNetwork.Node id=5>]
        >>> net.nodeNameToNodes(-1)
        [<music21.scale.intervalNetwork.Node id=4>]
        >>> net.nodeNameToNodes(8)
        [<music21.scale.intervalNetwork.Node id=Terminus.LOW>,
         <music21.scale.intervalNetwork.Node id=Terminus.HIGH>]
        '''
        # if a number, this is interpreted as a node degree
        if isinstance(nodeId, int):
            post = []
            nodeStep = self.getNodeDegreeDictionary(
                equateTermini=equateTermini)
            for nId, nStep in nodeStep.items():
                if nodeId == nStep:
                    post.append(self.nodes[nId])
            # if no matches, and moduli comparisons are permitted
            if not post and permitDegreeModuli:
                for nId, nStep in nodeStep.items():
                    if self.degreeModulus(nodeId) == nStep:
                        post.append(self.nodes[nId])
            return post
        elif isinstance(nodeId, Terminus):
            if nodeId == Terminus.LOW:
                return self.terminusLowNodes  # returns a list
            elif nodeId == Terminus.HIGH:
                return self.terminusHighNodes  # returns a list
        elif isinstance(nodeId, Node):
            # look for direct match
            for nId in self.nodes:
                n = self.nodes[nId]
                if n is nodeId:  # could be a == comparison?
                    return [n]  # return only one
        elif isinstance(nodeId, str):
            raise IntervalNetworkException(f'Strings like {nodeId!r} are no longer valid nodeIds.')
        else:  # match coords
            raise IntervalNetworkException(f'cannot filter by: {nodeId}')

    def getNext(self, nodeStart, direction):
        '''
        Given a Node, get two lists, one of next Edges, and one of next Nodes,
        searching all Edges to find all matches.

        There may be more than one possibility. If so, the caller must look
        at the Edges and determine which to use

        >>> edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        >>> net = scale.intervalNetwork.IntervalNetwork()
        >>> net.fillBiDirectedEdges(edgeList)
        >>> net.nodeNameToNodes(1)[0]
        <music21.scale.intervalNetwork.Node id=Terminus.LOW>
        '''

        postEdge = []
        postNodeId = []
        # search all edges to find Edges that start with this node id
        srcId = nodeStart.id

        # if we are at terminus low and descending, must wrap around
        if srcId == Terminus.LOW and direction == Direction.DESCENDING:
            srcId = Terminus.HIGH
        # if we are at terminus high and ascending, must wrap around
        elif srcId == Terminus.HIGH and direction == Direction.ASCENDING:
            srcId = Terminus.LOW

        for k in self.edges:
            e = self.edges[k]
            # only getting ascending connections
            pairs = e.getConnections(direction)
            if not pairs:
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

    def processAlteredNodes(self,
                            alteredDegrees,
                            n,
                            p,
                            *,
                            direction):
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
        # if ascending or descending, and this is a bidirectional alteration
        # then apply

        if direction == directionSpec:
            match = True
        # if request is bidrectional and the spec is for ascending and
        # descending
        elif (direction == Direction.BI
              and directionSpec in (Direction.ASCENDING, Direction.DESCENDING)):
            match = True

        elif (direction in (Direction.ASCENDING, Direction.DESCENDING)
              and directionSpec == Direction.BI):
            match = True

        if match:
            # environLocal.printDebug(['matched direction', direction])
            pPost = self.transposePitchAndApplySimplification(
                alteredDegrees[n.degree]['interval'], p)
            return pPost

        return p

    def getUnalteredPitch(
        self,
        pitchObj,
        nodeObj,
        *,
        direction=Direction.BI,
        alteredDegrees=None
    ) -> pitch.Pitch:
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

    def nextPitch(
        self,
        pitchReference: pitch.Pitch | str,
        nodeName: Node | int | Terminus | None,
        pitchOrigin: pitch.Pitch | str,
        *,
        direction: Direction = Direction.ASCENDING,
        stepSize=1,
        alteredDegrees=None,
        getNeighbor: bool | Direction = True
    ):
        # noinspection PyShadowingNames
        '''
        Given a pitchReference, nodeName, and a pitch origin, return the next pitch.

        The `nodeName` parameter may be a :class:`~music21.scale.intervalNetwork.Node` object,
        a node degree, a Terminus Enum, or a None (indicating Terminus.LOW).


        >>> edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        >>> net = scale.intervalNetwork.IntervalNetwork()
        >>> net.fillBiDirectedEdges(edgeList)
        >>> net.nextPitch('g', 1, 'f#5', direction=scale.Direction.ASCENDING)
        <music21.pitch.Pitch G5>
        >>> net.nextPitch('g', 1, 'f#5', direction=scale.Direction.DESCENDING)
        <music21.pitch.Pitch E5>

        The `stepSize` parameter can be configured to permit different sized steps
        in the specified direction.

        >>> net.nextPitch('g', 1, 'f#5',
        ...               direction=scale.Direction.ASCENDING,
        ...               stepSize=2)
        <music21.pitch.Pitch A5>

        Altered degrees can be given to temporarily change the pitches returned
        without affecting the network as a whole.

        >>> alteredDegrees = {2: {'direction': scale.Direction.BI,
        ...                       'interval': interval.Interval('-a1')}}
        >>> net.nextPitch('g', 1, 'g2',
        ...               direction=scale.Direction.ASCENDING,
        ...               alteredDegrees=alteredDegrees)
        <music21.pitch.Pitch A-2>
        >>> net.nextPitch('g', 1, 'a-2',
        ...               direction=scale.Direction.ASCENDING,
        ...               alteredDegrees=alteredDegrees)
        <music21.pitch.Pitch B2>
        '''
        if pitchOrigin is None:
            raise TypeError('No pitch origin for calling next on this pitch!')

        if isinstance(pitchOrigin, str):
            pitchOriginObj = pitch.Pitch(pitchOrigin)
        else:
            pitchOriginObj = copy.deepcopy(pitchOrigin)

        pCollect = None

        # get the node id that we are starting with
        nodeId = self.getRelativeNodeId(pitchReference,
                                        nodeId=nodeName,
                                        pitchTarget=pitchOriginObj,
                                        direction=direction,
                                        alteredDegrees=alteredDegrees)

        # environLocal.printDebug(['nextPitch()', 'got node Id', nodeId,
        #  'direction', direction, 'self.nodes[nodeId].degree', self.nodes[nodeId].degree,
        #  'pitchOriginObj', pitchOriginObj])
        usedNeighbor = False
        # if no match, get the neighbor
        if (nodeId is None
                and getNeighbor in (True, Direction.ASCENDING, Direction.DESCENDING, Direction.BI)):
            usedNeighbor = True
            lowId, highId = self.getNeighborNodeIds(pitchReference=pitchReference,
                                                    nodeName=nodeName,
                                                    pitchTarget=pitchOriginObj,
                                                    direction=direction)  # must add direction

            # environLocal.printDebug(['nextPitch()', 'looking for neighbor',
            #                         'getNeighbor', getNeighbor, 'source nodeId', nodeId,
            #                         'lowId/highId', lowId, highId])

            # replace the node with the nearest neighbor
            if getNeighbor == Direction.DESCENDING:
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
        p.octave = pitchOriginObj.octave

        # correct for derived pitch crossing octave boundary
        # https://github.com/cuthbertLab/music21/issues/319
        alterSemitones = 0
        degree = self.nodeIdToDegree(nodeId)
        if alteredDegrees and degree in alteredDegrees:
            alterSemitones = alteredDegrees[degree]['interval'].semitones
        if ((usedNeighbor and getNeighbor == Direction.DESCENDING)
                or (not usedNeighbor and direction == Direction.ASCENDING)):
            while p.octave is not None and p.transpose(alterSemitones) > pitchOriginObj:
                p.octave -= 1
        else:
            while p.octave is not None and p.transpose(alterSemitones) < pitchOriginObj:
                p.octave += 1

        # pitchObj = p
        n = self.nodes[nodeId]
        # pCollect = p  # usually p, unless altered

        for i in range(stepSize):
            postEdge, postNode = self.getNext(n, direction)
            if len(postEdge) > 1:
                # do a weighted selection based on node weights,
                e, n = self.weightedSelection(postEdge, postNode)
                intervalObj = e.interval
            else:
                intervalObj = postEdge[0].interval  # get first
                n = postNode[0]  # n is passed on

            # environLocal.printDebug(['nextPitch()', 'intervalObj', intervalObj,
            #  'p', p, 'postNode', postNode])
            # n = postNode[0]

            # for now, only taking first edge
            if direction == Direction.ASCENDING:
                p = self.transposePitchAndApplySimplification(intervalObj, p)
            else:
                p = self.transposePitchAndApplySimplification(intervalObj.reverse(), p)
            pCollect = self.processAlteredNodes(alteredDegrees=alteredDegrees,
                                                 n=n,
                                                 p=p,
                                                 direction=direction)

        return pCollect

    # TODO: need to collect intervals as well

    def _getCacheKey(
        self,
        nodeObj: Node,
        pitchReference: pitch.Pitch,
        minPitch: pitch.Pitch | None,
        maxPitch: pitch.Pitch | None,
        *,
        includeFirst: bool,
        reverse: bool | None = None,  # only meaningful for descending
    ) -> CacheKey:
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
        return (nodeObj.id,
                pitchReference.nameWithOctave,
                minKey,
                maxKey,
                includeFirst,
                reverse,
                )

    def realizeAscending(
        self,
        pitchReference: pitch.Pitch | str,
        nodeId: Node | int | Terminus | None = None,
        minPitch: pitch.Pitch | str | None = None,
        maxPitch: pitch.Pitch | str | None = None,
        *,
        alteredDegrees=None,
        fillMinMaxIfNone=False
    ) -> tuple[list[pitch.Pitch], list[Terminus | int]]:
        # noinspection PyShadowingNames
        '''
        Given a reference pitch, realize upwards to a maximum pitch.

        >>> edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']

        >>> net = scale.intervalNetwork.IntervalNetwork()
        >>> net.fillBiDirectedEdges(edgeList)
        >>> (pitches, nodeKeys) = net.realizeAscending('c2', 1, 'c5', 'c6')
        >>> [str(p) for p in pitches]
        ['C5', 'D5', 'E5', 'F5', 'G5', 'A5', 'B5', 'C6']
        >>> nodeKeys
        [Terminus.HIGH, 0, 1, 2, 3, 4, 5, Terminus.HIGH]

        >>> net = scale.intervalNetwork.IntervalNetwork(octaveDuplicating=True)
        >>> net.fillBiDirectedEdges(edgeList)
        >>> (pitches, nodeKeys) = net.realizeAscending('c2', 1, 'c5', 'c6')
        >>> [str(p) for p in pitches]
        ['C5', 'D5', 'E5', 'F5', 'G5', 'A5', 'B5', 'C6']
        >>> nodeKeys
        [Terminus.LOW, 0, 1, 2, 3, 4, 5, Terminus.HIGH]
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
                                                direction=Direction.ASCENDING,
                                                alteredDegrees=alteredDegrees)

        # see if we can get from cache
        if self.deterministic:
            # environLocal.printDebug('using cached scale segment')
            ck = self._getCacheKey(nodeObj,
                                   pitchReference,
                                   minPitch,
                                   maxPitch,
                                   includeFirst=False)
            if ck in self._ascendingCache:
                return self._ascendingCache[ck]
        else:
            ck = None

        # if this network is octaveDuplicating, then we can shift
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
            if n.id == Terminus.HIGH:
                if maxPitch is None:  # if not defined, stop at terminus high
                    break
                n = self.terminusLowNodes[0]
            # this returns a list of possible edges and nodes
            nextBundle = self.getNext(n, Direction.ASCENDING)
            # environLocal.printDebug(['realizeAscending()', 'n', n, 'nextBundle', nextBundle])

            # if we cannot continue to ascend, then we must break
            if nextBundle is None:
                break
            postEdge, postNode = nextBundle
            # make probabilistic selection here if more than one
            if len(postEdge) > 1:
                # do a weighted selection based on node weights,
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
                                                 direction=Direction.ASCENDING)

        if attempts >= maxAttempts:
            raise IntervalNetworkException(
                'Cannot realize these pitches; is your scale '
                + "well-formed? (especially check if you're giving notes without octaves)")

        # store in cache
        if self.deterministic and ck is not None:
            self._ascendingCache[ck] = post, postNodeId

        # environLocal.printDebug(['realizeAscending()', 'post', post, 'postNodeId', postNodeId])

        return post, postNodeId

    def realizeDescending(
        self,
        pitchReference: pitch.Pitch | str,
        nodeId: Node | int | Terminus | None = None,
        minPitch: pitch.Pitch | str | None = None,
        maxPitch: pitch.Pitch | str | None = None,
        *,
        alteredDegrees=None,
        includeFirst=False,
        fillMinMaxIfNone=False,
        reverse=True
    ):
        # noinspection PyShadowingNames
        '''
        Given a reference pitch, realize downward to a minimum.

        If no minimum is given, the terminus is used.

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
        [Terminus.LOW, 0, 1, 2, 3, 4, 5]
        >>> (pitches, nodeKeys) = net.realizeDescending('c3', 1, 'c2', includeFirst=True)
        >>> [str(p) for p in pitches]
        ['C2', 'D2', 'E2', 'F2', 'G2', 'A2', 'B2', 'C3']
        >>> nodeKeys
        [Terminus.LOW, 0, 1, 2, 3, 4, 5, Terminus.LOW]

        >>> (pitches, nodeKeys) = net.realizeDescending('a6', scale.Terminus.HIGH)
        >>> [str(p) for p in pitches]
        ['A5', 'B5', 'C#6', 'D6', 'E6', 'F#6', 'G#6']
        >>> nodeKeys
        [Terminus.LOW, 0, 1, 2, 3, 4, 5]

        >>> (pitches, nodeKeys) = net.realizeDescending('a6', scale.Terminus.HIGH,
        ...                                             includeFirst=True)
        >>> [str(p) for p in pitches]
        ['A5', 'B5', 'C#6', 'D6', 'E6', 'F#6', 'G#6', 'A6']
        >>> nodeKeys
        [Terminus.LOW, 0, 1, 2, 3, 4, 5, Terminus.HIGH]

        >>> net = scale.intervalNetwork.IntervalNetwork(octaveDuplicating=True)
        >>> net.fillBiDirectedEdges(edgeList)
        >>> (pitches, nodeKeys) = net.realizeDescending('c2', 1, 'c0', 'c1')
        >>> [str(p) for p in pitches]
        ['C0', 'D0', 'E0', 'F0', 'G0', 'A0', 'B0']
        >>> nodeKeys
        [Terminus.LOW, 0, 1, 2, 3, 4, 5]
        '''
        ck = None

        if isinstance(pitchReference, str):
            pitchRef = pitch.Pitch(pitchReference)
        else:
            pitchRef = copy.deepcopy(pitchReference)

        # must set an octave for pitch reference, even if not given
        if pitchRef.octave is None:
            pitchRef.octave = 4

        # get first node if no node is provided
        if isinstance(nodeId, Node):
            nodeObj = nodeId
        elif nodeId is None:  # assume low terminus by default
            # this is useful for appending a descending segment with an
            # ascending segment
            nodeObj = self.terminusLowNodes[0]
        else:
            nodeObj = self.nodeNameToNodes(nodeId)[0]

        minPitchObj: pitch.Pitch | None
        if isinstance(minPitch, str):
            minPitchObj = pitch.Pitch(minPitch)
        else:
            minPitchObj = minPitch

        maxPitchObj: pitch.Pitch | None
        if isinstance(maxPitch, str):
            maxPitchObj = pitch.Pitch(maxPitch)
        else:
            maxPitchObj = maxPitch

        if fillMinMaxIfNone and minPitchObj is None and maxPitchObj is None:
            # environLocal.printDebug(['realizeDescending()', 'fillMinMaxIfNone'])
            minPitchObj, maxPitchObj = self.realizeMinMax(pitchRef,
                                                          nodeObj,
                                                          alteredDegrees=alteredDegrees)

        # when the pitch reference is altered, we need to get the
        # unaltered version of this pitch.
        pitchRef = self.getUnalteredPitch(pitchRef,
                                          nodeObj,
                                          direction=Direction.DESCENDING,
                                          alteredDegrees=alteredDegrees)

        # see if we can get from cache
        if self.deterministic:
            ck = self._getCacheKey(nodeObj,
                                   pitchRef,
                                   minPitch=minPitchObj,
                                   maxPitch=maxPitchObj,
                                   includeFirst=includeFirst,
                                   reverse=reverse,
                                   )
            if ck in self._descendingCache:
                return self._descendingCache[ck]

        # if this network is octaveDuplicating, then we can shift
        # reference down octaves to just above minPitch
        if self.octaveDuplicating and maxPitchObj is not None:
            pitchRef.transposeAboveTarget(maxPitchObj, minimize=True, inPlace=True)

        n = nodeObj
        p = pitchRef
        pCollect = p  # usually p, unless the tone has been altered
        pre = []
        preNodeId = []  # store node ids as well

        isFirst = True
        while True:
            appendPitch = False
            if (minPitchObj is not None
                    and _gte(p.ps, minPitchObj.ps)
                    and maxPitchObj is not None
                    and _lte(p.ps, maxPitchObj.ps)):
                appendPitch = True
            elif (minPitchObj is not None
                  and _gte(p.ps, minPitchObj.ps)
                  and maxPitchObj is None):
                appendPitch = True
            elif (maxPitchObj is not None
                  and _lte(p.ps, maxPitchObj.ps)
                  and minPitchObj is None):
                appendPitch = True
            elif minPitchObj is None and maxPitchObj is None:
                appendPitch = True

            # environLocal.printDebug(['realizeDescending', 'appending pitch', pCollect,
            #        'includeFirst', includeFirst])

            if (appendPitch and not isFirst) or (appendPitch and isFirst and includeFirst):
                pre.append(pCollect)
                preNodeId.append(n.id)

            isFirst = False

            if minPitchObj is not None and p.ps <= minPitchObj.ps:
                break
            if n.id == Terminus.LOW:
                if minPitchObj is None:  # if not defined, stop at terminus high
                    break
                # get high and continue
                n = self.terminusHighNodes[0]
            if n.id == Terminus.LOW:
                if minPitchObj is None:  # if not defined, stop at terminus high
                    break

            nextBundle = self.getNext(n, Direction.DESCENDING)
            # environLocal.printDebug(['realizeDescending()', 'n', n, 'nextBundle', nextBundle])

            if nextBundle is None:
                break
            postEdge, postNode = nextBundle
            if len(postEdge) > 1:
                # do a weighted selection based on node weights,
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
                                                direction=Direction.DESCENDING)

        if reverse:
            pre.reverse()
            preNodeId.reverse()

        # store in cache
        if self.deterministic and ck is not None:
            self._descendingCache[ck] = pre, preNodeId

        return pre, preNodeId

    def realize(self,
                pitchReference: str | pitch.Pitch,
                nodeId: Node | int | Terminus | None = None,
                minPitch: pitch.Pitch | str | None = None,
                maxPitch: pitch.Pitch | str | None = None,
                direction: Direction = Direction.ASCENDING,
                alteredDegrees=None,
                reverse=False):
        # noinspection PyShadowingNames
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
        [Terminus.LOW, 0, 1, 2, 3, 4, 5, Terminus.HIGH]

        >>> alteredDegrees = {7: {'direction': scale.Direction.BI,
        ...                       'interval': interval.Interval('-a1')}}
        >>> (pitches, nodeKeys) = net.realize('c2', 1, 'c2', 'c4', alteredDegrees=alteredDegrees)
        >>> [str(p) for p in pitches]
        ['C2', 'D2', 'E2', 'F2', 'G2', 'A2', 'B-2', 'C3',
         'D3', 'E3', 'F3', 'G3', 'A3', 'B-3', 'C4']
        >>> nodeKeys
        [Terminus.LOW, 0, 1, 2, 3, 4, 5, Terminus.HIGH, 0, 1, 2, 3, 4, 5, Terminus.HIGH]
        '''
        # get first node if no node is provided
        # environLocal.printDebug(['got pre pitch:', pre])
        # environLocal.printDebug(['got pre node:', preNodeId])
        if pitchReference is None:
            raise IntervalNetworkException('pitchReference cannot be None')

        if isinstance(pitchReference, str):
            pitchRef = pitch.Pitch(pitchReference)
        else:  # make a copy b/c may manipulate
            pitchRef = copy.deepcopy(pitchReference)

        # must set an octave for pitch reference, even if not given
        if pitchRef.octave is None:
            pitchRef.octave = pitchRef.implicitOctave

        minPitchObj: pitch.Pitch | None
        if isinstance(minPitch, str):
            minPitchObj = pitch.Pitch(minPitch)
        else:
            minPitchObj = minPitch

        maxPitchObj: pitch.Pitch | None
        if isinstance(maxPitch, str):
            maxPitchObj = pitch.Pitch(maxPitch)
        else:
            maxPitchObj = maxPitch

        directedRealization = False
        if self.octaveDuplicating:
            directedRealization = True

        # environLocal.printDebug(['directedRealization', directedRealization,
        #            'direction', direction, 'octaveDuplicating', self.octaveDuplicating])

        # realize by calling ascending/descending
        if directedRealization:
            # assumes we have min and max pitch as not none
            if direction == Direction.ASCENDING:
                # move pitch reference to below minimum
                if self.octaveDuplicating and minPitchObj is not None:
                    pitchRef.transposeBelowTarget(minPitchObj, inPlace=True)

                mergedPitches, mergedNodes = self.realizeAscending(
                    pitchReference=pitchRef,
                    nodeId=nodeId,
                    minPitch=minPitchObj,
                    maxPitch=maxPitchObj,
                    alteredDegrees=alteredDegrees,
                    fillMinMaxIfNone=True)

            elif direction == Direction.DESCENDING:
                # move pitch reference to above minimum
                if self.octaveDuplicating and maxPitchObj is not None:
                    pitchRef.transposeAboveTarget(maxPitchObj, inPlace=True)

                # fillMinMaxIfNone will result in a complete scale
                # being returned if no min and max are given (otherwise
                # we would just get the reference pitch).

                mergedPitches, mergedNodes = self.realizeDescending(
                    pitchReference=pitchRef,
                    nodeId=nodeId,
                    minPitch=minPitchObj,
                    maxPitch=maxPitchObj,
                    alteredDegrees=alteredDegrees,
                    includeFirst=True,
                    fillMinMaxIfNone=True)

            elif direction == Direction.BI:
                # this is a union of both ascending and descending
                pitchReferenceA = copy.deepcopy(pitchRef)
                pitchReferenceB = copy.deepcopy(pitchRef)

                if self.octaveDuplicating and minPitchObj is not None:
                    pitchReferenceA.transposeBelowTarget(minPitchObj, inPlace=True)

                # pitchReferenceA.transposeBelowTarget(minPitchObj, inPlace=True)

                post, postNodeId = self.realizeAscending(pitchReference=pitchReferenceA,
                                                         nodeId=nodeId,
                                                         minPitch=minPitchObj,
                                                         maxPitch=maxPitchObj,
                                                         alteredDegrees=alteredDegrees)

                if self.octaveDuplicating and maxPitchObj is not None:
                    pitchReferenceB.transposeAboveTarget(maxPitchObj, inPlace=True)

                # pitchReferenceB.transposeAboveTarget(maxPitchObj, inPlace=True)

                pre, preNodeId = self.realizeDescending(pitchReference=pitchReferenceB,
                                                        nodeId=nodeId,
                                                        minPitch=minPitchObj,
                                                        maxPitch=maxPitchObj,
                                                        alteredDegrees=alteredDegrees,
                                                        includeFirst=True)

                # We need to create union of both lists, but keep order,
                # and also keep the nodeId list in order

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
                    f'cannot match direction specification: {direction!r}')

        else:  # non directed realization
            # TODO: if not octave repeating, and ascending or descending,
            # have to travel to a pitch
            # at the proper extreme, and then go the opposite way
            # presently, this will realize ascending from reference,
            # then descending from reference
            post, postNodeId = self.realizeAscending(pitchReference=pitchRef,
                                                     nodeId=nodeId,
                                                     minPitch=minPitchObj,
                                                     maxPitch=maxPitchObj,
                                                     alteredDegrees=alteredDegrees)
            pre, preNodeId = self.realizeDescending(pitchReference=pitchRef,
                                                    nodeId=nodeId,
                                                    minPitch=minPitchObj,
                                                    maxPitch=maxPitchObj,
                                                    alteredDegrees=alteredDegrees,
                                                    includeFirst=False)

            # environLocal.printDebug(['realize()', 'pre', pre, preNodeId])
            mergedPitches, mergedNodes = pre + post, preNodeId + postNodeId

        if reverse:
            # Make new objects, because this value might be cached in intervalNetwork's
            # _descendingCache, and mutating it would be dangerous.
            mergedPitches = list(reversed(mergedPitches))
            mergedNodes = list(reversed(mergedNodes))

        return mergedPitches, mergedNodes

    def realizePitch(
        self,
        pitchReference: str | pitch.Pitch,
        nodeId: Node | int | Terminus | None = None,
        minPitch: pitch.Pitch | str | None = None,
        maxPitch: pitch.Pitch | str | None = None,
        direction: Direction = Direction.ASCENDING,
        alteredDegrees=None,
        reverse=False,
    ) -> list[pitch.Pitch]:
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

    def realizeIntervals(
        self,
        nodeId: Node | int | Terminus | None = None,
        minPitch: pitch.Pitch | str | None = None,
        maxPitch: pitch.Pitch | str | None = None,
        direction: Direction = Direction.ASCENDING,
        alteredDegrees=None,
        reverse=False,
    ) -> list[interval.Interval]:
        '''
        Realize the sequence of intervals between the specified pitches, or the termini.

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

    def realizeTermini(
        self,
        pitchReference: str | pitch.Pitch,
        nodeId: Node | int | Terminus | None = None,
        alteredDegrees=None,
    ) -> tuple[pitch.Pitch, pitch.Pitch]:
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

        post = self.realizeAscending(
            pitchReference=pitchReference,
            nodeId=nodeId,
            alteredDegrees=alteredDegrees,
            fillMinMaxIfNone=False)[0]  # avoid recursion by setting false
        pre = self.realizeDescending(
            pitchReference=pitchReference,
            nodeId=nodeId,
            alteredDegrees=alteredDegrees,
            includeFirst=False,
            fillMinMaxIfNone=False)[0]  # avoid recursion by setting false

        # environLocal.printDebug(['realize()', 'pre', pre, preNodeId])
        mergedPitches = pre + post

        # environLocal.printDebug(['realizeTermini()', 'pList', mergedPitches,
        #            'pitchReference', pitchReference, 'nodeId', nodeId])
        return mergedPitches[0], mergedPitches[-1]

    def realizeMinMax(
        self,
        pitchReference: str | pitch.Pitch,
        nodeId: Node | int | Terminus | None = None,
        alteredDegrees=None,
    ) -> tuple[pitch.Pitch, pitch.Pitch]:
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
            if i == 0 and nId in (Terminus.LOW, Terminus.HIGH):
                continue
            # turn off collection after finding next terminus
            elif nId in (Terminus.LOW, Terminus.HIGH) and collect is True:
                postPairs.append((p, nId))
                break
            elif nId in (Terminus.LOW, Terminus.HIGH) and collect is False:
                collect = True
            if collect:
                postPairs.append((p, nId))
        # environLocal.printDebug(['realizeMinMax()', 'postPairs', postPairs])

        prePairs = []
        collect = False
        for i, nId in enumerate(preNodeId):
            p = pre[i]
            # if first id is a terminus, skip
            if i == 0 and nId in (Terminus.LOW, Terminus.HIGH):
                continue
            # turn off collection after finding next terminus
            elif nId in (Terminus.LOW, Terminus.HIGH) and collect is True:
                prePairs.append((p, nId))
                break
            elif nId in (Terminus.LOW, Terminus.HIGH) and collect is False:
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

        # may not be first or last to get min/max
        return minPitch, maxPitch

    def realizePitchByDegree(
        self,
        pitchReference: pitch.Pitch | str,
        nodeId: Node | int | Terminus | None = None,
        nodeDegreeTargets=(1,),
        minPitch: pitch.Pitch | str | None = None,
        maxPitch: pitch.Pitch | str | None = None,
        direction: Direction = Direction.ASCENDING,
        alteredDegrees=None,
    ):
        # noinspection PyShadowingNames
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
        # noinspection PyPackageRequirements
        import networkx  # type: ignore  # pylint: disable=import-error
        weight = 1
        style = 'solid'

        def sortTerminusLowThenIntThenTerminusHigh(a):
            '''
            return a two-tuple where the first element is -1 if 'Terminus.LOW',
            0 if an int, and 1 if 'Terminus.HIGH' or another string, and
            the second element is the value itself.
            '''
            sortFirst = 0
            if isinstance(a, str):
                if a.upper() == 'Terminus.LOW':
                    sortFirst = -1
                else:
                    sortFirst = 1
            return (sortFirst, a)

        # g = networkx.DiGraph()
        g = networkx.MultiDiGraph()

        for unused_eId, e in self.edges.items():
            if e.direction == Direction.ASCENDING:
                weight = 0.9  # these values are just for display
                style = 'solid'
            elif e.direction == Direction.DESCENDING:
                weight = 0.6
                style = 'solid'
            elif e.direction == Direction.BI:
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
            g.node[nId]['pos'] = (degreeCount[n.degree], n.degree)  # pylint: disable=no-member
            degreeCount[n.degree] += 1
        environLocal.printDebug(['got degree count', degreeCount])
        return g

    def plot(self,
             **keywords):
        '''
        Given a method and keyword configuration arguments, create and display a plot.

        Requires `networkx` to be installed.

        * Changed in v8: other parameters were unused and removed.
        '''
        #
        # >>> s = corpus.parse('bach/bwv324.xml') #_DOCS_HIDE
        # >>> s.plot('pianoroll', doneAction=None) #_DOCS_HIDE
        # >>> #_DOCS_SHOW s = corpus.parse('bach/bwv57.8')
        # >>> #_DOCS_SHOW s.plot('pianoroll')
        #
        # .. image:: images/PlotHorizontalBarPitchSpaceOffset.*
        #     :width: 600
        # import is here to avoid import of matplotlib problems
        from music21 import graph
        # first ordered arg can be method type
        g = graph.primitives.GraphNetworkxGraph(
            networkxGraph=self.getNetworkxGraph())
        g.process()

    def getRelativeNodeId(
        self,
        pitchReference: pitch.Pitch | str,
        nodeId: Node | int | Terminus | None,
        pitchTarget: pitch.Pitch | note.Note | str,
        *,
        comparisonAttribute: str = 'ps',
        direction: Direction = Direction.ASCENDING,
        alteredDegrees=None
    ):
        '''
        Given a reference pitch assigned to node id, determine the
        relative node id of pitchTarget, even if displaced over multiple octaves

        The `nodeId` parameter may be
        a :class:`~music21.scale.intervalNetwork.Node` object, a node degree,
        a terminus string, or a None (indicating Terminus.LOW).

        Returns None if no match.

        If `getNeighbor` is True, or direction, the nearest node will be returned.

        If more than one node defines the same pitch, Node weights are used
        to select a single node.


        >>> edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        >>> net = scale.intervalNetwork.IntervalNetwork(edgeList)
        >>> net.getRelativeNodeId('a', 1, 'a4')
        Terminus.LOW
        >>> net.getRelativeNodeId('a', 1, 'b4')
        0
        >>> net.getRelativeNodeId('a', 1, 'c#4')
        1
        >>> net.getRelativeNodeId('a', 1, 'c4', comparisonAttribute='step')
        1
        >>> net.getRelativeNodeId('a', 1, 'c', comparisonAttribute='step')
        1
        >>> net.getRelativeNodeId('a', 1, 'b-4') is None
        True
        '''
        # TODO: this always takes the first: need to add weighted selection

        nodeObj: Node
        if nodeId is None:  # assume first
            nodeObj = self.terminusLowNodes[0]
        else:
            nodeObj = self.nodeNameToNodes(nodeId)[0]

        # environLocal.printDebug(['getRelativeNodeId', 'result of nodeNameToNodes',
        #   self.nodeNameToNodes(nodeName)])

        if isinstance(pitchTarget, str):
            pitchTargetObj = pitch.Pitch(pitchTarget)
        elif isinstance(pitchTarget, note.Note):
            pitchTargetObj = pitchTarget.pitch
        else:
            pitchTargetObj = pitchTarget

        saveOctave = pitchTargetObj.octave
        if saveOctave is None:
            pitchTargetObj.octave = pitchTargetObj.implicitOctave

        # try an octave spread first
        # if a scale degree is larger than an octave this will fail
        minPitch = pitchTargetObj.transpose(-12, inPlace=False)
        maxPitch = pitchTargetObj.transpose(12, inPlace=False)

        realizedPitch, realizedNode = self.realize(pitchReference,
                                                   nodeObj,
                                                   minPitch=minPitch,
                                                   maxPitch=maxPitch,
                                                   direction=direction,
                                                   alteredDegrees=alteredDegrees)

        # environLocal.printDebug(['getRelativeNodeId()', 'nodeObj', nodeObj,
        #    'realizedPitch', realizedPitch, 'realizedNode', realizedNode])

        post = []  # collect more than one
        for i in range(len(realizedPitch)):
            # environLocal.printDebug(['getRelativeNodeId', 'comparing',
            #   realizedPitch[i], realizedNode[i]])

            # comparison of attributes, not object
            match = False
            if (getattr(pitchTargetObj, comparisonAttribute)
                    == getattr(realizedPitch[i], comparisonAttribute)):
                match = True
            if match:
                if realizedNode[i] not in post:  # may be more than one match
                    post.append(realizedNode[i])

        if saveOctave is None:
            pitchTargetObj.octave = None

        if not post:
            return None
        elif len(post) == 1:
            return post[0]
        else:  # do a weighted selection
            # environLocal.printDebug(['getRelativeNodeId()', 'got multiple matches', post])
            # use node keys stored in post, get node, and collect weights
            return common.weightedSelection(post,
                                            [self.nodes[x].weight for x in post])

    def getNeighborNodeIds(
        self,
        pitchReference: pitch.Pitch | str,
        nodeName: Node | int | Terminus | None,
        pitchTarget: pitch.Pitch | str,
        direction: Direction = Direction.ASCENDING,
        alteredDegrees=None,
    ):
        '''
        Given a reference pitch assigned to a node id, determine the node ids
        that neighbor this pitch.

        Returns None if an exact match.

        >>> edgeList = ['M2', 'M2', 'm2', 'M2', 'M2', 'M2', 'm2']
        >>> net = scale.intervalNetwork.IntervalNetwork(edgeList)
        >>> net.getNeighborNodeIds('c4', 1, 'b-')
        (4, 5)
        >>> net.getNeighborNodeIds('c4', 1, 'b')
        (5, Terminus.HIGH)
        '''
        # TODO: this takes the first, need to add probabilistic selection
        if nodeName is None:  # assume first
            nodeId = self.terminusLowNodes[0]
        else:
            nodeId = self.nodeNameToNodes(nodeName)[0]

        if isinstance(pitchTarget, str):
            pitchTargetObj = pitch.Pitch(pitchTarget)
        else:
            pitchTargetObj = pitchTarget

        savedOctave = pitchTargetObj.octave
        if savedOctave is None:
            # don't alter permanently, in case a Pitch object was passed in.
            pitchTargetObj.octave = pitchTargetObj.implicitOctave
        # try an octave spread first
        # if a scale degree is larger than an octave this will fail
        minPitch = pitchTargetObj.transpose(-12, inPlace=False)
        maxPitch = pitchTargetObj.transpose(12, inPlace=False)

        realizedPitch, realizedNode = self.realize(pitchReference,
                                                   nodeId,
                                                   minPitch=minPitch,
                                                   maxPitch=maxPitch,
                                                   direction=direction,
                                                   alteredDegrees=alteredDegrees)

        lowNeighbor = None
        highNeighbor = None
        for i in range(len(realizedPitch)):
            if pitchTargetObj.ps < realizedPitch[i].ps:
                highNeighbor = realizedNode[i]
                # low neighbor may be a previously-encountered pitch
                return lowNeighbor, highNeighbor
            lowNeighbor = realizedNode[i]

        if savedOctave is None:
            pitchTargetObj.octave = savedOctave
        return None

    def getRelativeNodeDegree(
        self,
        pitchReference: pitch.Pitch | str,
        nodeId,
        pitchTarget: pitch.Pitch | str,
        comparisonAttribute='ps',
        direction: Direction = Direction.ASCENDING,
        alteredDegrees=None,
    ):
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
            nodeId=nodeId,
            pitchTarget=pitchTarget,
            comparisonAttribute=comparisonAttribute,
            alteredDegrees=alteredDegrees,
            direction=direction)

        if nId is None:
            return None
        else:
            return self.nodeIdToDegree(nId)

    def getPitchFromNodeDegree(
        self,
        pitchReference: pitch.Pitch | str,
        nodeName: Node | int | Terminus | None,
        nodeDegreeTarget,
        direction: Direction = Direction.ASCENDING,
        minPitch=None,
        maxPitch=None,
        alteredDegrees=None,
        equateTermini=True,
    ):
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
        >>> net.getPitchFromNodeDegree('c', 1, 6, scale.Direction.ASCENDING)
        <music21.pitch.Pitch A4>
        >>> net.getPitchFromNodeDegree('c', 1, 6, scale.Direction.DESCENDING)
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
        elif [n.id for n in nodeTargetIdList] == [Terminus.LOW, Terminus.HIGH]:
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

            # get the pitch when we have a node id to match
            for i, nId in enumerate(realizedNode):
                # environLocal.printDebug(['comparing', nId, 'nodeTargetId', nodeTargetId])

                if nId == nodeTargetId.id:
                    return realizedPitch[i]
                # NOTE: this condition may be too generous, and was added to solve
                # a non-tracked problem.
                # only match this generously if we are equating termini
                if equateTermini:
                    if ((nId in (Terminus.HIGH, Terminus.LOW))
                         and (nodeTargetId.id in (Terminus.HIGH, Terminus.LOW))):
                        return realizedPitch[i]

            # environLocal.printDebug(['getPitchFromNodeDegree() on trial', trial, ',
            #    failed to find node', nodeTargetId])

    @staticmethod
    def filterPitchList(
        pitchTarget: t.Union[list[str], list[pitch.Pitch], str, pitch.Pitch]
    ) -> tuple[list[pitch.Pitch], pitch.Pitch, pitch.Pitch]:
        '''
        Given a list or one pitch, check if all are pitch objects; convert if necessary.
        Return a 3-tuple: a list of all pitches, the min value and the max value.

        >>> Net = scale.intervalNetwork.IntervalNetwork
        >>> Net.filterPitchList(['c#4', 'f5', 'd3'])
        ([<music21.pitch.Pitch C#4>, <music21.pitch.Pitch F5>, <music21.pitch.Pitch D3>],
         <music21.pitch.Pitch D3>,
         <music21.pitch.Pitch F5>)

        A single string or pitch can be given.

        >>> Net.filterPitchList('c#')
        ([<music21.pitch.Pitch C#>],
         <music21.pitch.Pitch C#>,
         <music21.pitch.Pitch C#>)

        Empty lists raise value errors:

        >>> Net.filterPitchList([])
        Traceback (most recent call last):
        ValueError: There must be at least one pitch given.

        * Changed in v8: staticmethod.  Raise value error on empty
        '''
        pitchList: list[pitch.Pitch]
        if not isinstance(pitchTarget, (list, tuple)):
            pitchObj: pitch.Pitch
            if isinstance(pitchTarget, str):
                pitchObj = pitch.Pitch(pitchTarget)
            else:
                pitchObj = pitchTarget
            pitchList = [pitchObj]
        else:
            # convert a list of string into pitch objects
            pitchList = []
            for p in pitchTarget:
                if isinstance(p, str):
                    pitchList.append(pitch.Pitch(p))
                else:
                    pitchList.append(p)

        if not pitchList:
            raise ValueError('There must be at least one pitch given.')

        # automatically derive a min and max from the supplied pitch
        sortList = [(pitchList[i].ps, i) for i in range(len(pitchList))]
        sortList.sort()
        minPitch = pitchList[sortList[0][1]]  # first index
        maxPitch = pitchList[sortList[-1][1]]  # last index

        return pitchList, minPitch, maxPitch

    def match(self,
              pitchReference: pitch.Pitch | str,
              nodeId,
              pitchTarget,
              comparisonAttribute='pitchClass',
              alteredDegrees=None):
        # noinspection PyShadowingNames
        '''
        Given one or more pitches in `pitchTarget`, return a
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
            nodeId = self.terminusLowNodes[0]
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
                    pitchReference: pitch.Pitch | str,
                    nodeId,
                    pitchTarget,
                    comparisonAttribute='pitchClass',
                    minPitch=None,
                    maxPitch=None,
                    direction: Direction = Direction.ASCENDING,
                    alteredDegrees=None):
        # noinspection PyShadowingNames
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
            nodeId = self.terminusLowNodes[0]
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


    _SCALE_STARTS: tuple[str, ...] = (
        'C', 'C#', 'D-',
        'D', 'D#', 'E-',
        'E', 'F',
        'F#', 'G',
        'G#', 'A', 'B-',
        'B', 'C-',
    )

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

        # pitch strings in _SCALE_STARTS are converted to actual pitches in .realize,
        # and then manipulated.  If they were Pitch objects already, they would get
        # deepcopied which is very slow.
        for p in self._SCALE_STARTS:
            # Realize scales from each pitch, and then compare to pitchTarget.
            # PitchTarget may be a list of pitches
            matched, unused_noMatch = self.match(
                p,
                nodeId,
                pitchTarget,
                comparisonAttribute=comparisonAttribute,
                alteredDegrees=alteredDegrees)
            sortList.append((len(matched), pitch.Pitch(p)))

        sortList.sort()
        sortList.reverse()  # want most matches first
        if resultsReturned is not None:
            return sortList[:resultsReturned]
        else:
            return sortList

    def transposePitchAndApplySimplification(
        self,
        intervalObj: interval.Interval,
        pitchObj: pitch.Pitch
    ) -> pitch.Pitch:
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
                        f'unknown pitchSimplification type {pitchSimplification},'
                        + ' allowable values are "maxAccidental" (default), "simplifyEnharmonic", '
                        + '"mostCommon", or None (or "none")')
        return pPost


class BoundIntervalNetwork(IntervalNetwork):
    '''
    This class is kept only because of the ICMC Paper.  Just use IntervalNetwork instead.
    '''
    pass


# ------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [IntervalNetwork, Node, Edge]

if __name__ == '__main__':
    import music21
    music21.mainTest()

