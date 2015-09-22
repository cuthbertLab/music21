# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         features.native.py
# Purpose:      music21 feature extractors
#
# Authors:      Christopher Ariza
#
# Copyright:    Copyright © 2011 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------
'''
Original music21 feature extractors.
'''

import unittest
import re
import math

try: 
    from urllib import FancyURLopener # @UnusedImport @UnresolvedImport  # pylint: disable=no-name-in-module
    from urllib import urlencode # @UnusedImport @UnresolvedImport # pylint: disable=no-name-in-module
except ImportError: # python3 
    from urllib.request import FancyURLopener # @UnresolvedImport @Reimport
    from urllib.parse import urlencode # @UnresolvedImport @Reimport
    
from music21.features import base as featuresModule
from music21.ext import six
from music21 import text
from music21 import environment
_MOD = 'features/native.py'
environLocal = environment.Environment(_MOD)

#from music21.ext import six

#-------------------------------------------------------------------------------
# ideas for other music21 features extactors

# notation features: clef usage, enharmonic usage
# chromatic alteration related to beat position

# key signature histogram
# array of circle of fiths

# lyrics
# luca gloria:
# searching for numbers of hits
# vowel metrical postiion
# idea of language/text specific # DONE

# essen locale and elevation

# automatic key analysis
# as a method of feature extraction

# key detection on windowed segments
# prevalence m/M over 4 bar windwows

# key ambiguity list
# correlation coefficient
# harmony realization also adds pitches not available in midi


#-------------------------------------------------------------------------------
class NativeFeatureException(featuresModule.FeatureException):
    pass


class QualityFeature(featuresModule.FeatureExtractor):
    '''
    Extends the jSymbolic QualityFeature to automatically find mode
    
    Set to 0 if the key signature indicates that 
    a recording is major, set to 1 if it indicates 
    that it is minor.  A Music21
    addition: if no key mode is found in the piece, analyze the piece to
    discover what mode it is most likely in.


    Example: Handel, Rinaldo Aria (musicxml) is explicitly encoded as being in Major:
    
    
    >>> s = corpus.parse('handel/rinaldo/lascia_chio_pianga') 
    >>> fe = features.native.QualityFeature(s)
    >>> f = fe.extract()
    >>> f.vector
    [0]


    now we will try it with the last movement of Schoenberg's opus 19 which has
    no mode explicitly encoded in the musicxml but which our analysis routines
    believe (having very little to go on) fits the profile of e-minor best. 


    >>> schoenberg19mvmt6= corpus.parse('schoenberg/opus19', 6)
    >>> fe2 = features.native.QualityFeature(schoenberg19mvmt6)
    >>> f2 = fe2.extract()
    >>> f2.vector
    [1]


    OMIT_FROM_DOCS
    
    # for monophonic melodies
    # incomplete measures / pickups for monophonic melodies

    '''
    id = 'P22'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        featuresModule.FeatureExtractor.__init__(self, dataOrStream=dataOrStream,  *arguments, **keywords)

        self.name = 'Quality'
        self.description = '''
            Set to 0 if the key signature indicates that 
            a recording is major, set to 1 if it indicates 
            that it is minor and set to 0 if key signature is unknown. Music21
            addition: if no key mode is found in the piece, analyze the piece to
            discover what mode it is most likely in.
            '''
        self.isSequential = True
        self.dimensions = 1

    def _process(self):
        '''Do processing necessary, storing result in _feature.
        '''
        allKeys = self.data['flat.getElementsByClass.KeySignature']
        keyFeature = None
        for x in allKeys:
            if x.mode == 'major':
                keyFeature = 0
                break
            elif x.mode == 'minor':
                keyFeature = 1
                break
        if keyFeature is None:
            analyzedMode = self.data['flat.analyzedKey'].mode
            if analyzedMode == 'major':
                keyFeature = 0
            elif analyzedMode == 'minor':
                keyFeature = 1
            else:
                raise NativeFeatureException("should be able to get a mode from something here -- perhaps there are no notes?")

        self._feature.vector[0] = keyFeature
    

