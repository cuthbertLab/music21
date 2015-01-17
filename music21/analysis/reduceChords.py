# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         reduceChords.py
# Purpose:      Tools for eliminating passing chords, etc.
#
# Authors:      Michael Scott Cuthbert, Josiah Wolf Oberholtzer
#
# Copyright:    Copyright © 2013 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#------------------------------------------------------------------------------

'''
Automatically reduce a MeasureStack to a single chord or group of chords.
'''

import collections
import itertools
import unittest
from music21 import chord
from music21 import exceptions21
from music21 import environment
from music21 import meter
from music21 import note
from music21 import pitch
from music21 import stream
#from music21 import tie

environLocal = environment.Environment('reduceChords')


#------------------------------------------------------------------------------


def testMeasureStream1():
    '''
    returns a simple measure stream for testing:


    >>> s = analysis.reduceChords.testMeasureStream1()
    >>> s.show('text')
    {0.0} <music21.meter.TimeSignature 4/4>
    {0.0} <music21.chord.Chord C4 E4 G4 C5>
    {2.0} <music21.chord.Chord C4 E4 F4 B4>
    {3.0} <music21.chord.Chord C4 E4 G4 C5>
    '''
    #from music21 import chord
    measure = stream.Measure()
    timeSignature = meter.TimeSignature('4/4')
    chord1 = chord.Chord('C4 E4 G4 C5')
    chord1.quarterLength = 2.0
    chord2 = chord.Chord('C4 E4 F4 B4')
    chord3 = chord.Chord('C4 E4 G4 C5')
    for element in (timeSignature, chord1, chord2, chord3):
        measure.append(element)
    return measure


#------------------------------------------------------------------------------
class ChordReducerException(exceptions21.Music21Exception):
    pass

class ChordReducer(object):
    r'''
    A chord reducer.
    '''

    ### INITIALIZER ###

    def __init__(self):
        self.weightAlgorithm = self.qlbsmpConsonance
        self.maxChords = 3
        self.positionInMeasure = None
        self.numberOfElementsInMeasure = None

    def run(
        self,
        inputScore,
        allowableChords=None,
        closedPosition=False,
        forbiddenChords=None,
        maximumNumberOfChords=3,
        ):
        from music21.stream import timespans
        if 'Score' not in inputScore.classes:
            raise ChordReducerException("Must be called on a stream.Score")

        tree = timespans.streamToTimespanTree(inputScore, flatten=True, classList=(note.Note, chord.Chord))

        if allowableChords is not None:
            assert all(isinstance(x, chord.Chord) for x in allowableChords)
            intervalClassSets = []
            for x in allowableChords:
                intervalClassSet = self._getIntervalClassSet(x.pitches)
                intervalClassSets.append(intervalClassSet)
            allowableChords = frozenset(intervalClassSets)

        if forbiddenChords is not None:
            assert all(isinstance(x, chord.Chord) for x in forbiddenChords)
            intervalClassSets = []
            for x in allowableChords:
                intervalClassSet = self._getIntervalClassSet(x.pitches)
                intervalClassSets.append(intervalClassSet)
            forbiddenChords = frozenset(intervalClassSets)

        self.removeZeroDurationTimespans(tree)
        self.splitByBass(tree)
        self.removeVerticalDissonances(
            tree=tree,
            allowableChords=allowableChords,
            forbiddenChords=forbiddenChords,
            )

        partwiseTrees = tree.toPartwiseTimespanTrees()

        self.fillBassGaps(tree, partwiseTrees)

        self.removeShortTimespans(tree, partwiseTrees, duration=0.5)
        self.fillBassGaps(tree, partwiseTrees)
        self.fillMeasureGaps(tree, partwiseTrees)

        self.removeShortTimespans(tree, partwiseTrees, duration=1.0)
        self.fillBassGaps(tree, partwiseTrees)
        self.fillMeasureGaps(tree, partwiseTrees)

        reduction = stream.Score()
        #partwiseReduction = tree.toPartwiseScore()
        #for part in partwiseReduction:
        #    reduction.append(part)
        chordifiedReduction = timespans.timespansToChordifiedStream(
            tree,
            templateStream=inputScore,
            )
        chordifiedPart = stream.Part()
        for measure in chordifiedReduction:
            reducedMeasure = self.reduceMeasureToNChords(
                measure,
                maximumNumberOfChords=maximumNumberOfChords,
                weightAlgorithm=self.qlbsmpConsonance,
                trimBelow=0.25,
                )
            chordifiedPart.append(reducedMeasure)
        reduction.append(chordifiedPart)

        if closedPosition:
            for x in reduction.flat.getElementsByClass('Chord'):
                x.closedPosition(forceOctave=4, inPlace=True)

        return reduction

    ### PRIVATE METHODS ###

    @staticmethod
    def _debug(tree):
        for part, subtree in tree.toPartwiseTimespanTrees().items():
            print(part)
            timespans = [x for x in subtree]
            for timespan in timespans:
                print('\t', timespan)
            overlap = subtree.maximumOverlap
            if 1 < overlap:
                print(part)
                raise Exception()

    @staticmethod
    def _getIntervalClassSet(pitches):
        result = set()
        pitches = [pitch.Pitch(x) for x in pitches]
        for i, x in enumerate(pitches):
            for y in pitches[i + 1:]:
                interval = int(abs(x.ps - y.ps))
                interval %= 12
                if 6 < interval:
                    interval = 12 - interval
                result.add(interval)
        if 0 in result:
            result.remove(0)
        return frozenset(result)

    def _iterateElementsPairwise(self, inputStream):
        elementBuffer = []
        prototype = (
            chord.Chord,
            note.Note,
            note.Rest,
            )
        for element in inputStream.flat:
            if not isinstance(element, prototype):
                continue
            elementBuffer.append(element)
            if len(elementBuffer) == 2:
                yield tuple(elementBuffer)
                elementBuffer.pop(0)

    ### PUBLIC METHODS ###

    def alignHockets(self, tree):
        r'''
        Aligns hockets between parts in `tree`.
        '''
        for verticalities in tree.iterateVerticalitiesNwise(n=2):
            verticalityOne, verticalityTwo = verticalities
            pitchSetOne = verticalityOne.pitchSet
            pitchSetTwo = verticalityTwo.pitchSet
            if not verticalityOne.isConsonant or \
                not verticalityTwo.isConsonant:
                continue
            if verticalityOne.measureNumber != verticalityTwo.measureNumber:
                continue
            if verticalityOne.pitchSet == verticalityTwo.pitchSet:
                continue
            if pitchSetOne.issubset(pitchSetTwo):
                for timespan in verticalityTwo.startTimespans:
                    tree.remove(timespan)
                    newTimespan = timespan.new(
                        beatStrength=verticalityOne.beatStrength,
                        offset=verticalityOne.offset,
                        )
                    tree.insert(newTimespan)
            elif pitchSetTwo.issubset(pitchSetOne):
                for timespan in verticalityOne.startTimespans:
                    if timespan.endTime < verticalityTwo.offset:
                        tree.remove(timespan)
                        newTimespan = timespan.new(
                            endTime=verticalityTwo.offset,
                            )
                        tree.insert(newTimespan)

    def collapseArpeggios(self, tree):
        r'''
        Collapses arpeggios in `tree`.
        '''
        for verticalities in tree.iterateVerticalitiesNwise(n=2):
            one, two = verticalities
            onePitches = sorted(one.pitchSet)
            twoPitches = sorted(two.pitchSet)
            if onePitches[0].nameWithOctave != twoPitches[0].nameWithOctave:
                continue
            elif one.measureNumber != two.measureNumber:
                continue
            bothPitches = set()
            bothPitches.update([x.nameWithOctave for x in onePitches])
            bothPitches.update([x.nameWithOctave for x in twoPitches])
            bothPitches = sorted([pitch.Pitch(x) for x in bothPitches])
            #if not timespanStream.Verticality.pitchesAreConsonant(bothPitches):
            #    intervalClasses = self._getIntervalClassSet(bothPitches)
            #    if intervalClasses not in (
            #        frozenset([1, 3, 4]),
            #        frozenset([1, 4, 5]),
            #        frozenset([2, 3, 5]),
            #        frozenset([2, 4, 6]),
            #        ):
            #        continue
            horizontalities = tree.unwrapVerticalities(verticalities)
            for unused_part, timespans in horizontalities.items():
                if len(timespans) < 2:
                    continue
                elif timespans[0].pitches == timespans[1].pitches:
                    continue
                bothPitches = timespans[0].pitches + timespans[1].pitches
                sumChord = chord.Chord(bothPitches)
                tree.remove(timespans)
                merged = timespans[0].new(
                    element=sumChord,
                    endTime=timespans[1].endTime,
                    )
                tree.insert(merged)

    def computeMeasureChordWeights(
        self,
        measureObject,
        weightAlgorithm=None,
        ):
        '''
        Compute measure chord weights:

        >>> s = analysis.reduceChords.testMeasureStream1().notes
        >>> cr = analysis.reduceChords.ChordReducer()
        >>> cws = cr.computeMeasureChordWeights(s)
        >>> for pcs in sorted(cws):
        ...     print("%18r  %2.1f" % (pcs, cws[pcs]))
            (0, 4, 7)  3.0
        (0, 11, 4, 5)  1.0

        Add beatStrength:

        >>> cws = cr.computeMeasureChordWeights(s,
        ...     weightAlgorithm=cr.quarterLengthBeatStrength)
        >>> for pcs in sorted(cws):
        ...     print("%18r  %2.1f" % (pcs, cws[pcs]))
            (0, 4, 7)  2.2
        (0, 11, 4, 5)  0.5

        Give extra weight to the last element in a measure:

        >>> cws = cr.computeMeasureChordWeights(s,
        ...     weightAlgorithm=cr.quarterLengthBeatStrengthMeasurePosition)
        >>> for pcs in sorted(cws):
        ...     print("%18r  %2.1f" % (pcs, cws[pcs]))
            (0, 4, 7)  3.0
        (0, 11, 4, 5)  0.5

        Make consonance count a lot:

        >>> cws = cr.computeMeasureChordWeights(s,
        ...     weightAlgorithm=cr.qlbsmpConsonance)
        >>> for pcs in sorted(cws):
        ...     print("%18r  %2.1f" % (pcs, cws[pcs]))
             (0, 4, 7)  3.0
         (0, 11, 4, 5)  0.1
        '''
        if weightAlgorithm is None:
            weightAlgorithm = self.quarterLengthOnly
        presentPCs = {}
        self.positionInMeasure = 0
        self.numberOfElementsInMeasure = len(measureObject)
        for i, c in enumerate(measureObject):
            self.positionInMeasure = i
            if c.isNote:
                p = tuple(c.pitch.pitchClass)
            else:
                p = tuple(set([x.pitchClass for x in c.pitches]))
            if p not in presentPCs:
                presentPCs[p] = 0.0
            presentPCs[p] += weightAlgorithm(c)
        self.positionInMeasure = 0
        self.numberOfElementsInMeasure = 0
        return presentPCs

    def fillBassGaps(self, tree, partwiseTrees):
        def procedure(timespan):
            verticality = tree.getVerticalityAt(timespan.offset)
            return verticality.bassTimespan
        for unused_part, subtree in partwiseTrees.items():
            timespans = [x for x in subtree]
            for bassTimespan, group in itertools.groupby(timespans, procedure):
                group = list(group)

                if bassTimespan is None:
                    continue

                if bassTimespan.offset < group[0].offset:
                    beatStrength = bassTimespan.beatStrength
                    offset = bassTimespan.offset
                    previousTimespan = tree.findPreviousElementTimespanInSameStreamByClass(group[0])
                    if previousTimespan is not None:
                        if previousTimespan.endTime > group[0].offset:
                            msg = ('Timespan offset errors: previousTimespan.endTime, ' + 
                                                        str(previousTimespan.endTime) + ' should be before ' +
                                                        str(group[0].offset) + ' previousTimespan: ' + repr(previousTimespan) +
                                                        ' groups: ' + repr(group) + ' group[0]: ' + repr(group[0])
                                                        )
                            print(msg)
                            #raise ChordReducerException(msg)
                        if offset < previousTimespan.endTime:
                            offset = previousTimespan.endTime
                    tree.remove(group[0])
                    subtree.remove(group[0])
                    newTimespan = group[0].new(
                        beatStrength=beatStrength,
                        offset=offset,
                        )
                    tree.insert(newTimespan)
                    subtree.insert(newTimespan)
                    group[0] = newTimespan

                if group[-1].endTime < bassTimespan.endTime:
                    endTime = bassTimespan.endTime
                    tree.remove(group[-1])
                    subtree.remove(group[-1])
                    newTimespan = group[-1].new(
                        endTime=endTime,
                        )
                    tree.insert(newTimespan)
                    subtree.insert(newTimespan)
                    group[-1] = newTimespan

                for i in range(len(group) - 1):
                    timespanOne, timespanTwo = group[i], group[i + 1]
                    if timespanOne.pitches == timespanTwo.pitches or \
                        timespanOne.endTime != timespanTwo.offset:
                        newTimespan = timespanOne.new(
                            endTime=timespanTwo.endTime,
                            )
                        group[i] = newTimespan
                        group[i + 1] = newTimespan
                        tree.remove((timespanOne, timespanTwo))
                        subtree.remove((timespanOne, timespanTwo))
                        tree.insert(newTimespan)
                        subtree.insert(newTimespan)

    def fillMeasureGaps(self, tree, partwiseTrees):
        r'''
        Fills measure gaps in `tree`.
        '''
        for unused_part, subtree in partwiseTrees.items():
            toRemove = set()
            toInsert = set()
            for unused_measureNumber, group in itertools.groupby(
                              subtree, lambda x: x.measureNumber):
                group = list(group)
                for i in range(len(group) - 1):
                    timespanOne, timespanTwo = group[i], group[i + 1]
                    if timespanOne.pitches == timespanTwo.pitches or \
                        timespanOne.endTime != timespanTwo.offset:
                        newTimespan = timespanOne.new(
                            endTime=timespanTwo.endTime,
                            )
                        group[i] = newTimespan
                        group[i + 1] = newTimespan
                        toInsert.add(newTimespan)
                        toRemove.add(timespanOne)
                        toRemove.add(timespanTwo)
                if group[0].offset != group[0].parentOffset:
                    newTimespan = group[0].new(
                        beatStrength=1.0,
                        offset=group[0].parentOffset,
                        )
                    toRemove.add(group[0])
                    toInsert.add(newTimespan)
                    group[0] = newTimespan
                if group[-1].endTime != group[-1].parentEndTime:
                    newTimespan = group[-1].new(
                        endTime=group[-1].parentEndTime,
                        )
                    toRemove.add(group[-1])
                    toInsert.add(newTimespan)
                    group[-1] = newTimespan
            # The insertion list may contain timespans later marked for removal
            # Therefore insertion must occur before removals
            toInsert.difference_update(toRemove)
            tree.insert(toInsert)
            tree.remove(toRemove)
            subtree.insert(toInsert)
            subtree.remove(toRemove)

    def fuseTimespansByPart(self, tree, part):
        def procedure(timespan):
            measureNumber = timespan.measureNumber
            pitches = timespan.pitches
            return measureNumber, pitches
        mapping = tree.toPartwiseTimespanTrees()
        subtree = mapping[part]
        timespans = [x for x in subtree]
        for unused_key, group in itertools.groupby(timespans, procedure):
            #measureNumber, pitches = key
            group = list(group)
            if len(group) == 1:
                continue
            tree.remove(group)
            newTimespan = group[0].new(
                endTime=group[-1].endTime,
                )
            tree.insert(newTimespan)

    def qlbsmpConsonance(self, chordObject):
        '''
        Everything from before plus consonance
        '''
        consonanceScore = 1.0 if chordObject.isConsonant() else 0.1
        if self.positionInMeasure == self.numberOfElementsInMeasure - 1:
            # call beatStrength 1
            weight = chordObject.quarterLength
        else:
            weight = self.quarterLengthBeatStrengthMeasurePosition(chordObject)
        weight *= consonanceScore
        return weight

    def quarterLengthBeatStrength(self, chordObject):
        weight = chordObject.quarterLength * chordObject.beatStrength
        return weight

    def quarterLengthBeatStrengthMeasurePosition(self, chordObject):
        if self.positionInMeasure == self.numberOfElementsInMeasure - 1:
            return chordObject.quarterLength  # call beatStrength 1
        else:
            return self.quarterLengthBeatStrength(chordObject)

    def quarterLengthOnly(self, chordObject):
        return chordObject.quarterLength

    def reduceMeasureToNChords(
        self,
        measureObject,
        maximumNumberOfChords=1,
        weightAlgorithm=None,
        trimBelow=0.25,
        ):
        '''
        Reduces measure to `n` chords:

        >>> s = analysis.reduceChords.testMeasureStream1()
        >>> cr = analysis.reduceChords.ChordReducer()

        Reduce to a maximum of 3 chords; though here we will only get one
        because the other chord is below the trimBelow threshold.

        >>> newS = cr.reduceMeasureToNChords(s, 3,
        ...     weightAlgorithm=cr.qlbsmpConsonance,
        ...     trimBelow=0.3)
        >>> newS.show('text')
        {0.0} <music21.meter.TimeSignature 4/4>
        {0.0} <music21.chord.Chord C4 E4 G4 C5>

        >>> newS[-1].quarterLength
        4.0

        '''
        #from music21 import note
        #if inputMeasure.isFlat is False:
        #    measureObject = inputMeasure.flat.notes
        #else:
        #    measureObject = inputMeasure.notes
        chordWeights = self.computeMeasureChordWeights(
            measureObject.flat.notes,
            weightAlgorithm,
            )
        if maximumNumberOfChords > len(chordWeights):
            maximumNumberOfChords = len(chordWeights)
        sortedChordWeights = sorted(
            chordWeights,
            key=chordWeights.get,
            reverse=True,
            )
        maxNChords = sortedChordWeights[:maximumNumberOfChords]
        if len(maxNChords) == 0:
            r = note.Rest()
            r.quarterLength = measureObject.duration.quarterLength
            for c in measureObject:
                measureObject.remove(c)
            measureObject.insert(0, r)
            return measureObject
        maxChordWeight = chordWeights[maxNChords[0]]
        trimmedMaxChords = []
        for pcTuples in maxNChords:
            if chordWeights[pcTuples] >= maxChordWeight * trimBelow:
                trimmedMaxChords.append(pcTuples)
            else:
                break
        currentGreedyChord = None
        currentGreedyChordPCs = None
        currentGreedyChordNewLength = 0.0
        for c in measureObject:
            if isinstance(c, note.Note):
                p = tuple(c.pitch.pitchClass)
            elif isinstance(c, chord.Chord):
                p = tuple(set([x.pitchClass for x in c.pitches]))
            else:
                continue
            if p in trimmedMaxChords and p != currentGreedyChordPCs:
                # keep this chord
                if currentGreedyChord is None and c.offset != 0.0:
                    currentGreedyChordNewLength = c.offset
                    c.offset = 0.0
                elif currentGreedyChord is not None:
                    currentGreedyChord.quarterLength = currentGreedyChordNewLength
                    currentGreedyChordNewLength = 0.0
                currentGreedyChord = c
                for n in c:
                    #n.tie = None
                    if n.pitch.accidental is not None:
                        n.pitch.accidental.displayStatus = None
                currentGreedyChordPCs = p
                currentGreedyChordNewLength += c.quarterLength
            else:
                currentGreedyChordNewLength += c.quarterLength
                measureObject.remove(c)
        if currentGreedyChord is not None:
            currentGreedyChord.quarterLength = currentGreedyChordNewLength
            currentGreedyChordNewLength = 0.0
        # even chord lengths...
        for i in range(1, len(measureObject)):
            c = measureObject[i]
            cOffsetCurrent = c.offset
            cOffsetSyncop = cOffsetCurrent - int(cOffsetCurrent)
            if round(cOffsetSyncop, 3) in [0.250, 0.125, 0.333, 0.063, 0.062]:
                lastC = measureObject[i - 1]
                lastC.quarterLength -= cOffsetSyncop
                c.offset = int(cOffsetCurrent)
                c.quarterLength += cOffsetSyncop
        return measureObject

    def removeNonChordTones(self, tree):
        r'''
        Removes timespans containing passing and neighbor tones from `tree`.
        '''
        for verticalities in tree.iterateVerticalitiesNwise(n=3):
            horizontalities = tree.unwrapVerticalities(verticalities)
            for unused_part, horizontality in horizontalities.items():
                if not horizontality.hasPassingTone and \
                    not horizontality.hasNeighborTone:
                    continue
                elif horizontality[0].measureNumber != \
                    horizontality[1].measureNumber:
                    continue
                merged = horizontality[0].new(
                    endTime=horizontality[1].endTime,
                    )
                tree.remove((horizontality[0], horizontality[1]))
                tree.insert(merged)

    def removeShortTimespans(self, tree, partwiseTrees, duration=0.5):
        r'''
        Removes timespans in `tree` shorter than `duration`.

        Special treatment is given to groups of short timespans if they take up
        an entire measure. In that case, the timespans with the most common
        sets of pitches are kept.
        '''
        def procedure(timespan):
            measureNumber = timespan.measureNumber
            isShort = timespan.quarterLength < duration
            verticality = tree.getVerticalityAt(timespan.offset)
            bassTimespan = verticality.bassTimespan
            if bassTimespan is not None:
                if bassTimespan.quarterLength < duration:
                    bassTimespan = None
            return measureNumber, isShort, bassTimespan
        for unused_part, subtree in partwiseTrees.items():
            timespansToRemove = []
            for key, group in itertools.groupby(subtree, procedure):
                unused_measureNumber, isShort, bassTimespan = key
                group = list(group)
                if not isShort:
                    continue
                isEntireMeasure = False
                if group[0].offset == group[0].parentOffset:
                    if group[-1].endTime == group[0].parentEndTime:
                        isEntireMeasure = True
                if bassTimespan is not None:
                    if group[0].offset == bassTimespan.offset:
                        if group[-1].endTime == bassTimespan.endTime:
                            isEntireMeasure = True
                if isEntireMeasure:
                    counter = collections.Counter()
                    for timespan in group:
                        counter[timespan.pitches] += timespan.quarterLength
                    bestPitches, unused_totalDuration = counter.most_common()[0]
                    for timespan in group:
                        if timespan.pitches != bestPitches:
                            timespansToRemove.append(timespan)
                else:
                    timespansToRemove.extend(group)
            tree.remove(timespansToRemove)
            subtree.remove(timespansToRemove)

    def removeVerticalDissonances(
        self,
        tree=None,
        allowableChords=None,
        forbiddenChords=None,
        ):
        r'''
        Removes timespans in each dissonant verticality of `tree` whose pitches
        are above the lowest pitch in that verticality.
        '''
        for verticality in tree.iterateVerticalities():
            isConsonant = False
            pitches = verticality.pitchSet
            intervalClassSet = self._getIntervalClassSet(pitches)
            #print verticality, intervalClassSet, allowableChords, forbiddenChords
            if allowableChords and intervalClassSet in allowableChords:
                isConsonant = True
            if verticality.isConsonant:
                isConsonant = True
            if forbiddenChords and intervalClassSet in forbiddenChords:
                isConsonant = False
            if isConsonant:
                #print '\tCONSONANT'
                continue
            #print '\tNOT CONSONANT'
            pitchSet = verticality.pitchSet
            lowestPitch = min(pitchSet)
            for timespan in verticality.startTimespans:
                if min(timespan.pitches) != lowestPitch:
                    tree.remove(timespan)

    def removeZeroDurationTimespans(self, tree):
        zeroDurationTimespans = [x for x in tree if x.quarterLength == 0]
        tree.remove(zeroDurationTimespans)

    def splitByBass(self, tree):
        parts = tree.allParts
        for part in parts:
            self.fuseTimespansByPart(tree, part)
        mapping = tree.toPartwiseTimespanTrees()
        bassPart = parts[-1]
        bassTree = mapping[bassPart]
        bassOffsets = bassTree.allOffsets
        tree.splitAt(bassOffsets)


#------------------------------------------------------------------------------


class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testSimpleMeasure(self):
        #from music21 import chord
        s = stream.Measure()
        c1 = chord.Chord('C4 E4 G4 C5')
        c1.quarterLength = 2.0
        c2 = chord.Chord('C4 E4 F4 B4')
        c3 = chord.Chord('C4 E4 G4 C5')
        for c in [c1, c2, c3]:
            s.append(c)


class TestExternal(unittest.TestCase):

    def runTest(self):
        pass

    def testTrecentoMadrigal(self):
        from music21 import corpus

        score = corpus.parse('PMFC_06_Giovanni-05_Donna').measures(1, 10)
        #score = corpus.parse('bach/bwv846').measures(1, 19)
        #score = corpus.parse('bach/bwv66.6')
        #score = corpus.parse('beethoven/opus18no1', 2).measures(1, 30)
        #score = corpus.parse('beethoven/opus18no1', 2).measures(1, 8)
        #score = corpus.parse('PMFC_06_Giovanni-05_Donna').measures(90, 118)
        #score = corpus.parse('PMFC_06_Piero_1').measures(1, 10)
        #score = corpus.parse('PMFC_06-Jacopo').measures(1, 30)
        #score = corpus.parse('PMFC_12_13').measures(1, 40)
        #score = corpus.parse('monteverdi/madrigal.4.16.xml').measures(1, 8)

        chordReducer = ChordReducer()
        reduction = chordReducer.run(
            score,
            allowableChords=(
                chord.Chord("F#4 A4 C5"),
                ),
            closedPosition=True,
            forbiddenChords=None,
            maximumNumberOfChords=3,
            )

        for part in reduction:
            score.insert(0, part)

        score.show()


#------------------------------------------------------------------------------
# define presented order in documentation

_DOC_ORDER = []

if __name__ == "__main__":
    #TestExternal().testTrecentoMadrigal()
    import music21
    music21.mainTest(TestExternal)
