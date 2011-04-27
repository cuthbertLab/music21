#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         features.native.py
# Purpose:      music21 feature extractors
#
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

'''Original music21 feature extractors.
'''



import unittest
import music21

from music21.features import base as featuresModule

from music21 import environment
_MOD = 'features/native.py'
environLocal = environment.Environment(_MOD)






# ideas for other music21 features extactors
# and not available in midi

# clef usage
# enhmaronic usage

# key signature histogram
# array of circle of fiths

# lyrics
# luca gloria: is common
# searching for numbers of hits
# is vowel placed on strongest beat
# wikifonia

# essen local
# getting elevation

# automatic key analysis
# as a method of feature extraction



#-------------------------------------------------------------------------------
# features that use metrical distinctions

class FirstBeatAttackPrevelance(featuresModule.FeatureExtractor):
    '''
    >>> from music21 import *
    >>> s = corpus.parse('hwv56/movement3-05.md')
    >>> fe = features.native.FirstBeatAttackPrevelance(s)
    '''
    def __init__(self, dataOrStream=None, *arguments, **keywords):
        featuresModule.FeatureExtractor.__init__(self, dataOrStream=dataOrStream,  *arguments, **keywords)

        self.name = 'First Beat Attack Prevelance'
        self.description = 'Fraction of first beats of a measure that have notes that start on this beat.'
        self.dimensions = 1
        self.discrete = False 




#-------------------------------------------------------------------------------
# employing symbolic durations


