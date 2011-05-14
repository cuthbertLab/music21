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
# luca gloria:
# searching for numbers of hits
# is vowel placed on strongest beat
# wikifonia

# idea of language specific

# essen local
# getting elevation

# automatic key analysis
# as a method of feature extraction

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


    Example: Mozart k155, mvmt 2 (musicxml) is explicitly encoded as being in Major:

    
    >>> from music21 import *
    >>> mozart155mvmt2 = corpus.parse('mozart/k155', 2)
    >>> fe = features.native.QualityFeature(mozart155mvmt2)
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
                raise NativeFeaturesException("should be able to get a mode from something here -- perhaps there are no notes?")

        self._feature.vector[0] = keyFeature
    
    




#=======
# key detection on windowed segments
# prevalence m/M over 4 bar windwows

# chromatic alteration related to beat position


# landini cadence
# scales steps 7 / 7 / 6 / 1
# antepenultimate note is half step below final




#-------------------------------------------------------------------------------
# features that use metrical distinctions

class FirstBeatAttackPrevelance(featuresModule.FeatureExtractor):
    '''
    >>> from music21 import *
    >>> s = corpus.parse('hwv56/movement3-05.md')
    >>> fe = features.native.FirstBeatAttackPrevelance(s)
    '''
    id = 'MP1'
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
    >>> from music21 import *
    >>> s = corpus.parse('hwv56/movement3-05.md')
    >>> fe = features.native.MostCommonNoteQuarterLength(s)
    >>> fe.extract().vector 
    [0.5]
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
    id = 'QL3'
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
    '''Difference between the longest and shortest quarter lengths.

    >>> from music21 import *
    >>> s = corpus.parse('hwv56/movement3-05.md')
    >>> fe = features.native.RangeOfNoteQuarterLengths(s)
    >>> fe.extract().vector 
    [3.75]
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

class UniquePitchClassSetSimultaneities(featuresModule.FeatureExtractor):
    '''Number of unique pitch class simultaneities.

    >>> from music21 import *
    >>> s = corpus.parse('hwv56/movement3-05.md')
    >>> fe = features.native.UniquePitchClassSetSimultaneities(s)
    >>> fe.extract().vector
    [15]
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

    >>> from music21 import *
    >>> s = corpus.parse('hwv56/movement3-05.md')
    >>> fe = features.native.UniqueSetClassSimultaneities(s)
    >>> fe.extract().vector
    [7]
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


class MostCommonPitchClassSetSimultaneityPrevelance(
    featuresModule.FeatureExtractor):
    '''Fraction of all pitch class simultaneities that are the most common simultaneity.

    >>> from music21 import *
    >>> s = corpus.parse('hwv56/movement3-05.md')
    >>> fe = features.native.MostCommonPitchClassSetSimultaneityPrevelance(s)
    >>> fe.extract().vector
    [0.166666666...]
    '''
    id = 'CS3'
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
    '''Fraction of all set class simultaneities that are the most common simultaneity.

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
    id = 'CS4'
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
    '''Percentage of all simultaneities that are major triads.

    >>> from music21 import *
    >>> s = corpus.parse('hwv56/movement3-05.md')
    >>> fe = features.native.MajorTriadSimultaneityPrevelance(s)
    >>> fe.extract().vector
    [0.1666666666...]
    '''
    id = 'CS5'
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
    '''Percentage of all simultaneities that are minor triads.

    >>> from music21 import *
    >>> s = corpus.parse('hwv56/movement3-05.md')
    >>> fe = features.native.MinorTriadSimultaneityPrevelance(s)
    >>> fe.extract().vector # same as major in this work
    [0.1666666666...]
    '''
    id = 'CS6'
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
    '''Percentage of all simultaneities that are dominant seventh.

    >>> from music21 import *
    >>> s = corpus.parse('hwv56/movement3-05.md')
    >>> fe = features.native.DominantSeventhSimultaneityPrevelance(s)
    >>> fe.extract().vector 
    [0.0]
    '''
    id = 'CS7'
    def __init__(self, dataOrStream=None, *arguments, **keywords):
        featuresModule.FeatureExtractor.__init__(self, dataOrStream=dataOrStream,  *arguments, **keywords)

        self.name = 'Dominant Seventh Simultaneity Prevelance'
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


class DiminishedTriadSimultaneityPrevelance(featuresModule.FeatureExtractor):
    '''Percentage of all simultaneities that are diminished triads.

    >>> from music21 import *
    >>> s = corpus.parse('bwv66.6')
    >>> fe = features.native.DiminishedTriadSimultaneityPrevelance(s)
    >>> fe.extract().vector 
    [0.020408163265...]
    '''
    id = 'CS8'
    def __init__(self, dataOrStream=None, *arguments, **keywords):
        featuresModule.FeatureExtractor.__init__(self, dataOrStream=dataOrStream,  *arguments, **keywords)

        self.name = 'Diminished Triad Simultaneity Prevelance'
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


class TriadSimultaneityPrevelance(featuresModule.FeatureExtractor):
    '''
    Gives the proportion of all simultaneities which form triads (major,
    minor, diminished, or augmented)
    
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
    id = 'CS9'
    def __init__(self, dataOrStream=None, *arguments, **keywords):
        featuresModule.FeatureExtractor.__init__(self, dataOrStream=dataOrStream,  *arguments, **keywords)

        self.name = 'Triad Simultaneity Prevelance'
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


