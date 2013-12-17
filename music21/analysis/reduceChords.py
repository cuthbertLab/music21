# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         reduceChords.py
# Purpose:      Tools for eliminating passing chords, etc.
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2013 Michael Scott Cuthbert and the music21 Project
# License:      LGPL, see license.txt
#------------------------------------------------------------------------------

'''
Automatically reduce a MeasureStack to a single chord or group of chords.
'''

import unittest
import copy
from music21 import chord
from music21 import meter
from music21 import note
from music21 import stream
from music21 import tie
from music21 import environment

environLocal = environment.Environment('reduceChords')


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
    from music21 import chord
    measure = stream.Measure()
    timeSignature = meter.TimeSignature('4/4')
    chord1 = chord.Chord('C4 E4 G4 C5')
    chord1.quarterLength = 2.0
    chord2 = chord.Chord('C4 E4 F4 B4')
    chord3 = chord.Chord('C4 E4 G4 C5')
    for element in (timeSignature, chord1, chord2, chord3):
        measure.append(element)
    return measure


class Verticality(object):

    ### CLASS VARIABLES ###

    __slots__ = (
        '_overlapElements',
        '_startElements',
        )

    ### INITIALIZER ###

    def __init__(
        self,
        startElements={},
        overlapElements=None,
        ):
        assert isinstance(startElements, dict) and startElements
        assert isinstance(overlapElements, (dict, type(None)))
        self._startElements = startElements
        self._overlapElements = overlapElements or {}

    ### PUBLIC METHODS ###

    @staticmethod
    def iterateVerticalities(expr):
        '''
        Iterate overlapping elements:

        ::

            >>> score = corpus.parse('PMFC_06_Giovanni-05_Donna')
            >>> for i in range(1, 5):
            ...     measure = score.measure(i)
            ...     print 'Measure {}:'.format(i)
            ...     verticalities = analysis.reduceChords.Verticality.iterateVerticalities(measure)
            ...     for j, verticality in enumerate(verticalities):
            ...         print '\tVerticality {}:'.format(j)
            ...         print '\t\tOld:', verticality.overlapElements
            ...         print '\t\tNew:', verticality.startElements
            ...
            Measure 1:
                Verticality 0:
                    Old: {}
                    New: {0: <music21.note.Note D>, 1: <music21.note.Note G>}
            Measure 2:
                Verticality 0:
                    Old: {}
                    New: {0: <music21.note.Note D>, 1: <music21.note.Note G>}
                Verticality 1:
                    Old: {1: <music21.note.Note G>}
                    New: {0: <music21.note.Note C>}
            Measure 3:
                Verticality 0:
                    Old: {}
                    New: {0: <music21.note.Note B>, 1: <music21.note.Note G>}
            Measure 4:
                Verticality 0:
                    Old: {}
                    New: {0: <music21.note.Note B>, 1: <music21.note.Note G>}
                Verticality 1:
                    Old: {1: <music21.note.Note G>}
                    New: {0: <music21.note.Note B>}
                Verticality 2:
                    Old: {1: <music21.note.Note G>}
                    New: {0: <music21.note.Note C>}

        '''
        leafLists = []
        for part in expr:
            innerMeasure = part.getElementsByClass('Measure')[0]
            leaves = innerMeasure.notesAndRests
            leafLists.append(leaves)
        currentIndices = [0 for _ in leafLists]
        currentStartOffset = None
        earliestStopOffset = None
        latestStopOffset = None
        for i, index in enumerate(currentIndices):
            leaf = leafLists[i][index]
            startOffset = leaf.offset
            stopOffset = leaf.offset + leaf.quarterLength
            if currentStartOffset is None or startOffset < currentStartOffset:
                currentStartOffset = startOffset
            if earliestStopOffset is None or stopOffset < earliestStopOffset:
                earliestStopOffset = stopOffset
            if latestStopOffset is None or latestStopOffset < stopOffset:
                latestStopOffset = stopOffset
        overlapElements = {}
        startElements = {}
        for j, pair in enumerate(zip(leafLists, currentIndices)):
            leaves, i = pair
            leaf = leaves[i]
            if leaf.offset == currentStartOffset:
                startElements[j] = leaf
            else:
                overlapElements[j] = leaf
        yield Verticality(
            startElements=startElements,
            overlapElements=overlapElements,
            )
        while True:
            indexIsLast = []
            for i, index in enumerate(currentIndices):
                if (index + 1) == len(leafLists[i]):
                    indexIsLast.append(True)
                    continue
                indexIsLast.append(False)
                thisLeaf = leafLists[i][index]
                nextLeaf = leafLists[i][index + 1]
                if nextLeaf.offset == earliestStopOffset:
                    currentIndices[i] = index + 1
            currentStartOffset = earliestStopOffset
            earliestStopOffset = None
            for i, index in enumerate(currentIndices):
                thisLeaf = leafLists[i][index]
                stopOffset = thisLeaf.offset + thisLeaf.quarterLength
                if latestStopOffset < stopOffset:
                    latestStopOffset = stopOffset
                if earliestStopOffset is None or \
                    stopOffset < earliestStopOffset:
                    earliestStopOffset = stopOffset
            if all(indexIsLast):
                break
            overlapElements = {}
            startElements = {}
            for j, pair in enumerate(zip(leafLists, currentIndices)):
                leaves, i = pair
                leaf = leaves[i]
                if leaf.offset == currentStartOffset:
                    startElements[j] = leaf
                else:
                    overlapElements[j] = leaf
            yield Verticality(
                startElements=startElements,
                overlapElements=overlapElements,
                )
        raise StopIteration

    @staticmethod
    def iterateVerticalitiesNwise(expr, n=2):
        verticalities = tuple(Verticality.iterateVerticalities(expr))
        if len(verticalities) < n:
            yield verticalities
        else:
            verticalityBuffer = []
            for verticality in expr:
                verticalityBuffer.append(verticality)
                if len(verticalityBuffer) == n:
                    yield tuple(verticalityBuffer)
                    verticalityBuffer.pop(0)

    ### PUBLIC PROPERTIES ###

    @property
    def elements(self):
        return self.startElements.values() + self.overlapElements.values()

    @property
    def overlapElements(self):
        return self._overlapElements

    @property
    def startElements(self):
        return self._startElements

    @property
    def startOffset(self):
        return self._startElements.values()[0].offset

    @property
    def earliestStartOffset(self):
        if self.overlapElements:
            return min(x.offset for x in self.overlapElements.values())
        return self.startOffset

    @property
    def earliestStopOffset(self):
        return min(x.offset + x.quarterLength for x in self.elements)

    @property
    def latestStopOffset(self):
        return max(x.offset + x.quarterLength for x in self.elements)


class ChordReducer(object):
    r'''
    A chord reducer.
    '''

    ### INITIALIZER ###

    def __init__(self):
        self.printDebug = False
        self.weightAlgorithm = self.qlbsmpConsonance
        self.maxChords = 3

    ### PRIVATE METHODS ###

    def _alignByLyrics(self, inputMeasure):
        reallignments = []
        for verticality in Verticality.iterateVerticalities(inputMeasure):
            elements = verticality.elements
            if not all(x.hasLyrics() for x in elements):
                continue
            if not len(set(x.lyric for x in elements)) == 1:
                continue
            bestBeatStrength = elements[0].beatStrength
            bestOffset = elements[0].offset
            for x in elements[1:]:
                if bestBeatStrength < x.beatStrength:
                    bestBeatStrength = x.beatStrength
                    bestOffset = x.offset
            for x in elements:
                if x.beatStrength != bestBeatStrength:
                    reallignments.append((x, bestOffset))
        for element, newOffset in reallignments:
            if isinstance(element, note.Rest):
                continue
            oldOffset = element.offset
            for site in element.sites.getSites():
                element.sites.setOffsetBySite(site, newOffset)
            element.quarterLength += (oldOffset - newOffset)
            element.offset = newOffset

    def _buildOutputMeasure(self,
        closedPosition,
        forceOctave,
        i,
        inputMeasure,
        inputMeasureReduction,
        lastPitchedObject,
        lastTimeSignature,
        ):
        outputMeasure = stream.Measure()
        outputMeasure.number = i
        #inputMeasureReduction.show('text')
        cLast = None
        cLastEnd = 0.0
        for cEl in inputMeasureReduction:
            cElCopy = copy.deepcopy(cEl)
            if 'Chord' in cEl.classes:
                if closedPosition is not False:
                    if forceOctave is not False:
                        cElCopy.closedPosition(
                            forceOctave=forceOctave,
                            inPlace=True,
                            )
                    else:
                        cElCopy.closedPosition(inPlace=True)
                    cElCopy.removeRedundantPitches(inPlace=True)
            newOffset = cEl.getOffsetBySite(inputMeasureReduction)
            # extend over gaps
            if cLast is not None:
                if round(newOffset - cLastEnd, 6) != 0.0:
                    cLast.quarterLength += newOffset - cLastEnd
            cLast = cElCopy
            cLastEnd = newOffset + cElCopy.quarterLength
            outputMeasure._insertCore(newOffset, cElCopy)
        tsContext = inputMeasure.getContextByClass('TimeSignature')
        #tsContext = inputMeasure.parts[0].getContextByClass('TimeSignature')
        if tsContext is not None:
            if round(tsContext.barDuration.quarterLength - cLastEnd, 6) != 0.0:
                cLast.quarterLength += tsContext.barDuration.quarterLength - cLastEnd
        outputMeasure._elementsChanged()
        # add ties
        if lastPitchedObject is not None:
            firstPitched = outputMeasure[0]
            if lastPitchedObject.isNote and firstPitched.isNote:
                if lastPitchedObject.pitch == firstPitched.pitch:
                    lastPitchedObject.tie = tie.Tie("start")
            elif lastPitchedObject.isChord and firstPitched.isChord:
                if len(lastPitchedObject) == len(firstPitched):
                    allSame = True
                    for pitchI in range(len(lastPitchedObject)):
                        if lastPitchedObject.pitches[pitchI] != firstPitched.pitches[pitchI]:
                            allSame = False
                    if allSame is True:
                        lastPitchedObject.tie = tie.Tie('start')
        lastPitchedObject = outputMeasure[-1]
        #sourceMeasureTs = inputMeasure.parts[0].getElementsByClass('Measure')[0].timeSignature
        sourceMeasureTs = tsContext
        if sourceMeasureTs != lastTimeSignature:
            outputMeasure.timeSignature = copy.deepcopy(sourceMeasureTs)
            lastTimeSignature = sourceMeasureTs
        return lastPitchedObject, lastTimeSignature, outputMeasure

    def _collapseArpeggios(self, inputMeasure):
        if not len(inputMeasure):
            return inputStream
        newStream = stream.Stream()
        currentChords = []
        currentPitches = set()
        for currentChord in inputMeasure:
            if currentChord.isRest:
                currentChords = []
                currentPitches = set()
                newStream.append(currentChord)
                continue
            tieSet = self._getTieSet(currentChord)
            if not tieSet:
                currentChords = []
                currentPitches = set()
                newStream.append(currentChord)
            elif all(x == 'stop' for x in tieSet):
                currentChords.append(currentChord)
                currentPitches.update(currentChord.pitchNames)
                newChord = chord.Chord(currentPitches)
                newChord.quarterLength = \
                    sum(x.quarterLength for x in currentChords)
                if newChord.isTriad() or \
                    newChord.isSeventh() or \
                    newChord.isConsonant():
                    newStream.append(newChord)
                else:
                    for oldChord in currentChords:
                        newStream.append(oldChord)
                currentChords = []
                currentPitches = set()
            else:
                currentChords.append(currentChord)
                currentPitches.update(currentChord.pitchNames)
        if currentChords:
            newChord = chord.Chord(currentPitches)
            newChord.quarterLength = \
                sum(x.quarterLength for x in currentChords)
            if newChord.isTriad() or \
                newChord.isSeventh() or \
                newChord.isConsonant():
                newStream.append(currentChord)
            else:
                for oldChord in currentChords:
                    newStream.append(oldChord)
        return newStream

    def _collapseIdenticalChords(self, inputMeasure):
        if not len(inputMeasure):
            return inputMeasure
        outputMeasure = stream.Stream()
        if not inputMeasure[0].isRest:
            previousChord = chord.Chord(set(inputMeasure[0].pitchNames))
            previousChord.quarterLength = inputMeasure[0].quarterLength
        else:
            previousChord = inputMeasure[0]
        for currentChord in inputMeasure[1:]:
            if previousChord.isChord and currentChord.isChord:
                previousPitches = set(previousChord.pitchNames)
                currentPitches = set(currentChord.pitchNames)
                if previousPitches == currentPitches:
                    previousChord.quarterLength += currentChord.quarterLength
                else:
                    outputMeasure.append(previousChord)
                    previousChord = chord.Chord(set(currentChord.pitchNames))
                    previousChord.quarterLength = currentChord.quarterLength
            else:
                outputMeasure.append(previousChord)
                if currentChord.isChord:
                    previousChord = chord.Chord(set(currentChord.pitchNames))
                    previousChord.quarterLength = currentChord.quarterLength
                else:
                    previousChord = currentChord
        outputMeasure.append(previousChord)
        return outputMeasure

    def _getTieSet(self, chord):
        result = set()
        for note in chord._notes:
            if note.tie is not None:
                result.add(note.tie.type)
        return result

    ### PUBLIC METHODS ###

    def computeMeasureChordWeights(self, measureObj, weightAlgorithm=None):
        '''
        Compute measure chord weights:

        ::

            >>> s = analysis.reduceChords.testMeasureStream1().notes
            >>> cr = analysis.reduceChords.ChordReducer()
            >>> cws = cr.computeMeasureChordWeights(s)
            >>> for pcs in sorted(cws):
            ...     print "%18r  %2.1f" % (pcs, cws[pcs])
                (0, 4, 7)  3.0
            (0, 11, 4, 5)  1.0

        Add beatStrength:

        ::

            >>> cws = cr.computeMeasureChordWeights(s,
            ...     weightAlgorithm=cr.quarterLengthBeatStrength)
            >>> for pcs in sorted(cws):
            ...     print "%18r  %2.1f" % (pcs, cws[pcs])
                (0, 4, 7)  2.2
            (0, 11, 4, 5)  0.5

        Give extra weight to the last element in a measure:

        ::

            >>> cws = cr.computeMeasureChordWeights(s,
            ...     weightAlgorithm=cr.quarterLengthBeatStrengthMeasurePosition)
            >>> for pcs in sorted(cws):
            ...     print "%18r  %2.1f" % (pcs, cws[pcs])
                (0, 4, 7)  3.0
            (0, 11, 4, 5)  0.5

        Make consonance count a lot:

        >>> cws = cr.computeMeasureChordWeights(s,
        ...     weightAlgorithm=cr.qlbsmpConsonance)
        >>> for pcs in sorted(cws):
        ...     print "%18r  %2.1f" % (pcs, cws[pcs])
             (0, 4, 7)  3.0
         (0, 11, 4, 5)  0.1
        '''
        if weightAlgorithm is None:
            weightAlgorithm = self.quarterLengthOnly
        presentPCs = {}
        self.positionInMeasure = 0
        self.numberOfElementsInMeasure = len(measureObj)
        for i, c in enumerate(measureObj):
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

    def multiPartReduction(
        self,
        inputStream,
        maxChords=2,
        alignLyrics=False,
        closedPosition=False,
        collapseArpeggios=False,
        collapseIdenticalChords=False,
        forceOctave=False,
        ):
        '''
        Return a multipart reduction of a stream.
        '''
        i = 0
        outputStream = stream.Part()
        allMeasures = inputStream.parts[0].getElementsByClass('Measure')
        measureCount = len(allMeasures)
        lastPitchedObject = None
        lastTimeSignature = None
        while i <= measureCount:
            inputMeasure = inputStream.measure(i, ignoreNumbers=True)
            if not len(inputMeasure.flat.notesAndRests):
                if not i:
                    pass
                else:
                    break
            else:
                environLocal.printDebug(str(i))
                inputMeasure = copy.deepcopy(inputMeasure)
                if alignLyrics:
                    self._alignByLyrics(inputMeasure)

                inputMeasureReduction = \
                    inputMeasure.chordify().flat.notesAndRests
                if collapseArpeggios:
                    #print 'Chordify:'
                    #inputMeasureReduction.show('text')

                    #print 'Collapse Arpeggios:'
                    inputMeasureReduction = self._collapseArpeggios(
                        inputMeasureReduction)
                    #inputMeasureReduction.show('text')

                if collapseIdenticalChords:
                    #print 'Collapse Identical Chords:'
                    inputMeasureReduction = self._collapseIdenticalChords(
                        inputMeasureReduction)
                    #inputMeasureReduction.show('text')