#-------------------------------------------------------------------------------
class TonalCertainty(featuresModule.FeatureExtractor):
    '''    
    >>> s = corpus.parse('bwv66.6') 
    >>> fe = features.native.TonalCertainty(s)
    >>> f = fe.extract()
    >>> f.vector
    [1.26...]

    >>> pitches = [56, 55, 56, 57, 58, 57, 58, 59, 60, 59, 60, 61, 62, 61, 62, 63, 64, 63, 64, 65, 66, 65, 66, 67]
    >>> s = stream.Stream()
    >>> for pitch in pitches:
    ...   s.append(note.Note(pitch))
    >>> features.native.TonalCertainty(s).extract().vector
    [0.0]
    '''
    id = 'K1' # TODO: need id
    def __init__(self, dataOrStream=None, *arguments, **keywords):
        featuresModule.FeatureExtractor.__init__(self, dataOrStream=dataOrStream,  *arguments, **keywords)

        self.name = 'Tonal Certainty'
        self.description = 'A floating point magnitude value that suggest tonal certainty based on automatic key analysis.'
        self.dimensions = 1
        self.discrete = False 

    def _process(self):
        '''Do processing necessary, storing result in _feature.
        '''
        self._feature.vector[0] = self.data['flat.tonalCertainty']


#-------------------------------------------------------------------------------
# features that use metrical distinctions

class FirstBeatAttackPrevalence(featuresModule.FeatureExtractor):
    '''
    >>> s = corpus.parse('bwv66.6') 
    >>> fe = features.native.FirstBeatAttackPrevalence(s)
    >>> f = fe.extract()
    >>> f.vector
    [0]

    TODO: That seems to be a bug!!!
    '''
    id = 'MP1'
    def __init__(self, dataOrStream=None, *arguments, **keywords):
        featuresModule.FeatureExtractor.__init__(self, dataOrStream=dataOrStream,  *arguments, **keywords)

        self.name = 'First Beat Attack Prevalence'
        self.description = 'Fraction of first beats of a measure that have notes that start on this beat.'
        self.dimensions = 1
        self.discrete = False 




#-------------------------------------------------------------------------------
# employing symbolic durations


class UniqueNoteQuarterLengths(featuresModule.FeatureExtractor):
    '''    
    >>> s = corpus.parse('bwv66.6') 
    >>> fe = features.native.UniqueNoteQuarterLengths(s)
    >>> fe.extract().vector 
    [3]
    '''
    id = 'QL1'
    def __init__(self, dataOrStream=None, *arguments, **keywords):
        featuresModule.FeatureExtractor.__init__(self, dataOrStream=dataOrStream,  *arguments, **keywords)

        self.name = 'Unique Note Quarter Lengths'
        self.description = 'The number of unique note quarter lengths.'
        self.dimensions = 1
        self.discrete = True 

    def _process(self):
        '''Do processing necessary, storing result in _feature.
        '''
        count = 0
        histo = self.data['noteQuarterLengthHistogram']
        for key in histo:
            # all defined keys should be greater than zero, but just in case
            if histo[key] > 0:
                count += 1
        self._feature.vector[0] = count


class MostCommonNoteQuarterLength(featuresModule.FeatureExtractor):
    '''
    >>> s = corpus.parse('bwv66.6') 
    >>> fe = features.native.MostCommonNoteQuarterLength(s)
    >>> fe.extract().vector 
    [1.0]
    '''
    id = 'QL2'
    def __init__(self, dataOrStream=None, *arguments, **keywords):
        featuresModule.FeatureExtractor.__init__(self, dataOrStream=dataOrStream,  *arguments, **keywords)

        self.name = 'Most Common Note Quarter Length'
        self.description = 'The value of the most common quarter length.'
        self.dimensions = 1
        self.discrete = False 

    def _process(self):
        '''Do processing necessary, storing result in _feature.
        '''
        histo = self.data['noteQuarterLengthHistogram']
        maximum = 0
        ql = 0
        for key in histo:
            # all defined keys should be greater than zero, but just in case
            if histo[key] >= maximum:
                maximum = histo[key]
                ql = key
        self._feature.vector[0] = ql


class MostCommonNoteQuarterLengthPrevalence(featuresModule.FeatureExtractor):
    '''
    >>> s = corpus.parse('bwv66.6') 
    >>> fe = features.native.MostCommonNoteQuarterLengthPrevalence(s)
    >>> fe.extract().vector 
    [0.60...]
    '''
    id = 'QL3'
    def __init__(self, dataOrStream=None, *arguments, **keywords):
        featuresModule.FeatureExtractor.__init__(self, dataOrStream=dataOrStream,  *arguments, **keywords)

        self.name = 'Most Common Note Quarter Length Prevalence'
        self.description = 'Fraction of notes that have the most common quarter length.'
        self.dimensions = 1
        self.discrete = False 

    def _process(self):
        '''Do processing necessary, storing result in _feature.
        '''
        summation = 0 # count of all 
        histo = self.data['noteQuarterLengthHistogram']
        maxKey = 0 # max found for any one key
        for key in histo:
            # all defined keys should be greater than zero, but just in case
            if histo[key] > 0:
                summation += histo[key]
                if histo[key] >= maxKey:
                    maxKey = histo[key]
        self._feature.vector[0] = maxKey / float(summation)



class RangeOfNoteQuarterLengths(featuresModule.FeatureExtractor):
    '''Difference between the longest and shortest quarter lengths.
    
    >>> s = corpus.parse('bwv66.6') 
    >>> fe = features.native.RangeOfNoteQuarterLengths(s)
    >>> fe.extract().vector 
    [1.5]
    '''
    id = 'QL4'
    def __init__(self, dataOrStream=None, *arguments, **keywords):
        featuresModule.FeatureExtractor.__init__(self, dataOrStream=dataOrStream,  *arguments, **keywords)

        self.name = 'Range of Note Quarter Lengths'
        self.description = 'Difference between the longest and shortest quarter lengths.'
        self.dimensions = 1
        self.discrete = False

    def _process(self):
        '''Do processing necessary, storing result in _feature.
        '''
        histo = self.data['noteQuarterLengthHistogram']
        minVal = min(histo.keys())
        maxVal = max(histo.keys())
        self._feature.vector[0] = maxVal - minVal


#-------------------------------------------------------------------------------
# various ways of looking at chordify representation

# percentage of closed-position chords and
# percentage of closed-position chords above bass  -- which looks at how many
#2 (or 3 in the second one) note chordify simultaneities are the same after
# running .closedPosition() on them.  For the latter, we just delete the
# lowest note of the chord before running that.


class UniquePitchClassSetSimultaneities(featuresModule.FeatureExtractor):
    '''Number of unique pitch class simultaneities.

    >>> s = corpus.parse('bwv66.6') 
    >>> fe = features.native.UniquePitchClassSetSimultaneities(s)
    >>> fe.extract().vector
    [25]
    '''
    id = 'CS1'
    def __init__(self, dataOrStream=None, *arguments, **keywords):
        featuresModule.FeatureExtractor.__init__(self, dataOrStream=dataOrStream,  *arguments, **keywords)

        self.name = 'Unique Pitch Class Set Simultaneities'
        self.description = 'Number of unique pitch class simultaneities.'
        self.dimensions = 1
        self.discrete = False 

    def _process(self):
        '''Do processing necessary, storing result in _feature.
        '''
        count = 0
        histo = self.data['chordifyPitchClassSetHistogram']
        for key in histo:
            # all defined keys should be greater than zero, but just in case
            if histo[key] > 0:
                count += 1
        self._feature.vector[0] = count


class UniqueSetClassSimultaneities(featuresModule.FeatureExtractor):
    '''Number of unique set class simultaneities.
    
    >>> s = corpus.parse('bwv66.6') 
    >>> fe = features.native.UniqueSetClassSimultaneities(s)
    >>> fe.extract().vector
    [12]
    '''
    id = 'CS2'
    def __init__(self, dataOrStream=None, *arguments, **keywords):
        featuresModule.FeatureExtractor.__init__(self, dataOrStream=dataOrStream,  *arguments, **keywords)

        self.name = 'Unique Set Class Simultaneities'
        self.description = 'Number of unique set class simultaneities.'
        self.dimensions = 1
        self.discrete = False 

    def _process(self):
        '''Do processing necessary, storing result in _feature.
        '''
        count = 0
        histo = self.data['chordifySetClassHistogram']
        for key in histo:
            # all defined keys should be greater than zero, but just in case
            if histo[key] > 0:
                count += 1
        self._feature.vector[0] = count


class MostCommonPitchClassSetSimultaneityPrevalence(
    featuresModule.FeatureExtractor):
    '''Fraction of all pitch class simultaneities that are the most common simultaneity.

    >>> s = corpus.parse('bwv66.6') 
    >>> fe = features.native.MostCommonPitchClassSetSimultaneityPrevalence(s)
    >>> fe.extract().vector
    [0.132...]
    '''
    id = 'CS3'
    def __init__(self, dataOrStream=None, *arguments, **keywords):
        featuresModule.FeatureExtractor.__init__(self, dataOrStream=dataOrStream,  *arguments, **keywords)

        self.name = 'Most Common Pitch Class Set Simultaneity Prevalence'
        self.description = 'Fraction of all pitch class simultaneities that are the most common simultaneity.'
        self.dimensions = 1
        self.discrete = False 

    def _process(self):
        '''Do processing necessary, storing result in _feature.
        '''
        summation = 0 # count of all 
        histo = self.data['chordifyPitchClassSetHistogram']
        maxKey = 0 # max found for any one key
        for key in histo:
            # all defined keys should be greater than zero, but just in case
            if histo[key] > 0:
                summation += histo[key]
                if histo[key] >= maxKey:
                    maxKey = histo[key]
        self._feature.vector[0] = maxKey / float(summation)


class MostCommonSetClassSimultaneityPrevalence(featuresModule.FeatureExtractor):
    '''
    Fraction of all set class simultaneities that the most common simultaneity 
    occupies.
    
    >>> s = corpus.parse('bwv66.6') 
    >>> fe = features.native.MostCommonSetClassSimultaneityPrevalence(s)
    >>> fe.extract().vector
    [0.679...]
    >>> s2 = corpus.parse('schoenberg/opus19', 6)
    >>> fe2 = features.native.MostCommonSetClassSimultaneityPrevalence(s2)
    >>> fe2.extract().vector
    [0.184...]
    '''
    id = 'CS4'
    def __init__(self, dataOrStream=None, *arguments, **keywords):
        featuresModule.FeatureExtractor.__init__(self, dataOrStream=dataOrStream,  *arguments, **keywords)

        self.name = 'Most Common Set Class Simultaneity Prevalence'
        self.description = 'Fraction of all set class simultaneities that are the most common simultaneity.'
        self.dimensions = 1
        self.discrete = False 

    def _process(self):
        '''
        Do processing necessary, storing result in _feature.
        '''
        summation = 0 # count of all 
        histo = self.data['chordifySetClassHistogram']
        maxKey = 0 # max found for any one key
        for key in histo:
            # all defined keys should be greater than zero, but just in case
            if histo[key] > 0:
                summation += histo[key]
                if histo[key] >= maxKey:
                    maxKey = histo[key]
        self._feature.vector[0] = maxKey / float(summation)


class MajorTriadSimultaneityPrevalence(featuresModule.FeatureExtractor):
    '''
    Percentage of all simultaneities that are major triads.
    
    >>> s = corpus.parse('bwv66.6') 
    >>> fe = features.native.MajorTriadSimultaneityPrevalence(s)
    >>> fe.extract().vector
    [0.45...]
    '''
    id = 'CS5'
    def __init__(self, dataOrStream=None, *arguments, **keywords):
        featuresModule.FeatureExtractor.__init__(self, dataOrStream=dataOrStream,  *arguments, **keywords)

        self.name = 'Major Triad Simultaneity Prevalence'
        self.description = 'Percentage of all simultaneities that are major triads.'
        self.dimensions = 1
        self.discrete = False 

    def _process(self):
        '''Do processing necessary, storing result in _feature.
        '''
        # use for total number of chords
        total = len(self.data['chordify.getElementsByClass.Chord'])

        histo = self.data['chordifyTypesHistogram']
        # using incomplete
        part = histo['isMajorTriad'] + histo['isIncompleteMajorTriad'] 
        self._feature.vector[0] = part / float(total)


class MinorTriadSimultaneityPrevalence(featuresModule.FeatureExtractor):
    '''Percentage of all simultaneities that are minor triads.
    
    >>> s = corpus.parse('bwv66.6') 
    >>> fe = features.native.MinorTriadSimultaneityPrevalence(s)
    >>> fe.extract().vector # same as major in this work
    [0.226...]
    '''
    id = 'CS6'
    def __init__(self, dataOrStream=None, *arguments, **keywords):
        featuresModule.FeatureExtractor.__init__(self, dataOrStream=dataOrStream,  *arguments, **keywords)

        self.name = 'Minor Triad Simultaneity Prevalence'
        self.description = 'Percentage of all simultaneities that are minor triads.'
        self.dimensions = 1
        self.discrete = False 

    def _process(self):
        '''Do processing necessary, storing result in _feature.
        '''
        # use for total number of chords
        total = len(self.data['chordify.getElementsByClass.Chord'])
        histo = self.data['chordifyTypesHistogram']
        # using incomplete
        part = histo['isMinorTriad'] + histo['isIncompleteMinorTriad'] 
        self._feature.vector[0] = part / float(total)


class DominantSeventhSimultaneityPrevalence(featuresModule.FeatureExtractor):
    '''Percentage of all simultaneities that are dominant seventh.
    
    >>> s = corpus.parse('bwv66.6') 
    >>> fe = features.native.DominantSeventhSimultaneityPrevalence(s)
    >>> fe.extract().vector 
    [0.075...]
    '''
    id = 'CS7'
    def __init__(self, dataOrStream=None, *arguments, **keywords):
        featuresModule.FeatureExtractor.__init__(self, dataOrStream=dataOrStream,  *arguments, **keywords)

        self.name = 'Dominant Seventh Simultaneity Prevalence'
        self.description = 'Percentage of all simultaneities that are dominant seventh.'
        self.dimensions = 1
        self.discrete = False 

    def _process(self):
        '''Do processing necessary, storing result in _feature.
        '''
        # use for total number of chords
        total = len(self.data['chordify.getElementsByClass.Chord'])
        histo = self.data['chordifyTypesHistogram']
        # using incomplete
        part = histo['isDominantSeventh']
        self._feature.vector[0] = part / float(total)


class DiminishedTriadSimultaneityPrevalence(featuresModule.FeatureExtractor):
    '''Percentage of all simultaneities that are diminished triads.

    
    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.native.DiminishedTriadSimultaneityPrevalence(s)
    >>> fe.extract().vector 
    [0.018867924528...]
    '''
    id = 'CS8'
    def __init__(self, dataOrStream=None, *arguments, **keywords):
        featuresModule.FeatureExtractor.__init__(self, dataOrStream=dataOrStream,  *arguments, **keywords)

        self.name = 'Diminished Triad Simultaneity Prevalence'
        self.description = 'Percentage of all simultaneities that are diminished triads.'
        self.dimensions = 1
        self.discrete = False 

    def _process(self):
        '''Do processing necessary, storing result in _feature.
        '''
        # use for total number of chords
        total = len(self.data['chordify.getElementsByClass.Chord'])
        histo = self.data['chordifyTypesHistogram']
        # using incomplete
        part = histo['isDiminishedTriad']
        self._feature.vector[0] = part / float(total)


class TriadSimultaneityPrevalence(featuresModule.FeatureExtractor):
    '''
    Gives the proportion of all simultaneities which form triads (major,
    minor, diminished, or augmented)
    
    
    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.native.TriadSimultaneityPrevalence(s)
    >>> fe.extract().vector 
    [0.71698...]
    >>> s2 = corpus.parse('schoenberg/opus19', 2)
    >>> fe2 = features.native.TriadSimultaneityPrevalence(s2)
    >>> fe2.extract().vector
    [0.022727...]
    '''
    id = 'CS9'
    def __init__(self, dataOrStream=None, *arguments, **keywords):
        featuresModule.FeatureExtractor.__init__(self, dataOrStream=dataOrStream,  *arguments, **keywords)

        self.name = 'Triad Simultaneity Prevalence'
        self.description = 'Proportion of all simultaneities that form triads.'
        self.dimensions = 1
        self.discrete = False 

    def _process(self):
        '''Do processing necessary, storing result in _feature.
        '''
        # use for total number of chords
        total = len(self.data['chordify.getElementsByClass.Chord'])
        histo = self.data['chordifyTypesHistogram']
        # using incomplete
        part = histo['isTriad']
        self._feature.vector[0] = part / float(total)



class DiminishedSeventhSimultaneityPrevalence(featuresModule.FeatureExtractor):
    '''Percentage of all simultaneities that are diminished seventh chords.
    
    >>> s = corpus.parse('bwv66.6') 
    >>> fe = features.native.DiminishedSeventhSimultaneityPrevalence(s)
    >>> fe.extract().vector 
    [0.0]
    '''
    id = 'CS10'
    def __init__(self, dataOrStream=None, *arguments, **keywords):
        featuresModule.FeatureExtractor.__init__(self, dataOrStream=dataOrStream,  *arguments, **keywords)

        self.name = 'Diminished Seventh Simultaneity Prevalence'
        self.description = 'Percentage of all simultaneities that are diminished seventh chords.'
        self.dimensions = 1
        self.discrete = False 

    def _process(self):
        '''Do processing necessary, storing result in _feature.
        '''
        # use for total number of chords
        total = len(self.data['chordify.getElementsByClass.Chord'])
        histo = self.data['chordifyTypesHistogram']
        # using incomplete
        part = histo['isDiminishedSeventh']
        self._feature.vector[0] = part / float(total)

class IncorrectlySpelledTriadPrevalence(featuresModule.FeatureExtractor):
    '''
    Percentage of all triads that are spelled incorrectly.

    example:

    Mozart k155 movement 2 has a single instance of an incorrectly spelled
    triad (m. 17, where the C# of an A-major chord has a lower neighbor B#
    thus temporarily creating an incorrectly spelled A-minor chord).
    
    We would expect highly chromatic music such as Reger or Wagner to have
    a higher percentage, or automatically rendered MIDI
    transcriptions (which don't distinguish between D# and Eb).
        
    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.native.IncorrectlySpelledTriadPrevalence(s)
    >>> fe.extract().vector 
    [0.02...]
    '''
    id = 'CS11'
    def __init__(self, dataOrStream=None, *arguments, **keywords):
        featuresModule.FeatureExtractor.__init__(self, dataOrStream=dataOrStream,  *arguments, **keywords)

        self.name = 'Incorrectly Spelled Triad Prevalence'
        self.description = 'Percentage of all triads that are spelled incorrectly.'
        self.dimensions = 1
        self.discrete = False 

    def _process(self):
        '''Do processing necessary, storing result in _feature.
        '''
        # use for total number of chords
        histo = self.data['chordifyTypesHistogram']
        # using incomplete
        totalCorrectlySpelled = histo['isTriad']
        forteData = self.data['chordifySetClassHistogram']
        totalForteTriads = 0
        if "3-11" in forteData:
            totalForteTriads += forteData['3-11']
        if "3-12" in forteData:
            totalForteTriads += forteData['3-12']
        if "3-10" in forteData:
            totalForteTriads += forteData['3-10']
        
        totalIncorrectlySpelled = totalForteTriads - totalCorrectlySpelled
        
        self._feature.vector[0] = totalIncorrectlySpelled / float(totalForteTriads)


class ChordBassMotionFeature(featuresModule.FeatureExtractor):
    '''
    A twelve element feature that reports the fraction
    of all chord motion of music21.harmony.Harmony objects
    that move up by i-half-steps. (a half-step motion down would
    be stored in i = 11).  i = 0 is always 0.0 since consecutive
    chords on the same pitch are ignored (unless there are 0 or 1 harmonies, in which case it is 1)
       
    Sample test on Dylan's Blowing In The Wind (not included), showing all motion is 3rds, 6ths, or especially 4ths and 5ths.
    
    s = corpus.parse('demos/BlowinInTheWind') 
    fe = features.native.ChordBassMotionFeature(s)
    fe.extract().vector 
    
    [0.0, 0.0, 0.0, 0.0416..., 0.0416..., 0.166..., 0.0, 0.54166..., 0.0, 0.0, 0.2083... 0.0]


    For comparison, the Beatles Here Comes the Sun has more tone motion

    [0.0, 0.05..., 0.14..., 0.03..., 0.06..., 0.3..., 0.008..., 0.303..., 0.0, 0.0, 0.07..., 0.008...]
    
    Post 1990s music has a lot more semitone motion.
    
    '''
    id = 'CS12'
    def __init__(self, dataOrStream=None, *arguments, **keywords):
        featuresModule.FeatureExtractor.__init__(self, dataOrStream=dataOrStream,  *arguments, **keywords)

        self.name = 'Chord Bass Motion'
        self.description = '12-element vector showing the fraction of chords that move by x semitones (where x=0 is always 0 unless there are 0 or 1 harmonies, in which case it is 1).'
        self.dimensions = 12
        self.discrete = False 

    def _process(self):
        '''Do processing necessary, storing result in _feature.
        '''
        # use for total number of chords
        harms = self.data['flat.getElementsByClass.Harmony']

        totMotion = [0,0,0,0,0,0,0,0,0,0,0,0]
        totalHarmonicMotion = 0
        lastHarm = None
        
        for thisHarm in harms:
            if lastHarm is None:
                lastHarm = thisHarm
            else:
                if lastHarm.bass() is not None:
                    lastBass = lastHarm.bass()
                else:
                    lastBass = lastHarm.root()
                    
                if thisHarm.bass() is not None:
                    thisBass = thisHarm.bass()
                else:
                    thisBass = thisHarm.root()
                    
                if lastBass.pitchClass == thisBass.pitchClass:
                    pass
                else:
                    halfStepMotion = (lastBass.pitchClass - thisBass.pitchClass) % 12
                    totMotion[halfStepMotion] += 1
                    totalHarmonicMotion += 1
                    lastHarm = thisHarm
                    
        if totalHarmonicMotion == 0:
            vector = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        else:
            totHarmonicMotionFraction = [0.0, 0,0, 0,0,0, 0,0,0, 0,0,0]
            for i in range(1, 12):
                totHarmonicMotionFraction[i] = float(totMotion[i]) / totalHarmonicMotion
            vector = totHarmonicMotionFraction


        self._feature.vector = vector


