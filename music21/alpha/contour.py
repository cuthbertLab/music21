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
        raise ContourException('could not find matplotlib, contour mapping is not allowed (numpy is also required)')
    if 'numpy' in base._missingImport:
        raise ContourException('could not find numpy, contour mapping is not allowed')    
    import matplotlib.pyplot as plt # @UnresolvedImport
    import numpy
    return (plt, numpy)



class ContourFinder(object):
    def __init__(self, s=None):
        '''
        ContourFinder is a class for finding 2-dimensional contours of a piece based on different metrics.  
        
        Predefined metrics are 'dissonance', 'tonality', and 'spacing'.  
        To get a contour, use ContourFinder(myStream).getContour('dissonance'), for example.
        
        If you wish to create your own metric for giving a numerical score to a stream, you can call 
        ContourFinder(myStream).getContour('myMetricName', metric=myMetric)
        
        ContourFinder looks at a moving window of m measures, and moves that window by n measures each time.  
        M and n are specified by 'window' and 'slide', which are both 1 by default.    
        
        
        >>> s = corpus.parse('bwv29.8')
        >>> #_DOCS_SHOW ContourFinder(s).plot('tonality')
        
        TODO: image here...
        
        '''
        self.s = s # a stream.Score object
        self.sChords = None #lazy evaluation...
        self.key = None
        
        self._contours = { } #A dictionary mapping a contour type to a normalized contour dictionary
        
        #self.metrics contains a dictionary mapping the name of a metric to a tuple (x,y) where x=metric function and y=needsChordify
        
        self._metrics = {"dissonance": (self.dissonanceMetric, True), "spacing": (self.spacingMetric, True), 
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
        Returns a dictionary mapping measure numbers to that measure's score under the provided metric.
        Ignores pickup measures entirely.
        
        Window is a positive integer indicating how many measure the metric should look at at once, and slide is 
        a positive integer indicating by how many measures the window should slide over each time the metric is measured.
                
        e.g. if window=4 and slide=2, metric = f, the result will be of the form:
        { measures 1-4: f(measures 1-4), measures 3-6: f(measures 3-6), measures 5-8: f( measures5-8), ...}
        
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
    def getContour(self, cType, window=None, slide=None, overwrite=False, metric=None, needsChordify=False, normalized=False):
        '''
        Stores and then returns a normalized contour of the type cType.  
        cType can be either 'spacing', 'tonality', or 'dissonance'.
        
        If using a metric that is not predefined, cType is any string that signifies what your metric measures.  
        In this case, you must pass getContour a metric function which takes in a music21 stream and outputs a score.
        If passing a metric that requires the music21 stream be just chords, specify needsChordify=True.  
        
        Window is how many measures are considered at a time and slide is the number of measures the window moves
        over each time.  By default, measure and slide are both 1. 
                
        Each time you call getContour for a cType, the result is cached.  If you wish to get the contour 
        for the same cType more than once, with different parameters (with a different window and slide, for example)
        then specify overwrite=True
        
        To get a contour where measures map to the metric values, use normalized=False (the default), but to get a contour
        which evenly divides time between 1.0 and 100.0, use normalized=True
        
        >>> cf = alpha.contour.ContourFinder( corpus.parse('bwv10.7'))
        >>> mycontour = cf.getContour('dissonance')
        >>> [mycontour[x] for x in sorted(mycontour.keys())]
        [0.0, 0.25, 0.5, 0.5, 0.0, 0.0, 0.25, 0.75, 0.0, 0.0, 0.5, 0.75, 0.75, 0.0, 0.5, 0.5, 0.5, 0.5, 0.75, 0.75, 0.75, 0.0]
        
        >>> mycontour = cf.getContour('always one', 2, 2, metric= lambda x: 1.0)
        >>> [mycontour[x] for x in sorted(mycontour.keys())]
        [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
        
        >>> mycontour = cf.getContour('spacing', metric = lambda x: 2, overwrite=False)
        Traceback (most recent call last):
        OverwriteException: Attempted to overwrite 'spacing' metric but did not specify overwrite=True
        
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
                    raise OverwriteException("Attempted to overwrite cached contour of type %s but did not specify overwrite=True" % cType)
                else:
                    return self._contours[cType]
            elif cType in self._metrics:
                if metric is not None:
                    raise OverwriteException("Attempted to overwrite '%s' metric but did not specify overwrite=True" % cType)
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
            
                
#         
#         if cType in self._contours:
#             if overwrite is False:
#                 if metric is not None:
#                     raise OverwriteException("Attempted to calculate a different value for metric %s but did not specify overwrite=True" % cType)
#                 else:
#                     return self._contours[cType] #already calculated!
#             else: #overwrite something we already have cached
#                 
#         elif cType in self._metrics:
#             if metric is not None:
#                 if overwrite is False:
#                     #trying to overwrite something... raise an exception
#                     raise OverwriteException("Attempted to overwrite metric for %s but did not specify overwrite=True" % cType)
#                 else:
#                     self._metrics[cType] = (metric, needsChordify)
#             elif overwrite: #overwrite is true, we are not given a metric, but we have one stored.  
#                 pass
#             else:
#                 metric, needsChordify = self._metrics[cType]
#         else:
#             self._metrics[cType] = (metric, needsChordify) 
#         
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
    def plot(self, cType, contourIn=None, regression=True, order=4, title='Contour Plot', fileName=None):
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
            return score*1.0/n
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
        An AggragateContour object is an object that stores and consolidates contour information for a large group 
        of pieces.  
        
        To add a piece to the aggregate contour, use AggregateContour.addPieceToContour(piece, cType), where cType is
        the type of contour (the default possibilities are 'tonality', 'spacing', and 'dissonance'), and piece is either
        a parsed music21 stream or a ContourFinder object.  
        
        To get the combined contour as list of ordered pairs, use AggragateContour.getCombinedContour(), and to 
        get the combined contour as a polynomial approximation, use AggragateContour.getCombinedContourPoly().
        You can plot contours with AggragateContour.plotAggragateContour(cType).  
        
        To compare a normalized contour to the aggragate, use AggragateContour.dissimilarityScore(cType, contour).
        
        '''
        if aggContours is None:
            self.aggContours = {}  # = {'spacing': [ {1:2, 2:3}, {...}, ...], 'tonality': [...], ... }
        else:
            self.aggContours = aggContours
        self._aggContoursAsList = {}
        self._aggContoursPoly = {}
    
    def addPieceToContour(self, piece, cType, metric=None, window=1, slide=1, order=8, needsChordify=False):
        '''
        Adds a piece to the aggregate contour.  
        
        piece is either a music21 stream, or a ContourFinder object (which should have a stream wrapped inside of it).
        
        cType is the contour type.  
        
        If using a metric that is not predefined, cType is any string that signifies what your metric measures.  
        In this case, you must pass getContour a metric function which takes in a music21 stream and outputs a score.
        If passing a metric that requires the music21 stream be just chords, specify needsChordify=True.  
        
        Window is how many measures are considered at a time and slide is the number of measures the window moves
        over each time.  By default, measure and slide are both 1. 
          
        
        
        '''
        
        if hasattr(piece, 'isContourFinder') and piece.isContourFinder:
            pass
        else: 
            piece = ContourFinder(piece)
            
        contour = piece.getContour(cType, window=window, slide=slide, overwrite=False, metric=metric, 
                                   needsChordify=needsChordify, normalized=True)
        
        
        
        if cType not in self.aggContours:
            self.aggContours[cType] = []
            
        self.aggContours[cType].append(contour)
        
        return
        
        
        
    
    def getCombinedContour(self, cType): #, metric=None, window=1, slide=1, order=8):
        '''
        Returns the combined contour of the type specified by cType.  Instead of a dictionary,
        this contour is just a list of ordered pairs (tuples) with the first value being time and the
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
        
        #TODO: maybe have an option of specifying a different color thing for each individual contour...
        
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
    
    goodChorales = ['bach/bwv330', 'bach/bwv245.22', 'bach/bwv431', 'bach/bwv324', 'bach/bwv384', 'bach/bwv379', 'bach/bwv365', 'bach/bwv298', 'bach/bwv351', 'bach/bwv341', 'bach/bwv421', 'bach/bwv420', 'bach/bwv331', 'bach/bwv84.5', 'bach/bwv253', 'bach/bwv434', 'bach/bwv26.6', 'bach/bwv64.2', 'bach/bwv313', 'bach/bwv314', 'bach/bwv166.6', 'bach/bwv414', 'bach/bwv264', 'bach/bwv179.6', 'bach/bwv67.7', 'bach/bwv273', 'bach/bwv373', 'bach/bwv376', 'bach/bwv375', 'bach/bwv151.5', 'bach/bwv47.5', 'bach/bwv197.10', 'bach/bwv48.3', 'bach/bwv88.7', 'bach/bwv310', 'bach/bwv244.46', 'bach/bwv153.1', 'bach/bwv69.6', 'bach/bwv333', 'bach/bwv104.6', 'bach/bwv338', 'bach/bwv155.5', 'bach/bwv345', 'bach/bwv435', 'bach/bwv323', 'bach/bwv245.3', 'bach/bwv144.3', 'bach/bwv405', 'bach/bwv406', 'bach/bwv316', 'bach/bwv258', 'bach/bwv254', 'bach/bwv256', 'bach/bwv257', 'bach/bwv69.6-a', 'bach/bwv86.6', 'bach/bwv388', 'bach/bwv308', 'bach/bwv307', 'bach/bwv244.32', 'bach/bwv268', 'bach/bwv260', 'bach/bwv110.7', 'bach/bwv40.3', 'bach/bwv164.6', 'bach/bwv9.7', 'bach/bwv114.7', 'bach/bwv364', 'bach/bwv291', 'bach/bwv245.17', 'bach/bwv297', 'bach/bwv20.11', 'bach/bwv319', 'bach/bwv244.3', 'bach/bwv248.35-3', 'bach/bwv96.6', 'bach/bwv48.7', 'bach/bwv337', 'bach/bwv334', 'bach/bwv101.7', 'bach/bwv168.6', 'bach/bwv55.5', 'bach/bwv154.3', 'bach/bwv89.6', 'bach/bwv2.6', 'bach/bwv392', 'bach/bwv395', 'bach/bwv401', 'bach/bwv408', 'bach/bwv259', 'bach/bwv382', 'bach/bwv244.37', 'bach/bwv127.5', 'bach/bwv44.7', 'bach/bwv303', 'bach/bwv263', 'bach/bwv262', 'bach/bwv248.46-5', 'bach/bwv13.6', 'bach/bwv377', 'bach/bwv416', 'bach/bwv354', 'bach/bwv244.10', 'bach/bwv288', 'bach/bwv285', 'bach/bwv113.8', 'bach/bwv393', 'bach/bwv360', 'bach/bwv363', 'bach/bwv367', 'bach/bwv90.5', 'bach/bwv245.11', 'bach/bwv5.7', 'bach/bwv289', 'bach/bwv83.5', 'bach/bwv359', 'bach/bwv352', 'bach/bwv102.7', 'bach/bwv394', 'bach/bwv227.11', 'bach/bwv244.40', 'bach/bwv244.44', 'bach/bwv424', 'bach/bwv244.25', 'bach/bwv80.8', 'bach/bwv244.54', 'bach/bwv78.7', 'bach/bwv57.8', 'bach/bwv194.6', 'bach/bwv397', 'bach/bwv64.8', 'bach/bwv318', 'bach/bwv315', 'bach/bwv153.5', 'bach/bwv39.7', 'bach/bwv108.6', 'bach/bwv386', 'bach/bwv25.6', 'bach/bwv417', 'bach/bwv415', 'bach/bwv302', 'bach/bwv380', 'bach/bwv74.8', 'bach/bwv422', 'bach/bwv133.6', 'bach/bwv270', 'bach/bwv272', 'bach/bwv38.6', 'bach/bwv271', 'bach/bwv183.5', 'bach/bwv103.6', 'bach/bwv287', 'bach/bwv32.6', 'bach/bwv245.26', 'bach/bwv248.5', 'bach/bwv411', 'bach/bwv369', 'bach/bwv339', 'bach/bwv361', 'bach/bwv399', 'bach/bwv16.6', 'bach/bwv419', 'bach/bwv87.7', 'bach/bwv4.8', 'bach/bwv358', 'bach/bwv154.8', 'bach/bwv278', 'bach/bwv156.6', 'bach/bwv248.33-3', 'bach/bwv81.7', 'bach/bwv227.7', 'bach/bwv427', 'bach/bwv77.6', 'bach/bwv410', 'bach/bwv329', 'bach/bwv85.6', 'bach/bwv385', 'bach/bwv309', 'bach/bwv305', 'bach/bwv18.5-l', 'bach/bwv18.5-w', 'bach/bwv197.5', 'bach/bwv30.6', 'bach/bwv296', 'bach/bwv292', 'bach/bwv353', 'bach/bwv301', 'bach/bwv347', 'bach/bwv284', 'bach/bwv429', 'bach/bwv436', 'bach/bwv430', 'bach/bwv381', 'bach/bwv36.4-2', 'bach/bwv412', 'bach/bwv65.7', 'bach/bwv280', 'bach/bwv169.7', 'bach/bwv428', 'bach/bwv346', 'bach/bwv248.12-2', 'bach/bwv426', 'bach/bwv159.5', 'bach/bwv121.6', 'bach/bwv418', 'bach/bwv28.6', 'bach/bwv326', 'bach/bwv327', 'bach/bwv321', 'bach/bwv65.2', 'bach/bwv144.6', 'bach/bwv194.12', 'bach/bwv398', 'bach/bwv317', 'bach/bwv153.9', 'bach/bwv300', 'bach/bwv56.5', 'bach/bwv423', 'bach/bwv306', 'bach/bwv40.6', 'bach/bwv123.6', 'bach/bwv245.28', 'bach/bwv279', 'bach/bwv378', 'bach/bwv366', 'bach/bwv45.7', 'bach/bwv295', 'bach/bwv245.14', 'bach/bwv122.6', 'bach/bwv355', 'bach/bwv357', 'bach/bwv94.8', 'bach/bwv348', 'bach/bwv349', 'bach/bwv312', 'bach/bwv325', 'bach/bwv245.37', 'bach/bwv37.6', 'bach/bwv283', 'bach/bwv299', 'bach/bwv294', 'bach/bwv245.15', 'bach/bwv176.6', 'bach/bwv391', 'bach/bwv350', 'bach/bwv400', 'bach/bwv372', 'bach/bwv402', 'bach/bwv282', 'bach/bwv374', 'bach/bwv60.5', 'bach/bwv356', 'bach/bwv389', 'bach/bwv40.8', 'bach/bwv174.5', 'bach/bwv340', 'bach/bwv433', 'bach/bwv322', 'bach/bwv403', 'bach/bwv267', 'bach/bwv261', 'bach/bwv245.40', 'bach/bwv33.6', 'bach/bwv269', 'bach/bwv266', 'bach/bwv43.11', 'bach/bwv10.7', 'bach/bwv343', 'bach/bwv311']
    currentNum = 1
    
    #BCI = corpus.chorales.Iterator(1, 371, returnType='filename') #highest number is 371
    #highestNum = BCI.highestNumber
    #currentNum = BCI.currentNumber
    for chorale in goodChorales: 
        
        print(currentNum)
        
        currentNum +=1
          
#         '''          
#         if chorale == 'bach/bwv277':
#             continue    #this chorale here has an added measure container randomly in the middle which breaks things.  
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
        
        print(cType, ": totalSuccesses =", str(totalSuccesses), "totalFailures =", str(totalFailures))

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

def _plotAgAndComp(piece):
    megaContour = {'tonality': [{1.0: 0.07841, 10.429: 0.0956, 90.571: 0.1635, 67.0: 0.2418, 62.286: 0.10518, 29.286: 0.14037, 57.571: 0.11613, 34.0: 0.14037, 81.143: 0.06714, 15.143: 0.13556, 71.714: 0.13613, 52.857: 0.16336, 38.714: 0.03082, 5.714: 0.0919, 48.143: 0.15973, 95.286: 0.10994, 24.571: 0.00873, 85.857: 0.13556, 43.429: 0.03783, 100.0: 0.14037, 19.857: 0.12143, 76.429: 0.05031}, {1.0: 0.23952, 16.231: 0.06082, 100.0: 0.14037, 31.462: 0.22008, 39.077: 0.10426, 46.692: 0.06576, 54.308: 0.30191, 77.154: 0.05614, 23.846: 0.17364, 61.923: 0.2822, 69.538: 0.06654, 84.769: 0.0592, 92.385: 0.04335, 8.615: 0.24568}, {50.5: 0.32289, 1.0: 0.07471, 60.4: 0.19201, 40.6: 0.11228, 80.2: 0.09335, 20.8: 0.05635, 70.3: 0.04559, 30.7: 0.16305, 10.9: 0.22975, 90.1: 0.15342, 100.0: 0.21646}, {50.5: 0.2594, 1.0: 0.06712, 60.4: 0.09926, 40.6: 0.11803, 80.2: 0.16883, 20.8: 0.10201, 70.3: 0.10751, 30.7: 0.11207, 10.9: 0.17913, 90.1: 0.1005, 100.0: 0.12884}, {25.75: 0.04122, 1.0: 0.14438, 100.0: 0.06354, 20.8: 0.14438, 40.6: 0.2283, 50.5: 0.17805, 85.15: 0.18354, 10.9: 0.12193, 70.3: 0.29475, 15.85: 0.07112, 55.45: 0.121, 60.4: 0.05409, 30.7: 0.12193, 35.65: 0.07112, 5.95: 0.04691, 95.05: 0.04101, 65.35: 0.38046, 45.55: 0.13164, 90.1: 0.11665, 80.2: 0.13398, 75.25: 0.32159}, {37.474: 0.18863, 1.0: 0.10981, 16.632: 0.17958, 100.0: 0.24052, 27.053: 0.08962, 68.737: 0.30933, 6.211: 0.10757, 79.158: 0.26402, 53.105: 0.04651, 32.263: 0.20989, 47.895: 0.25, 42.684: 0.30334, 84.368: 0.29418, 63.526: 0.07972, 73.947: 0.17775, 89.579: 0.30161, 21.842: 0.20588, 58.316: 0.07284, 94.789: 0.07561, 11.421: 0.09045}, {7.6: 0.24327, 1.0: 0.11168, 34.0: 0.24327, 67.0: 0.30224, 86.8: 0.11929, 93.4: 0.11487, 47.2: 0.09974, 40.6: 0.03516, 60.4: 0.28701, 20.8: 0.07864, 73.6: 0.16986, 27.4: 0.11168, 14.2: 0.03516, 53.8: 0.26912, 80.2: 0.10946, 100.0: 0.04746}, {9.25: 0.06827, 1.0: 0.20628, 34.0: 0.14984, 58.75: 0.14067, 75.25: 0.38256, 42.25: 0.06522, 83.5: 0.1708, 91.75: 0.20575, 67.0: 0.15937, 25.75: 0.1539, 100.0: 0.19784, 50.5: 0.14741, 17.5: 0.32868}, {7.6: 0.37553, 1.0: 0.14755, 34.0: 0.1133, 67.0: 0.15733, 86.8: 0.09563, 93.4: 0.18972, 47.2: 0.1806, 40.6: 0.2549, 60.4: 0.25698, 20.8: 0.2549, 73.6: 0.11114, 27.4: 0.19352, 14.2: 0.21201, 53.8: 0.28969, 80.2: 0.39895, 100.0: 0.2908}, {1.0: 0.11988, 10.429: 0.2549, 90.571: 0.11567, 67.0: 0.10036, 62.286: 0.15327, 29.286: 0.11988, 57.571: 0.03184, 34.0: 0.30465, 81.143: 0.23268, 15.143: 0.10672, 71.714: 0.06785, 52.857: 0.06234, 38.714: 0.2549, 5.714: 0.30834, 48.143: 0.06586, 95.286: 0.04086, 24.571: 0.04665, 85.857: 0.3024, 43.429: 0.10672, 100.0: 0.17007, 19.857: 0.06586, 76.429: 0.21192}, {5.5: 0.07808, 1.0: 0.10591, 77.5: 0.32581, 32.5: 0.07808, 95.5: 0.14113, 10.0: 0.30507, 19.0: 0.21575, 41.5: 0.0838, 28.0: 0.10591, 14.5: 0.09506, 37.0: 0.30507, 46.0: 0.21575, 55.0: 0.10901, 23.5: 0.31691, 64.0: 0.11049, 73.0: 0.23805, 82.0: 0.14554, 68.5: 0.1451, 91.0: 0.16948, 59.5: 0.12463, 50.5: 0.30481, 100.0: 0.2139, 86.5: 0.0923}, {9.25: 0.20185, 1.0: 0.1236, 34.0: 0.15217, 58.75: 0.32529, 75.25: 0.15839, 42.25: 0.12631, 83.5: 0.09431, 91.75: 0.10712, 67.0: 0.24971, 25.75: 0.17169, 100.0: 0.07332, 50.5: 0.07916, 17.5: 0.15115}, {13.375: 0.24056, 1.0: 0.09833, 38.125: 0.11299, 75.25: 0.22158, 100.0: 0.2125, 50.5: 0.3195, 87.625: 0.19869, 25.75: 0.16343, 62.875: 0.0763}, {9.25: 0.13539, 1.0: 0.1152, 34.0: 0.1483, 58.75: 0.04256, 75.25: 0.23175, 42.25: 0.1193, 83.5: 0.29477, 91.75: 0.06296, 67.0: 0.18672, 25.75: 0.10208, 100.0: 0.05991, 50.5: 0.09462, 17.5: 0.28052}, {9.25: 0.21719, 1.0: 0.20676, 34.0: 0.22941, 58.75: 0.27345, 75.25: 0.2698, 42.25: 0.20412, 83.5: 0.15796, 91.75: 0.15454, 67.0: 0.2534, 25.75: 0.19274, 100.0: 0.15036, 50.5: 0.26742, 17.5: 0.19634}, {7.6: 0.34389, 1.0: 0.07935, 34.0: 0.34389, 67.0: 0.0353, 86.8: 0.15135, 93.4: 0.07188, 47.2: 0.14067, 40.6: 0.05477, 60.4: 0.31691, 20.8: 0.14067, 73.6: 0.28331, 27.4: 0.07935, 14.2: 0.05477, 53.8: 0.06371, 80.2: 0.05741, 100.0: 0.2908}, {9.25: 0.11495, 1.0: 0.07402, 34.0: 0.12301, 58.75: 0.21255, 75.25: 0.06307, 42.25: 0.13085, 83.5: 0.24498, 91.75: 0.13495, 67.0: 0.24971, 25.75: 0.13009, 100.0: 0.14037, 50.5: 0.27848, 17.5: 0.19612}, {50.5: 0.05917, 1.0: 0.06378, 60.4: 0.06044, 40.6: 0.16727, 80.2: 0.10171, 20.8: 0.09891, 70.3: 0.37454, 30.7: 0.10407, 10.9: 0.03675, 90.1: 0.09885, 100.0: 0.08442}, {50.5: 0.25109, 1.0: 0.06093, 60.4: 0.24922, 40.6: 0.09576, 80.2: 0.07168, 20.8: 0.04946, 70.3: 0.08658, 30.7: 0.09576, 10.9: 0.12851, 90.1: 0.02126, 100.0: 0.1122}, {9.25: 0.22117, 1.0: 0.08099, 34.0: 0.15951, 58.75: 0.11752, 75.25: 0.03095, 42.25: 0.1018, 83.5: 0.17541, 91.75: 0.05221, 67.0: 0.05352, 25.75: 0.07332, 100.0: 0.07889, 50.5: 0.04907, 17.5: 0.12244}, {64.0: 0.19153, 1.0: 0.087, 100.0: 0.2908, 37.0: 0.17342, 73.0: 0.2864, 10.0: 0.08239, 46.0: 0.09222, 82.0: 0.13667, 19.0: 0.12845, 55.0: 0.19956, 91.0: 0.04429, 28.0: 0.23535}, {50.5: 0.185, 1.0: 0.23677, 60.4: 0.07152, 40.6: 0.16044, 80.2: 0.11226, 20.8: 0.09571, 70.3: 0.16669, 30.7: 0.0839, 10.9: 0.14699, 90.1: 0.03427, 100.0: 0.18052}, {9.25: 0.16169, 1.0: 0.11749, 34.0: 0.06874, 58.75: 0.11985, 75.25: 0.18901, 42.25: 0.06874, 83.5: 0.19689, 91.75: 0.10601, 67.0: 0.13556, 25.75: 0.06202, 100.0: 0.14037, 50.5: 0.24971, 17.5: 0.05345}, {1.0: 0.0849, 16.231: 0.19324, 100.0: 0.18542, 31.462: 0.07545, 39.077: 0.1504, 46.692: 0.2249, 54.308: 0.05592, 77.154: 0.22542, 23.846: 0.15737, 61.923: 0.15925, 69.538: 0.13127, 84.769: 0.20714, 92.385: 0.24438, 8.615: 0.02723}, {1.0: 0.04669, 16.231: 0.14046, 100.0: 0.0969, 31.462: 0.1239, 39.077: 0.10849, 46.692: 0.2639, 54.308: 0.33231, 77.154: 0.16333, 23.846: 0.04272, 61.923: 0.07114, 69.538: 0.26118, 84.769: 0.13281, 92.385: 0.18911, 8.615: 0.06588}, {64.0: 0.18843, 1.0: 0.10878, 100.0: 0.1866, 37.0: 0.07058, 73.0: 0.09171, 10.0: 0.06779, 46.0: 0.1703, 82.0: 0.16789, 19.0: 0.07943, 55.0: 0.07343, 91.0: 0.06552, 28.0: 0.22076}, {64.0: 0.26405, 1.0: 0.09113, 100.0: 0.19189, 37.0: 0.09071, 73.0: 0.11562, 10.0: 0.16967, 46.0: 0.07355, 82.0: 0.19102, 19.0: 0.23487, 55.0: 0.09373, 91.0: 0.06101, 28.0: 0.19102}, {50.5: 0.1266, 1.0: 0.12451, 43.429: 0.26374, 100.0: 0.21429, 64.643: 0.11203, 78.786: 0.11912, 29.286: 0.14067, 22.214: 0.13976, 92.929: 0.11618, 8.071: 0.28065, 36.357: 0.12809, 71.714: 0.22569, 85.857: 0.07921, 15.143: 0.17644, 57.571: 0.13841}, {1.0: 0.06874, 34.0: 0.14037, 67.0: 0.30839, 100.0: 0.14037, 12.0: 0.05807, 45.0: 0.09545, 78.0: 0.08088, 23.0: 0.10106, 56.0: 0.15185, 89.0: 0.09612}, {64.0: 0.14701, 1.0: 0.04637, 100.0: 0.05692, 37.0: 0.04637, 73.0: 0.11252, 10.0: 0.12435, 46.0: 0.16255, 82.0: 0.101, 19.0: 0.20721, 55.0: 0.20721, 91.0: 0.08225, 28.0: 0.07874}, {9.25: 0.12488, 1.0: 0.19568, 34.0: 0.13219, 58.75: 0.0565, 75.25: 0.05513, 42.25: 0.20321, 83.5: 0.18278, 91.75: 0.17573, 67.0: 0.09731, 25.75: 0.10157, 100.0: 0.18358, 50.5: 0.09879, 17.5: 0.07364}, {64.0: 0.15018, 1.0: 0.08369, 100.0: 0.21109, 37.0: 0.0806, 73.0: 0.19981, 10.0: 0.10534, 46.0: 0.13524, 82.0: 0.15215, 19.0: 0.22524, 55.0: 0.36615, 91.0: 0.07203, 28.0: 0.09068}, {1.0: 0.10609, 34.0: 0.20488, 67.0: 0.15315, 100.0: 0.22589, 12.0: 0.15453, 45.0: 0.22703, 78.0: 0.20432, 23.0: 0.05973, 56.0: 0.26567, 89.0: 0.12653}, {64.0: 0.14126, 1.0: 0.0991, 100.0: 0.2528, 37.0: 0.19129, 73.0: 0.09889, 10.0: 0.26222, 46.0: 0.10732, 82.0: 0.14736, 19.0: 0.29305, 55.0: 0.07416, 91.0: 0.15405, 28.0: 0.2498}, {64.0: 0.30322, 1.0: 0.06686, 100.0: 0.05692, 37.0: 0.08966, 73.0: 0.07435, 10.0: 0.052, 46.0: 0.22729, 82.0: 0.12878, 19.0: 0.11852, 55.0: 0.08333, 91.0: 0.04399, 28.0: 0.14706}, {50.5: 0.35721, 1.0: 0.09452, 43.429: 0.07736, 100.0: 0.14037, 64.643: 0.22094, 78.786: 0.10491, 29.286: 0.07932, 22.214: 0.07306, 92.929: 0.07467, 8.071: 0.2817, 36.357: 0.11113, 71.714: 0.13708, 85.857: 0.09767, 15.143: 0.08613, 57.571: 0.14291}, {7.6: 0.15036, 1.0: 0.08756, 34.0: 0.4363, 67.0: 0.32286, 86.8: 0.16667, 93.4: 0.13426, 47.2: 0.31691, 40.6: 0.41181, 60.4: 0.08314, 20.8: 0.31691, 73.6: 0.2549, 27.4: 0.13141, 14.2: 0.06199, 53.8: 0.11485, 80.2: 0.1938, 100.0: 0.2908}, {1.0: 0.11861, 34.0: 0.24762, 67.0: 0.09385, 100.0: 0.14037, 12.0: 0.05544, 45.0: 0.04764, 78.0: 0.0821, 23.0: 0.20525, 56.0: 0.04344, 89.0: 0.0615}, {50.5: 0.09925, 1.0: 0.08469, 60.4: 0.07655, 40.6: 0.02313, 80.2: 0.09884, 20.8: 0.15799, 70.3: 0.27302, 30.7: 0.05229, 10.9: 0.09159, 90.1: 0.08984, 100.0: 0.18389}, {7.6: 0.25759, 1.0: 0.25712, 34.0: 0.23238, 67.0: 0.20961, 86.8: 0.16636, 93.4: 0.10486, 47.2: 0.078, 40.6: 0.02824, 60.4: 0.26595, 20.8: 0.18804, 73.6: 0.22327, 27.4: 0.09603, 14.2: 0.2464, 53.8: 0.13431, 80.2: 0.16119, 100.0: 0.23706}, {37.474: 0.18782, 1.0: 0.1103, 16.632: 0.28102, 100.0: 0.11166, 27.053: 0.07051, 68.737: 0.23662, 6.211: 0.17831, 79.158: 0.39738, 53.105: 0.25673, 32.263: 0.07308, 47.895: 0.03419, 42.684: 0.18219, 84.368: 0.09766, 63.526: 0.13015, 73.947: 0.11882, 89.579: 0.24396, 21.842: 0.12743, 58.316: 0.15334, 94.789: 0.12429, 11.421: 0.08868}, {50.5: 0.20941, 1.0: 0.12368, 60.4: 0.15395, 40.6: 0.20611, 80.2: 0.18958, 20.8: 0.20174, 70.3: 0.32003, 30.7: 0.10499, 10.9: 0.10404, 90.1: 0.206, 100.0: 0.2908}, {9.25: 0.10963, 1.0: 0.13425, 34.0: 0.35516, 58.75: 0.3144, 75.25: 0.0425, 42.25: 0.13037, 83.5: 0.1907, 91.75: 0.12597, 67.0: 0.24655, 25.75: 0.25172, 100.0: 0.14037, 50.5: 0.24971, 17.5: 0.41872}, {7.6: 0.13312, 1.0: 0.08814, 34.0: 0.32964, 67.0: 0.08137, 86.8: 0.08485, 93.4: 0.08856, 47.2: 0.07237, 40.6: 0.04386, 60.4: 0.15517, 20.8: 0.07889, 73.6: 0.26221, 27.4: 0.09132, 14.2: 0.16816, 53.8: 0.14935, 80.2: 0.05039, 100.0: 0.0738}, {1.0: 0.11035, 34.0: 0.06415, 67.0: 0.11287, 100.0: 0.1354, 12.0: 0.12256, 45.0: 0.11921, 78.0: 0.17857, 23.0: 0.17703, 56.0: 0.11727, 89.0: 0.11779}, {64.0: 0.38285, 1.0: 0.10033, 100.0: 0.05692, 37.0: 0.10144, 73.0: 0.0802, 10.0: 0.24301, 46.0: 0.22729, 82.0: 0.07895, 19.0: 0.09571, 55.0: 0.08333, 91.0: 0.01607, 28.0: 0.19775}, {50.5: 0.13548, 1.0: 0.06242, 60.4: 0.13011, 40.6: 0.06044, 80.2: 0.09916, 20.8: 0.10186, 70.3: 0.21718, 30.7: 0.05917, 10.9: 0.05367, 90.1: 0.03782, 100.0: 0.06674}, {50.5: 0.22604, 1.0: 0.19224, 43.429: 0.29653, 100.0: 0.30092, 64.643: 0.06506, 78.786: 0.10899, 29.286: 0.07974, 22.214: 0.07129, 92.929: 0.15959, 8.071: 0.2981, 36.357: 0.22174, 71.714: 0.13431, 85.857: 0.08605, 15.143: 0.10063, 57.571: 0.33224}, {9.25: 0.22117, 1.0: 0.08559, 34.0: 0.0765, 58.75: 0.11752, 75.25: 0.16762, 42.25: 0.27509, 83.5: 0.39966, 91.75: 0.11143, 67.0: 0.06649, 25.75: 0.06745, 100.0: 0.07889, 50.5: 0.03504, 17.5: 0.09859}, {13.375: 0.10141, 1.0: 0.06182, 38.125: 0.14731, 75.25: 0.08291, 100.0: 0.05145, 50.5: 0.09615, 87.625: 0.06995, 25.75: 0.13981, 62.875: 0.26549}, {1.0: 0.10453, 48.348: 0.1204, 91.391: 0.10999, 44.043: 0.31368, 5.304: 0.14208, 87.087: 0.09897, 13.913: 0.11873, 22.522: 0.12619, 82.783: 0.2447, 39.739: 0.24888, 31.13: 0.24713, 78.478: 0.04944, 74.174: 0.21693, 61.261: 0.04639, 35.435: 0.10298, 95.696: 0.03648, 65.565: 0.14475, 100.0: 0.06612, 9.609: 0.13556, 69.87: 0.12852, 56.957: 0.17573, 26.826: 0.16619, 18.217: 0.06242, 52.652: 0.09143}, {25.75: 0.09715, 1.0: 0.0953, 100.0: 0.14037, 20.8: 0.18397, 40.6: 0.07478, 50.5: 0.12081, 85.15: 0.30266, 10.9: 0.08015, 70.3: 0.1659, 15.85: 0.06492, 55.45: 0.14046, 60.4: 0.03457, 30.7: 0.20049, 35.65: 0.09852, 5.95: 0.25992, 95.05: 0.09861, 65.35: 0.22474, 45.55: 0.06093, 90.1: 0.16253, 80.2: 0.12398, 75.25: 0.14529}, {64.0: 0.34544, 1.0: 0.16237, 100.0: 0.2908, 37.0: 0.14609, 73.0: 0.30158, 10.0: 0.11628, 46.0: 0.13792, 82.0: 0.13275, 19.0: 0.23815, 55.0: 0.07803, 91.0: 0.04931, 28.0: 0.13288}, {9.25: 0.14493, 1.0: 0.07783, 34.0: 0.13447, 58.75: 0.24622, 75.25: 0.26725, 42.25: 0.24523, 83.5: 0.15796, 91.75: 0.31202, 67.0: 0.2534, 25.75: 0.13447, 100.0: 0.2549, 50.5: 0.24521, 17.5: 0.07913}, {50.5: 0.07745, 1.0: 0.07821, 60.4: 0.1166, 40.6: 0.11736, 80.2: 0.29429, 20.8: 0.12724, 70.3: 0.29347, 30.7: 0.08159, 10.9: 0.05119, 90.1: 0.32515, 100.0: 0.47611}, {1.0: 0.08682, 16.231: 0.19392, 100.0: 0.07302, 31.462: 0.14037, 39.077: 0.09639, 46.692: 0.44524, 54.308: 0.05311, 77.154: 0.17942, 23.846: 0.04651, 61.923: 0.10033, 69.538: 0.06094, 84.769: 0.32994, 92.385: 0.04289, 8.615: 0.13149}, {64.0: 0.22147, 1.0: 0.04954, 100.0: 0.14037, 37.0: 0.16671, 73.0: 0.1062, 10.0: 0.07194, 46.0: 0.17123, 82.0: 0.15243, 19.0: 0.16788, 55.0: 0.04346, 91.0: 0.03259, 28.0: 0.16499}, {50.5: 0.11214, 1.0: 0.1445, 60.4: 0.20231, 40.6: 0.17098, 80.2: 0.15509, 20.8: 0.19784, 70.3: 0.24884, 30.7: 0.13652, 10.9: 0.09609, 90.1: 0.08899, 100.0: 0.2908}, {1.0: 0.18954, 48.348: 0.31691, 91.391: 0.17555, 44.043: 0.16947, 5.304: 0.10414, 87.087: 0.09725, 13.913: 0.2549, 22.522: 0.16535, 82.783: 0.11796, 39.739: 0.27437, 31.13: 0.11796, 78.478: 0.08828, 74.174: 0.15889, 61.261: 0.15036, 35.435: 0.0586, 95.696: 0.40677, 65.565: 0.31691, 100.0: 0.31691, 9.609: 0.15909, 69.87: 0.21734, 56.957: 0.21484, 26.826: 0.06567, 18.217: 0.3342, 52.652: 0.12785}, {9.25: 0.18391, 1.0: 0.22454, 34.0: 0.21131, 58.75: 0.26676, 75.25: 0.22964, 42.25: 0.13806, 83.5: 0.20688, 91.75: 0.3463, 67.0: 0.2534, 25.75: 0.19525, 100.0: 0.2549, 50.5: 0.24093, 17.5: 0.04845}, {13.375: 0.31597, 1.0: 0.17429, 50.5: 0.0667, 75.25: 0.09574, 69.063: 0.26424, 25.75: 0.10345, 62.875: 0.22157, 7.188: 0.17494, 56.688: 0.17793, 31.938: 0.24078, 19.563: 0.12509, 93.813: 0.09795, 44.313: 0.25725, 81.438: 0.25695, 100.0: 0.31691, 87.625: 0.19062, 38.125: 0.19106}, {7.6: 0.15224, 1.0: 0.23663, 34.0: 0.36387, 67.0: 0.22901, 86.8: 0.30571, 93.4: 0.03034, 47.2: 0.30434, 40.6: 0.10215, 60.4: 0.09661, 20.8: 0.06659, 73.6: 0.2161, 27.4: 0.08496, 14.2: 0.09949, 53.8: 0.21228, 80.2: 0.22668, 100.0: 0.05499}, {1.0: 0.08276, 16.231: 0.14046, 100.0: 0.1108, 31.462: 0.21688, 39.077: 0.09915, 46.692: 0.1502, 54.308: 0.14413, 77.154: 0.33044, 23.846: 0.06215, 61.923: 0.15666, 69.538: 0.05376, 84.769: 0.25125, 92.385: 0.10623, 8.615: 0.03186}, {7.6: 0.39839, 1.0: 0.04024, 34.0: 0.08028, 67.0: 0.3047, 86.8: 0.14396, 93.4: 0.0537, 47.2: 0.2724, 40.6: 0.10217, 60.4: 0.35369, 20.8: 0.07552, 73.6: 0.16832, 27.4: 0.15478, 14.2: 0.14656, 53.8: 0.10874, 80.2: 0.10823, 100.0: 0.14037}, {50.5: 0.09658, 1.0: 0.13003, 43.429: 0.08953, 100.0: 0.05814, 64.643: 0.05234, 78.786: 0.1703, 29.286: 0.09175, 22.214: 0.08257, 92.929: 0.03721, 8.071: 0.08489, 36.357: 0.07889, 71.714: 0.06977, 85.857: 0.14966, 15.143: 0.151, 57.571: 0.09658}, {7.6: 0.2419, 1.0: 0.10873, 34.0: 0.14067, 67.0: 0.08605, 86.8: 0.19322, 93.4: 0.09416, 47.2: 0.08605, 40.6: 0.08903, 60.4: 0.08903, 20.8: 0.17652, 73.6: 0.18967, 27.4: 0.11836, 14.2: 0.33431, 53.8: 0.18967, 80.2: 0.19317, 100.0: 0.19513}, {7.6: 0.34389, 1.0: 0.07935, 34.0: 0.34389, 67.0: 0.0353, 86.8: 0.15135, 93.4: 0.07188, 47.2: 0.14067, 40.6: 0.05477, 60.4: 0.31691, 20.8: 0.14067, 73.6: 0.28331, 27.4: 0.07935, 14.2: 0.05477, 53.8: 0.06371, 80.2: 0.05741, 100.0: 0.2908}, {9.25: 0.12637, 1.0: 0.08924, 34.0: 0.10648, 58.75: 0.09367, 75.25: 0.24971, 42.25: 0.02434, 83.5: 0.17672, 91.75: 0.09404, 67.0: 0.03495, 25.75: 0.06598, 100.0: 0.08953, 50.5: 0.37509, 17.5: 0.23506}, {64.0: 0.24951, 1.0: 0.14682, 100.0: 0.2908, 37.0: 0.1282, 73.0: 0.24624, 10.0: 0.07388, 46.0: 0.19899, 82.0: 0.04334, 19.0: 0.1787, 55.0: 0.10766, 91.0: 0.06172, 28.0: 0.1193}, {7.6: 0.12618, 1.0: 0.23259, 34.0: 0.2383, 67.0: 0.33724, 86.8: 0.34863, 93.4: 0.05894, 47.2: 0.2267, 40.6: 0.24982, 60.4: 0.23403, 20.8: 0.14037, 73.6: 0.2267, 27.4: 0.09619, 14.2: 0.13328, 53.8: 0.31846, 80.2: 0.08956, 100.0: 0.14037}, {1.0: 0.06213, 34.0: 0.1738, 67.0: 0.22239, 100.0: 0.15482, 12.0: 0.09801, 45.0: 0.09075, 78.0: 0.2594, 23.0: 0.12705, 56.0: 0.20569, 89.0: 0.2055}, {64.0: 0.2304, 1.0: 0.09793, 100.0: 0.07392, 37.0: 0.16586, 73.0: 0.13395, 10.0: 0.11518, 46.0: 0.28195, 82.0: 0.10663, 19.0: 0.01376, 55.0: 0.24654, 91.0: 0.02213, 28.0: 0.08047}, {9.25: 0.09663, 1.0: 0.0788, 34.0: 0.08067, 58.75: 0.23055, 75.25: 0.29634, 42.25: 0.14067, 83.5: 0.17649, 91.75: 0.15158, 67.0: 0.11998, 25.75: 0.14549, 100.0: 0.2908, 50.5: 0.08059, 17.5: 0.08392}, {50.5: 0.1718, 1.0: 0.08356, 43.429: 0.24355, 100.0: 0.14037, 64.643: 0.11323, 78.786: 0.32564, 29.286: 0.02016, 22.214: 0.08743, 92.929: 0.09869, 8.071: 0.08018, 36.357: 0.16941, 71.714: 0.06273, 85.857: 0.27417, 15.143: 0.12301, 57.571: 0.16335}, {9.25: 0.21153, 1.0: 0.20147, 34.0: 0.12663, 58.75: 0.05712, 75.25: 0.26233, 42.25: 0.14717, 83.5: 0.14296, 91.75: 0.06567, 67.0: 0.34364, 25.75: 0.13447, 100.0: 0.2908, 50.5: 0.34226, 17.5: 0.04576}, {1.0: 0.07755, 16.231: 0.10923, 100.0: 0.33451, 31.462: 0.26768, 39.077: 0.17621, 46.692: 0.16939, 54.308: 0.06323, 77.154: 0.3266, 23.846: 0.28582, 61.923: 0.14125, 69.538: 0.04433, 84.769: 0.11672, 92.385: 0.28507, 8.615: 0.12283}, {50.5: 0.16385, 1.0: 0.07721, 60.4: 0.17181, 40.6: 0.12301, 80.2: 0.37898, 20.8: 0.05371, 70.3: 0.04586, 30.7: 0.14037, 10.9: 0.33257, 90.1: 0.07385, 100.0: 0.14037}, {1.0: 0.08004, 10.429: 0.18515, 90.571: 0.31865, 67.0: 0.33885, 62.286: 0.3025, 29.286: 0.15973, 57.571: 0.44157, 34.0: 0.14037, 81.143: 0.2418, 15.143: 0.11996, 71.714: 0.20179, 52.857: 0.38262, 38.714: 0.18944, 5.714: 0.08938, 48.143: 0.46046, 95.286: 0.10612, 24.571: 0.24971, 85.857: 0.16832, 43.429: 0.37299, 100.0: 0.14037, 19.857: 0.2418, 76.429: 0.14037}, {64.0: 0.2015, 1.0: 0.10106, 100.0: 0.04394, 37.0: 0.05387, 73.0: 0.22676, 10.0: 0.10425, 46.0: 0.22729, 82.0: 0.0734, 19.0: 0.06634, 55.0: 0.08333, 91.0: 0.10715, 28.0: 0.18719}, {1.0: 0.0893, 34.0: 0.04884, 67.0: 0.02727, 100.0: 0.14329, 12.0: 0.22146, 45.0: 0.11921, 78.0: 0.16441, 23.0: 0.23692, 56.0: 0.11727, 89.0: 0.15431}, {50.5: 0.14975, 1.0: 0.17396, 60.4: 0.14675, 40.6: 0.17456, 80.2: 0.1933, 20.8: 0.20174, 70.3: 0.20084, 30.7: 0.10122, 10.9: 0.08466, 90.1: 0.11484, 100.0: 0.2908}, {7.6: 0.17169, 1.0: 0.09658, 34.0: 0.39724, 67.0: 0.18699, 86.8: 0.13406, 93.4: 0.09038, 47.2: 0.08963, 40.6: 0.06081, 60.4: 0.06883, 20.8: 0.06044, 73.6: 0.17922, 27.4: 0.05517, 14.2: 0.14026, 53.8: 0.11807, 80.2: 0.24914, 100.0: 0.08986}, {1.0: 0.09126, 10.429: 0.06567, 90.571: 0.15492, 67.0: 0.13674, 62.286: 0.06726, 29.286: 0.14964, 57.571: 0.0899, 34.0: 0.14037, 81.143: 0.28368, 15.143: 0.08428, 71.714: 0.09929, 52.857: 0.07232, 38.714: 0.25505, 5.714: 0.20178, 48.143: 0.05846, 95.286: 0.20443, 24.571: 0.09479, 85.857: 0.14326, 43.429: 0.1718, 100.0: 0.14037, 19.857: 0.09794, 76.429: 0.26872}, {9.25: 0.33231, 1.0: 0.11395, 34.0: 0.12301, 58.75: 0.09394, 75.25: 0.13007, 42.25: 0.19304, 83.5: 0.14921, 91.75: 0.08815, 67.0: 0.24971, 25.75: 0.14037, 100.0: 0.14037, 50.5: 0.23275, 17.5: 0.10316}, {64.0: 0.17092, 1.0: 0.05585, 100.0: 0.15735, 37.0: 0.11053, 73.0: 0.17949, 10.0: 0.09983, 46.0: 0.10979, 82.0: 0.10096, 19.0: 0.28813, 55.0: 0.24959, 91.0: 0.135, 28.0: 0.17051}, {50.5: 0.06782, 1.0: 0.10726, 60.4: 0.29685, 40.6: 0.11423, 80.2: 0.18291, 20.8: 0.15519, 70.3: 0.21089, 30.7: 0.13277, 10.9: 0.06665, 90.1: 0.14563, 100.0: 0.2908}, {1.0: 0.11035, 34.0: 0.11256, 67.0: 0.03992, 100.0: 0.1354, 12.0: 0.1451, 45.0: 0.07369, 78.0: 0.20925, 23.0: 0.28921, 56.0: 0.13985, 89.0: 0.1074}, {13.375: 0.25424, 1.0: 0.17429, 50.5: 0.08686, 75.25: 0.10065, 69.063: 0.18079, 25.75: 0.10345, 62.875: 0.162, 7.188: 0.17494, 56.688: 0.20568, 31.938: 0.2477, 19.563: 0.12509, 93.813: 0.12407, 44.313: 0.25725, 81.438: 0.2477, 100.0: 0.31691, 87.625: 0.21649, 38.125: 0.40998}, {9.25: 0.3218, 1.0: 0.20147, 34.0: 0.11415, 58.75: 0.05712, 75.25: 0.13638, 42.25: 0.14717, 83.5: 0.34161, 91.75: 0.04862, 67.0: 0.34927, 25.75: 0.12455, 100.0: 0.23872, 50.5: 0.34226, 17.5: 0.10067}, {9.25: 0.26627, 1.0: 0.25386, 34.0: 0.0668, 58.75: 0.19627, 75.25: 0.17383, 42.25: 0.17182, 83.5: 0.17606, 91.75: 0.09905, 67.0: 0.13863, 25.75: 0.08438, 100.0: 0.28934, 50.5: 0.22107, 17.5: 0.20323}, {64.0: 0.29013, 1.0: 0.10177, 100.0: 0.03097, 37.0: 0.01916, 73.0: 0.21974, 10.0: 0.11016, 46.0: 0.22729, 82.0: 0.18184, 19.0: 0.10827, 55.0: 0.07225, 91.0: 0.08944, 28.0: 0.17441}, {50.5: 0.07873, 1.0: 0.08604, 60.4: 0.062, 40.6: 0.15503, 80.2: 0.12582, 20.8: 0.10454, 70.3: 0.12012, 30.7: 0.15501, 10.9: 0.05711, 90.1: 0.16274, 100.0: 0.09871}, {35.941: 0.12068, 1.0: 0.1221, 82.529: 0.10899, 100.0: 0.30092, 12.647: 0.10063, 53.412: 0.29653, 76.706: 0.13431, 59.235: 0.22604, 70.882: 0.06506, 94.176: 0.15959, 18.471: 0.06754, 41.765: 0.06394, 88.353: 0.08605, 24.294: 0.08647, 65.059: 0.33224, 47.588: 0.22174, 30.118: 0.2937, 6.824: 0.2981}, {9.25: 0.19979, 1.0: 0.25386, 34.0: 0.09545, 58.75: 0.06466, 75.25: 0.21587, 42.25: 0.16137, 83.5: 0.2413, 91.75: 0.13487, 67.0: 0.06988, 25.75: 0.09041, 100.0: 0.16779, 50.5: 0.24995, 17.5: 0.06144}, {9.25: 0.10553, 1.0: 0.09657, 34.0: 0.04111, 58.75: 0.15451, 75.25: 0.0578, 42.25: 0.17398, 83.5: 0.14668, 91.75: 0.04783, 67.0: 0.2861, 25.75: 0.06783, 100.0: 0.08606, 50.5: 0.28195, 17.5: 0.06585}, {1.0: 0.08798, 16.231: 0.05476, 100.0: 0.21434, 31.462: 0.2109, 39.077: 0.18967, 46.692: 0.12028, 54.308: 0.24015, 77.154: 0.1716, 23.846: 0.14062, 61.923: 0.10961, 69.538: 0.15823, 84.769: 0.12691, 92.385: 0.06975, 8.615: 0.2657}, {9.25: 0.15057, 1.0: 0.10641, 34.0: 0.13447, 58.75: 0.0473, 75.25: 0.14081, 42.25: 0.06329, 83.5: 0.05435, 91.75: 0.11211, 67.0: 0.2097, 25.75: 0.13107, 100.0: 0.2908, 50.5: 0.31691, 17.5: 0.04931}, {50.5: 0.2458, 1.0: 0.0829, 60.4: 0.05723, 40.6: 0.1612, 80.2: 0.10754, 20.8: 0.16156, 70.3: 0.32118, 30.7: 0.09372, 10.9: 0.30538, 90.1: 0.03888, 100.0: 0.19819}, {50.5: 0.15742, 1.0: 0.10685, 60.4: 0.29425, 40.6: 0.08392, 80.2: 0.15356, 20.8: 0.03151, 70.3: 0.1486, 30.7: 0.06972, 10.9: 0.06815, 90.1: 0.08187, 100.0: 0.05392}, {1.0: 0.07755, 16.231: 0.10923, 100.0: 0.33451, 31.462: 0.26768, 39.077: 0.17621, 46.692: 0.16939, 54.308: 0.06323, 77.154: 0.3266, 23.846: 0.28582, 61.923: 0.14125, 69.538: 0.04433, 84.769: 0.11672, 92.385: 0.28507, 8.615: 0.12283}, {13.375: 0.06107, 1.0: 0.02085, 38.125: 0.04577, 75.25: 0.25596, 100.0: 0.12124, 50.5: 0.12447, 87.625: 0.29226, 25.75: 0.14296, 62.875: 0.149}, {64.0: 0.0462, 1.0: 0.07635, 100.0: 0.09551, 37.0: 0.13941, 73.0: 0.11243, 10.0: 0.06762, 46.0: 0.23759, 82.0: 0.19265, 19.0: 0.04787, 55.0: 0.21568, 91.0: 0.04626, 28.0: 0.19265}, {9.25: 0.29754, 1.0: 0.09007, 34.0: 0.24602, 58.75: 0.23542, 75.25: 0.23768, 42.25: 0.32665, 83.5: 0.13262, 91.75: 0.10538, 67.0: 0.46573, 25.75: 0.22425, 100.0: 0.2908, 50.5: 0.24311, 17.5: 0.18822}, {1.0: 0.07781, 34.0: 0.12953, 67.0: 0.16058, 100.0: 0.14037, 12.0: 0.10198, 45.0: 0.14037, 78.0: 0.18163, 23.0: 0.20151, 56.0: 0.09012, 89.0: 0.08796}, {1.0: 0.1903, 16.231: 0.19128, 100.0: 0.20793, 31.462: 0.14067, 39.077: 0.09907, 46.692: 0.20016, 54.308: 0.08397, 77.154: 0.19693, 23.846: 0.09366, 61.923: 0.16654, 69.538: 0.16897, 84.769: 0.19322, 92.385: 0.03182, 8.615: 0.37928}, {7.6: 0.12107, 1.0: 0.08473, 34.0: 0.28888, 67.0: 0.04637, 86.8: 0.1023, 93.4: 0.04893, 47.2: 0.26251, 40.6: 0.11919, 60.4: 0.32552, 20.8: 0.07047, 73.6: 0.06484, 27.4: 0.05691, 14.2: 0.05711, 53.8: 0.04669, 80.2: 0.06827, 100.0: 0.06484}, {25.75: 0.15319, 1.0: 0.07819, 100.0: 0.09725, 20.8: 0.11352, 40.6: 0.05396, 50.5: 0.292, 85.15: 0.02442, 10.9: 0.0737, 70.3: 0.07474, 15.85: 0.20806, 55.45: 0.39066, 60.4: 0.2624, 30.7: 0.08658, 35.65: 0.14037, 5.95: 0.14037, 95.05: 0.03907, 65.35: 0.29552, 45.55: 0.17251, 90.1: 0.1315, 80.2: 0.18642, 75.25: 0.06955}, {9.25: 0.07284, 1.0: 0.07198, 34.0: 0.06956, 58.75: 0.2183, 75.25: 0.33828, 42.25: 0.14067, 83.5: 0.35446, 91.75: 0.12131, 67.0: 0.15476, 25.75: 0.26179, 100.0: 0.2908, 50.5: 0.05589, 17.5: 0.08434}, {9.25: 0.18448, 1.0: 0.09366, 34.0: 0.1835, 58.75: 0.09631, 75.25: 0.2709, 42.25: 0.11797, 83.5: 0.14293, 91.75: 0.00887, 67.0: 0.29791, 25.75: 0.19532, 100.0: 0.06132, 50.5: 0.16659, 17.5: 0.27745}, {64.0: 0.26527, 1.0: 0.09334, 100.0: 0.14037, 37.0: 0.10643, 73.0: 0.14975, 10.0: 0.08099, 46.0: 0.33425, 82.0: 0.43144, 19.0: 0.19995, 55.0: 0.06599, 91.0: 0.07232, 28.0: 0.24762}, {7.6: 0.23759, 1.0: 0.08616, 34.0: 0.28286, 67.0: 0.09351, 86.8: 0.14637, 93.4: 0.09342, 47.2: 0.29512, 40.6: 0.20115, 60.4: 0.32028, 20.8: 0.178, 73.6: 0.11691, 27.4: 0.10131, 14.2: 0.11522, 53.8: 0.07319, 80.2: 0.12499, 100.0: 0.20361}, {9.25: 0.23258, 1.0: 0.08046, 34.0: 0.06222, 58.75: 0.42472, 75.25: 0.36111, 42.25: 0.13485, 83.5: 0.05126, 91.75: 0.09197, 67.0: 0.08037, 25.75: 0.08603, 100.0: 0.07889, 50.5: 0.30047, 17.5: 0.36373}, {1.0: 0.10008, 34.0: 0.1738, 67.0: 0.12726, 100.0: 0.14484, 12.0: 0.11508, 45.0: 0.09009, 78.0: 0.17274, 23.0: 0.17525, 56.0: 0.24522, 89.0: 0.1017}, {1.0: 0.07943, 34.0: 0.15913, 67.0: 0.03992, 100.0: 0.2261, 12.0: 0.11544, 45.0: 0.11921, 78.0: 0.08879, 23.0: 0.11934, 56.0: 0.11727, 89.0: 0.0485}, {1.0: 0.02897, 16.231: 0.19072, 100.0: 0.14037, 31.462: 0.06381, 39.077: 0.2267, 46.692: 0.0516, 54.308: 0.11581, 77.154: 0.14328, 23.846: 0.16832, 61.923: 0.14074, 69.538: 0.15973, 84.769: 0.09904, 92.385: 0.07508, 8.615: 0.08924}, {1.0: 0.1108, 34.0: 0.04336, 67.0: 0.20443, 100.0: 0.14037, 12.0: 0.15254, 45.0: 0.14037, 78.0: 0.15344, 23.0: 0.14257, 56.0: 0.15039, 89.0: 0.04709}, {13.375: 0.14995, 1.0: 0.06488, 38.125: 0.09758, 75.25: 0.35437, 100.0: 0.14067, 50.5: 0.26738, 87.625: 0.11911, 25.75: 0.28255, 62.875: 0.21834}, {9.25: 0.05254, 1.0: 0.07326, 34.0: 0.12632, 58.75: 0.05054, 75.25: 0.1227, 42.25: 0.09188, 83.5: 0.22912, 91.75: 0.04595, 67.0: 0.06527, 25.75: 0.25479, 100.0: 0.05492, 50.5: 0.08058, 17.5: 0.23379}, {64.0: 0.38406, 1.0: 0.11878, 100.0: 0.17203, 37.0: 0.17293, 73.0: 0.06316, 10.0: 0.1429, 46.0: 0.1782, 82.0: 0.15453, 19.0: 0.05481, 55.0: 0.20148, 91.0: 0.10575, 28.0: 0.16756}, {1.0: 0.10983, 48.348: 0.24845, 91.391: 0.08353, 44.043: 0.06119, 5.304: 0.19403, 87.087: 0.31581, 13.913: 0.24845, 22.522: 0.14763, 82.783: 0.38493, 39.739: 0.29713, 31.13: 0.2549, 78.478: 0.27466, 74.174: 0.31016, 61.261: 0.19174, 35.435: 0.15701, 95.696: 0.19174, 65.565: 0.14067, 100.0: 0.2908, 9.609: 0.08523, 69.87: 0.12697, 56.957: 0.0902, 26.826: 0.29843, 18.217: 0.34958, 52.652: 0.14089}, {13.375: 0.17351, 1.0: 0.14165, 50.5: 0.0831, 75.25: 0.07033, 69.063: 0.14165, 25.75: 0.12325, 62.875: 0.24035, 7.188: 0.07033, 56.688: 0.12688, 31.938: 0.09562, 19.563: 0.11614, 93.813: 0.2513, 44.313: 0.03879, 81.438: 0.26382, 100.0: 0.14599, 87.625: 0.12886, 38.125: 0.1414}, {1.0: 0.05974, 34.0: 0.14037, 67.0: 0.05322, 100.0: 0.14037, 12.0: 0.08924, 45.0: 0.05091, 78.0: 0.13041, 23.0: 0.03417, 56.0: 0.1446, 89.0: 0.06241}, {1.0: 0.3161, 34.0: 0.0804, 67.0: 0.1468, 100.0: 0.16367, 12.0: 0.33401, 45.0: 0.06715, 78.0: 0.219, 23.0: 0.06373, 56.0: 0.12311, 89.0: 0.105}, {7.6: 0.04742, 1.0: 0.04915, 34.0: 0.11491, 67.0: 0.23227, 86.8: 0.14127, 93.4: 0.24697, 47.2: 0.2549, 40.6: 0.19046, 60.4: 0.18141, 20.8: 0.31691, 73.6: 0.2549, 27.4: 0.0852, 14.2: 0.05021, 53.8: 0.30131, 80.2: 0.22889, 100.0: 0.2908}, {64.0: 0.08829, 1.0: 0.01822, 100.0: 0.5016, 37.0: 0.18842, 73.0: 0.1601, 10.0: 0.06501, 46.0: 0.21712, 82.0: 0.19548, 19.0: 0.08615, 55.0: 0.21185, 91.0: 0.38606, 28.0: 0.0535}, {1.0: 0.09509, 34.0: 0.09666, 67.0: 0.22477, 100.0: 0.20118, 12.0: 0.10271, 45.0: 0.17389, 78.0: 0.08378, 23.0: 0.19373, 56.0: 0.12329, 89.0: 0.13299}, {7.6: 0.20575, 1.0: 0.17661, 34.0: 0.05301, 67.0: 0.36445, 86.8: 0.23948, 93.4: 0.03657, 47.2: 0.15973, 40.6: 0.0258, 60.4: 0.08906, 20.8: 0.18182, 73.6: 0.20179, 27.4: 0.23432, 14.2: 0.05537, 53.8: 0.12811, 80.2: 0.11316, 100.0: 0.14037}, {64.0: 0.07975, 1.0: 0.07751, 100.0: 0.14037, 37.0: 0.09066, 73.0: 0.28652, 10.0: 0.09841, 46.0: 0.17293, 82.0: 0.11226, 19.0: 0.18116, 55.0: 0.10704, 91.0: 0.01376, 28.0: 0.07632}, {1.0: 0.06525, 16.231: 0.12401, 100.0: 0.14877, 31.462: 0.12966, 39.077: 0.14067, 46.692: 0.14067, 54.308: 0.07558, 77.154: 0.11137, 23.846: 0.12684, 61.923: 0.10575, 69.538: 0.09356, 84.769: 0.2367, 92.385: 0.17407, 8.615: 0.08269}, {7.6: 0.13292, 1.0: 0.03899, 34.0: 0.32103, 67.0: 0.0604, 86.8: 0.24713, 93.4: 0.32141, 47.2: 0.30259, 40.6: 0.23245, 60.4: 0.24971, 20.8: 0.07337, 73.6: 0.13292, 27.4: 0.19277, 14.2: 0.06797, 53.8: 0.29043, 80.2: 0.05506, 100.0: 0.33231}, {13.375: 0.11537, 1.0: 0.18272, 38.125: 0.0739, 75.25: 0.16282, 100.0: 0.2908, 50.5: 0.22894, 87.625: 0.06678, 25.75: 0.24102, 62.875: 0.24078}, {7.6: 0.15525, 1.0: 0.0617, 34.0: 0.32914, 67.0: 0.17828, 86.8: 0.33565, 93.4: 0.07035, 47.2: 0.16058, 40.6: 0.19179, 60.4: 0.0667, 20.8: 0.0629, 73.6: 0.2343, 27.4: 0.19154, 14.2: 0.02809, 53.8: 0.10247, 80.2: 0.03995, 100.0: 0.06636}, {64.0: 0.14721, 1.0: 0.10492, 100.0: 0.18194, 37.0: 0.27194, 73.0: 0.32443, 10.0: 0.05373, 46.0: 0.18967, 82.0: 0.13089, 19.0: 0.22158, 55.0: 0.06764, 91.0: 0.20278, 28.0: 0.21245}, {1.0: 0.09047, 16.231: 0.06985, 100.0: 0.2908, 31.462: 0.21137, 39.077: 0.14715, 46.692: 0.3674, 54.308: 0.28712, 77.154: 0.1975, 23.846: 0.27087, 61.923: 0.26686, 69.538: 0.08499, 84.769: 0.13152, 92.385: 0.10596, 8.615: 0.08534}, {35.941: 0.24971, 1.0: 0.13129, 82.529: 0.25662, 100.0: 0.14037, 12.647: 0.06453, 53.412: 0.30794, 76.706: 0.27357, 59.235: 0.26633, 70.882: 0.25635, 94.176: 0.12793, 18.471: 0.18157, 41.765: 0.11214, 88.353: 0.16458, 24.294: 0.14037, 65.059: 0.35861, 47.588: 0.19112, 30.118: 0.15413, 6.824: 0.10422}, {50.5: 0.09752, 1.0: 0.07593, 60.4: 0.20076, 40.6: 0.09278, 80.2: 0.27744, 20.8: 0.25452, 70.3: 0.21548, 30.7: 0.08939, 10.9: 0.33553, 90.1: 0.06109, 100.0: 0.2908}, {7.6: 0.17314, 1.0: 0.18035, 34.0: 0.20262, 67.0: 0.16719, 86.8: 0.02948, 93.4: 0.11349, 47.2: 0.35031, 40.6: 0.21502, 60.4: 0.09382, 20.8: 0.18642, 73.6: 0.23641, 27.4: 0.18137, 14.2: 0.15308, 53.8: 0.09348, 80.2: 0.2151, 100.0: 0.14037}, {1.0: 0.1108, 34.0: 0.04336, 67.0: 0.20443, 100.0: 0.14037, 12.0: 0.15254, 45.0: 0.14037, 78.0: 0.15344, 23.0: 0.14257, 56.0: 0.15039, 89.0: 0.04709}, {7.6: 0.15036, 1.0: 0.08756, 34.0: 0.4363, 67.0: 0.32286, 86.8: 0.16667, 93.4: 0.13426, 47.2: 0.31691, 40.6: 0.41181, 60.4: 0.08314, 20.8: 0.31691, 73.6: 0.2549, 27.4: 0.13141, 14.2: 0.06199, 53.8: 0.11485, 80.2: 0.1938, 100.0: 0.2908}, {50.5: 0.15688, 1.0: 0.06885, 60.4: 0.08755, 40.6: 0.01953, 80.2: 0.10731, 20.8: 0.06165, 70.3: 0.10005, 30.7: 0.09539, 10.9: 0.12886, 90.1: 0.09137, 100.0: 0.31691}, {50.5: 0.07884, 1.0: 0.077, 60.4: 0.0957, 40.6: 0.12876, 80.2: 0.12802, 20.8: 0.10359, 70.3: 0.14367, 30.7: 0.08173, 10.9: 0.10017, 90.1: 0.15226, 100.0: 0.05145}, {9.25: 0.30142, 1.0: 0.39842, 34.0: 0.10839, 58.75: 0.17924, 75.25: 0.31114, 42.25: 0.08823, 83.5: 0.12906, 91.75: 0.10836, 67.0: 0.19913, 25.75: 0.08345, 100.0: 0.19505, 50.5: 0.07676, 17.5: 0.02394}, {50.5: 0.08465, 1.0: 0.08838, 60.4: 0.10451, 40.6: 0.13929, 80.2: 0.08143, 20.8: 0.1894, 70.3: 0.29008, 30.7: 0.08785, 10.9: 0.05559, 90.1: 0.04281, 100.0: 0.17007}, {7.6: 0.20233, 1.0: 0.154, 34.0: 0.32354, 67.0: 0.11859, 86.8: 0.05084, 93.4: 0.00873, 47.2: 0.3707, 40.6: 0.18282, 60.4: 0.16126, 20.8: 0.24971, 73.6: 0.20021, 27.4: 0.12941, 14.2: 0.18273, 53.8: 0.09289, 80.2: 0.10271, 100.0: 0.14037}, {64.0: 0.20421, 1.0: 0.08639, 100.0: 0.19106, 37.0: 0.19633, 73.0: 0.20626, 10.0: 0.13613, 46.0: 0.18651, 82.0: 0.10868, 19.0: 0.19851, 55.0: 0.17265, 91.0: 0.18663, 28.0: 0.09541}, {7.6: 0.12048, 1.0: 0.14037, 34.0: 0.39059, 67.0: 0.26046, 86.8: 0.28965, 93.4: 0.05743, 47.2: 0.24971, 40.6: 0.20738, 60.4: 0.09801, 20.8: 0.24971, 73.6: 0.14037, 27.4: 0.11585, 14.2: 0.22218, 53.8: 0.35962, 80.2: 0.08235, 100.0: 0.14037}, {9.25: 0.07284, 1.0: 0.10482, 34.0: 0.07284, 58.75: 0.25012, 75.25: 0.27518, 42.25: 0.12463, 83.5: 0.05859, 91.75: 0.12538, 67.0: 0.26847, 25.75: 0.10482, 100.0: 0.2908, 50.5: 0.138, 17.5: 0.12463}, {7.6: 0.40375, 1.0: 0.13488, 34.0: 0.1886, 67.0: 0.08223, 86.8: 0.135, 93.4: 0.18631, 47.2: 0.31691, 40.6: 0.16568, 60.4: 0.25333, 20.8: 0.30293, 73.6: 0.31691, 27.4: 0.29827, 14.2: 0.16199, 53.8: 0.11921, 80.2: 0.18714, 100.0: 0.2908}, {50.5: 0.09658, 1.0: 0.13003, 43.429: 0.08953, 100.0: 0.05814, 64.643: 0.05234, 78.786: 0.1703, 29.286: 0.09175, 22.214: 0.08257, 92.929: 0.03721, 8.071: 0.08489, 36.357: 0.07889, 71.714: 0.06977, 85.857: 0.14966, 15.143: 0.151, 57.571: 0.09658}, {64.0: 0.06302, 1.0: 0.09603, 100.0: 0.15786, 37.0: 0.11228, 73.0: 0.18423, 10.0: 0.11995, 46.0: 0.13906, 82.0: 0.15213, 19.0: 0.07683, 55.0: 0.04312, 91.0: 0.09476, 28.0: 0.15796}, {13.375: 0.07107, 1.0: 0.12305, 50.5: 0.23428, 75.25: 0.29406, 69.063: 0.1576, 25.75: 0.13491, 62.875: 0.09845, 7.188: 0.11605, 56.688: 0.30542, 31.938: 0.25477, 19.563: 0.12171, 93.813: 0.18874, 44.313: 0.25675, 81.438: 0.13644, 100.0: 0.18133, 87.625: 0.21603, 38.125: 0.31495}, {1.0: 0.35154, 10.429: 0.34015, 90.571: 0.09478, 67.0: 0.04013, 62.286: 0.17085, 29.286: 0.16638, 57.571: 0.33322, 34.0: 0.15611, 81.143: 0.31691, 15.143: 0.33725, 71.714: 0.03347, 52.857: 0.09447, 38.714: 0.13233, 5.714: 0.21113, 48.143: 0.13414, 95.286: 0.19021, 24.571: 0.18343, 85.857: 0.15706, 43.429: 0.26417, 100.0: 0.2908, 19.857: 0.10628, 76.429: 0.15228}, {50.5: 0.26418, 1.0: 0.20753, 43.429: 0.2628, 100.0: 0.3034, 64.643: 0.10139, 78.786: 0.19298, 29.286: 0.04544, 22.214: 0.11053, 92.929: 0.01701, 8.071: 0.26506, 36.357: 0.11768, 71.714: 0.16408, 85.857: 0.25776, 15.143: 0.11208, 57.571: 0.33054}, {6.5: 0.24649, 1.0: 0.24655, 34.0: 0.06757, 67.0: 0.32568, 100.0: 0.07126, 61.5: 0.16406, 28.5: 0.05492, 83.5: 0.20744, 94.5: 0.0375, 12.0: 0.09628, 45.0: 0.19797, 78.0: 0.10505, 23.0: 0.06939, 56.0: 0.11686, 89.0: 0.24211, 50.5: 0.23038, 39.5: 0.07382, 72.5: 0.06341, 17.5: 0.13996}, {25.75: 0.26134, 1.0: 0.18109, 100.0: 0.2908, 20.8: 0.32651, 40.6: 0.30569, 50.5: 0.31691, 85.15: 0.23295, 10.9: 0.10447, 70.3: 0.25293, 15.85: 0.20493, 55.45: 0.31562, 60.4: 0.09439, 30.7: 0.31054, 35.65: 0.07426, 5.95: 0.33416, 95.05: 0.18352, 65.35: 0.24845, 45.55: 0.13741, 90.1: 0.01649, 80.2: 0.23398, 75.25: 0.09029}, {1.0: 0.12811, 34.0: 0.09392, 67.0: 0.04754, 100.0: 0.1354, 12.0: 0.15477, 45.0: 0.14067, 78.0: 0.1975, 23.0: 0.18939, 56.0: 0.11727, 89.0: 0.11232}, {50.5: 0.25487, 1.0: 0.12583, 43.429: 0.19516, 100.0: 0.18736, 64.643: 0.19727, 78.786: 0.31197, 29.286: 0.06017, 22.214: 0.24797, 92.929: 0.10063, 8.071: 0.15091, 36.357: 0.28921, 71.714: 0.41194, 85.857: 0.07465, 15.143: 0.2549, 57.571: 0.40594}, {7.6: 0.16728, 1.0: 0.09253, 34.0: 0.31932, 67.0: 0.1749, 86.8: 0.17995, 93.4: 0.08271, 47.2: 0.25333, 40.6: 0.18765, 60.4: 0.28441, 20.8: 0.13012, 73.6: 0.25539, 27.4: 0.08723, 14.2: 0.31896, 53.8: 0.16563, 80.2: 0.11273, 100.0: 0.2908}, {1.0: 0.1268, 10.429: 0.0885, 90.571: 0.078, 67.0: 0.14067, 62.286: 0.12878, 29.286: 0.12245, 57.571: 0.25376, 34.0: 0.35194, 81.143: 0.06714, 15.143: 0.12655, 71.714: 0.25139, 52.857: 0.13115, 38.714: 0.25333, 5.714: 0.18539, 48.143: 0.21598, 95.286: 0.11681, 24.571: 0.20551, 85.857: 0.25376, 43.429: 0.14803, 100.0: 0.31691, 19.857: 0.1981, 76.429: 0.13084}, {13.375: 0.13434, 1.0: 0.10535, 50.5: 0.24713, 75.25: 0.36915, 69.063: 0.3038, 25.75: 0.06517, 62.875: 0.35984, 7.188: 0.36827, 56.688: 0.04587, 31.938: 0.04891, 19.563: 0.08953, 93.813: 0.10196, 44.313: 0.13556, 81.438: 0.22962, 100.0: 0.14037, 87.625: 0.09645, 38.125: 0.12565}, {7.6: 0.08592, 1.0: 0.07698, 34.0: 0.33974, 67.0: 0.31481, 86.8: 0.13734, 93.4: 0.22039, 47.2: 0.13175, 40.6: 0.5337, 60.4: 0.19881, 20.8: 0.0659, 73.6: 0.21341, 27.4: 0.23988, 14.2: 0.10286, 53.8: 0.19626, 80.2: 0.18086, 100.0: 0.03158}, {1.0: 0.10373, 16.231: 0.15277, 100.0: 0.14037, 31.462: 0.06819, 39.077: 0.15245, 46.692: 0.06805, 54.308: 0.09426, 77.154: 0.28184, 23.846: 0.17137, 61.923: 0.05463, 69.538: 0.18864, 84.769: 0.12907, 92.385: 0.11316, 8.615: 0.06765}, {50.5: 0.34743, 1.0: 0.09894, 60.4: 0.22697, 40.6: 0.14721, 80.2: 0.0451, 20.8: 0.20467, 70.3: 0.14577, 30.7: 0.12995, 10.9: 0.24764, 90.1: 0.06804, 100.0: 0.20361}, {37.474: 0.079, 1.0: 0.23186, 16.632: 0.27713, 100.0: 0.30171, 27.053: 0.17951, 68.737: 0.16906, 6.211: 0.41576, 79.158: 0.28102, 53.105: 0.07617, 32.263: 0.18119, 47.895: 0.24881, 42.684: 0.16851, 84.368: 0.1504, 63.526: 0.19337, 73.947: 0.18689, 89.579: 0.0827, 21.842: 0.16317, 58.316: 0.06709, 94.789: 0.18363, 11.421: 0.10959}, {7.6: 0.08585, 1.0: 0.14037, 34.0: 0.15746, 67.0: 0.11089, 86.8: 0.18146, 93.4: 0.22743, 47.2: 0.2736, 40.6: 0.268, 60.4: 0.29532, 20.8: 0.45947, 73.6: 0.24971, 27.4: 0.11486, 14.2: 0.31949, 53.8: 0.25308, 80.2: 0.08046, 100.0: 0.14037}, {6.5: 0.10808, 1.0: 0.06605, 34.0: 0.09058, 67.0: 0.21959, 100.0: 0.2908, 61.5: 0.15405, 28.5: 0.09315, 83.5: 0.1205, 94.5: 0.11364, 12.0: 0.15372, 45.0: 0.03639, 78.0: 0.12554, 23.0: 0.10808, 56.0: 0.18764, 89.0: 0.21363, 50.5: 0.09003, 39.5: 0.25469, 72.5: 0.18883, 17.5: 0.06605}, {50.5: 0.24205, 1.0: 0.02998, 60.4: 0.08785, 40.6: 0.17579, 80.2: 0.08582, 20.8: 0.25219, 70.3: 0.12395, 30.7: 0.16148, 10.9: 0.11008, 90.1: 0.1797, 100.0: 0.2908}, {50.5: 0.3709, 1.0: 0.08533, 60.4: 0.06579, 40.6: 0.09831, 80.2: 0.1378, 20.8: 0.07397, 70.3: 0.08864, 30.7: 0.07355, 10.9: 0.13803, 90.1: 0.07389, 100.0: 0.19971}, {35.941: 0.24971, 1.0: 0.08852, 82.529: 0.23649, 100.0: 0.05991, 12.647: 0.41778, 53.412: 0.24971, 76.706: 0.25263, 59.235: 0.17123, 70.882: 0.1829, 94.176: 0.11253, 18.471: 0.27976, 41.765: 0.08766, 88.353: 0.15416, 24.294: 0.37509, 65.059: 0.15946, 47.588: 0.12976, 30.118: 0.18534, 6.824: 0.25503}, {50.5: 0.24493, 1.0: 0.17078, 43.429: 0.26027, 100.0: 0.14037, 64.643: 0.19491, 78.786: 0.24353, 29.286: 0.12851, 22.214: 0.09773, 92.929: 0.1071, 8.071: 0.0831, 36.357: 0.18973, 71.714: 0.25734, 85.857: 0.1441, 15.143: 0.12518, 57.571: 0.11051}, {50.5: 0.06258, 1.0: 0.06566, 60.4: 0.08852, 40.6: 0.05899, 80.2: 0.18387, 20.8: 0.25017, 70.3: 0.18489, 30.7: 0.14854, 10.9: 0.09258, 90.1: 0.17096, 100.0: 0.13118}, {50.5: 0.09943, 1.0: 0.25021, 60.4: 0.09917, 40.6: 0.15462, 80.2: 0.17036, 20.8: 0.07817, 70.3: 0.07954, 30.7: 0.05927, 10.9: 0.18544, 90.1: 0.09295, 100.0: 0.19978}, {6.5: 0.31691, 1.0: 0.08175, 34.0: 0.1987, 67.0: 0.08278, 100.0: 0.31691, 61.5: 0.07799, 28.5: 0.31016, 83.5: 0.12452, 94.5: 0.22769, 12.0: 0.25968, 45.0: 0.19474, 78.0: 0.11553, 23.0: 0.17669, 56.0: 0.10582, 89.0: 0.31691, 50.5: 0.0615, 39.5: 0.08425, 72.5: 0.14344, 17.5: 0.17939}, {35.941: 0.08072, 1.0: 0.04752, 82.529: 0.19291, 100.0: 0.1817, 12.647: 0.08162, 53.412: 0.11052, 76.706: 0.24689, 59.235: 0.08479, 70.882: 0.08401, 94.176: 0.06374, 18.471: 0.06099, 41.765: 0.06677, 88.353: 0.10355, 24.294: 0.07223, 65.059: 0.08723, 47.588: 0.13006, 30.118: 0.10243, 6.824: 0.05742}, {1.0: 0.18853, 34.0: 0.05786, 67.0: 0.04145, 100.0: 0.30633, 12.0: 0.06727, 45.0: 0.05498, 78.0: 0.19284, 23.0: 0.04614, 56.0: 0.11758, 89.0: 0.23836}, {1.0: 0.1219, 16.231: 0.26388, 100.0: 0.14037, 31.462: 0.32001, 39.077: 0.20136, 46.692: 0.08335, 54.308: 0.14037, 77.154: 0.07512, 23.846: 0.36198, 61.923: 0.16672, 69.538: 0.504, 84.769: 0.16832, 92.385: 0.04661, 8.615: 0.09612}, {50.5: 0.22719, 1.0: 0.10047, 60.4: 0.07284, 40.6: 0.0938, 80.2: 0.18534, 20.8: 0.2567, 70.3: 0.29917, 30.7: 0.17011, 10.9: 0.24183, 90.1: 0.20695, 100.0: 0.1923}, {64.0: 0.21159, 1.0: 0.09866, 100.0: 0.07337, 37.0: 0.15842, 73.0: 0.06783, 10.0: 0.11518, 46.0: 0.31785, 82.0: 0.10796, 19.0: 0.08004, 55.0: 0.24667, 91.0: 0.07387, 28.0: 0.07337}, {13.375: 0.11933, 1.0: 0.04611, 50.5: 0.05279, 75.25: 0.06802, 69.063: 0.12502, 25.75: 0.06942, 62.875: 0.14037, 7.188: 0.06806, 56.688: 0.06285, 31.938: 0.0344, 19.563: 0.21481, 93.813: 0.07856, 44.313: 0.2061, 81.438: 0.24498, 100.0: 0.05468, 87.625: 0.11766, 38.125: 0.15007}, {7.6: 0.12478, 1.0: 0.06297, 34.0: 0.23557, 67.0: 0.08924, 86.8: 0.1687, 93.4: 0.11417, 47.2: 0.24559, 40.6: 0.03076, 60.4: 0.29365, 20.8: 0.23476, 73.6: 0.33785, 27.4: 0.14528, 14.2: 0.10189, 53.8: 0.11915, 80.2: 0.17976, 100.0: 0.11142}, {1.0: 0.08973, 34.0: 0.14683, 67.0: 0.08388, 100.0: 0.2908, 12.0: 0.20342, 45.0: 0.19189, 78.0: 0.19901, 23.0: 0.26685, 56.0: 0.23661, 89.0: 0.08541}, {1.0: 0.07951, 16.231: 0.16819, 100.0: 0.05468, 31.462: 0.16818, 39.077: 0.10136, 46.692: 0.07216, 54.308: 0.07637, 77.154: 0.01908, 23.846: 0.1906, 61.923: 0.08603, 69.538: 0.20339, 84.769: 0.10125, 92.385: 0.16121, 8.615: 0.15436}, {50.5: 0.16243, 1.0: 0.06834, 60.4: 0.30329, 40.6: 0.25501, 80.2: 0.18734, 20.8: 0.17478, 70.3: 0.15376, 30.7: 0.07857, 10.9: 0.05406, 90.1: 0.12484, 100.0: 0.18389}, {37.474: 0.25548, 1.0: 0.10422, 16.632: 0.07613, 100.0: 0.2908, 27.053: 0.0317, 68.737: 0.06737, 6.211: 0.03489, 79.158: 0.31691, 53.105: 0.162, 32.263: 0.24854, 47.895: 0.14802, 42.684: 0.3315, 84.368: 0.29886, 63.526: 0.1076, 73.947: 0.2728, 89.579: 0.10897, 21.842: 0.23783, 58.316: 0.20784, 94.789: 0.20568, 11.421: 0.13922}, {7.6: 0.1867, 1.0: 0.07561, 34.0: 0.33444, 67.0: 0.0763, 86.8: 0.22036, 93.4: 0.10569, 47.2: 0.2704, 40.6: 0.20269, 60.4: 0.13095, 20.8: 0.06279, 73.6: 0.1001, 27.4: 0.07795, 14.2: 0.12043, 53.8: 0.12879, 80.2: 0.10668, 100.0: 0.19723}, {9.25: 0.09384, 1.0: 0.04541, 34.0: 0.23096, 58.75: 0.27814, 75.25: 0.08707, 42.25: 0.22567, 83.5: 0.18399, 91.75: 0.02154, 67.0: 0.35204, 25.75: 0.20274, 100.0: 0.05468, 50.5: 0.35007, 17.5: 0.15719}, {50.5: 0.12849, 1.0: 0.07607, 60.4: 0.28389, 40.6: 0.07817, 80.2: 0.20963, 20.8: 0.0886, 70.3: 0.03941, 30.7: 0.06199, 10.9: 0.25254, 90.1: 0.1497, 100.0: 0.06185}, {64.0: 0.11867, 1.0: 0.05971, 100.0: 0.04657, 37.0: 0.13703, 73.0: 0.14171, 10.0: 0.08706, 46.0: 0.14333, 82.0: 0.38615, 19.0: 0.10209, 55.0: 0.07529, 91.0: 0.15082, 28.0: 0.08924}, {50.5: 0.23801, 1.0: 0.09476, 60.4: 0.35601, 40.6: 0.34795, 80.2: 0.2228, 20.8: 0.15192, 70.3: 0.18111, 30.7: 0.19569, 10.9: 0.15255, 90.1: 0.07581, 100.0: 0.09273}, {1.0: 0.107, 16.231: 0.09128, 100.0: 0.18626, 31.462: 0.11727, 39.077: 0.08379, 46.692: 0.14067, 54.308: 0.31192, 77.154: 0.07803, 23.846: 0.09719, 61.923: 0.27089, 69.538: 0.16401, 84.769: 0.14067, 92.385: 0.03245, 8.615: 0.22201}, {9.25: 0.2176, 1.0: 0.08559, 34.0: 0.16646, 58.75: 0.11111, 75.25: 0.25085, 42.25: 0.37934, 83.5: 0.22401, 91.75: 0.05184, 67.0: 0.02615, 25.75: 0.09386, 100.0: 0.08988, 50.5: 0.03504, 17.5: 0.0546}, {9.25: 0.17427, 1.0: 0.07015, 34.0: 0.10685, 58.75: 0.10796, 75.25: 0.28812, 42.25: 0.06883, 83.5: 0.24868, 91.75: 0.02524, 67.0: 0.02367, 25.75: 0.08629, 100.0: 0.08612, 50.5: 0.02454, 17.5: 0.01903}, {7.6: 0.12618, 1.0: 0.23259, 34.0: 0.2383, 67.0: 0.33724, 86.8: 0.34863, 93.4: 0.05894, 47.2: 0.2267, 40.6: 0.24982, 60.4: 0.23403, 20.8: 0.14037, 73.6: 0.2267, 27.4: 0.09619, 14.2: 0.13328, 53.8: 0.31846, 80.2: 0.08956, 100.0: 0.14037}, {7.6: 0.10963, 1.0: 0.06105, 34.0: 0.2267, 67.0: 0.1028, 86.8: 0.08976, 93.4: 0.05743, 47.2: 0.11736, 40.6: 0.0521, 60.4: 0.1446, 20.8: 0.14037, 73.6: 0.17986, 27.4: 0.06005, 14.2: 0.17198, 53.8: 0.04412, 80.2: 0.13141, 100.0: 0.05641}, {50.5: 0.11774, 1.0: 0.03284, 60.4: 0.08867, 40.6: 0.04447, 80.2: 0.24775, 20.8: 0.08455, 70.3: 0.23086, 30.7: 0.06735, 10.9: 0.05649, 90.1: 0.10882, 100.0: 0.05991}, {7.6: 0.30142, 1.0: 0.38469, 34.0: 0.30142, 67.0: 0.06484, 86.8: 0.15234, 93.4: 0.18366, 47.2: 0.07834, 40.6: 0.0403, 60.4: 0.12927, 20.8: 0.05646, 73.6: 0.20911, 27.4: 0.38469, 14.2: 0.0403, 53.8: 0.14633, 80.2: 0.2796, 100.0: 0.2908}, {64.0: 0.02486, 1.0: 0.07734, 100.0: 0.31691, 37.0: 0.09022, 73.0: 0.09466, 10.0: 0.15657, 46.0: 0.37903, 82.0: 0.12064, 19.0: 0.24777, 55.0: 0.18923, 91.0: 0.13025, 28.0: 0.10708}, {9.25: 0.07284, 1.0: 0.06188, 34.0: 0.07987, 58.75: 0.18967, 75.25: 0.16406, 42.25: 0.14067, 83.5: 0.17429, 91.75: 0.12211, 67.0: 0.17365, 25.75: 0.13012, 100.0: 0.2819, 50.5: 0.13534, 17.5: 0.12619}, {9.25: 0.22108, 1.0: 0.05762, 34.0: 0.26065, 58.75: 0.07035, 75.25: 0.09173, 42.25: 0.40442, 83.5: 0.17607, 91.75: 0.0848, 67.0: 0.25612, 25.75: 0.07883, 100.0: 0.14037, 50.5: 0.17513, 17.5: 0.06238}, {7.6: 0.29022, 1.0: 0.25386, 34.0: 0.12809, 67.0: 0.28986, 86.8: 0.23858, 93.4: 0.15803, 47.2: 0.13663, 40.6: 0.21289, 60.4: 0.11994, 20.8: 0.13581, 73.6: 0.16768, 27.4: 0.14067, 14.2: 0.19786, 53.8: 0.34122, 80.2: 0.19861, 100.0: 0.30133}, {64.0: 0.18536, 1.0: 0.17554, 100.0: 0.2908, 37.0: 0.08639, 73.0: 0.12835, 10.0: 0.12472, 46.0: 0.22728, 82.0: 0.0977, 19.0: 0.20463, 55.0: 0.06533, 91.0: 0.04115, 28.0: 0.07754}, {64.0: 0.2558, 1.0: 0.06752, 100.0: 0.12468, 37.0: 0.05371, 73.0: 0.21577, 10.0: 0.07693, 46.0: 0.13774, 82.0: 0.22023, 19.0: 0.11466, 55.0: 0.16592, 91.0: 0.13602, 28.0: 0.13236}, {37.474: 0.22271, 1.0: 0.07664, 16.632: 0.06605, 100.0: 0.14037, 27.053: 0.11915, 68.737: 0.10395, 6.211: 0.08017, 79.158: 0.19401, 53.105: 0.19504, 32.263: 0.29961, 47.895: 0.05857, 42.684: 0.05796, 84.368: 0.10193, 63.526: 0.10555, 73.947: 0.19977, 89.579: 0.10126, 21.842: 0.07219, 58.316: 0.17864, 94.789: 0.06252, 11.421: 0.08267}, {1.0: 0.09999, 16.231: 0.13689, 100.0: 0.19805, 31.462: 0.31691, 39.077: 0.10905, 46.692: 0.1523, 54.308: 0.33687, 77.154: 0.09171, 23.846: 0.13931, 61.923: 0.10783, 69.538: 0.14702, 84.769: 0.16904, 92.385: 0.07851, 8.615: 0.13003}, {9.25: 0.06181, 1.0: 0.04818, 34.0: 0.08838, 58.75: 0.22094, 75.25: 0.07984, 42.25: 0.18967, 83.5: 0.24259, 91.75: 0.19525, 67.0: 0.24551, 25.75: 0.14053, 100.0: 0.08629, 50.5: 0.20647, 17.5: 0.15117}, {7.6: 0.22104, 1.0: 0.22517, 34.0: 0.22104, 67.0: 0.33197, 86.8: 0.05293, 93.4: 0.05711, 47.2: 0.14373, 40.6: 0.13845, 60.4: 0.0375, 20.8: 0.11938, 73.6: 0.3377, 27.4: 0.18459, 14.2: 0.13845, 53.8: 0.05769, 80.2: 0.07997, 100.0: 0.04394}, {9.25: 0.14905, 1.0: 0.05399, 34.0: 0.10013, 58.75: 0.05703, 75.25: 0.07929, 42.25: 0.20464, 83.5: 0.32768, 91.75: 0.11025, 67.0: 0.15306, 25.75: 0.06058, 100.0: 0.05664, 50.5: 0.10866, 17.5: 0.14456}, {9.25: 0.08157, 1.0: 0.1671, 34.0: 0.12018, 58.75: 0.14037, 75.25: 0.30989, 42.25: 0.15015, 83.5: 0.06595, 91.75: 0.21538, 67.0: 0.08686, 25.75: 0.13174, 100.0: 0.06222, 50.5: 0.12168, 17.5: 0.35716}, {64.0: 0.2015, 1.0: 0.04408, 100.0: 0.05381, 37.0: 0.04462, 73.0: 0.21779, 10.0: 0.08983, 46.0: 0.33376, 82.0: 0.13211, 19.0: 0.10479, 55.0: 0.10194, 91.0: 0.12107, 28.0: 0.20706}, {1.0: 0.1067, 34.0: 0.27196, 67.0: 0.13059, 100.0: 0.14037, 12.0: 0.08482, 45.0: 0.03134, 78.0: 0.10953, 23.0: 0.1989, 56.0: 0.05057, 89.0: 0.23595}, {37.474: 0.03714, 1.0: 0.04447, 16.632: 0.12076, 100.0: 0.31444, 27.053: 0.16893, 68.737: 0.10124, 6.211: 0.1528, 79.158: 0.08925, 53.105: 0.09827, 32.263: 0.15264, 47.895: 0.14916, 42.684: 0.20892, 84.368: 0.04736, 63.526: 0.234, 73.947: 0.09967, 89.579: 0.07155, 21.842: 0.06092, 58.316: 0.16026, 94.789: 0.08686, 11.421: 0.12087}, {50.5: 0.09658, 1.0: 0.0915, 43.429: 0.08953, 100.0: 0.09871, 64.643: 0.02241, 78.786: 0.16084, 29.286: 0.06226, 22.214: 0.10279, 92.929: 0.12554, 8.071: 0.07728, 36.357: 0.07889, 71.714: 0.05413, 85.857: 0.1866, 15.143: 0.07209, 57.571: 0.15029}, {1.0: 0.24294, 34.0: 0.16185, 67.0: 0.23623, 100.0: 0.14599, 12.0: 0.28461, 45.0: 0.14597, 78.0: 0.14853, 23.0: 0.16164, 56.0: 0.23272, 89.0: 0.25911}, {5.125: 0.07087, 1.0: 0.12395, 83.5: 0.06074, 58.75: 0.15416, 67.0: 0.10932, 9.25: 0.15398, 13.375: 0.09592, 34.0: 0.08518, 21.625: 0.39272, 42.25: 0.20344, 46.375: 0.31705, 50.5: 0.18647, 29.875: 0.08663, 17.5: 0.05922, 25.75: 0.17004, 71.125: 0.17636, 87.625: 0.30992, 79.375: 0.30569, 91.75: 0.08093, 95.875: 0.05809, 62.875: 0.09251, 38.125: 0.08092, 100.0: 0.14037, 54.625: 0.2439, 75.25: 0.21494}, {64.0: 0.18717, 1.0: 0.09054, 100.0: 0.17007, 37.0: 0.09252, 73.0: 0.07296, 10.0: 0.30765, 46.0: 0.12248, 82.0: 0.25027, 19.0: 0.06109, 55.0: 0.11203, 91.0: 0.08872, 28.0: 0.31691}, {9.25: 0.2176, 1.0: 0.08559, 34.0: 0.16646, 58.75: 0.11111, 75.25: 0.25085, 42.25: 0.37934, 83.5: 0.22401, 91.75: 0.05184, 67.0: 0.02615, 25.75: 0.09386, 100.0: 0.08988, 50.5: 0.03504, 17.5: 0.0546}, {9.25: 0.14576, 1.0: 0.06496, 34.0: 0.09046, 58.75: 0.20455, 75.25: 0.31638, 42.25: 0.26752, 83.5: 0.16086, 91.75: 0.10316, 67.0: 0.14976, 25.75: 0.16182, 100.0: 0.24532, 50.5: 0.03523, 17.5: 0.06245}, {64.0: 0.30591, 1.0: 0.07345, 100.0: 0.24415, 37.0: 0.08974, 73.0: 0.14268, 10.0: 0.08739, 46.0: 0.13122, 82.0: 0.13141, 19.0: 0.28055, 55.0: 0.22448, 91.0: 0.36981, 28.0: 0.22417}, {50.5: 0.1476, 1.0: 0.09046, 60.4: 0.07937, 40.6: 0.11567, 80.2: 0.15295, 20.8: 0.157, 70.3: 0.17887, 30.7: 0.10757, 10.9: 0.14969, 90.1: 0.06617, 100.0: 0.18358}, {9.25: 0.178, 1.0: 0.05551, 34.0: 0.13447, 58.75: 0.2327, 75.25: 0.24456, 42.25: 0.23942, 83.5: 0.09385, 91.75: 0.12501, 67.0: 0.2534, 25.75: 0.13447, 100.0: 0.13223, 50.5: 0.26133, 17.5: 0.07673}, {1.0: 0.0765, 34.0: 0.05533, 67.0: 0.27706, 100.0: 0.19798, 12.0: 0.12795, 45.0: 0.31691, 78.0: 0.21353, 23.0: 0.09012, 56.0: 0.12558, 89.0: 0.05684}, {1.0: 0.11394, 34.0: 0.051, 67.0: 0.17743, 100.0: 0.19221, 12.0: 0.27814, 45.0: 0.0968, 78.0: 0.15773, 23.0: 0.1657, 56.0: 0.1502, 89.0: 0.11418}, {64.0: 0.41612, 1.0: 0.07402, 100.0: 0.07539, 37.0: 0.10114, 73.0: 0.10571, 10.0: 0.06942, 46.0: 0.2267, 82.0: 0.21259, 19.0: 0.05231, 55.0: 0.11425, 91.0: 0.09623, 28.0: 0.13484}, {50.5: 0.17785, 1.0: 0.06393, 60.4: 0.08221, 40.6: 0.16648, 80.2: 0.3338, 20.8: 0.13361, 70.3: 0.09961, 30.7: 0.13122, 10.9: 0.28621, 90.1: 0.08853, 100.0: 0.13778}, {7.6: 0.36424, 1.0: 0.06982, 34.0: 0.08919, 67.0: 0.2397, 86.8: 0.17676, 93.4: 0.0774, 47.2: 0.27026, 40.6: 0.10725, 60.4: 0.33064, 20.8: 0.0757, 73.6: 0.18739, 27.4: 0.19439, 14.2: 0.13345, 53.8: 0.11731, 80.2: 0.12856, 100.0: 0.14037}, {64.0: 0.18582, 1.0: 0.11614, 100.0: 0.15391, 37.0: 0.13499, 73.0: 0.23499, 10.0: 0.06377, 46.0: 0.10979, 82.0: 0.07637, 19.0: 0.22731, 55.0: 0.28954, 91.0: 0.22559, 28.0: 0.15697}, {50.5: 0.17892, 1.0: 0.08328, 60.4: 0.0721, 40.6: 0.12127, 80.2: 0.1776, 20.8: 0.10685, 70.3: 0.08974, 30.7: 0.12127, 10.9: 0.03466, 90.1: 0.02676, 100.0: 0.14873}, {64.0: 0.31292, 1.0: 0.08327, 100.0: 0.2908, 37.0: 0.0617, 73.0: 0.16178, 10.0: 0.11271, 46.0: 0.06364, 82.0: 0.04598, 19.0: 0.17099, 55.0: 0.0924, 91.0: 0.09301, 28.0: 0.05925}, {9.25: 0.09014, 1.0: 0.08075, 34.0: 0.11854, 58.75: 0.1724, 75.25: 0.2049, 42.25: 0.10774, 83.5: 0.12807, 91.75: 0.06296, 67.0: 0.20118, 25.75: 0.19645, 100.0: 0.19505, 50.5: 0.16876, 17.5: 0.14331}, {9.25: 0.07637, 1.0: 0.08004, 34.0: 0.10601, 58.75: 0.10758, 75.25: 0.06336, 42.25: 0.14778, 83.5: 0.34815, 91.75: 0.0774, 67.0: 0.05894, 25.75: 0.18107, 100.0: 0.06032, 50.5: 0.32377, 17.5: 0.13189}, {1.0: 0.12452, 34.0: 0.18337, 67.0: 0.31987, 100.0: 0.11158, 12.0: 0.1124, 45.0: 0.0815, 78.0: 0.23564, 23.0: 0.14963, 56.0: 0.26332, 89.0: 0.09174}, {50.5: 0.17245, 1.0: 0.14352, 60.4: 0.04174, 40.6: 0.11567, 80.2: 0.17056, 20.8: 0.03238, 70.3: 0.10644, 30.7: 0.10757, 10.9: 0.10502, 90.1: 0.03715, 100.0: 0.16281}, {1.0: 0.35154, 10.429: 0.34015, 90.571: 0.09478, 67.0: 0.04013, 62.286: 0.17085, 29.286: 0.16638, 57.571: 0.33322, 34.0: 0.15611, 81.143: 0.31691, 15.143: 0.33725, 71.714: 0.03347, 52.857: 0.09447, 38.714: 0.13233, 5.714: 0.21113, 48.143: 0.13414, 95.286: 0.19021, 24.571: 0.18343, 85.857: 0.15706, 43.429: 0.26417, 100.0: 0.2908, 19.857: 0.10628, 76.429: 0.15228}, {50.5: 0.26712, 1.0: 0.07721, 60.4: 0.15391, 40.6: 0.11716, 80.2: 0.25313, 20.8: 0.05598, 70.3: 0.1284, 30.7: 0.14037, 10.9: 0.36742, 90.1: 0.07971, 100.0: 0.14037}, {64.0: 0.18967, 1.0: 0.17658, 100.0: 0.14443, 37.0: 0.09194, 73.0: 0.10662, 10.0: 0.30765, 46.0: 0.15184, 82.0: 0.31125, 19.0: 0.06109, 55.0: 0.02807, 91.0: 0.07824, 28.0: 0.31691}, {50.5: 0.09658, 1.0: 0.13003, 43.429: 0.08953, 100.0: 0.05814, 64.643: 0.05234, 78.786: 0.1703, 29.286: 0.09175, 22.214: 0.08257, 92.929: 0.03721, 8.071: 0.08489, 36.357: 0.07889, 71.714: 0.06977, 85.857: 0.14966, 15.143: 0.151, 57.571: 0.09658}, {6.5: 0.24649, 1.0: 0.24655, 34.0: 0.06757, 67.0: 0.32568, 100.0: 0.07126, 61.5: 0.16406, 28.5: 0.05492, 83.5: 0.20744, 94.5: 0.0375, 12.0: 0.09628, 45.0: 0.19797, 78.0: 0.10505, 23.0: 0.06939, 56.0: 0.11686, 89.0: 0.24211, 50.5: 0.23038, 39.5: 0.07382, 72.5: 0.06341, 17.5: 0.13996}, {13.375: 0.07107, 1.0: 0.12305, 50.5: 0.23428, 75.25: 0.29406, 69.063: 0.1576, 25.75: 0.13491, 62.875: 0.09845, 7.188: 0.11605, 56.688: 0.30542, 31.938: 0.25477, 19.563: 0.12171, 93.813: 0.18874, 44.313: 0.25675, 81.438: 0.13644, 100.0: 0.18133, 87.625: 0.21603, 38.125: 0.31495}, {13.375: 0.10505, 1.0: 0.16081, 38.125: 0.11815, 75.25: 0.09292, 100.0: 0.06219, 50.5: 0.13163, 87.625: 0.34765, 25.75: 0.27767, 62.875: 0.11396}, {9.25: 0.07604, 1.0: 0.07189, 34.0: 0.08679, 58.75: 0.17321, 75.25: 0.11477, 42.25: 0.07053, 83.5: 0.31996, 91.75: 0.07321, 67.0: 0.24971, 25.75: 0.09661, 100.0: 0.14037, 50.5: 0.06837, 17.5: 0.07321}, {7.6: 0.37785, 1.0: 0.06513, 34.0: 0.08924, 67.0: 0.32475, 86.8: 0.21803, 93.4: 0.12628, 47.2: 0.24379, 40.6: 0.08971, 60.4: 0.35369, 20.8: 0.09129, 73.6: 0.16832, 27.4: 0.13427, 14.2: 0.14018, 53.8: 0.11538, 80.2: 0.20144, 100.0: 0.14037}, {64.0: 0.40334, 1.0: 0.2082, 100.0: 0.22946, 37.0: 0.27636, 73.0: 0.12388, 10.0: 0.13959, 46.0: 0.09894, 82.0: 0.14224, 19.0: 0.20315, 55.0: 0.09961, 91.0: 0.06114, 28.0: 0.28979}, {9.25: 0.12591, 1.0: 0.10191, 34.0: 0.09679, 58.75: 0.16788, 75.25: 0.13229, 42.25: 0.10553, 83.5: 0.31012, 91.75: 0.05027, 67.0: 0.26263, 25.75: 0.04954, 100.0: 0.14037, 50.5: 0.13461, 17.5: 0.04426}, {6.5: 0.12342, 1.0: 0.08924, 34.0: 0.53008, 67.0: 0.21572, 100.0: 0.14037, 61.5: 0.25414, 28.5: 0.61306, 83.5: 0.15408, 94.5: 0.10995, 12.0: 0.08694, 45.0: 0.36972, 78.0: 0.28676, 23.0: 0.50329, 56.0: 0.24322, 89.0: 0.32264, 50.5: 0.24289, 39.5: 0.49497, 72.5: 0.06513, 17.5: 0.14037}, {9.25: 0.06736, 1.0: 0.17018, 34.0: 0.14037, 58.75: 0.45873, 75.25: 0.19391, 42.25: 0.14037, 83.5: 0.04179, 91.75: 0.1231, 67.0: 0.17091, 25.75: 0.09814, 100.0: 0.14037, 50.5: 0.23843, 17.5: 0.01868}, {9.25: 0.23258, 1.0: 0.08046, 34.0: 0.06222, 58.75: 0.42472, 75.25: 0.36111, 42.25: 0.13485, 83.5: 0.05126, 91.75: 0.09197, 67.0: 0.08037, 25.75: 0.08603, 100.0: 0.07889, 50.5: 0.30047, 17.5: 0.36373}, {13.375: 0.11933, 1.0: 0.04611, 50.5: 0.05279, 75.25: 0.06802, 69.063: 0.12502, 25.75: 0.06942, 62.875: 0.14037, 7.188: 0.06806, 56.688: 0.06285, 31.938: 0.0344, 19.563: 0.21481, 93.813: 0.07856, 44.313: 0.2061, 81.438: 0.24498, 100.0: 0.05468, 87.625: 0.11766, 38.125: 0.15007}, {50.5: 0.3024, 1.0: 0.12236, 60.4: 0.26311, 40.6: 0.33212, 80.2: 0.08363, 20.8: 0.08343, 70.3: 0.28931, 30.7: 0.24971, 10.9: 0.12113, 90.1: 0.27885, 100.0: 0.26564}, {50.5: 0.04014, 1.0: 0.11043, 60.4: 0.1009, 40.6: 0.02971, 80.2: 0.07771, 20.8: 0.16198, 70.3: 0.31362, 30.7: 0.11578, 10.9: 0.13886, 90.1: 0.09044, 100.0: 0.25291}, {50.5: 0.01868, 1.0: 0.05373, 43.429: 0.13069, 100.0: 0.14037, 64.643: 0.05274, 78.786: 0.13979, 29.286: 0.1523, 22.214: 0.04748, 92.929: 0.1005, 8.071: 0.05796, 36.357: 0.26772, 71.714: 0.22282, 85.857: 0.04408, 15.143: 0.08203, 57.571: 0.0713}, {9.25: 0.07284, 1.0: 0.06749, 34.0: 0.07302, 58.75: 0.19416, 75.25: 0.35573, 42.25: 0.14067, 83.5: 0.19114, 91.75: 0.11449, 67.0: 0.1953, 25.75: 0.12338, 100.0: 0.2908, 50.5: 0.06233, 17.5: 0.08233}, {64.0: 0.13123, 1.0: 0.14409, 100.0: 0.15622, 37.0: 0.23499, 73.0: 0.09457, 10.0: 0.31999, 46.0: 0.24084, 82.0: 0.22712, 19.0: 0.20485, 55.0: 0.23584, 91.0: 0.02315, 28.0: 0.27978}, {50.5: 0.15742, 1.0: 0.10685, 60.4: 0.29425, 40.6: 0.08392, 80.2: 0.15356, 20.8: 0.03151, 70.3: 0.1486, 30.7: 0.06972, 10.9: 0.06815, 90.1: 0.08187, 100.0: 0.05392}, {7.6: 0.22837, 1.0: 0.06184, 34.0: 0.17329, 67.0: 0.07106, 86.8: 0.31184, 93.4: 0.05059, 47.2: 0.23566, 40.6: 0.13698, 60.4: 0.24111, 20.8: 0.10523, 73.6: 0.29738, 27.4: 0.05928, 14.2: 0.16754, 53.8: 0.23764, 80.2: 0.15223, 100.0: 0.2908}, {50.5: 0.17892, 1.0: 0.08328, 60.4: 0.0721, 40.6: 0.12127, 80.2: 0.1776, 20.8: 0.10685, 70.3: 0.08974, 30.7: 0.12127, 10.9: 0.03466, 90.1: 0.02676, 100.0: 0.14873}, {7.6: 0.24279, 1.0: 0.19772, 34.0: 0.06955, 67.0: 0.3497, 86.8: 0.23249, 93.4: 0.11932, 47.2: 0.15973, 40.6: 0.04233, 60.4: 0.11347, 20.8: 0.18182, 73.6: 0.20179, 27.4: 0.26454, 14.2: 0.09437, 53.8: 0.15746, 80.2: 0.15444, 100.0: 0.14037}, {50.5: 0.21109, 1.0: 0.07478, 60.4: 0.09012, 40.6: 0.16079, 80.2: 0.14415, 20.8: 0.07628, 70.3: 0.1263, 30.7: 0.14674, 10.9: 0.14924, 90.1: 0.09844, 100.0: 0.09152}, {50.5: 0.27106, 1.0: 0.23677, 60.4: 0.12324, 40.6: 0.06388, 80.2: 0.20515, 20.8: 0.10899, 70.3: 0.15178, 30.7: 0.04354, 10.9: 0.16465, 90.1: 0.0509, 100.0: 0.07834}, {1.0: 0.11367, 34.0: 0.10536, 67.0: 0.06631, 100.0: 0.21496, 12.0: 0.3032, 45.0: 0.22916, 78.0: 0.16313, 23.0: 0.21302, 56.0: 0.25396, 89.0: 0.12733}, {9.25: 0.24891, 1.0: 0.0499, 34.0: 0.27485, 58.75: 0.33408, 75.25: 0.10708, 42.25: 0.18811, 83.5: 0.12188, 91.75: 0.0822, 67.0: 0.21418, 25.75: 0.20697, 100.0: 0.14067, 50.5: 0.23516, 17.5: 0.33844}, {13.375: 0.08761, 1.0: 0.0882, 50.5: 0.03399, 75.25: 0.11998, 69.063: 0.26284, 25.75: 0.20254, 62.875: 0.24743, 7.188: 0.24155, 56.688: 0.04905, 31.938: 0.24432, 19.563: 0.26111, 93.813: 0.03574, 44.313: 0.1444, 81.438: 0.08017, 100.0: 0.14037, 87.625: 0.03326, 38.125: 0.08526}, {1.0: 0.12767, 34.0: 0.24762, 67.0: 0.21876, 100.0: 0.14037, 12.0: 0.06199, 45.0: 0.04496, 78.0: 0.16982, 23.0: 0.24539, 56.0: 0.03292, 89.0: 0.14344}, {5.125: 0.08204, 1.0: 0.11393, 83.5: 0.15337, 58.75: 0.36915, 67.0: 0.26625, 9.25: 0.19896, 13.375: 0.16096, 34.0: 0.05414, 21.625: 0.05414, 42.25: 0.14037, 46.375: 0.16824, 50.5: 0.35394, 29.875: 0.14037, 17.5: 0.14657, 25.75: 0.18353, 71.125: 0.40501, 87.625: 0.13598, 79.375: 0.18252, 91.75: 0.2126, 95.875: 0.08334, 62.875: 0.42546, 38.125: 0.18353, 100.0: 0.14037, 54.625: 0.34426, 75.25: 0.41181}, {9.25: 0.178, 1.0: 0.10599, 34.0: 0.13447, 58.75: 0.28826, 75.25: 0.22418, 42.25: 0.14827, 83.5: 0.15489, 91.75: 0.10662, 67.0: 0.2534, 25.75: 0.12652, 100.0: 0.15036, 50.5: 0.20684, 17.5: 0.04519}, {50.5: 0.23248, 1.0: 0.07397, 43.429: 0.17068, 100.0: 0.19505, 64.643: 0.23026, 78.786: 0.19688, 29.286: 0.16714, 22.214: 0.28197, 92.929: 0.0369, 8.071: 0.20091, 36.357: 0.09305, 71.714: 0.17606, 85.857: 0.17123, 15.143: 0.1887, 57.571: 0.08832}, {9.25: 0.19979, 1.0: 0.25386, 34.0: 0.09545, 58.75: 0.06466, 75.25: 0.21587, 42.25: 0.16137, 83.5: 0.2413, 91.75: 0.13487, 67.0: 0.06988, 25.75: 0.09041, 100.0: 0.16779, 50.5: 0.24995, 17.5: 0.06144}, {64.0: 0.21961, 1.0: 0.11018, 100.0: 0.0617, 37.0: 0.13851, 73.0: 0.18892, 10.0: 0.11377, 46.0: 0.34738, 82.0: 0.14455, 19.0: 0.01715, 55.0: 0.20744, 91.0: 0.07798, 28.0: 0.0617}, {50.5: 0.06074, 1.0: 0.13056, 43.429: 0.115, 100.0: 0.14037, 64.643: 0.03348, 78.786: 0.18106, 29.286: 0.18655, 22.214: 0.10582, 92.929: 0.13182, 8.071: 0.06348, 36.357: 0.28268, 71.714: 0.10913, 85.857: 0.02071, 15.143: 0.09015, 57.571: 0.05376}, {13.375: 0.16315, 1.0: 0.09696, 50.5: 0.02727, 75.25: 0.0445, 69.063: 0.19019, 25.75: 0.23085, 62.875: 0.29282, 7.188: 0.21121, 56.688: 0.05938, 31.938: 0.19718, 19.563: 0.10055, 93.813: 0.05245, 44.313: 0.10672, 81.438: 0.0919, 100.0: 0.24845, 87.625: 0.18201, 38.125: 0.06894}, {64.0: 0.3895, 1.0: 0.12, 100.0: 0.05042, 37.0: 0.04924, 73.0: 0.11356, 10.0: 0.11016, 46.0: 0.22729, 82.0: 0.08159, 19.0: 0.07869, 55.0: 0.08333, 91.0: 0.11492, 28.0: 0.23564}, {9.25: 0.07284, 1.0: 0.06297, 34.0: 0.09157, 58.75: 0.1767, 75.25: 0.3043, 42.25: 0.14067, 83.5: 0.23, 91.75: 0.16123, 67.0: 0.12267, 25.75: 0.24036, 100.0: 0.2908, 50.5: 0.07653, 17.5: 0.05821}, {9.25: 0.08337, 1.0: 0.03864, 34.0: 0.35816, 58.75: 0.07259, 75.25: 0.15181, 42.25: 0.17372, 83.5: 0.26206, 91.75: 0.25083, 67.0: 0.38989, 25.75: 0.13538, 100.0: 0.24356, 50.5: 0.12066, 17.5: 0.09252}, {1.0: 0.12236, 10.429: 0.08343, 90.571: 0.28877, 67.0: 0.23519, 62.286: 0.2549, 29.286: 0.28773, 57.571: 0.23809, 34.0: 0.12807, 81.143: 0.05086, 15.143: 0.24971, 71.714: 0.25067, 52.857: 0.12154, 38.714: 0.14067, 5.714: 0.12113, 48.143: 0.2135, 95.286: 0.24162, 24.571: 0.28723, 85.857: 0.24434, 43.429: 0.12236, 100.0: 0.2908, 19.857: 0.2549, 76.429: 0.30108}, {25.75: 0.1198, 1.0: 0.21235, 100.0: 0.34888, 20.8: 0.18046, 40.6: 0.17231, 50.5: 0.11157, 85.15: 0.14773, 10.9: 0.2549, 70.3: 0.36029, 15.85: 0.07093, 55.45: 0.20076, 60.4: 0.21404, 30.7: 0.19137, 35.65: 0.20604, 5.95: 0.16838, 95.05: 0.1198, 65.35: 0.26464, 45.55: 0.08037, 90.1: 0.03182, 80.2: 0.23136, 75.25: 0.22901}, {50.5: 0.06447, 1.0: 0.09301, 60.4: 0.15368, 40.6: 0.05385, 80.2: 0.20561, 20.8: 0.14966, 70.3: 0.19379, 30.7: 0.1453, 10.9: 0.08485, 90.1: 0.05906, 100.0: 0.12603}, {7.6: 0.24327, 1.0: 0.11168, 34.0: 0.24327, 67.0: 0.30224, 86.8: 0.11929, 93.4: 0.11487, 47.2: 0.09974, 40.6: 0.03516, 60.4: 0.28701, 20.8: 0.07864, 73.6: 0.16986, 27.4: 0.11168, 14.2: 0.03516, 53.8: 0.26912, 80.2: 0.10946, 100.0: 0.04746}, {64.0: 0.38285, 1.0: 0.11783, 100.0: 0.05692, 37.0: 0.05717, 73.0: 0.0802, 10.0: 0.2421, 46.0: 0.33376, 82.0: 0.12094, 19.0: 0.09419, 55.0: 0.11787, 91.0: 0.05194, 28.0: 0.14002}, {9.25: 0.25197, 1.0: 0.09902, 34.0: 0.12338, 58.75: 0.16694, 75.25: 0.07602, 42.25: 0.20131, 83.5: 0.26791, 91.75: 0.06342, 67.0: 0.23155, 25.75: 0.13601, 100.0: 0.2908, 50.5: 0.24111, 17.5: 0.18665}, {64.0: 0.2304, 1.0: 0.09866, 100.0: 0.06222, 37.0: 0.15842, 73.0: 0.12308, 10.0: 0.11518, 46.0: 0.34106, 82.0: 0.13214, 19.0: 0.06613, 55.0: 0.25228, 91.0: 0.07302, 28.0: 0.06044}, {64.0: 0.17246, 1.0: 0.05614, 100.0: 0.04152, 37.0: 0.1148, 73.0: 0.18751, 10.0: 0.06942, 46.0: 0.23882, 82.0: 0.05417, 19.0: 0.08333, 55.0: 0.05066, 91.0: 0.04764, 28.0: 0.13806}, {9.25: 0.14493, 1.0: 0.20616, 34.0: 0.21131, 58.75: 0.25703, 75.25: 0.22487, 42.25: 0.21149, 83.5: 0.15796, 91.75: 0.17306, 67.0: 0.2534, 25.75: 0.19525, 100.0: 0.11918, 50.5: 0.24093, 17.5: 0.07913}, {64.0: 0.11964, 1.0: 0.07007, 100.0: 0.19505, 37.0: 0.07058, 73.0: 0.17951, 10.0: 0.07448, 46.0: 0.18202, 82.0: 0.20641, 19.0: 0.1188, 55.0: 0.05939, 91.0: 0.07851, 28.0: 0.26113}, {9.25: 0.14995, 1.0: 0.08242, 34.0: 0.11288, 58.75: 0.08531, 75.25: 0.16423, 42.25: 0.22901, 83.5: 0.14708, 91.75: 0.14173, 67.0: 0.09659, 25.75: 0.11038, 100.0: 0.2908, 50.5: 0.1689, 17.5: 0.09928}, {9.25: 0.23409, 1.0: 0.3209, 34.0: 0.13337, 58.75: 0.15902, 75.25: 0.35052, 42.25: 0.10389, 83.5: 0.218, 91.75: 0.04848, 67.0: 0.16709, 25.75: 0.10811, 100.0: 0.2908, 50.5: 0.16258, 17.5: 0.0281}]}
    compContour = ContourFinder(piece).getContour('tonality', normalized=True)
    AggregateContour(megaContour).plot('tonality', showPoints=False, comparisonContour=compContour)

    
#------------------------
class Test(unittest.TestCase):
    
    def runTest(self):
        pass
    
if __name__ == "__main__":
    import music21
    music21.mainTest(Test)

