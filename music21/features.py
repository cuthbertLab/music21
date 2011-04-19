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

        # data storage; possibly use numpy array
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

        self.name = 'Basic Pitch Histogram'
        self.description = 'A features array with bins corresponding to the values of the basic pitch histogram.'
        self.isSequential = True
        self.dimensions = 128

 
class BeatHistogramFeature(FeatureExtractor):
    '''A feature exractor that finds a feature array with entries corresponding to the frequency values of each of the bins of the beat histogram (except the first 40 empty ones).

    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Beat Histogram'
        self.description = 'A feature array with entries corresponding to the frequency values of each of the bins of the beat histogram (except the first 40 empty ones).'
        self.isSequential = True
        self.dimensions = 161

  
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

        self.name = 'Fifths Pitch Histogram'
        self.description = 'A feature array with bins corresponding to the values of the 5ths pitch class histogram.'
        self.isSequential = True
        self.dimensions = 12

 
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

        self.name = 'Initial Time Signature'
        self.description = 'A feature array with two elements. The first is the numerator of the first occurring time signature and the second is the denominator of the first occurring time signature. Both are set to 0 if no time signature is present.'
        self.isSequential = True
        self.dimensions = 2


 
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

        self.name = 'Maximum Number of Independent Voices'
        self.description = 'Maximum number of different channels in which notes have sounded simultaneously.'
        self.isSequential = True
        self.dimensions = 1


 
class MelodicFifthsFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Melodic Fifths'
        self.description = 'Fraction of melodic intervals that are perfect fifths.'
        self.isSequential = True
        self.dimensions = 1

 
class MelodicIntervalHistogramFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
        self.name = 'Melodic Interval Histogram'
        self.description = 'A features array with bins corresponding to the values of the melodic interval histogram.'
        self.isSequential = True
        self.dimensions = 128


class MelodicIntervalsInLowestLineFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
        self.name = 'Melodic Intervals in Lowest Line'
        self.description = 'Average melodic interval in semitones of the channel with the lowest average pitch divided by the average melodic interval of all channels that contain at least two notes.'
        self.isSequential = True
        self.dimensions = 1


class MelodicOctavesFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Melodic Octaves'
        self.description = 'Fraction of melodic intervals that are octaves.'
        self.isSequential = True
        self.dimensions = 1


 
class MelodicThirdsFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Melodic Thirds'
        self.description = 'Fraction of melodic intervals that are major or minor thirds.'
        self.isSequential = True
        self.dimensions = 1


 
class MelodicTritonesFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Melodic Tritones'
        self.description = 'Fraction of melodic intervals that are tritones.'
        self.isSequential = True
        self.dimensions = 1


 
class MinimumNoteDurationFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
        self.name = 'Minimum Note Duration'
        self.description = 'Duration of the shortest note (in seconds).'
        self.isSequential = True
        self.dimensions = 1


class MostCommonMelodicIntervalFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Most Common Melodic Interval'
        self.description = 'Melodic interval with the highest frequency.'
        self.isSequential = True
        self.dimensions = 1


 
class MostCommonMelodicIntervalPrevalenceFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Most Common Melodic Interval Prevalence'
        self.description = 'Fraction of melodic intervals that belong to the most common interval.'
        self.isSequential = True
        self.dimensions = 1


 
class MostCommonPitchClassFeature(FeatureExtractor):
    '''A feature exractor that finds the bin label of the most common pitch class.

    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Most Common Pitch Class'
        self.description = 'Bin label of the most common pitch class.'
        self.isSequential = True
        self.dimensions = 1
        

 
class MostCommonPitchClassPrevalenceFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Most Common Pitch Class Prevalence'
        self.description = 'Fraction of Note Ons corresponding to the most common pitch class.'
        self.isSequential = True
        self.dimensions = 1


 
class MostCommonPitchFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
        self.name = 'Most Common Pitch'
        self.description = 'Bin label of the most common pitch divided by the number of possible pitches.'
        self.isSequential = True
        self.dimensions = 1


class MostCommonPitchPrevalenceFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
        self.name = 'Most Common Pitch Prevalence'
        self.description = 'Fraction of Note Ons corresponding to the most common pitch.'
        self.isSequential = True
        self.dimensions = 1


class NoteDensityFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Note Density'
        self.description = 'Average number of notes per second.'
        self.isSequential = True
        self.dimensions = 1

 
class NotePrevalenceOfPitchedInstrumentsFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Note Prevalence of Pitched Instruments'
        self.description = 'The fraction of (pitched) notes played by each General MIDI Instrument. There is one entry for each instrument, which is set to the number of Note Ons played using the corresponding MIDI patch divided by the total number of Note Ons in the recording.'
        self.isSequential = True
        self.dimensions = 128
 

class NotePrevalenceOfUnpitchedInstrumentsFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Note Prevalence of Unpitched Instruments'
        self.description = 'The fraction of (unpitched) notes played by each General MIDI Percussion Key Map Instrument. There is one entry for each instrument, which is set to the number of Note Ons played using the corresponding MIDI note value divided by the total number of Note Ons in the recording. It should be noted that only instruments 35 to 81 are included here, as they are the ones that meet the official standard. They are numbered in this array from 0 to 46.'
        self.isSequential = True
        self.dimensions = 47


 
class NumberOfCommonMelodicIntervalsFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Number of Common Melodic Intervals'
        self.description = 'Number of melodic intervals that represent at least 9% of all melodic intervals.'
        self.isSequential = True
        self.dimensions = 1



class NumberOfCommonPitchesFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Number of Common Pitches'
        self.description = 'Number of pitches that account individually for at least 9% of all notes.'
        self.isSequential = True
        self.dimensions = 1

 
class NumberOfModeratePulsesFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Number of Moderate Pulses'
        self.description = 'Number of beat peaks with normalized frequencies over 0.01.'
        self.isSequential = True
        self.dimensions = 1


 
class NumberOfRelativelyStrongPulsesFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Number of Relatively Strong Pulses'
        self.description = 'Number of beat peaks with frequencies at least 30% as high as the frequency of the bin with the highest frequency.'
        self.isSequential = True
        self.dimensions = 1

 
class NumberOfStrongPulsesFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Number of Strong Pulses'
        self.description = 'Number of beat peaks with normalized frequencies over 0.1.'
        self.isSequential = True
        self.dimensions = 1

 
class OverallDynamicRangeFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Overall Dynamic Range'
        self.description = 'The maximum loudness minus the minimum loudness value.'
        self.isSequential = True
        self.dimensions = 1



 
class PitchClassDistributionFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Pitch Class Distribution'
        self.description = 'A feature array with 12 entries where the first holds the frequency of the bin of the pitch class histogram with the highest frequency, and the following entries holding the successive bins of the histogram, wrapping around if necessary.'
        self.isSequential = True
        self.dimensions = 12

 
class PitchClassVarietyFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Pitch Class Variety'
        self.description = 'Number of pitch classes used at least once.'
        self.isSequential = True
        self.dimensions = 1


 


 
class PitchVarietyFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Pitch Variety'
        self.description = 'Number of pitches used at least once.'
        self.isSequential = True
        self.dimensions = 1


 
class PolyrhythmsFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Polyrhythms'
        self.description = 'Number of beat peaks with frequencies at least 30% of the highest frequency whose bin labels are not integer multiples or factors (using only multipliers of 1, 2, 3, 4, 6 and 8) (with an accepted error of +/- 3 bins) of the bin label of the peak with the highest frequency. This number is then divided by the total number of beat bins with frequencies over 30% of the highest frequency.'
        self.isSequential = True
        self.dimensions = 1

 
class PrimaryRegisterFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
        self.name = 'Primary Register'
        self.description = 'Average MIDI pitch.'
        self.isSequential = True
        self.dimensions = 1