#                print 'Reduce to N Chords:'
#                inputMeasureReduction = self.reduceMeasureToNChords(
#                    chordifiedInputMeasure,
#                    maxChords,
#                    weightAlgorithm=self.qlbsmpConsonance,
#                    trimBelow=0.3,
#                    )
#                inputMeasureReduction.show('text')
#                print

                lastPitchedObject, lastTimeSignature, outputMeasure = \
                    self._buildOutputMeasure(
                        closedPosition,
                        forceOctave,
                        i,
                        inputMeasure,
                        inputMeasureReduction,
                        lastPitchedObject,
                        lastTimeSignature,
                        )
                outputStream._appendCore(outputMeasure)
            if self.printDebug:
                print i, " ",
                if i % 20 == 0 and i != 0:
                    print ""
            i += 1
        outputStream._elementsChanged()
        outputStream.getElementsByClass('Measure')[0].insert(
            0, outputStream.bestClef(allowTreble8vb=True))
        #outputStream.makeNotation(inPlace=True)
        return outputStream

    def qlbsmpConsonance(self, c):
        '''
        Everything from before plus consonance
        '''
        consonanceScore = 1.0 if c.isConsonant() else 0.1
        if self.positionInMeasure == self.numberOfElementsInMeasure - 1:
            return c.quarterLength * consonanceScore  # call beatStrength 1
        return self.quarterLengthBeatStrengthMeasurePosition(c) * consonanceScore

    def quarterLengthBeatStrength(self, c):
        return c.quarterLength * c.beatStrength

    def quarterLengthBeatStrengthMeasurePosition(self, c):
        if self.positionInMeasure == self.numberOfElementsInMeasure - 1:
            return c.quarterLength  # call beatStrength 1
        else:
            return self.quarterLengthBeatStrength(c)

    def quarterLengthOnly(self, c):
        return c.quarterLength

    def reduceMeasureToNChords(
        self,
        measureObj,
        numChords=1,
        weightAlgorithm=None,
        trimBelow=0.25,
        ):
        '''
        Reduces measure to `n` chords:

        ::

            >>> s = analysis.reduceChords.testMeasureStream1()
            >>> cr = analysis.reduceChords.ChordReducer()

        Reduce to a maximum of 3 chords; though here we will only get one
        because the other chord is below the trimBelow threshold.

        ::

            >>> newS = cr.reduceMeasureToNChords(s, 3,
            ...     weightAlgorithm=cr.qlbsmpConsonance,
            ...     trimBelow=0.3)
            >>> newS.show('text')
            {0.0} <music21.chord.Chord C4 E4 G4 C5>

        ::

            >>> newS[0].quarterLength
            4.0

        '''
        from music21 import note
        if measureObj.isFlat is False:
            mObj = measureObj.flat.notes
        else:
            mObj = measureObj.notes

        chordWeights = self.computeMeasureChordWeights(mObj, weightAlgorithm)

        if numChords > len(chordWeights):
            numChords = len(chordWeights)

        sortedChordWeights = sorted(chordWeights, key=chordWeights.get, reverse=True)
        maxNChords = sortedChordWeights[:numChords]
        if len(maxNChords) == 0:
            r = note.Rest()
            r.quarterLength = mObj.duration.quarterLength
            for c in mObj:
                mObj.remove(c)
            mObj.insert(0, r)
            return mObj
        maxChordWeight = chordWeights[maxNChords[0]]

        trimmedMaxChords = []
        for pcTuples in maxNChords:
            if chordWeights[pcTuples] >= maxChordWeight * trimBelow:
                trimmedMaxChords.append(pcTuples)
                #print chordWeights[pcTuples], maxChordWeight
            else:
                break

        currentGreedyChord = None
        currentGreedyChordPCs = None
        currentGreedyChordNewLength = 0.0
        for c in mObj:
            if c.isNote:
                p = tuple(c.pitch.pitchClass)
            else:
                p = tuple(set([x.pitchClass for x in c.pitches]))
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
                    n.tie = None
                    if n.pitch.accidental is not None:
                        n.pitch.accidental.displayStatus = None
                currentGreedyChordPCs = p
                currentGreedyChordNewLength += c.quarterLength
            else:
                currentGreedyChordNewLength += c.quarterLength
                mObj.remove(c)
        if currentGreedyChord is not None:
            currentGreedyChord.quarterLength = currentGreedyChordNewLength
            currentGreedyChordNewLength = 0.0

        # even chord lengths...
        for i in range(1, len(mObj)):
            c = mObj[i]
            cOffsetCurrent = c.offset
            cOffsetSyncop = cOffsetCurrent - int(cOffsetCurrent)
            if round(cOffsetSyncop, 3) in [0.250, 0.125, 0.333, 0.063, 0.062]:
                lastC = mObj[i - 1]
                lastC.quarterLength -= cOffsetSyncop
                c.offset = int(cOffsetCurrent)
                c.quarterLength += cOffsetSyncop

        return mObj