#class IncorrectlySpelledTriad

class DiminishedSeventhSimultaneityPrevelance(featuresModule.FeatureExtractor):
    '''Percentage of all simultaneities that are diminished seventh chords.

    >>> from music21 import *
    >>> s = corpus.parse('hwv56/movement3-05.md')
    >>> fe = features.native.DiminishedSeventhSimultaneityPrevelance(s)
    >>> fe.extract().vector 
    [0.0]
    '''
    id = 'CS10'
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




class IncorrectlySpelledTriadPrevelance(featuresModule.FeatureExtractor):
    '''Percentage of all 0,3,7 set classes that are incorrectly spelled triads..

    >>> from music21 import *
    >>> s = corpus.parse('hwv56/movement3-05.md')
    >>> fe = features.native.DiminishedSeventhSimultaneityPrevelance(s)
    >>> fe.extract().vector 
    [0.0]
    '''
    id = 'CS11'
    def __init__(self, dataOrStream=None, *arguments, **keywords):
        featuresModule.FeatureExtractor.__init__(self, dataOrStream=dataOrStream,  *arguments, **keywords)

        self.name = 'Incorrectly Spelled Triad Prevelance'
        self.description = 'Percentage of all 0,3,7 set classes that are incorrectly spelled triads.'
        self.dimensions = 1
        self.discrete = False 

    def _process(self):
        '''Do processing necessary, storing result in _feature.
        '''
        # use for total number of chords
        #total = len(self.data['chordify.getElementsByClass.Chord'])

        histo = self.data['chordifyTypesHistogram']        

        # find number of chords that that are not triads but have 
        # a 0,3,7 pitch class set
        count = 0
        for c in self.data['chordify.getElementsByClass.Chord']:
            if c.normalForm == [0, 3, 7] and c.isTriad() is False:
                count += 1
        environLocal.printDebug(['got count', count])
        # isTriad stores a count
        total = histo['isTriad'] + count
        self._feature.vector[0] = count / float(total)









featureExtractors = [
QualityFeature, #p22

UniqueNoteQuarterLengths, # ql1
MostCommonNoteQuarterLength, # ql2
MostCommonNoteQuarterLengthPrevelance, # ql3
RangeOfNoteQuarterLengths, # ql4

UniquePitchClassSetSimultaneities, # cs1
UniqueSetClassSimultaneities, # cs2
MostCommonPitchClassSetSimultaneityPrevelance, # cs3
MostCommonSetClassSimultaneityPrevelance, # cs4
MajorTriadSimultaneityPrevelance, # cs5
MinorTriadSimultaneityPrevelance, # cs6
DominantSeventhSimultaneityPrevelance, # cs7
DiminishedTriadSimultaneityPrevelance, # cs8
TriadSimultaneityPrevelance, # cs9
DiminishedSeventhSimultaneityPrevelance, # cs10
IncorrectlySpelledTriadPrevelance, # cs10

]





#-------------------------------------------------------------------------------
class Test(unittest.TestCase):
    
    def runTest(self):
        pass

    def testIncorrectlySpelledTriadPrevelance(self):
        from music21 import stream, features, chord, corpus, graph

        s = stream.Stream()
        s.append(chord.Chord(['c', 'e', 'g']))
        s.append(chord.Chord(['c', 'e', 'g']))
        s.append(chord.Chord(['c', 'd#', 'g']))
        s.append(chord.Chord(['c', 'd#', 'g']))

        fe = features.native.IncorrectlySpelledTriadPrevelance(s)
        self.assertEqual(str(fe.extract().vector[0]), '0.5')


#         streamList = corpus.bachChorales[200:220]
#         feList = ['cs9', 'cs11']
#         p = graph.PlotFeatures(streamList, feList)
#         p.process()



if __name__ == "__main__":
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof




