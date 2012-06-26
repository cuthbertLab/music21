# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         variant.py
# Purpose:      Translate MusicXML and music21 objects
#
# Authors:      Christopher Ariza
#               Evan Lynch
#
# Copyright:    (c) 2012 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
'''
Contains :class:`~music21.variant.Variant` and its subclasses, as well as functions for merging
and showing different variant streams. These functions and the variant class should only be
used when variants of a score are the same length and contain the same measure structure at
this time.
'''

import unittest

import music21
import copy
import difflib

from music21 import common
from music21 import stream
from music21 import environment
from music21 import note
from music21 import search

_MOD = "variant.py" # TODO: call variant
environLocal = environment.Environment(_MOD)



#-- Functions
def mergeVariantMeasureStreams(streamX, streamY, variantName, inPlace = False):
    '''
    Takes two streams of measures and returns a stream (new if inPlace is False) with the second
    merged with the first as variants. This function differs from mergeVariantStreams by
    dealing with streams that are of different length. This function matches measures that are
    exactly equal and creates variant objects for regions of measures that differ at all. If more
    refined variants are sought (with variation within the bar considered and related but different
    bars associated with each other), use variant.refineVariant().
    
    In this example, the second bar has been deleted in the second version, a new bar has been inserted between the
    original third and fourth bars, and two bars have been added at the end.
    
    >>> from music21 import *
    >>> data1M1 = [('a', 'quarter'), ('b', 'eighth'), ('c', 'eighth'), ('a', 'quarter'), ('a', 'quarter')]
    >>> data1M2 = [('b', 'eighth'), ('c', 'eighth'), ('a', 'quarter'), ('a', 'quarter'),('b', 'quarter')]
    >>> data1M3 = [('c', 'quarter'), ('d', 'quarter'), ('e', 'quarter'), ('e', 'quarter')]
    >>> data1M4 = [('d', 'quarter'), ('g', 'eighth'), ('g', 'eighth'), ('a', 'quarter'), ('b', 'quarter')]
    
    >>> data2M1 = [('a', 'quarter'), ('b', 'eighth'), ('c', 'eighth'), ('a', 'quarter'), ('a', 'quarter')]
    >>> data2M2 = [('c', 'quarter'), ('d', 'quarter'), ('e', 'quarter'), ('e', 'quarter')]
    >>> data2M3 = [('e', 'quarter'), ('g', 'eighth'), ('g', 'eighth'), ('a', 'quarter'), ('b', 'quarter')]
    >>> data2M4 = [('d', 'quarter'), ('g', 'eighth'), ('g', 'eighth'), ('a', 'quarter'), ('b', 'quarter')]
    >>> data2M5 = [('f', 'eighth'), ('c', 'quarter'), ('a', 'eighth'), ('a', 'quarter'), ('b', 'quarter')]
    >>> data2M6 = [('g', 'quarter'), ('d', 'quarter'), ('e', 'quarter'), ('e', 'quarter')]
    
    >>> data1 = [data1M1, data1M2, data1M3, data1M4]
    >>> data2 = [data2M1, data2M2, data2M3, data2M4, data2M5, data2M6]
    >>> stream1 = stream.Stream()
    >>> stream2 = stream.Stream()
    >>> mNumber = 1
    >>> for d in data1:
    ...    m = stream.Measure()
    ...    m.number = mNumber
    ...    mNumber += 1
    ...    for pitchName,durType in d:
    ...        n = note.Note(pitchName)
    ...        n.duration.type = durType
    ...        m.append(n)
    ...    stream1.append(m)
    >>> mNumber = 1
    >>> for d in data2:
    ...    m = stream.Measure()
    ...    m.number = mNumber
    ...    mNumber += 1
    ...    for pitchName,durType in d:
    ...        n = note.Note(pitchName)
    ...        n.duration.type = durType
    ...        m.append(n)
    ...    stream2.append(m)
    >>> #_DOCS_SHOW stream1.show()
    
    
    .. image:: images/variant_measuresStreamMergeStream1.*
        :width: 600
    
    >>> #_DOCS_SHOW stream2.show()
    
    
    .. image:: images/variant_measuresStreamMergeStream2.*
        :width: 600

    >>> mergedStream = mergeVariantMeasureStreams(stream1, stream2, 'paris', inPlace = False)
    >>> mergedStream.show('text')
    {0.0} <music21.stream.Measure 1 offset=0.0>
        {0.0} <music21.note.Note A>
        {1.0} <music21.note.Note B>
        {1.5} <music21.note.Note C>
        {2.0} <music21.note.Note A>
        {3.0} <music21.note.Note A>
    {4.0} <music21.variant.Variant object at ...>
    {4.0} <music21.stream.Measure 2 offset=4.0>
        {0.0} <music21.note.Note B>
        {0.5} <music21.note.Note C>
        {1.0} <music21.note.Note A>
        {2.0} <music21.note.Note A>
        {3.0} <music21.note.Note B>
    {8.0} <music21.stream.Measure 3 offset=8.0>
        {0.0} <music21.note.Note C>
        {1.0} <music21.note.Note D>
        {2.0} <music21.note.Note E>
        {3.0} <music21.note.Note E>
    {12.0} <music21.variant.Variant object at ...>
    {12.0} <music21.stream.Measure 4 offset=12.0>
        {0.0} <music21.note.Note D>
        {1.0} <music21.note.Note G>
        {1.5} <music21.note.Note G>
        {2.0} <music21.note.Note A>
        {3.0} <music21.note.Note B>
    {16.0} <music21.variant.Variant object at ...>
    
    >>> mergedStream.variants[0].replacementDuration
    4.0
    >>> mergedStream.variants[1].replacementDuration
    0.0
    
    >>> parisStream = mergedStream.activateVariants('paris', inPlace = False)
    >>> parisStream.show('text')
    {0.0} <music21.stream.Measure 1 offset=0.0>
        {0.0} <music21.note.Note A>
        {1.0} <music21.note.Note B>
        {1.5} <music21.note.Note C>
        {2.0} <music21.note.Note A>
        {3.0} <music21.note.Note A>
    {4.0} <music21.variant.Variant object at ...>
    {4.0} <music21.stream.Measure 2 offset=4.0>
        {0.0} <music21.note.Note C>
        {1.0} <music21.note.Note D>
        {2.0} <music21.note.Note E>
        {3.0} <music21.note.Note E>
    {8.0} <music21.variant.Variant object at ...>
    {8.0} <music21.stream.Measure 3 offset=8.0>
        {0.0} <music21.note.Note E>
        {1.0} <music21.note.Note G>
        {1.5} <music21.note.Note G>
        {2.0} <music21.note.Note A>
        {3.0} <music21.note.Note B>
    {12.0} <music21.stream.Measure 4 offset=12.0>
        {0.0} <music21.note.Note D>
        {1.0} <music21.note.Note G>
        {1.5} <music21.note.Note G>
        {2.0} <music21.note.Note A>
        {3.0} <music21.note.Note B>
    {16.0} <music21.variant.Variant object at ...>
    {16.0} <music21.stream.Measure 5 offset=16.0>
        {0.0} <music21.note.Note F>
        {0.5} <music21.note.Note C>
        {1.5} <music21.note.Note A>
        {2.0} <music21.note.Note A>
        {3.0} <music21.note.Note B>
    {20.0} <music21.stream.Measure 6 offset=20.0>
        {0.0} <music21.note.Note G>
        {1.0} <music21.note.Note D>
        {2.0} <music21.note.Note E>
        {3.0} <music21.note.Note E>
    
    >>> parisStream.variants[0].replacementDuration
    0.0
    >>> parisStream.variants[1].replacementDuration
    4.0
    >>> parisStream.variants[2].replacementDuration
    8.0
    '''
    if inPlace is True:
        returnObj = streamX
    else:
        returnObj = copy.deepcopy(streamX)
    
    regions = _getRegionsFromStreams(returnObj,streamY)
    for regionType, xRegionStartMeasure, xRegionEndMeasure, yRegionStartMeasure, yRegionEndMeasure in regions: # Note that the 'end' measure indices are 1 greater than the 0-indexed number of the measure.
        if xRegionStartMeasure >= len(returnObj.getElementsByClass('Measure')):
            startOffset = returnObj.duration.quarterLength #This deals with insertion at the end case where returnObj.measure(xRegionStartMeasure+1) does not exist.
        else:
            startOffset = returnObj.measure(xRegionStartMeasure+1).getOffsetBySite(returnObj)
        if regionType is 'equal':
            #yRegion = streamY.measures(yRegionStartMeasure+1, yRegionEndMeasure)
            continue #Do nothing
        elif regionType is 'replace':
            xRegion = returnObj.measures(xRegionStartMeasure+1, xRegionEndMeasure)
            replacementDuration = xRegion.duration.quarterLength
            yRegion = streamY.measures(yRegionStartMeasure+1, yRegionEndMeasure)                      
        elif regionType is 'delete':
            xRegion = returnObj.measures(xRegionStartMeasure+1, xRegionEndMeasure)
            replacementDuration = xRegion.duration.quarterLength
            yRegion = None
        elif regionType is 'insert':
            yRegion = streamY.measures(yRegionStartMeasure+1, yRegionEndMeasure)
            replacementDuration = 0.0
        addVariant(returnObj, startOffset, yRegion, variantName = variantName, replacementDuration = replacementDuration)
    return returnObj

    
def addVariant(s,startOffset, sVariant, variantName = None, variantGroups = None, replacementDuration = None):
    '''
    Takes a stream, the location of the variant to be added to that stream (startOffset), the content of the
    variant to be added (sVariant), and the duration of the section of the stream which the variant
    replaces (replacementDuration). If replacementDuration is 0, this is an insertion. If sVariant is 
    None, this is a deletion.
    
    >>> from music21 import *
    >>> data1M1 = [('a', 'quarter'), ('b', 'eighth'), ('c', 'eighth'), ('a', 'quarter'), ('a', 'quarter')]
    >>> data1M3 = [('c', 'quarter'), ('d', 'quarter'), ('e', 'quarter'), ('e', 'quarter')]
    >>> data1M2 = [('b', 'eighth'), ('c', 'eighth'), ('a', 'quarter'), ('a', 'quarter'),('b', 'quarter')]
    >>> data2M2 = [('b', 'eighth'), ('c', 'quarter'), ('a', 'eighth'), ('a', 'quarter'), ('b', 'quarter')]
    >>> data1 = [data1M1, data1M2, data1M3]
    >>> tempPart = stream.Part()
    >>> stream1 = stream.Stream()
    >>> stream2 = stream.Stream()
    >>> for d in data1:
    ...    m = stream.Measure()
    ...    for pitchName,durType in d:
    ...        n = note.Note(pitchName)
    ...        n.duration.type = durType
    ...        m.append(n)
    ...    stream1.append(m)
    >>> m = stream.Measure()
    >>> for pitchName,durType in data2M2:
    ...    n = note.Note(pitchName)
    ...    n.duration.type = durType
    ...    m.append(n)
    >>> stream2.append(m)
    >>> addVariant(stream1, 4.0, stream2, variantName = 'rhythmic switch', replacementDuration = 4.0)
    >>> stream1.show('text')
    {0.0} <music21.stream.Measure 0 offset=0.0>
        {0.0} <music21.note.Note A>
        {1.0} <music21.note.Note B>
        {1.5} <music21.note.Note C>
        {2.0} <music21.note.Note A>
        {3.0} <music21.note.Note A>
    {4.0} <music21.variant.Variant object at ...>
    {4.0} <music21.stream.Measure 0 offset=4.0>
        {0.0} <music21.note.Note B>
        {0.5} <music21.note.Note C>
        {1.0} <music21.note.Note A>
        {2.0} <music21.note.Note A>
        {3.0} <music21.note.Note B>
    {8.0} <music21.stream.Measure 0 offset=8.0>
        {0.0} <music21.note.Note C>
        {1.0} <music21.note.Note D>
        {2.0} <music21.note.Note E>
        {3.0} <music21.note.Note E>
    
    >>> stream1 = stream.Stream()
    >>> stream1.repeatAppend(note.Note('e'), 6)
    >>> variant1 = variant.Variant()
    >>> variant1.repeatAppend(note.Note('f'), 3)
    >>> startOffset = 3.0
    >>> addVariant(stream1, startOffset, variant1, variantName = 'paris', replacementDuration = 3.0)
    >>> stream1.show('text')
    {0.0} <music21.note.Note E>
    {1.0} <music21.note.Note E>
    {2.0} <music21.note.Note E>
    {3.0} <music21.variant.Variant object at ...>
    {3.0} <music21.note.Note E>
    {4.0} <music21.note.Note E>
    {5.0} <music21.note.Note E>
    '''
    tempVariant = music21.variant.Variant()
    
    if variantGroups is not None:
        tempVariant.groups = variantGroups
    if variantName is not None:
        tempVariant.groups.append(variantName)
        
    tempVariant.replacementDuration = replacementDuration
           
    if sVariant is None: #deletion
        pass
    else: #replacement or insertion
        if type(sVariant) is music21.stream.Measure: #sVariant is a measure put it in a variant and insert.
            tempVariant.append(sVariant)
        else: #sVariant is not a measure
            sVariantMeasures = sVariant.getElementsByClass('Measure')
            if sVariantMeasures == []: # If there are no measures, work element-wise
                for e in sVariant:
                    offset = e.getOffsetBySite(sVariant)+startOffset
                    tempVariant.insert(offset, e)
            else: # if there are measures work measure-wise
                for m in sVariantMeasures:
                    tempVariant.append(m)

    s.insert(startOffset, tempVariant)



def refineVariant(s, sVariant, inPlace = False):
    '''
    Given a stream and variant contained in that stream, returns a stream with that variant 'refined.'
    It is refined in the sense that, (with the best estimates) measures which have been determined
    to be related are merged within the measure. Suppose a four-bar phrase in a piece is a slightly
    different five-bar phrase in a variant. In the variant, every F# has been replaced by an F,
    and the last bar is repeated. Given this streams, mergeVariantMeasureStreams would return
    the first stream with a single variant object containing the entire 5 bars of the variant.
    Calling refineVariant on this stream and that variant object would result in a variant object
    in the measures for each F#/F pair, and a variant object containing the added bar at the end.
    For a more detailed explanation of how similar measures are properly associated with each other
    look at the documentation for _getBestListandScore
    
    Note that this code does not work properly yet.
    
    >>> from music21 import *
    >>> v = variant.Variant()
    >>> variantDataM1 = [('b', 'eighth'), ('c', 'eighth'), ('a', 'quarter'), ('a', 'quarter'),('b', 'quarter')]
    >>> variantDataM2 = [('c', 'quarter'), ('d', 'quarter'), ('e', 'quarter'), ('e', 'quarter')]
    >>> variantData = [variantDataM1, variantDataM2]
    >>> for d in variantData:
    ...    m = stream.Measure()
    ...    for pitchName,durType in d:
    ...        n = note.Note(pitchName)
    ...        n.duration.type = durType
    ...        m.append(n)
    ...    v.append(m)
    >>> v.groups = ['paris']
    >>> v.replacementDuration = 8.0
    
    >>> s = stream.Stream()
    >>> streamDataM1 = [('a', 'quarter'), ('b', 'quarter'), ('a', 'quarter'), ('g', 'quarter')]
    >>> streamDataM2 = [('b', 'eighth'), ('c', 'quarter'), ('a', 'eighth'), ('a', 'quarter'), ('b', 'quarter')]
    >>> streamDataM3 = [('c', 'quarter'), ('b', 'quarter'), ('a', 'quarter'), ('a', 'quarter')]
    >>> streamDataM4 = [('c', 'quarter'), ('b', 'quarter'), ('a', 'quarter'), ('a', 'quarter')]
    >>> streamData = [streamDataM1, streamDataM2, streamDataM3, streamDataM4]
    >>> for d in streamData:
    ...    m = stream.Measure()
    ...    for pitchName,durType in d:
    ...        n = note.Note(pitchName)
    ...        n.duration.type = durType
    ...        m.append(n)
    ...    s.append(m)
    >>> s.insert(4.0, v)

    >>> refineVariant(s, v, inPlace = True)
    >>> s.show('text')
    {0.0} <music21.stream.Measure 0 offset=0.0>
        {0.0} <music21.note.Note A>
        {1.0} <music21.note.Note B>
        {2.0} <music21.note.Note A>
        {3.0} <music21.note.Note G>
    {4.0} <music21.stream.Measure 0 offset=4.0>
        {0.0} <music21.note.Note B>
        {0.5} <music21.variant.Variant object at ...>
        {0.5} <music21.note.Note C>
        {1.5} <music21.note.Note A>
        {2.0} <music21.note.Note A>
        {3.0} <music21.note.Note B>
    {8.0} <music21.stream.Measure 0 offset=8.0>
        {0.0} <music21.note.Note C>
        {1.0} <music21.variant.Variant object at ...>
        {1.0} <music21.note.Note B>
        {2.0} <music21.note.Note A>
        {3.0} <music21.note.Note A>
    {12.0} <music21.stream.Measure 0 offset=12.0>
        {0.0} <music21.note.Note C>
        {1.0} <music21.note.Note B>
        {2.0} <music21.note.Note A>
        {3.0} <music21.note.Note A>
    
    '''
    # stream that will be returned
    if not (sVariant in s.variants):
        raise VariantException('sVariant not found in stream s.')
    
    if inPlace is True:
        returnObject = s
        variantRegion = sVariant
    else:
        sVariantIndex = s.variants.index(sVariant)
        
        returnObject = copy.deepcopy(s)
        variantRegion = returnObject.variants(sVariantIndex)
        
    
    # useful parameters from variant and its location
    variantGroups = sVariant.groups
    replacementDuration = sVariant.replacementDuration
    startOffset = sVariant.getOffsetBySite(s)
    endOffset = replacementDuration+startOffset
    
    # region associated with the given variant in the stream
    returnRegion = returnObject.getElementsByOffset(startOffset, offsetEnd = endOffset, includeEndBoundary=False, classList = ['Measure'])

    # associating measures in variantRegion to those in returnRegion -> This is done via 0 indexed lists corresponding to measures
    returnRegionMeasureList = [i for i in range(len(returnRegion))]
    badnessDict = {}
    listDict = {}
    variantMeasureList, badness = _getBestListandScore(returnRegion, variantRegion, badnessDict, listDict)
    
    # badness is a measure of how different the streams are. The list returned, variantMeasureList, minimizes that quantity.
    
    # mentioned lists are compared via difflib for optimal edit regions (equal, delete, insert, replace)
    sm = difflib.SequenceMatcher()
    sm.set_seqs(returnRegionMeasureList, variantMeasureList)
    regions = sm.get_opcodes()
    
    # each region is processed for variants.
    for regionType, returnStart, returnEnd, variantStart, variantEnd in regions:
        startOffset = returnRegion[returnStart].getOffsetBySite(returnRegion)
        endOffset = returnRegion[returnEnd-1].getOffsetBySite(returnRegion)+returnRegion[returnEnd-1].duration.quarterLength       
        if regionType is 'equal':
            returnSubRegion = returnRegion.measures(returnStart+1, returnEnd)
            variantSubRegion = variantRegion.measures(variantStart+1, variantEnd)
            mergeVariantStreams([returnSubRegion, variantSubRegion], variantGroups, inPlace = True)
            continue
        
        elif regionType is 'replace':
            returnSubRegion = returnRegion.measures(returnStart+1, returnEnd)
            replacementDuration = returnSubRegion.duration.quarterLength
            variantSubRegion = variantRegion.measures(variantStart+1, variantEnd)                      
        elif regionType is 'delete':
            returnSubRegion = returnRegion.measures(returnStart+1, returnEnd)
            replacementDuration = returnSubRegion.duration.quarterLength
            variantSubRegion = None
        elif regionType is 'insert':
            variantSubRegion = variantRegion.measures(variantStart+1, variantEnd)
            replacementDuration = 0.0
        addVariant(returnRegion, startOffset, variantSubRegion, variantGroups = variantGroups, replacementDuration = replacementDuration)
            
    returnObject.remove(variantRegion) # The original variant object has been replaced by more refined variant objects and so should be deleted.
    if inPlace:
        return
    else:
        return returnObject

def _getBestListandScore(streamX, streamY, badnessDict, listDict, isNone = False, streamXindex = -1, streamYindex = -1):
    '''
    This is a recursive function which makes a map between two related streams of measures.
    It is designed for streams of measures that contain few if any measures that are actually
    identical and that have a different number of measures (within reason). For example,
    if one stream has 10 bars of eighth notes and the second stream has the same ten bars
    of eighth notes except with some dotted rhythms mixed in and the fifth bar is repeated.
    The first, streamX, is the reference stream. This function returns a list of
    integers with length len(streamY) which maps each measure of StreamY to the measure
    in streamX it is most likely associated with. For example, if the returned list is
    [0, 2, 3, 'addedBar', 4]. This indicates that streamY is most similar to streamX
    after the second bar of streamX has been removed and a new bar inserted between
    bars 4 and 5. Note that this list has measures 0-indexed. This function generates this map by
    minimizing the difference or 'badness' for the sequence of measures on the whole as determined
    by the helper function _simscore which compares measures for similarity. 'addedBar' appears
    in the list where this function has determined that the bar appearing
    in streamY does not have a counterpart in streamX anywhere and is an insertion.
    
    >>> from music21 import *
    >>> badnessDict = {}
    >>> listDict = {}
    >>> stream1 = stream.Stream()
    >>> stream2 = stream.Stream()
    
    >>> data1M1 = [('a', 'quarter'), ('b', 'eighth'), ('c', 'eighth'), ('a', 'quarter'), ('a', 'quarter')]
    >>> data1M2 = [('b', 'eighth'), ('c', 'eighth'), ('a', 'quarter'), ('a', 'quarter'),('b', 'quarter')]
    >>> data1M3 = [('c', 'quarter'), ('d', 'quarter'), ('e', 'quarter'), ('e', 'quarter')]
    
    >>> data2M1 = [('a', 'quarter'), ('b', 'quarter'), ('c', 'quarter'), ('g#', 'quarter')]
    >>> data2M2 = [('b', 'eighth'), ('c', 'quarter'), ('a', 'eighth'), ('a', 'quarter'), ('b', 'quarter')]
    >>> data2M3 = [('c', 'quarter'), ('b', 'quarter'), ('a', 'quarter'), ('a', 'quarter')]
    >>> data2M4 = [('c', 'quarter'), ('b', 'quarter'), ('a', 'quarter'), ('a', 'quarter')]
    >>> data1 = [data1M1, data1M2, data1M3]
    >>> data2 = [data2M1, data2M2, data2M3, data2M4]
    >>> for d in data1:
    ...    m = stream.Measure()
    ...    for pitchName,durType in d:
    ...        n = note.Note(pitchName)
    ...        n.duration.type = durType
    ...        m.append(n)
    ...    stream1.append(m)
    >>> for d in data2:
    ...    m = stream.Measure()
    ...    for pitchName,durType in d:
    ...        n = note.Note(pitchName)
    ...        n.duration.type = durType
    ...        m.append(n)
    ...    stream2.append(m)
    >>> kList, kBadness = _getBestListandScore(stream1, stream2, badnessDict, listDict, isNone = False)
    >>> kList
    [0, 1, 2, 'addedBar']
    '''
    # Initialize 'Best' Values for maximizing algorithm
    bestScore = 1
    bestNormalizedScore = 1
    bestList = []
    
    # Base Cases:
    if streamYindex>=len(streamY):
        listDict[(streamXindex,streamYindex,isNone)] = []
        badnessDict[(streamXindex,streamYindex,isNone)] = 0.0
        return [],0
    
    # Query Dict for existing results    
    if (streamXindex, streamYindex, isNone) in badnessDict.keys():
        badness = badnessDict[(streamXindex,streamYindex,isNone)]
        bestList = listDict[(streamXindex,streamYindex,isNone)]
        return bestList, badness
    
    #Get salient similarity score
    if streamXindex is -1 and streamYindex is -1:
        simscore = 0
    elif isNone:
        simscore = 0.5
    else:
        simscore = _diffscore(streamX[streamXindex],streamY[streamYindex])
    

    # Check the added bar case:
    kList, kBadness = _getBestListandScore(streamX, streamY, badnessDict, listDict, isNone = True, streamXindex = streamXindex, streamYindex = streamYindex+1)
    if kList is None:
        kList = []
    if len(kList) is not 0:
        normalizedBadness = kBadness/float(len(kList))
    else:
        normalizedBadness = 0
    if normalizedBadness <= bestNormalizedScore:
        bestScore = kBadness
        bestNormalizedScore = normalizedBadness
        bestList = kList
    
    # Check the other cases
    for k in range(streamXindex+1,len(streamX)):
        kList, kBadness = _getBestListandScore(streamX, streamY, badnessDict, listDict, isNone = False, streamXindex = k, streamYindex = streamYindex+1)
        if kList is None:
            kList = []
        if len(kList) is not 0:
            normalizedBadness = kBadness/float(len(kList))
        else:
            normalizedBadness = 0
        if normalizedBadness <= bestNormalizedScore:
            bestScore = kBadness
            bestNormalizedScore = normalizedBadness
            bestList = kList

    # Prepare and Return Results
    returnList = copy.deepcopy(bestList)
    if isNone:
        returnList.insert(0, 'addedBar')
    elif streamXindex is -1:
        pass
    else:
        returnList.insert(0, streamXindex)
    badness = bestScore + simscore
    
    badnessDict[(streamXindex, streamYindex,isNone)] = badness
    listDict[(streamXindex, streamYindex,isNone)] = returnList
    return returnList, badness

def _diffscore(measureX, measureY):
    '''
    Helper function for _getBestListandScore which compares to measures and returns a value
    associated with their similarity. The higher the normalized (0,1) value the poorer the match.
    This should be calibrated such that the value that appears in _getBestListandScore for
    isNone is true (i.e. testing when a bar does not associate with any existing bars the reference
    stream), is well matched with the similarity scores generated by this function.
    
    >>> from music21 import *
    >>> m1 = stream.Measure()
    >>> m2 = stream.Measure()
    >>> m1.append([note.Note('e'), note.Note('f'), note.Note('g'), note.Note('a')])
    >>> m2.append([note.Note('e'), note.Note('f'), note.Note('g#'), note.Note('a')])
    >>> _diffscore(m1, m2)
    0.02083333...
    
    '''
    if measureX is measureY:
        return 0.0
    
    pitchSumX, pitchSumY = 0.0,0.0
    for n in measureX.notes:
        pitchSumX += n.pitchClass
    for n in measureY.notes:
        pitchSumY += n.pitchClass
    
    xAveragePitch = pitchSumX / float(len(measureX.notes))
    yAveragePitch = pitchSumY / float(len(measureY.notes))
    
    return abs(yAveragePitch-xAveragePitch)/12.0

def _getRegionsFromStreams(streamX,streamY):
    '''
    Takes in two streams, returns a list of 5-tuples via difflib.get_opcodes() working on measure differences.
    
    >>> from music21 import *
    >>> s1 = converter.parse("d4 e8. f16 GG4 b'4 b-2 c4 d8. e16 FF4 a'4 b-2", "2/4")
    >>> #                     *0:Eq  *1:Rep        * *3:Eq             *6:In
    >>> s2 = converter.parse("d4 e8. f16 FF4 b'4 c4 d8. e16 FF4 a'4 b-2 b-2", "2/4")
    >>> s1m = s1.makeMeasures()
    >>> s2m = s2.makeMeasures()
    >>> regions = _getRegionsFromStreams(s1m, s2m)
    >>> regions
    [('equal', 0, 1, 0, 1), ('replace', 1, 3, 1, 2), ('equal', 3, 6, 2, 5), ('insert', 6, 6, 5, 6)]
    
    '''
    hashesX = getMeasureHashes(streamX)
    hashesY = getMeasureHashes(streamY)
    sm = difflib.SequenceMatcher()
    sm.set_seqs(hashesX,hashesY)
    regions = sm.get_opcodes()
    return regions

def getMeasureHashes(s):
    '''
    Takes in a stream containing measures and returns a list of hashes, one for each measure. Currently
    implemented with search.translateStreamToString()
    
    >>> from music21 import *
    >>> s = converter.parse("c4 d8. e16 FF4 a'4 b-2", "2/4")
    >>> sm = s.makeMeasures()
    >>> hashes = getMeasureHashes(sm)
    >>> hashes
    ['<P>K@<', ')PQP', 'FZ']
    '''
    hashes = []
    for m in s.getElementsByClass('Measure'):
        hashes.append(search.translateStreamToString(m.notesAndRests))
    return hashes


def mergeVariantStreams(streams, variantNames, inPlace = False):
    '''
    Pass this function a list of streams (they must be of the same length or a VariantException will be raised).
    It will return a stream which merges the differences between the streams into variant objects keeping the
    first stream in the list as the default. If inPlace is True, the first stream in the list will be modified,
    otherwise a new stream will be returned. Pass a list of names to associate variants with their sources, if this list
    does not contain an entry for each non-default variant, naming may not behave properly. Variants that have the
    same differences from the default will be saved as separate variant objects (i.e. more than once under different names).
    Also, note that a streams with bars of differing lengths will not behave properly.
    
    >>> from music21 import *
    >>> stream1 = stream.Stream()
    >>> stream2paris = stream.Stream()
    >>> stream3london = stream.Stream()
    >>> data1 = [('a', 'quarter'), ('b', 'eighth'), ('c', 'eighth'), ('a', 'quarter'), ('a', 'quarter'),
    ...    ('b', 'eighth'), ('c', 'eighth'), ('a', 'quarter'), ('a', 'quarter'),
    ...    ('b', 'quarter'), ('c', 'quarter'), ('d', 'quarter'), ('e', 'quarter')]
    >>> data2 = [('a', 'quarter'), ('b', 'quarter'), ('a', 'quarter'), ('g', 'quarter'),
    ...    ('b', 'eighth'), ('c', 'quarter'), ('a', 'eighth'), ('a', 'quarter'),
    ...    ('b', 'quarter'), ('c', 'quarter'), ('b', 'quarter'), ('a', 'quarter')]
    >>> data3 = [('a', 'quarter'), ('b', 'eighth'), ('c', 'eighth'), ('a', 'quarter'), ('a', 'quarter'),
    ...    ('b', 'eighth'), ('c', 'eighth'), ('a', 'quarter'), ('a', 'quarter'),
    ...    ('c', 'quarter'), ('c', 'quarter'), ('d', 'quarter'), ('e', 'quarter')]
    >>> for pitchName,durType in data1:
    ...    n = note.Note(pitchName)
    ...    n.duration.type = durType
    ...    stream1.append(n)
    >>> for pitchName,durType in data2:
    ...    n = note.Note(pitchName)
    ...    n.duration.type = durType
    ...    stream2paris.append(n)
    >>> for pitchName,durType in data3:
    ...    n = note.Note(pitchName)
    ...    n.duration.type = durType
    ...    stream3london.append(n)
    >>> mergedStreams = mergeVariantStreams([stream1, stream2paris, stream3london], ['paris', 'london'])
    >>> mergedStreams.show('t')
    {0.0} <music21.note.Note A>
    {1.0} <music21.variant.Variant object at ...>
    {1.0} <music21.note.Note B>
    {1.5} <music21.note.Note C>
    {2.0} <music21.note.Note A>
    {3.0} <music21.variant.Variant object at ...>
    {3.0} <music21.note.Note A>
    {4.0} <music21.note.Note B>
    {4.5} <music21.variant.Variant object at ...>
    {4.5} <music21.note.Note C>
    {5.0} <music21.note.Note A>
    {6.0} <music21.note.Note A>
    {7.0} <music21.variant.Variant object at ...>
    {7.0} <music21.note.Note B>
    {8.0} <music21.note.Note C>
    {9.0} <music21.variant.Variant object at ...>
    {9.0} <music21.note.Note D>
    {10.0} <music21.note.Note E>
    
    >>> mergedStreams.activateVariants('london').show('t')
    {0.0} <music21.note.Note A>
    {1.0} <music21.variant.Variant object at ...>
    {1.0} <music21.note.Note B>
    {1.5} <music21.note.Note C>
    {2.0} <music21.note.Note A>
    {3.0} <music21.variant.Variant object at ...>
    {3.0} <music21.note.Note A>
    {4.0} <music21.note.Note B>
    {4.5} <music21.variant.Variant object at ...>
    {4.5} <music21.note.Note C>
    {5.0} <music21.note.Note A>
    {6.0} <music21.note.Note A>
    {7.0} <music21.variant.Variant object at ...>
    {7.0} <music21.note.Note C>
    {8.0} <music21.note.Note C>
    {9.0} <music21.variant.Variant object at ...>
    {9.0} <music21.note.Note D>
    {10.0} <music21.note.Note E>
        
    If the streams contain parts and measures, the merge function will iterate through them and determine
    and store variant differences within each measure/part.
    
    >>> stream1 = stream.Stream()
    >>> stream2 = stream.Stream()
    >>> data1M1 = [('a', 'quarter'), ('b', 'eighth'), ('c', 'eighth'), ('a', 'quarter'), ('a', 'quarter')]
    >>> data1M2 = [('b', 'eighth'), ('c', 'eighth'), ('a', 'quarter'), ('a', 'quarter'),('b', 'quarter')]
    >>> data1M3 = [('c', 'quarter'), ('d', 'quarter'), ('e', 'quarter'), ('e', 'quarter')]
    >>> data2M1 = [('a', 'quarter'), ('b', 'quarter'), ('a', 'quarter'), ('g', 'quarter')]
    >>> data2M2 = [('b', 'eighth'), ('c', 'quarter'), ('a', 'eighth'), ('a', 'quarter'), ('b', 'quarter')]
    >>> data2M3 = [('c', 'quarter'), ('b', 'quarter'), ('a', 'quarter'), ('a', 'quarter')]
    >>> data1 = [data1M1, data1M2, data1M3]
    >>> data2 = [data2M1, data2M2, data2M3]
    >>> tempPart = stream.Part()
    >>> for d in data1:
    ...    m = stream.Measure()
    ...    for pitchName,durType in d:
    ...        n = note.Note(pitchName)
    ...        n.duration.type = durType
    ...        m.append(n)
    ...    tempPart.append(m)
    >>> stream1.append(tempPart)
    >>> tempPart = stream.Part()
    >>> for d in data2:
    ...    m = stream.Measure()
    ...    for pitchName,durType in d:
    ...        n = note.Note(pitchName)
    ...        n.duration.type = durType
    ...        m.append(n)
    ...    tempPart.append(m)
    >>> stream2.append(tempPart)
    >>> mergedStreams = mergeVariantStreams([stream1, stream2], ['paris'])
    >>> mergedStreams.show('t')
    {0.0} <music21.stream.Part ...>
        {0.0} <music21.stream.Measure 0 offset=0.0>
            {0.0} <music21.note.Note A>
            {1.0} <music21.variant.Variant object at ...>
            {1.0} <music21.note.Note B>
            {1.5} <music21.note.Note C>
            {2.0} <music21.note.Note A>
            {3.0} <music21.variant.Variant object at ...>
            {3.0} <music21.note.Note A>
        {4.0} <music21.stream.Measure 0 offset=4.0>
            {0.0} <music21.note.Note B>
            {0.5} <music21.variant.Variant object at ...>
            {0.5} <music21.note.Note C>
            {1.0} <music21.note.Note A>
            {2.0} <music21.note.Note A>
            {3.0} <music21.note.Note B>
        {8.0} <music21.stream.Measure 0 offset=8.0>
            {0.0} <music21.note.Note C>
            {1.0} <music21.variant.Variant object at ...>
            {1.0} <music21.note.Note D>
            {2.0} <music21.note.Note E>
            {3.0} <music21.note.Note E>
    >>> #_DOCS_SHOW mergedStreams.show()
    
    
    .. image:: images/variant_measuresAndParts.*
        :width: 600
        
    
    >>> for p in mergedStreams.getElementsByClass('Part'):
    ...    for m in p.getElementsByClass('Measure'):
    ...        m.activateVariants('paris', inPlace = True)
    >>> mergedStreams.show('t')
    {0.0} <music21.stream.Part ...>
        {0.0} <music21.stream.Measure 0 offset=0.0>
            {0.0} <music21.note.Note A>
            {1.0} <music21.variant.Variant object at ...>
            {1.0} <music21.note.Note B>
            {2.0} <music21.note.Note A>
            {3.0} <music21.variant.Variant object at ...>
            {3.0} <music21.note.Note G>
        {4.0} <music21.stream.Measure 0 offset=4.0>
            {0.0} <music21.note.Note B>
            {0.5} <music21.variant.Variant object at ...>
            {0.5} <music21.note.Note C>
            {1.5} <music21.note.Note A>
            {2.0} <music21.note.Note A>
            {3.0} <music21.note.Note B>
        {8.0} <music21.stream.Measure 0 offset=8.0>
            {0.0} <music21.note.Note C>
            {1.0} <music21.variant.Variant object at ...>
            {1.0} <music21.note.Note B>
            {2.0} <music21.note.Note A>
            {3.0} <music21.note.Note A>
    >>> #_DOCS_SHOW mergedStreams.show()
    
    
    .. image:: images/variant_measuresAndParts2.*
        :width: 600
    
    If barlines do not match up, an exception will be thrown. Here two streams that are identical
    are merged, except one is in 3/4, the other in 4/4. This throws an exception.
    
    >>> streamDifferentMeasures = stream.Stream()
    >>> dataDiffM1 = [('a', 'quarter'), ('b', 'eighth'), ('c', 'eighth'), ('a', 'quarter')]
    >>> dataDiffM2 = [ ('a', 'quarter'), ('b', 'eighth'), ('c', 'eighth'), ('a', 'quarter')]
    >>> dataDiffM3 = [('a', 'quarter'), ('b', 'quarter'), ('c', 'quarter')]
    >>> dataDiffM4 = [('d', 'quarter'), ('e', 'quarter'), ('e', 'quarter')]
    >>> dataDiff = [dataDiffM1, dataDiffM2, dataDiffM3, dataDiffM4]
    >>> streamDifferentMeasures.insert(0.0, meter.TimeSignature('3/4'))
    >>> tempPart = stream.Part()
    >>> for d in dataDiff:
    ...    m = stream.Measure()
    ...    for pitchName,durType in d:
    ...        n = note.Note(pitchName)
    ...        n.duration.type = durType
    ...        m.append(n)
    ...    tempPart.append(m)
    >>> streamDifferentMeasures.append(tempPart)
    >>> mergedStreams = mergeVariantStreams([stream1, streamDifferentMeasures], ['paris'])
    Traceback (most recent call last):
    ...
    VariantException: _mergeVariants cannot merge streams which are of different lengths
    '''
    
    if inPlace is True:
        returnObj = streams[0]
    else:
        returnObj = copy.deepcopy(streams[0])

    variantNames.insert(0, None) # Adds a None element at beginning (corresponding to default variant streams[0])
    while len(streams) > len(variantNames): # Adds Blank names if too few
        variantNames.append(None)
    while len(streams) < len(variantNames): # Removes extra names
        variantNames.pop
    
    zipped = zip(streams,variantNames)
    
    for s,variantName in zipped[1:]:
        if returnObj.highestTime != s.highestTime:
            raise VariantException('cannot merge streams of different lengths')

        returnObjParts = returnObj.getElementsByClass('Part')
        if len(returnObjParts) != 0: # If parts exist, iterate through them.
            sParts = s.getElementsByClass('Part')
            for i in range(len(returnObjParts)):
                returnObjPart = returnObjParts[i]
                sPart = sParts[i]
                
                returnObjMeasures = returnObjPart.getElementsByClass('Measure')
                if len(returnObjMeasures) != 0: # If measures exist and parts exist, iterate through them both.
                    for j in range(len(returnObjMeasures)):
                        returnObjMeasure = returnObjMeasures[j]
                        sMeasure = sPart.getElementsByClass('Measure')[j]
                        _mergeVariants(returnObjMeasure,sMeasure,variantName = variantName, inPlace = True)
                
                else: # If parts exist but no measures.
                    _mergeVariants(returnObjPart,sPart,variantName = variantName, inPlace = True)
        else:
            returnObjMeasures = returnObj.getElementsByClass('Measure')
            if len(returnObjMeasures) != 0: #If no parts, but still measures, iterate through them.
                for j in range(len(returnObjMeasures)):
                    returnObjMeasure = returnObjMeasures[j]
                    sMeasure = s.getElementsByClass('Measure')[j]
                    _mergeVariants(returnObjMeasure,sMeasure, variantName = variantName, inPlace = True)
            else: # If no parts and no measures.
                _mergeVariants(returnObj,s,variantName = variantName, inPlace = True)
           
    return returnObj

def _mergeVariants(streamA, streamB, containsVariants = False, variantName = None, inPlace = False):
    '''
    This is a helper function for mergeVariantStreams which takes two streams (which cannot contain container
    streams like measures and parts) and merges the second into the first via variant objects.
    If the first already contains variant objects, containsVariants should be set to true and the
    function will compare streamB to the streamA as well as the variant streams contained in streamA.
    Note that variant streams in streamB will be ignored and lost.
    
    >>> from music21 import *
    >>> stream1 = stream.Stream()
    >>> stream2 = stream.Stream()
    >>> data1 = [('a', 'quarter'), ('b', 'eighth'), ('c', 'eighth'), ('a', 'quarter'), ('a', 'quarter'),
    ...    ('b', 'eighth'), ('c', 'eighth'), ('a', 'quarter'), ('a', 'quarter'),
    ...    ('b', 'quarter'), ('c', 'quarter'), ('d', 'quarter'), ('e', 'quarter')]
    >>> data2 = [('a', 'quarter'), ('b', 'quarter'), ('a', 'quarter'), ('g', 'quarter'),
    ...    ('b', 'eighth'), ('c', 'quarter'), ('a', 'eighth'), ('a', 'quarter'),
    ...    ('b', 'quarter'), ('c', 'quarter'), ('b', 'quarter'), ('a', 'quarter')]
    >>> for pitchName,durType in data1:
    ...    n = note.Note(pitchName)
    ...    n.duration.type = durType
    ...    stream1.append(n)
    >>> for pitchName,durType in data2:
    ...    n = note.Note(pitchName)
    ...    n.duration.type = durType
    ...    stream2.append(n)
    >>> mergedStreams = _mergeVariants(stream1, stream2, variantName = 'paris')
    >>> mergedStreams.show('t')
    {0.0} <music21.note.Note A>
    {1.0} <music21.variant.Variant object at ...>
    {1.0} <music21.note.Note B>
    {1.5} <music21.note.Note C>
    {2.0} <music21.note.Note A>
    {3.0} <music21.variant.Variant object at ...>
    {3.0} <music21.note.Note A>
    {4.0} <music21.note.Note B>
    {4.5} <music21.variant.Variant object at ...>
    {4.5} <music21.note.Note C>
    {5.0} <music21.note.Note A>
    {6.0} <music21.note.Note A>
    {7.0} <music21.note.Note B>
    {8.0} <music21.note.Note C>
    {9.0} <music21.variant.Variant object at ...>
    {9.0} <music21.note.Note D>
    {10.0} <music21.note.Note E>
    
    >>> mergedStreams.activateVariants('paris').show('t')
    {0.0} <music21.note.Note A>
    {1.0} <music21.variant.Variant object at ...>
    {1.0} <music21.note.Note B>
    {2.0} <music21.note.Note A>
    {3.0} <music21.variant.Variant object at ...>
    {3.0} <music21.note.Note G>
    {4.0} <music21.note.Note B>
    {4.5} <music21.variant.Variant object at ...>
    {4.5} <music21.note.Note C>
    {5.5} <music21.note.Note A>
    {6.0} <music21.note.Note A>
    {7.0} <music21.note.Note B>
    {8.0} <music21.note.Note C>
    {9.0} <music21.variant.Variant object at ...>
    {9.0} <music21.note.Note B>
    {10.0} <music21.note.Note A>
    
    >>> stream1.append(note.Note('e'))
    >>> mergedStreams = _mergeVariants(stream1, stream2, variantName = ['paris'])
    Traceback (most recent call last):
    ...
    VariantException: _mergeVariants cannot merge streams which are of different lengths
    '''
    # TODO: Add the feature for merging a stream to a stream with existing variants (it has to compare against both the stream and the contained variant)
    if (len(streamA.getElementsByClass('Measure')) is not 0) or \
    (len(streamA.getElementsByClass('Part')) is not 0) or \
    (len(streamB.getElementsByClass('Measure')) is not 0) or \
    (len(streamB.getElementsByClass('Part')) is not 0):
        raise VariantException('_mergeVariants cannot merge streams which contain measures or parts.')
    
    if streamA.highestTime != streamB.highestTime:
        raise VariantException('_mergeVariants cannot merge streams which are of different lengths')
    
    if inPlace is True:
        returnObj = streamA
    else:
        returnObj = copy.deepcopy(streamA)
    
    i=0
    j=0
    inVariant = False
    streamAnotes = streamA.flat.notesAndRests
    streamBnotes = streamB.flat.notesAndRests
    while i<len(streamAnotes) and j<len(streamBnotes):
        if i == len(streamAnotes):
            i = len(streamAnotes)-1
        if j == len(streamBnotes):
            break
        if streamAnotes[i].getOffsetBySite(streamA.flat) == streamBnotes[j].getOffsetBySite(streamB.flat): # Comparing Notes at same offset TODO: Will not work until __eq__ overwritten for Generalized Notes
            if streamAnotes[i] != streamBnotes[j]: # If notes are different, start variant if not started and append note.
                if inVariant is False:
                    variantStart = streamBnotes[j].getOffsetBySite(streamB.flat)
                    inVariant = True
                    noteBuffer = []
                    noteBuffer.append(streamBnotes[j])
                else:
                    noteBuffer.append(streamBnotes[j])
            else: # If notes are the same, end and insert variant if in variant. 
                if inVariant is True:
                    returnObj.insert(variantStart,_generateVariant(noteBuffer,streamB,variantStart,variantName))
                    inVariant = False
                    noteBuffer = []
                else:
                    inVariant = False
                
            i += 1
            j += 1
            continue
                
        elif streamAnotes[i].getOffsetBySite(streamA.flat) > streamBnotes[j].getOffsetBySite(streamB.flat):
            if inVariant is False:
                variantStart = streamBnotes[j].getOffsetBySite(streamB.flat)
                noteBuffer = []
                noteBuffer.append(streamBnotes[j])
                inVariant = True
            else:
                noteBuffer.append(streamBnotes[j])
            j += 1
            continue
        
        else: #Less-than
            i += 1
            continue
    
    if inVariant is True: #insert final variant if exists
        returnObj.insert(variantStart,_generateVariant(noteBuffer,streamB,variantStart,variantName))
        inVariant = False
        noteBuffer = []
    
    if inPlace is True:
        return None
    else:
        return returnObj

def _generateVariant(noteList, originStream, start, variantName = None):
    '''
    Helper function for mergeVariantStreams which takes a list of consecutive notes from a stream and returns
    a variant object containing the notes from the list at the offsets derived from their original context.
    
    >>> originStream = stream.Stream()
    >>> data = [('a', 'quarter'), ('b', 'eighth'), ('c', 'eighth'), ('a', 'quarter'), ('a', 'quarter'),
    ...    ('b', 'eighth'), ('c', 'eighth'), ('a', 'quarter'), ('a', 'quarter'),
    ...    ('b', 'quarter'), ('c', 'quarter'), ('d', 'quarter'), ('e', 'quarter')]
    >>> for pitchName,durType in data:
    ...    n = note.Note(pitchName)
    ...    n.duration.type = durType
    ...    originStream.append(n)
    >>> noteList = []
    >>> for n in originStream.notes[2:5]:
    ...    noteList.append(n)
    >>> start = originStream.notes[2].offset
    >>> variantName = 'paris'
    >>> v = _generateVariant(noteList, originStream, start, variantName)
    >>> v.show('text')
    {0.0} <music21.note.Note C>
    {0.5} <music21.note.Note A>
    {1.5} <music21.note.Note A>
    
    >>> v.groups
    ['paris']
    
    '''
    returnVariant = music21.variant.Variant()
    for n in noteList:
        returnVariant.insert(n.getOffsetBySite(originStream.flat)-start, n)
    if variantName is not None:
        returnVariant.groups = [ variantName ]
    return returnVariant


def mergePartAsOssia(mainpart, ossiapart, ossiaName, inPlace = False, compareByMeasureNumber = False, recurseInMeasures = False):
    '''
    Some MusicXML files are generated with full parts that have only a few non-rest measures instead of ossia parts, such as those
    created by Sibelius 7. This function
    takes two streams (mainpart and ossiapart), the second interpreted as an ossia. It outputs a stream with the ossia part merged into the stream as a 
    group of variants.
    
    If compareByMeasureNumber is True, then the ossia measures will be paired with the measures in the mainpart that have the
    same measure.number. Otherwise, they will be paired by offset. In most cases these should have the same result.
    
    >>> from music21 import *
    >>> mainstream = converter.parse("  A4 B4 C4 D4   E1    F2 E2     E8 F8 F4 G2   G2 G4 F4   F4 F4 F4 F4   G1      ", "4/4")
    >>> ossiastream = converter.parse(" r1            r1    r1        E4 E4 F4 G4   r1         F2    F2      r1      ", "4/4")
    >>> mainstream.makeMeasures(inPlace = True)
    >>> ossiastream.makeMeasures(inPlace = True)
    
    >>> # mainstream.__class__ = stream.Part
    >>> mainpart = stream.Part()
    >>> for m in mainstream:
    ...    mainpart.insert(m.offset, m)
    >>> ossiapart = stream.Part()
    >>> for m in ossiastream:
    ...    ossiapart.insert(m.offset, m)
    
    >>> s = stream.Stream()
    >>> s.insert(0.0, ossiapart)
    >>> s.insert(0.0, mainpart)
    >>> #_DOCS_SHOW s.show()
    
    >>> mainpartWithOssiaVariantsFT = variant.mergePartAsOssia(mainpart, ossiapart,
    ...                                                            ossiaName = 'Parisian Variant',
    ...                                                            inPlace = False,
    ...                                                            compareByMeasureNumber = False,
    ...                                                            recurseInMeasures = True)
    >>> mainpartWithOssiaVariantsTT = variant.mergePartAsOssia(mainpart, ossiapart,
    ...                                                            ossiaName = 'Parisian Variant',
    ...                                                            inPlace = False,
    ...                                                            compareByMeasureNumber = True,
    ...                                                            recurseInMeasures = True)
    >>> mainpartWithOssiaVariantsFF = variant.mergePartAsOssia(mainpart, ossiapart,
    ...                                                            ossiaName = 'Parisian Variant',
    ...                                                            inPlace = False,
    ...                                                            compareByMeasureNumber = False,
    ...                                                            recurseInMeasures = False)
    >>> mainpartWithOssiaVariantsTF = variant.mergePartAsOssia(mainpart, ossiapart,
    ...                                                            ossiaName = 'Parisian Variant',
    ...                                                            inPlace = False,
    ...                                                            compareByMeasureNumber = True,
    ...                                                            recurseInMeasures = False)
                                                                
    >>> mainpartWithOssiaVariantsFT.show('text') == mainpartWithOssiaVariantsTT.show('text')
    {0.0} <music21.stream.Measure ...
    True
    
    >>> mainpartWithOssiaVariantsFF.show('text') == mainpartWithOssiaVariantsFT.show('text')
    {0.0} <music21.stream.Measure ...
    True
    
    >>> mainpartWithOssiaVariantsFT.show('text')
    {0.0} <music21.stream.Measure 1 offset=0.0>
    ...
    {12.0} <music21.stream.Measure 4 offset=12.0>
        {0.0} <music21.variant.Variant object at ...>
        {0.0} <music21.note.Note E>
        {0.5} <music21.note.Note F>
        {1.0} <music21.note.Note F>
        {2.0} <music21.note.Note G>
    {16.0} <music21.stream.Measure 5 offset=16.0>
    ...
    {20.0} <music21.stream.Measure 6 offset=20.0>
        {0.0} <music21.variant.Variant object at ...>
        {0.0} <music21.note.Note F>
        {1.0} <music21.note.Note F>
        {2.0} <music21.note.Note F>
        {3.0} <music21.note.Note F>
    ...
    
    >>> mainpartWithOssiaVariantsFF.activateVariants('Parisian Variant').show('text')
    {0.0} <music21.stream.Measure 1 offset=0.0>
    ...
    {12.0} <music21.variant.Variant object at ...>
    {12.0} <music21.stream.Measure 4 offset=12.0>
        {0.0} <music21.note.Note E>
        {1.0} <music21.note.Note E>
        {2.0} <music21.note.Note F>
        {3.0} <music21.note.Note G>
    {16.0} <music21.stream.Measure 5 offset=16.0>
    ...
    {20.0} <music21.variant.Variant object at ...>
    {20.0} <music21.stream.Measure 6 offset=20.0>
        {0.0} <music21.note.Note F>
        {2.0} <music21.note.Note F>
    ...
    
    '''
    if inPlace is True:
        returnObj = mainpart
    else:
        returnObj = copy.deepcopy(mainpart)
    
    if compareByMeasureNumber is True:
        for ossiaMeasure in ossiapart.getElementsByClass("Measure"):
            if len(ossiaMeasure.notes) > 0: #If the measure is not just rests
                ossiaNumber = ossiaMeasure.number
                returnMeasure = returnObj.measure(ossiaNumber)
                if recurseInMeasures is True: 
                    mergeVariantStreams([returnMeasure, ossiaMeasure], [ossiaName], inPlace = True)
                else:
                    ossiaOffset = returnMeasure.getOffsetBySite(returnObj)
                    addVariant(returnObj, ossiaOffset, ossiaMeasure, variantName = ossiaName, variantGroups = None, replacementDuration = None)
    else:
        for ossiaMeasure in ossiapart.getElementsByClass("Measure"):
            if len(ossiaMeasure.notes) > 0: #If the measure is not just rests
                ossiaOffset = ossiaMeasure.getOffsetBySite(ossiapart)
                if recurseInMeasures is True:
                    returnMeasure = returnObj.getElementsByOffset(ossiaOffset, classList = [stream.Measure])[0]
                    mergeVariantStreams([returnMeasure, ossiaMeasure], [ossiaName], inPlace = True)
                else:
                    addVariant(returnObj, ossiaOffset, ossiaMeasure, variantName = ossiaName, variantGroups = None, replacementDuration = None)
        
    if inPlace is True:
        return
    else:
        return returnObj


#-------------------------------------------------------------------------------
# classes



class VariantException(Exception):
    pass

class Variant(music21.Music21Object):
    '''A Music21Object that stores elements like a Stream, but does not represent itself externally to a Stream; i.e., the contents of a Variant are not flattened.

    This is accomplished not by subclassing, but by object composition: similar to the Spanner, the Variant contains a Stream as a private attribute. Calls to this Stream, for the Variant, are automatically delegated by use of the __getattr__ method. Special casses are overridden or managed as necessary: e.g., the Duration of a Variant is generally always zero. 

    To use Variants from a Stream, see the :func:`~music21.stream.Stream.activateVariants` method. 

    >>> from music21 import *
    >>> v = variant.Variant()
    >>> v.repeatAppend(note.Note(), 8)
    >>> len(v.notes)
    8
    >>> v.highestTime
    0.0
    >>> v.duration # handled by Music21Object
    <music21.duration.Duration 0.0>
    >>> v.isStream
    False

    >>> s = stream.Stream()
    >>> s.append(v)
    >>> s.append(note.Note())
    >>> s.highestTime
    1.0
    >>> s.show('t') # doctest: +ELLIPSIS
    {0.0} <music21.variant.Variant object at ...>
    {0.0} <music21.note.Note C>
    >>> s.flat.show('t') # doctest: +ELLIPSIS
    {0.0} <music21.variant.Variant object at ...>
    {0.0} <music21.note.Note C>
    '''

    classSortOrder = 0  # variants should always come first?
    isVariant = True

    # this copies the init of Streams
    def __init__(self, givenElements=None, *args, **keywords):
        music21.Music21Object.__init__(self)
        self._cache = {}
        self.exposeTime = False
        self._stream = stream.VariantStorage(givenElements=givenElements, 
                                             *args, **keywords)
        
        self._replacementDuration = None

    def __deepcopy__(self, memo):
        new = self.__class__()
        old = self
        for name in self.__dict__.keys():
            if name.startswith('__'):
                continue
            if name == '_cache':
                continue
            part = getattr(self, name)
            # functionality duplicated from Music21Object
            if name == '_activeSite':
                setattr(new, name, self.activeSite)
            elif name == '_definedContexts':
                newValue = copy.deepcopy(part, memo)
                newValue.containedById = id(new)
                setattr(new, name, newValue)
            # do not deepcopy _components, as this will copy the 
            # contained objects
            # this means that the new object is not really free of the 
            # old elements it described
            elif name == '_stream':
                # this passes references; does not copy contained
                #for c in old._stream:
                #    new._stream.insert(c.getOffsetBySite(old._stream), c)
                # this copies the contained stream
                new._stream = copy.deepcopy(old._stream)
            else: 
                #environLocal.printDebug(['Spanner.__deepcopy__', name])
                newValue = copy.deepcopy(part, memo)
                setattr(new, name, newValue)
        # do after all other copying
        new._idLastDeepCopyOf = id(self)
        return new


    #---------------------------------------------------------------------------
    # as _stream is a private Stream, unwrap/wrap methods need to override
    # Music21Object to get at these objects 
    # this is the same as with Spanners

    def purgeOrphans(self):
        self._stream.purgeOrphans()
        music21.Music21Object.purgeOrphans(self)

    def purgeLocations(self, rescanIsDead=False):
        # must override Music21Object to purge locations from the contained
        self._stream.purgeLocations(rescanIsDead=rescanIsDead)
        music21.Music21Object.purgeLocations(self, rescanIsDead=rescanIsDead)

    def unwrapWeakref(self):
        '''Overridden method for unwrapping all Weakrefs.
        '''
        # call base method: this gets defined contexts and active site
        music21.Music21Object.unwrapWeakref(self)
        # for contained objects that have weak refs
        self._stream.unwrapWeakref()
        # this presently is not a weakref but in case of future changes


    def wrapWeakref(self):
        '''Overridden method for unwrapping all Weakrefs.
        '''
        # call base method: this gets defined contexts and active site
        music21.Music21Object.wrapWeakref(self)
        self._stream.wrapWeakref()


    def freezeIds(self):
        music21.Music21Object.freezeIds(self)
        self._stream.freezeIds()

    def unfreezeIds(self):
        music21.Music21Object.unfreezeIds(self)
        self._stream.unfreezeIds()


    '''
    def __repr__(self):
        return "<music21.variant.%s offset=%s groups=%s>" % \
            (self.__class__.__name__, self.offset, self.groups)
    '''
    
    def __getattr__(self, attr):
        '''This defers all calls not defined in this Class to calls on the privately contained Stream.
        '''
        #environLocal.pd(['relaying unmatched attribute request to private Stream'])

        # must mask pitches so as not to recurse
        # TODO: check tt recurse does not go into this
        if attr in ['flat', 'pitches']: 
            raise AttributeError
        try:
            return getattr(self._stream, attr)
        except:
            raise
        
    def __getitem__(self, key):
        return self._stream.__getitem__(key)
        

    def __len__(self):
        return len(self._stream)


    def getElementIds(self):
        if 'elementIds' not in self._cache or self._cache['elementIds'] is None:
            self._cache['elementIds'] = [id(c) for c in self._stream._elements]
        return self._cache['elementIds']


    def replaceElement(self, old, new):
        '''When copying a Variant, we need to update the Variant with new references for copied elements. Given the old component, this method will replace the old with the new.

        The `old` parameter can be either an object or object id. 

        This method is very similar to the replaceComponent method on Spanner. 

        >>> from music21 import *
        >>> n1 = note.Note('g')
        >>> n2 = note.Note('f#')
        >>> c1 = clef.AltoClef()
        >>> c2 = clef.BassClef()
        >>> sl = spanner.Spanner(n1, n2, c1)
        >>> sl.replaceComponent(c1, c2)
        >>> sl[-1] == c2
        True
        '''
        if old is None:
            return None # do nothing
        if common.isNum(old):
            # this must be id(obj), not obj.id
            e = self._stream.getElementByObjectId(old)
            if e is not None:
                self._stream.replace(e, new, allTargetSites=False)
        else:
            # do not do all Sites: only care about this one
            self._stream.replace(old, new, allTargetSites=False)


    #---------------------------------------------------------------------------
    # Stream  simulation/overrides

    def _getHighestTime(self):
        if self.exposeTime:
            return self._stream.highestTime
        else:
            return 0.0

    highestTime = property(_getHighestTime, doc='''
        This property masks calls to Stream.highestTime. Assuming `exposeTime` is False, this always returns zero, making the Variant always take zero time. 

        >>> from music21 import *
        >>> v = variant.Variant()
        >>> v.append(note.Note(quarterLength=4))
        >>> v.highestTime
        0.0

        ''')

    def _getHighestOffset(self):
        if self.exposeTime:
            return self._stream.highestOffset
        else:
            return 0.0

    highestOffset = property(_getHighestOffset, doc='''
        This property masks calls to Stream.highestOffset. Assuming `exposeTime` is False, this always returns zero, making the Variant always take zero time. 

        >>> from music21 import *
        >>> v = variant.Variant()
        >>> v.append(note.Note(quarterLength=4))
        >>> v.highestOffset
        0.0

        ''')

    def show(self, fmt=None, app=None):
        '''
        Call show() on the Stream contained by this Variant. 

        This method must be overridden, otherwise Music21Object.show() is called.

        >>> from music21 import *
        >>> v = variant.Variant()
        >>> v.repeatAppend(note.Note(quarterLength=.25), 8)
        >>> v.show('t')
        {0.0} <music21.note.Note C>
        {0.25} <music21.note.Note C>
        {0.5} <music21.note.Note C>
        {0.75} <music21.note.Note C>
        {1.0} <music21.note.Note C>
        {1.25} <music21.note.Note C>
        {1.5} <music21.note.Note C>
        {1.75} <music21.note.Note C>
        '''
        self._stream.show(fmt=fmt, app=app)



    #---------------------------------------------------------------------------
    # particular to this class

    def _getContainedHighestTime(self):
        return self._stream.highestTime

    containedHighestTime = property(_getContainedHighestTime, doc='''
        This property calls the contained Stream.highestTime.

        >>> from music21 import *
        >>> v = variant.Variant()
        >>> v.append(note.Note(quarterLength=4))
        >>> v.containedHighestTime
        4.0
        ''')

    def _getContainedHighestOffset(self):
        return self._stream.highestOffset

    containedHighestOffset = property(_getContainedHighestOffset, doc='''
        This property calls the contained Stream.highestOffset.

        >>> from music21 import *
        >>> v = variant.Variant()
        >>> v.append(note.Note(quarterLength=4))
        >>> v.append(note.Note())
        >>> v.containedHighestOffset
        4.0

        ''')

    def _getContainedSite(self):
        return self._stream

    containedSite = property(_getContainedSite, doc='''
        Return a reference to the Stream contained in this Variant.
        ''')
    
    def _getReplacementDuration(self):
        if self._replacementDuration is None:
            return self._stream.duration.quarterLength
        else:
            return self._replacementDuration
    
    def _setReplacementDuration(self, value):
        self._replacementDuration = value
    
    replacementDuration = property(_getReplacementDuration, _setReplacementDuration, doc='''
        Set or Return the quarterLength duration in the main stream which this variant
        object replaces in the variant version of the stream. If replacementDuration is
        not set, it is assumed to be the same length as the variant. If, it is set to 0,
        the variant should be interpreted as an insertion. Setting replacementDuration
        to None will return the value to the default which is the duration of the variant
        itself.
        ''')
    
    def _getLengthType(self):
        lengthDifference = self.replacementDuration - self.containedHighestTime
        if lengthDifference > 0.0:
            return 'deletion'
        elif lengthDifference < 0.0:
            return 'elongation'
        else:
            return 'replacement'
    
    lengthType = property(_getLengthType, doc='''
        Returns 'deletion' if variant is shorter than the region it replaces, 'elongation'
        if the variant is longer than the region it replaces, and 'replacement' if it is
        the same length.
        ''')

#-------------------------------------------------------------------------------
# class VariantBundle(object):
#     '''A utility object for processing collections of Varaints. 
# 
#     This object serves a very similar purpose as the SpannerBundle; Variants and Spanners are similar in design and both require special handling in copying. 
#     '''
# 
#     def __init__(self, *arguments, **keywords):
#         self._storage = [] # a simple list, not a Stream
#         for arg in arguments:
#             if common.isListLike(arg):
#                 for e in arg:
#                     self._storage.append(e)    
#             # take a Stream and use its .variants property to get all Variants            
#             elif arg.isStream:
#                 for e in arg.variants:
#                     self._storage.append(e)
#             # assume its a spanner
#             elif 'Variant' in arg.classes:
#                 self._storage.append(arg)
# 
# 
#     def __len__(self):
#         return len(self._storage)
# 
#     def __repr__(self):
#         return '<music21.variant.VariantBundle of size %s>' % self.__len__()
# 
#     def replaceElement(self, old, new):
#         '''Given a variant component (an object), replace all old components with new components for all Variant objects contained in this bundle.
# 
#         The `old` parameter can be either an object or object id. 
# 
#         If no replacements are found, no errors are raised.
#         '''
#         # idTarget is the old id that we want to replace
#         if common.isNum(old): # assume this is an id
#             idTarget = old
#         else:
#             idTarget = id(old)
# 
#         # looking at each variant, if we w find that it includes an id to 
#         # an object listed as old, replace it with the object listed as new
#         for v in self._storage: # Variants in a list
#             if idTarget in v.getElementIds():
#                 v.replaceElement(old, new)



#-------------------------------------------------------------------------------


class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testBasicA(self):
        from music21 import variant, stream, note

        o = variant.Variant()
        o.append(note.Note('G3', quarterLength=2.0))
        o.append(note.Note('f3', quarterLength=2.0))
        
        self.assertEqual(o.highestOffset, 0)
        self.assertEqual(o.highestTime, 0)

        o.exposeTime = True

        self.assertEqual(o.highestOffset, 2.0)
        self.assertEqual(o.highestTime, 4.0)


    def testBasicB(self):
        '''Testing relaying attributes requests to private Stream with __getattr__
        '''
        from music21 import variant, stream, note

        v = variant.Variant()
        v.append(note.Note('G3', quarterLength=2.0))
        v.append(note.Note('f3', quarterLength=2.0))
        # these are Stream attributes
        self.assertEqual(v.highestOffset, 0.0)
        self.assertEqual(v.highestTime, 0.0)

        self.assertEqual(len(v.notes), 2)
        self.assertEqual(v.hasElementOfClass('Note'), True)
        v.pop(1) # remove the last tiem

        self.assertEqual(v.highestOffset, 0.0)
        self.assertEqual(v.highestTime, 0.0)
        self.assertEqual(len(v.notes), 1)

        #v.show('t')

    def testVariantGroupA(self):
        '''Variant groups are used to distinguish
        '''
        from music21 import variant
        v1 = variant.Variant()
        v1.groups.append('alt-a')

        v1 = variant.Variant()
        v1.groups.append('alt-b')
        self.assertEqual('alt-b' in v1.groups, True)


    def testVariantClassA(self):
        from music21 import stream, variant, note

        m1 = stream.Measure()
        v1 = variant.Variant()
        v1.append(m1)

        self.assertEqual(v1.isClassOrSubclass(['Variant']), True)

        self.assertEqual(v1.hasElementOfClass('Variant'), False)
        self.assertEqual(v1.hasElementOfClass('Measure'), True)

    def testDeepCopyVariantA(self):
        from music21 import note, stream, variant
    
        s = stream.Stream()
        s.repeatAppend(note.Note('G4'), 8)
        vn1 = note.Note('F#4')
        vn2 = note.Note('A-4')
    
        v1 = variant.Variant([vn1, vn2])
        v1Copy = copy.deepcopy(v1)
        # copies stored objects; they point to the different Notes vn1/vn2
        self.assertEqual(v1Copy[0] is v1[0], False)
        self.assertEqual(v1Copy[1] is v1[1], False)
        self.assertEqual(v1[0] is vn1, True)
        self.assertEqual(v1Copy[0] is vn1, False)
    
        # normal in-place variant functionality
        s.insert(5, v1)
        self.assertEqual(str([p for p in s.pitches]), 
            '[G4, G4, G4, G4, G4, G4, G4, G4]')
        sv = s.activateVariants(inPlace=False)
        self.assertEqual(str([p for p in sv.pitches]), 
            '[G4, G4, G4, G4, G4, F#4, A-4, G4, G4]')
    
        # test functionality on a deepcopy    
        sCopy = copy.deepcopy(s)
        self.assertEqual(len(sCopy.variants), 1)
        self.assertEqual(str([p for p in sCopy.pitches]), 
            '[G4, G4, G4, G4, G4, G4, G4, G4]')
        sCopy.activateVariants(inPlace=True)
        self.assertEqual(str([p for p in sCopy.pitches]), 
            '[G4, G4, G4, G4, G4, F#4, A-4, G4, G4]')


    def testDeepCopyVariantB(self):
        from music21 import note, stream, variant
    
        s = stream.Stream()
        s.repeatAppend(note.Note('G4'), 8)
        vn1 = note.Note('F#4')
        vn2 = note.Note('A-4')
        v1 = variant.Variant([vn1, vn2])
        s.insert(5, v1)
    
        # as we deepcopy the elements in the variants, we have new Notes
        sCopy = copy.deepcopy(s)
        sCopy.activateVariants(inPlace=True)
        self.assertEqual(str([p for p in sCopy.pitches]), 
            '[G4, G4, G4, G4, G4, F#4, A-4, G4, G4]')
        # can transpose the note in place
        sCopy.notes[5].transpose(12, inPlace=True)
        self.assertEqual(str([p for p in sCopy.pitches]), 
            '[G4, G4, G4, G4, G4, F#5, A-4, G4, G4]')
    
        # however, if the the Variant deepcopy still references the original
        # notes it had, then when we try to activate the variant in the 
        # in original Stream, we would get unexpected results (the octave shift)
    
        s.activateVariants(inPlace=True)
        self.assertEqual(str([p for p in s.pitches]), 
            '[G4, G4, G4, G4, G4, F#4, A-4, G4, G4]')



#     def testVariantBundleA(self):
#         from music21 import note, stream, variant
# 
#         s = stream.Stream()
#         s.repeatAppend(note.Note('G4'), 8)
#         vn1 = note.Note('F#4')
#         vn2 = note.Note('A-4')
#         v1 = variant.Variant([vn1, vn2])
#         s.insert(5, v1)
# 
#         vb = s.variantBundle
#         self.assertEqual(str(vb), '<music21.variant.VariantBundle of size 1>')
#         self.assertEqual(len(vb), 1) # has one variant

if __name__ == "__main__":
    music21.mainTest(Test)
    