#-------------------------------------------------------------------------------
# metadata

class URLOpenerUI(FancyURLopener):
    version = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11) Gecko/20071127 Firefox/2.0.0.11'

googleResultsRE = re.compile(r'([\d\,]+) results')

class ComposerPopularity(featuresModule.FeatureExtractor):
    '''
    composer's popularity today, as measured by the number of
    Google search results (log-10)

    
    >>> #_DOCS_SHOW s = corpus.parse('mozart/k155', 2)
    >>> s = stream.Score() #_DOCS_HIDE
    >>> s.append(metadata.Metadata()) #_DOCS_HIDE
    >>> s.metadata.composer = "W.A. Mozart" #_DOCS_HIDE
    >>> fe = features.native.ComposerPopularity(s)
    >>> fe.extract().vector[0] > 6.0 
    True
    '''
    id = 'MD1'
    def __init__(self, dataOrStream=None, *arguments, **keywords):
        featuresModule.FeatureExtractor.__init__(self, dataOrStream=dataOrStream,  *arguments, **keywords)

        self.name = 'Composer Popularity'
        self.description = 'Composer popularity today, as measured by the number of Google search results (log-10).'
        self.dimensions = 1
        self.discrete = False 

    def _process(self):
        '''Do processing necessary, storing result in _feature.
        '''
        # use for total number of chords
        
        resultsLog = 0
#        try:
        md = self.data['metadata']
        if md is None:
            return 0
        composer = md.composer
        if composer is None or composer == "":
            return 0
        paramsBasic = {'q': composer}

        myGoogle = URLOpenerUI()
        params = urlencode(paramsBasic)
        page = myGoogle.open("http://www.google.com/search?%s" % params)
        the_page = page.read()
        if six.PY3:
            the_page = the_page.decode('utf-8')
        
        m = googleResultsRE.search(the_page)
        if m is not None and m.group(0):
            totalRes = int(m.group(1).replace(',',""))
            if totalRes > 0:
                resultsLog = math.log(totalRes, 10)
            else: 
                resultsLog = -1
#        except:
#            resultsLog = 0
        
        self._feature.vector[0] = resultsLog



#-------------------------------------------------------------------------------
# melodic contour


class LandiniCadence(featuresModule.FeatureExtractor):
    '''Return a bolean if one or more Parts end with a Landini-like cadential figure.

    
    '''
    id = 'MC1'
    def __init__(self, dataOrStream=None, *arguments, **keywords):
        featuresModule.FeatureExtractor.__init__(self, dataOrStream=dataOrStream,  *arguments, **keywords)

        self.name = 'Ends With Landini Melodic Contour'
        self.description = 'Boolean that indicates the presence of a Landini-like cadential figure in one or more parts.'
        self.dimensions = 1
        self.discrete = False 

    def _process(self):
        '''Do processing necessary, storing result in _feature.
        '''
        # store plausible ending half step movements
        # these need to be lists for comparison
        match = [[-2, 3], [-1, -2, 3]]

        cBundle = []
        if self.data.partsCount > 0:
            for i in range(self.data.partsCount):
                cList = self.data['parts'][i]['contourList']
                cBundle.append(cList)
        else:
            cList = self.data['contourList']
            cBundle.append(cList)

        # iterate over each contour
        found = False
        for cList in cBundle:
            # remove repeated notes
            cListClean = []
            for c in cList:
                if c != 0:
                    cListClean.append(c)
            # find matches
            for cMatch in match:
                #environLocal.printDebug(['cList', cList, 'cListClean', cListClean, 'cMatch', cMatch])
                # compare to last
                if len(cListClean) >= len(cMatch):
                    # get the len of the last elements
                    if cListClean[-len(cMatch):] == cMatch:
                        found = True
                        break
            if found: 
                break
        if found:
            self._feature.vector[0] = 1



#------------------------------------------------------------------------------
# text features

class LanguageFeature(featuresModule.FeatureExtractor):
    '''
    language of text as a number
    the number is the index of text.LanguageDetector.languageCodes + 1
    or 0 if there is no language.

    
    Detect that the language of a Handel aria is Italian.

    >>> s = corpus.parse('handel/rinaldo/lascia_chio_pianga') 
    >>> fe = features.native.LanguageFeature(s)
    >>> fe.extract().vector
    [3]
    '''
    id = 'TX1'

    def __init__(self, dataOrStream=None, *arguments, **keywords):
        featuresModule.FeatureExtractor.__init__(self, dataOrStream=dataOrStream,  *arguments, **keywords)

        self.name = 'Language Feature'
        self.description = 'Languge of the lyrics of the piece given as a numeric value from text.LanguageDetector.mostLikelyLanguageNumeric().'
        self.dimensions = 1
        self.discrete = True
        self.languageDetector = text.LanguageDetector()
    def _process(self):
        '''Do processing necessary, storing result in _feature.
        '''
        storedLyrics = self.data['assembledLyrics']
        self._feature.vector[0] = self.languageDetector.mostLikelyLanguageNumeric(storedLyrics)




#-------------------------------------------------------------------------------




featureExtractors = [
QualityFeature, #p22

TonalCertainty, #k1

UniqueNoteQuarterLengths, # ql1
MostCommonNoteQuarterLength, # ql2
MostCommonNoteQuarterLengthPrevalence, # ql3
RangeOfNoteQuarterLengths, # ql4

UniquePitchClassSetSimultaneities, # cs1
UniqueSetClassSimultaneities, # cs2
MostCommonPitchClassSetSimultaneityPrevalence, # cs3
MostCommonSetClassSimultaneityPrevalence, # cs4
MajorTriadSimultaneityPrevalence, # cs5
MinorTriadSimultaneityPrevalence, # cs6
DominantSeventhSimultaneityPrevalence, # cs7
DiminishedTriadSimultaneityPrevalence, # cs8
TriadSimultaneityPrevalence, # cs9
DiminishedSeventhSimultaneityPrevalence, # cs10
IncorrectlySpelledTriadPrevalence, # cs11
ChordBassMotionFeature, #cs12

ComposerPopularity, #md1

LandiniCadence, #mc1

LanguageFeature, #tx1
]





#-------------------------------------------------------------------------------
class Test(unittest.TestCase):
    
    def runTest(self):
        pass

    def testIncorrectlySpelledTriadPrevalence(self):
        from music21 import stream, features, chord
        
        s = stream.Stream()
        s.append(chord.Chord(['c', 'e', 'g']))
        s.append(chord.Chord(['c', 'e', 'a']))
        s.append(chord.Chord(['c', 'd#', 'g']))
        s.append(chord.Chord(['c', 'd#', 'a--']))

        fe = features.native.IncorrectlySpelledTriadPrevalence(s)
        self.assertEqual(str(fe.extract().vector[0]), '0.5')



    def testLandiniCadence(self):
        from music21 import converter, features

        s = converter.parse('tinynotation: 3/4 f#4 f# e g2')
        fe = features.native.LandiniCadence(s)
        self.assertEqual(fe.extract().vector[0], 1)        
        
        s = converter.parse('tinynotation: 3/4 f#4 f# f# g2')
        fe = features.native.LandiniCadence(s)
        self.assertEqual(fe.extract().vector[0], 0)        

        s = converter.parse('tinynotation: 3/4 f#4 e a g2')
        fe = features.native.LandiniCadence(s)
        self.assertEqual(fe.extract().vector[0], 0)        



if __name__ == "__main__":
    import music21
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof




