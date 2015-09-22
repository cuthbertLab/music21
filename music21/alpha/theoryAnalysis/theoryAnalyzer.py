# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         theoryAnalyzer.py
# Purpose:      Framework for analyzing music theory aspects of a score
#
# Authors:      Beth Hadley
#               Lars Johnson
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2009-2015 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------

'''
===========================================
Module Introduction
===========================================

Theory Analyzer methods provide easy analysis tools for common music theory type queries regarding
a :class:`~music21.stream.Score` (**must have parts**), such as finding the parallel fifths, 
locating the passing tones, finding
dissonant harmonic intervals, etc. These analysis methods typically operate in the following way:

1. the score is automatically parsed into small bits for analysis (such as 
   :class:`~music21.voiceLeading.Verticality`, 
   :class:`~music21.voiceLeading.VoiceLeadingQuartet`,  etc.)
2. these bits are analyzed for certain attributes, according to analysis 
   methods in :class:`~music21.voiceLeading`
3. the results are stored in the score's analysisData dictionary, 
   (and also returned as a list depending on which method is called)

===========================================
Example Module Uses
===========================================

**get voiceLeading objects from a score**
these methods break the score up into voiceLeading atoms, and return objects of that type. 
These objects are then useful
because they provide easy access to the components within them, and 
those components (notes, chords, etc.) contain
a direct pointer to the original object in the score.

* :meth:`~music21.alpha.theoryAnalysis.theoryAnalyzer.getVerticalities` 
* :meth:`~music21.alpha.theoryAnalysis.theoryAnalyzer.getVLQs` 
* :meth:`~music21.alpha.theoryAnalysis.theoryAnalyzer.getThreeNoteLinearSegments` 
* :meth:`~music21.alpha.theoryAnalysis.theoryAnalyzer.getLinearSegments` 
* :meth:`~music21.alpha.theoryAnalysis.theoryAnalyzer.getVerticalityNTuplets` 
* :meth:`~music21.alpha.theoryAnalysis.theoryAnalyzer.getHarmonicIntervals` 
* :meth:`~music21.alpha.theoryAnalysis.theoryAnalyzer.getMelodicIntervals` 

You can then iterate through these objects and access the attributes directly. Here is an example
of this that will analyze the root motion in a score:

    
    >>> p = corpus.parse('leadsheet').flat.getElementsByClass('Harmony')
    >>> p = harmony.realizeChordSymbolDurations(p)
    >>> averageMotion = 0
    >>> l = alpha.theoryAnalysis.theoryAnalyzer.getLinearSegments(p,0,2, ['Harmony']) 
    >>> # gets a list of tuples, adjacent chord symbol objects in the score
    >>> for x in l:
    ...    averageMotion += abs(x.rootInterval().intervalClass) 
    >>> #rootInterval() returns the interval between the roots of the first chordSymbol and second
    >>> averageMotion = averageMotion // len(l)
    >>> averageMotion #average intervalClass in this piece is about 4
    4
    
**get only interesting music theory voiceLeading objects from a score**
These methods return voiceLeading objects identified by certain methods. For example,
they may return all the parallel fifths in the score as voiceLeadingQuartetObjects.

* :meth:`~music21.alpha.theoryAnalysis.theoryAnalyzer.getHarmonicIntervals` 
* :meth:`~music21.alpha.theoryAnalysis.theoryAnalyzer.getMelodicIntervals` 
* :meth:`~music21.alpha.theoryAnalysis.theoryAnalyzer.getParallelFifths` 
* :meth:`~music21.alpha.theoryAnalysis.theoryAnalyzer.getPassingTones` 
* :meth:`~music21.alpha.theoryAnalysis.theoryAnalyzer.getNeighborTones` 

**identify music theory objects in score**
These identify methods were the original purpose of theoryAnalyzer, to identify interesting
music theory anomalies in a score, color them, and write specific text regarding them. 
However, if you find these methods more
useful as 'get' methods (such as those above), merely run the identify method and 
access the score's ``self.analysisData['dictKey']``

* :meth:`~music21.alpha.theoryAnalysis.theoryAnalyzer.identifyParallelFifths` 
* :meth:`~music21.alpha.theoryAnalysis.theoryAnalyzer.identifyParallelOctaves` 
* :meth:`~music21.alpha.theoryAnalysis.theoryAnalyzer.identifyParallelUnisons` 
* :meth:`~music21.alpha.theoryAnalysis.theoryAnalyzer.identifyHiddenFifths` 
* :meth:`~music21.alpha.theoryAnalysis.theoryAnalyzer.identifyHiddenOctaves`
* :meth:`~music21.alpha.theoryAnalysis.theoryAnalyzer.identifyImproperResolutions` 
* :meth:`~music21.alpha.theoryAnalysis.theoryAnalyzer.identifyLeapNotSetWithStep` 
* :meth:`~music21.alpha.theoryAnalysis.theoryAnalyzer.identifyOpensIncorrectly` 
* :meth:`~music21.alpha.theoryAnalysis.theoryAnalyzer.identifyClosesIncorrectly` 
* :meth:`~music21.alpha.theoryAnalysis.theoryAnalyzer.identifyPassingTones`
* :meth:`~music21.alpha.theoryAnalysis.theoryAnalyzer.identifyDissonantHarmonicIntervals` 
* :meth:`~music21.alpha.theoryAnalysis.theoryAnalyzer.identifyImproperDissonantIntervals`
* :meth:`~music21.alpha.theoryAnalysis.theoryAnalyzer.identifyDissonantMelodicIntervals` 
* :meth:`~music21.alpha.theoryAnalysis.theoryAnalyzer.identifyObliqueMotion` 
* :meth:`~music21.alpha.theoryAnalysis.theoryAnalyzer.identifySimilarMotion` 
* :meth:`~music21.alpha.theoryAnalysis.theoryAnalyzer.identifyParallelMotion`
* :meth:`~music21.alpha.theoryAnalysis.theoryAnalyzer.identifyContraryMotion` 
* :meth:`~music21.alpha.theoryAnalysis.theoryAnalyzer.identifyOutwardContraryMotion`
* :meth:`~music21.alpha.theoryAnalysis.theoryAnalyzer.identifyInwardContraryMotion` 
* :meth:`~music21.alpha.theoryAnalysis.theoryAnalyzer.identifyAntiParallelMotion` 
* :meth:`~music21.alpha.theoryAnalysis.theoryAnalyzer.identifyTonicAndDominantRomanNumerals` 
* :meth:`~music21.alpha.theoryAnalysis.theoryAnalyzer.identifyHarmonicIntervals`
* :meth:`~music21.alpha.theoryAnalysis.theoryAnalyzer.identifyScaleDegrees` 
* :meth:`~music21.alpha.theoryAnalysis.theoryAnalyzer.identifyMotionType`
* :meth:`~music21.alpha.theoryAnalysis.theoryAnalyzer.identifyCommonPracticeErrors`

**special use case: remove passing tones/neighbor tones**
These methods provide a preliminary implementation for removing passing tones and 
neighbor tones from a score.
As an example, the steps involved in these methods calls include:

1. break the score into Verticalities 
2. forms verticalityTriplets out of these vertical slices 
3. break each verticalityTriplet into threeNoteLinearSegments 
4. check to see if the threeNoteLinearSegment couldBePassingTone() or 
   couldBeNeighborTone() (horizontal analysis) 
5. check to see if the Verticality identified as a possible passingTone or neighborTone is dissonant
6. check to see if previous Verticality and next Verticality isdissonant
7. if all checks are true, the passingTone or neighborTone is removed from the score 
   (because the whole point of parsing the score into voiceLeadingObjects was to 
   maintain a direct pointer to the original object in the score.)
8. the gap created by the deletion is filled in by extending the duration of the previous note

    
>>> p = corpus.parse('bwv6.6').measures(0,20)
>>> #_DOCS_SHOW p.show()
    .. image:: images/completebach.*
    :width: 500
        
>>> alpha.theoryAnalysis.theoryAnalyzer.removePassingTones(p)
>>> alpha.theoryAnalysis.theoryAnalyzer.removeNeighborTones(p)
>>> #_DOCS_SHOW p.show()
    .. image:: images/bachnononharm.*
    :width: 500

===========================================
Detailed Method Documentation
===========================================


OMIT_FROM_DOCS
This module was originally written for the WWNorton theory checking project, 
but re-factored to provide a more
general interface to identifying common music-theory type analysis of a score. 
Thus, most methods are 'identify'
methods, which color the score, print to the result dict, etc. 
If this module were to be re-written, all 'identify'
methods should be changed to 'get' methods and return lists of notable atoms, 
and one single identify method should
be written to color/write comments, etc. But for now, all methods serve their 
purpose and the appropriate get methods
can easily be written (reference getPassingTones for example)
'''

import music21

from music21 import common
from music21 import corpus
from music21 import interval
from music21 import voiceLeading
from music21 import roman
from music21 import note
from music21 import chord
from music21 import key
from music21.alpha.theoryAnalysis import theoryResult

import string
import unittest
    
from collections import defaultdict

from music21 import environment
_MOD = 'theoryAnalyzer.py'
environLocal = environment.Environment(_MOD)

_DOC_ORDER = ['getVerticalities', 'getVLQs', 'getThreeNoteLinearSegments', 
              'getLinearSegments', 'getVerticalityNTuplets','getHarmonicIntervals', 
              'getMelodicIntervals', 'getParallelFifths', 'getPassingTones', 
              'getNeighborTones','getParallelOctaves', 'identifyParallelFifths',  
              'identifyParallelOctaves', 'identifyParallelUnisons',
              'identifyHiddenFifths', 'identifyHiddenOctaves', 'identifyImproperResolutions',
              'identifyLeapNotSetWithStep', 'identifyOpensIncorrectly', 'identifyClosesIncorrectly',
              'identifyPassingTones', 'removePassingTones', 'identifyNeighborTones', 
              'removeNeighborTones', 'identifyDissonantHarmonicIntervals', 
              'identifyImproperDissonantIntervals',
              'identifyDissonantMelodicIntervals', 'identifyObliqueMotion', 'identifySimilarMotion', 
              'identifyParallelMotion',
              'identifyContraryMotion', 'identifyOutwardContraryMotion', 
              'identifyInwardContraryMotion', 'identifyAntiParallelMotion', 
              'identifyTonicAndDominantRomanNumerals', 'identifyHarmonicIntervals', 
              'identifyScaleDegrees', 'identifyMotionType', 
              'identifyCommonPracticeErrors',
              'addAnalysisData', 'removeFromAnalysisData', 'setKeyMeasureMap', 
              'getKeyMeasureMap','getKeyAtMeasure',
              'getResultsString', 'colorResults', 'getHTMLResultsString', 
              'getAllPartNumPairs', 'getNotes'
            ]


def addAnalysisData(score):
    '''
    adds an attribute "analysisData" to a Stream object if it does not exist.

    also adds to any embedded Streams...
    
    >>> p = stream.Part()
    >>> s = stream.Score()
    >>> s.insert(0, p)
    >>> hasattr(p, 'analysisData')
    False
    >>> hasattr(s, 'analysisData')
    False
    >>> alpha.theoryAnalysis.theoryAnalyzer.addAnalysisData(s)
    >>> hasattr(p, 'analysisData')
    True
    >>> hasattr(s, 'analysisData')
    True
    >>> 'ResultDict' in p.analysisData
    True
    '''
    # adds analysisData if it does not exist...
    if not(hasattr(score, 'analysisData')):
        score.analysisData = defaultdict(list)
        score.analysisData['ResultDict'] = defaultdict(dict)
    for s in score.recurse(streamsOnly = True):
        if not(hasattr(s, 'analysisData')):
            s.analysisData = defaultdict(list)
            s.analysisData['ResultDict'] = defaultdict(dict)
        


#---------------------------------------------------------------------------------------
# Methods to split the score up into little pieces for analysis
# The little pieces are all from voiceLeading.py, such as
# Vertical Slices, VoiceLeadingQuartet, ThreeNoteLinearSegment, and VerticalityNTuplet       
    
def getVerticalities(score, classFilterList=['Note', 'Chord', 'Harmony', 'Rest']):
    '''
    returns a list of :class:`~music21.voiceLeading.Verticality` objects in
    by parsing the score. Note that it uses the combined rhythm of the parts 
    to determine what vertical slices to take. Default is to return only objects of
    type Note, Chord, Harmony, and Rest.

    >>> n1 = note.Note('c5')
    >>> n1.quarterLength = 4
    >>> n2 = note.Note('f4')
    >>> n2.quarterLength = 2
    >>> n3 = note.Note('g4')
    >>> n3.quarterLength = 2
    >>> sc = stream.Score()
    >>> part0 = stream.Part()
    >>> part0.append(n1)
    >>> part1 = stream.Part()
    >>> part1.append(n2)
    >>> part1.append(n3)
    >>> sc.insert(part0)
    >>> sc.insert(part1)
    >>> alpha.theoryAnalysis.theoryAnalyzer.getVerticalities(sc)
    [<music21.voiceLeading.Verticality contentDict=... >, 
     <music21.voiceLeading.Verticality contentDict=... >]
    >>> len(alpha.theoryAnalysis.theoryAnalyzer.getVerticalities(sc))
    2

    >>> sc4 = stream.Score()
    >>> part4 = stream.Part()
    >>> part4.append(chord.Chord(['A','B','C']))
    >>> part4.append(chord.Chord(['A','B','C']))
    >>> part4.append(chord.Chord(['A','B','C']))
    >>> sc4.insert(part4)
    >>> alpha.theoryAnalysis.theoryAnalyzer.getVerticalities(sc4)
    [<music21.voiceLeading.Verticality contentDict=defaultdict(<... 'list'>, {0: [<music21.chord.Chord A B C>]}) >, 
     <music21.voiceLeading.Verticality contentDict=defaultdict(<... 'list'>, {0: [<music21.chord.Chord A B C>]}) >, 
     <music21.voiceLeading.Verticality contentDict=defaultdict(<... 'list'>, {0: [<music21.chord.Chord A B C>]}) >]

    >>> sc3 = stream.Score()
    >>> p1 = stream.Part()
    >>> p1.append(harmony.ChordSymbol('C', quarterLength = 1))
    >>> p1.append(harmony.ChordSymbol('D', quarterLength = 3))
    >>> p1.append(harmony.ChordSymbol('E7', quarterLength = 4))
    >>> sc3.append(p1)
    >>> alpha.theoryAnalysis.theoryAnalyzer.getVerticalities(sc3)
    [<music21.voiceLeading.Verticality contentDict=defaultdict(<... 'list'>, {0: [<music21.harmony.ChordSymbol C>]}) >, 
     <music21.voiceLeading.Verticality contentDict=defaultdict(<... 'list'>, {0: [<music21.harmony.ChordSymbol D>]}) >, 
     <music21.voiceLeading.Verticality contentDict=defaultdict(<... 'list'>, {0: [<music21.harmony.ChordSymbol E7>]}) >]
    '''   
    
    vsList = []
    addAnalysisData(score)
    if 'Verticalities' in score.analysisData and score.analysisData['Verticalities'] != None:
        return score.analysisData['Verticalities']

    # if elements exist at same offset, return both 

    # If speed is an issue, could try using offset maps...
    
    chordifiedSc = score.chordify()
    
    for c in chordifiedSc.flat.getElementsByClass('Chord'):
        contentDict = defaultdict(list)
        partNum= 0
        
        if len(score.parts) > 1:
            for part in score.parts:
                elementStream = part.flat.getElementsByOffset(c.offset, 
                                                              mustBeginInSpan=False, 
                                                              classList=classFilterList)
                #el = part.flat.getElementAtOrBefore(c.offset,classList=['Note','Rest', 'Chord', 'Harmony'])
                for el in elementStream.elements:
                    contentDict[partNum].append(el)    
                partNum +=1
        else:
            elementStream = score.flat.getElementsByOffset(c.offset, 
                                                           mustBeginInSpan=False, 
                                                           classList=classFilterList)
            #el = part.flat.getElementAtOrBefore(c.offset,classList=['Note','Rest', 'Chord', 'Harmony'])
            for el in elementStream.elements:
                contentDict[partNum].append(el)    
            partNum +=1

        vs = voiceLeading.Verticality(contentDict)
        vsList.append(vs)
    if classFilterList == ['Note', 'Chord', 'Harmony', 'Rest']:
        score.analysisData['Verticalities'] = vsList
    
    return vsList
     
def getVLQs(score, partNum1, partNum2):
    '''
    extracts and returns a list of the :class:`~music21.voiceLeading.VoiceLeadingQuartet` 
    objects present between partNum1 and partNum2 in the score

    >>> sc = stream.Score()
    >>> part0 = stream.Part()
    >>> part0.append(note.Note('c4'))
    >>> part0.append(note.Note('g4'))
    >>> part0.append(note.Note('c5'))
    >>> sc.insert(part0)
    >>> part1 = stream.Part()
    >>> part1.append(note.Note('d4'))
    >>> part1.append(note.Note('e4'))
    >>> part1.append(note.Note('f5'))
    >>> sc.insert(part1)
    >>> alpha.theoryAnalysis.theoryAnalyzer.getVLQs(sc, 0, 1)
    [<music21.voiceLeading.VoiceLeadingQuartet v1n1=<music21.note.Note C>, v1n2=<music21.note.Note G>, v2n1=<music21.note.Note D>, v2n2=<music21.note.Note E> >,
     <music21.voiceLeading.VoiceLeadingQuartet v1n1=<music21.note.Note G>, v1n2=<music21.note.Note C>, v2n1=<music21.note.Note E>, v2n2=<music21.note.Note F> >]
    >>> len(alpha.theoryAnalysis.theoryAnalyzer.getVLQs(sc, 0, 1))
    2
    '''
    from music21.stream import timespans
    tsCol = timespans.streamToTimespanTree(score, flatten=True, classList=(note.Note, chord.Chord))
    allVLQs = []
    defaultKey = None
    
    for v in tsCol.iterateVerticalities():
        vlqs = v.getAllVoiceLeadingQuartets(partPairNumbers=[(partNum1, partNum2)])
        for vlq in vlqs:
            newKey = vlq.v1n1.getContextByClass('KeySignature')
            if newKey is None:
                if defaultKey is None:
                    defaultKey = score.analyze('key')
                newKey = defaultKey
            vlq.key = newKey
            #vlq.key = getKeyAtMeasure(score, vlq.v1n1.measureNumber)
        allVLQs.extend(vlqs)
    return allVLQs
    # Caches the list of VLQs once they have been computed
    # for a specified set of partNums
    vlqCacheKey = str(partNum1) + "," + str(partNum2)

    addAnalysisData(score)    
    if 'vlqs' in score.analysisData and vlqCacheKey in score.analysisData['vlqs']:
        return score.analysisData['vlqs'][vlqCacheKey]
    
    vlqList = []
    
    verticalities = getVerticalities(score)
    
    for (i, verticality) in enumerate(verticalities[:-1]):
        nextVerticality = verticalities[i + 1]
        
        v1n1 = verticality.getObjectsByPart(partNum1, classFilterList=['Note'])
        v1n2 = nextVerticality.getObjectsByPart(partNum1, classFilterList=['Note'])
         
        v2n1 = verticality.getObjectsByPart(partNum2, classFilterList=['Note'])
        v2n2 = nextVerticality.getObjectsByPart(partNum2, classFilterList=['Note'])
        
        if v1n1 != None and v1n2 != None and v2n1 != None and v2n2 != None:
            getKeyAtMeasure(score, v1n1.measureNumber)
            
            vlq = voiceLeading.VoiceLeadingQuartet(v1n1, v1n2, v2n1, v2n2, 
                                                   key=getKeyAtMeasure(score, v1n1.measureNumber))
            
            vlqList.append(vlq)
        
    if 'vlqs' not in score.analysisData:
        score.analysisData['vlqs'] = {vlqCacheKey: vlqList}
    else:
        score.analysisData['vlqs'][vlqCacheKey] = vlqList
 
    return vlqList
    
def getThreeNoteLinearSegments(score, partNum):
    '''
    extracts and returns a list of the :class:`~music21.voiceLeading.ThreeNoteLinearSegment` 
    objects present in partNum in the score (three note linear segments are made up of ONLY
    three notes)
    
    >>> sc = stream.Score()
    >>> part0 = stream.Part()
    >>> part0.append(note.Note('c4'))
    >>> part0.append(note.Note('g4'))
    >>> part0.append(note.Note('c5'))
    >>> part0.append(note.Note('c6'))
    >>> sc.insert(part0)
    >>> alpha.theoryAnalysis.theoryAnalyzer.getThreeNoteLinearSegments(sc, 0)
    [<music21.voiceLeading.ThreeNoteLinearSegment n1=<music21.note.Note C> n2=<music21.note.Note G> n3=<music21.note.Note C> >, 
     <music21.voiceLeading.ThreeNoteLinearSegment n1=<music21.note.Note G> n2=<music21.note.Note C> n3=<music21.note.Note C> >]
    >>> len(alpha.theoryAnalysis.theoryAnalyzer.getThreeNoteLinearSegments(sc, 0))
    2
    >>> alpha.theoryAnalysis.theoryAnalyzer.getThreeNoteLinearSegments(sc, 0)[1]
    <music21.voiceLeading.ThreeNoteLinearSegment n1=<music21.note.Note G> n2=<music21.note.Note C> n3=<music21.note.Note C> >
    '''
    # Caches the list of TNLS once they have been computed
    # for a specified partNum
    
    tnlsCacheKey = str(partNum)
    addAnalysisData(score)

    if 'ThreeNoteLinearSegments' in score.analysisData and tnlsCacheKey in score.analysisData['ThreeNoteLinearSegments']:
        return score.analysisData['ThreeNoteLinearSegments'][tnlsCacheKey]
    else:
        if 'ThreeNoteLinearSegments' not in score.analysisData:
            score.analysisData['ThreeNoteLinearSegments'] = {tnlsCacheKey: getLinearSegments(score, partNum, 3, ['Note'])}
        else:
            score.analysisData['ThreeNoteLinearSegments'][tnlsCacheKey] = getLinearSegments(score, partNum, 3, ['Note'])
    return score.analysisData['ThreeNoteLinearSegments'][tnlsCacheKey]

def getLinearSegments(score, partNum, lengthLinearSegment, classFilterList=None):
    '''
    extracts and returns a list of all the linear segments in the piece at 
    the partNum specified, the length of which specified by lengthLinearSegment: 
    Currently Supported: :class:`~music21.voiceLeading.ThreeNoteLinearSegment` 
    
    

    >>> sc = stream.Score()
    >>> part0 = stream.Part()
    >>> part0.append(note.Note('c4'))
    >>> part0.append(note.Note('g4'))
    >>> part0.append(note.Note('c5'))
    >>> part0.append(note.Note('c6'))
    >>> sc.insert(part0)
    >>> len(alpha.theoryAnalysis.theoryAnalyzer.getLinearSegments(sc, 0,3, ['Note']))
    2
    >>> alpha.theoryAnalysis.theoryAnalyzer.getLinearSegments(sc, 0,3, ['Note'])
    [<music21.voiceLeading.ThreeNoteLinearSegment n1=<music21.note.Note C> n2=<music21.note.Note G> n3=<music21.note.Note C> >,
     <music21.voiceLeading.ThreeNoteLinearSegment n1=<music21.note.Note G> n2=<music21.note.Note C> n3=<music21.note.Note C> >]

    >>> sc2 = stream.Score()
    >>> part1 = stream.Part()
    >>> part1.append(chord.Chord(['C','E','G']))
    >>> part1.append(chord.Chord(['G','B','D']))
    >>> part1.append(chord.Chord(['E','G','C']))
    >>> part1.append(chord.Chord(['F','A','C']))
    >>> sc2.insert(part1)
    >>> alpha.theoryAnalysis.theoryAnalyzer.getLinearSegments(sc2, 0,2, ['Chord'])
    [<music21.voiceLeading.TwoChordLinearSegment objectList=[<music21.chord.Chord C E G>, <music21.chord.Chord G B D>]  >,
     <music21.voiceLeading.TwoChordLinearSegment objectList=[<music21.chord.Chord G B D>, <music21.chord.Chord E G C>]  >,
     <music21.voiceLeading.TwoChordLinearSegment objectList=[<music21.chord.Chord E G C>, <music21.chord.Chord F A C>]  >]
    >>> len(alpha.theoryAnalysis.theoryAnalyzer.getLinearSegments(sc2, 0,2, ['Chord']))
    3
    >>> for x in alpha.theoryAnalysis.theoryAnalyzer.getLinearSegments(sc2, 0,2, ['Chord']):
    ...   print("%r %r" % (x.rootInterval(), x.bassInterval()))
    <music21.interval.ChromaticInterval 7> <music21.interval.ChromaticInterval 2>
    <music21.interval.ChromaticInterval -7> <music21.interval.ChromaticInterval -2>
    <music21.interval.ChromaticInterval 5> <music21.interval.ChromaticInterval 0>

    >>> sc3 = stream.Score()
    >>> part2 = stream.Part()
    >>> part2.append(harmony.ChordSymbol('D-', quarterLength = 1))
    >>> part2.append(harmony.ChordSymbol('C11', quarterLength = 1))
    >>> part2.append(harmony.ChordSymbol('C7', quarterLength = 1))
    >>> sc3.insert(part2)
    >>> len(alpha.theoryAnalysis.theoryAnalyzer.getLinearSegments(sc3, 0,2, ['Harmony']))
    2
    >>> alpha.theoryAnalysis.theoryAnalyzer.getLinearSegments(sc3,0,2, ['Harmony'])
    [<music21.voiceLeading.TwoChordLinearSegment objectList=[<music21.harmony.ChordSymbol D->, <music21.harmony.ChordSymbol C11>]  >,
     <music21.voiceLeading.TwoChordLinearSegment objectList=[<music21.harmony.ChordSymbol C11>, <music21.harmony.ChordSymbol C7>]  >]
    '''
    
    linearSegments = []
    #no caching here - possibly implement later on...
    verticalities = getVerticalities(score)

    for i in range(0, len(verticalities)-lengthLinearSegment+1):
        objects = []
        for n in range(0,lengthLinearSegment):
            objects.append(verticalities[i+n].getObjectsByPart(partNum, classFilterList))           
            #print objects
        if lengthLinearSegment == 3 and 'Note' in _getTypeOfAllObjects(objects):
            tnls = voiceLeading.ThreeNoteLinearSegment(objects[0], objects[1], objects[2])
            linearSegments.append(tnls)
        elif lengthLinearSegment == 2 and ('Chord' in _getTypeOfAllObjects(objects)) and None not in objects:
            tcls = voiceLeading.TwoChordLinearSegment(objects[0], objects[1])
            linearSegments.append(tcls)
        else:
            if None not in objects:
                nols = voiceLeading.NObjectLinearSegment(objects)
                linearSegments.append(nols)
    return linearSegments

def _getTypeOfAllObjects(objectList):
    
    setList = []
    for obj in objectList:
        if obj != None:
            setList.append(set(obj.classes))
    if setList:
        lastSet = setList[0]
        
        for setObj in setList:
            newIntersection = lastSet.intersection(setObj)
            lastSet = setObj
        
        return newIntersection
    else: return []

def getVerticalityNTuplets(score, ntupletNum):
    '''
    extracts and returns a list of the :class:`~music21.voiceLeading.VerticalityNTuplet` or the 
    corresponding subclass (currently only supports triplets) 
    
    >>> sc = stream.Score()
    >>> part0 = stream.Part()
    >>> part1 = stream.Part()
    >>> part0.append(note.Note('c4'))
    >>> part0.append(note.Note('g4'))
    >>> part0.append(note.Note('c5'))
    >>> part0.append(note.Note('e6'))
    >>> part1.append(note.Note('e4'))
    >>> part1.append(note.Note('f4'))
    >>> part1.append(note.Note('a5'))
    >>> part1.append(note.Note('d6'))
    >>> sc.insert(part0)
    >>> sc.insert(part1) 
    >>> len(alpha.theoryAnalysis.theoryAnalyzer.getVerticalityNTuplets(sc, 3))
    2
    >>> alpha.theoryAnalysis.theoryAnalyzer.getVerticalityNTuplets(sc, 3)[1]
    <music21.voiceLeading.VerticalityTriplet 
        listofVerticalities=[<music21.voiceLeading.Verticality...>,
                             <music21.voiceLeading.Verticality...>,
                             <music21.voiceLeading.Verticality...>] >
    '''

    verticalityNTuplets = []
    addAnalysisData(score)
    if 'Verticalities' not in score.analysisData:
        verticalities = getVerticalities(score)
    else:
        verticalities = score.analysisData['Verticalities']
        if verticalities == None:
            verticalities = getVerticalities(score)
    for i in range(0, len(verticalities)-(ntupletNum-1)):
        verticalityList = []
        for countNum in range(i,i+ntupletNum):
            verticalityList.append(verticalities[countNum])
        if ntupletNum == 3:
            vsnt = voiceLeading.VerticalityTriplet(verticalityList)
        else: 
            vsnt = voiceLeading.VerticalityNTuplet(verticalityList)
        verticalityNTuplets.append(vsnt)
    return verticalityNTuplets


#---------------------------------------------------------------------------------------
# Method to split the score up into very very small pieces 
#(just notes, just harmonic intervals, or just melodic intervals)
# TODO: consider deleting getNotes method and consider refactoring getHarmonicIntervals()
# and getMelodicIntervals() to be extracted from a vertical Slice

def getHarmonicIntervals(score, partNum1, partNum2):
    '''
    returns a list of all the harmonic intervals (:class:`~music21.interval.Interval` ) 
    occurring between the two specified parts.

    >>> sc = stream.Score()
    >>> part0 = stream.Part()
    >>> part0.append(note.Note('e4'))
    >>> part0.append(note.Note('d4'))
    >>> part1 = stream.Part()
    >>> part1.append(note.Note('a3'))
    >>> part1.append(note.Note('b3'))
    >>> sc.insert(part0)
    >>> sc.insert(part1)
    >>> len(alpha.theoryAnalysis.theoryAnalyzer.getHarmonicIntervals(sc, 0,1))
    2
    >>> alpha.theoryAnalysis.theoryAnalyzer.getHarmonicIntervals(sc, 0,1)[0].name
    'P5'
    >>> alpha.theoryAnalysis.theoryAnalyzer.getHarmonicIntervals(sc, 0,1)[1].name
    'm3'
    '''
    hInvList = []
    verticalities = getVerticalities(score)
    for verticality in verticalities:
        
        nUpper = verticality.getObjectsByPart(partNum1, classFilterList=['Note'])
        nLower = verticality.getObjectsByPart(partNum2, classFilterList=['Note'])
        
        if nLower is None or nUpper is None:
            hIntv = None
        else:
            hIntv = interval.notesToInterval(nLower, nUpper)
        
        hInvList.append(hIntv)
                
    return hInvList

def getMelodicIntervals(score, partNum):
    '''
    returns a list of all the melodic intervals (:class:`~music21.interval.Interval`) 
    in the specified part.

    >>> sc = stream.Score()
    >>> part0 = stream.Part()
    >>> part0.append(note.Note('c4'))
    >>> part0.append(note.Note('g4'))
    >>> part0.append(note.Note('c5'))
    >>> sc.insert(part0)
    >>> alpha.theoryAnalysis.theoryAnalyzer.getMelodicIntervals(sc,0)
    [<music21.interval.Interval P5>, <music21.interval.Interval P4>]
    >>> alpha.theoryAnalysis.theoryAnalyzer.getMelodicIntervals(sc, 0)[0].name
    'P5'
    >>> alpha.theoryAnalysis.theoryAnalyzer.getMelodicIntervals(sc, 0)[1].name
    'P4'
    '''
    mInvList = []
    noteList = score.parts[partNum].flat.getElementsByClass(['Note','Rest'])
    for (i,n1) in enumerate(noteList[:-1]):
        n2 = noteList[i + 1]
        
        if n1.isClassOrSubclass(['Note']) and n2.isClassOrSubclass(['Note']):
            mIntv = interval.notesToInterval(n1, n2)
        else:
            mIntv = None
        
        mInvList.append(mIntv)
                
    return mInvList

def getNotes(score, partNum):
    '''
    returns a list of notes present in the score. If Rests are present, appends None to the list

    >>> sc = stream.Score()
    >>> p = stream.Part()
    >>> p.repeatAppend(note.Note('C'), 3)
    >>> p.append(note.Rest(1.0))
    >>> sc.append(p)
    >>> alpha.theoryAnalysis.theoryAnalyzer.getNotes(sc, 0)
    [<music21.note.Note C>, <music21.note.Note C>, <music21.note.Note C>, None]

    '''
    noteList = []
    noteOrRestList = score.parts[partNum].flat.getElementsByClass(['Note','Rest'])
    for nr in noteOrRestList:
        if nr.isClassOrSubclass(['Note']):
            n = nr
        else:
            n = None
        
        noteList.append(n)
                
    return noteList    

#---------------------------------------------------------------------------------------
# Helper for identifying across all parts - used for recursion in identify functions

def getAllPartNumPairs(score):
    '''
    Gets a list of all possible pairs of partNumbers:
    tuples (partNum1, partNum2) where 0 <= partNum1 < partnum2 < numParts

    >>> sc = stream.Score()
    >>> part0 = stream.Part()
    >>> part0.append(note.Note('c5'))
    >>> part1 = stream.Part()
    >>> part1.append(note.Note('g4'))
    >>> part2 = stream.Part()
    >>> part2.append(note.Note('c4'))
    >>> sc.insert(part0)
    >>> sc.insert(part1)
    >>> sc.insert(part2)
    >>> alpha.theoryAnalysis.theoryAnalyzer.getAllPartNumPairs(sc)
    [(0, 1), (0, 2), (1, 2)]
    >>> alpha.theoryAnalysis.theoryAnalyzer.getAllPartNumPairs(sc)[0]
    (0, 1)
    >>> alpha.theoryAnalysis.theoryAnalyzer.getAllPartNumPairs(sc)[1]
    (0, 2)
    >>> alpha.theoryAnalysis.theoryAnalyzer.getAllPartNumPairs(sc)[2]
    (1, 2)
    '''
    partNumPairs = []
    numParts = len(score.parts)
    for partNum1 in range(0, numParts-1):
        for partNum2 in range(partNum1 + 1, numParts):
            partNumPairs.append((partNum1,partNum2))
    
    return partNumPairs

def _updateScoreResultDict(score, dictKey, tr):
    if 'ResultDict' not in score.analysisData:
        score.analysisData['ResultDict'] = {dictKey : [tr] }
    elif dictKey not in score.analysisData['ResultDict']:
        score.analysisData['ResultDict'][dictKey] = [tr]
    else:
        score.analysisData['ResultDict'][dictKey].append(tr)
#---------------------------------------------------------------------------------------
# Analysis of the score occurs based on the little segments that the score 
# can be divided up into. Each little segment has its own template from which the methods
# can be tested. Each identify method accepts a long list of parameters, as indicated here:
'''
- partNum1 is the first part in the VLQ, partNum2 is the second
- color is the color to mark the VLQ theory result object
- dictKey is the dictionary key in the resultDict to assign the result objects found to
- testFunction is the function to test (if not False is returned, a theory Result object is created)
- textFunction is the function that returns the text as a string to be set as the 
  theory result object's text parameter   
- startIndex is the first VLQ in the list to start with (0 is default). endIndex 
  is the first VLQ in list not to search (length of VLQ list is default), meaning default 
  values are to search the entire vlqList
- if editorialDictKey is specified, the elements in the VLQ as specified by editorialMarkList 
  are assigned the editorialValue

'''
# Template for analysis based on VLQs   

def _identifyBasedOnVLQ(score, partNum1, partNum2, dictKey, testFunction, textFunction=None, 
                        color=None,
                        startIndex=0, endIndex = None, editorialDictKey=None, 
                        editorialValue=None, editorialMarkList=None):
    if editorialMarkList is None:
        editorialMarkList = []
    addAnalysisData(score)

    if partNum1 == None or partNum2 == None:
        for (partNum1,partNum2) in getAllPartNumPairs(score):
            _identifyBasedOnVLQ(score, partNum1, partNum2, dictKey, testFunction, 
                                textFunction, color,
                                startIndex, endIndex, editorialDictKey, 
                                editorialValue, editorialMarkList)
    else:
      
        vlqList = getVLQs(score, partNum1, partNum2)
        if endIndex == None and startIndex >=0:
            endIndex = len(vlqList)
   
        for vlq in vlqList[startIndex:endIndex]:
            
            if testFunction(vlq) is not False: # True or value
                tr = theoryResult.VLQTheoryResult(vlq)
                tr.value = testFunction(vlq)
                if textFunction == None:
                    tr.text = tr.value
                else:    
                    tr.text = textFunction(vlq, partNum1, partNum2)
                if editorialDictKey != None:
                    tr.markNoteEditorial(editorialDictKey, editorialValue, editorialMarkList)
                if color is not None:
                    tr.color(color)
                _updateScoreResultDict(score, dictKey, tr)
                        
def _identifyBasedOnHarmonicInterval(score, partNum1, partNum2, color, dictKey, 
                                     testFunction, textFunction, valueFunction=None):
    addAnalysisData(score)
    if valueFunction == None:
        valueFunction = testFunction
    
    if partNum1 == None or partNum2 == None:
        for (partNum1,partNum2) in getAllPartNumPairs(score):
            _identifyBasedOnHarmonicInterval(score, partNum1, partNum2, color, dictKey, 
                                             testFunction, textFunction, 
                                             valueFunction=valueFunction)
    else:
        hIntvList = getHarmonicIntervals(score, partNum1, partNum2)
        
        for hIntv in hIntvList:
            if testFunction(hIntv) is not False: # True or value
                
                tr = theoryResult.IntervalTheoryResult(hIntv)
                tr.value = valueFunction(hIntv)
                tr.text = textFunction(hIntv, partNum1, partNum2)
               
                if color is not None:
                    tr.color(color)
                _updateScoreResultDict(score, dictKey, tr)
                               
def _identifyBasedOnMelodicInterval(score, partNum, color, dictKey, testFunction, textFunction):
    addAnalysisData(score)    
    if partNum == None:
        for partNum in range(0, len(score.parts)):
            _identifyBasedOnMelodicInterval(score, partNum, color, dictKey, 
                                            testFunction, textFunction)
    else:
        mIntvList = getMelodicIntervals(score, partNum)
        
        for mIntv in mIntvList:
            if testFunction(mIntv) is not False: # True or value
                tr = theoryResult.IntervalTheoryResult(mIntv)
                tr.value = testFunction(mIntv)
                tr.text = textFunction(mIntv, partNum)
                if color is not None:
                    tr.color(color)
                _updateScoreResultDict(score, dictKey, tr)
                
def _identifyBasedOnNote(score, partNum, color, dictKey, testFunction, textFunction): 
    addAnalysisData(score)

    if partNum == None: 
        for partNum in range(0, len(score.parts)):
            _identifyBasedOnNote(score, partNum, color, dictKey, testFunction, textFunction)
    else:
        
        nList = getNotes(score, partNum)
        
        for n in nList:
            if testFunction(score, n) is not False: # True or value
                tr = theoryResult.NoteTheoryResult(n)
                tr.value = testFunction(score, n)
                
                tr.text = textFunction(n, partNum, tr.value)
                if color is not None:
                    tr.color(color)
                _updateScoreResultDict(score, dictKey, tr)
                   
def _identifyBasedOnVerticality(score, color, dictKey, testFunction, 
                                textFunction, responseOffsetMap=None):
    if responseOffsetMap is None:
        responseOffsetMap = []
    addAnalysisData(score)
    if 'Verticalities' not in score.analysisData:
        unused_vslist = getVerticalities(score)
    
    for vs in score.analysisData['Verticalities']:
        if responseOffsetMap and vs.offset(leftAlign=True) not in responseOffsetMap:
            continue
        if testFunction(vs, score) is not False:
            tr = theoryResult.VerticalityTheoryResult(vs)
            tr.value = testFunction(vs, score)
            
            if dictKey == 'romanNumerals' or  dictKey == 'romanNumeralsVandI':
                tr.text = textFunction(vs, tr.value)
            else:
                tr.text = textFunction(vs, score)
            
            _updateScoreResultDict(score, dictKey, tr)

def _identifyBasedOnVerticalityNTuplet(score, partNumToIdentify, dictKey, 
                                       testFunction, textFunction=None, color=None, 
                                       editorialDictKey=None, editorialValue=None, 
                                       editorialMarkDict=None, nTupletNum=3):
    if editorialMarkDict is None:
        editorialMarkDict = {} 

    addAnalysisData(score)
    if partNumToIdentify == None:
        for partNum in range(0,len(score.parts)):
            _identifyBasedOnVerticalityNTuplet(score, partNum, dictKey, testFunction, 
                                               textFunction, color,
                                               editorialDictKey=editorialDictKey, 
                                               editorialValue=editorialValue, 
                                               editorialMarkDict=editorialMarkDict, 
                                               nTupletNum=nTupletNum)
    else:
        for vsnt in getVerticalityNTuplets(score, nTupletNum):
            if testFunction(vsnt, partNumToIdentify) is not False:
                tr = theoryResult.VerticalityNTupletTheoryResult(vsnt, partNumToIdentify)
                if editorialDictKey != None:
                    tr.markNoteEditorial(editorialDictKey, editorialValue, editorialMarkDict)
                if textFunction is not None:
                    tr.text = textFunction(vsnt, partNumToIdentify)
                if color is not None:
                    tr.color(color)
                _updateScoreResultDict(score, dictKey, tr)

def _identifyBasedOnThreeNoteLinearSegment(score, partNum, color, dictKey, 
                                           testFunction, textFunction):            

    addAnalysisData(score)
    if partNum == None:
        for partNum in range(0,len(score.parts)):
            _identifyBasedOnThreeNoteLinearSegment(score, partNum, color, dictKey, 
                                                   testFunction, textFunction)
    else:
        tnlsList = getThreeNoteLinearSegments(score, partNum)

        for tnls in tnlsList:
            if testFunction(tnls) is not False:
                tr = theoryResult.ThreeNoteLinearSegmentTheoryResult(tnls)
                tr.value = testFunction(tnls)
                tr.text = textFunction(tnls, partNum)
                if color is not None: 
                    tr.color(color)
                _updateScoreResultDict(score, dictKey, tr)

#---------------------------------------------------------------------------------------
# Here are the public-interface methods that users call directly on the theory analyzer score 
# these methods call the identify template methods above based
                    
#-------------------------------------------------------------------------------           
# Theory Errors using VLQ template

def identifyParallelFifths(score, partNum1=None, partNum2=None, color=None, dictKey='parallelFifths'):
    '''
    
    Identifies parallel fifths (calls :meth:`~music21.voiceLeading.VoiceLeadingQuartet.parallelFifth`) between 
    two parts (if specified) or between all possible pairs of parts (if not specified) 
    and stores the resulting list of VLQTheoryResult objects in ``score.analysisData['ResultDict']['parallelFifths']``. 
    Optionally, a color attribute may be specified to color all corresponding notes in the score.
    
    

    >>> sc = stream.Score()
    >>> part0 = stream.Part()
    >>> p0measure1 = stream.Measure(number=1)
    >>> p0measure1.append(note.Note('c5'))
    >>> p0measure1.append(note.Note('d5'))
    >>> p0measure1.append(note.Note('e5'))
    >>> p0measure1.append(note.Note('g5'))
    >>> part0.append(p0measure1)
    >>> part1 = stream.Part()
    >>> p1measure1 = stream.Measure(number=1)
    >>> p1measure1.append(note.Note('c4'))
    >>> p1measure1.append(note.Note('g4'))
    >>> p1measure1.append(note.Note('a4'))
    >>> p1measure1.append(note.Note('c4'))
    >>> part1.append(p1measure1)
    >>> sc.insert(part0)
    >>> sc.insert(part1)
    >>> alpha.theoryAnalysis.theoryAnalyzer.identifyParallelFifths(sc)
    >>> len(sc.analysisData['ResultDict']['parallelFifths'])
    2
    >>> sc.analysisData['ResultDict']['parallelFifths'][0].text
    'Parallel fifth in measure 1: Part 1 moves from D to E while part 2 moves from G to A'
    '''
    testFunction = lambda vlq: vlq.parallelFifth()
    textFunction = lambda vlq, pn1, pn2: "Parallel fifth in measure " + str(vlq.v1n1.measureNumber) +": "\
                 + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
                 + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name+ " to " + vlq.v2n2.name
    _identifyBasedOnVLQ(score, partNum1, partNum2, dictKey,testFunction,textFunction, color)

def getParallelFifths(score, partNum1=None, partNum2=None):
    '''
    Identifies all parallel fifths in score, or only the parallel fifths found between partNum1 and partNum2, and
    returns these as instances of :class:`~music21.voiceLeading.VoiceLeadingQuartet`
    
    

    >>> sc = stream.Score()
    >>> part0 = stream.Part()
    >>> p0measure1 = stream.Measure(number=1)
    >>> p0measure1.append(note.Note('c5'))
    >>> p0measure1.append(note.Note('d5'))
    >>> p0measure1.append(note.Note('e5'))
    >>> p0measure1.append(note.Note('g5'))
    >>> part0.append(p0measure1)
    >>> part1 = stream.Part()
    >>> p1measure1 = stream.Measure(number=1)
    >>> p1measure1.append(note.Note('c4'))
    >>> p1measure1.append(note.Note('g4'))
    >>> p1measure1.append(note.Note('a4'))
    >>> p1measure1.append(note.Note('c4'))
    >>> part1.append(p1measure1)
    >>> sc.insert(part0)
    >>> sc.insert(part1)
    >>> alpha.theoryAnalysis.theoryAnalyzer.getParallelFifths(sc)
    [<music21.voiceLeading.VoiceLeadingQuartet v1n1=<music21.note.Note D>, v1n2=<music21.note.Note E>, v2n1=<music21.note.Note G>, v2n2=<music21.note.Note A>  >, 
     <music21.voiceLeading.VoiceLeadingQuartet v1n1=<music21.note.Note E>, v1n2=<music21.note.Note G>, v2n1=<music21.note.Note A>, v2n2=<music21.note.Note C>  >]
    >>> len(sc.analysisData['ResultDict']['parallelFifths'])
    2
    '''
    testFunction = lambda vlq: vlq.parallelFifth()
    _identifyBasedOnVLQ(score, partNum1, partNum2, dictKey='parallelFifths', testFunction=testFunction)

    if score.analysisData['ResultDict'] and 'parallelFifths' in score.analysisData['ResultDict']:
        return [tr.vlq for tr in score.analysisData['ResultDict']['parallelFifths']]
    else:
        return None
    
def identifyParallelOctaves(score, partNum1=None, partNum2=None, 
                            color=None, dictKey='parallelOctaves'):
    '''
    Identifies parallel octaves (calls :meth:`~music21.voiceLeading.VoiceLeadingQuartet.parallelOctave`) between 
    two parts (if specified) or between all possible pairs of parts (if not specified) 
    and stores the resulting list of ``VLQTheoryResult`` objects in ``score.analysisData['ResultDict']['parallelOctaves']``. 
    Optionally, a color attribute may be specified to color all corresponding notes in the score.
    
    

    >>> sc = stream.Score()
    >>> part0 = stream.Part()
    >>> p0measure1 = stream.Measure(number=1)
    >>> p0measure1.append(note.Note('c5'))
    >>> p0measure1.append(note.Note('g5'))
    >>> part0.append(p0measure1)
    >>> part1 = stream.Part()
    >>> p1measure1 = stream.Measure(number=1)
    >>> p1measure1.append(note.Note('c4'))
    >>> p1measure1.append(note.Note('g4'))
    >>> part1.append(p1measure1)
    >>> sc.insert(part0)
    >>> sc.insert(part1)
    >>> alpha.theoryAnalysis.theoryAnalyzer.identifyParallelOctaves(sc)
    >>> len(sc.analysisData['ResultDict']['parallelOctaves'])
    1
    >>> sc.analysisData['ResultDict']['parallelOctaves'][0].text
    'Parallel octave in measure 1: Part 1 moves from C to G while part 2 moves from C to G'
    '''
    
    testFunction = lambda vlq: vlq.parallelOctave()
    textFunction = lambda vlq, pn1, pn2: "Parallel octave in measure " + str(vlq.v1n1.measureNumber) +": "\
                 + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
                 + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name+ " to " + vlq.v2n2.name
    _identifyBasedOnVLQ(score, partNum1, partNum2, dictKey, testFunction, textFunction, color)
    
def getParallelOctaves(score, partNum1=None, partNum2=None):    
    '''
    Identifies all parallel octaves in score (if no part numbers specified), 
    or only the parallel octaves found between partNum1 and partNum2, and
    returns these as instances of :class:`~music21.voiceLeading.VoiceLeadingQuartet`
    
    

    >>> sc = stream.Score()
    >>> part0 = stream.Part()
    >>> p0measure1 = stream.Measure(number=1)
    >>> p0measure1.append(note.Note('c5'))
    >>> p0measure1.append(note.Note('g5'))
    >>> part0.append(p0measure1)
    >>> part1 = stream.Part()
    >>> p1measure1 = stream.Measure(number=1)
    >>> p1measure1.append(note.Note('c4'))
    >>> p1measure1.append(note.Note('g4'))
    >>> part1.append(p1measure1)
    >>> sc.insert(part0)
    >>> sc.insert(part1)
    >>> alpha.theoryAnalysis.theoryAnalyzer.getParallelOctaves(sc)
    [<music21.voiceLeading.VoiceLeadingQuartet v1n1=<music21.note.Note C>, v1n2=<music21.note.Note G>, v2n1=<music21.note.Note C>, v2n2=<music21.note.Note G>  >]
    '''
    testFunction = lambda vlq: vlq.parallelOctave()
    _identifyBasedOnVLQ(score, partNum1, partNum2, dictKey='parallelOctaves', testFunction=testFunction)
    if score.analysisData['ResultDict'] and 'parallelOctaves' in score.analysisData['ResultDict']:
        return [tr.vlq for tr in score.analysisData['ResultDict']['parallelOctaves']]
    else:
        return None
       
def identifyParallelUnisons(score, partNum1=None, partNum2=None, color=None, dictKey='parallelUnisons'):
    '''
    Identifies parallel unisons (calls :meth:`~music21.voiceLeading.VoiceLeadingQuartet.parallelUnison`) between 
    two parts (if specified) or between all possible pairs of parts (if not specified) 
    and stores the resulting list of VLQTheoryResult objects in ``score.analysisData['ResultDict']['parallelUnisons']``. 
    Optionally, a color attribute may be specified to color all corresponding notes in the score.
    
    

    >>> sc = stream.Score()
    >>> part0 = stream.Part()
    >>> p0measure1 = stream.Measure(number=1)
    >>> p0measure1.append(note.Note('c5'))
    >>> p0measure1.append(note.Note('d5'))
    >>> p0measure1.append(note.Note('e5'))
    >>> p0measure1.append(note.Note('f5'))
    >>> part0.append(p0measure1)
    >>> part1 = stream.Part()
    >>> p1measure1 = stream.Measure(number=1)
    >>> p1measure1.append(note.Note('c5'))
    >>> p1measure1.append(note.Note('d5'))
    >>> p1measure1.append(note.Note('e5'))
    >>> p1measure1.append(note.Note('f5'))
    >>> part1.append(p1measure1)
    >>> sc.insert(part0)
    >>> sc.insert(part1)
   
    >>> alpha.theoryAnalysis.theoryAnalyzer.identifyParallelUnisons(sc)
    >>> len(sc.analysisData['ResultDict']['parallelUnisons'])
    3
    >>> sc.analysisData['ResultDict']['parallelUnisons'][2].text
    'Parallel unison in measure 1: Part 1 moves from E to F while part 2 moves from E to F'

    '''
    
    testFunction = lambda vlq: vlq.parallelUnison()
    textFunction = lambda vlq, pn1, pn2: "Parallel unison in measure " + str(vlq.v1n1.measureNumber) +": "\
                 + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
                 + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name+ " to " + vlq.v2n2.name
    _identifyBasedOnVLQ(score, partNum1, partNum2, dictKey, testFunction, textFunction, color)
    
def identifyHiddenFifths(score, partNum1=None, partNum2=None, color=None, dictKey='hiddenFifths'):
    '''
    Identifies hidden fifths (calls :meth:`~music21.voiceLeading.VoiceLeadingQuartet.hiddenFifth`) between 
    two parts (if specified) or between all possible pairs of parts (if not specified) 
    and stores the resulting list of VLQTheoryResult objects in ``self.resultDict['hiddenFifths']``. 
    Optionally, a color attribute may be specified to color all corresponding notes in the score.
    
    

    >>> sc = stream.Score()
    >>> part0 = stream.Part()
    >>> p0measure1 = stream.Measure(number=1)
    >>> p0measure1.append(note.Note('e5'))
    >>> p0measure1.append(note.Note('d5'))
    >>> part0.append(p0measure1)
    >>> part1 = stream.Part()
    >>> p1measure1 = stream.Measure(number=1)
    >>> p1measure1.append(note.Note('c5'))
    >>> p1measure1.append(note.Note('g4'))
    >>> part1.append(p1measure1)
    >>> sc.insert(part0)
    >>> sc.insert(part1)
    >>> alpha.theoryAnalysis.theoryAnalyzer.identifyHiddenFifths(sc)
    >>> len(sc.analysisData['ResultDict']['hiddenFifths'])
    1
    >>> sc.analysisData['ResultDict']['hiddenFifths'][0].text
    'Hidden fifth in measure 1: Part 1 moves from E to D while part 2 moves from C to G'
    '''
    
    testFunction = lambda vlq: vlq.hiddenFifth()
    textFunction = lambda vlq, pn1, pn2: "Hidden fifth in measure " + str(vlq.v1n1.measureNumber) +": "\
                 + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
                 + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name+ " to " + vlq.v2n2.name
    _identifyBasedOnVLQ(score, partNum1, partNum2, dictKey, testFunction, textFunction, color)
    
def identifyHiddenOctaves(score, partNum1 = None, partNum2 = None, color = None,dictKey = 'hiddenOctaves'):
    '''
    Identifies hidden octaves (calls :meth:`~music21.voiceLeading.VoiceLeadingQuartet.hiddenOctave`) between 
    two parts (if specified) or between all possible pairs of parts (if not specified) 
    and stores the resulting list of VLQTheoryResult objects in ``score.analysisData['ResultDict']['hiddenOctaves']``. 
    Optionally, a color attribute may be specified to color all corresponding notes in the score.
    
    

    >>> sc = stream.Score()
    >>> part0 = stream.Part()
    >>> p0measure1 = stream.Measure(number=1)
    >>> p0measure1.append(note.Note('e4'))
    >>> p0measure1.append(note.Note('f4'))
    >>> part0.append(p0measure1)
    >>> part1 = stream.Part()
    >>> p1measure1 = stream.Measure(number=1)
    >>> p1measure1.append(note.Note('d3'))
    >>> p1measure1.append(note.Note('f3'))
    >>> part1.append(p1measure1)
    >>> sc.insert(part0)
    >>> sc.insert(part1)
    >>> alpha.theoryAnalysis.theoryAnalyzer.identifyHiddenOctaves(sc)
    >>> len(sc.analysisData['ResultDict']['hiddenOctaves'])
    1
    >>> sc.analysisData['ResultDict']['hiddenOctaves'][0].text
    'Hidden octave in measure 1: Part 1 moves from E to F while part 2 moves from D to F'
    '''
    
    testFunction = lambda vlq: vlq.hiddenOctave()
    textFunction = lambda vlq, pn1, pn2: "Hidden octave in measure " + str(vlq.v1n1.measureNumber) +": "\
                 + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
                 + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name+ " to " + vlq.v2n2.name
    _identifyBasedOnVLQ(score, partNum1, partNum2, dictKey, testFunction, textFunction, color)
    
def identifyImproperResolutions(score, partNum1 = None, partNum2 = None, color = None, 
                                dictKey = 'improperResolution', editorialMarkList=[]):
    '''
    Identifies improper resolutions of dissonant intervals (calls :meth:`~music21.voiceLeading.VoiceLeadingQuartet.improperResolution`) 
    between two parts (if specified) or between all possible pairs of parts (if not specified) 
    and stores the resulting list of VLQTheoryResult objects in ``self.resultDict['improperResolution']``. 
    Optionally, a color attribute may be specified to color all corresponding notes in the score.
    
    

    >>> sc = stream.Score()
    >>> part0 = stream.Part()
    >>> p0measure1 = stream.Measure(number=1)
    >>> p0measure1.append(note.Note('f#4'))
    >>> p0measure1.append(note.Note('a4'))
    >>> part0.append(p0measure1)
    >>> part1 = stream.Part()
    >>> p1measure1 = stream.Measure(number=1)
    >>> p1measure1.append(note.Note('C3'))
    >>> p1measure1.append(note.Note('B2'))
    >>> part1.append(p1measure1)
    >>> sc.insert(part0)
    >>> sc.insert(part1)
    >>> alpha.theoryAnalysis.theoryAnalyzer.identifyImproperResolutions(sc)
    >>> len(sc.analysisData['ResultDict']['improperResolution'])
    1
    >>> sc.analysisData['ResultDict']['improperResolution'][0].text
    'Improper resolution of Augmented Fourth in measure 1: Part 1 moves from F# to A while part 2 moves from C to B'

    '''
    #TODO: incorporate Jose's resolution rules into this method (italian6, etc.)
    testFunction = lambda vlq: vlq.improperResolution()
    textFunction = lambda vlq, pn1, pn2: "Improper resolution of " + vlq.vIntervals[0].simpleNiceName +" in measure " + str(vlq.v1n1.measureNumber) +": "\
             + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
             + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name + " to " + vlq.v2n2.name
    _identifyBasedOnVLQ(score, partNum1, partNum2, dictKey, testFunction, 
                        textFunction, color, editorialDictKey='isImproperResolution', 
                        editorialValue=True, editorialMarkList=editorialMarkList)
    
def identifyLeapNotSetWithStep(score, partNum1 = None, partNum2 = None, 
                               color = None, dictKey = 'LeapNotSetWithStep'):
    '''
    Identifies a leap/skip in one voice not set with a step in the other voice 
    (calls :meth:`~music21.voiceLeading.VoiceLeadingQuartet.leapNotSetWithStep`) 
    between two parts (if specified) or between all possible pairs of parts (if not specified) 
    and stores the resulting list of VLQTheoryResult objects in ``self.resultDict['leapNotSetWithStep']``. 
    Optionally, a color attribute may be specified to color all corresponding notes in the score.
    
    

    >>> sc = stream.Score()
    >>> part0 = stream.Part()
    >>> p0measure1 = stream.Measure(number=1)
    >>> p0measure1.append(note.Note('C4'))
    >>> p0measure1.append(note.Note('G3'))
    >>> part0.append(p0measure1)
    >>> part1 = stream.Part()
    >>> p1measure1 = stream.Measure(number=1)
    >>> p1measure1.append(note.Note('A2'))
    >>> p1measure1.append(note.Note('D2'))
    >>> part1.append(p1measure1)
    >>> sc.insert(part0)
    >>> sc.insert(part1)
    >>> alpha.theoryAnalysis.theoryAnalyzer.identifyLeapNotSetWithStep(sc)
    >>> len(sc.analysisData['ResultDict']['LeapNotSetWithStep'])
    1
    >>> sc.analysisData['ResultDict']['LeapNotSetWithStep'][0].text
    'Leap not set with step in measure 1: Part 1 moves from C to G while part 2 moves from A to D'
    '''
    
    testFunction = lambda vlq: vlq.leapNotSetWithStep()
    textFunction = lambda vlq, pn1, pn2: "Leap not set with step in measure " + str(vlq.v1n1.measureNumber) +": "\
             + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
             + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name + " to " + vlq.v2n2.name
    _identifyBasedOnVLQ(score, partNum1, partNum2, dictKey, testFunction, textFunction, color)

def identifyOpensIncorrectly(score, partNum1=None, partNum2=None, 
                             color=None, dictKey = 'opensIncorrectly'):
    '''
    Identifies if the piece opens correctly; calls :meth:`~music21.voiceLeading.VoiceLeadingQuartet.opensIncorrectly`
    
    

    >>> sc = stream.Score()
    >>> part0 = stream.Part()
    >>> p0measure1 = stream.Measure(number=1)
    >>> p0measure1.append(note.Note('C#4'))
    >>> p0measure1.append(note.Note('G3'))
    >>> part0.append(p0measure1)
    >>> part1 = stream.Part()
    >>> p1measure1 = stream.Measure(number=1)
    >>> p1measure1.append(note.Note('A2'))
    >>> p1measure1.append(note.Note('D2'))
    >>> part1.append(p1measure1)
    >>> sc.insert(part0)
    >>> sc.insert(part1)
    >>> alpha.theoryAnalysis.theoryAnalyzer.identifyOpensIncorrectly(sc)
    >>> len(sc.analysisData['ResultDict']['opensIncorrectly'])
    1
    >>> sc.analysisData['ResultDict']['opensIncorrectly'][0].text
    'Opening harmony is not in style'

    '''
    
    testFunction = lambda vlq: vlq.opensIncorrectly()
    textFunction = lambda vlq, pn1, pn2: "Opening harmony is not in style"
    _identifyBasedOnVLQ(score, partNum1, partNum2, dictKey, testFunction, 
                        textFunction, color, startIndex = 0, endIndex = 1)
    
def identifyClosesIncorrectly(score, partNum1 = None, partNum2 = None, color = None, dictKey = 'closesIncorrectly'):
    '''
    Identifies if the piece closes correctly; calls :meth:`~music21.voiceLeading.VoiceLeadingQuartet.closesIncorrectly`
    
    

    >>> sc = stream.Score()
    >>> part0 = stream.Part()
    >>> p0measure1 = stream.Measure(number=1)
    >>> p0measure1.append(note.Note('B4'))
    >>> p0measure1.append(note.Note('A4'))
    >>> p0measure1.append(note.Note('A4'))
    >>> part0.append(p0measure1)
    >>> part1 = stream.Part()
    >>> p1measure1 = stream.Measure(number=1)
    >>> p1measure1.append(note.Note('G2'))
    >>> p1measure1.append(note.Note('F2'))
    >>> p1measure1.append(note.Note('G2'))
    >>> part1.append(p1measure1)
    >>> sc.insert(part0)
    >>> sc.insert(part1)

    >>> alpha.theoryAnalysis.theoryAnalyzer.setKeyMeasureMap(sc,{1:'G'})
    >>> alpha.theoryAnalysis.theoryAnalyzer.identifyClosesIncorrectly(sc)
    >>> len(sc.analysisData['ResultDict']['closesIncorrectly'])
    1
    >>> sc.analysisData['ResultDict']['closesIncorrectly'][0].text
    'Closing harmony is not in style'
    
    '''
    testFunction = lambda vlq: vlq.closesIncorrectly() 
    textFunction = lambda vlq, pn1, pn2: "Closing harmony is not in style"
    _identifyBasedOnVLQ(score, partNum1, partNum2, dictKey, testFunction, textFunction, color, startIndex=-1)    

# Using the Vertical Slice N Tuplet Template

def identifyPassingTones(score, partNumToIdentify = None, color = None, dictKey = None, 
                         unaccentedOnly=True, 
                         editorialDictKey=None, editorialValue=True):
    '''
    Identifies the passing tones in the piece by looking at the vertical and horizontal cross-sections. Optionally
    specify unaccentedOnly to identify only unaccented passing tones (passing tones on weak beats). unaccentedOnly
    by default set to True
    
    Optionally label each identified passing tone with an editorial :class:`~music21.editorial.NoteEditorial` value of 
    editorialValue at ``note.editorial.misc[editorialDictKey]``
    
    

    >>> sc = stream.Score()
    >>> sc.insert(0, meter.TimeSignature('2/4'))
    >>> part0 = stream.Part()
    >>> p0measure1 = stream.Measure(number=1)
    >>> p0measure1.append(note.Note('A4', quarterLength = 0.5))
    >>> p0measure1.append(note.Note('G4', quarterLength = 0.5))
    >>> p0measure1.append(note.Note('F#4', quarterLength = 1.0))
    >>> part0.append(p0measure1)
    >>> part1 = stream.Part()
    >>> p1measure1 = stream.Measure(number=1)
    >>> p1measure1.append(note.Note('A2', quarterLength = 1.0))
    >>> p1measure1.append(note.Note('D3', quarterLength = 1.0))
    >>> part1.append(p1measure1)
    >>> sc.insert(part0)
    >>> sc.insert(part1)
    >>> alpha.theoryAnalysis.theoryAnalyzer.identifyPassingTones(sc)
    >>> len(sc.analysisData['ResultDict']['unaccentedPassingTones'])
    1
    >>> sc.analysisData['ResultDict']['unaccentedPassingTones'][0].text
    'G identified as a passing tone in part 1'
    
    '''
    if dictKey == None and unaccentedOnly:
        dictKey = 'unaccentedPassingTones'
    elif dictKey == None:
        dictKey = 'accentedPassingTones'
    testFunction = lambda vst, pn: vst.hasPassingTone(pn, unaccentedOnly)
    textFunction = lambda vsnt, pn:  vsnt.tnlsDict[pn].n2.name + ' identified as a passing tone in part ' + str(pn+1)
    _identifyBasedOnVerticalityNTuplet(score, partNumToIdentify, dictKey, testFunction, textFunction, color, editorialDictKey, editorialValue, editorialMarkDict={1:[partNumToIdentify]}, nTupletNum=3)

def getPassingTones(score, dictKey=None, partNumToIdentify=None, unaccentedOnly=True):
    '''
    returns a list of all passing tones present in the score, as identified by 
    :meth:`~music21.voiceLeading.VerticalityTriplet.hasPassingTone`
    
    

    >>> sc = stream.Score()
    >>> sc.insert(0, meter.TimeSignature('2/4'))
    >>> part0 = stream.Part()
    >>> p0measure1 = stream.Measure(number=1)
    >>> p0measure1.append(note.Note('A4', quarterLength = 0.5))
    >>> p0measure1.append(note.Note('G4', quarterLength = 0.5))
    >>> p0measure1.append(note.Note('F#4', quarterLength = 1.0))
    >>> part0.append(p0measure1)
    >>> part1 = stream.Part()
    >>> p1measure1 = stream.Measure(number=1)
    >>> p1measure1.append(note.Note('A2', quarterLength = 1.0))
    >>> p1measure1.append(note.Note('D3', quarterLength = 1.0))
    >>> part1.append(p1measure1)
    >>> sc.insert(part0)
    >>> sc.insert(part1)
    >>> alpha.theoryAnalysis.theoryAnalyzer.getPassingTones(sc)
    [<music21.note.Note G>]
    '''
    if dictKey == None and unaccentedOnly:
        dictKey = 'unaccentedPassingTones'
    elif dictKey == None:
        dictKey = 'accentedPassingTones'
    testFunction = lambda vst, pn: vst.hasPassingTone(pn, unaccentedOnly)
    _identifyBasedOnVerticalityNTuplet(score, partNumToIdentify, dictKey=dictKey, testFunction=testFunction, nTupletNum=3)
    if dictKey in score.analysisData['ResultDict']:
        return [tr.vsnt.tnlsDict[tr.partNumIdentified].n2 for tr in score.analysisData['ResultDict'][dictKey]]
    else:
        return None

def getNeighborTones(score, dictKey=None, partNumToIdentify=None, unaccentedOnly=True):
    '''
    returns a list of all passing tones present in the score, as identified by :meth:`~music21.voiceLeading.VerticalityTriplet.hasNeighborTone`
    
    

    >>> sc = stream.Score()
    >>> sc.insert(0, meter.TimeSignature('2/4'))
    >>> part0 = stream.Part()
    >>> p0measure1 = stream.Measure(number=1)
    >>> p0measure1.append(note.Note('E-3', quarterLength = 1.0))
    >>> p0measure1.append(note.Note('C3', quarterLength = 1.0))
    >>> part0.append(p0measure1)
    >>> part1 = stream.Part()
    >>> p1measure1 = stream.Measure(number=1)
    >>> p1measure1.append(note.Note('C2', quarterLength = 0.5))
    >>> p1measure1.append(note.Note('B1', quarterLength = 0.5))
    >>> p1measure1.append(note.Note('C2', quarterLength = 1.0))
    >>> part1.append(p1measure1)
    >>> sc.insert(part0)
    >>> sc.insert(part1)
    >>> alpha.theoryAnalysis.theoryAnalyzer.getNeighborTones(sc)
    [<music21.note.Note B>]
    '''
    if dictKey == None and unaccentedOnly:
        dictKey = 'unaccentedNeighborTones'
    elif dictKey == None:
        dictKey = 'accentedNeighborTones'
    testFunction = lambda vst, pn: vst.hasNeighborTone(pn, unaccentedOnly)
    _identifyBasedOnVerticalityNTuplet(score, partNumToIdentify, dictKey=dictKey, testFunction=testFunction, nTupletNum=3)
    if dictKey in score.analysisData['ResultDict']:
        return [tr.vsnt.tnlsDict[tr.partNumIdentified].n2 for tr in score.analysisData['ResultDict'][dictKey]]
    else:
        return None

def removePassingTones(score, dictKey='unaccentedPassingTones'):
    '''
    primitively removes the passing tones found in a piece and fills the gap by extending note duraitons 
    (method under development)

    
    >>> sc = stream.Score()
    >>> sc.insert(0, meter.TimeSignature('2/4'))
    >>> part0 = stream.Part()
    >>> p0measure1 = stream.Measure(number=1)
    >>> p0measure1.append(note.Note('A4', quarterLength = 0.5))
    >>> p0measure1.append(note.Note('G4', quarterLength = 0.5))
    >>> p0measure1.append(note.Note('F#4', quarterLength = 1.0))
    >>> part0.append(p0measure1)
    >>> part1 = stream.Part()
    >>> p1measure1 = stream.Measure(number=1)
    >>> p1measure1.append(note.Note('A2', quarterLength = 1.0))
    >>> p1measure1.append(note.Note('D3', quarterLength = 1.0))
    >>> part1.append(p1measure1)
    >>> sc.insert(part0)
    >>> sc.insert(part1)
    >>> alpha.theoryAnalysis.theoryAnalyzer.removePassingTones(sc)
    >>> for x in sc.flat.notes:
    ...   print(x)
    <music21.note.Note A>
    <music21.note.Note A>
    <music21.note.Note F#>
    <music21.note.Note D>
    '''
    getPassingTones(score, dictKey=dictKey)
    for tr in score.analysisData['ResultDict'][dictKey]:
        a = tr.vsnt.tnlsDict[tr.partNumIdentified] #identifiedThreeNoteLinearSegment
        durationNewTone = a.n1.duration.quarterLength + a.n2.duration.quarterLength
        for obj in score.recurse():
            if obj.id == a.n2.id:
                obj.activeSite.remove(obj)
                break
        a.n1.duration = music21.duration.Duration(durationNewTone)
        score.stripTies(inPlace=True, matchByPitch=True, retainContainers=False)
    score.analysisData['Verticalities'] = None
    
def removeNeighborTones(score, dictKey='unaccentedNeighborTones'):
    '''
    primitively removes the neighbor tones found in a piece and fills the gap by extending note duraitons 
    (method under development)
    
    
    >>> from music21.alpha.theoryAnalysis import *
    >>> sc = stream.Score()
    >>> sc.insert(0, meter.TimeSignature('2/4'))
    >>> part0 = stream.Part()
    >>> p0measure1 = stream.Measure(number=1)
    >>> p0measure1.append(note.Note('E-3', quarterLength = 1.0))
    >>> p0measure1.append(note.Note('C3', quarterLength = 1.0))
    >>> part0.append(p0measure1)
    >>> part1 = stream.Part()
    >>> p1measure1 = stream.Measure(number=1)
    >>> p1measure1.append(note.Note('C2', quarterLength = 0.5))
    >>> p1measure1.append(note.Note('B1', quarterLength = 0.5))
    >>> p1measure1.append(note.Note('C2', quarterLength = 1.0))
    >>> part1.append(p1measure1)
    >>> sc.insert(part0)
    >>> sc.insert(part1)
    >>> theoryAnalyzer.removeNeighborTones(sc)
    >>> for x in sc.flat.notes:
    ...   print(x)
    <music21.note.Note E->
    <music21.note.Note C>
    <music21.note.Note C>
    <music21.note.Note C>
    '''
    getNeighborTones(score, dictKey=dictKey)
    for tr in score.analysisData['ResultDict'][dictKey]:
        a = tr.vsnt.tnlsDict[tr.partNumIdentified] #identifiedThreeNoteLinearSegment
        durationNewTone = a.n1.duration.quarterLength + a.n2.duration.quarterLength
        for obj in score.recurse():
            if obj.id == a.n2.id:
                obj.activeSite.remove(obj)
                break
        a.n1.duration = music21.duration.Duration(durationNewTone)
        score.stripTies(inPlace=True, matchByPitch=True, retainContainers=False)
        #a.n1.color = 'red'
    score.analysisData['Verticalities'] = None

def identifyNeighborTones(score, partNumToIdentify = None, color = None, dictKey = None, 
                          unaccentedOnly=True,
                          editorialDictKey='isNeighborTone', editorialValue=True):
    '''
    Identifies the neighbor tones in the piece by looking at the vertical and horizontal cross-sections. Optionally
    specify unaccentedOnly to identify only unaccented neighbor tones (neighbor tones on weak beats). unaccentedOnly
    by default set to True
    
    

    >>> sc = stream.Score()
    >>> sc.insert(0, meter.TimeSignature('2/4'))
    >>> part0 = stream.Part()
    >>> p0measure1 = stream.Measure(number=1)
    >>> p0measure1.append(note.Note('E-3', quarterLength = 1.0))
    >>> p0measure1.append(note.Note('C3', quarterLength = 1.0))
    >>> part0.append(p0measure1)
    >>> part1 = stream.Part()
    >>> p1measure1 = stream.Measure(number=1)
    >>> p1measure1.append(note.Note('C2', quarterLength = 0.5))
    >>> p1measure1.append(note.Note('B1', quarterLength = 0.5))
    >>> p1measure1.append(note.Note('C2', quarterLength = 1.0))
    >>> part1.append(p1measure1)
    >>> sc.insert(part0)
    >>> sc.insert(part1)
    >>> alpha.theoryAnalysis.theoryAnalyzer.identifyNeighborTones(sc)
    >>> len(sc.analysisData['ResultDict']['unaccentedNeighborTones'])
    1
    >>> sc.analysisData['ResultDict']['unaccentedNeighborTones'][0].text
    'B identified as a neighbor tone in part 2'
    '''
    if dictKey == None and unaccentedOnly:
        dictKey = 'unaccentedNeighborTones'
    elif dictKey == None:
        dictKey = 'accentedNeighborTones'
        
    testFunction = lambda vst, pn: vst.hasNeighborTone(pn, unaccentedOnly)
    textFunction = lambda vsnt, pn:  vsnt.tnlsDict[pn].n2.name + ' identified as a neighbor tone in part ' + str(pn+1)
    _identifyBasedOnVerticalityNTuplet(score, partNumToIdentify,  dictKey, testFunction, textFunction, color, editorialDictKey, editorialValue, editorialMarkDict={1:[partNumToIdentify]}, nTupletNum=3)

def identifyDissonantHarmonicIntervals(score, partNum1 = None, partNum2 = None, color = None, 
                                       dictKey = 'dissonantHarmonicIntervals'):
    '''
    Identifies dissonant harmonic intervals (calls :meth:`~music21.interval.Interval.isConsonant`) 
    between the two parts (if specified) or between all possible pairs of parts (if not specified) 
    and stores the resulting list of IntervalTheoryResultObject objects in ``self.resultDict['dissonantHarmonicIntervals']``. 
    Optionally, a color attribute may be specified to color all corresponding notes in the score.
            
    

    >>> sc = stream.Score()
    >>> part0 = stream.Part()
    >>> p0measure1 = stream.Measure(number=1)
    >>> p0measure1.append(note.Note('c'))
    >>> p0measure1.append(note.Note('f'))
    >>> p0measure1.append(note.Note('b'))
    >>> p0measure1.append(note.Note('c'))
    >>> part0.append(p0measure1)
    >>> part1 = stream.Part()
    >>> p1measure1 = stream.Measure(number=1)
    >>> p1measure1.append(note.Note('b-'))
    >>> p1measure1.append(note.Note('c'))
    >>> p1measure1.append(note.Note('f'))
    >>> p1measure1.append(note.Note('c'))
    >>> part1.append(p1measure1)
    >>> sc.insert(part0)
    >>> sc.insert(part1)
    >>> alpha.theoryAnalysis.theoryAnalyzer.identifyDissonantHarmonicIntervals(sc)
    >>> len(sc.analysisData['ResultDict']['dissonantHarmonicIntervals'])
    3
    >>> sc.analysisData['ResultDict']['dissonantHarmonicIntervals'][2].text
    'Dissonant harmonic interval in measure 1: Augmented Fourth from F to B between part 1 and part 2'
    '''
    testFunction = lambda hIntv: hIntv is not None and not hIntv.isConsonant()
    textFunction = lambda hIntv, pn1, pn2: "Dissonant harmonic interval in measure " + str(hIntv.noteStart.measureNumber) +": " \
                 + str(hIntv.simpleNiceName) + " from " + str(hIntv.noteStart.name) + " to " + str(hIntv.noteEnd.name) \
                 + " between part " + str(pn1 + 1) + " and part " + str(pn2 + 1)
    _identifyBasedOnHarmonicInterval(score, partNum1, partNum2, color, dictKey, testFunction, textFunction)

def identifyImproperDissonantIntervals(score, partNum1 = None, partNum2 = None, color = None, 
                                       dictKey = 'improperDissonantIntervals', unaccentedOnly=True):
    '''
    Identifies dissonant harmonic intervals that are not passing tones or neighbor tones or don't resolve correctly
    
    

    >>> sc = stream.Score()
    >>> part0 = stream.Part()
    >>> p0measure1 = stream.Measure(number=1)
    >>> p0measure1.append(note.Note('a3'))
    >>> p0measure1.append(note.Note('f3'))
    >>> p0measure1.append(note.Note('e3'))
    >>> p0measure1.append(note.Note('c4'))
    >>> part0.append(p0measure1)
    >>> part1 = stream.Part()
    >>> p1measure1 = stream.Measure(number=1)
    >>> p1measure1.append(note.Note('b2'))
    >>> p1measure1.append(note.Note('c3'))
    >>> p1measure1.append(note.Note('b2'))
    >>> p1measure1.append(note.Note('c3'))
    >>> part1.append(p1measure1)
    >>> sc.insert(part0)
    >>> sc.insert(part1)
    >>> alpha.theoryAnalysis.theoryAnalyzer.identifyImproperDissonantIntervals(sc)
    >>> len(sc.analysisData['ResultDict']['improperDissonantIntervals'])
    2
    >>> sc.analysisData['ResultDict']['improperDissonantIntervals'][1].text
    'Improper dissonant harmonic interval in measure 1: Perfect Fourth from C to F between part 1 and part 2'

    '''
   
    if partNum1 == None or partNum2 == None:
        for (partNum1,partNum2) in getAllPartNumPairs(score):
            identifyImproperDissonantIntervals(score, partNum1, partNum2, color, dictKey, unaccentedOnly)
    else:
        identifyDissonantHarmonicIntervals(score, partNum1, partNum2, dictKey='h1')
        identifyPassingTones(score, partNum1, dictKey='pt1', unaccentedOnly=unaccentedOnly)
        identifyPassingTones(score, partNum2, dictKey='pt2', unaccentedOnly=unaccentedOnly)
        identifyNeighborTones(score, partNum1, dictKey='nt1', unaccentedOnly=unaccentedOnly)
        identifyNeighborTones(score, partNum1, dictKey='nt2', unaccentedOnly=unaccentedOnly)
        identifyImproperResolutions(score, partNum1, partNum2, dictKey='res', editorialMarkList=[1,2,3,4])
        if 'ResultDict' in score.analysisData and 'h1' in score.analysisData['ResultDict']:
            for resultTheoryObject in score.analysisData['ResultDict']['h1'] :
                if  (resultTheoryObject.hasEditorial('isPassingTone', True) or 
                     resultTheoryObject.hasEditorial('isNeigborTone', True)) or \
                     not resultTheoryObject.hasEditorial('isImproperResolution', True):
                    continue
                else:
                    intv = resultTheoryObject.intv
                    tr = theoryResult.IntervalTheoryResult(intv)
                    #tr.value = valueFunction(hIntv)
                    tr.text = "Improper dissonant harmonic interval in measure " + str(intv.noteStart.measureNumber) +": " \
                     + str(intv.niceName) + " from " + str(intv.noteStart.name) + " to " + str(intv.noteEnd.name) \
                     + " between part " + str(partNum1 + 1) + " and part " + str(partNum2 + 1)
                    if color is not None:
                        tr.color(color)
                    _updateScoreResultDict(score, dictKey, tr)

        removeFromAnalysisData(score, ['h1','pt1', 'pt2', 'nt1', 'nt2'])
       
def identifyDissonantMelodicIntervals(score, partNum = None, color = None, 
                                      dictKey='dissonantMelodicIntervals'):
    '''
    Identifies dissonant melodic intervals (A2, A4, d5, m7, M7) in the part (if specified) 
    or for all parts (if not specified) and stores the resulting list of 
    IntervalTheoryResultObject objects in ``self.resultDict['dissonantMelodicIntervals']``. 
    Optionally, a color attribute may be specified to color all corresponding notes in the score.
    
    

    >>> sc = stream.Score()
    >>> part0 = stream.Part()
    >>> p0measure1 = stream.Measure(number=1)
    >>> p0measure1.append(note.Note('f3'))
    >>> p0measure1.append(note.Note('g#3'))
    >>> part0.append(p0measure1)
    >>> part1 = stream.Part()
    >>> p1measure1 = stream.Measure(number=1)
    >>> p1measure1.append(note.Note('d2'))
    >>> p1measure1.append(note.Note('a-2'))
    >>> part1.append(p1measure1)
    >>> sc.insert(part0)
    >>> sc.insert(part1)
    >>> alpha.theoryAnalysis.theoryAnalyzer.identifyDissonantMelodicIntervals(sc)
    >>> len(sc.analysisData['ResultDict']['dissonantMelodicIntervals'])
    2
    >>> sc.analysisData['ResultDict']['dissonantMelodicIntervals'][0].text
    'Dissonant melodic interval in part 1 measure 1: Augmented Second from F to G#'
    >>> sc.analysisData['ResultDict']['dissonantMelodicIntervals'][1].text
    'Dissonant melodic interval in part 2 measure 1: Diminished Fifth from D to A-'

    '''
    testFunction = lambda mIntv: mIntv is not None and mIntv.simpleName in ["A2","A4","d5","m7","M7"]
    textFunction = lambda mIntv, pn: "Dissonant melodic interval in part " + str(pn + 1) + " measure " + str(mIntv.noteStart.measureNumber) +": "\
                 + str(mIntv.simpleNiceName) + " from " + str(mIntv.noteStart.name) + " to " + str(mIntv.noteEnd.name)
    _identifyBasedOnMelodicInterval(score, partNum, color, dictKey, testFunction, textFunction)                

#-------------------------------------------------------------------------------           
# Other Theory Properties to Identify (not specifically checking errors in a counterpoint assignment)

# Theory Properties using VLQ template - No doc tests needed
    
def identifyObliqueMotion(score, partNum1 = None, partNum2 = None, color = None):
    dictKey = 'obliqueMotion'
    testFunction = lambda vlq: vlq.obliqueMotion()
    textFunction = lambda vlq, pn1, pn2: "Oblique motion in measure " + str(vlq.v1n1.measureNumber) +": "\
                 + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
                 + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name+ " to " + vlq.v2n2.name
    _identifyBasedOnVLQ(score, partNum1, partNum2, dictKey, testFunction, textFunction, color)
    
def identifySimilarMotion(score, partNum1 = None, partNum2 = None, color = None):
    dictKey = 'similarMotion'
    testFunction = lambda vlq: vlq.similarMotion()
    textFunction = lambda vlq, pn1, pn2: "Similar motion in measure " + str(vlq.v1n1.measureNumber) +": "\
                 + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
                 + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name+ " to " + vlq.v2n2.name
    _identifyBasedOnVLQ(score, partNum1, partNum2, dictKey, testFunction, textFunction, color)
    
def identifyParallelMotion(score, partNum1 = None, partNum2 = None, color = None):
    dictKey = 'parallelMotion'
    testFunction = lambda vlq: vlq.parallelMotion()
    textFunction = lambda vlq, pn1, pn2: "Parallel motion in measure " + str(vlq.v1n1.measureNumber) +": "\
                 + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
                 + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name+ " to " + vlq.v2n2.name
    _identifyBasedOnVLQ(score, partNum1, partNum2, dictKey, testFunction, textFunction, color)
    
def identifyContraryMotion(score, partNum1 = None, partNum2 = None, color = None):
    dictKey = 'contraryMotion'
    testFunction = lambda vlq: vlq.contraryMotion()
    textFunction = lambda vlq, pn1, pn2: "Contrary motion in measure " + str(vlq.v1n1.measureNumber) +": "\
                 + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
                 + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name+ " to " + vlq.v2n2.name
    _identifyBasedOnVLQ(score, partNum1, partNum2, dictKey, testFunction, textFunction, color)
    
def identifyOutwardContraryMotion(score, partNum1 = None, partNum2 = None, color = None):
    dictKey = 'outwardContraryMotion'
    testFunction = lambda vlq: vlq.outwardContraryMotion()
    textFunction = lambda vlq, pn1, pn2: "Outward contrary motion in measure " + str(vlq.v1n1.measureNumber) +": "\
                 + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
                 + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name+ " to " + vlq.v2n2.name
    _identifyBasedOnVLQ(score, partNum1, partNum2, dictKey, testFunction, textFunction, color)
    
def identifyInwardContraryMotion(score, partNum1 = None, partNum2 = None, color = None):
    dictKey = 'inwardContraryMotion'
    testFunction = lambda vlq: vlq.inwardContraryMotion()
    textFunction = lambda vlq, pn1, pn2: "Inward contrary motion in measure " + str(vlq.v1n1.measureNumber) +": "\
                 + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
                 + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name+ " to " + vlq.v2n2.name
    _identifyBasedOnVLQ(score, partNum1, partNum2, color, dictKey, testFunction, textFunction)
    
def identifyAntiParallelMotion(score, partNum1 = None, partNum2 = None, color = None):
    dictKey = 'antiParallelMotion'
    testFunction = lambda vlq: vlq.antiParallelMotion()
    textFunction = lambda vlq, pn1, pn2: "Anti-parallel motion in measure " + str(vlq.v1n1.measureNumber) +": "\
                 + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
                 + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name+ " to " + vlq.v2n2.name
    _identifyBasedOnVLQ(score, partNum1, partNum2, dictKey, testFunction, textFunction, color)

# More Properties, not using VLQ template

def identifyTonicAndDominantRomanNumerals(score, color = None, 
                                          dictKey = 'romanNumeralsVandI', responseOffsetMap = []):
    '''
    Identifies the roman numerals in the piece by iterating throgh the vertical slices and figuring
    out which roman numeral best corresponds to that vertical slice. Optionally specify the responseOffsetMap
    which limits the resultObjects returned to only those with ``verticality's.offset(leftAlign=True)`` included
    in the list. For example, if only roman numerals were to be written for the vertical slice at offset 0, 6, and 7
    in the piece, pass ``responseOffsetMap = [0,6,7]``
    
    >>> sc = stream.Score()
    >>> part0 = stream.Part()
    >>> p0measure1 = stream.Measure(number=1)
    >>> p0measure1.append(note.Note('a3'))
    >>> p0measure1.append(note.Note('B-3'))
    >>> part0.append(p0measure1)
    >>> part1 = stream.Part()
    >>> p1measure1 = stream.Measure(number=1)
    >>> p1measure1.append(note.Note('c2'))
    >>> p1measure1.append(note.Note('g2'))
    >>> part1.append(p1measure1)
    >>> sc.insert(part0)
    >>> sc.insert(part1)
    >>> alpha.theoryAnalysis.theoryAnalyzer.setKeyMeasureMap(sc, {0:'Bb'} )
    >>> alpha.theoryAnalysis.theoryAnalyzer.identifyTonicAndDominantRomanNumerals(sc)
    >>> len(sc.analysisData['ResultDict']['romanNumeralsVandI'])
    2
    >>> sc.analysisData['ResultDict']['romanNumeralsVandI'][0].text
    'Roman Numeral of A,C is V64'
    >>> sc.analysisData['ResultDict']['romanNumeralsVandI'][1].text
    'Roman Numeral of B-,G is I'
    
    '''
    def testFunction(vs, score):
        noteList = vs.getObjectsByClass('Note')
        if not None in noteList:
            inChord = chord.Chord(noteList)
            inKey = getKeyAtMeasure(score, noteList[0].measureNumber)
            chordBass = noteList[-1]
            inChord.bass(chordBass.pitch)
            return roman.identifyAsTonicOrDominant(inChord, inKey)
        else:
            return False
       
    def textFunction(vs, rn):
        notes = ''
        for n in vs.getObjectsByClass('Note'):
            notes+= n.name + ','
        notes = notes[:-1]
        return "Roman Numeral of " + notes + ' is ' + rn
    _identifyBasedOnVerticality(score, color, dictKey, testFunction, textFunction, 
                                responseOffsetMap=responseOffsetMap)                

# TODO: improve this method...it's the beginnings of a harmonic analysis system for music21, but not developed well enough
# for general use - it was used briefly as a proof-of-concept for some music theory homework assignments

#
#def identifyRomanNumerals(score, color = None, dictKey = 'romanNumerals', responseOffsetMap = []):
#    '''
#    Identifies the roman numerals in the piece by iterating throgh the vertical slices and figuring
#    out which roman numeral best corresponds to that vertical slice. (calls :meth:`~music21.roman.romanNumeralFromChord`)
#    
#    Optionally specify the responseOffsetMap which limits the resultObjects returned to only those with 
#    verticality's.offset(leftAlign=True) included in the list. For example, if only roman numerals
#    were to be written for the vertical slice at offset 0, 6, and 7 in the piece, pass responseOffsetMap = [0,6,7]
#    
#    '''
#    def testFunction(vs, score, responseOffsetMap=[]):
#        noteList = vs.noteList
#
#        if not None in noteList:
#            inChord = chord.Chord(noteList)
#            inChord.bass(noteList[-1])
#            inKey = getKeyAtMeasure(score, noteList[0].measureNumber)
#            rn = roman.romanNumeralFromChord(inChord, inKey)
#            return rn
#        else:
#            return False
#       
#    def textFunction(vs, rn):
#        notes = ''
#        for n in vs.noteList:
#            notes+= n.name + ','
#        notes = notes[:-1]
#        return "Roman Numeral of " + notes + ' is ' + rn
#    _identifyBasedOnVerticality(score, color, dictKey, testFunction, textFunction, responseOffsetMap=responseOffsetMap)                
    
def identifyHarmonicIntervals(score, partNum1 = None, partNum2 = None, 
                              color = None, dictKey = 'harmonicIntervals'):
    '''
    identify all the harmonic intervals in the score between partNum1 or partNum2, or if not specified ALL
    possible combinations
    
    :class:`~music21.alpha.theoryAnalysis.theoryAnalyzerIntervalTheoryResult` created with ``.value`` set to the string most commonly
    used to identify the interval (0 through 9, with A4 and d5)

    >>> sc = stream.Score()
    >>> part0 = stream.Part()
    >>> p0measure1 = stream.Measure(number=1)
    >>> p0measure1.append(note.Note('a3'))
    >>> p0measure1.append(note.Note('f#3'))
    >>> p0measure1.append(note.Note('e3'))
    >>> p0measure1.append(note.Note('c4'))
    >>> part0.append(p0measure1)
    >>> part1 = stream.Part()
    >>> p1measure1 = stream.Measure(number=1)
    >>> p1measure1.append(note.Note('b2'))
    >>> p1measure1.append(note.Note('c3'))
    >>> p1measure1.append(note.Note('b2'))
    >>> p1measure1.append(note.Note('c3'))
    >>> part1.append(p1measure1)
    >>> sc.insert(part0)
    >>> sc.insert(part1)
    >>> alpha.theoryAnalysis.theoryAnalyzer.identifyHarmonicIntervals(sc)
    >>> len(sc.analysisData['ResultDict']['harmonicIntervals'])
    4
    >>> sc.analysisData['ResultDict']['harmonicIntervals'][1].value
    'A4'
    >>> sc.analysisData['ResultDict']['harmonicIntervals'][0].text
    'harmonic interval between B and A between parts 1 and 2 is a Minor Seventh'

    '''
    testFunction = lambda hIntv: hIntv.generic.undirected if hIntv is not None else False
    textFunction = lambda hIntv, pn1, pn2: "harmonic interval between " + hIntv.noteStart.name + ' and ' + hIntv.noteEnd.name + \
                 ' between parts ' + str(pn1 + 1) + ' and ' + str(pn2 + 1) + ' is a ' + str(hIntv.niceName)
    def valueFunction(hIntv):
        augordimIntervals = ['A4','d5']
        if hIntv.simpleName in augordimIntervals:
            return hIntv.simpleName
        else:
            value = hIntv.generic.undirected
            while value > 9:
                value -= 7
            return value
    _identifyBasedOnHarmonicInterval(score, partNum1, partNum2, color, dictKey, testFunction, textFunction, valueFunction=valueFunction)
    
def identifyScaleDegrees(score, partNum = None, color = None, dictKey = 'scaleDegrees'):
    '''
    identify all the scale degrees in the score in partNum, or if not specified ALL partNums

    >>> sc = stream.Score()
    >>> part0 = stream.Part()
    >>> p0measure1 = stream.Measure(number=1)
    >>> p0measure1.append(note.Note('a3'))
    >>> p0measure1.append(note.Note('f#3'))
    >>> p0measure1.append(note.Note('e3'))
    >>> p0measure1.append(note.Note('c4'))
    >>> part0.append(p0measure1)
    >>> part1 = stream.Part()
    >>> p1measure1 = stream.Measure(number=1)
    >>> p1measure1.append(note.Note('b2'))
    >>> p1measure1.append(note.Note('c3'))
    >>> p1measure1.append(note.Note('b2'))
    >>> p1measure1.append(note.Note('c3'))
    >>> part1.append(p1measure1)
    >>> sc.insert(part0)
    >>> sc.insert(part1)
    >>> alpha.theoryAnalysis.theoryAnalyzer.setKeyMeasureMap(sc, {0:'G'})
    >>> alpha.theoryAnalysis.theoryAnalyzer.identifyScaleDegrees(sc)
    >>> len(sc.analysisData['ResultDict']['scaleDegrees'])
    8
    >>> sc.analysisData['ResultDict']['scaleDegrees'][1].value
    '7'
    >>> sc.analysisData['ResultDict']['scaleDegrees'][1].text
    'scale degree of F# in part 1 is 7'
    '''
    
    testFunction = lambda sc, n:  (str(getKeyAtMeasure(sc, n.measureNumber).getScale().getScaleDegreeFromPitch(n.pitch)) ) if n is not None else False
    textFunction = lambda n, pn, scaleDegree: "scale degree of " + n.name + ' in part ' + str(pn+ 1) + ' is ' + str(scaleDegree) 
    _identifyBasedOnNote(score, partNum, color, dictKey, testFunction, textFunction)
        
def identifyMotionType(score, partNum1 = None, partNum2 = None, 
                       color = None, dictKey = 'motionType'):
    '''
    Identifies the motion types in the score by analyzing each voice leading quartet between partNum1 and
    partNum2, or all possible voiceLeadingQuartets if not specified
    
    :class:`~music21.theoryResult.VLQTheoryResult` by calling :meth:`~music21.voiceLeading.VoiceLeadingQuartet.motionType`
    Possible values for VLQTheoryResult are 'Oblique', 'Parallel', 'Similar', 'Contrary', 'Anti-Parallel', 'No Motion'
    
    

    >>> sc = stream.Score()
    >>> part0 = stream.Part()
    >>> p0measure1 = stream.Measure(number=1)
    >>> p0measure1.append(note.Note('a3'))
    >>> p0measure1.append(note.Note('f#3'))
    >>> p0measure1.append(note.Note('e3'))
    >>> p0measure1.append(note.Note('c4'))
    >>> part0.append(p0measure1)
    >>> part1 = stream.Part()
    >>> p1measure1 = stream.Measure(number=1)
    >>> p1measure1.append(note.Note('b2'))
    >>> p1measure1.append(note.Note('c3'))
    >>> p1measure1.append(note.Note('b2'))
    >>> p1measure1.append(note.Note('c3'))
    >>> part1.append(p1measure1)
    >>> sc.insert(part0)
    >>> sc.insert(part1)
    >>> alpha.theoryAnalysis.theoryAnalyzer.identifyMotionType(sc)
    >>> len(sc.analysisData['ResultDict']['motionType'])
    3
    >>> sc.analysisData['ResultDict']['motionType'][1].value
    'Similar'
    >>> sc.analysisData['ResultDict']['motionType'][1].text
    'Similar Motion in measure 1: Part 1 moves from F# to E while part 2 moves from C to B'
    '''
    
    testFunction = lambda vlq: vlq.motionType().value
    textFunction = lambda vlq, pn1, pn2: (vlq.motionType().value + ' Motion in measure '+ str(vlq.v1n1.measureNumber) +": " \
                 + "Part " + str(pn1 + 1) + " moves from " + vlq.v1n1.name + " to " + vlq.v1n2.name + " "\
                 + "while part " + str(pn2 + 1) + " moves from " + vlq.v2n1.name+ " to " + vlq.v2n2.name)  if vlq.motionType() != "No Motion" else 'No motion'
    _identifyBasedOnVLQ(score, partNum1, partNum2, dictKey, testFunction, textFunction, color)
    
#-------------------------------------------------------------------------------
# Combo method that wraps many identify methods into one 

def identifyCommonPracticeErrors(score, partNum1=None, partNum2=None, 
                                 dictKey='commonPracticeErrors'):
    '''
    wrapper method that calls all identify methods for common-practice counterpoint errors, 
    assigning a color identifier to each
    
    ParallelFifths = red, ParallelOctaves = yellow, HiddenFifths = orange, HiddenOctaves = green, 
    ParallelUnisons = blue, ImproperResolutions = purple, improperDissonances = white, 
    DissonantMelodicIntervals = cyan, incorrectOpening = brown, incorrectClosing = gray
    '''
   
    identifyParallelFifths(score, partNum1, partNum2, 'red', dictKey)
    identifyParallelOctaves(score, partNum1, partNum2, 'yellow', dictKey)
    identifyHiddenFifths(score, partNum1, partNum2, 'orange', dictKey)
    identifyHiddenOctaves(score, partNum1, partNum2, 'green', dictKey)
    identifyParallelUnisons(score, partNum1, partNum2, 'blue', dictKey)
    identifyImproperResolutions(score, partNum1, partNum2, 'purple', dictKey)
    #identifyLeapNotSetWithStep(score, partNum1, partNum2, 'white', dictKey)
    identifyImproperDissonantIntervals(score, partNum1, partNum2, 'white', dictKey, unaccentedOnly = True)
    identifyDissonantMelodicIntervals(score, partNum1,'cyan', dictKey)  
    identifyOpensIncorrectly(score, partNum1, partNum2, 'brown', dictKey)
    identifyClosesIncorrectly(score, partNum1, partNum2, 'gray', dictKey)              
    
    
#------------------------------------------------------------------------------- 
# Output methods for reading out information from theoryAnalyzerResult objects
           
def getResultsString(score, typeList=None):
    '''
    returns string of all results found by calling all identify methods on the TheoryAnalyzer score

    

    >>> sc = stream.Score()
    >>> part0 = stream.Part()
    >>> p0measure1 = stream.Measure(number=1)
    >>> p0measure1.append(note.Note('c5'))
    >>> p0measure1.append(note.Note('d5'))
    >>> p0measure1.append(note.Note('e5'))
    >>> p0measure1.append(note.Note('g5'))
    >>> part0.append(p0measure1)
    >>> part1 = stream.Part()
    >>> p1measure1 = stream.Measure(number=1)
    >>> p1measure1.append(note.Note('c4'))
    >>> p1measure1.append(note.Note('g4'))
    >>> p1measure1.append(note.Note('a4'))
    >>> p1measure1.append(note.Note('c4'))
    >>> part1.append(p1measure1)
    >>> sc.insert(part0)
    >>> sc.insert(part1)
    >>> alpha.theoryAnalysis.theoryAnalyzer.identifyCommonPracticeErrors(sc)
    >>> print(alpha.theoryAnalysis.theoryAnalyzer.getResultsString(sc))
    commonPracticeErrors: 
    Parallel fifth in measure 1: Part 1 moves from D to E while part 2 moves from G to A
    Parallel fifth in measure 1: Part 1 moves from E to G while part 2 moves from A to C
    Hidden fifth in measure 1: Part 1 moves from C to D while part 2 moves from C to G
    Closing harmony is not in style
    '''
    resultStr = ""
    addAnalysisData(score)
    for resultType in score.analysisData['ResultDict']:
        if typeList is None or resultType in typeList:
            resultStr+=resultType+": \n"
            for result in score.analysisData['ResultDict'][resultType]:
                resultStr += result.text
                resultStr += "\n"
    resultStr = resultStr[0:-1] #remove final new line character
    return resultStr

def getHTMLResultsString(score, typeList=None):
    '''
    returns string of all results found by calling all identify methods on the TheoryAnalyzer score
    '''
    resultStr = ""
    addAnalysisData(score)
    for resultType in score.analysisData['ResultDict']:
        if typeList is None or resultType in typeList:
            resultStr+="<b>"+resultType+"</B>: <br /><ul>"
            for result in score.analysisData['ResultDict'][resultType]:
                resultStr += "<li style='color:"+result.currentColor+"'><b>"+result.text.sub(':',"</b>:<span style='color:black'>")+"</span></li>"
            resultStr += "</ul><br />"
            
    return resultStr
        
def colorResults(score, color='red', typeList=None):
    '''
    colors the notes of all results found in typeList by calling all identify methods on Theory Analyzer.
    '''
    addAnalysisData(score)
    for resultType in score.analysisData['ResultDict']:
        if typeList is None or resultType in typeList:
            for result in score.analysisData['ResultDict'][resultType]:
                result.color(color)

def removeFromAnalysisData(score, dictKeys):  
    '''
    remove a result entry or entries from the resultDict by specifying which key or keys in the dictionary
    you'd like removed. Pass in a list of dictKeys or just a single dictionary key.
    
    
    >>> sc = stream.Score()
    >>> alpha.theoryAnalysis.theoryAnalyzer.addAnalysisData(sc)
    >>> sc.analysisData['ResultDict'] = {'sampleDictKey': 'sample response', 'h1':'another sample response', '5':'third sample response'}
    >>> alpha.theoryAnalysis.theoryAnalyzer.removeFromAnalysisData(sc, 'sampleDictKey')
    >>> for k in sorted(list(sc.analysisData['ResultDict'].keys())):
    ...     print("{0}\t{1}".format(k, sc.analysisData['ResultDict'][k]))
    5   third sample response
    h1  another sample response
    >>> alpha.theoryAnalysis.theoryAnalyzer.removeFromAnalysisData(sc, ['h1', '5'])
    >>> sc.analysisData['ResultDict']
    {}
    '''  
    addAnalysisData(score)
    if isinstance(dictKeys, list):
        for dictKey in dictKeys:
            try:
                del score.analysisData['ResultDict'][dictKey]
            except:
                pass
                #raise TheoryAnalyzerException('got a dictKey to remove from resultDictionary that wasnt in the dictionary: %s', dictKey)
    else:
        try:
            del score.analysisData['ResultDict'][dictKeys] 
        except:
            pass
            #raise TheoryAnalyzerException('got a dictKey to remove from resultDictionary that wasn''t in the dictionary: %s', dictKeys)
#        
def getKeyMeasureMap(score):
    '''
    returns the keymeasuremap in the score, if present. returns None otherwise
    '''
    addAnalysisData(score)
    if 'KeyMeasureMap' in score.analysisData:
        return score.analysisData['KeyMeasureMap']
    else:
        return None

def setKeyMeasureMap(score, keyMeasureMap):
    '''
    easily specify the key of the score by measure in a dictionary correlating measure number to key, such as
    {1:'C', 2:'D', 3:'B-',5:'g'}. optionally pass in the music21 key object or the key string. This is used
    for analysis purposes only - no key object is actually added to the score.
    Check the music xml to verify measure numbers; pickup measures are usually 0.
    
    >>> from music21.alpha.theoryAnalysis import *
    >>> n1 = note.Note('c5')
    >>> n1.quarterLength = 4
    >>> n2 = note.Note('f4')
    >>> n2.quarterLength = 2
    >>> n3 = note.Note('g4')
    >>> n3.quarterLength = 2
    >>> sc = stream.Score()
    >>> part0 = stream.Part()
    >>> part0.append(n1)
    >>> part1 = stream.Part()
    >>> part1.append(n2)
    >>> part1.append(n3)
    >>> sc.insert(part0)
    >>> sc.insert(part1)
    >>> alpha.theoryAnalysis.theoryAnalyzer.setKeyMeasureMap(sc, {1:'C',2:'a'})
    >>> alpha.theoryAnalysis.theoryAnalyzer.getKeyMeasureMap(sc)[1]
    'C'
    >>> alpha.theoryAnalysis.theoryAnalyzer.getKeyMeasureMap(sc)[2]
    'a'
    '''
    addAnalysisData(score)
    score.analysisData['KeyMeasureMap'] = keyMeasureMap
    
def getKeyAtMeasure(score, measureNumber):
    '''
    uses keyMeasureMap to return music21 key object. If keyMeasureMap not specified,
    returns key analysis of theory score as a whole.  
    
    >>> from music21.alpha.theoryAnalysis import *
    >>> s = stream.Score()
    >>> alpha.theoryAnalysis.theoryAnalyzer.setKeyMeasureMap(s, {1:'C', 2:'G', 4:'a', 7:'C'})
    >>> alpha.theoryAnalysis.theoryAnalyzer.getKeyAtMeasure(s, 3)
    <music21.key.Key of G major>
    >>> alpha.theoryAnalysis.theoryAnalyzer.getKeyAtMeasure(s, 5)
    <music21.key.Key of a minor>
    >>> sc = corpus.parse('bach/bwv66.6')
    >>> alpha.theoryAnalysis.theoryAnalyzer.getKeyAtMeasure(sc, 5)
    <music21.key.Key of f# minor>
    '''
    keyMeasureMap = getKeyMeasureMap(score)
    if keyMeasureMap:
        for dictKey in sorted(list(keyMeasureMap.keys()), reverse=True):
            if measureNumber >= dictKey:                             
                if common.isStr(keyMeasureMap[dictKey]):
                    return key.Key(key.convertKeyStringToMusic21KeyString(keyMeasureMap[dictKey]))
                else:
                    return keyMeasureMap[dictKey]
        if measureNumber == 0: #just in case of a pickup measure
            if 1 in keyMeasureMap:
                return key.Key(key.convertKeyStringToMusic21KeyString(keyMeasureMap[1]))
        else:
            return score.analyze('key')
    else:
        return score.analyze('key')

class TheoryAnalyzerException(music21.Music21Exception):
    pass

# ------------------------------------------------------------

class Test(unittest.TestCase):
    
    def testChordMotionExample(self):
        pass # in doctest
#         from music21 import harmony, theoryAnalysis
#         p = corpus.parse('leadsheet').flat.getElementsByClass('Harmony')
#         harmony.realizeChordSymbolDurations(p)
#         averageMotion = 0
#         l = alpha.theoryAnalysis.theoryAnalyzer.getLinearSegments(p,0,2, ['Harmony'])
#         for x in l:
#             averageMotion+= abs(x.rootInterval().intervalClass)
#         averageMotion = averageMotion // len(l)
#         self.assertEqual(averageMotion, 4)
#     
        
    
class TestExternal(unittest.TestCase):
    
    def runTest(self):
        pass 
    
    def demo(self):
        from music21 import converter
        sc = converter.parse('/Users/bhadley/Dropbox/Music21Theory/TestFiles/TheoryAnalyzer/TATest.xml')
        identifyCommonPracticeErrors(sc)
        
        #sc.show()
    def removeNHTones(self):
        from music21.alpha.theoryAnalysis import theoryAnalyzer
        p = corpus.parse('bwv6.6').measures(0,20)
        p.show()
        theoryAnalyzer.removePassingTones(p)
        theoryAnalyzer.removeNeighborTones(p)
        p.show()
                
if __name__ == "__main__":
    music21.mainTest(Test)

    
    
    