class QualityFeature(FeatureExtractor):
    '''A feature exractor that sets the feature to 0 if the key signature indicates that a recording is major, set to 1 if it indicates that it is minor and set to 0 if key signature is unknown.

    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Quality'
        self.description = 'Set to 0 if the key signature indicates that a recording is major, set to 1 if it indicates that it is minor and set to 0 if key signature is unknown.'
        self.isSequential = True
        self.dimensions = 1

 
class QuintupleMeterFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Quintuple Meter'
        self.description = 'Set to 1 if numerator of initial time signature is 5, set to 0 otherwise.'
        self.isSequential = True
        self.dimensions = 1


 
class RangeFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Range'
        self.description = 'Difference between highest and lowest pitches.'
        self.isSequential = True
        self.dimensions = 1


 
class RangeOfHighestLineFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Range of Highest Line'
        self.description = 'Difference between the highest note and the lowest note played in the channel with the highest average pitch divided by the difference between the highest note and the lowest note in the piece.'
        self.isSequential = True
        self.dimensions = 1


 
class RelativeNoteDensityOfHighestLineFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Relative Note Density of Highest Line'
        self.description = 'Number of Note Ons in the channel with the highest average pitch divided by the average number of Note Ons in all channels that contain at least one note.'
        self.isSequential = True
        self.dimensions = 1


 
class RelativeRangeOfLoudestVoiceFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Relative Range of Loudest Voice'
        self.description = 'Difference between the highest note and the lowest note played in the channel with the highest average loudness divided by the difference between the highest note and the lowest note overall in the piece.'
        self.isSequential = True
        self.dimensions = 1


 
class RelativeStrengthOfMostCommonIntervalsFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Relative Strength of Most Common Intervals'
        self.description = 'Fraction of melodic intervals that belong to the second most common interval divided by the fraction of melodic intervals belonging to the most common interval.'
        self.isSequential = True
        self.dimensions = 1


 
class RelativeStrengthOfTopPitchClassesFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
        self.name = 'Relative Strength of Top Pitch Classes'
        self.description = 'The frequency of the 2nd most common pitch class divided by the frequency of the most common pitch class.'
        self.isSequential = True
        self.dimensions = 1


class RelativeStrengthOfTopPitchesFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Relative Strength of Top Pitches'
        self.description = 'The frequency of the 2nd most common pitch divided by the frequency of the most common pitch.'
        self.isSequential = True
        self.dimensions = 1


 
class RepeatedNotesFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
        self.name = 'Repeated Notes'
        self.description = 'Fraction of notes that are repeated melodically.'
        self.isSequential = True
        self.dimensions = 1


class RhythmicLoosenessFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Rhythmic Looseness'
        self.description = 'Average width of beat histogram peaks (in beats per minute). Width is measured for all peaks with frequencies at least 30% as high as the highest peak, and is defined by the distance between the points on the peak in question that are 30% of the height of the peak.'
        self.isSequential = True
        self.dimensions = 1

 
class RhythmicVariabilityFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Rhythmic Variability'
        self.description = 'Standard deviation of the bin values (except the first 40 empty ones).'
        self.isSequential = True
        self.dimensions = 1

 

 
class SecondStrongestRhythmicPulseFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
        self.name = 'Second Strongest Rhythmic Pulse'
        self.description = 'Bin label of the beat bin of the peak with the second highest frequency.'
        self.isSequential = True
        self.dimensions = 1


class SizeOfMelodicArcsFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Size of Melodic Arcs'
        self.description = 'Average melodic interval separating the top note of melodic peaks and the bottom note of melodic troughs.'
        self.isSequential = True
        self.dimensions = 1

 
class StaccatoIncidenceFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Staccato Incidence'
        self.description = 'Number of notes with durations of less than a 10th of a second divided by the total number of notes in the recording.'
        self.isSequential = True
        self.dimensions = 1


 
class StepwiseMotionFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
        self.name = 'Stepwise Motion'
        self.description = 'Fraction of melodic intervals that corresponded to a minor or major second.'
        self.isSequential = True
        self.dimensions = 1


class StrengthOfSecondStrongestRhythmicPulseFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
        self.name = 'Strength of Second Strongest Rhythmic Pulse'
        self.description = 'Frequency of the beat bin of the peak with the second highest frequency.'
        self.isSequential = True
        self.dimensions = 1


class StrengthOfStrongestRhythmicPulseFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Strength of Strongest Rhythmic Pulse'
        self.description = 'Frequency of the beat bin with the highest frequency.'
        self.isSequential = True
        self.dimensions = 1

 
class StrengthRatioOfTwoStrongestRhythmicPulsesFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Strength Ratio of Two Strongest Rhythmic Pulses'
        self.description = 'The frequency of the higher (in terms of frequency) of the two beat bins corresponding to the peaks with the highest frequency divided by the frequency of the lower.'
        self.isSequential = True
        self.dimensions = 1


 
class StrongestRhythmicPulseFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Strongest Rhythmic Pulse'
        self.description = 'Bin label of the beat bin with the highest frequency.'
        self.isSequential = True
        self.dimensions = 1

 
class StrongTonalCentresFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Strong Tonal Centres'
        self.description = 'Number of peaks in the fifths pitch histogram that each account for at least 9% of all Note Ons.'
        self.isSequential = True
        self.dimensions = 1


 
class TimePrevalenceOfPitchedInstrumentsFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
        self.name = 'Time Prevalence of Pitched Instruments'
        self.description = 'The fraction of the total time of the recording in which a note was sounding for each (pitched) General MIDI Instrument. There is one entry for each instrument, which is set to the total time in seconds during which a given instrument was sounding one or more notes divided by the total length in seconds of the piece.'
        self.isSequential = True
        self.dimensions = 128


class TripleMeterFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Triple Meter'
        self.description = 'Set to 1 if numerator of initial time signature is 3, set to 0 otherwise.'
        self.isSequential = True
        self.dimensions = 1


 

 
class VariabilityOfNoteDurationFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
        self.name = 'Variability of Note Duration'
        self.description = 'Standard deviation of note durations in seconds.'
        self.isSequential = True
        self.dimensions = 1


class VariabilityOfNotePrevalenceOfPitchedInstrumentsFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
        self.name = 'Variability of Note Prevalence of Pitched Instruments'
        self.description = 'Standard deviation of the fraction of Note Ons played by each (pitched) General MIDI instrument that is used to play at least one note.'
        self.isSequential = True
        self.dimensions = 1


class VariabilityOfNotePrevalenceOfUnpitchedInstrumentsFeature(
    FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Variability of Note Prevalence of Unpitched Instruments'
        self.description = 'Standard deviation of the fraction of Note Ons played by each (unpitched) MIDI Percussion Key Map instrument that is used to play at least one note. It should be noted that only instruments 35 to 81 are included here, as they are the ones that are included in the official standard.'
        self.isSequential = True
        self.dimensions = 1

 
class VariabilityOfNumberOfIndependentVoicesFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Variability of Number of Independent Voices'
        self.description = 'Standard deviation of number of different channels in which notes have sounded simultaneously. Rests are not included in this calculation.'
        self.isSequential = True
        self.dimensions = 1


 
class VariabilityOfTimeBetweenAttacksFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
        self.name = 'Variability of Time Between Attacks'
        self.description = 'Standard deviation of the times, in seconds, between Note On events (regardless of channel).'
        self.isSequential = True
        self.dimensions = 1


class VariationOfDynamicsFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Variation of Dynamics'
        self.description = 'Standard deviation of loudness levels of all notes.'
        self.isSequential = True
        self.dimensions = 1


 
class VariationOfDynamicsInEachVoiceFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Variation of Dynamics In Each Voice'
        self.description = 'The average of the standard deviations of loudness levels within each channel that contains at least one note.'
        self.isSequential = True
        self.dimensions = 1

 
class VibratoPrevalenceFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Vibrato Prevalence'
        self.description = 'Number of notes for which Pitch Bend messages change direction at least twice divided by total number of notes that have Pitch Bend messages associated with them.'
        self.isSequential = True
        self.dimensions = 1


 
class VoiceEqualityDynamicsFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
        self.name = 'Voice Equality - Dynamics'
        self.description = 'Standard deviation of the average volume of notes in each channel that contains at least one note.'
        self.isSequential = True
        self.dimensions = 1


class VoiceEqualityMelodicLeapsFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
        self.name = 'Voice Equality - Melodic Leaps'
        self.description = 'Standard deviation of the average melodic leap in MIDI pitches for each channel that contains at least one note.'
        self.isSequential = True
        self.dimensions = 1


class VoiceEqualityNoteDurationFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
        self.name = 'Voice Equality - Note Duration'
        self.description = 'Standard deviation of the total duration of notes in seconds in each channel that contains at least one note.'
        self.isSequential = True
        self.dimensions = 1


class VoiceEqualityNumberOfNotesFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
        self.name = 'Voice Equality - Number of Notes'
        self.description = 'Standard deviation of the total number of Note Ons in each channel that contains at least one note.'
        self.isSequential = True
        self.dimensions = 1


class VoiceEqualityRangeFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
        self.name = 'Voice Equality - Range'
        self.description = 'Standard deviation of the differences between the highest and lowest pitches in each channel that contains at least one note.'
        self.isSequential = True
        self.dimensions = 1


class VoiceSeparationFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)
 
        self.name = 'Voice Separation'
        self.description = 'Average separation in semi-tones between the average pitches of consecutive channels (after sorting based/non average pitch) that contain at least one note.'
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

        self.name = 'Number of Pitched Instruments'
        self.description = 'Total number of General MIDI patches that are used to play at least one note.'
        self.isSequential = True
        self.dimensions = 1


class NumberOfUnpitchedInstrumentsFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Number of Unpitched Instruments'
        self.description = 'Number of distinct MIDI Percussion Key Map patches that were used to play at least one note. It should be noted that only instruments 35 to 81 are included here, as they are the ones that are included in the official standard.'
        self.isSequential = True
        self.dimensions = 1



class OrchestralStringsFractionFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Orchestral Strings Fraction'
        self.description = 'Fraction of all Note Ons belonging to orchestral strings patches(General MIDI patches 41 or 47).'
        self.isSequential = True
        self.dimensions = 1



class PercussionPrevalenceFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Percussion Prevalence'
        self.description = 'Total number of Note Ons corresponding to unpitched percussion instruments divided by total number of Note Ons in the recording.'
        self.isSequential = True
        self.dimensions = 1


class SaxophoneFractionFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Saxophone Fraction'
        self.description = 'Fraction of all Note Ons belonging to saxophone patches (GeneralMIDI patches 65 or 68).'
        self.isSequential = True
        self.dimensions = 1


class StringEnsembleFractionFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'String Ensemble Fraction'
        self.description = 'Fraction of all Note Ons belonging to string ensemble patches(General MIDI patches 49 to 52).'
        self.isSequential = True
        self.dimensions = 1



class StringKeyboardFractionFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'String Keyboard Fraction'
        self.description = 'Fraction of all Note Ons belonging to string keyboard patches (GeneralMIDI patches 1 to 8).'
        self.isSequential = True
        self.dimensions = 1


class UnpitchedInstrumentsPresentFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Unpitched Instruments Present'
        self.description = 'Which unpitched MIDI Percussion Key Map instruments are present. There is one entry for each instrument, which is set to 1.0 if there is at least one Note On in the recording corresponding to the instrument and to 0.0 if there is not. It should be noted that only instruments 35 to 81 are included here, as they are the ones that meet the official standard. They are numbered in this array from 0 to 46.'
        self.isSequential = True
        self.dimensions = 47


class PitchedInstrumentsPresentFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)


        self.name = 'Pitched Instruments Present'
        self.description = 'Which pitched General MIDI Instruments are present. There is one entry for each instrument, which is set to 1.0 if there is at least one Note On in the recording corresponding to the instrument and to 0.0 if there is not.'
        self.isSequential = True
        self.dimensions = 128


class ViolinFractionFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Violin Fraction'
        self.description = 'Fraction of all Note Ons belonging to violin patches (GeneralMIDI patches 41 or 111).'
        self.isSequential = True
        self.dimensions = 1


class WoodwindsFractionFeature(FeatureExtractor):
    '''
    >>> from music21 import *
    '''
    def __init__(self, streamObj, *arguments, **keywords):
        FeatureExtractor.__init__(self, streamObj,  *arguments, **keywords)

        self.name = 'Woodwinds Fraction'
        self.description = 'Fraction of all Note Ons belonging to woodwind patches (GeneralMIDI patches 69 or 76).'
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




