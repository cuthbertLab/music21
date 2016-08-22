# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         discrete.py
# Purpose:      Framework for modular, windowed analysis
#
# Authors:      Jared Sadoian
#               Christopher Ariza
#
# Copyright:    Copyright © 2010-2011 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------

'''
Modular analysis procedures for use alone or 
applied with :class:`music21.analysis.windowed.WindowedAnalysis` class. 

All procedures should inherit from 
:class:`music21.analysis.discrete.DiscreteAnalysis`, 
or provide a similar interface. 

The :class:`music21.analysis.discrete.KrumhanslSchmuckler` 
(for algorithmic key detection) and 
:class:`music21.analysis.discrete.Ambitus` (for pitch range analysis) provide examples.
'''
#TODO: make an analysis.base for the Discrete and analyzeStream aspects, then create
# range and key modules in analysis

import unittest

from music21 import exceptions21

from music21 import pitch
from music21 import interval
from music21 import key



from music21 import environment
_MOD = 'discrete.py'
environLocal = environment.Environment(_MOD)



#------------------------------------------------------------------------------
class DiscreteAnalysisException(exceptions21.Music21Exception):
    pass

class DiscreteAnalysis(object):
    ''' Parent class for analytical methods.

    Each analytical method returns a discrete numerical (or other) results as well as a color. 
    Colors can be used in mapping output.

    Analytical methods may make use of a `referenceStream` to 
    configure the processor on initialization. 
    '''
    # define in subclass
    name = ''
    identifiers = []
    def __init__(self, referenceStream=None):
        # store a reference stream if needed
        self._referenceStream = referenceStream

        # store unique solutions encountered over a single run; this can be used
        # to configure the generation of a legend based only on the values 
        # that have been produced.
        # store pairs of sol, color
        self._solutionsFound = []

        # store alternative solutions, which may be sorted or not
        self._alternativeSolutions = []

    def _rgbToHex(self, rgb):
        '''Utility conversion method
        '''
        rgb = int(round(rgb[0])), int(round(rgb[1])), int(round(rgb[2]))
        return '#%02x%02x%02x' % rgb    

    def _hexToRgb(self, value):
        '''Utility conversion method    
        >>> da = analysis.discrete.DiscreteAnalysis()
        >>> da._hexToRgb('#ffffff')
        [255, 255, 255]
        >>> da._hexToRgb('#000000')
        [0, 0, 0]
        '''
        value = value.lstrip('#')
        lv = len(value)
        return list(int(value[i:i+lv//3], 16) for i in range(0, lv, lv//3))

    def _rgbLimit(self, value):
        '''Utility conversion method    
        >>> da = analysis.discrete.DiscreteAnalysis()
        >>> da._rgbLimit(300)
        255
        >>> da._rgbLimit(-30)
        0
        '''
        if value < 0:
            value = 0
        elif value > 255:
            value = 255
        return value


    def clearSolutionsFound(self):
        '''Clear all stored solutions 
        '''
        self._solutionsFound = []

    def getColorsUsed(self):
        '''
        Based on solutions found so far with with this processor, 
        return the colors that have been used.
        '''
        post = []
        for unused_solution, color in self._solutionsFound:
            if color not in post:
                post.append(color)
        return post    

    def getSolutionsUsed(self):
        '''
        Based on solutions found so far with with this processor, 
        return the solutions that have been used.
        '''
        post = []
        for solution, unused_color in self._solutionsFound:
            if solution not in post:
                post.append(solution)
        return post   

    def solutionLegend(self, compress=False):
        '''A list of pairs showing all discrete results and the assigned color.
        Data should be organized to be passed to 
        :class:`music21.graph.GraphColorGridLegend`.

        If `compress` is True, the legend will only show values for solutions
        that have been encountered. 
        '''
        pass


    def solutionUnitString(self):
        '''
        Return a string describing the solution values. Used in Legend formation. 
        '''
        return None
    
    def solutionToColor(self, result):
        '''
        Given a analysis specific result, return the appropriate color. 
        Must be able to handle None in the case that there is no result.
        '''
        pass
    
    def process(self, subStream):
        '''
        Given a Stream, apply the analysis to all components of this Stream. 
        Expected return is a solution (method specific) and a color value.
        '''
        pass


    def getSolution(self, subStream):
        '''
        For a given Stream, apply the analysis and return the best solution.
        '''
        pass


#------------------------------------------------------------------------------
# alternative names
# PitchClassKeyFinding
# KeySearchByProbeTone
# ProbeToneKeyFinding

class KeyWeightKeyAnalysis(DiscreteAnalysis):
    '''
    Base class for all key-weight key analysis subclasses.
    '''
    _DOC_ALL_INHERITED = False

    # these are specialized in subclass
    name = 'KeyWeightKeyAnalysis Base Class'
    identifiers = ['key.baseClass', 'keyscape.baseClass']

    # in general go to Gb, F#: favor F# majorKeyColors
    # favor eb minor
    # C- major cannot be determined if no enharmonics are present
    # C# major can be determined w/o enharmonics
    keysValidMajor = ['C', 'C#', 'C-',
                      'D-', 'D',
                      'E-', 'E',
                      'F', 'F#',
                      'G-', 'G',
                      'A-', 'A',
                      'B-', 'B',
                    ]

    keysValidMinor = ['C', 'C#',
                      'D', 'D#',
                      'E-', 'E',
                      'F', 'F#',
                      'G', 'G#',
                      'A-', 'A', 'A#',
                      'B-', 'B',
                    ]

    def __init__(self, referenceStream=None):
        DiscreteAnalysis.__init__(self, referenceStream=referenceStream)
        # store sharp/flat count on init if available
        if referenceStream is not None:
            self.sharpFlatCount = self._getSharpFlatCount(referenceStream)
        else:
            self.sharpFlatCount = None
        self._majorKeyColors = {}
        self._minorKeyColors = {}
        self._fillColorDictionaries()
    
    def _fillColorDictionaries(self):
        '''
        >>> p = analysis.discrete.KrumhanslSchmuckler()
        >>> len(p._majorKeyColors)
        15
        >>> p._majorKeyColors['C']
        '#ff816b'
        '''
        # for each step, assign a color
        # names taken from http://chaos2.org/misc/rgb.html    
        # idea is basically:
        # red, orange, yellow, green, cyan, blue, purple, pink
        stepLib = {'C': '#CD4F39', # tomato3
                'D': '#DAA520', # goldenrod
                'E': '#BCEE68', # DarkOliveGreen2
                'F': '#96CDCD', # PaleTurquoise3
                'G': '#6495ED', # cornflower blue
                'A': '#8968CD', # MediumPurple3
                'B': '#FF83FA', # orchid1
                } 

        for dst, valid in [(self._majorKeyColors, self.keysValidMajor), 
                           (self._minorKeyColors, self.keysValidMinor)]:
            for validKey in valid:
                # convert to pitch object
                validKey = pitch.Pitch(validKey)
                step = validKey.step # get C for C#
                rgbStep = self._hexToRgb(stepLib[step])
                # make all the colors a bit lighter
                for i in range(len(rgbStep)):
                    rgbStep[i] = self._rgbLimit(rgbStep[i] + 50)
        
                #make minor darker
                if valid == self.keysValidMinor:
                    for i in range(len(rgbStep)):
                        rgbStep[i] = self._rgbLimit(rgbStep[i] - 100)
        
                if len(validKey.name) > 1:
                    magnitude = 15
                    if validKey.name[1] == '-':
                        # index and value shift for each of rgb values
                        shiftLib = {0: magnitude, 1: magnitude, 2: -magnitude}                   
                    elif validKey.name[1] == '#':                   
                        shiftLib = {0: -magnitude, 1: -magnitude, 2: magnitude}                   
                    for i in shiftLib:
                        rgbStep[i] = self._rgbLimit(rgbStep[i] + shiftLib[i])
                # add to dictionary
                dst[validKey.name] = self._rgbToHex(rgbStep)


    def _getSharpFlatCount(self, subStream):
        '''
        Determine count of sharps and flats in a Stream
        
        >>> s = corpus.parse('bach/bwv66.6')
        >>> p = analysis.discrete.KrumhanslSchmuckler()
        >>> p._getSharpFlatCount(s.flat)
        (87, 0)
        '''
        # pitches gets a flat representation
        flatCount = 0
        sharpCount = 0
        for p in subStream.pitches:
            if p.accidental is not None:
                if p.accidental.alter < 0:
                    flatCount += -1
                elif p.accidental.alter > 0:
                    sharpCount += 1
        return sharpCount, flatCount

    def _getWeights(self, weightType='major'): 
        '''
        Returns the key weights. To provide different key weights, 
        subclass and override this method. The defaults here are KrumhanslSchmuckler.
            
        >>> a = analysis.discrete.KrumhanslSchmuckler()
        >>> len(a._getWeights('major'))
        12
        >>> len(a._getWeights('minor'))
        12            
        '''
        weightType = weightType.lower()
        if weightType == 'major':
            return [6.35, 2.33, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
        elif weightType == 'minor':
            return [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]    
        else:
            raise DiscreteAnalysisException('no weights defined for weight type: %s' % weightType)

    def _getPitchClassDistribution(self, streamObj):
        '''
        Given a flat Stream, obtain a pitch class distribution. 
        The value of each pitch class is scaled by its duration in quarter lengths.

        >>> a = analysis.discrete.KrumhanslSchmuckler()
        >>> s = stream.Stream()
        >>> n1 = note.Note('c')
        >>> n1.quarterLength = 3
        >>> n2 = note.Note('f#')
        >>> n2.quarterLength = 2
        >>> s.append(n1)
        >>> s.append(n2)
        >>> a._getPitchClassDistribution(s)
        [3.0, 0, 0, 0, 0, 0, 2.0, 0, 0, 0, 0, 0]
        >>> c1 = chord.Chord(['d', 'e', 'b-'])
        >>> c1.quarterLength = 1.5
        >>> s.append(c1)
        >>> a._getPitchClassDistribution(s)
        [3.0, 0, 1.5, 0, 1.5, 0, 2.0, 0, 0, 0, 1.5, 0]
        '''
        # storage for 12 pitch classes
        pcDist = [0]*12
        if len(streamObj.notes) == 0:
            return None

        for n in streamObj.notes:        
            length = n.quarterLength
            if n.isChord:
                for m in n.pitchClasses:
                    pcDist[m] = pcDist[m] + (1 * length)
            else:
                pcDist[n.pitch.pitchClass] = pcDist[n.pitch.pitchClass] + (1 * length)
        return pcDist


    def _convoluteDistribution(self, pcDistribution, weightType='major'):
        ''' Takes in a pitch class distribution as a list and convolutes it
            over Sapp's given distribution for finding key, returning the result. 
        '''
        # may get an empty distribution
        if pcDistribution is None:
            return None

        soln = [0] * 12
        toneWeights = self._getWeights(weightType)
        for i in range(len(soln)):
            for j in range(len(pcDistribution)):
                soln[i] = soln[i] + (toneWeights[(j - i) % 12] * pcDistribution[j])
        return soln  
    
    def _getLikelyKeys(self, keyResults, differences):
        ''' Takes in a list of probably key results in points and returns a
            list of keys in letters, sorted from most likely to least likely
        '''
        # case of empty data
        if keyResults is None:
            return None

        likelyKeys = [0] * 12
        a = sorted(keyResults)
        a.reverse()
        
        #Return pairs, the pitch class and the correlation value, in order by point value
        for i in range(len(a)):
            # pitch objects created here
            likelyKeys[i] = (pitch.Pitch(keyResults.index(a[i])),
                             differences[keyResults.index(a[i])])
            #environLocal.printDebug(['added likely key', likelyKeys[i]])
        return likelyKeys
        
        
    def _getDifference(self, keyResults, pcDistribution, weightType):
        ''' Takes in a list of numerical probable key results and returns the
            difference of the top two keys
        '''
        # case of empty analysis
        if keyResults is None:
            return None
 
        soln = [0] * 12
        top = [0] * 12
        bottomRight = [0] * 12
        bottomLeft = [0] * 12
            
        toneWeights = self._getWeights(weightType)
        profileAverage = float(sum(toneWeights)) / len(toneWeights)
        histogramAverage = float(sum(pcDistribution)) / len(pcDistribution) 
            
        for i in range(len(soln)):
            for j in range(len(toneWeights)):
                top[i] = top[i] + ((
                    toneWeights[(j - i) % 12]-profileAverage) * (
                    pcDistribution[j]-histogramAverage))

                bottomRight[i] = bottomRight[i] + ((
                    toneWeights[(j-i)%12]-profileAverage)**2)
                bottomLeft[i] = bottomLeft[i] + ((
                    pcDistribution[j]-histogramAverage)**2)

                if (bottomRight[i] == 0 or bottomLeft[i] == 0):
                    soln[i] = 0
                else:
                    soln[i] = float(top[i]) / ((bottomRight[i]*bottomLeft[i])**.5)
        return soln    

    def solutionLegend(self, compress=False):
        ''' Returns a list of lists of possible results for the creation of a legend.

        
        >>> p = analysis.discrete.KrumhanslSchmuckler()
        >>> post = p.solutionLegend()
        '''
        # need a presentation order for legend; not alphabetical
        _keySortOrder = ['C-', 'C', 'C#',
                          'D-', 'D', 'D#',
                          'E-', 'E',
                          'F', 'F#',
                          'G-', 'G', 'G#',
                          'A-', 'A', 'A#',
                          'B-', 'B',
                        ]
        if compress:
            colorsUsed = self.getColorsUsed()
            solutionsUsed = self.getSolutionsUsed()

            #environLocal.printDebug(['colors used:', colorsUsed])
            keySortOrderFiltered = []
            for keyEl in _keySortOrder:
                for sol in solutionsUsed: # three values
                    if sol[0] is None: 
                        continue
                    if keyEl == sol[0].name: # first is key string
                        keySortOrderFiltered.append(keyEl)
                        break
        else:
            keySortOrderFiltered = _keySortOrder

        data = []
        for yLabel in ['Major', 'Minor']:
            if yLabel == 'Major':
                valid = self.keysValidMajor
            elif yLabel == 'Minor':
                valid = self.keysValidMinor
            row = []
            row.append(yLabel)
            pairs = []
            for keyPitch in [pitch.Pitch(p) for p in keySortOrderFiltered]:
                try:
                    color = self.solutionToColor([keyPitch, yLabel])
                except KeyError: # no such color defined; expected in a few 
                    color = None # will be masked
                mask = False
                if compress:
                    if color not in colorsUsed:
                        mask = True
                if keyPitch.name not in valid:
                    mask = True
                if mask:
                    # set as white so as to maintain spacing
                    color = '#ffffff' 
                    keyStr = ''
                else:
                    # replace all '-' with 'b' (or proper flat symbol)
                    #keyStr = key.name.replace('-', 'b')
                    keyStr = keyPitch.name
                    # make minor keys in lower case
                    if yLabel == 'Minor':
                        keyStr = keyStr.lower()
                pairs.append((keyStr, color))
            row.append(pairs)
            data.append(row)    
        return data
    
    def solutionUnitString(self):
        '''
        Return a string describing the solution values. Used in Legend formation. 
        '''
        return 'Keys'

    
    def solutionToColor(self, solution):
        solutionKey = solution[0]
        # key may be None
        if solutionKey is None:
            return '#ffffff'
        modality = solution[1].lower()
        if modality == 'major':
            return self._majorKeyColors[solutionKey.name]
        else:
            return self._minorKeyColors[solutionKey.name]

    
    def _likelyKeys(self, sStream):
        pcDistribution = self._getPitchClassDistribution(sStream)
        #environLocal.printDebug(['process(); pcDistribution', pcDistribution])
    
        keyResultsMajor = self._convoluteDistribution(pcDistribution, 'major')
        differenceMajor = self._getDifference(keyResultsMajor, 
                          pcDistribution, 'major')
        likelyKeysMajor = self._getLikelyKeys(keyResultsMajor, differenceMajor)
        

        keyResultsMinor = self._convoluteDistribution(pcDistribution, 'minor')   
        differenceMinor = self._getDifference(keyResultsMinor, 
                          pcDistribution, 'minor')
        likelyKeysMinor = self._getLikelyKeys(keyResultsMinor, differenceMinor)

        return likelyKeysMajor, likelyKeysMinor


    def _bestKeyEnharmonic(self, pitchObj, mode, sStream=None):
        '''
        
        >>> ks = analysis.discrete.KrumhanslSchmuckler()
        >>> s = converter.parse('tinynotation: 4/4 b-4 e- f g-')
        >>> ks._bestKeyEnharmonic(pitch.Pitch('e#'), 'minor', s)
        <music21.pitch.Pitch F>
        >>> ks._bestKeyEnharmonic(pitch.Pitch('f-'), 'major', s)
        <music21.pitch.Pitch E>

        '''
        if pitchObj is None:
            return None

        # this does not yet seem necessary
        # if not done at init with ref stream, do now
#         if self.sharpFlatCount is None:
#             sharpFlatCount = self._getSharpFlatCount(sStream)
#         else:
#             sharpFlatCount = self.sharpFlatCount
# 
#         if sharpFlatCount[0] > sharpFlatCount[1]:
#             favor = 'sharp'
#         elif sharpFlatCount[1] > sharpFlatCount[0]:
#             favor = 'flat'
#         else:
#             favor = None

        flipEnharmonic = False
#         if pitchObj.accidental is not None:
#             # if we have a sharp key and we need to favor flat, get enharm
#             if pitchObj.accidental.alter > 0 and favor == 'flat':
#                 flipEnharmonic = True
#             elif pitchObj.accidental.alter < 0 and favor == 'sharp':
#                 flipEnharmonic = True

#         if flipEnharmonic == False:
        if mode == 'major':
            if pitchObj.name not in self.keysValidMajor:
                flipEnharmonic = True
        elif mode == 'minor':
            if pitchObj.name not in self.keysValidMinor:
                flipEnharmonic = True
        #environLocal.printDebug(['pre flip enharmonic', pitchObj])
        if flipEnharmonic:
            pitchObj.getEnharmonic(inPlace=True)
        #environLocal.printDebug(['post flip enharmonic', pitchObj])
        return pitchObj


    def process(self, sStream, storeAlternatives=False):    
        '''
        Takes in a Stream or sub-Stream and performs analysis 
        on all contents of the Stream. The 
        :class:`~music21.analysis.windowed.WindowedAnalysis` 
        windowing system can be used to get numerous results 
        by calling this method. 

        Returns two values, a solution data list and a color string.

        The data list contains a key (as a string), a mode 
        (as a string), and a correlation value (degree of certainty)
        '''
        sStream = sStream.flat.notesAndRests
        # this is the sample distribution used in the paper, for some testing purposes
        #pcDistribution = [7,0,5,0,7,16,0,16,0,15,6,0]
        
        # this is the distribution for the melody of "happy birthday"
        #pcDistribution = [9,0,3,0,2,5,0,2,0,2,2,0]
    
        likelyKeysMajor, likelyKeysMinor = self._likelyKeys(sStream)

        #find the largest correlation value to use to select major or minor as the resulting key
        # values are the result of _getLikelyKeys
        # each first index is the sorted results; there will be 12
        # each first index is tuple
        # the tuple defines a Pitch, as well as the differences value
        # from _getDifference

        #if likelyKeysMajor is None or likelyKeysMinor is None:
        #    mode = None
        #    solution = (None, mode, 0)

        # see which has a higher correlation coefficient, the first major or the
        # the first minor
        if likelyKeysMajor is not None:
            sortList = [(coefficient, p, 'major') for 
                        (p, coefficient) in likelyKeysMajor]
        else:
            sortList = []
        if likelyKeysMinor is not None:
            sortList += [(coefficient, p, 'minor') for 
                         (p, coefficient) in likelyKeysMinor]
        if len(sortList) == 0:
            raise DiscreteAnalysisException('failed to get likely keys for Stream component')

        sortList.sort()
        sortList.reverse()
        #environLocal.printDebug(['sortList', sortList])

        coefficient, p, mode = sortList[0]
        p = self._bestKeyEnharmonic(p, mode, sStream)
        solution = (p, mode, coefficient)

        color = self.solutionToColor(solution)

        # store all aleternatives in solution format
        if storeAlternatives:
            self._alternativeSolutions = []
            # get all but first
            for coefficient, p, mode in sortList[1:]:
                # adjust enharmonic spelling
                p = self._bestKeyEnharmonic(p, mode, sStream)
                self._alternativeSolutions.append((p, mode, coefficient))

        # store solutions for compressed legend generation
        self._solutionsFound.append((solution, color))
        return solution, color        
    
    def _solutionToObject(self, solution):
        '''Convert a solution into an appropriate object representation, returning a Key object.
        '''
        k = key.Key(tonic=solution[0], mode=solution[1])
        k.correlationCoefficient = solution[2]
        return k

    def getSolution(self, sStream):
        '''
        Return a music21 Key object defining the results of the analysis. 
        Do not call process before calling this method, as this method calls process. 

        Note that all alternative solutions are returned as Key objects and stored 
        on a list found at Key.alternateInterpretations.

        
        >>> s = corpus.parse('bach/bwv66.6')
        >>> p = analysis.discrete.KrumhanslSchmuckler()
        >>> p.getSolution(s) # this seems correct
        <music21.key.Key of f# minor>

        >>> s = corpus.parse('bach/bwv57.8')
        >>> p = analysis.discrete.KrumhanslSchmuckler(s)
        >>> p.getSolution(s) 
        <music21.key.Key of B- major>
        '''
        # always take a flat version here, otherwise likely to get nothing
        solution, unused_color = self.process(sStream.flat, storeAlternatives=True)
        # assign best solution
        k = self._solutionToObject(solution)
        if k.alternateInterpretations is None:
            k.alternateInterpretations = []
            
        for sol in self._alternativeSolutions:
            # append each additional interpretation
            k.alternateInterpretations.append(self._solutionToObject(sol))
        return k



#------------------------------------------------------------------------------
# specialize subclass by class

class KrumhanslSchmuckler(KeyWeightKeyAnalysis):
    '''
    Implementation of Krumhansl-Schmuckler weightings for 
    Krumhansl-Schmuckler key determination algorithm.
    '''
    _DOC_ALL_INHERITED = False
    name = 'Krumhansl Schmuckler Key Analysis'
    identifiers = ['key.krumhansl', 'key.schmuckler',  'key.krumhansl-schmuckler', 
                   'key.krumhanslschmuckler', 
                   'krumhansl', 'schmuckler',  'krumhansl-schmuckler', 
                   'krumhanslschmuckler', 
                   ]

    def __init__(self, referenceStream=None):
        KeyWeightKeyAnalysis.__init__(self, referenceStream=referenceStream)

    def _getWeights(self, weightType='major'): 
        '''
        Returns the key weights. To provide different key weights, 
        subclass and override this method. The defaults here are KrumhanslSchmuckler.
            
        
        >>> a = analysis.discrete.KrumhanslSchmuckler()
        >>> len(a._getWeights('major'))
        12
        >>> len(a._getWeights('minor'))
        12            
        '''
        weightType = weightType.lower()
        if weightType == 'major':
            return [6.35, 2.33, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
        elif weightType == 'minor':
            return [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]    
        else:
            raise DiscreteAnalysisException('no weights defined for weight type: %s' % weightType)


class KrumhanslKessler(KeyWeightKeyAnalysis):
    '''
    Implementation of Krumhansl-Kessler weightings for Krumhansl-Schmuckler 
    key determination algorithm.

    Values from from http://extra.humdrum.org/man/keycor/, which describes these 
    weightings as "Strong tendency to identify the dominant key as the tonic."
    '''
    # from http://extra.humdrum.org/man/keycor/
    _DOC_ALL_INHERITED = False
    name = 'Krumhansl Kessler Key Analysis'
    identifiers = ['key.kessler', 'key.krumhansl-kessler', 'key.krumhanslkessler',
                   'kessler', 'krumhansl-kessler', 'krumhanslkessler',
                   ]

    def __init__(self, referenceStream=None):
        KeyWeightKeyAnalysis.__init__(self, referenceStream=referenceStream)

    def _getWeights(self, weightType='major'): 
        '''
        Returns the key weights.    
        
        >>> a = analysis.discrete.KrumhanslKessler()
        >>> len(a._getWeights('major'))
        12
        >>> len(a._getWeights('minor'))
        12            
        '''
        weightType = weightType.lower()
        # note: only one value is different from KrumhanslSchmuckler
        if weightType == 'major':
            return [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 
                3.66, 2.29, 2.88]
        elif weightType == 'minor':
            return [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]    
        else:
            raise DiscreteAnalysisException('no weights defined for weight type: %s' % weightType)


class AardenEssen(KeyWeightKeyAnalysis):
    '''
    Implementation of Aarden-Essen weightings for Krumhansl-Schmuckler key determination algorithm.

    Values from from http://extra.humdrum.org/man/keycor/, which 
    describes these weightings as "Weak tendency to identify the subdominant key as the tonic."

    (N.B. -- we are not sure exactly where the minor weightings come from, and recommend
    only using these weights for major).
    '''
    # from http://extra.humdrum.org/man/keycor/
    _DOC_ALL_INHERITED = False
    name = 'Aarden Essen Key Analysis'
    identifiers = ['key.aarden', 'key.essen', 'key.aarden-essen', 'key.aardenessen',
                   'aarden', 'essen', 'aarden-essen', 'aardenessen',
                   ]
    # adding these identifiers make this the default
    identifiers.append('key')
    identifiers.append('keyscape')

    def __init__(self, referenceStream=None):
        KeyWeightKeyAnalysis.__init__(self, referenceStream=referenceStream)

    def _getWeights(self, weightType='major'): 
        '''
        Returns the key weights.     
        
        >>> a = analysis.discrete.AardenEssen()
        >>> len(a._getWeights('major'))
        12
        >>> len(a._getWeights('minor'))
        12            
        '''
        weightType = weightType.lower()
        # note: only one value is different from KrumhanslSchmuckler
        if weightType == 'major':
            return [17.7661, 0.145624, 14.9265, 0.160186, 19.8049, 11.3587,
                0.291248, 22.062, 0.145624, 
                8.15494, 0.232998, 4.95122]
        elif weightType == 'minor':
            return [18.2648, 0.737619, 14.0499, 16.8599, 0.702494, 14.4362, 
                    0.702494, 18.6161, 4.56621, 1.93186, 7.37619, 1.75623]    
        else:
            raise DiscreteAnalysisException('no weights defined for weight type: %s' % weightType)


class SimpleWeights(KeyWeightKeyAnalysis):
    '''
    Implementation of Craig Sapp's simple weights for Krumhansl-Schmuckler 
    key determination algorithm.

    Values from from http://extra.humdrum.org/man/keycor/, which describes 
    these weightings as "Performs most consistently with large regions of music, 
    becomes noisier with smaller regions of music."
    '''
    # from http://extra.humdrum.org/man/keycor/
    _DOC_ALL_INHERITED = False
    name = 'Simple Weight Key Analysis'
    identifiers = ['key.simple', 'key.weight', 'key.simple-weight', 'key.simpleweight',
                   'simple', 'weight', 'simple-weight', 'simpleweight',
                   ]

    def __init__(self, referenceStream=None):
        KeyWeightKeyAnalysis.__init__(self, referenceStream=referenceStream)

    def _getWeights(self, weightType='major'): 
        '''
        Returns the key weights.     
        
        >>> a = analysis.discrete.SimpleWeights()
        >>> len(a._getWeights('major'))
        12
        >>> len(a._getWeights('minor'))
        12            
        '''
        weightType = weightType.lower()
        # note: only one value is different from KrumhanslSchmuckler
        if weightType == 'major':
            return [2, 0, 1, 0, 1, 1, 0, 2, 0, 1, 0, 1]
        elif weightType == 'minor':
            return [2, 0, 1, 1, 0, 1, 0, 2, 1, 0, 0.5, 0.5]    
        else:
            raise DiscreteAnalysisException('no weights defined for weight type: %s' % weightType)


class BellmanBudge(KeyWeightKeyAnalysis):
    '''
    Implementation of Bellman-Budge weightings for Krumhansl-Schmuckler key determination algorithm.

    Values from from http://extra.humdrum.org/man/keycor/, which describes these 
    weightings as "No particular tendencies for confusions with neighboring keys."
    '''
    # from http://extra.humdrum.org/man/keycor/
    _DOC_ALL_INHERITED = False
    name = 'Bellman Budge Key Analysis'
    identifiers = ['key.bellman', 'key.budge', 'key.bellman-budge', 'key.bellmanbudge',
                   'bellman', 'budge', 'bellman-budge', 'bellmanbudge',
                   ]

    def __init__(self, referenceStream=None):
        KeyWeightKeyAnalysis.__init__(self, referenceStream=referenceStream)

    def _getWeights(self, weightType='major'): 
        '''
        Returns the key weights. 
        
        >>> a = analysis.discrete.BellmanBudge()
        >>> len(a._getWeights('major'))
        12
        >>> len(a._getWeights('minor'))
        12            
        >>> a._getWeights('major')
        [16.8..., 0.8..., 12.9..., 1.4..., ...]

        '''
        weightType = weightType.lower()
        # note: only one value is different from KrumhanslSchmuckler
        if weightType == 'major':
            return [16.80, 0.86, 12.95, 1.41, 13.49, 11.93, 1.25, 20.28, 1.80, 8.04, 0.62, 10.57]
        elif weightType == 'minor':
            return [18.16, 0.69, 12.99, 13.34, 1.07, 11.15, 1.38, 21.07, 7.49, 1.53, 0.92, 10.21]    
        else:
            raise DiscreteAnalysisException('no weights defined for weight type: %s' % weightType)



class TemperleyKostkaPayne(KeyWeightKeyAnalysis):
    '''
    Implementation of Temperley-Kostka-Payne weightings for Krumhansl-Schmuckler 
    key determination algorithm.

    Values from from http://extra.humdrum.org/man/keycor/, which describes 
    these weightings as "Strong tendency to identify the relative major as the tonic 
    in minor keys. Well-balanced for major keys."
    '''
    # from http://extra.humdrum.org/man/keycor/
    _DOC_ALL_INHERITED = False
    name = 'Temperley Kostka Payne Key Analysis'
    identifiers = ['key.temperley', 'key.kostka', 'key.payne', 
                   'key.temperley-kostka-payne', 'key.temperleykostkapayne',                   
                   'temperley', 'kostka', 'payne', 
                   'temperley-kostka-payne', 'temperleykostkapayne'
                   ]

    def __init__(self, referenceStream=None):
        KeyWeightKeyAnalysis.__init__(self, referenceStream=referenceStream)

    def _getWeights(self, weightType='major'): 
        ''' Returns the key weights. 
        
        >>> a = analysis.discrete.TemperleyKostkaPayne()
        >>> len(a._getWeights('major'))
        12
        >>> len(a._getWeights('minor'))
        12            
        '''
        weightType = weightType.lower()
        # note: only one value is different from KrumhanslSchmuckler
        if weightType == 'major':
            return [0.748, 0.060, 0.488, 0.082, 0.670, 0.460, 
                    0.096, 0.715, 0.104, 0.366, 0.057, 0.400]
        elif weightType == 'minor':
            return [0.712, 0.084, 0.474, 0.618, 0.049, 0.460, 
                    0.105, 0.747, 0.404, 0.067, 0.133, 0.330]    
        else:
            raise DiscreteAnalysisException('no weights defined for weight type: %s' % weightType)

# store a constant with all classes 
keyWeightKeyAnalysisClasses = [KrumhanslSchmuckler, KrumhanslKessler, 
                               AardenEssen, SimpleWeights, BellmanBudge, TemperleyKostkaPayne]



















#------------------------------------------------------------------------------
class Ambitus(DiscreteAnalysis):
    '''
    An basic analysis method for measuring register. 
    '''
    _DOC_ALL_INHERITED = False

    name = 'Ambitus Analysis'
    # provide possible string matches for this processor
    identifiers = ['ambitus', 'range', 'span']

    def __init__(self, referenceStream=None):
        '''
        
        >>> ambitusAnalysis = analysis.discrete.Ambitus()
        >>> ambitusAnalysis.identifiers[0]
        'ambitus'
        '''
        DiscreteAnalysis.__init__(self, referenceStream=referenceStream)
        self._pitchSpanColors = {}
        self._generateColors()


    def _generateColors(self, numColors=None):
        '''
        Provide uniformly distributed colors across the entire range.
        '''
        if numColors is None:
            if self._referenceStream is not None:
                # get total range for entire piece
                minPitch, maxPitch = self.getPitchRanges(self._referenceStream)
            else:
                minPitch, maxPitch = 0, 130 # a large default
        else: # create minPitch maxPitch
            minPitch, maxPitch = 0, numColors

        valueRange = maxPitch - minPitch
        if valueRange == 0:
            valueRange = 1 # avoid float division by zero
        step = 0
        antiBlack = 25
        for i in range(minPitch, maxPitch+1):
            # do not use all 255 to avoid going to black
            val = int(round(((255.0 - antiBlack)/ valueRange) * step)) + antiBlack
            # store in dictionary the accepted values, not the step
            self._pitchSpanColors[i] = self._rgbToHex(((val*.75), (val*.6), val))
            step += 1

        #environLocal.printDebug([self._pitchSpanColors])
    
    def getPitchSpan(self, subStream):
        '''
        For a given subStream, return the pitch with the minimum and 
        maximum pitch space value found. 

        This public method may be used by other classes. 

        ignores ChordSymbol objects...
        
        >>> s = corpus.parse('bach/bwv66.6')
        >>> p = analysis.discrete.Ambitus()
        >>> pitchMin, pitchMax = p.getPitchSpan(s.parts[0].getElementsByClass('Measure')[3])
        >>> pitchMin.ps, pitchMax.ps
        (66.0, 71.0)
        >>> p.getPitchSpan(s.parts[0].getElementsByClass('Measure')[6])
        (<music21.pitch.Pitch A4>, <music21.pitch.Pitch C#5>)

        >>> s = stream.Stream()
        >>> c = chord.Chord(['a2', 'b4', 'c8'])
        >>> s.append(c)
        >>> p.getPitchSpan(s)
        (<music21.pitch.Pitch A2>, <music21.pitch.Pitch C8>)
        '''
        ssfn = subStream.flat.notes
        if len(ssfn) == 0:
            # need to handle case of no pitches
            return None

        # find the min and max pitch space value for all pitches
        psFound = []
        pitchesFound = []
        for n in ssfn:
            #environLocal.printDebug([n])
            pitches = []
            if 'Chord' in n.classes and 'ChordSymbol' not in n.classes:
                pitches = n.pitches
            elif 'Note' in n.classes:
                pitches = [n.pitch]
            psFound += [p.ps for p in pitches]
            pitchesFound.extend(pitches)
        # in some cases no pitch space values are found due to all rests
        if psFound == []:
            return None
        # use built-in functions
        minPitchIndex = psFound.index(min(psFound))
        maxPitchIndex = psFound.index(max(psFound))
        
        return pitchesFound[minPitchIndex], pitchesFound[maxPitchIndex]

    
    def getPitchRanges(self, subStream):
        '''
        For a given subStream, return the smallest .ps difference 
        between any two pitches and the largest difference 
        between any two pitches. This is used to get the 
        smallest and largest ambitus possible in a given work. 

        
        >>> p = analysis.discrete.Ambitus()
        >>> s = stream.Stream()
        >>> c = chord.Chord(['a2', 'b4', 'c8'])
        >>> s.append(c)
        >>> [int(thisPitch.ps) for thisPitch in p.getPitchSpan(s)]
        [45, 108]
        >>> p.getPitchRanges(s)
        (26, 63)

        >>> s = corpus.parse('bach/bwv66.6')
        >>> p.getPitchRanges(s)
        (0, 34)
        
        
        >>> s = stream.Stream()
        >>> p.getPitchRanges(s)
        (0, 0)
        '''
        ssfn = subStream.flat.notes
        
        psFound = []
        for n in ssfn:
            pitches = []
            if 'Chord' in n.classes:
                pitches = n.pitches
            elif 'Note' in n.classes:
                pitches = [n.pitch]
            for p in pitches:
                psFound.append(p.ps)
        psFound.sort()
        psRange = []
        for i in range(len(psFound)-1):
            p1 = psFound[i]
            for j in range(i+1, len(psFound)):
                p2 = psFound[j]
                # p2 should always be equal or greater than p1
                psRange.append(p2-p1)
        
        if len(psRange) == 0:
            return 0, 0
        else:
            return int(min(psRange)), int(max(psRange))


    def solutionLegend(self, compress=False):
        '''
        Return legend data. 

        >>> s = corpus.parse('bach/bwv66.6')
        >>> p = analysis.discrete.Ambitus(s.parts[0]) #provide ref stream
        >>> len(p.solutionLegend())
        2
        >>> [len(x) for x in p.solutionLegend()]
        [2, 2]

        >>> [len(y) for y in [x for x in p.solutionLegend()]]
        [2, 2]

        >>> s = corpus.parse('bach/bwv66.6')
        >>> p = analysis.discrete.Ambitus()
        >>> p.solutionLegend(compress=True) # empty if nothing processed
        [['', []], ['', []]]

        >>> x = p.process(s.parts[0])
        >>> [len(y) for y in [x for x in p.solutionLegend(compress=True)]]
        [2, 2]

        >>> x = p.process(s.parts[1])
        >>> [len(y) for y in [x for x in p.solutionLegend(compress=True)]]
        [2, 2]

        '''
        if compress:
            colorsUsed = self.getColorsUsed()

        data = []

        colors = {} # a filtered dictionary
        for i in range(len(self._pitchSpanColors.keys())):
            if compress:
                if self._pitchSpanColors[i] not in colorsUsed:
                    continue
            colors[i] = self._pitchSpanColors[i]  

        # keys here are solutions, not colors
        keys = list(colors.keys())
        keys.sort()

        keysTopRow = keys[:(len(keys)//2)]
        keysBottomRow = keys[(len(keys)//2):]

        # split keys into two groups for two rows (optional)
        for keyGroup in [keysTopRow, keysBottomRow]:
            row = []
            row.append('') # empty row label
            pairs = []
            for i in keyGroup:
                color = colors[i] # get form colors
                pairs.append((i, color))
            row.append(pairs)
            data.append(row)

        return data

    def solutionUnitString(self):
        '''
        Return a string describing the solution values. Used in Legend formation. 
        '''
        return 'Half-Steps'


    def solutionToColor(self, result):
        '''
        
        >>> p = analysis.discrete.Ambitus()
        >>> s = stream.Stream()
        >>> c = chord.Chord(['a2', 'b4', 'c8'])
        >>> s.append(c)
        >>> min, max = p.getPitchSpan(s)
        >>> p.solutionToColor(max.ps - min.ps).startswith('#')
        True
        '''    
        # a result of None may be possible
        if result is None:
            return self._rgbToHex((255, 255, 255))

        return self._pitchSpanColors[result]
    
    
    def process(self, sStream):
        '''
        Given a Stream, return a solution (as an interval) and a color string. 

        >>> p = analysis.discrete.Ambitus()
        >>> s = stream.Stream()
        >>> c = chord.Chord(['a2', 'b4', 'c8'])
        >>> s.append(c)
        >>> p.process(s)
        (<music21.interval.Interval m38>, '#665288')
        '''
        post = self.getPitchSpan(sStream)
        if post is not None:
            solution = interval.Interval(noteStart=post[0], noteEnd=post[1])
        else:
            solution = None
        color = self.solutionToColor(post[1].ps - post[0].ps)
        
        # store solutions for compressed legend generation
        self._solutionsFound.append((solution, color))
        return solution, color


    def getSolution(self, sStream):
        '''
        Procedure to only return an Inteval object.
        
        >>> s = corpus.parse('bach/bwv66.6')
        >>> p = analysis.discrete.Ambitus()
        >>> p.getSolution(s)
        <music21.interval.Interval m21>
        '''
        solution, unused_color = self.process(sStream)
        return solution




#------------------------------------------------------------------------------
class MelodicIntervalDiversity(DiscreteAnalysis):
    '''
    An analysis method to determine the diversity of intervals used in a Stream.
    '''
    _DOC_ALL_INHERITED = False

    name = 'Interval Diversity'
    # provide possible string matches for this processor
    identifiers = ['interval.diversity', 'intervals']

    def __init__(self, referenceStream=None):
        '''
        '''
        DiscreteAnalysis.__init__(self, referenceStream=referenceStream)


    def solutionToColor(self, solution):
        # TODO: map diversity to color span
        return '#ffffff'

    def countMelodicIntervals(self, sStream, found=None, ignoreDirection=True, ignoreUnison=True):
        '''
        Find all unique melodic intervals in this Stream. 

        If `found` is provided as a dictionary, this dictionary will be used to store Intervals, 
        and counts of Intervals already found will be incremented.
        '''
        # note that Stream.findConsecutiveNotes() and Stream.melodicIntervals()
        # offer similar approaches, but return Streams and manage offsets and durations, 
        # components not needed here
    
        if found is None:
            found = {}

        # if this has parts, need to move through each at a time
        if sStream.hasPartLikeStreams():
            procList = [s for s in sStream.getElementsByClass('Stream')]
        else: # assume a single list of notes
            procList = [sStream]

        for p in procList:
            # get only Notes for now, skipping rests and chords
            noteStream = p.stripTies(inPlace=False).getElementsByClass('Note').stream()
            #noteStream.show()
            for i, n in enumerate(noteStream):
                if i <= len(noteStream) - 2:
                    nNext = noteStream[i+1]
                else:
                    nNext = None

                if nNext is not None:
                    #environLocal.printDebug(['creating interval from notes:', n, nNext, i])
                    i = interval.notesToInterval(n, nNext)
                    if ignoreUnison: # will apply to enharmonic eq unisons
                        if i.chromatic.semitones == 0:
                            continue
                    if ignoreDirection:
                        if i.chromatic.semitones < 0:
                            i = i.reverse()
                    # must use directed name for cases where ignoreDirection
                    # is false
                    if i.directedName not in found:
                        found[i.directedName] = [i, 1]
                    else:
                        found[i.directedName][1] += 1 # increment counter
                        
#         def compare(x, y):
#             return abs(x.chromatic.semitones) - abs(y.chromatic.semitones)
#         found.sort(cmp=compare)

        return found

    def process(self, sStream, ignoreDirection=True):
        '''
        Find how many unique intervals are used in this Stream
        '''
        uniqueIntervals = self.countMelodicIntervals(sStream, ignoreDirection)
        return len(uniqueIntervals), self.solutionToColor(len(uniqueIntervals))


    def getSolution(self, sStream):
        '''Solution is the number of unique intervals.
        '''
        solution, unused_color = self.process(sStream.flat)
        return solution


#------------------------------------------------------------------------------
# public access function

def analyzeStream(streamObj, *args, **keywords):
    '''
    Public interface to discrete analysis methods to be applied 
    to a Stream given as an argument. Methods return process-specific data format. 
    See subclasses for details. 

    Analysis methods can be specified as arguments or by use of a `method` 
    keyword argument. If `method` is the class name, that class is returned. 
    Otherwise, the :attr:`~music21.analysis.discrete.DiscreteAnalysis.indentifiers` 
    list of all :class:`~music21.analysis.discrete.DiscreteAnalysis` subclass objects 
    will be searched for matches. The first match that is found is returned. 

    :class:`~music21.analysis.discrete.Ambitus`
    :class:`~music21.analysis.discrete.KrumhanslSchmuckler`
    
    >>> s = corpus.parse('bach/bwv66.6')
    >>> analysis.discrete.analyzeStream(s, 'Krumhansl')
    <music21.key.Key of f# minor>
    >>> analysis.discrete.analyzeStream(s, 'ambitus')
    <music21.interval.Interval m21>

    >>> analysis.discrete.analyzeStream(s, 'key')
    <music21.key.Key of f# minor>
    >>> analysis.discrete.analyzeStream(s, 'range')
    <music21.interval.Interval m21>


    Note that the same results can be obtained by calling "analyze" directly on the stream object:
    >>> s.analyze('key')
    <music21.key.Key of f# minor>
    >>> s.analyze('range')
    <music21.interval.Interval m21>

    '''
    if 'method' in keywords:
        method = keywords['method']
    if args:
        method = args[0]
        
    match = analysisClassFromMethodName(method)
    
    if match is not None:
        obj = match() # NOTE: Cuthbert, this was previously analysisClassName()? - out of scope
        #environLocal.printDebug(['analysis method used:', obj])
        return obj.getSolution(streamObj)

    # if no match raise error
    raise DiscreteAnalysisException('no such analysis method: %s' % method)

def analysisClassFromMethodName(method):
    '''
    Returns an analysis class given a method name, or None if none can be found

    Searches first the class name, then the .identifiers array for each class,
    then a subset of any identifier.
    
    >>> acfmn = analysis.discrete.analysisClassFromMethodName
    >>> acfmn('aarden')
    <class 'music21.analysis.discrete.AardenEssen'>
    >>> acfmn('range')
    <class 'music21.analysis.discrete.Ambitus'>
    
    This one is fundamentally important...
    
    >>> acfmn('key')
    <class 'music21.analysis.discrete.AardenEssen'>
    
    >>> print(repr(acfmn('asdfadsfasdf')))
    None
    '''
    analysisClasses = [
        Ambitus,
        KrumhanslSchmuckler,
        KrumhanslKessler,
        AardenEssen,
        SimpleWeights,
        BellmanBudge,
        TemperleyKostkaPayne,
    ]
    match = None
    for analysisClass in analysisClasses:    
        # this is a very loose matching, as there are few classes now
        if (method.lower() in analysisClass.__name__.lower()
                or method.lower() in analysisClass.name):
            match = analysisClass
            #environLocal.printDebug(['matched analysis class name'])
            break
        
    if match is None:
        # no match for exact class name, so check to see if .identifiers matches
        for analysisClass in analysisClasses:    
            for idStr in analysisClass.identifiers:
                if method == idStr:
                    match = analysisClass
                    #environLocal.printDebug(['matched idStr', idStr])
                    break

    if match is None:
        # no match for identifiers, so see if the id is a subset of identifiers.
        for analysisClass in analysisClasses:    
            for idStr in analysisClass.identifiers:
                if method in idStr:
                    match = analysisClass
                    #environLocal.printDebug(['matched idStr', idStr])
                    break
            if match is not None:
                break

    return match

#------------------------------------------------------------------------------
class TestExternal(unittest.TestCase):

    def runTest(self):
        pass
    
    
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testKeyAnalysisKrumhansl(self):
        from music21 import converter

        p = KrumhanslSchmuckler()
        s1 = converter.parse('tinynotation: 4/4 c4 d e f g a b c   c#4 d# e# f#')
        s2 = converter.parse('tinynotation: 4/4 c#4 d# e# f#  f g a b- c d e f')
        s3 = converter.parse('tinynotation: 4/4 c4 d e f g a b c   c#4 d# e# f#  ' + 
                             'c#4 d# e# f#  f g a b- c d e f')

        #self.assertEqual(p._getPitchClassDistribution(s1), 
        #            [1.0, 0, 1.0, 0, 0, 0, 0, 0, 0, 0, 0, 0])

        p.process(s1.flat)
        likelyKeysMajor1, likelyKeysMinor1 = p._likelyKeys(s1.flat)
        likelyKeysMajor1.sort()
        likelyKeysMinor1.sort()
        allResults1 =  likelyKeysMajor1 + likelyKeysMinor1
        #print
        #post = []
        unused_post = sorted([(y, x) for x, y in allResults1])
        #print post

        p.process(s2.flat)
        likelyKeysMajor2, likelyKeysMinor2 = p._likelyKeys(s2.flat)
        likelyKeysMajor2.sort()
        likelyKeysMinor2.sort()
        allResults2 =  likelyKeysMajor2 + likelyKeysMinor2
        #print
        #post = []
        unused_post = sorted([(y, x) for x, y in allResults2])
        #print post

        likelyKeysMajor3, likelyKeysMinor3 = p._likelyKeys(s3.flat)
        likelyKeysMajor3.sort()
        likelyKeysMinor3.sort()
        allResults3 =  likelyKeysMajor3 + likelyKeysMinor3
        #print
        #post = []
        unused_post = sorted([(y, x) for x, y in allResults3])
        #print post

        avg = []
        for i in range(len(allResults1)):
            p, count1 = allResults1[i]
            p, count2 = allResults2[i]
            avg.append((p, (count1+count2)/2.0))
        #print
        #post = []
        unused_post = sorted([(y, x) for x, y in avg])
        #print post


    def testIntervalDiversity(self):
        from music21 import note, stream, corpus
        
        s = stream.Stream()
        s.append(note.Note('g#3'))
        s.append(note.Note('a3'))
        s.append(note.Note('g4'))

        mid = MelodicIntervalDiversity()
        midDict = mid.countMelodicIntervals(s)
        self.assertEqual(str(midDict['m7']), "[<music21.interval.Interval m7>, 1]")
        self.assertEqual(str(midDict['m2']), "[<music21.interval.Interval m2>, 1]")
        self.assertEqual(len(midDict), 2)

        s = stream.Stream()
        s.append(note.Note('c3'))
        s.append(note.Note('d3'))
        s.append(note.Note('c3'))
        s.append(note.Note('d3'))

        mid = MelodicIntervalDiversity()
        midDict = mid.countMelodicIntervals(s)
        self.assertEqual(len(midDict), 1)
        self.assertEqual(str(midDict['M2']), "[<music21.interval.Interval M2>, 3]")

        midDict = mid.countMelodicIntervals(s, ignoreDirection=False)
        self.assertEqual(len(midDict), 2)
        self.assertEqual(str(midDict['M-2']), "[<music21.interval.Interval M-2>, 1]")
        self.assertEqual(str(midDict['M2']), "[<music21.interval.Interval M2>, 2]")

        mid = MelodicIntervalDiversity()
        s = corpus.parse('corelli/opus3no1/1grave')
        #s.show()

        midDict = mid.countMelodicIntervals(s.parts[1])
        self.assertEqual(len(midDict), 9)
        self.assertEqual(str(midDict['P5']), "[<music21.interval.Interval P5>, 8]")
        self.assertEqual(str(midDict['P4']), "[<music21.interval.Interval P4>, 7]")       
        self.assertEqual(str(midDict['m3']), "[<music21.interval.Interval m3>, 1]")
        self.assertEqual(str(midDict['M2']), "[<music21.interval.Interval M2>, 21]")       
       

        midDict = mid.countMelodicIntervals(s)
        self.assertEqual(len(midDict), 10)
        self.assertEqual(str(sorted(list(midDict))), 
                         "['M2', 'M3', 'M6', 'P15', 'P4', 'P5', 'P8', 'd5', 'm2', 'm3']")
        self.assertEqual(str(midDict['P15']), "[<music21.interval.Interval P15>, 1]")
        self.assertEqual(str(midDict['P5']), "[<music21.interval.Interval P5>, 16]")
        self.assertEqual(str(midDict['P4']), "[<music21.interval.Interval P4>, 29]")       
        self.assertEqual(str(midDict['M3']), "[<music21.interval.Interval M3>, 16]")
        self.assertEqual(str(midDict['m3']), "[<music21.interval.Interval m3>, 12]")
        self.assertEqual(str(midDict['M2']), "[<music21.interval.Interval M2>, 79]")       
        self.assertEqual(str(midDict['m2']), "[<music21.interval.Interval m2>, 43]")       
        

    def testKeyAnalysisSpelling(self):
        from music21 import stream, note
            
        for p in ['A', 'B-', 'A-']:
            s = stream.Stream()
            s.append(note.Note(p))
            self.assertEqual(str(s.analyze('Krumhansl').tonic), p)


    def testKeyAnalysisDiverseWeights(self):
        from music21 import converter
        from music21.musicxml import testFiles
        # use a musicxml test file with independently confirmed results
        s = converter.parse(testFiles.edgefield82b) # @UndefinedVariable

        p = KrumhanslSchmuckler()
        k = p.getSolution(s)
        post = [k.tonic, k.mode, k.correlationCoefficient]
        self.assertEqual(str(post[0]), 'F#')
        self.assertEqual(str(post[1]), 'major')
        self.assertEqual(str(post[2])[0:7], '0.81210')

        p = KrumhanslKessler()
        k = p.getSolution(s)
        post = [k.tonic, k.mode, k.correlationCoefficient]
        self.assertEqual(str(post[0]), 'F#')
        self.assertEqual(str(post[1]), 'major')

        p = AardenEssen()
        k = p.getSolution(s)
        post = [k.tonic, k.mode, k.correlationCoefficient]
        self.assertEqual(str(post[0]), 'F#')
        self.assertEqual(str(post[1]), 'minor')

        p = SimpleWeights()
        k = p.getSolution(s)
        post = [k.tonic, k.mode, k.correlationCoefficient]
        self.assertEqual(str(post[0]), 'F#')
        self.assertEqual(str(post[1]), 'minor')

        p = BellmanBudge()
        k = p.getSolution(s)
        post = [k.tonic, k.mode, k.correlationCoefficient]
        self.assertEqual(str(post[0]), 'F#')
        self.assertEqual(str(post[1]), 'minor')


        p = TemperleyKostkaPayne()
        k = p.getSolution(s)
        post = [k.tonic, k.mode, k.correlationCoefficient]
        self.assertEqual(str(post[0]), 'F#')
        self.assertEqual(str(post[1]), 'minor')


    def testKeyAnalysisLikelyKeys(self):
        from music21 import note, stream
        s = stream.Stream()
        s.repeatAppend(note.Note('c'), 6)
        s.repeatAppend(note.Note('g'), 4)
        s.repeatAppend(note.Note('a'), 2)
        
        k = s.analyze('KrumhanslSchmuckler')
        self.assertEqual(str(k), 'C major')
        self.assertEqual(" ".join(kp.tonicPitchNameWithCase for kp in k.alternateInterpretations), 
                         'c G a F g e f E- A- B- d D A b b- c# f# C# E g# F# B e-')

        k = s.analyze('AardenEssen')
        self.assertEqual(str(k), 'F major')
        self.assertEqual(" ".join(kp.tonicPitchNameWithCase for kp in k.alternateInterpretations),
                         'C c g f a G d A- B- E- e b- D A f# C# b E c# e- F# B g#') 
        
        #s.plot('grid', 'KrumhanslSchmuckler')
        #s.plot('windowed', 'aarden')


# define presented order in documentation
_DOC_ORDER = [analyzeStream, DiscreteAnalysis, Ambitus, MelodicIntervalDiversity, 
              KeyWeightKeyAnalysis, SimpleWeights, AardenEssen, BellmanBudge, 
              KrumhanslSchmuckler, KrumhanslKessler, TemperleyKostkaPayne]

#------------------------------------------------------------------------------

if __name__ == "__main__":
    import music21
    music21.mainTest(Test)



#------------------------------------------------------------------------------
# eof