#------------------------------------------------------------------------------


class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testSimpleMeasure(self):
        from music21 import chord
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
        #score = corpus.parse('bach/bwv846').measures(1, 19)
        #score = corpus.parse('beethoven/opus18no1', 2).measures(1, 3)
        #score = corpus.parse('beethoven/opus18no1', 2).measures(1, 19)
        score = corpus.parse('PMFC_06_Giovanni-05_Donna').measures(1, 30)
        #score = corpus.parse('PMFC_06_Giovanni-05_Donna').measures(90, 118)
        #score = corpus.parse('PMFC_06_Piero_1').measures(1, 10)
        #score = corpus.parse('PMFC_06-Jacopo').measures(1, 30)
        #score = corpus.parse('PMFC_12_13').measures(1, 40)

        # fix clef
        fixClef = False
        if fixClef:
            from music21 import clef
            firstMeasure = score.parts[1].getElementsByClass('Measure')[0]
            startClefs = firstMeasure.getElementsByClass('Clef')
            if len(startClefs):
                clef1 = startClefs[0]
                firstMeasure.remove(clef1)
            firstMeasure.insert(0, clef.Treble8vbClef())

        chordReducer = ChordReducer()
        #chordReducer.printDebug = True
        reduction = chordReducer.multiPartReduction(
            score,
            alignLyrics=True,
            closedPosition=True,
            collapseArpeggios=True,
            collapseIdenticalChords=True,
            maxChords=3,
            )
        #reduction = chordReducer.multiPartReduction(
        #    score,
        #    closedPosition=True,
        #    )
        score.insert(0, reduction)
        score.show()


#------------------------------------------------------------------------------
# define presented order in documentation

_DOC_ORDER = []

if __name__ == "__main__":
    #TestExternal().testTrecentoMadrigal()
    import music21
    music21.mainTest(TestExternal)
