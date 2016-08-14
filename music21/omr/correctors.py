# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         omr/correctors.py
# Purpose:      music21 modules for correcting the output from OMR software
#
# Authors:      Maura Church
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2014 Maura Church, Michael Scott Cuthbert, and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
import math
import difflib
import copy
import collections

import os
import inspect

pathName = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

K525omrFilePath = pathName + os.sep + 'k525OMRMvt1.xml'
K525groundTruthFilePath = pathName + os.sep + 'k525GTMvt1.xml'
K525omrShortPath = pathName + os.sep + 'k525OMRshort.xml'
K525groundTruthShortPath = pathName + os.sep + 'k525GTshort.xml'

debug = False

MeasureRelationship = collections.namedtuple('MeasureRelationship', 
                                             ['flaggedMeasurePart', 'flaggedMeasureIndex',
                                              'correctMeasurePart', 'correctMeasureIndex',
                                              'correctionProbability'])
PriorsIntegrationScore = collections.namedtuple('PriorsIntegrationScore', 
                                                ['total', 'horizontal', 'vertical', 'ignored'])

class ScoreCorrector(object):
    '''
    takes in a music21.stream.Score object and runs OMR correction on it.    
    '''
    def __init__(self, score=None):
        self.score = score
        self.singleParts = []
        self.measureSlices = []
        self.distributionArray = None
        for p in range(len(score.parts)):
            self.singleParts.append(self.getSinglePart(p))
            #this is an array of SinglePart objects
    def run(self):
        '''
        Run all known models for OMR correction on
        this score
        '''
        return self.runPriorModel()
    
    def runPriorModel(self):
        '''
        run the horizontal and vertical correction models
        on the score.  Returns the new self.score object.
        '''
        correctingArrayHorizontalAllParts = self.runHorizontalCorrectionModel()
        correctingArrayVerticalAllParts = self.runVerticalCorrectionModel()
        self.generateCorrectedScore(correctingArrayHorizontalAllParts,
                                   correctingArrayVerticalAllParts)
        return self.score
    
    def getAllHashes(self):
        '''
        Returns an array of arrays, each of which is the hashed notes for a part
                
        >>> p1 = stream.Part()
        >>> p1.insert(0, meter.TimeSignature('4/4'))
        >>> p1.append(note.Note('C', type = 'half'))
        >>> p1.append(note.Rest(type='half'))
        >>> p1.append(note.Note('C', type = 'half'))
        >>> p1.append(note.Rest(type='half'))
        >>> p1.makeMeasures(inPlace = True)
        >>> p2 = stream.Part()
        >>> p2.insert(0, meter.TimeSignature('4/4'))
        >>> p2.repeatAppend(note.Note('C', type = 'quarter'), 8)
        >>> p2.makeMeasures(inPlace = True)
        >>> s = stream.Score()
        >>> s.insert(0, p1)
        >>> s.insert(0, p2)
        >>> ss = omr.correctors.ScoreCorrector(s)
        >>> ss.getAllHashes()
        [['Z[', 'Z['], ['PPPP', 'PPPP']]
        '''
        allPartsHashes = []
        for p in self.singleParts:
            allPartsHashes.append(p.hashedNotes)
        return allPartsHashes
    
    def getSinglePart(self, pn):
        '''
        returns a NEW SinglePart object for part number pn from the score

        '''
        
        return SinglePart(self.score.parts[pn], pn)

    def runHorizontalCorrectionModel(self):
        '''
        runs for sp in self.singleParts:
            sp.runHorizontalCorrectionModel()
            
        returns correctingArrayAllParts
        '''
        correctingArrayAllParts = []
        for sp in self.singleParts:
            correctingArrayOnePart = sp.runHorizontalCorrectionModel() 
            correctingArrayAllParts.append(correctingArrayOnePart)
        return correctingArrayAllParts
    
    def getMeasureSlice(self, i):
        '''
        Given an index, i, returns a MeasureSlice object at that index
        
        >>> omrPath = omr.correctors.K525omrShortPath
        >>> omrScore = converter.parse(omrPath)
        >>> ssOMR = omr.correctors.ScoreCorrector(omrScore)
        >>> ssOMR.getMeasureSlice(4)
        <music21.omr.correctors.MeasureSlice object at 0x...>
        '''
        try:
            ms = self.measureSlices[i]
            if ms == 0:
                raise IndexError("nope...")
        except IndexError:
            ms = MeasureSlice(self,i)
            if i >= len(self.measureSlices):
                self.measureSlices.extend(0 for _ in range(len(self.measureSlices), i + 1))
            self.measureSlices[i] = ms
            vpd = self.verticalProbabilityDist()
            ms.allProbabilities = vpd
        return ms
    
    def getAllIncorrectMeasures(self):
        '''
        Returns an array of the incorrect measure indices arrays for each part.
        This is used in the MeasureSlice object to make sure we're not comparing a flagged
        measure to other flagged measures in its slice
        
        >>> omrPath = omr.correctors.K525omrShortPath
        >>> omrScore = converter.parse(omrPath)
        >>> ssOMR = omr.correctors.ScoreCorrector(omrScore)
        >>> ssOMR
        <music21.omr.correctors.ScoreCorrector object at 0x...>
        >>> ssOMR.getAllIncorrectMeasures()
        [[1, 3, 9, 10, 12, 17, 20], [2, 12, 14, 17], [1, 9], []]
        '''
        allPartsIncorrectMeasures = []
        for p in range(len(self.singleParts)):
            im = self.singleParts[p].incorrectMeasures
            allPartsIncorrectMeasures.append(im)
     
        return allPartsIncorrectMeasures
    
    
    def verticalProbabilityDist(self):
        '''
        Uses a score and returns an array of probabilities.
        For n in the array, n is the the probability that the nth part

        '''
        if self.distributionArray is not None:
            return self.distributionArray
        distributionArray = []
        numberOfParts = len(self.singleParts)
        for i in range(numberOfParts):
            distributionArray.append(self.getVerticalProbabilityDistributionSinglePart(i))
        self.distributionArray = distributionArray
        return distributionArray

    def getVerticalProbabilityDistributionSinglePart(self, pn):
        '''
        Returns the Vertical Probability Distribution (PrP) for a single part.
        
        Get the Priors for the Violin II part (first 20 measures only)
        
        >>> omrPath = omr.correctors.K525omrShortPath
        >>> omrScore = converter.parse(omrPath)
        >>> ssOMR = omr.correctors.ScoreCorrector(omrScore)
        >>> allDists = ssOMR.getVerticalProbabilityDistributionSinglePart(1)
        >>> ["%0.3f" % p for p in allDists]
        ['0.571', '1.000', '0.667', '0.714']
        '''
        i = pn
        numberOfParts = len(self.singleParts)
        partDistArray = [0]*numberOfParts 
        lengthOfScore = len(self.singleParts[i].hashedNotes)
        for k in range(lengthOfScore):
            measureDistArray = self.getVerticalProbabilityDistributionSinglePartSingleMeasure(i, k)
            for l in range(numberOfParts):
                partDistArray[l] += measureDistArray[l]
        normalizedPartDistArray = [x/lengthOfScore for x in partDistArray]
        return normalizedPartDistArray

    def getVerticalProbabilityDistributionSinglePartSingleMeasure(self, pn, measureIndex):
        i = pn
        k = measureIndex
        numberOfParts = len(self.singleParts)
        mh = MeasureHash(self.singleParts[i].measureStream[k]) 
        measureDistArray = [0]*numberOfParts
        mh.setSequenceMatcher(self.singleParts[i].hashedNotes[k])
        for l in range(numberOfParts):
            if l == i:
                measureDistArray[l] = 1.0
                #put a huge placeholder in for the incorrect measures to keep indices consistent
            else:
                measureDifference = mh.getMeasureDifference(self.singleParts[l].hashedNotes[k])
                if measureDifference == 1.0:
                    measureDistArray[l] = 1.0
                else:
                    measureDistArray[l] = 0.0
        return measureDistArray

    def runVerticalSearch(self, i, pn):
        '''
        Returns an array of the minimum distance measure indices
        given a measure (with index i) within a part pn to compare to 
        '''      
        ms = self.getMeasureSlice(i)
        correctingMeasure = ms.runSliceSearch(pn)
        return correctingMeasure

    def substituteOneMeasureContentsForAnother(self, sourceHorizontalIndex, sourceVerticalIndex, 
                                        destinationHorizontalIndex, destinationVerticalIndex):
        '''
        Takes a destination measure, deletes its contents, and replaces them 
        with the contents of a source measure but retains as many pitches as possible
        
        The destination measure would normally be in the set F of flagged measures 
        (having an incorrect number of beats)
        while the source measure is in the set C of correcting measures. 
        
        >>> s = corpus.parse('bwv66.6').measures(1,2)
        >>> s.show('text')
        {0.0} <music21.stream.Part Soprano>
            ...
            {0.0} <music21.stream.Measure 1 offset=0.0>
                {0.0} <music21.note.Note A>
                {1.0} <music21.note.Note B>
                {2.0} <music21.note.Note C#>
                {3.0} <music21.note.Note E>
            {4.0} <music21.stream.Measure 2 offset=4.0>
                {0.0} <music21.note.Note C#>
                {1.0} <music21.note.Note B>
                {2.0} <music21.note.Note A>
                {3.0} <music21.note.Note C#>
        {0.0} <music21.stream.Part Alto>
             ...
            {0.0} <music21.stream.Measure 1 offset=0.0>
                {0.0} <music21.note.Note F#>
                {1.0} <music21.note.Note E>
                {2.0} <music21.note.Note E>
                {3.0} <music21.note.Note E>
            {4.0} <music21.stream.Measure 2 offset=4.0>
                {0.0} <music21.note.Note E>
                {0.5} <music21.note.Note A>
                {1.0} <music21.note.Note G#>
                {2.0} <music21.note.Note E>
                {3.0} <music21.note.Note G#>
        ...

        Replace part 1, measure 2 (index 1) with part 0, measure 1 (index 0) while retaining
        as many pitches as possible. The eighth-notes will become quarters:
        
        >>> scOMR = omr.correctors.ScoreCorrector(s)
        >>> scOMR.substituteOneMeasureContentsForAnother(0, 0, 1, 1)
        >>> s2 = scOMR.score
        >>> s2.show('text')
        {0.0} <music21.stream.Part Soprano>
            ...
            {0.0} <music21.stream.Measure 1 offset=0.0>
                {0.0} <music21.note.Note A>
                {1.0} <music21.note.Note B>
                {2.0} <music21.note.Note C#>
                {3.0} <music21.note.Note E>
            {4.0} <music21.stream.Measure 2 offset=4.0>
                {0.0} <music21.note.Note C#>
                {1.0} <music21.note.Note B>
                {2.0} <music21.note.Note A>
                {3.0} <music21.note.Note C#>
        {0.0} <music21.stream.Part Alto>
             ...
            {0.0} <music21.stream.Measure 1 offset=0.0>
                {0.0} <music21.note.Note F#>
                {1.0} <music21.note.Note E>
                {2.0} <music21.note.Note E>
                {3.0} <music21.note.Note E>
            {4.0} <music21.stream.Measure 2 offset=4.0>
                {0.0} <music21.note.Note E>
                {1.0} <music21.note.Note A>
                {2.0} <music21.note.Note G#>
                {3.0} <music21.note.Note E>
        ...
        '''      

        # Measure object
        incorrectMeasure = (
            self.singleParts[destinationVerticalIndex].measureStream[destinationHorizontalIndex]) 
        # Measure object     
        correctMeasure = self.singleParts[sourceVerticalIndex].measureStream[sourceHorizontalIndex] 
        oldNotePitches = [n.pitch for n in incorrectMeasure.getElementsByClass("Note")]
        for el in incorrectMeasure.elements:
            incorrectMeasure.remove(el)   
             
        pitchIndex = 0
        for el in correctMeasure:
            newEl = copy.deepcopy(el)
            try:
                if "Note" in newEl.classes:
                    oldPitch = oldNotePitches[pitchIndex]
                    newEl.pitch.octave = oldPitch.octave
                    newEl.pitch.name = oldPitch.name
                    pitchIndex += 1
            except IndexError:
                pass
            incorrectMeasure.append(newEl) 
                               
    def runVerticalCorrectionModel(self): 
        '''
        Runs a basic vertical correction model on a ScoreCorrector object.
        That is, for each flagged measure, this method replaces the rhythm in that flagged measure
        with the rhythm of a measure with the least difference. 
        '''
        unused_allProbabilities = self.verticalProbabilityDist()
        correctingMeasuresAllParts =[]
        for p in range(len(self.singleParts)):
            correctingMeasuresOnePart = []
            im = self.singleParts[p].incorrectMeasures
            for i in range(len(im)):
                incorrectMeasureIndex = im[i]
                correctingMeasure = self.runVerticalSearch(incorrectMeasureIndex,p)
                correctingMeasuresOnePart.append(correctingMeasure)
            correctingMeasuresAllParts.append(correctingMeasuresOnePart)
        return correctingMeasuresAllParts

    def generateCorrectedScore(self, horizontalArray, verticalArray):
        '''
        Given two correcting arrays (one from the horizontal model and one from 
        the vertical model),
        which offer source measures for each flagged measure in each part, 
        this method compares the probabilities of proposed 
        source measures for each flagged measure,
        and replaces the flagged measures contents with the more probable source measure
        using substituteOneMeasureContentsForAnother.
        It then rehashes the score so that a new difference comparison can be run.
        
        Returns a collections.namedtuple of the total number of flagged measures, the total number
        corrected by the horizontal (Prior based on Distance) and the 
        vertical (Prior based on Parts)
        methods.
        '''
        totalFlagged = 0
        totalHorizontal = 0
        totalVertical = 0
        totalIgnored = 0
        
        numParts = len(self.singleParts)
        for p in range(numParts):
            for h in range(len(horizontalArray[p])):
                for v in range(len(verticalArray[p])):
                    horizontalTuple = horizontalArray[p][h]
                    verticalTuple = verticalArray[p][v]

                    if horizontalTuple.flaggedMeasurePart != verticalTuple.flaggedMeasurePart:
                        continue
                    if horizontalTuple.flaggedMeasureIndex != verticalTuple.flaggedMeasureIndex:
                        continue
                    

                    destinationHorizontalIndex = horizontalTuple.flaggedMeasureIndex
                    destinationVerticalIndex = horizontalTuple.flaggedMeasurePart
                    
                    totalFlagged += 1
                    #if verticalTuple.correctionProbability == 0.0 and numParts > 2:
                    #    totalIgnored += 1
                    #el
                    if horizontalTuple.correctionProbability > verticalTuple.correctionProbability:
                        totalHorizontal += 1
                        sourceHorizontalIndex = horizontalTuple.correctMeasureIndex
                        sourceVerticalIndex = horizontalTuple.correctMeasurePart
                        self.substituteOneMeasureContentsForAnother(
                                sourceHorizontalIndex, sourceVerticalIndex, 
                                destinationHorizontalIndex, destinationVerticalIndex)
                    else: 
                        # horizontalTuple.correctionProbability <= 
                        #                verticalTuple.correctionProbability:
                        totalVertical += 1
                        sourceHorizontalIndex = verticalTuple.correctMeasureIndex
                        sourceVerticalIndex = verticalTuple.correctMeasurePart
                        self.substituteOneMeasureContentsForAnother(
                                sourceHorizontalIndex, sourceVerticalIndex, 
                                destinationHorizontalIndex, destinationVerticalIndex)
                     
            self.singleParts[p].hashedNotes = (
                            self.singleParts[p].getSequenceHashesFromMeasureStream()    )
        return PriorsIntegrationScore(totalFlagged, totalHorizontal, totalVertical, totalIgnored)

class SinglePart(object):
    def __init__(self, part=None, pn=None):
        self.scorePart = part
        self.partNumber = pn
        self.indexArray = None
        self.probabilityDistribution = None
        self.correctingMeasure = None
        if part is not None:
            self.measureStream = self.getMeasures()
            self.hashedNotes = self.getSequenceHashesFromMeasureStream()
            self.incorrectMeasures = self.getIncorrectMeasureIndices(runFast=True)
        else:
            self.measureStream = None
            self.hashedNotes = None
            self.incorrectMeasures = None

    def getMeasures(self):
        self.measureStream = self.scorePart.getElementsByClass('Measure')
    
        return self.measureStream
    

    def getIncorrectMeasureIndices(self, runFast = False):
        '''
        Returns an array of all the measures that OMR software would flag - that is, 
        measures that do 
        not have the correct number of beats given the current time signature
        
        if runFast is True (by default), assumes that the initial TimeSignature 
        is the TimeSignature for the entire piece.
        
        >>> p = stream.Part()
        >>> ts = meter.TimeSignature('6/8')
        >>> m1 = stream.Measure()
        >>> m1.number = 1
        >>> m1.append(ts)
        >>> m1.append(note.Note('C4', quarterLength = 3.0))
        >>> p.append(m1)
        >>> m2 = stream.Measure()
        >>> m2.number = 2
        >>> m2.append(note.Note('C4', quarterLength = 1.5))
        >>> p.append(m2)
        
        >>> sp = omr.correctors.SinglePart(p, pn = 0)
        >>> sp.getIncorrectMeasureIndices()
        [1]
        
        >>> p[1]
        <music21.stream.Measure 2 offset=3.0>
        >>> p[1].insert(0, meter.TimeSignature('3/8'))
        >>> sp.getIncorrectMeasureIndices(runFast=False)
        []
        
        '''
        from music21 import meter
        self.incorrectMeasures = []
        if runFast is True:
            try:
                m = self.measureStream[0]
                ts = m.timeSignature or m.getContextByClass('TimeSignature')
            except IndexError:
                ts = meter.TimeSignature('4/4') 
            if ts is None:
                ts = meter.TimeSignature('4/4')
        for i in range(len(self.measureStream)):
            if runFast is False:
                m = self.measureStream[i]
                ts = m.timeSignature or m.getContextByClass('TimeSignature')
            tsOmr = ts.barDuration.quarterLength
            if self.measureStream[i].duration.quarterLength == tsOmr:
                continue
            else:
                self.incorrectMeasures.append(i)
                #note: these measures are 0 indexed - this differs from measure number
                    
        return self.incorrectMeasures
        #This is an array of indices
    
    def getSequenceHashesFromMeasureStream(self):
        '''
        takes in a measure stream of a part
        returns an array of hashed strings
        '''
        measureStreamNotes = []
        measureStreamMeasures = self.measureStream.getElementsByClass('Measure')
    
        for i in range(len(measureStreamMeasures)):
            mh = MeasureHash(measureStreamMeasures[i])
            myHashedNotes = mh.getHashString()
            measureStreamNotes.append(myHashedNotes)
            
        return measureStreamNotes
    

    def horizontalProbabilityDist(self, regenerate = False):
        '''
        Uses (takes?) an array of hashed measures and returns an array of probabilities.
        For n in the array, n is the the probability that the measure (n-(length of score)) away
        from a flagged measure will offer a rhythmic solution. 
        
        These are the probabilities that, within a part, a measure offers a solution, given its
        distance from a flagged measure.
        '''
        if regenerate is False and self.probabilityDistribution is not None:
            return self.probabilityDistribution
        sizeOfArray = len(self.hashedNotes)*2
        allDistArray = [0]*sizeOfArray
        indexArray = [0]*sizeOfArray
        for i in range(len(self.hashedNotes)):
            mh = MeasureHash(self.measureStream[i])
            mh.setSequenceMatcher(self.hashedNotes[i])
            distArray = []
            for k in range(len(self.hashedNotes)):
                arrayIndex = len(self.hashedNotes)-(i-k)
                indexArray[arrayIndex] = -(i-k)
                if i == k:
                    distArray.append(100)
                    #put a huge placeholder in for the incorrect measures 
                    #to keep indices consistent
                    allDistArray[arrayIndex] = len(self.hashedNotes)
                else:
                    measureDifference = mh.getMeasureDifference(self.hashedNotes[k])
                    if measureDifference == 1.0:
                        distArray.append(1.0)
                        allDistArray[arrayIndex] += 1.0
                    else:
                        distArray.append(0.0)
                        allDistArray[arrayIndex] += 0.0
                
        indexArray.pop(0)
        normalizedDistArray = [x/len(self.hashedNotes) for x in allDistArray]
        normalizedDistArray.pop(0)
        self.probabilityDistribution = normalizedDistArray
        self.indexArray = indexArray
        return self.probabilityDistribution
    

    def runHorizontalSearch(self, i):
        '''
        Returns an array of the indices of the minimum distance measures
        given a measure (with index i) to compare to.
        
        '''
        unused_probabilityDistribution = self.horizontalProbabilityDist()
        incorrectMeasures = self.incorrectMeasures
        incorrectMeasureIndex = incorrectMeasures[i]
        hashedNotesI = self.hashedNotes[incorrectMeasureIndex]
        mh = MeasureHash(self.measureStream[incorrectMeasureIndex])
        mh.setSequenceMatcher(hashedNotesI)
        probabilityArray = []
        for k in range(len(self.hashedNotes)):
            if k in incorrectMeasures:
                probabilityArray.append(0.0)
                #put a huge placeholder in for the incorrect measures to keep indices consistent
            else:
                priorBasedOnChangesProbability = mh.getProbabilityBasedOnChanges(
                                                                        self.hashedNotes[k])
                priorBasedOnDistanceProbability = self.getProbabilityDistribution(k, 
                                                                            incorrectMeasureIndex)
                priorBasedOnChangesAndDistance = (priorBasedOnChangesProbability * 
                                                  priorBasedOnDistanceProbability)
                probabilityArray.append(priorBasedOnChangesAndDistance)   
        
        maximumProbability = max(probabilityArray)
        
        # Minimum distance measures weighting with change probabilities
        maximumProbabilityMeasures = [] 
        for l, m in enumerate(probabilityArray):
            if m == maximumProbability:
                maximumProbabilityMeasures.append(l)
        
        self.correctingMeasure = MeasureRelationship(self.partNumber, incorrectMeasureIndex,
                                            self.partNumber, maximumProbabilityMeasures[0],
                                            maximumProbability)

        return self.correctingMeasure
    

    def runHorizontalCorrectionModel(self):
        '''
        Runs a basic horizontal correction model on a score.
        That is, for each flagged measure, this method replaces the rhythm in that flagged measure
        with the rhythm of a measure with the least difference. 
        '''
        correctingArray = []
        for i in range(len(self.incorrectMeasures)):
            #incorrectMeasureIndex = self.incorrectMeasures[i]
            correctingMeasure = self.runHorizontalSearch(i)
            correctingArray.append(correctingMeasure)
        return correctingArray

    def getProbabilityDistribution(self, sourceIndex, destinationIndex):

        probabilityDistribution = self.probabilityDistribution
        index = (sourceIndex-destinationIndex)+len(self.hashedNotes)-1
        distanceProbability = probabilityDistribution[index]
        distanceProbability = distanceProbability
        
        return distanceProbability
     
class MeasureSlice(object):
    '''
    represents a single measure from all parts
    '''
     
    def __init__(self, score, i):
        self.arrayOfMeasureObjects = []
        self.score = score
        self.index = i
        self.sliceMeasureHashObjects = []
        self.allProbabilities = None
        self.correctingMeasure = None
        # Array of Measure hash objects
        for l in range(len(self.score.singleParts)):
            part = self.score.singleParts[l]
            measures = part.getMeasures()
            self.arrayOfMeasureObjects.append(measures[i])
            #appends a measure object
    
    def getSliceHashes(self):
        '''
        >>> omrPath = omr.correctors.K525omrShortPath
        >>> omrScore = converter.parse(omrPath)
        >>> ssOMR = omr.correctors.ScoreCorrector(omrScore)
        >>> ssOMR
        <music21.omr.correctors.ScoreCorrector object at 0x...>
        >>> measureSlice = ssOMR.getMeasureSlice(2)
        >>> measureSlice
        <music21.omr.correctors.MeasureSlice object at 0x...>
        '''
        
        for l in range(len(self.arrayOfMeasureObjects)):
            mh = MeasureHash(self.arrayOfMeasureObjects[l])
            self.sliceMeasureHashObjects.append(mh)
        return self.sliceMeasureHashObjects
        # do we want to put this method in the init, so that we call
        # it once and it gets both measures and hashes?
        
    def runSliceSearch(self, incorrectPartIndex):
        '''
        Takes in an incorrectPartIndex and returns an array
        of the measure indices within the slice that have the
        maximum probability to correct a given flagged measures.
        
        Returns a namedtuple (MeasureRelationship)
        
        >>> omrPath = omr.correctors.K525omrShortPath
        >>> omrScore = converter.parse(omrPath)
        >>> ssOMR = omr.correctors.ScoreCorrector(omrScore)
        >>> measureSlice = ssOMR.getMeasureSlice(2)
        >>> measureSlice
        <music21.omr.correctors.MeasureSlice object at 0x...>
        >>> measureSlice.runSliceSearch(1)
        MeasureRelationship(flaggedMeasurePart=1, flaggedMeasureIndex=2, 
            correctMeasurePart=3, correctMeasureIndex=2, correctionProbability=0.0054...)
 
        >>> measureSlice = ssOMR.getMeasureSlice(3)
        >>> measureSlice.runSliceSearch(0)
        MeasureRelationship(flaggedMeasurePart=0, 
            flaggedMeasureIndex=3, correctMeasurePart=1, correctMeasureIndex=3, 
            correctionProbability=2.41...e-14)
        '''
        probabilityArray = []
        sliceHashes = self.getSliceHashes()
        allIncorrectMeasures = self.score.getAllIncorrectMeasures()
        mh = sliceHashes[incorrectPartIndex] #Measure Hash Object
        mh.setSequenceMatcher()
        for k in range(len(self.arrayOfMeasureObjects)):
            if k == incorrectPartIndex:
                probabilityArray.append(0.0)
                #put a huge placeholder in for the incorrect measure to keep indices consistent
            elif self.index in allIncorrectMeasures[k]:
                probabilityArray.append(0.0)
                #put a huge placeholder in for any other measures in the measure slice
                #that are flagged  
            else:                  
                hashString = sliceHashes[k].getHashString()
                priorBasedOnChangesProbability = mh.getProbabilityBasedOnChanges(hashString)
                ap = self.allProbabilities
                priorBasedOnVerticalDistanceProbability = ap[incorrectPartIndex][k]
                priorBasedOnChangesAndDistance = (priorBasedOnChangesProbability * 
                                                  priorBasedOnVerticalDistanceProbability)
                probabilityArray.append(priorBasedOnChangesAndDistance)
#           
        maximumProbability = max(probabilityArray)
        maximumProbabilityMeasures = []        
        for l, m in enumerate(probabilityArray):
            if m == maximumProbability:
                maximumProbabilityMeasures.append(l)
        self.correctingMeasure = MeasureRelationship(incorrectPartIndex, self.index,
                                                     maximumProbabilityMeasures[0], self.index,
                                                     maximumProbability)
        
        return self.correctingMeasure  

            
class MeasureHash(object):
    '''
    Able to do a number of matching, substitution and hashing operations on
    a given measure object
    '''
    
    def __init__(self, measureObject = None):
        self.measureObject = measureObject
        self.hashString = None
        self.sequenceMatcher = None
        if self.measureObject is not None:
            self.getHashString()
        
    def getHashString(self):
        '''
        takes a stream and returns a hashed string for searching on
        and stores it in self.hashString
        
        If a measure object has multiple voices, use the first  voice.

        >>> m = stream.Measure()
        >>> m.append(note.Note('C', quarterLength=1.5))
        >>> m.append(note.Note('C', quarterLength=0.5))
        >>> m.append(note.Rest(quarterLength=1.5))
        >>> m.append(note.Note('B', quarterLength=0.5))

        >>> hasher = omr.correctors.MeasureHash(m)
        >>> hasher.getHashString()
        'VFUF'
        >>> hasher.hashString == 'VFUF'
        True
        '''
        hashString = ''
        if self.measureObject is None:
            return ''
        mo = self.measureObject
        if mo.isFlat is True:
            mo = mo.notesAndRests
        else:
            subStream = mo.chordify()
            mo = subStream.notesAndRests
            #Turns multi-voice measures into a flat measures  with chords that combine the voices
        
        for n in mo:
            if n.duration.quarterLength == 0.0:
                hashString += self.hashGrace(n)
            elif n.isNote:
                hashString += self.hashNote(n)
            elif not n.isNote:
                if n.isRest:
                    hashString += self.hashRest(n)
                elif n.isChord:
                    hashString += self.hashNote(n)
        self.hashString = hashString
        return hashString
    
    def hashNote(self,n):
        '''
        Encodes a note
        
        >>> hasher = omr.correctors.MeasureHash()

        >>> n = note.Note('C')
        >>> n.duration.type = 'quarter'
        >>> hasher.hashNote(n)
        'P'
        >>> n2 = note.Note('C')
        >>> n2.duration.type = 'half'
        >>> hasher.hashNote(n2)
        'Z'
        >>> n3 = note.Note('C', quarterLength=1.5)
        >>> hasher.hashNote(n3)
        'V'
        '''
        
        duration1to127 = self.hashQuarterLength(n.duration.quarterLength)
        if duration1to127%2==0 and duration1to127>0:
            byteEncoding = chr(duration1to127)
        elif duration1to127%2==1 and duration1to127>0:
            byteEncoding = chr(duration1to127+1)
        elif duration1to127 < 0:
            byteEncoding = chr(1)
        return byteEncoding

    def hashGrace(self,n):
        '''
        Gives a Grace Note a duration of a 128th note

        '''
        graceNoteDuration = self.hashQuarterLength(.015625)
        byteEncoding = chr(graceNoteDuration)
        return byteEncoding
    
    def hashRest(self, r):
        '''
        Encodes a rest

        >>> r = note.Rest(1.0)
        >>> hasher = omr.correctors.MeasureHash()
        >>> hasher.hashRest(r)
        'Q'
        
        '''
        duration1to127 = self.hashQuarterLength(r.duration.quarterLength)
        if duration1to127%2==0 and duration1to127 > 0:
            byteEncoding = chr(duration1to127+1)
        elif duration1to127%2==1 and duration1to127 > 0:
            byteEncoding = chr(duration1to127)
        elif duration1to127 < 0:
            byteEncoding = chr(1)
        return byteEncoding
    
    def hashQuarterLength(self,ql):
        '''
        Turns a QuarterLength duration into an integer from 1 to 127

        >>> hasher = omr.correctors.MeasureHash()
        >>> hasher.hashQuarterLength(1.0)
        80
        
        >>> hasher.hashQuarterLength(2.0)
        90
        '''
        duration1to127 = int(math.log(ql * 256, 2)*10)
        if duration1to127 >= 127:
            duration1to127 = 127
        elif duration1to127 == 0:
            duration1to127 = 1
        return duration1to127
    
    def setSequenceMatcher(self, hashes = None):
        if hashes is None:
            if self.hashString is None:
                hashes = self.getHashString()
                self.hashString = hashes
            else:
                hashes = self.hashString
        self.sequenceMatcher = difflib.SequenceMatcher(None, hashes,"")
        
        
    def getMeasureDifference(self, hashString):
        '''
        Returns the difference ratio between two measures
        b is the "correct" measure that we want to replace the flagged measure with
        
        Takes a hashString
        
        >>> m = stream.Measure()
        >>> m.append(note.Note('C', quarterLength=1.5))
        >>> m.append(note.Note('C', quarterLength=0.5))
        >>> m.append(note.Rest(quarterLength=1.5))
        >>> m.append(note.Note('B', quarterLength=0.5))

        >>> hasher = omr.correctors.MeasureHash(m)
        >>> hasher.setSequenceMatcher()
        >>> hasher.getMeasureDifference('VGUF')
        0.25
        
        >>> m = stream.Measure()
        >>> m.append(note.Note('C', quarterLength=1.5))
        >>> m.append(note.Note('C', quarterLength=0.5))
        >>> m.append(note.Rest(quarterLength=1.5))
        >>> m.append(note.Note('B', quarterLength=0.5))
        
        >>> hasher = omr.correctors.MeasureHash(m)
        >>> hasher.setSequenceMatcher()
        >>> hasher.getMeasureDifference('VFUF')
        1.0
        
        '''

        self.sequenceMatcher.set_seq2(hashString)
        myRatio = self.sequenceMatcher.ratio()
        if myRatio == 1.0:
            myRatio = 0.0
        return 1-myRatio 
              
    def getOpCodes(self, otherHash = None):
        '''
        Gets the opcodes from a simple sequenceMatcher for the current measureHash
        
        Example of Violin II vs. Viola and Cello in K525 I, m. 17
        
        >>> vlnII = converter.parse('tinynotation: 4/4 e4 e8. e8 c4 c8 c8').flat.notes.stream()
        >>> viola = converter.parse('tinynotation: 4/4 c4 c8  c8 A4 A8 A8').flat.notes.stream()
        >>> cello = converter.parse('tinynotation: 4/4 C4 C4     D4 D4   ').flat.notes.stream()
        >>> vlnIIMH = omr.correctors.MeasureHash(vlnII)
        >>> violaMH = omr.correctors.MeasureHash(viola)
        >>> celloMH = omr.correctors.MeasureHash(cello)
        >>> vlnIIMH.getOpCodes(violaMH.hashString)
        [('equal', 0, 1, 0, 1), ('replace', 1, 2, 1, 2), ('equal', 2, 6, 2, 6)]
        >>> vlnIIMH.getOpCodes(celloMH.hashString)
        [('equal', 0, 1, 0, 1), ('delete', 1, 3, 1, 1), 
         ('equal', 3, 4, 1, 2), ('replace', 4, 6, 2, 4)]
        '''
        if self.sequenceMatcher is None:
            self.setSequenceMatcher()
        if otherHash is not None:
            self.sequenceMatcher.set_seq2(otherHash) 
        return self.sequenceMatcher.get_opcodes()
        
    def getProbabilityBasedOnChanges(self, otherHash):
        '''
        Takes a hash string
        
        >>> otherHash = 'e'
        >>> hashString = 'GFPGF'
        >>> mh = omr.correctors.MeasureHash()
        >>> mh.hashString = hashString
        >>> mh.getProbabilityBasedOnChanges(otherHash)
        2.9472832125e-14
        
        Example of Violin II vs. Viola and Cello in K525 I, m. 17
        
        >>> vlnII = converter.parse('tinynotation: 4/4 e4 e8. e8 c4 c8 c8').flat.notes.stream()
        >>> viola = converter.parse('tinynotation: 4/4 c4 c8  c8 A4 A8 A8').flat.notes.stream()
        >>> cello = converter.parse('tinynotation: 4/4 C4 C4     D4 D4   ').flat.notes.stream()
        >>> vlnIIMH = omr.correctors.MeasureHash(vlnII)
        >>> violaMH = omr.correctors.MeasureHash(viola)
        >>> celloMH = omr.correctors.MeasureHash(cello)
        >>> vlnIIMH.getProbabilityBasedOnChanges(violaMH.hashString)
        0.0076295...
        >>> vlnIIMH.getProbabilityBasedOnChanges(celloMH.hashString)
        4.077...e-09
        '''
        
        opcodes = self.getOpCodes(otherHash)
        allProbability = 0.0

        for opcode in opcodes:
            oneProbability = self.differenceProbabilityForOneOpCode(opcode,otherHash)
            if opcodes.index(opcode) == 0:  
                allProbability = oneProbability
            else:
                allProbability *= oneProbability
        return allProbability

    
    def differenceProbabilityForOneOpCode(self, opCodeTuple, source, destination=None):
        '''
        Given an opCodeTuple and a source, differenceProbabilityForOneOpCode
        returns the difference probability for one type of opcode 
        (replace, insert, delete, or equal).
        Here, the destination is in the set F of flagged measures and the 
        source is in the set C of correcting measures. 
        Source and destination are both hashStrings
                
        >>> source = "PFPFFF"
        >>> destination = "PFPFGF"
        >>> ops = ('equal', 0, 4, 0, 4)
        >>> mh = omr.correctors.MeasureHash()
        >>> mh.differenceProbabilityForOneOpCode(ops, source, destination)
        0.8762013031640626
        
        Omission
        
        >>> ops2 = ('insert', 4, 4, 4, 5)
        >>> mh2 = omr.correctors.MeasureHash()
        >>> mh2.differenceProbabilityForOneOpCode(ops2, source, destination)
        0.009
        
        >>> ops3 = ('replace', 2, 4, 2, 4)
        >>> mh3 = omr.correctors.MeasureHash()
        >>> mh3.differenceProbabilityForOneOpCode(ops3, "PPPPP", "PPVZP")
        0.0001485
        
        Five deletes in a row:
        
        >>> ops4 = ('delete', 0, 5, 0, 0)
        >>> mh3 = omr.correctors.MeasureHash()
        >>> mh3.differenceProbabilityForOneOpCode(ops4, 'e', 'GFPGF')
        1.024e-12
                
        Example of Violin II vs. Viola in K525 I, m. 17
        
        >>> vlnII = converter.parse('tinynotation: 4/4 e4 e8. e8 c4 c8 c8').flat.notes.stream()
        >>> viola = converter.parse('tinynotation: 4/4 c4 c8  c8 A4 A8 A8').flat.notes.stream()
        >>> vlnIIMH = omr.correctors.MeasureHash(vlnII)
        >>> violaMH = omr.correctors.MeasureHash(viola)
        >>> vlnIIMH.hashString
        'PLFPFF'
        >>> violaMH.hashString
        'PFFPFF'
        >>> opCodes = vlnIIMH.getOpCodes(violaMH.hashString)
        >>> for oc in opCodes:
        ...    print("%30r : %.3f" % 
        ...           (oc, vlnIIMH.differenceProbabilityForOneOpCode(oc, violaMH.hashString)))
                 ('equal', 0, 1, 0, 1) : 0.968
               ('replace', 1, 2, 1, 2) : 0.009
                 ('equal', 2, 6, 2, 6) : 0.876
        '''
        if destination is None:
            destination = self.hashString
            if destination is None:
                raise Exception("HashString has not yet been set!")
        
        opCodeType = opCodeTuple[0]
        if opCodeType == 'equal':
            lengthOfEqualSection = opCodeTuple[4]-opCodeTuple[3]
            return (self.getProbabilityOnEquality())**lengthOfEqualSection
        elif opCodeType == 'replace':
            sourceSnippet = source[opCodeTuple[3]:opCodeTuple[4]]
            destinationSnippet = destination[opCodeTuple[1]:opCodeTuple[2]]
            return self.getProbabilityOnSubstitute(sourceSnippet, destinationSnippet)
        elif opCodeType == 'insert':
            numberOfOmissions = opCodeTuple[4]-opCodeTuple[3]
            return  self.getProbabilityOnOmission()**numberOfOmissions
        elif opCodeType == 'delete':
            numberOfAdditions = opCodeTuple[2]-opCodeTuple[1]
            return self.getProbabilityOnAddition()**numberOfAdditions 
        else:
            raise Exception("Incorrect opcode type!")
        
    def getProbabilityOnEquality(self):
        '''
        Parts or the whole of a string were equal.
        
        >>> omr.correctors.MeasureHash().getProbabilityOnEquality()
        0.9675
        '''
        return .9675     
        
        
    def getProbabilityOnOmission(self):
        '''
        In order for the source to be correct,
        the destination omitted a symbol.
        Associated with type 'delete' and in the case of replacement of
        a dotted version of a note with an undotted version (or double dot with dotted, etc.)
        
        >>> omr.correctors.MeasureHash().getProbabilityOnOmission()
        0.009        
        '''
        return .009
   
    def getProbabilityOnAddition(self):  
        '''
        In order for the source to be correct,
        the destination added a symbol
        Associated with type 'insert'
        
        >>> omr.correctors.MeasureHash().getProbabilityOnAddition()
        0.004
        '''        
        return .004
    
    def getProbabilityOnSubstitute(self, source, destination):
        '''
        Source and destination are measureHash strings
        Source is in set C of correcting measures.
        Destination is in set F of flagged measures. 
        
        (Rossant & Bloch)
        
        * value change: 50.77% of all errors (inverse: .0197)
        * confusions: 9.23% of all errors (inverse: .108)
            Note: these get the most probability, because they are the rarest
        * omission: 27.69% of all errors (inverse: .0361)
        * addition: 12.31% of all errors (inverse: .08125)
        
        >>> mh = omr.correctors.MeasureHash()
        
        Replacement of eighth note (F) for quarter note (P) = shift of one value:
        
        >>> mh.getProbabilityOnSubstitute('F','P')
        0.0165
        
        Replacement of eighth note (F) for eighth rest (G) = shift of one type:
        
        >>> mh.getProbabilityOnSubstitute('F','G')
        0.003
        
        Omission of any symbol, less common so costs more
        The proposed correction assumes that the incorrect measure omitted a symbol
        
        >>> mh.getProbabilityOnSubstitute('','P')
        0.009
        
        Addition of any symbol, less common so costs more
        The proposed correction assumes that the incorrect measure added a symbol
        
        >>> mh.getProbabilityOnSubstitute('P','')
        0.004
        
        Combination of value shift and an addition:
        
        >>> mh.getProbabilityOnSubstitute('F','PP')
        0.0001485
        
        
        Take minimum length. Compare index to index. Any additional letters
        in the flagged measure get graded as additions. Any additional letters
        in the comparison measure get graded as omissions. 
        
        '''        
        ls = len(source)
        ld = len(destination)
        if ls > ld:
            numberOfAdditions = ls - ld
            baseProbability = self.getProbabilityOnAddition()**numberOfAdditions
            source = source[0:-1*(numberOfAdditions)]
        elif ls < ld:
            numberOfOmissions = ld - ls
            baseProbability = self.getProbabilityOnOmission()**numberOfOmissions
            destination = destination[0:-1*(numberOfOmissions)]
        else:
            baseProbability = 1.0
        for i in range(len(source)):
            sourceChar = source[i]
            destChar = destination[i]
            baseProbability *= self.getProbabilityFromOneCharSub(sourceChar, destChar)
        
        return baseProbability
            
    def getProbabilityFromOneCharSub(self, source, destination):
        '''
        Source and destination are strings of one character
        
        >>> mh = omr.correctors.MeasureHash()
        
        Eighth note to eighth rest:
        
        >>> mh.getProbabilityFromOneCharSub('F','G')
        0.003
        
        Eighth note to quarter note:
        
        >>> mh.getProbabilityFromOneCharSub('F','P')
        0.0165
        
        Eighth note to half note:
        
        >>> mh.getProbabilityFromOneCharSub('F','Z')
        0.0002722...
        
        Quarter note to dotted quarter note:
        
        >>> mh.getProbabilityFromOneCharSub('P','V')
        0.009
        
        
        Dotted quarter note to quarter note:
        
        >>> mh.getProbabilityFromOneCharSub('V','P')
        0.004
        
        >>> mh.getProbabilityFromOneCharSub('A','Y')
        3.6e-05
        '''
        charDiff = ord(source)-ord(destination)
        absCharDiff = math.fabs(charDiff)
        
        if charDiff == 0.0:
            return 1.0      
        elif absCharDiff % 10 == 0.0:
            numberOfShifts = absCharDiff / 10.0
            return .0165 ** numberOfShifts
        elif charDiff == 6.0:
            #addition
            return self.getProbabilityOnAddition()
        elif charDiff == -6.0:
            #omission
            return self.getProbabilityOnOmission()
        elif absCharDiff % 2 != 0:
            return .003
            # eighth rest to eighth note receives equal probability as eighth rest to quarter note
        else:
            # anything else is counted as an omission and an addition
            # ex: double dots, triplets
            return self.getProbabilityOnOmission() * self.getProbabilityOnAddition()
                          
    
if __name__ == '__main__':
    import music21
#     s = converter.parse(K525omrFilePath)
    #from music21 import *                        # @UnusedImport @UnusedWildImport
    #s = converter.parse('/Users/MC/Work/' +      # @UndefinedVariable
    #             'K525_from_SmartScore.xml')
    #scor = omr.correctors.ScoreCorrector(s)      # @UndefinedVariable
    #s2 = scor.run()
    #s2.show()

    music21.mainTest()
