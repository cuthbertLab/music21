#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         features.py
# Purpose:      music21 functions for simple feature extraction
#
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------


# features here are a based on those found in a numerous other software 
# packages, including  the following;
# jsymbolic (lgpl): http://jmir.sourceforge.net/jSymbolic.html


import unittest
import music21

from music21 import environment
_MOD = 'repeat.py'
environLocal = environment.Environment(_MOD)


#-------------------------------------------------------------------------------
class FeatureExtractor(object):
    def __init__(self, streamObj, *arguments, **keywords):
        self._src = streamObj


    def extractFeature(self):
        '''Extract the feature and return the result. 
        '''
    
#-------------------------------------------------------------------------------
# 112 feature extractors


class AmountOfArpeggiationFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
class AverageMelodicIntervalFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
class AverageNoteDurationFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class AverageNoteToNoteDynamicsChangeFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class AverageNumberOfIndependentVoicesFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class AverageRangeOfGlissandosFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class AverageTimeBetweenAttacksFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class AverageTimeBetweenAttacksForEachVoiceFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class AverageVariabilityOfTimeBetweenAttacksForEachVoiceFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class BasicPitchHistogramFeature(FeatureExtractor):
    '''A feature exractor that finds a features array with bins corresponding to the values of the basic pitch histogram.

    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class BeatHistogramFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class BrassFractionFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class ChangesOfMeterFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class ChromaticMotionFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class CombinedStrengthOfTwoStrongestRhythmicPulsesFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class CompoundOrSimpleMeterFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class DirectionOfMotionFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class DistanceBetweenMostCommonMelodicIntervalsFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class DominantSpreadFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class DurationFeature(FeatureExtractor):
    '''A feature exractor that extracts the duration in seconds.

    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class DurationOfMelodicArcsFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)



 
class FifthsPitchHistogramFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class GlissandoPrevalenceFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class HarmonicityOfTwoStrongestRhythmicPulsesFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class ImportanceOfBassRegisterFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class ImportanceOfHighRegisterFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class ImportanceOfLoudestVoiceFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class ImportanceOfMiddleRegisterFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class InitialTempoFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class InitialTimeSignatureFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class IntervalBetweenStrongestPitchClassesFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class IntervalBetweenStrongestPitchesFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class MaximumNoteDurationFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class MaximumNumberOfIndependentVoicesFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class MelodicFifthsFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class MelodicIntervalHistogramFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
class MelodicIntervalsInLowestLineFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
class MelodicOctavesFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class MelodicThirdsFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class MelodicTritonesFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class MinimumNoteDurationFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
class MostCommonMelodicIntervalFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class MostCommonMelodicIntervalPrevalenceFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class MostCommonPitchClassFeature(FeatureExtractor):
    '''A feature exractor that finds the bin label of the most common pitch class.

    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class MostCommonPitchClassPrevalenceFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class MostCommonPitchFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
class MostCommonPitchPrevalenceFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
class NoteDensityFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class NotePrevalenceOfPitchedInstrumentsFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class NotePrevalenceOfUnpitchedInstrumentsFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class NumberOfCommonMelodicIntervalsFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)


class NumberOfCommonPitchesFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class NumberOfModeratePulsesFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)


 
class NumberOfRelativelyStrongPulsesFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class NumberOfStrongPulsesFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 

 
class OverallDynamicRangeFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)


 
class PitchClassDistributionFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class PitchClassVarietyFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class PitchedInstrumentsPresentFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class PitchVarietyFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class PolyrhythmsFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class PrimaryRegisterFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
class QualityFeature(FeatureExtractor):
    '''A feature exractor that sets the feature to 0 if the key signature indicates that a recording is major, set to 1 if it indicates that it is minor and set to 0 if key signature is unknown.

    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class QuintupleMeterFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class RangeFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class RangeOfHighestLineFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class RelativeNoteDensityOfHighestLineFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class RelativeRangeOfLoudestVoiceFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class RelativeStrengthOfMostCommonIntervalsFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class RelativeStrengthOfTopPitchClassesFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
class RelativeStrengthOfTopPitchesFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class RepeatedNotesFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
class RhythmicLoosenessFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class RhythmicVariabilityFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 

 
class SecondStrongestRhythmicPulseFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
class SizeOfMelodicArcsFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class StaccatoIncidenceFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class StepwiseMotionFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
class StrengthOfSecondStrongestRhythmicPulseFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
class StrengthOfStrongestRhythmicPulseFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class StrengthRatioOfTwoStrongestRhythmicPulsesFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)


 
class StrongestRhythmicPulseFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class StrongTonalCentresFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class TimePrevalenceOfPitchedInstrumentsFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
class TripleMeterFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 

 
class VariabilityOfNoteDurationFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
class VariabilityOfNotePrevalenceOfPitchedInstrumentsFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
class VariabilityOfNotePrevalenceOfUnpitchedInstrumentsFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class VariabilityOfNumberOfIndependentVoicesFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class VariabilityOfTimeBetweenAttacksFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
class VariationOfDynamicsFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class VariationOfDynamicsInEachVoiceFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class VibratoPrevalenceFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class VoiceEqualityDynamicsFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
class VoiceEqualityMelodicLeapsFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
class VoiceEqualityNoteDurationFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
class VoiceEqualityNumberOfNotesFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
class VoiceEqualityRangeFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
class VoiceSeparationFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
#-------------------------------------------------------------------------------
# instrumentation specific


class AcousticGuitarFractionFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class ElectricGuitarFractionFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)


 
class ElectricInstrumentFractionFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class NumberOfPitchedInstrumentsFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

class NumberOfUnpitchedInstrumentsFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)


class OrchestralStringsFractionFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)


class PercussionPrevalenceFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

class SaxophoneFractionFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

class StringEnsembleFractionFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)


class StringKeyboardFractionFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

class UnpitchedInstrumentsPresentFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)


class ViolinFractionFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

class WoodwindsFractionFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 








#-------------------------------------------------------------------------------
class Test(unittest.TestCase):
    
    def runTest(self):
        pass




if __name__ == "__main__":
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof




