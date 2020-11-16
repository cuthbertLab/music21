# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         features.jSymbolic.py
# Purpose:      music21 functions for simple feature extraction
#
# Authors:      Christopher Ariza
#
# Copyright:    Copyright © 2011 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
The features implemented here are based on those found in jSymbolic and
defined in Cory McKay's MA Thesis, "Automatic Genre Classification of MIDI Recordings"

The LGPL jSymbolic system can be found here: http://jmir.sourceforge.net/jSymbolic.html
'''
import copy
import math
import statistics
import unittest
from collections import OrderedDict

from music21 import common
from music21 import base
# from music21 import exceptions21
from music21.features import base as featuresModule

from music21 import environment
_MOD = 'features.jSymbolic'
environLocal = environment.Environment(_MOD)


# ------------------------------------------------------------------------------
# 112 feature extractors


# ------------------------------------------------------------------------------
# melody

class MelodicIntervalHistogramFeature(featuresModule.FeatureExtractor):
    '''
    A features array with bins corresponding to the values of the melodic interval histogram.

    128 dimensions

    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.MelodicIntervalHistogramFeature(s)
    >>> f = fe.extract()
    >>> f.vector[0:5]
    [0.144..., 0.220..., 0.364..., 0.062..., 0.050...]
    '''
    id = 'M1'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Melodic Interval Histogram'
        self.description = ('A features array with bins corresponding to '
                            'the values of the melodic interval histogram.')
        self.isSequential = True
        self.dimensions = 128
        self.normalize = True

    def process(self):
        '''Do processing necessary, storing result in feature.
        '''
        for i, value in enumerate(self.data['midiIntervalHistogram']):
            self.feature.vector[i] = value


class AverageMelodicIntervalFeature(featuresModule.FeatureExtractor):
    '''
    Average melodic interval (in semitones).

    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.AverageMelodicIntervalFeature(s)
    >>> f = fe.extract()
    >>> f.vector
    [2.44...]
    '''
    id = 'M2'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Average Melodic Interval'
        self.description = 'Average melodic interval (in semitones).'
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        '''Do processing necessary, storing result in feature.
        '''
        values = []
        # already summed by part if parts exist
        histo = self.data['midiIntervalHistogram']
        for i, value in enumerate(histo):
            for j in range(value):
                values.append(i)
        if not values:
            raise JSymbolicFeatureException('input lacks notes')
        self.feature.vector[0] = sum(values) / float(len(values))


class MostCommonMelodicIntervalFeature(featuresModule.FeatureExtractor):
    '''

    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.MostCommonMelodicIntervalFeature(s)
    >>> f = fe.extract()
    >>> f.vector
    [2]
    '''
    id = 'M3'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Most Common Melodic Interval'
        self.description = 'Melodic interval with the highest frequency.'
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        '''Do processing necessary, storing result in feature.
        '''
        # already summed by part if parts exist
        histo = self.data['midiIntervalHistogram']
        maxValue = max(histo)
        maxIndex = histo.index(maxValue)
        self.feature.vector[0] = maxIndex


class DistanceBetweenMostCommonMelodicIntervalsFeature(
        featuresModule.FeatureExtractor):
    '''

    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.DistanceBetweenMostCommonMelodicIntervalsFeature(s)
    >>> f = fe.extract()
    >>> f.vector
    [1]
    '''
    id = 'M4'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Distance Between Most Common Melodic Intervals'
        self.description = ('Absolute value of the difference between the '
                            'most common melodic interval and the second most '
                            'common melodic interval.')
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        '''Do processing necessary, storing result in feature.
        '''
        # copy b/c will manipulate
        histo = copy.deepcopy(self.data['midiIntervalHistogram'])
        maxValue = max(histo)
        maxIndex = histo.index(maxValue)
        histo[maxIndex] = 0  # set to zero
        secondValue = max(histo)
        secondIndex = histo.index(secondValue)

        self.feature.vector[0] = abs(maxIndex - secondIndex)


class MostCommonMelodicIntervalPrevalenceFeature(
        featuresModule.FeatureExtractor):
    '''
    Fraction of melodic intervals that belong to the most common interval.

    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.MostCommonMelodicIntervalPrevalenceFeature(s)
    >>> f = fe.extract()
    >>> f.vector
    [0.364...]
    '''
    id = 'M5'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Most Common Melodic Interval Prevalence'
        self.description = 'Fraction of melodic intervals that belong to the most common interval.'
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        '''Do processing necessary, storing result in feature.
        '''
        # copy b/c will manipulate
        histo = copy.deepcopy(self.data['midiIntervalHistogram'])
        maxValue = max(histo)
        count = sum(histo)
        if not count:
            raise JSymbolicFeatureException('input lacks notes')
        self.feature.vector[0] = maxValue / float(count)


class RelativeStrengthOfMostCommonIntervalsFeature(
        featuresModule.FeatureExtractor):
    '''

    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.RelativeStrengthOfMostCommonIntervalsFeature(s)
    >>> f = fe.extract()
    >>> f.vector
    [0.603...]
    '''
    id = 'M6'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Relative Strength of Most Common Intervals'
        self.description = ('Fraction of melodic intervals that belong '
                            'to the second most common interval divided by the '
                            'fraction of melodic intervals belonging to the most common interval.')
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        '''Do processing necessary, storing result in feature.
        '''
        # copy b/c will manipulate
        histo = copy.deepcopy(self.data['midiIntervalHistogram'])
        count = sum(histo)
        maxValue = max(histo)
        maxIndex = histo.index(maxValue)
        histo[maxIndex] = 0  # set to zero
        secondValue = max(histo)
        # secondIndex = histo.index(secondValue)
        if not count:
            raise JSymbolicFeatureException('input lacks notes')
        self.feature.vector[0] = (secondValue / float(count)) / (maxValue / float(count))


class NumberOfCommonMelodicIntervalsFeature(featuresModule.FeatureExtractor):
    '''
    Number of melodic intervals that represent at least 9% of all melodic intervals.

    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.NumberOfCommonMelodicIntervalsFeature(s)
    >>> f = fe.extract()
    >>> f.vector
    [3]
    '''
    id = 'M7'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Number of Common Melodic Intervals'
        self.description = ('Number of melodic intervals that represent '
                            'at least 9% of all melodic intervals.')
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        '''Do processing necessary, storing result in feature.
        '''
        histo = self.data['midiIntervalHistogram']
        total = sum(histo)
        if not total:
            raise JSymbolicFeatureException('input lacks notes')
        post = 0
        for i, count in enumerate(histo):
            if count / float(total) >= 0.09:
                post += 1
        self.feature.vector[0] = post


class AmountOfArpeggiationFeature(featuresModule.FeatureExtractor):
    '''
    Fraction of horizontal intervals that are repeated notes, minor thirds, major thirds,
    perfect fifths, minor sevenths, major sevenths, octaves, minor tenths or major tenths.

    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.AmountOfArpeggiationFeature(s)
    >>> f = fe.extract()
    >>> f.name
    'Amount of Arpeggiation'
    >>> f.vector
    [0.333...]
    '''
    id = 'M8'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Amount of Arpeggiation'
        self.description = ('Fraction of horizontal intervals that are repeated notes, '
                            'minor thirds, major thirds, perfect fifths, minor sevenths, '
                            'major sevenths, octaves, minor tenths or major tenths.')
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        '''Do processing necessary, storing result in feature.
        '''
        histo = self.data['midiIntervalHistogram']
        total = sum(histo)
        if total == 0:
            return  # do nothing
        # intervals to look for
        targets = [0, 3, 4, 7, 10, 11, 12, 15, 16]
        total = sum(histo)
        count = 0
        for t in targets:
            count += histo[t]
        if not count:
            raise JSymbolicFeatureException('input lacks notes')
        self.feature.vector[0] = count / float(total)


class RepeatedNotesFeature(featuresModule.FeatureExtractor):
    '''
    Fraction of notes that are repeated melodically

    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.RepeatedNotesFeature(s)
    >>> f = fe.extract()
    >>> f.vector
    [0.144...]
    '''
    id = 'M9'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Repeated Notes'
        self.description = 'Fraction of notes that are repeated melodically.'
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        '''Do processing necessary, storing result in feature.
        '''
        histo = self.data['midiIntervalHistogram']
        total = sum(histo)
        if total == 0:
            return  # do nothing
        # intervals to look for
        targets = [0]
        total = sum(histo)
        if not total:
            raise JSymbolicFeatureException('input lacks notes')
        count = 0
        for t in targets:
            count += histo[t]
        self.feature.vector[0] = count / float(total)


class ChromaticMotionFeature(featuresModule.FeatureExtractor):
    '''
    Fraction of melodic intervals corresponding to a semitone.

    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.ChromaticMotionFeature(s)
    >>> f = fe.extract()
    >>> f.vector
    [0.220...]
    '''
    id = 'm10'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Chromatic Motion'
        self.description = 'Fraction of melodic intervals corresponding to a semi-tone.'
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        '''Do processing necessary, storing result in feature.
        '''
        histo = self.data['midiIntervalHistogram']
        total = sum(histo)
        if not total:
            raise JSymbolicFeatureException('input lacks notes')
        # intervals to look for
        targets = [1]
        count = 0
        for t in targets:
            count += histo[t]
        self.feature.vector[0] = count / float(total)


class StepwiseMotionFeature(featuresModule.FeatureExtractor):
    '''
    Fraction of melodic intervals that corresponded to a minor or major second

    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.StepwiseMotionFeature(s)
    >>> f = fe.extract()
    >>> f.vector
    [0.584...]
    '''
    id = 'M11'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Stepwise Motion'
        self.description = ('Fraction of melodic intervals that corresponded '
                            'to a minor or major second.')
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        '''Do processing necessary, storing result in feature.
        '''
        histo = self.data['midiIntervalHistogram']
        total = sum(histo)
        if not total:
            raise JSymbolicFeatureException('input lacks notes')
        # intervals to look for
        targets = [1, 2]
        count = 0
        for t in targets:
            count += histo[t]
        self.feature.vector[0] = count / float(total)


class MelodicThirdsFeature(featuresModule.FeatureExtractor):
    '''
    Fraction of melodic intervals that are major or minor thirds

    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.MelodicThirdsFeature(s)
    >>> f = fe.extract()
    >>> f.vector
    [0.113...]
    '''
    id = 'M12'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Melodic Thirds'
        self.description = 'Fraction of melodic intervals that are major or minor thirds.'
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        '''Do processing necessary, storing result in feature.
        '''
        histo = self.data['midiIntervalHistogram']
        total = sum(histo)
        if not total:
            raise JSymbolicFeatureException('input lacks notes')
        # intervals to look for
        targets = [3, 4]
        count = 0
        for t in targets:
            count += histo[t]
        self.feature.vector[0] = count / float(total)


class MelodicFifthsFeature(featuresModule.FeatureExtractor):
    '''
    Fraction of melodic intervals that are perfect fifths

    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.MelodicFifthsFeature(s)
    >>> f = fe.extract()
    >>> f.vector
    [0.056...]
    '''
    id = 'M13'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Melodic Fifths'
        self.description = 'Fraction of melodic intervals that are perfect fifths.'
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        '''Do processing necessary, storing result in feature.
        '''
        histo = self.data['midiIntervalHistogram']
        total = sum(histo)
        if not total:
            raise JSymbolicFeatureException('input lacks notes')
        # intervals to look for
        targets = [7]
        count = 0
        for t in targets:
            count += histo[t]
        self.feature.vector[0] = count / float(total)


class MelodicTritonesFeature(featuresModule.FeatureExtractor):
    '''
    Fraction of melodic intervals that are tritones

    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.MelodicTritonesFeature(s)
    >>> f = fe.extract()
    >>> f.vector
    [0.012...]
    '''
    id = 'M14'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Melodic Tritones'
        self.description = 'Fraction of melodic intervals that are tritones.'
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        '''Do processing necessary, storing result in feature.
        '''
        histo = self.data['midiIntervalHistogram']
        total = sum(histo)
        if not total:
            raise JSymbolicFeatureException('input lacks notes')
        # intervals to look for
        targets = [6]
        count = 0
        for t in targets:
            count += histo[t]
        self.feature.vector[0] = count / float(total)


class MelodicOctavesFeature(featuresModule.FeatureExtractor):
    '''
    Fraction of melodic intervals that are octaves

    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.MelodicOctavesFeature(s)
    >>> f = fe.extract()
    >>> f.vector
    [0.018...]
    '''
    id = 'M15'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Melodic Octaves'
        self.description = 'Fraction of melodic intervals that are octaves.'
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        '''Do processing necessary, storing result in feature.
        '''
        histo = self.data['midiIntervalHistogram']
        total = sum(histo)
        if not total:
            raise JSymbolicFeatureException('input lacks notes')
        # intervals to look for
        targets = [12, 24, 48, 60, 72, 84, 96, 108, 120]
        count = 0
        for t in targets:
            count += histo[t]
        self.feature.vector[0] = count / float(total)


class DirectionOfMotionFeature(featuresModule.FeatureExtractor):
    '''
    Returns the fraction of melodic intervals that are rising rather than falling.
    Unisons are omitted.

    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.DirectionOfMotionFeature(s)
    >>> f = fe.extract()
    >>> f.vector
    [0.470...]
    '''
    id = 'm17'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Direction of Motion'
        self.description = 'Fraction of melodic intervals that are rising rather than falling.'
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        '''Do processing necessary, storing result in feature.
        '''
        rising = 0
        falling = 0
        cBundle = []
        if self.data.partsCount > 0:
            for i in range(self.data.partsCount):
                cList = self.data['parts'][i]['contourList']
                cBundle.append(cList)
        else:
            cList = self.data['contourList']
            cBundle.append(cList)

        for cList in cBundle:
            for c in cList:
                if c > 0:
                    rising += 1
                elif c < 0:
                    falling += 1
        if not (falling or rising):
            raise JSymbolicFeatureException('input lacks notes')
        self.feature.vector[0] = rising / float(falling + rising)


class DurationOfMelodicArcsFeature(featuresModule.FeatureExtractor):
    '''
    Average number of notes that separate melodic peaks and troughs
    in any part. This is calculated as the total number of intervals
    (not counting unisons) divided by the number of times the melody
    changes direction.

    Example: C D E D C E D C C
    Intervals: [0] 2 2 -2 -2 2 2 -4 0
    Changes direction (equivalent to +/- sign) three times.
    There are seven non-unison (nonzero) intervals.
    Thus the duration of arcs is 7/3 ~= 2.333...
    >>> s = converter.parse("tinyNotation: c' d' e' d' c' d' e'2 c'2 c'2")
    >>> fe = features.jSymbolic.DurationOfMelodicArcsFeature(s)
    >>> fe.extract().vector
    [2.333...]

    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.DurationOfMelodicArcsFeature(s)
    >>> fe.extract().vector
    [1.74...]
    '''
    id = 'M18'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Duration of Melodic Arcs'
        self.description = ('Average number of notes that separate melodic '
                            'peaks and troughs in any part. This is calculated as the '
                            'total number of intervals (not counting unisons) divided '
                            'by the number of times the melody changes direction.')
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        '''Do processing necessary, storing result in feature.
        '''
        # `cList` contains a list of melodic intervals in a part.
        # For example, C4 E4 G4 E4 C4 results in a cList of [4, 3, -3, -4].
        # Each part is encoded in a separate cList; cBundle contains all
        # the cList arrays.
        cBundle = []
        if self.data.partsCount > 0:
            for i in range(self.data.partsCount):
                cList = self.data['parts'][i]['contourList']
                cBundle.append(cList)
        else:
            cList = self.data['contourList']
            cBundle.append(cList)

        direction_changes = 0
        nonUnison_intervals = 0
        # For each part, count how many times the direction changes
        # by looking at the sign of the interval.
        ASCENDING = 1
        DESCENDING = -1
        STATIONARY = 0
        for cList in cBundle:
            current_direction = STATIONARY
            for interval in cList:
                if interval != 0:
                    nonUnison_intervals += 1
                if current_direction == ASCENDING:
                    if interval < 0:
                        direction_changes += 1
                        current_direction = DESCENDING
                elif current_direction == DESCENDING:
                    if interval > 0:
                        direction_changes += 1
                        current_direction = ASCENDING
                else:  # if we begin stationary
                    if interval > 0:
                        current_direction = ASCENDING
                    elif interval < 0:
                        current_direction = DESCENDING
        # Duration of melodic arcs is 0 if it never changes direction
        if direction_changes == 0:
            duration_of_melodic_arcs = 0
        else:
            duration_of_melodic_arcs = nonUnison_intervals / direction_changes
        self.feature.vector[0] = duration_of_melodic_arcs


class SizeOfMelodicArcsFeature(featuresModule.FeatureExtractor):
    '''
    Average span (in semitones) between melodic peaks and troughs
    in any part. Each time the melody changes direction begins a
    new arc. The average size of melodic arcs is defined as the
    total size of melodic intervals between changes of directions -
    or between the start of the melody and the first change of
    direction - divided by the number of direction changes.

    Example: C D E D C E D C C
    Intervals: [0] 2 2 -2 -2 2 2 -4 0
    Changes direction (equivalent to +/- sign) three times.
    The total sum of interval distance up to the last change
    of direction is 12. We don't count the last interval,
    the descending major third, because it is not between
    changes of direction.
    Thus the average size of melodic arcs is 12/3 = 4.
    >>> s = converter.parse("tinyNotation: c' d' e' d' c' d' e'2 c'2 c'2")
    >>> fe = features.jSymbolic.SizeOfMelodicArcsFeature(s)
    >>> fe.extract().vector
    [4.0]

    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.SizeOfMelodicArcsFeature(s)
    >>> fe.extract().vector
    [4.84...]
    '''
    id = 'M19'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Size of Melodic Arcs'
        self.description = ('Average span (in semitones) between melodic peaks '
                            'and troughs in any part. Each time the melody changes '
                            'direction begins a new arc. The average size of'
                            'melodic arcs is defined as the total size of melodic'
                            'intervals between changes of directions - or between'
                            'the start of the melody and the first change of'
                            'direction - divided by the number of direction changes.')
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        '''Do processing necessary, storing result in feature.
        '''
        # `cList` contains a list of melodic intervals in a part.
        # For example, C4 E4 G4 E4 C4 results in a cList of [4, 3, -3, -4].
        # Each part is encoded in a separate cList; cBundle contains all
        # the cList arrays.
        cBundle = []
        if self.data.partsCount > 0:
            for i in range(self.data.partsCount):
                cList = self.data['parts'][i]['contourList']
                cBundle.append(cList)
        else:
            cList = self.data['contourList']
            cBundle.append(cList)

        direction_changes = 0
        sum_of_intervals = 0
        # For each part, count how many times the direction changes
        # by looking at the sign of the interval.
        ASCENDING = 1
        DESCENDING = -1
        STATIONARY = 0
        for cList in cBundle:
            current_direction = STATIONARY
            this_arc_interval = 0
            for interval in cList:
                if current_direction == ASCENDING:
                    if interval > 0:
                        this_arc_interval += abs(interval)
                    elif interval < 0:
                        # total interval before the change gets added
                        sum_of_intervals += this_arc_interval
                        direction_changes += 1
                        current_direction = DESCENDING
                        # start fresh with the new arc on this interval
                        this_arc_interval = abs(interval)
                elif current_direction == DESCENDING:
                    if interval < 0:
                        this_arc_interval += abs(interval)
                    elif interval > 0:
                        # total interval before the change gets added
                        sum_of_intervals += this_arc_interval
                        direction_changes += 1
                        current_direction = ASCENDING
                        # start fresh with the new arc on this interval
                        this_arc_interval = abs(interval)
                else:  # if we begin stationary
                    if interval > 0:
                        current_direction = ASCENDING
                        this_arc_interval += abs(interval)
                    elif interval < 0:
                        current_direction = DESCENDING
                        this_arc_interval += abs(interval)

        # If it never changes direction, the size of melodic arcs is defined to be 0
        if direction_changes == 0:
            size_of_melodic_arcs = 0
        else:
            size_of_melodic_arcs = sum_of_intervals / direction_changes
        self.feature.vector[0] = size_of_melodic_arcs


# ------------------------------------------------------------------------------
# pitch


class MostCommonPitchPrevalenceFeature(featuresModule.FeatureExtractor):
    '''
    Fraction of Notes corresponding to the most common pitch.

    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.MostCommonPitchPrevalenceFeature(s)
    >>> fe.extract().vector[0]
    0.116...
    '''
    id = 'P1'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Most Common Pitch Prevalence'
        self.description = 'Fraction of Note Ons corresponding to the most common pitch.'
        self.isSequential = True
        self.dimensions = 1
        self.discrete = False

    def process(self):
        '''Do processing necessary, storing result in feature.
        '''
        histo = self.data['pitches.midiPitchHistogram']
        if not histo:
            raise JSymbolicFeatureException('input lacks notes')
        # if a tie this will return the first
        # if all zeros will return zero
        pcMax = max(histo.values())
        pcCount = sum(histo.values())
        # the number of the max divided by total for all
        self.feature.vector[0] = pcMax / float(pcCount)


class MostCommonPitchClassPrevalenceFeature(featuresModule.FeatureExtractor):
    '''
    Fraction of Notes corresponding to the most common pitch class.

    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.MostCommonPitchClassPrevalenceFeature(s)
    >>> fe.extract().vector
    [0.196...]
    '''
    id = 'P2'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Most Common Pitch Class Prevalence'
        self.description = 'Fraction of Note Ons corresponding to the most common pitch class.'
        self.isSequential = True
        self.dimensions = 1
        self.discrete = False

    def process(self):
        '''Do processing necessary, storing result in feature.
        '''
        histo = self.data['pitches.pitchClassHistogram']
        # if a tie this will return the first
        # if all zeros will return zero
        pc = histo.index(max(histo))
        pcCount = sum(histo)
        if not pcCount:
            raise JSymbolicFeatureException('input lacks notes')
        # the number of the max divided by total for all
        self.feature.vector[0] = histo[pc] / float(pcCount)


class RelativeStrengthOfTopPitchesFeature(featuresModule.FeatureExtractor):
    '''
    The frequency of the 2nd most common pitch divided by the frequency of the most common pitch.

    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.RelativeStrengthOfTopPitchesFeature(s)
    >>> fe.extract().vector
    [0.947...]
    '''
    id = 'P3'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Relative Strength of Top Pitches'
        self.description = ('The frequency of the 2nd most common pitch '
                            'divided by the frequency of the most common pitch.')
        self.isSequential = True
        self.dimensions = 1
        self.discrete = False

    def process(self):
        '''Do processing necessary, storing result in feature.
        '''
        histo = self.data['pitches.midiPitchHistogram']
        # if a tie this will return the first
        # if all zeros will return zero
        try:
            pMax, pSecond = histo.most_common(2)[:2]  # need [:2] in case of ties
            self.feature.vector[0] = float(pSecond[1] / pMax[1])
        except ZeroDivisionError:
            raise JSymbolicFeatureException('input lacks notes')
        except (IndexError, ValueError):
            self.feature.vector[0] = 0.0


class RelativeStrengthOfTopPitchClassesFeature(featuresModule.FeatureExtractor):
    '''

    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.RelativeStrengthOfTopPitchClassesFeature(s)
    >>> fe.extract().vector
    [0.906...]
    '''
    id = 'P4'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Relative Strength of Top Pitch Classes'
        self.description = ('The frequency of the 2nd most common pitch class '
                            'divided by the frequency of the most common pitch class.')
        self.isSequential = True
        self.dimensions = 1
        self.discrete = False

    def process(self):
        '''Do processing necessary, storing result in feature.
        '''
        # copy b/c will edit
        histo = copy.deepcopy(self.data['pitches.pitchClassHistogram'])
        # if a tie this will return the first
        # if all zeros will return zero
        pIndexMax = histo.index(max(histo))
        pCountMax = histo[pIndexMax]
        if not pCountMax:
            raise JSymbolicFeatureException('input lacks notes')
        # set that position to zero and find next max
        histo[pIndexMax] = 0
        pIndexSecond = histo.index(max(histo))
        pCountSecond = histo[pIndexSecond]
        # the number of the max divided by total for all
        self.feature.vector[0] = pCountSecond / float(pCountMax)


class IntervalBetweenStrongestPitchesFeature(featuresModule.FeatureExtractor):
    '''
    Absolute value of the difference between the pitches of the two most common MIDI pitches.

    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.IntervalBetweenStrongestPitchesFeature(s)
    >>> fe.extract().vector
    [5]
    '''
    id = 'P5'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Interval Between Strongest Pitches'
        self.description = ('Absolute value of the difference between '
                            'the pitches of the two most common MIDI pitches.')
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        '''Do processing necessary, storing result in feature.
        '''
        histo = self.data['pitches.midiPitchHistogram']
        # if a tie this will return the first
        # if all zeros will return zero
        try:
            pMax, pSecond = histo.most_common(2)[:2]  # need [:2] in case of ties
            self.feature.vector[0] = abs(pSecond[0] - pMax[0])

        except (IndexError, ValueError):
            self.feature.vector[0] = 0.0


class IntervalBetweenStrongestPitchClassesFeature(
        featuresModule.FeatureExtractor):
    '''

    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.IntervalBetweenStrongestPitchClassesFeature(s)
    >>> fe.extract().vector
    [5]
    '''
    id = 'P6'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Interval Between Strongest Pitch Classes'
        self.description = ('Absolute value of the difference between the pitch '
                            'classes of the two most common MIDI pitch classes.')
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        '''Do processing necessary, storing result in feature.
        '''
        histo = copy.deepcopy(self.data['pitches.pitchClassHistogram'])
        # if a tie this will return the first
        # if all zeros will return zero
        pIndexMax = histo.index(max(histo))
        # set that position to zero and find next max
        histo[pIndexMax] = 0
        pIndexSecond = histo.index(max(histo))

        # the number of the max divided by total for all
        self.feature.vector[0] = abs(pIndexMax - pIndexSecond)


class NumberOfCommonPitchesFeature(featuresModule.FeatureExtractor):
    '''
    Number of pitches that account individually for at least 9% of all notes.

    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.NumberOfCommonPitchesFeature(s)
    >>> fe.extract().vector
    [3]
    '''
    id = 'P7'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Number of Common Pitches'
        self.description = ('Number of pitches that account individually '
                            'for at least 9% of all notes.')
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        '''Do processing necessary, storing result in feature.
        '''
        histo = self.data['pitches.midiPitchHistogram']
        total = sum(histo.values())
        post = 0
        for count in histo.values():
            if count / total >= 0.09:
                post += 1
        self.feature.vector[0] = post


class PitchVarietyFeature(featuresModule.FeatureExtractor):
    '''
    Number of pitches used at least once.

    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.PitchVarietyFeature(s)
    >>> fe.extract().vector
    [24]
    '''
    id = 'P8'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Pitch Variety'
        self.description = 'Number of pitches used at least once.'
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        '''Do processing necessary, storing result in feature.
        '''
        histo = self.data['pitches.midiPitchHistogram']
        post = 0
        for i, count in enumerate(histo):
            if count >= 1:
                post += 1
        self.feature.vector[0] = post


class PitchClassVarietyFeature(featuresModule.FeatureExtractor):
    '''
    Number of pitch classes used at least once.

    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.PitchClassVarietyFeature(s)
    >>> fe.extract().vector
    [10]
    '''
    id = 'P9'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Pitch Class Variety'
        self.description = 'Number of pitch classes used at least once.'
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        '''Do processing necessary, storing result in feature.
        '''
        histo = self.data['pitches.pitchClassHistogram']
        post = 0
        for i, count in enumerate(histo):
            if count >= 1:
                post += 1
        self.feature.vector[0] = post


class RangeFeature(featuresModule.FeatureExtractor):
    '''
    Difference between highest and lowest pitches. In semitones

    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.RangeFeature(s)
    >>> fe.extract().vector
    [34]
    '''
    id = 'P10'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Range'
        self.description = 'Difference between highest and lowest pitches.'
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        '''Do processing necessary, storing result in feature.
        '''
        histo = self.data['pitches.midiPitchHistogram']
        if not histo:
            raise JSymbolicFeatureException('input lacks notes')
        minIndex = min(histo.keys())
        maxIndex = max(histo.keys())

        self.feature.vector[0] = maxIndex - minIndex


class MostCommonPitchFeature(featuresModule.FeatureExtractor):
    '''
    Bin label of the most common pitch.

    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.MostCommonPitchFeature(s)
    >>> fe.extract().vector
    [61]
    '''
    id = 'P11'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Most Common Pitch'
        self.description = 'Bin label of the most common pitch.'
        self.isSequential = True
        self.dimensions = 1
        self.discrete = False

    def process(self):
        '''Do processing necessary, storing result in feature.
        '''
        histo = self.data['pitches.midiPitchHistogram']
        try:
            pNumberMax = histo.most_common(1)[0][0]
            self.feature.vector[0] = pNumberMax
        except IndexError:
            self.feature.vector[0] = 0.0


class PrimaryRegisterFeature(featuresModule.FeatureExtractor):
    '''
    Average MIDI pitch.

    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.PrimaryRegisterFeature(s)
    >>> fe.extract().vector
    [61.12...]
    '''
    id = 'P12'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Primary Register'
        self.description = 'Average MIDI pitch.'
        self.isSequential = True
        self.dimensions = 1
        self.discrete = False

    def process(self):
        '''
        Do processing necessary, storing result in feature.
        '''
        histo = self.data['pitches']
        if not histo:
            raise JSymbolicFeatureException('input lacks notes')
        self.feature.vector[0] = statistics.mean([p.ps for p in histo])


class ImportanceOfBassRegisterFeature(featuresModule.FeatureExtractor):
    '''
    Fraction of Notes between MIDI pitches 0 and 54.

    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.ImportanceOfBassRegisterFeature(s)
    >>> fe.extract().vector
    [0.184...]
    '''
    id = 'P13'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Importance of Bass Register'
        self.description = 'Fraction of Note Ons between MIDI pitches 0 and 54.'
        self.isSequential = True
        self.dimensions = 1
        self.discrete = False

    def process(self):
        '''Do processing necessary, storing result in feature.
        '''
        histo = self.data['pitches.midiPitchHistogram']
        if not histo:
            raise JSymbolicFeatureException('input lacks notes')
        matches = []
        # assuming we just average the active pitch values
        for i, count in histo.items():
            if i <= 54:  # index is midi note number
                matches.append(count)
        matchedSum = sum(matches)
        # divide number found by total
        self.feature.vector[0] = matchedSum / float(sum(histo.values()))


class ImportanceOfMiddleRegisterFeature(featuresModule.FeatureExtractor):
    '''
    Fraction of Notes between MIDI pitches 55 and 72

    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.ImportanceOfMiddleRegisterFeature(s)
    >>> fe.extract().vector
    [0.766...]
    '''
    id = 'P14'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Importance of Middle Register'
        self.description = 'Fraction of Note Ons between MIDI pitches 55 and 72.'
        self.isSequential = True
        self.dimensions = 1
        self.discrete = False

    def process(self):
        '''Do processing necessary, storing result in feature.
        '''
        histo = self.data['pitches.midiPitchHistogram']
        if not histo:
            raise JSymbolicFeatureException('input lacks notes')
        matches = []
        # assuming we just average the active pitch values
        for i, count in histo.items():
            if 55 <= i <= 72:  # index is midi note number
                matches.append(count)
        matchedSum = sum(matches)
        # divide number found by total
        self.feature.vector[0] = matchedSum / float(sum(histo.values()))


class ImportanceOfHighRegisterFeature(featuresModule.FeatureExtractor):
    '''
    Fraction of Notes between MIDI pitches 73 and 127.

    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.ImportanceOfHighRegisterFeature(s)
    >>> fe.extract().vector
    [0.049...]
    '''
    id = 'P15'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Importance of High Register'
        self.description = 'Fraction of Note Ons between MIDI pitches 73 and 127.'
        self.isSequential = True
        self.dimensions = 1
        self.discrete = False

    def process(self):
        '''Do processing necessary, storing result in feature.
        '''
        histo = self.data['pitches.midiPitchHistogram']
        if not histo:
            raise JSymbolicFeatureException('input lacks notes')
        matches = []
        # assuming we just average the active pitch values
        for i, count in histo.items():
            if i >= 73:  # index is midi note number
                matches.append(count)
        matchedSum = sum(matches)
        # divide number found by total
        self.feature.vector[0] = matchedSum / float(sum(histo.values()))


class MostCommonPitchClassFeature(featuresModule.FeatureExtractor):
    '''
    Bin label of the most common pitch class.

    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.MostCommonPitchClassFeature(s)
    >>> fe.extract().vector
    [1]
    '''
    id = 'P16'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Most Common Pitch Class'
        self.description = 'Bin label of the most common pitch class.'
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        '''Do processing necessary, storing result in feature.
        '''
        histo = self.data['pitches.pitchClassHistogram']
        pIndexMax = histo.index(max(histo))
        self.feature.vector[0] = pIndexMax


class DominantSpreadFeature(featuresModule.FeatureExtractor):
    '''
    Not implemented

    Largest number of consecutive pitch classes separated by perfect
    5ths that accounted for at least 9% each of the notes.
    '''
    id = 'P17'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Dominant Spread'
        self.description = ('Largest number of consecutive pitch classes separated by '
                            'perfect 5ths that accounted for at least 9% each of the notes.')
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        raise JSymbolicFeatureException('not yet implemented')
        # TODO: implement


class StrongTonalCentresFeature(featuresModule.FeatureExtractor):
    '''
    Not implemented

    Number of peaks in the fifths pitch histogram that each account
    for at least 9% of all Note Ons.
    '''
    id = 'P18'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Strong Tonal Centres'
        self.description = ('Number of peaks in the fifths pitch histogram that each account '
                            'for at least 9% of all Note Ons.')
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        raise JSymbolicFeatureException('not yet implemented')
        # TODO: implement


class BasicPitchHistogramFeature(featuresModule.FeatureExtractor):
    '''
    A feature extractor that finds a features array with bins corresponding
    to the values of the basic pitch histogram.

    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.BasicPitchHistogramFeature(s)
    >>> f = fe.extract()
    >>> f.vector
    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, \
0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, \
0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, \
0.0, 0.0, 0.0, 0.006..., 0.0, 0.0, 0.006..., 0.006..., 0.030..., \
0.0, 0.036..., 0.012..., 0.0, 0.006..., 0.018..., 0.061..., 0.0, \
0.042..., 0.073..., 0.012..., 0.092..., 0.0, 0.116..., 0.061..., \
0.006..., 0.085..., 0.018..., 0.110..., 0.0, 0.042..., 0.055..., \
0.0, 0.049..., 0.0, 0.042..., 0.0, 0.0, 0.006..., 0.0, 0.0, 0.0, \
0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, \
0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, \
0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, \
0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    '''
    id = 'P19'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Basic Pitch Histogram'
        self.description = ('A features array with bins corresponding to the '
                            'values of the basic pitch histogram.')
        self.isSequential = True
        self.dimensions = 128
        self.normalize = True

    def process(self):
        '''Do processing necessary, storing result in feature.
        '''
        for i, count in self.data['pitches.midiPitchHistogram'].items():
            self.feature.vector[i] = count


class PitchClassDistributionFeature(featuresModule.FeatureExtractor):
    '''
    A feature array with 12 entries where the first holds the frequency
    of the bin of the pitch class histogram with the highest frequency,
    and the following entries holding the successive bins of the histogram,
    wrapping around if necessary.

    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.PitchClassDistributionFeature(s)
    >>> f = fe.extract()
    >>> f.vector
    [0.196..., 0.073..., 0.006..., 0.098..., 0.036..., 0.177..., 0.0, \
0.085..., 0.134..., 0.018..., 0.171..., 0.0]

    '''
    id = 'P20'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Pitch Class Distribution'
        self.description = ('A feature array with 12 entries where the first holds '
                            'the frequency of the bin of the pitch class histogram with '
                            'the highest frequency, and the following entries holding '
                            'the successive bins of the histogram, wrapping around if necessary.')
        self.isSequential = True
        self.dimensions = 12
        self.discrete = False
        self.normalize = True

    def process(self):
        '''Do processing necessary, storing result in feature.
        '''
        # Create vector with [C, C#, D...]
        temp = [0] * self.dimensions
        for i, count in enumerate(self.data['pitches.pitchClassHistogram']):
            temp[i] = count
        # Now rearrange so that the most common is in array 0 as per
        # original jSymbolic documentation and implementation
        m = temp.index(max(temp))
        # m will become 0, m + 1 will become 1, etc.
        for i, val in enumerate(temp):
            self.feature.vector[(i - m) % self.dimensions] = val


class FifthsPitchHistogramFeature(featuresModule.FeatureExtractor):
    '''
    A feature array with bins corresponding to the values of the 5ths pitch class
    histogram. Instead of the bins being arranged according to semitones --
    [C, C#, D...] -- they are arranged according to the circle of fifths:
    [C, G, D, A, E, B, F#, C#, G#, D#, A#, F]. Viewing such a histogram
    may draw attention to the prevalence of a tonal center, including the
    prevalence of dominant relationships in the piece.

    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.FifthsPitchHistogramFeature(s)
    >>> f = fe.extract()
    >>> f.vector
    [0.0, 0.0, 0.073..., 0.134..., 0.098..., 0.171..., 0.177..., 0.196..., \
0.085..., 0.006..., 0.018..., 0.036...]
    '''
    id = 'P21'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Fifths Pitch Histogram'
        self.description = ('A feature array with bins corresponding to the values of the '
                            '5ths pitch class histogram.')
        self.isSequential = True
        self.dimensions = 12
        self.normalize = True

        # create pc to index mapping
        self._mapping = {}
        for i in range(12):
            self._mapping[i] = (7 * i) % 12

    def process(self):
        '''Do processing necessary, storing result in feature.
        '''
        for i, count in enumerate(self.data['pitches.pitchClassHistogram']):
            self.feature.vector[self._mapping[i]] = count


class QualityFeature(featuresModule.FeatureExtractor):
    '''
    Set to 0 if the key signature indicates that
    a recording is major, set to 1 if it indicates
    that it is minor.  In jSymbolic, this is set to 0 if key signature is unknown.

    See features.native.QualityFeature for a music21 improvement on this method

    Example: Handel, Rinaldo Aria (musicxml) is explicitly encoded as being in Major:

    >>> s = corpus.parse('handel/rinaldo/lascia_chio_pianga')
    >>> fe = features.jSymbolic.QualityFeature(s)
    >>> f = fe.extract()
    >>> f.vector
    [0]

    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.QualityFeature(s)
    >>> f = fe.extract()
    >>> f.vector
    [1]
    '''
    id = 'P22'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Quality'
        self.description = '''
            Set to 0 if the key signature indicates that
            a recording is major, set to 1 if it indicates
            that it is minor and set to 0 if key signature is unknown.
            '''
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        '''Do processing necessary, storing result in feature.
        '''
        allKeys = self.data['flat.getElementsByClass(Key)']
        keyFeature = None
        for x in allKeys:
            if x.mode == 'major':
                keyFeature = 0
                break
            elif x.mode == 'minor':
                keyFeature = 1
                break
        if keyFeature is None:
            keyFeature = 0

        self.feature.vector[0] = keyFeature


class GlissandoPrevalenceFeature(featuresModule.FeatureExtractor):
    '''
    Not yet implemented in music21

    Number of Note Ons that have at least one MIDI Pitch Bend associated
    with them divided by total number of pitched Note Ons.
    '''
    id = 'P23'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Glissando Prevalence'
        self.description = ('Number of Note Ons that have at least one MIDI Pitch Bend '
                            'associated with them divided by total number of pitched Note Ons.')
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        raise JSymbolicFeatureException('not yet implemented')
        # TODO: implement


class AverageRangeOfGlissandosFeature(featuresModule.FeatureExtractor):
    '''
    Not yet implemented in music21

    Average range of MIDI Pitch Bends, where "range" is defined
    as the greatest value of the absolute difference between 64 and the
    second data byte of all MIDI Pitch Bend messages falling between the
    Note On and Note Off messages of any note
    '''
    id = 'P24'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Average Range Of Glissandos'
        self.description = ('Average range of MIDI Pitch Bends, where "range" is '
                            'defined as the greatest value of the absolute difference '
                            'between 64 and the second data byte of all MIDI Pitch Bend '
                            'messages falling between the Note On and Note Off messages '
                            'of any note.')
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        raise JSymbolicFeatureException('not yet implemented')
        # TODO: implement


class VibratoPrevalenceFeature(featuresModule.FeatureExtractor):
    '''
    Not yet implemented in music21

    Number of notes for which Pitch Bend messages change direction at least twice divided by
    total number of notes that have Pitch Bend messages associated with them.

    '''
    id = 'P25'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Vibrato Prevalence'
        self.description = ('Number of notes for which Pitch Bend messages change '
                            'direction at least twice divided by total number of notes '
                            'that have Pitch Bend messages associated with them.')
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        raise JSymbolicFeatureException('not yet implemented')
        # TODO: implement


class PrevalenceOfMicrotonesFeature(featuresModule.FeatureExtractor):
    '''
    not yet implemented

    Number of Note Ons that are preceded by isolated MIDI Pitch Bend
    messages as a fraction of the total number of Note Ons.'

    '''
    id = 'P26'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream,
                         *arguments, **keywords)

        self.name = 'Prevalence Of Microtones'
        self.description = ('Number of Note Ons that are preceded by isolated MIDI Pitch '
                            'Bend messages as a fraction of the total number of Note Ons.')
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        raise JSymbolicFeatureException('not yet implemented')
        # TODO: implement


# ------------------------------------------------------------------------------
# rhythm

class StrongestRhythmicPulseFeature(featuresModule.FeatureExtractor):
    '''
    Bin label of the beat bin of the peak with the highest frequency.

    >>> sch = corpus.parse('schoenberg/opus19', 2)
    >>> for p in sch.parts:
    ...     p.insert(0, tempo.MetronomeMark('Langsam', 70))
    >>> fe = features.jSymbolic.StrongestRhythmicPulseFeature(sch)
    >>> f = fe.extract()
    >>> f.vector[0]
    140

    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.StrongestRhythmicPulseFeature(s)
    >>> f = fe.extract()
    >>> f.vector
    [120]
    '''

    id = 'R1'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Strongest Rhythmic Pulse'
        self.description = 'Bin label of the beat bin with the highest frequency.'
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        beatHisto = self.data['flat.secondsMap.beatHistogram']
        self.feature.vector[0] = beatHisto.index(max(beatHisto))


class SecondStrongestRhythmicPulseFeature(featuresModule.FeatureExtractor):
    '''
    Bin label of the beat bin of the peak with the second highest frequency.

    >>> sch = corpus.parse('schoenberg/opus19', 2)
    >>> for p in sch.parts:
    ...     p.insert(0, tempo.MetronomeMark('Langsam', 70))
    >>> fe = features.jSymbolic.SecondStrongestRhythmicPulseFeature(sch)
    >>> f = fe.extract()
    >>> f.vector[0]
    70

    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.SecondStrongestRhythmicPulseFeature(s)
    >>> f = fe.extract()
    >>> f.vector
    [60]

    '''
    id = 'R2'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Second Strongest Rhythmic Pulse'
        self.description = ('Bin label of the beat bin of the peak '
                            'with the second highest frequency.')
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        beatHisto = copy.copy(self.data['flat.secondsMap.beatHistogram'])
        highestIndex = beatHisto.index(max(beatHisto))
        beatHisto[highestIndex] = 0

        self.feature.vector[0] = beatHisto.index(max(beatHisto))


class HarmonicityOfTwoStrongestRhythmicPulsesFeature(
        featuresModule.FeatureExtractor):
    '''
    The bin label of the higher (in terms of bin label) of the two beat bins of the
    peaks with the highest frequency divided by the bin label of the lower.

    >>> sch = corpus.parse('schoenberg/opus19', 2)
    >>> for p in sch.parts:
    ...     p.insert(0, tempo.MetronomeMark('Langsam', 70))
    >>> fe = features.jSymbolic.HarmonicityOfTwoStrongestRhythmicPulsesFeature(sch)
    >>> f = fe.extract()
    >>> f.vector[0]
    2.0

    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.HarmonicityOfTwoStrongestRhythmicPulsesFeature(s)
    >>> f = fe.extract()
    >>> f.vector
    [2.0]

    '''
    id = 'R3'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Harmonicity of Two Strongest Rhythmic Pulses'
        self.description = ('The bin label of the higher (in terms of bin label) of the '
                            'two beat bins of the peaks with the highest frequency '
                            'divided by the bin label of the lower.')
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        beatHisto = copy.copy(self.data['flat.secondsMap.beatHistogram'])
        highestIndex = beatHisto.index(max(beatHisto))
        beatHisto[highestIndex] = 0

        secondHighest = beatHisto.index(max(beatHisto))
        self.feature.vector[0] = float(highestIndex / secondHighest)


class StrengthOfStrongestRhythmicPulseFeature(featuresModule.FeatureExtractor):
    '''
    Frequency of the beat bin with the highest frequency.

    >>> sch = corpus.parse('schoenberg/opus19', 2)
    >>> for p in sch.parts:
    ...     p.insert(0, tempo.MetronomeMark('Langsam', 70))
    >>> fe = features.jSymbolic.StrengthOfStrongestRhythmicPulseFeature(sch)
    >>> fe.extract().vector[0]
    0.853...
    '''
    id = 'R4'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Strength of Strongest Rhythmic Pulse'
        self.description = 'Frequency of the beat bin with the highest frequency.'
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        beatHisto = self.data['flat.secondsMap.beatHistogram']
        self.feature.vector[0] = max(beatHisto) / sum(beatHisto)


class StrengthOfSecondStrongestRhythmicPulseFeature(
        featuresModule.FeatureExtractor):
    '''
    Frequency of the beat bin of the peak with the second highest frequency.

    >>> sch = corpus.parse('schoenberg/opus19', 2)
    >>> for p in sch.parts:
    ...     p.insert(0, tempo.MetronomeMark('Langsam', 70))
    >>> fe = features.jSymbolic.StrengthOfSecondStrongestRhythmicPulseFeature(sch)
    >>> fe.extract().vector[0]
    0.12...
    '''
    id = 'R5'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Strength of Second Strongest Rhythmic Pulse'
        self.description = ('Frequency of the beat bin of the peak '
                            'with the second highest frequency.')
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        beatHisto = copy.copy(self.data['flat.secondsMap.beatHistogram'])
        sumHisto = sum(beatHisto)

        highestIndex = beatHisto.index(max(beatHisto))
        beatHisto[highestIndex] = 0

        secondHighest = max(beatHisto)
        self.feature.vector[0] = secondHighest / sumHisto


class StrengthRatioOfTwoStrongestRhythmicPulsesFeature(
        featuresModule.FeatureExtractor):
    '''
    The frequency of the higher (in terms of frequency) of the two beat bins
    corresponding to the peaks with the highest frequency divided by the frequency of the lower.


    >>> sch = corpus.parse('schoenberg/opus19', 2)
    >>> for p in sch.parts:
    ...     p.insert(0, tempo.MetronomeMark('Langsam', 70))
    >>> fe = features.jSymbolic.StrengthRatioOfTwoStrongestRhythmicPulsesFeature(sch)
    >>> fe.extract().vector[0]
    7.0

    '''
    id = 'R6'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Strength Ratio of Two Strongest Rhythmic Pulses'
        self.description = ('The frequency of the higher (in terms of frequency) of the two '
                            'beat bins corresponding to the peaks with the highest '
                            'frequency divided by the frequency of the lower.')
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        beatHisto = copy.copy(self.data['flat.secondsMap.beatHistogram'])

        theHighest = max(beatHisto)
        highestIndex = beatHisto.index(theHighest)
        beatHisto[highestIndex] = 0

        secondHighest = max(beatHisto)
        self.feature.vector[0] = theHighest / secondHighest


class CombinedStrengthOfTwoStrongestRhythmicPulsesFeature(
        featuresModule.FeatureExtractor):
    '''
    The sum of the frequencies of the two beat bins of the peaks with the highest frequencies.

    >>> sch = corpus.parse('schoenberg/opus19', 2)
    >>> for p in sch.parts:
    ...     p.insert(0, tempo.MetronomeMark('Langsam', 70))
    >>> fe = features.jSymbolic.CombinedStrengthOfTwoStrongestRhythmicPulsesFeature(sch)
    >>> fe.extract().vector[0]
    0.975...
    '''
    id = 'R7'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Combined Strength of Two Strongest Rhythmic Pulses'
        self.description = ('The sum of the frequencies of the two beat bins '
                            'of the peaks with the highest frequencies.')
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        beatHisto = copy.copy(self.data['flat.secondsMap.beatHistogram'])
        sumHisto = sum(beatHisto)

        theHighest = max(beatHisto)
        highestIndex = beatHisto.index(theHighest)
        beatHisto[highestIndex] = 0

        secondHighest = max(beatHisto)
        self.feature.vector[0] = (theHighest + secondHighest) / sumHisto


class NumberOfStrongPulsesFeature(featuresModule.FeatureExtractor):
    '''
    Not yet implemented

    Number of beat peaks with normalized frequencies over 0.1.

    '''
    id = 'R8'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Number of Strong Pulses'
        self.description = 'Number of beat peaks with normalized frequencies over 0.1.'
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        raise JSymbolicFeatureException('not yet implemented')
        # TODO: implement


class NumberOfModeratePulsesFeature(featuresModule.FeatureExtractor):
    '''
    Not yet implemented

    Number of beat peaks with normalized frequencies over 0.01.
    '''
    id = 'R9'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Number of Moderate Pulses'
        self.description = 'Number of beat peaks with normalized frequencies over 0.01.'
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        raise JSymbolicFeatureException('not yet implemented')
        # TODO: implement


class NumberOfRelativelyStrongPulsesFeature(featuresModule.FeatureExtractor):
    '''
    not yet implemented

    Number of beat peaks with frequencies at least 30% as high as the
    frequency of the bin with the highest frequency.
    '''
    id = 'R10'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Number of Relatively Strong Pulses'
        self.description = '''Number of beat peaks with frequencies at least 30% as high as
                'the frequency of the bin with the highest frequency.'''
        self.isSequential = True
        self.dimensions = 1


class RhythmicLoosenessFeature(featuresModule.FeatureExtractor):
    '''
    not yet implemented

    Average width of beat histogram peaks (in beats per minute).
    Width is measured for all peaks with frequencies at least 30% as high as the highest peak,
    and is defined by the distance between the points on the peak in question that are
    30% of the height of the peak.
    '''
    id = 'R11'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Rhythmic Looseness'
        self.description = '''Average width of beat histogram peaks (in beats per minute).
        Width is measured for all peaks with frequencies at least 30% as high as the
        highest peak, and is defined by the distance between the points on the peak in
        question that are 30% of the height of the peak.'''
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        raise JSymbolicFeatureException('not yet implemented')
        # TODO: implement


class PolyrhythmsFeature(featuresModule.FeatureExtractor):
    '''
    Not yet implemented

    Number of beat peaks with frequencies at least 30% of the highest frequency
    whose bin labels are not integer multiples or factors
    (using only multipliers of 1, 2, 3, 4, 6 and 8) (with an accepted
    error of +/- 3 bins) of the bin label of the peak with the highest frequency.
    This number is then divided by the total number of beat bins with frequencies
    over 30% of the highest frequency.
    '''
    id = 'R12'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        featuresModule.FeatureExtractor.__init__(self,
                                                 dataOrStream=dataOrStream,
                                                 *arguments, **keywords)

        self.name = 'Polyrhythms'
        self.description = '''
        Number of beat peaks with frequencies at least 30% of the highest frequency
        whose bin labels are not integer multiples or factors
        (using only multipliers of 1, 2, 3, 4, 6 and 8) (with an accepted
        error of +/- 3 bins) of the bin label of the peak with the highest frequency.
        This number is then divided by the total number of beat bins with frequencies
        over 30% of the highest frequency.'''
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        raise JSymbolicFeatureException('not yet implemented')
        # TODO: implement


class RhythmicVariabilityFeature(featuresModule.FeatureExtractor):
    '''
    Not yet implemented

    Standard deviation of the bin values (except the first 40 empty ones).
    '''
    id = 'R13'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Rhythmic Variability'
        self.description = 'Standard deviation of the bin values (except the first 40 empty ones).'
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        raise JSymbolicFeatureException('not yet implemented')
        # TODO: implement


class BeatHistogramFeature(featuresModule.FeatureExtractor):
    '''
    Not yet implemented

    A feature extractor that finds a feature array with entries corresponding to the frequency
    values of each of the bins of the beat histogram (except the first 40 empty ones).


    '''
    id = 'R14'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Beat Histogram'
        self.description = ('A feature array with entries corresponding to the '
                            'frequency values of each of the bins of the beat histogram '
                            '(except the first 40 empty ones).')
        self.isSequential = True
        self.dimensions = 161
        self.discrete = False

    def process(self):
        raise JSymbolicFeatureException('not yet implemented')
        # TODO: implement


class NoteDensityFeature(featuresModule.FeatureExtractor):
    '''
    Gives the average number of notes per second, taking into account
    the tempo at any moment in the piece.  Unlike jSymbolic, music21
    quantizes notes from MIDI somewhat before running this test; this
    function is meant to be run on encoded MIDI scores rather than
    recorded MIDI performances.

    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.NoteDensityFeature(s)
    >>> f = fe.extract()
    >>> f.vector
    [9.055...]
    '''
    id = 'R15'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Note Density'
        self.description = 'Average number of notes per second.'
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        secondsMap = self.data['flat.secondsMap']
        # The average number of notes per second in the piece is calculated
        # by taking the total number of notes in the piece and dividing by
        # the end time of the piece (in seconds).
        end_times = [bundle['endTimeSeconds'] for bundle in secondsMap]
        end_times.sort()  # may already be sorted?
        # Create a list of difference in time offset between consecutive notes
        if not end_times:
            self.feature.vector[0] = 0.0
        else:
            self.feature.vector[0] = float(len(end_times)) / end_times[-1]


class AverageNoteDurationFeature(featuresModule.FeatureExtractor):
    '''
    Average duration of notes in seconds.

    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.AverageNoteDurationFeature(s)
    >>> f = fe.extract()
    >>> f.vector
    [0.441...]

    >>> s.insert(0, tempo.MetronomeMark(number=240))
    >>> fe = features.jSymbolic.AverageNoteDurationFeature(s)
    >>> f = fe.extract()
    >>> f.vector
    [0.220858...]
    '''

    id = 'R17'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Average Note Duration'
        self.description = 'Average duration of notes in seconds.'
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        secondsMap = self.data['flat.secondsMap']
        if not secondsMap:
            raise JSymbolicFeatureException('input lacks notes')
        total = 0.0
        for bundle in secondsMap:
            total += bundle['durationSeconds']
        self.feature.vector[0] = total / len(secondsMap)


class VariabilityOfNoteDurationFeature(featuresModule.FeatureExtractor):
    '''Standard deviation of note durations in seconds.

    # In this piece, we have:
    #     9 half notes or tied pair of quarters
    #     98 untied quarters or tied pair of eighths
    #     56 untied eighths
    # BPM = 120 means a half note is a second.
    # Mean duration should thus be 0.44171779141104295
    # and standard deviation should be  0.17854763448902145
    >>> s = corpus.parse('bwv66.6')
    >>> for p in s.parts:
    ...     p.insert(0, tempo.MetronomeMark(number=120))
    >>> fe = features.jSymbolic.VariabilityOfNoteDurationFeature(s)
    >>> f = fe.extract()
    >>> f.vector[0]
    0.178...
    '''
    id = 'R18'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Variability of Note Duration'
        self.description = 'Standard deviation of note durations in seconds.'
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        secondsMap = self.data['flat.secondsMap']
        if not secondsMap:
            raise JSymbolicFeatureException('input lacks notes')
        note_durations = []
        for bundle in secondsMap:
            note_durations.append(bundle['durationSeconds'])
        self.feature.vector[0] = statistics.pstdev(note_durations)


class MaximumNoteDurationFeature(featuresModule.FeatureExtractor):
    '''
    Duration of the longest note (in seconds).

    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.MaximumNoteDurationFeature(s)
    >>> f = fe.extract()
    >>> f.vector
    [1.0]
    '''

    id = 'R19'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Maximum Note Duration'
        self.description = 'Duration of the longest note (in seconds).'
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        secondsMap = self.data['flat.secondsMap']
        if not secondsMap:
            raise JSymbolicFeatureException('input lacks notes')
        maxSeconds = 0.0
        for bundle in secondsMap:
            if bundle['durationSeconds'] > maxSeconds:
                maxSeconds = bundle['durationSeconds']
        self.feature.vector[0] = maxSeconds


class MinimumNoteDurationFeature(featuresModule.FeatureExtractor):
    '''
    Duration of the shortest note (in seconds).

    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.MinimumNoteDurationFeature(s)
    >>> f = fe.extract()
    >>> f.vector
    [0.25]
    '''
    id = 'R20'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Minimum Note Duration'
        self.description = 'Duration of the shortest note (in seconds).'
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        secondsMap = self.data['flat.secondsMap']
        if not secondsMap:
            raise JSymbolicFeatureException('input lacks notes')
        # an arbitrary number from the coll
        minSeconds = secondsMap[0]['durationSeconds']
        for bundle in secondsMap:
            if bundle['durationSeconds'] < minSeconds:
                minSeconds = bundle['durationSeconds']
        self.feature.vector[0] = minSeconds


class StaccatoIncidenceFeature(featuresModule.FeatureExtractor):
    '''
    Number of notes with durations of less than a 10th of a second divided by
    the total number of notes in the recording.

    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.StaccatoIncidenceFeature(s)
    >>> f = fe.extract()
    >>> f.vector
    [0.0]
    '''

    id = 'R21'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Staccato Incidence'
        self.description = ('Number of notes with durations of less than a 10th '
                            'of a second divided by the total number of notes in the recording.')
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        secondsMap = self.data['flat.secondsMap']
        if not secondsMap:
            raise JSymbolicFeatureException('input lacks notes')
        count = 0
        for bundle in secondsMap:
            if bundle['durationSeconds'] < 0.10:
                count += 1
        self.feature.vector[0] = count / float(len(secondsMap))


class AverageTimeBetweenAttacksFeature(featuresModule.FeatureExtractor):
    '''
    Average time in seconds between Note On events (regardless of channel).

    >>> s = corpus.parse('bwv66.6')
    >>> for p in s.parts:
    ...     p.insert(0, tempo.MetronomeMark(number=120))
    >>> fe = features.jSymbolic.AverageTimeBetweenAttacksFeature(s)
    >>> f = fe.extract()
    >>> print(f.vector)
    [0.35]
    '''

    id = 'R22'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Average Time Between Attacks'
        self.description = 'Average time in seconds between Note On events (regardless of channel).'
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        secondsMap = self.data['flat.secondsMap']
        # Get a list of note onset times
        onsets = [bundle['offsetSeconds'] for bundle in secondsMap]
        if not onsets:
            raise JSymbolicFeatureException('input lacks notes')
        onsets.sort()  # may already be sorted?
        # Create a list of difference in time offset between consecutive notes
        differences = []
        for i, o in enumerate(onsets):
            if i == len(onsets) - 1:  # stop before the last
                break
            oNext = onsets[i + 1]
            # Don't include simultaneous attacks
            dif = oNext - o
            if not common.almostEquals(dif, 0.0):
                differences.append(dif)
        self.feature.vector[0] = sum(differences) / float(len(differences))


class VariabilityOfTimeBetweenAttacksFeature(featuresModule.FeatureExtractor):
    '''
    Standard deviation of the times, in seconds, between Note On events (regardless of channel).

    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.VariabilityOfTimeBetweenAttacksFeature(s)
    >>> f = fe.extract()
    >>> print(f.vector)
    [0.15]
    '''

    id = 'R23'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Variability of Time Between Attacks'
        self.description = ('Standard deviation of the times, in seconds, '
                            'between Note On events (regardless of channel).')
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        secondsMap = self.data['flat.secondsMap']
        # Create a list of difference in time offset between consecutive notes
        onsets = [bundle['offsetSeconds'] for bundle in secondsMap]
        if not onsets:
            raise JSymbolicFeatureException('input lacks notes')
        onsets.sort()  # may already be sorted?
        differences = []
        for i, o in enumerate(onsets):
            if i == len(onsets) - 1:  # stop before the last
                break
            oNext = onsets[i + 1]
            # Don't include simultaneous attacks
            dif = oNext - o
            if not common.almostEquals(dif, 0.0):
                differences.append(dif)
        self.feature.vector[0] = statistics.pstdev(differences)


class AverageTimeBetweenAttacksForEachVoiceFeature(
        featuresModule.FeatureExtractor):
    '''
    Average of average times in seconds between Note On events on individual channels
    that contain at least one note.

    >>> s = corpus.parse('bwv66.6')
    >>> for p in s.parts:
    ...     p.insert(0, tempo.MetronomeMark(number=120))
    >>> fe = features.jSymbolic.AverageTimeBetweenAttacksForEachVoiceFeature(s)
    >>> f = fe.extract()
    >>> print(f.vector[0])
    0.442...
    '''
    id = 'R24'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Average Time Between Attacks For Each Voice'
        self.description = ('Average of average times in seconds between Note On events '
                            'on individual channels that contain at least one note.')
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        onsetsByPart = []
        avgByPart = []
        if self.data.partsCount > 0:
            for i in range(self.data.partsCount):
                secondsMap = self.data['parts'][i]['flat.secondsMap']
                onsets = [bundle['offsetSeconds'] for bundle in secondsMap]
                onsetsByPart.append(onsets)
        else:
            secondsMap = self.data['flat.secondsMap']
            onsets = [bundle['offsetSeconds'] for bundle in secondsMap]
            onsetsByPart.append(onsets)

        for onsets in onsetsByPart:
            # Create a list of difference in time offset between consecutive notes
            onsets.sort()  # may already be sorted?
            differences = []
            for i, o in enumerate(onsets):
                if i == len(onsets) - 1:  # stop before the last
                    break
                oNext = onsets[i + 1]
                # Don't include simultaneous attacks
                dif = oNext - o
                if not common.almostEquals(dif, 0.0):
                    differences.append(dif)
            if not differences:
                raise JSymbolicFeatureException('at least one part lacks notes')
            avgByPart.append(sum(differences) / float(len(differences)))

        self.feature.vector[0] = sum(avgByPart) / len(avgByPart)


class AverageVariabilityOfTimeBetweenAttacksForEachVoiceFeature(
        featuresModule.FeatureExtractor):
    '''
    Average standard deviation, in seconds, of time between Note On events on individual
    channels that contain at least one note.

    >>> s = corpus.parse('bwv66.6')
    >>> for p in s.parts:
    ...     p.insert(0, tempo.MetronomeMark(number=120))
    >>> fe = features.jSymbolic.AverageVariabilityOfTimeBetweenAttacksForEachVoiceFeature(s)
    >>> f = fe.extract()
    >>> f.vector
    [0.177...]
    '''

    id = 'R25'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Average Variability of Time Between Attacks For Each Voice'
        self.description = ('Average standard deviation, in seconds, of time between '
                            'Note On events on individual channels that contain '
                            'at least one note.')
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        onsetsByPart = []
        stdDeviationByPart = []

        if self.data.partsCount > 0:
            for i in range(self.data.partsCount):
                secondsMap = self.data['parts'][i]['flat.secondsMap']
                onsets = [bundle['offsetSeconds'] for bundle in secondsMap]
                onsetsByPart.append(onsets)
        else:
            secondsMap = self.data['flat.secondsMap']
            onsets = [bundle['offsetSeconds'] for bundle in secondsMap]
            onsetsByPart.append(onsets)

        for onsets in onsetsByPart:
            # Create a list of difference in time offset between consecutive notes
            onsets.sort()  # may already be sorted?
            differences = []
            for i, o in enumerate(onsets):
                if i == len(onsets) - 1:  # stop before the last
                    break
                oNext = onsets[i + 1]
                dif = oNext - o
                # Don't include simultaneous attacks
                if not common.almostEquals(dif, 0.0):
                    differences.append(dif)
            if not differences:
                raise JSymbolicFeatureException('at least one part lacks notes')
            stdDeviationByPart.append(statistics.pstdev(differences))
        self.feature.vector[0] = (sum(stdDeviationByPart)
                                  / len(stdDeviationByPart))


# class IncidenceOfCompleteRestsFeature(featuresModule.FeatureExtractor):
#    '''
#    Not implemented in jSymbolic
#
#    '''
#    def __init__(self, dataOrStream=None, *arguments, **keywords):
#        super().__init__(dataOrStream=dataOrStream,
#                    *arguments, **keywords)
#
#        self.name = 'Incidence Of Complete Rests'
#        self.description = ('Total amount of time in seconds in which no notes are sounding'
#                    ' on any channel divided by the total length of the recording')
#        self.isSequential = True
#        self.dimensions = 1
#
# class MaximumCompleteRestDurationFeature(featuresModule.FeatureExtractor):
#    '''
#    Not implemented in jSymbolic
#
#    '''
#    def __init__(self, dataOrStream=None, *arguments, **keywords):
#        super().__init__(dataOrStream=dataOrStream,
#                        *arguments, **keywords)
#
#        self.name = 'Maximum Complete Rest Duration'
#        self.description = ('Maximum amount of time in seconds in which no notes '
#                'are sounding on any channel.')
#        self.isSequential = True
#        self.dimensions = 1
#
# class AverageRestDurationPerVoiceFeature(featuresModule.FeatureExtractor):
#    '''
#    Not implemented in jSymbolic
#
#    '''
#    def __init__(self, dataOrStream=None, *arguments, **keywords):
#        super().__init__(dataOrStream=dataOrStream,
#                        *arguments, **keywords)
#
#        self.name = 'Average Rest Duration Per Voice'
#        self.description = ('Average, in seconds, of the average amounts of time in each '
#                'channel in which no note is sounding (counting only channels with at least '
#                'one note), divided by the total duration of the recording')
#        self.isSequential = True
#        self.dimensions = 1
#
# class AverageVariabilityOfRestDurationsAcrossVoicesFeature(featuresModule.FeatureExtractor):
#    '''
#    Not implemented in jSymbolic
#
#    '''
#    def __init__(self, dataOrStream=None, *arguments, **keywords):
#        super().__init__(dataOrStream=dataOrStream,
#                    *arguments, **keywords)
#
#        self.name = 'Average Variability Of Rest Durations Across Voices'
#        self.description = ('Standard deviation, in seconds, of the average amounts of time '
#                    'in each channel in which no note is sounding (counting only '
#                    'channels with at least one note)'
#        self.isSequential = True
#        self.dimensions = 1


class InitialTempoFeature(featuresModule.FeatureExtractor):
    '''
    Tempo in beats per minute at the start of the recording.

    >>> s = corpus.parse('bwv66.6')
    >>> for p in s.parts:
    ...     p.insert(0, tempo.MetronomeMark(number=120))
    >>> fe = features.jSymbolic.InitialTempoFeature(s)
    >>> f = fe.extract()
    >>> f.vector  # a default
    [120.0]
    '''

    id = 'R30'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Initial Tempo'
        self.description = 'Tempo in beats per minute at the start of the recording.'
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        triples = self.data['metronomeMarkBoundaries']
        # the first is the a default, if necessary; also provides start/end time
        mm = triples[0][2]
        # assume we want quarter bpm, not bpm in other division
        self.feature.vector[0] = mm.getQuarterBPM()


class InitialTimeSignatureFeature(featuresModule.FeatureExtractor):
    '''
    A feature array with two elements. The first is the numerator of the first occurring
    time signature and the second is the denominator of the first occurring time signature.
    Both are set to 0 if no time signature is present.

    >>> s1 = stream.Stream()
    >>> s1.append(meter.TimeSignature('3/4'))
    >>> fe = features.jSymbolic.InitialTimeSignatureFeature(s1)
    >>> fe.extract().vector
    [3, 4]

    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.InitialTimeSignatureFeature(s)
    >>> f = fe.extract()
    >>> f.vector
    [4, 4]
    '''

    id = 'R31'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Initial Time Signature'
        self.description = ('A feature array with two elements. '
                            'The first is the numerator of the first occurring time signature '
                            'and the second is the denominator of the first occurring time '
                            'signature. Both are set to 0 if no time signature is present.')
        self.isSequential = True
        self.dimensions = 2

    def process(self):
        elements = self.data['flat.getElementsByClass(TimeSignature)']
        if not elements:
            return  # vector already zero
        ts = elements[0]
        environLocal.printDebug(['found ts', ts])
        self.feature.vector[0] = elements[0].numerator
        self.feature.vector[1] = elements[0].denominator


class CompoundOrSimpleMeterFeature(featuresModule.FeatureExtractor):
    '''
    Set to 1 if the initial meter is compound (numerator of time signature
    is greater than or equal to 6 and is evenly divisible by 3) and to 0 if it is simple
    (if the above condition is not fulfilled).

    >>> s1 = stream.Stream()
    >>> s1.append(meter.TimeSignature('3/4'))
    >>> fe = features.jSymbolic.CompoundOrSimpleMeterFeature(s1)
    >>> fe.extract().vector
    [0]

    >>> s2 = stream.Stream()
    >>> s2.append(meter.TimeSignature('9/8'))
    >>> fe.setData(s2)  # change the data
    >>> fe.extract().vector
    [1]

    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.CompoundOrSimpleMeterFeature(s)
    >>> f = fe.extract()
    >>> f.vector
    [0]
    '''

    id = 'R32'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Compound Or Simple Meter'
        self.description = ('Set to 1 if the initial meter is compound '
                            '(numerator of time signature is greater than or equal to 6 '
                            'and is evenly divisible by 3) and to 0 if it is simple '
                            '(if the above condition is not fulfilled).')
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        from music21 import meter

        elements = self.data['flat.getElementsByClass(TimeSignature)']

        if elements:
            try:
                countName = elements[0].beatDivisionCountName
            except meter.TimeSignatureException:
                return  # do nothing
            if countName == 'Compound':
                self.feature.vector[0] = 1


class TripleMeterFeature(featuresModule.FeatureExtractor):
    '''
    Set to 1 if numerator of initial time signature is 3, set to 0 otherwise.

    >>> s1 = stream.Stream()
    >>> s1.append(meter.TimeSignature('5/4'))
    >>> fe = features.jSymbolic.TripleMeterFeature(s1)
    >>> fe.extract().vector
    [0]

    >>> s2 = stream.Stream()
    >>> s2.append(meter.TimeSignature('3/4'))
    >>> fe.setData(s2)  # change the data
    >>> fe.extract().vector
    [1]

    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.TripleMeterFeature(s)
    >>> f = fe.extract()
    >>> f.vector
    [0]
    '''

    id = 'R33'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Triple Meter'
        self.description = ('Set to 1 if numerator of initial time signature is 3, '
                            'set to 0 otherwise.')
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        elements = self.data['flat.getElementsByClass(TimeSignature)']
        # not: not looking at other triple meters
        if elements and elements[0].numerator == 3:
            self.feature.vector[0] = 1


class QuintupleMeterFeature(featuresModule.FeatureExtractor):
    '''
    Set to 1 if numerator of initial time signature is 5, set to 0 otherwise.

    >>> s1 = stream.Stream()
    >>> s1.append(meter.TimeSignature('5/4'))
    >>> fe = features.jSymbolic.QuintupleMeterFeature(s1)
    >>> fe.extract().vector
    [1]

    >>> s2 = stream.Stream()
    >>> s2.append(meter.TimeSignature('3/4'))
    >>> fe.setData(s2)  # change the data
    >>> fe.extract().vector
    [0]

    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.QuintupleMeterFeature(s)
    >>> f = fe.extract()
    >>> f.vector
    [0]
    '''

    id = 'R34'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Quintuple Meter'
        self.description = ('Set to 1 if numerator of initial time signature is 5, '
                            'set to 0 otherwise.')
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        elements = self.data['flat.getElementsByClass(TimeSignature)']
        if elements and elements[0].numerator == 5:
            self.feature.vector[0] = 1


class ChangesOfMeterFeature(featuresModule.FeatureExtractor):
    '''Returns 1 if the time signature is changed one or more
    times during the recording.

    >>> s1 = stream.Stream()
    >>> s1.append(meter.TimeSignature('3/4'))
    >>> fe = features.jSymbolic.ChangesOfMeterFeature(s1)
    >>> fe.extract().vector
    [0]

    >>> s2 = stream.Stream()
    >>> s2.append(meter.TimeSignature('3/4'))
    >>> s2.append(meter.TimeSignature('4/4'))
    >>> fe.setData(s2)  # change the data
    >>> fe.extract().vector
    [1]

    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.ChangesOfMeterFeature(s)
    >>> f = fe.extract()
    >>> f.vector
    [0]
    '''
    id = 'R35'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Changes of Meter'
        self.description = ('Set to 1 if the time signature is changed one or more '
                            'times during the recording')
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        elements = self.data['flat.getElementsByClass(TimeSignature)']
        if len(elements) <= 1:
            return  # vector already zero
        first = elements[0]
        for e in elements[1:]:
            if not first.ratioEqual(e):
                self.feature.vector[0] = 1
                return


class DurationFeature(featuresModule.FeatureExtractor):
    '''A feature extractor that extracts the duration of the piece in seconds.

    >>> s = corpus.parse('bwv66.6')
    >>> for p in s.parts:
    ...     p.insert(0, tempo.MetronomeMark(number=120))
    >>> fe = features.jSymbolic.DurationFeature(s)
    >>> f = fe.extract()
    >>> f.vector[0]
    18.0
    '''
    id = 'R36'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Duration'
        self.description = 'The total duration in seconds of the music.'
        self.isSequential = False  # this is the only jSymbolic non seq feature
        self.dimensions = 1
        self.discrete = False

    def process(self):
        secondsMap = self.data['flat.secondsMap']
        if not secondsMap:
            raise JSymbolicFeatureException('input lacks duration')
        # The total duration of the piece is the same as the latest end time
        # of all the notes.
        end_times = [bundle['endTimeSeconds'] for bundle in secondsMap]
        end_times.sort()  # may already be sorted?
        self.feature.vector[0] = end_times[-1]


# ------------------------------------------------------------------------------
# dynamics


class OverallDynamicRangeFeature(featuresModule.FeatureExtractor):
    '''
    Not implemented

    The maximum loudness minus the minimum loudness value.

    TODO: implement
    '''
    id = 'D1'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Overall Dynamic Range'
        self.description = 'The maximum loudness minus the minimum loudness value.'
        self.isSequential = True
        self.dimensions = 1


class VariationOfDynamicsFeature(featuresModule.FeatureExtractor):
    '''
    Not implemented

    Standard deviation of loudness levels of all notes.


    TODO: implement

    '''
    id = 'D2'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Variation of Dynamics'
        self.description = 'Standard deviation of loudness levels of all notes.'
        self.isSequential = True
        self.dimensions = 1


class VariationOfDynamicsInEachVoiceFeature(featuresModule.FeatureExtractor):
    '''
    Not implemented

    The average of the standard deviations of loudness levels within each
    channel that contains at least one note.

    TODO: implement

    '''
    id = 'D3'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Variation of Dynamics In Each Voice'
        self.description = ('The average of the standard deviations of loudness '
                            'levels within each channel that contains at least one note.')
        self.isSequential = True
        self.dimensions = 1


class AverageNoteToNoteDynamicsChangeFeature(featuresModule.FeatureExtractor):
    '''
    Not implemented

    Average change of loudness from one note to the next note in the
    same channel (in MIDI velocity units).


    TODO: implement

    '''

    id = 'D4'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Average Note To Note Dynamics Change'
        self.description = ('Average change of loudness from one note to the next note '
                            'in the same channel (in MIDI velocity units).')
        self.isSequential = True
        self.dimensions = 1


# ------------------------------------------------------------------------------
# texture based


class MaximumNumberOfIndependentVoicesFeature(featuresModule.FeatureExtractor):
    '''
    Maximum number of different channels in which notes have sounded simultaneously.
    Here, Parts are treated as channels.

    >>> s = corpus.parse('handel/rinaldo/lascia_chio_pianga')
    >>> fe = features.jSymbolic.MaximumNumberOfIndependentVoicesFeature(s)
    >>> f = fe.extract()
    >>> f.vector
    [3]

    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.MaximumNumberOfIndependentVoicesFeature(s)
    >>> f = fe.extract()
    >>> f.vector
    [4]
    '''

    id = 'T1'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Maximum Number of Independent Voices'
        self.description = ('Maximum number of different channels in which notes '
                            'have sounded simultaneously. Here, Parts are treated as channels.')
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        # for each chordify, find the largest number different groups
        found = 0
        for c in self.data['chordify.flat.getElementsByClass(Chord)']:
            # create a group to aggregate all groups for each pitch in this
            # chord
            g = base.Groups()
            for p in c.pitches:
                for gSub in p.groups:
                    g.append(gSub)  # add to temporary group; will act as a set
            if len(g) > found:
                found = len(g)
        self.feature.vector[0] = found


class AverageNumberOfIndependentVoicesFeature(featuresModule.FeatureExtractor):
    '''
    Average number of different channels in which notes have sounded simultaneously.
    Rests are not included in this calculation. Here, Parts are treated as voices

    >>> s = corpus.parse('handel/rinaldo/lascia_chio_pianga')
    >>> fe = features.jSymbolic.AverageNumberOfIndependentVoicesFeature(s)
    >>> f = fe.extract()
    >>> f.vector
    [1.528...]

    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.AverageNumberOfIndependentVoicesFeature(s)
    >>> f = fe.extract()
    >>> f.vector
    [3.90...]
    '''
    id = 'T2'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Average Number of Independent Voices'
        self.description = ('Average number of different channels in which notes have '
                            'sounded simultaneously. Rests are not included in this '
                            'calculation. Here, Parts are treated as voices')
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        # for each chordify, find the largest number different groups
        found = []
        for c in self.data['chordify.flat.getElementsByClass(Chord)']:
            # create a group to aggregate all groups for each pitch in this
            # chord
            g = base.Groups()
            for p in c.pitches:
                for gSub in p.groups:
                    g.append(gSub)  # add to temporary group; will act as a set
            found.append(len(g))
        if not found:
            raise JSymbolicFeatureException('input lacks notes')
        self.feature.vector[0] = sum(found) / float(len(found))


class VariabilityOfNumberOfIndependentVoicesFeature(
        featuresModule.FeatureExtractor):
    '''
    Standard deviation of number of different channels in which notes have sounded simultaneously.
    Rests are not included in this calculation.


    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.jSymbolic.VariabilityOfNumberOfIndependentVoicesFeature(s)
    >>> f = fe.extract()
    >>> f.vector
    [0.449...]
    '''
    id = 'T3'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Variability of Number of Independent Voices'
        self.description = ('Standard deviation of number of different channels '
                            'in which notes have sounded simultaneously. Rests are '
                            'not included in this calculation.')
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        # for each chordify, find the largest number different groups
        found = []
        for c in self.data['chordify.flat.getElementsByClass(Chord)']:
            # create a group to aggregate all groups for each pitch in this
            # chord
            g = base.Groups()
            for p in c.pitches:
                for gSub in p.groups:
                    g.append(gSub)  # add to temporary group; will act as a set
            found.append(len(g))
        if found:
            self.feature.vector[0] = statistics.pstdev(found)
        else:
            raise JSymbolicFeatureException('input lacks notes')


class VoiceEqualityNumberOfNotesFeature(featuresModule.FeatureExtractor):
    '''
    Not implemented



    TODO: implement

    Standard deviation of the total number of Note Ons in each channel
    that contains at least one note.
    '''
    id = 'T4'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Voice Equality - Number of Notes'
        self.description = ('Standard deviation of the total number of Note Ons '
                            'in each channel that contains at least one note.')
        self.isSequential = True
        self.dimensions = 1


class VoiceEqualityNoteDurationFeature(featuresModule.FeatureExtractor):
    '''
    Not implemented



    TODO: implement

    '''
    id = 'T5'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Voice Equality - Note Duration'
        self.description = ('Standard deviation of the total duration of notes in seconds '
                            'in each channel that contains at least one note.')
        self.isSequential = True
        self.dimensions = 1


class VoiceEqualityDynamicsFeature(featuresModule.FeatureExtractor):
    '''
    Not implemented



    TODO: implement

    '''
    id = 'T6'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Voice Equality - Dynamics'
        self.description = ('Standard deviation of the average volume of notes '
                            'in each channel that contains at least one note.')
        self.isSequential = True
        self.dimensions = 1


class VoiceEqualityMelodicLeapsFeature(featuresModule.FeatureExtractor):
    '''
    Not implemented



    TODO: implement

    '''
    id = 'T7'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Voice Equality - Melodic Leaps'
        self.description = '''Standard deviation of the average melodic leap in MIDI pitches
        for each channel that contains at least one note.'''
        self.isSequential = True
        self.dimensions = 1


class VoiceEqualityRangeFeature(featuresModule.FeatureExtractor):
    '''
    Not implemented

    Standard deviation of the differences between the highest and lowest
    pitches in each channel that contains at least one note.
    '''
    id = 'T8'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Voice Equality - Range'
        self.description = '''Standard deviation of the differences between the
        highest and lowest pitches in each channel that contains at least one note.'''
        self.isSequential = True
        self.dimensions = 1


class ImportanceOfLoudestVoiceFeature(featuresModule.FeatureExtractor):
    '''
    Not implemented



    TODO: implement

    '''
    id = 'T9'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Importance of Loudest Voice'
        self.description = '''Difference between the average loudness of the loudest channel
        and the average loudness of the other channels that contain at least one note.'''
        self.isSequential = True
        self.dimensions = 1


class RelativeRangeOfLoudestVoiceFeature(featuresModule.FeatureExtractor):
    '''
    Not implemented



    TODO: implement

    '''
    id = 'T10'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Relative Range of Loudest Voice'
        self.description = '''Difference between the highest note and the lowest note
        played in the channel with the highest average loudness divided by the difference
        between the highest note and the lowest note overall in the piece.'''
        self.isSequential = True
        self.dimensions = 1


class RangeOfHighestLineFeature(featuresModule.FeatureExtractor):
    '''
    Not implemented



    TODO: implement

    '''
    id = 'T12'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Range of Highest Line'
        self.description = '''Difference between the highest note and the lowest note
        played in the channel with the highest average pitch divided by the difference
        between the highest note and the lowest note in the piece.'''
        self.isSequential = True
        self.dimensions = 1


class RelativeNoteDensityOfHighestLineFeature(featuresModule.FeatureExtractor):
    '''
    Not implemented



    TODO: implement

    '''
    id = 'T13'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Relative Note Density of Highest Line'
        self.description = '''Number of Note Ons in the channel with the highest average
        pitch divided by the average number of Note Ons in all channels that contain at
        least one note.'''
        self.isSequential = True
        self.dimensions = 1


class MelodicIntervalsInLowestLineFeature(featuresModule.FeatureExtractor):
    '''
    Not implemented



    TODO: implement

    '''
    id = 'T15'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Melodic Intervals in Lowest Line'
        self.description = '''Average melodic interval in semitones of the channel
        with the lowest average pitch divided by the average melodic interval of all
        channels that contain at least two notes.'''
        self.isSequential = True
        self.dimensions = 1


class VoiceSeparationFeature(featuresModule.FeatureExtractor):
    '''
    Not implemented

    Average separation in semi-tones between the average pitches of consecutive
    channels (after sorting based/non average pitch) that contain at least one note.
    '''
    id = 'T20'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Voice Separation'
        self.description = '''Average separation in semi-tones between the average pitches of
        consecutive channels (after sorting based/non average pitch) that contain at
        least one note.'''
        self.isSequential = True
        self.dimensions = 1


# ------------------------------------------------------------------------------
# instrumentation


class PitchedInstrumentsPresentFeature(featuresModule.FeatureExtractor):
    '''
    Which pitched General MIDI Instruments are present. There is one entry
    for each instrument, which is set to 1.0 if there is at least one Note On
    in the recording corresponding to the instrument and to 0.0 if there is not.

    >>> s1 = stream.Stream()
    >>> s1.append(instrument.AcousticGuitar())
    >>> s1.append(note.Note())
    >>> s1.append(instrument.Tuba())
    >>> s1.append(note.Note())
    >>> fe = features.jSymbolic.PitchedInstrumentsPresentFeature(s1)
    >>> fe.extract().vector
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
     1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
     0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
     1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
     0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
     0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    '''
    id = 'I1'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Pitched Instruments Present'
        self.description = '''Which pitched General MIDI Instruments are present.
        There is one entry for each instrument, which is set to 1.0 if there is at
        least one Note On in the recording corresponding to the instrument and to
        0.0 if there is not.'''
        self.isSequential = True
        self.dimensions = 128

    def process(self):
        '''Do processing necessary, storing result in feature.
        '''
        s = self.data['partitionByInstrument']
        # each part has content for each instrument
        # count = 0
        if s is not None:
            for p in s.parts:
                # always one instrument
                x = p.getElementsByClass('Instrument')
                if x:
                    i = x[0]
                    if p.recurse().notes:
                        self.feature.vector[i.midiProgram] = 1
                else:
                    pass
        else:
            raise JSymbolicFeatureException('input lacks instruments')


class UnpitchedInstrumentsPresentFeature(featuresModule.FeatureExtractor):
    '''
    Not yet implemented

    Which unpitched MIDI Percussion Key Map instruments are present.
    There is one entry for each instrument, which is set to 1.0 if there is
    at least one Note On in the recording corresponding to the instrument and to
    0.0 if there is not. It should be noted that only instruments 35 to 81 are included here,
    as they are the ones that meet the official standard. They are numbered in this
    array from 0 to 46.
    '''
    # NOTE: this is incorrect: these are not instruments 35 to 81, but pitch
    # values in for events on midi program channel 10

    id = 'I2'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Unpitched Instruments Present'
        self.description = '''Which unpitched MIDI Percussion Key Map instruments are present.
        There is one entry for each instrument, which is set to 1.0 if there is at least one
        Note On in the recording corresponding to the instrument and to 0.0 if there is not.
        It should be noted that only instruments 35 to 81 are included here, as they are the
        ones that meet the official standard. They are numbered in this array from 0 to 46.'''
        self.isSequential = True
        self.dimensions = 47

    def process(self):
        raise JSymbolicFeatureException('not yet implemented')
        # TODO: implement


class NotePrevalenceOfPitchedInstrumentsFeature(
        featuresModule.FeatureExtractor):
    '''

    >>> s1 = stream.Stream()
    >>> s1.append(instrument.AcousticGuitar())
    >>> s1.repeatAppend(note.Note(), 4)
    >>> s1.append(instrument.Tuba())
    >>> s1.append(note.Note())
    >>> fe = features.jSymbolic.NotePrevalenceOfPitchedInstrumentsFeature(s1)
    >>> fe.extract().vector
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
     0.8..., 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
     0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.2...,
     0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
     0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
     0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
     0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

    '''
    id = 'I3'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Note Prevalence of Pitched Instruments'
        self.description = ('The fraction of (pitched) notes played by each '
                            'General MIDI Instrument. There is one entry for '
                            'each instrument, which is set to the number of '
                            'Note Ons played using the corresponding MIDI patch '
                            'divided by the total number of Note Ons in the recording.')
        self.isSequential = True
        self.dimensions = 128

    def process(self):
        '''Do processing necessary, storing result in feature.
        '''
        s = self.data['partitionByInstrument']
        total = sum(self.data['pitches.pitchClassHistogram'])
        # each part has content for each instrument
        # count = 0
        if not s:
            raise JSymbolicFeatureException('input lacks notes')
        for p in s.parts:
            # always one instrument
            i = p.getElementsByClass('Instrument')[0]
            pNotes = p.recurse().notes
            if pNotes:
                self.feature.vector[i.midiProgram] = len(pNotes) / float(total)


class NotePrevalenceOfUnpitchedInstrumentsFeature(
        featuresModule.FeatureExtractor):
    '''
    Not implemented



    TODO: implement

    '''
    id = 'I4'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Note Prevalence of Unpitched Instruments'
        self.description = '''The fraction of (unpitched) notes played by each General MIDI
        Percussion Key Map Instrument. There is one entry for each instrument, which is set
        to the number of Note Ons played using the corresponding MIDI note value divided by
        the total number of Note Ons in the recording. It should be noted that only instruments
        35 to 81 are included here, as they are the ones that meet the official standard.
        They are numbered in this array from 0 to 46.'''
        self.isSequential = True
        self.dimensions = 47

    # TODO: need to find events in channel 10.


class TimePrevalenceOfPitchedInstrumentsFeature(
        featuresModule.FeatureExtractor):
    '''
    Not implemented

    The fraction of the total time of the recording in
    which a note was sounding for each (pitched) General
    MIDI Instrument. There is one entry for each instrument,
    which is set to the total time in seconds during which a
    given instrument was sounding one or more notes divided by the total length
    in seconds of the piece.'

    TODO: implement

    '''
    id = 'I5'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Time Prevalence of Pitched Instruments'
        self.description = ('The fraction of the total time of the recording in which a note '
                            'was sounding for each (pitched) General MIDI Instrument. '
                            'There is one entry for each instrument, which is set to the total '
                            'time in seconds during which a given instrument was sounding one '
                            'or more notes divided by the total length in seconds of the piece.')
        self.isSequential = True
        self.dimensions = 128
    # TODO: this can be done by symbolic duration in native.py


class VariabilityOfNotePrevalenceOfPitchedInstrumentsFeature(
        featuresModule.FeatureExtractor):
    '''
    Standard deviation of the fraction of Note Ons played
    by each (pitched) General MIDI instrument that is
    used to play at least one note.

    >>> s1 = stream.Stream()
    >>> s1.append(instrument.AcousticGuitar())
    >>> s1.repeatAppend(note.Note(), 5)
    >>> s1.append(instrument.Tuba())
    >>> s1.append(note.Note())
    >>> fe = features.jSymbolic.VariabilityOfNotePrevalenceOfPitchedInstrumentsFeature(s1)
    >>> fe.extract().vector
    [0.33333...]

    '''
    id = 'I6'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Variability of Note Prevalence of Pitched Instruments'
        self.description = ('Standard deviation of the fraction of Note Ons played '
                            'by each (pitched) General MIDI instrument that is '
                            'used to play at least one note.')
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        s = self.data['partitionByInstrument']
        total = sum(self.data['pitches.pitchClassHistogram'])
        if not s:
            raise JSymbolicFeatureException('input lacks instruments')
        if not total:
            raise JSymbolicFeatureException('input lacks notes')
        # each part has content for each instrument
        coll = []
        for p in s.parts:
            # always one instrument
            i = p.iter.getElementsByClass('Instrument')[0]
            pNotes = p.recurse().notes
            if pNotes:
                coll.append(len(pNotes) / float(total))
        # would be faster to use numpy
        # numpy.std(coll)
        mean = sum(coll) / len(coll)
        # squared deviations from the mean
        partial = [pow(n - mean, 2) for n in coll]
        self.feature.vector[0] = math.sqrt(sum(partial) / len(partial))


class VariabilityOfNotePrevalenceOfUnpitchedInstrumentsFeature(
        featuresModule.FeatureExtractor):
    '''
    Not implemented

    Standard deviation of the fraction of Note Ons played by each (unpitched) MIDI Percussion Key
    Map instrument that is used to play at least one note. It should be noted that only
    instruments 35 to 81 are included here, as they are the ones that are included in the
    official standard.


    TODO: implement

    '''
    id = 'I7'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Variability of Note Prevalence of Unpitched Instruments'
        self.description = (
            'Standard deviation of the fraction of Note Ons played by each (unpitched) '
            'MIDI Percussion Key Map instrument that is used to play at least one note. '
            'It should be noted that only instruments 35 to 81 are included here, '
            'as they are the ones that are included in the official standard.')
        self.isSequential = True
        self.dimensions = 1


class NumberOfPitchedInstrumentsFeature(featuresModule.FeatureExtractor):
    '''
    Total number of General MIDI patches that are used to play at least one note.

    >>> s1 = stream.Stream()
    >>> s1.append(instrument.AcousticGuitar())
    >>> s1.append(note.Note())
    >>> s1.append(instrument.Tuba())
    >>> s1.append(note.Note())
    >>> fe = features.jSymbolic.NumberOfPitchedInstrumentsFeature(s1)
    >>> fe.extract().vector
    [2]

    '''
    id = 'I8'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Number of Pitched Instruments'
        self.description = ('Total number of General MIDI patches that are used to '
                            'play at least one note.')
        self.isSequential = True
        self.dimensions = 1

    def process(self):
        '''Do processing necessary, storing result in feature.
        '''
        s = self.data['partitionByInstrument']
        # each part has content for each instrument
        count = 0
        if not s:
            raise JSymbolicFeatureException('input lacks instruments')
        for p in s.parts:
            if p.recurse().notes:
                count += 1
        self.feature.vector[0] = count


class NumberOfUnpitchedInstrumentsFeature(featuresModule.FeatureExtractor):
    '''
    Not implemented

    Number of distinct MIDI Percussion Key Map patches that were used to play at
    least one note. It should be noted that only instruments 35 to 81 are
    included here, as they are the ones that are included in the official standard.

    TODO: implement
    '''

    id = 'I9'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Number of Unpitched Instruments'
        self.description = ('Number of distinct MIDI Percussion Key Map patches that were '
                            'used to play at least one note. It should be noted that only '
                            'instruments 35 to 81 are included here, as they are the ones '
                            'that are included in the official standard.')
        self.isSequential = True
        self.dimensions = 1


class PercussionPrevalenceFeature(featuresModule.FeatureExtractor):
    '''
    Not implemented

    Total number of Note Ons corresponding to unpitched percussion instruments
    divided by the total number of Note Ons in the recording.
    '''

    id = 'I10'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Percussion Prevalence'
        self.description = ('Total number of Note Ons corresponding to unpitched percussion '
                            'instruments divided by total number of Note Ons in the recording.')
        self.isSequential = True
        self.dimensions = 1


class InstrumentFractionFeature(featuresModule.FeatureExtractor):
    '''
    TODO: Add description of feature

    This subclass is in-turn subclassed by all FeatureExtractors that
    look at the proportional usage of an Instrument
    '''

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        # subclasses must define
        self._targetPrograms = []

    def process(self):
        '''Do processing necessary, storing result in feature.
        '''
        s = self.data['partitionByInstrument']
        total = sum(self.data['pitches.pitchClassHistogram'])
        count = 0
        if not s:
            raise JSymbolicFeatureException('input lacks instruments')
        if not total:
            raise JSymbolicFeatureException('input lacks notes')
        for p in s.parts:
            i = p.getElementsByClass('Instrument')[0]
            if i.midiProgram in self._targetPrograms:
                count += len(p.flat.notes)
        self.feature.vector[0] = count / float(total)


class StringKeyboardFractionFeature(InstrumentFractionFeature):
    '''
    Fraction of all Note Ons belonging to string keyboard patches
    (General MIDI patches 1 to 8).

    >>> s1 = stream.Stream()
    >>> s1.append(instrument.Piano())
    >>> s1.repeatAppend(note.Note(), 9)
    >>> s1.append(instrument.Tuba())
    >>> s1.append(note.Note())
    >>> fe = features.jSymbolic.StringKeyboardFractionFeature(s1)
    >>> fe.extract().vector
    [0.9...]
    '''

    id = 'I11'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'String Keyboard Fraction'
        self.description = ('Fraction of all Note Ons belonging to string keyboard patches '
                            '(General MIDI patches 1 to 8).')
        self.isSequential = True
        self.dimensions = 1

        self._targetPrograms = range(8)


class AcousticGuitarFractionFeature(InstrumentFractionFeature):
    '''
    A feature extractor that extracts the fraction of all Note Ons belonging to
    acoustic guitar patches (General MIDI patches 25 and 26).

    >>> s1 = stream.Stream()
    >>> s1.append(instrument.AcousticGuitar())
    >>> s1.repeatAppend(note.Note(), 3)
    >>> s1.append(instrument.Tuba())
    >>> s1.append(note.Note())
    >>> fe = features.jSymbolic.AcousticGuitarFractionFeature(s1)
    >>> fe.extract().vector
    [0.75]
    '''

    id = 'I12'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Acoustic Guitar Fraction'
        self.description = ('Fraction of all Note Ons belonging to acoustic guitar patches '
                            '(General MIDI patches 25 and 26).')
        self.isSequential = True
        self.dimensions = 1

        self._targetPrograms = [24, 25]


class ElectricGuitarFractionFeature(InstrumentFractionFeature):
    '''
    >>> s1 = stream.Stream()
    >>> s1.append(instrument.ElectricGuitar())
    >>> s1.repeatAppend(note.Note(), 4)
    >>> s1.append(instrument.Tuba())
    >>> s1.repeatAppend(note.Note(), 4)
    >>> fe = features.jSymbolic.ElectricGuitarFractionFeature(s1)
    >>> fe.extract().vector
    [0.5]
    '''

    id = 'I13'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Electric Guitar Fraction'
        self.description = ('Fraction of all Note Ons belonging to '
                            'electric guitar patches (General MIDI patches 27 to 32).')
        self.isSequential = True
        self.dimensions = 1

        self._targetPrograms = list(range(26, 32))


class ViolinFractionFeature(InstrumentFractionFeature):
    '''
    Fraction of all Note Ons belonging to violin patches (General MIDI
    patches 41 or 111).

    >>> s1 = stream.Stream()
    >>> s1.append(instrument.Violin())
    >>> s1.repeatAppend(note.Note(), 2)
    >>> s1.append(instrument.Tuba())
    >>> s1.repeatAppend(note.Note(), 8)
    >>> fe = features.jSymbolic.ViolinFractionFeature(s1)
    >>> fe.extract().vector
    [0.2...]
    '''

    id = 'I14'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Violin Fraction'
        self.description = ('Fraction of all Note Ons belonging to violin patches '
                            '(General MIDI patches 41 or 111).')
        self.isSequential = True
        self.dimensions = 1

        self._targetPrograms = [40, 110]


class SaxophoneFractionFeature(InstrumentFractionFeature):
    '''
    Fraction of all Note Ons belonging to saxophone patches (General MIDI
    patches 65 through 68).
    # NOTE: incorrect

    >>> s1 = stream.Stream()
    >>> s1.append(instrument.SopranoSaxophone())
    >>> s1.repeatAppend(note.Note(), 6)
    >>> s1.append(instrument.Tuba())
    >>> s1.repeatAppend(note.Note(), 4)
    >>> fe = features.jSymbolic.SaxophoneFractionFeature(s1)
    >>> print(fe.extract().vector[0])
    0.6
    '''
    id = 'I15'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Saxophone Fraction'
        self.description = ('Fraction of all Note Ons belonging to saxophone patches '
                            '(General MIDI patches 65 through 68).')
        self.isSequential = True
        self.dimensions = 1

        self._targetPrograms = [64, 65, 66, 67]


class BrassFractionFeature(InstrumentFractionFeature):
    '''
    A feature extractor that extracts the fraction of all Note Ons
    belonging to brass patches (General MIDI patches 57 through 68).

    TODO: Conflict in source: only does 57-62?

    >>> s1 = stream.Stream()
    >>> s1.append(instrument.SopranoSaxophone())
    >>> s1.repeatAppend(note.Note(), 6)
    >>> s1.append(instrument.Tuba())
    >>> s1.repeatAppend(note.Note(), 4)
    >>> fe = features.jSymbolic.BrassFractionFeature(s1)
    >>> print(fe.extract().vector[0])
    0.4
    '''

    id = 'I16'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Brass Fraction'
        self.description = ('Fraction of all Note Ons belonging to brass patches '
                            '(General MIDI patches 57 through 68).')  # note: incorrect
        self.isSequential = True
        self.dimensions = 1

        self._targetPrograms = list(range(56, 62))


class WoodwindsFractionFeature(InstrumentFractionFeature):
    '''
    Fraction of all Note Ons belonging to woodwind patches
    (General MIDI patches 69 through 76).

    TODO: Conflict in source: does 69-79?

    >>> s1 = stream.Stream()
    >>> s1.append(instrument.Flute())
    >>> s1.repeatAppend(note.Note(), 3)
    >>> s1.append(instrument.Tuba())
    >>> s1.repeatAppend(note.Note(), 7)
    >>> fe = features.jSymbolic.WoodwindsFractionFeature(s1)
    >>> print(fe.extract().vector[0])
    0.3
    '''

    id = 'I17'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Woodwinds Fraction'
        self.description = ('Fraction of all Note Ons belonging to woodwind patches '
                            '(General MIDI patches 69 through 76).')
        self.isSequential = True
        self.dimensions = 1

        self._targetPrograms = list(range(68, 80))  # include ocarina!


class OrchestralStringsFractionFeature(InstrumentFractionFeature):
    '''
    Fraction of all Note Ons belonging to orchestral strings patches
    (General MIDI patches 41 or 47).

    >>> s1 = stream.Stream()
    >>> s1.append(instrument.Violoncello())
    >>> s1.repeatAppend(note.Note(), 4)
    >>> s1.append(instrument.Tuba())
    >>> s1.repeatAppend(note.Note(), 6)
    >>> fe = features.jSymbolic.OrchestralStringsFractionFeature(s1)
    >>> print(fe.extract().vector[0])
    0.4
    '''

    id = 'I18'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Orchestral Strings Fraction'
        self.description = ('Fraction of all Note Ons belonging to orchestral strings patches '
                            '(General MIDI patches 41 or 47).')
        self.isSequential = True
        self.dimensions = 1

        self._targetPrograms = list(range(41, 46))


class StringEnsembleFractionFeature(InstrumentFractionFeature):
    '''
    Not implemented

    Fraction of all Note Ons belonging to string ensemble patches
    (General MIDI patches 49 to 52).
    '''
    # TODO: add tests, do not yet have instrument to model

    id = 'I19'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'String Ensemble Fraction'
        self.description = ('Fraction of all Note Ons belonging to string ensemble patches '
                            '(General MIDI patches 49 to 52).')
        self.isSequential = True
        self.dimensions = 1

        self._targetPrograms = [48, 49, 50, 51]


class ElectricInstrumentFractionFeature(InstrumentFractionFeature):
    '''
    Fraction of all Note Ons belonging to electric instrument patches
    (General MIDI patches 5, 6, 17, 19, 27 through 32, 24 through 40).

    >>> s1 = stream.Stream()
    >>> s1.append(instrument.ElectricOrgan())
    >>> s1.repeatAppend(note.Note(), 8)
    >>> s1.append(instrument.Tuba())
    >>> s1.repeatAppend(note.Note(), 2)
    >>> fe = features.jSymbolic.ElectricInstrumentFractionFeature(s1)
    >>> print(fe.extract().vector[0])
    0.8
    '''
    id = 'I20'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        super().__init__(dataOrStream=dataOrStream, *arguments, **keywords)

        self.name = 'Electric Instrument Fraction'
        self.description = ('Fraction of all Note Ons belonging to electric instrument patches '
                            '(General MIDI patches 5, 6, 17, 19, 27 to 32 or 34 to 40).')
        self.isSequential = True
        self.dimensions = 1

        self._targetPrograms = [4, 5, 16, 18, 26, 27, 28, 29,
                                30, 31, 33, 34, 35, 36, 37, 38, 39]  # accept synth bass


# -----------------------------------------------------------------------------
class JSymbolicFeatureException(featuresModule.FeatureException):
    pass


extractorsById = OrderedDict([
    ('D', [
        None,
        OverallDynamicRangeFeature,
        VariationOfDynamicsFeature,
        VariationOfDynamicsInEachVoiceFeature,
        AverageNoteToNoteDynamicsChangeFeature,
    ]),
    ('I', [
        None,
        PitchedInstrumentsPresentFeature,
        UnpitchedInstrumentsPresentFeature,
        NotePrevalenceOfPitchedInstrumentsFeature,
        NotePrevalenceOfUnpitchedInstrumentsFeature,
        TimePrevalenceOfPitchedInstrumentsFeature,
        VariabilityOfNotePrevalenceOfPitchedInstrumentsFeature,
        VariabilityOfNotePrevalenceOfUnpitchedInstrumentsFeature,
        NumberOfPitchedInstrumentsFeature,
        NumberOfUnpitchedInstrumentsFeature,
        PercussionPrevalenceFeature,
        StringKeyboardFractionFeature,
        AcousticGuitarFractionFeature,
        ElectricGuitarFractionFeature,
        ViolinFractionFeature,
        SaxophoneFractionFeature,
        BrassFractionFeature,
        WoodwindsFractionFeature,
        OrchestralStringsFractionFeature,
        StringEnsembleFractionFeature,
        ElectricInstrumentFractionFeature,
    ]),
    ('M', [
        None,
        MelodicIntervalHistogramFeature,
        AverageMelodicIntervalFeature,
        MostCommonMelodicIntervalFeature,
        DistanceBetweenMostCommonMelodicIntervalsFeature,
        MostCommonMelodicIntervalPrevalenceFeature,
        RelativeStrengthOfMostCommonIntervalsFeature,
        NumberOfCommonMelodicIntervalsFeature,
        AmountOfArpeggiationFeature,
        RepeatedNotesFeature,
        ChromaticMotionFeature,
        StepwiseMotionFeature,
        MelodicThirdsFeature,
        MelodicFifthsFeature,
        MelodicTritonesFeature,
        MelodicOctavesFeature,
        None,  # EmbellishmentFeature,
        DirectionOfMotionFeature,
        DurationOfMelodicArcsFeature,
        SizeOfMelodicArcsFeature,
        None,  # MelodicPitchVarietyFeature,
    ]),
    ('P', [
        None,
        MostCommonPitchPrevalenceFeature,
        MostCommonPitchClassPrevalenceFeature,
        RelativeStrengthOfTopPitchesFeature,
        RelativeStrengthOfTopPitchClassesFeature,
        IntervalBetweenStrongestPitchesFeature,
        IntervalBetweenStrongestPitchClassesFeature,
        NumberOfCommonPitchesFeature,
        PitchVarietyFeature,
        PitchClassVarietyFeature,
        RangeFeature,
        MostCommonPitchFeature,
        PrimaryRegisterFeature,
        ImportanceOfBassRegisterFeature,
        ImportanceOfMiddleRegisterFeature,
        ImportanceOfHighRegisterFeature,
        MostCommonPitchClassFeature,
        DominantSpreadFeature,
        StrongTonalCentresFeature,
        BasicPitchHistogramFeature,
        PitchClassDistributionFeature,
        FifthsPitchHistogramFeature,
        QualityFeature,
        GlissandoPrevalenceFeature,
        AverageRangeOfGlissandosFeature,
        VibratoPrevalenceFeature,
        None,  # PrevalenceOfMicroTonesFeature,
    ]),
    ('R', [
        None,
        StrongestRhythmicPulseFeature,
        SecondStrongestRhythmicPulseFeature,
        HarmonicityOfTwoStrongestRhythmicPulsesFeature,
        StrengthOfStrongestRhythmicPulseFeature,
        StrengthOfSecondStrongestRhythmicPulseFeature,
        StrengthRatioOfTwoStrongestRhythmicPulsesFeature,
        CombinedStrengthOfTwoStrongestRhythmicPulsesFeature,
        NumberOfStrongPulsesFeature,
        NumberOfModeratePulsesFeature,
        NumberOfRelativelyStrongPulsesFeature,
        RhythmicLoosenessFeature,
        PolyrhythmsFeature,
        RhythmicVariabilityFeature,
        BeatHistogramFeature,
        NoteDensityFeature,
        None,  # NoteDensityVariabilityFeature
        AverageNoteDurationFeature,
        VariabilityOfNoteDurationFeature,
        MaximumNoteDurationFeature,
        MinimumNoteDurationFeature,
        StaccatoIncidenceFeature,
        AverageTimeBetweenAttacksFeature,
        VariabilityOfTimeBetweenAttacksFeature,
        AverageTimeBetweenAttacksForEachVoiceFeature,
        AverageVariabilityOfTimeBetweenAttacksForEachVoiceFeature,
        None,  # IncidenceOfCompleteRestsFeature,
        None,  # MaximumCompleteRestDurationFeature,
        None,  # AverageRestDurationPerVoiceFeature,
        None,  # AverageVariabilityOfRestDurationsAcrossVoicesFeature,
        InitialTempoFeature,
        InitialTimeSignatureFeature,
        CompoundOrSimpleMeterFeature,
        TripleMeterFeature,
        QuintupleMeterFeature,
        ChangesOfMeterFeature,
        DurationFeature,
    ]),
    ('T', [
        None,
        MaximumNumberOfIndependentVoicesFeature,
        AverageNumberOfIndependentVoicesFeature,
        VariabilityOfNumberOfIndependentVoicesFeature,
        VoiceEqualityNumberOfNotesFeature,
        VoiceEqualityNoteDurationFeature,
        VoiceEqualityDynamicsFeature,
        VoiceEqualityMelodicLeapsFeature,
        VoiceEqualityRangeFeature,
        ImportanceOfLoudestVoiceFeature,
        RelativeRangeOfLoudestVoiceFeature,
        None,  # RelativeRangeIsolationOfLoudestVoiceFeature,
        RangeOfHighestLineFeature,
        RelativeNoteDensityOfHighestLineFeature,
        None,  # RelativeNoteDurationsOfLowestLineFeature
        MelodicIntervalsInLowestLineFeature,
        None,  # SimultaneityFeature
        None,  # VariabilityOfSimultaneityFeature
        None,  # VoiceOverlapFeature
        None,  # ParallelMotionFeature
        VoiceSeparationFeature,
    ]),
    ('C', [
        None,
        None,  # VerticalIntervalsFeature,
        None,  # ChordTypesFeature,
        None,  # MostCommonVerticalIntervalFeature,
        None,  # SecondMostCommonVerticalIntervalFeature,
        None,  # DistanceBetweenTwoMostCommonVerticalIntervalsFeature,
        None,  # PrevalenceOfMostCommonVerticalIntervalFeature,
        None,  # PrevalenceOfSecondMostCommonVerticalIntervalFeature,
        None,  # RatioOfPrevalenceOfTwoMostCommonVerticalIntervalsFeature,
        None,  # AverageNumberOfSimultaneousPitchClassesFeature,
        None,  # VariabilityOfNumberOfSimultaneousPitchClassesFeature,
        None,  # MinorMajorRatioFeature,
        None,  # PerfectVerticalIntervalsFeature,
        None,  # UnisonsFeature,
        None,  # VerticalMinorSecondsFeature,
        None,  # VerticalThirdsFeature,
        None,  # VerticalFifthsFeature,
        None,  # VerticalTritonesFeature,
        None,  # VerticalOctavesFeature,
        None,  # VerticalDissonanceRatioFeature,
        None,  # PartialChordsFeature,
        None,  # MinorMajorTriadRatioFeature,
        None,  # StandardTriadsFeature,
        None,  # DiminishedAndAugmentedTriadsFeature,
        None,  # DominantSeventhChordsFeature,
        None,  # SeventhsChordsFeature,
        None,  # ComplexChordsFeature,
        None,  # NonStandardChordsFeature,
        None,  # ChordDurationFeature,
    ]),

])


def getExtractorByTypeAndNumber(extractorType, number):
    '''
    Typical usage:

    >>> t5 = features.jSymbolic.getExtractorByTypeAndNumber('T', 5)
    >>> t5.__name__
    'VoiceEqualityNoteDurationFeature'
    >>> bachExample = corpus.parse('bach/bwv66.6')
    >>> fe = t5(bachExample)

    Features unimplemented in jSymbolic but documented in the dissertation return None

    >>> features.jSymbolic.getExtractorByTypeAndNumber('C', 20) is None
    True

    Totally unknown features return an exception:

    >>> features.jSymbolic.getExtractorByTypeAndNumber('L', 900)
    Traceback (most recent call last):
    music21.features.jSymbolic.JSymbolicFeatureException: Could not find
        any jSymbolic features of type L

    >>> features.jSymbolic.getExtractorByTypeAndNumber('C', 200)
    Traceback (most recent call last):
    music21.features.jSymbolic.JSymbolicFeatureException: jSymbolic
        features of type C do not have number 200

    You could also find all the feature extractors this way:

    >>> fs = features.jSymbolic.extractorsById
    >>> for k in fs:
    ...     for i in range(len(fs[k])):
    ...       if fs[k][i] is not None:
    ...         n = fs[k][i].__name__
    ...         if fs[k][i] not in features.jSymbolic.featureExtractors:
    ...            n += ' (not implemented)'
    ...         print('%s %d %s' % (k, i, n))
    D 1 OverallDynamicRangeFeature (not implemented)
    D 2 VariationOfDynamicsFeature (not implemented)
    D 3 VariationOfDynamicsInEachVoiceFeature (not implemented)
    D 4 AverageNoteToNoteDynamicsChangeFeature (not implemented)
    I 1 PitchedInstrumentsPresentFeature
    I 2 UnpitchedInstrumentsPresentFeature (not implemented)
    I 3 NotePrevalenceOfPitchedInstrumentsFeature
    I 4 NotePrevalenceOfUnpitchedInstrumentsFeature (not implemented)
    I 5 TimePrevalenceOfPitchedInstrumentsFeature (not implemented)
    I 6 VariabilityOfNotePrevalenceOfPitchedInstrumentsFeature
    I 7 VariabilityOfNotePrevalenceOfUnpitchedInstrumentsFeature (not implemented)
    I 8 NumberOfPitchedInstrumentsFeature
    I 9 NumberOfUnpitchedInstrumentsFeature (not implemented)
    I 10 PercussionPrevalenceFeature (not implemented)
    I 11 StringKeyboardFractionFeature
    I 12 AcousticGuitarFractionFeature
    I 13 ElectricGuitarFractionFeature
    I 14 ViolinFractionFeature
    I 15 SaxophoneFractionFeature
    I 16 BrassFractionFeature
    I 17 WoodwindsFractionFeature
    I 18 OrchestralStringsFractionFeature
    I 19 StringEnsembleFractionFeature
    I 20 ElectricInstrumentFractionFeature
    M 1 MelodicIntervalHistogramFeature
    M 2 AverageMelodicIntervalFeature
    M 3 MostCommonMelodicIntervalFeature
    M 4 DistanceBetweenMostCommonMelodicIntervalsFeature
    M 5 MostCommonMelodicIntervalPrevalenceFeature
    M 6 RelativeStrengthOfMostCommonIntervalsFeature
    M 7 NumberOfCommonMelodicIntervalsFeature
    M 8 AmountOfArpeggiationFeature
    M 9 RepeatedNotesFeature
    M 10 ChromaticMotionFeature
    M 11 StepwiseMotionFeature
    M 12 MelodicThirdsFeature
    M 13 MelodicFifthsFeature
    M 14 MelodicTritonesFeature
    M 15 MelodicOctavesFeature
    M 17 DirectionOfMotionFeature
    M 18 DurationOfMelodicArcsFeature
    M 19 SizeOfMelodicArcsFeature
    P 1 MostCommonPitchPrevalenceFeature
    P 2 MostCommonPitchClassPrevalenceFeature
    P 3 RelativeStrengthOfTopPitchesFeature
    P 4 RelativeStrengthOfTopPitchClassesFeature
    P 5 IntervalBetweenStrongestPitchesFeature
    P 6 IntervalBetweenStrongestPitchClassesFeature
    P 7 NumberOfCommonPitchesFeature
    P 8 PitchVarietyFeature
    P 9 PitchClassVarietyFeature
    P 10 RangeFeature
    P 11 MostCommonPitchFeature
    P 12 PrimaryRegisterFeature
    P 13 ImportanceOfBassRegisterFeature
    P 14 ImportanceOfMiddleRegisterFeature
    P 15 ImportanceOfHighRegisterFeature
    P 16 MostCommonPitchClassFeature
    P 17 DominantSpreadFeature (not implemented)
    P 18 StrongTonalCentresFeature (not implemented)
    P 19 BasicPitchHistogramFeature
    P 20 PitchClassDistributionFeature
    P 21 FifthsPitchHistogramFeature
    P 22 QualityFeature
    P 23 GlissandoPrevalenceFeature (not implemented)
    P 24 AverageRangeOfGlissandosFeature (not implemented)
    P 25 VibratoPrevalenceFeature (not implemented)
    R 1 StrongestRhythmicPulseFeature (not implemented)
    R 2 SecondStrongestRhythmicPulseFeature (not implemented)
    R 3 HarmonicityOfTwoStrongestRhythmicPulsesFeature (not implemented)
    R 4 StrengthOfStrongestRhythmicPulseFeature (not implemented)
    R 5 StrengthOfSecondStrongestRhythmicPulseFeature (not implemented)
    R 6 StrengthRatioOfTwoStrongestRhythmicPulsesFeature (not implemented)
    R 7 CombinedStrengthOfTwoStrongestRhythmicPulsesFeature (not implemented)
    R 8 NumberOfStrongPulsesFeature (not implemented)
    R 9 NumberOfModeratePulsesFeature (not implemented)
    R 10 NumberOfRelativelyStrongPulsesFeature (not implemented)
    R 11 RhythmicLoosenessFeature (not implemented)
    R 12 PolyrhythmsFeature (not implemented)
    R 13 RhythmicVariabilityFeature (not implemented)
    R 14 BeatHistogramFeature (not implemented)
    R 15 NoteDensityFeature
    R 17 AverageNoteDurationFeature
    R 18 VariabilityOfNoteDurationFeature
    R 19 MaximumNoteDurationFeature
    R 20 MinimumNoteDurationFeature
    R 21 StaccatoIncidenceFeature
    R 22 AverageTimeBetweenAttacksFeature
    R 23 VariabilityOfTimeBetweenAttacksFeature
    R 24 AverageTimeBetweenAttacksForEachVoiceFeature
    R 25 AverageVariabilityOfTimeBetweenAttacksForEachVoiceFeature
    R 30 InitialTempoFeature
    R 31 InitialTimeSignatureFeature
    R 32 CompoundOrSimpleMeterFeature
    R 33 TripleMeterFeature
    R 34 QuintupleMeterFeature
    R 35 ChangesOfMeterFeature
    R 36 DurationFeature
    T 1 MaximumNumberOfIndependentVoicesFeature
    T 2 AverageNumberOfIndependentVoicesFeature
    T 3 VariabilityOfNumberOfIndependentVoicesFeature
    T 4 VoiceEqualityNumberOfNotesFeature (not implemented)
    T 5 VoiceEqualityNoteDurationFeature (not implemented)
    T 6 VoiceEqualityDynamicsFeature (not implemented)
    T 7 VoiceEqualityMelodicLeapsFeature (not implemented)
    T 8 VoiceEqualityRangeFeature (not implemented)
    T 9 ImportanceOfLoudestVoiceFeature (not implemented)
    T 10 RelativeRangeOfLoudestVoiceFeature (not implemented)
    T 12 RangeOfHighestLineFeature (not implemented)
    T 13 RelativeNoteDensityOfHighestLineFeature (not implemented)
    T 15 MelodicIntervalsInLowestLineFeature (not implemented)
    T 20 VoiceSeparationFeature (not implemented)
    '''
    try:
        return extractorsById[extractorType][number]
    except KeyError:
        raise JSymbolicFeatureException(
            'Could not find any jSymbolic features of type %s' % (extractorType))
    except IndexError:
        raise JSymbolicFeatureException(
            'jSymbolic features of type %s do not have number %d' % (extractorType, number))


featureExtractors = [

    MelodicIntervalHistogramFeature,  # m1
    AverageMelodicIntervalFeature,  # m2
    MostCommonMelodicIntervalFeature,  # m3
    DistanceBetweenMostCommonMelodicIntervalsFeature,  # m4
    MostCommonMelodicIntervalPrevalenceFeature,  # m5
    RelativeStrengthOfMostCommonIntervalsFeature,  # m6
    NumberOfCommonMelodicIntervalsFeature,  # m7
    AmountOfArpeggiationFeature,  # m8
    RepeatedNotesFeature,  # m9
    ChromaticMotionFeature,  # m10
    StepwiseMotionFeature,  # m11
    MelodicThirdsFeature,  # m12
    MelodicFifthsFeature,  # m13
    MelodicTritonesFeature,  # m14
    MelodicOctavesFeature,  # m15
    DirectionOfMotionFeature,  # m17
    DurationOfMelodicArcsFeature,  # m18
    SizeOfMelodicArcsFeature,  # m 19

    PitchedInstrumentsPresentFeature,  # i1
    NotePrevalenceOfPitchedInstrumentsFeature,  # i3
    VariabilityOfNotePrevalenceOfPitchedInstrumentsFeature,  # i6
    NumberOfPitchedInstrumentsFeature,  # i8
    StringKeyboardFractionFeature,  # i11
    AcousticGuitarFractionFeature,  # i12
    ElectricGuitarFractionFeature,  # i13
    ViolinFractionFeature,  # i14
    SaxophoneFractionFeature,  # i15
    BrassFractionFeature,  # i16
    WoodwindsFractionFeature,  # i17
    OrchestralStringsFractionFeature,  # i18
    StringEnsembleFractionFeature,  # i19
    ElectricInstrumentFractionFeature,  # i20
    # t11 not in jSymbolic
    # t14 not in jSymbolic
    # t16-19 not in jSymbolic

    NoteDensityFeature,  # r15
    AverageNoteDurationFeature,  # r17
    VariabilityOfNoteDurationFeature,  # r18
    MaximumNoteDurationFeature,  # r19
    MinimumNoteDurationFeature,  # r20
    StaccatoIncidenceFeature,  # r21
    AverageTimeBetweenAttacksFeature,  # r22
    VariabilityOfTimeBetweenAttacksFeature,  # r23
    AverageTimeBetweenAttacksForEachVoiceFeature,  # r24
    AverageVariabilityOfTimeBetweenAttacksForEachVoiceFeature,  # r25
    # r26-29 not in jSymbolic
    InitialTempoFeature,  # r30
    InitialTimeSignatureFeature,  # r31
    CompoundOrSimpleMeterFeature,  # r32
    TripleMeterFeature,  # r33
    QuintupleMeterFeature,  # r34
    ChangesOfMeterFeature,  # r35
    DurationFeature,  # r36

    MaximumNumberOfIndependentVoicesFeature,  # t1
    AverageNumberOfIndependentVoicesFeature,  # t2
    VariabilityOfNumberOfIndependentVoicesFeature,  # t3

    MostCommonPitchPrevalenceFeature,  # p1
    MostCommonPitchClassPrevalenceFeature,  # p2
    RelativeStrengthOfTopPitchesFeature,  # p3
    RelativeStrengthOfTopPitchClassesFeature,  # p4
    IntervalBetweenStrongestPitchesFeature,  # p5
    IntervalBetweenStrongestPitchClassesFeature,  # p6
    NumberOfCommonPitchesFeature,  # p7
    PitchVarietyFeature,  # p8
    PitchClassVarietyFeature,  # p9
    RangeFeature,  # p10
    MostCommonPitchFeature,  # p11
    PrimaryRegisterFeature,  # p12
    ImportanceOfBassRegisterFeature,  # p13
    ImportanceOfMiddleRegisterFeature,  # p14
    ImportanceOfHighRegisterFeature,  # p15
    MostCommonPitchClassFeature,  # p16
    BasicPitchHistogramFeature,  # p19
    PitchClassDistributionFeature,  # p20
    FifthsPitchHistogramFeature,  # p21
    QualityFeature,  # p22
    # p26 is not in jSymbolic
    # m16 is not in jSymbolic
    # m20 is not in jSymbolic

    # c types are not in jSymbolic
]


def getCompletionStats():
    '''
    >>> features.jSymbolic.getCompletionStats()
    completion stats: 72/112 (0.6428...)
    '''
    countTotal = 0
    countComplete = 0
    for k in extractorsById:  # a dictionary of lists
        group = extractorsById[k]
        for i in range(len(group)):
            if group[i] is not None:
                unused_n = group[i].__name__
                countTotal += 1
                if group[i] in featureExtractors:
                    countComplete += 1
    print('completion stats: %s/%s (%s)' % (
        countComplete, countTotal, (float(countComplete) / countTotal)))


# ------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def testAverageMelodicIntervalFeature(self):
        from music21 import stream, pitch, note, features
        s = stream.Stream()
        p = pitch.Pitch('c2')
        s.append(note.Note(copy.deepcopy(p)))

        for i in ['p5', 'p5', 'p5', 'p4', 'p4', 'p4']:
            p = p.transpose(i)
            s.append(note.Note(copy.deepcopy(p)))

        fe = features.jSymbolic.AverageMelodicIntervalFeature(s)
        f = fe.extract()
        # average of 3 p5 and 3 p4 is the tritone
        self.assertEqual(f.vector, [6.0])

    def testMostCommonMelodicIntervalFeature(self):
        from music21 import stream, pitch, note, features
        s = stream.Stream()
        p = pitch.Pitch('c2')
        s.append(note.Note(copy.deepcopy(p)))

        for i in ['p5', 'p5', 'p5', 'p4', 'p4', 'p4', 'p4']:
            p = p.transpose(i)
            s.append(note.Note(copy.deepcopy(p)))

        fe = features.jSymbolic.MostCommonMelodicIntervalFeature(s)
        f = fe.extract()
        # average of 3 p5 and 3 p4 is the tritone
        self.assertEqual(f.vector, [5])

    def testDistanceBetweenMostCommonMelodicIntervalsFeature(self):
        from music21 import stream, pitch, note, features
        s = stream.Stream()
        p = pitch.Pitch('c2')
        s.append(note.Note(copy.deepcopy(p)))

        for i in ['p5', 'p5', 'p5', 'p4', 'p4', 'p4', 'p4', 'm2', 'm3']:
            p = p.transpose(i)
            s.append(note.Note(copy.deepcopy(p)))

        fe = features.jSymbolic.DistanceBetweenMostCommonMelodicIntervalsFeature(s)
        f = fe.extract()
        self.assertEqual(f.vector, [2])

    def testMostCommonMelodicIntervalPrevalenceFeature(self):
        from music21 import stream, pitch, note, features
        s = stream.Stream()
        p = pitch.Pitch('c2')
        s.append(note.Note(copy.deepcopy(p)))

        for i in ['p5', 'p5', 'p4', 'p4', 'p4', 'p4', 'm2', 'm3']:
            p = p.transpose(i)
            s.append(note.Note(copy.deepcopy(p)))

        fe = features.jSymbolic.MostCommonMelodicIntervalPrevalenceFeature(s)
        f = fe.extract()
        self.assertEqual(f.vector, [0.5])

    def testRelativeStrengthOfMostCommonIntervalsFeature(self):
        from music21 import stream, pitch, note, features
        s = stream.Stream()
        p = pitch.Pitch('c2')
        s.append(note.Note(copy.deepcopy(p)))

        for i in ['p5', 'p5', 'p5', 'p4', 'p4', 'p4', 'p4', 'm2', 'm3']:
            p = p.transpose(i)
            s.append(note.Note(copy.deepcopy(p)))

        fe = features.jSymbolic.RelativeStrengthOfMostCommonIntervalsFeature(s)
        f = fe.extract()
        self.assertEqual(f.vector, [0.75])

    def testNumberOfCommonMelodicIntervalsFeature(self):
        from music21 import stream, pitch, note, features
        s = stream.Stream()
        p = pitch.Pitch('c2')
        s.append(note.Note(copy.deepcopy(p)))

        for i in ['p5', 'p4', 'p4', 'p4', 'p4', 'p4', 'p4', 'p4', 'p4', 'p4', 'p4', 'm2', 'm3']:
            p = p.transpose(i)
            s.append(note.Note(copy.deepcopy(p)))

        fe = features.jSymbolic.NumberOfCommonMelodicIntervalsFeature(s)
        f = fe.extract()
        self.assertEqual(f.vector, [1])

    def testAmountOfArpeggiationFeature(self):
        from music21 import stream, pitch, note, features
        s = stream.Stream()
        p = pitch.Pitch('c2')
        s.append(note.Note(copy.deepcopy(p)))

        for i in ['m2', 'm2', 'M2', 'M3', 'p5', 'p8']:
            p = p.transpose(i)
            s.append(note.Note(copy.deepcopy(p)))

        fe = features.jSymbolic.AmountOfArpeggiationFeature(s)
        f = fe.extract()
        self.assertEqual(f.vector, [0.5])

    def testRepeatedNotesFeature(self):
        from music21 import stream, pitch, note, features
        s = stream.Stream()
        p = pitch.Pitch('c2')
        s.append(note.Note(copy.deepcopy(p)))

        for i in ['p1', 'p1', 'p1', 'M2', 'M3', 'p5']:
            p = p.transpose(i)
            s.append(note.Note(copy.deepcopy(p)))

        fe = features.jSymbolic.RepeatedNotesFeature(s)
        f = fe.extract()
        self.assertEqual(f.vector, [0.5])

    def testChromaticMotionFeature(self):
        from music21 import stream, pitch, note, features
        s = stream.Stream()
        p = pitch.Pitch('c2')
        s.append(note.Note(copy.deepcopy(p)))

        for i in ['m2', 'm2', 'm2', 'M2', 'M3', 'p5']:
            p = p.transpose(i)
            s.append(note.Note(copy.deepcopy(p)))

        fe = features.jSymbolic.ChromaticMotionFeature(s)
        f = fe.extract()
        self.assertEqual(f.vector, [0.5])

    def testStepwiseMotionFeature(self):
        from music21 import stream, pitch, note, features
        s = stream.Stream()
        p = pitch.Pitch('c2')
        s.append(note.Note(copy.deepcopy(p)))

        for i in ['m2', 'm2', 'm2', 'M2', 'M3', 'p5']:
            p = p.transpose(i)
            s.append(note.Note(copy.deepcopy(p)))

        fe = features.jSymbolic.StepwiseMotionFeature(s)
        f = fe.extract()
        self.assertEqual(f.vector, [2 / 3])

    def testMelodicThirdsFeature(self):
        from music21 import stream, pitch, note, features
        s = stream.Stream()
        p = pitch.Pitch('c2')
        s.append(note.Note(copy.deepcopy(p)))

        for i in ['m2', 'm2', 'm2', 'M2', 'M3', 'p5']:
            p = p.transpose(i)
            s.append(note.Note(copy.deepcopy(p)))

        fe = features.jSymbolic.MelodicThirdsFeature(s)
        f = fe.extract()
        self.assertEqual(f.vector, [1 / 6])

    def testMelodicFifthsFeature(self):
        from music21 import stream, pitch, note, features
        s = stream.Stream()
        p = pitch.Pitch('c2')
        s.append(note.Note(copy.deepcopy(p)))

        for i in ['m2', 'm2', 'm2', 'M2', 'p5', 'p5']:
            p = p.transpose(i)
            s.append(note.Note(copy.deepcopy(p)))

        fe = features.jSymbolic.MelodicFifthsFeature(s)
        f = fe.extract()
        self.assertEqual(f.vector, [2 / 6])

    def testMelodicTritonesFeature(self):
        from music21 import stream, pitch, note, features
        s = stream.Stream()
        p = pitch.Pitch('c2')
        s.append(note.Note(copy.deepcopy(p)))

        for i in ['m2', 'm2', 'm2', 'M2', 'p5', 'd5']:
            p = p.transpose(i)
            s.append(note.Note(copy.deepcopy(p)))

        fe = features.jSymbolic.MelodicTritonesFeature(s)
        f = fe.extract()
        self.assertEqual(f.vector, [1 / 6])

    def testMelodicOctavesFeature(self):
        from music21 import stream, pitch, note, features
        s = stream.Stream()
        p = pitch.Pitch('c2')
        s.append(note.Note(copy.deepcopy(p)))

        for i in ['m2', 'm2', 'm2', 'M2', 'p5', 'p8']:
            p = p.transpose(i)
            s.append(note.Note(copy.deepcopy(p)))

        fe = features.jSymbolic.MelodicOctavesFeature(s)
        f = fe.extract()
        self.assertEqual(f.vector, [1 / 6])

    def testDirectionOfMotionFeature(self):
        from music21 import stream, pitch, note, features
        # all up
        s = stream.Stream()
        p = pitch.Pitch('c2')
        s.append(note.Note(copy.deepcopy(p)))
        for i in ['m2', 'm2', 'm2', 'M2', 'p5', 'p8']:
            p = p.transpose(i)
            s.append(note.Note(copy.deepcopy(p)))
        fe = features.jSymbolic.DirectionOfMotionFeature(s)
        f = fe.extract()
        self.assertEqual(f.vector, [1.0])

        # half down, half up
        s = stream.Stream()
        p = pitch.Pitch('c2')
        s.append(note.Note(copy.deepcopy(p)))
        for i in ['m2', 'm2', '-m2', '-M2', '-p5', 'p8']:
            p = p.transpose(i)
            s.append(note.Note(copy.deepcopy(p)))
        fe = features.jSymbolic.DirectionOfMotionFeature(s)
        f = fe.extract()
        self.assertEqual(f.vector, [0.5])

        # downward only
        s = stream.Stream()
        p = pitch.Pitch('c2')
        s.append(note.Note(copy.deepcopy(p)))
        for i in ['-m2', '-m2', '-m2', '-M2', '-p5', '-p8']:
            p = p.transpose(i)
            s.append(note.Note(copy.deepcopy(p)))
        fe = features.jSymbolic.DirectionOfMotionFeature(s)
        f = fe.extract()
        self.assertEqual(f.vector, [0.0])

    def testDurationOfMelodicArcsFeature(self):
        from music21 import stream, pitch, note, features
        # all up
        # in jSymbolic implementation, all up means there
        # is no melodic arc and thus the average duration
        # of melodic arc is set to 0.
        s = stream.Stream()
        p = pitch.Pitch('c2')
        s.append(note.Note(copy.deepcopy(p)))
        for i in ['m2', 'm2', 'm2', 'M2', 'p5', 'p8']:
            p = p.transpose(i)
            s.append(note.Note(copy.deepcopy(p)))
        fe = features.jSymbolic.DurationOfMelodicArcsFeature(s)
        f = fe.extract()
        self.assertEqual(f.vector, [0])

        s = stream.Stream()
        p = pitch.Pitch('c2')
        s.append(note.Note(copy.deepcopy(p)))
        for i in ['m2', 'm2', '-p8', 'M2', 'p5', '-p8', 'p8', '-p8']:
            p = p.transpose(i)
            s.append(note.Note(copy.deepcopy(p)))
        fe = features.jSymbolic.DurationOfMelodicArcsFeature(s)
        f = fe.extract()
        self.assertAlmostEqual(f.vector[0], 8 / 5)

    def testSizeOfMelodicArcsFeature(self):
        from music21 import stream, pitch, note, features
        # all up
        s = stream.Stream()
        p = pitch.Pitch('c2')
        s.append(note.Note(copy.deepcopy(p)))
        for i in ['m2', 'm2', 'm2', 'M2', 'p5', 'p8']:
            p = p.transpose(i)
            s.append(note.Note(copy.deepcopy(p)))
        fe = features.jSymbolic.SizeOfMelodicArcsFeature(s)
        unused_f = fe.extract()
        # self.assertEqual(f.vector, [5])

        s = stream.Stream()
        p = pitch.Pitch('c2')
        s.append(note.Note(copy.deepcopy(p)))
        for i in ['m2', 'm2', '-p8', 'M2', 'p5', '-p8', 'p8', '-p8']:
            p = p.transpose(i)
            s.append(note.Note(copy.deepcopy(p)))
        fe = features.jSymbolic.SizeOfMelodicArcsFeature(s)
        unused_f = fe.extract()
        # self.assertAlmostEqual(f.vector[0], 1 + 2/3)

    def testNoteDensityFeatureA(self):
        from music21 import stream, note, tempo, features
        s = stream.Stream()
        s.insert(0, tempo.MetronomeMark(number=60))
        s.insert(0, note.Note(quarterLength=8))
        s.insert(1, note.Note(quarterLength=7))
        s.insert(2, note.Note(quarterLength=6))
        s.insert(3, note.Note(quarterLength=5))
        s.insert(4, note.Note(quarterLength=4))
        s.insert(5, note.Note(quarterLength=3))
        s.insert(6, note.Note(quarterLength=2))
        s.insert(7, note.Note(quarterLength=1))

        fe = features.jSymbolic.NoteDensityFeature(s)
        f = fe.extract()
        # 8 notes in the span of 8 seconds
        self.assertAlmostEqual(f.vector[0], 1.0)

        s = stream.Stream()
        s.insert(0, tempo.MetronomeMark(number=240))
        s.insert(0, note.Note(quarterLength=8))
        s.insert(1, note.Note(quarterLength=7))
        s.insert(2, note.Note(quarterLength=6))
        s.insert(3, note.Note(quarterLength=5))
        s.insert(4, note.Note(quarterLength=4))
        s.insert(5, note.Note(quarterLength=3))
        s.insert(6, note.Note(quarterLength=2))
        s.insert(7, note.Note(quarterLength=1))

        # 8 notes in the span of 2 seconds
        fe = features.jSymbolic.NoteDensityFeature(s)
        f = fe.extract()
        self.assertAlmostEqual(f.vector[0], 4.0)

    def testFeatureCount(self):
        from music21 import features
        fs = features.jSymbolic.extractorsById
        feTotal = 0
        feImplemented = 0
        for k in fs:
            for i in range(len(fs[k])):
                if fs[k][i] is not None:
                    feTotal += 1
                    if fs[k][i] in features.jSymbolic.featureExtractors:
                        feImplemented += 1
        environLocal.printDebug(['fe total:', feTotal, 'fe implemented',
                                 feImplemented, 'percent', feImplemented / float(feTotal)])

    def testBeatHistogram(self):
        from music21 import corpus, tempo
        sch = corpus.parse('schoenberg/opus19', 2)
        for p in sch.parts:
            p.insert(0, tempo.MetronomeMark('Langsam', 70))
        fe = StrongestRhythmicPulseFeature(sch)
        f = fe.extract()
        self.assertEqual(140.0, f.vector[0])


if __name__ == '__main__':
    import music21
    music21.mainTest(Test)

