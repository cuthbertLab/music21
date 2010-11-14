#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         windowed.py
# Purpose:      Framework for modular, windowed analysis
#
# Authors:      Jared Sadoian
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

'''Modular analysis procedures for use alone or applied with :class:`music21.analysis.windowed.WindowedAnalysis` class. 

All procedures should inherit from :class:`music21.analysis.discrete.DiscreteAnalysis`, or provide a similar interface. 

The :class:`music21.analysis.discrete.KrumhanslSchmuckler` (for algorithmic key detection) and :class:`music21.analysis.discrete.Ambitus` (for pitch range analysis) provide examples.
'''

import unittest
import sys
import music21

from music21 import meter
from music21 import pitch
from music21 import stream 
from music21 import interval



from music21 import environment
_MOD = 'discrete.py'
environLocal = environment.Environment(_MOD)



#------------------------------------------------------------------------------
class DiscreteAnalysisException(Exception):
    pass

class DiscreteAnalysis(object):
    ''' Parent class for analytical methods.

    Each analytical method returns a discrete numerical (or other) results as well as a color. Colors can be used in mapping output.

    Analytical methods may make use of a `referenceStream` to configure the processor on initialization. 
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

    def _rgbToHex(self, rgb):
        '''Utility conversion method
        '''
        rgb = int(round(rgb[0])), int(round(rgb[1])), int(round(rgb[2]))
        return '#%02x%02x%02x' % rgb    

    def _hexToRgb(self, value):
        '''Utility conversion method    
        >>> da = DiscreteAnalysis()
        >>> da._hexToRgb('#ffffff')
        [255, 255, 255]
        >>> da._hexToRgb('#000000')
        [0, 0, 0]
        '''
        value = value.lstrip('#')
        lv = len(value)
        return list(int(value[i:i+lv/3], 16) for i in range(0, lv, lv/3))

    def _rgbLimit(self, value):
        '''Utility conversion method    
        >>> da = DiscreteAnalysis()
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
        '''Based on solutions found so far with with this processor, return the colors that have been used.
        '''
        post = []
        for solution, color in self._solutionsFound:
            if color not in post:
                post.append(color)
        return post    

    def getSolutionsUsed(self):
        '''Based on solutions found so far with with this processor, return the solutions that have been used.
        '''
        post = []
        for solution, color in self._solutionsFound:
            if solution not in post:
                post.append(solution)
        return post   

    def solutionLegend(self, compress=False):
        '''A list of pairs showing all discrete results and the assigned color. Data should be organized to be passed to :class:`music21.graph.GraphColorGridLegend`.

        If `compress` is True, the legend will only show values for solutions that have been encountered. 
        '''
        pass


    def solutionUnitString(self):
        '''Return a string describing the solution values. Used in Legend formation. 
        '''
        return None
    
    def solutionToColor(self, result):
        '''Given a analysis specific result, return the appropriate color. Must be able to handle None in the case that there is no result.
        '''
        pass
    
    def process(self, subStream):
        '''Given a Stream, apply the analysis to all components of this Stream. Expected return is a solution (method specific) and a color value.
        '''
        pass


    def getSolution(self, subStream):
        '''For a given Stream, apply the analysis and return the best solution.
        '''
        pass


#------------------------------------------------------------------------------
# alternative names
# PitchClassKeyFinding
# KeySearchByProbeTone
# ProbeToneKeyFinding

class KrumhanslSchmuckler(DiscreteAnalysis):
    ''' Implementation of the Krumhansl-Schmuckler key determination algorithm
    '''
    _DOC_ALL_INHERITED = False

    name = 'Krumhansl Schmuckler Key Analysis'

    identifiers = ['krumhansl', 'schmuckler', 'key', 'keyscape']

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
        if referenceStream != None:
            self.sharpFlatCount = self._getSharpFlatCount(referenceStream)
        else:
            self.sharpFlatCount = None
        
        self._majorKeyColors = {}
        self._minorKeyColors = {}
        self._fillColorDictionaries()
    
    def _fillColorDictionaries(self):
        '''
        >>> p = KrumhanslSchmuckler()
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
            for key in valid:
                # convert to pitch object
                key = pitch.Pitch(key)
                step = key.step # get C for C#
                rgbStep = self._hexToRgb(stepLib[step])
                # make all the colors a bit lighter
                for i in range(len(rgbStep)):
                    rgbStep[i] = self._rgbLimit(rgbStep[i] + 50)
        
                #make minor darker
                if valid == self.keysValidMinor:
                    for i in range(len(rgbStep)):
                        rgbStep[i] = self._rgbLimit(rgbStep[i] - 100)
        
                if len(key.name) > 1:
                    magnitude = 15
                    if key.name[1] == '-':
                        # index and value shift for each of rgb values
                        shiftLib = {0: magnitude, 1: magnitude, 2: -magnitude}                   
                    elif key.name[1] == '#':                   
                        shiftLib = {0: -magnitude, 1: -magnitude, 2: magnitude}                   
                    for i in shiftLib.keys():
                        rgbStep[i] = self._rgbLimit(rgbStep[i] + shiftLib[i])
                # add to dictionary
                dst[key.name] = self._rgbToHex(rgbStep)


    def _getSharpFlatCount(self, subStream):
        '''Determine count of sharps and flats in a Stream

        >>> from music21 import *
        >>> s = corpus.parseWork('bach/bwv66.6')
        >>> p = KrumhanslSchmuckler()
        >>> p._getSharpFlatCount(s.flat)
        (87, 0)
        '''
        # pitches gets a flat representation
        flatCount = 0
        sharpCount = 0
        for p in subStream.pitches:
            if p.accidental != None:
                if p.accidental.alter < 0:
                    flatCount += -1
                elif p.accidental.alter > 0:
                    sharpCount += 1
        return sharpCount, flatCount

    def _getWeights(self, weightType='major'): 
        ''' Returns either the a weight key profile as described by Sapp and others
            
        >>> a = KrumhanslSchmuckler()
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
        '''Given a flat Stream, obtain a pitch class distribution. The value of each pitch class is scaled by its duration in quarter lengths.

        >>> from music21 import note, stream, chord
        >>> a = KrumhanslSchmuckler()
        >>> s = stream.Stream()
        >>> n1 = note.Note('c')
        >>> n1.quarterLength = 3
        >>> n2 = note.Note('f#')
        >>> n2.quarterLength = 2
        >>> s.append(n1)
        >>> s.append(n2)
        >>> a._getPitchClassDistribution(s)
        [3, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0]
        >>> c1 = chord.Chord(['d', 'e', 'b-'])
        >>> c1.quarterLength = 1.5
        >>> s.append(c1)
        >>> a._getPitchClassDistribution(s)
        [3, 0, 1.5, 0, 1.5, 0, 2, 0, 0, 0, 1.5, 0]
        '''
        # storage for 12 pitch classes
        pcDist = [0]*12
        if len(streamObj.notes) == 0:
            return None

        for n in streamObj.notes:        
            if not n.isRest:
                length = n.quarterLength
                if n.isChord:
                    for m in n.pitchClasses:
                        pcDist[m] = pcDist[m] + (1 * length)
                else:
                    pcDist[n.pitchClass] = pcDist[n.pitchClass] + (1 * length)
        return pcDist


    def _convoluteDistribution(self, pcDistribution, weightType='major'):
        ''' Takes in a pitch class distribution as a list and convolutes it
            over Sapp's given distribution for finding key, returning the result. 
        '''
        # may get an empty distribution
        if pcDistribution == None:
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
        if keyResults == None:
            return None

        likelyKeys = [0] * 12
        a = sorted(keyResults)
        a.reverse()
        
        #Return pairs, the pitch class and the correlation value, in order by point value
        for i in range(len(a)):
            # pitch objects created here
            likelyKeys[i] = (pitch.Pitch(keyResults.index(a[i])),
                             differences[keyResults.index(a[i])])
        return likelyKeys
        
        
    def _getDifference(self, keyResults, pcDistribution, weightType):
        ''' Takes in a list of numerical probable key results and returns the
            difference of the top two keys
        '''
        # case of empty analysis
        if keyResults == None:
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

        >>> from music21 import *
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
            for key in _keySortOrder:
                for sol in solutionsUsed: # three v alues
                    if sol[0] == None: 
                        continue
                    if key == sol[0].name: # first is key string
                        keySortOrderFiltered.append(key)
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
            for key in [pitch.Pitch(p) for p in keySortOrderFiltered]:
                try:
                    color = self.solutionToColor([key, yLabel])
                except KeyError: # no such color defined; expected in a few 
                    color = None # will be masked
                mask = False
                if compress:
                    if color not in colorsUsed:
                        mask = True
                if key.name not in valid:
                    mask = True
                if mask:
                    # set as white so as to maintain spacing
                    color = '#ffffff' 
                    keyStr = ''
                else:
                    # replace all '-' with 'b' (or proper flat symbol)
                    #keyStr = key.name.replace('-', 'b')
                    keyStr = key.name
                    # make minor keys in lower case
                    if yLabel == 'Minor':
                        keyStr = keyStr.lower()
                pairs.append((keyStr, color))
            row.append(pairs)
            data.append(row)    
        return data
    
    def solutionUnitString(self):
        '''Return a string describing the solution values. Used in Legend formation. 
        '''
        return 'Keys'

    
    def solutionToColor(self, solution):
        key = solution[0]
        # key may be None
        if key == None:
            return '#ffffff'
        modality = solution[1].lower()
        if modality == 'major':
            return self._majorKeyColors[key.name]
        else:
            return self._minorKeyColors[key.name]



    
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
        >>> from music21 import *
        >>> p = analysis.discrete.KrumhanslSchmuckler()
        >>> s = converter.parse('b-4 e- f g-', '4/4')
        >>> p._bestKeyEnharmonic(pitch.Pitch('e#'), 'minor', s)
        F4
        >>> p._bestKeyEnharmonic(pitch.Pitch('f-'), 'major', s)
        E4

        '''
        if pitchObj == None:
            return None

        # this does not yet seem necessary
        # if not done at init with ref stream, do now
#         if self.sharpFlatCount == None:
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
#         if pitchObj.accidental != None:
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

        if flipEnharmonic:
            pitchObj.getEnharmonic(inPlace=True)
        return pitchObj


    def process(self, sStream):    
        ''' Takes in a Stream or sub-Stream and performs analysis on all contents of the Stream. The :class:`~music21.analysis.windowed.WindowedAnalysis` windowing system can be used to get numerous results by calling this method. 

        Returns two values, a solution data list and a color string.

        The data list contains a key (as a string), a mode (as a string), and a correlation value (degree of certainty)
        '''
        sStream = sStream.flat.notes
        # this is the sample distribution used in the paper, for some testing purposes
        #pcDistribution = [7,0,5,0,7,16,0,16,0,15,6,0]
        
        # this is the distribution for the melody of "happy birthday"
        #pcDistribution = [9,0,3,0,2,5,0,2,0,2,2,0]
    
        likelyKeysMajor, likelyKeysMinor = self._likelyKeys(sStream)

        #find the largest correlation value to use to select major or minor as the resulting key
        if likelyKeysMajor == None or likelyKeysMinor == None:
            mode = None
            solution = (None, mode, 0)
        elif likelyKeysMajor[0][1] > likelyKeysMinor[0][1]:
            mode = 'major'
            solution = (likelyKeysMajor[0][0], mode, likelyKeysMajor[0][1])
        else:
            mode = 'minor'
            solution = (likelyKeysMinor[0][0], mode, likelyKeysMinor[0][1])

        # first solution is pitch object
        p = self._bestKeyEnharmonic(solution[0], mode, sStream)
        solution = (p, mode, solution[2])

        color = self.solutionToColor(solution)


        # store solutions for compressed legend generation
        self._solutionsFound.append((solution, color))
        return solution, color        
    

    def getSolution(self, sStream):
        ''' procedure to only return a text solution
        >>> from music21 import *
        >>> s = corpus.parseWork('bach/bwv66.6')
        >>> p = KrumhanslSchmuckler()
        >>> p.getSolution(s) # this seems correct
        (F#, 'minor', 0.81547089257624916)

        >>> s = corpus.parseWork('bach/bwv57.8')
        >>> p = KrumhanslSchmuckler(s)
        >>> p.getSolution(s) 
        (B-, 'major', 0.89772788962941652)
        '''
        # always take a flat version here, otherwise likely to get nothing
        solution, color = self.process(sStream.flat)
        return solution




#------------------------------------------------------------------------------
class Ambitus(DiscreteAnalysis):
    '''An basic analysis method for measuring register. 
    '''
    _DOC_ALL_INHERITED = False

    name = 'Sadoian Ambitus Analysis'
    # provide possible string matches for this processor
    identifiers = ['ambitus', 'range', 'span']

    def __init__(self, referenceStream=None):
        '''
        >>> p = Ambitus()
        >>> p.identifiers[0]
        'ambitus'
        '''
        DiscreteAnalysis.__init__(self, referenceStream=referenceStream)
        self._pitchSpanColors = {}
        self._generateColors()


    def _generateColors(self, numColors=None):
        '''Provide uniformly distributed colors across the entire range.
        '''
        if numColors == None:
            if self._referenceStream != None:
                # get total range for entire piece
                min, max = self.getPitchRanges(self._referenceStream)
            else:
                min, max = 0, 130 # a large default
        else: # create min max
            min, max = 0, numColors

        valueRange = max - min
        step = 0
        antiBlack = 25
        for i in range(min, max+1):
            # do not use all 255 to avoid going to black
            val = int(round(((255.0 - antiBlack)/ valueRange) * step)) + antiBlack
            # store in dictionary the accepted values, not the step
            self._pitchSpanColors[i] = self._rgbToHex(((val*.75), (val*.6), val))
            step += 1

        #environLocal.printDebug([self._pitchSpanColors])
    
    def getPitchSpan(self, subStream):
        '''For a given subStream, return the minimum and maximum pitch space value found. 

        This public method may be used by other classes. 

        >>> from music21 import *
        >>> s = corpus.parseWork('bach/bwv66.6')
        >>> p = Ambitus()
        >>> p.getPitchSpan(s.parts[0].getElementsByClass('Measure')[3])
        (66, 71)
        >>> p.getPitchSpan(s.parts[0].getElementsByClass('Measure')[6])
        (69, 73)

        >>> s = stream.Stream()
        >>> c = chord.Chord(['a2', 'b4', 'c8'])
        >>> s.append(c)
        >>> p.getPitchSpan(s)
        (45, 108)
        '''
        
        if len(subStream.flat.notes) == 0:
            # need to handle case of no pitches
            return None

        # find the min and max pitch space value for all pitches
        psFound = []
        for n in subStream.flat.notes:
            #environLocal.printDebug([n])
            pitches = []
            if 'Chord' in n.classes:
                pitches = n.pitches
            elif 'Note' in n.classes:
                pitches = [n.pitch]
            psFound += [p.ps for p in pitches]

        # in some cases no pitch space values are found due to all rests
        if psFound == []:
            return None
        # use built-in functions
        return int(min(psFound)), int(max(psFound))

    
    def getPitchRanges(self, subStream):
        '''For a given subStream, return the smallest difference between any two pitches and the largest difference between any two pitches. This is used to get the smallest and largest ambitus possible in a given work. 

        >>> from music21 import *
        >>> p = Ambitus()
        >>> s = stream.Stream()
        >>> c = chord.Chord(['a2', 'b4', 'c8'])
        >>> s.append(c)
        >>> p.getPitchSpan(s)
        (45, 108)
        >>> p.getPitchRanges(s)
        (26, 63)

        >>> s = corpus.parseWork('bach/bwv66.6')
        >>> p.getPitchRanges(s)
        (0, 34)
        '''
        psFound = []
        for n in subStream.flat.notes:
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

        return int(min(psRange)), int(max(psRange))


    def solutionLegend(self, compress=False):
        '''Return legend data. 

        >>> from music21 import *
        >>> s = corpus.parseWork('bach/bwv66.6')
        >>> p = analysis.discrete.Ambitus(s.parts[0]) #provide ref stream
        >>> len(p.solutionLegend())
        2
        >>> [len(x) for x in p.solutionLegend()]
        [2, 2]

        >>> [len(y) for y in [x for x in p.solutionLegend()]]
        [2, 2]

        >>> s = corpus.parseWork('bach/bwv66.6')
        >>> p = Ambitus()
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
        keys = colors.keys()
        keys.sort()

        keysTopRow = keys[:(len(keys)/2)]
        keysBottomRow = keys[(len(keys)/2):]

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
        '''Return a string describing the solution values. Used in Legend formation. 
        '''
        return 'Half-Steps'


    def solutionToColor(self, result):
        '''
        >>> from music21 import *
        >>> p = Ambitus()
        >>> s = stream.Stream()
        >>> c = chord.Chord(['a2', 'b4', 'c8'])
        >>> s.append(c)
        >>> min, max = p.getPitchSpan(s)
        >>> p.solutionToColor(max-min).startswith('#')
        True
        '''    
        # a result of None may be possible
        if result == None:
            return self._rgbToHex((255, 255, 255))

        return self._pitchSpanColors[result]
    
    
    def process(self, sStream):
        '''Given a Stream, return a solution (in half steps) and a color string. 

        >>> from music21 import *
        >>> p = analysis.discrete.Ambitus()
        >>> s = stream.Stream()
        >>> c = chord.Chord(['a2', 'b4', 'c8'])
        >>> s.append(c)
        >>> p.process(s)
        (63, '#665288')
        '''
        sStream = sStream.flat.notes

        post = self.getPitchSpan(sStream)
        if post != None:
            solution = post[1] - post[0] # max-min
        else:
            solution = None
        color = self.solutionToColor(solution)
        
        # store solutions for compressed legend generation
        self._solutionsFound.append((solution, color))
        return solution, color


    def getSolution(self, sStream):
        '''Procedure to only return an Inteval object.

        >>> from music21 import *
        >>> s = corpus.parseWork('bach/bwv66.6')
        >>> p = Ambitus()
        >>> p.getSolution(s)
        <music21.interval.Interval m21>

        '''
        solution, color = self.process(sStream)
        return interval.Interval(solution)




#------------------------------------------------------------------------------
class MelodicIntervalDiversity(DiscreteAnalysis):
    '''An analysis method to determine the diversity of intervals used in a Stream.
    '''
    _DOC_ALL_INHERITED = False

    name = 'Interval Diversity'
    # provide possible string matches for this processor
    identifiers = ['ambitus', 'range', 'span']

    def __init__(self, referenceStream=None):
        '''
        '''
        DiscreteAnalysis.__init__(self, referenceStream=referenceStream)


    def solutionToColor(self, solution):
        # TODO: map diversity to color span
        return '#ffffff'

    def countMelodicIntervals(self, sStream, found=None, ignoreDirection=True, 
        ignoreUnison=True):
        '''
        Find all unique melodic intervals in this Stream. 

        If `found` is provided as a dictionary, this dictionary will be used to store Intervals, and counts of Intervals already found will be incremented.
        '''
        # note that Stream.findConsecutiveNotes() and Stream.melodicIntervals()
        # offer similar approaches, but return Streams and manage offsets and durations, components not needed here
    
        if found == None:
            found = {}

        # if this has parts, need to move through each at a time
        if sStream.hasPartLikeStreams():
            procList = [s for s in sStream.getElementsByClass('Stream')]
        else: # assume a single list of notes
            procList = [sStream]

        for p in procList:
            # get only Notes for now, skipping rests and chords
            noteStream = p.stripTies(inPlace=False).getElementsByClass('Note')
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
                    if i.directedName not in found.keys():
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
        uniqueIntervals = countMelodicIntervals(sStream, ignoreDirection)
        return len(uniqueIntervals), self.solutionToColor(len(uniqueIntervals))


    def getSolution(self, sStream):
        '''Solution is the number of unique intervals.
        '''
        solution, color = self.process(sStream.flat)
        return solution


#------------------------------------------------------------------------------
# public access function

def analyzeStream(streamObj, *args, **keywords):
    '''Public interface to discrete analysis methods to be applied to a Stream given as an argument. Methods return process-specific data format. See base-classes for details. 

    Analysis methods can be specified as arguments or by use of a `method` keyword argument. If `method` is the class name, that class is returned. Otherwise, the :attr:`~music21.analysis.discrete.DiscreteAnalysis.indentifiers` list of all :class:`~music21.analysis.discrete.DiscreteAnalysis` subclass objects will be searched for matches. The first match that is found is returned. 

    :class:`~music21.analysis.discrete.Ambitus`
    :class:`~music21.analysis.discrete.KrumhanslSchmuckler`

    >>> from music21 import *
    >>> s = corpus.parseWork('bach/bwv66.6')
    >>> analysis.discrete.analyzeStream(s, 'Krumhansl')
    (F#, 'minor', 0.81547089257624916)
    >>> analysis.discrete.analyzeStream(s, 'ambitus')
    <music21.interval.Interval m21>

    >>> analysis.discrete.analyzeStream(s, 'key')[:2]
    (F#, 'minor')
    >>> analysis.discrete.analyzeStream(s, 'range')
    <music21.interval.Interval m21>
    '''
    analysisClasses = [
        Ambitus,
        KrumhanslSchmuckler,
    ]

    if 'method' in keywords:
        method = keywords['method']

    if len(args) > 0:
        method = args[0]

    match = None
    for analysisClassName in analysisClasses:    
        # this is a very loose matching, as there are few classes now
        if (method.lower() in analysisClassName.__name__.lower() or
            method.lower() in analysisClassName.name):
            match = analysisClassName
            #environLocal.printDebug(['matched analysis class name'])
            break
        else:
            for idStr in analysisClassName.identifiers:
                if method in idStr:
                    match = analysisClassName
                    #environLocal.printDebug(['matched idStr', idStr])

                    break
            if match != None:
                break

    if match != None:
        obj = analysisClassName()
        return obj.getSolution(streamObj)


    # if no match raise error
    raise DiscreteAnalysisException('no such analysis method: %s' % method)

#------------------------------------------------------------------------------
class TestExternal(unittest.TestCase):

    def runTest(self):
        pass
    
    
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testKrumhansl(self):
        from music21 import converter, stream

        p = KrumhanslSchmuckler()
        s1 = converter.parse('c4 d e f g a b c   c#4 d# e# f#', '4/4')
        s2 = converter.parse('c#4 d# e# f#  f g a b- c d e f', '4/4')
        s3 = converter.parse('c4 d e f g a b c   c#4 d# e# f#  c#4 d# e# f#  f g a b- c d e f', '4/4')

        #self.assertEqual(p._getPitchClassDistribution(s1), [1.0, 0, 1.0, 0, 0, 0, 0, 0, 0, 0, 0, 0])

        p.process(s1)
        likelyKeysMajor1, likelyKeysMinor1 = p._likelyKeys(s1)
        likelyKeysMajor1.sort()
        likelyKeysMinor1.sort()
        allResults1 =  likelyKeysMajor1 + likelyKeysMinor1
        #print
        post = []
        post = sorted([(y, x) for x, y in allResults1])
        #print post

        p.process(s2)
        likelyKeysMajor2, likelyKeysMinor2 = p._likelyKeys(s2)
        likelyKeysMajor2.sort()
        likelyKeysMinor2.sort()
        allResults2 =  likelyKeysMajor2 + likelyKeysMinor2
        #print
        post = []
        post = sorted([(y, x) for x, y in allResults2])
        #print post

        likelyKeysMajor3, likelyKeysMinor3 = p._likelyKeys(s3)
        likelyKeysMajor3.sort()
        likelyKeysMinor3.sort()
        allResults3 =  likelyKeysMajor3 + likelyKeysMinor3
        #print
        post = []
        post = sorted([(y, x) for x, y in allResults3])
        #print post

        avg = []
        for i in range(len(allResults1)):
            p, count1 = allResults1[i]
            p, count2 = allResults2[i]
            avg.append((p, (count1+count2)/2.0))
        #print
        post = []
        post = sorted([(y, x) for x, y in avg])
        #print post


    def testIntervalDiversity(self):
        from music21 import note, stream, corpus
        
        s = stream.Stream()
        s.append(note.Note('g#3'))
        s.append(note.Note('a3'))
        s.append(note.Note('g4'))

        id = MelodicIntervalDiversity()
        self.assertEqual(str(id.countMelodicIntervals(s)), "{'m7': [<music21.interval.Interval m7>, 1], 'm2': [<music21.interval.Interval m2>, 1]}")


        s = stream.Stream()
        s.append(note.Note('c3'))
        s.append(note.Note('d3'))
        s.append(note.Note('c3'))
        s.append(note.Note('d3'))

        id = MelodicIntervalDiversity()
        self.assertEqual(str(id.countMelodicIntervals(s)), "{'M2': [<music21.interval.Interval M2>, 3]}")

        self.assertEqual(str(id.countMelodicIntervals(s, ignoreDirection=False)), """{'M-2': [<music21.interval.Interval M-2>, 1], 'M2': [<music21.interval.Interval M2>, 2]}""")

        id = MelodicIntervalDiversity()
        s = corpus.parseWork('hwv56', '1-08')
        #s.show()

        self.assertEqual(str(id.countMelodicIntervals(s.parts[1])), "{'P5': [<music21.interval.Interval P5>, 1], 'P4': [<music21.interval.Interval P4>, 1], 'm3': [<music21.interval.Interval m3>, 1], 'M2': [<music21.interval.Interval M2>, 2]}")

        self.assertEqual(str(id.countMelodicIntervals(s)), "{'M3': [<music21.interval.Interval M3>, 1], 'P4': [<music21.interval.Interval P4>, 5], 'P5': [<music21.interval.Interval P5>, 2], 'M2': [<music21.interval.Interval M2>, 8], 'm3': [<music21.interval.Interval m3>, 3], 'm2': [<music21.interval.Interval m2>, 1]}")
        


#------------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) == 1: # normal conditions
        music21.mainTest(Test)
    elif len(sys.argv) > 1:
        t = Test()

        #t.testKrumhansl()

        t.testIntervalDiversity()




#------------------------------------------------------------------------------
# eof