class UniqueNoteQuarterLengths(featuresModule.FeatureExtractor):
    '''
    >>> from music21 import *
    >>> s = corpus.parse('hwv56/movement3-05.md')
    >>> fe = features.native.UniqueNoteQuarterLengths(s)
    >>> fe.extract().vector 
    [7]
    '''
    id = 'D1'
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
    >>> from music21 import *
    >>> s = corpus.parse('hwv56/movement3-05.md')
    >>> fe = features.native.MostCommonNoteQuarterLength(s)
    >>> fe.extract().vector 
    [0.5]
    '''
    id = 'D2'
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
        max = 0
        ql = 0
        for key in histo:
            # all defined keys should be greater than zero, but just in case
            if histo[key] >= max:
                max = histo[key]
                ql = key
        self._feature.vector[0] = ql


class MostCommonNoteQuarterLengthPrevelance(featuresModule.FeatureExtractor):
    '''
    >>> from music21 import *
    >>> s = corpus.parse('hwv56/movement3-05.md')
    >>> fe = features.native.MostCommonNoteQuarterLengthPrevelance(s)
    >>> fe.extract().vector 
    [0.533333...]
    '''
    id = 'D3'
    def __init__(self, dataOrStream=None, *arguments, **keywords):
        featuresModule.FeatureExtractor.__init__(self, dataOrStream=dataOrStream,  *arguments, **keywords)

        self.name = 'Most Common Note Quarter Length Prevalance'
        self.description = 'Fraction of notes that have the most common quarter length.'
        self.dimensions = 1
        self.discrete = False 

    def _process(self):
        '''Do processing necessary, storing result in _feature.
        '''
        sum = 0 # count of all 
        histo = self.data['noteQuarterLengthHistogram']
        maxKey = 0 # max found for any one key
        for key in histo:
            # all defined keys should be greater than zero, but just in case
            if histo[key] > 0:
                sum += histo[key]
                if histo[key] >= maxKey:
                    maxKey = histo[key]
        self._feature.vector[0] = maxKey / float(sum)



class RangeOfNoteQuarterLengths(featuresModule.FeatureExtractor):
    '''
    >>> from music21 import *
    >>> s = corpus.parse('hwv56/movement3-05.md')
    >>> fe = features.native.RangeOfNoteQuarterLengths(s)
    >>> fe.extract().vector 
    [3.75]
    '''
    id = 'D4'
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

class UniquePitchClassSetSimultaneities(featuresModule.FeatureExtractor):
    '''
    >>> from music21 import *
    >>> s = corpus.parse('hwv56/movement3-05.md')
    >>> fe = features.native.UniquePitchClassSetSimultaneities(s)
    >>> fe.extract().vector
    [15]
    '''
    id = 'S1'
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
    '''
    >>> from music21 import *
    >>> s = corpus.parse('hwv56/movement3-05.md')
    >>> fe = features.native.UniqueSetClassSimultaneities(s)
    >>> fe.extract().vector
    [7]
    '''
    id = 'S2'
    def __init__(self, dataOrStream=None, *arguments, **keywords):
        featuresModule.FeatureExtractor.__init__(self, dataOrStream=dataOrStream,  *arguments, **keywords)

        self.name = 'Unique Set Class Simultaneities'
        self.description = 'Number of unique pitch class simultaneities.'
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


class MostCommonPitchClassSetSimultaneityPrevelance(
    featuresModule.FeatureExtractor):
    '''
    >>> from music21 import *
    >>> s = corpus.parse('hwv56/movement3-05.md')
    >>> fe = features.native.MostCommonPitchClassSetSimultaneityPrevelance(s)
    >>> fe.extract().vector
    [0.166666666...]
    '''
    id = 'S3'
    def __init__(self, dataOrStream=None, *arguments, **keywords):
        featuresModule.FeatureExtractor.__init__(self, dataOrStream=dataOrStream,  *arguments, **keywords)

        self.name = 'Most Common Pitch Class Set Simultaneity Prevelance'
        self.description = 'Fraction of all pitch class simultaneities that are the most common simultaneity.'
        self.dimensions = 1
        self.discrete = False 

    def _process(self):
        '''Do processing necessary, storing result in _feature.
        '''
        sum = 0 # count of all 
        histo = self.data['chordifyPitchClassSetHistogram']
        maxKey = 0 # max found for any one key
        for key in histo:
            # all defined keys should be greater than zero, but just in case
            if histo[key] > 0:
                sum += histo[key]
                if histo[key] >= maxKey:
                    maxKey = histo[key]
        self._feature.vector[0] = maxKey / float(sum)


class MostCommonSetClassSimultaneityPrevelance(featuresModule.FeatureExtractor):
    '''
    >>> from music21 import *
    >>> s = corpus.parse('hwv56/movement3-05.md')
    >>> fe = features.native.MostCommonSetClassSimultaneityPrevelance(s)
    >>> fe.extract().vector
    [0.2916...]
    >>> s2 = corpus.parse('schoenberg/opus19', 6)
    >>> fe2 = features.native.MostCommonSetClassSimultaneityPrevelance(s2)
    >>> fe2.extract().vector
    [0.3846...]
    '''
    id = 'S4'
    def __init__(self, dataOrStream=None, *arguments, **keywords):
        featuresModule.FeatureExtractor.__init__(self, dataOrStream=dataOrStream,  *arguments, **keywords)

        self.name = 'Most Common Set Class Simultaneity Prevelance'
        self.description = 'Fraction of all set class simultaneities that are the most common simultaneity.'
        self.dimensions = 1
        self.discrete = False 

    def _process(self):
        '''Do processing necessary, storing result in _feature.
        '''
        sum = 0 # count of all 
        histo = self.data['chordifySetClassHistogram']
        maxKey = 0 # max found for any one key
        for key in histo:
            # all defined keys should be greater than zero, but just in case
            if histo[key] > 0:
                sum += histo[key]
                if histo[key] >= maxKey:
                    maxKey = histo[key]
        self._feature.vector[0] = maxKey / float(sum)


class MajorTriadSimultaneityPrevelance(featuresModule.FeatureExtractor):
    '''
    >>> from music21 import *
    >>> s = corpus.parse('hwv56/movement3-05.md')
    >>> fe = features.native.MajorTriadSimultaneityPrevelance(s)
    >>> fe.extract().vector
    [0.1666666666...]
    '''
    id = 'S5'
    def __init__(self, dataOrStream=None, *arguments, **keywords):
        featuresModule.FeatureExtractor.__init__(self, dataOrStream=dataOrStream,  *arguments, **keywords)

        self.name = 'Major Triad Simultaneity Prevelance'
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


class MinorTriadSimultaneityPrevelance(featuresModule.FeatureExtractor):
    '''
    >>> from music21 import *
    >>> s = corpus.parse('hwv56/movement3-05.md')
    >>> fe = features.native.MinorTriadSimultaneityPrevelance(s)
    >>> fe.extract().vector # same as major in this work
    [0.1666666666...]
    '''
    id = 'S6'
    def __init__(self, dataOrStream=None, *arguments, **keywords):
        featuresModule.FeatureExtractor.__init__(self, dataOrStream=dataOrStream,  *arguments, **keywords)

        self.name = 'Minor Triad Simultaneity Prevelance'
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


class DominantSeventhSimultaneityPrevelance(featuresModule.FeatureExtractor):
    '''
    >>> from music21 import *
    >>> s = corpus.parse('hwv56/movement3-05.md')
    >>> fe = features.native.DominantSeventhSimultaneityPrevelance(s)
    >>> fe.extract().vector 
    [0.0]
    '''
    id = 'S7'
    def __init__(self, dataOrStream=None, *arguments, **keywords):
        featuresModule.FeatureExtractor.__init__(self, dataOrStream=dataOrStream,  *arguments, **keywords)

        self.name = 'Dominant Seventh Simultaneity Prevelance'
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
        part = histo['isDominantSeventh']
        self._feature.vector[0] = part / float(total)


class DiminishedTriadSimultaneityPrevelance(featuresModule.FeatureExtractor):
    '''
    >>> from music21 import *
    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.native.DiminishedTriadSimultaneityPrevelance(s)
    >>> fe.extract().vector 
    [0.020408163265...]
    '''
    id = 'S8'
    def __init__(self, dataOrStream=None, *arguments, **keywords):
        featuresModule.FeatureExtractor.__init__(self, dataOrStream=dataOrStream,  *arguments, **keywords)

        self.name = 'Diminished Triad Simultaneity Prevelance'
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
        part = histo['isDiminishedTriad']
        self._feature.vector[0] = part / float(total)


class TriadSimultaneityPrevelance(featuresModule.FeatureExtractor):
    '''
    >>> from music21 import *
    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.native.TriadSimultaneityPrevelance(s)
    >>> fe.extract().vector 
    [0.7142857142...]
    >>> s2 = corpus.parse('schoenberg/opus19', 2)
    >>> fe2 = features.native.TriadSimultaneityPrevelance(s2)
    >>> fe2.extract().vector
    [0.04...]
    '''
    id = 'S9'
    def __init__(self, dataOrStream=None, *arguments, **keywords):
        featuresModule.FeatureExtractor.__init__(self, dataOrStream=dataOrStream,  *arguments, **keywords)

        self.name = 'Triad Simultaneity Prevelance'
        self.description = 'Percentage of all simultaneities that triads.'
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


class DiminishedSeventhSimultaneityPrevelance(featuresModule.FeatureExtractor):
    '''
    >>> from music21 import *
    >>> s = corpus.parse('hwv56/movement3-05.md')
    >>> fe = features.native.DiminishedSeventhSimultaneityPrevelance(s)
    >>> fe.extract().vector 
    [0.0]
    '''
    id = 'S10'
    def __init__(self, dataOrStream=None, *arguments, **keywords):
        featuresModule.FeatureExtractor.__init__(self, dataOrStream=dataOrStream,  *arguments, **keywords)

        self.name = 'Diminished Seventh Simultaneity Prevelance'
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


featureExtractors = [
UniqueNoteQuarterLengths, # d1
MostCommonNoteQuarterLength, # d2
MostCommonNoteQuarterLengthPrevelance, # d3
RangeOfNoteQuarterLengths, # d4

UniquePitchClassSetSimultaneities, # s1
UniqueSetClassSimultaneities, # s2
MostCommonPitchClassSetSimultaneityPrevelance, # s3
MostCommonSetClassSimultaneityPrevelance, # s4
MajorTriadSimultaneityPrevelance, # s5
MinorTriadSimultaneityPrevelance, # s6
DominantSeventhSimultaneityPrevelance, # s7
DiminishedTriadSimultaneityPrevelance, # s8
TriadSimultaneityPrevelance, # s9
DiminishedSeventhSimultaneityPrevelance, # s10

]





#-------------------------------------------------------------------------------
class Test(unittest.TestCase):
    
    def runTest(self):
        pass




if __name__ == "__main__":
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof




