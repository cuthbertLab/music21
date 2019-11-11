# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         analysis/floatingKey.py
# Purpose:      Framework for floating key analysis
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2015 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
The floatingKey analyzer will give an approximation of the key at any point in
a score down to the measure level using a fixed window.  It helps smooth out
measures emphasizing non-chord tones, etc.
'''
import copy
from music21 import key
from music21.exceptions21 import AnalysisException

class FloatingKeyException(AnalysisException):
    pass

class KeyAnalyzer:
    '''
    KeyAnalyzer is the main object to use for floating analysis.

    The `windowSize` attribute (default 4) determines how many measures to look at in making
    the decision.  Make it larger for pieces (like Mozart sonatas) that you expect fewer key
    changes.  Make it smaller for pieces (like Bach chorales) that you expect more key changes.
    Or set it to an integer based on the number of the measures in the piece.

    The `weightAlgorithm` attribute determines how to scale the weight of measures according to
    their distance.  Currently only one algorithm is supported: floatingKey.divide.

    TODO: Needs more work to work with second endings, partial measures, etc.

    >>> b = corpus.parse('bwv66.6')
    >>> ka = analysis.floatingKey.KeyAnalyzer(b)
    >>> ka.windowSize = 2  # chorale uses quick key changes
    >>> ka.run()  # first measure is the pickup
    [<music21.key.Key of A major>, <music21.key.Key of A major>, <music21.key.Key of A major>,
     <music21.key.Key of f# minor>, <music21.key.Key of f# minor>, <music21.key.Key of f# minor>,
     <music21.key.Key of f# minor>, <music21.key.Key of f# minor>,
     <music21.key.Key of f# minor>, <music21.key.Key of f# minor>]

    Raw analysis (no smoothing):

    >>> ka.getRawKeyByMeasure()
    [<music21.key.Key of A major>, <music21.key.Key of E major>, <music21.key.Key of A major>,
     <music21.key.Key of f# minor>, <music21.key.Key of E major>, <music21.key.Key of A major>,
     <music21.key.Key of b minor>, <music21.key.Key of C# major>,
     <music21.key.Key of F# major>, <music21.key.Key of b minor>]

    Major smoothing...

    >>> ka.windowSize = ka.numMeasures // 2
    >>> ka.run()  # only the pickup seems to be in A major by this approach
    [<music21.key.Key of A major>, <music21.key.Key of f# minor>, <music21.key.Key of f# minor>,
     <music21.key.Key of f# minor>, <music21.key.Key of f# minor>, <music21.key.Key of f# minor>,
     <music21.key.Key of f# minor>, <music21.key.Key of f# minor>,
     <music21.key.Key of f# minor>, <music21.key.Key of f# minor>]
    '''
    def __init__(self, s=None):
        if s is None:
            raise FloatingKeyException('Need a Stream to initialize')
        self.stream = s
        self.windowSize = 4
        self.rawKeyByMeasure = []
        self._interpretationMeasureDict = {}

        self.weightAlgorithm = divide
        if s.hasPartLikeStreams():
            p = s.parts[0]
        else:
            p = s
        self.numMeasures = len(p.getElementsByClass('Measure'))  # could be wrong for endings, etc.
        if self.numMeasures == 0:
            raise FloatingKeyException("Stream must have Measures inside it")

    def run(self):
        self.getRawKeyByMeasure()
        return self.smoothInterpretationByMeasure()

    def getRawKeyByMeasure(self):
        keyByMeasure = []
        for i in range(self.numMeasures):
            m = self.stream.measure(i)
            if m is None or not m.recurse().notes:
                k = None
            else:
                k = m.analyze('key')
            keyByMeasure.append(k)
        self.rawKeyByMeasure = keyByMeasure
        return keyByMeasure

    def getInterpretationByMeasure(self, mNumber):
        '''
        Returns a dictionary of interpretations for the measure.
        '''
        if mNumber in self._interpretationMeasureDict:
            return self._interpretationMeasureDict[mNumber]  # CACHE
        if not self.rawKeyByMeasure:
            self.getRawKeyByMeasure()
        mk = self.rawKeyByMeasure[mNumber]
        if mk is None:
            return None
        # noinspection PyDictCreation
        interpretations = {}
        interpretations[mk.tonicPitchNameWithCase] = mk.correlationCoefficient
        for otherKey in mk.alternateInterpretations:
            interpretations[otherKey.tonicPitchNameWithCase] = otherKey.correlationCoefficient
        self._interpretationMeasureDict[mNumber] = interpretations
        return copy.copy(interpretations)  # for manipulating

    def smoothInterpretationByMeasure(self):
        smoothedKeysByMeasure = []
        algorithm = self.weightAlgorithm

        for i in range(self.numMeasures):
            baseInterpretations = self.getInterpretationByMeasure(i)
            if baseInterpretations is None:
                continue
            for j in range(-1 * self.windowSize, self.windowSize + 1):  # -2, -1, 0, 1, 2 etc.
                mNum = i + j
                if mNum < 0 or mNum >= self.numMeasures or mNum == i:
                    continue
                newInterpretations = self.getInterpretationByMeasure(mNum)
                if newInterpretations is not None:
                    for k in baseInterpretations:
                        coefficient = algorithm(newInterpretations[k], j)
                        baseInterpretations[k] += coefficient
            bestName = max(baseInterpretations, key=baseInterpretations.get)
            smoothedKeysByMeasure.append(key.Key(bestName))

        return smoothedKeysByMeasure

def divide(coefficient, distance):
    '''
    Divide the coefficient by the absolute value of the distance + 1

    >>> analysis.floatingKey.divide(4.0, -1)
    2.0
    '''
    return coefficient / (abs(distance) + 1)


if __name__ == '__main__':
    import music21
    music21.mainTest()
