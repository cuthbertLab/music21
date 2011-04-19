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
class Feature(object):
    '''An object representation of a feature, capable of presentation in a variety of formats, and returned from FeatureExtractor objects.
    '''
    def __init__(self):
        # these values will be filled by the extractor
        self.name = None # string name representation
        self.description = None # string description
        self.isSequential = None # True or False
        self.dimensions = None # number of dimensions

        # data storage
        self._vector = []

#-------------------------------------------------------------------------------
class FeatureExtractor(object):
    def __init__(self, streamObj, *arguments, **keywords):
        self._src = streamObj
        self._feature = None # Feature object

        self.name = None # string name representation
        self.description = None # string description
        self.isSequential = None # True or False
        self.dimensions = None # number of dimensions

    def _fillFeautureAttributes(self, feature=None):
        '''Fill the attributes of a Feature with the descriptors in the FeatureExtractor.
        '''
        # operate on passed-in feature or self._feature
        if feature is None:
            feature = self._feature
        feature.name = self.name
        feature.description = self.description
        feature.isSequential = self.isSequential
        feature.dimensions = self.dimensions
        return feature

    def _process(self):
        '''Do processing necessary, storing result in _feature.
        '''
        self._feature = Feature()
        self._fillFeautureAttributes() # will fill self._feature

    def extract(self, source=None):
        '''Extract the feature and return the result. 
        '''
        if source is not None:
            self._src = source
        self._process() # will set feature object
        return self._feature    

#-------------------------------------------------------------------------------
# 112 feature extractors


class AmountOfArpeggiationFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    >>> s = stream.Stream()
    >>> fe = features.AmountOfArpeggiationFeature(s)
    >>> f = fe.extract()
    >>> f.name
    'Amount of Arpeggiation'
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Amount of Arpeggiation'
        self.description = 'Fraction of horizontal intervals that are repeated notes, minor thirds, major thirds, perfect fifths, minor sevenths, major sevenths, octaves, minor tenths or major tenths.'
        self.isSequential = True
        self.dimensions = 1



class AverageMelodicIntervalFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
        self.name = 'Average Melodic Interval'
        self.description = 'Average melodic interval (in semi-tones).'
        self.isSequential = True
        self.dimensions = 1


class AverageNoteDurationFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Average Note Duration'
        self.description = 'Average duration of notes in seconds.s'
        self.isSequential = True
        self.dimensions = 1

 
class AverageNoteToNoteDynamicsChangeFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Average Note To Note Dynamics Change'
        self.description = 'Average change of loudness from one note to the next note in the same channel (in MIDI velocity units).'
        self.isSequential = True
        self.dimensions = 1

 
class AverageNumberOfIndependentVoicesFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Average Number of Independent Voices'
        self.description = 'Average number of different channels in which notes have sounded simultaneously. Rests are not included in this calculation.'
        self.isSequential = True
        self.dimensions = 1

 
class AverageRangeOfGlissandosFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Average Range of Glissandos'
        self.description = 'Average range of Pitch Bends, where range is defined as the greatest value of the absolute difference between 64 and the second data byte of all MIDI Pitch Bend messages falling betweenthe Note On and Note Off messages of any note.'
        self.isSequential = True
        self.dimensions = 1

 
class AverageTimeBetweenAttacksFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Average Time Between Attacks'
        self.description = 'Average time in seconds between Note On events (regardless of channel).'
        self.isSequential = True
        self.dimensions = 1

 
class AverageTimeBetweenAttacksForEachVoiceFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Average Time Between Attacks For Each Voice'
        self.description = 'Average of average times in seconds between Note On events on individual channels that contain at least one note.'
        self.isSequential = True
        self.dimensions = 1


 
class AverageVariabilityOfTimeBetweenAttacksForEachVoiceFeature(
    FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Average Variability of Time Between Attacks For Each Voice'
        self.description = 'Average standard deviation, in seconds, of time between Note On events on individual channels that contain at least one note.'
        self.isSequential = True
        self.dimensions = 1

 
class BasicPitchHistogramFeature(FeatureExtractor):
    '''A feature exractor that finds a features array with bins corresponding to the values of the basic pitch histogram.

    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

 
class BeatHistogramFeature(FeatureExtractor):
    '''A feature exractor that finds a feature array with entries corresponding to the frequency values of each of the bins of the beat histogram (except the first 40 empty ones).

    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1

  
class ChangesOfMeterFeature(FeatureExtractor):
    '''A feature exractor that sets the feature to 1 if the time signature is changed one or more times during the recording.

    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Changes of Meter'
        self.description = 'Set to 1 if the time signature is changed one or more times during the recording'
        self.isSequential = True
        self.dimensions = 1

    def _process(self):
        # flatten; look for more than one type of meter
        pass
 

class ChromaticMotionFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Chromatic Motion'
        self.description = 'Fraction of melodic intervals corresponding to a semi-tone.'
        self.isSequential = True
        self.dimensions = 1

 
class CombinedStrengthOfTwoStrongestRhythmicPulsesFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Combined Strength of Two Strongest Rhythmic Pulses'
        self.description = 'The sum of the frequencies of the two beat bins of the peaks with the highest frequencies.'
        self.isSequential = True
        self.dimensions = 1


 
class CompoundOrSimpleMeterFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Compound Or Simple Meter'
        self.description = 'Set to 1 if the initial meter is compound (numerator of time signature is greater than or equal to 6 and is evenly divisible by 3) and to 0 if it is simple (if the above condition is not fulfilled).'
        self.isSequential = True
        self.dimensions = 1


 
class DirectionOfMotionFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Direction of Motion'
        self.description = 'Fraction of melodic intervals that are rising rather than falling.'
        self.isSequential = True
        self.dimensions = 1

 
class DistanceBetweenMostCommonMelodicIntervalsFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Distance Between Most Common Melodic Intervals'
        self.description = 'Absolute value of the difference between the most common melodic interval and the second most common melodic interval.'
        self.isSequential = True
        self.dimensions = 1


 
class DominantSpreadFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Dominant Spread'
        self.description = 'Largest number of consecutive pitch classes separated by perfect 5ths that accounted for at least 9% each of the notes.'
        self.isSequential = True
        self.dimensions = 1


 
class DurationFeature(FeatureExtractor):
    '''A feature exractor that extracts the duration in seconds.

    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Duration'
        self.description = 'The total duration in seconds of the music.'
        self.isSequential = False
        self.dimensions = 1

 
class DurationOfMelodicArcsFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Duration of Melodic Arcs'
        self.description = 'Average number of notes that separate melodic peaks and troughs in any channel.'
        self.isSequential = True
        self.dimensions = 1


 
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

        self.name = 'Glissando Prevalence'
        self.description = 'Number of Note Ons that have at least one MIDI Pitch Bend associated with them divided by total number of pitched Note Ons.'
        self.isSequential = True
        self.dimensions = 1

 
class HarmonicityOfTwoStrongestRhythmicPulsesFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Harmonicity of Two Strongest Rhythmic Pulses'
        self.description = 'The bin label of the higher (in terms of bin label) of the two beat bins of the peaks with the highest frequency divided by the bin label of the lower.'
        self.isSequential = True
        self.dimensions = 1


 
class ImportanceOfBassRegisterFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Importance of Bass Register'
        self.description = 'Fraction of Note Ons between MIDI pitches 0 and 54.'
        self.isSequential = True
        self.dimensions = 1


 
class ImportanceOfHighRegisterFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Importance of High Register'
        self.description = 'Fraction of Note Ons between MIDI pitches 73 and 127.'
        self.isSequential = True
        self.dimensions = 1


 
class ImportanceOfLoudestVoiceFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Importance of Loudest Voice'
        self.description = 'Difference between the average loudness of the loudest channel and the average loudness of the other channels that contain at least one note.'
        self.isSequential = True
        self.dimensions = 1


 
class ImportanceOfMiddleRegisterFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Importance of Middle Register'
        self.description = 'Fraction of Note Ons between MIDI pitches 55 and 72.'
        self.isSequential = True
        self.dimensions = 1


 
class InitialTempoFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Initial Tempo'
        self.description = 'Tempo in beats per minute at the start of the recording.'
        self.isSequential = True
        self.dimensions = 1


 
class InitialTimeSignatureFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1


 
class IntervalBetweenStrongestPitchClassesFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Interval Between Strongest Pitch Classes'
        self.description = 'Absolute value of the difference between the pitch classes of the two most common MIDI pitch classes.'
        self.isSequential = True
        self.dimensions = 1


 
class IntervalBetweenStrongestPitchesFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Interval Between Strongest Pitches'
        self.description = 'Absolute value of the difference between the pitches of the two most common MIDI pitches.'
        self.isSequential = True
        self.dimensions = 1


 
class MaximumNoteDurationFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Maximum Note Duration'
        self.description = 'Duration of the longest note (in seconds).'
        self.isSequential = True
        self.dimensions = 1


 
class MaximumNumberOfIndependentVoicesFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1


 
class MelodicFifthsFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1

 
class MelodicIntervalHistogramFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1


class MelodicIntervalsInLowestLineFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1


class MelodicOctavesFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1


 
class MelodicThirdsFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1


 
class MelodicTritonesFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1


 
class MinimumNoteDurationFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1


class MostCommonMelodicIntervalFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1


 
class MostCommonMelodicIntervalPrevalenceFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1


 
class MostCommonPitchClassFeature(FeatureExtractor):
    '''A feature exractor that finds the bin label of the most common pitch class.

    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1


 
class MostCommonPitchClassPrevalenceFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1


 
class MostCommonPitchFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1


class MostCommonPitchPrevalenceFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1


class NoteDensityFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1

 
class NotePrevalenceOfPitchedInstrumentsFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1
 

class NotePrevalenceOfUnpitchedInstrumentsFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1


 
class NumberOfCommonMelodicIntervalsFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1



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

        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1


 
class NumberOfRelativelyStrongPulsesFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1

 
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

        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1



 
class PitchClassDistributionFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1

 
class PitchClassVarietyFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1


 
class PitchedInstrumentsPresentFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1


 
class PitchVarietyFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1


 
class PolyrhythmsFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1

 
class PrimaryRegisterFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1


class QualityFeature(FeatureExtractor):
    '''A feature exractor that sets the feature to 0 if the key signature indicates that a recording is major, set to 1 if it indicates that it is minor and set to 0 if key signature is unknown.

    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1

 
class QuintupleMeterFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1


 
class RangeFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1


 
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

        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1


 
class RelativeRangeOfLoudestVoiceFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1


 
class RelativeStrengthOfMostCommonIntervalsFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1


 
class RelativeStrengthOfTopPitchClassesFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1


class RelativeStrengthOfTopPitchesFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1


 
class RepeatedNotesFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1


class RhythmicLoosenessFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1

 
class RhythmicVariabilityFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1

 

 
class SecondStrongestRhythmicPulseFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1


class SizeOfMelodicArcsFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1

 
class StaccatoIncidenceFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1


 
class StepwiseMotionFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1


class StrengthOfSecondStrongestRhythmicPulseFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1


class StrengthOfStrongestRhythmicPulseFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1

 
class StrengthRatioOfTwoStrongestRhythmicPulsesFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1


 
class StrongestRhythmicPulseFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1

 
class StrongTonalCentresFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1


 
class TimePrevalenceOfPitchedInstrumentsFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1


class TripleMeterFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1


 

 
class VariabilityOfNoteDurationFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1


class VariabilityOfNotePrevalenceOfPitchedInstrumentsFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1


class VariabilityOfNotePrevalenceOfUnpitchedInstrumentsFeature(
    FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1

 
class VariabilityOfNumberOfIndependentVoicesFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1


 
class VariabilityOfTimeBetweenAttacksFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1


class VariationOfDynamicsFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1


 
class VariationOfDynamicsInEachVoiceFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1

 
class VibratoPrevalenceFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1


 
class VoiceEqualityDynamicsFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1


class VoiceEqualityMelodicLeapsFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1


class VoiceEqualityNoteDurationFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1


class VoiceEqualityNumberOfNotesFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1


class VoiceEqualityRangeFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1


class VoiceSeparationFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1


#-------------------------------------------------------------------------------
# instrumentation specific


class AcousticGuitarFractionFeature(FeatureExtractor):
    '''A feature exractor that extracts the fraction of all Note Ons belonging to acoustic guitar patches (General MIDI patches 25 to 26).

    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Acoustic Guitar Fraction'
        self.description = 'Fraction of all Note Ons belonging to acoustic guitar patches (General MIDI patches 25 to 26).'
        self.isSequential = True
        self.dimensions = 1

 
class BrassFractionFeature(FeatureExtractor):
    '''A feature exractor that extracts the fraction of all Note Ons belonging to brass patches (General MIDI patches 57 or 68).

    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Brass Fraction'
        self.description = 'Fraction of all Note Ons belonging to brass patches (GeneralMIDI patches 57 or 68).'
        self.isSequential = True
        self.dimensions = 1



class ElectricGuitarFractionFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Electric Guitar Fraction'
        self.description = 'Fraction of all Note Ons belonging to electric guitar patches (GeneralMIDI patches 27 to 32).'
        self.isSequential = True
        self.dimensions = 1

 
class ElectricInstrumentFractionFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Electric Instrument Fraction'
        self.description = 'Fraction of all Note Ons belonging to electric instrument patches(General MIDI patches 5, 6, 17, 19, 27 to 32 or 34 to 40).'
        self.isSequential = True
        self.dimensions = 1

 
class NumberOfPitchedInstrumentsFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1


class NumberOfUnpitchedInstrumentsFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1



class OrchestralStringsFractionFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1



class PercussionPrevalenceFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1


class SaxophoneFractionFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1


class StringEnsembleFractionFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1



class StringKeyboardFractionFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1


class UnpitchedInstrumentsPresentFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1



class ViolinFractionFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1


class WoodwindsFractionFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = ''
        self.description = ''
        self.isSequential = True
        self.dimensions = 1

 








#-------------------------------------------------------------------------------
class Test(unittest.TestCase):
    
    def runTest(self):
        pass




if __name__ == "__main__":
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof




