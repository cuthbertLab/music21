# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         alpha/analysis/aligner.py
# Purpose:      A general aligner that tries its best to align two streams
#
# Authors:      Emily Zhang
#
# Copyright:    Copyright © 2015 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
from collections import Counter
import enum
import operator
import unittest

from music21 import base
from music21 import exceptions21
from music21 import metadata
from music21.alpha.analysis import hasher


class AlignerException(exceptions21.Music21Exception):
    pass


class AlignmentTracebackException(AlignerException):
    pass


class ChangeOps(enum.IntEnum):
    '''
    >>> ins = alpha.analysis.aligner.ChangeOps.Insertion
    >>> ins.color
    'green'

    >>> deletion = alpha.analysis.aligner.ChangeOps.Deletion
    >>> deletion.color
    'red'

    >>> subs = alpha.analysis.aligner.ChangeOps.Substitution
    >>> subs.color
    'purple'

    >>> noChange = alpha.analysis.aligner.ChangeOps.NoChange
    >>> noChange.color is None
    True
    '''
    Insertion = 0
    Deletion = 1
    Substitution = 2
    NoChange = 3

    @property
    def color(self):
        colorDict = {0: 'green', 1: 'red', 2: 'purple', 3: None}
        return colorDict[self.value]


class StreamAligner:
    '''
    Stream Aligner is a dumb object that takes in two streams and forces them to align
    without any thought to any external variables

    These terms are associated with the Target stream are:
    - n, the number of rows in the distance matrix, the left-most column of the matrix
    - i, the index into rows in the distance matrix
    - the first element of tuple

    These terms are associated with the Source stream are:
    - m, the number of columns in the distance matrix, the top-most row of the matrix
    - j, the index into columns in the distance matrix
    - the second element of tuple
    '''

    def __init__(self, targetStream=None, sourceStream=None, hasher_func=None, preHashed=False):
        self.targetStream = targetStream
        self.sourceStream = sourceStream

        self.distanceMatrix = None

        if hasher_func is None:
            hasher_func = self.getDefaultHasher()

        self.hasher = hasher_func
        self.preHashed = preHashed

        self.changes = []
        self.similarityScore = 0

        # self.n and self.m will be the size of the distance matrix, set later
        self.n = 0
        self.m = 0

        self.hashedTargetStream = None
        self.hashedSourceStream = None
        self.changesCount = None

    def getDefaultHasher(self):
        '''
        returns a default hasher.Hasher object
        that does not hashOffset or include the reference.

        called by __init__ if no hasher is passed in.

        >>> sa = alpha.analysis.aligner.StreamAligner()
        >>> h = sa.getDefaultHasher()
        >>> h
        <music21.alpha.analysis.hasher.Hasher object at 0x1068cf6a0>
        >>> h.hashOffset
        False
        >>> h.includeReference
        True
        '''
        h = hasher.Hasher()
        h.hashOffset = False
        h.includeReference = True
        return h

    def align(self):
        self.makeHashedStreams()
        self.setupDistanceMatrix()
        self.populateDistanceMatrix()
        self.calculateChangesList()

    def makeHashedStreams(self):
        '''
        Hashes streams if not pre-hashed

        >>> tStream = stream.Stream()
        >>> sStream = stream.Stream()

        >>> note1 = note.Note('C4')
        >>> note2 = note.Note('D4')
        >>> note3 = note.Note('C4')
        >>> note4 = note.Note('E4')

        >>> tStream.append([note1, note2])
        >>> sStream.append([note3, note4])
        >>> sa1 = alpha.analysis.aligner.StreamAligner(tStream, sStream)

        >>> h = alpha.analysis.hasher.Hasher()
        >>> h.includeReference = True

        >>> toBeHashedTarStream = stream.Stream()
        >>> toBeHashedSouStream = stream.Stream()

        >>> note5 = note.Note('A4')
        >>> note6 = note.Note('B4')
        >>> note7 = note.Note('A4')
        >>> note8 = note.Note('G4')

        >>> toBeHashedTarStream.append([note5, note6])
        >>> toBeHashedSouStream.append([note7, note8])
        >>> hashedTarStr = h.hashStream(toBeHashedTarStream)
        >>> hashedSouStr = h.hashStream(toBeHashedSouStream)
        >>> sa2 = alpha.analysis.aligner.StreamAligner(
        ...             hashedTarStr, hashedSouStr, preHashed=True)

        >>> sa2.makeHashedStreams()
        >>> sa1.makeHashedStreams()

        >>> sa1.hashedTargetStream
        [NoteHashWithReference(Pitch=60, Duration=1.0),
         NoteHashWithReference(Pitch=62, Duration=1.0)]
        >>> sa1.hashedSourceStream
        [NoteHashWithReference(Pitch=60, Duration=1.0),
         NoteHashWithReference(Pitch=64, Duration=1.0)]

        >>> sa2.hashedTargetStream
        [NoteHashWithReference(Pitch=69, Duration=1.0, Offset=0.0),
         NoteHashWithReference(Pitch=71, Duration=1.0, Offset=1.0)]
        >>> sa2.hashedSourceStream
        [NoteHashWithReference(Pitch=69, Duration=1.0, Offset=0.0),
         NoteHashWithReference(Pitch=67, Duration=1.0, Offset=1.0)]

        '''
        if not self.preHashed:
            self.hashedTargetStream = self.hasher.hashStream(self.targetStream)
            self.hashedSourceStream = self.hasher.hashStream(self.sourceStream)

        else:
            self.hashedTargetStream = self.targetStream
            self.hashedSourceStream = self.sourceStream

    def setupDistanceMatrix(self):
        '''
        Creates a distance matrix of the right size after hashing

        >>> note1 = note.Note('C4')
        >>> note2 = note.Note('D4')
        >>> note3 = note.Note('C4')
        >>> note4 = note.Note('E4')

        Test for streams of length 3 and 4

        >>> target0 = converter.parse('tinyNotation: C4 D C E')
        >>> source0 = converter.parse('tinyNotation: C4 D C')


        >>> sa0 = alpha.analysis.aligner.StreamAligner(target0, source0)
        >>> sa0.setupDistanceMatrix()
        >>> sa0.distanceMatrix.size
        20
        >>> sa0.distanceMatrix.shape
        (5, 4)

        Test for empty target stream

        >>> target1 = stream.Stream()
        >>> source1 = stream.Stream()
        >>> source1.append(note1)
        >>> sa1 = alpha.analysis.aligner.StreamAligner(target1, source1)
        >>> sa1.makeHashedStreams()
        >>> sa1.setupDistanceMatrix()
        Traceback (most recent call last):
        music21.alpha.analysis.aligner.AlignerException:
        Cannot perform alignment with empty target stream.

        Test for empty source stream

        >>> target2 = stream.Stream()
        >>> source2 = stream.Stream()
        >>> target2.append(note3)
        >>> sa2 = alpha.analysis.aligner.StreamAligner(target2, source2)
        >>> sa2.makeHashedStreams()
        >>> sa2.setupDistanceMatrix()
        Traceback (most recent call last):
        music21.alpha.analysis.aligner.AlignerException:
            Cannot perform alignment with empty source stream.

        '''
        if not self.hashedTargetStream:
            self.makeHashedStreams()
        # n and m will be the dimensions of the Distance Matrix we set up
        self.n = len(self.hashedTargetStream)
        self.m = len(self.hashedSourceStream)

        if self.n == 0:
            raise AlignerException('Cannot perform alignment with empty target stream.')

        if self.m == 0:
            raise AlignerException('Cannot perform alignment with empty source stream.')

        if 'numpy' in base._missingImport:
            raise AlignerException('Cannot run Aligner without numpy.')
        import numpy as np

        self.distanceMatrix = np.zeros((self.n + 1, self.m + 1), dtype=int)

    def populateDistanceMatrix(self):
        '''
        Sets up the distance matrix for back-tracing

        >>> note1 = note.Note('C#4')
        >>> note2 = note.Note('C4')

        Test 1: similar streams

        >>> targetA = stream.Stream()
        >>> sourceA = stream.Stream()
        >>> targetA.append([note1, note2])
        >>> sourceA.append([note1, note2])
        >>> saA = alpha.analysis.aligner.StreamAligner(targetA, sourceA)
        >>> saA.makeHashedStreams()
        >>> saA.setupDistanceMatrix()
        >>> saA.populateDistanceMatrix()
        >>> saA.distanceMatrix
        array([[0, 2, 4],
               [2, 0, 2],
               [4, 2, 0]])

        Second Test

        >>> targetB = stream.Stream()
        >>> sourceB = stream.Stream()
        >>> targetB.append([note1, note2])
        >>> sourceB.append(note1)
        >>> saB = alpha.analysis.aligner.StreamAligner(targetB, sourceB)
        >>> saB.makeHashedStreams()
        >>> saB.setupDistanceMatrix()
        >>> saB.populateDistanceMatrix()
        >>> saB.distanceMatrix
        array([[0, 2],
               [2, 0],
               [4, 2]])

        Third Test

        >>> note3 = note.Note('D5')
        >>> note3.quarterLength = 3
        >>> note4 = note.Note('E3')
        >>> targetC = stream.Stream()
        >>> sourceC = stream.Stream()
        >>> targetC.append([note1, note2, note4])
        >>> sourceC.append([note3, note1, note4])
        >>> saC = alpha.analysis.aligner.StreamAligner(targetC, sourceC)
        >>> saC.makeHashedStreams()
        >>> saC.setupDistanceMatrix()
        >>> saC.populateDistanceMatrix()
        >>> saC.distanceMatrix
        array([[0, 2, 4, 6],
           [2, 2, 2, 4],
           [4, 4, 3, 3],
           [6, 6, 5, 3]])

        '''

        # calculate insert and delete costs based on the first tuple in the Source S
        insertCost = self.insertCost(self.hashedSourceStream[0])
        deleteCost = self.deleteCost(self.hashedSourceStream[0])

        # setup all the entries in the first column, the target stream
        for i in range(1, self.n + 1):
            self.distanceMatrix[i][0] = self.distanceMatrix[i - 1][0] + insertCost

        # setup all the entries in the first row, the source stream
        for j in range(1, self.m + 1):
            self.distanceMatrix[0][j] = self.distanceMatrix[0][j - 1] + deleteCost

        # fill in rest of matrix
        for i in range(1, self.n + 1):
            for j in range(1, self.m + 1):
                substCost = self.substitutionCost(self.hashedTargetStream[i - 1],
                                                  self.hashedSourceStream[j - 1])

                previousValues = [self.distanceMatrix[i - 1][j] + insertCost,
                                   self.distanceMatrix[i][j - 1] + deleteCost,
                                   self.distanceMatrix[i - 1][j - 1] + substCost]

                self.distanceMatrix[i][j] = min(previousValues)

    def getPossibleMovesFromLocation(self, i, j):
        '''
        i and j are current row and column index in self.distanceMatrix
        returns all possible moves (0 up to 3)
        vertical, horizontal, diagonal costs of adjacent entries in self.distMatrix

        >>> target = stream.Stream()
        >>> source = stream.Stream()

        >>> note1 = note.Note('C4')
        >>> note2 = note.Note('D4')
        >>> note3 = note.Note('C4')
        >>> note4 = note.Note('E4')

        >>> target.append([note1, note2, note3, note4])
        >>> source.append([note1, note2, note3])
        >>> sa = alpha.analysis.aligner.StreamAligner(target, source)
        >>> sa.makeHashedStreams()
        >>> sa.setupDistanceMatrix()
        >>> for i in range(4+1):
        ...     for j in range(3+1):
        ...         sa.distanceMatrix[i][j] = i * j

        >>> sa.distanceMatrix
        array([[ 0,  0,  0,  0],
               [ 0,  1,  2,  3],
               [ 0,  2,  4,  6],
               [ 0,  3,  6,  9],
               [ 0,  4,  8, 12]])

        >>> sa.getPossibleMovesFromLocation(0, 0)
        [None, None, None]

        >>> sa.getPossibleMovesFromLocation(1, 1)
        [0, 0, 0]

        >>> sa.getPossibleMovesFromLocation(4, 3)
        [9, 8, 6]

        >>> sa.getPossibleMovesFromLocation(2, 2)
        [2, 2, 1]

        >>> sa.getPossibleMovesFromLocation(0, 2)
        [None, 0, None]

        >>> sa.getPossibleMovesFromLocation(3, 0)
        [0, None, None]

        '''
        verticalCost = self.distanceMatrix[i - 1][j] if i >= 1 else None
        horizontalCost = self.distanceMatrix[i][j - 1] if j >= 1 else None
        diagonalCost = self.distanceMatrix[i - 1][j - 1] if (i >= 1 and j >= 1) else None

        possibleMoves = [verticalCost, horizontalCost, diagonalCost]
        return possibleMoves

    def getOpFromLocation(self, i, j):
        '''
        Insert, Delete, Substitution, No Change = range(4)

        return the direction that traceback moves
        0: vertical movement, insertion
        1: horizontal movement, deletion
        2: diagonal movement, substitution
        3: diagonal movement, no change

        raises a ValueError if i == 0 and j == 0.
        >>> target = stream.Stream()
        >>> source = stream.Stream()

        >>> note1 = note.Note('C4')
        >>> note2 = note.Note('D4')
        >>> note3 = note.Note('C4')
        >>> note4 = note.Note('E4')

        >>> target.append([note1, note2, note3, note4])
        >>> source.append([note1, note2, note3])

        >>> sa = alpha.analysis.aligner.StreamAligner(target, source)
        >>> sa.makeHashedStreams()
        >>> sa.setupDistanceMatrix()
        >>> sa.populateDistanceMatrix()
        >>> sa.distanceMatrix
        array([[0, 2, 4, 6],
               [2, 0, 2, 4],
               [4, 2, 0, 2],
               [6, 4, 2, 0],
               [8, 6, 4, 2]])


        >>> sa.getOpFromLocation(4, 3)
        <ChangeOps.Insertion: 0>

        >>> sa.getOpFromLocation(2, 2)
        <ChangeOps.NoChange: 3>

        >>> sa.getOpFromLocation(0, 2)
        <ChangeOps.Deletion: 1>

        >>> sa.distanceMatrix[0][0] = 1
        >>> sa.distanceMatrix
        array([[1, 2, 4, 6],
               [2, 0, 2, 4],
               [4, 2, 0, 2],
               [6, 4, 2, 0],
               [8, 6, 4, 2]])

        >>> sa.getOpFromLocation(1, 1)
        <ChangeOps.Substitution: 2>

        >>> sa.getOpFromLocation(0, 0)
        Traceback (most recent call last):
        ValueError: No movement possible from the origin
        '''
        possibleMoves = self.getPossibleMovesFromLocation(i, j)

        if possibleMoves[0] is None:
            if possibleMoves[1] is None:
                raise ValueError('No movement possible from the origin')
            return ChangeOps.Deletion
        elif possibleMoves[1] is None:
            return ChangeOps.Insertion

        currentCost = self.distanceMatrix[i][j]
        minIndex, minNewCost = min(enumerate(possibleMoves), key=operator.itemgetter(1))
        if currentCost == minNewCost:
            return ChangeOps.NoChange
        else:
            return ChangeOps(minIndex)

    def insertCost(self, tup):
        '''
        Cost of inserting an extra hashed item.
        For now, it's just the size of the keys of the NoteHashWithReference

        >>> target = stream.Stream()
        >>> source = stream.Stream()

        >>> note1 = note.Note('C4')
        >>> note2 = note.Note('D4')
        >>> note3 = note.Note('C4')
        >>> note4 = note.Note('E4')

        >>> target.append([note1, note2, note3, note4])
        >>> source.append([note1, note2, note3])

        This is a StreamAligner with default hasher settings

        >>> sa0 = alpha.analysis.aligner.StreamAligner(target, source)
        >>> sa0.align()
        >>> tup0 = sa0.hashedTargetStream[0]
        >>> sa0.insertCost(tup0)
        2

        This is a StreamAligner with a modified hasher that doesn't hash pitch at all

        >>> sa1 = alpha.analysis.aligner.StreamAligner(target, source)
        >>> sa1.hasher.hashPitch = False
        >>> sa1.align()
        >>> tup1 = sa1.hashedTargetStream[0]
        >>> sa1.insertCost(tup1)
        1

        This is a StreamAligner with a modified hasher that hashes 3 additional properties

        >>> sa2 = alpha.analysis.aligner.StreamAligner(target, source)
        >>> sa2.hasher.hashOctave = True
        >>> sa2.hasher.hashIntervalFromLastNote = True
        >>> sa2.hasher.hashIsAccidental = True
        >>> sa2.align()
        >>> tup2 = sa2.hashedTargetStream[0]
        >>> sa2.insertCost(tup2)
        5
        '''
        keyDictSize = len(tup.hashItemsKeys)
        return keyDictSize

    def deleteCost(self, tup):
        '''
        Cost of deleting an extra hashed item.
        For now, it's just the size of the keys of the NoteHashWithReference

        >>> target = stream.Stream()
        >>> source = stream.Stream()

        >>> note1 = note.Note('C4')
        >>> note2 = note.Note('D4')
        >>> note3 = note.Note('C4')
        >>> note4 = note.Note('E4')

        >>> target.append([note1, note2, note3, note4])
        >>> source.append([note1, note2, note3])

        This is a StreamAligner with default hasher settings

        >>> sa0 = alpha.analysis.aligner.StreamAligner(target, source)
        >>> sa0.align()
        >>> tup0 = sa0.hashedSourceStream[0]
        >>> sa0.deleteCost(tup0)
        2

        This is a StreamAligner with a modified hasher that doesn't hash pitch at all

        >>> sa1 = alpha.analysis.aligner.StreamAligner(target, source)
        >>> sa1.hasher.hashPitch = False
        >>> sa1.align()
        >>> tup1 = sa1.hashedSourceStream[0]
        >>> sa1.deleteCost(tup1)
        1

        This is a StreamAligner with a modified hasher that hashes 3 additional properties

        >>> sa2 = alpha.analysis.aligner.StreamAligner(target, source)
        >>> sa2.hasher.hashOctave = True
        >>> sa2.hasher.hashIntervalFromLastNote = True
        >>> sa2.hasher.hashIsAccidental = True
        >>> sa2.align()
        >>> tup2 = sa2.hashedSourceStream[0]
        >>> sa2.deleteCost(tup2)
        5
        '''
        keyDictSize = len(tup.hashItemsKeys)
        return keyDictSize

    def substitutionCost(self, targetTup, sourceTup):
        '''
        Finds the cost of substituting the targetTup with the sourceTup.
        For now it's just an interpolation of how many things they have in common

        Example: equality testing, both streams made from same note
        targetA will not have the same reference as sourceA
        but their hashes will be equal, which makes for their hashed objects to be
        able to be equal.

        >>> note1 = note.Note('C4')
        >>> targetA = stream.Stream()
        >>> sourceA = stream.Stream()
        >>> targetA.append(note1)
        >>> sourceA.append(note1)
        >>> targetA == sourceA
        False

        >>> saA = alpha.analysis.aligner.StreamAligner(targetA, sourceA)
        >>> saA.align()
        >>> hashedItem1A = saA.hashedTargetStream[0]
        >>> hashedItem2A = saA.hashedSourceStream[0]
        >>> print(hashedItem1A)
        NoteHashWithReference(Pitch=60, Duration=1.0)

        >>> print(hashedItem2A)
        NoteHashWithReference(Pitch=60, Duration=1.0)

        >>> saA.tupleEqualityWithoutReference(hashedItem1A, hashedItem2A)
        True
        >>> saA.substitutionCost(hashedItem1A, hashedItem2A)
        0

        >>> note2 = note.Note('D4')
        >>> targetB = stream.Stream()
        >>> sourceB = stream.Stream()
        >>> targetB.append(note1)
        >>> sourceB.append(note2)
        >>> saB = alpha.analysis.aligner.StreamAligner(targetB, sourceB)
        >>> saB.align()
        >>> hashedItem1B = saB.hashedTargetStream[0]
        >>> hashedItem2B = saB.hashedSourceStream[0]

        hashed items only differ in 1 spot

        >>> print(hashedItem1B)
        NoteHashWithReference(Pitch=60, Duration=1.0)

        >>> print(hashedItem2B)
        NoteHashWithReference(Pitch=62, Duration=1.0)

        >>> saB.substitutionCost(hashedItem1B, hashedItem2B)
        1

        >>> note3 = note.Note('E4')
        >>> note4 = note.Note('E#4')
        >>> note4.duration = duration.Duration('half')
        >>> targetC = stream.Stream()
        >>> sourceC = stream.Stream()
        >>> targetC.append(note3)
        >>> sourceC.append(note4)
        >>> saC = alpha.analysis.aligner.StreamAligner(targetC, sourceC)
        >>> saC.align()
        >>> hashedItem1C = saC.hashedTargetStream[0]
        >>> hashedItem2C = saC.hashedSourceStream[0]

        hashed items should differ in 2 spots

        >>> print(hashedItem1C)
        NoteHashWithReference(Pitch=64, Duration=1.0)

        >>> print(hashedItem2C)
        NoteHashWithReference(Pitch=65, Duration=2.0)

        >>> saC.substitutionCost(hashedItem1C, hashedItem2C)
        2
        '''
        if self.tupleEqualityWithoutReference(targetTup, sourceTup):
            return 0

        totalPossibleDifferences = len(targetTup.hashItemsKeys)
        numSimilaritiesInTuple = self.calculateNumSimilarities(targetTup, sourceTup)
        totalPossibleDifferences -= numSimilaritiesInTuple
        return totalPossibleDifferences

    def calculateNumSimilarities(self, targetTup, sourceTup):
        '''
        Returns the number of attributes that two tuples have that are the same

        >>> target = stream.Stream()
        >>> source = stream.Stream()

        >>> note1 = note.Note('D1')
        >>> target.append([note1])
        >>> source.append([note1])
        >>> sa = alpha.analysis.aligner.StreamAligner(target, source)

        >>> from collections import namedtuple
        >>> NoteHash = namedtuple('NoteHash', ['Pitch', 'Duration'])
        >>> nh1 = NoteHash(60, 4)
        >>> nhwr1 = alpha.analysis.hasher.NoteHashWithReference(nh1)
        >>> nhwr1.reference = note.Note('C4')
        >>> nhwr1
        NoteHashWithReference(Pitch=60, Duration=4)

        >>> nh2 = NoteHash(60, 4)
        >>> nhwr2 = alpha.analysis.hasher.NoteHashWithReference(nh2)
        >>> nhwr2.reference = note.Note('C4')
        >>> nhwr2
        NoteHashWithReference(Pitch=60, Duration=4)

        >>> sa.calculateNumSimilarities(nhwr1, nhwr2)
        2

        >>> nh3 = NoteHash(61, 4)
        >>> nhwr3 = alpha.analysis.hasher.NoteHashWithReference(nh3)
        >>> nhwr3.reference = note.Note('C#4')
        >>> nhwr3
        NoteHashWithReference(Pitch=61, Duration=4)

        >>> sa.calculateNumSimilarities(nhwr1, nhwr3)
        1

        >>> nh4 = NoteHash(59, 1)
        >>> nhwr4 = alpha.analysis.hasher.NoteHashWithReference(nh4)
        >>> nhwr4.reference = note.Note('B3')
        >>> nhwr4
        NoteHashWithReference(Pitch=59, Duration=1)

        >>> sa.calculateNumSimilarities(nhwr2, nhwr4)
        0
        '''

        count = 0
        for val in targetTup.hashItemsKeys:
            if getattr(targetTup, val) == getattr(sourceTup, val):
                count += 1
        return count

    def tupleEqualityWithoutReference(self, tup1, tup2):
        '''
        Returns whether two hashed items have the same attributes,
        even though their references are different?

        >>> target = stream.Stream()
        >>> source = stream.Stream()

        >>> note1 = note.Note('D1')
        >>> target.append([note1])
        >>> source.append([note1])
        >>> sa = alpha.analysis.aligner.StreamAligner(target, source)

        >>> from collections import namedtuple
        >>> NoteHash = namedtuple('NoteHash', ['Pitch', 'Duration'])
        >>> nh1 = NoteHash(60, 4)
        >>> nhwr1 = alpha.analysis.hasher.NoteHashWithReference(nh1)
        >>> nhwr1.reference = note.Note('C4')
        >>> nhwr1
        NoteHashWithReference(Pitch=60, Duration=4)

        >>> nh2 = NoteHash(60, 4)
        >>> nhwr2 = alpha.analysis.hasher.NoteHashWithReference(nh2)
        >>> nhwr2.reference = note.Note('B#3')
        >>> nhwr2
        NoteHashWithReference(Pitch=60, Duration=4)

        >>> sa.tupleEqualityWithoutReference(nhwr1, nhwr2)
        True

        This is a very difference has

        >>> nh3 = NoteHash(61, 4)
        >>> nhwr3 = alpha.analysis.hasher.NoteHashWithReference(nh3)
        >>> nhwr3.reference = note.Note('C#4')
        >>> nhwr3
        NoteHashWithReference(Pitch=61, Duration=4)

        >>> sa.tupleEqualityWithoutReference(nhwr1, nhwr3)
        False

        '''
        for val in tup1.hashItemsKeys:
            if getattr(tup1, val) != getattr(tup2, val):
                return False
        return True

    def calculateChangesList(self):
        '''
        Traverses through self.distanceMatrix from bottom right corner to top left looking at
        bestOp at every move to determine which change was most likely at any point. Compiles
        the list of changes in self.changes. Also calculates some metrics like self.similarityScore
        and self.changesCount.

        >>> note1 = note.Note('C#4')
        >>> note2 = note.Note('C4')

        test 1: one insertion, one no change. Target stream has one more note than
        source stream, so source stream needs an insertion to match target stream.
        should be 0.5 similarity between the two

        >>> targetA = stream.Stream()
        >>> sourceA = stream.Stream()
        >>> targetA.append([note1, note2])
        >>> sourceA.append(note1)
        >>> saA = alpha.analysis.aligner.StreamAligner(targetA, sourceA)
        >>> saA.makeHashedStreams()
        >>> saA.setupDistanceMatrix()
        >>> saA.populateDistanceMatrix()
        >>> saA.calculateChangesList()
        >>> saA.changesCount[alpha.analysis.aligner.ChangeOps.Insertion]
        1
        >>> saA.changesCount[alpha.analysis.aligner.ChangeOps.NoChange]
        1
        >>> saA.similarityScore
        0.5

        test 2: one deletion, one no change. Target stream has one fewer note than
        source stream, so source stream needs a deletion to match target stream.
        should be 0.5 similarity between the two

        >>> targetB = stream.Stream()
        >>> sourceB = stream.Stream()
        >>> targetB.append(note1)
        >>> sourceB.append([note1, note2])
        >>> saB = alpha.analysis.aligner.StreamAligner(targetB, sourceB)
        >>> saB.makeHashedStreams()
        >>> saB.setupDistanceMatrix()
        >>> saB.populateDistanceMatrix()
        >>> saB.calculateChangesList()
        >>> saB.changesCount[alpha.analysis.aligner.ChangeOps.Deletion]
        1
        >>> saB.changesCount[alpha.analysis.aligner.ChangeOps.NoChange]
        1
        >>> saB.similarityScore
        0.5

        test 3: no changes

        >>> targetC = stream.Stream()
        >>> sourceC = stream.Stream()
        >>> targetC.append([note1, note2])
        >>> sourceC.append([note1, note2])
        >>> saC = alpha.analysis.aligner.StreamAligner(targetC, sourceC)
        >>> saC.makeHashedStreams()
        >>> saC.setupDistanceMatrix()
        >>> saC.populateDistanceMatrix()
        >>> saC.calculateChangesList()
        >>> saC.changesCount[alpha.analysis.aligner.ChangeOps.NoChange]
        2
        >>> saC.similarityScore
        1.0

        test 4: 1 no change, 1 substitution

        >>> targetD = stream.Stream()
        >>> sourceD = stream.Stream()
        >>> note3 = note.Note('C4')
        >>> note3.quarterLength = 2  # same pitch and offset as note2
        >>> targetD.append([note1, note2])
        >>> sourceD.append([note1, note3])
        >>> saD = alpha.analysis.aligner.StreamAligner(targetD, sourceD)
        >>> saD.makeHashedStreams()
        >>> saD.setupDistanceMatrix()
        >>> saD.populateDistanceMatrix()
        >>> saD.calculateChangesList()
        >>> saD.changesCount[alpha.analysis.aligner.ChangeOps.Substitution]
        1
        >>> saD.changesCount[alpha.analysis.aligner.ChangeOps.NoChange]
        1
        >>> saD.similarityScore
        0.5

        '''
        i = self.n
        j = self.m
        while i != 0 or j != 0:

            # check if possible moves are indexable
            bestOp = self.getOpFromLocation(i, j)
            targetStreamReference = self.hashedTargetStream[i - 1].reference
            sourceStreamReference = self.hashedSourceStream[j - 1].reference
            opTuple = (targetStreamReference, sourceStreamReference, bestOp)
            self.changes.insert(0, opTuple)

            # changes are done for this cell -- where to move next?

            # bestOp : 0: insertion, 1: deletion, 2: substitution; 3: nothing
            if bestOp == ChangeOps.Insertion:
                i -= 1

            elif bestOp == ChangeOps.Deletion:
                j -= 1

            elif bestOp == ChangeOps.Substitution:
                i -= 1
                j -= 1

            else:  # 3: ChangeOps.NoChange
                i -= 1
                j -= 1
        if i != 0 and j != 0:
            raise AlignmentTracebackException('Traceback of best alignment did not end properly')

        self.changesCount = Counter(elem[2] for elem in self.changes)
        self.similarityScore = float(self.changesCount[ChangeOps.NoChange]) / len(self.changes)

    def showChanges(self, show=False):
        '''
        Visual and debugging feature to display which notes are changed.
        Will open in musescore, unless show is set to False
        '''
        for (idx, (midiNoteRef, omrNoteRef, change)) in enumerate(self.changes):
            if change == ChangeOps.NoChange:
                pass
            else:  # change is Insertion, Deletion, Substitution
                midiNoteRef.style.color = change.color
                midiNoteRef.addLyric(idx)
                omrNoteRef.style.color = change.color
                omrNoteRef.addLyric(idx)

        self.targetStream.metadata = metadata.Metadata()
        self.sourceStream.metadata = metadata.Metadata()

        self.targetStream.metadata.title = 'Target ' + str(self.targetStream.id)
        self.sourceStream.metadata.title = 'Source ' + str(self.targetStream.id)

        self.targetStream.metadata.movementName = self.targetStream.metadata.title
        self.sourceStream.metadata.movementName = self.sourceStream.metadata.title

        if show:
            self.targetStream.show()
            self.sourceStream.show()


class Test(unittest.TestCase):
    def testSimpleStreamOneNote(self):
        '''
        two streams of the same note should have 1.0 similarity
        '''
        from music21 import stream
        from music21 import note

        target = stream.Stream()
        source = stream.Stream()

        note1 = note.Note('C4')
        note2 = note.Note('C4')

        target.append(note1)
        source.append(note2)

        sa = StreamAligner(target, source)
        sa.align()

        self.assertEqual(sa.similarityScore, 1.0)

    def testSimpleStreamOneNoteDifferent(self):
        '''
        two streams of two different notes should have 0.0 similarity
        '''
        from music21 import stream
        from music21 import note

        target = stream.Stream()
        source = stream.Stream()

        note1 = note.Note('C4')
        note2 = note.Note('C#4')
        note2.quarterLength = 4

        target.append(note1)
        source.append(note2)

        sa = StreamAligner(target, source)
        sa.align()

        self.assertEqual(sa.similarityScore, 0.0)

    def testSameSimpleStream(self):
        '''
        two streams of the same notes should have 1.0 percentage similarity
        '''
        from music21 import stream
        from music21 import note

        target = stream.Stream()
        source = stream.Stream()

        note1 = note.Note('C4')
        note2 = note.Note('D4')
        note3 = note.Note('E4')
        note4 = note.Note('F4')

        target.append([note1, note2, note3, note4])
        source.append([note1, note2, note3, note4])

        sa = StreamAligner(target, source)
        sa.align()

        self.assertEqual(sa.similarityScore, 1.0)

    def testSameSimpleStream2(self):
        '''
        two streams of the 2/3 same notes should have 2/3 similarity
        '''
        from music21 import stream
        from music21 import note

        target = stream.Stream()
        source = stream.Stream()

        note1 = note.Note('C4')
        note2 = note.Note('D#4')
        note3 = note.Note('D-4')
        note4 = note.Note('C4')

        target.append([note1, note2, note4])
        source.append([note1, note3, note4])

        sa = StreamAligner(target, source)
        sa.align()

        self.assertEqual(sa.similarityScore, 2 / 3)

    def testSameOneOffStream(self):
        '''
        two streams with just 1 note different should have 0.75 percentage similarity
        '''
        from music21 import stream
        from music21 import note

        target = stream.Stream()
        source = stream.Stream()

        note1 = note.Note('C4')
        note2 = note.Note('D4')
        note3 = note.Note('E4')
        note4 = note.Note('F4')
        note5 = note.Note('G4')

        target.append([note1, note2, note3, note4])
        source.append([note1, note2, note3, note5])

        sa = StreamAligner(target, source)
        sa.align()

        self.assertEqual(sa.similarityScore, 0.75)

    def testOneOffDeletionStream(self):
        '''
        two streams, both the same, but one has an extra note should
        have 0.75 percentage similarity
        '''
        from music21 import stream
        from music21 import note

        target = stream.Stream()
        source = stream.Stream()

        note1 = note.Note('C4')
        note2 = note.Note('D4')
        note3 = note.Note('E4')
        note4 = note.Note('F4')

        target.append([note1, note2, note3, note4])
        source.append([note1, note2, note3])

        sa = StreamAligner(target, source)
        sa.align()
        sa.showChanges()

        self.assertEqual(sa.similarityScore, 0.75)

    def testChordSimilarityStream(self):
        '''
        two streams, one with explicit chord
        '''
        from music21 import stream
        from music21 import chord

        target = stream.Stream()
        source = stream.Stream()

        cMajor = chord.Chord(['E3', 'C4', 'G4'])
        target.append(cMajor)
        source.append(cMajor)

        sa = StreamAligner(target, source)
        sa.align()
        self.assertEqual(sa.similarityScore, 1.)

    def testShowInsertion(self):
        '''
        two streams:
        MIDI is CCCB
        OMR is CCC

        Therefore there needs to be an insertion to get from OMR to MIDI
        '''
        from music21 import stream
        from music21 import note

        target = stream.Stream()
        source = stream.Stream()

        noteC1 = note.Note('C4')
        noteC2 = note.Note('C4')
        noteC3 = note.Note('C4')
        noteC4 = note.Note('C4')
        noteC5 = note.Note('C4')
        noteC6 = note.Note('C4')
        noteB = note.Note('B3')

        target.append([noteC1, noteC2, noteC3, noteB])
        source.append([noteC4, noteC5, noteC6])

        sa = StreamAligner(target, source)
        sa.align()
        sa.showChanges()

        self.assertEqual(target.getElementById(sa.changes[3][0].id).style.color, 'green')
        self.assertEqual(target.getElementById(sa.changes[3][0].id).lyric, '3')
        self.assertEqual(source.getElementById(sa.changes[3][1].id).style.color, 'green')
        self.assertEqual(source.getElementById(sa.changes[3][1].id).lyric, '3')

    def testShowDeletion(self):
        '''
        two streams:

        MIDI is `CCC`

        OMR is `CCCB`

        Therefore there needs to be an deletion to get from OMR to MIDI.
        '''
        from music21 import stream
        from music21 import note

        target = stream.Stream()
        source = stream.Stream()

        noteC1 = note.Note('C4')
        noteC2 = note.Note('C4')
        noteC3 = note.Note('C4')
        noteC4 = note.Note('C4')
        noteC5 = note.Note('C4')
        noteC6 = note.Note('C4')
        noteB = note.Note('B3')

        target.append([noteC1, noteC2, noteC3])
        source.append([noteC4, noteC5, noteC6, noteB])

        sa = StreamAligner(target, source)
        sa.align()
        sa.showChanges()

        self.assertEqual(target.getElementById(sa.changes[3][0].id).style.color, 'red')
        self.assertEqual(target.getElementById(sa.changes[3][0].id).lyric, '3')
        self.assertEqual(source.getElementById(sa.changes[3][1].id).style.color, 'red')
        self.assertEqual(source.getElementById(sa.changes[3][1].id).lyric, '3')

    def testShowSubstitution(self):
        '''
        two streams:
        MIDI is CCC
        OMR is CCB

        Therefore there needs to be an substitution to get from OMR to MIDI
        '''
        from music21 import stream
        from music21 import note

        target = stream.Stream()
        source = stream.Stream()

        noteC1 = note.Note('C4')
        noteC2 = note.Note('C4')
        noteC3 = note.Note('C4')
        noteC4 = note.Note('C4')
        noteC5 = note.Note('C4')
        noteB = note.Note('B3')

        target.append([noteC1, noteC2, noteC3])
        source.append([noteC4, noteC5, noteB])

        sa = StreamAligner(target, source)
        sa.align()
        sa.showChanges()

        self.assertEqual(target.getElementById(sa.changes[2][0].id).style.color, 'purple')
        self.assertEqual(target.getElementById(sa.changes[2][0].id).lyric, '2')
        self.assertEqual(source.getElementById(sa.changes[2][1].id).style.color, 'purple')
        self.assertEqual(source.getElementById(sa.changes[2][1].id).lyric, '2')


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)
