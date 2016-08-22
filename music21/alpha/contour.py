# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         contour.py
# Purpose:      Represent a piece by its contour
#
# Authors:      Daniel Manesh
#
# Copyright:    Copyright © 2009-2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
This module defines the ContourFinder and AggregateContour objects.
'''
from __future__ import division, print_function

import random
import unittest

from music21 import base # for _missingImport testing.
from music21 import repeat
from music21 import exceptions21
from music21 import corpus

from music21 import environment
_MOD = 'contour.py'
environLocal = environment.Environment(_MOD)

#---------------------------------------------------
class ContourException(exceptions21.Music21Exception):
    pass

class OverwriteException(exceptions21.Music21Exception):
    pass

def _getExtendedModules():
    '''
    this is done inside a def, so that the slow import of matplotlib is not done
    in ``from music21 import *`` unless it's actually needed.

    Returns a tuple: (plt, numpy, sp = None)
    '''
    if 'matplotlib' in base._missingImport:
        raise ContourException(
            'could not find matplotlib, contour mapping is not allowed (numpy is also required)')
    if 'numpy' in base._missingImport:
        raise ContourException('could not find numpy, contour mapping is not allowed')    
    import matplotlib.pyplot as plt # @UnresolvedImport
    import numpy
    return (plt, numpy)



class ContourFinder(object):
    def __init__(self, s=None):
        '''
        ContourFinder is a class for finding 2-dimensional contours 
        of a piece based on different metrics.  
        
        Predefined metrics are 'dissonance', 'tonality', and 'spacing'.  
        To get a contour, use ContourFinder(myStream).getContour('dissonance'), for example.
        
        If you wish to create your own metric for giving a numerical score to a stream, you can call 
        ContourFinder(myStream).getContour('myMetricName', metric=myMetric)
        
        ContourFinder looks at a moving window of m measures, and moves that window by 
        n measures each time.  
        M and n are specified by 'window' and 'slide', which are both 1 by default.    
        
        
        >>> s = corpus.parse('bwv29.8')
        >>> #_DOCS_SHOW ContourFinder(s).plot('tonality')
        
        TODO: image here...
        
        '''
        self.s = s # a stream.Score object
        self.sChords = None #lazy evaluation...
        self.key = None
        
        self._contours = { } #A dictionary mapping a contour type to a normalized contour dictionary
        
        #self.metrics contains a dictionary mapping the name of a metric to a tuple (x,y) 
        # where x=metric function and y=needsChordify
        
        self._metrics = {"dissonance": (self.dissonanceMetric, True), 
                         "spacing": (self.spacingMetric, True), 
                        "tonality": (self.tonalDistanceMetric, False) }
        self.isContourFinder = True
        
        
    def setKey(self, key):
        '''
        Sets the key of ContourFinder's internal stream.  If not set manually, self.key will
        be determined by self.s.analyze('key'). 
         
        '''
        self.key = key
        
    def getContourValuesForMetric(self, metric, window=1, slide=1, needChordified=False):
        '''
        Returns a dictionary mapping measure numbers to that measure's score under 
        the provided metric.
        Ignores pickup measures entirely.
        
        Window is a positive integer indicating how many measure the metric should 
        look at at once, and slide is 
        a positive integer indicating by how many measures the window should slide 
        over each time the metric is measured.
                
        e.g. if window=4 and slide=2, metric = f, the result will be of the form:
        { measures 1-4: f(measures 1-4), 
        measures 3-6: f(measures 3-6), 
        measures 5-8: f( measures5-8), ...}
        
        >>> metric = lambda s: len(s.measureOffsetMap())
        >>> c = corpus.parse('bwv10.7')
        >>> res = alpha.contour.ContourFinder(c).getContourValuesForMetric(metric, 3, 2, False)
        
        >>> resList = sorted(list(res.keys()))
        >>> resList
        [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21]
        >>> [res[x] for x in resList]
        [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2]
        
        
        OMIT_FROM_DOCS
        >>> #set([1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21]).issubset(set(res.keys()))
        
        '''
        res = {}
        
        
        if needChordified:
            if self.sChords is None:
                self.sChords = self.s.chordify()
            s = self.sChords
        else:
            s = self.s
            
        
        mOffsets = s.measureOffsetMap()
        hasPickup = repeat.RepeatFinder(s).hasPickup()
        numMeasures = len(mOffsets) - hasPickup
    
        
        for i in range(1, numMeasures+1, slide):  #or numMeasures-window+1
            fragment = s.measures(i, i+window-1)
            
            #TODO: maybe check that i+window-1 is less than numMeasures + window/2
            
            resValue = metric(fragment)
            
            res[i] = resValue
            
        return res
    
    #TODO: tests that use simple 4-bar pieces that we have to create...
    #ALSO: Need pictures or something! Need a clear demonstration!
    def getContour(self, cType, window=None, slide=None, overwrite=False, 
                   metric=None, needsChordify=False, normalized=False):
        '''
        Stores and then returns a normalized contour of the type cType.  
        cType can be either 'spacing', 'tonality', or 'dissonance'.
        
        If using a metric that is not predefined, cType is any string that 
        signifies what your metric measures.  
        In this case, you must pass getContour a metric function which takes 
        in a music21 stream and outputs a score.
        If passing a metric that requires the music21 stream be just chords, 
        specify needsChordify=True.  
        
        Window is how many measures are considered at a time and slide is the 
        number of measures the window moves
        over each time.  By default, measure and slide are both 1. 
                
        Each time you call getContour for a cType, the result is cached.  
        If you wish to get the contour 
        for the same cType more than once, with different parameters 
        (with a different window and slide, for example)
        then specify overwrite=True
        
        To get a contour where measures map to the metric values, 
        use normalized=False (the default), but to get a contour
        which evenly divides time between 1.0 and 100.0, use normalized=True
        
        >>> cf = alpha.contour.ContourFinder( corpus.parse('bwv10.7'))
        >>> mycontour = cf.getContour('dissonance')
        >>> [mycontour[x] for x in sorted(mycontour.keys())]
        [0.0, 0.25, 0.5, 0.5, 0.0, 0.0, 0.25, 0.75, 0.0, 0.0, 0.5, 0.75, 0.75, 
         0.0, 0.5, 0.5, 0.5, 0.5, 0.75, 0.75, 0.75, 0.0]
        
        >>> mycontour = cf.getContour('always one', 2, 2, metric= lambda x: 1.0)
        >>> [mycontour[x] for x in sorted(mycontour.keys())]
        [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
        
        >>> mycontour = cf.getContour('spacing', metric = lambda x: 2, overwrite=False)
        Traceback (most recent call last):
        OverwriteException: Attempted to overwrite 'spacing' metric but did 
                not specify overwrite=True
        
        >>> mycontour = cf.getContour('spacing', slide=3, metric = lambda x: 2.0, overwrite=True)
        >>> [mycontour[x] for x in sorted(mycontour.keys())]
        [2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0]
        
        >>> mycontour = cf.getContour('spacing')
        >>> [mycontour[x] for x in sorted(mycontour.keys())]
        [2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0]        
        '''
        
        if overwrite is False:
            if cType in self._contours:
                if window is not None or slide is not None:
                    raise OverwriteException(
                        "Attempted to overwrite cached contour of type {0}".format(cType) + 
                        " but did not specify overwrite=True")
                else:
                    return self._contours[cType]
            elif cType in self._metrics:
                if metric is not None:
                    raise OverwriteException("Attempted to overwrite '{0}' ".format(cType) + 
                                             "metric but did not specify overwrite=True")
                else:
                    metric, needsChordify = self._metrics[cType]
            else:
                self._metrics[cType] = (metric, needsChordify)
        else:
            if metric is None:
                if cType in self._metrics:
                    metric, needsChordify = self._metrics[cType]
                else:
                    raise ContourException("Must provide your own metric for type: %s" % cType)
            
        
        if slide is None:
            slide = 1
            
        if window is None:
            window = 1
            
        contour = self.getContourValuesForMetric(metric, window, slide, needsChordify)
        
        if normalized:
            contour = self._normalizeContour(contour, 100.0)
        
        self._contours[cType] = contour
        
        return contour
    
    
    def _normalizeContour(self, contourDict, maxKey):
        '''
        Normalize a contour dictionary so that the values of the keys range from 0.0 to length.
        
        >>> mycontour = { 0.0: 1.0, 3.0: 0.5, 6.0: 0.8, 9.0: 0.3, 12.0: 0.15, 
        ...            15.0: 0.13, 18.0: 0.4, 21.0: 0.6 }
        >>> res = alpha.contour.ContourFinder()._normalizeContour(mycontour, 100)
        >>> resKeys = list(res.keys())
        >>> resKeys.sort()
        >>> contourKeys = list(mycontour.keys())
        >>> contourKeys.sort()
        >>> len(contourKeys) == len(resKeys)
        True
        >>> x = True
        >>> for i in range(len(contourKeys)):
        ...    if mycontour[contourKeys[i]] != res[resKeys[i]]:
        ...        x = False
        >>> x
        True
        >>> 100.0 in res
        True
        >>> 0.0 in res
        True
        '''
        myKeys = list(contourDict.keys())
        myKeys.sort()
        numKeys = len(myKeys)
        
        spacing = (maxKey)/(numKeys-1.0)
        res = {}
        i = 0.0
                
        for j in myKeys:
            
            res[round(i, 3)] = round(float(contourDict[j]), 5)
            i += spacing
            
        return res
        
    #TODO: give same args as getContour, maybe? Also, test this.
    def plot(self, cType, contourIn=None, regression=True, order=4, 
             title='Contour Plot', fileName=None):
        (plt, numpy) = _getExtendedModules()

        if contourIn is None:
            if cType not in self._contours:
                contourIn = self.getContour(cType)
            else:
                contourIn = self._contours[cType]
        
        x = contourIn.keys()
        x.sort()
        y = [contourIn[i] for i in x]
        
        plt.plot(x, y, '.', label='contour', markersize=5)
        
        
        if regression:
            p = numpy.poly1d( numpy.polyfit(x, y, order) )
    
            t = numpy.linspace(0, x[-1], x[-1]+1)
            
            
            
            plt.plot(t, p(t), 'o-', label='estimate', markersize=1) #probably change label
            
        plt.xlabel('Time (arbitrary units)')
        plt.ylabel('Value for %s metric' % cType) 
        plt.title(title) #say for which piece
        #plt.savefig(filename + '.png')
        
        if fileName is not None:
            plt.savefig(fileName + '.png')
        else:
            plt.show()
        
        plt.clf()
    

    def randomize(self, contourDict):
        '''
        Returns a version of contourDict where the keys-to-values mapping is scrambled.  
        
        
        >>> myDict = {1:1, 2:2, 3:3, 4:4, 5:5, 6:6, 7:7, 8:8, 9:9, 10:10, 11:11, 12:12, 13:13, 
        ...           14:14, 15:15, 16:16, 17:17, 18:18, 19:19, 20:20}
        >>> res = alpha.contour.ContourFinder().randomize(myDict)
        >>> res == myDict
        False
        >>> sorted(list(res.keys())) == sorted(list(myDict.keys()))
        True
        >>> sorted(list(res.values())) == sorted(list(myDict.values()))
        True         
        
        '''
        res = {}
        
        myKeys = list(contourDict.keys())
        myValues = list(contourDict.values())
        
        random.shuffle(myKeys)
        
        for i in range(len(myKeys)):
            res[myKeys[i]] = myValues[i]
        
        return res
    
    
    #--- code for the metrics
    def _calcGenericMetric(self, inpStream, chordMetric):
        '''
        Helper function which, given a metric value for a chord, calculates a metric
        for a series of measures by taking the sum of each chord's metric value weighted by
        its duration. 
        
        '''
        
        score = 0
        n=0
        
        for measure in inpStream:
            if 'Measure' in measure.classes:
                for chord in measure:
                    if 'Chord' in chord.classes:
                        dur = chord.duration.quarterLength
                        score += chordMetric(chord)*dur
                        n += dur
                        
        if n != 0:
            return score / n
        else:
            return None
            
    def dissonanceMetric(self, inpStream):
        '''
        inpStream is a stream containing some number of measures which each contain chords.  
        Output is a number between 0 and 1 which is proportional to the number of dissonant chords. 
        
        To work correctly, input must contain measures and no parts.
        
        
        >>> c = corpus.parse('bwv102.7').chordify()
        >>> alpha.contour.ContourFinder().dissonanceMetric( c.measures(1, 1) )
        0.25
        >>> alpha.contour.ContourFinder().dissonanceMetric( c.measures(8, 8) )
        0.5
        >>> alpha.contour.ContourFinder().dissonanceMetric( c.measures(1, 10)) < 1.0
        True
        '''
        
        return self._calcGenericMetric(inpStream, lambda x: 1-x.isConsonant() )
    
    def spacingMetric(self, inpStream):
        '''
        Defines a metric which takes a music21 stream containng measures and no parts.
        This metric measures how spaced out notes in a piece are.  
        
        '''
        
        #TODO: FIGURE OUT IF THIS IS REASONABLE! MIGHT WANT TO JUST DO: sqrt( sum(dist^2) )  
        def spacingForChord(chord):
            pitches = [ x.ps for x in chord.pitches ]
            pitches.sort()
            res = 0
            
            if len(pitches) <= 1:
                return 0
            elif len(pitches) == 2:
                return (pitches[1]-pitches[0])
            else:
                res += (pitches[1]-pitches[0])**(.7)
                for i in range(1, len(pitches)-1):
                    res += (pitches[i+1]-pitches[i])**(1.5)
            return res
        
        return self._calcGenericMetric(inpStream, spacingForChord)
        
        
        
    def tonalDistanceMetric(self, inpStream):
        '''
        Returns a number between 0.0 and 1.0 that is a measure of how far away the key of
        inpStream is from the key of ContourFinder's internal stream.  
        '''
        
        if self.key is None:
            self.key = self.s.analyze('key')
        
        guessedKey = inpStream.analyze('key')
        
        certainty = -2 #should be replaced by a value between -1 and 1
        
        if guessedKey == self.key:
            certainty = guessedKey.correlationCoefficient
        else:
            for pkey in guessedKey.alternateInterpretations:
                if pkey == self.key:
                    certainty =  pkey.correlationCoefficient
                    break
                
        return (1 - certainty)/2.0
        


class AggregateContour(object):
    
    def __init__(self, aggContours=None):
        '''
        An AggragateContour object is an object that stores and consolidates 
        contour information for a large group 
        of pieces.  
        
        To add a piece to the aggregate contour, use 
        AggregateContour.addPieceToContour(piece, cType), where cType is
        the type of contour (the default possibilities are 
        'tonality', 'spacing', and 'dissonance'), and piece is either
        a parsed music21 stream or a ContourFinder object.  
        
        To get the combined contour as list of ordered pairs, use 
        AggragateContour.getCombinedContour(), and to 
        get the combined contour as a polynomial approximation, use 
        AggragateContour.getCombinedContourPoly().
        You can plot contours with AggragateContour.plotAggragateContour(cType).  
        
        To compare a normalized contour to the aggragate, use 
        AggragateContour.dissimilarityScore(cType, contour).
        
        '''
        if aggContours is None:
            self.aggContours = {}  
            # = {'spacing': [ {1:2, 2:3}, {...}, ...], 'tonality': [...], ... }
        else:
            self.aggContours = aggContours
        self._aggContoursAsList = {}
        self._aggContoursPoly = {}
    
    def addPieceToContour(self, piece, cType, metric=None, window=1, 
                          slide=1, order=8, needsChordify=False):
        '''
        Adds a piece to the aggregate contour.  
        
        piece is either a music21 stream, or a ContourFinder object (which 
        should have a stream wrapped inside of it).
        
        cType is the contour type.  
        
        If using a metric that is not predefined, cType is any string 
        that signifies what your metric measures.  
        In this case, you must pass getContour a metric function 
        which takes in a music21 stream and outputs a score.
        If passing a metric that requires the music21 stream be 
        just chords, specify needsChordify=True.  
        
        Window is how many measures are considered at a time and 
        slide is the number of measures the window moves
        over each time.  By default, measure and slide are both 1. 
        '''
        if hasattr(piece, 'isContourFinder') and piece.isContourFinder:
            pass
        else: 
            piece = ContourFinder(piece)
            
        contour = piece.getContour(cType, window=window, slide=slide, 
                                   overwrite=False, metric=metric, 
                                   needsChordify=needsChordify, normalized=True)
        
        
        
        if cType not in self.aggContours:
            self.aggContours[cType] = []
            
        self.aggContours[cType].append(contour)
        
        return
        
        
        
    
    def getCombinedContour(self, cType): #, metric=None, window=1, slide=1, order=8):
        '''
        Returns the combined contour of the type specified by cType.  Instead of a dictionary,
        this contour is just a list of ordered pairs (tuples) with the 
        first value being time and the
        second value being the score.  
        
        '''
        
        if cType in self._aggContoursAsList:
            return self._aggContoursAsList[cType]
        elif cType in self.aggContours:
            contour = self.aggContours[cType]
            res = []
            for contDict in contour:
                res.extend( [ (x, contDict[x]) for x in contDict] )
            self._aggContoursAsList[cType] = res
            return res
        else:
            return None
        
    def getCombinedContourPoly(self, cType, order=8):
        '''
        Returns the polynomial fit for the aggregate contour of type cType.  
        
        Order is the order of the resulting polynomial.  e.g. For a linear regression, order=1.  
        '''
        (unused_plt, numpy) = _getExtendedModules()

        if cType in self._aggContoursPoly:
            return self._aggContoursPoly[cType]
        elif cType in self._aggContoursAsList:
            contList = self._aggContoursAsList[cType]
        elif cType in self.aggContours:
            contList = self.getCombinedContour(cType)
        else:
            return None
        
        x, y = zip(*contList)
        self._aggContoursPoly[cType] = numpy.poly1d( numpy.polyfit(x, y, order))
        return self._aggContoursPoly[cType]
        
    
    def plot(self, cType, showPoints=True, comparisonContour=None, regression=True, order=6):
        
        #TODO: maybe have an option of specifying a different 
        # color thing for each individual contour...
        
        if cType not in self.aggContours: #['dissonance', 'tonality', 'distance']:
            return None
        else:
            contour = self.getCombinedContour(cType)
        
        
        
#         elif cType not in self._aggContoursAsList:
#             contour = self.getCombinedContour(cType)
#         else:
#             contour = self._aggContoursAsList[cType]
#         
        (plt, numpy) = _getExtendedModules() #@UnusedVariable

        x, y = zip(*contour)   
        
        if showPoints:     
            plt.plot(x, y, '.', label='contour', markersize=5)
        
        if comparisonContour is not None:
            x = comparisonContour.keys()
            y = [comparisonContour[i] for i in x]
            
            plt.plot(x, y, '.', label='compContour', markersize=8)
        #p = numpy.poly1d( numpy.polyfit(x, y, order))
        p = self.getCombinedContourPoly(cType) 
            
        if regression:
            t = numpy.linspace(0, max(x), max(x)+1)  
            plt.plot(t, p(t), 'o-', label='estimate', markersize=1) #probably change label
            
        plt.xlabel('Time (percentage of piece)')
        plt.ylabel('Value') #change this
        plt.title('title') #say for which piece
        #plt.savefig(filename + '.png')
        plt.show()
        
        plt.clf()
        
    def dissimilarityScore(self, cType, contourDict):
        '''
        Returns a score based on how dissimilar the input contourDict is from 
        the aggregate contour of type cType.  
        
        Requires contourDict be normalized with values from 1.0 to 100.0 
        
        '''        
        p = self.getCombinedContourPoly(cType)
        
        return sum( [abs(contourDict[x] - p(x)) for x in contourDict] )
    
    
    
_DOC_ORDER = [ContourFinder, AggregateContour]

def _getOutliers():
    BCI = corpus.chorales.Iterator(returnType='filename')
    highestNum = BCI.highestNumber
    currentNum = BCI.currentNumber
    lengthDict = {}
    for chorale in BCI:
        print(currentNum)
        
        if currentNum is not highestNum:
            currentNum = BCI.currentNumber
        
        s = corpus.parse(chorale)
        
        if chorale == 'bach/bwv277':
            continue
        elif len(s.parts) is not 4:
            continue
        
        rf = repeat.RepeatFinder(s)
        s = rf.simplify()
        lengthDict[chorale] = len(s.measureOffsetMap()) - rf.hasPickup()
        
    return lengthDict

    
        
def _runExperiment():
    #get chorale iterator, initialize ac
    
    ac = AggregateContour()
    #unresolved problem numbers: 88 (repeatFinder fails!)
    
    goodChorales = ['bach/bwv330', 'bach/bwv245.22', 'bach/bwv431', 
                    'bach/bwv324', 'bach/bwv384', 'bach/bwv379', 'bach/bwv365', 
                    'bach/bwv298', 'bach/bwv351', 'bach/bwv341', 'bach/bwv421', 
                    'bach/bwv420', 'bach/bwv331', 'bach/bwv84.5', 'bach/bwv253', 
                    'bach/bwv434', 'bach/bwv26.6', 'bach/bwv64.2', 'bach/bwv313', 
                    'bach/bwv314', 'bach/bwv166.6', 'bach/bwv414', 'bach/bwv264', 
                    'bach/bwv179.6', 'bach/bwv67.7', 'bach/bwv273', 'bach/bwv373', 
                    'bach/bwv376', 'bach/bwv375', 'bach/bwv151.5', 'bach/bwv47.5', 
                    'bach/bwv197.10', 'bach/bwv48.3', 'bach/bwv88.7', 'bach/bwv310', 
                    'bach/bwv244.46', 'bach/bwv153.1', 'bach/bwv69.6', 'bach/bwv333', 
                    'bach/bwv104.6', 'bach/bwv338', 'bach/bwv155.5', 'bach/bwv345', 
                    'bach/bwv435', 'bach/bwv323', 'bach/bwv245.3', 'bach/bwv144.3', 'bach/bwv405', 
                    'bach/bwv406', 'bach/bwv316', 'bach/bwv258', 'bach/bwv254', 
                    'bach/bwv256', 'bach/bwv257', 'bach/bwv69.6-a', 'bach/bwv86.6', 
                    'bach/bwv388', 'bach/bwv308', 'bach/bwv307', 'bach/bwv244.32', 
                    'bach/bwv268', 'bach/bwv260', 'bach/bwv110.7', 'bach/bwv40.3', 
                    'bach/bwv164.6', 'bach/bwv9.7', 'bach/bwv114.7', 'bach/bwv364', 
                    'bach/bwv291', 'bach/bwv245.17', 'bach/bwv297', 'bach/bwv20.11', 
                    'bach/bwv319', 'bach/bwv244.3', 'bach/bwv248.35-3', 'bach/bwv96.6', 
                    'bach/bwv48.7', 'bach/bwv337', 'bach/bwv334', 'bach/bwv101.7', 
                    'bach/bwv168.6', 'bach/bwv55.5', 'bach/bwv154.3', 'bach/bwv89.6', 
                    'bach/bwv2.6', 'bach/bwv392', 'bach/bwv395', 'bach/bwv401', 'bach/bwv408', 
                    'bach/bwv259', 'bach/bwv382', 'bach/bwv244.37', 'bach/bwv127.5', 
                    'bach/bwv44.7', 'bach/bwv303', 'bach/bwv263', 'bach/bwv262', 
                    'bach/bwv248.46-5', 'bach/bwv13.6', 'bach/bwv377', 'bach/bwv416', 
                    'bach/bwv354', 'bach/bwv244.10', 'bach/bwv288', 'bach/bwv285', 
                    'bach/bwv113.8', 'bach/bwv393', 'bach/bwv360', 'bach/bwv363', 
                    'bach/bwv367', 'bach/bwv90.5', 'bach/bwv245.11', 'bach/bwv5.7', 
                    'bach/bwv289', 'bach/bwv83.5', 'bach/bwv359', 'bach/bwv352', 
                    'bach/bwv102.7', 'bach/bwv394', 'bach/bwv227.11', 'bach/bwv244.40', 
                    'bach/bwv244.44', 'bach/bwv424', 'bach/bwv244.25', 'bach/bwv80.8', 
                    'bach/bwv244.54', 'bach/bwv78.7', 'bach/bwv57.8', 'bach/bwv194.6', 
                    'bach/bwv397', 'bach/bwv64.8', 'bach/bwv318', 'bach/bwv315', 
                    'bach/bwv153.5', 'bach/bwv39.7', 'bach/bwv108.6', 'bach/bwv386', 
                    'bach/bwv25.6', 'bach/bwv417', 'bach/bwv415', 'bach/bwv302', 
                    'bach/bwv380', 'bach/bwv74.8', 'bach/bwv422', 'bach/bwv133.6', 
                    'bach/bwv270', 'bach/bwv272', 'bach/bwv38.6', 'bach/bwv271', 'bach/bwv183.5', 
                    'bach/bwv103.6', 'bach/bwv287', 'bach/bwv32.6', 'bach/bwv245.26', 
                    'bach/bwv248.5', 'bach/bwv411', 'bach/bwv369', 'bach/bwv339', 
                    'bach/bwv361', 'bach/bwv399', 'bach/bwv16.6', 'bach/bwv419', 
                    'bach/bwv87.7', 'bach/bwv4.8', 'bach/bwv358', 'bach/bwv154.8', 
                    'bach/bwv278', 'bach/bwv156.6', 'bach/bwv248.33-3', 'bach/bwv81.7', 
                    'bach/bwv227.7', 'bach/bwv427', 'bach/bwv77.6', 'bach/bwv410', 
                    'bach/bwv329', 'bach/bwv85.6', 'bach/bwv385', 'bach/bwv309', 
                    'bach/bwv305', 'bach/bwv18.5-l', 'bach/bwv18.5-w', 'bach/bwv197.5', 
                    'bach/bwv30.6', 'bach/bwv296', 'bach/bwv292', 'bach/bwv353', 
                    'bach/bwv301', 'bach/bwv347', 
                    'bach/bwv284', 'bach/bwv429', 'bach/bwv436', 'bach/bwv430', 
                    'bach/bwv381', 'bach/bwv36.4-2', 'bach/bwv412', 'bach/bwv65.7', 'bach/bwv280', 
                    'bach/bwv169.7', 'bach/bwv428', 'bach/bwv346', 'bach/bwv248.12-2', 
                    'bach/bwv426', 
                    'bach/bwv159.5', 'bach/bwv121.6', 'bach/bwv418', 'bach/bwv28.6', 
                    'bach/bwv326', 'bach/bwv327', 'bach/bwv321', 'bach/bwv65.2', 
                    'bach/bwv144.6', 'bach/bwv194.12', 'bach/bwv398', 'bach/bwv317', 
                    'bach/bwv153.9', 'bach/bwv300', 'bach/bwv56.5', 'bach/bwv423',
                    'bach/bwv306', 'bach/bwv40.6', 'bach/bwv123.6', 'bach/bwv245.28', 
                    'bach/bwv279', 'bach/bwv378', 'bach/bwv366', 'bach/bwv45.7', 'bach/bwv295', 
                    'bach/bwv245.14', 'bach/bwv122.6', 'bach/bwv355', 'bach/bwv357', 
                    'bach/bwv94.8', 'bach/bwv348', 'bach/bwv349', 'bach/bwv312', 
                    'bach/bwv325', 'bach/bwv245.37', 'bach/bwv37.6', 'bach/bwv283', 
                    'bach/bwv299', 'bach/bwv294', 'bach/bwv245.15', 'bach/bwv176.6', 
                    'bach/bwv391', 'bach/bwv350', 'bach/bwv400', 'bach/bwv372', 
                    'bach/bwv402', 'bach/bwv282', 'bach/bwv374', 'bach/bwv60.5', 
                    'bach/bwv356', 'bach/bwv389', 'bach/bwv40.8', 'bach/bwv174.5', 
                    'bach/bwv340', 'bach/bwv433', 'bach/bwv322', 'bach/bwv403', 
                    'bach/bwv267', 'bach/bwv261', 'bach/bwv245.40', 'bach/bwv33.6', 
                    'bach/bwv269', 'bach/bwv266', 'bach/bwv43.11', 'bach/bwv10.7',
                    'bach/bwv343', 'bach/bwv311']
    currentNum = 1
    
    #BCI = corpus.chorales.Iterator(1, 371, returnType='filename') #highest number is 371
    #highestNum = BCI.highestNumber
    #currentNum = BCI.currentNumber
    for chorale in goodChorales: 
        
        print(currentNum)
        
        currentNum +=1
          
#         '''          
#         if chorale == 'bach/bwv277':
#             continue    #this chorale here has an added measure 
#                         # container randomly in the middle which breaks things.  
#         '''
        chorale = corpus.parse(chorale)
        
#         '''
#         if len(chorale.parts) is not 4:
#             print("chorale had too many parts")
#             continue
#         '''
        
        chorale = repeat.RepeatFinder(chorale).simplify()
        
#         '''
#         length = len( chorale.measureOffsetMap() )
#         if length < 10:
#             print("too short")
#             continue
#         elif length > 25:
#             print("too long")
#             continue
#         '''
        cf= ContourFinder(chorale)
        ac.addPieceToContour(cf, 'dissonance')
        ac.addPieceToContour(cf, 'tonality')
        ac.addPieceToContour(cf, 'spacing')
    
    print(ac.aggContours['dissonance'])
    print(ac.aggContours['tonality'])
    print(ac.aggContours['spacing'])
    
    for cType in ['spacing', 'tonality', 'dissonance']:
        
        print("considering", cType, ": ")
        
        cf = ContourFinder()
        totalSuccesses = 0
        totalFailures = 0
        
        for j in range( len(ac.aggContours[cType])): 
            contDict = ac.aggContours[cType][j]
            
            observed = ac.dissimilarityScore(cType, contDict)
            successes = 0
            
            for i in range(100):
                randomized = ac.dissimilarityScore( cType, cf.randomize(contDict) )
                
                if randomized > observed:
                    successes += 1
            
            if successes > 50:
                totalSuccesses += 1
                #print "GREAT SUCCESS!"
            else:
                totalFailures += 1
                print("failure: chorale " + goodChorales[j])  #index ", str(i)
        
        print(cType, ": totalSuccesses =", str(totalSuccesses), 
              "totalFailures =", str(totalFailures))

def _plotChoraleContours():
    BCI = corpus.chorales.Iterator(1, 75, returnType='filename')
    for chorale in BCI:
        s = corpus.parse(chorale)
        cf = ContourFinder(s)
        chorale = chorale[5:]
        print(chorale)
        #cf.plot('dissonance', fileName= chorale + 'dissonance', regression=False)
        try:
            cf.plot('tonality', fileName= chorale + 'tonality', regression=False)
        except exceptions21.Music21Exception:
            print(chorale)
            s.show()
            break
    pass

    
#------------------------
class Test(unittest.TestCase):
    
    def runTest(self):
        pass
    
if __name__ == "__main__":
    import music21
    music21.mainTest(Test)

